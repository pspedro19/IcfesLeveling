"""
Study plans system tests for the ICFES Leveling backend.
"""
import pytest
from unittest.mock import patch, Mock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import json

from app.models import StudyPlan, StudyPlanTopic, Subject, Topic, User, DiagnosticTest
from app.services.study_plan_service import StudyPlanService
from app.services.ai_study_plan_service import AIStudyPlanService
from app.schemas.study_plan import StudyPlanCreate, StudyPlanUpdate


@pytest.mark.integration
class TestStudyPlanEndpoints:
    """Test study plan endpoints."""

    def test_generate_study_plan_success(self, client: TestClient, create_test_user, create_test_subject, create_test_diagnostic):
        """Test successful study plan generation."""
        with patch('app.core.security.decode_token') as mock_decode:
            mock_decode.return_value = {"sub": create_test_user.id, "username": create_test_user.username}
            
            headers = {"Authorization": "Bearer valid_token"}
            response = client.post(f"/api/v1/study-plans/generate/{create_test_subject.id}", headers=headers)

            assert response.status_code == 200
            data = response.json()
            assert "id" in data
            assert "title" in data
            assert "description" in data
            assert "topics" in data
            assert "estimated_weeks" in data

    def test_generate_study_plan_no_diagnostic(self, client: TestClient, create_test_user, create_test_subject):
        """Test study plan generation without prior diagnostic."""
        with patch('app.core.security.decode_token') as mock_decode:
            mock_decode.return_value = {"sub": create_test_user.id, "username": create_test_user.username}
            
            headers = {"Authorization": "Bearer valid_token"}
            response = client.post(f"/api/v1/study-plans/generate/{create_test_subject.id}", headers=headers)

            # Should still create a basic plan or return appropriate error
            assert response.status_code in [200, 400]

    def test_get_user_study_plans(self, client: TestClient, create_test_user, create_test_study_plan):
        """Test getting user's study plans."""
        with patch('app.core.security.decode_token') as mock_decode:
            mock_decode.return_value = {"sub": create_test_user.id, "username": create_test_user.username}
            
            headers = {"Authorization": "Bearer valid_token"}
            response = client.get(f"/api/v1/study-plans/user/{create_test_user.id}", headers=headers)

            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
            assert len(data) >= 1
            assert data[0]["user_id"] == create_test_user.id

    def test_get_study_plan_details(self, client: TestClient, create_test_user, create_test_study_plan):
        """Test getting specific study plan details."""
        with patch('app.core.security.decode_token') as mock_decode:
            mock_decode.return_value = {"sub": create_test_user.id, "username": create_test_user.username}
            
            headers = {"Authorization": "Bearer valid_token"}
            response = client.get(f"/api/v1/study-plans/{create_test_study_plan.id}", headers=headers)

            assert response.status_code == 200
            data = response.json()
            assert data["id"] == create_test_study_plan.id
            assert data["title"] == create_test_study_plan.title

    def test_update_study_plan(self, client: TestClient, create_test_user, create_test_study_plan):
        """Test updating a study plan."""
        update_data = {
            "title": "Updated Study Plan Title",
            "description": "Updated description",
            "status": "active"
        }

        with patch('app.core.security.decode_token') as mock_decode:
            mock_decode.return_value = {"sub": create_test_user.id, "username": create_test_user.username}
            
            headers = {"Authorization": "Bearer valid_token"}
            response = client.put(f"/api/v1/study-plans/{create_test_study_plan.id}", json=update_data, headers=headers)

            assert response.status_code == 200
            data = response.json()
            assert data["title"] == "Updated Study Plan Title"

    def test_delete_study_plan(self, client: TestClient, create_test_user, create_test_study_plan):
        """Test deleting a study plan."""
        with patch('app.core.security.decode_token') as mock_decode:
            mock_decode.return_value = {"sub": create_test_user.id, "username": create_test_user.username}
            
            headers = {"Authorization": "Bearer valid_token"}
            response = client.delete(f"/api/v1/study-plans/{create_test_study_plan.id}", headers=headers)

            assert response.status_code == 204

            # Verify deletion
            get_response = client.get(f"/api/v1/study-plans/{create_test_study_plan.id}", headers=headers)
            assert get_response.status_code == 404

    def test_mark_topic_completed(self, client: TestClient, create_test_user, create_test_study_plan, create_test_topic):
        """Test marking a topic as completed in study plan."""
        with patch('app.core.security.decode_token') as mock_decode:
            mock_decode.return_value = {"sub": create_test_user.id, "username": create_test_user.username}
            
            headers = {"Authorization": "Bearer valid_token"}
            response = client.post(
                f"/api/v1/study-plans/{create_test_study_plan.id}/topics/{create_test_topic.id}/complete",
                headers=headers
            )

            assert response.status_code == 200
            data = response.json()
            assert "message" in data
            assert "xp_gained" in data

    def test_get_study_plan_progress(self, client: TestClient, create_test_user, create_test_study_plan):
        """Test getting study plan progress."""
        with patch('app.core.security.decode_token') as mock_decode:
            mock_decode.return_value = {"sub": create_test_user.id, "username": create_test_user.username}
            
            headers = {"Authorization": "Bearer valid_token"}
            response = client.get(f"/api/v1/study-plans/{create_test_study_plan.id}/progress", headers=headers)

            assert response.status_code == 200
            data = response.json()
            assert "completion_percentage" in data
            assert "completed_topics" in data
            assert "total_topics" in data
            assert "estimated_completion_date" in data

    def test_unauthorized_access(self, client: TestClient, create_test_study_plan):
        """Test unauthorized access to study plans."""
        response = client.get(f"/api/v1/study-plans/{create_test_study_plan.id}")
        assert response.status_code == 401

    def test_access_other_user_plan(self, client: TestClient, create_test_study_plan):
        """Test accessing another user's study plan."""
        with patch('app.core.security.decode_token') as mock_decode:
            mock_decode.return_value = {"sub": "other-user-id", "username": "otheruser"}
            
            headers = {"Authorization": "Bearer valid_token"}
            response = client.get(f"/api/v1/study-plans/{create_test_study_plan.id}", headers=headers)

            assert response.status_code == 403


