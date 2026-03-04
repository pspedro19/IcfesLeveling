from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta, timezone
from typing import Optional
from sqlalchemy import func

from ..core.database import get_db
from ..core import security # Import as alias
from ..core.config import settings
from ..schemas.user import UserCreate, UserLogin, UserResponse, GuestUserCreate
from ..schemas.token import RefreshTokenRequest # New import
from ..models.user import User
from ..models.user_profile import UserProfile
from ..models.refresh_token import RefreshToken
from ..middleware.rate_limit import rate_limit
from datetime import datetime

router = APIRouter(prefix="/auth", tags=["authentication"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

@router.post("/register", response_model=UserResponse)
@rate_limit(limit=5, window=60)
async def register(request: Request, user_data: UserCreate, db: Session = Depends(get_db)):
    """Registrar un nuevo usuario"""
    existing_user = db.query(User).filter(
        (User.username == user_data.username) | (User.email == user_data.email)
    ).first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username o email ya existe"
        )
    
    hashed_password = security.get_password_hash(user_data.password)
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
@rate_limit(limit=5, window=60)
async def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Iniciar sesión y obtener token"""
    user = db.query(User).filter(User.username == form_data.username).first()
    
    if not user or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )

    refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    refresh_token_str, refresh_payload = security.create_refresh_token(
        data={"sub": str(user.id)}, expires_delta=refresh_token_expires, return_payload=True
    )

    # Store the new refresh token in the database
    db_refresh_token = RefreshToken(
        user_id=user.id,
        jti=refresh_payload["jti"],
        expires_at=datetime.fromtimestamp(refresh_payload["exp"])
    )
    db.add(db_refresh_token)
    db.commit()

    return {
        "access_token": access_token,
        "refresh_token": refresh_token_str,
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "token_type": "bearer",
        "user": UserResponse.from_orm(user)
    }

@router.get("/me", response_model=UserResponse)
@rate_limit(limit=100, window=60)
async def get_me(request: Request, current_user: User = Depends(security.get_current_user)):
    """Obtener información del usuario actual"""
    return current_user

@router.post("/refresh")
@rate_limit(limit=10, window=60)
async def refresh_token(
    request: Request,
    refresh_token_request: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """Renovar token de acceso usando un refresh token con rotación"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid refresh token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = security.verify_token(refresh_token_request.refresh_token)

    if payload is None or payload.get("type") != "refresh":
        raise credentials_exception

    user_id: str = payload.get("sub")
    jti: str = payload.get("jti")
    if not user_id or not jti:
        raise credentials_exception

    # Verify token in database
    db_token = db.query(RefreshToken).filter(RefreshToken.jti == jti).first()

    # TOKEN REUSE DETECTION: If token was already revoked, someone is reusing it!
    # This could indicate token theft - revoke ALL tokens for this user
    if db_token and db_token.revoked:
        # Potential security breach - revoke all user tokens
        db.query(RefreshToken).filter(
            RefreshToken.user_id == db_token.user_id
        ).update({"revoked": True})
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token reuse detected. All sessions revoked for security.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not db_token or db_token.expires_at < datetime.utcnow():
        raise credentials_exception

    if str(db_token.user_id) != user_id:
        raise credentials_exception

    # Revoke the used token (rotation)
    db_token.revoked = True
    db.flush()

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception

    # Issue a new access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    new_access_token = security.create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )

    # Issue a new refresh token (rotation)
    refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    new_refresh_token_str, new_refresh_payload = security.create_refresh_token(
        data={"sub": str(user.id)}, expires_delta=refresh_token_expires, return_payload=True
    )

    # Store the new refresh token
    new_db_refresh_token = RefreshToken(
        user_id=user.id,
        jti=new_refresh_payload["jti"],
        expires_at=datetime.fromtimestamp(new_refresh_payload["exp"])
    )
    db.add(new_db_refresh_token)
    db.commit()

    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token_str,
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "token_type": "bearer"
    }

@router.post("/logout")
@rate_limit(limit=10, window=60)
async def logout(
    request: Request,
    refresh_token_request: RefreshTokenRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_user)
):
    """
    Logout user by revoking their refresh token.
    Requires valid access token in Authorization header.
    """
    payload = security.verify_token(refresh_token_request.refresh_token)

    if payload is None or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid refresh token"
        )

    jti = payload.get("jti")
    if not jti:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid refresh token format"
        )

    # Find and revoke the token
    db_token = db.query(RefreshToken).filter(RefreshToken.jti == jti).first()

    if db_token:
        # Verify token belongs to current user
        if db_token.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Token does not belong to current user"
            )
        db_token.revoked = True
        db.commit()

    return {"message": "Successfully logged out"}

@router.post("/logout-all")
@rate_limit(limit=5, window=60)
async def logout_all_sessions(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_user)
):
    """
    Logout from all devices by revoking all refresh tokens for the user.
    Useful when user suspects account compromise.
    """
    # Revoke all refresh tokens for this user
    revoked_count = db.query(RefreshToken).filter(
        RefreshToken.user_id == current_user.id,
        RefreshToken.revoked == False
    ).update({"revoked": True})

    db.commit()

    return {
        "message": f"Successfully logged out from {revoked_count} session(s)",
        "sessions_revoked": revoked_count
    }

@router.post("/register-guest", response_model=UserResponse)
@rate_limit(limit=5, window=60)
async def register_guest(request: Request, guest_data: GuestUserCreate, db: Session = Depends(get_db)):
    """Registrar un usuario invitado con sus datos previos"""
    existing_user = db.query(User).filter(
        (User.username == guest_data.username) | (User.email == guest_data.email)
    ).first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username o email ya existe"
        )
    
    hashed_password = security.get_password_hash(guest_data.password)
    db_user = User(
        username=guest_data.username,
        email=guest_data.email,
        display_name=guest_data.username,
        hashed_password=hashed_password,
        level=1,
        experience=int(guest_data.guestData.initialScore * 10)
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    user_profile = UserProfile(
        user_id=db_user.id,
        hero_class="assassin",
        selected_subjects=[],
        personality_type="balanced",
        study_preferences={
            "session_duration": 30,
            "difficulty_preference": "adaptive",
            "notification_enabled": True
        },
        achievements=[],
        rank="E",
        rank_progress=guest_data.guestData.initialScore,
        total_questions_answered=guest_data.guestData.questionsAnswered,
        total_study_time=guest_data.guestData.timeSpent,
        badges=["guest_convert"],
        titles=["Cazador Renacido"],
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
    
    db_user.orbs = 500
    # The following fields do not exist on the User model
    # db_user.is_premium = True 
    # db_user.premium_expires_at = func.now() + timedelta(days=3)
    db.commit()
    
    return db_user
 