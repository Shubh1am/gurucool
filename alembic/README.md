This folder contains Alembic scaffolding for database migrations.

Usage:

1. Install Alembic in your environment: `pip install alembic`
2. Set `DATABASE_URL` in your environment or `.env`.
3. Create a new migration: `alembic revision --autogenerate -m "create tables"`
4. Apply migrations: `alembic upgrade head`

The `env.py` is configured to pick up `SQLModel` metadata for autogeneration.
