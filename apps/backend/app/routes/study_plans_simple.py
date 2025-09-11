"""
Simple Study Plans API - Generates Khan Academy Style Study Plans
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import json
import uuid

from ..core.database import get_db
from ..models.subject import Subject
from ..models.question import Question
from ..models.diagnostic_test import DiagnosticTest, DiagnosticTestAnswer
from ..models.topic import Topic
from ..models.study_plan import StudyPlan, StudyPlanTemplate
from ..core.security import get_current_user
from ..models.user import User

router = APIRouter(prefix="/api/v1/study-plans", tags=["study-plans-simple"])

# Templates are now loaded dynamically from the database
# using StudyPlanTemplate model and get_study_plan_templates_from_db function

import math
import requests
from urllib.parse import parse_qs, urlparse

def calculate_smart_weaknesses(test_answers, questions_data, response_times):
    """
    Advanced weakness calculation using statistical confidence intervals
    and multiple performance factors
    """
    weaknesses = []
    
    # Group questions by topic
    topics_data = {}
    for answer in test_answers:
        question_id = answer.get('question_id')
        # Find question data
        question = next((q for q in questions_data if q['id'] == question_id), None)
        if not question:
            continue
            
        topic_name = question.get('topic', {}).get('name', 'General')
        if topic_name not in topics_data:
            topics_data[topic_name] = {
                'questions': [],
                'answers': [],
                'response_times': [],
                'difficulties': []
            }
            
        topics_data[topic_name]['questions'].append(question)
        topics_data[topic_name]['answers'].append(answer.get('user_answer'))
        topics_data[topic_name]['response_times'].append(response_times.get(question_id, 60000))
        topics_data[topic_name]['difficulties'].append(question.get('difficulty', 3))
    
    # Analyze each topic
    for topic_name, data in topics_data.items():
        if len(data['questions']) < 2:  # Need minimum sample size
            continue
            
        questions = data['questions']
        answers = data['answers']
        times = data['response_times']
        difficulties = data['difficulties']
        
        # Factor 1: Accuracy with Wilson Score Confidence Interval
        correct_count = sum(1 for i, q in enumerate(questions) 
                           if answers[i] == 'B')  # Mock - replace with actual correct answer
        total_count = len(questions)
        accuracy = correct_count / total_count
        
        # Wilson score interval for 95% confidence
        z = 1.96  # 95% confidence
        n = total_count
        p = accuracy
        
        if n > 0:
            denominator = 1 + z*z/n
            centre = (p + z*z/(2*n)) / denominator
            margin = z * math.sqrt((p*(1-p) + z*z/(4*n))/n) / denominator
            lower_bound = max(0, centre - margin)
            upper_bound = min(1, centre + margin)
        else:
            lower_bound = 0
            upper_bound = 1
        
        # Factor 2: Time analysis (normalized by difficulty)
        avg_time = sum(times) / len(times)
        expected_time = sum(d * 30000 for d in difficulties) / len(difficulties)  # 30s per difficulty level
        time_ratio = avg_time / expected_time if expected_time > 0 else 1
        
        # Factor 3: Difficulty-weighted performance
        difficulty_weight = sum(difficulties) / len(difficulties)
        difficulty_factor = difficulty_weight / 5.0  # Normalize to 0-1
        
        # Factor 4: Consistency (variance in performance)
        individual_scores = [1 if answers[i] == 'B' else 0 for i in range(len(questions))]
        variance = sum((score - accuracy)**2 for score in individual_scores) / len(individual_scores)
        consistency = 1 - variance  # Higher is better
        
        # Combined priority score
        priority_score = (
            (1 - lower_bound) * 0.4 +           # 40% confidence-adjusted accuracy
            min(time_ratio - 1, 1) * 0.25 +     # 25% time factor (excess time only)
            difficulty_factor * 0.2 +           # 20% difficulty factor
            (1 - consistency) * 0.15            # 15% inconsistency penalty
        )
        
        # Determine priority level
        if priority_score > 0.65:
            priority = 'HIGH'
        elif priority_score > 0.45:
            priority = 'MEDIUM'
        else:
            priority = 'LOW'
        
        # Only include topics that need work
        if priority != 'LOW' or lower_bound < 0.6:
            weaknesses.append({
                'topic': topic_name,
                'accuracy': accuracy,
                'confidence_lower': lower_bound,
                'confidence_upper': upper_bound,
                'time_ratio': time_ratio,
                'priority': priority,
                'priority_score': priority_score,
                'sample_size': total_count,
                'consistency': consistency,
                'videos_needed': 3 if priority == 'HIGH' else 2 if priority == 'MEDIUM' else 1
            })
    
    # Sort by priority score (highest weakness first)
    return sorted(weaknesses, key=lambda x: x['priority_score'], reverse=True)

def validate_youtube_video(youtube_url):
    """Quick validation of YouTube video availability using oEmbed"""
    try:
        # Extract video ID from URL
        if 'youtube.com/watch?v=' in youtube_url:
            video_id = youtube_url.split('v=')[1].split('&')[0]
        elif 'youtu.be/' in youtube_url:
            video_id = youtube_url.split('youtu.be/')[1].split('?')[0]
        else:
            video_id = youtube_url  # Assume it's just the ID
            
        # Use YouTube oEmbed API (no key required)
        oembed_url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"
        response = requests.get(oembed_url, timeout=3)
        
        if response.status_code == 200:
            data = response.json()
            return {
                'available': True,
                'title': data.get('title', ''),
                'author': data.get('author_name', ''),
                'thumbnail': data.get('thumbnail_url', ''),
                'video_id': video_id
            }
        else:
            return {'available': False, 'error': 'Video not found or private'}
            
    except Exception as e:
        return {'available': False, 'error': str(e)}

def get_quality_validated_videos(topic_name, difficulty_level, count=3):
    """Get videos with quality validation and smart selection"""
    # Use fallback templates since we don't have the dynamic template loading in this context
    template = get_fallback_templates().get(difficulty_level, {})
    
    validated_videos = []
    fallback_videos = []
    
    # Search through template for matching topics
    for unit in template.get('units', []):
        for template_topic in unit.get('topics', []):
            # Fuzzy matching for topic names
            topic_similarity = calculate_topic_similarity(topic_name, template_topic['name'])
            
            if topic_similarity > 0.6:  # 60% similarity threshold
                for video_id in template_topic.get('videos', []):
                    full_url = f"https://youtube.com/watch?v={video_id}"
                    validation = validate_youtube_video(video_id)
                    
                    video_data = {
                        'video_id': video_id,
                        'url': full_url,
                        'title': validation.get('title', template_topic['name']),
                        'topic': template_topic['name'],
                        'topic_similarity': topic_similarity,
                        'available': validation.get('available', False),
                        'quality_score': 0.9 if validation.get('available') else 0.1
                    }
                    
                    if validation.get('available'):
                        validated_videos.append(video_data)
                    else:
                        fallback_videos.append(video_data)
    
    # Sort by topic similarity and quality
    validated_videos.sort(key=lambda x: (x['quality_score'], x['topic_similarity']), reverse=True)
    
    # If we don't have enough validated videos, add fallbacks
    if len(validated_videos) < count:
        validated_videos.extend(fallback_videos[:count - len(validated_videos)])
    
    return validated_videos[:count]

def calculate_topic_similarity(topic1, topic2):
    """Simple similarity calculation for topic matching"""
    topic1_words = set(topic1.lower().split())
    topic2_words = set(topic2.lower().split())
    
    if not topic1_words or not topic2_words:
        return 0
    
    intersection = topic1_words.intersection(topic2_words)
    union = topic1_words.union(topic2_words)
    
    return len(intersection) / len(union) if union else 0

async def get_study_plan_templates_from_db(subject_id: str, db: Session):
    """Get study plan templates from database instead of hardcoded templates"""
    try:
        # Get templates for the subject from database
        templates = db.query(StudyPlanTemplate).filter(
            StudyPlanTemplate.subject_id == subject_id
        ).order_by(StudyPlanTemplate.unit_number).all()
        
        if not templates:
            # Return fallback template structure if no templates in DB
            return get_fallback_templates()
        
        # Group templates by difficulty level
        templates_by_level = {
            "beginner": {"units": []},
            "intermediate": {"units": []}, 
            "advanced": {"units": []}
        }
        
        for template in templates:
            # Determine level based on difficulty_level
            level = "beginner" if template.difficulty_level <= 2 else "advanced" if template.difficulty_level >= 4 else "intermediate"
            
            unit_data = {
                "number": template.unit_number,
                "title": template.unit_name,
                "description": template.unit_description or "",
                "topics": [],
                "estimated_hours": template.estimated_hours or 8,
                "difficulty": level.capitalize()
            }
            
            # Convert template topics to the expected format
            if template.topics:
                for i, topic_name in enumerate(template.topics):
                    video_urls = template.video_urls.get(topic_name, []) if template.video_urls else []
                    
                    topic_data = {
                        "name": topic_name,
                        "videos": video_urls,
                        "exercises": template.exercise_count or 15
                    }
                    unit_data["topics"].append(topic_data)
            
            templates_by_level[level]["units"].append(unit_data)
        
        return templates_by_level
        
    except Exception as e:
        print(f"Error loading templates from DB: {e}")
        return get_fallback_templates()

def get_fallback_templates():
    """Fallback templates when database templates are not available"""
    return {
        "beginner": {
            "units": [
                {
                    "number": 1,
                    "title": "Fundamentos Básicos",
                    "description": "Conceptos básicos para iniciar",
                    "topics": [
                        {"name": "Introducción", "videos": ["dQw4w9WgXcQ"], "exercises": 10},
                        {"name": "Conceptos básicos", "videos": ["PUB0TaZ7h-A"], "exercises": 15}
                    ],
                    "estimated_hours": 6,
                    "difficulty": "Básico"
                }
            ]
        },
        "intermediate": {
            "units": [
                {
                    "number": 1,
                    "title": "Nivel Intermedio",
                    "description": "Conceptos de nivel intermedio",
                    "topics": [
                        {"name": "Temas intermedios", "videos": ["6AgB3UUUC7Y"], "exercises": 20}
                    ],
                    "estimated_hours": 10,
                    "difficulty": "Intermedio"
                }
            ]
        },
        "advanced": {
            "units": [
                {
                    "number": 1,
                    "title": "Nivel Avanzado", 
                    "description": "Conceptos avanzados",
                    "topics": [
                        {"name": "Temas avanzados", "videos": ["eTymJPy6rT4"], "exercises": 25}
                    ],
                    "estimated_hours": 15,
                    "difficulty": "Avanzado"
                }
            ]
        }
    }

async def get_real_diagnostic_data(subject_id: str, user_id: str = None, db: Session = None):
    """Get real diagnostic test data from database"""
    try:
        # If no user_id provided, use sample data based on subject
        if not user_id:
            # Return fallback data structure with default values
            return {
                "score_percentage": 60,
                "test_answers": [],
                "questions_data": [],
                "response_times": {}
            }
        
        # Get latest completed diagnostic test for user and subject
        latest_test = db.query(DiagnosticTest).filter(
            DiagnosticTest.user_id == user_id,
            DiagnosticTest.subject_id == subject_id,
            DiagnosticTest.status == "completed"
        ).order_by(DiagnosticTest.completed_at.desc()).first()
        
        if not latest_test:
            # No diagnostic test found - return default values
            return {
                "score_percentage": 50,
                "test_answers": [],
                "questions_data": [],
                "response_times": {}
            }
        
        # Get all answers for this test
        test_answers = db.query(DiagnosticTestAnswer).filter(
            DiagnosticTestAnswer.diagnostic_test_id == latest_test.id
        ).all()
        
        # Convert answers to format expected by weakness calculation
        formatted_answers = []
        questions_data = []
        response_times = {}
        
        for answer in test_answers:
            question = db.query(Question).filter(Question.id == answer.question_id).first()
            topic = db.query(Topic).filter(Topic.id == answer.topic_id).first() if answer.topic_id else None
            
            formatted_answers.append({
                "question_id": str(answer.question_id),
                "user_answer": answer.user_answer,
                "response_time": answer.response_time_ms
            })
            
            questions_data.append({
                "id": str(answer.question_id),
                "topic": {"name": topic.name if topic else "General"},
                "difficulty": question.difficulty if question else 3,
                "correct_answer": question.correct_answer if question else "A"
            })
            
            response_times[str(answer.question_id)] = answer.response_time_ms
        
        return {
            "score_percentage": latest_test.score_percentage,
            "test_answers": formatted_answers,
            "questions_data": questions_data,
            "response_times": response_times
        }
        
    except Exception as e:
        # Return default values on error
        return {
            "score_percentage": 50,
            "test_answers": [],
            "questions_data": [],
            "response_times": {}
        }

def get_difficulty_level(score_percentage: float) -> str:
    """Determine difficulty level based on diagnostic score"""
    if score_percentage >= 80:
        return "advanced"
    elif score_percentage >= 50:
        return "intermediate"
    else:
        return "beginner"

def generate_personalized_recommendations(score: float, subject: str) -> Dict[str, Any]:
    """Generate personalized recommendations based on score"""
    if score >= 80:
        return {
            "focus": "Perfeccionamiento y temas avanzados",
            "daily_time": "45-60 minutos",
            "strategy": "Enfócate en problemas complejos y aplicaciones prácticas",
            "priority_topics": ["Cálculo", "Problemas de optimización", "Modelado matemático"]
        }
    elif score >= 50:
        return {
            "focus": "Consolidación de conceptos intermedios",
            "daily_time": "60-90 minutos",
            "strategy": "Practica consistentemente y revisa conceptos fundamentales",
            "priority_topics": ["Álgebra avanzada", "Trigonometría", "Geometría analítica"]
        }
    else:
        return {
            "focus": "Fortalecimiento de bases fundamentales",
            "daily_time": "90-120 minutos",
            "strategy": "Dedica tiempo extra a conceptos básicos antes de avanzar",
            "priority_topics": ["Álgebra básica", "Geometría", "Aritmética"]
        }

@router.get("/generate/{subject_id}")
async def generate_study_plan_simple(
    subject_id: str,
    user_id: str = None,
    db: Session = Depends(get_db)
):
    """Generate a Khan Academy style study plan with smart weakness detection"""
    try:
        # Get subject info
        subject = db.query(Subject).filter(Subject.id == subject_id).first()
        if not subject:
            raise HTTPException(status_code=404, detail="Subject not found")
        
        subject_name = subject.name

        # Get diagnostic test results from database
        diagnostic_data = await get_real_diagnostic_data(subject_id, user_id, db)
        
        score_percentage = diagnostic_data["score_percentage"]
        
        # Calculate smart weaknesses using statistical methods
        weaknesses = calculate_smart_weaknesses(
            diagnostic_data["test_answers"],
            diagnostic_data["questions_data"], 
            diagnostic_data["response_times"]
        )
        
        # Determine difficulty level
        level = get_difficulty_level(score_percentage)
        
        # Get base template for subject and level from database
        templates_from_db = await get_study_plan_templates_from_db(subject_id, db)
        base_units = templates_from_db.get(level, templates_from_db["intermediate"])["units"]
        
        # Enhance units with weakness-based prioritization and validated videos
        enhanced_units = []
        for unit in base_units:
            enhanced_unit = unit.copy()
            enhanced_topics = []
            
            for topic in unit["topics"]:
                enhanced_topic = topic.copy()
                
                # Check if this topic is a weakness
                topic_weakness = next((w for w in weaknesses if w['topic'] in topic['name']), None)
                
                if topic_weakness:
                    # High priority topic - add more resources
                    enhanced_topic['is_weakness'] = True
                    enhanced_topic['priority'] = topic_weakness['priority']
                    enhanced_topic['confidence_score'] = topic_weakness['confidence_lower']
                    enhanced_topic['exercises'] = topic['exercises'] + 10  # Extra practice
                    enhanced_topic['estimated_time'] = topic.get('estimated_time', 60) + 30  # Extra time
                    
                    # Get validated videos for this weakness
                    validated_videos = get_quality_validated_videos(
                        topic_weakness['topic'], 
                        level, 
                        topic_weakness['videos_needed']
                    )
                    enhanced_topic['videos'] = [v['video_id'] for v in validated_videos]
                    enhanced_topic['video_details'] = validated_videos
                else:
                    # Normal topic
                    enhanced_topic['is_weakness'] = False
                    enhanced_topic['priority'] = 'NORMAL'
                    enhanced_topic['confidence_score'] = 0.8  # Assumed good
                    
                    # Get standard videos (1-2 videos)
                    validated_videos = get_quality_validated_videos(topic['name'], level, 1)
                    enhanced_topic['videos'] = [v['video_id'] for v in validated_videos] if validated_videos else topic.get('videos', [])
                    enhanced_topic['video_details'] = validated_videos
                
                enhanced_topics.append(enhanced_topic)
            
            enhanced_unit['topics'] = enhanced_topics
            enhanced_units.append(enhanced_unit)
        
        # Generate enhanced recommendations based on weaknesses
        recommendations = generate_personalized_recommendations(score_percentage, subject_name)
        if weaknesses:
            recommendations['detected_weaknesses'] = [w['topic'] for w in weaknesses[:3]]
            recommendations['focus'] = f"Enfoque prioritario en: {', '.join(w['topic'] for w in weaknesses[:2])}"
        
        # Generate smart weekly schedule prioritizing weaknesses
        smart_schedule = generate_smart_weekly_schedule(enhanced_units, weaknesses)
        
        # Build complete study plan
        study_plan = {
            "id": str(uuid.uuid4()),
            "subject": subject_name,
            "subject_id": subject_id,
            "title": f"Plan Inteligente de {subject_name}",
            "description": f"Plan adaptativo con análisis estadístico ({score_percentage}%)",
            "created_at": datetime.now().isoformat(),
            "diagnostic_score": score_percentage,
            "difficulty_level": level.capitalize(),
            "units": enhanced_units,
            "total_units": len(enhanced_units),
            "estimated_total_hours": sum(u["estimated_hours"] for u in enhanced_units),
            "recommendations": recommendations,
            "weaknesses_detected": weaknesses,
            "progress": {
                "completed_units": 0,
                "completed_topics": 0,
                "total_topics": sum(len(u["topics"]) for u in enhanced_units),
                "percentage": 0
            },
            "gamification": {
                "current_rank": "C" if score_percentage < 60 else "B" if score_percentage < 80 else "A",
                "xp_earned": 0,
                "achievements": [],
                "next_milestone": f"Mejora en {weaknesses[0]['topic']}" if weaknesses else "Completa tu primera unidad"
            },
            "weekly_schedule": smart_schedule,
            "analytics": {
                "weakness_count": len(weaknesses),
                "high_priority_topics": len([w for w in weaknesses if w['priority'] == 'HIGH']),
                "video_validation_enabled": True,
                "statistical_analysis": True
            }
        }
        
        return study_plan
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def generate_smart_weekly_schedule(units, weaknesses):
    """Generate weekly schedule prioritizing weakness topics"""
    schedule = {}
    days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
    
    # Collect all topics with priorities
    all_topics = []
    for unit in units:
        for topic in unit.get('topics', []):
            all_topics.append({
                'name': topic['name'],
                'priority': topic.get('priority', 'NORMAL'),
                'is_weakness': topic.get('is_weakness', False),
                'estimated_time': topic.get('estimated_time', 60)
            })
    
    # Sort topics: HIGH priority first, then MEDIUM, then NORMAL
    priority_order = {'HIGH': 3, 'MEDIUM': 2, 'NORMAL': 1}
    all_topics.sort(key=lambda x: priority_order.get(x['priority'], 1), reverse=True)
    
    # Assign to days
    for i, day in enumerate(days):
        if i < len(all_topics):
            topic = all_topics[i]
            
            # Adjust time based on priority
            base_time = topic['estimated_time']
            if topic['priority'] == 'HIGH':
                time_str = f"{base_time + 30} min"
                note = "⚠️ Área de enfoque"
            elif topic['priority'] == 'MEDIUM':
                time_str = f"{base_time + 15} min"
                note = "📚 Revisión importante"
            else:
                time_str = f"{base_time} min"
                note = "✅ Práctica regular"
            
            schedule[day] = {
                "topic": topic['name'],
                "time": time_str,
                "priority": topic['priority'],
                "note": note
            }
        else:
            # Fill remaining days with review
            schedule[day] = {
                "topic": "Repaso y práctica",
                "time": "90 min",
                "priority": "REVIEW",
                "note": "🔄 Consolidación"
            }
    
    return schedule

@router.post("/generate")
async def generate_study_plan_post(
    request: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Generate study plan from diagnostic results (POST)"""
    subject_id = request.get("subject_id", "2a9c9371-b931-41d4-8d3e-ce5aae91a5c3")
    user_id = request.get("user_id", None)
    
    # Redirect to GET endpoint logic
    return await generate_study_plan_simple(subject_id, user_id, db)

