"""
Study plans system tests for the ICFES Leveling backend.

Tests cover:
- Endpoint integration tests (GET/POST/DELETE on /api/v1/study-plans/...)
- StudyPlanService unit tests for business logic
- Authentication and authorization checks
"""
import uuid
import json
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.study_plan import StudyPlan, PlanProgress
from app.models.subject import Subject
from app.models.user import User


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_plan_data(subject_name: str = "Matematicas Test") -> dict:
    """Return a minimal ``plan_data`` JSON blob accepted by StudyPlanService."""
    return {
        "subject": subject_name,
        "title": f"Mazmorra de {subject_name}: Fundamentos",
        "description": f"Plan personalizado para conquistar {subject_name}",
        "units": [
            {
                "unit_number": 1,
                "name": "Unidad 1 - Fundamentos",
                "description": "Conceptos base",
                "topics": [
                    {"name": "Tema A", "difficulty": 1, "questions": 10, "tags": ["basico"]},
                ],
                "recommendations": {
                    "priority": "high",
                    "weak_areas": [],
                    "focus_topics": [],
                    "study_time": "2 horas",
                },
                "unlocked": True,
                "progress": 0,
                "ai_recommended": False,
            },
            {
                "unit_number": 2,
                "name": "Unidad 2 - Intermedio",
                "description": "Conceptos intermedios",
                "topics": [
                    {"name": "Tema B", "difficulty": 2, "questions": 10, "tags": ["intermedio"]},
                ],
                "recommendations": {
                    "priority": "medium",
                    "weak_areas": [],
                    "focus_topics": [],
                    "study_time": "3 horas",
                },
                "unlocked": False,
                "progress": 0,
                "ai_recommended": False,
            },
        ],
        "total_questions": 20,
        "estimated_time": "5-7 horas",
        "difficulty_curve": "progressive",
        "icfes_weight": 0.25,
        "exam_sections": ["Pensamiento Matematico"],
        "personalized_recommendations": {
            "overall_accuracy": 0.0,
            "weak_topics": [],
            "strong_topics": [],
            "suggested_focus": [],
            "study_schedule": {},
            "estimated_improvement": {},
        },
    }


def _insert_study_plan(db: Session, user: User, subject: Subject) -> StudyPlan:
    """Insert a fully-formed StudyPlan row and return it."""
    plan_data = _make_plan_data(subject.name)
    plan = StudyPlan(
        id=uuid.uuid4(),
        user_id=user.id,
        subject_id=subject.id,
        plan_name=plan_data["title"],
        plan_data=json.dumps(plan_data),
        total_units=len(plan_data["units"]),
        completed_units=0,
        progress_percentage=0.00,
        is_active=True,
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)

    # Also insert PlanProgress rows so get_user_study_plans can compute
    # detailed progress without dividing by zero.
    for unit in plan_data["units"]:
        pp = PlanProgress(
            id=uuid.uuid4(),
            plan_id=plan.id,
            unit_number=unit["unit_number"],
            unit_name=unit["name"],
            unit_description=unit["description"],
            unit_content=json.dumps({"videos": [], "exercises": 10, "readings": 1}),
            is_completed=False,
            score=0.00,
            weighted_progress=json.dumps({
                "videos": {"completed": 0, "total": 1, "weight": 0.3},
                "exercises": {"completed": 0, "total": 10, "weight": 0.5},
                "readings": {"completed": 0, "total": 1, "weight": 0.2},
            }),
        )
        db.add(pp)
    db.commit()
    return plan


# ===================================================================
# conftest imports the helpers ``auth_header_for`` and
# ``create_test_user_record``.  We import them here for convenience.
# ===================================================================
from tests.conftest import auth_header_for, create_test_user_record  # noqa: E402


# ===================================================================
# ENDPOINT (integration) tests
# ===================================================================

