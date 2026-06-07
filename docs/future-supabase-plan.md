# Future Supabase Plan

Supabase is intentionally not implemented in this local build.

## Migration Path

1. Create a Supabase project.
2. Enable pgvector in Supabase Postgres.
3. Apply equivalent Alembic schema or SQL migrations.
4. Move uploaded files to Supabase Storage.
5. Decide whether to keep app-owned JWT auth or migrate to Supabase Auth.
6. Re-embed documents if embedding dimensions change.
7. Update database URL and storage service implementation.

## Table Mapping

All current tables map directly to Supabase Postgres. The most sensitive migration is `users`, because Supabase Auth may own identities separately from app roles.

## Risks

- Embedding dimension mismatch.
- Storage path migration.
- RLS policy design.
- Audit log retention and privacy requirements.
- Production secret handling.

