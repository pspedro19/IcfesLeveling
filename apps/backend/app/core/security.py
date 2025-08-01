from datetime import datetime, timedelta
from typing import Optional, Union, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from .config import settings
from .database import get_db
from ..models.user import User

# Configuración de password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verificar contraseña"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Generar hash de contraseña"""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Crear token JWT"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> Optional[str]:
    """Verificar token JWT y retornar user_id"""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            return None
        return user_id
    except JWTError:
        return None

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """Obtener usuario actual desde token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    user_id = verify_token(token)
    if user_id is None:
        raise credentials_exception
    
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception
    
    return user

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