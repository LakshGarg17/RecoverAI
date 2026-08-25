# RecoverAI Database Layer

This directory manages database sessions, connection pooling, and Alembic schema migrations.

## Database Technologies
- **ORM**: SQLAlchemy 2.0
- **Engine**: PostgreSQL (Production/Supabase/Neon), SQLite (Local zero-config dev fallback)
- **Migrations**: Alembic

## Running Migrations

Ensure your Python virtual environment is activated, then run:

```bash
# Apply all pending migrations
alembic upgrade head

# Create a new migration revision after modifying models in backend/app/models/
alembic revision --autogenerate -m "describe_your_changes"

# Rollback last migration
alembic downgrade -1
```
