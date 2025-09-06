"""
Test configuration and fixtures for the ICFES Leveling backend tests.
"""
import asyncio
import os
import tempfile
import pytest
from typing import Generator, AsyncGenerator
from unittest.mock import Mock, patch
import redis
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
from clickhouse_driver import Client as ClickHouseClient
import pandas as pd

# Import app components
from app.main import app
from app.core.database import Base, get_db
from app.core.config import settings
from app.models import *  # Import all models
from app.services.cache_service import CacheService


# Test Database Configuration
TEST_DATABASE_URL = "sqlite:///:memory:"

# Create test engine
test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

# Create test session
TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=test_engine
)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
def db_session() -> Generator[Session, None, None]:
    """Create a fresh database session for each test."""
    # Create all tables
    Base.metadata.create_all(bind=test_engine)
    
    # Create session
    session = TestingSessionLocal()
    
    try:
        yield session
    finally:
        session.close()
        # Drop all tables after test
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def override_get_db(db_session: Session):
    """Override the get_db dependency for testing."""
    def _override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = _override_get_db
    yield
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def client(override_get_db) -> TestClient:
    """Create a test client for the FastAPI application."""
    return TestClient(app)


@pytest.fixture(scope="function")
def mock_redis():
    """Mock Redis client for testing."""
    with patch('redis.Redis') as mock:
        redis_mock = Mock()
        mock.return_value = redis_mock
        yield redis_mock


@pytest.fixture(scope="function")
def mock_clickhouse():
    """Mock ClickHouse client for testing."""
    with patch('clickhouse_driver.Client') as mock:
        clickhouse_mock = Mock()
        mock.return_value = clickhouse_mock
        yield clickhouse_mock


@pytest.fixture(scope="function")
def cache_service(mock_redis):
    """Create a mock cache service for testing."""
    return CacheService(mock_redis)


# Test Data Fixtures
@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        "id": "test-user-123",
        "username": "testuser",
        "email": "test@example.com",
        "password_hash": "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj/5pW5h2jha",
        "display_name": "Test User",
        "rank": "D",
        "level": 1,
        "xp": 0,
        "hp": 100,
        "mp": 50,
        "power": 10,
        "wisdom": 10,
        "speed": 10,
        "resistance": 10,
        "credits": 1000,
        "gems": 10,
        "is_active": True,
        "is_premium": False
    }


@pytest.fixture
def sample_subject_data():
    """Sample subject data for testing."""
    return {
        "id": 1,
        "name": "Matemáticas",
        "code": "MAT",
        "description": "Matemáticas para ICFES",
        "difficulty_level": 3,
        "estimated_hours": 40,
        "is_active": True
    }


@pytest.fixture
def sample_topic_data():
    """Sample topic data for testing."""
    return {
        "id": 1,
        "name": "Álgebra",
        "subject_id": 1,
        "difficulty_level": 2,
        "estimated_time": 120,
        "prerequisites": [],
        "learning_objectives": ["Resolver ecuaciones lineales"],
        "is_active": True
    }


@pytest.fixture
def sample_question_data():
    """Sample question data for testing."""
    return {
        "id": 1,
        "topic_id": 1,
        "subject_id": 1,
        "question_text": "¿Cuál es el valor de x en 2x + 4 = 10?",
        "options": {
            "A": "2",
            "B": "3", 
            "C": "4",
            "D": "5"
        },
        "correct_answer": "B",
        "difficulty": 2,
        "explanation": "Despejando x: 2x = 6, por lo tanto x = 3",
        "question_type": "multiple_choice",
        "competency": "Razonamiento cuantitativo",
        "is_active": True
    }


@pytest.fixture
def sample_study_plan_data():
    """Sample study plan data for testing."""
    return {
        "id": 1,
        "user_id": "test-user-123",
        "subject_id": 1,
        "title": "Plan de Matemáticas - Nivel Básico",
        "description": "Plan personalizado para matemáticas",
        "difficulty_level": 2,
        "estimated_weeks": 8,
        "topics": [1, 2, 3],
        "is_active": True,
        "status": "active"
    }


@pytest.fixture
def sample_diagnostic_test_data():
    """Sample diagnostic test data for testing."""
    return {
        "id": 1,
        "user_id": "test-user-123",
        "subject_id": 1,
        "questions_answered": 10,
        "correct_answers": 7,
        "score_percentage": 70.0,
        "time_taken": 1800,  # 30 minutes
        "rank_assigned": "C",
        "status": "completed"
    }


@pytest.fixture
def create_test_user(db_session: Session, sample_user_data):
    """Create a test user in the database."""
    user = User(**sample_user_data)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def create_test_subject(db_session: Session, sample_subject_data):
    """Create a test subject in the database."""
    subject = Subject(**sample_subject_data)
    db_session.add(subject)
    db_session.commit()
    db_session.refresh(subject)
    return subject


@pytest.fixture
def create_test_topic(db_session: Session, sample_topic_data, create_test_subject):
    """Create a test topic in the database."""
    topic_data = sample_topic_data.copy()
    topic_data["subject_id"] = create_test_subject.id
    topic = Topic(**topic_data)
    db_session.add(topic)
    db_session.commit()
    db_session.refresh(topic)
    return topic


