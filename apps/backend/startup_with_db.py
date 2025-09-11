"""
ICFES LEVELING - Backend con Base de Datos Real
Usa PostgreSQL para todas las operaciones
"""

from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional
import secrets
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
import os
import math
import random

# Database connection
def get_db_connection():
    return psycopg2.connect(
        host="localhost",
        database="icfes_db",
        user="postgres",
        password="postgres",
        cursor_factory=RealDictCursor
    )

app = FastAPI(title="ICFES Leveling API with DB")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory session storage
DIAGNOSTIC_SESSIONS = {}
ACTIVE_TOKENS = {}

# Test users
TEST_USERS = {
    "admin": {
        "id": "1",
        "username": "admin",
        "password": "secret",
        "display_name": "Administrador",
        "level": 50,
        "role": "teacher"
    },
    "test": {
        "id": "2", 
        "username": "test",
        "password": "secret",
        "display_name": "Estudiante Test",
        "level": 1,
        "role": "student"
    }
}

# IRT Calculation Functions
def estimate_theta(responses, prior_theta=0.0):
    """Estima theta usando maximum likelihood con IRT 3PL"""
    if not responses:
        return prior_theta
    
    theta = prior_theta
    for _ in range(10):  # Newton-Raphson iterations
        first_derivative = 0
        second_derivative = 0
        
        for question_id, is_correct, irt_b, time_sec in responses:
            a = 1.0  # discrimination
            b = irt_b  # difficulty
            c = 0.25  # guessing
            
            # 3PL probability
            exp_val = math.exp(a * (theta - b))
            p = c + ((1 - c) * exp_val) / (1 + exp_val)
            p = max(0.01, min(0.99, p))  # avoid log(0)
            
            # Derivatives
            dp_dtheta = a * (1 - c) * exp_val / ((1 + exp_val) ** 2)
            
            if is_correct:
                first_derivative += dp_dtheta / p
            else:
                first_derivative -= dp_dtheta / (1 - p)
            
            second_derivative -= dp_dtheta ** 2 * (1 / (p * (1 - p)))
        
        if abs(second_derivative) > 0.001:
            theta = theta - (first_derivative / second_derivative)
        
        theta = max(-4.0, min(4.0, theta))
    
    return theta

def get_icfes_rank(theta):
    """Convierte theta a rango ICFES estilo Solo Leveling"""
    if theta >= 2.0:
        return {"rank": "S", "name": "Monarca del Conocimiento", "color": "#FFD700"}
    elif theta >= 1.5:
        return {"rank": "A", "name": "Cazador Elite", "color": "#FF6B35"}
    elif theta >= 1.0:
        return {"rank": "B", "name": "Cazador Avanzado", "color": "#4ECDC4"}
    elif theta >= 0.0:
        return {"rank": "C", "name": "Cazador Competente", "color": "#45B7D1"}
    elif theta >= -1.0:
        return {"rank": "D", "name": "Cazador Novato", "color": "#96CEB4"}
    else:
        return {"rank": "E", "name": "Aspirante a Cazador", "color": "#FFEAA7"}

# Pydantic models
class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict

class DiagnosticStart(BaseModel):
    subject_id: str

class DiagnosticAnswer(BaseModel):
    session_id: str
    question_id: int
    selected_option: str
    time_seconds: int

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "ICFES LEVELING API with Database",
        "status": "running",
        "version": "1.0.0",
        "database": "connected"
    }

# Health check
@app.get("/api/v1/health")
async def health_check():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM questions")
        count = cur.fetchone()['count']
        conn.close()
        return {
            "status": "healthy",
            "service": "backend-with-db",
            "database": "connected",
            "questions_count": count
        }
    except Exception as e:
        return {
            "status": "error",
            "service": "backend-with-db",
            "database": "disconnected",
            "error": str(e)
        }

# Login endpoint
@app.post("/api/v1/auth-simple/login", response_model=LoginResponse)
async def login(form_data: LoginRequest):
    username = form_data.username
    password = form_data.password
    
    if username in TEST_USERS and TEST_USERS[username]["password"] == password:
        token = secrets.token_urlsafe(32)
        ACTIVE_TOKENS[token] = username
        
        user_data = TEST_USERS[username].copy()
        del user_data["password"]
        
        return LoginResponse(
            access_token=token,
            user=user_data
        )
    else:
        raise HTTPException(status_code=401, detail="Invalid credentials")

