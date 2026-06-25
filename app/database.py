"""Database configuration and session management."""

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.membership import LEGACY_PLAN_MAP, normalize_plan_months
from app.paths import get_database_path

DATABASE_URL = f"sqlite:///{get_database_path()}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """SQLAlchemy declarative base."""


def run_migrations() -> None:
    """Apply lightweight SQLite migrations for existing local databases."""
    inspector = inspect(engine)
    if "members" not in inspector.get_table_names():
        return

    columns = {column["name"] for column in inspector.get_columns("members")}

    with engine.begin() as connection:
        if "plan_months" not in columns:
            connection.execute(
                text("ALTER TABLE members ADD COLUMN plan_months INTEGER")
            )

        if "membership_plan" in columns:
            rows = connection.execute(
                text("SELECT id, membership_plan FROM members")
            ).fetchall()
            for row_id, raw_plan in rows:
                if raw_plan is None:
                    continue
                try:
                    months = normalize_plan_months(raw_plan)
                except ValueError:
                    months = LEGACY_PLAN_MAP.get(str(raw_plan), 3)
                connection.execute(
                    text(
                        "UPDATE members SET plan_months = :months WHERE id = :member_id"
                    ),
                    {"months": months, "member_id": row_id},
                )

            if connection.dialect.name == "sqlite":
                try:
                    connection.execute(
                        text("ALTER TABLE members DROP COLUMN membership_plan")
                    )
                except Exception:
                    pass


def get_db():
    """Yield a database session for request scope."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
