"""
Diagnostic system tests for the ICFES Leveling backend.
"""
import pytest
from unittest.mock import patch, Mock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import json

from app.models import DiagnosticTest, Question, Subject, Topic, User
from app.services.diagnostic_service import DiagnosticService
from app.services.diagnostic_analytics_service import DiagnosticAnalyticsService
from app.schemas.diagnostic_test import DiagnosticTestCreate, DiagnosticSubmission


@pytest.mark.integration
class TestDiagnosticEndpoints:
    """Test diagnostic system endpoints."""

    def test_get_diagnostic_questions_success(self, client: TestClient, create_test_subject, create_test_topic, db_session: Session):
        """Test getting diagnostic questions for a subject."""
        # Create test questions
        questions = []
        for i in range(15):
            question = Question(
                id=i + 1,
                topic_id=create_test_topic.id,
                subject_id=create_test_subject.id,
                question_text=f"Test question {i + 1}?",
                options={
                    "A": f"Option A {i + 1}",
                    "B": f"Option B {i + 1}",
                    "C": f"Option C {i + 1}",
                    "D": f"Option D {i + 1}"
                },
                correct_answer="A",
                difficulty=(i % 3) + 1,
                question_type="multiple_choice",
                is_active=True
            )
            questions.append(question)
            db_session.add(question)
        
        db_session.commit()

        response = client.get(f"/api/v1/diagnostic/test-questions/{create_test_subject.id}")

        assert response.status_code == 200
        data = response.json()
        assert "questions" in data
        assert len(data["questions"]) == 10  # Default limit
        
        for question in data["questions"]:
            assert "id" in question
            assert "question_text" in question
            assert "options" in question
            assert "difficulty" in question
            assert "correct_answer" not in question  # Should be hidden

    def test_get_diagnostic_questions_nonexistent_subject(self, client: TestClient):
        """Test getting diagnostic questions for non-existent subject."""
        response = client.get("/api/v1/diagnostic/test-questions/9999")

        assert response.status_code == 404

    def test_get_diagnostic_questions_no_questions(self, client: TestClient, create_test_subject):
        """Test getting diagnostic questions when no questions exist."""
        response = client.get(f"/api/v1/diagnostic/test-questions/{create_test_subject.id}")

        assert response.status_code == 200
        data = response.json()
        assert "questions" in data
        assert len(data["questions"]) == 0

    def test_submit_diagnostic_test_success(self, client: TestClient, create_test_user, create_test_subject, create_test_question):
        """Test successful diagnostic test submission."""
        submission_data = {
            "user_id": create_test_user.id,
            "subject_id": create_test_subject.id,
            "answers": [
                {
                    "question_id": create_test_question.id,
                    "selected_answer": "B",
                    "time_taken": 30
                }
            ],
            "total_time": 30
        }

        with patch('app.core.security.decode_token') as mock_decode:
            mock_decode.return_value = {"sub": create_test_user.id, "username": create_test_user.username}
            
            headers = {"Authorization": "Bearer valid_token"}
            response = client.post("/api/v1/diagnostic/submit", json=submission_data, headers=headers)

            assert response.status_code == 200
            data = response.json()
            assert "test_id" in data
            assert "score_percentage" in data
            assert "rank_assigned" in data
            assert "correct_answers" in data
            assert "total_questions" in data

    def test_submit_diagnostic_test_unauthorized(self, client: TestClient, create_test_user, create_test_subject, create_test_question):
        """Test diagnostic test submission without authentication."""
        submission_data = {
            "user_id": create_test_user.id,
            "subject_id": create_test_subject.id,
            "answers": [
                {
                    "question_id": create_test_question.id,
                    "selected_answer": "B",
                    "time_taken": 30
                }
            ],
            "total_time": 30
        }

        response = client.post("/api/v1/diagnostic/submit", json=submission_data)

        assert response.status_code == 401

    def test_submit_diagnostic_test_invalid_data(self, client: TestClient, create_test_user):
        """Test diagnostic test submission with invalid data."""
        submission_data = {
            "user_id": create_test_user.id,
            "subject_id": 9999,  # Non-existent subject
            "answers": [],
            "total_time": 0
        }

        with patch('app.core.security.decode_token') as mock_decode:
            mock_decode.return_value = {"sub": create_test_user.id, "username": create_test_user.username}
            
            headers = {"Authorization": "Bearer valid_token"}
            response = client.post("/api/v1/diagnostic/submit", json=submission_data, headers=headers)

            assert response.status_code in [400, 422]

    def test_get_diagnostic_results_success(self, client: TestClient, create_test_diagnostic, create_test_user):
        """Test getting diagnostic test results."""
        with patch('app.core.security.decode_token') as mock_decode:
            mock_decode.return_value = {"sub": create_test_user.id, "username": create_test_user.username}
            
            headers = {"Authorization": "Bearer valid_token"}
            response = client.get(f"/api/v1/diagnostic/results/{create_test_diagnostic.id}", headers=headers)

            assert response.status_code == 200
            data = response.json()
            assert "id" in data
            assert "score_percentage" in data
            assert "rank_assigned" in data
            assert "created_at" in data

    def test_get_diagnostic_results_unauthorized(self, client: TestClient, create_test_diagnostic):
        """Test getting diagnostic results without authentication."""
        response = client.get(f"/api/v1/diagnostic/results/{create_test_diagnostic.id}")

        assert response.status_code == 401

    def test_get_diagnostic_results_not_found(self, client: TestClient, create_test_user):
        """Test getting results for non-existent diagnostic test."""
        with patch('app.core.security.decode_token') as mock_decode:
            mock_decode.return_value = {"sub": create_test_user.id, "username": create_test_user.username}
            
            headers = {"Authorization": "Bearer valid_token"}
            response = client.get("/api/v1/diagnostic/results/9999", headers=headers)

            assert response.status_code == 404

    def test_get_user_diagnostic_history(self, client: TestClient, create_test_user, create_test_diagnostic):
        """Test getting user's diagnostic test history."""
        with patch('app.core.security.decode_token') as mock_decode:
            mock_decode.return_value = {"sub": create_test_user.id, "username": create_test_user.username}
            
            headers = {"Authorization": "Bearer valid_token"}
            response = client.get(f"/api/v1/diagnostic/user/{create_test_user.id}/history", headers=headers)

            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
            assert len(data) >= 1