@pytest.mark.unit
class TestStudyPlanService:
    """Test study plan service functionality."""

    def test_create_study_plan(self, db_session: Session, create_test_user, create_test_subject, create_test_topic):
        """Test creating a study plan."""
        service = StudyPlanService(db_session)
        
        plan_data = {
            "user_id": create_test_user.id,
            "subject_id": create_test_subject.id,
            "title": "Test Study Plan",
            "description": "A test study plan",
            "difficulty_level": 2,
            "estimated_weeks": 8
        }

        plan = service.create_study_plan(plan_data)

        assert plan.id is not None
        assert plan.user_id == create_test_user.id
        assert plan.subject_id == create_test_subject.id
        assert plan.title == "Test Study Plan"
        assert plan.status == "active"

    def test_get_user_study_plans(self, db_session: Session, create_test_user, create_test_study_plan):
        """Test getting user's study plans."""
        service = StudyPlanService(db_session)
        
        plans = service.get_user_study_plans(create_test_user.id)

        assert len(plans) >= 1
        assert all(plan.user_id == create_test_user.id for plan in plans)

    def test_add_topic_to_plan(self, db_session: Session, create_test_study_plan, create_test_topic):
        """Test adding a topic to a study plan."""
        service = StudyPlanService(db_session)
        
        plan_topic = service.add_topic_to_plan(
            create_test_study_plan.id,
            create_test_topic.id,
            order_index=1,
            estimated_hours=4
        )

        assert plan_topic.study_plan_id == create_test_study_plan.id
        assert plan_topic.topic_id == create_test_topic.id
        assert plan_topic.order_index == 1
        assert plan_topic.status == "pending"

    def test_complete_topic(self, db_session: Session, create_test_study_plan, create_test_topic, create_test_user):
        """Test completing a topic in study plan."""
        service = StudyPlanService(db_session)
        
        # First add topic to plan
        service.add_topic_to_plan(create_test_study_plan.id, create_test_topic.id)
        
        # Then complete it
        result = service.complete_topic(create_test_study_plan.id, create_test_topic.id, create_test_user.id)

        assert result["status"] == "completed"
        assert "xp_gained" in result
        assert result["xp_gained"] > 0

        # Verify user XP was updated
        db_session.refresh(create_test_user)
        assert create_test_user.xp > 0

    def test_calculate_progress(self, db_session: Session, create_test_study_plan, create_test_topic):
        """Test calculating study plan progress."""
        service = StudyPlanService(db_session)
        
        # Add multiple topics
        topics = []
        for i in range(5):
            topic = Topic(
                id=i + 10,  # Avoid ID conflicts
                name=f"Topic {i + 1}",
                subject_id=create_test_study_plan.subject_id,
                difficulty_level=2,
                estimated_time=60,
                is_active=True
            )
            topics.append(topic)
            db_session.add(topic)
        
        db_session.commit()

        # Add topics to plan
        for i, topic in enumerate(topics):
            service.add_topic_to_plan(create_test_study_plan.id, topic.id, order_index=i)

        # Complete some topics
        service.complete_topic(create_test_study_plan.id, topics[0].id, create_test_study_plan.user_id)
        service.complete_topic(create_test_study_plan.id, topics[1].id, create_test_study_plan.user_id)

        progress = service.calculate_progress(create_test_study_plan.id)

        assert progress["total_topics"] == 5
        assert progress["completed_topics"] == 2
        assert progress["completion_percentage"] == 40.0
        assert progress["current_topic"] is not None

    def test_get_recommended_topics(self, db_session: Session, create_test_user, create_test_subject, create_test_diagnostic):
        """Test getting recommended topics based on diagnostic results."""
        service = StudyPlanService(db_session)
        
        # Create topics with different difficulties
        topics = []
        for i in range(5):
            topic = Topic(
                id=i + 20,  # Avoid ID conflicts
                name=f"Topic {i + 1}",
                subject_id=create_test_subject.id,
                difficulty_level=(i % 3) + 1,
                estimated_time=60,
                learning_objectives=[f"Learn objective {i + 1}"],
                is_active=True
            )
            topics.append(topic)
            db_session.add(topic)
        
        db_session.commit()

        recommended_topics = service.get_recommended_topics(create_test_user.id, create_test_subject.id)

        assert isinstance(recommended_topics, list)
        assert len(recommended_topics) > 0
        
        # Should prioritize easier topics for lower-performing users
        if create_test_diagnostic.score_percentage < 70:
            assert any(topic.difficulty_level <= 2 for topic in recommended_topics[:3])

    def test_adaptive_plan_adjustment(self, db_session: Session, create_test_user, create_test_study_plan):
        """Test adaptive adjustment of study plan based on performance."""
        service = StudyPlanService(db_session)
        
        # Simulate poor performance
        performance_data = {
            "recent_scores": [45, 50, 55],
            "time_spent": 120,  # minutes
            "difficulty_feedback": "too_hard"
        }

        adjusted_plan = service.adjust_plan_based_on_performance(
            create_test_study_plan.id,
            performance_data
        )

        assert adjusted_plan["difficulty_level"] <= create_test_study_plan.difficulty_level
        assert "adjustments_made" in adjusted_plan
        assert len(adjusted_plan["adjustments_made"]) > 0

    def test_estimate_completion_time(self, db_session: Session, create_test_study_plan, create_test_user):
        """Test estimating study plan completion time."""
        service = StudyPlanService(db_session)
        
        # Add topics with estimated times
        total_estimated_hours = 0
        for i in range(3):
            topic = Topic(
                id=i + 30,  # Avoid ID conflicts
                name=f"Timed Topic {i + 1}",
                subject_id=create_test_study_plan.subject_id,
                difficulty_level=2,
                estimated_time=120,  # 2 hours each
                is_active=True
            )
            total_estimated_hours += 2
            db_session.add(topic)
            
        db_session.commit()

        for i in range(3):
            service.add_topic_to_plan(create_test_study_plan.id, i + 30)

        completion_estimate = service.estimate_completion_time(create_test_study_plan.id)

        assert "estimated_hours" in completion_estimate
        assert "estimated_weeks" in completion_estimate
        assert "completion_date" in completion_estimate
        assert completion_estimate["estimated_hours"] >= total_estimated_hours


