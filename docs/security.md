# Security

## Authentication

Passwords are hashed with bcrypt. JWTs require an explicit secret of at least 32 characters; there is no application fallback. The web login returns the user record and sets an HttpOnly, SameSite=Strict cookie; it never exposes the token body to browser code or stores credentials in Web Storage. Non-browser clients use the separate `/auth/token` endpoint. Cookie-authenticated state changes additionally require an exact allowlisted `Origin`; CORS uses the same explicit origin list with credentials enabled. Production startup rejects an insecure cookie configuration. Demo credentials are local-only and frontend prefilling requires explicit `NEXT_PUBLIC_DEMO_MODE=true`.

## RBAC

Public registration always creates a viewer and does not accept a role field. Roles are admin, analyst, reviewer, and viewer; elevated roles are provisioned only by the trusted seed/administrative plane. FastAPI dependencies enforce route-level access. Chat session IDs are owner-checked before reuse, query traces/citations are owner-only except for admins, and retrieval only searches processed documents visible to all authenticated workspace members. Failed permission checks are audit logged where practical.

## Upload Safety

Uploads validate extension and size, sanitize filenames, prevent path traversal, store a content hash, and write to a configured local upload directory.

## Prompt Injection

Processing detects suspicious document instructions such as "ignore previous instructions" and "reveal system prompt". The system stores warnings and treats uploaded content as untrusted evidence, never as instructions.

## Rate Limiting

Login and chat routes use a simple local in-memory limiter. Redis is included in the local stack for future distributed rate limiting.

## Secrets

The repository includes `.env.example` only. Real `.env` files are ignored.

## Threat Model and Limits

Controls address self-registration privilege escalation, token theft through browser storage, weak committed signing secrets, horizontal chat-session access, path traversal, oversized/unsupported uploads, and basic prompt-injection indicators. SameSite cookies assume the frontend and API are deployed as one trusted site. This is a single-workspace build: it does not claim organization/tenant isolation, SSO, malware scanning, distributed rate limiting, key rotation/revocation, immutable audit storage, or a backup/restore system. Add those controls, HTTPS, a managed secret store, CSP, and security monitoring before internet-facing production use.