@pytest.mark.unit
class TestDiagnosticService:
    """Test diagnostic service functionality."""

    def test_generate_diagnostic_questions(self, db_session: Session, create_test_subject, create_test_topic):
        """Test generating diagnostic questions."""
        # Create questions with different difficulties
        questions = []
        for difficulty in [1, 2, 3]:
            for i in range(5):
                question = Question(
                    id=(difficulty - 1) * 5 + i + 1,
                    topic_id=create_test_topic.id,
                    subject_id=create_test_subject.id,
                    question_text=f"Difficulty {difficulty} question {i + 1}",
                    options={"A": "A", "B": "B", "C": "C", "D": "D"},
                    correct_answer="A",
                    difficulty=difficulty,
                    question_type="multiple_choice",
                    is_active=True
                )
                questions.append(question)
                db_session.add(question)
        
        db_session.commit()

        service = DiagnosticService(db_session)
        selected_questions = service.generate_diagnostic_questions(create_test_subject.id, count=10)

        assert len(selected_questions) == 10
        
        # Check difficulty distribution
        difficulties = [q.difficulty for q in selected_questions]
        assert 1 in difficulties  # Easy questions
        assert 2 in difficulties  # Medium questions
        assert 3 in difficulties  # Hard questions

    def test_calculate_score(self, db_session: Session, create_test_subject, create_test_topic):
        """Test score calculation."""
        # Create test questions
        questions = []
        for i in range(5):
            question = Question(
                id=i + 1,
                topic_id=create_test_topic.id,
                subject_id=create_test_subject.id,
                question_text=f"Test question {i + 1}",
                options={"A": "A", "B": "B", "C": "C", "D": "D"},
                correct_answer="A",
                difficulty=2,
                question_type="multiple_choice",
                is_active=True
            )
            questions.append(question)
            db_session.add(question)
        
        db_session.commit()

        service = DiagnosticService(db_session)
        
        # Test perfect score
        answers = [
            {"question_id": q.id, "selected_answer": "A", "time_taken": 30}
            for q in questions
        ]
        
        score_data = service.calculate_score(answers)
        assert score_data["correct_answers"] == 5
        assert score_data["total_questions"] == 5
        assert score_data["score_percentage"] == 100.0

        # Test partial score
        answers[2]["selected_answer"] = "B"  # Wrong answer
        answers[4]["selected_answer"] = "C"  # Wrong answer
        
        score_data = service.calculate_score(answers)
        assert score_data["correct_answers"] == 3
        assert score_data["score_percentage"] == 60.0

    def test_assign_rank(self, db_session: Session):
        """Test rank assignment based on score."""
        service = DiagnosticService(db_session)

        # Test different score ranges
        assert service.assign_rank(95) == "S"
        assert service.assign_rank(85) == "A"
        assert service.assign_rank(70) == "B"
        assert service.assign_rank(50) == "C"
        assert service.assign_rank(30) == "D"
        assert service.assign_rank(10) == "E"

    def test_create_diagnostic_test(self, db_session: Session, create_test_user, create_test_subject):
        """Test creating diagnostic test record."""
        service = DiagnosticService(db_session)
        
        test_data = {
            "user_id": create_test_user.id,
            "subject_id": create_test_subject.id,
            "score_percentage": 75.0,
            "correct_answers": 8,
            "total_questions": 10,
            "time_taken": 600,
            "rank_assigned": "B"
        }

        diagnostic_test = service.create_diagnostic_test(test_data)

        assert diagnostic_test.id is not None
        assert diagnostic_test.user_id == create_test_user.id
        assert diagnostic_test.subject_id == create_test_subject.id
        assert diagnostic_test.score_percentage == 75.0
        assert diagnostic_test.rank_assigned == "B"

    def test_get_user_diagnostic_history(self, db_session: Session, create_test_user, create_test_diagnostic):
        """Test getting user diagnostic history."""
        service = DiagnosticService(db_session)
        
        history = service.get_user_diagnostic_history(create_test_user.id)

        assert len(history) >= 1
        assert history[0].user_id == create_test_user.id

    def test_update_user_rank(self, db_session: Session, create_test_user):
        """Test updating user rank after diagnostic."""
        service = DiagnosticService(db_session)
        
        original_rank = create_test_user.rank
        service.update_user_rank(create_test_user.id, "A")
        
        db_session.refresh(create_test_user)
        assert create_test_user.rank == "A"
        assert create_test_user.rank != original_rank


