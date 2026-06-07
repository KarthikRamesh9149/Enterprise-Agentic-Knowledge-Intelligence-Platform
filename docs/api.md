# API

All protected routes require `Authorization: Bearer <token>`.

## Health

- `GET /health`

## Authentication

- `POST /auth/register`
- `POST /auth/login`
- `GET /auth/me`

## Documents

- `POST /documents/upload` admin, analyst
- `GET /documents`
- `GET /documents/{document_id}`
- `DELETE /documents/{document_id}` admin or owner analyst
- `POST /documents/{document_id}/process` admin or owner analyst
- `GET /documents/{document_id}/chunks`

## Chat

- `POST /chat/query`
- `GET /chat/history`
- `GET /chat/sessions`
- `GET /chat/sessions/{session_id}`
- `GET /chat/queries/{query_id}/trace`
- `GET /chat/queries/{query_id}/citations`

## Review

- `GET /review/items` admin, reviewer
- `GET /review/items/{review_id}` admin, reviewer
- `POST /review/items/{review_id}/approve` admin, reviewer
- `POST /review/items/{review_id}/edit` admin, reviewer
- `POST /review/items/{review_id}/reject` admin, reviewer
- `POST /review/items/{review_id}/regenerate` admin, reviewer

## Evaluations

- `POST /evals/run` admin
- `GET /evals/runs` admin
- `GET /evals/runs/{run_id}` admin
- `GET /evals/summary` admin

## Admin

- `GET /admin/audit-logs` admin
- `GET /admin/analytics` admin
- `GET /admin/users` admin
- `GET /admin/system-health` admin

