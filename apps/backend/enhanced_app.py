from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List
import os
import json
from datetime import datetime

app = FastAPI(
    title="ICFES Leveling API",
    description="Sistema de recomendaciones educativas ICFES",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class LoginRequest(BaseModel):
    email: str
    password: str

class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None

class User(BaseModel):
    id: int
    username: str
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_active: bool = True

# Mock data storage
mock_users = [
    {
        "id": 1,
        "username": "student1",
        "email": "student1@icfes.com",
        "password": "password123",
        "first_name": "Estudiante",
        "last_name": "Demo",
        "is_active": True
    },
    {
        "id": 2,
        "username": "admin",
        "email": "admin@icfes.com", 
        "password": "admin123",
        "first_name": "Admin",
        "last_name": "Sistema",
        "is_active": True
    }
]

# Basic endpoints
@app.get("/")
async def root():
    return {"message": "ICFES Leveling API is running!", "status": "online"}

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "backend",
        "version": "1.0.0",
        "environment": "development"
    }

@app.get("/api/health")
async def api_health():
    return {
        "status": "healthy",
        "api": "ready",
        "timestamp": datetime.utcnow().isoformat()
    }

# Authentication endpoints
@app.post("/api/auth/login")
async def login(request: LoginRequest):
    try:
        # Find user
        user = None
        for u in mock_users:
            if u["email"] == request.email and u["password"] == request.password:
                user = u
                break
        
        if not user:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Return mock token and user data
        return {
            "access_token": f"mock_token_{user['id']}",
            "token_type": "bearer",
            "user": {
                "id": user["id"],
                "username": user["username"],
                "email": user["email"],
                "first_name": user["first_name"],
                "last_name": user["last_name"],
                "is_active": user["is_active"]
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/auth/register")
async def register(request: RegisterRequest):
    try:
        # Check if user exists
        for u in mock_users:
            if u["email"] == request.email or u["username"] == request.username:
                raise HTTPException(status_code=400, detail="User already exists")
        
        # Create new user
        new_user = {
            "id": len(mock_users) + 1,
            "username": request.username,
            "email": request.email,
            "password": request.password,
            "first_name": request.first_name,
            "last_name": request.last_name,
            "is_active": True
        }
        mock_users.append(new_user)
        
        return {
            "access_token": f"mock_token_{new_user['id']}",
            "token_type": "bearer",
            "user": {
                "id": new_user["id"],
                "username": new_user["username"],
                "email": new_user["email"],
                "first_name": new_user["first_name"],
                "last_name": new_user["last_name"],
                "is_active": new_user["is_active"]
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/auth/me")
async def get_current_user(request: Request):
    try:
        # Mock authentication - get token from header
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="No valid token")
        
        token = auth_header.split(" ")[1]
        if not token.startswith("mock_token_"):
            raise HTTPException(status_code=401, detail="Invalid token")
        
        user_id = int(token.replace("mock_token_", ""))
        user = None
        for u in mock_users:
            if u["id"] == user_id:
                user = u
                break
        
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        
        return {
            "id": user["id"],
            "username": user["username"],
            "email": user["email"],
            "first_name": user["first_name"],
            "last_name": user["last_name"],
            "is_active": user["is_active"]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Mock subjects endpoint
@app.get("/api/subjects")
async def get_subjects():
    return [
        {"id": 1, "name": "Matemáticas", "icon": "📊"},
        {"id": 2, "name": "Lectura Crítica", "icon": "📚"},
        {"id": 3, "name": "Ciencias Naturales", "icon": "🔬"},
        {"id": 4, "name": "Sociales y Ciudadanas", "icon": "🌍"},
        {"id": 5, "name": "Inglés", "icon": "🌐"}
    ]

# Mock questions endpoints
@app.get("/api/questions/subject/{subject_id}")
async def get_questions_by_subject(subject_id: int):
    return {
        "subject_id": subject_id,
        "questions": [
            {
                "id": f"{subject_id}_1",
                "text": f"Pregunta de ejemplo para la materia {subject_id}",
                "options": ["Opción A", "Opción B", "Opción C", "Opción D"],
                "correct_answer": "A",
                "difficulty": 2
            }
        ]
    }

# Sistema de recomendaciones endpoints
@app.get("/api/v1/recommendations/system/health")
async def recommendations_health():
    return {
        "overall_status": "excellent",
        "overall_score": 0.923,
        "components": {
            "embeddings": {"score": 0.95, "status": "healthy"},
            "recommendations": {"score": 0.89, "status": "good"},
            "weakness_analysis": {"score": 0.91, "status": "healthy"}
        },
        "last_check": datetime.utcnow().isoformat()
    }

@app.get("/api/v2/recommendations/system/health")
async def recommendations_v2_health():
    return {
        "overall_status": "excellent",
        "overall_score": 0.923,
        "components": {
            "embeddings": {"score": 0.95, "status": "healthy"},
            "recommendations": {"score": 0.89, "status": "good"},
            "weakness_analysis": {"score": 0.91, "status": "healthy"},
            "yaml_plans": {"score": 0.88, "status": "good"},
            "performance": {"score": 0.93, "status": "healthy"}
        },
        "last_check": datetime.utcnow().isoformat()
    }

@app.get("/api/v2/recommendations/student/{student_id}")
async def get_student_recommendations(student_id: str):
    return {
        "student_id": student_id,
        "recommendations": [
            {
                "video_id": 1001,
                "title": "Resolución de Ecuaciones Cuadráticas - Método Factorización",
                "channel": "MathExpert",
                "duration_minutes": 12.5,
                "youtube_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                "recommendation_score": 0.89,
                "recommendation_type": "error_remediation",
                "confidence_level": "high",
                "targets_weakness": {
                    "subject": "Matemáticas",
                    "topic": "Ecuaciones Cuadráticas",
                    "severity": "critical",
                    "priority_score": 0.85
                }
            }
        ],
        "weaknesses_summary": [
            {
                "subject": "Matemáticas",
                "topic": "Ecuaciones Cuadráticas",
                "severity": "critical",
                "priority_score": 0.85,
                "needs_action": "immediate_practice"
            }
        ],
        "summary": {
            "total_weaknesses_analyzed": 3,
            "critical_weaknesses": 1,
            "recommendations_generated": 1,
            "average_recommendation_score": 0.89
        },
        "status": "success",
        "generated_at": datetime.utcnow().isoformat()
    }

# Mock dashboard endpoint
@app.get("/api/dashboard/stats")
async def get_dashboard_stats():
    return {
        "total_users": len(mock_users),
        "active_sessions": 5,
        "total_questions": 1247,
        "recommendation_accuracy": 0.89,
        "system_health": "excellent"
    }

@app.get("/docs")
async def get_documentation():
    return {
        "message": "API Documentation",
        "swagger_ui": "http://localhost:4000/docs",
        "redoc": "http://localhost:4000/redoc"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=4000)