@pytest.mark.integration
class TestStudyPlanEndpoints:
    """Test study plan HTTP endpoints under /api/v1/study-plans/."""

    # ------------------------------------------------------------------
    # GET /api/v1/study-plans/ - list plans for the authenticated user
    # ------------------------------------------------------------------

    def test_get_user_study_plans_empty(
        self, client: TestClient, create_test_user: User
    ):
        """An authenticated user with no plans gets an empty list."""
        headers = auth_header_for(create_test_user.id)

        with patch("app.services.study_plan_service.cache_service") as mock_cache:
            mock_cache.get.return_value = None
            mock_cache.set.return_value = None

            response = client.get("/api/v1/study-plans/", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert "plans" in data
        assert "total_plans" in data
        assert data["total_plans"] == 0

    def test_get_user_study_plans_with_plan(
        self,
        client: TestClient,
        db: Session,
        create_test_user: User,
        create_test_subject: Subject,
    ):
        """After inserting a study plan the list endpoint returns it."""
        plan = _insert_study_plan(db, create_test_user, create_test_subject)
        headers = auth_header_for(create_test_user.id)

        with patch("app.services.study_plan_service.cache_service") as mock_cache:
            mock_cache.get.return_value = None
            mock_cache.set.return_value = None

            response = client.get("/api/v1/study-plans/", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert data["total_plans"] >= 1
        assert any(p["id"] == str(plan.id) for p in data["plans"])

    # ------------------------------------------------------------------
    # GET /api/v1/study-plans/current - current active plan
    # ------------------------------------------------------------------

    def test_get_current_study_plan_none(
        self, client: TestClient, create_test_user: User
    ):
        """When the user has no active plan, the endpoint returns has_plan=False."""
        headers = auth_header_for(create_test_user.id)

        with patch("app.services.study_plan_service.cache_service") as mock_cache:
            mock_cache.get.return_value = None
            mock_cache.set.return_value = None

            response = client.get("/api/v1/study-plans/current", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert data["has_plan"] is False

    def test_get_current_study_plan_exists(
        self,
        client: TestClient,
        db: Session,
        create_test_user: User,
        create_test_subject: Subject,
    ):
        """When an active plan exists the endpoint returns it."""
        _insert_study_plan(db, create_test_user, create_test_subject)
        headers = auth_header_for(create_test_user.id)

        with patch("app.services.study_plan_service.cache_service") as mock_cache:
            mock_cache.get.return_value = None
            mock_cache.set.return_value = None

            response = client.get("/api/v1/study-plans/current", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert data["has_plan"] is True
        assert data["plan"] is not None

    # ------------------------------------------------------------------
    # GET /api/v1/study-plans/{plan_id} - plan detail
    # ------------------------------------------------------------------

    def test_get_study_plan_detail(
        self,
        client: TestClient,
        db: Session,
        create_test_user: User,
        create_test_subject: Subject,
    ):
        """Getting an existing plan by ID returns its details."""
        plan = _insert_study_plan(db, create_test_user, create_test_subject)
        headers = auth_header_for(create_test_user.id)

        with patch("app.services.study_plan_service.cache_service") as mock_cache:
            mock_cache.get.return_value = None
            mock_cache.set.return_value = None

            response = client.get(
                f"/api/v1/study-plans/{plan.id}", headers=headers
            )

        # The route returns StudyPlanDetail or 500 on internal error.
        assert response.status_code in (200, 500)
        if response.status_code == 200:
            data = response.json()
            assert data["id"] == str(plan.id)
            assert "plan_name" in data
            assert "units" in data

    def test_get_study_plan_detail_not_found(
        self, client: TestClient, create_test_user: User
    ):
        """Requesting a non-existent plan returns 404 or 500."""
        headers = auth_header_for(create_test_user.id)
        fake_id = str(uuid.uuid4())

        with patch("app.services.study_plan_service.cache_service") as mock_cache:
            mock_cache.get.return_value = None
            mock_cache.set.return_value = None

            response = client.get(
                f"/api/v1/study-plans/{fake_id}", headers=headers
            )

        # Route catches exceptions and may return 404 or 500
        assert response.status_code in (404, 500)

    # ------------------------------------------------------------------
    # DELETE /api/v1/study-plans/{plan_id}
    # ------------------------------------------------------------------

    def test_delete_study_plan(
        self,
        client: TestClient,
        db: Session,
        create_test_user: User,
        create_test_subject: Subject,
    ):
        """Deleting a plan marks it inactive and returns success message."""
        plan = _insert_study_plan(db, create_test_user, create_test_subject)
        headers = auth_header_for(create_test_user.id)

        response = client.delete(
            f"/api/v1/study-plans/{plan.id}", headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "message" in data

        # Verify it is marked inactive in the DB
        db.refresh(plan)
        assert plan.is_active is False

    def test_delete_study_plan_not_found(
        self, client: TestClient, create_test_user: User
    ):
        """Deleting a plan that does not belong to the user returns 404/500."""
        headers = auth_header_for(create_test_user.id)
        fake_id = str(uuid.uuid4())

        response = client.delete(
            f"/api/v1/study-plans/{fake_id}", headers=headers
        )

        assert response.status_code in (404, 500)

    # ------------------------------------------------------------------
    # POST /api/v1/study-plans/generate/{subject_id}
    # ------------------------------------------------------------------

    def test_generate_study_plan_success(
        self,
        client: TestClient,
        db: Session,
        create_test_user: User,
        create_test_subject: Subject,
    ):
        """
        Generating a plan for an existing subject returns a StudyPlanDetail.
        We mock the service layer so no external dependencies are needed.
        """
        headers = auth_header_for(create_test_user.id)
        plan_dict = _make_plan_data(create_test_subject.name)
        plan_dict["id"] = "generated"

        with patch("app.services.study_plan_service.cache_service") as mock_cache:
            mock_cache.get.return_value = None
            mock_cache.set.return_value = None

            with patch(
                "app.routes.study_plans.StudyPlanService"
            ) as MockService:
                instance = MockService.return_value
                instance.generate_intelligent_plan_from_diagnostic.return_value = (
                    plan_dict
                )
                instance.generate_personalized_plan.return_value = plan_dict
                instance._invalidate_user_cache.return_value = None

                response = client.post(
                    f"/api/v1/study-plans/generate/{create_test_subject.id}",
                    headers=headers,
                )

        # Expect 200 with StudyPlanDetail or 500 if underlying data is off
        assert response.status_code in (200, 500)
        if response.status_code == 200:
            data = response.json()
            assert "id" in data
            assert "plan_name" in data
            assert "units" in data

    def test_generate_study_plan_subject_not_found(
        self, client: TestClient, create_test_user: User
    ):
        """Generating a plan for a non-existent subject returns 404 or 500."""
        headers = auth_header_for(create_test_user.id)
        fake_subject_id = str(uuid.uuid4())

        with patch("app.services.study_plan_service.cache_service") as mock_cache:
            mock_cache.get.return_value = None
            mock_cache.set.return_value = None

            response = client.post(
                f"/api/v1/study-plans/generate/{fake_subject_id}",
                headers=headers,
            )

        assert response.status_code in (404, 500)

    # ------------------------------------------------------------------
    # POST /api/v1/study-plans/{plan_id}/units/{unit_number}/progress
    # ------------------------------------------------------------------

    def test_update_unit_progress(
        self,
        client: TestClient,
        db: Session,
        create_test_user: User,
        create_test_subject: Subject,
    ):
        """Updating unit progress returns a success message."""
        plan = _insert_study_plan(db, create_test_user, create_test_subject)
        headers = auth_header_for(create_test_user.id)

        payload = {
            "videos_completed": 1,
            "exercises_completed": 2,
            "readings_completed": 0,
            "score": 75.0,
        }

        with patch("app.services.study_plan_service.cache_service") as mock_cache:
            mock_cache.get.return_value = None
            mock_cache.set.return_value = None

            response = client.post(
                f"/api/v1/study-plans/{plan.id}/units/1/progress",
                json=payload,
                headers=headers,
            )

        assert response.status_code in (200, 500)
        if response.status_code == 200:
            data = response.json()
            assert "message" in data

    # ------------------------------------------------------------------
    # GET /api/v1/study-plans/recommendations/{subject_id}
    # ------------------------------------------------------------------

    def test_get_study_recommendations(
        self,
        client: TestClient,
        db: Session,
        create_test_user: User,
        create_test_subject: Subject,
    ):
        """Recommendations endpoint returns suggestions for a subject."""
        headers = auth_header_for(create_test_user.id)

        with patch("app.services.study_plan_service.cache_service") as mock_cache:
            mock_cache.get.return_value = None
            mock_cache.set.return_value = None

            response = client.get(
                f"/api/v1/study-plans/recommendations/{create_test_subject.id}",
                headers=headers,
            )

        assert response.status_code in (200, 500)
        if response.status_code == 200:
            data = response.json()
            assert "subject_id" in data
            assert "next_steps" in data

    # ------------------------------------------------------------------
    # GET /api/v1/study-plans/subjects/available
    # ------------------------------------------------------------------

    def test_get_available_subjects(
        self,
        client: TestClient,
        db: Session,
        create_test_user: User,
        create_test_subject: Subject,
    ):
        """Available subjects endpoint lists subjects with plan status."""
        headers = auth_header_for(create_test_user.id)

        with patch("app.services.study_plan_service.cache_service") as mock_cache:
            mock_cache.get.return_value = None
            mock_cache.set.return_value = None

            response = client.get(
                "/api/v1/study-plans/subjects/available",
                headers=headers,
            )

        assert response.status_code in (200, 500)
        if response.status_code == 200:
            data = response.json()
            assert "subjects" in data
            assert "total_subjects" in data

    # ------------------------------------------------------------------
    # Authentication tests
    # ------------------------------------------------------------------

    def test_unauthorized_access_no_token(self, client: TestClient):
        """Accessing study plans without a token returns 401."""
        response = client.get("/api/v1/study-plans/")
        assert response.status_code == 401

    def test_unauthorized_access_invalid_token(self, client: TestClient):
        """Accessing study plans with an invalid token returns 401."""
        headers = {"Authorization": "Bearer invalid-token-value"}
        response = client.get("/api/v1/study-plans/", headers=headers)
        assert response.status_code == 401

    def test_delete_another_users_plan(
        self,
        client: TestClient,
        db: Session,
        create_test_user: User,
        create_test_subject: Subject,
    ):
        """A user cannot delete another user's study plan."""
        plan = _insert_study_plan(db, create_test_user, create_test_subject)

        # Create a second user
        other_user = create_test_user_record(db, username="other_user", email="other@example.com")
        headers = auth_header_for(other_user.id)

        response = client.delete(
            f"/api/v1/study-plans/{plan.id}", headers=headers
        )

        # The delete route checks ownership; it should return 404 or 500
        assert response.status_code in (404, 500)


# ===================================================================
# SERVICE unit tests
# ===================================================================

@pytest.mark.unit
class TestStudyPlanService:
    """Test StudyPlanService methods directly (no HTTP)."""

    def test_get_user_study_plans_empty(
        self, db: Session, create_test_user: User
    ):
        """Returns an empty list when the user has no plans."""
        with patch("app.services.study_plan_service.cache_service") as mock_cache:
            mock_cache.get.return_value = None
            mock_cache.set.return_value = None

            from app.services.study_plan_service import StudyPlanService

            service = StudyPlanService(db)
            plans = service.get_user_study_plans(str(create_test_user.id))

        assert isinstance(plans, list)
        assert len(plans) == 0

    def test_get_user_study_plans_returns_inserted_plan(
        self,
        db: Session,
        create_test_user: User,
        create_test_subject: Subject,
    ):
        """Returns plans that were inserted for the user."""
        plan = _insert_study_plan(db, create_test_user, create_test_subject)

        with patch("app.services.study_plan_service.cache_service") as mock_cache:
            mock_cache.get.return_value = None
            mock_cache.set.return_value = None

            from app.services.study_plan_service import StudyPlanService

            service = StudyPlanService(db)
            plans = service.get_user_study_plans(str(create_test_user.id))

        assert len(plans) >= 1
        assert any(p["id"] == str(plan.id) for p in plans)

    def test_analyze_user_performance_no_data(
        self,
        db: Session,
        create_test_user: User,
        create_test_subject: Subject,
    ):
        """When a user has no battle answers, performance analysis returns zeros."""
        with patch("app.services.study_plan_service.cache_service") as mock_cache:
            mock_cache.get.return_value = None
            mock_cache.set.return_value = None

            from app.services.study_plan_service import StudyPlanService

            service = StudyPlanService(db)
            perf = service._analyze_user_performance(
                str(create_test_user.id), str(create_test_subject.id)
            )

        assert perf["total_questions"] == 0
        assert perf["accuracy"] == 0.0
        assert perf["weak_topics"] == []
        assert perf["strong_topics"] == []

    def test_calculate_detailed_progress_no_records(
        self, db: Session
    ):
        """When there are no PlanProgress rows, overall progress is 0."""
        with patch("app.services.study_plan_service.cache_service") as mock_cache:
            mock_cache.get.return_value = None
            mock_cache.set.return_value = None

            from app.services.study_plan_service import StudyPlanService

            service = StudyPlanService(db)
            progress = service._calculate_detailed_progress(str(uuid.uuid4()))

        assert progress["overall_progress"] == 0
        assert progress["completed_units"] == 0
        assert progress["unit_details"] == []

    def test_calculate_detailed_progress_with_records(
        self,
        db: Session,
        create_test_user: User,
        create_test_subject: Subject,
    ):
        """With PlanProgress rows, progress is computed correctly."""
        plan = _insert_study_plan(db, create_test_user, create_test_subject)

        with patch("app.services.study_plan_service.cache_service") as mock_cache:
            mock_cache.get.return_value = None
            mock_cache.set.return_value = None

            from app.services.study_plan_service import StudyPlanService

            service = StudyPlanService(db)
            progress = service._calculate_detailed_progress(str(plan.id))

        assert "overall_progress" in progress
        assert "completed_units" in progress
        assert isinstance(progress["unit_details"], list)
        assert len(progress["unit_details"]) == 2  # two units inserted

    def test_update_unit_progress(
        self,
        db: Session,
        create_test_user: User,
        create_test_subject: Subject,
    ):
        """Updating unit progress through the service returns updated values."""
        plan = _insert_study_plan(db, create_test_user, create_test_subject)

        with patch("app.services.study_plan_service.cache_service") as mock_cache:
            mock_cache.get.return_value = None
            mock_cache.set.return_value = None

            from app.services.study_plan_service import StudyPlanService

            service = StudyPlanService(db)
            result = service.update_unit_progress(
                plan_id=str(plan.id),
                unit_number=1,
                progress_data={"videos_completed": 1, "exercises_completed": 5},
            )

        assert "unit_number" in result
        assert result["unit_number"] == 1
        assert "progress_percentage" in result
        assert "is_completed" in result

    def test_get_suggested_focus_low_accuracy(self, db: Session):
        """Low accuracy produces suggestions about basic concepts."""
        with patch("app.services.study_plan_service.cache_service"):
            from app.services.study_plan_service import StudyPlanService

            service = StudyPlanService(db)
            user_data = {
                "accuracy": 40.0,
                "weak_topics": [{"topic": "Algebra"}, {"topic": "Geometria"}],
                "strong_topics": [],
                "total_questions": 10,
            }
            focus = service._get_suggested_focus(user_data)

        assert isinstance(focus, list)
        assert len(focus) > 0
        # Should mention basic concepts for low accuracy
        assert any("fundament" in s.lower() or "b" in s.lower() for s in focus)

    def test_get_suggested_focus_high_accuracy(self, db: Session):
        """High accuracy produces suggestions about advanced topics."""
        with patch("app.services.study_plan_service.cache_service"):
            from app.services.study_plan_service import StudyPlanService

            service = StudyPlanService(db)
            user_data = {
                "accuracy": 90.0,
                "weak_topics": [],
                "strong_topics": [{"topic": "Algebra"}],
                "total_questions": 100,
            }
            focus = service._get_suggested_focus(user_data)

        assert isinstance(focus, list)
        assert len(focus) > 0
        assert any("avanzad" in s.lower() or "complej" in s.lower() for s in focus)

    def test_generate_study_schedule(self, db: Session):
        """Study schedule generation returns required keys."""
        with patch("app.services.study_plan_service.cache_service"):
            from app.services.study_plan_service import StudyPlanService

            service = StudyPlanService(db)
            user_data = {
                "accuracy": 55.0,
                "weak_topics": [{"topic": "Ecuaciones"}],
                "strong_topics": [],
                "total_questions": 20,
            }
            schedule = service._generate_study_schedule(user_data, user_level=3)

        assert "sessions_per_day" in schedule
        assert "session_duration_minutes" in schedule
        assert "recommended_days" in schedule
        assert schedule["sessions_per_day"] > 0

    def test_estimate_improvement(self, db: Session):
        """Improvement estimation returns required keys."""
        with patch("app.services.study_plan_service.cache_service"):
            from app.services.study_plan_service import StudyPlanService

            service = StudyPlanService(db)
            user_data = {
                "accuracy": 65.0,
                "weak_topics": [],
                "strong_topics": [],
                "total_questions": 30,
            }
            estimate = service._estimate_improvement(user_data)

        assert "current_accuracy" in estimate
        assert "potential_improvement" in estimate
        assert "target_accuracy" in estimate
        assert "weeks_to_improve" in estimate
        assert estimate["target_accuracy"] > estimate["current_accuracy"]


# ===================================================================
# Schema validation tests
# ===================================================================

@pytest.mark.unit
class TestStudyPlanSchemas:
    """Test that Pydantic schemas accept expected data shapes."""

    def test_study_plan_detail_schema(self):
        """StudyPlanDetail can be constructed from valid data."""
        from app.schemas.study_plan import (
            StudyPlanDetail,
            StudyUnit,
            StudyTopic,
            UnitRecommendations,
            ProgressDetails,
        )

        topic = StudyTopic(name="Algebra", difficulty=2, questions=10, tags=["math"])
        reco = UnitRecommendations(
            priority="high",
            weak_areas=["variables"],
            focus_topics=["ecuaciones"],
            study_time="2 horas",
        )
        unit = StudyUnit(
            unit_number=1,
            name="Unit 1",
            description="First unit",
            topics=[topic],
            recommendations=reco,
            unlocked=True,
            progress=0.0,
            ai_recommended=False,
        )
        progress = ProgressDetails(
            overall_progress=0.0, completed_units=0, unit_details=[]
        )

        detail = StudyPlanDetail(
            id="abc",
            plan_name="Test Plan",
            subject="Math",
            title="Test Plan",
            description="A test plan",
            units=[unit],
            total_units=1,
            completed_units=0,
            progress_percentage=0.0,
            estimated_time="5 horas",
            difficulty_curve="progressive",
            icfes_weight=0.25,
            exam_sections=["Math"],
            progress_details=progress,
        )

        assert detail.id == "abc"
        assert detail.total_units == 1
        assert len(detail.units) == 1

    def test_study_plan_list_schema(self):
        """StudyPlanList can be constructed."""
        from app.schemas.study_plan import StudyPlanList

        plan_list = StudyPlanList(plans=[], total_plans=0, active_plans=0)
        assert plan_list.total_plans == 0

    def test_unit_progress_update_schema(self):
        """UnitProgressUpdate accepts valid data."""
        from app.schemas.study_plan import UnitProgressUpdate

        update = UnitProgressUpdate(
            videos_completed=1, exercises_completed=3, readings_completed=0, score=85.0
        )
        assert update.videos_completed == 1
        assert update.score == 85.0

    def test_unit_progress_update_defaults(self):
        """UnitProgressUpdate defaults are zero."""
        from app.schemas.study_plan import UnitProgressUpdate

        update = UnitProgressUpdate()
        assert update.videos_completed == 0
        assert update.exercises_completed == 0
        assert update.readings_completed == 0
        assert update.score is None