@pytest.mark.unit
class TestAIStudyPlanService:
    """Test AI-powered study plan service."""

    @patch('app.services.ai_study_plan_service.openai.ChatCompletion.create')
    def test_generate_ai_study_plan(self, mock_openai, db_session: Session, create_test_user, create_test_subject, create_test_diagnostic):
        """Test AI-generated study plan."""
        # Mock OpenAI response
        mock_response = {
            "choices": [{
                "message": {
                    "content": json.dumps({
                        "title": "AI-Generated Math Study Plan",
                        "description": "Personalized plan based on diagnostic results",
                        "topics": ["Algebra", "Geometry", "Calculus"],
                        "estimated_weeks": 10,
                        "difficulty_progression": "gradual"
                    })
                }
            }]
        }
        mock_openai.return_value = Mock(**mock_response)

        service = AIStudyPlanService(db_session)
        
        ai_plan = service.generate_ai_study_plan(
            create_test_user.id,
            create_test_subject.id,
            diagnostic_results=create_test_diagnostic
        )

        assert "title" in ai_plan
        assert "description" in ai_plan
        assert "topics" in ai_plan
        assert "estimated_weeks" in ai_plan
        mock_openai.assert_called_once()

    @patch('app.services.ai_study_plan_service.openai.ChatCompletion.create')
    def test_get_ai_learning_tips(self, mock_openai, db_session: Session):
        """Test AI-generated learning tips."""
        mock_response = {
            "choices": [{
                "message": {
                    "content": json.dumps({
                        "tips": [
                            "Practice daily for consistency",
                            "Focus on weak areas first",
                            "Use spaced repetition"
                        ],
                        "motivation": "You're making great progress!"
                    })
                }
            }]
        }
        mock_openai.return_value = Mock(**mock_response)

        service = AIStudyPlanService(db_session)
        
        learning_data = {
            "subject": "Mathematics",
            "current_level": "B",
            "recent_scores": [70, 75, 80],
            "study_time": 5  # hours per week
        }
        
        tips = service.get_ai_learning_tips(learning_data)

        assert "tips" in tips
        assert "motivation" in tips
        assert len(tips["tips"]) > 0
        mock_openai.assert_called_once()

    def test_analyze_learning_pattern(self, db_session: Session, create_test_user):
        """Test analyzing user learning patterns."""
        service = AIStudyPlanService(db_session)
        
        # Create mock study session data
        study_sessions = [
            {"date": "2024-01-01", "duration": 60, "topics_covered": 2, "score": 80},
            {"date": "2024-01-02", "duration": 45, "topics_covered": 1, "score": 75},
            {"date": "2024-01-03", "duration": 90, "topics_covered": 3, "score": 85},
        ]
        
        pattern_analysis = service.analyze_learning_pattern(study_sessions)

        assert "optimal_session_length" in pattern_analysis
        assert "best_study_times" in pattern_analysis
        assert "productivity_trends" in pattern_analysis
        assert "recommendations" in pattern_analysis

    def test_predict_performance(self, db_session: Session):
        """Test predicting future performance."""
        service = AIStudyPlanService(db_session)
        
        historical_data = {
            "scores": [60, 65, 70, 75, 80],
            "study_hours": [5, 6, 4, 7, 6],
            "topics_completed": [2, 2, 1, 3, 2]
        }
        
        prediction = service.predict_performance(historical_data, weeks_ahead=4)

        assert "predicted_score" in prediction
        assert "confidence_interval" in prediction
        assert "factors" in prediction
        assert prediction["predicted_score"] > 0


