import math
import time
from dataclasses import asdict, dataclass, field
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import Document, DocumentChunk, DocumentStatus
from app.services.providers import get_embedding_provider, get_llm_provider


@dataclass
class AgentState:
    user_id: UUID
    question: str
    session_id: UUID
    top_k: int = 8
    document_ids: list[UUID] | None = None
    document_type: str | None = None
    uploaded_by: UUID | None = None
    question_type: str = "research_synthesis"
    rewritten_question: str = ""
    retrieval_plan: str = ""
    retrieved_chunks: list[dict[str, Any]] = field(default_factory=list)
    reranked_chunks: list[dict[str, Any]] = field(default_factory=list)
    draft_answer: str = ""
    citations: list[dict[str, Any]] = field(default_factory=list)
    critic_feedback: str = ""
    confidence_score: float = 0
    confidence_band: str = "low"
    human_review_required: bool = False
    final_answer: str = ""
    total_tokens: int = 0
    estimated_cost: float = 0
    trace: list[dict[str, Any]] = field(default_factory=list)


def _trace(state: AgentState, node: str, inp: str, out: str, started: float) -> None:
    state.trace.append(
        {
            "node_name": node,
            "input_summary": inp[:500],
            "output_summary": out[:500],
            "status": "completed",
            "latency_ms": int((time.perf_counter() - started) * 1000),
        }
    )


def classify_question(state: AgentState) -> AgentState:
    started = time.perf_counter()
    q = state.question.lower()
    if "compare" in q:
        state.question_type = "comparison"
    elif "risk" in q:
        state.question_type = "risk_summary"
    elif "weak" in q or "citation" in q:
        state.question_type = "citation_audit"
    else:
        state.question_type = "research_synthesis"
    state.rewritten_question = state.question.strip()
    _trace(state, "question_classifier", state.question, state.question_type, started)
    return state


def plan_retrieval(state: AgentState) -> AgentState:
    started = time.perf_counter()
    state.retrieval_plan = f"Retrieve top {state.top_k} processed chunks for {state.question_type}."
    _trace(state, "planner", state.question_type, state.retrieval_plan, started)
    return state


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b, strict=False))
    an = math.sqrt(sum(x * x for x in a)) or 1
    bn = math.sqrt(sum(y * y for y in b)) or 1
    return dot / (an * bn)


def retrieve_chunks(db: Session, state: AgentState) -> AgentState:
    started = time.perf_counter()
    query_vector = get_embedding_provider().embed(state.rewritten_question or state.question)
    distance = DocumentChunk.embedding.cosine_distance(query_vector).label("distance")
    stmt = (
        select(DocumentChunk, Document, distance)
        .join(Document, Document.id == DocumentChunk.document_id)
        .where(Document.status == DocumentStatus.processed)
        .order_by(distance)
        .limit(state.top_k)
    )
    if state.document_ids:
        stmt = stmt.where(Document.id.in_(state.document_ids))
    if state.document_type:
        stmt = stmt.where(Document.document_type == state.document_type)
    if state.uploaded_by:
        stmt = stmt.where(Document.uploaded_by == state.uploaded_by)
    rows = db.execute(stmt).all()
    scored = []
    for chunk, doc, db_distance in rows:
        score = 1 - float(db_distance or 0)
        scored.append(
            {
                "chunk_id": chunk.id,
                "document_id": doc.id,
                "document_name": doc.original_filename,
                "document_type": doc.document_type,
                "content": chunk.content,
                "page_number": chunk.page_number,
                "section_title": chunk.section_title,
                "relevance_score": round(max(0.0, min(1.0, score)), 4),
            }
        )
    state.retrieved_chunks = scored
    _trace(state, "retriever", state.retrieval_plan, f"Retrieved {len(state.retrieved_chunks)} chunks", started)
    return state


def rerank_chunks(state: AgentState) -> AgentState:
    started = time.perf_counter()
    q_terms = set(state.question.lower().split())
    state.reranked_chunks = sorted(
        state.retrieved_chunks,
        key=lambda c: (len(q_terms.intersection(c["content"].lower().split())), c["relevance_score"]),
        reverse=True,
    )
    _trace(state, "reranker", "retrieved chunks", f"Reranked {len(state.reranked_chunks)} chunks", started)
    return state