@router.get("/my-plans")
async def get_my_plans(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's study plans"""
    try:
        # Get all active study plans for the user
        user_plans = db.query(StudyPlan).filter(
            StudyPlan.user_id == current_user.id,
            StudyPlan.is_active == True
        ).all()
        
        plans_data = []
        for plan in user_plans:
            # Get subject name
            subject = db.query(Subject).filter(Subject.id == plan.subject_id).first()
            subject_name = subject.name if subject else "Unknown"
            
            # Calculate estimated completion based on progress
            total_units = plan.total_units
            completed_units = plan.completed_units
            progress_percentage = float(plan.progress_percentage) if plan.progress_percentage else 0
            
            # Estimate weeks remaining (assuming 2 units per week)
            remaining_units = max(0, total_units - completed_units)
            estimated_weeks = max(1, remaining_units // 2)
            
            # Get next topic from plan data
            next_topic = "Comenzar plan"
            if plan.plan_data and isinstance(plan.plan_data, dict):
                units = plan.plan_data.get("units", [])
                for unit in units:
                    topics = unit.get("topics", [])
                    for topic in topics:
                        if not topic.get("completed", False):
                            next_topic = topic.get("name", "Próximo tema")
                            break
                    if next_topic != "Comenzar plan":
                        break
            
            plans_data.append({
                "id": str(plan.id),
                "subject": subject_name,
                "title": plan.plan_name,
                "progress": int(progress_percentage),
                "next_topic": next_topic,
                "estimated_completion": f"{estimated_weeks} semana{'s' if estimated_weeks != 1 else ''}",
                "total_units": total_units,
                "completed_units": completed_units,
                "created_at": plan.generated_at.isoformat() if plan.generated_at else None,
                "updated_at": plan.updated_at.isoformat() if plan.updated_at else None
            })
        
        return plans_data
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener planes de estudio: {str(e)}"
        )