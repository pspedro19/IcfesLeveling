#!/usr/bin/env python3
"""
Minimal startup script for ICFES backend
Runs a basic version of the API with core endpoints only
"""

import os
import sys
import uvicorn
from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
import secrets
import random
import math
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor

# Create minimal FastAPI app
app = FastAPI(
    title="ICFES LEVELING API (Minimal)",
    description="Minimal backend for ICFES Leveling",
    version="0.1.0"
)

# Configure CORS
ALLOWED_ORIGINS = [
    "*"  # Allow all origins for development testing
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Test users database (in-memory)
TEST_USERS = {
    "admin": {
        "username": "admin",
        "password": "secret",
        "display_name": "Admin User",
        "level": 50,
        "rank": "S",
        "role": "admin",
        "is_admin": True,
        "experience": 50000,
        "orbs": 10000,
        "crystals": 5000
    },
    "test": {
        "username": "test",
        "password": "secret", 
        "display_name": "Test User",
        "level": 1,
        "rank": "E",
        "role": "user",
        "is_admin": False,
        "experience": 0,
        "orbs": 100,
        "crystals": 10
    },
    "student1": {
        "username": "student1",
        "password": "secret",
        "display_name": "Student One",
        "level": 15,
        "rank": "C",
        "role": "user",
        "is_admin": False,
        "experience": 1500,
        "orbs": 500,
        "crystals": 50
    }
}

# Store active tokens (in-memory)
ACTIVE_TOKENS = {}

# Store diagnostic sessions (in-memory)
DIAGNOSTIC_SESSIONS = {}

# Store user progress (in-memory)
USER_PROGRESS = {}

# Banco de preguntas simuladas para MVP (basado en patrón ICFES real)
SAMPLE_QUESTIONS = {
    "matematicas": [
        {
            "id": 1, "statement": "Si un rectángulo tiene una longitud de 12 metros y un ancho de 8 metros, ¿cuál es su área?",
            "option_a": "96 metros cuadrados", "option_b": "20 metros cuadrados", "option_c": "40 metros cuadrados", "option_d": "32 metros cuadrados",
            "correct_answer": "A", "subject_id": "matematicas", "topic": "Geometría", "difficulty": "facil", "irt_b": -1.5
        },
        {
            "id": 2, "statement": "Resuelva la ecuación: 3x + 7 = 22",
            "option_a": "x = 3", "option_b": "x = 5", "option_c": "x = 7", "option_d": "x = 15",
            "correct_answer": "B", "subject_id": "matematicas", "topic": "Álgebra", "difficulty": "medio", "irt_b": 0.0
        },
        {
            "id": 3, "statement": "¿Cuál es la derivada de f(x) = x³ + 2x² - 5x + 1?",
            "option_a": "3x² + 4x - 5", "option_b": "x³ + 2x² - 5", "option_c": "3x² + 4x + 1", "option_d": "2x² + 4x - 5",
            "correct_answer": "A", "subject_id": "matematicas", "topic": "Cálculo", "difficulty": "dificil", "irt_b": 1.8
        },
    ],
    "fisica": [
        {
            "id": 11, "statement": "Un objeto cae libremente desde una altura de 20 metros. ¿Cuánto tiempo tarda en llegar al suelo? (g = 10 m/s²)",
            "option_a": "1 segundo", "option_b": "2 segundos", "option_c": "3 segundos", "option_d": "4 segundos",
            "correct_answer": "B", "subject_id": "fisica", "topic": "Cinemática", "difficulty": "medio", "irt_b": -0.5
        },
        {
            "id": 12, "statement": "¿Qué ley establece que 'toda acción genera una reacción de igual magnitud pero en sentido contrario'?",
            "option_a": "Primera ley de Newton", "option_b": "Segunda ley de Newton", "option_c": "Tercera ley de Newton", "option_d": "Ley de gravitación universal",
            "correct_answer": "C", "subject_id": "fisica", "topic": "Dinámica", "difficulty": "facil", "irt_b": -1.0
        },
    ],
    "quimica": [
        {
            "id": 21, "statement": "¿Cuál es la fórmula química del agua?",
            "option_a": "H2O", "option_b": "CO2", "option_c": "NaCl", "option_d": "CH4",
            "correct_answer": "A", "subject_id": "quimica", "topic": "Química General", "difficulty": "facil", "irt_b": -2.0
        },
        {
            "id": 22, "statement": "En una reacción de combustión completa del metano (CH4), ¿cuáles son los productos?",
            "option_a": "CO + H2", "option_b": "CO2 + H2O", "option_c": "C + H2O", "option_d": "CH3OH + O2",
            "correct_answer": "B", "subject_id": "quimica", "topic": "Reacciones Químicas", "difficulty": "medio", "irt_b": 0.3
        },
    ],
    "biologia": [
        {
            "id": 31, "statement": "¿Cuál es la función principal de los ribosomas en la célula?",
            "option_a": "Producir energía", "option_b": "Sintetizar proteínas", "option_c": "Almacenar información genética", "option_d": "Digerir sustancias",
            "correct_answer": "B", "subject_id": "biologia", "topic": "Biología Celular", "difficulty": "medio", "irt_b": 0.2
        },
    ],
    "espanol": [
        {
            "id": 41, "statement": "¿Cuál es la función del sujeto en una oración?",
            "option_a": "Indica la acción", "option_b": "Modifica al verbo", "option_c": "Realiza o padece la acción", "option_d": "Complementa el predicado",
            "correct_answer": "C", "subject_id": "espanol", "topic": "Gramática", "difficulty": "facil", "irt_b": -1.2
        },
        {
            "id": 42, "statement": "En el texto: 'El viento susurraba entre las hojas', la figura retórica empleada es:",
            "option_a": "Metáfora", "option_b": "Personificación", "option_c": "Hipérbole", "option_d": "Comparación",
            "correct_answer": "B", "subject_id": "espanol", "topic": "Literatura", "difficulty": "medio", "irt_b": 0.5
        },
    ]
}

# Función IRT básica para calcular probabilidad de respuesta correcta
def irt_probability(theta, b, a=1.0, c=0.1):
    """
    Calcula P(correct) usando modelo IRT 3PL simplificado
    theta: habilidad del estudiante (-4 a 4)
    b: dificultad del ítem (-3 a 3)
    a: discriminación (fijo en 1.0 para simplicidad)
    c: adivinanza (0.1 por defecto)
    """
    return c + (1 - c) / (1 + math.exp(-a * (theta - b)))

# Database connection helper
def get_db_connection():
    try:
        return psycopg2.connect(
            host="localhost",
            port=5433,
            database="gameplay_db",
            user="gameplay",
            password="gameplay123",
            cursor_factory=RealDictCursor
        )
    except Exception as e:
        print(f"Database connection failed: {e}")
        return None

# Function to get questions from database
def get_questions_from_db(subject_id, limit=10):
    """Get questions from database for a subject"""
    try:
        conn = get_db_connection()
        if not conn:
            return []
        
        cur = conn.cursor()
        
        # Map subject IDs to names
        subject_map = {
            "matematicas": "Matemáticas",
            "fisica": "Física", 
            "quimica": "Química",
            "biologia": "Biología",
            "espanol": "Español",
            "ciencias-naturales": "Ciencias Naturales",
            "ciencias-sociales": "Ciencias Sociales",
            "ingles": "Inglés",
            "lenguaje": "Lenguaje"
        }
        
        subject_name = subject_map.get(subject_id, "Matemáticas")
        
        cur.execute("""
            SELECT q.id, q.statement, q.option_a, q.option_b, q.option_c, q.option_d,
                   q.correct_answer, q.topic, COALESCE(q.difficulty, 5) as difficulty,
                   COALESCE(q.parametro_irt_b, 0) as irt_b
            FROM questions q
            JOIN subjects s ON q.subject_id = s.id
            WHERE s.name = %s
            ORDER BY RANDOM()
            LIMIT %s
        """, (subject_name, limit))
        
        questions = cur.fetchall()
        conn.close()
        
        # Convert to expected format
        result = []
        for q in questions:
            result.append({
                "id": q["id"],
                "statement": q["statement"],
                "option_a": q["option_a"],
                "option_b": q["option_b"],
                "option_c": q["option_c"],
                "option_d": q["option_d"],
                "correct_answer": q["correct_answer"],
                "subject_id": subject_id,
                "topic": q["topic"] or "General",
                "difficulty": "medio",
                "irt_b": float(q["irt_b"])
            })
        
        return result
        
    except Exception as e:
        print(f"Error getting questions from DB: {e}")
        return []

# Función para calcular nuevo theta usando estimación simple
def estimate_theta(responses):
    """
    Estima theta basado en respuestas usando aproximación simple
    responses: lista de (is_correct, irt_b)
    """
    if not responses:
        return 0.0
    
    correct = sum(1 for r in responses if r[0])
    total = len(responses)
    
    # Estimación simple basada en porcentaje y dificultad promedio
    prop_correct = correct / total
    avg_difficulty = sum(r[1] for r in responses) / total
    
    # Conversión aproximada de proporción correcta a theta
    if prop_correct >= 0.95:
        theta = 2.5
    elif prop_correct >= 0.85:
        theta = 1.5
    elif prop_correct >= 0.75:
        theta = 1.0
    elif prop_correct >= 0.60:
        theta = 0.5
    elif prop_correct >= 0.45:
        theta = 0.0
    elif prop_correct >= 0.30:
        theta = -0.5
    elif prop_correct >= 0.15:
        theta = -1.0
    else:
        theta = -1.5
    
    # Ajustar por dificultad promedio
    theta += avg_difficulty * 0.3
    
    return max(-4.0, min(4.0, theta))

# Sistema de rangos ICFES
def get_icfes_rank(theta):
    """Convierte theta a rango ICFES estilo Solo Leveling"""
    if theta >= 2.0:
        return {"rank": "S", "name": "Monarca del Conocimiento", "color": "#FFD700", "min_score": 401, "max_score": 500}
    elif theta >= 1.5:
        return {"rank": "A", "name": "Cazador Elite", "color": "#FF6B35", "min_score": 351, "max_score": 400}
    elif theta >= 1.0:
        return {"rank": "B", "name": "Cazador Avanzado", "color": "#4ECDC4", "min_score": 301, "max_score": 350}
    elif theta >= 0.0:
        return {"rank": "C", "name": "Cazador Competente", "color": "#45B7D1", "min_score": 251, "max_score": 300}
    elif theta >= -1.0:
        return {"rank": "D", "name": "Cazador Novato", "color": "#96CEB4", "min_score": 201, "max_score": 250}
    else:
        return {"rank": "E", "name": "Aspirante a Cazador", "color": "#FFEAA7", "min_score": 0, "max_score": 200}

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

class DiagnosticQuestion(BaseModel):
    id: int
    statement: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str
    correct_answer: str
    subject_id: str
    topic: str
    difficulty: str
    irt_b: float  # IRT difficulty parameter

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "ICFES LEVELING API (Minimal)",
        "status": "running",
        "version": "0.1.0",
        "endpoints": [
            "/api/v1/auth-simple/login",
            "/api/v1/health",
            "/api/v1/subjects",
            "/api/v1/subjects/dynamic",
            "/api/v1/diagnostic/start",
            "/api/v1/diagnostic/{session_id}/next-question",
            "/api/v1/diagnostic/{session_id}/answer",
            "/api/v1/diagnostic/{session_id}/result",
            "/api/v1/dashboard/student",
            "/api/v1/dashboard/teacher"
        ]
    }

