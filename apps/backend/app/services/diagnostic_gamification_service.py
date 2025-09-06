"""
Diagnostic Gamification Service
Integrates diagnostic test results with the gamification system including XP, battles, and achievements
"""
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import logging
import math

from ..models.diagnostic_test import DiagnosticTest, DiagnosticTestAnswer
from ..models.user import User
from ..models.question import Question, Topic
from ..models.subject import Subject

logger = logging.getLogger(__name__)

class DiagnosticGamificationService:
    """
    Service to handle gamification aspects of diagnostic tests including XP calculation,
    battle damage, achievements, and boss battle integration
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.logger = logger
        
        # XP calculation parameters
        self.BASE_XP_PER_QUESTION = 10
        self.CORRECT_ANSWER_BONUS = 15
        self.DIFFICULTY_MULTIPLIERS = {
            1: 0.8, 2: 0.9, 3: 1.0, 4: 1.1, 5: 1.2,
            6: 1.3, 7: 1.4, 8: 1.5, 9: 1.7, 10: 2.0
        }
        
        # Battle system parameters
        self.BASE_DAMAGE_PER_CORRECT = 25
        self.CRITICAL_HIT_THRESHOLD = 0.8  # 80% accuracy triggers critical hits
        self.COMBO_MULTIPLIER = 1.2
        
        # Achievement thresholds
        self.ACHIEVEMENT_THRESHOLDS = {
            "first_diagnostic": {"tests": 1, "xp": 50},
            "diagnostic_warrior": {"tests": 5, "xp": 200},
            "diagnostic_master": {"tests": 10, "xp": 500},
            "perfectionist": {"perfect_tests": 1, "xp": 300},
            "speed_demon": {"fast_completion": True, "xp": 150},
            "consistent_learner": {"streak": 7, "xp": 250},
            "rank_climber": {"rank_improvement": True, "xp": 400}
        }
        
        # Boss battle integration
        self.BOSS_DAMAGE_MULTIPLIER = 2.5
        self.BOSS_XP_BONUS = 100
        
        # Rank progression rewards
        self.RANK_REWARDS = {
            'S': {"xp_bonus": 500, "crystals": 50, "orbs": 200},
            'A': {"xp_bonus": 300, "crystals": 30, "orbs": 150},
            'B': {"xp_bonus": 200, "crystals": 20, "orbs": 100},
            'C': {"xp_bonus": 100, "crystals": 10, "orbs": 75},
            'D': {"xp_bonus": 50, "crystals": 5, "orbs": 50},
            'E': {"xp_bonus": 25, "crystals": 2, "orbs": 25}
        }

    def calculate_diagnostic_rewards(self, test_id: str) -> Dict[str, Any]:
        """
        Calculate comprehensive rewards for completing a diagnostic test
        """
        test = self.db.query(DiagnosticTest).filter(DiagnosticTest.id == test_id).first()
        if not test:
            raise ValueError("Test not found")
            
        answers = self.db.query(DiagnosticTestAnswer).filter(
            DiagnosticTestAnswer.diagnostic_test_id == test_id
        ).all()
        
        if not answers:
            return {"xp": 0, "damage": 0, "achievements": [], "rewards": {}}
        
        # Calculate base metrics
        total_questions = len(answers)
        correct_answers = sum(1 for a in answers if a.is_correct)
        accuracy = correct_answers / total_questions if total_questions > 0 else 0
        
        # Calculate XP with various bonuses
        xp_breakdown = self._calculate_xp_breakdown(answers, test, accuracy)
        total_xp = xp_breakdown["total"]
        
        # Calculate battle damage
        damage_breakdown = self._calculate_battle_damage(answers, test, accuracy)
        total_damage = damage_breakdown["total"]
        
        # Check for achievements
        achievements = self._check_diagnostic_achievements(test, accuracy)
        
        # Calculate rank-based rewards
        rank = self._determine_rank_from_score(test.score_percentage)
        rank_rewards = self.RANK_REWARDS.get(rank, self.RANK_REWARDS['E'])
        
        # Calculate boss battle performance
        boss_performance = self._calculate_boss_battle_performance(test, accuracy, total_damage)
        
        return {
            "xp": {
                "total": total_xp,
                "breakdown": xp_breakdown
            },
            "damage": {
                "total": total_damage,
                "breakdown": damage_breakdown
            },
            "achievements": achievements,
            "rank": rank,
            "rank_rewards": rank_rewards,
            "boss_battle": boss_performance,
            "battle_stats": {
                "accuracy": accuracy * 100,
                "combo_achieved": damage_breakdown.get("combo_bonus", 0) > 0,
                "critical_hits": damage_breakdown.get("critical_hits", 0),
                "perfect_streak": self._calculate_perfect_streak(answers)
            },
            "power_progression": self._calculate_power_progression(test, accuracy)
        }

    def apply_diagnostic_rewards(self, user_id: str, rewards: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply calculated rewards to user account
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("User not found")
            
        # Store original stats for comparison
        original_level = user.level
        original_rank = user.rank
        
        # Apply XP and check for level up
        xp_earned = rewards["xp"]["total"]
        level_up_occurred = user.add_experience(xp_earned)
        
        # Apply rank rewards
        rank_rewards = rewards.get("rank_rewards", {})
        user.crystals += rank_rewards.get("crystals", 0)
        user.orbs += rank_rewards.get("orbs", 0)
        
        # Update rank if improved
        new_rank = rewards.get("rank", "E")
        if self._is_rank_improvement(user.rank, new_rank):
            user.rank = new_rank
            
        # Apply battle stats improvements
        battle_stats = rewards.get("battle_stats", {})
        if battle_stats.get("accuracy", 0) > 80:
            user.power = min(100, user.power + 2)
        if battle_stats.get("combo_achieved"):
            user.speed = min(100, user.speed + 1)
        if rewards.get("rank") in ['A', 'S']:
            user.wisdom = min(100, user.wisdom + 3)
            
        self.db.commit()
        
        # Record achievements
        achievement_records = self._record_achievements(user_id, rewards["achievements"])
        
        return {
            "level_up": level_up_occurred,
            "new_level": user.level,
            "level_change": user.level - original_level,
            "rank_up": user.rank != original_rank,
            "new_rank": user.rank,
            "achievements_unlocked": len(achievement_records),
            "achievement_details": achievement_records,
            "currency_earned": {
                "crystals": rank_rewards.get("crystals", 0),
                "orbs": rank_rewards.get("orbs", 0)
            },
            "stat_improvements": {
                "power": user.power,
                "wisdom": user.wisdom,
                "speed": user.speed
            }
        }

    def create_boss_battle_from_diagnostic(self, test_id: str) -> Optional[Dict[str, Any]]:
        """
        Create a boss battle scenario based on diagnostic test performance
        """
        test = self.db.query(DiagnosticTest).filter(DiagnosticTest.id == test_id).first()
        if not test or test.score_percentage < 70:  # Only create boss battles for good performance
            return None
            
        # Determine boss type based on subject and performance
        boss_config = self._determine_boss_config(test)
        
        # Calculate boss stats based on user performance
        boss_stats = self._calculate_boss_stats(test)
        
        return {
            "boss_id": f"diagnostic_boss_{test.subject_id}_{int(datetime.utcnow().timestamp())}",
            "boss_name": boss_config["name"],
            "boss_type": boss_config["type"],
            "boss_level": boss_config["level"],
            "boss_hp": boss_stats["hp"],
            "boss_power": boss_stats["power"],
            "rewards": {
                "xp": self.BOSS_XP_BONUS * boss_config["level"],
                "crystals": boss_config["level"] * 25,
                "orbs": boss_config["level"] * 50,
                "special_item": boss_config.get("special_item")
            },
            "battle_modifiers": {
                "user_damage_bonus": min(2.0, test.score_percentage / 50),
                "time_limit": 300,  # 5 minutes
                "difficulty_scaling": boss_config["level"]
            },
            "unlock_requirements": {
                "test_id": str(test_id),
                "min_score": 70,
                "subject": test.subject.name if test.subject else "General"
            }
        }

    def calculate_study_plan_integration(self, test_id: str) -> Dict[str, Any]:
        """
        Generate study plan recommendations based on diagnostic results
        """
        test = self.db.query(DiagnosticTest).filter(DiagnosticTest.id == test_id).first()
        if not test:
            raise ValueError("Test not found")
            
        answers = self.db.query(DiagnosticTestAnswer).filter(
            DiagnosticTestAnswer.diagnostic_test_id == test_id
        ).all()
        
        # Analyze performance by topic
        topic_performance = self._analyze_topic_performance(answers)
        
        # Generate adaptive study recommendations
        study_recommendations = []
        priority_topics = []
        
        for topic_id, performance in topic_performance.items():
            topic = self.db.query(Topic).filter(Topic.id == topic_id).first()
            topic_name = topic.name if topic else "Unknown Topic"
            
            if performance["accuracy"] < 0.5:  # Less than 50% accuracy
                priority_topics.append({
                    "topic_id": str(topic_id),
                    "topic_name": topic_name,
                    "priority": "high",
                    "accuracy": performance["accuracy"],
                    "recommended_time": max(2, int(5 * (0.6 - performance["accuracy"]) * 10)),  # Hours
                    "difficulty_adjustment": "easy"
                })
            elif performance["accuracy"] < 0.7:  # 50-70% accuracy
                study_recommendations.append({
                    "topic_id": str(topic_id),
                    "topic_name": topic_name,
                    "priority": "medium",
                    "accuracy": performance["accuracy"],
                    "recommended_time": max(1, int(3 * (0.8 - performance["accuracy"]) * 10)),
                    "difficulty_adjustment": "medium"
                })
        
        return {
            "priority_topics": priority_topics,
            "recommended_topics": study_recommendations,
            "study_intensity": self._calculate_study_intensity(test.score_percentage),
            "estimated_preparation_time": self._estimate_preparation_time(topic_performance),
            "next_diagnostic_date": datetime.utcnow() + timedelta(weeks=2),
            "gamification_goals": self._generate_study_goals(topic_performance, test.score_percentage)
        }

    # Private helper methods
    
    def _calculate_xp_breakdown(self, answers: List[DiagnosticTestAnswer], 
                               test: DiagnosticTest, accuracy: float) -> Dict[str, Any]:
        """Calculate detailed XP breakdown with bonuses"""
        total_questions = len(answers)
        correct_answers = sum(1 for a in answers if a.is_correct)
        
        # Base XP
        base_xp = total_questions * self.BASE_XP_PER_QUESTION
        
        # Correct answer bonus
        correct_bonus = correct_answers * self.CORRECT_ANSWER_BONUS
        
        # Difficulty bonus
        difficulty_bonus = 0
        for answer in answers:
            question = self.db.query(Question).filter(Question.id == answer.question_id).first()
            if question and answer.is_correct:
                multiplier = self.DIFFICULTY_MULTIPLIERS.get(question.difficulty, 1.0)
                difficulty_bonus += self.BASE_XP_PER_QUESTION * (multiplier - 1.0)
        
        # Accuracy bonus
        accuracy_bonus = 0
        if accuracy >= 0.9:
            accuracy_bonus = base_xp * 0.5
        elif accuracy >= 0.8:
            accuracy_bonus = base_xp * 0.3
        elif accuracy >= 0.7:
            accuracy_bonus = base_xp * 0.2
        
        # Speed bonus
        speed_bonus = self._calculate_speed_bonus(answers, test)
        
        # Consistency bonus
        consistency_bonus = self._calculate_consistency_bonus(answers)
        
        total = int(base_xp + correct_bonus + difficulty_bonus + accuracy_bonus + speed_bonus + consistency_bonus)
        
        return {
            "base": int(base_xp),
            "correct_answers": int(correct_bonus),
            "difficulty": int(difficulty_bonus),
            "accuracy": int(accuracy_bonus),
            "speed": int(speed_bonus),
            "consistency": int(consistency_bonus),
            "total": total
        }
    
    def _calculate_battle_damage(self, answers: List[DiagnosticTestAnswer], 
                               test: DiagnosticTest, accuracy: float) -> Dict[str, Any]:
        """Calculate battle damage with critical hits and combos"""
        correct_answers = sum(1 for a in answers if a.is_correct)
        base_damage = correct_answers * self.BASE_DAMAGE_PER_CORRECT
        
        # Critical hit bonus
        critical_hits = 0
        critical_bonus = 0
        if accuracy >= self.CRITICAL_HIT_THRESHOLD:
            critical_hits = max(1, int(correct_answers * (accuracy - 0.7)))
            critical_bonus = critical_hits * self.BASE_DAMAGE_PER_CORRECT * 0.5
        
        # Combo bonus for consecutive correct answers
        combo_bonus = self._calculate_combo_damage(answers)
        
        # Difficulty bonus
        difficulty_bonus = 0
        for answer in answers:
            if answer.is_correct:
                question = self.db.query(Question).filter(Question.id == answer.question_id).first()
                if question and question.difficulty >= 7:
                    difficulty_bonus += self.BASE_DAMAGE_PER_CORRECT * 0.3
        
        total = int(base_damage + critical_bonus + combo_bonus + difficulty_bonus)
        
        return {
            "base": int(base_damage),
            "critical": int(critical_bonus),
            "critical_hits": critical_hits,
            "combo_bonus": int(combo_bonus),
            "difficulty": int(difficulty_bonus),
            "total": total
        }
    
    def _calculate_speed_bonus(self, answers: List[DiagnosticTestAnswer], test: DiagnosticTest) -> float:
        """Calculate bonus for fast completion"""
        if not answers or not test.time_spent_seconds:
            return 0
            
        avg_time_per_question = test.time_spent_seconds / len(answers)
        optimal_time = 45  # 45 seconds per question
        
        if avg_time_per_question <= optimal_time:
            speed_factor = optimal_time / avg_time_per_question
            return len(answers) * self.BASE_XP_PER_QUESTION * min(0.3, (speed_factor - 1) * 0.1)
        
        return 0
    
    def _calculate_consistency_bonus(self, answers: List[DiagnosticTestAnswer]) -> float:
        """Calculate bonus for consistent performance"""
        if len(answers) < 5:
            return 0
            
        # Calculate streaks of correct answers
        current_streak = 0
        max_streak = 0
        
        for answer in answers:
            if answer.is_correct:
                current_streak += 1
                max_streak = max(max_streak, current_streak)
            else:
                current_streak = 0
        
        if max_streak >= 5:
            return max_streak * 5  # 5 XP per streak length
        
        return 0
    
    def _calculate_combo_damage(self, answers: List[DiagnosticTestAnswer]) -> float:
        """Calculate combo damage bonus"""
        combo_multiplier = 1.0
        current_streak = 0
        total_combo_damage = 0
        
        for answer in answers:
            if answer.is_correct:
                current_streak += 1
                if current_streak >= 3:  # Combo starts at 3 consecutive correct
                    combo_multiplier = min(2.0, 1.0 + (current_streak - 2) * 0.1)
                    total_combo_damage += self.BASE_DAMAGE_PER_CORRECT * (combo_multiplier - 1.0)
            else:
                current_streak = 0
                combo_multiplier = 1.0
        
        return total_combo_damage
    
    def _calculate_perfect_streak(self, answers: List[DiagnosticTestAnswer]) -> int:
        """Calculate the longest perfect streak"""
        current_streak = 0
        max_streak = 0
        
        for answer in answers:
            if answer.is_correct:
                current_streak += 1
                max_streak = max(max_streak, current_streak)
            else:
                current_streak = 0
        
        return max_streak
    
    def _check_diagnostic_achievements(self, test: DiagnosticTest, accuracy: float) -> List[Dict[str, Any]]:
        """Check which achievements were unlocked"""
        achievements = []
        user_id = test.user_id
        
        # Count user's diagnostic tests
        total_tests = self.db.query(DiagnosticTest).filter(
            and_(DiagnosticTest.user_id == user_id, DiagnosticTest.status == "completed")
        ).count()
        
        # First diagnostic achievement
        if total_tests == 1:
            achievements.append({
                "id": "first_diagnostic",
                "name": "Primera Evaluación",
                "description": "Completaste tu primer test diagnóstico",
                "xp": self.ACHIEVEMENT_THRESHOLDS["first_diagnostic"]["xp"],
                "rarity": "common"
            })
        
        # Multiple tests achievements
        if total_tests == 5:
            achievements.append({
                "id": "diagnostic_warrior",
                "name": "Guerrero Diagnóstico",
                "description": "Completaste 5 tests diagnósticos",
                "xp": self.ACHIEVEMENT_THRESHOLDS["diagnostic_warrior"]["xp"],
                "rarity": "rare"
            })
        elif total_tests == 10:
            achievements.append({
                "id": "diagnostic_master",
                "name": "Maestro Diagnóstico",
                "description": "Completaste 10 tests diagnósticos",
                "xp": self.ACHIEVEMENT_THRESHOLDS["diagnostic_master"]["xp"],
                "rarity": "epic"
            })
        
        # Perfect score achievement
        if accuracy >= 0.95:
            achievements.append({
                "id": "perfectionist",
                "name": "Perfeccionista",
                "description": "Obtuviste una puntuación casi perfecta",
                "xp": self.ACHIEVEMENT_THRESHOLDS["perfectionist"]["xp"],
                "rarity": "legendary"
            })
        
        # Speed achievement
        if test.time_spent_seconds and len(test.answers) > 0:
            avg_time = test.time_spent_seconds / len(test.answers)
            if avg_time <= 30 and accuracy >= 0.8:  # Fast and accurate
                achievements.append({
                    "id": "speed_demon",
                    "name": "Demonio de la Velocidad",
                    "description": "Completaste el test rápidamente y con alta precisión",
                    "xp": self.ACHIEVEMENT_THRESHOLDS["speed_demon"]["xp"],
                    "rarity": "epic"
                })
        
        return achievements
    
    def _record_achievements(self, user_id: str, achievements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Record achievements in the database"""
        recorded = []
        
        for achievement in achievements:
            # Check if user already has this achievement
            # This would typically check a user_achievements table
            # For now, we'll assume all achievements are new
            recorded.append({
                "achievement_id": achievement["id"],
                "name": achievement["name"],
                "description": achievement["description"],
                "xp_awarded": achievement["xp"],
                "rarity": achievement["rarity"],
                "unlocked_at": datetime.utcnow()
            })
        
        return recorded
    
    def _determine_rank_from_score(self, score: float) -> str:
        """Determine rank based on score"""
        if score >= 90:
            return 'S'
        elif score >= 80:
            return 'A'
        elif score >= 65:
            return 'B'
        elif score >= 50:
            return 'C'
        elif score >= 35:
            return 'D'
        else:
            return 'E'
    
    def _is_rank_improvement(self, current_rank: str, new_rank: str) -> bool:
        """Check if new rank is an improvement"""
        rank_values = {'E': 1, 'D': 2, 'C': 3, 'B': 4, 'A': 5, 'S': 6}
        return rank_values.get(new_rank, 1) > rank_values.get(current_rank, 1)
    
    def _calculate_power_progression(self, test: DiagnosticTest, accuracy: float) -> Dict[str, Any]:
        """Calculate power progression metrics"""
        return {
            "battle_power": int(accuracy * 100 + test.score_percentage * 0.5),
            "mastery_level": self._get_mastery_level(accuracy),
            "combat_effectiveness": min(100, int(accuracy * 120)),
            "recommended_opponents": self._get_recommended_opponents(accuracy, test.score_percentage)
        }
    
    def _get_mastery_level(self, accuracy: float) -> str:
        """Get mastery level description"""
        if accuracy >= 0.95:
            return "Legendary Master"
        elif accuracy >= 0.85:
            return "Expert"
        elif accuracy >= 0.75:
            return "Advanced"
        elif accuracy >= 0.65:
            return "Intermediate"
        elif accuracy >= 0.5:
            return "Novice"
        else:
            return "Beginner"
    
    def _get_recommended_opponents(self, accuracy: float, score: float) -> List[str]:
        """Get recommended battle opponents based on performance"""
        if score >= 85:
            return ["Shadow Master", "Crystal Dragon", "Void Keeper"]
        elif score >= 70:
            return ["Iron Golem", "Fire Elemental", "Storm Guardian"]
        elif score >= 55:
            return ["Forest Troll", "Cave Spider", "Wind Spirit"]
        else:
            return ["Training Dummy", "Slime", "Wooden Scarecrow"]
    
    def _determine_boss_config(self, test: DiagnosticTest) -> Dict[str, Any]:
        """Determine boss configuration based on test results"""
        subject_name = test.subject.name if test.subject else "General"
        score_percentage = test.score_percentage
        
        # Boss configurations by subject
        boss_configs = {
            "Matemáticas": {
                "name": "El Numerón Supremo",
                "type": "mathematical_entity",
                "special_item": "Calculadora Legendaria"
            },
            "Lectura Crítica": {
                "name": "El Guardián de las Palabras",
                "type": "literary_spirit",
                "special_item": "Pluma de Sabiduría"
            },
            "Ciencias Naturales": {
                "name": "El Maestro de los Elementos",
                "type": "elemental_lord",
                "special_item": "Orbe de Conocimiento"
            },
            "Ciencias Sociales": {
                "name": "El Cronarca",
                "type": "time_guardian",
                "special_item": "Brújula del Tiempo"
            },
            "Inglés": {
                "name": "The Language Master",
                "type": "linguistic_entity",
                "special_item": "Universal Translator"
            }
        }
        
        config = boss_configs.get(subject_name, {
            "name": "El Conocimiento Absoluto",
            "type": "wisdom_entity",
            "special_item": "Cristal de Sabiduría"
        })
        
        # Determine level based on performance
        if score_percentage >= 90:
            config["level"] = 5
        elif score_percentage >= 80:
            config["level"] = 4
        elif score_percentage >= 70:
            config["level"] = 3
        else:
            config["level"] = 2
        
        return config
    
    def _calculate_boss_stats(self, test: DiagnosticTest) -> Dict[str, int]:
        """Calculate boss stats based on test performance"""
        base_hp = 1000
        base_power = 100
        
        # Scale based on user performance (higher performance = stronger boss)
        performance_multiplier = (test.score_percentage / 100) * 1.5 + 0.5
        
        return {
            "hp": int(base_hp * performance_multiplier),
            "power": int(base_power * performance_multiplier)
        }
    
    def _calculate_boss_battle_performance(self, test: DiagnosticTest, 
                                         accuracy: float, total_damage: int) -> Dict[str, Any]:
        """Calculate boss battle performance metrics"""
        return {
            "eligible": test.score_percentage >= 70,
            "recommended_level": max(1, int(test.score_percentage / 20)),
            "user_power_estimate": int(accuracy * 150 + test.score_percentage * 0.8),
            "estimated_damage": int(total_damage * self.BOSS_DAMAGE_MULTIPLIER),
            "win_probability": min(95, max(5, int(accuracy * 100 + (test.score_percentage - 70) * 2))),
            "rewards_preview": {
                "xp": self.BOSS_XP_BONUS * max(1, int(test.score_percentage / 20)),
                "crystals": max(1, int(test.score_percentage / 20)) * 25,
                "special_drops": test.score_percentage >= 85
            }
        }
    
    def _analyze_topic_performance(self, answers: List[DiagnosticTestAnswer]) -> Dict[str, Dict[str, Any]]:
        """Analyze performance by topic"""
        topic_stats = {}
        
        for answer in answers:
            if not answer.topic_id:
                continue
                
            topic_id = str(answer.topic_id)
            if topic_id not in topic_stats:
                topic_stats[topic_id] = {
                    "total": 0,
                    "correct": 0,
                    "response_times": []
                }
            
            stats = topic_stats[topic_id]
            stats["total"] += 1
            if answer.is_correct:
                stats["correct"] += 1
            if answer.response_time_ms:
                stats["response_times"].append(answer.response_time_ms)
        
        # Calculate derived metrics
        for topic_id, stats in topic_stats.items():
            stats["accuracy"] = stats["correct"] / stats["total"] if stats["total"] > 0 else 0
            if stats["response_times"]:
                stats["avg_response_time"] = sum(stats["response_times"]) / len(stats["response_times"])
            else:
                stats["avg_response_time"] = 0
        
        return topic_stats
    
    def _calculate_study_intensity(self, score_percentage: float) -> str:
        """Calculate recommended study intensity"""
        if score_percentage >= 85:
            return "maintenance"  # Light review to maintain level
        elif score_percentage >= 70:
            return "moderate"     # Regular practice
        elif score_percentage >= 55:
            return "intensive"    # Daily focused study
        else:
            return "remedial"     # Comprehensive review needed
    
    def _estimate_preparation_time(self, topic_performance: Dict[str, Dict[str, Any]]) -> int:
        """Estimate time needed for preparation in hours"""
        total_hours = 0
        
        for topic_id, performance in topic_performance.items():
            accuracy = performance["accuracy"]
            if accuracy < 0.5:
                total_hours += 8  # 8 hours for weak topics
            elif accuracy < 0.7:
                total_hours += 4  # 4 hours for moderate topics
            else:
                total_hours += 2  # 2 hours for review
        
        return max(10, min(100, total_hours))  # Between 10 and 100 hours
    
    def _generate_study_goals(self, topic_performance: Dict[str, Dict[str, Any]], 
                            overall_score: float) -> List[Dict[str, Any]]:
        """Generate gamified study goals"""
        goals = []
        
        # Overall improvement goal
        if overall_score < 70:
            goals.append({
                "type": "score_improvement",
                "title": "Ascender de Rango",
                "description": f"Mejorar puntuación general del {overall_score:.0f}% al 70%",
                "target_value": 70,
                "current_value": overall_score,
                "reward_xp": 200,
                "deadline_days": 30
            })
        
        # Topic-specific goals
        weak_topics = [(topic_id, perf) for topic_id, perf in topic_performance.items() 
                       if perf["accuracy"] < 0.6]
        
        for i, (topic_id, performance) in enumerate(weak_topics[:3]):  # Top 3 weakest topics
            topic = self.db.query(Topic).filter(Topic.id == topic_id).first()
            topic_name = topic.name if topic else f"Tema {i+1}"
            
            goals.append({
                "type": "topic_mastery",
                "title": f"Dominar {topic_name}",
                "description": f"Alcanzar 70% de precisión en {topic_name}",
                "target_value": 0.7,
                "current_value": performance["accuracy"],
                "reward_xp": 150,
                "deadline_days": 14
            })
        
        # Speed goal
        if any(perf.get("avg_response_time", 0) > 60000 for perf in topic_performance.values()):
            goals.append({
                "type": "speed_improvement",
                "title": "Velocidad de Respuesta",
                "description": "Reducir tiempo promedio de respuesta a menos de 1 minuto",
                "target_value": 60,
                "current_value": max(perf.get("avg_response_time", 0) / 1000 
                                   for perf in topic_performance.values()) if topic_performance else 0,
                "reward_xp": 100,
                "deadline_days": 21
            })
        
        return goals