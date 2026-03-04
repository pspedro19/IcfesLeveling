"""
Two-Phase Diagnostic system tests for the ICFES Leveling backend.

Tests cover the endpoints defined in app.routes.diagnostic_two_phase:
- POST /api/v1/diagnostic/quick/start
- POST /api/v1/diagnostic/quick/submit
- POST /api/v1/diagnostic/deep/start/{subject_id}
- POST /api/v1/diagnostic/deep/submit
"""
import uuid
from unittest.mock import patch, MagicMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.subject import Subject
from app.models.topic import Topic
from app.models.question import Question
from app.models.diagnostic_two_phase import TwoPhaseDignostic, TwoPhaseDiagnosticAnswer

# Import conftest helpers (they are available at module level)
from tests.conftest import auth_header_for, create_test_user_record


# ---------------------------------------------------------------------------
# Helpers for creating test data
# ---------------------------------------------------------------------------

def _create_subjects(db: Session, count: int = 5):
    """Create test subjects and return them."""
    subjects = []
    for i in range(count):
        subj = Subject(
            id=uuid.uuid4(),
            name=f"Subject {i + 1}",
            description=f"Test subject {i + 1}",
        )
        db.add(subj)
        subjects.append(subj)
    db.commit()
    for s in subjects:
        db.refresh(s)
    return subjects


def _create_topic_for_subject(db: Session, subject: Subject):
    """Create a single test topic linked to a subject."""
    topic = Topic(
        id=uuid.uuid4(),
        subject_id=subject.id,
        name=f"Topic for {subject.name}",
        description="Test topic",
    )
    db.add(topic)
    db.commit()
    db.refresh(topic)
    return topic


def _create_questions_for_subject(
    db: Session,
    subject: Subject,
    topic: Topic,
    count: int = 5,
    difficulty: int = 3,
):
    """Create questions linked to subject and topic."""
    questions = []
    for i in range(count):
        q = Question(
            id=uuid.uuid4(),
            subject_id=subject.id,
            topic_id=topic.id,
            pregunta_texto=f"Question {i + 1} for {subject.name}?",
            opcion_a_texto=f"Option A {i + 1}",
            opcion_b_texto=f"Option B {i + 1}",
            opcion_c_texto=f"Option C {i + 1}",
            opcion_d_texto=f"Option D {i + 1}",
            respuesta_correcta="b",
            difficulty=difficulty,
        )
        db.add(q)
        questions.append(q)
    db.commit()
    for q in questions:
        db.refresh(q)
    return questions


