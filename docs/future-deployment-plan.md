# Future Deployment Plan

Deployment is intentionally excluded from this build.

## Suggested Plan

- Frontend: deploy Next.js to a managed frontend platform.
- Backend: deploy FastAPI to a managed container or function platform.
- Database: Supabase or managed PostgreSQL with pgvector.
- Redis: managed Redis.
- Storage: Supabase Storage or object storage.

## Production Checklist

- Replace demo JWT secret.
- Use HTTPS-only cookies or a hardened token storage strategy.
- Configure CORS to exact origins.
- Add structured production logs and tracing.
- Add backup and restore policy.
- Add stronger distributed rate limiting.
- Add vulnerability scanning and dependency updates.
- Review all RBAC paths and audit log retention.

## Vercel Note

The Vercel CLI is not installed in this environment. Install it with `npm i -g vercel` later if you want `vercel env pull`, `vercel deploy`, and `vercel logs`.

