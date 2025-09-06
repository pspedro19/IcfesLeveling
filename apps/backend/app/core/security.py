from datetime import datetime, timedelta
from typing import Optional, Union, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
import uuid
import hashlib
import secrets

from .config import settings
from .database import get_db
from ..models.user import User

# Configuración de password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login", auto_error=False)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verificar contraseña"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Generar hash de contraseña"""
    # Add salt for extra security in production
    if settings.ENVIRONMENT == "production":
        # Use higher cost factor in production for better security
        return pwd_context.hash(password, rounds=12)
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Crear token de acceso JWT"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # Add token ID for revocation support
    to_encode.update({
        "exp": expire,
        "jti": secrets.token_urlsafe(16),  # JWT ID for revocation
        "iat": datetime.utcnow()  # Issued at
    })
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> Optional[dict]:
    """Verificar token JWT"""
    try:
        payload = jwt.decode(
            token, 
            settings.JWT_SECRET, 
            algorithms=[settings.ALGORITHM],
            options={"verify_exp": True, "verify_iat": True}
        )
        
        # Additional validation for production
        if settings.ENVIRONMENT == "production":
            # Check if token was issued in the future (clock skew attack)
            if "iat" in payload:
                issued_at = datetime.fromtimestamp(payload["iat"])
                if issued_at > datetime.utcnow() + timedelta(seconds=30):
                    return None
        
        return payload
    except JWTError:
        return None

async def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Obtener usuario actual desde token JWT"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Strict authentication in production
    if settings.ENVIRONMENT == "production" and not token:
        raise credentials_exception
    
    # Development mode: allow requests without token for testing
    # This will be automatically disabled in production
    if settings.ENVIRONMENT == "development" and not token:
        # Return a mock admin user for development testing
        mock_user = User(
            id=uuid.uuid4(),
            email="admin@icfes-leveling.dev",
            username="admin_user", 
            hashed_password="",
            is_active=True,
            display_name="Admin User",
            level=99,
            experience=50000,
            rank="S",
            hp=100,
            mp=50,
            power=10,
            wisdom=10,
            speed=10,
            orbs=1000,
            crystals=0,
            streak_days=0,
            premium_plan="admin",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        # Set a consistent ID for development to avoid database lookups
        mock_user.id = uuid.UUID("00000000-0000-0000-0000-000000000001")
        return mock_user
    
    if not token:
        raise credentials_exception
    
    try:
        payload = verify_token(token)
        if payload is None:
            raise credentials_exception
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception
    
    return user

async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Obtener usuario activo actual"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

# Note: get_current_admin_user removed since is_admin field doesn't exist in User model

def calculate_level(experience: int) -> int:
    """Calcular nivel basado en experiencia"""
    # Fórmula exponencial: level = floor(sqrt(exp / 100)) + 1
    return int((experience / 100) ** 0.5) + 1

def calculate_rank(level: int) -> str:
    """Calcular rango basado en nivel"""
    if level >= 90:
        return "SSS"
    elif level >= 80:
        return "SS"
    elif level >= 70:
        return "S"
    elif level >= 60:
        return "A"
    elif level >= 50:
        return "B"
    elif level >= 30:
        return "C"
    elif level >= 15:
        return "D"
    else:
        return "E"

def calculate_damage(
    user_power: int,
    user_wisdom: int,
    is_correct: bool,
    response_time_ms: int,
    difficulty: int,
    combo_count: int = 0
) -> int:
    """Calcular daño basado en múltiples factores"""
    if not is_correct:
        return 0
    
    # Daño base
    base_damage = (user_power + user_wisdom) * 2
    
    # Multiplicador por tiempo de respuesta (crítico si < 3 segundos)
    time_multiplier = 1.0
    if response_time_ms < 3000:
        time_multiplier = 2.0  # Crítico
    elif response_time_ms < 10000:
        time_multiplier = 1.5
    elif response_time_ms < 20000:
        time_multiplier = 1.2
    
    # Multiplicador por dificultad
    difficulty_multiplier = 1 + (difficulty - 1) * 0.1
    
    # Multiplicador por combo
    combo_multiplier = 1 + (combo_count * 0.1)
    
    total_damage = int(base_damage * time_multiplier * difficulty_multiplier * combo_multiplier)
    return max(1, total_damage)  # Mínimo 1 de daño

def calculate_experience_gain(
    is_correct: bool,
    difficulty: int,
    response_time_ms: int,
    combo_count: int = 0
) -> int:
    """Calcular experiencia ganada"""
    if not is_correct:
        return max(1, difficulty)  # Experiencia mínima por intentar
    
    # Experiencia base por dificultad
    base_exp = difficulty * 10
    
    # Bonus por tiempo rápido
    time_bonus = 0
    if response_time_ms < 5000:
        time_bonus = base_exp * 0.5
    elif response_time_ms < 15000:
        time_bonus = base_exp * 0.2
    
    # Bonus por combo
    combo_bonus = combo_count * 5
    
    total_exp = base_exp + time_bonus + combo_bonus
    return int(total_exp)

def calculate_orbs_gain(
    is_correct: bool,
    difficulty: int,
    critical_hit: bool
) -> int:
    """Calcular orbes ganados"""
    if not is_correct:
        return 1  # Orbe mínimo por intentar
    
    base_orbs = difficulty * 2
    
    if critical_hit:
        base_orbs *= 2
    
    return base_orbs 