def generate_answer(state: AgentState) -> AgentState:
    started = time.perf_counter()
    result = get_llm_provider().generate(state.question, state.reranked_chunks)
    state.draft_answer = result.answer
    state.total_tokens = result.total_tokens
    state.estimated_cost = result.estimated_cost
    _trace(state, "answer_generator", state.question, state.draft_answer, started)
    return state


def verify_citations(state: AgentState) -> AgentState:
    started = time.perf_counter()
    state.citations = []
    for idx, chunk in enumerate(state.reranked_chunks[:4], start=1):
        quote = chunk["content"][: settings.citation_max_chars]
        status = "verified" if quote and f"[C{idx}]" in state.draft_answer else "weak"
        state.citations.append({**chunk, "quote": quote, "verification_status": status})
    _trace(state, "citation_verifier", state.draft_answer, f"Verified {len(state.citations)} citations", started)
    return state


def critique_answer(state: AgentState) -> AgentState:
    started = time.perf_counter()
    weak = [c for c in state.citations if c["verification_status"] != "verified"]
    if not state.citations:
        state.critic_feedback = "No supporting citations were retrieved."
    elif weak:
        state.critic_feedback = "Some claims have weak citation support."
    else:
        state.critic_feedback = "Answer is grounded in retrieved citations."
    _trace(state, "critic", state.draft_answer, state.critic_feedback, started)
    return state


def score_confidence(state: AgentState) -> AgentState:
    started = time.perf_counter()
    if not state.citations:
        score = 0.15
    else:
        verified = sum(1 for c in state.citations if c["verification_status"] == "verified")
        avg_rel = sum(c["relevance_score"] for c in state.citations) / len(state.citations)
        score = min(0.95, 0.25 + 0.45 * avg_rel + 0.25 * (verified / len(state.citations)))
    state.confidence_score = round(score, 3)
    state.confidence_band = "high" if score >= 0.75 else "medium" if score >= 0.5 else "low"
    _trace(state, "confidence_scorer", state.critic_feedback, state.confidence_band, started)
    return state


def decide_human_review(state: AgentState) -> AgentState:
    started = time.perf_counter()
    state.human_review_required = state.confidence_score < 0.55 or not state.citations
    _trace(state, "human_review_decision", state.confidence_band, str(state.human_review_required), started)
    return state


def build_final_response(state: AgentState) -> AgentState:
    started = time.perf_counter()
    state.final_answer = state.draft_answer
    _trace(state, "final_response_builder", state.draft_answer, "Final response assembled", started)
    return state


def run_agent_workflow(db: Session, state: AgentState) -> AgentState:
    try:
        from langgraph.graph import END, START, StateGraph

        graph = StateGraph(dict)  # type: ignore[type-var]

        def node(fn):
            def wrapped(raw: dict) -> dict:
                next_state = fn(AgentState(**raw))
                return asdict(next_state)

            return wrapped

        graph.add_node("question_classifier", node(classify_question))
        graph.add_node("planner", node(plan_retrieval))
        graph.add_node("retriever", node(lambda s: retrieve_chunks(db, s)))
        graph.add_node("reranker", node(rerank_chunks))
        graph.add_node("answer_generator", node(generate_answer))
        graph.add_node("citation_verifier", node(verify_citations))
        graph.add_node("critic", node(critique_answer))
        graph.add_node("confidence_scorer", node(score_confidence))
        graph.add_node("human_review_decision", node(decide_human_review))
        graph.add_node("final_response_builder", node(build_final_response))
        graph.add_edge(START, "question_classifier")
        graph.add_edge("question_classifier", "planner")
        graph.add_edge("planner", "retriever")
        graph.add_edge("retriever", "reranker")
        graph.add_edge("reranker", "answer_generator")
        graph.add_edge("answer_generator", "citation_verifier")
        graph.add_edge("citation_verifier", "critic")
        graph.add_edge("critic", "confidence_scorer")
        graph.add_edge("confidence_scorer", "human_review_decision")
        graph.add_edge("human_review_decision", "final_response_builder")
        graph.add_edge("final_response_builder", END)
        result = graph.compile().invoke(asdict(state))
        return AgentState(**result)
    except Exception:
        for step in (
            classify_question,
            plan_retrieval,
            lambda s: retrieve_chunks(db, s),
            rerank_chunks,
            generate_answer,
            verify_citations,
            critique_answer,
            score_confidence,
            decide_human_review,
            build_final_response,
        ):
            state = step(state)
        return state
