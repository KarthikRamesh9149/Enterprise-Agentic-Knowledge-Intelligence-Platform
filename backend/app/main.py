from contextlib import asynccontextmanager
from uuid import UUID

from fastapi import Depends, FastAPI, File, HTTPException, Request, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import current_user, require_roles
from app.core.config import settings
from app.core.security import create_access_token, hash_password, verify_password
from app.db.models import (
    AgentTrace,
    AuditLog,
    ChatMessage,
    ChatSession,
    Document,
    DocumentChunk,
    DocumentStatus,
    EvaluationCase,
    EvaluationRun,
    QueryStatus,
    RAGCitation,
    RAGQuery,
    ReviewItem,
    ReviewStatus,
    Role,
    SystemMetric,
    User,
    now_utc,
)
from app.db.session import Base, SessionLocal, engine, get_db
from app.schemas.api import (
    ChatQueryRequest,
    ChatQueryResponse,
    ChunkRead,
    DocumentRead,
    EvalRunRequest,
    LoginRequest,
    ReviewAction,
    ReviewRead,
    TokenResponse,
    TraceRead,
    UserCreate,
    UserRead,
)
from app.services.audit import write_audit
from app.services.documents import create_document, delete_document_file, process_document
from app.services.rag import answer_question, user_queries
from app.services.rate_limit import rate_limit


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.app_env == "test":
        Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health(db: Session = Depends(get_db)) -> dict:
    db.execute(select(1))
    return {"status": "ok", "app": settings.app_name}


@app.post("/auth/register", response_model=UserRead)
def register(payload: UserCreate, request: Request, db: Session = Depends(get_db)) -> User:
    if db.scalar(select(User).where(User.email == payload.email)):
        raise HTTPException(status_code=400, detail="Email already registered")
    role = payload.role if payload.role in {Role.viewer, Role.analyst} else Role.viewer
    user = User(email=payload.email, hashed_password=hash_password(payload.password), role=role)
    db.add(user)
    db.commit()
    db.refresh(user)
    write_audit(db, user.id, "auth.register", "user", str(user.id), {"role": user.role.value}, request)
    return user


@app.post("/auth/login", response_model=TokenResponse)
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)) -> TokenResponse:
    rate_limit(request, "login")
    user = db.scalar(select(User).where(User.email == payload.email))
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    write_audit(db, user.id, "auth.login", "user", str(user.id), {}, request)
    return TokenResponse(access_token=create_access_token(str(user.id), {"role": user.role.value}))


@app.get("/auth/me", response_model=UserRead)
def me(user: User = Depends(current_user)) -> User:
    return user


@app.post("/documents/upload", response_model=DocumentRead)
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
    user: User = Depends(require_roles(Role.admin, Role.analyst)),
    db: Session = Depends(get_db),
) -> Document:
    content = await file.read()
    document = create_document(db, file, content, user)
    write_audit(db, user.id, "document.upload", "document", str(document.id), {"filename": document.original_filename}, request)
    return document


@app.get("/documents", response_model=list[DocumentRead])
def documents(user: User = Depends(current_user), db: Session = Depends(get_db)) -> list[Document]:
    stmt = select(Document).order_by(Document.created_at.desc())
    if user.role == Role.analyst:
        stmt = stmt.where((Document.uploaded_by == user.id) | (Document.status == DocumentStatus.processed))
    elif user.role in {Role.viewer, Role.reviewer}:
        stmt = stmt.where(Document.status == DocumentStatus.processed)
    return list(db.scalars(stmt).all())