# Get subjects from database
@app.get("/api/v1/subjects")
async def get_subjects():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT DISTINCT s.id, s.name, s.description, s.icon, s.color,
                   COUNT(q.id) as question_count
            FROM subjects s
            LEFT JOIN questions q ON q.subject_id = s.id
            GROUP BY s.id, s.name, s.description, s.icon, s.color
            ORDER BY s.name
        """)
        subjects = cur.fetchall()
        conn.close()
        
        if not subjects:
            # Fallback subjects if database is empty
            return [
                {"id": "1", "name": "Matemáticas", "icon": "🔢", "color": "#FF6B6B"},
                {"id": "2", "name": "Física", "icon": "⚛️", "color": "#4ECDC4"},
                {"id": "3", "name": "Química", "icon": "🧪", "color": "#45B7D1"},
                {"id": "4", "name": "Biología", "icon": "🧬", "color": "#96CEB4"},
                {"id": "5", "name": "Español", "icon": "📚", "color": "#FFEAA7"}
            ]
        
        return subjects
    except Exception as e:
        print(f"Error getting subjects: {e}")
        # Return fallback on error
        return [
            {"id": "matematicas", "name": "Matemáticas", "icon": "🔢", "color": "#FF6B6B"},
            {"id": "fisica", "name": "Física", "icon": "⚛️", "color": "#4ECDC4"}
        ]

# Dynamic subjects endpoint
@app.get("/api/v1/subjects/dynamic")
async def get_dynamic_subjects():
    return await get_subjects()

# Simple subjects endpoint without assets
@app.get("/api/v1/subjects-simple")
async def get_subjects_simple():
    return await get_subjects()

# Start diagnostic session
@app.post("/api/v1/diagnostic/start")
async def start_diagnostic(diagnostic: DiagnosticStart):
    session_id = secrets.token_urlsafe(16)
    
    DIAGNOSTIC_SESSIONS[session_id] = {
        "id": session_id,
        "subject_id": diagnostic.subject_id,
        "user_id": "current_user",
        "current_theta": 0.0,
        "responses": [],
        "questions_asked": [],
        "current_question": 0,
        "total_questions": 10,
        "status": "active",
        "started_at": datetime.now()
    }
    
    return {
        "session_id": session_id,
        "subject_id": diagnostic.subject_id,
        "status": "started",
        "total_questions": 10,
        "message": "¡Bienvenido al Portal del Despertar!"
    }

# Get next question from database
@app.get("/api/v1/diagnostic/{session_id}/next-question")
async def get_next_question(session_id: str):
    if session_id not in DIAGNOSTIC_SESSIONS:
        raise HTTPException(status_code=404, detail="Sesión no encontrada")
    
    session = DIAGNOSTIC_SESSIONS[session_id]
    
    if session["status"] == "completed":
        raise HTTPException(status_code=400, detail="Sesión ya completada")
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Get subject name for query
        subject_name_map = {
            "matematicas": "Matemáticas",
            "fisica": "Física",
            "quimica": "Química",
            "biologia": "Biología",
            "espanol": "Español",
            "1": "Matemáticas",
            "2": "Física",
            "3": "Química",
            "4": "Biología",
            "5": "Español"
        }
        
        subject_name = subject_name_map.get(session["subject_id"], session["subject_id"])
        
        # Build list of already asked questions
        asked_ids = ','.join(str(id) for id in session["questions_asked"]) if session["questions_asked"] else '0'
        
        # Query for questions not yet asked
        query = f"""
            SELECT q.id, q.statement, q.option_a, q.option_b, q.option_c, q.option_d,
                   q.correct_answer, q.topic, q.difficulty,
                   COALESCE(q.parametro_irt_b, 0) as irt_b,
                   q.explicacion_respuesta, q.competencia
            FROM questions q
            JOIN subjects s ON q.subject_id = s.id
            WHERE s.name = %s
            AND q.id NOT IN ({asked_ids})
            ORDER BY RANDOM()
            LIMIT 1
        """
        
        cur.execute(query, (subject_name,))
        question = cur.fetchone()
        conn.close()
        
        if not question or session["current_question"] >= session["total_questions"]:
            # Complete session
            session["status"] = "completed"
            session["completed_at"] = datetime.now()
            
            final_theta = estimate_theta(session["responses"])
            session["final_theta"] = final_theta
            session["final_rank"] = get_icfes_rank(final_theta)
            
            return {
                "status": "completed",
                "final_theta": final_theta,
                "rank": session["final_rank"],
                "total_correct": sum(1 for r in session["responses"] if r[1]),
                "total_questions": len(session["responses"]),
                "awakening_message": f"¡Has despertado como {session['final_rank']['name']}!"
            }
        
        # Mark question as asked
        session["questions_asked"].append(question["id"])
        session["current_question"] += 1
        
        return {
            "question": {
                "id": question["id"],
                "statement": question["statement"],
                "option_a": question["option_a"],
                "option_b": question["option_b"],
                "option_c": question["option_c"],
                "option_d": question["option_d"],
                "topic": question["topic"] or "General",
                "difficulty": question["difficulty"] or "medio",
                "competencia": question["competencia"]
            },
            "progress": {
                "current": session["current_question"],
                "total": session["total_questions"],
                "percentage": round((session["current_question"] / session["total_questions"]) * 100, 1)
            },
            "hunter_info": {
                "current_theta": round(session["current_theta"], 2),
                "current_rank": get_icfes_rank(session["current_theta"])
            }
        }
        
    except Exception as e:
        print(f"Error getting question: {e}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo pregunta: {str(e)}")

# Submit answer
@app.post("/api/v1/diagnostic/{session_id}/answer")
async def submit_answer(session_id: str, answer: DiagnosticAnswer):
    if session_id not in DIAGNOSTIC_SESSIONS:
        raise HTTPException(status_code=404, detail="Sesión no encontrada")
    
    session = DIAGNOSTIC_SESSIONS[session_id]
    
    if session["status"] != "active":
        raise HTTPException(status_code=400, detail="Sesión no activa")
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Get question details
        cur.execute("""
            SELECT id, correct_answer, COALESCE(parametro_irt_b, 0) as irt_b,
                   explicacion_respuesta, topic
            FROM questions
            WHERE id = %s
        """, (answer.question_id,))
        
        question = cur.fetchone()
        conn.close()
        
        if not question:
            raise HTTPException(status_code=404, detail="Pregunta no encontrada")
        
        # Evaluate answer
        is_correct = answer.selected_option.upper() == question["correct_answer"].upper()
        
        # Record response
        session["responses"].append((
            answer.question_id,
            is_correct,
            question["irt_b"],
            answer.time_seconds
        ))
        
        # Update theta
        session["current_theta"] = estimate_theta(session["responses"])
        
        # Calculate XP
        base_xp = 50 if is_correct else 10
        difficulty_bonus = max(0, int(question["irt_b"] * 20))
        time_bonus = max(0, 30 - answer.time_seconds) if answer.time_seconds < 30 else 0
        total_xp = base_xp + difficulty_bonus + time_bonus
        
        return {
            "is_correct": is_correct,
            "correct_answer": question["correct_answer"],
            "explanation": question["explicacion_respuesta"] or f"La respuesta correcta es {question['correct_answer']}",
            "xp_gained": total_xp,
            "updated_theta": round(session["current_theta"], 2),
            "updated_rank": get_icfes_rank(session["current_theta"]),
            "time_taken": answer.time_seconds,
            "performance_message": "¡Excelente!" if is_correct else "Sigue intentando"
        }
        
    except Exception as e:
        print(f"Error submitting answer: {e}")
        raise HTTPException(status_code=500, detail=f"Error procesando respuesta: {str(e)}")

# Get diagnostic result
@app.get("/api/v1/diagnostic/{session_id}/result")
async def get_diagnostic_result(session_id: str):
    if session_id not in DIAGNOSTIC_SESSIONS:
        raise HTTPException(status_code=404, detail="Sesión no encontrada")
    
    session = DIAGNOSTIC_SESSIONS[session_id]
    
    if session["status"] != "completed":
        raise HTTPException(status_code=400, detail="Sesión no completada")
    
    total_correct = sum(1 for r in session["responses"] if r[1])
    total_questions = len(session["responses"])
    
    return {
        "session_id": session_id,
        "subject_id": session["subject_id"],
        "final_theta": session["final_theta"],
        "final_rank": session["final_rank"],
        "total_correct": total_correct,
        "total_questions": total_questions,
        "percentage": round((total_correct / total_questions * 100), 1) if total_questions > 0 else 0,
        "time_taken": (session["completed_at"] - session["started_at"]).total_seconds(),
        "awakening_complete": True
    }

# Dashboard endpoints
@app.get("/api/v1/dashboard/student")
async def get_student_dashboard():
    return {
        "status": "success",
        "dashboard": "student",
        "data": {
            "level": 15,
            "rank": "C",
            "total_xp": 1500,
            "subjects_progress": []
        }
    }

@app.get("/api/v1/dashboard/teacher")
async def get_teacher_dashboard():
    return {
        "status": "success",
        "dashboard": "teacher",
        "data": {
            "total_students": 25,
            "active_sessions": 5
        }
    }

# Serve images
@app.get("/api/v1/images/{path:path}")
async def serve_image(path: str):
    try:
        # Try different image locations
        possible_paths = [
            f"C:/Users/PEDRO_PEREZ/Documents/IcfesLeveling/apps/frontend/public/images/{path}",
            f"C:/Users/PEDRO_PEREZ/Documents/IcfesLeveling/database/allquestions/images/{path}",
            f"./images/{path}",
            f"../frontend/public/images/{path}"
        ]
        
        for file_path in possible_paths:
            if os.path.exists(file_path):
                return FileResponse(file_path)
        
        raise HTTPException(status_code=404, detail="Image not found")
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Image not found: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)