@pytest.mark.unit
class TestDiagnosticAnalytics:
    """Test diagnostic analytics functionality."""

    def test_calculate_performance_metrics(self, db_session: Session, create_test_user, create_test_subject):
        """Test calculating performance metrics."""
        # Create multiple diagnostic tests
        tests = []
        for i in range(3):
            test = DiagnosticTest(
                user_id=create_test_user.id,
                subject_id=create_test_subject.id,
                score_percentage=70.0 + (i * 5),  # Improving scores
                correct_answers=7 + i,
                questions_answered=10,
                time_taken=600 - (i * 60),  # Faster times
                rank_assigned=["C", "B", "B"][i],
                status="completed"
            )
            tests.append(test)
            db_session.add(test)
        
        db_session.commit()

        analytics_service = DiagnosticAnalyticsService(db_session)
        metrics = analytics_service.calculate_performance_metrics(create_test_user.id, create_test_subject.id)

        assert "average_score" in metrics
        assert "improvement_trend" in metrics
        assert "average_time" in metrics
        assert "total_tests" in metrics
        assert metrics["total_tests"] == 3

    def test_identify_weak_areas(self, db_session: Session, create_test_user, create_test_subject, create_test_topic):
        """Test identifying weak areas based on diagnostic results."""
        # Create questions for different topics
        questions = []
        for i in range(5):
            question = Question(
                id=i + 1,
                topic_id=create_test_topic.id,
                subject_id=create_test_subject.id,
                question_text=f"Test question {i + 1}",
                options={"A": "A", "B": "B", "C": "C", "D": "D"},
                correct_answer="A",
                difficulty=2,
                question_type="multiple_choice",
                is_active=True
            )
            questions.append(question)
            db_session.add(question)
        
        db_session.commit()

        analytics_service = DiagnosticAnalyticsService(db_session)
        
        # Mock answer data with some wrong answers
        wrong_answers = [
            {"question_id": 1, "selected_answer": "B", "correct_answer": "A"},
            {"question_id": 2, "selected_answer": "C", "correct_answer": "A"},
        ]
        
        weak_areas = analytics_service.identify_weak_areas(wrong_answers)

        assert isinstance(weak_areas, list)
        assert len(weak_areas) > 0

    def test_generate_improvement_suggestions(self, db_session: Session):
        """Test generating improvement suggestions."""
        analytics_service = DiagnosticAnalyticsService(db_session)
        
        performance_data = {
            "score_percentage": 60.0,
            "rank": "C",
            "weak_topics": ["Algebra", "Geometry"],
            "time_efficiency": 0.7
        }
        
        suggestions = analytics_service.generate_improvement_suggestions(performance_data)

        assert isinstance(suggestions, list)
        assert len(suggestions) > 0
        
        for suggestion in suggestions:
            assert "recommendation" in suggestion
            assert "priority" in suggestion

    def test_compare_with_peers(self, db_session: Session, create_test_user, create_test_subject):
        """Test comparing performance with peers."""
        # Create peer users and their diagnostic tests
        peer_users = []
        for i in range(5):
            peer_user = User(
                id=f"peer-user-{i + 1}",
                username=f"peer{i + 1}",
                email=f"peer{i + 1}@example.com",
                password_hash="hash",
                display_name=f"Peer {i + 1}",
                rank=["D", "C", "B", "A", "S"][i],
                is_active=True
            )
            peer_users.append(peer_user)
            db_session.add(peer_user)
        
        db_session.commit()

        # Create diagnostic tests for peers
        for i, peer in enumerate(peer_users):
            test = DiagnosticTest(
                user_id=peer.id,
                subject_id=create_test_subject.id,
                score_percentage=60.0 + (i * 5),
                correct_answers=6 + i,
                questions_answered=10,
                time_taken=600,
                rank_assigned=["D", "C", "B", "A", "S"][i],
                status="completed"
            )
            db_session.add(test)
        
        db_session.commit()

        analytics_service = DiagnosticAnalyticsService(db_session)
        comparison = analytics_service.compare_with_peers(create_test_user.id, create_test_subject.id)

        assert "user_percentile" in comparison
        assert "average_peer_score" in comparison
        assert "rank_distribution" in comparison


