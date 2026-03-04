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
        "iat": datetime.utcnow(),  # Issued at
        "type": "access"  # Token type
    })
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None, return_payload: bool = False):
    """Crear token de refresh JWT"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    # Add token ID for revocation support
    to_encode.update({
        "exp": expire,
        "jti": secrets.token_urlsafe(16),  # JWT ID for revocation
        "iat": datetime.utcnow(),  # Issued at
        "type": "refresh"  # Token type
    })
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.ALGORITHM)
    if return_payload:
        return encoded_jwt, to_encode
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
    
    # Authentication is ALWAYS required - no bypass allowed
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


async def get_current_user_optional(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Get current user from JWT token, but return None if no token provided.

    Used for endpoints that work for both authenticated and unauthenticated users,
    providing additional features for logged-in users.
    """
    if not token:
        return None

    try:
        payload = verify_token(token)
        if payload is None:
            return None
        user_id: str = payload.get("sub")
        if user_id is None:
            return None
    except JWTError:
        return None

    user = db.query(User).filter(User.id == user_id).first()
    return user

# Note: get_current_admin_user removed since is_admin field doesn't exist in User model