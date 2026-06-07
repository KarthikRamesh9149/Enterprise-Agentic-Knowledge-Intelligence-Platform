from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.db.models import DocumentStatus, QueryStatus, ReviewStatus, Role


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    role: Role = Role.viewer


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserRead(BaseModel):
    id: UUID
    email: str
    role: Role
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class DocumentRead(BaseModel):
    id: UUID
    filename: str
    original_filename: str
    document_type: str
    source_type: str
    uploaded_by: UUID
    status: DocumentStatus
    file_size: int
    content_hash: str
    error_message: str | None
    event_metadata: dict[str, Any]
    created_at: datetime
    processed_at: datetime | None
    model_config = ConfigDict(from_attributes=True)


class ChunkRead(BaseModel):
    id: UUID
    document_id: UUID
    chunk_index: int
    content: str
    page_number: int | None
    section_title: str | None
    event_metadata: dict[str, Any]
    model_config = ConfigDict(from_attributes=True)


class ChatQueryRequest(BaseModel):
    question: str = Field(min_length=3, max_length=4000)
    session_id: UUID | None = None
    top_k: int = Field(default=8, ge=1, le=20)
    document_ids: list[UUID] | None = None
    document_type: str | None = None
    uploaded_by: UUID | None = None


class CitationRead(BaseModel):
    id: UUID
    document_id: UUID
    chunk_id: UUID
    quote: str
    page_number: int | None
    relevance_score: float
    verification_status: str
    model_config = ConfigDict(from_attributes=True)


class TraceRead(BaseModel):
    id: UUID
    node_name: str
    input_summary: str
    output_summary: str
    status: str
    latency_ms: int
    error_message: str | None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class ChatQueryResponse(BaseModel):
    query_id: UUID
    session_id: UUID
    answer: str
    citations: list[CitationRead]
    confidence_score: float
    confidence_band: str
    status: QueryStatus
    human_review_required: bool
    retrieved_evidence: list[dict[str, Any]]
    trace: list[dict[str, Any]]
    latency_ms: int


class ReviewAction(BaseModel):
    reviewed_answer: str | None = None
    reviewer_notes: str | None = None


class ReviewRead(BaseModel):
    id: UUID
    query_id: UUID
    status: ReviewStatus
    reason: str
    original_answer: str
    reviewed_answer: str | None
    reviewer_id: UUID | None
    reviewer_notes: str | None
    created_at: datetime
    reviewed_at: datetime | None
    model_config = ConfigDict(from_attributes=True)


class EvalRunRequest(BaseModel):
    dataset_name: str = "annual_report_questions"
    name: str = "Local mock evaluation"
