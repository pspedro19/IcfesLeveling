"""
Unified Video Recommendation Service (Orchestrator/Facade)
This service acts as the central entry point for all video recommendation and learning
analytics functionalities. It orchestrates and delegates tasks to specialized sub-services.

LOGICA_DE_NEGOCIO.md Videos 100%:
- Enhanced post-error recommendations based on error patterns
- Difficulty-appropriate content matching
- Related topic suggestions for comprehensive learning
"""

import logging
from typing import List, Dict, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import text, and_, or_, func
from uuid import UUID
from datetime import datetime, timedelta
from collections import Counter

# Import specialized services
from .video_matching_service import VideoMatchingService
from .video_learning_planner import VideoLearningPlanner
from .video_progress_service import VideoProgressService
from ..models.youtube_links import YouTubeLinks # Needed for basic queries if any remain
from ..schemas.video_matching import MatchingRequest, FailedQuestion # For orchestrator methods

logger = logging.getLogger(__name__)


# =============================================================================
# POST-ERROR RECOMMENDATION CONSTANTS (LOGICA_DE_NEGOCIO.md)
# =============================================================================

# Error pattern analysis
ERROR_PATTERN_WEIGHTS = {
    "conceptual": 1.5,      # Fundamental concept misunderstanding
    "procedural": 1.2,      # Steps/process error
    "careless": 0.8,        # Quick/rushed mistake
    "unknown": 1.0,         # Default weight
}

# Video type mapping for error types
VIDEO_TYPE_FOR_ERROR = {
    "conceptual": ["explicacion", "tutorial", "teoria"],
    "procedural": ["ejercicio_resuelto", "paso_a_paso", "practica"],
    "careless": ["repaso_rapido", "tips", "resumen"],
}

# Difficulty adjustment based on performance
DIFFICULTY_ADJUSTMENT = {
    "very_low": -2,    # Score < 30%
    "low": -1,         # Score 30-50%
    "medium": 0,       # Score 50-70%
    "high": 1,         # Score > 70% but still wrong
}

