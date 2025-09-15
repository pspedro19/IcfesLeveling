"""
Enhanced Personalized Study Plan System
Generates individual YAML files for each student by subject based on diagnostic weaknesses
"""

import yaml
import json
import uuid
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from sqlalchemy.orm import Session
from sqlalchemy import text
from dataclasses import dataclass, asdict

from ..models.diagnostic_test import DiagnosticTest, DiagnosticTestAnswer
from ..models.question_video_recommendations import QuestionVideoRecommendations
from ..models.youtube_catalog import YoutubeCatalog
from ..models.study_plan import StudyPlan, PlanProgress
from ..core.database import get_db

logger = logging.getLogger(__name__)

@dataclass
class PersonalizedUnit:
    """Represents a personalized learning unit"""
    unit_number: int
    title: str
    description: str
    focus_area: str
    difficulty_level: int
    estimated_hours: float
    videos: List[Dict[str, Any]]
    practice_questions: List[str]
    learning_objectives: List[str]
    weak_concepts: List[str]
    priority_score: float

@dataclass
class StudyPlanMetadata:
    """Metadata for the study plan"""
    student_id: str
    subject_id: str
    diagnostic_test_id: str
    weakness_areas: List[str]
    strength_areas: List[str]
    overall_score: float
    target_improvement: float
    plan_duration_weeks: int
    reassessment_date: str
    created_at: str
    version: str

