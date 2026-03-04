"""
Shared test fixtures for the ICFES Leveling backend test suite.

This conftest sets up:
- A SQLite in-memory database for fast, isolated tests
- A TestClient with dependency overrides for the DB session
- Helper functions for generating test JWT tokens
- A mock authenticated user fixture

Usage:
    All fixtures defined here are automatically available to any test file
    in this directory and subdirectories.
"""

import os
import uuid
from datetime import datetime, timedelta
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

# ---------------------------------------------------------------------------
# Environment variable overrides -- MUST be set BEFORE importing app code
# so that pydantic Settings validation does not fail.
# ---------------------------------------------------------------------------
os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")
os.environ.setdefault("JWT_SECRET", "test-secret-key-that-is-at-least-32-characters-long-for-validation")
os.environ.setdefault("SECRET_KEY", "test-secret-key-that-is-at-least-32-characters-long-for-validation")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379")
os.environ.setdefault("ENVIRONMENT", "testing")

# ---------------------------------------------------------------------------
# Database backend selection.
# Set USE_POSTGRES=1 to test against a real PostgreSQL instance.
# Otherwise, use SQLite in-memory with type monkey-patches.
# ---------------------------------------------------------------------------
USE_POSTGRES = os.environ.get("USE_POSTGRES", "0") == "1"

if not USE_POSTGRES:
    # Make PostgreSQL-specific types work with SQLite for testing.
    # Monkey-patches SQLiteTypeCompiler to handle UUID, JSONB, ARRAY, JSON types
    # that are normally PostgreSQL-only. MUST run BEFORE model imports.
    from sqlalchemy.dialects.sqlite.base import SQLiteTypeCompiler

    def _visit_UUID(self, type_, **kw):
        return "CHAR(32)"

    def _visit_JSONB(self, type_, **kw):
        return "TEXT"

    def _visit_ARRAY(self, type_, **kw):
        return "TEXT"

    def _visit_JSON(self, type_, **kw):
        return "TEXT"

    SQLiteTypeCompiler.visit_UUID = _visit_UUID
    SQLiteTypeCompiler.visit_JSONB = _visit_JSONB
    SQLiteTypeCompiler.visit_ARRAY = _visit_ARRAY
    # Only set visit_JSON if not already defined
    if not hasattr(SQLiteTypeCompiler, 'visit_JSON'):
        SQLiteTypeCompiler.visit_JSON = _visit_JSON

from app.core.database import Base, get_db  # noqa: E402
from app.core.security import create_access_token  # noqa: E402
from app.models.user import User  # noqa: E402

# ---------------------------------------------------------------------------
# Test database engine
# ---------------------------------------------------------------------------
if USE_POSTGRES:
    # Real PostgreSQL — use DATABASE_URL from environment
    _pg_url = os.environ.get("DATABASE_URL", "postgresql://gameplay:gameplay123@localhost:5433/gameplay_db")
    engine = create_engine(_pg_url)

    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
    )
else:
    # SQLite in-memory for speed and isolation
    SQLALCHEMY_TEST_URL = "sqlite://"

    engine = create_engine(
        SQLALCHEMY_TEST_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # SQLite does not support UUID natively -- enable foreign key support
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


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="function")
def db() -> Generator[Session, None, None]:
    """
    Create a fresh database for every test function.

    Tables are created before the test and dropped after to ensure
    complete isolation between tests.
    """
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


# Keep the old name as an alias so existing tests still work
@pytest.fixture(scope="function")
def db_session(db) -> Generator[Session, None, None]:
    """Alias for ``db`` -- backwards compatibility with existing tests."""
    yield db


def _reset_security_middleware(app):
    """
    Reset the in-memory state of RateLimitSecurityMiddleware so that
    rate-limit counters and blocked-IP sets don't leak between tests.

    Walks ``app.middleware_stack`` (built on first request) to find the
    RateLimitSecurityMiddleware instance and clear its dicts/sets.
    """
    start = getattr(app, "middleware_stack", app)
    current = start
    for _ in range(30):
        if hasattr(current, "request_counts"):
            current.request_counts.clear()
        if hasattr(current, "blocked_ips"):
            current.blocked_ips.clear()
        if hasattr(current, "app"):
            current = current.app
        else:
            break


@pytest.fixture()
def client(db: Session) -> Generator[TestClient, None, None]:
    """
    Provide a TestClient whose DB dependency is overridden to use the
    test database session.
    """
    from app.main import app

    def _override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db
    _reset_security_middleware(app)
    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------