# ---------------------------------------------------------------------------
# Quick Diagnostic Endpoint Tests
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestQuickDiagnosticEndpoints:
    """Test quick diagnostic endpoints (POST /api/v1/diagnostic/quick/...)."""

    def test_start_quick_diagnostic_requires_auth(self, client: TestClient):
        """POST /diagnostic/quick/start without token returns 401."""
        response = client.post("/api/v1/diagnostic/quick/start")
        assert response.status_code == 401

    def test_start_quick_diagnostic_success(
        self, client: TestClient, db: Session, create_test_user
    ):
        """POST /diagnostic/quick/start with auth and sufficient subjects returns 200."""
        # The service requires at least 5 subjects
        subjects = _create_subjects(db, count=5)
        # Create at least 3 questions per subject so the service can find them
        for subj in subjects:
            topic = _create_topic_for_subject(db, subj)
            _create_questions_for_subject(db, subj, topic, count=3, difficulty=3)

        headers = auth_header_for(create_test_user.id)
        response = client.post("/api/v1/diagnostic/quick/start", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "diagnostic_id" in data
        assert "questions" in data
        assert "total" in data
        assert "time_limit_minutes" in data

    def test_start_quick_diagnostic_insufficient_subjects(
        self, client: TestClient, db: Session, create_test_user
    ):
        """POST /diagnostic/quick/start with fewer than 5 subjects returns 500."""
        # Only 2 subjects -- service raises RuntimeError
        _create_subjects(db, count=2)
        headers = auth_header_for(create_test_user.id)
        response = client.post("/api/v1/diagnostic/quick/start", headers=headers)
        assert response.status_code == 500

    def test_start_quick_diagnostic_already_completed(
        self, client: TestClient, db: Session, create_test_user
    ):
        """POST /diagnostic/quick/start when already completed returns 400."""
        # Insert a completed quick diagnostic directly
        diag = TwoPhaseDignostic(
            user_id=create_test_user.id,
            diagnostic_type="quick",
            status="completed",
        )
        db.add(diag)
        db.commit()

        # Need 5 subjects so the endpoint doesn't fail earlier
        _create_subjects(db, count=5)

        headers = auth_header_for(create_test_user.id)
        response = client.post("/api/v1/diagnostic/quick/start", headers=headers)
        assert response.status_code == 400

    def test_submit_quick_diagnostic_requires_auth(self, client: TestClient):
        """POST /diagnostic/quick/submit without token returns 401."""
        body = {
            "diagnostic_id": str(uuid.uuid4()),
            "answers": [],
        }
        response = client.post("/api/v1/diagnostic/quick/submit", json=body)
        assert response.status_code == 401

    def test_submit_quick_diagnostic_not_found(
        self, client: TestClient, create_test_user
    ):
        """POST /diagnostic/quick/submit with non-existent diagnostic_id returns 404."""
        headers = auth_header_for(create_test_user.id)
        body = {
            "diagnostic_id": str(uuid.uuid4()),
            "answers": [
                {
                    "question_id": str(uuid.uuid4()),
                    "answer_id": "A",
                    "time_spent_seconds": 10,
                }
            ],
        }
        response = client.post(
            "/api/v1/diagnostic/quick/submit", json=body, headers=headers
        )
        assert response.status_code == 404

    def test_submit_quick_diagnostic_success(
        self, client: TestClient, db: Session, create_test_user
    ):
        """Full quick-diagnostic flow: start then submit."""
        # Setup: 5 subjects, each with 3 questions
        subjects = _create_subjects(db, count=5)
        all_questions = []
        for subj in subjects:
            topic = _create_topic_for_subject(db, subj)
            qs = _create_questions_for_subject(db, subj, topic, count=3, difficulty=3)
            all_questions.extend(qs)

        headers = auth_header_for(create_test_user.id)

        # Step 1: Start
        start_resp = client.post(
            "/api/v1/diagnostic/quick/start", headers=headers
        )
        assert start_resp.status_code == 200
        start_data = start_resp.json()
        diagnostic_id = start_data["diagnostic_id"]
        returned_questions = start_data["questions"]
        assert len(returned_questions) > 0

        # Step 2: Submit answers for every returned question
        answers = []
        for q in returned_questions:
            answers.append(
                {
                    "question_id": q["id"],
                    "answer_id": "B",  # correct answer is "b"
                    "time_spent_seconds": 20,
                }
            )

        submit_body = {
            "diagnostic_id": diagnostic_id,
            "answers": answers,
        }
        submit_resp = client.post(
            "/api/v1/diagnostic/quick/submit", json=submit_body, headers=headers
        )
        assert submit_resp.status_code == 200
        submit_data = submit_resp.json()
        assert submit_data["completed"] is True
        assert "correct" in submit_data
        assert "total" in submit_data
        assert "rank" in submit_data
        assert "theta" in submit_data
        assert "weak_areas" in submit_data

    def test_submit_quick_diagnostic_already_completed(
        self, client: TestClient, db: Session, create_test_user
    ):
        """Submitting a quick diagnostic that is already completed returns 400."""
        diag = TwoPhaseDignostic(
            user_id=create_test_user.id,
            diagnostic_type="quick",
            status="completed",
        )
        db.add(diag)
        db.commit()
        db.refresh(diag)

        headers = auth_header_for(create_test_user.id)
        body = {
            "diagnostic_id": str(diag.id),
            "answers": [
                {
                    "question_id": str(uuid.uuid4()),
                    "answer_id": "A",
                    "time_spent_seconds": 10,
                }
            ],
        }
        response = client.post(
            "/api/v1/diagnostic/quick/submit", json=body, headers=headers
        )
        assert response.status_code == 400


# ---------------------------------------------------------------------------
# Deep Diagnostic Endpoint Tests
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestDeepDiagnosticEndpoints:
    """Test deep diagnostic endpoints (POST /api/v1/diagnostic/deep/...)."""

    def test_start_deep_diagnostic_requires_auth(self, client: TestClient):
        """POST /diagnostic/deep/start/{subject_id} without token returns 401."""
        response = client.post(
            f"/api/v1/diagnostic/deep/start/{uuid.uuid4()}"
        )
        assert response.status_code == 401

    def test_start_deep_diagnostic_subject_not_found(
        self, client: TestClient, create_test_user
    ):
        """POST /diagnostic/deep/start with non-existent subject returns 404."""
        headers = auth_header_for(create_test_user.id)
        response = client.post(
            f"/api/v1/diagnostic/deep/start/{uuid.uuid4()}", headers=headers
        )
        assert response.status_code == 404

    def test_start_deep_diagnostic_success(
        self,
        client: TestClient,
        db: Session,
        create_test_user,
        create_test_subject,
        create_test_topic,
    ):
        """POST /diagnostic/deep/start with valid subject returns 200."""
        # DeepDiagnosticStartResponse requires total >= 15, service limits to 20
        _create_questions_for_subject(
            db, create_test_subject, create_test_topic, count=20, difficulty=3
        )

        headers = auth_header_for(create_test_user.id)
        response = client.post(
            f"/api/v1/diagnostic/deep/start/{create_test_subject.id}",
            headers=headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "diagnostic_id" in data
        assert "subject_id" in data
        assert "subject_name" in data
        assert "questions" in data
        assert "total" in data
        assert data["total"] >= 15

    def test_start_deep_diagnostic_already_completed(
        self,
        client: TestClient,
        db: Session,
        create_test_user,
        create_test_subject,
    ):
        """POST /diagnostic/deep/start when already completed for that subject returns 400."""
        diag = TwoPhaseDignostic(
            user_id=create_test_user.id,
            diagnostic_type="deep",
            subject_id=create_test_subject.id,
            status="completed",
        )
        db.add(diag)
        db.commit()

        headers = auth_header_for(create_test_user.id)
        response = client.post(
            f"/api/v1/diagnostic/deep/start/{create_test_subject.id}",
            headers=headers,
        )
        assert response.status_code == 400

    def test_submit_deep_diagnostic_requires_auth(self, client: TestClient):
        """POST /diagnostic/deep/submit without token returns 401."""
        body = {
            "diagnostic_id": str(uuid.uuid4()),
            "answers": [],
        }
        response = client.post("/api/v1/diagnostic/deep/submit", json=body)
        assert response.status_code == 401

    def test_submit_deep_diagnostic_not_found(
        self, client: TestClient, create_test_user
    ):
        """POST /diagnostic/deep/submit with unknown diagnostic_id returns 404."""
        headers = auth_header_for(create_test_user.id)
        body = {
            "diagnostic_id": str(uuid.uuid4()),
            "answers": [
                {
                    "question_id": str(uuid.uuid4()),
                    "answer_id": "A",
                    "time_spent_seconds": 10,
                }
            ],
        }
        response = client.post(
            "/api/v1/diagnostic/deep/submit", json=body, headers=headers
        )
        assert response.status_code == 404

    def test_submit_deep_diagnostic_success(
        self,
        client: TestClient,
        db: Session,
        create_test_user,
        create_test_subject,
        create_test_topic,
    ):
        """Full deep-diagnostic flow: start then submit.

        Note: The service stores a SkillTreeItem.model_dump() into a JSONB column.
        In the SQLite test environment JSONB is mapped to TEXT, and the default
        model_dump() produces uuid.UUID objects that Python's json module cannot
        serialise.  We patch model_dump to use mode='json' so UUIDs become
        strings, matching what PostgreSQL's native JSONB driver does in
        production.
        """
        _create_questions_for_subject(
            db, create_test_subject, create_test_topic, count=20, difficulty=3
        )

        headers = auth_header_for(create_test_user.id)

        # Step 1: Start deep diagnostic
        start_resp = client.post(
            f"/api/v1/diagnostic/deep/start/{create_test_subject.id}",
            headers=headers,
        )
        assert start_resp.status_code == 200
        start_data = start_resp.json()
        diagnostic_id = start_data["diagnostic_id"]
        returned_questions = start_data["questions"]

        # Step 2: Submit answers
        answers = []
        for q in returned_questions:
            answers.append(
                {
                    "question_id": q["id"],
                    "answer_id": "B",  # correct answer is "b"
                    "time_spent_seconds": 15,
                }
            )

        submit_body = {
            "diagnostic_id": diagnostic_id,
            "answers": answers,
        }

        # Patch SkillTreeItem.model_dump to produce JSON-safe output (SQLite compat)
        from app.schemas.diagnostic import SkillTreeItem
        _original_model_dump = SkillTreeItem.model_dump

        def _json_safe_dump(self, **kwargs):
            kwargs["mode"] = "json"
            return _original_model_dump(self, **kwargs)

        with patch.object(SkillTreeItem, "model_dump", _json_safe_dump):
            submit_resp = client.post(
                "/api/v1/diagnostic/deep/submit", json=submit_body, headers=headers
            )

        assert submit_resp.status_code == 200
        submit_data = submit_resp.json()
        assert submit_data["completed"] is True
        assert "correct" in submit_data
        assert "total" in submit_data
        assert "skill_tree" in submit_data
        assert "subject_id" in submit_data


# ---------------------------------------------------------------------------
# Service-level unit tests
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestDiagnosticTwoPhaseService:
    """Unit tests for DiagnosticTwoPhaseService."""

    def test_start_quick_diagnostic_creates_record(
        self, db: Session, create_test_user
    ):
        """start_quick_diagnostic creates a TwoPhaseDignostic with status in_progress."""
        from app.services.diagnostic_two_phase_service import DiagnosticTwoPhaseService

        # Need at least 5 subjects
        subjects = _create_subjects(db, count=5)

        service = DiagnosticTwoPhaseService(db)
        diag = service.start_quick_diagnostic(create_test_user.id)

        assert diag is not None
        assert diag.diagnostic_type == "quick"
        assert diag.status == "in_progress"
        assert diag.user_id == create_test_user.id

    def test_start_quick_diagnostic_returns_existing_in_progress(
        self, db: Session, create_test_user
    ):
        """If an in-progress quick diagnostic exists, it is returned instead of creating a new one."""
        from app.services.diagnostic_two_phase_service import DiagnosticTwoPhaseService

        _create_subjects(db, count=5)
        service = DiagnosticTwoPhaseService(db)

        diag1 = service.start_quick_diagnostic(create_test_user.id)
        diag2 = service.start_quick_diagnostic(create_test_user.id)

        assert diag1.id == diag2.id

    def test_start_quick_diagnostic_raises_if_completed(
        self, db: Session, create_test_user
    ):
        """start_quick_diagnostic raises ValueError if already completed."""
        from app.services.diagnostic_two_phase_service import DiagnosticTwoPhaseService

        _create_subjects(db, count=5)

        existing = TwoPhaseDignostic(
            user_id=create_test_user.id,
            diagnostic_type="quick",
            status="completed",
        )
        db.add(existing)
        db.commit()

        service = DiagnosticTwoPhaseService(db)
        with pytest.raises(ValueError, match="DIAGNOSTIC_COMPLETED"):
            service.start_quick_diagnostic(create_test_user.id)

    def test_submit_quick_diagnostic_not_found(
        self, db: Session, create_test_user
    ):
        """submit_quick_diagnostic raises ValueError for non-existent diagnostic."""
        from app.services.diagnostic_two_phase_service import DiagnosticTwoPhaseService

        service = DiagnosticTwoPhaseService(db)
        with pytest.raises(ValueError, match="DIAGNOSTIC_NOT_FOUND"):
            service.submit_quick_diagnostic(
                create_test_user.id, uuid.uuid4(), []
            )

    def test_start_deep_diagnostic_subject_not_found(
        self, db: Session, create_test_user
    ):
        """start_deep_diagnostic raises ValueError for non-existent subject."""
        from app.services.diagnostic_two_phase_service import DiagnosticTwoPhaseService

        service = DiagnosticTwoPhaseService(db)
        with pytest.raises(ValueError, match="SUBJECT_NOT_FOUND"):
            service.start_deep_diagnostic(create_test_user.id, uuid.uuid4())

    def test_start_deep_diagnostic_creates_record(
        self, db: Session, create_test_user, create_test_subject
    ):
        """start_deep_diagnostic creates a deep diagnostic linked to the subject."""
        from app.services.diagnostic_two_phase_service import DiagnosticTwoPhaseService

        service = DiagnosticTwoPhaseService(db)
        diag = service.start_deep_diagnostic(
            create_test_user.id, create_test_subject.id
        )

        assert diag is not None
        assert diag.diagnostic_type == "deep"
        assert diag.status == "in_progress"
        assert diag.subject_id == create_test_subject.id

    def test_deep_diagnostic_submit_service(
        self, db: Session, create_test_user, create_test_subject, create_test_topic
    ):
        """Test the deep diagnostic submit at service level.

        Patches SkillTreeItem.model_dump to produce JSON-safe output because
        SQLite TEXT columns cannot serialise uuid.UUID objects (production
        PostgreSQL JSONB handles this natively).
        """
        from app.services.diagnostic_two_phase_service import DiagnosticTwoPhaseService
        from app.schemas.diagnostic import DiagnosticAnswerInput, SkillTreeItem

        # Create enough questions
        _create_questions_for_subject(
            db, create_test_subject, create_test_topic, count=20, difficulty=3
        )
        service = DiagnosticTwoPhaseService(db)

        # Start deep diagnostic
        diag = service.start_deep_diagnostic(create_test_user.id, create_test_subject.id)
        questions = service.get_deep_diagnostic_questions(diag)

        # Build answers
        answers = [
            DiagnosticAnswerInput(
                question_id=q.id,
                answer_id="B",
                time_spent_seconds=15,
            )
            for q in questions
        ]

        # Patch model_dump to produce JSON-safe output (SQLite compat)
        _original_model_dump = SkillTreeItem.model_dump

        def _json_safe_dump(self, **kwargs):
            kwargs["mode"] = "json"
            return _original_model_dump(self, **kwargs)

        with patch.object(SkillTreeItem, "model_dump", _json_safe_dump):
            result = service.submit_deep_diagnostic(create_test_user.id, diag.id, answers)

        assert result["completed"] is True
        assert result["correct"] == len(questions)
        assert "skill_tree" in result

    def test_theta_to_rank_mapping(self):
        """_theta_to_rank returns correct ranks for various theta values."""
        from app.services.diagnostic_two_phase_service import _theta_to_rank

        assert _theta_to_rank(-2.0) == "E"
        assert _theta_to_rank(-1.0) == "D"
        assert _theta_to_rank(0.0) == "C"
        assert _theta_to_rank(0.7) == "B"
        assert _theta_to_rank(1.2) == "A"
        assert _theta_to_rank(2.0) == "S"

    def test_calculate_initial_theta(self):
        """_calculate_initial_theta produces reasonable logit values."""
        from app.services.diagnostic_two_phase_service import _calculate_initial_theta

        # Perfect score -> positive theta
        theta_perfect = _calculate_initial_theta(10, 10)
        assert theta_perfect > 0

        # Zero score -> negative theta
        theta_zero = _calculate_initial_theta(0, 10)
        assert theta_zero < 0

        # 50% -> theta near 0
        theta_half = _calculate_initial_theta(5, 10)
        assert -0.5 < theta_half < 0.5

        # Edge case: 0 total -> 0.0
        assert _calculate_initial_theta(0, 0) == 0.0


# ---------------------------------------------------------------------------
# Integration: Complete Diagnostic Flow
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestCompleteDiagnosticFlow:
    """End-to-end integration tests for the two-phase diagnostic."""

    def test_quick_then_deep_flow(self, client: TestClient, db: Session):
        """Full flow: register user, quick diagnostic, then deep diagnostic."""
        # Create a user
        user = create_test_user_record(db, username="flow_user", email="flow@test.com")
        headers = auth_header_for(user.id)

        # Create 5 subjects with topics and questions
        # Need 20 questions per subject to satisfy DeepDiagnosticStartResponse (total >= 15)
        subjects = _create_subjects(db, count=5)
        for subj in subjects:
            topic = _create_topic_for_subject(db, subj)
            _create_questions_for_subject(db, subj, topic, count=20, difficulty=3)

        # --- Quick diagnostic ---
        quick_start = client.post(
            "/api/v1/diagnostic/quick/start", headers=headers
        )
        assert quick_start.status_code == 200
        quick_data = quick_start.json()
        diagnostic_id = quick_data["diagnostic_id"]
        questions = quick_data["questions"]

        # Submit answers (all correct)
        answers = [
            {
                "question_id": q["id"],
                "answer_id": "B",
                "time_spent_seconds": 15,
            }
            for q in questions
        ]
        quick_submit = client.post(
            "/api/v1/diagnostic/quick/submit",
            json={"diagnostic_id": diagnostic_id, "answers": answers},
            headers=headers,
        )
        assert quick_submit.status_code == 200
        result = quick_submit.json()
        assert result["completed"] is True
        assert result["correct"] == len(questions)

        # --- Deep diagnostic for first subject ---
        first_subject = subjects[0]
        deep_start = client.post(
            f"/api/v1/diagnostic/deep/start/{first_subject.id}",
            headers=headers,
        )
        assert deep_start.status_code == 200
        deep_data = deep_start.json()
        deep_diag_id = deep_data["diagnostic_id"]
        deep_questions = deep_data["questions"]

        deep_answers = [
            {
                "question_id": q["id"],
                "answer_id": "B",
                "time_spent_seconds": 10,
            }
            for q in deep_questions
        ]

        # Patch SkillTreeItem.model_dump for SQLite JSONB compat
        from app.schemas.diagnostic import SkillTreeItem
        _original = SkillTreeItem.model_dump

        def _json_safe(self, **kwargs):
            kwargs["mode"] = "json"
            return _original(self, **kwargs)

        with patch.object(SkillTreeItem, "model_dump", _json_safe):
            deep_submit = client.post(
                "/api/v1/diagnostic/deep/submit",
                json={"diagnostic_id": deep_diag_id, "answers": deep_answers},
                headers=headers,
            )
        assert deep_submit.status_code == 200
        deep_result = deep_submit.json()
        assert deep_result["completed"] is True
        assert "skill_tree" in deep_result

    def test_submit_quick_diagnostic_partial_correct(
        self, client: TestClient, db: Session
    ):
        """Submit quick diagnostic with mix of correct/incorrect answers.

        When some answers are wrong, the service generates WeakArea objects
        that contain UUID fields.  We patch WeakArea.model_dump to produce
        JSON-safe output so that SQLite's TEXT-backed JSONB column can
        serialise them (PostgreSQL handles this natively).
        """
        user = create_test_user_record(
            db, username="partial_user", email="partial@test.com"
        )
        headers = auth_header_for(user.id)

        subjects = _create_subjects(db, count=5)
        for subj in subjects:
            topic = _create_topic_for_subject(db, subj)
            _create_questions_for_subject(db, subj, topic, count=3, difficulty=3)

        # Start
        start_resp = client.post(
            "/api/v1/diagnostic/quick/start", headers=headers
        )
        assert start_resp.status_code == 200
        data = start_resp.json()

        # Submit with alternating correct/incorrect answers
        answers = []
        for i, q in enumerate(data["questions"]):
            answers.append(
                {
                    "question_id": q["id"],
                    # "B" is correct, "A" is wrong
                    "answer_id": "B" if i % 2 == 0 else "A",
                    "time_spent_seconds": 20,
                }
            )

        # Patch WeakArea.model_dump for SQLite JSONB compat
        from app.schemas.diagnostic import WeakArea
        _original_wa = WeakArea.model_dump

        def _json_safe_wa(self, **kwargs):
            kwargs["mode"] = "json"
            return _original_wa(self, **kwargs)

        with patch.object(WeakArea, "model_dump", _json_safe_wa):
            submit_resp = client.post(
                "/api/v1/diagnostic/quick/submit",
                json={"diagnostic_id": data["diagnostic_id"], "answers": answers},
                headers=headers,
            )
        assert submit_resp.status_code == 200
        result = submit_resp.json()
        assert result["completed"] is True
        # With alternating answers, roughly half should be correct
        assert result["correct"] < result["total"]
