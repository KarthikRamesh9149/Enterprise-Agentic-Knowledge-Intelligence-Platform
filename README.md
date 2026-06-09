# Enterprise Agentic Knowledge Intelligence Platform

Portfolio-grade local enterprise AI product for AI Engineer, GenAI Engineer, Agentic AI Builder, LLMOps Engineer, and Data Scientist roles.

The platform ingests AI research notes and company annual report excerpts, chunks and embeds them into local PostgreSQL with pgvector, answers questions with citation-grounded RAG, records product-level LangGraph-style traces, routes weak answers to human review, and exposes audit, analytics, and evaluation workflows.

## Why It Matters

This repository demonstrates practical enterprise AI engineering: auth, RBAC, document ingestion, vector search, grounded generation, confidence scoring, human oversight, observability, evaluations, Dockerized local infrastructure, and production-oriented documentation.

## Features

- FastAPI backend with JWT auth and RBAC roles: admin, analyst, reviewer, viewer.
- Next.js enterprise SaaS frontend with role-aware navigation.
- Local PostgreSQL plus pgvector and Redis through Docker Compose.
- Upload and process PDF, TXT, Markdown, and CSV files.
- Deterministic mock embedding and LLM providers for free local demos.
- Optional OpenAI-compatible embedding and chat providers through environment variables.
- Citation-grounded RAG with confidence bands, retrieved evidence, and trace steps.
- Human review queue with approve, edit, reject, and regenerate actions.
- Admin audit logs, analytics, system health, and evaluation runner.
- Demo data and JSONL evaluation cases.
- CI workflow for backend and frontend checks.

## Architecture

```mermaid
flowchart LR
  Users["Enterprise users<br/>admin, analyst, reviewer, viewer"]

  subgraph UI["Next.js workspace"]
    Shell["Role-aware app shell"]
    Views["Dashboard, documents, chat, review, evals, admin"]
    Client["Typed API client"]
  end

  subgraph API["FastAPI application"]
    Auth["JWT auth and RBAC"]
    Docs["Document ingestion"]
    Chat["Citation-grounded chat"]
    Review["Human review queue"]
    Admin["Analytics, audit, evals"]
  end

  subgraph Agent["Agent workflow"]
    Plan["Classify and plan"]
    Retrieve["Retrieve and rerank"]
    Generate["Generate with citations"]
    Verify["Verify, score, route"]
    Plan --> Retrieve --> Generate --> Verify
  end

  subgraph AI["AI providers"]
    LocalAI["Deterministic local providers"]
    OpenAI["OpenAI Responses API<br/>gpt-5-mini"]
    Embed["OpenAI embeddings<br/>text-embedding-3-small"]
  end

  subgraph Data["Data plane"]
    Postgres[("PostgreSQL 16")]
    Vector[("pgvector HNSW")]
    Redis[("Redis")]
    Uploads[("Local upload volume")]
  end

  subgraph Ops["Governance and quality"]
    Audit["Audit logs"]
    Traces["Agent traces"]
    Metrics["Confidence and latency metrics"]
    CI["GitHub Actions CI"]
  end

  Users --> Shell --> Views --> Client --> Auth
  Client --> Docs
  Client --> Chat
  Client --> Review
  Client --> Admin

  Docs --> Uploads
  Docs --> Postgres
  Docs --> Embed
  Embed --> Vector
  Chat --> Agent
  Retrieve --> Vector
  Generate --> LocalAI
  Generate --> OpenAI
  Verify --> Review

  Auth --> Redis
  Auth --> Postgres
  Chat --> Postgres
  Review --> Postgres
  Admin --> Postgres
  Auth --> Audit
  Agent --> Traces
  Chat --> Metrics
  CI --> API
  CI --> UI
```

## Local Setup

1. Copy `.env.example` to `.env` if you want custom values.
2. Run `docker compose up --build`.
3. Run migrations: `docker compose run --rm backend alembic upgrade head`.
4. Seed demo users: `docker compose run --rm backend python -m app.scripts.seed`.
5. Open `http://localhost:3000`.

Seeded local demo credentials:

- `admin@example.com` / `LocalAdmin123!`
- `analyst@example.com` / `LocalAnalyst123!`
- `reviewer@example.com` / `LocalReviewer123!`
- `viewer@example.com` / `LocalViewer123!`

## OpenAI Configuration

The app works without API keys using mock providers. To use OpenAI-compatible providers locally:

```env
EMBEDDING_PROVIDER=openai
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
OPENAI_CHAT_MODEL=gpt-5-mini
MAX_OUTPUT_TOKENS=1200
OPENAI_REASONING_EFFORT=minimal
OPENAI_TEXT_VERBOSITY=low
RAG_TOP_K=8
RAG_MAX_CONTEXT_CHARS=12000
CITATION_MAX_CHARS=360
```

Token efficiency plan:

- Use `text-embedding-3-small` for low-cost embeddings.
- Use `gpt-5-mini` as the default cost-efficient reasoning/chat model.
- Keep `top_k` at 8 or lower for normal questions.
- Cap retrieved context with `RAG_MAX_CONTEXT_CHARS`.
- Keep `MAX_OUTPUT_TOKENS` near 1200 for board-level summaries; use lower values for short Q&A demos.
- Use `OPENAI_REASONING_EFFORT=minimal` and `OPENAI_TEXT_VERBOSITY=low` for low-latency, low-token grounded answers.
- Route low-confidence answers to review instead of asking the model to over-explain.

Official OpenAI docs currently list `gpt-5-mini` as a faster, cost-efficient GPT-5 option and `text-embedding-3-small` as the low-cost embedding model. The OpenAI provider uses the Responses API for model calls. See [OpenAI models](https://platform.openai.com/docs/models), [Responses API](https://platform.openai.com/docs/api-reference/responses), and [pricing](https://platform.openai.com/docs/pricing/).

## Common Commands

```bash
make up
make migrate
make seed
make backend-test
make backend-lint
make backend-typecheck
make frontend-typecheck
make frontend-build
make verify
```

## Workflow

1. Log in as analyst.
2. Upload files from `demo-data`.
3. Process each document.
4. Ask questions in Chat.
5. Inspect answer citations, confidence, evidence, and trace.
6. Log in as reviewer/admin to process review items.
7. Run evaluations from the Evaluations page.
8. Inspect audit logs and analytics as admin.

## Documentation

- [Architecture](docs/architecture.md)
- [Database Plan](docs/database.md)
- [API](docs/api.md)
- [Security](docs/security.md)
- [Evaluation](docs/evaluation.md)
- [Local Development](docs/local-development.md)
- [Demo Script](docs/demo-script.md)
- [OpenAI Token Plan](docs/openai-token-plan.md)
