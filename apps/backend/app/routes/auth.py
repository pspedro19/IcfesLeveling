from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from typing import Optional
from sqlalchemy import func

from ..core.database import get_db
from ..core.security import create_access_token, get_password_hash, verify_password, get_current_user
from ..core.config import settings
from ..schemas.user import UserCreate, UserLogin, UserResponse, GuestUserCreate
from ..models.user import User
from ..models.user_profile import UserProfile

router = APIRouter(prefix="/auth", tags=["authentication"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

@router.post("/register", response_model=UserResponse)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """Registrar un nuevo usuario"""
    # Verificar si el usuario ya existe
    existing_user = db.query(User).filter(
        (User.username == user_data.username) | (User.email == user_data.email)
    ).first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username o email ya existe"
        )
    
    # Crear nuevo usuario
    hashed_password = get_password_hash(user_data.password)
    db_user = User(
        username=user_data.username,
        email=user_data.email,
        display_name=user_data.display_name,
        hashed_password=hashed_password
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user

@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Iniciar sesión y obtener token"""
    user = db.query(User).filter(User.username == form_data.username).first()
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Actualizar último login (si el campo existe)
    # user.last_login = db.query(func.now()).scalar()
    # db.commit()
    
    # Crear token de acceso
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": UserResponse.from_orm(user)
    }

@router.get("/me", response_model=UserResponse)
def get_current_user(
    current_user: User = Depends(get_current_user)
):
    """Obtener información del usuario actual"""
    return current_user

@router.post("/refresh")
def refresh_token(
    current_user: User = Depends(get_current_user)
):
    """Renovar token de acceso"""
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(current_user.id)}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

@router.post("/register-guest", response_model=UserResponse)
def register_guest(guest_data: GuestUserCreate, db: Session = Depends(get_db)):
    """Registrar un usuario invitado con sus datos previos"""
    # Verificar si el usuario ya existe
    existing_user = db.query(User).filter(
        (User.username == guest_data.username) | (User.email == guest_data.email)
    ).first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username o email ya existe"
        )
    
    # Crear nuevo usuario
    hashed_password = get_password_hash(guest_data.password)
    db_user = User(
        username=guest_data.username,
        email=guest_data.email,
        display_name=guest_data.username,
        hashed_password=hashed_password,
        level=1,  # Nivel inicial
        total_exp=int(guest_data.guestData.initialScore * 10)  # Conversión de score a exp
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # Crear perfil de usuario con datos del invitado
    user_profile = UserProfile(
        user_id=db_user.id,
        hero_class="assassin",  # Clase por defecto
        selected_subjects=[],  # Se configurará en onboarding
        personality_type="balanced",  # Por defecto
        study_preferences={
            "session_duration": 30,
            "difficulty_preference": "adaptive",
            "notification_enabled": True
        },
        achievements=[],
        rank="E",  # Rango inicial basado en score
        rank_progress=guest_data.guestData.initialScore,
        total_questions_answered=guest_data.guestData.questionsAnswered,
        total_study_time=guest_data.guestData.timeSpent,
        badges=["guest_convert"],  # Badge especial por conversión
        titles=["Cazador Renacido"],  # Título especial
        current_title="Cazador Renacido",
        avatar_frame="default",
        theme_preference="dark"
    )
    
    if guest_data.guestData.initialScore >= 80:
        user_profile.rank = "B"
    elif guest_data.guestData.initialScore >= 60:
        user_profile.rank = "C"
    elif guest_data.guestData.initialScore >= 40:
        user_profile.rank = "D"
    
    db.add(user_profile)
    db.commit()
    
    # Bonus de bienvenida
    db_user.orbs = 500  # 500 orbes de bonus
    db_user.is_premium = True
    db_user.premium_expires_at = func.now() + timedelta(days=3)  # 3 días de premium gratis
    db.commit()
    
    return db_user 