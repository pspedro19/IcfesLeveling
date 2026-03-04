"""
Service for the Two-Phase Diagnostic System
ICFES Leveling Backend

Enhanced with IRT (Item Response Theory) integration for:
- True adaptive question selection using Fisher information function
- Maximum Likelihood Estimation (MLE) for theta calculation
- Real-time theta updates during test-taking
- Subject-specific ability estimation
"""

import logging
import math
from datetime import datetime
from typing import List, Optional, Tuple, Dict, Any
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from ..models.user import User
from ..models.subject import Subject
from ..models.question import Question
from ..models.topic import Topic
from ..models.diagnostic_two_phase import (
    TwoPhaseDignostic,
    TwoPhaseDiagnosticAnswer,
    UserEngagement,
    TopicMastery,
)
from ..schemas.diagnostic import (
    DiagnosticAnswerInput,
    WeakArea,
    WeakAreaPriority,
    SkillTreeItem,
    SkillStatus,
)
from .irt_calculation_service import IRTCalculationService

logger = logging.getLogger(__name__)


# =============================================================================
# LEGACY HELPER FUNCTIONS (kept for backward compatibility)
# =============================================================================

def _calculate_initial_theta(correct: int, total: int) -> float:
    """Legacy simple theta calculation - kept for fallback"""
    if total == 0:
        return 0.0
    p = max(0.05, min(0.95, correct / total))
    theta = math.log(p / (1 - p))
    return max(-3.0, min(3.0, theta))

def _theta_to_rank(theta: float) -> str:
    if theta < -1.5: return "E"
    if theta < -0.5: return "D"
    if theta < 0.5: return "C"
    if theta < 1.0: return "B"
    if theta < 1.5: return "A"
    return "S"

def _determine_priority(score: float) -> WeakAreaPriority:
    if score < 0.4: return WeakAreaPriority.HIGH
    if score < 0.6: return WeakAreaPriority.MEDIUM
    return WeakAreaPriority.LOW

def _determine_skill_status(mastery_score: float) -> SkillStatus:
    if mastery_score < 0.4: return SkillStatus.WEAK
    if mastery_score < 0.7: return SkillStatus.LEARNING
    return SkillStatus.STRONG

def _questions_to_unlock(mastery_score: float) -> int:
    if mastery_score >= 0.7: return 0
    if mastery_score >= 0.4: return 5
    return 10