# Health check
@app.get("/api/v1/health")
async def health_check():
    return {"status": "healthy", "service": "backend-minimal"}

# Simple login endpoint
@app.post("/api/v1/auth-simple/login", response_model=LoginResponse)
async def login(form_data: LoginRequest):
    username = form_data.username
    password = form_data.password
    
    # Check if user exists and password matches
    if username in TEST_USERS and TEST_USERS[username]["password"] == password:
        # Generate token
        token = secrets.token_urlsafe(32)
        ACTIVE_TOKENS[token] = username
        
        # Return user data
        user_data = TEST_USERS[username].copy()
        del user_data["password"]  # Don't send password back
        
        return LoginResponse(
            access_token=token,
            user=user_data
        )
    else:
        raise HTTPException(status_code=401, detail="Invalid credentials")

# Get current user
@app.get("/api/v1/auth/me")
async def get_current_user(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    token = authorization.replace("Bearer ", "")
    if token not in ACTIVE_TOKENS:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    username = ACTIVE_TOKENS[token]
    user_data = TEST_USERS[username].copy()
    del user_data["password"]
    return user_data

# Subjects endpoint
@app.get("/api/v1/subjects")
async def get_subjects():
    return [
        {"id": "1", "name": "Matemáticas", "icon": "🔢", "color": "#FF6B6B"},
        {"id": "2", "name": "Física", "icon": "⚛️", "color": "#4ECDC4"},
        {"id": "3", "name": "Química", "icon": "🧪", "color": "#45B7D1"},
        {"id": "4", "name": "Biología", "icon": "🧬", "color": "#96CEB4"},
        {"id": "5", "name": "Español", "icon": "📚", "color": "#FFEAA7"}
    ]

# Dynamic subjects endpoint for diagnostic test
@app.get("/api/v1/subjects/dynamic")
async def get_dynamic_subjects():
    return [
        {
            "id": "ciencias-naturales",
            "name": "Ciencias Naturales",
            "description": "Evaluación de competencias en ciencias naturales",
            "icon": "🔬",
            "color": "#2ECC71",
            "config": {
                "total_questions": 30,
                "time_limit_minutes": 60,
                "difficulty_levels": ["facil", "medio", "dificil"],
                "topics": ["Biología", "Química", "Física", "Medio Ambiente"]
            }
        },
        {
            "id": "ciencias-sociales",
            "name": "Ciencias Sociales",
            "description": "Evaluación de competencias en ciencias sociales",
            "icon": "🌍",
            "color": "#E67E22",
            "config": {
                "total_questions": 30,
                "time_limit_minutes": 60,
                "difficulty_levels": ["facil", "medio", "dificil"],
                "topics": ["Historia", "Geografía", "Democracia", "Economía"]
            }
        },
        {
            "id": "matematicas",
            "name": "Matemáticas",
            "description": "Evaluación de competencias matemáticas del ICFES",
            "icon": "🔢",
            "color": "#FF6B6B",
            "config": {
                "total_questions": 30,
                "time_limit_minutes": 60,
                "difficulty_levels": ["facil", "medio", "dificil"],
                "topics": ["Algebra", "Geometría", "Estadística", "Cálculo"]
            }
        },
        {
            "id": "fisica",
            "name": "Física",
            "description": "Evaluación de competencias en física",
            "icon": "⚛️",
            "color": "#4ECDC4",
            "config": {
                "total_questions": 25,
                "time_limit_minutes": 50,
                "difficulty_levels": ["facil", "medio", "dificil"],
                "topics": ["Mecánica", "Termodinámica", "Electromagnetismo", "Óptica"]
            }
        },
        {
            "id": "quimica",
            "name": "Química",
            "description": "Evaluación de competencias en química",
            "icon": "🧪",
            "color": "#45B7D1",
            "config": {
                "total_questions": 25,
                "time_limit_minutes": 50,
                "difficulty_levels": ["facil", "medio", "dificil"],
                "topics": ["Química General", "Química Orgánica", "Bioquímica"]
            }
        },
        {
            "id": "biologia",
            "name": "Biología",
            "description": "Evaluación de competencias en biología",
            "icon": "🧬",
            "color": "#96CEB4",
            "config": {
                "total_questions": 25,
                "time_limit_minutes": 50,
                "difficulty_levels": ["facil", "medio", "dificil"],
                "topics": ["Biología Celular", "Genética", "Ecología", "Evolución"]
            }
        },
        {
            "id": "espanol",
            "name": "Español",
            "description": "Evaluación de competencias en lenguaje y literatura",
            "icon": "📚",
            "color": "#FFEAA7",
            "config": {
                "total_questions": 30,
                "time_limit_minutes": 60,
                "difficulty_levels": ["facil", "medio", "dificil"],
                "topics": ["Comprensión Lectora", "Gramática", "Literatura", "Redacción"]
            }
        }
    ]

# Student dashboard endpoint
@app.get("/api/v1/dashboard/student")
async def get_student_dashboard():
    return {
        "stats": {
            "currentLevel": 15,
            "currentRank": "C",
            "experience": 1500,
            "experienceToNext": 2000,
            "totalBattles": 45,
            "winRate": 0.67,
            "currentStreak": 5,
            "mastery": {
                "mathematics": 0.75,
                "physics": 0.60,
                "chemistry": 0.65,
                "biology": 0.70,
                "spanish": 0.80
            },
            "theta": {
                "current": 0.45,
                "trend": "up",
                "history": [0.30, 0.35, 0.40, 0.42, 0.45]
            }
        },
        "recentActivity": [
            {"type": "battle", "subject": "Matemáticas", "result": "victory", "xp": 100},
            {"type": "quest", "name": "Daily Practice", "status": "completed", "xp": 50},
            {"type": "achievement", "name": "First Steps", "description": "Complete 10 battles"}
        ],
        "recommendations": [
            {
                "type": "practice",
                "subject": "Física",
                "topic": "Cinemática",
                "reason": "Identified weakness",
                "difficulty": "medium"
            },
            {
                "type": "video",
                "title": "Understanding Vectors",
                "duration": "15 min",
                "subject": "Física"
            }
        ]
    }

# Diagnostic questions endpoint - returns questions from database
@app.get("/api/v1/diagnostic-public/diagnostic-questions/{subject_id}")
async def get_diagnostic_questions(subject_id: str, limit: int = 20):
    """Get questions for diagnostic test from database"""
    # Try to get questions from database
    db_questions = get_questions_from_db(subject_id, limit)
    
    if db_questions:
        # Format questions for frontend
        formatted_questions = []
        for q in db_questions:
            formatted_questions.append({
                "id": q["id"],
                "statement": q["statement"],
                "options": [
                    {"id": "A", "text": q["option_a"]},
                    {"id": "B", "text": q["option_b"]},
                    {"id": "C", "text": q["option_c"]},
                    {"id": "D", "text": q["option_d"]}
                ],
                "correct_answer": q["correct_answer"],
                "subject_id": subject_id,
                "topic": q.get("topic", "General"),
                "difficulty": q.get("difficulty", "medio"),
                "irt_b": q.get("irt_b", 0)
            })
        return formatted_questions
    
    # Fallback to sample questions if DB fails
    sample_questions = SAMPLE_QUESTIONS.get(subject_id, [])[:limit]
    formatted_questions = []
    for q in sample_questions:
        formatted_questions.append({
            "id": q["id"],
            "statement": q["statement"],
            "options": [
                {"id": "A", "text": q["option_a"]},
                {"id": "B", "text": q["option_b"]},
                {"id": "C", "text": q["option_c"]},
                {"id": "D", "text": q["option_d"]}
            ],
            "correct_answer": q["correct_answer"],
            "subject_id": subject_id,
            "topic": q.get("topic", "General"),
            "difficulty": q.get("difficulty", "medio"),
            "irt_b": q.get("irt_b", 0)
        })
    
    if not formatted_questions:
        raise HTTPException(status_code=404, detail="No questions available for this subject")
    
    return formatted_questions

# Subject assets endpoint (dummy endpoint to avoid 404 errors)
@app.get("/api/v1/subjects/{subject_id}/assets")
async def get_subject_assets(subject_id: str):
    """Return dummy assets for subjects to avoid 404 errors"""
    return {
        "subject_id": subject_id,
        "assets": {
            "icon": "📚",
            "color": "#6B46C1",
            "image": f"/images/subjects/{subject_id}.png"
        }
    }

# Teacher dashboard endpoint
@app.get("/api/v1/dashboard/teacher")
async def get_teacher_dashboard():
    return {
        "classes": [
            {
                "id": "class-1",
                "name": "11-A Mathematics",
                "subject": "Matemáticas",
                "totalStudents": 25,
                "activeStudents": 20,
                "avgMastery": 0.72,
                "progressDelta": 0.05
            },
            {
                "id": "class-2",
                "name": "11-B Physics",
                "subject": "Física",
                "totalStudents": 28,
                "activeStudents": 22,
                "avgMastery": 0.68,
                "progressDelta": 0.03
            }
        ],
        "studentAnalytics": {
            "totalStudents": 53,
            "activeToday": 42,
            "avgTimeSpent": 45,
            "completionRate": 0.78
        },
        "weaknessAnalysis": {
            "topWeaknesses": [
                {"topic": "Trigonometría", "affectedStudents": 15, "avgScore": 0.45},
                {"topic": "Vectores", "affectedStudents": 12, "avgScore": 0.52},
                {"topic": "Derivadas", "affectedStudents": 8, "avgScore": 0.58}
            ]
        },
        "alerts": [
            {
                "type": "risk",
                "student": "Student 5",
                "message": "3 consecutive failed attempts",
                "severity": "high"
            },
            {
                "type": "achievement",
                "student": "Student 12",
                "message": "Completed all weekly goals",
                "severity": "positive"
            }
        ]
    }

# 🚀 PORTAL DEL DESPERTAR - Endpoints del diagnóstico adaptativo

@app.post("/api/v1/diagnostic/start")
async def start_diagnostic(diagnostic: DiagnosticStart):
    """Inicia una sesión de diagnóstico adaptativo para una materia"""
    session_id = secrets.token_urlsafe(16)
    
    # Inicializar sesión
    DIAGNOSTIC_SESSIONS[session_id] = {
        "id": session_id,
        "subject_id": diagnostic.subject_id,
        "user_id": "current_user",  # En MVP usamos usuario fijo
        "current_theta": 0.0,  # Empezamos con habilidad neutra
        "responses": [],  # Lista de (question_id, is_correct, irt_b, time_seconds)
        "questions_asked": [],  # IDs de preguntas ya mostradas
        "current_question": 0,
        "total_questions": 10,  # MVP: 10 preguntas por materia
        "status": "active",
        "started_at": datetime.now()
    }
    
    return {
        "session_id": session_id,
        "subject_id": diagnostic.subject_id,
        "status": "started",
        "total_questions": 10,
        "current_question": 0,
        "message": "¡Bienvenido al Portal del Despertar! Prepárate para descubrir tu potencial como Cazador del Conocimiento."
    }

@app.get("/api/v1/diagnostic/{session_id}/next-question")
async def get_next_question(session_id: str):
    """Obtiene la siguiente pregunta adaptativa"""
    if session_id not in DIAGNOSTIC_SESSIONS:
        raise HTTPException(status_code=404, detail="Sesión no encontrada")
    
    session = DIAGNOSTIC_SESSIONS[session_id]
    
    if session["status"] == "completed":
        raise HTTPException(status_code=400, detail="Sesión ya completada")
    
    # Primero intentar obtener preguntas de la base de datos
    subject_questions = get_questions_from_db(session["subject_id"], 20)
    
    # Si no hay preguntas en DB, usar las de ejemplo
    if not subject_questions:
        subject_questions = SAMPLE_QUESTIONS.get(session["subject_id"], [])
    
    if not subject_questions:
        raise HTTPException(status_code=400, detail="No hay preguntas disponibles para esta materia")
    
    # Filtrar preguntas no mostradas
    available_questions = [q for q in subject_questions if q["id"] not in session["questions_asked"]]
    
    if not available_questions or session["current_question"] >= session["total_questions"]:
        # Completar sesión
        session["status"] = "completed"
        session["completed_at"] = datetime.now()
        
        # Calcular theta final y rango
        final_theta = estimate_theta(session["responses"])
        session["final_theta"] = final_theta
        session["final_rank"] = get_icfes_rank(final_theta)
        
        return {
            "status": "completed",
            "final_theta": final_theta,
            "rank": session["final_rank"],
            "total_correct": sum(1 for r in session["responses"] if r[1]),
            "total_questions": len(session["responses"]),
            "awakening_message": f"¡Felicitaciones! Has despertado como {session['final_rank']['name']} (Rango {session['final_rank']['rank']})!"
        }
    
    # Seleccionar pregunta más apropiada para el theta actual
    current_theta = session["current_theta"]
    
    # Ordenar por proximidad al theta actual (adaptativo básico)
    def question_score(q):
        difficulty_match = abs(q["irt_b"] - current_theta)  # Menor es mejor
        return difficulty_match
    
    next_question = min(available_questions, key=question_score)
    
    # Marcar como mostrada
    session["questions_asked"].append(next_question["id"])
    session["current_question"] += 1
    
    return {
        "question": {
            "id": next_question["id"],
            "statement": next_question["statement"],
            "option_a": next_question["option_a"],
            "option_b": next_question["option_b"],
            "option_c": next_question["option_c"],
            "option_d": next_question["option_d"],
            "subject_id": next_question["subject_id"],
            "topic": next_question["topic"],
            "difficulty": next_question["difficulty"]
        },
        "progress": {
            "current": session["current_question"],
            "total": session["total_questions"],
            "percentage": round((session["current_question"] / session["total_questions"]) * 100, 1)
        },
        "hunter_info": {
            "current_theta": round(current_theta, 2),
            "current_rank": get_icfes_rank(current_theta)
        }
    }

@app.post("/api/v1/diagnostic/{session_id}/answer")
async def submit_answer(session_id: str, answer: DiagnosticAnswer):
    """Procesa una respuesta y actualiza el theta del estudiante"""
    if session_id not in DIAGNOSTIC_SESSIONS:
        raise HTTPException(status_code=404, detail="Sesión no encontrada")
    
    session = DIAGNOSTIC_SESSIONS[session_id]
    
    if session["status"] != "active":
        raise HTTPException(status_code=400, detail="Sesión no activa")
    
    # Buscar la pregunta en el banco
    question = None
    for subject_questions in SAMPLE_QUESTIONS.values():
        for q in subject_questions:
            if q["id"] == answer.question_id:
                question = q
                break
        if question:
            break
    
    if not question:
        raise HTTPException(status_code=404, detail="Pregunta no encontrada")
    
    # Evaluar respuesta
    is_correct = answer.selected_option.upper() == question["correct_answer"]
    
    # Registrar respuesta
    session["responses"].append((
        answer.question_id,
        is_correct,
        question["irt_b"],
        answer.time_seconds
    ))
    
    # Actualizar theta
    session["current_theta"] = estimate_theta(session["responses"])
    
    # Calcular XP y recompensas
    base_xp = 50 if is_correct else 10
    difficulty_bonus = max(0, int(question["irt_b"] * 20))  # Bonus por dificultad
    time_bonus = max(0, 30 - answer.time_seconds) if answer.time_seconds < 30 else 0
    total_xp = base_xp + difficulty_bonus + time_bonus
    
    return {
        "is_correct": is_correct,
        "correct_answer": question["correct_answer"],
        "explanation": f"Respuesta correcta: {question['correct_answer']}. Tema: {question['topic']}",
        "xp_gained": total_xp,
        "updated_theta": round(session["current_theta"], 2),
        "updated_rank": get_icfes_rank(session["current_theta"]),
        "time_taken": answer.time_seconds,
        "performance_message": "¡Excelente!" if is_correct and answer.time_seconds < 20 else "¡Bien hecho!" if is_correct else "No te rindas, sigue entrenando"
    }

@app.get("/api/v1/diagnostic/{session_id}/result")
async def get_diagnostic_result(session_id: str):
    """Obtiene el resultado final del diagnóstico"""
    if session_id not in DIAGNOSTIC_SESSIONS:
        raise HTTPException(status_code=404, detail="Sesión no encontrada")
    
    session = DIAGNOSTIC_SESSIONS[session_id]
    
    if session["status"] != "completed":
        raise HTTPException(status_code=400, detail="Sesión no completada")
    
    # Análisis de fortalezas y debilidades
    topics_performance = {}
    for question_id, is_correct, irt_b, time_sec in session["responses"]:
        # Encontrar la pregunta para obtener el tema
        question = None
        for subject_questions in SAMPLE_QUESTIONS.values():
            for q in subject_questions:
                if q["id"] == question_id:
                    question = q
                    break
            if question:
                break
        
        if question:
            topic = question["topic"]
            if topic not in topics_performance:
                topics_performance[topic] = {"correct": 0, "total": 0}
            topics_performance[topic]["total"] += 1
            if is_correct:
                topics_performance[topic]["correct"] += 1
    
    # Identificar fortalezas y debilidades
    strengths = []
    weaknesses = []
    for topic, perf in topics_performance.items():
        percentage = (perf["correct"] / perf["total"]) * 100
        if percentage >= 70:
            strengths.append({"topic": topic, "percentage": percentage})
        elif percentage < 50:
            weaknesses.append({"topic": topic, "percentage": percentage})
    
    total_correct = sum(1 for r in session["responses"] if r[1])
    accuracy = (total_correct / len(session["responses"])) * 100
    
    # Proyección de puntaje ICFES
    estimated_score = int(session["final_rank"]["min_score"] + 
                         (session["final_rank"]["max_score"] - session["final_rank"]["min_score"]) * 
                         (session["final_theta"] + 4) / 8)  # Normalizar theta [-4,4] a [0,1]
    
    return {
        "session_id": session_id,
        "subject_id": session["subject_id"],
        "final_theta": session["final_theta"],
        "final_rank": session["final_rank"],
        "total_questions": len(session["responses"]),
        "total_correct": total_correct,
        "accuracy_percentage": round(accuracy, 1),
        "estimated_icfes_score": estimated_score,
        "strengths": sorted(strengths, key=lambda x: x["percentage"], reverse=True),
        "weaknesses": sorted(weaknesses, key=lambda x: x["percentage"]),
        "topics_performance": topics_performance,
        "awakening_message": f"¡Has despertado como {session['final_rank']['name']}!",
        "next_steps": {
            "unlock_biblioteca": True,
            "recommended_practice": weaknesses[:3] if weaknesses else ["Continúa practicando para mantener tu nivel"],
            "arena_unlock": accuracy >= 60
        }
    }

# Run the server
if __name__ == "__main__":
    print("\n" + "="*60)
    print("ICFES LEVELING MINIMAL BACKEND")
    print("="*60)
    print(f"Starting server on http://0.0.0.0:8000")
    print(f"CORS enabled for frontend on port 3000")
    print(f"API docs available at http://localhost:8000/docs")
    print("\nTest Accounts:")
    print("  - admin/secret (Admin, Level 50)")
    print("  - test/secret (New User, Level 1)")
    print("  - student1/secret (Student, Level 15)")
    print("\nKey Endpoints:")
    print("  - POST /api/v1/auth-simple/login")
    print("  - GET /api/v1/dashboard/student")
    print("  - GET /api/v1/dashboard/teacher")
    print("  - GET /api/v1/subjects")
    print("="*60 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)