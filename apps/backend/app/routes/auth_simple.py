from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from ..core.database import get_db
from ..models.user import User
from ..core.security import verify_password, create_access_token, get_password_hash
import uuid
from ..core.config import settings

router = APIRouter(prefix="/auth-simple", tags=["auth-simple"])

@router.post("/login")
def login_simple(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Iniciar sesión simple y obtener token"""
    try:
        user = db.query(User).filter(User.username == form_data.username).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuario no encontrado",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not verify_password(form_data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Contraseña incorrecta",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Crear token de acceso
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": str(user.id)}, expires_delta=access_token_expires
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": str(user.id),
                "username": user.username,
                "email": user.email,
                "level": user.level,
                "rank": user.rank,
                "premium_plan": "free"  # Default since column doesn't exist
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error en login: {str(e)}"
        )

@router.get("/test")
def test_auth():
    """Endpoint de prueba para verificar que funciona"""
    return {"status": "auth working", "message": "Sistema de autenticación funcionando"}

@router.post("/test-password")
def test_password(password: str = "secret", db: Session = Depends(get_db)):
    """Test password verification"""
    try:
        user = db.query(User).filter(User.username == "admin").first()
        if not user:
            return {"error": "User not found"}
        
        # Try to verify password
        is_valid = verify_password(password, user.hashed_password)
        
        return {
            "password_provided": password,
            "stored_hash": user.hashed_password,
            "is_valid": is_valid,
            "hash_length": len(user.hashed_password),
            "hash_starts_with": user.hashed_password[:10] if user.hashed_password else "None"
        }
    except Exception as e:
        return {"error": str(e)}

@router.post("/create-test-users")
def create_test_users(db: Session = Depends(get_db)):
    """Crear usuarios de prueba con hashes correctos"""
    try:
        users_created = []
        
        # Check and create admin user if not exists
        if not db.query(User).filter(User.username == "admin").first():
            admin_hash = get_password_hash("secret")
            admin_user = User(
                id=uuid.uuid4(),
                username="admin",
                email="admin@test.com",
                hashed_password=admin_hash,
                level=50,
                experience=10000,
                rank="S",
                hp=200,
                mp=150,
                power=50,
                wisdom=50,
                speed=50,
                orbs=1000,
                crystals=500,
                is_active=True
            )
            db.add(admin_user)
            users_created.append("admin")
        
        # Check and create test user if not exists
        if not db.query(User).filter(User.username == "test").first():
            test_hash = get_password_hash("secret")
            test_user = User(
                id=uuid.uuid4(),
                username="test",
                email="test@test.com",
                hashed_password=test_hash,
                level=1,
                experience=0,
                rank="E",
                hp=100,
                mp=50,
                power=10,
                wisdom=10,
                speed=10,
                orbs=0,
                crystals=0,
                is_active=True
            )
            db.add(test_user)
            users_created.append("test")
        
        # Check and create student1 user if not exists
        if not db.query(User).filter(User.username == "student1").first():
            student1_hash = get_password_hash("secret")
            student1_user = User(
                id=uuid.uuid4(),
                username="student1",
                email="student1@test.com",
                hashed_password=student1_hash,
                level=5,
                experience=0,
                rank="D",
                hp=100,
                mp=50,
                power=10,
                wisdom=10,
                speed=10,
                orbs=0,
                crystals=0,
                is_active=True
            )
            db.add(student1_user)
            users_created.append("student1")
        
        if users_created:
            db.commit()
        
        return {
            "status": "success",
            "message": f"Usuarios creados: {', '.join(users_created) if users_created else 'ninguno (ya existían)'}",
            "users_created": users_created,
            "available_users": [
                {"username": "admin", "password": "secret", "level": 50, "rank": "S"},
                {"username": "test", "password": "secret", "level": 1, "rank": "E"},
                {"username": "student1", "password": "secret", "level": 5, "rank": "D"}
            ]
        }
        
    except Exception as e:
        return {"status": "error", "error": str(e)}

@router.get("/users")
def list_users(db: Session = Depends(get_db)):
    """Listar usuarios para testing"""
    try:
        users = db.query(User).limit(10).all()
        return {
            "status": "success",
            "users": [
                {
                    "username": user.username,
                    "email": user.email,
                    "level": user.level,
                    "rank": user.rank,
                    "premium_plan": "free"  # Default since column doesn't exist
                }
                for user in users
            ]
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}

@router.post("/reset-test-users")
def reset_test_users(db: Session = Depends(get_db)):
    """Reset test users passwords"""
    try:
        # Update existing users with correct password hashes
        admin_user = db.query(User).filter(User.username == "admin").first()
        if admin_user:
            admin_user.hashed_password = get_password_hash("secret")
        
        test_user = db.query(User).filter(User.username == "test").first()
        if test_user:
            test_user.hashed_password = get_password_hash("secret")
            
        student1_user = db.query(User).filter(User.username == "student1").first()
        if student1_user:
            student1_user.hashed_password = get_password_hash("secret")
        
        db.commit()
        
        return {
            "status": "success",
            "message": "Test users passwords reset to 'secret'",
            "users_updated": ["admin", "test", "student1"]
        }
        
    except Exception as e:
        return {"status": "error", "error": str(e)}