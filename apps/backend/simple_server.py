#!/usr/bin/env python3
"""
Servidor simplificado para pruebas del sistema ICFES Leveling
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import random
import json

# Initialize FastAPI app
app = FastAPI(title="ICFES Leveling Test Server", version="1.0.0")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage
users_db = {}
tests_db = {}
study_plans_db = {}
videos_db = {}
session_counter = 0

# Models
class UserRegister(BaseModel):
    email: str
    password: str
    display_name: str

class UserLogin(BaseModel):
    username: str
    password: str

class DiagnosticSubmit(BaseModel):
    user_id: int
    subject_id: int
    answers: List[Dict[str, Any]]
    time_spent: int

class StudyPlanRequest(BaseModel):
    user_id: int
    subject_id: int
    weak_topics: List[str]

# Sample data
SUBJECTS = {
    1: {"name": "Matemáticas", "topics": ["Álgebra", "Geometría", "Cálculo", "Estadística"]},
    2: {"name": "Lenguaje", "topics": ["Comprensión", "Gramática", "Literatura", "Redacción"]},
    3: {"name": "Ciencias", "topics": ["Física", "Química", "Biología", "Ecología"]},
    4: {"name": "Sociales", "topics": ["Historia", "Geografía", "Filosofía", "Economía"]},
    5: {"name": "Inglés", "topics": ["Grammar", "Reading", "Listening", "Writing"]}
}

SAMPLE_QUESTIONS = [
    {
        "id": i,
        "text": f"Pregunta de ejemplo {i}",
        "options": ["Opción A", "Opción B", "Opción C", "Opción D"],
        "correct_answer": random.choice(["A", "B", "C", "D"]),
        "difficulty": random.choice([1, 2, 3]),
        "topic": random.choice(["Álgebra", "Geometría", "Cálculo"])
    }
    for i in range(1, 21)
]

SAMPLE_VIDEOS = [
    {
        "id": i,
        "title": f"Video educativo {i}",
        "url": f"https://youtube.com/watch?v=video{i}",
        "duration": random.randint(5, 30),
        "topic": random.choice(["Álgebra", "Geometría", "Cálculo"])
    }
    for i in range(1, 11)
]

# Routes
@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.post("/auth/register")
async def register(user: UserRegister):
    global session_counter
    session_counter += 1
    user_id = session_counter
    
    users_db[user_id] = {
        "id": user_id,
        "email": user.email,
        "display_name": user.display_name,
        "level": 1,
        "xp": 0,
        "rank": "E",
        "created_at": datetime.now().isoformat()
    }
    
    return {
        "user": users_db[user_id],
        "access_token": f"test_token_{user_id}",
        "token_type": "bearer"
    }

@app.post("/auth/login")
async def login(credentials: UserLogin):
    # Simulate login - always succeed for testing
    user_id = 1
    if user_id not in users_db:
        users_db[user_id] = {
            "id": user_id,
            "email": credentials.username,
            "display_name": "Test User",
            "level": 1,
            "xp": 0,
            "rank": "E"
        }
    
    return {
        "user": users_db[user_id],
        "access_token": f"test_token_{user_id}",
        "token_type": "bearer"
    }

@app.get("/api/v1/subjects")
async def get_subjects():
    return [
        {"id": id, "name": data["name"], "icon": "📚"}
        for id, data in SUBJECTS.items()
    ]

@app.get("/api/v1/diagnostic/test-questions/{subject_id}")
async def get_diagnostic_questions(subject_id: int):
    if subject_id not in SUBJECTS:
        raise HTTPException(status_code=404, detail="Subject not found")
    
    # Return adaptive questions
    questions = SAMPLE_QUESTIONS[:10]
    for q in questions:
        q["subject_id"] = subject_id
    
    return {
        "subject": SUBJECTS[subject_id]["name"],
        "questions": questions,
        "total": len(questions),
        "time_limit": 30
    }

@app.post("/api/v1/diagnostic/submit")
async def submit_diagnostic_test(submission: DiagnosticSubmit):
    global session_counter
    session_counter += 1
    test_id = session_counter
    
    # Calculate score
    correct = random.randint(3, 8)
    total = len(submission.answers)
    score = (correct / total) * 100
    
    # Determine rank
    if score >= 90:
        rank = "S"
    elif score >= 80:
        rank = "A"
    elif score >= 60:
        rank = "B"
    elif score >= 40:
        rank = "C"
    else:
        rank = "D"
    
    # Store test result
    tests_db[test_id] = {
        "id": test_id,
        "user_id": submission.user_id,
        "subject_id": submission.subject_id,
        "score": score,
        "rank": rank,
        "correct_answers": correct,
        "total_questions": total,
        "weak_topics": random.sample(SUBJECTS[submission.subject_id]["topics"], 2),
        "timestamp": datetime.now().isoformat()
    }
    
    # Update user stats
    if submission.user_id in users_db:
        users_db[submission.user_id]["xp"] += correct * 10
        users_db[submission.user_id]["rank"] = rank
    
    return tests_db[test_id]

@app.get("/api/v1/diagnostic/results/{test_id}")
async def get_test_results(test_id: int):
    if test_id not in tests_db:
        raise HTTPException(status_code=404, detail="Test not found")
    return tests_db[test_id]

@app.post("/api/v1/study-plans/generate")
async def generate_study_plan(request: StudyPlanRequest):
    global session_counter
    session_counter += 1
    plan_id = session_counter
    
    # Generate adaptive study plan
    plan = {
        "id": plan_id,
        "user_id": request.user_id,
        "subject_id": request.subject_id,
        "weak_topics": request.weak_topics,
        "sessions": [
            {
                "day": i + 1,
                "topic": request.weak_topics[i % len(request.weak_topics)],
                "activities": [
                    {"type": "video", "content": f"Video sobre {request.weak_topics[i % len(request.weak_topics)]}"},
                    {"type": "exercise", "content": f"Ejercicios de {request.weak_topics[i % len(request.weak_topics)]}"},
                    {"type": "quiz", "content": f"Quiz de {request.weak_topics[i % len(request.weak_topics)]}"}
                ]
            }
            for i in range(7)
        ],
        "created_at": datetime.now().isoformat()
    }
    
    study_plans_db[plan_id] = plan
    return plan

@app.get("/api/v1/study-plans/{plan_id}")
async def get_study_plan(plan_id: int):
    if plan_id not in study_plans_db:
        raise HTTPException(status_code=404, detail="Study plan not found")
    return study_plans_db[plan_id]

@app.get("/api/v1/videos/recommendations")
async def get_video_recommendations(user_id: int = 1, topic: str = None):
    videos = SAMPLE_VIDEOS
    if topic:
        videos = [v for v in videos if v["topic"] == topic]
    
    # Add context for why the video is recommended
    for video in videos:
        video["recommendation_reason"] = f"Recomendado porque fallaste preguntas sobre {video['topic']}"
    
    return {
        "videos": videos[:5],
        "total": len(videos)
    }

@app.post("/api/v1/ai/explanation")
async def get_ai_explanation(question_id: int = 1):
    return {
        "question_id": question_id,
        "explanation": f"Esta pregunta evalúa tu comprensión sobre conceptos fundamentales. La respuesta correcta se basa en...",
        "tips": [
            "Revisa los conceptos básicos",
            "Practica con ejercicios similares",
            "Mira los videos recomendados"
        ]
    }

@app.get("/api/v1/users/{user_id}/progress")
async def get_user_progress(user_id: int):
    if user_id not in users_db:
        raise HTTPException(status_code=404, detail="User not found")
    
    user = users_db[user_id]
    
    # Add progress stats
    progress = {
        **user,
        "total_tests": len([t for t in tests_db.values() if t["user_id"] == user_id]),
        "study_plans": len([p for p in study_plans_db.values() if p["user_id"] == user_id]),
        "videos_watched": random.randint(0, 20),
        "exercises_completed": random.randint(0, 50),
        "current_streak": random.randint(0, 7)
    }
    
    return progress

@app.post("/api/v1/sessions/save")
async def save_session(user_id: int, data: Dict[str, Any]):
    # Simulate session saving
    return {
        "status": "saved",
        "user_id": user_id,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/v1/sessions/load/{user_id}")
async def load_session(user_id: int):
    if user_id not in users_db:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "user": users_db[user_id],
        "last_activity": datetime.now().isoformat(),
        "pending_tasks": []
    }

if __name__ == "__main__":
    import uvicorn
    print("Starting ICFES Leveling Test Server on http://localhost:4000")
    print("This is a simplified server for testing purposes")
    uvicorn.run(app, host="127.0.0.1", port=4000)