@pytest.mark.integration
class TestStudyPlanIntegration:
    """Integration tests for study plan system."""

    def test_diagnostic_to_study_plan_flow(self, client: TestClient, db_session: Session, create_test_user, create_test_subject, create_test_topic):
        """Test complete flow from diagnostic to study plan creation."""
        # Create diagnostic test result
        diagnostic = DiagnosticTest(
            user_id=create_test_user.id,
            subject_id=create_test_subject.id,
            score_percentage=65.0,
            correct_answers=6,
            questions_answered=10,
            time_taken=600,
            rank_assigned="C",
            status="completed"
        )
        db_session.add(diagnostic)
        db_session.commit()

        with patch('app.core.security.decode_token') as mock_decode:
            mock_decode.return_value = {"sub": create_test_user.id, "username": create_test_user.username}
            
            headers = {"Authorization": "Bearer valid_token"}
            
            # Generate study plan based on diagnostic
            response = client.post(f"/api/v1/study-plans/generate/{create_test_subject.id}", headers=headers)
            assert response.status_code == 200
            
            plan_data = response.json()
            plan_id = plan_data["id"]
            
            # Get plan details
            details_response = client.get(f"/api/v1/study-plans/{plan_id}", headers=headers)
            assert details_response.status_code == 200
            
            details_data = details_response.json()
            assert details_data["difficulty_level"] <= 3  # Adjusted for C rank

    def test_study_plan_progress_tracking(self, client: TestClient, db_session: Session, create_test_user, create_test_study_plan, create_test_topic):
        """Test tracking progress through a study plan."""
        with patch('app.core.security.decode_token') as mock_decode:
            mock_decode.return_value = {"sub": create_test_user.id, "username": create_test_user.username}
            
            headers = {"Authorization": "Bearer valid_token"}

            # Get initial progress
            progress_response = client.get(f"/api/v1/study-plans/{create_test_study_plan.id}/progress", headers=headers)
            assert progress_response.status_code == 200
            
            initial_progress = progress_response.json()
            initial_percentage = initial_progress.get("completion_percentage", 0)

            # Complete a topic
            complete_response = client.post(
                f"/api/v1/study-plans/{create_test_study_plan.id}/topics/{create_test_topic.id}/complete",
                headers=headers
            )
            assert complete_response.status_code == 200

            # Check updated progress
            updated_progress_response = client.get(f"/api/v1/study-plans/{create_test_study_plan.id}/progress", headers=headers)
            assert updated_progress_response.status_code == 200
            
            updated_progress = updated_progress_response.json()
            updated_percentage = updated_progress.get("completion_percentage", 0)
            
            assert updated_percentage > initial_percentage

    def test_multiple_concurrent_study_plans(self, client: TestClient, db_session: Session, create_test_user):
        """Test user with multiple active study plans."""
        # Create multiple subjects
        subjects = []
        for i in range(3):
            subject = Subject(
                id=i + 10,  # Avoid conflicts
                name=f"Subject {i + 1}",
                code=f"SUB{i + 1}",
                description=f"Test subject {i + 1}",
                is_active=True
            )
            subjects.append(subject)
            db_session.add(subject)
        
        db_session.commit()

        with patch('app.core.security.decode_token') as mock_decode:
            mock_decode.return_value = {"sub": create_test_user.id, "username": create_test_user.username}
            
            headers = {"Authorization": "Bearer valid_token"}

            # Generate study plans for each subject
            plan_ids = []
            for subject in subjects:
                response = client.post(f"/api/v1/study-plans/generate/{subject.id}", headers=headers)
                
                if response.status_code == 200:
                    plan_data = response.json()
                    plan_ids.append(plan_data["id"])

            # Get all user's study plans
            all_plans_response = client.get(f"/api/v1/study-plans/user/{create_test_user.id}", headers=headers)
            assert all_plans_response.status_code == 200
            
            all_plans_data = all_plans_response.json()
            assert len(all_plans_data) >= len(plan_ids)

    @patch('app.services.ai_study_plan_service.openai.ChatCompletion.create')
    def test_ai_enhanced_study_plan_generation(self, mock_openai, client: TestClient, db_session: Session, create_test_user, create_test_subject, create_test_diagnostic):
        """Test AI-enhanced study plan generation."""
        # Mock AI response
        mock_response = {
            "choices": [{
                "message": {
                    "content": json.dumps({
                        "title": "AI-Enhanced Study Plan",
                        "description": "Optimized based on your learning style",
                        "topics": ["Fundamentals", "Intermediate", "Advanced"],
                        "estimated_weeks": 12,
                        "personalized_tips": ["Focus on visual learning", "Practice daily"]
                    })
                }
            }]
        }
        mock_openai.return_value = Mock(**mock_response)

        with patch('app.core.security.decode_token') as mock_decode:
            mock_decode.return_value = {"sub": create_test_user.id, "username": create_test_user.username}
            
            headers = {"Authorization": "Bearer valid_token"}
            
            # Request AI-enhanced plan generation
            response = client.post(
                f"/api/v1/study-plans/generate/{create_test_subject.id}?ai_enhanced=true",
                headers=headers
            )
            
            # Should work even if AI enhancement fails
            assert response.status_code == 200