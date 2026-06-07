# Security

## Authentication

Passwords are hashed with Passlib bcrypt. JWTs use a configurable secret, algorithm, and expiration. Demo credentials are local-only and documented as non-production credentials.

## RBAC

Roles are admin, analyst, reviewer, and viewer. FastAPI dependencies enforce route-level access. Failed permission checks are audit logged where practical.

## Upload Safety

Uploads validate extension and size, sanitize filenames, prevent path traversal, store a content hash, and write to a configured local upload directory.

## Prompt Injection

Processing detects suspicious document instructions such as "ignore previous instructions" and "reveal system prompt". The system stores warnings and treats uploaded content as untrusted evidence, never as instructions.

## Rate Limiting

Login and chat routes use a simple local in-memory limiter. Redis is included in the local stack for future distributed rate limiting.

## Secrets

The repository includes `.env.example` only. Real `.env` files are ignored.

## Local-Only Limits

This build is not production hardened. Before public deployment, add HTTPS, secure cookie/session strategy, stronger rate limiting, managed secrets, backup policy, and security monitoring.