class DiagnosticTwoPhaseService:
    def __init__(self, db: Session):
        self.db = db

    async def get_or_create_engagement(self, user_id: UUID) -> UserEngagement:
        engagement = self.db.query(UserEngagement).filter(UserEngagement.user_id == user_id).first()
        if not engagement:
            engagement = UserEngagement(user_id=user_id)
            self.db.add(engagement)
            self.db.commit()
            self.db.refresh(engagement)
        return engagement

    def start_quick_diagnostic(self, user_id: UUID) -> TwoPhaseDignostic:
        existing = self.db.query(TwoPhaseDignostic).filter(
            TwoPhaseDignostic.user_id == user_id,
            TwoPhaseDignostic.diagnostic_type == "quick",
            TwoPhaseDignostic.status == "completed"
        ).first()
        if existing:
            raise ValueError("DIAGNOSTIC_COMPLETED")

        in_progress = self.db.query(TwoPhaseDignostic).filter(
            TwoPhaseDignostic.user_id == user_id,
            TwoPhaseDignostic.diagnostic_type == "quick",
            TwoPhaseDignostic.status == "in_progress"
        ).first()
        if in_progress:
            return in_progress

        subjects = self.db.query(Subject).all()
        if len(subjects) < 5:
            raise RuntimeError("Not enough subjects in database for quick diagnostic")
        
        diagnostic = TwoPhaseDignostic(
            user_id=user_id,
            diagnostic_type="quick",
            status="in_progress"
        )
        self.db.add(diagnostic)
        self.db.commit()
        self.db.refresh(diagnostic)
        return diagnostic

    def get_quick_diagnostic_questions(self, diagnostic: TwoPhaseDignostic) -> List[Question]:
        """
        Get questions for quick diagnostic with proper difficulty distribution.

        Per README_NEGOCIO.md spec: 1 easy + 1 medium + 1 hard per subject (15 total).
        Difficulty levels:
        - Easy: difficulty 1-3
        - Medium: difficulty 4-6
        - Hard: difficulty 7-10
        """
        subjects = self.db.query(Subject).all()
        questions = []

        for subject in subjects[:5]:
            # Get 1 EASY question (difficulty 1-3)
            easy_q = self.db.query(Question).filter(
                Question.subject_id == subject.id,
                Question.difficulty <= 3
            ).order_by(func.random()).first()

            # Get 1 MEDIUM question (difficulty 4-6)
            medium_q = self.db.query(Question).filter(
                Question.subject_id == subject.id,
                Question.difficulty >= 4,
                Question.difficulty <= 6
            ).order_by(func.random()).first()

            # Get 1 HARD question (difficulty 7-10)
            hard_q = self.db.query(Question).filter(
                Question.subject_id == subject.id,
                Question.difficulty >= 7
            ).order_by(func.random()).first()

            # Add questions (with fallback if specific difficulty not available)
            subject_questions = []
            if easy_q:
                subject_questions.append(easy_q)
            if medium_q:
                subject_questions.append(medium_q)
            if hard_q:
                subject_questions.append(hard_q)

            # If we don't have all 3 difficulties, fill with random questions
            if len(subject_questions) < 3:
                needed = 3 - len(subject_questions)
                existing_ids = [q.id for q in subject_questions]
                fallback = self.db.query(Question).filter(
                    Question.subject_id == subject.id,
                    ~Question.id.in_(existing_ids)
                ).order_by(func.random()).limit(needed).all()
                subject_questions.extend(fallback)

            questions.extend(subject_questions)

        diagnostic.total_questions = len(questions)
        self.db.commit()
        return questions

    def submit_quick_diagnostic(self, user_id: UUID, diagnostic_id: UUID, answers: List[DiagnosticAnswerInput]) -> dict:
        diagnostic = self.db.query(TwoPhaseDignostic).filter(
            TwoPhaseDignostic.id == diagnostic_id,
            TwoPhaseDignostic.user_id == user_id,
            TwoPhaseDignostic.diagnostic_type == "quick"
        ).first()

        if not diagnostic:
            raise ValueError("DIAGNOSTIC_NOT_FOUND")
        if diagnostic.status == "completed":
            raise ValueError("DIAGNOSTIC_COMPLETED")

        correct_count = 0
        total_time = 0
        subject_scores = {}

        for answer in answers:
            question = self.db.query(Question).filter(Question.id == answer.question_id).first()
            if not question: continue

            is_correct = answer.answer_id.upper() == (question.respuesta_correcta or "").upper()
            total_time += answer.time_spent_seconds
            if is_correct: correct_count += 1

            subject_id = str(question.subject_id)
            if subject_id not in subject_scores:
                subject_scores[subject_id] = {"correct": 0, "total": 0, "subject": question.subject}
            subject_scores[subject_id]["total"] += 1
            if is_correct: subject_scores[subject_id]["correct"] += 1
            
            db_answer = TwoPhaseDiagnosticAnswer(
                diagnostic_id=diagnostic.id, question_id=question.id, answer_id=answer.answer_id.upper(),
                was_correct=is_correct, time_spent_seconds=answer.time_spent_seconds
            )
            self.db.add(db_answer)

        theta = _calculate_initial_theta(correct_count, len(answers))
        rank = _theta_to_rank(theta)
        
        weak_areas = []
        for subject_id, scores in subject_scores.items():
            if scores["total"] > 0:
                score = scores["correct"] / scores["total"]
                if score < 0.7:
                    weak_areas.append(WeakArea(
                        subject_id=UUID(subject_id), subject_name=scores["subject"].name,
                        score=round(score, 2), priority=_determine_priority(score)
                    ))
        weak_areas.sort(key=lambda x: (0 if x.priority == WeakAreaPriority.HIGH else 1 if x.priority == WeakAreaPriority.MEDIUM else 2))

        diagnostic.completed_at = datetime.utcnow()
        diagnostic.correct_answers = correct_count
        diagnostic.time_spent_seconds = total_time
        diagnostic.theta_estimate = theta
        diagnostic.status = "completed"
        diagnostic.weak_areas = [w.model_dump() for w in weak_areas]

        user = self.db.query(User).filter(User.id == user_id).first()
        user.rank = rank
        
        # This part is tricky because of the async call in the original code.
        # For a service, we should avoid async calls if the service is synchronous.
        # Let's assume get_or_create_engagement is synchronous for now.
        engagement = self.db.query(UserEngagement).filter(UserEngagement.user_id == user_id).first()
        if not engagement:
            engagement = UserEngagement(user_id=user_id)
            self.db.add(engagement)
        engagement.quick_diagnostic_completed = True

        self.db.commit()

        return {
            "completed": True, "correct": correct_count, "total": len(answers),
            "rank": rank, "theta": theta, "weak_areas": weak_areas
        }

    def start_deep_diagnostic(self, user_id: UUID, subject_id: UUID) -> TwoPhaseDignostic:
        subject = self.db.query(Subject).filter(Subject.id == subject_id).first()
        if not subject: raise ValueError("SUBJECT_NOT_FOUND")

        existing = self.db.query(TwoPhaseDignostic).filter_by(
            user_id=user_id, diagnostic_type="deep", subject_id=subject_id, status="completed"
        ).first()
        if existing: raise ValueError("DIAGNOSTIC_COMPLETED")

        in_progress = self.db.query(TwoPhaseDignostic).filter_by(
            user_id=user_id, diagnostic_type="deep", subject_id=subject_id, status="in_progress"
        ).first()
        if in_progress: return in_progress

        diagnostic = TwoPhaseDignostic(
            user_id=user_id, diagnostic_type="deep", subject_id=subject_id, status="in_progress"
        )
        self.db.add(diagnostic)
        self.db.commit()
        self.db.refresh(diagnostic)
        return diagnostic

    def get_deep_diagnostic_questions(self, diagnostic: TwoPhaseDignostic) -> List[Question]:
        questions = self.db.query(Question).filter(
            Question.subject_id == diagnostic.subject_id
        ).order_by(Question.difficulty, func.random()).limit(20).all()
        if len(questions) < 5: raise RuntimeError("Not enough questions for this subject")
        diagnostic.total_questions = len(questions)
        self.db.commit()
        return questions

    def submit_deep_diagnostic(self, user_id: UUID, diagnostic_id: UUID, answers: List[DiagnosticAnswerInput]) -> dict:
        diagnostic = self.db.query(TwoPhaseDignostic).filter_by(id=diagnostic_id, user_id=user_id, diagnostic_type="deep").first()
        if not diagnostic: raise ValueError("DIAGNOSTIC_NOT_FOUND")
        if diagnostic.status == "completed": raise ValueError("DIAGNOSTIC_COMPLETED")

        correct_count = 0
        total_time = 0
        topic_scores = {}

        for answer in answers:
            question = self.db.query(Question).filter_by(id=answer.question_id).first()
            if not question: continue

            is_correct = answer.answer_id.upper() == (question.respuesta_correcta or "").upper()
            total_time += answer.time_spent_seconds
            if is_correct: correct_count += 1
            
            if question.topic_id:
                topic_id = str(question.topic_id)
                if topic_id not in topic_scores:
                    topic_scores[topic_id] = {"correct": 0, "total": 0, "topic": question.topic}
                topic_scores[topic_id]["total"] += 1
                if is_correct: topic_scores[topic_id]["correct"] += 1

            db_answer = TwoPhaseDiagnosticAnswer(
                diagnostic_id=diagnostic.id, question_id=question.id, answer_id=answer.answer_id.upper(),
                was_correct=is_correct, time_spent_seconds=answer.time_spent_seconds
            )
            self.db.add(db_answer)

        skill_tree = []
        for topic_id, scores in topic_scores.items():
            if scores["total"] > 0 and scores["topic"]:
                mastery_score = scores["correct"] / scores["total"]
                topic_mastery = self.db.query(TopicMastery).filter_by(user_id=user_id, topic_id=UUID(topic_id)).first()
                if topic_mastery:
                    topic_mastery.mastery_score = mastery_score
                    topic_mastery.questions_seen += scores["total"]
                    topic_mastery.questions_correct += scores["correct"]
                    topic_mastery.last_practiced_at = datetime.utcnow()
                else:
                    topic_mastery = TopicMastery(
                        user_id=user_id, topic_id=UUID(topic_id), mastery_score=mastery_score,
                        questions_seen=scores["total"], questions_correct=scores["correct"],
                        last_practiced_at=datetime.utcnow()
                    )
                    self.db.add(topic_mastery)
                
                skill_tree.append(SkillTreeItem(
                    topic_id=UUID(topic_id), topic_name=scores["topic"].name, mastery_score=round(mastery_score, 2),
                    status=_determine_skill_status(mastery_score), questions_to_unlock=_questions_to_unlock(mastery_score)
                ))
        skill_tree.sort(key=lambda x: x.mastery_score)

        diagnostic.completed_at = datetime.utcnow()
        diagnostic.correct_answers = correct_count
        diagnostic.time_spent_seconds = total_time
        diagnostic.status = "completed"
        diagnostic.skill_tree = [s.model_dump() for s in skill_tree]
        self.db.commit()

        return {
            "completed": True, "subject_id": diagnostic.subject_id,
            "correct": correct_count, "total": len(answers), "skill_tree": skill_tree
        }

    # =========================================================================
    # IRT-ENHANCED ADAPTIVE TESTING METHODS
    # =========================================================================

    def _get_irt_service(self) -> IRTCalculationService:
        """Get or create IRT calculation service instance"""
        if not hasattr(self, '_irt_service'):
            self._irt_service = IRTCalculationService(self.db)
        return self._irt_service

    def calculate_theta_irt(self, responses: List[Dict]) -> Tuple[float, float, bool]:
        """
        Calculate theta using IRT 3PL model with Maximum Likelihood Estimation

        Args:
            responses: List of dicts with keys:
                - question_id: UUID of the question
                - is_correct: bool indicating if answer was correct

        Returns:
            Tuple of (theta, standard_error, converged)
        """
        irt_service = self._get_irt_service()

        # Build response tuples for IRT calculation (is_correct, a, b, c)
        irt_responses = []
        for response in responses:
            question = self.db.query(Question).filter(
                Question.id == response['question_id']
            ).first()

            if question:
                # Get IRT parameters with defaults
                a = question.parametro_irt_a if question.parametro_irt_a is not None else 1.0
                b = question.parametro_irt_b if question.parametro_irt_b is not None else 0.0
                c = question.parametro_irt_c if question.parametro_irt_c is not None else 0.25

                irt_responses.append((
                    response['is_correct'],
                    a, b, c
                ))

        if not irt_responses:
            return 0.0, 1.0, False

        # Use MLE estimation from IRT service
        theta, se, converged = irt_service.estimate_theta_mle(irt_responses)

        logger.info(f"IRT theta calculation: theta={theta:.3f}, SE={se:.3f}, converged={converged}")
        return theta, se, converged

    def calculate_theta_with_progression(self, responses: List[Dict]) -> Dict[str, Any]:
        """
        Calculate theta with full progression tracking for each response

        Args:
            responses: List of response dicts ordered by time

        Returns:
            Dict with theta_final, standard_error, progression, and confidence_interval
        """
        irt_service = self._get_irt_service()

        progression = []
        current_theta = 0.0
        current_se = 1.0

        for i, response in enumerate(responses):
            question = self.db.query(Question).filter(
                Question.id == response['question_id']
            ).first()

            if question:
                # Update theta with this response
                current_theta, current_se = irt_service.update_theta_adaptive(
                    current_theta,
                    current_se,
                    response['is_correct'],
                    question
                )

                progression.append({
                    "item_number": i + 1,
                    "question_id": str(response['question_id']),
                    "is_correct": response['is_correct'],
                    "theta_estimate": round(current_theta, 4),
                    "standard_error": round(current_se, 4),
                    "difficulty_b": question.parametro_irt_b
                })

        # Calculate 95% confidence interval
        ci_lower = current_theta - 1.96 * current_se
        ci_upper = current_theta + 1.96 * current_se

        return {
            "theta_final": round(current_theta, 4),
            "standard_error": round(current_se, 4),
            "confidence_interval": [round(ci_lower, 4), round(ci_upper, 4)],
            "progression": progression
        }

    def select_next_question_adaptive(
        self,
        current_theta: float,
        answered_question_ids: List[str],
        subject_id: Optional[str] = None,
        topic_id: Optional[str] = None
    ) -> Optional[Question]:
        """
        Select the next question with highest information at current theta

        Uses Fisher information function to select the most informative question
        for the examinee's current ability estimate.

        Args:
            current_theta: Current ability estimate
            answered_question_ids: List of already answered question IDs (as strings)
            subject_id: Optional subject filter
            topic_id: Optional topic filter for deep diagnostics

        Returns:
            Question with highest information value, or None if no suitable questions
        """
        irt_service = self._get_irt_service()

        # Build base query for available questions
        query = self.db.query(Question).filter(
            and_(
                ~Question.id.in_([UUID(qid) for qid in answered_question_ids]) if answered_question_ids else True,
                # Prefer questions with valid IRT parameters
                Question.parametro_irt_a.isnot(None),
                Question.parametro_irt_b.isnot(None)
            )
        )

        # Apply subject filter
        if subject_id:
            query = query.filter(Question.subject_id == UUID(subject_id))

        # Apply topic filter for deep diagnostics
        if topic_id:
            query = query.filter(Question.topic_id == UUID(topic_id))

        available_questions = query.all()

        if not available_questions:
            # Fallback: try without IRT parameter requirements
            fallback_query = self.db.query(Question).filter(
                ~Question.id.in_([UUID(qid) for qid in answered_question_ids]) if answered_question_ids else True
            )
            if subject_id:
                fallback_query = fallback_query.filter(Question.subject_id == UUID(subject_id))
            if topic_id:
                fallback_query = fallback_query.filter(Question.topic_id == UUID(topic_id))

            available_questions = fallback_query.limit(1).all()
            if available_questions:
                logger.warning("No questions with IRT parameters found, using fallback selection")
                return available_questions[0]
            return None

        # Calculate information for each question at current theta
        question_scores = []
        for question in available_questions:
            a = question.parametro_irt_a if question.parametro_irt_a is not None else 1.0
            b = question.parametro_irt_b if question.parametro_irt_b is not None else 0.0
            c = question.parametro_irt_c if question.parametro_irt_c is not None else 0.25

            # Calculate Fisher information at current theta
            information = irt_service.calculate_information_function(current_theta, a, b, c)
            question_scores.append((question, information))

        # Select question with maximum information
        if question_scores:
            best_question, best_info = max(question_scores, key=lambda x: x[1])
            logger.info(
                f"Selected adaptive question {best_question.id} with "
                f"information={best_info:.4f} at theta={current_theta:.3f}"
            )
            return best_question

        return None

    def get_adaptive_questions_batch(
        self,
        current_theta: float,
        answered_question_ids: List[str],
        subject_id: str,
        batch_size: int = 5
    ) -> List[Question]:
        """
        Get a batch of adaptive questions sorted by information value

        Useful for prefetching questions in adaptive testing.

        Args:
            current_theta: Current ability estimate
            answered_question_ids: Already answered question IDs
            subject_id: Subject to filter questions
            batch_size: Number of questions to return

        Returns:
            List of questions ordered by information value (descending)
        """
        irt_service = self._get_irt_service()

        query = self.db.query(Question).filter(
            and_(
                Question.subject_id == UUID(subject_id),
                ~Question.id.in_([UUID(qid) for qid in answered_question_ids]) if answered_question_ids else True,
                Question.parametro_irt_a.isnot(None),
                Question.parametro_irt_b.isnot(None)
            )
        )

        available_questions = query.all()

        # Calculate information and sort
        question_info = []
        for question in available_questions:
            a = question.parametro_irt_a if question.parametro_irt_a is not None else 1.0
            b = question.parametro_irt_b if question.parametro_irt_b is not None else 0.0
            c = question.parametro_irt_c if question.parametro_irt_c is not None else 0.25

            info = irt_service.calculate_information_function(current_theta, a, b, c)
            question_info.append((question, info))

        # Sort by information (descending) and return top batch_size
        question_info.sort(key=lambda x: x[1], reverse=True)
        return [q for q, _ in question_info[:batch_size]]

    def calculate_subject_thetas(self, responses: List[Dict]) -> Dict[str, Dict]:
        """
        Calculate separate theta estimates for each subject

        Args:
            responses: List of response dicts with question_id, is_correct, subject_id

        Returns:
            Dict mapping subject_id to {theta, standard_error, count}
        """
        irt_service = self._get_irt_service()

        # Group responses by subject
        subject_responses = {}
        for response in responses:
            question = self.db.query(Question).filter(
                Question.id == response['question_id']
            ).first()

            if question:
                subject_id = str(question.subject_id)
                if subject_id not in subject_responses:
                    subject_responses[subject_id] = []

                a = question.parametro_irt_a if question.parametro_irt_a is not None else 1.0
                b = question.parametro_irt_b if question.parametro_irt_b is not None else 0.0
                c = question.parametro_irt_c if question.parametro_irt_c is not None else 0.25

                subject_responses[subject_id].append((response['is_correct'], a, b, c))

        # Calculate theta for each subject
        subject_thetas = {}
        for subject_id, irt_responses in subject_responses.items():
            if len(irt_responses) >= 2:  # Need at least 2 responses for reliable estimate
                theta, se, converged = irt_service.estimate_theta_mle(irt_responses)
            else:
                # Fallback to simple calculation for small samples
                correct = sum(1 for r, _, _, _ in irt_responses if r)
                theta = _calculate_initial_theta(correct, len(irt_responses))
                se = 1.0
                converged = False

            # Get subject name
            subject = self.db.query(Subject).filter(Subject.id == UUID(subject_id)).first()

            subject_thetas[subject_id] = {
                "theta": round(theta, 4),
                "standard_error": round(se, 4),
                "converged": converged,
                "response_count": len(irt_responses),
                "subject_name": subject.name if subject else "Unknown",
                "rank": _theta_to_rank(theta)
            }

        return subject_thetas

    def theta_to_percentile(self, theta: float) -> int:
        """
        Convert theta to percentile rank (1-99)

        Uses standard normal distribution assumption for theta.

        Args:
            theta: Ability estimate

        Returns:
            Percentile rank (1-99)
        """
        import scipy.stats as stats

        # Theta is approximately normally distributed with mean 0 and SD 1
        percentile = stats.norm.cdf(theta) * 100
        return max(1, min(99, int(round(percentile))))

    def submit_quick_diagnostic_irt(
        self,
        user_id: UUID,
        diagnostic_id: UUID,
        answers: List[DiagnosticAnswerInput]
    ) -> dict:
        """
        Enhanced quick diagnostic submission with full IRT analysis

        Returns comprehensive IRT metrics including:
        - MLE theta estimate
        - Standard error and confidence interval
        - Theta progression
        - Subject-specific ability estimates
        - Percentile rank
        """
        diagnostic = self.db.query(TwoPhaseDignostic).filter(
            TwoPhaseDignostic.id == diagnostic_id,
            TwoPhaseDignostic.user_id == user_id,
            TwoPhaseDignostic.diagnostic_type == "quick"
        ).first()

        if not diagnostic:
            raise ValueError("DIAGNOSTIC_NOT_FOUND")
        if diagnostic.status == "completed":
            raise ValueError("DIAGNOSTIC_COMPLETED")

        # Process answers and collect responses for IRT
        responses = []
        subject_scores = {}
        total_time = 0

        for answer in answers:
            question = self.db.query(Question).filter(
                Question.id == answer.question_id
            ).first()
            if not question:
                continue

            is_correct = answer.answer_id.upper() == (question.respuesta_correcta or "").upper()
            total_time += answer.time_spent_seconds

            responses.append({
                'question_id': question.id,
                'is_correct': is_correct,
                'subject_id': str(question.subject_id)
            })

            # Track subject scores
            subject_id = str(question.subject_id)
            if subject_id not in subject_scores:
                subject_scores[subject_id] = {"correct": 0, "total": 0, "subject": question.subject}
            subject_scores[subject_id]["total"] += 1
            if is_correct:
                subject_scores[subject_id]["correct"] += 1

            # Save answer to database
            db_answer = TwoPhaseDiagnosticAnswer(
                diagnostic_id=diagnostic.id,
                question_id=question.id,
                answer_id=answer.answer_id.upper(),
                was_correct=is_correct,
                time_spent_seconds=answer.time_spent_seconds
            )
            self.db.add(db_answer)

        # Calculate IRT theta with full progression
        theta_result = self.calculate_theta_with_progression(responses)
        theta = theta_result["theta_final"]
        se = theta_result["standard_error"]

        # Calculate subject-specific thetas
        subject_thetas = self.calculate_subject_thetas(responses)

        # Determine rank
        rank = _theta_to_rank(theta)

        # Calculate percentile
        percentile = self.theta_to_percentile(theta)

        # Identify weak areas with IRT-based scoring
        weak_areas = []
        for subject_id, scores in subject_scores.items():
            if scores["total"] > 0:
                # Use subject-specific theta if available
                if subject_id in subject_thetas:
                    subject_theta = subject_thetas[subject_id]["theta"]
                    score = (subject_theta + 3) / 6  # Normalize to 0-1 range
                else:
                    score = scores["correct"] / scores["total"]

                if score < 0.7:
                    weak_areas.append(WeakArea(
                        subject_id=UUID(subject_id),
                        subject_name=scores["subject"].name,
                        score=round(max(0, min(1, score)), 2),
                        priority=_determine_priority(score)
                    ))

        weak_areas.sort(key=lambda x: (
            0 if x.priority == WeakAreaPriority.HIGH else
            1 if x.priority == WeakAreaPriority.MEDIUM else 2
        ))

        # Update diagnostic record
        diagnostic.completed_at = datetime.utcnow()
        diagnostic.correct_answers = sum(1 for r in responses if r['is_correct'])
        diagnostic.time_spent_seconds = total_time
        diagnostic.theta_estimate = theta
        diagnostic.status = "completed"
        diagnostic.weak_areas = [w.model_dump() for w in weak_areas]

        # Update user rank
        user = self.db.query(User).filter(User.id == user_id).first()
        user.rank = rank

        # Update engagement
        engagement = self.db.query(UserEngagement).filter(
            UserEngagement.user_id == user_id
        ).first()
        if not engagement:
            engagement = UserEngagement(user_id=user_id)
            self.db.add(engagement)
        engagement.quick_diagnostic_completed = True

        self.db.commit()

        return {
            "completed": True,
            "correct": diagnostic.correct_answers,
            "total": len(answers),
            "rank": rank,
            "theta": round(theta, 4),
            "weak_areas": weak_areas,
            # Enhanced IRT metrics
            "irt_metrics": {
                "theta_estimate": round(theta, 4),
                "standard_error": round(se, 4),
                "confidence_interval_95": theta_result["confidence_interval"],
                "percentile": percentile,
                "theta_progression": theta_result["progression"],
                "subject_abilities": subject_thetas
            }
        }
