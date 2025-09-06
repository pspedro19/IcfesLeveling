"""
Test Session Management Service
Handles advanced session management for diagnostic tests including state persistence,
automatic recovery, and real-time session tracking
"""
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import logging
import json
import uuid
from dataclasses import dataclass, asdict
from enum import Enum

from ..models.diagnostic_test import DiagnosticTest, DiagnosticTestAnswer
from ..models.user import User
from ..models.question import Question, Topic
from ..models.subject import Subject

logger = logging.getLogger(__name__)

class SessionStatus(Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    EXPIRED = "expired"
    COMPLETED = "completed"
    ABANDONED = "abandoned"

@dataclass
class SessionState:
    """Represents the current state of a test session"""
    session_id: str
    test_id: str
    user_id: str
    current_question_index: int
    questions_data: List[Dict[str, Any]]
    answered_questions: Dict[str, str]  # question_id -> answer
    response_times: Dict[str, int]  # question_id -> response_time_ms
    session_start_time: datetime
    last_activity_time: datetime
    time_remaining_seconds: int
    status: SessionStatus
    adaptive_params: Dict[str, Any]
    metadata: Dict[str, Any]

class TestSessionManager:
    """
    Manages diagnostic test sessions with advanced features like automatic save,
    recovery, and real-time state tracking
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.logger = logger
        
        # Session configuration
        self.SESSION_TIMEOUT_MINUTES = 30  # Session expires after 30 minutes of inactivity
        self.AUTO_SAVE_INTERVAL_SECONDS = 30  # Auto-save every 30 seconds
        self.MAX_SESSION_DURATION_HOURS = 3  # Maximum session duration
        
        # Recovery configuration
        self.RECOVERY_WINDOW_HOURS = 24  # Can recover sessions within 24 hours
        self.MAX_RECOVERY_ATTEMPTS = 3
        
        # Active sessions cache (in production, use Redis)
        self._active_sessions: Dict[str, SessionState] = {}

    def create_test_session(self, test_id: str, user_id: str, 
                           questions: List[Dict[str, Any]], 
                           time_limit_minutes: int = 90,
                           adaptive_mode: bool = True) -> SessionState:
        """
        Create a new test session with full state management
        """
        session_id = str(uuid.uuid4())
        
        # Initialize adaptive parameters
        adaptive_params = {
            "enabled": adaptive_mode,
            "current_theta": 0.0,
            "confidence_interval": (-1.0, 1.0),
            "adaptation_history": [],
            "difficulty_progression": []
        } if adaptive_mode else {}
        
        # Create session state
        session_state = SessionState(
            session_id=session_id,
            test_id=test_id,
            user_id=user_id,
            current_question_index=0,
            questions_data=questions,
            answered_questions={},
            response_times={},
            session_start_time=datetime.utcnow(),
            last_activity_time=datetime.utcnow(),
            time_remaining_seconds=time_limit_minutes * 60,
            status=SessionStatus.ACTIVE,
            adaptive_params=adaptive_params,
            metadata={
                "total_questions": len(questions),
                "time_limit_minutes": time_limit_minutes,
                "browser_info": None,
                "recovery_attempts": 0,
                "auto_save_count": 0
            }
        )
        
        # Store in active sessions cache
        self._active_sessions[session_id] = session_state
        
        # Persist initial state to database
        self._persist_session_state(session_state)
        
        self.logger.info(f"Created test session {session_id} for user {user_id}, test {test_id}")
        return session_state

    def get_session_state(self, session_id: str, user_id: str) -> Optional[SessionState]:
        """
        Get current session state with automatic recovery if needed
        """
        # Check active sessions cache first
        if session_id in self._active_sessions:
            session = self._active_sessions[session_id]
            if session.user_id == user_id:
                # Update last activity
                session.last_activity_time = datetime.utcnow()
                self._check_session_timeout(session)
                return session
        
        # Try to recover from database
        recovered_session = self._recover_session_from_db(session_id, user_id)
        if recovered_session:
            self._active_sessions[session_id] = recovered_session
            return recovered_session
        
        return None

    def update_session_progress(self, session_id: str, user_id: str,
                              question_id: str, user_answer: str,
                              response_time_ms: int,
                              additional_data: Optional[Dict[str, Any]] = None) -> SessionState:
        """
        Update session progress with answer submission
        """
        session = self.get_session_state(session_id, user_id)
        if not session:
            raise ValueError("Session not found or expired")
        
        if session.status != SessionStatus.ACTIVE:
            raise ValueError(f"Session is not active: {session.status}")
        
        # Record the answer
        session.answered_questions[question_id] = user_answer
        session.response_times[question_id] = response_time_ms
        session.last_activity_time = datetime.utcnow()
        
        # Update adaptive parameters if enabled
        if session.adaptive_params.get("enabled"):
            self._update_adaptive_state(session, question_id, user_answer, response_time_ms)
        
        # Update metadata
        if additional_data:
            session.metadata.update(additional_data)
        
        # Auto-advance question index if this was the current question
        current_question = session.questions_data[session.current_question_index]
        if current_question["id"] == question_id:
            session.current_question_index = min(
                session.current_question_index + 1,
                len(session.questions_data) - 1
            )
        
        # Check if test is complete
        if len(session.answered_questions) >= len(session.questions_data):
            session.status = SessionStatus.COMPLETED
            self._finalize_session(session)
        
        # Auto-save progress
        self._auto_save_session(session)
        
        self.logger.info(f"Updated session {session_id}: answered {len(session.answered_questions)}/{len(session.questions_data)}")
        return session

    def pause_session(self, session_id: str, user_id: str) -> SessionState:
        """
        Pause an active session
        """
        session = self.get_session_state(session_id, user_id)
        if not session:
            raise ValueError("Session not found")
        
        if session.status == SessionStatus.ACTIVE:
            session.status = SessionStatus.PAUSED
            session.last_activity_time = datetime.utcnow()
            
            # Calculate remaining time
            elapsed_time = (datetime.utcnow() - session.session_start_time).total_seconds()
            session.time_remaining_seconds = max(0, session.time_remaining_seconds - int(elapsed_time))
            
            self._persist_session_state(session)
            self.logger.info(f"Paused session {session_id}")
        
        return session

    def resume_session(self, session_id: str, user_id: str) -> SessionState:
        """
        Resume a paused session
        """
        session = self.get_session_state(session_id, user_id)
        if not session:
            raise ValueError("Session not found")
        
        if session.status == SessionStatus.PAUSED:
            # Check if session has expired
            if self._is_session_expired(session):
                session.status = SessionStatus.EXPIRED
                self._persist_session_state(session)
                raise ValueError("Session has expired")
            
            session.status = SessionStatus.ACTIVE
            session.last_activity_time = datetime.utcnow()
            self._persist_session_state(session)
            self.logger.info(f"Resumed session {session_id}")
        
        return session

    def abandon_session(self, session_id: str, user_id: str, 
                       save_progress: bool = True) -> SessionState:
        """
        Mark session as abandoned and optionally save progress
        """
        session = self.get_session_state(session_id, user_id)
        if not session:
            raise ValueError("Session not found")
        
        session.status = SessionStatus.ABANDONED
        session.last_activity_time = datetime.utcnow()
        
        if save_progress:
            self._persist_session_state(session)
            self.logger.info(f"Abandoned session {session_id} with progress saved")
        else:
            # Remove from active sessions but don't persist
            if session_id in self._active_sessions:
                del self._active_sessions[session_id]
            self.logger.info(f"Abandoned session {session_id} without saving")
        
        return session

    def get_recoverable_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get list of sessions that can be recovered for a user
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=self.RECOVERY_WINDOW_HOURS)
        
        # Query from diagnostic tests with incomplete status
        incomplete_tests = self.db.query(DiagnosticTest).filter(
            and_(
                DiagnosticTest.user_id == user_id,
                DiagnosticTest.status == "in_progress",
                DiagnosticTest.started_at >= cutoff_time
            )
        ).all()
        
        recoverable_sessions = []
        
        for test in incomplete_tests:
            session_data = test.score_by_topic.get("session_state")
            if session_data:
                # Check recovery eligibility
                recovery_attempts = session_data.get("metadata", {}).get("recovery_attempts", 0)
                if recovery_attempts < self.MAX_RECOVERY_ATTEMPTS:
                    recoverable_sessions.append({
                        "session_id": session_data.get("session_id"),
                        "test_id": str(test.id),
                        "subject": test.subject.name if test.subject else "Unknown",
                        "progress": f"{len(session_data.get('answered_questions', {}))} / {session_data.get('metadata', {}).get('total_questions', 0)}",
                        "last_activity": session_data.get("last_activity_time"),
                        "time_remaining": session_data.get("time_remaining_seconds", 0),
                        "can_recover": True
                    })
        
        return recoverable_sessions

    def recover_session(self, session_id: str, user_id: str) -> SessionState:
        """
        Recover a previously abandoned or interrupted session
        """
        recovered_session = self._recover_session_from_db(session_id, user_id)
        
        if not recovered_session:
            raise ValueError("Session cannot be recovered")
        
        # Check recovery eligibility
        if recovered_session.metadata.get("recovery_attempts", 0) >= self.MAX_RECOVERY_ATTEMPTS:
            raise ValueError("Maximum recovery attempts exceeded")
        
        if self._is_session_expired(recovered_session):
            raise ValueError("Session has expired and cannot be recovered")
        
        # Update recovery metadata
        recovered_session.metadata["recovery_attempts"] = recovered_session.metadata.get("recovery_attempts", 0) + 1
        recovered_session.metadata["last_recovery"] = datetime.utcnow().isoformat()
        recovered_session.status = SessionStatus.ACTIVE
        recovered_session.last_activity_time = datetime.utcnow()
        
        # Add to active sessions
        self._active_sessions[session_id] = recovered_session
        self._persist_session_state(recovered_session)
        
        self.logger.info(f"Recovered session {session_id} (attempt {recovered_session.metadata['recovery_attempts']})")
        return recovered_session

    def get_session_analytics(self, session_id: str, user_id: str) -> Dict[str, Any]:
        """
        Get detailed analytics for a session
        """
        session = self.get_session_state(session_id, user_id)
        if not session:
            raise ValueError("Session not found")
        
        # Calculate progress metrics
        total_questions = len(session.questions_data)
        answered_questions = len(session.answered_questions)
        progress_percentage = (answered_questions / total_questions * 100) if total_questions > 0 else 0
        
        # Calculate time metrics
        elapsed_time = (session.last_activity_time - session.session_start_time).total_seconds()
        avg_time_per_question = elapsed_time / answered_questions if answered_questions > 0 else 0
        
        # Calculate accuracy if we have correct answers
        correct_count = 0
        for question_id, user_answer in session.answered_questions.items():
            question = next((q for q in session.questions_data if q["id"] == question_id), None)
            if question and question.get("correct_answer") == user_answer:
                correct_count += 1
        
        accuracy = (correct_count / answered_questions * 100) if answered_questions > 0 else 0
        
        # Response time analysis
        response_times = list(session.response_times.values())
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        return {
            "session_id": session_id,
            "status": session.status.value,
            "progress": {
                "answered": answered_questions,
                "total": total_questions,
                "percentage": progress_percentage,
                "current_question": session.current_question_index + 1
            },
            "timing": {
                "elapsed_seconds": elapsed_time,
                "remaining_seconds": session.time_remaining_seconds,
                "avg_time_per_question": avg_time_per_question,
                "avg_response_time_ms": avg_response_time
            },
            "performance": {
                "accuracy_percentage": accuracy,
                "correct_answers": correct_count,
                "adaptive_theta": session.adaptive_params.get("current_theta", 0.0) if session.adaptive_params else None
            },
            "session_health": {
                "auto_saves": session.metadata.get("auto_save_count", 0),
                "recovery_attempts": session.metadata.get("recovery_attempts", 0),
                "last_activity": session.last_activity_time.isoformat(),
                "is_healthy": self._assess_session_health(session)
            }
        }

    def cleanup_expired_sessions(self) -> int:
        """
        Clean up expired sessions from memory and database
        """
        cleanup_count = 0
        expired_sessions = []
        
        # Find expired sessions in memory
        for session_id, session in self._active_sessions.items():
            if self._is_session_expired(session) or session.status in [SessionStatus.COMPLETED, SessionStatus.ABANDONED]:
                expired_sessions.append(session_id)
        
        # Remove from memory
        for session_id in expired_sessions:
            session = self._active_sessions.pop(session_id, None)
            if session:
                if session.status == SessionStatus.ACTIVE:
                    session.status = SessionStatus.EXPIRED
                    self._persist_session_state(session)
                cleanup_count += 1
        
        # Clean up old database records
        cutoff_time = datetime.utcnow() - timedelta(hours=self.RECOVERY_WINDOW_HOURS * 2)
        old_tests = self.db.query(DiagnosticTest).filter(
            and_(
                DiagnosticTest.status == "in_progress",
                DiagnosticTest.started_at < cutoff_time
            )
        ).all()
        
        for test in old_tests:
            session_data = test.score_by_topic.get("session_state")
            if session_data:
                # Mark as expired in database
                session_data["status"] = SessionStatus.EXPIRED.value
                test.score_by_topic["session_state"] = session_data
                cleanup_count += 1
        
        if old_tests:
            self.db.commit()
        
        self.logger.info(f"Cleaned up {cleanup_count} expired sessions")
        return cleanup_count

    # Private helper methods
    
    def _persist_session_state(self, session: SessionState):
        """
        Persist session state to database
        """
        test = self.db.query(DiagnosticTest).filter(DiagnosticTest.id == session.test_id).first()
        if not test:
            raise ValueError("Test not found for session persistence")
        
        # Convert session to serializable format
        session_data = {
            "session_id": session.session_id,
            "user_id": session.user_id,
            "current_question_index": session.current_question_index,
            "answered_questions": session.answered_questions,
            "response_times": session.response_times,
            "session_start_time": session.session_start_time.isoformat(),
            "last_activity_time": session.last_activity_time.isoformat(),
            "time_remaining_seconds": session.time_remaining_seconds,
            "status": session.status.value,
            "adaptive_params": session.adaptive_params,
            "metadata": session.metadata
        }
        
        # Store in test's score_by_topic field
        if not test.score_by_topic:
            test.score_by_topic = {}
        test.score_by_topic["session_state"] = session_data
        
        # Update auto-save counter
        session.metadata["auto_save_count"] = session.metadata.get("auto_save_count", 0) + 1
        
        self.db.commit()

    def _recover_session_from_db(self, session_id: str, user_id: str) -> Optional[SessionState]:
        """
        Recover session state from database
        """
        # Find test with matching session
        tests = self.db.query(DiagnosticTest).filter(
            DiagnosticTest.user_id == user_id,
            DiagnosticTest.status == "in_progress"
        ).all()
        
        for test in tests:
            session_data = test.score_by_topic.get("session_state")
            if session_data and session_data.get("session_id") == session_id:
                try:
                    # Reconstruct session state
                    return SessionState(
                        session_id=session_data["session_id"],
                        test_id=str(test.id),
                        user_id=session_data["user_id"],
                        current_question_index=session_data["current_question_index"],
                        questions_data=test.score_by_topic.get("questions_data", []),
                        answered_questions=session_data["answered_questions"],
                        response_times=session_data["response_times"],
                        session_start_time=datetime.fromisoformat(session_data["session_start_time"]),
                        last_activity_time=datetime.fromisoformat(session_data["last_activity_time"]),
                        time_remaining_seconds=session_data["time_remaining_seconds"],
                        status=SessionStatus(session_data["status"]),
                        adaptive_params=session_data["adaptive_params"],
                        metadata=session_data["metadata"]
                    )
                except (KeyError, ValueError) as e:
                    self.logger.error(f"Error recovering session {session_id}: {e}")
                    continue
        
        return None

    def _update_adaptive_state(self, session: SessionState, question_id: str, 
                             user_answer: str, response_time_ms: int):
        """
        Update adaptive parameters based on answer
        """
        # Find the question in the questions data
        question_data = next((q for q in session.questions_data if q["id"] == question_id), None)
        if not question_data:
            return
        
        is_correct = user_answer == question_data.get("correct_answer", "")
        difficulty = question_data.get("difficulty", 5)
        
        # Simple adaptive algorithm (can be enhanced with IRT)
        current_theta = session.adaptive_params["current_theta"]
        
        if is_correct:
            theta_change = 0.1 * (difficulty - 5) / 5  # Positive for hard questions
        else:
            theta_change = -0.1 * (difficulty - 5) / 5  # Negative for easy questions
        
        # Consider response time
        if response_time_ms < 30000:  # Fast response
            theta_change *= 1.2
        elif response_time_ms > 90000:  # Slow response
            theta_change *= 0.8
        
        new_theta = max(-3, min(3, current_theta + theta_change))
        
        # Update adaptive parameters
        session.adaptive_params["current_theta"] = new_theta
        session.adaptive_params["adaptation_history"].append({
            "question_id": question_id,
            "correct": is_correct,
            "theta_before": current_theta,
            "theta_after": new_theta,
            "response_time": response_time_ms,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Update difficulty progression
        session.adaptive_params["difficulty_progression"].append(difficulty)
        
        # Update confidence interval (simplified)
        n_responses = len(session.adaptive_params["adaptation_history"])
        se = 1.0 / max(1, n_responses ** 0.5)
        margin = 1.96 * se
        session.adaptive_params["confidence_interval"] = (new_theta - margin, new_theta + margin)

    def _check_session_timeout(self, session: SessionState):
        """
        Check if session has timed out and update status if needed
        """
        if session.status != SessionStatus.ACTIVE:
            return
        
        time_since_activity = datetime.utcnow() - session.last_activity_time
        if time_since_activity > timedelta(minutes=self.SESSION_TIMEOUT_MINUTES):
            session.status = SessionStatus.EXPIRED
            self.logger.info(f"Session {session.session_id} expired due to inactivity")

    def _is_session_expired(self, session: SessionState) -> bool:
        """
        Check if a session has expired
        """
        # Check inactivity timeout
        time_since_activity = datetime.utcnow() - session.last_activity_time
        if time_since_activity > timedelta(minutes=self.SESSION_TIMEOUT_MINUTES):
            return True
        
        # Check maximum session duration
        total_duration = datetime.utcnow() - session.session_start_time
        if total_duration > timedelta(hours=self.MAX_SESSION_DURATION_HOURS):
            return True
        
        # Check if time remaining has expired
        if session.time_remaining_seconds <= 0:
            return True
        
        return False

    def _auto_save_session(self, session: SessionState):
        """
        Auto-save session if enough time has passed
        """
        last_save_count = session.metadata.get("auto_save_count", 0)
        time_since_start = (datetime.utcnow() - session.session_start_time).total_seconds()
        
        # Auto-save every interval or if significant progress made
        if (time_since_start > last_save_count * self.AUTO_SAVE_INTERVAL_SECONDS or
            len(session.answered_questions) % 5 == 0):  # Every 5 questions
            self._persist_session_state(session)

    def _finalize_session(self, session: SessionState):
        """
        Finalize a completed session
        """
        session.status = SessionStatus.COMPLETED
        session.last_activity_time = datetime.utcnow()
        
        # Calculate final metrics
        total_time = (session.last_activity_time - session.session_start_time).total_seconds()
        session.metadata["completion_time_seconds"] = total_time
        session.metadata["final_question_count"] = len(session.answered_questions)
        
        # Persist final state
        self._persist_session_state(session)
        
        # Remove from active sessions
        if session.session_id in self._active_sessions:
            del self._active_sessions[session.session_id]
        
        self.logger.info(f"Finalized session {session.session_id} with {len(session.answered_questions)} answers")

    def _assess_session_health(self, session: SessionState) -> bool:
        """
        Assess the health of a session
        """
        # Check for signs of healthy session
        healthy_indicators = 0
        
        # Regular activity
        time_since_activity = (datetime.utcnow() - session.last_activity_time).total_seconds()
        if time_since_activity < 300:  # Active within 5 minutes
            healthy_indicators += 1
        
        # Reasonable progress
        if session.current_question_index > 0:
            healthy_indicators += 1
        
        # Consistent response times
        response_times = list(session.response_times.values())
        if response_times:
            avg_time = sum(response_times) / len(response_times)
            if 10000 <= avg_time <= 120000:  # Between 10s and 2m
                healthy_indicators += 1
        
        # Regular saves
        if session.metadata.get("auto_save_count", 0) > 0:
            healthy_indicators += 1
        
        return healthy_indicators >= 2