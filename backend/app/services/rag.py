import time

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agents.workflow import AgentState, run_agent_workflow
from app.db.models import (
    AgentTrace,
    ChatMessage,
    ChatSession,
    QueryStatus,
    RAGCitation,
    RAGQuery,
    ReviewItem,
    User,
)
from app.schemas.api import ChatQueryRequest


def answer_question(db: Session, user: User, payload: ChatQueryRequest) -> tuple[RAGQuery, list[RAGCitation], AgentState]:
    start = time.perf_counter()
    session = db.get(ChatSession, payload.session_id) if payload.session_id else None
    if not session:
        session = ChatSession(user_id=user.id, title=payload.question[:80])
        db.add(session)
        db.flush()
    db.add(ChatMessage(session_id=session.id, role="user", content=payload.question))
    state = AgentState(
        user_id=user.id,
        question=payload.question,
        session_id=session.id,
        top_k=payload.top_k,
        document_ids=payload.document_ids,
        document_type=payload.document_type,
        uploaded_by=payload.uploaded_by,
    )
    state = run_agent_workflow(db, state)
    status = QueryStatus.needs_review if state.human_review_required else QueryStatus.completed
    query = RAGQuery(
        user_id=user.id,
        session_id=session.id,
        question=payload.question,
        rewritten_question=state.rewritten_question,
        answer=state.final_answer,
        confidence_score=state.confidence_score,
        confidence_band=state.confidence_band,
        status=status,
        latency_ms=int((time.perf_counter() - start) * 1000),
        total_tokens=state.total_tokens,
        estimated_cost=state.estimated_cost,
    )
    db.add(query)
    db.flush()
    citations = []
    for citation in state.citations:
        row = RAGCitation(
            query_id=query.id,
            document_id=citation["document_id"],
            chunk_id=citation["chunk_id"],
            quote=citation["quote"],
            page_number=citation["page_number"],
            relevance_score=citation["relevance_score"],
            verification_status=citation["verification_status"],
        )
        db.add(row)
        citations.append(row)
    for trace in state.trace:
        db.add(AgentTrace(query_id=query.id, **trace))
    if state.human_review_required:
        db.add(
            ReviewItem(
                query_id=query.id,
                reason=f"Confidence {state.confidence_band}: {state.critic_feedback}",
                original_answer=state.final_answer,
            )
        )
    db.add(ChatMessage(session_id=session.id, role="assistant", content=state.final_answer))
    db.commit()
    db.refresh(query)
    for citation in citations:
        db.refresh(citation)
    return query, citations, state


def user_queries(db: Session, user: User) -> list[RAGQuery]:
    stmt = select(RAGQuery).where(RAGQuery.user_id == user.id).order_by(RAGQuery.created_at.desc())
    return list(db.scalars(stmt).all())