@app.get("/documents/{document_id}", response_model=DocumentRead)
def document_detail(document_id: UUID, user: User = Depends(current_user), db: Session = Depends(get_db)) -> Document:
    doc = db.get(Document, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if user.role != Role.admin and doc.status != DocumentStatus.processed and doc.uploaded_by != user.id:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    return doc


@app.delete("/documents/{document_id}")
def delete_document(
    document_id: UUID,
    request: Request,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> dict:
    doc = db.get(Document, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if user.role != Role.admin and not (user.role == Role.analyst and doc.uploaded_by == user.id):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    delete_document_file(doc)
    db.delete(doc)
    db.commit()
    write_audit(db, user.id, "document.delete", "document", str(document_id), {}, request)
    return {"status": "deleted"}


@app.post("/documents/{document_id}/process", response_model=DocumentRead)
def process_document_endpoint(
    document_id: UUID,
    request: Request,
    user: User = Depends(require_roles(Role.admin, Role.analyst)),
    db: Session = Depends(get_db),
) -> Document:
    doc = db.get(Document, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if user.role == Role.analyst and doc.uploaded_by != user.id:
        raise HTTPException(status_code=403, detail="Analysts can only process their own documents")
    processed = process_document(db, doc)
    write_audit(db, user.id, "document.process", "document", str(doc.id), {"status": processed.status.value}, request)
    return processed


@app.get("/documents/{document_id}/chunks", response_model=list[ChunkRead])
def document_chunks(document_id: UUID, user: User = Depends(current_user), db: Session = Depends(get_db)) -> list[DocumentChunk]:
    _ = document_detail(document_id, user, db)
    return list(db.scalars(select(DocumentChunk).where(DocumentChunk.document_id == document_id).order_by(DocumentChunk.chunk_index)).all())


@app.post("/chat/query", response_model=ChatQueryResponse)
def chat_query(
    payload: ChatQueryRequest,
    request: Request,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> ChatQueryResponse:
    rate_limit(request, "chat")
    query, citations, state = answer_question(db, user, payload)
    write_audit(db, user.id, "chat.query", "rag_query", str(query.id), {"confidence": query.confidence_score}, request)
    db.add(SystemMetric(metric_name="query_latency_ms", metric_value=query.latency_ms, dimensions={"status": query.status.value}))
    db.add(SystemMetric(metric_name="confidence_score", metric_value=query.confidence_score, dimensions={"band": query.confidence_band}))
    db.commit()
    return ChatQueryResponse(
        query_id=query.id,
        session_id=query.session_id,
        answer=query.answer,
        citations=citations,
        confidence_score=query.confidence_score,
        confidence_band=query.confidence_band,
        status=query.status,
        human_review_required=query.status == QueryStatus.needs_review,
        retrieved_evidence=state.reranked_chunks,
        trace=state.trace,
        latency_ms=query.latency_ms,
    )


@app.get("/chat/history")
def chat_history(user: User = Depends(current_user), db: Session = Depends(get_db)) -> list[dict]:
    return [
        {
            "id": str(q.id),
            "question": q.question,
            "answer": q.answer,
            "confidence_score": q.confidence_score,
            "confidence_band": q.confidence_band,
            "status": q.status.value,
            "created_at": q.created_at,
        }
        for q in user_queries(db, user)
    ]


@app.get("/chat/sessions")
def chat_sessions(user: User = Depends(current_user), db: Session = Depends(get_db)) -> list[dict]:
    sessions = db.scalars(select(ChatSession).where(ChatSession.user_id == user.id).order_by(ChatSession.updated_at.desc())).all()
    return [{"id": str(s.id), "title": s.title, "created_at": s.created_at, "updated_at": s.updated_at} for s in sessions]


@app.get("/chat/sessions/{session_id}")
def chat_session(session_id: UUID, user: User = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    session = db.get(ChatSession, session_id)
    if not session or session.user_id != user.id:
        raise HTTPException(status_code=404, detail="Session not found")
    messages = db.scalars(select(ChatMessage).where(ChatMessage.session_id == session_id).order_by(ChatMessage.created_at)).all()
    return {"id": str(session.id), "title": session.title, "messages": [{"role": m.role, "content": m.content, "created_at": m.created_at} for m in messages]}


@app.get("/chat/queries/{query_id}/trace", response_model=list[TraceRead])
def query_trace(query_id: UUID, user: User = Depends(current_user), db: Session = Depends(get_db)) -> list[AgentTrace]:
    query = db.get(RAGQuery, query_id)
    if not query or (query.user_id != user.id and user.role != Role.admin):
        raise HTTPException(status_code=404, detail="Query not found")
    return list(db.scalars(select(AgentTrace).where(AgentTrace.query_id == query_id).order_by(AgentTrace.created_at)).all())


@app.get("/chat/queries/{query_id}/citations")
def query_citations(query_id: UUID, user: User = Depends(current_user), db: Session = Depends(get_db)) -> list[dict]:
    query = db.get(RAGQuery, query_id)
    if not query or (query.user_id != user.id and user.role != Role.admin):
        raise HTTPException(status_code=404, detail="Query not found")
    rows = db.scalars(select(RAGCitation).where(RAGCitation.query_id == query_id)).all()
    return [{"id": str(c.id), "quote": c.quote, "verification_status": c.verification_status, "relevance_score": c.relevance_score} for c in rows]


@app.get("/review/items", response_model=list[ReviewRead])
def review_items(user: User = Depends(require_roles(Role.admin, Role.reviewer)), db: Session = Depends(get_db)) -> list[ReviewItem]:
    return list(db.scalars(select(ReviewItem).order_by(ReviewItem.created_at.desc())).all())


@app.get("/review/items/{review_id}", response_model=ReviewRead)
def review_item(review_id: UUID, user: User = Depends(require_roles(Role.admin, Role.reviewer)), db: Session = Depends(get_db)) -> ReviewItem:
    item = db.get(ReviewItem, review_id)
    if not item:
        raise HTTPException(status_code=404, detail="Review item not found")
    return item


def _review_action(review_id: UUID, status_: ReviewStatus, payload: ReviewAction, request: Request, user: User, db: Session) -> ReviewItem:
    item = review_item(review_id, user, db)
    item.status = status_
    item.reviewed_answer = payload.reviewed_answer
    item.reviewer_notes = payload.reviewer_notes
    item.reviewer_id = user.id
    item.reviewed_at = now_utc()
    db.commit()
    db.refresh(item)
    write_audit(db, user.id, f"review.{status_.value}", "review_item", str(item.id), {}, request)
    return item


@app.post("/review/items/{review_id}/approve", response_model=ReviewRead)
def approve(review_id: UUID, payload: ReviewAction, request: Request, user: User = Depends(require_roles(Role.admin, Role.reviewer)), db: Session = Depends(get_db)) -> ReviewItem:
    return _review_action(review_id, ReviewStatus.approved, payload, request, user, db)


@app.post("/review/items/{review_id}/edit", response_model=ReviewRead)
def edit(review_id: UUID, payload: ReviewAction, request: Request, user: User = Depends(require_roles(Role.admin, Role.reviewer)), db: Session = Depends(get_db)) -> ReviewItem:
    return _review_action(review_id, ReviewStatus.edited, payload, request, user, db)


@app.post("/review/items/{review_id}/reject", response_model=ReviewRead)
def reject(review_id: UUID, payload: ReviewAction, request: Request, user: User = Depends(require_roles(Role.admin, Role.reviewer)), db: Session = Depends(get_db)) -> ReviewItem:
    return _review_action(review_id, ReviewStatus.rejected, payload, request, user, db)


@app.post("/review/items/{review_id}/regenerate", response_model=ReviewRead)
def regenerate(review_id: UUID, payload: ReviewAction, request: Request, user: User = Depends(require_roles(Role.admin, Role.reviewer)), db: Session = Depends(get_db)) -> ReviewItem:
    return _review_action(review_id, ReviewStatus.regenerated, payload, request, user, db)


@app.post("/evals/run")
def run_evals(payload: EvalRunRequest, request: Request, user: User = Depends(require_roles(Role.admin)), db: Session = Depends(get_db)) -> dict:
    cases = [
        {"question": "Summarize AI infrastructure risks.", "expected_keywords": ["risk", "infrastructure", "ai"]},
        {"question": "What does the research say about RAG limitations?", "expected_keywords": ["rag", "limitations", "retrieval"]},
    ]
    run = EvaluationRun(name=payload.name, dataset_name=payload.dataset_name, status="running", created_by=user.id)
    db.add(run)
    db.flush()
    passed = 0
    for case in cases:
        q, citations, _state = answer_question(db, user, ChatQueryRequest(question=case["question"]))
        keywords = case["expected_keywords"]
        coverage = sum(1 for k in keywords if k in q.answer.lower()) / len(keywords)
        ok = coverage >= 0.34 and len(citations) >= 1
        passed += int(ok)
        db.add(EvaluationCase(run_id=run.id, question=case["question"], expected_keywords=keywords, answer=q.answer, metrics={"keyword_coverage": coverage, "citation_count": len(citations)}, passed=ok))
    run.status = "completed"
    run.completed_at = now_utc()
    run.metrics = {"cases": len(cases), "passed": passed, "pass_rate": passed / len(cases)}
    db.commit()
    write_audit(db, user.id, "eval.run", "evaluation_run", str(run.id), run.metrics, request)
    return {"id": str(run.id), "metrics": run.metrics, "status": run.status}


@app.get("/evals/runs")
def eval_runs(user: User = Depends(require_roles(Role.admin)), db: Session = Depends(get_db)) -> list[dict]:
    rows = db.scalars(select(EvaluationRun).order_by(EvaluationRun.created_at.desc())).all()
    return [{"id": str(r.id), "name": r.name, "dataset_name": r.dataset_name, "status": r.status, "metrics": r.metrics, "created_at": r.created_at} for r in rows]


@app.get("/evals/runs/{run_id}")
def eval_run(run_id: UUID, user: User = Depends(require_roles(Role.admin)), db: Session = Depends(get_db)) -> dict:
    run = db.get(EvaluationRun, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Eval run not found")
    cases = db.scalars(select(EvaluationCase).where(EvaluationCase.run_id == run.id)).all()
    return {"id": str(run.id), "metrics": run.metrics, "cases": [{"question": c.question, "passed": c.passed, "metrics": c.metrics, "answer": c.answer} for c in cases]}


@app.get("/evals/summary")
def eval_summary(user: User = Depends(require_roles(Role.admin)), db: Session = Depends(get_db)) -> dict:
    runs = db.scalars(select(EvaluationRun)).all()
    return {"total_runs": len(runs), "latest": runs[-1].metrics if runs else {}}


@app.get("/admin/audit-logs")
def audit_logs(request: Request, user: User = Depends(require_roles(Role.admin)), db: Session = Depends(get_db)) -> list[dict]:
    write_audit(db, user.id, "admin.audit_logs_access", "audit_log", None, {}, request)
    rows = db.scalars(select(AuditLog).order_by(AuditLog.created_at.desc()).limit(200)).all()
    return [{"id": str(r.id), "user_id": str(r.user_id) if r.user_id else None, "action": r.action, "resource_type": r.resource_type, "resource_id": r.resource_id, "event_metadata": r.event_metadata, "created_at": r.created_at} for r in rows]


@app.get("/admin/analytics")
def analytics(user: User = Depends(require_roles(Role.admin)), db: Session = Depends(get_db)) -> dict:
    doc_total = db.scalar(select(func.count(Document.id))) or 0
    processed = db.scalar(select(func.count(Document.id)).where(Document.status == DocumentStatus.processed)) or 0
    failed = db.scalar(select(func.count(Document.id)).where(Document.status == DocumentStatus.failed)) or 0
    query_total = db.scalar(select(func.count(RAGQuery.id))) or 0
    avg_conf = db.scalar(select(func.avg(RAGQuery.confidence_score))) or 0
    avg_latency = db.scalar(select(func.avg(RAGQuery.latency_ms))) or 0
    review_total = db.scalar(select(func.count(ReviewItem.id))) or 0
    citation_total = db.scalar(select(func.count(RAGCitation.id))) or 0
    return {
        "total_users": db.scalar(select(func.count(User.id))) or 0,
        "total_documents": doc_total,
        "processed_documents": processed,
        "failed_documents": failed,
        "total_queries": query_total,
        "average_confidence": round(float(avg_conf), 3),
        "average_latency_ms": round(float(avg_latency), 1),
        "citation_pass_rate": 1.0 if citation_total else 0,
        "human_review_rate": round(review_total / query_total, 3) if query_total else 0,
        "recent_failures": [],
        "most_queried_documents": [],
    }


@app.get("/admin/users", response_model=list[UserRead])
def admin_users(user: User = Depends(require_roles(Role.admin)), db: Session = Depends(get_db)) -> list[User]:
    return list(db.scalars(select(User).order_by(User.created_at.desc())).all())


@app.get("/admin/system-health")
def system_health(user: User = Depends(require_roles(Role.admin)), db: Session = Depends(get_db)) -> dict:
    db.execute(select(1))
    return {"database": "ok", "redis": "optional-local", "mock_providers": settings.embedding_provider == "mock" and settings.llm_provider == "mock"}

