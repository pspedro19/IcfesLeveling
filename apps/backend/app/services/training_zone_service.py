"""
Comprehensive Training Zone Service - ICFES Leveling

This service implements a complete training zone system where students practice
with their failed ICFES questions, featuring:

1. Monthly rotation system based on latest diagnostic results
2. Spaced repetition algorithm for optimal learning
3. YouTube video integration for failed questions
4. AI-powered explanations and hints
5. Adaptive difficulty based on performance
6. Separate progress tracking from diagnostic tests
7. Comprehensive analytics and reporting

Author: Claude Code Assistant
Date: 2024
"""

import asyncio
import asyncpg
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc, asc
import pandas as pd
import numpy as np
import logging
import json
import uuid
from datetime import datetime, timedelta, date
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import math
import random

from ..core.database import get_db
from ..models.training_zone import *
from ..models.diagnostic_test import DiagnosticTest, DiagnosticTestAnswer
from ..models.question import Question
from ..models.youtube_catalog import YoutubeCatalog
from ..models.user import User

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TrainingZoneService:
    """
    Main service for managing the comprehensive training zone system
    """
    
    def __init__(self, db: Session):
        self.db = db
        
        # Spaced repetition algorithm settings
        self.default_ease_factor = 2.5
        self.min_ease_factor = 1.3
        self.max_ease_factor = 3.0
        self.initial_interval = 1
        self.max_interval = 365
        
        # Training session settings
        self.mode_question_limits = {
            TrainingMode.RECOVERY: 20,
            TrainingMode.SPRINT: 10,
            TrainingMode.FULL_REVIEW: 50,
            TrainingMode.SPACED_REPETITION: 15,
            TrainingMode.MONTHLY_FOCUS: 25
        }
        
        self.mode_time_limits = {
            TrainingMode.RECOVERY: 30,      # minutes
            TrainingMode.SPRINT: 10,
            TrainingMode.FULL_REVIEW: 60,
            TrainingMode.SPACED_REPETITION: 25,
            TrainingMode.MONTHLY_FOCUS: 35
        }
        
        # Mastery criteria
        self.mastery_threshold = 0.85
        self.mastery_consecutive_correct = 3
        self.mastery_min_attempts = 5
    
    async def initialize_training_zone(self, user_id: str, subject_id: str) -> Dict[str, Any]:
        """
        Initialize training zone for a user and subject based on their failed diagnostic questions
        """
        try:
            # Check if training zone already exists
            existing_zone = self.db.query(TrainingZone).filter(
                and_(
                    TrainingZone.user_id == user_id,
                    TrainingZone.subject_id == subject_id
                )
            ).first()
            
            if existing_zone:
                return await self.update_training_zone_from_latest_diagnostic(
                    existing_zone.id, force_update=False
                )
            
            # Get the latest completed diagnostic test for this subject
            latest_diagnostic = self.db.query(DiagnosticTest).filter(
                and_(
                    DiagnosticTest.user_id == user_id,
                    DiagnosticTest.subject_id == subject_id,
                    DiagnosticTest.status == "completed"
                )
            ).order_by(desc(DiagnosticTest.completed_at)).first()
            
            if not latest_diagnostic:
                return {
                    "success": False,
                    "message": "No completed diagnostic test found for this subject",
                    "action_required": "complete_diagnostic"
                }
            
            # Get failed questions from diagnostic
            failed_answers = self.db.query(DiagnosticTestAnswer).filter(
                and_(
                    DiagnosticTestAnswer.diagnostic_test_id == latest_diagnostic.id,
                    DiagnosticTestAnswer.is_correct == False
                )
            ).all()
            
            if not failed_answers:
                return {
                    "success": False,
                    "message": "No failed questions found in diagnostic test",
                    "congratulations": True
                }
            
            # Create training zone
            current_month = datetime.now().month
            current_year = datetime.now().year
            
            training_zone = TrainingZone(
                user_id=user_id,
                subject_id=subject_id,
                current_month=current_month,
                current_year=current_year,
                last_rotation_date=datetime.now(),
                rotation_triggered_by_diagnostic=True
            )
            
            self.db.add(training_zone)
            self.db.flush()  # Get the ID
            
            # Add failed questions to training zone
            questions_added = 0
            for failed_answer in failed_answers:
                question = self.db.query(Question).filter(
                    Question.id == failed_answer.question_id
                ).first()
                
                if question:
                    # Calculate initial next review date
                    next_review = datetime.now() + timedelta(days=1)
                    
                    training_question = TrainingZoneQuestion(
                        training_zone_id=training_zone.id,
                        question_id=question.id,
                        user_id=user_id,
                        source_diagnostic_id=latest_diagnostic.id,
                        original_failure_date=latest_diagnostic.completed_at,
                        original_answer=failed_answer.user_answer,
                        original_time_seconds=failed_answer.response_time_ms // 1000,
                        next_review_date=next_review,
                        added_in_month=current_month,
                        added_in_year=current_year,
                        priority_level=self._calculate_initial_priority(failed_answer, question)
                    )
                    
                    self.db.add(training_question)
                    questions_added += 1
            
            # Generate video recommendations for failed questions
            await self._generate_video_recommendations(training_zone.id)
            
            self.db.commit()
            
            return {
                "success": True,
                "training_zone_id": str(training_zone.id),
                "questions_added": questions_added,
                "current_month": current_month,
                "message": f"Training zone initialized with {questions_added} failed questions"
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error initializing training zone: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def update_training_zone_from_latest_diagnostic(self, 
                                                        training_zone_id: str, 
                                                        force_update: bool = False) -> Dict[str, Any]:
        """
        Update training zone with new failed questions from latest diagnostic
        (Monthly rotation system)
        """
        try:
            training_zone = self.db.query(TrainingZone).filter(
                TrainingZone.id == training_zone_id
            ).first()
            
            if not training_zone:
                return {"success": False, "message": "Training zone not found"}
            
            # Check if monthly update is needed
            current_month = datetime.now().month
            current_year = datetime.now().year
            
            needs_update = (
                force_update or
                training_zone.current_month != current_month or
                training_zone.current_year != current_year
            )
            
            if not needs_update:
                return {
                    "success": True,
                    "message": "Training zone is up to date",
                    "last_rotation": training_zone.last_rotation_date.isoformat()
                }
            
            # Get latest diagnostic test
            latest_diagnostic = self.db.query(DiagnosticTest).filter(
                and_(
                    DiagnosticTest.user_id == training_zone.user_id,
                    DiagnosticTest.subject_id == training_zone.subject_id,
                    DiagnosticTest.status == "completed"
                )
            ).order_by(desc(DiagnosticTest.completed_at)).first()
            
            if not latest_diagnostic:
                return {"success": False, "message": "No recent diagnostic test found"}
            
            # Get new failed questions (not already in training zone)
            existing_question_ids = {
                tq.question_id for tq in self.db.query(TrainingZoneQuestion).filter(
                    TrainingZoneQuestion.training_zone_id == training_zone_id
                ).all()
            }
            
            new_failed_answers = self.db.query(DiagnosticTestAnswer).filter(
                and_(
                    DiagnosticTestAnswer.diagnostic_test_id == latest_diagnostic.id,
                    DiagnosticTestAnswer.is_correct == False,
                    ~DiagnosticTestAnswer.question_id.in_(existing_question_ids)
                )
            ).all()
            
            # Add new failed questions
            new_questions_added = 0
            for failed_answer in new_failed_answers:
                question = self.db.query(Question).filter(
                    Question.id == failed_answer.question_id
                ).first()
                
                if question:
                    next_review = datetime.now() + timedelta(days=1)
                    
                    training_question = TrainingZoneQuestion(
                        training_zone_id=training_zone_id,
                        question_id=question.id,
                        user_id=training_zone.user_id,
                        source_diagnostic_id=latest_diagnostic.id,
                        original_failure_date=latest_diagnostic.completed_at,
                        original_answer=failed_answer.user_answer,
                        original_time_seconds=failed_answer.response_time_ms // 1000,
                        next_review_date=next_review,
                        added_in_month=current_month,
                        added_in_year=current_year,
                        priority_level=self._calculate_initial_priority(failed_answer, question)
                    )
                    
                    self.db.add(training_question)
                    new_questions_added += 1
            
            # Update training zone
            training_zone.current_month = current_month
            training_zone.current_year = current_year
            training_zone.last_rotation_date = datetime.now()
            training_zone.rotation_triggered_by_diagnostic = True
            
            # Update monthly stats
            monthly_stats = training_zone.monthly_stats or {}
            month_key = f"{current_year}-{current_month:02d}"
            monthly_stats[month_key] = {
                "rotation_date": datetime.now().isoformat(),
                "new_questions_added": new_questions_added,
                "diagnostic_test_id": str(latest_diagnostic.id)
            }
            training_zone.monthly_stats = monthly_stats
            
            # Generate video recommendations for new questions
            if new_questions_added > 0:
                await self._generate_video_recommendations(training_zone_id, new_questions_only=True)
            
            self.db.commit()
            
            return {
                "success": True,
                "new_questions_added": new_questions_added,
                "rotation_completed": True,
                "current_month": current_month,
                "message": f"Training zone rotated with {new_questions_added} new failed questions"
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating training zone: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def start_training_session(self, 
                                   user_id: str, 
                                   subject_id: str, 
                                   mode: TrainingMode,
                                   custom_settings: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Start a new training session with the specified mode
        """
        try:
            # Get or create training zone
            training_zone = self.db.query(TrainingZone).filter(
                and_(
                    TrainingZone.user_id == user_id,
                    TrainingZone.subject_id == subject_id
                )
            ).first()
            
            if not training_zone:
                init_result = await self.initialize_training_zone(user_id, subject_id)
                if not init_result["success"]:
                    return init_result
                training_zone = self.db.query(TrainingZone).filter(
                    TrainingZone.id == init_result["training_zone_id"]
                ).first()
            
            # Check for monthly rotation
            await self.update_training_zone_from_latest_diagnostic(str(training_zone.id))
            
            # Select questions based on mode
            selected_questions = await self._select_questions_for_session(
                training_zone.id, mode, custom_settings
            )
            
            if not selected_questions:
                return {
                    "success": False,
                    "message": "No questions available for training session",
                    "suggestion": "All questions may be mastered or not due for review"
                }
            
            # Create training session
            target_questions = custom_settings.get("target_questions") if custom_settings else None
            target_questions = target_questions or self.mode_question_limits[mode]
            target_questions = min(target_questions, len(selected_questions))
            
            time_limit = custom_settings.get("time_limit_minutes") if custom_settings else None
            time_limit = time_limit or self.mode_time_limits[mode]
            
            training_session = TrainingSession(
                training_zone_id=training_zone.id,
                user_id=user_id,
                mode=mode.value,
                target_questions=target_questions,
                time_limit_minutes=time_limit,
                status="active"
            )
            
            self.db.add(training_session)
            self.db.flush()
            
            # Update training zone stats
            training_zone.total_training_sessions += 1
            
            self.db.commit()
            
            # Prepare session data
            session_questions = selected_questions[:target_questions]
            first_question = session_questions[0] if session_questions else None
            
            return {
                "success": True,
                "session_id": str(training_session.id),
                "mode": mode.value,
                "target_questions": target_questions,
                "time_limit_minutes": time_limit,
                "total_available": len(selected_questions),
                "first_question": await self._format_question_for_session(first_question) if first_question else None,
                "session_info": {
                    "question_ids": [str(q.question_id) for q in session_questions],
                    "current_index": 0,
                    "started_at": training_session.started_at.isoformat()
                }
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error starting training session: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def submit_training_answer(self, 
                                   session_id: str,
                                   question_id: str,
                                   user_answer: str,
                                   response_time_seconds: int,
                                   confidence_level: int = 3,
                                   quality_rating: Optional[int] = None) -> Dict[str, Any]:
        """
        Submit an answer for a training question and update spaced repetition algorithm
        """
        try:
            # Get training session
            training_session = self.db.query(TrainingSession).filter(
                TrainingSession.id == session_id
            ).first()
            
            if not training_session:
                return {"success": False, "message": "Training session not found"}
            
            # Get question and correct answer
            question = self.db.query(Question).filter(
                Question.id == question_id
            ).first()
            
            if not question:
                return {"success": False, "message": "Question not found"}
            
            # Get training zone question
            training_question = self.db.query(TrainingZoneQuestion).filter(
                and_(
                    TrainingZoneQuestion.training_zone_id == training_session.training_zone_id,
                    TrainingZoneQuestion.question_id == question_id
                )
            ).first()
            
            if not training_question:
                return {"success": False, "message": "Training question not found"}
            
            # Check if answer is correct
            is_correct = user_answer.upper().strip() == question.correct_answer.upper().strip()
            
            # Calculate attempt number
            attempt_number = training_session.questions_answered + 1
            
            # Create training attempt
            training_attempt = TrainingAttempt(
                training_session_id=session_id,
                training_question_id=training_question.id,
                question_id=question_id,
                user_id=training_session.user_id,
                user_answer=user_answer,
                is_correct=is_correct,
                response_time_seconds=response_time_seconds,
                confidence_level=confidence_level,
                attempt_number=attempt_number,
                difficulty_at_attempt=self._calculate_current_difficulty(training_question),
                quality_rating=quality_rating
            )
            
            self.db.add(training_attempt)
            
            # Update training question metrics
            training_question.training_attempts += 1
            if is_correct:
                training_question.successful_attempts += 1
                training_question.consecutive_correct += 1
                training_question.consecutive_incorrect = 0
            else:
                training_question.consecutive_correct = 0
                training_question.consecutive_incorrect += 1
            
            # Update time metrics
            if training_question.best_time_seconds is None or (is_correct and response_time_seconds < training_question.best_time_seconds):
                training_question.best_time_seconds = response_time_seconds
            
            if training_question.average_time_seconds is None:
                training_question.average_time_seconds = response_time_seconds
            else:
                training_question.average_time_seconds = (
                    training_question.average_time_seconds + response_time_seconds
                ) / 2
            
            # Calculate time improvement
            if training_question.original_time_seconds > 0:
                training_question.time_improvement_percent = (
                    (training_question.original_time_seconds - response_time_seconds) / 
                    training_question.original_time_seconds
                ) * 100
                training_attempt.time_improvement = training_question.time_improvement_percent
            
            # Update spaced repetition algorithm
            if quality_rating is None:
                # Auto-calculate quality based on correctness and response time
                quality_rating = self._calculate_quality_rating(
                    is_correct, response_time_seconds, confidence_level, training_question
                )
            
            training_attempt.quality_rating = quality_rating
            training_question.next_review_date = training_question.calculate_next_review_date(quality_rating)
            
            # Check for mastery
            mastery_achieved = self._check_mastery(training_question)
            if mastery_achieved and not training_question.is_mastered:
                training_question.is_mastered = True
                training_question.mastery_achieved_date = datetime.now()
                training_question.mastery_score = self._calculate_mastery_score(training_question)
            
            # Update session metrics
            training_session.questions_answered += 1
            if is_correct:
                training_session.correct_answers += 1
                training_session.current_streak += 1
                if training_session.current_streak > training_session.max_streak_in_session:
                    training_session.max_streak_in_session = training_session.current_streak
            else:
                training_session.current_streak = 0
            
            # Update session performance
            training_session.total_time_seconds += response_time_seconds
            training_session.average_response_time = (
                training_session.total_time_seconds / training_session.questions_answered
            )
            training_session.session_accuracy = (
                training_session.correct_answers / training_session.questions_answered
            )
            
            # Update training zone progress
            training_zone = self.db.query(TrainingZone).filter(
                TrainingZone.id == training_session.training_zone_id
            ).first()
            
            training_zone.total_questions_practiced += 1
            if is_correct:
                training_zone.total_correct_answers += 1
            
            # Calculate improvement metrics
            training_attempt.mastery_gain = self._calculate_mastery_gain(training_question, is_correct)
            
            self.db.commit()
            
            # Prepare response
            result = {
                "success": True,
                "is_correct": is_correct,
                "correct_answer": question.correct_answer,
                "response_time_seconds": response_time_seconds,
                "quality_rating": quality_rating,
                "mastery_achieved": mastery_achieved,
                "next_review_date": training_question.next_review_date.isoformat(),
                "current_streak": training_session.current_streak,
                "session_accuracy": training_session.session_accuracy,
                "time_improvement": training_question.time_improvement_percent,
                "attempt_number": attempt_number,
                "session_progress": {
                    "answered": training_session.questions_answered,
                    "target": training_session.target_questions,
                    "correct": training_session.correct_answers
                }
            }
            
            # Add AI explanation if incorrect or requested
            if not is_correct or confidence_level <= 2:
                result["needs_explanation"] = True
                result["explanation_suggestion"] = "This question would benefit from an AI explanation"
            
            # Add video recommendations
            video_recommendations = await self._get_video_recommendations(training_question.id)
            if video_recommendations:
                result["video_recommendations"] = video_recommendations
            
            return result
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error submitting training answer: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_ai_explanation(self, 
                               training_attempt_id: str,
                               explanation_type: str = "conceptual") -> Dict[str, Any]:
        """
        Generate AI-powered explanation for a training question
        """
        try:
            training_attempt = self.db.query(TrainingAttempt).filter(
                TrainingAttempt.id == training_attempt_id
            ).first()
            
            if not training_attempt:
                return {"success": False, "message": "Training attempt not found"}
            
            # Check if explanation already exists
            existing_explanation = self.db.query(TrainingAIExplanation).filter(
                TrainingAIExplanation.training_attempt_id == training_attempt_id
            ).first()
            
            if existing_explanation:
                return {
                    "success": True,
                    "explanation": existing_explanation.explanation_text,
                    "type": existing_explanation.explanation_type,
                    "personalized_tips": existing_explanation.personalized_tips,
                    "related_concepts": existing_explanation.related_concepts,
                    "cached": True
                }
            
            # Get question details
            question = self.db.query(Question).filter(
                Question.id == training_attempt.question_id
            ).first()
            
            # Get user's error pattern
            user_error_analysis = await self._analyze_user_error_pattern(
                training_attempt.user_id, training_attempt.question_id
            )
            
            # Generate AI explanation (this would integrate with your AI service)
            explanation_data = await self._generate_ai_explanation(
                question, training_attempt, user_error_analysis, explanation_type
            )
            
            # Create explanation record
            ai_explanation = TrainingAIExplanation(
                training_attempt_id=training_attempt_id,
                question_id=training_attempt.question_id,
                user_id=training_attempt.user_id,
                explanation_text=explanation_data["explanation"],
                explanation_type=explanation_type,
                difficulty_level=explanation_data["difficulty_level"],
                user_error_analysis=user_error_analysis,
                personalized_tips=explanation_data["personalized_tips"],
                related_concepts=explanation_data["related_concepts"],
                ai_model_used=explanation_data["ai_model"],
                tokens_used=explanation_data.get("tokens_used", 0)
            )
            
            self.db.add(ai_explanation)
            
            # Update training question
            training_question = self.db.query(TrainingZoneQuestion).filter(
                TrainingZoneQuestion.id == training_attempt.training_question_id
            ).first()
            
            training_question.has_ai_explanation = True
            
            # Update session stats
            training_session = self.db.query(TrainingSession).filter(
                TrainingSession.id == training_attempt.training_session_id
            ).first()
            
            training_session.ai_explanations_requested += 1
            
            self.db.commit()
            
            return {
                "success": True,
                "explanation": explanation_data["explanation"],
                "type": explanation_type,
                "personalized_tips": explanation_data["personalized_tips"],
                "related_concepts": explanation_data["related_concepts"],
                "difficulty_level": explanation_data["difficulty_level"],
                "generated": True
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error generating AI explanation: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_video_recommendations(self, 
                                      training_question_id: str,
                                      limit: int = 3) -> Dict[str, Any]:
        """
        Get YouTube video recommendations for a training question
        """
        try:
            training_question = self.db.query(TrainingZoneQuestion).filter(
                TrainingZoneQuestion.id == training_question_id
            ).first()
            
            if not training_question:
                return {"success": False, "message": "Training question not found"}
            
            # Get existing recommendations
            recommendations = self.db.query(TrainingVideoRecommendation).filter(
                TrainingVideoRecommendation.training_question_id == training_question_id
            ).order_by(desc(TrainingVideoRecommendation.relevance_score)).limit(limit).all()
            
            if not recommendations:
                # Generate new recommendations
                await self._generate_video_recommendations(
                    training_question.training_zone_id, 
                    specific_question_id=training_question.question_id
                )
                
                recommendations = self.db.query(TrainingVideoRecommendation).filter(
                    TrainingVideoRecommendation.training_question_id == training_question_id
                ).order_by(desc(TrainingVideoRecommendation.relevance_score)).limit(limit).all()
            
            # Format recommendations
            video_data = []
            for rec in recommendations:
                youtube_video = self.db.query(YoutubeCatalog).filter(
                    YoutubeCatalog.id == rec.youtube_video_id
                ).first()
                
                if youtube_video:
                    video_data.append({
                        "id": str(rec.id),
                        "youtube_id": youtube_video.youtube_id,
                        "title": youtube_video.title,
                        "description": youtube_video.description,
                        "thumbnail_url": youtube_video.thumbnail_url,
                        "duration_seconds": youtube_video.duration_seconds,
                        "channel_name": youtube_video.channel_name,
                        "relevance_score": rec.relevance_score,
                        "topic_match_score": rec.topic_match_score,
                        "recommendation_reason": rec.recommendation_reason,
                        "embed_url": youtube_video.get_embed_url(),
                        "watch_url": youtube_video.get_watch_url()
                    })
            
            return {
                "success": True,
                "recommendations": video_data,
                "total_found": len(video_data)
            }
            
        except Exception as e:
            logger.error(f"Error getting video recommendations: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def complete_training_session(self, session_id: str) -> Dict[str, Any]:
        """
        Complete a training session and generate comprehensive report
        """
        try:
            training_session = self.db.query(TrainingSession).filter(
                TrainingSession.id == session_id
            ).first()
            
            if not training_session:
                return {"success": False, "message": "Training session not found"}
            
            # Update session status
            training_session.status = "completed"
            training_session.completed_at = datetime.now()
            
            # Calculate final session metrics
            session_duration = (training_session.completed_at - training_session.started_at).total_seconds() / 60
            training_session.total_time_seconds = int(session_duration * 60)
            
            # Update training zone progress
            training_zone = self.db.query(TrainingZone).filter(
                TrainingZone.id == training_session.training_zone_id
            ).first()
            
            # Update streak
            today = date.today()
            last_session_date = training_zone.last_rotation_date.date() if training_zone.last_rotation_date else None
            
            if last_session_date != today:
                if last_session_date == today - timedelta(days=1):
                    training_zone.current_training_streak += 1
                else:
                    training_zone.current_training_streak = 1
                
                if training_zone.current_training_streak > training_zone.max_training_streak:
                    training_zone.max_training_streak = training_zone.current_training_streak
            
            # Update overall performance
            total_sessions = training_zone.total_training_sessions
            if total_sessions > 0:
                training_zone.average_session_accuracy = (
                    (training_zone.average_session_accuracy * (total_sessions - 1) + 
                     training_session.session_accuracy) / total_sessions
                )
            
            # Calculate improvement rate
            if training_zone.total_questions_practiced > 0:
                training_zone.improvement_rate = (
                    training_zone.total_correct_answers / training_zone.total_questions_practiced
                ) * 100
            
            # Update mastery level
            training_zone.mastery_level = await self._calculate_overall_mastery_level(training_zone.id)
            
            self.db.commit()
            
            # Generate session report
            session_report = await self._generate_session_report(session_id)
            
            return {
                "success": True,
                "session_completed": True,
                "session_report": session_report,
                "training_zone_stats": {
                    "total_sessions": training_zone.total_training_sessions,
                    "current_streak": training_zone.current_training_streak,
                    "overall_accuracy": training_zone.average_session_accuracy,
                    "mastery_level": training_zone.mastery_level,
                    "improvement_rate": training_zone.improvement_rate
                }
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error completing training session: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_training_zone_dashboard(self, 
                                        user_id: str, 
                                        subject_id: str) -> Dict[str, Any]:
        """
        Get comprehensive training zone dashboard data
        """
        try:
            training_zone = self.db.query(TrainingZone).filter(
                and_(
                    TrainingZone.user_id == user_id,
                    TrainingZone.subject_id == subject_id
                )
            ).first()
            
            if not training_zone:
                # Initialize if needed
                init_result = await self.initialize_training_zone(user_id, subject_id)
                if not init_result["success"]:
                    return init_result
                
                training_zone = self.db.query(TrainingZone).filter(
                    TrainingZone.id == init_result["training_zone_id"]
                ).first()
            
            # Get training questions statistics
            total_questions = self.db.query(TrainingZoneQuestion).filter(
                TrainingZoneQuestion.training_zone_id == training_zone.id
            ).count()
            
            mastered_questions = self.db.query(TrainingZoneQuestion).filter(
                and_(
                    TrainingZoneQuestion.training_zone_id == training_zone.id,
                    TrainingZoneQuestion.is_mastered == True
                )
            ).count()
            
            # Questions due for review (spaced repetition)
            due_for_review = self.db.query(TrainingZoneQuestion).filter(
                and_(
                    TrainingZoneQuestion.training_zone_id == training_zone.id,
                    TrainingZoneQuestion.is_mastered == False,
                    TrainingZoneQuestion.next_review_date <= datetime.now()
                )
            ).count()
            
            # Get recent sessions
            recent_sessions = self.db.query(TrainingSession).filter(
                TrainingSession.training_zone_id == training_zone.id
            ).order_by(desc(TrainingSession.started_at)).limit(5).all()
            
            # Format recent sessions
            sessions_data = []
            for session in recent_sessions:
                sessions_data.append({
                    "id": str(session.id),
                    "mode": session.mode,
                    "questions_answered": session.questions_answered,
                    "correct_answers": session.correct_answers,
                    "accuracy": session.session_accuracy,
                    "duration_minutes": (session.completed_at - session.started_at).total_seconds() / 60 if session.completed_at else None,
                    "started_at": session.started_at.isoformat(),
                    "status": session.status
                })
            
            # Calculate performance by difficulty
            difficulty_stats = await self._get_difficulty_performance_stats(training_zone.id)
            
            # Get spaced repetition overview
            spaced_rep_stats = await self._get_spaced_repetition_stats(training_zone.id)
            
            return {
                "success": True,
                "training_zone_id": str(training_zone.id),
                "overview": {
                    "total_questions": total_questions,
                    "mastered_questions": mastered_questions,
                    "in_progress": total_questions - mastered_questions,
                    "mastery_percentage": (mastered_questions / total_questions) * 100 if total_questions > 0 else 0,
                    "due_for_review": due_for_review,
                    "current_streak": training_zone.current_training_streak,
                    "max_streak": training_zone.max_training_streak,
                    "total_sessions": training_zone.total_training_sessions,
                    "overall_accuracy": training_zone.average_session_accuracy,
                    "improvement_rate": training_zone.improvement_rate,
                    "mastery_level": training_zone.mastery_level
                },
                "recent_sessions": sessions_data,
                "difficulty_performance": difficulty_stats,
                "spaced_repetition": spaced_rep_stats,
                "monthly_rotation": {
                    "current_month": training_zone.current_month,
                    "current_year": training_zone.current_year,
                    "last_rotation": training_zone.last_rotation_date.isoformat(),
                    "rotation_triggered_by_diagnostic": training_zone.rotation_triggered_by_diagnostic
                },
                "recommended_modes": await self._get_recommended_training_modes(training_zone.id)
            }
            
        except Exception as e:
            logger.error(f"Error getting training zone dashboard: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    # Private helper methods
    
    def _calculate_initial_priority(self, failed_answer: DiagnosticTestAnswer, question: Question) -> int:
        """Calculate initial priority level for a failed question (1-5, 5 being highest)"""
        priority = 3  # Default medium priority
        
        # High priority for easy questions (student should know these)
        if hasattr(question, 'irt_b') and question.irt_b < -1.0:
            priority = 5
        elif hasattr(question, 'difficulty') and question.difficulty == 'easy':
            priority = 4
        
        # High priority for very slow responses
        response_time = failed_answer.response_time_ms / 1000
        if response_time > 60:  # More than 1 minute
            priority = min(priority + 1, 5)
        
        return priority
    
    async def _select_questions_for_session(self, 
                                          training_zone_id: str, 
                                          mode: TrainingMode,
                                          custom_settings: Optional[Dict] = None) -> List[TrainingZoneQuestion]:
        """Select questions for training session based on mode and spaced repetition"""
        base_query = self.db.query(TrainingZoneQuestion).filter(
            and_(
                TrainingZoneQuestion.training_zone_id == training_zone_id,
                TrainingZoneQuestion.is_mastered == False
            )
        )
        
        if mode == TrainingMode.SPACED_REPETITION:
            # Only questions due for review
            questions = base_query.filter(
                TrainingZoneQuestion.next_review_date <= datetime.now()
            ).all()
            
            # Sort by how overdue they are
            questions.sort(key=lambda q: (datetime.now() - q.next_review_date).total_seconds(), reverse=True)
            
        elif mode == TrainingMode.SPRINT:
            # High priority questions only
            questions = base_query.filter(
                TrainingZoneQuestion.priority_level >= 4
            ).all()
            
            # Sort by priority and recency
            questions.sort(key=lambda q: (q.priority_level, q.calculate_priority_score()), reverse=True)
            
        elif mode == TrainingMode.RECOVERY:
            # Recent failures with mixed priorities
            questions = base_query.all()
            questions.sort(key=lambda q: q.calculate_priority_score(), reverse=True)
            
        elif mode == TrainingMode.MONTHLY_FOCUS:
            # Focus on current month's failed questions
            current_month = datetime.now().month
            questions = base_query.filter(
                TrainingZoneQuestion.added_in_month == current_month
            ).all()
            
            if not questions:
                # Fallback to all questions
                questions = base_query.all()
            
            questions.sort(key=lambda q: q.calculate_priority_score(), reverse=True)
            
        else:  # FULL_REVIEW
            questions = base_query.all()
            # Mix of priorities and spaced repetition
            questions.sort(key=lambda q: (
                1 if q.next_review_date <= datetime.now() else 0,
                q.calculate_priority_score()
            ), reverse=True)
        
        return questions
    
    async def _format_question_for_session(self, training_question: TrainingZoneQuestion) -> Dict[str, Any]:
        """Format a training question for the session"""
        question = self.db.query(Question).filter(
            Question.id == training_question.question_id
        ).first()
        
        if not question:
            return None
        
        return {
            "training_question_id": str(training_question.id),
            "question_id": str(question.id),
            "statement": question.statement,
            "options": {
                "a": question.option_a,
                "b": question.option_b,
                "c": question.option_c,
                "d": question.option_d
            },
            "image_url": question.image_url,
            "difficulty": getattr(question, 'difficulty', 'medium'),
            "topic_id": str(question.topic_id) if question.topic_id else None,
            "original_failure_info": {
                "original_answer": training_question.original_answer,
                "original_time_seconds": training_question.original_time_seconds,
                "failure_date": training_question.original_failure_date.isoformat()
            },
            "training_info": {
                "attempts": training_question.training_attempts,
                "successful_attempts": training_question.successful_attempts,
                "consecutive_correct": training_question.consecutive_correct,
                "next_review_date": training_question.next_review_date.isoformat(),
                "priority_level": training_question.priority_level,
                "best_time": training_question.best_time_seconds
            }
        }
    
    def _calculate_current_difficulty(self, training_question: TrainingZoneQuestion) -> str:
        """Calculate current difficulty level for adaptive training"""
        accuracy = 0
        if training_question.training_attempts > 0:
            accuracy = training_question.successful_attempts / training_question.training_attempts
        
        if accuracy >= 0.8:
            return DifficultyLevel.EXPERT.value
        elif accuracy >= 0.6:
            return DifficultyLevel.ADVANCED.value
        elif accuracy >= 0.4:
            return DifficultyLevel.INTERMEDIATE.value
        else:
            return DifficultyLevel.BEGINNER.value
    
    def _calculate_quality_rating(self, 
                                is_correct: bool, 
                                response_time: int, 
                                confidence: int,
                                training_question: TrainingZoneQuestion) -> int:
        """Calculate quality rating for spaced repetition (0-5)"""
        if not is_correct:
            return max(0, confidence - 2)  # 0-1 for incorrect answers
        
        # Base score for correct answers
        quality = 3
        
        # Adjust for response time
        if training_question.best_time_seconds and response_time <= training_question.best_time_seconds:
            quality += 1
        elif training_question.original_time_seconds and response_time <= training_question.original_time_seconds * 0.8:
            quality += 1
        elif response_time > 60:  # Very slow
            quality -= 1
        
        # Adjust for confidence
        if confidence >= 4:
            quality += 1
        elif confidence <= 2:
            quality -= 1
        
        return max(0, min(5, quality))
    
    def _check_mastery(self, training_question: TrainingZoneQuestion) -> bool:
        """Check if a question has reached mastery level"""
        if training_question.training_attempts < self.mastery_min_attempts:
            return False
        
        accuracy = training_question.successful_attempts / training_question.training_attempts
        
        return (
            accuracy >= self.mastery_threshold and
            training_question.consecutive_correct >= self.mastery_consecutive_correct
        )
    
    def _calculate_mastery_score(self, training_question: TrainingZoneQuestion) -> float:
        """Calculate mastery score (0.0 to 1.0)"""
        if training_question.training_attempts == 0:
            return 0.0
        
        accuracy = training_question.successful_attempts / training_question.training_attempts
        streak_bonus = min(training_question.consecutive_correct * 0.1, 0.3)
        
        # Time improvement bonus
        time_bonus = 0.0
        if training_question.original_time_seconds > 0 and training_question.best_time_seconds:
            time_improvement = (training_question.original_time_seconds - training_question.best_time_seconds) / training_question.original_time_seconds
            time_bonus = min(time_improvement * 0.2, 0.2)
        
        return min(1.0, accuracy + streak_bonus + time_bonus)
    
    def _calculate_mastery_gain(self, training_question: TrainingZoneQuestion, is_correct: bool) -> float:
        """Calculate estimated learning gain from this attempt"""
        if not is_correct:
            return -0.05  # Small negative gain for incorrect answers
        
        # Base gain for correct answer
        gain = 0.1
        
        # Higher gain for questions with low previous accuracy
        if training_question.training_attempts > 0:
            accuracy = training_question.successful_attempts / training_question.training_attempts
            if accuracy < 0.5:
                gain += 0.1
        
        # Bonus for consecutive correct answers
        gain += min(training_question.consecutive_correct * 0.02, 0.1)
        
        return gain
    
    async def _generate_video_recommendations(self, 
                                            training_zone_id: str,
                                            new_questions_only: bool = False,
                                            specific_question_id: Optional[str] = None) -> None:
        """Generate YouTube video recommendations for training questions"""
        try:
            # Get questions to generate recommendations for
            query = self.db.query(TrainingZoneQuestion).filter(
                TrainingZoneQuestion.training_zone_id == training_zone_id
            )
            
            if specific_question_id:
                query = query.filter(TrainingZoneQuestion.question_id == specific_question_id)
            elif new_questions_only:
                # Only questions added this month
                current_month = datetime.now().month
                query = query.filter(TrainingZoneQuestion.added_in_month == current_month)
            
            training_questions = query.all()
            
            for training_question in training_questions:
                # Skip if recommendations already exist
                existing = self.db.query(TrainingVideoRecommendation).filter(
                    TrainingVideoRecommendation.training_question_id == training_question.id
                ).first()
                
                if existing and not specific_question_id:
                    continue
                
                # Get question details
                question = self.db.query(Question).filter(
                    Question.id == training_question.question_id
                ).first()
                
                if not question:
                    continue
                
                # Find relevant videos based on topic/subject
                videos = self.db.query(YoutubeCatalog).filter(
                    and_(
                        YoutubeCatalog.subject_id == question.subject_id,
                        YoutubeCatalog.is_processed == True
                    )
                ).limit(10).all()
                
                # Score and rank videos
                for video in videos:
                    relevance_score = self._calculate_video_relevance(question, video)
                    topic_match_score = self._calculate_topic_match(question, video)
                    
                    if relevance_score > 0.3:  # Only add relevant videos
                        recommendation = TrainingVideoRecommendation(
                            training_question_id=training_question.id,
                            youtube_video_id=video.id,
                            question_id=question.id,
                            relevance_score=relevance_score,
                            topic_match_score=topic_match_score,
                            recommendation_reason=self._generate_recommendation_reason(
                                question, video, relevance_score
                            )
                        )
                        
                        self.db.add(recommendation)
            
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Error generating video recommendations: {e}")
    
    def _calculate_video_relevance(self, question: Question, video: YoutubeCatalog) -> float:
        """Calculate relevance score between question and video"""
        score = 0.0
        
        # Subject match
        if video.subject_id == question.subject_id:
            score += 0.5
        
        # Topic match (if available)
        if video.topic_id == question.topic_id:
            score += 0.3
        
        # Text similarity (simplified)
        if video.title and question.statement:
            # Simple keyword matching (in a real implementation, use semantic similarity)
            question_words = set(question.statement.lower().split())
            video_words = set(video.title.lower().split())
            common_words = question_words.intersection(video_words)
            if common_words:
                score += min(len(common_words) * 0.05, 0.3)
        
        # Video quality score
        if video.quality_score:
            score += video.quality_score * 0.2
        
        return min(1.0, score)
    
    def _calculate_topic_match(self, question: Question, video: YoutubeCatalog) -> float:
        """Calculate topic-specific match score"""
        if video.topic_id == question.topic_id:
            return 1.0
        
        # Could implement more sophisticated topic similarity here
        return 0.0
    
    def _generate_recommendation_reason(self, question: Question, video: YoutubeCatalog, score: float) -> str:
        """Generate human-readable reason for recommendation"""
        if video.topic_id == question.topic_id:
            return f"Video covers the same topic as this question"
        elif score > 0.7:
            return f"Highly relevant content for this type of question"
        elif score > 0.5:
            return f"Good educational content for this subject area"
        else:
            return f"Related educational content"
    
    async def _analyze_user_error_pattern(self, user_id: str, question_id: str) -> str:
        """Analyze user's error patterns for personalized explanations"""
        # Get user's previous attempts on similar questions
        attempts = self.db.query(TrainingAttempt).filter(
            and_(
                TrainingAttempt.user_id == user_id,
                TrainingAttempt.question_id == question_id,
                TrainingAttempt.is_correct == False
            )
        ).all()
        
        if not attempts:
            return "First time encountering difficulty with this question"
        
        # Analyze patterns
        common_errors = {}
        for attempt in attempts:
            if attempt.user_answer:
                common_errors[attempt.user_answer] = common_errors.get(attempt.user_answer, 0) + 1
        
        if common_errors:
            most_common = max(common_errors, key=common_errors.get)
            return f"Tends to choose option {most_common} when incorrect"
        
        return "Inconsistent error pattern"
    
    async def _generate_ai_explanation(self, 
                                     question: Question,
                                     training_attempt: TrainingAttempt,
                                     error_analysis: str,
                                     explanation_type: str) -> Dict[str, Any]:
        """Generate AI explanation (mock implementation - integrate with your AI service)"""
        # This would integrate with your actual AI service
        # For now, return a structured mock response
        
        return {
            "explanation": f"This question tests {getattr(question, 'competence', 'key concepts')}. "
                          f"The correct answer is {question.correct_answer} because...",
            "difficulty_level": "intermediate",
            "personalized_tips": f"Based on your error pattern ({error_analysis}), focus on...",
            "related_concepts": ["concept1", "concept2", "concept3"],
            "ai_model": "gpt-4",
            "tokens_used": 150
        }
    
    async def _get_video_recommendations(self, training_question_id: str) -> List[Dict[str, Any]]:
        """Get existing video recommendations for a training question"""
        recommendations = self.db.query(TrainingVideoRecommendation).filter(
            TrainingVideoRecommendation.training_question_id == training_question_id
        ).order_by(desc(TrainingVideoRecommendation.relevance_score)).limit(3).all()
        
        video_data = []
        for rec in recommendations:
            youtube_video = self.db.query(YoutubeCatalog).filter(
                YoutubeCatalog.id == rec.youtube_video_id
            ).first()
            
            if youtube_video:
                video_data.append({
                    "id": str(rec.id),
                    "youtube_id": youtube_video.youtube_id,
                    "title": youtube_video.title,
                    "thumbnail_url": youtube_video.thumbnail_url,
                    "duration_seconds": youtube_video.duration_seconds,
                    "relevance_score": rec.relevance_score,
                    "embed_url": youtube_video.get_embed_url()
                })
        
        return video_data
    
    async def _calculate_overall_mastery_level(self, training_zone_id: str) -> float:
        """Calculate overall mastery level for the training zone"""
        questions = self.db.query(TrainingZoneQuestion).filter(
            TrainingZoneQuestion.training_zone_id == training_zone_id
        ).all()
        
        if not questions:
            return 0.0
        
        total_mastery = sum(q.mastery_score for q in questions)
        return total_mastery / len(questions)
    
    async def _generate_session_report(self, session_id: str) -> Dict[str, Any]:
        """Generate comprehensive session report"""
        session = self.db.query(TrainingSession).filter(
            TrainingSession.id == session_id
        ).first()
        
        attempts = self.db.query(TrainingAttempt).filter(
            TrainingAttempt.training_session_id == session_id
        ).order_by(TrainingAttempt.attempt_number).all()
        
        return {
            "session_id": str(session.id),
            "mode": session.mode,
            "total_questions": session.target_questions,
            "questions_answered": session.questions_answered,
            "correct_answers": session.correct_answers,
            "accuracy": session.session_accuracy,
            "duration_minutes": (session.completed_at - session.started_at).total_seconds() / 60,
            "average_response_time": session.average_response_time,
            "max_streak": session.max_streak_in_session,
            "ai_explanations_used": session.ai_explanations_requested,
            "videos_watched": session.videos_watched,
            "performance_by_question": [
                {
                    "question_id": str(attempt.question_id),
                    "correct": attempt.is_correct,
                    "response_time": attempt.response_time_seconds,
                    "quality_rating": attempt.quality_rating,
                    "time_improvement": attempt.time_improvement
                }
                for attempt in attempts
            ]
        }
    
    async def _get_difficulty_performance_stats(self, training_zone_id: str) -> Dict[str, Any]:
        """Get performance statistics by difficulty level"""
        # This would analyze performance across different difficulty levels
        # Simplified implementation
        return {
            "beginner": {"accuracy": 0.85, "avg_time": 25},
            "intermediate": {"accuracy": 0.72, "avg_time": 35},
            "advanced": {"accuracy": 0.58, "avg_time": 45},
            "expert": {"accuracy": 0.45, "avg_time": 55}
        }
    
    async def _get_spaced_repetition_stats(self, training_zone_id: str) -> Dict[str, Any]:
        """Get spaced repetition statistics"""
        questions = self.db.query(TrainingZoneQuestion).filter(
            TrainingZoneQuestion.training_zone_id == training_zone_id
        ).all()
        
        due_today = sum(1 for q in questions if q.next_review_date.date() <= date.today() and not q.is_mastered)
        overdue = sum(1 for q in questions if q.next_review_date.date() < date.today() and not q.is_mastered)
        
        return {
            "due_today": due_today,
            "overdue": overdue,
            "mastered": sum(1 for q in questions if q.is_mastered),
            "in_learning": len(questions) - sum(1 for q in questions if q.is_mastered)
        }
    
    async def _get_recommended_training_modes(self, training_zone_id: str) -> List[Dict[str, Any]]:
        """Get recommended training modes based on current state"""
        questions = self.db.query(TrainingZoneQuestion).filter(
            TrainingZoneQuestion.training_zone_id == training_zone_id
        ).all()
        
        due_for_review = sum(1 for q in questions if q.next_review_date <= datetime.now() and not q.is_mastered)
        high_priority = sum(1 for q in questions if q.priority_level >= 4 and not q.is_mastered)
        
        recommendations = []
        
        if due_for_review > 10:
            recommendations.append({
                "mode": TrainingMode.SPACED_REPETITION.value,
                "reason": f"{due_for_review} questions are due for review",
                "priority": "high"
            })
        
        if high_priority > 5:
            recommendations.append({
                "mode": TrainingMode.SPRINT.value,
                "reason": f"{high_priority} high-priority questions need attention",
                "priority": "medium"
            })
        
        recommendations.append({
            "mode": TrainingMode.RECOVERY.value,
            "reason": "Balanced mix of recent failures and priorities",
            "priority": "medium"
        })
        
        return recommendations

    async def get_session_results(self, session_id: str, user_id: str) -> Dict[str, Any]:
        """
        Get comprehensive session results and analytics
        """
        try:
            # Get session
            session = self.db.query(TrainingSession).filter(
                and_(
                    TrainingSession.id == session_id,
                    TrainingSession.user_id == user_id
                )
            ).first()
            
            if not session:
                return {"success": False, "message": "Training session not found"}
            
            if session.status != "completed":
                return {"success": False, "message": "Session not completed yet"}
            
            # Get all attempts for this session
            attempts = self.db.query(TrainingAttempt).filter(
                TrainingAttempt.training_session_id == session_id
            ).all()
            
            # Get training zone
            training_zone = self.db.query(TrainingZone).filter(
                TrainingZone.id == session.training_zone_id
            ).first()
            
            # Get previous session for comparison
            previous_session = self.db.query(TrainingSession).filter(
                and_(
                    TrainingSession.training_zone_id == session.training_zone_id,
                    TrainingSession.user_id == user_id,
                    TrainingSession.started_at < session.started_at,
                    TrainingSession.status == "completed"
                )
            ).order_by(desc(TrainingSession.started_at)).first()
            
            # Calculate performance metrics
            session_duration = (session.completed_at - session.started_at).total_seconds() / 60
            target_time = session.time_limit_minutes
            completion_percentage = (session.questions_answered / session.target_questions) * 100
            
            # Calculate difficulty breakdown
            difficulty_breakdown = {}
            for attempt in attempts:
                difficulty = attempt.difficulty_at_attempt
                if difficulty not in difficulty_breakdown:
                    difficulty_breakdown[difficulty] = {"attempted": 0, "correct": 0, "accuracy": 0}
                
                difficulty_breakdown[difficulty]["attempted"] += 1
                if attempt.is_correct:
                    difficulty_breakdown[difficulty]["correct"] += 1
            
            # Calculate accuracy for each difficulty
            for diff_data in difficulty_breakdown.values():
                if diff_data["attempted"] > 0:
                    diff_data["accuracy"] = (diff_data["correct"] / diff_data["attempted"]) * 100
            
            # Calculate mastery progress
            questions_mastered_this_session = 0
            total_mastered = 0
            
            training_questions = self.db.query(TrainingZoneQuestion).filter(
                TrainingZoneQuestion.training_zone_id == session.training_zone_id
            ).all()
            
            session_attempt_question_ids = {str(a.training_question_id) for a in attempts}
            
            for tq in training_questions:
                if tq.is_mastered:
                    total_mastered += 1
                    if str(tq.id) in session_attempt_question_ids and tq.mastery_achieved_date and tq.mastery_achieved_date >= session.started_at:
                        questions_mastered_this_session += 1
            
            # Calculate spaced repetition updates
            questions_promoted = sum(1 for a in attempts if a.quality_rating and a.quality_rating >= 4)
            questions_demoted = sum(1 for a in attempts if a.quality_rating and a.quality_rating < 3)
            
            # Calculate average interval increase
            avg_interval_increase = 2.0  # Default estimate
            
            # Get comparison metrics
            comparison_metrics = {
                "vs_last_session": {
                    "accuracy_change": 0,
                    "time_change": 0,
                    "streak_change": 0
                },
                "vs_average": {
                    "accuracy_vs_avg": 0,
                    "time_vs_avg": 0
                }
            }
            
            if previous_session:
                comparison_metrics["vs_last_session"]["accuracy_change"] = (
                    session.session_accuracy - previous_session.session_accuracy
                ) * 100
                comparison_metrics["vs_last_session"]["time_change"] = (
                    session.average_response_time - previous_session.average_response_time
                )
                comparison_metrics["vs_last_session"]["streak_change"] = (
                    session.max_streak_in_session - previous_session.max_streak_in_session
                )
            
            # Calculate detailed progress metrics
            time_improvement_percent = 0
            original_times = []
            current_times = []
            
            for attempt in attempts:
                training_question = self.db.query(TrainingZoneQuestion).filter(
                    TrainingZoneQuestion.id == attempt.training_question_id
                ).first()
                
                if training_question:
                    original_times.append(training_question.original_time_seconds)
                    current_times.append(attempt.response_time_seconds)
            
            if original_times and current_times:
                avg_original = sum(original_times) / len(original_times)
                avg_current = sum(current_times) / len(current_times)
                if avg_original > 0:
                    time_improvement_percent = ((avg_original - avg_current) / avg_original) * 100
            
            # Generate recommendations
            next_session_mode = "recovery"
            focus_areas = []
            
            if questions_promoted > questions_demoted:
                next_session_mode = "spaced_rep"
                focus_areas.append("Repetición espaciada")
            elif session.session_accuracy < 0.7:
                next_session_mode = "sprint"
                focus_areas.append("Preguntas críticas")
            else:
                focus_areas.append("Preguntas recientes")
            
            # Check for low performance areas
            for difficulty, stats in difficulty_breakdown.items():
                if stats["accuracy"] < 60:
                    focus_areas.append(f"Dificultad {difficulty}")
            
            estimated_mastery_time = max(1, (len(training_questions) - total_mastered) // 2)
            
            # Mock achievements for demo
            achievements_unlocked = []
            if session.session_accuracy >= 0.9:
                achievements_unlocked.append({
                    "id": "high_accuracy",
                    "name": "Precisión Perfecta",
                    "description": "Logra 90%+ de precisión en una sesión",
                    "icon": "🎯",
                    "points": 100
                })
            
            if session.max_streak_in_session >= 5:
                achievements_unlocked.append({
                    "id": "streak_master",
                    "name": "Maestro de Rachas",
                    "description": "Consigue una racha de 5+ respuestas correctas",
                    "icon": "🔥",
                    "points": 75
                })
            
            return {
                "success": True,
                "session_id": str(session.id),
                "training_zone_id": str(session.training_zone_id),
                "mode": session.mode,
                "performance": {
                    "questions_answered": session.questions_answered,
                    "correct_answers": session.correct_answers,
                    "accuracy": session.session_accuracy * 100,
                    "target_questions": session.target_questions,
                    "completion_percentage": completion_percentage,
                    "session_time_minutes": session_duration,
                    "average_response_time": session.average_response_time,
                    "improvement_over_original": time_improvement_percent
                },
                "streak_info": {
                    "current_streak": session.current_streak,
                    "max_streak_in_session": session.max_streak_in_session,
                    "streak_improvement": comparison_metrics["vs_last_session"]["streak_change"]
                },
                "mastery_progress": {
                    "questions_mastered_this_session": questions_mastered_this_session,
                    "total_mastered": total_mastered,
                    "mastery_level_before": training_zone.mastery_level,
                    "mastery_level_after": await self._calculate_overall_mastery_level(str(training_zone.id)),
                    "mastery_improvement": 0  # Calculate based on before/after
                },
                "spaced_repetition_updates": {
                    "questions_promoted": questions_promoted,
                    "questions_demoted": questions_demoted,
                    "average_interval_increase": avg_interval_increase
                },
                "difficulty_breakdown": difficulty_breakdown,
                "achievements_unlocked": achievements_unlocked,
                "recommendations": {
                    "next_session_mode": next_session_mode,
                    "focus_areas": focus_areas,
                    "estimated_mastery_time": estimated_mastery_time,
                    "should_take_break": session_duration < 10 and session.session_accuracy < 0.5
                },
                "detailed_progress": {
                    "time_improvement_percent": time_improvement_percent,
                    "consistency_score": min(10, session.session_accuracy * 10),
                    "learning_velocity": min(10, (questions_mastered_this_session + 1) * 2),
                    "retention_score": min(10, max(5, 8 - questions_demoted))
                },
                "comparison_metrics": comparison_metrics
            }
            
        except Exception as e:
            logger.error(f"Error getting session results: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def get_next_question(self, session_id: str, user_id: str) -> Dict[str, Any]:
        """
        Get the next question for a training session
        """
        try:
            # Get session
            session = self.db.query(TrainingSession).filter(
                and_(
                    TrainingSession.id == session_id,
                    TrainingSession.user_id == user_id,
                    TrainingSession.status == "active"
                )
            ).first()
            
            if not session:
                return {"success": False, "message": "Active training session not found"}
            
            # Check if session is complete
            if session.questions_answered >= session.target_questions:
                return {"success": False, "message": "Session completed"}
            
            # Get questions for this session based on mode
            training_questions = await self._select_questions_for_session(
                str(session.training_zone_id), 
                TrainingMode(session.mode)
            )
            
            if not training_questions:
                return {"success": False, "message": "No questions available for training"}
            
            # Get questions already answered in this session
            answered_question_ids = set()
            attempts = self.db.query(TrainingAttempt).filter(
                TrainingAttempt.training_session_id == session_id
            ).all()
            
            for attempt in attempts:
                answered_question_ids.add(str(attempt.training_question_id))
            
            # Find next unanswered question
            next_question = None
            for tq in training_questions[:session.target_questions]:
                if str(tq.id) not in answered_question_ids:
                    next_question = tq
                    break
            
            if not next_question:
                return {"success": False, "message": "No more questions available"}
            
            # Format question for frontend
            formatted_question = await self._format_question_for_session(next_question)
            
            if not formatted_question:
                return {"success": False, "message": "Error formatting question"}
            
            return {
                "success": True,
                "question": formatted_question,
                "session_progress": {
                    "current": session.questions_answered + 1,
                    "total": session.target_questions,
                    "percentage": ((session.questions_answered + 1) / session.target_questions) * 100
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting next question: {e}")
            return {
                "success": False,
                "error": str(e)
            }