class VideoRecommendationService:
    def __init__(self, db: Session):
        self.db = db
        # Instantiate specialized services
        # TODO: Pass real OpenAI API key to VideoMatchingService
        self.matching_service = VideoMatchingService(db=db, openai_api_key=None)
        self.learning_planner = VideoLearningPlanner(db=db)
        self.progress_tracker = VideoProgressService(db=db)

    # =========================================================================
    # ENHANCED POST-ERROR RECOMMENDATIONS (LOGICA_DE_NEGOCIO.md)
    # =========================================================================

    async def get_enhanced_post_error_videos(
        self,
        user_id: str,
        question_data: Dict[str, Any],
        error_analysis: Dict[str, Any] = None,
        limit: int = 5
    ) -> Dict[str, Any]:
        """
        Get enhanced video recommendations after a wrong answer.

        Analyzes error patterns to recommend the most appropriate videos:
        - Conceptual errors -> Explanatory videos
        - Procedural errors -> Step-by-step tutorials
        - Careless errors -> Quick review videos

        Args:
            user_id: Student ID
            question_data: Failed question details
            error_analysis: Optional pre-computed error analysis
            limit: Maximum videos to return

        Returns:
            Comprehensive recommendation with primary video, alternatives, and learning path
        """
        # Analyze error type if not provided
        if not error_analysis:
            error_analysis = self._analyze_error_pattern(question_data)

        error_type = error_analysis.get("error_type", "unknown")
        topic_id = question_data.get("topic_id")
        subject_id = question_data.get("subject_id")
        question_difficulty = question_data.get("difficulty", 3)

        # Determine appropriate video types for this error
        video_types = VIDEO_TYPE_FOR_ERROR.get(error_type, ["explicacion"])

        # Adjust difficulty based on performance
        performance_level = error_analysis.get("performance_level", "medium")
        difficulty_adj = DIFFICULTY_ADJUSTMENT.get(performance_level, 0)
        target_difficulty = max(1, min(5, question_difficulty + difficulty_adj))

        # Get primary video recommendations
        primary_videos = await self._fetch_videos_for_topic(
            topic_id=topic_id,
            subject_id=subject_id,
            video_types=video_types,
            difficulty=target_difficulty,
            limit=limit
        )

        # Get prerequisite topic videos if conceptual error
        prerequisite_videos = []
        if error_type == "conceptual":
            prereq_topics = self._get_prerequisite_topics(topic_id)
            for prereq_id in prereq_topics[:2]:  # Max 2 prerequisites
                prereq_vids = await self._fetch_videos_for_topic(
                    topic_id=prereq_id,
                    video_types=["explicacion", "teoria"],
                    difficulty=target_difficulty - 1,
                    limit=2
                )
                prerequisite_videos.extend(prereq_vids)

        # Get related topic videos for broader understanding
        related_videos = []
        if len(primary_videos) < 3:
            related_topics = self._get_related_topics(topic_id, subject_id)
            for rel_topic in related_topics[:2]:
                rel_vids = await self._fetch_videos_for_topic(
                    topic_id=rel_topic,
                    video_types=video_types,
                    difficulty=target_difficulty,
                    limit=2
                )
                related_videos.extend(rel_vids)

        # Build recommendation response
        result = {
            "error_analysis": {
                "error_type": error_type,
                "error_weight": ERROR_PATTERN_WEIGHTS.get(error_type, 1.0),
                "performance_level": performance_level,
                "target_difficulty": target_difficulty,
            },
            "primary_video": primary_videos[0] if primary_videos else None,
            "alternative_videos": primary_videos[1:limit] if len(primary_videos) > 1 else [],
            "prerequisite_videos": prerequisite_videos[:3],
            "related_topic_videos": related_videos[:3],
            "learning_path": self._build_learning_path(
                error_type=error_type,
                primary_video=primary_videos[0] if primary_videos else None,
                prerequisite_videos=prerequisite_videos,
            ),
            "motivational_message": self._get_motivational_message(error_type),
        }

        logger.info(f"Enhanced post-error recommendations for user {user_id}: "
                   f"error_type={error_type}, videos_found={len(primary_videos)}")

        return result

    def _analyze_error_pattern(self, question_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze the error pattern to determine error type.
        """
        time_spent = question_data.get("time_spent_seconds", 30)
        question_difficulty = question_data.get("difficulty", 3)
        attempt_number = question_data.get("attempt_number", 1)
        selected_answer = question_data.get("selected_answer", "")
        correct_answer = question_data.get("correct_answer", "")

        # Determine error type based on patterns
        if time_spent < 10:
            # Very fast response likely means careless
            error_type = "careless"
            performance_level = "medium"
        elif time_spent > 120 and question_difficulty >= 4:
            # Long time on hard question = conceptual issue
            error_type = "conceptual"
            performance_level = "low"
        elif attempt_number > 1:
            # Multiple attempts = procedural issue
            error_type = "procedural"
            performance_level = "low"
        elif len(selected_answer) > 0 and len(correct_answer) > 0:
            # Check if answers are close (procedural) or completely wrong (conceptual)
            # This is a simplified heuristic
            error_type = "procedural" if attempt_number == 1 else "conceptual"
            performance_level = "medium"
        else:
            error_type = "unknown"
            performance_level = "medium"

        return {
            "error_type": error_type,
            "performance_level": performance_level,
            "time_spent": time_spent,
            "was_quick": time_spent < 15,
            "was_slow": time_spent > 90,
        }

    async def _fetch_videos_for_topic(
        self,
        topic_id: str = None,
        subject_id: str = None,
        video_types: List[str] = None,
        difficulty: int = 3,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Fetch videos matching topic and criteria.
        """
        try:
            query_parts = ["SELECT * FROM youtube_links WHERE estado = 'activo'"]
            params = {}

            if topic_id:
                query_parts.append("AND codigo_tema = :topic_id")
                params["topic_id"] = topic_id

            if subject_id:
                query_parts.append("AND area_evaluada = :subject_id")
                params["subject_id"] = subject_id

            if video_types:
                type_placeholders = ", ".join([f":vtype_{i}" for i in range(len(video_types))])
                query_parts.append(f"AND tipo_contenido IN ({type_placeholders})")
                for i, vtype in enumerate(video_types):
                    params[f"vtype_{i}"] = vtype

            query_parts.append("AND nivel_dificultad BETWEEN :diff_min AND :diff_max")
            params["diff_min"] = max(1, difficulty - 1)
            params["diff_max"] = min(5, difficulty + 1)

            query_parts.append("""
                ORDER BY
                    ABS(nivel_dificultad - :target_diff) ASC,
                    calidad_score DESC,
                    relevancia_score DESC
                LIMIT :limit
            """)
            params["target_diff"] = difficulty
            params["limit"] = limit

            full_query = " ".join(query_parts)
            result = self.db.execute(text(full_query), params)
            videos = result.fetchall()

            return [
                {
                    "id": str(v.id),
                    "youtube_id": v.youtube_id,
                    "title": v.video_title,
                    "channel": v.channel_name,
                    "duration_seconds": v.duration_seconds,
                    "difficulty": v.nivel_dificultad,
                    "type": v.tipo_contenido,
                    "xp_reward": v.puntos_xp,
                    "topic": v.codigo_tema,
                    "subject": v.area_evaluada,
                }
                for v in videos
            ]

        except Exception as e:
            logger.error(f"Error fetching videos for topic: {e}")
            return []

    def _get_prerequisite_topics(self, topic_id: str) -> List[str]:
        """Get prerequisite topics for a given topic."""
        # Import from mastery service
        try:
            from .mastery_service import TOPIC_PREREQUISITES
            return TOPIC_PREREQUISITES.get(topic_id, [])
        except Exception:
            return []

    def _get_related_topics(self, topic_id: str, subject_id: str) -> List[str]:
        """Get related topics in the same subject."""
        try:
            result = self.db.execute(
                text("""
                    SELECT DISTINCT codigo_tema
                    FROM youtube_links
                    WHERE area_evaluada = :subject_id
                    AND codigo_tema != :topic_id
                    AND estado = 'activo'
                    LIMIT 5
                """),
                {"subject_id": subject_id, "topic_id": topic_id}
            )
            return [r[0] for r in result.fetchall()]
        except Exception:
            return []

    def _build_learning_path(
        self,
        error_type: str,
        primary_video: Dict = None,
        prerequisite_videos: List[Dict] = None
    ) -> List[Dict[str, Any]]:
        """Build a suggested learning path based on error analysis."""
        path = []

        # For conceptual errors, start with prerequisites
        if error_type == "conceptual" and prerequisite_videos:
            for i, video in enumerate(prerequisite_videos[:2]):
                path.append({
                    "step": i + 1,
                    "type": "prerequisite",
                    "video": video,
                    "description": "Refuerza los conceptos base primero",
                })

        # Add primary video
        if primary_video:
            path.append({
                "step": len(path) + 1,
                "type": "main",
                "video": primary_video,
                "description": "Video principal para este tema",
            })

        # Add practice step
        path.append({
            "step": len(path) + 1,
            "type": "practice",
            "video": None,
            "description": "Practica con 5 preguntas similares",
        })

        return path

    def _get_motivational_message(self, error_type: str) -> str:
        """Get a motivational message based on error type."""
        messages = {
            "conceptual": "Equivocarse es parte del aprendizaje. Este video te ayudara a entender el concepto desde cero.",
            "procedural": "Casi lo tienes! Solo necesitas repasar los pasos correctos.",
            "careless": "Toma tu tiempo. La velocidad viene con la practica.",
            "unknown": "Cada error es una oportunidad de aprender algo nuevo.",
        }
        return messages.get(error_type, messages["unknown"])

    # --- Methods that delegate to VideoMatchingService (formerly EnhancedVideoRecommendationEngine) ---
    async def get_recommended_videos_for_failed_question(self, question_id: str, student_id: str, question_text: str, subject_area: str, topic: str, difficulty: float, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Orchestrates getting video recommendations for a failed question using the VideoMatchingService.
        """
        # Construct the FailedQuestion object (simplified, full data would come from the failed response)
        failed_q = FailedQuestion(
            question_id=question_id,
            student_id=student_id,
            question_text=question_text,
            question_type="multiple_choice", # Placeholder
            correct_answer="", # Placeholder
            student_answer="", # Placeholder
            distractors=[], # Placeholder
            subject_area=subject_area,
            topic=topic,
            subtopic="", # Placeholder
            competency="", # Placeholder
            component="", # Placeholder
            cognitive_level="", # Placeholder
            time_spent_seconds=0, # Placeholder
            attempt_number=1, # Placeholder
            failed_at=datetime.now(),
            question_difficulty=difficulty,
            student_theta=0.0 # Placeholder
        )
        
        # Construct the MatchingRequest
        matching_request = MatchingRequest(
            failed_question=failed_q,
            max_videos=limit
        )
        
        # Delegate to VideoMatchingService
        result = await self.matching_service.match_videos_for_failed_question(matching_request)
        return result.video_matches

    # --- Methods that delegate to VideoLearningPlanner (formerly EnhancedVideoRecommendationService) ---
    async def refresh_monthly_recommendations(self, user_id: str, subject_id: str, diagnostic_results: Dict[str, Any]) -> Dict[str, Any]:
        return await self.learning_planner.refresh_monthly_recommendations(user_id, subject_id, diagnostic_results)

    async def get_adaptive_video_recommendations(self, user_id: str, subject_id: str, recommendation_type: str = "adaptive", count: int = 20) -> List[Dict[str, Any]]:
        return await self.learning_planner.get_adaptive_video_recommendations(user_id, subject_id, recommendation_type, count)
    
    async def get_learning_path_videos(self, user_id: str, subject_id: str, path_segment: str = "current") -> Dict[str, Any]:
        return await self.learning_planner.get_learning_path_videos(user_id, subject_id, path_segment)

    # --- Methods that delegate to VideoProgressService ---
    async def track_video_event(self, user_id: str, video_id: str, event_type: str, current_time: int, video_duration: int, session_id: str, metadata: Optional[Dict] = None) -> bool:
        return await self.progress_tracker.track_video_event(user_id, video_id, VideoProgressService.VideoEventType(event_type), current_time, video_duration, session_id, metadata)
    
    async def track_video_interaction(self, user_id: str, video_id: str, interaction_data: Dict[str, Any]) -> Dict[str, Any]:
        return await self.progress_tracker.track_video_interaction(user_id, video_id, interaction_data)

    async def get_video_learning_analytics(self, user_id: str, time_period: int = 30, video_id: str = None) -> Dict[str, Any]:
        return await self.progress_tracker.get_video_learning_analytics(user_id, time_period, video_id)
    
    async def create_adaptive_video_playlist(self, user_id: str, learning_objective: str, target_duration_minutes: int = 60, difficulty_progression: str = "adaptive") -> Dict[str, Any]:
        # This functionality might be part of the learning_planner or a new service, or stay here
        # For now, it's a placeholder.
        logger.warning("create_adaptive_video_playlist is a placeholder. Needs implementation or delegation.")
        return {"error": "Not yet implemented in orchestrator"}

    # --- Original simple query methods (adapted or re-implemented here if still needed) ---
    # These methods can be adapted to use the new recommendation engine
    def get_basic_video_recommendations(
        self,
        user_id: str,
        topic_codes: List[str] = None,
        difficulty_level: int = None,
        content_type: str = None,
        limit: int = 10
    ) -> List[Dict]:
        logger.warning("Using basic video recommendations. Consider using adaptive recommendations.")
        # This could call the recommendation engine for a simpler, filtered query
        # For now, a simplified direct query to youtube_links
        # (This logic was present in the original video_recommendation_service.py)
        
        try:
            query = text("""
                SELECT id, codigo_tema, area_evaluada, tema_principal, canal_sugerido, youtube_url, youtube_id,
                       video_title, channel_name, duration_seconds, tipo_contenido, nivel_dificultad,
                       proceso_cognitivo, calidad_score, relevancia_score, tiempo_estimado_estudio, puntos_xp
                FROM youtube_links 
                WHERE estado = 'activo'
            """)
            params = {}
            
            if topic_codes:
                placeholders = ','.join([f':topic_{i}' for i in range(len(topic_codes))])
                query += f" AND codigo_tema IN ({placeholders})"
                for i, topic in enumerate(topic_codes):
                    params[f'topic_{i}'] = topic
            
            if difficulty_level:
                query += " AND nivel_dificultad = :difficulty"
                params['difficulty'] = difficulty_level
            
            if content_type:
                query += " AND tipo_contenido = :content_type"
                params['content_type'] = content_type
            
            query += """
                ORDER BY 
                    calidad_score DESC, 
                    relevancia_score DESC,
                    orden_recomendacion ASC
                LIMIT :limit
            """
            params['limit'] = limit
            
            result = self.db.execute(text(query), params)
            videos = result.fetchall()
            
            video_list = []
            for video in videos:
                video_list.append({
                    'id': str(video.id), 'codigo_tema': video.codigo_tema, 'area_evaluada': video.area_evaluada,
                    'tema_principal': video.tema_principal, 'canal_sugerido': video.canal_sugerido,
                    'youtube_url': video.youtube_url, 'youtube_id': video.youtube_id,
                    'video_title': video.video_title, 'channel_name': video.channel_name,
                    'duration_seconds': video.duration_seconds, 'tipo_contenido': video.tipo_contenido,
                    'nivel_dificultad': video.nivel_dificultad, 'proceso_cognitivo': video.proceso_cognitivo,
                    'calidad_score': float(video.calidad_score) if video.calidad_score else None,
                    'relevancia_score': float(video.relevancia_score) if video.relevancia_score else None,
                    'tiempo_estimado_estudio': video.tiempo_estimado_estudio, 'puntos_xp': video.puntos_xp
                })
            
            logger.info(f"✅ {len(video_list)} basic videos recommended for user {user_id}")
            return video_list
            
        except Exception as e:
            logger.error(f"❌ Error obtaining basic video recommendations: {e}")
            return []
            
    def get_personalized_video_recommendations(
        self, 
        user_id: str, 
        diagnostic_results: Dict,
        limit: int = 15
    ) -> Dict[str, List[Dict]]:
        # This method needs to be integrated with the learning_planner
        logger.warning("get_personalized_video_recommendations is a placeholder. Needs integration with learning planner.")
        return self.learning_planner.get_adaptive_video_recommendations(user_id, diagnostic_results.get("subject_id"), count=limit)
    
    def get_video_by_topic(self, topic_code: str, difficulty_level: int = None, content_type: str = None) -> Optional[Dict]:
        logger.warning("get_video_by_topic is a placeholder. Consider using recommendation engine.")
        # Similar to get_basic_video_recommendations but for a single topic
        videos = self.get_basic_video_recommendations(
            user_id="system", topic_codes=[topic_code], difficulty_level=difficulty_level, content_type=content_type, limit=1
        )
        return videos[0] if videos else None
    
    def get_random_video_recommendation(self, user_id: str, area_evaluada: str = None) -> Optional[Dict]:
        logger.warning("get_random_video_recommendation is a placeholder. Consider using recommendation engine.")
        # Direct query
        try:
            query = """ SELECT * FROM youtube_links WHERE estado = 'activo' """
            params = {}
            if area_evaluada:
                query += " AND area_evaluada = :area"
                params['area'] = area_evaluada
            query += """ ORDER BY RANDOM() LIMIT 1 """
            result = self.db.execute(text(query), params)
            video = result.fetchone()
            if video:
                return {
                    'id': str(video.id), 'codigo_tema': video.codigo_tema, 'area_evaluada': video.area_evaluada,
                    'tema_principal': video.tema_principal, 'youtube_url': video.youtube_url, 'youtube_id': video.youtube_id,
                    'video_title': video.video_title, 'channel_name': video.channel_name, 'duration_seconds': video.duration_seconds,
                    'puntos_xp': video.puntos_xp
                }
            return None
        except Exception as e:
            logger.error(f"❌ Error obtaining random video recommendation: {e}")
            return None
    
    def get_video_playlist_for_study_plan(self, user_id: str, study_plan: Dict, limit_per_unit: int = 5) -> Dict[str, List[Dict]]:
        logger.warning("get_video_playlist_for_study_plan is a placeholder. Needs integration with learning planner.")
        playlist = {}
        if 'units' not in study_plan: return playlist
        for unit in study_plan['units']:
            unit_name = unit.get('name', 'Unidad')
            focus_topics = unit.get('focus_topics', [])
            if focus_topics:
                unit_videos = self.get_basic_video_recommendations(
                    user_id=user_id, topic_codes=focus_topics[:3], difficulty_level=unit.get('difficulty_level', 3), limit=limit_per_unit
                )
                playlist[unit_name] = unit_videos
            else:
                playlist[unit_name] = []
        return playlist
