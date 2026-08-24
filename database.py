import os
from sqlmodel import SQLModel, create_engine, Session
from dotenv import load_dotenv

load_dotenv()

# Read DATABASE_URL from env; fallback to docker-compose DB
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@db:5432/gharkaguru")

engine = create_engine(DATABASE_URL, echo=False)


def create_db_and_tables():
    """Create SQLModel tables. Safe to run multiple times."""
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session


# Optionally initialize DB on start (useful for first-time cluster deployment).
if os.getenv("INIT_DB_ON_START", "true").lower() in ("1", "true", "yes"):
    try:
        create_db_and_tables()
    except Exception:
        # In some environments DB may not be ready yet; startup script or job should retry.
        pass
