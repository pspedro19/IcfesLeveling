# .claude/tests/conftest.py
# ═══════════════════════════════════════════════════════════════
# Fixtures compartidos para la suite de tests del backend
# SINCRONICO — Coincide con la arquitectura real del backend
# ═══════════════════════════════════════════════════════════════

import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

# ─── Environment overrides (ANTES de importar app) ────────────
os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")
os.environ.setdefault("JWT_SECRET", "test-secret-key-that-is-at-least-32-characters-long-for-validation")
os.environ.setdefault("SECRET_KEY", "test-secret-key-that-is-at-least-32-characters-long-for-validation")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379")
os.environ.setdefault("ENVIRONMENT", "testing")

from app.core.database import Base, get_db  # noqa: E402
from app.core.security import create_access_token  # noqa: E402
from app.models.user import User  # noqa: E402


# ─── Database Testing ────────────────────────────────────────

SQLALCHEMY_TEST_URL = "sqlite://"

engine = create_engine(
    SQLALCHEMY_TEST_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


@event.listens_for(engine, "connect")
def _set_sqlite_pragma(dbapi_conn, connection_record):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


# ─── Fixtures ────────────────────────────────────────────────

@pytest.fixture(scope="function")
def db() -> Generator[Session, None, None]:
    """DB aislada por test con create/drop automatico."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session(db) -> Generator[Session, None, None]:
    """Alias para compatibilidad."""
    yield db


@pytest.fixture()
def client(db: Session) -> Generator[TestClient, None, None]:
    """TestClient con DB override."""
    from app.main import app

    def _override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app, raise_server_exceptions=False) as tc:
        yield tc
    app.dependency_overrides.clear()


# ─── Auth helpers ─────────────────────────────────────────────

def create_test_user(db: Session, **overrides) -> User:
    """Crea un usuario de test en la BD."""
    defaults = dict(
        id=uuid.uuid4(),
        username=f"testuser_{uuid.uuid4().hex[:8]}",
        email=f"test_{uuid.uuid4().hex[:8]}@example.com",
        hashed_password="$2b$12$LJ3m4ys7Jg0tZnTVOQB8JeE4xJGkQOZy3Kl0VHfWZ5cNzN8rX5Pu",
        display_name="Test User",
        level=5,
        experience=500,
        rank="D",
        hp=100,
        mp=50,
        power=15,
        wisdom=12,
        speed=10,
        gold=1000,
        orbs=500,
        crystals=50,
        hearts=5,
        max_hearts=5,
        current_streak=3,
        longest_streak=10,
        previous_streak=0,
        daily_goal_xp=20,
        is_active=True,
        streak_freeze_count=1,
    )
    defaults.update(overrides)
    user = User(**defaults)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def make_auth_token(user_id: uuid.UUID) -> str:
    """Genera JWT de test."""
    return create_access_token(
        data={"sub": str(user_id)},
        expires_delta=timedelta(hours=1),
    )


def auth_header_for(user_id: uuid.UUID) -> dict:
    """Header Authorization para requests."""
    return {"Authorization": f"Bearer {make_auth_token(user_id)}"}


@pytest.fixture()
def sample_user(db: Session) -> User:
    """Usuario estandar para tests."""
    return create_test_user(db)


@pytest.fixture()
def premium_user(db: Session) -> User:
    """Usuario premium con corazones ilimitados."""
    return create_test_user(
        db,
        premium_plan="premium",
        unlimited_hearts_until=datetime.now(timezone.utc) + timedelta(days=30),
    )


@pytest.fixture()
def veteran_user(db: Session) -> User:
    """Usuario veterano nivel 50."""
    return create_test_user(
        db,
        level=50,
        experience=240100,
        rank="B",
        current_streak=30,
        longest_streak=45,
        gold=50000,
        onboarding_completed=True,
    )


@pytest.fixture()
def depleted_user(db: Session) -> User:
    """Usuario sin corazones (grace mode)."""
    return create_test_user(
        db,
        hearts=0,
        onboarding_completed=True,
    )


@pytest.fixture()
def auth_headers(sample_user) -> dict:
    """Headers de autenticacion para sample_user."""
    return auth_header_for(sample_user.id)
