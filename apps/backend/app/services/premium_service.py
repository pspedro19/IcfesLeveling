from sqlalchemy.orm import Session
from ..models.user import User
from ..models.real_mentor import RealMentor
from ..models.mentor_session import MentorSession
from ..models.predictive_analytics import PredictiveAnalytics
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

class PremiumService:
    def __init__(self, db: Session):
        self.db = db
    
    def check_premium_status(self, user_id: str) -> Dict[str, Any]:
        """Verificar estado premium del usuario"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return {"is_premium": False, "message": "Usuario no encontrado"}
        
        is_premium = user.is_premium and (
            user.premium_expires_at is None or 
            user.premium_expires_at > datetime.utcnow()
        )
        
        return {
            "is_premium": is_premium,
            "premium_expires_at": user.premium_expires_at,
            "premium_plan": user.premium_plan,
            "ai_requests_remaining": max(0, user.ai_requests_limit - user.ai_requests_used),
            "simulacros_remaining": max(0, user.simulacros_limit - user.simulacros_used)
        }
    
    def upgrade_to_premium(self, user_id: str, plan: str, duration_days: int) -> Dict[str, Any]:
        """Actualizar usuario a premium"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return {"success": False, "message": "Usuario no encontrado"}
        
        user.is_premium = True
        user.premium_plan = plan
        user.premium_expires_at = datetime.utcnow() + timedelta(days=duration_days)
        
        # Actualizar límites premium
        if plan == "monthly":
            user.ai_requests_limit = 100  # 100 requests/day
            user.simulacros_limit = 10   # 10 simulacros/month
        elif plan == "yearly":
            user.ai_requests_limit = 200  # 200 requests/day
            user.simulacros_limit = 20   # 20 simulacros/month
        
        self.db.commit()
        return {"success": True, "message": "Actualización a premium exitosa"}
    
    def check_ai_request_limit(self, user_id: str) -> Dict[str, Any]:
        """Verificar límite de requests de IA"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return {"can_request": False, "message": "Usuario no encontrado"}
        
        # Reset daily counter if needed
        if user.ai_requests_used >= user.ai_requests_limit:
            return {"can_request": False, "message": "Límite diario alcanzado"}
        
        return {"can_request": True, "remaining": user.ai_requests_limit - user.ai_requests_used}
    
    def increment_ai_request(self, user_id: str):
        """Incrementar contador de requests de IA"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if user:
            user.ai_requests_used += 1
            self.db.commit()
    
    def get_available_mentors(self, subject_id: Optional[str] = None) -> List[Dict]:
        """Obtener mentores reales disponibles"""
        query = self.db.query(RealMentor).filter(RealMentor.is_available == True)
        if subject_id:
            query = query.filter(RealMentor.subject_id == subject_id)
        
        mentors = query.all()
        return [
            {
                "id": str(mentor.id),
                "name": mentor.name,
                "subject": mentor.subject.name if mentor.subject else "General",
                "bio": mentor.bio,
                "avatar_url": mentor.avatar_url,
                "rating": float(mentor.rating),
                "hourly_rate": float(mentor.hourly_rate)
            }
            for mentor in mentors
        ]
    
    def schedule_mentor_session(self, user_id: str, mentor_id: str, 
                              session_date: datetime, duration_minutes: int) -> Dict[str, Any]:
        """Programar sesión con mentor"""
        session = MentorSession(
            user_id=user_id,
            mentor_id=mentor_id,
            session_date=session_date,
            duration_minutes=duration_minutes
        )
        self.db.add(session)
        self.db.commit()
        return {"success": True, "session_id": str(session.id)}
    
    def generate_predictive_analytics(self, user_id: str) -> Dict[str, Any]:
        """Generar análisis predictivo avanzado (solo premium)"""
        # Simular análisis predictivo basado en progreso del usuario
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return {"success": False, "message": "Usuario no encontrado"}
        
        # Calcular predicción basada en nivel y experiencia
        base_score = 200 + (user.level * 5) + (user.experience // 100)
        confidence = min(0.95, 0.5 + (user.level / 100))
        
        analytics = PredictiveAnalytics(
            user_id=user_id,
            predicted_icfes_score=base_score,
            confidence_level=confidence,
            improvement_potential=min(100, 400 - base_score),
            recommended_focus_areas={
                "matematicas": user.level < 30,
                "lenguaje": user.level < 25,
                "ciencias": user.level < 35,
                "sociales": user.level < 20,
                "ingles": user.level < 15
            },
            next_milestone_date=datetime.utcnow().date() + timedelta(days=7)
        )
        
        self.db.add(analytics)
        self.db.commit()
        
        return {
            "success": True,
            "predicted_score": base_score,
            "confidence": confidence,
            "improvement_potential": min(100, 400 - base_score),
            "recommended_areas": analytics.recommended_focus_areas
        } 