def create_test_user_record(db: Session, **overrides) -> User:
    """
    Insert a test user into the database and return the ORM instance.

    Keyword arguments are merged into the default values so callers can
    customise any field (e.g. ``create_test_user_record(db, gold=5000)``).
    """
    defaults = dict(
        id=uuid.uuid4(),
        username=f"testuser_{uuid.uuid4().hex[:8]}",
        email=f"test_{uuid.uuid4().hex[:8]}@example.com",
        # bcrypt hash of "testpass123"
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
    """
    Generate a valid JWT access token for the given user id.

    The token is signed with the test JWT_SECRET configured above.
    """
    return create_access_token(
        data={"sub": str(user_id)},
        expires_delta=timedelta(hours=1),
    )


def auth_header_for(user_id: uuid.UUID) -> dict:
    """Return an Authorization header dict ready to pass to ``client.get(headers=...)``."""
    return {"Authorization": f"Bearer {make_auth_token(user_id)}"}


@pytest.fixture()
def test_user(db: Session) -> User:
    """Convenience fixture: inserts a default test user and returns it."""
    return create_test_user_record(db)


@pytest.fixture()
def create_test_user(db: Session) -> User:
    """
    Fixture used by test_auth.py, test_diagnostic.py, test_study_plans.py.
    Creates a user with predictable username='testuser' for login tests.
    """
    return create_test_user_record(
        db,
        username="testuser",
        email="testuser@example.com",
        display_name="Test User",
    )


@pytest.fixture()
def test_user_headers(test_user: User) -> dict:
    """Convenience fixture: returns auth headers for ``test_user``."""
    return auth_header_for(test_user.id)


# ---------------------------------------------------------------------------
# Model fixtures for diagnostic/study plan tests
# ---------------------------------------------------------------------------

@pytest.fixture()
def create_test_subject(db: Session):
    """Creates a test Subject in the DB."""
    from app.models.subject import Subject
    subject = Subject(
        id=uuid.uuid4(),
        name="Matematicas Test",
        description="Test math subject",
    )
    db.add(subject)
    db.commit()
    db.refresh(subject)
    return subject


@pytest.fixture()
def create_test_topic(db: Session, create_test_subject):
    """Creates a test Topic linked to the test Subject."""
    from app.models.topic import Topic
    topic = Topic(
        id=uuid.uuid4(),
        subject_id=create_test_subject.id,
        name="Algebra Basica Test",
        description="Test algebra topic",
    )
    db.add(topic)
    db.commit()
    db.refresh(topic)
    return topic


@pytest.fixture()
def create_test_question(db: Session, create_test_subject, create_test_topic):
    """Creates a test Question linked to subject and topic."""
    from app.models.question import Question
    question = Question(
        id=uuid.uuid4(),
        subject_id=create_test_subject.id,
        topic_id=create_test_topic.id,
        pregunta_texto="Cual es el resultado de 2+2?",
        opcion_a_texto="3",
        opcion_b_texto="4",
        opcion_c_texto="5",
        opcion_d_texto="6",
        respuesta_correcta="b",
        difficulty=3,
    )
    db.add(question)
    db.commit()
    db.refresh(question)
    return question


@pytest.fixture()
def create_test_diagnostic(db: Session, create_test_user, create_test_subject):
    """Creates a test DiagnosticTest record."""
    from app.models.diagnostic_two_phase import DiagnosticTest
    diagnostic = DiagnosticTest(
        id=uuid.uuid4(),
        user_id=create_test_user.id,
        subject_id=create_test_subject.id,
        status="completed",
    )
    db.add(diagnostic)
    db.commit()
    db.refresh(diagnostic)
    return diagnostic


@pytest.fixture()
def create_test_study_plan(db: Session, create_test_user, create_test_subject):
    """Creates a test StudyPlan record."""
    try:
        from app.models.study_plan import StudyPlan
        plan = StudyPlan(
            id=uuid.uuid4(),
            user_id=create_test_user.id,
            subject_id=create_test_subject.id,
            title="Plan de Prueba",
        )
        db.add(plan)
        db.commit()
        db.refresh(plan)
        return plan
    except Exception:
        # StudyPlan model may vary — return None and let test handle it
        return None


# ---------------------------------------------------------------------------
# Mock fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def mock_redis():
    """Provide a mock Redis client for tests that need it.

    The ``incr`` side keeps a per-key counter so rate-limit tests work.
    """
    from unittest.mock import Mock
    from collections import defaultdict

    store: dict = defaultdict(int)

    def _incr(key, amount=1):
        store[key] += amount
        return store[key]

    def _get(key):
        val = store.get(key)
        return str(val).encode() if val is not None else None

    mock = Mock()
    mock.get.side_effect = _get
    mock.set.return_value = True
    mock.setex.return_value = True
    mock.delete.return_value = True
    mock.incr.side_effect = _incr
    mock.incrby.side_effect = _incr
    mock.expire.return_value = True
    mock.pipeline.return_value = mock
    mock.execute.return_value = [True]
    mock.exists.return_value = False
    mock.hget.return_value = None
    mock.hset.return_value = True
    return mock
