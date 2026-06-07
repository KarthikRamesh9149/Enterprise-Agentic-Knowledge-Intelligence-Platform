"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-06-07
"""

from collections.abc import Sequence

import pgvector.sqlalchemy
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

from app.core.config import settings

revision: str = "0001_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    role = sa.Enum("admin", "analyst", "reviewer", "viewer", name="role")
    doc_status = sa.Enum("uploaded", "processing", "processed", "failed", name="documentstatus")
    review_status = sa.Enum("pending", "approved", "edited", "rejected", "regenerated", name="reviewstatus")
    query_status = sa.Enum("completed", "needs_review", "failed", name="querystatus")
    role.create(op.get_bind(), checkfirst=True)
    doc_status.create(op.get_bind(), checkfirst=True)
    review_status.create(op.get_bind(), checkfirst=True)
    query_status.create(op.get_bind(), checkfirst=True)

    op.create_table("users", sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("email", sa.String(255), nullable=False), sa.Column("hashed_password", sa.String(255), nullable=False), sa.Column("role", role, nullable=False), sa.Column("created_at", sa.DateTime(timezone=True)), sa.Column("updated_at", sa.DateTime(timezone=True)))
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_role", "users", ["role"])
    op.create_table("documents", sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("filename", sa.String(255), nullable=False), sa.Column("original_filename", sa.String(255), nullable=False), sa.Column("document_type", sa.String(32), nullable=False), sa.Column("source_type", sa.String(64)), sa.Column("uploaded_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id")), sa.Column("status", doc_status), sa.Column("storage_path", sa.Text(), nullable=False), sa.Column("file_size", sa.Integer(), nullable=False), sa.Column("content_hash", sa.String(128), nullable=False), sa.Column("error_message", sa.Text()), sa.Column("event_metadata", postgresql.JSONB()), sa.Column("created_at", sa.DateTime(timezone=True)), sa.Column("processed_at", sa.DateTime(timezone=True)), sa.UniqueConstraint("content_hash", "uploaded_by", name="uq_document_hash_user"))
    op.create_index("ix_documents_status", "documents", ["status"])
    op.create_index("ix_documents_uploaded_by", "documents", ["uploaded_by"])
    op.create_table("document_chunks", sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("document_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("documents.id", ondelete="CASCADE")), sa.Column("chunk_index", sa.Integer(), nullable=False), sa.Column("content", sa.Text(), nullable=False), sa.Column("page_number", sa.Integer()), sa.Column("section_title", sa.String(255)), sa.Column("embedding", pgvector.sqlalchemy.Vector(settings.embedding_dimension)), sa.Column("event_metadata", postgresql.JSONB()), sa.Column("created_at", sa.DateTime(timezone=True)))
    op.create_index("ix_document_chunks_document_id", "document_chunks", ["document_id"])
    op.create_index("ix_document_chunks_doc_idx", "document_chunks", ["document_id", "chunk_index"])
    op.execute("CREATE INDEX IF NOT EXISTS ix_document_chunks_embedding_hnsw ON document_chunks USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_document_chunks_content_fts ON document_chunks USING gin (to_tsvector('english', content))")
    op.create_table("chat_sessions", sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id")), sa.Column("title", sa.String(255)), sa.Column("created_at", sa.DateTime(timezone=True)), sa.Column("updated_at", sa.DateTime(timezone=True)))
    op.create_index("ix_chat_sessions_user_id", "chat_sessions", ["user_id"])
    op.create_table("chat_messages", sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("session_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("chat_sessions.id")), sa.Column("role", sa.String(32), nullable=False), sa.Column("content", sa.Text(), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True)))
    op.create_index("ix_chat_messages_session_id", "chat_messages", ["session_id"])
    op.create_table("rag_queries", sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id")), sa.Column("session_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("chat_sessions.id")), sa.Column("question", sa.Text(), nullable=False), sa.Column("rewritten_question", sa.Text()), sa.Column("answer", sa.Text()), sa.Column("confidence_score", sa.Float()), sa.Column("confidence_band", sa.String(32)), sa.Column("status", query_status), sa.Column("latency_ms", sa.Integer()), sa.Column("total_tokens", sa.Integer()), sa.Column("estimated_cost", sa.Float()), sa.Column("created_at", sa.DateTime(timezone=True)))
    op.create_index("ix_rag_queries_user_id", "rag_queries", ["user_id"])
    op.create_index("ix_rag_queries_session_id", "rag_queries", ["session_id"])
    op.create_table("rag_citations", sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("query_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("rag_queries.id", ondelete="CASCADE")), sa.Column("document_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("documents.id")), sa.Column("chunk_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("document_chunks.id")), sa.Column("quote", sa.Text(), nullable=False), sa.Column("page_number", sa.Integer()), sa.Column("relevance_score", sa.Float()), sa.Column("verification_status", sa.String(64)), sa.Column("created_at", sa.DateTime(timezone=True)))
    op.create_index("ix_rag_citations_query_id", "rag_citations", ["query_id"])
    op.create_table("agent_traces", sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("query_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("rag_queries.id", ondelete="CASCADE")), sa.Column("node_name", sa.String(128)), sa.Column("input_summary", sa.Text()), sa.Column("output_summary", sa.Text()), sa.Column("status", sa.String(32)), sa.Column("latency_ms", sa.Integer()), sa.Column("error_message", sa.Text()), sa.Column("created_at", sa.DateTime(timezone=True)))
    op.create_index("ix_agent_traces_query_id", "agent_traces", ["query_id"])
    op.create_index("ix_agent_traces_node_name", "agent_traces", ["node_name"])
    op.create_table("review_items", sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("query_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("rag_queries.id", ondelete="CASCADE")), sa.Column("status", review_status), sa.Column("reason", sa.Text(), nullable=False), sa.Column("original_answer", sa.Text(), nullable=False), sa.Column("reviewed_answer", sa.Text()), sa.Column("reviewer_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id")), sa.Column("reviewer_notes", sa.Text()), sa.Column("created_at", sa.DateTime(timezone=True)), sa.Column("reviewed_at", sa.DateTime(timezone=True)))
    op.create_index("ix_review_items_status", "review_items", ["status"])
    op.create_table("evaluation_runs", sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("name", sa.String(255), nullable=False), sa.Column("dataset_name", sa.String(255)), sa.Column("status", sa.String(32)), sa.Column("metrics", postgresql.JSONB()), sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id")), sa.Column("created_at", sa.DateTime(timezone=True)), sa.Column("completed_at", sa.DateTime(timezone=True)))
    op.create_table("evaluation_cases", sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("run_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("evaluation_runs.id", ondelete="CASCADE")), sa.Column("question", sa.Text(), nullable=False), sa.Column("expected_keywords", postgresql.JSONB()), sa.Column("expected_documents", postgresql.JSONB()), sa.Column("answer", sa.Text()), sa.Column("metrics", postgresql.JSONB()), sa.Column("passed", sa.Boolean()), sa.Column("created_at", sa.DateTime(timezone=True)))
    op.create_table("audit_logs", sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id")), sa.Column("action", sa.String(128)), sa.Column("resource_type", sa.String(128)), sa.Column("resource_id", sa.String(128)), sa.Column("event_metadata", postgresql.JSONB()), sa.Column("ip_address", sa.String(64)), sa.Column("user_agent", sa.Text()), sa.Column("created_at", sa.DateTime(timezone=True)))
    op.create_index("ix_audit_logs_created_at", "audit_logs", ["created_at"])
    op.create_table("system_metrics", sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("metric_name", sa.String(128)), sa.Column("metric_value", sa.Float(), nullable=False), sa.Column("dimensions", postgresql.JSONB()), sa.Column("created_at", sa.DateTime(timezone=True)))


def downgrade() -> None:
    for table in ["system_metrics", "audit_logs", "evaluation_cases", "evaluation_runs", "review_items", "agent_traces", "rag_citations", "rag_queries", "chat_messages", "chat_sessions", "document_chunks", "documents", "users"]:
        op.drop_table(table)
    for enum_name in ["querystatus", "reviewstatus", "documentstatus", "role"]:
        sa.Enum(name=enum_name).drop(op.get_bind(), checkfirst=True)