class PersonalizedStudyPlanGenerator:
    """
    Advanced generator for creating personalized study plans based on diagnostic weaknesses
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.storage_path = Path("/root/IcfesLeveling/storage/study_plans")
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
    async def generate_personalized_plan(
        self,
        user_id: str,
        subject_id: str,
        diagnostic_test_id: str,
        target_weeks: int = 8
    ) -> Dict[str, Any]:
        """
        Generate a comprehensive personalized study plan
        """
        try:
            logger.info(f"🎯 Generating personalized plan for user {user_id}, subject {subject_id}")
            
            # 1. Analyze diagnostic test results
            diagnostic_analysis = await self._analyze_diagnostic_results(
                user_id, subject_id, diagnostic_test_id
            )
            
            if not diagnostic_analysis['success']:
                return diagnostic_analysis
            
            # 2. Extract weakness patterns and create targeted learning units
            learning_units = await self._create_targeted_learning_units(
                diagnostic_analysis['weakness_data'],
                subject_id,
                target_weeks
            )
            
            # 3. Match videos to failed questions using advanced recommendation engine
            video_recommendations = await self._get_personalized_video_recommendations(
                diagnostic_analysis['failed_questions'],
                subject_id
            )
            
            # 4. Organize units with matched videos
            enriched_units = await self._enrich_units_with_videos(
                learning_units,
                video_recommendations
            )
            
            # 5. Create YAML structure
            study_plan_yaml = await self._create_study_plan_yaml(
                user_id,
                subject_id,
                diagnostic_test_id,
                enriched_units,
                diagnostic_analysis
            )
            
            # 6. Save to both database and file system
            plan_id = await self._save_study_plan(
                user_id,
                subject_id,
                study_plan_yaml,
                enriched_units,
                diagnostic_analysis
            )
            
            # 7. Schedule reassessment reminder
            await self._schedule_monthly_reassessment(user_id, subject_id, plan_id)
            
            return {
                'success': True,
                'plan_id': plan_id,
                'file_path': f"{self.storage_path}/{user_id}_{subject_id}_{plan_id}.yaml",
                'units': len(enriched_units),
                'total_videos': sum(len(unit.videos) for unit in enriched_units),
                'estimated_duration_weeks': target_weeks,
                'weakness_areas': diagnostic_analysis['weakness_areas'],
                'message': 'Personalized study plan generated successfully'
            }
            
        except Exception as e:
            logger.error(f"❌ Error generating personalized plan: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to generate personalized study plan'
            }
    
    async def _analyze_diagnostic_results(
        self,
        user_id: str,
        subject_id: str,
        diagnostic_test_id: str
    ) -> Dict[str, Any]:
        """
        Deep analysis of diagnostic test to identify specific weaknesses
        """
        try:
            # Get diagnostic test with answers
            query = text("""
                SELECT 
                    dt.id,
                    dt.score_percentage,
                    dt.strengths,
                    dt.weaknesses,
                    dt.score_by_topic,
                    json_agg(
                        json_build_object(
                            'question_id', dta.question_id,
                            'user_answer', dta.user_answer,
                            'is_correct', dta.is_correct,
                            'topic_id', dta.topic_id,
                            'response_time', dta.response_time_ms,
                            'question_text', q.question_text,
                            'correct_answer', q.correct_answer,
                            'difficulty_theta', q.difficulty_theta,
                            'topic_name', t.name
                        )
                    ) as answers
                FROM diagnostic_tests dt
                LEFT JOIN diagnostic_test_answers dta ON dt.id = dta.diagnostic_test_id
                LEFT JOIN questions q ON dta.question_id = q.id
                LEFT JOIN topics t ON dta.topic_id = t.id
                WHERE dt.id = :diagnostic_test_id 
                AND dt.user_id = :user_id 
                AND dt.subject_id = :subject_id
                GROUP BY dt.id
            """)
            
            result = self.db.execute(query, {
                'diagnostic_test_id': diagnostic_test_id,
                'user_id': user_id,
                'subject_id': subject_id
            }).first()
            
            if not result:
                return {
                    'success': False,
                    'error': 'Diagnostic test not found'
                }
            
            answers = json.loads(result[5]) if result[5] else []
            failed_questions = [ans for ans in answers if not ans['is_correct']]
            correct_questions = [ans for ans in answers if ans['is_correct']]
            
            # Analyze weakness patterns
            weakness_analysis = self._analyze_weakness_patterns(failed_questions)
            strength_analysis = self._analyze_strength_patterns(correct_questions)
            
            return {
                'success': True,
                'overall_score': result[1],
                'strengths': json.loads(result[2]) if result[2] else [],
                'weaknesses': json.loads(result[3]) if result[3] else [],
                'score_by_topic': json.loads(result[4]) if result[4] else {},
                'failed_questions': failed_questions,
                'correct_questions': correct_questions,
                'weakness_data': weakness_analysis,
                'strength_data': strength_analysis,
                'weakness_areas': list(weakness_analysis.keys()),
                'total_questions': len(answers),
                'accuracy_rate': len(correct_questions) / len(answers) if answers else 0
            }
            
        except Exception as e:
            logger.error(f"Error analyzing diagnostic results: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _analyze_weakness_patterns(self, failed_questions: List[Dict]) -> Dict[str, Dict]:
        """
        Advanced analysis of failure patterns to identify specific learning gaps
        """
        weakness_data = {}
        
        for question in failed_questions:
            topic_name = question.get('topic_name', 'General')
            difficulty = question.get('difficulty_theta', 0)
            response_time = question.get('response_time', 0)
            
            if topic_name not in weakness_data:
                weakness_data[topic_name] = {
                    'failed_count': 0,
                    'average_difficulty': 0,
                    'average_response_time': 0,
                    'question_ids': [],
                    'difficulty_levels': [],
                    'response_times': [],
                    'priority_score': 0
                }
            
            weakness_data[topic_name]['failed_count'] += 1
            weakness_data[topic_name]['question_ids'].append(question['question_id'])
            weakness_data[topic_name]['difficulty_levels'].append(difficulty)
            weakness_data[topic_name]['response_times'].append(response_time)
        
        # Calculate aggregated metrics
        for topic, data in weakness_data.items():
            data['average_difficulty'] = sum(data['difficulty_levels']) / len(data['difficulty_levels'])
            data['average_response_time'] = sum(data['response_times']) / len(data['response_times'])
            # Priority score: combines frequency and difficulty
            data['priority_score'] = data['failed_count'] * (1 + data['average_difficulty'])
        
        return weakness_data
    
    def _analyze_strength_patterns(self, correct_questions: List[Dict]) -> Dict[str, Dict]:
        """
        Analyze areas where student performed well
        """
        strength_data = {}
        
        for question in correct_questions:
            topic_name = question.get('topic_name', 'General')
            difficulty = question.get('difficulty_theta', 0)
            
            if topic_name not in strength_data:
                strength_data[topic_name] = {
                    'correct_count': 0,
                    'average_difficulty': 0,
                    'question_ids': [],
                    'mastery_level': 0
                }
            
            strength_data[topic_name]['correct_count'] += 1
            strength_data[topic_name]['question_ids'].append(question['question_id'])
            strength_data[topic_name]['average_difficulty'] += difficulty
        
        # Calculate mastery levels
        for topic, data in strength_data.items():
            if data['correct_count'] > 0:
                data['average_difficulty'] = data['average_difficulty'] / data['correct_count']
                data['mastery_level'] = min(1.0, data['correct_count'] * 0.2 + data['average_difficulty'] * 0.3)
        
        return strength_data
    
    async def _create_targeted_learning_units(
        self,
        weakness_data: Dict[str, Dict],
        subject_id: str,
        target_weeks: int
    ) -> List[PersonalizedUnit]:
        """
        Create learning units specifically targeting identified weaknesses
        """
        units = []
        
        # Sort weaknesses by priority score
        sorted_weaknesses = sorted(
            weakness_data.items(),
            key=lambda x: x[1]['priority_score'],
            reverse=True
        )
        
        units_per_week = max(1, len(sorted_weaknesses) // target_weeks)
        
        for i, (topic, weakness_info) in enumerate(sorted_weaknesses):
            unit_number = i + 1
            
            # Determine difficulty level based on failed questions
            avg_difficulty = weakness_info['average_difficulty']
            if avg_difficulty < -1:
                difficulty_level = 1  # Basic
            elif avg_difficulty < 0:
                difficulty_level = 2  # Intermediate
            else:
                difficulty_level = 3  # Advanced
            
            # Calculate estimated hours based on weakness severity
            base_hours = 4
            severity_multiplier = min(2.0, weakness_info['failed_count'] / 3)
            estimated_hours = base_hours * severity_multiplier
            
            unit = PersonalizedUnit(
                unit_number=unit_number,
                title=f"Unit {unit_number}: {topic} Mastery",
                description=f"Target your weakness in {topic} with personalized content",
                focus_area=topic,
                difficulty_level=difficulty_level,
                estimated_hours=estimated_hours,
                videos=[],  # Will be populated later
                practice_questions=weakness_info['question_ids'],
                learning_objectives=self._generate_learning_objectives(topic, weakness_info),
                weak_concepts=self._extract_weak_concepts(topic, weakness_info),
                priority_score=weakness_info['priority_score']
            )
            
            units.append(unit)
        
        return units
    
    def _generate_learning_objectives(self, topic: str, weakness_info: Dict) -> List[str]:
        """
        Generate specific learning objectives based on topic and weakness patterns
        """
        objectives = [
            f"Master fundamental concepts in {topic}",
            f"Solve {topic} problems with 80% accuracy",
            f"Apply {topic} concepts to complex scenarios"
        ]
        
        # Add specific objectives based on difficulty level
        avg_difficulty = weakness_info['average_difficulty']
        if avg_difficulty < -1:
            objectives.extend([
                f"Understand basic terminology in {topic}",
                f"Recognize {topic} problem patterns"
            ])
        elif avg_difficulty > 0:
            objectives.extend([
                f"Analyze advanced {topic} problems",
                f"Synthesize {topic} concepts across disciplines"
            ])
        
        return objectives
    
    def _extract_weak_concepts(self, topic: str, weakness_info: Dict) -> List[str]:
        """
        Extract specific weak concepts within a topic
        """
        # This would ideally analyze question content to extract specific concepts
        # For now, return general concepts based on topic
        concept_map = {
            'Algebra': ['Linear equations', 'Quadratic functions', 'Factorization'],
            'Geometry': ['Area calculations', 'Angle relationships', 'Similar triangles'],
            'Probability': ['Basic probability', 'Conditional probability', 'Combinations'],
            'Reading Comprehension': ['Main idea identification', 'Inference skills', 'Vocabulary'],
            'Grammar': ['Verb tenses', 'Subject-verb agreement', 'Punctuation'],
            'Chemistry': ['Chemical bonding', 'Stoichiometry', 'Periodic table'],
            'Physics': ['Motion equations', 'Force calculations', 'Energy conservation']
        }
        
        return concept_map.get(topic, [f"Basic {topic} concepts", f"Applied {topic} problems"])
    
    async def _get_personalized_video_recommendations(
        self,
        failed_questions: List[Dict],
        subject_id: str
    ) -> Dict[str, List[Dict]]:
        """
        Get YouTube video recommendations matched to specific failed questions
        """
        video_recommendations = {}
        
        try:
            for question in failed_questions:
                question_id = question['question_id']
                topic_name = question.get('topic_name', 'General')
                
                # Get video recommendations for this specific question
                query = text("""
                    SELECT 
                        qvr.total_score,
                        qvr.recommendation_type,
                        qvr.confidence_level,
                        qvr.learning_objective,
                        yc.youtube_id,
                        yc.title,
                        yc.url,
                        yc.duration_seconds,
                        yc.channel_name,
                        yc.tema_principal,
                        yc.quality_score
                    FROM question_video_recommendations qvr
                    JOIN youtube_catalog yc ON qvr.video_id = yc.id
                    WHERE qvr.question_id = :question_id
                    AND qvr.is_active = true
                    AND qvr.total_score >= 0.6
                    ORDER BY qvr.total_score DESC, yc.quality_score DESC
                    LIMIT 3
                """)
                
                results = self.db.execute(query, {'question_id': question_id}).fetchall()
                
                if topic_name not in video_recommendations:
                    video_recommendations[topic_name] = []
                
                for row in results:
                    video_data = {
                        'question_id': question_id,
                        'youtube_id': row[4],
                        'title': row[5],
                        'url': row[6],
                        'duration_seconds': row[7],
                        'duration_minutes': row[7] // 60 if row[7] else 0,
                        'channel_name': row[8],
                        'topic': row[9],
                        'recommendation_score': float(row[0]),
                        'recommendation_type': row[1],
                        'confidence_level': row[2],
                        'learning_objective': row[3],
                        'quality_score': float(row[10]) if row[10] else 0,
                        'xp_value': self._calculate_video_xp(row[7], float(row[0]))
                    }
                    
                    video_recommendations[topic_name].append(video_data)
            
            # If no specific recommendations found, get general topic videos
            for topic in video_recommendations.keys():
                if len(video_recommendations[topic]) < 2:
                    general_videos = await self._get_general_topic_videos(topic, subject_id)
                    video_recommendations[topic].extend(general_videos)
            
        except Exception as e:
            logger.error(f"Error getting video recommendations: {e}")
        
        return video_recommendations
    
    async def _get_general_topic_videos(self, topic: str, subject_id: str) -> List[Dict]:
        """
        Get general videos for a topic when specific recommendations aren't available
        """
        try:
            # Get subject name
            subject_query = text("SELECT name FROM subjects WHERE id = :subject_id")
            subject_result = self.db.execute(subject_query, {'subject_id': subject_id}).first()
            subject_name = subject_result[0] if subject_result else 'Mathematics'
            
            query = text("""
                SELECT 
                    youtube_id,
                    title,
                    url,
                    duration_seconds,
                    channel_name,
                    tema_principal,
                    quality_score
                FROM youtube_catalog
                WHERE area_evaluada = :subject_name
                AND (
                    LOWER(tema_principal) LIKE LOWER(:topic_pattern)
                    OR LOWER(title) LIKE LOWER(:topic_pattern)
                )
                AND processing_status = 'completed'
                ORDER BY quality_score DESC, view_count DESC
                LIMIT 2
            """)
            
            results = self.db.execute(query, {
                'subject_name': subject_name,
                'topic_pattern': f'%{topic}%'
            }).fetchall()
            
            videos = []
            for row in results:
                videos.append({
                    'question_id': None,
                    'youtube_id': row[0],
                    'title': row[1],
                    'url': row[2],
                    'duration_seconds': row[3],
                    'duration_minutes': row[3] // 60 if row[3] else 0,
                    'channel_name': row[4],
                    'topic': row[5],
                    'recommendation_score': 0.5,
                    'recommendation_type': 'general_topic',
                    'confidence_level': 'medium',
                    'learning_objective': f'Understand {topic} concepts',
                    'quality_score': float(row[6]) if row[6] else 0,
                    'xp_value': self._calculate_video_xp(row[3], 0.5)
                })
            
            return videos
            
        except Exception as e:
            logger.error(f"Error getting general topic videos: {e}")
            return []
    
    def _calculate_video_xp(self, duration_seconds: int, recommendation_score: float) -> int:
        """
        Calculate XP value for a video based on duration and recommendation quality
        """
        if not duration_seconds:
            return 10
        
        base_xp = min(100, duration_seconds // 60 * 5)  # 5 XP per minute, max 100
        quality_multiplier = 0.5 + (recommendation_score * 0.5)  # 0.5 to 1.0 multiplier
        
        return int(base_xp * quality_multiplier)
    
    async def _enrich_units_with_videos(
        self,
        learning_units: List[PersonalizedUnit],
        video_recommendations: Dict[str, List[Dict]]
    ) -> List[PersonalizedUnit]:
        """
        Enrich learning units with matched video recommendations
        """
        for unit in learning_units:
            topic = unit.focus_area
            if topic in video_recommendations:
                # Sort videos by recommendation score and limit to top 5
                videos = sorted(
                    video_recommendations[topic],
                    key=lambda x: x['recommendation_score'],
                    reverse=True
                )[:5]
                
                unit.videos = videos
            
            # Ensure minimum videos per unit
            if len(unit.videos) < 2:
                # Add placeholder or search for more general videos
                additional_videos = await self._get_general_topic_videos(topic, "general")
                unit.videos.extend(additional_videos[:2 - len(unit.videos)])
        
        return learning_units
    
    async def _create_study_plan_yaml(
        self,
        user_id: str,
        subject_id: str,
        diagnostic_test_id: str,
        units: List[PersonalizedUnit],
        diagnostic_analysis: Dict
    ) -> str:
        """
        Create comprehensive YAML structure for the personalized study plan
        """
        plan_metadata = StudyPlanMetadata(
            student_id=user_id,
            subject_id=subject_id,
            diagnostic_test_id=diagnostic_test_id,
            weakness_areas=diagnostic_analysis['weakness_areas'],
            strength_areas=list(diagnostic_analysis['strength_data'].keys()),
            overall_score=diagnostic_analysis['overall_score'],
            target_improvement=min(95.0, diagnostic_analysis['overall_score'] + 20.0),
            plan_duration_weeks=len(units),
            reassessment_date=(datetime.now() + timedelta(weeks=4)).isoformat(),
            created_at=datetime.now().isoformat(),
            version="2.1"
        )
        
        yaml_structure = {
            'personalized_study_plan': {
                'metadata': asdict(plan_metadata),
                'diagnostic_summary': {
                    'total_questions': diagnostic_analysis['total_questions'],
                    'accuracy_rate': round(diagnostic_analysis['accuracy_rate'], 3),
                    'primary_weaknesses': diagnostic_analysis['weakness_areas'][:3],
                    'main_strengths': list(diagnostic_analysis['strength_data'].keys())[:3]
                },
                'learning_path': {
                    'total_units': len(units),
                    'estimated_total_hours': sum(unit.estimated_hours for unit in units),
                    'units': [
                        {
                            'unit_number': unit.unit_number,
                            'title': unit.title,
                            'description': unit.description,
                            'focus_area': unit.focus_area,
                            'difficulty_level': unit.difficulty_level,
                            'estimated_hours': unit.estimated_hours,
                            'priority_score': unit.priority_score,
                            'learning_objectives': unit.learning_objectives,
                            'weak_concepts': unit.weak_concepts,
                            'recommended_videos': [
                                {
                                    'youtube_id': video['youtube_id'],
                                    'title': video['title'],
                                    'url': video['url'],
                                    'duration_minutes': video['duration_minutes'],
                                    'channel': video['channel_name'],
                                    'recommendation_score': video['recommendation_score'],
                                    'xp_value': video['xp_value'],
                                    'learning_objective': video['learning_objective'],
                                    'confidence_level': video['confidence_level']
                                }
                                for video in unit.videos
                            ],
                            'practice_questions': unit.practice_questions,
                            'completion_criteria': {
                                'videos_watched': len(unit.videos),
                                'practice_accuracy': 0.8,
                                'min_time_spent_hours': unit.estimated_hours * 0.7
                            }
                        }
                        for unit in units
                    ]
                },
                'reassessment_plan': {
                    'schedule_date': (datetime.now() + timedelta(weeks=4)).isoformat(),
                    'focus_areas': diagnostic_analysis['weakness_areas'],
                    'success_metrics': {
                        'target_overall_score': plan_metadata.target_improvement,
                        'weakness_improvement_threshold': 0.6,
                        'consistency_target': 0.75
                    }
                }
            }
        }
        
        return yaml.dump(yaml_structure, default_flow_style=False, allow_unicode=True, sort_keys=False)
    
    async def _save_study_plan(
        self,
        user_id: str,
        subject_id: str,
        yaml_content: str,
        units: List[PersonalizedUnit],
        diagnostic_analysis: Dict
    ) -> str:
        """
        Save study plan to both database and file system
        """
        plan_id = str(uuid.uuid4())
        
        try:
            # 1. Save to file system
            file_path = self.storage_path / f"{user_id}_{subject_id}_{plan_id}.yaml"
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(yaml_content)
            
            # 2. Save to database (study_plans table)
            study_plan_data = {
                'metadata': {
                    'total_units': len(units),
                    'total_videos': sum(len(unit.videos) for unit in units),
                    'weakness_areas': diagnostic_analysis['weakness_areas'],
                    'file_path': str(file_path)
                },
                'units': [asdict(unit) for unit in units]
            }
            
            query = text("""
                INSERT INTO study_plans (
                    id, user_id, subject_id, plan_name, plan_data, 
                    total_units, completed_units, progress_percentage, is_active
                ) VALUES (
                    :id, :user_id, :subject_id, :plan_name, :plan_data,
                    :total_units, 0, 0.0, true
                )
            """)
            
            self.db.execute(query, {
                'id': plan_id,
                'user_id': user_id,
                'subject_id': subject_id,
                'plan_name': f"Personalized Plan - {datetime.now().strftime('%Y-%m-%d')}",
                'plan_data': json.dumps(study_plan_data),
                'total_units': len(units)
            })
            
            # 3. Save to yml_storage for backward compatibility
            yml_query = text("""
                INSERT INTO yml_storage (
                    id, user_id, subject, yml_content, version, metadata
                ) VALUES (
                    :id, :user_id, :subject_id, :yml_content, '2.1', :metadata
                )
            """)
            
            metadata = json.dumps({
                'type': 'personalized_study_plan',
                'total_units': len(units),
                'total_videos': sum(len(unit.videos) for unit in units),
                'file_path': str(file_path),
                'created_at': datetime.now().isoformat()
            })
            
            self.db.execute(yml_query, {
                'id': f"yml_{plan_id}",
                'user_id': user_id,
                'subject_id': subject_id,
                'yml_content': yaml_content,
                'metadata': metadata
            })
            
            self.db.commit()
            logger.info(f"✅ Personalized study plan saved: {plan_id}")
            
        except Exception as e:
            logger.error(f"Error saving study plan: {e}")
            self.db.rollback()
            raise
        
        return plan_id
    
    async def _schedule_monthly_reassessment(
        self,
        user_id: str,
        subject_id: str,
        plan_id: str
    ) -> None:
        """
        Schedule monthly reassessment reminder
        """
        try:
            reassessment_date = datetime.now() + timedelta(days=30)
            
            # Save reassessment schedule to database
            query = text("""
                INSERT INTO notifications (
                    id, user_id, title, message, type, scheduled_for, 
                    metadata, is_active
                ) VALUES (
                    :id, :user_id, :title, :message, 'reassessment_reminder',
                    :scheduled_for, :metadata, true
                )
            """)
            
            metadata = json.dumps({
                'plan_id': plan_id,
                'subject_id': subject_id,
                'reassessment_type': 'monthly_progress'
            })
            
            self.db.execute(query, {
                'id': str(uuid.uuid4()),
                'user_id': user_id,
                'title': 'Monthly Study Plan Reassessment',
                'message': 'Time to evaluate your progress and update your study plan!',
                'scheduled_for': reassessment_date,
                'metadata': metadata
            })
            
            self.db.commit()
            logger.info(f"📅 Reassessment scheduled for {reassessment_date}")
            
        except Exception as e:
            logger.error(f"Error scheduling reassessment: {e}")
    
    async def update_plan_from_reassessment(
        self,
        user_id: str,
        subject_id: str,
        original_plan_id: str,
        reassessment_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update study plan based on monthly reassessment results
        """
        try:
            logger.info(f"🔄 Updating plan {original_plan_id} based on reassessment")
            
            # Generate new plan with updated weaknesses
            new_plan = await self.generate_personalized_plan(
                user_id=user_id,
                subject_id=subject_id,
                diagnostic_test_id=reassessment_results['diagnostic_test_id'],
                target_weeks=6  # Shorter plan for reassessment
            )
            
            if new_plan['success']:
                # Mark original plan as superseded
                update_query = text("""
                    UPDATE study_plans 
                    SET is_active = false,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = :original_plan_id
                """)
                
                self.db.execute(update_query, {'original_plan_id': original_plan_id})
                self.db.commit()
                
                return {
                    'success': True,
                    'new_plan_id': new_plan['plan_id'],
                    'message': 'Study plan updated based on reassessment',
                    'improvements': reassessment_results.get('improvements', [])
                }
            else:
                return new_plan
                
        except Exception as e:
            logger.error(f"Error updating plan from reassessment: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    async def get_student_plan(self, user_id: str, subject_id: str) -> Dict[str, Any]:
        """
        Retrieve the current active study plan for a student
        """
        try:
            query = text("""
                SELECT id, plan_name, plan_data, total_units, completed_units, 
                       progress_percentage, created_at, updated_at
                FROM study_plans
                WHERE user_id = :user_id AND subject_id = :subject_id AND is_active = true
                ORDER BY created_at DESC
                LIMIT 1
            """)
            
            result = self.db.execute(query, {
                'user_id': user_id,
                'subject_id': subject_id
            }).first()
            
            if not result:
                return {
                    'success': False,
                    'message': 'No active study plan found'
                }
            
            plan_data = json.loads(result[2])
            
            return {
                'success': True,
                'plan_id': result[0],
                'plan_name': result[1],
                'plan_data': plan_data,
                'total_units': result[3],
                'completed_units': result[4],
                'progress_percentage': float(result[5]),
                'created_at': result[6].isoformat() if result[6] else None,
                'updated_at': result[7].isoformat() if result[7] else None
            }
            
        except Exception as e:
            logger.error(f"Error retrieving student plan: {e}")
            return {
                'success': False,
                'error': str(e)
            }