@pytest.mark.integration
class TestDiagnosticIntegration:
    """Integration tests for diagnostic system."""

    def test_complete_diagnostic_flow(self, client: TestClient, db_session: Session, create_test_user, create_test_subject, create_test_topic):
        """Test complete diagnostic flow from questions to results."""
        # Create test questions
        questions = []
        for i in range(15):
            question = Question(
                id=i + 1,
                topic_id=create_test_topic.id,
                subject_id=create_test_subject.id,
                question_text=f"Test question {i + 1}?",
                options={
                    "A": f"Option A {i + 1}",
                    "B": f"Option B {i + 1}",
                    "C": f"Option C {i + 1}",
                    "D": f"Option D {i + 1}"
                },
                correct_answer="A",
                difficulty=(i % 3) + 1,
                question_type="multiple_choice",
                is_active=True
            )
            questions.append(question)
            db_session.add(question)
        
        db_session.commit()

        # Step 1: Get diagnostic questions
        response = client.get(f"/api/v1/diagnostic/test-questions/{create_test_subject.id}")
        assert response.status_code == 200
        questions_data = response.json()

        # Step 2: Submit diagnostic test
        answers = []
        for i, question in enumerate(questions_data["questions"]):
            answers.append({
                "question_id": question["id"],
                "selected_answer": "A" if i < 7 else "B",  # 70% correct
                "time_taken": 30
            })

        submission_data = {
            "user_id": create_test_user.id,
            "subject_id": create_test_subject.id,
            "answers": answers,
            "total_time": 300
        }

        with patch('app.core.security.decode_token') as mock_decode:
            mock_decode.return_value = {"sub": create_test_user.id, "username": create_test_user.username}
            
            headers = {"Authorization": "Bearer valid_token"}
            
            submit_response = client.post("/api/v1/diagnostic/submit", json=submission_data, headers=headers)
            assert submit_response.status_code == 200
            
            submit_data = submit_response.json()
            test_id = submit_data["test_id"]

            # Step 3: Get diagnostic results
            results_response = client.get(f"/api/v1/diagnostic/results/{test_id}", headers=headers)
            assert results_response.status_code == 200
            
            results_data = results_response.json()
            assert results_data["score_percentage"] == 70.0
            assert results_data["rank_assigned"] == "B"

    def test_multiple_subject_diagnostics(self, client: TestClient, db_session: Session, create_test_user):
        """Test taking diagnostics for multiple subjects."""
        # Create multiple subjects
        subjects = []
        for i in range(3):
            subject = Subject(
                id=i + 1,
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

            # Take diagnostic for each subject
            for subject in subjects:
                response = client.get(f"/api/v1/diagnostic/test-questions/{subject.id}")
                
                # Should handle gracefully even with no questions
                assert response.status_code in [200, 404]

    def test_diagnostic_performance_tracking(self, client: TestClient, db_session: Session, create_test_user, create_test_subject, create_test_question):
        """Test tracking diagnostic performance over time."""
        with patch('app.core.security.decode_token') as mock_decode:
            mock_decode.return_value = {"sub": create_test_user.id, "username": create_test_user.username}
            
            headers = {"Authorization": "Bearer valid_token"}

            # Take multiple diagnostic tests
            for score in [60, 70, 80]:  # Improving scores
                submission_data = {
                    "user_id": create_test_user.id,
                    "subject_id": create_test_subject.id,
                    "answers": [
                        {
                            "question_id": create_test_question.id,
                            "selected_answer": "B",  # Correct answer from fixture
                            "time_taken": 30
                        }
                    ],
                    "total_time": 30
                }

                response = client.post("/api/v1/diagnostic/submit", json=submission_data, headers=headers)
                assert response.status_code == 200

            # Get diagnostic history
            history_response = client.get(f"/api/v1/diagnostic/user/{create_test_user.id}/history", headers=headers)
            assert history_response.status_code == 200
            
            history_data = history_response.json()
            assert len(history_data) == 3