from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..core.database import get_db
from ..schemas.personality import (
    PersonalityTestRequest, PersonalityTestResponse,
    PersonalityQuestionResponse, UserProfileResponse
)
from ..services.personality_service import PersonalityAnalyzer
from ..models import PersonalityQuestion, UserProfile, HeroClass

router = APIRouter(prefix="/personality", tags=["personality"])

@router.get("/questions", response_model=List[PersonalityQuestionResponse])
async def get_personality_questions(db: Session = Depends(get_db)):
    """Obtiene todas las preguntas de personalidad activas"""
    analyzer = PersonalityAnalyzer(db)
    questions = analyzer.get_personality_questions()
    return questions

@router.post("/test", response_model=PersonalityTestResponse)
async def analyze_personality(request: PersonalityTestRequest, db: Session = Depends(get_db)):
    """Analiza las respuestas del test de personalidad y asigna una clase épica"""
    try:
        analyzer = PersonalityAnalyzer(db)
        result = analyzer.analyze_personality(request)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al analizar personalidad: {str(e)}")

@router.get("/profile/{user_id}", response_model=UserProfileResponse)
async def get_user_profile(user_id: str, db: Session = Depends(get_db)):
    """Obtiene el perfil de personalidad de un usuario"""
    profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Perfil no encontrado")
    
    # Incluir datos de la clase épica
    hero_class = db.query(HeroClass).filter(HeroClass.id == profile.hero_class_id).first()
    if hero_class:
        profile.hero_class = {
            "id": str(hero_class.id),
            "name": hero_class.name,
            "description": hero_class.description,
            "avatar_url": hero_class.avatar_url,
            "special_ability": hero_class.special_ability,
            "element": hero_class.element,
            "color_theme": hero_class.color_theme,
            "class_type": hero_class.class_type
        }
    
    return profile

@router.get("/hero-classes", response_model=List[dict])
async def get_hero_classes(db: Session = Depends(get_db)):
    """Obtiene todas las clases épicas disponibles"""
    hero_classes = db.query(HeroClass).all()
    return [
        {
            "id": str(hc.id),
            "name": hc.name,
            "description": hc.description,
            "avatar_url": hc.avatar_url,
            "special_ability": hc.special_ability,
            "element": hc.element,
            "color_theme": hc.color_theme,
            "class_type": hc.class_type
        }
        for hc in hero_classes
    ]

@router.get("/hero-class/{class_id}", response_model=dict)
async def get_hero_class(class_id: str, db: Session = Depends(get_db)):
    """Obtiene una clase épica específica"""
    hero_class = db.query(HeroClass).filter(HeroClass.id == class_id).first()
    if not hero_class:
        raise HTTPException(status_code=404, detail="Clase épica no encontrada")
    
    return {
        "id": str(hero_class.id),
        "name": hero_class.name,
        "description": hero_class.description,
        "avatar_url": hero_class.avatar_url,
        "special_ability": hero_class.special_ability,
        "element": hero_class.element,
        "color_theme": hero_class.color_theme,
        "class_type": hero_class.class_type,
        "stats_boost": hero_class.get_stats_boost()
    } 