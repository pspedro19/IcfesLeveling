"""
Adaptive Diagnostic Service
Implements advanced question selection algorithms with real-time difficulty adjustment
"""
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime, timedelta
import random
import math
import logging
from collections import defaultdict

from ..models.diagnostic_test import DiagnosticTest, DiagnosticTestAnswer
from ..models.question import Question, Topic
from ..models.subject import Subject
from ..models.user import User
from ..schemas.diagnostic_test import DiagnosticTestQuestion
from .diagnostic_service import DiagnosticService

logger = logging.getLogger(__name__)

class AdaptiveDiagnosticService(DiagnosticService):
    """
    Enhanced diagnostic service with adaptive question selection and real-time difficulty adjustment
    """
    
    def __init__(self, db: Session):
        super().__init__(db)
        self.db = db
        self.logger = logger
        
        # Adaptive algorithm parameters
        self.INITIAL_THETA = 0.0  # Starting ability estimate
        self.THETA_ADJUSTMENT_RATE = 0.5  # How quickly theta changes
        self.MIN_DIFFICULTY = 1
        self.MAX_DIFFICULTY = 10
        self.CONVERGENCE_THRESHOLD = 0.1  # When to stop adapting
        
        # Question pool parameters
        self.DIFFICULTY_BANDS = {
            'easy': (1, 3),
            'medium': (4, 6),
            'hard': (7, 10)
        }
        
        # ICFES rank thresholds
        self.ICFES_RANKS = {
            'S': {'min': 90, 'color': '#FFD700', 'name': 'Sobresaliente'},
            'A': {'min': 80, 'color': '#8B5CF6', 'name': 'Alto'},
            'B': {'min': 65, 'color': '#3B82F6', 'name': 'Medio Alto'},
            'C': {'min': 50, 'color': '#10B981', 'name': 'Medio'},
            'D': {'min': 35, 'color': '#F59E0B', 'name': 'Bajo'},
            'E': {'min': 0, 'color': '#EF4444', 'name': 'Insuficiente'}
        }

    def create_adaptive_diagnostic_test(self, user_id: str, subject_id: str, 
                                      test_type: str = "adaptive_icfes") -> DiagnosticTest:
        """Create a new adaptive diagnostic test with enhanced session tracking"""
        # Get user's previous performance for initial ability estimate
        previous_tests = self.db.query(DiagnosticTest).filter(
            and_(
                DiagnosticTest.user_id == user_id,
                DiagnosticTest.subject_id == subject_id,
                DiagnosticTest.status == "completed"
            )
        ).order_by(DiagnosticTest.completed_at.desc()).limit(3).all()
        
        # Calculate initial theta based on previous performance
        initial_theta = self._calculate_initial_theta(previous_tests)
        
        diagnostic_test = DiagnosticTest(
            user_id=user_id,
            subject_id=subject_id,
            test_type=test_type,
            status="in_progress",
            started_at=datetime.utcnow(),
            # Store adaptive parameters in test metadata
            score_by_topic={"adaptive_params": {
                "initial_theta": initial_theta,
                "current_theta": initial_theta,
                "adaptation_history": [],
                "difficulty_progression": [],
                "response_times": []
            }}
        )
        
        self.db.add(diagnostic_test)
        self.db.commit()
        self.db.refresh(diagnostic_test)
        
        self.logger.info(f"Created adaptive diagnostic test {diagnostic_test.id} for user {user_id}")
        return diagnostic_test

    def get_adaptive_diagnostic_questions(self, test_id: str, user_id: str, 
                                        num_questions: int = 20) -> List[DiagnosticTestQuestion]:
        """
        Get adaptively selected questions based on current user ability estimate
        """
        test = self.get_diagnostic_test_by_id(test_id)
        if not test or str(test.user_id) != str(user_id):
            raise ValueError("Test not found or access denied")
            
        # Get adaptive parameters from test metadata
        adaptive_params = test.score_by_topic.get("adaptive_params", {})
        current_theta = adaptive_params.get("current_theta", 0.0)
        
        # Get previously answered questions to avoid duplicates
        answered_questions = self.db.query(DiagnosticTestAnswer.question_id).filter(
            DiagnosticTestAnswer.diagnostic_test_id == test_id
        ).subquery()
        
        # Get question pool stratified by difficulty
        question_pools = self._get_stratified_question_pool(test.subject_id, answered_questions)
        
        # Select questions adaptively
        selected_questions = []
        remaining_questions = num_questions
        
        # Start with medium difficulty questions
        target_difficulty = self._theta_to_difficulty(current_theta)
        
        for i in range(num_questions):
            # Adjust target difficulty based on performance so far
            if i > 0:
                target_difficulty = self._calculate_next_difficulty(test_id, current_theta)
            
            # Select question closest to target difficulty
            question = self._select_optimal_question(
                question_pools, target_difficulty, answered_questions
            )
            
            if question:
                selected_questions.append(self._format_question_for_test(question))
                # Add to answered questions to avoid duplicates
                answered_questions = answered_questions.union(
                    self.db.query(Question.id).filter(Question.id == question.id)
                )
            
        self.logger.info(f"Selected {len(selected_questions)} adaptive questions for test {test_id}")
        return selected_questions

    def process_adaptive_answer(self, test_id: str, question_id: str, user_answer: str,
                              response_time_ms: int) -> Dict[str, Any]:
        """
        Process a single answer and update ability estimate in real-time
        """
        test = self.get_diagnostic_test_by_id(test_id)
        question = self.db.query(Question).filter(Question.id == question_id).first()
        
        if not test or not question:
            raise ValueError("Test or question not found")
            
        # Determine if answer is correct
        is_correct = user_answer.upper() == (question.respuesta_correcta or question.correct_answer or '').upper()
        
        # Save the answer
        test_answer = DiagnosticTestAnswer(
            diagnostic_test_id=test_id,
            question_id=question_id,
            user_answer=user_answer,
            is_correct=is_correct,
            response_time_ms=min(response_time_ms, 2147483647),
            topic_id=question.topic_id
        )
        self.db.add(test_answer)
        
        # Update adaptive parameters
        adaptive_params = test.score_by_topic.get("adaptive_params", {})
        current_theta = adaptive_params.get("current_theta", 0.0)
        
        # Calculate new theta using IRT-based adaptation
        new_theta = self._update_theta_estimate(current_theta, question, is_correct, response_time_ms)
        
        # Update test metadata
        adaptive_params["current_theta"] = new_theta
        adaptive_params["adaptation_history"].append({
            "question_id": str(question_id),
            "difficulty": question.difficulty,
            "correct": is_correct,
            "theta_before": current_theta,
            "theta_after": new_theta,
            "response_time": response_time_ms,
            "timestamp": datetime.utcnow().isoformat()
        })
        adaptive_params["difficulty_progression"].append(question.difficulty)
        adaptive_params["response_times"].append(response_time_ms)
        
        test.score_by_topic["adaptive_params"] = adaptive_params
        
        self.db.commit()
        
        # Calculate next recommended difficulty
        next_difficulty = self._calculate_next_difficulty(test_id, new_theta)
        
        return {
            "correct": is_correct,
            "new_theta": new_theta,
            "theta_change": new_theta - current_theta,
            "next_recommended_difficulty": next_difficulty,
            "confidence_interval": self._calculate_confidence_interval(new_theta, len(adaptive_params["adaptation_history"])),
            "performance_trend": self._analyze_performance_trend(adaptive_params["adaptation_history"][-5:])
        }

    def finalize_adaptive_test(self, test_id: str) -> Dict[str, Any]:
        """
        Finalize adaptive test with comprehensive analysis and rank assignment
        """
        test = self.get_diagnostic_test_by_id(test_id)
        if not test:
            raise ValueError("Test not found")
            
        # Get all answers for analysis
        answers = self.db.query(DiagnosticTestAnswer).filter(
            DiagnosticTestAnswer.diagnostic_test_id == test_id
        ).all()
        
        if not answers:
            raise ValueError("No answers found for test")
            
        # Calculate comprehensive metrics
        total_questions = len(answers)
        correct_answers = sum(1 for a in answers if a.is_correct)
        raw_percentage = (correct_answers / total_questions) * 100 if total_questions > 0 else 0
        
        # Get adaptive parameters
        adaptive_params = test.score_by_topic.get("adaptive_params", {})
        final_theta = adaptive_params.get("current_theta", 0.0)
        
        # Calculate ICFES-aligned score using theta
        icfes_score = self._theta_to_icfes_score(final_theta, raw_percentage)
        icfes_rank = self._calculate_icfes_rank(icfes_score)
        
        # Analyze performance patterns
        performance_analysis = self._analyze_comprehensive_performance(answers, adaptive_params)
        
        # Calculate gamification rewards
        xp_earned = self._calculate_adaptive_xp(answers, final_theta, icfes_rank)
        damage_dealt = self._calculate_battle_damage(answers, final_theta)
        
        # Update test record
        test.questions_answered = total_questions
        test.correct_answers = correct_answers
        test.score_percentage = icfes_score
        test.time_spent_seconds = sum(a.response_time_ms for a in answers) // 1000
        test.strengths = performance_analysis["strengths"]
        test.weaknesses = performance_analysis["weaknesses"]
        test.status = "completed"
        test.completed_at = datetime.utcnow()
        
        # Enhanced score_by_topic with all analytics
        test.score_by_topic.update({
            "final_metrics": {
                "icfes_score": icfes_score,
                "raw_percentage": raw_percentage,
                "final_theta": final_theta,
                "rank": icfes_rank,
                "difficulty_mastered": self._get_mastery_level(final_theta),
                "consistency_score": performance_analysis["consistency_score"],
                "speed_score": performance_analysis["speed_score"]
            },
            "gamification": {
                "xp_earned": xp_earned,
                "damage_dealt": damage_dealt,
                "battle_performance": self._calculate_battle_performance(final_theta, icfes_rank)
            }
        })
        
        self.db.commit()
        
        # Update user stats
        self._update_user_gamification_stats(test.user_id, xp_earned, icfes_rank)
        
        return {
            "test_id": str(test_id),
            "icfes_score": icfes_score,
            "raw_percentage": raw_percentage,
            "rank": icfes_rank,
            "final_theta": final_theta,
            "total_questions": total_questions,
            "correct_answers": correct_answers,
            "time_spent_minutes": test.time_spent_seconds / 60,
            "strengths": performance_analysis["strengths"],
            "weaknesses": performance_analysis["weaknesses"],
            "recommendations": self._generate_adaptive_recommendations(performance_analysis, final_theta),
            "gamification": {
                "xp_earned": xp_earned,
                "damage_dealt": damage_dealt,
                "level_up": False  # Will be calculated when updating user
            },
            "next_steps": self._generate_next_steps(final_theta, icfes_rank, performance_analysis)
        }

    # Private helper methods
    
    def _calculate_initial_theta(self, previous_tests: List[DiagnosticTest]) -> float:
        """Calculate initial ability estimate from previous tests"""
        if not previous_tests:
            return 0.0
            
        # Weight recent tests more heavily
        weighted_sum = 0
        total_weight = 0
        
        for i, test in enumerate(previous_tests):
            weight = 1 / (i + 1)  # More recent tests have higher weight
            if test.score_percentage:
                theta = self._percentage_to_theta(test.score_percentage)
                weighted_sum += theta * weight
                total_weight += weight
                
        return weighted_sum / total_weight if total_weight > 0 else 0.0
    
    def _percentage_to_theta(self, percentage: float) -> float:
        """Convert percentage score to theta estimate"""
        # Map percentage to theta using logit transformation
        p = max(0.01, min(0.99, percentage / 100))
        return math.log(p / (1 - p))
    
    def _theta_to_percentage(self, theta: float) -> float:
        """Convert theta estimate to percentage"""
        # Map theta to percentage using logistic function
        p = 1 / (1 + math.exp(-theta))
        return p * 100
    
    def _theta_to_difficulty(self, theta: float) -> int:
        """Convert theta to question difficulty level"""
        # Map theta (-3 to 3) to difficulty (1 to 10)
        normalized_theta = max(-3, min(3, theta))
        difficulty = int((normalized_theta + 3) * 10 / 6) + 1
        return max(1, min(10, difficulty))
    
    def _theta_to_icfes_score(self, theta: float, raw_percentage: float) -> float:
        """Convert theta and raw percentage to ICFES-aligned score"""
        # Combine theta-based estimate with raw performance
        theta_percentage = self._theta_to_percentage(theta)
        
        # Weight theta more heavily as it represents ability
        combined_score = 0.7 * theta_percentage + 0.3 * raw_percentage
        
        # Apply ICFES scaling (typically 0-500 scale, here 0-100)
        return max(0, min(100, combined_score))
    
    def _calculate_icfes_rank(self, score: float) -> str:
        """Calculate ICFES rank from score"""
        for rank, info in self.ICFES_RANKS.items():
            if score >= info['min']:
                return rank
        return 'E'
    
    def _get_stratified_question_pool(self, subject_id: str, answered_questions) -> Dict[str, List[Question]]:
        """Get questions organized by difficulty bands"""
        pools = {}
        
        for band, (min_diff, max_diff) in self.DIFFICULTY_BANDS.items():
            questions = self.db.query(Question).filter(
                and_(
                    Question.subject_id == subject_id,
                    Question.difficulty >= min_diff,
                    Question.difficulty <= max_diff,
                    ~Question.id.in_(answered_questions)
                )
            ).all()
            pools[band] = questions
            
        return pools
    
    def _select_optimal_question(self, question_pools: Dict[str, List[Question]], 
                               target_difficulty: int, answered_questions) -> Optional[Question]:
        """Select the most appropriate question for current ability level"""
        # Determine which pool to use based on target difficulty
        if target_difficulty <= 3:
            pool_order = ['easy', 'medium', 'hard']
        elif target_difficulty <= 6:
            pool_order = ['medium', 'easy', 'hard']
        else:
            pool_order = ['hard', 'medium', 'easy']
            
        for pool_name in pool_order:
            pool = question_pools.get(pool_name, [])
            if pool:
                # Find question closest to target difficulty
                best_question = min(pool, key=lambda q: abs(q.difficulty - target_difficulty))
                return best_question
                
        return None
    
    def _update_theta_estimate(self, current_theta: float, question: Question, 
                             is_correct: bool, response_time_ms: int) -> float:
        """Update ability estimate using IRT principles"""
        # Get question difficulty as theta value
        question_theta = self._difficulty_to_theta(question.difficulty)
        
        # Calculate expected probability of correct response
        expected_prob = 1 / (1 + math.exp(-(current_theta - question_theta)))
        
        # Actual response (1 for correct, 0 for incorrect)
        actual_response = 1 if is_correct else 0
        
        # Update theta using gradient descent-like approach
        adjustment = self.THETA_ADJUSTMENT_RATE * (actual_response - expected_prob)
        
        # Factor in response time (faster responses indicate higher confidence)
        time_factor = self._calculate_time_factor(response_time_ms)
        adjustment *= time_factor
        
        new_theta = current_theta + adjustment
        
        # Bound theta to reasonable range
        return max(-3, min(3, new_theta))
    
    def _difficulty_to_theta(self, difficulty: int) -> float:
        """Convert difficulty level to theta value"""
        # Map difficulty (1-10) to theta (-3 to 3)
        return ((difficulty - 1) * 6 / 9) - 3
    
    def _calculate_time_factor(self, response_time_ms: int) -> float:
        """Calculate confidence factor based on response time"""
        # Optimal response time is around 45 seconds
        optimal_time = 45000
        actual_time = max(1000, response_time_ms)  # Minimum 1 second
        
        if actual_time <= optimal_time:
            # Faster responses indicate higher confidence
            return 1.0 + (optimal_time - actual_time) / optimal_time * 0.2
        else:
            # Slower responses indicate lower confidence
            return max(0.5, 1.0 - (actual_time - optimal_time) / optimal_time * 0.3)
    
    def _calculate_next_difficulty(self, test_id: str, current_theta: float) -> int:
        """Calculate optimal difficulty for next question"""
        # Get recent performance
        recent_answers = self.db.query(DiagnosticTestAnswer).filter(
            DiagnosticTestAnswer.diagnostic_test_id == test_id
        ).order_by(DiagnosticTestAnswer.created_at.desc()).limit(3).all()
        
        # Base difficulty on current theta
        base_difficulty = self._theta_to_difficulty(current_theta)
        
        if len(recent_answers) >= 2:
            recent_correct = sum(1 for a in recent_answers if a.is_correct)
            if recent_correct == len(recent_answers):
                # All recent answers correct, increase difficulty
                base_difficulty = min(10, base_difficulty + 1)
            elif recent_correct == 0:
                # All recent answers wrong, decrease difficulty
                base_difficulty = max(1, base_difficulty - 1)
                
        return base_difficulty
    
    def _calculate_confidence_interval(self, theta: float, num_responses: int) -> Tuple[float, float]:
        """Calculate confidence interval for theta estimate"""
        # Standard error decreases with more responses
        se = 1.0 / math.sqrt(max(1, num_responses))
        
        # 95% confidence interval
        margin = 1.96 * se
        return (theta - margin, theta + margin)
    
    def _analyze_performance_trend(self, recent_history: List[Dict]) -> str:
        """Analyze recent performance trend"""
        if len(recent_history) < 3:
            return "insufficient_data"
            
        theta_changes = [h["theta_after"] - h["theta_before"] for h in recent_history]
        avg_change = sum(theta_changes) / len(theta_changes)
        
        if avg_change > 0.1:
            return "improving"
        elif avg_change < -0.1:
            return "declining"
        else:
            return "stable"
    
    def _analyze_comprehensive_performance(self, answers: List[DiagnosticTestAnswer], 
                                         adaptive_params: Dict) -> Dict[str, Any]:
        """Analyze comprehensive performance patterns"""
        if not answers:
            return {"strengths": [], "weaknesses": [], "consistency_score": 0, "speed_score": 0}
            
        # Topic-based analysis
        topic_performance = defaultdict(list)
        for answer in answers:
            if answer.topic_id:
                topic_performance[answer.topic_id].append(answer.is_correct)
                
        # Difficulty-based analysis
        difficulty_performance = defaultdict(list)
        for answer in answers:
            question = self.db.query(Question).filter(Question.id == answer.question_id).first()
            if question:
                diff_band = self._get_difficulty_band(question.difficulty)
                difficulty_performance[diff_band].append(answer.is_correct)
        
        # Generate strengths and weaknesses
        strengths = []
        weaknesses = []
        
        for topic_id, results in topic_performance.items():
            if len(results) >= 2:
                accuracy = sum(results) / len(results)
                topic = self.db.query(Topic).filter(Topic.id == topic_id).first()
                topic_name = topic.name if topic else "Topic desconocido"
                
                if accuracy >= 0.7:
                    strengths.append(f"{topic_name} - Dominio sólido ({accuracy*100:.0f}%)")
                elif accuracy < 0.5:
                    weaknesses.append(f"{topic_name} - Requiere refuerzo ({accuracy*100:.0f}%)")
        
        # Difficulty analysis
        for band, results in difficulty_performance.items():
            if len(results) >= 2:
                accuracy = sum(results) / len(results)
                if band == "hard" and accuracy >= 0.6:
                    strengths.append(f"Preguntas complejas - Buen manejo de conceptos avanzados")
                elif band == "easy" and accuracy < 0.6:
                    weaknesses.append(f"Conceptos básicos - Necesita reforzar fundamentos")
        
        # Calculate consistency score
        correct_sequence = [1 if a.is_correct else 0 for a in answers]
        consistency_score = self._calculate_consistency(correct_sequence)
        
        # Calculate speed score
        response_times = [a.response_time_ms for a in answers if a.response_time_ms > 0]
        speed_score = self._calculate_speed_score(response_times)
        
        return {
            "strengths": strengths[:5],  # Top 5 strengths
            "weaknesses": weaknesses[:5],  # Top 5 weaknesses
            "consistency_score": consistency_score,
            "speed_score": speed_score,
            "topic_performance": dict(topic_performance),
            "difficulty_performance": dict(difficulty_performance)
        }
    
    def _get_difficulty_band(self, difficulty: int) -> str:
        """Get difficulty band for a difficulty level"""
        if difficulty <= 3:
            return "easy"
        elif difficulty <= 6:
            return "medium"
        else:
            return "hard"
    
    def _calculate_consistency(self, sequence: List[int]) -> float:
        """Calculate performance consistency score"""
        if len(sequence) < 5:
            return 0.5
            
        # Calculate variance in sliding windows
        window_size = 5
        variances = []
        
        for i in range(len(sequence) - window_size + 1):
            window = sequence[i:i + window_size]
            mean_val = sum(window) / len(window)
            variance = sum((x - mean_val) ** 2 for x in window) / len(window)
            variances.append(variance)
        
        avg_variance = sum(variances) / len(variances) if variances else 0
        
        # Convert to 0-1 score (lower variance = higher consistency)
        consistency = 1 - min(1, avg_variance * 4)
        return max(0, consistency)
    
    def _calculate_speed_score(self, response_times: List[int]) -> float:
        """Calculate speed performance score"""
        if not response_times:
            return 0.5
            
        avg_time = sum(response_times) / len(response_times)
        optimal_time = 45000  # 45 seconds
        
        # Score based on deviation from optimal time
        if avg_time <= optimal_time:
            score = 1.0 - (optimal_time - avg_time) / optimal_time * 0.3
        else:
            score = max(0.1, 1.0 - (avg_time - optimal_time) / optimal_time)
        
        return min(1.0, max(0, score))
    
    def _calculate_adaptive_xp(self, answers: List[DiagnosticTestAnswer], 
                             final_theta: float, rank: str) -> int:
        """Calculate XP earned with adaptive bonuses"""
        base_xp = len(answers) * 10  # 10 XP per question
        correct_bonus = sum(20 if a.is_correct else 0 for a in answers)
        
        # Difficulty bonus based on theta
        difficulty_multiplier = 1 + max(0, final_theta) * 0.5
        
        # Rank bonus
        rank_bonuses = {'S': 100, 'A': 75, 'B': 50, 'C': 25, 'D': 10, 'E': 0}
        rank_bonus = rank_bonuses.get(rank, 0)
        
        total_xp = int((base_xp + correct_bonus) * difficulty_multiplier + rank_bonus)
        return max(50, total_xp)  # Minimum 50 XP
    
    def _calculate_battle_damage(self, answers: List[DiagnosticTestAnswer], final_theta: float) -> int:
        """Calculate battle damage for gamification"""
        correct_answers = sum(1 for a in answers if a.is_correct)
        base_damage = correct_answers * 25
        
        # Theta-based multiplier
        theta_multiplier = 1 + max(0, final_theta) * 0.3
        
        return int(base_damage * theta_multiplier)
    
    def _calculate_battle_performance(self, final_theta: float, rank: str) -> Dict[str, Any]:
        """Calculate battle performance metrics"""
        # Convert theta to battle stats
        power_level = max(1, int((final_theta + 3) * 20))
        accuracy = min(100, max(20, int(self._theta_to_percentage(final_theta))))
        
        return {
            "power_level": power_level,
            "accuracy": accuracy,
            "rank": rank,
            "battle_ready": rank in ['A', 'S'],
            "recommended_difficulty": "beginner" if rank in ['E', 'D'] else "intermediate" if rank in ['C', 'B'] else "advanced"
        }
    
    def _update_user_gamification_stats(self, user_id: str, xp_earned: int, rank: str):
        """Update user's gamification statistics"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if user:
            level_up = user.add_experience(xp_earned)
            
            # Update rank if it's an improvement
            current_rank_value = {'E': 1, 'D': 2, 'C': 3, 'B': 4, 'A': 5, 'S': 6}.get(user.rank, 1)
            new_rank_value = {'E': 1, 'D': 2, 'C': 3, 'B': 4, 'A': 5, 'S': 6}.get(rank, 1)
            
            if new_rank_value > current_rank_value:
                user.rank = rank
                
            self.db.commit()
            return level_up
        return False
    
    def _generate_adaptive_recommendations(self, performance_analysis: Dict, final_theta: float) -> List[str]:
        """Generate personalized recommendations based on adaptive analysis"""
        recommendations = []
        
        # Theta-based recommendations
        if final_theta < -1:
            recommendations.append("🎯 Enfócate en dominar conceptos fundamentales antes de avanzar")
            recommendations.append("📚 Dedica tiempo extra a la teoría básica y ejercicios simples")
        elif final_theta < 0:
            recommendations.append("💪 Tienes una base sólida, practica problemas de nivel intermedio")
            recommendations.append("🔍 Identifica patrones en los errores para mejorar la precisión")
        elif final_theta < 1:
            recommendations.append("🌟 Excelente progreso, desafíate con problemas más complejos")
            recommendations.append("📈 Enfócate en optimizar tu velocidad de respuesta")
        else:
            recommendations.append("🏆 Rendimiento sobresaliente, mantén la práctica regular")
            recommendations.append("🎓 Considera ayudar a otros estudiantes para reforzar tu conocimiento")
        
        # Consistency recommendations
        consistency = performance_analysis.get("consistency_score", 0.5)
        if consistency < 0.6:
            recommendations.append("⚡ Mejora tu consistencia con práctica diaria estructurada")
            
        # Speed recommendations
        speed = performance_analysis.get("speed_score", 0.5)
        if speed < 0.6:
            recommendations.append("⏱️ Practica con cronómetro para mejorar tu gestión del tiempo")
        
        return recommendations
    
    def _generate_next_steps(self, final_theta: float, rank: str, performance_analysis: Dict) -> List[str]:
        """Generate specific next steps for the student"""
        steps = []
        
        # Immediate next steps based on performance
        if rank in ['E', 'D']:
            steps.append("Comenzar plan de estudio básico con fundamentos")
            steps.append("Tomar diagnóstico de seguimiento en 2 semanas")
        elif rank in ['C', 'B']:
            steps.append("Continuar con plan de estudio intermedio")
            steps.append("Practicar simulacros semanales")
        else:
            steps.append("Mantener nivel con simulacros avanzados")
            steps.append("Explorar temas de profundización")
            
        # Topic-specific steps
        weaknesses = performance_analysis.get("weaknesses", [])
        if weaknesses:
            steps.append(f"Priorizar estudio en: {weaknesses[0].split(' - ')[0]}")
            
        return steps
    
    def _get_mastery_level(self, theta: float) -> str:
        """Get mastery level description from theta"""
        if theta < -1.5:
            return "Principiante"
        elif theta < -0.5:
            return "Básico"
        elif theta < 0.5:
            return "Intermedio"
        elif theta < 1.5:
            return "Avanzado"
        else:
            return "Experto"
    
    def _format_question_for_test(self, question: Question) -> DiagnosticTestQuestion:
        """Format question for test interface"""
        # Build options from individual fields
        options = []
        for letra in ['a', 'b', 'c', 'd']:
            texto = getattr(question, f'opcion_{letra}_texto')
            if texto:
                options.append(texto)
            else:
                options.append(f"Opción {letra.upper()}")
        
        return DiagnosticTestQuestion(
            id=str(question.id),
            question_text=question.pregunta_texto or question.question_text or "Pregunta sin texto",
            options=options,
            subject=question.subject.name if question.subject else "General",
            topic=question.topic.name if question.topic else "General",
            difficulty=question.difficulty,
            hint=question.hint,
            image_url=question.pregunta_imagen,
            options_images={}
        )