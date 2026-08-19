import os
from pathlib import Path

from dotenv import load_dotenv
from sqlmodel import SQLModel, Session, create_engine

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./driftsagent.db")

# Import all models so SQLModel registers them before create_all
import core.models.firma  # noqa: F401
import core.models.lager  # noqa: F401
import core.models.service  # noqa: F401
import core.models.innkjop  # noqa: F401
import core.models.audit  # noqa: F401

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
)


def create_db_and_tables() -> None:
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