@pytest.fixture
def create_test_question(db_session: Session, sample_question_data, create_test_topic, create_test_subject):
    """Create a test question in the database."""
    question_data = sample_question_data.copy()
    question_data["topic_id"] = create_test_topic.id
    question_data["subject_id"] = create_test_subject.id
    question = Question(**question_data)
    db_session.add(question)
    db_session.commit()
    db_session.refresh(question)
    return question


@pytest.fixture
def create_test_study_plan(db_session: Session, sample_study_plan_data, create_test_user, create_test_subject):
    """Create a test study plan in the database."""
    plan_data = sample_study_plan_data.copy()
    plan_data["user_id"] = create_test_user.id
    plan_data["subject_id"] = create_test_subject.id
    plan = StudyPlan(**plan_data)
    db_session.add(plan)
    db_session.commit()
    db_session.refresh(plan)
    return plan


@pytest.fixture
def create_test_diagnostic(db_session: Session, sample_diagnostic_test_data, create_test_user, create_test_subject):
    """Create a test diagnostic in the database."""
    diagnostic_data = sample_diagnostic_test_data.copy()
    diagnostic_data["user_id"] = create_test_user.id
    diagnostic_data["subject_id"] = create_test_subject.id
    diagnostic = DiagnosticTest(**diagnostic_data)
    db_session.add(diagnostic)
    db_session.commit()
    db_session.refresh(diagnostic)
    return diagnostic


# Mock external services
@pytest.fixture
def mock_openai():
    """Mock OpenAI API calls."""
    with patch('openai.ChatCompletion.create') as mock:
        mock.return_value.choices[0].message.content = "Mocked AI response"
        yield mock


@pytest.fixture
def mock_youtube_api():
    """Mock YouTube API calls."""
    mock_response = {
        "items": [{
            "id": {"videoId": "test123"},
            "snippet": {
                "title": "Test Video",
                "description": "Test Description",
                "thumbnails": {"default": {"url": "http://test.com/thumb.jpg"}}
            },
            "statistics": {
                "viewCount": "1000",
                "likeCount": "100"
            }
        }]
    }
    
    with patch('googleapiclient.discovery.build') as mock:
        mock.return_value.search.return_value.list.return_value.execute.return_value = mock_response
        yield mock


@pytest.fixture
def temporary_file():
    """Create a temporary file for testing."""
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        yield tmp.name
    os.unlink(tmp.name)


@pytest.fixture
def mock_excel_data():
    """Mock Excel data for testing import functions."""
    return pd.DataFrame({
        'Pregunta': ['¿Cuánto es 2+2?', '¿Cuál es la capital de Francia?'],
        'A)': ['3', 'Londres'],
        'B)': ['4', 'París'],
        'C)': ['5', 'Madrid'],
        'D)': ['6', 'Roma'],
        'Respuesta_Correcta': ['B', 'B'],
        'Materia': ['Matemáticas', 'Sociales'],
        'Competencia': ['Razonamiento', 'Conocimiento'],
        'Componente': ['Aritmética', 'Geografía']
    })


# Authentication fixtures
@pytest.fixture
def auth_headers():
    """Create authentication headers for testing."""
    # Mock JWT token
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.test.token"
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def mock_jwt():
    """Mock JWT token validation."""
    with patch('app.core.security.decode_token') as mock:
        mock.return_value = {"sub": "test-user-123", "username": "testuser"}
        yield mock


# Database cleanup utilities
def cleanup_database(session: Session):
    """Clean up all test data from database."""
    for table in reversed(Base.metadata.sorted_tables):
        session.execute(table.delete())
    session.commit()


# Test data generators
def generate_test_questions(count: int, subject_id: int, topic_id: int) -> list:
    """Generate test questions for bulk testing."""
    questions = []
    for i in range(count):
        questions.append({
            "id": i + 1,
            "topic_id": topic_id,
            "subject_id": subject_id,
            "question_text": f"Test question {i + 1}",
            "options": {"A": "Option A", "B": "Option B", "C": "Option C", "D": "Option D"},
            "correct_answer": "A",
            "difficulty": (i % 3) + 1,
            "question_type": "multiple_choice",
            "is_active": True
        })
    return questions


def generate_test_users(count: int) -> list:
    """Generate test users for bulk testing."""
    users = []
    for i in range(count):
        users.append({
            "id": f"test-user-{i + 1}",
            "username": f"testuser{i + 1}",
            "email": f"test{i + 1}@example.com",
            "password_hash": "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj/5pW5h2jha",
            "display_name": f"Test User {i + 1}",
            "rank": ["E", "D", "C", "B", "A", "S"][i % 6],
            "level": (i % 10) + 1,
            "is_active": True
        })
    return users


# Environment setup for tests
@pytest.fixture(autouse=True)
def setup_test_environment(monkeypatch):
    """Set up test environment variables."""
    monkeypatch.setenv("TESTING", "true")
    monkeypatch.setenv("DATABASE_URL", TEST_DATABASE_URL)
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/1")
    monkeypatch.setenv("JWT_SECRET", "test-secret-key")
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")