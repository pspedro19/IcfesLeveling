from typing import List, Dict, Any, Optional
import numpy as np
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
import logging

from ..models.user import User
from ..models.battle import BattleAnswer
from ..models.question import Question
from ..services.cache_service import cache_service

logger = logging.getLogger(__name__)

class RecommendationService:
    def __init__(self):
        self.min_questions_per_subject = 45
        self.min_data_points = 10
        
    def get_adaptive_recommendations(
        self,
        user_id: str,
        db: Session,
        days: int = 30
    ) -> Dict[str, Any]:
        """Generate adaptive recommendations for a user"""
        cache_key = f"recommendations:{user_id}:days:{days}"
        cached_recommendations = cache_service.get(cache_key)
        if cached_recommendations:
            return cached_recommendations
        
        user_data = self._gather_user_data(user_id, db, days)
        data_sufficiency = self._check_data_sufficiency(user_data)
        
        if not data_sufficiency["has_sufficient_data"]:
            return self._get_default_recommendations(data_sufficiency)
        
        performance_analysis = self._analyze_performance(user_data)
        
        recommendations = {
            "next_topics": self._recommend_next_topics(performance_analysis, user_data),
            "study_schedule": self._generate_study_schedule(performance_analysis, user_data),
            "rank_progression": self._calculate_rank_progression(performance_analysis, user_data),
            "data_sufficiency": data_sufficiency,
            "confidence_level": self._calculate_confidence_level(data_sufficiency, user_data)
        }
        
        cache_service.set(cache_key, recommendations, ttl=3600)
        return recommendations

    def _check_data_sufficiency(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check if user has sufficient data for reliable recommendations"""
        questions_by_subject = user_data.get("questions_by_subject", {})
        
        subjects_with_sufficient_data = []
        subjects_needing_more_data = []
        
        for subject, count in questions_by_subject.items():
            if count >= self.min_questions_per_subject:
                subjects_with_sufficient_data.append(subject)
            else:
                subjects_needing_more_data.append({
                    "subject": subject,
                    "current": count,
                    "needed": self.min_questions_per_subject - count
                })
        
        has_sufficient_data = len(subjects_with_sufficient_data) >= 2
        
        return {
            "has_sufficient_data": has_sufficient_data,
            "subjects_with_sufficient_data": subjects_with_sufficient_data,
            "subjects_needing_more_data": subjects_needing_more_data,
            "min_questions_per_subject": self.min_questions_per_subject,
            "recommendation_quality": "high" if has_sufficient_data else "low"
        }

    def _get_default_recommendations(self, data_sufficiency: Dict[str, Any]) -> Dict[str, Any]:
        """Get default recommendations when user has insufficient data"""
        return {
            "next_topics": [
                {
                    "topic": "General Practice",
                    "reason": "Build foundational knowledge",
                    "priority": "high",
                    "suggested_questions": 20,
                    "estimated_time": "30-45 minutos"
                }
            ],
            "study_schedule": {
                "daily_sessions": 2,
                "session_duration": 25,
                "focus_areas": ["Matemáticas", "Lenguaje"],
                "weekly_goals": [
                    "Completar 45 preguntas por materia",
                    "Mantener racha de estudio",
                    "Revisar explicaciones de errores"
                ]
            },
            "rank_progression": {
                "current_rank": "E",
                "next_rank": "D",
                "progress_percentage": 0,
                "questions_needed": data_sufficiency.get("subjects_needing_more_data", []),
                "estimated_time_to_next_rank": "2-3 semanas"
            },
            "data_sufficiency": data_sufficiency,
            "confidence_level": "low",
            "message": f"Necesitas completar al menos {self.min_questions_per_subject} preguntas por materia para recomendaciones personalizadas"
        }

    def _gather_user_data(self, user_id: str, db: Session, days: int) -> Dict[str, Any]:
        """Gather user data for analysis"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        battle_answers = db.query(BattleAnswer).join(
            BattleAnswer.battle
        ).filter(
            BattleAnswer.battle.has(user_id=user_id),
            BattleAnswer.created_at >= cutoff_date
        ).all()
        
        questions_by_subject = {}
        subject_performance = {}
        
        for answer in battle_answers:
            if answer.question and answer.question.subject:
                subject_name = answer.question.subject.name
                if subject_name not in questions_by_subject:
                    questions_by_subject[subject_name] = 0
                    subject_performance[subject_name] = {"correct": 0, "total": 0}
                
                questions_by_subject[subject_name] += 1
                subject_performance[subject_name]["total"] += 1
                
                if answer.is_correct:
                    subject_performance[subject_name]["correct"] += 1
        
        return {
            "total_questions_answered": len(battle_answers),
            "questions_by_subject": questions_by_subject,
            "subject_performance": subject_performance,
            "recent_answers": battle_answers[-50:] if battle_answers else []
        }

    def _analyze_performance(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze user performance patterns"""
        analysis = {
            "overall_accuracy": 0,
            "subject_accuracies": {},
            "weaknesses": [],
            "strengths": []
        }
        
        total_correct = sum(perf["correct"] for perf in user_data["subject_performance"].values())
        total_questions = sum(perf["total"] for perf in user_data["subject_performance"].values())
        
        if total_questions > 0:
            analysis["overall_accuracy"] = (total_correct / total_questions) * 100
        
        for subject, perf in user_data["subject_performance"].items():
            if perf["total"] >= 5:
                accuracy = (perf["correct"] / perf["total"]) * 100
                analysis["subject_accuracies"][subject] = accuracy
                
                if accuracy >= 80:
                    analysis["strengths"].append({
                        "subject": subject,
                        "accuracy": accuracy,
                        "questions_answered": perf["total"]
                    })
                elif accuracy <= 60:
                    analysis["weaknesses"].append({
                        "subject": subject,
                        "accuracy": accuracy,
                        "questions_answered": perf["total"]
                    })
        
        analysis["strengths"].sort(key=lambda x: x["accuracy"], reverse=True)
        analysis["weaknesses"].sort(key=lambda x: x["accuracy"])
        
        return analysis

    def _recommend_next_topics(self, analysis: Dict[str, Any], user_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Recommend next topics to study"""
        recommendations = []
        
        for weakness in analysis["weaknesses"][:3]:
            recommendations.append({
                "topic": weakness["subject"],
                "reason": f"Precisión actual: {weakness['accuracy']:.1f}%",
                "priority": "high",
                "suggested_questions": 20,
                "estimated_time": "30-45 minutos"
            })
        
        return recommendations

    def _generate_study_schedule(self, analysis: Dict[str, Any], user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate personalized study schedule"""
        schedule = {
            "daily_sessions": 3,
            "session_duration": 30,
            "focus_subjects": [],
            "weekly_goals": []
        }
        
        if analysis["weaknesses"]:
            schedule["focus_subjects"] = [w["subject"] for w in analysis["weaknesses"][:2]]
        
        schedule["weekly_goals"] = [
            f"Completar {self.min_questions_per_subject} preguntas por materia",
            "Mantener racha de estudio diario",
            "Revisar explicaciones de errores"
        ]
        
        return schedule

    def _calculate_rank_progression(self, analysis: Dict[str, Any], user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate rank progression and requirements"""
        rank_requirements = {
            "E": {"questions_needed": 0, "accuracy_required": 0},
            "D": {"questions_needed": 180, "accuracy_required": 60},
            "C": {"questions_needed": 360, "accuracy_required": 70},
            "B": {"questions_needed": 540, "accuracy_required": 80},
            "A": {"questions_needed": 720, "accuracy_required": 85},
            "S": {"questions_needed": 900, "accuracy_required": 90}
        }
        
        rank_order = ["E", "D", "C", "B", "A", "S"]
        current_rank = "E"  # Default, should get from user profile
        current_index = rank_order.index(current_rank)
        
        if current_index >= len(rank_order) - 1:
            next_rank = current_rank
            progress_percentage = 100
        else:
            next_rank = rank_order[current_index + 1]
            next_requirements = rank_requirements[next_rank]
            
            total_questions = user_data["total_questions_answered"]
            current_accuracy = analysis["overall_accuracy"]
            
            questions_progress = min(100, (total_questions / next_requirements["questions_needed"]) * 100)
            accuracy_progress = min(100, (current_accuracy / next_requirements["accuracy_required"]) * 100)
            
            progress_percentage = (questions_progress + accuracy_progress) / 2
        
        return {
            "current_rank": current_rank,
            "next_rank": next_rank,
            "progress_percentage": round(progress_percentage, 1),
            "questions_needed": rank_requirements[next_rank]["questions_needed"] - user_data["total_questions_answered"],
            "estimated_time_to_next_rank": "2-3 semanas"
        }

    def _calculate_confidence_level(self, data_sufficiency: Dict[str, Any], user_data: Dict[str, Any]) -> str:
        """Calculate confidence level of recommendations"""
        if data_sufficiency["has_sufficient_data"]:
            return "high"
        elif user_data["total_questions_answered"] >= 50:
            return "medium"
        else:
            return "low"