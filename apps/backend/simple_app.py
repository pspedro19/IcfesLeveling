from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
import os
from datetime import datetime
from excel_loader import load_icfes_questions

# Get dynamic host configuration
HOST_IP = os.getenv('HOST_IP', '143.110.195.148')
ALLOWED_ORIGINS = os.getenv('ALLOWED_ORIGINS', f'http://localhost:4001,http://127.0.0.1:4001,http://{HOST_IP}:4001').split(',')

# Load real ICFES questions at startup
print("🔧 Cargando preguntas reales ICFES desde Excel...")
REAL_ICFES_QUESTIONS = load_icfes_questions()
print(f"✅ {sum(len(qs) for qs in REAL_ICFES_QUESTIONS.values())} preguntas ICFES cargadas exitosamente")

app = FastAPI(
    title="ICFES Leveling API",
    description="Sistema de recomendaciones educativas ICFES",
    version="1.0.0"
)

# Add CORS middleware with dynamic origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
        "timestamp": "2024-09-17T01:13:00Z"
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

# Pydantic models
class LoginRequest(BaseModel):
    email: Optional[str] = None
    username: Optional[str] = None
    password: str

class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None

# Mock users - Sincronizados con el frontend
mock_users = [
    {
        "id": 1,
        "username": "admin",
        "email": "admin@icfes.com",
        "password": "secret",
        "first_name": "Admin",
        "last_name": "Sistema",
        "is_active": True,
        "role": "admin",
        "level": 50,
        "rank": "S"
    },
    {
        "id": 2,
        "username": "test",
        "email": "test@icfes.com",
        "password": "secret",
        "first_name": "Usuario",
        "last_name": "Prueba",
        "is_active": True,
        "role": "user",
        "level": 1,
        "rank": "E"
    },
    {
        "id": 3,
        "username": "student1",
        "email": "student1@icfes.com",
        "password": "secret",
        "first_name": "Estudiante",
        "last_name": "Activo",
        "is_active": True,
        "role": "student",
        "level": 5,
        "rank": "D"
    },
    {
        "id": 4,
        "username": "estudiante",
        "email": "estudiante@icfes.com",
        "password": "123456",
        "first_name": "Estudiante",
        "last_name": "Demo",
        "is_active": True,
        "role": "student",
        "level": 1,
        "rank": "E"
    }
]

# Authentication endpoints
@app.post("/api/auth/login")
async def login(request: LoginRequest):
    try:
        print(f"DEBUG: Login request received: email='{request.email}', username='{request.username}', password='{request.password}'")
        # Find user by email or username
        user = None
        login_identifier = request.email or request.username

        if not login_identifier:
            raise HTTPException(status_code=422, detail="Either email or username is required")

        for u in mock_users:
            if (u["email"] == login_identifier or u["username"] == login_identifier) and u["password"] == request.password:
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
# Additional auth endpoints that frontend expects
@app.post("/api/v1/auth-simple/login")
async def login_v1_simple(request: Request):
    try:
        # Log raw request for debugging
        body = await request.body()
        print(f"DEBUG: Raw request body: {body}")

        content_type = request.headers.get('content-type', '')
        print(f"DEBUG: Content-Type: {content_type}")

        # Parse based on content type
        import json
        from urllib.parse import parse_qs

        if 'application/json' in content_type:
            # JSON format
            data = json.loads(body)
            print(f"DEBUG: Parsed JSON: {data}")
        else:
            # Form data format (application/x-www-form-urlencoded)
            form_data = parse_qs(body.decode('utf-8'))
            print(f"DEBUG: Parsed form data: {form_data}")
            # Convert form data to dict (parse_qs returns lists)
            data = {k: v[0] if v else None for k, v in form_data.items()}
            print(f"DEBUG: Converted form data: {data}")

        # Create LoginRequest with flexible parsing
        login_request = LoginRequest(
            email=data.get('email'),
            username=data.get('username') or data.get('email'),
            password=data.get('password')
        )

        return await login(login_request)
    except Exception as e:
        print(f"DEBUG: Error parsing request: {e}")
        raise HTTPException(status_code=422, detail=f"Invalid request format: {str(e)}")

@app.post("/api/v1/auth-simple/register")
async def register_v1_simple(request: RegisterRequest):
    return await register(request)

@app.get("/api/v1/auth-simple/me")
async def get_current_user_v1_simple(request: Request):
    return await get_current_user(request)

@app.get("/api/subjects")
async def get_subjects():
    return [
        {"id": 1, "name": "Matemáticas", "icon": "📊"},
        {"id": 2, "name": "Lectura Crítica", "icon": "📚"},
        {"id": 3, "name": "Ciencias Naturales", "icon": "🔬"},
        {"id": 4, "name": "Sociales y Ciudadanas", "icon": "🌍"},
        {"id": 5, "name": "Inglés", "icon": "🌐"}
    ]

# Additional endpoints that might be needed
@app.get("/api/v1/subjects")
async def get_subjects_v1():
    return await get_subjects()

@app.get("/api/v1/questions")
async def get_questions_v1():
    return {
        "questions": [
            {
                "id": 1,
                "text": "¿Cuál es el resultado de 2 + 2?",
                "options": ["3", "4", "5", "6"],
                "correct_answer": "4",
                "subject": "Matemáticas",
                "difficulty": 1
            }
        ]
    }

@app.get("/api/v1/profile")
async def get_profile_v1(request: Request):
    return await get_current_user(request)

@app.get("/api/v1/dashboard")
async def get_dashboard_v1():
    return {
        "stats": {
            "total_questions": 100,
            "correct_answers": 75,
            "accuracy": 75.0,
            "level": 5,
            "xp": 1250
        }
    }

# Diagnostic endpoints
@app.get("/diagnostic-public/subjects")
async def get_diagnostic_subjects():
    """Endpoint for diagnostic test subjects"""
    return [
        {
            "id": 1,
            "name": "Matemáticas",
            "icon": "📊",
            "description": "Álgebra, geometría, cálculo y estadística",
            "questions_count": 25,
            "time_limit": 90
        },
        {
            "id": 2,
            "name": "Lectura Crítica",
            "icon": "📚",
            "description": "Comprensión, interpretación y análisis de textos",
            "questions_count": 30,
            "time_limit": 80
        },
        {
            "id": 3,
            "name": "Ciencias Naturales",
            "icon": "🔬",
            "description": "Física, química y biología",
            "questions_count": 20,
            "time_limit": 70
        },
        {
            "id": 4,
            "name": "Sociales y Ciudadanas",
            "icon": "🌍",
            "description": "Historia, geografía y formación ciudadana",
            "questions_count": 20,
            "time_limit": 60
        },
        {
            "id": 5,
            "name": "Inglés",
            "icon": "🌐",
            "description": "Comprensión de lectura en inglés",
            "questions_count": 20,
            "time_limit": 50
        }
    ]

# Diagnostic questions endpoint
@app.get("/api/v1/diagnostic-public/diagnostic-questions/{subject_id}")
async def get_diagnostic_questions(subject_id: int, limit: int = 20):
    """Get diagnostic questions for a specific subject"""

    # Use real ICFES questions loaded from Excel files
    real_questions = REAL_ICFES_QUESTIONS if REAL_ICFES_QUESTIONS else {
        1: [  # Matemáticas
            {
                "id": "1",
                "question_text": "¿Cuál es el resultado de 2 + 2?",
                "pregunta_texto": "¿Cuál es el resultado de 2 + 2?",
                "type": "multiple_choice",
                "options": {
                    "A": "3",
                    "B": "4",
                    "C": "5",
                    "D": "6"
                },
                "opcion_a_texto": "3",
                "opcion_b_texto": "4",
                "opcion_c_texto": "5",
                "opcion_d_texto": "6",
                "correct_answer": "B",
                "difficulty": 1,
                "subject_id": "1",
                "topic": "Aritmética básica",
                "explicacion_respuesta": "2 + 2 = 4. Esta es una operación básica de suma.",
                "error_comun": "Confundir la suma con otras operaciones matemáticas."
            },
            {
                "id": "2",
                "question_text": "Si x + 5 = 12, ¿cuál es el valor de x?",
                "pregunta_texto": "Si x + 5 = 12, ¿cuál es el valor de x?",
                "type": "multiple_choice",
                "options": {
                    "A": "5",
                    "B": "6",
                    "C": "7",
                    "D": "8"
                },
                "opcion_a_texto": "5",
                "opcion_b_texto": "6",
                "opcion_c_texto": "7",
                "opcion_d_texto": "8",
                "correct_answer": "C",
                "difficulty": 2,
                "subject_id": "1",
                "topic": "Álgebra",
                "explicacion_respuesta": "Para resolver x + 5 = 12, restamos 5 de ambos lados: x = 12 - 5 = 7.",
                "error_comun": "Sumar 5 en lugar de restar para despejar x."
            },
            {
                "id": "3",
                "question_text": "¿Cuál es el área de un rectángulo de 5 cm de largo y 3 cm de ancho?",
                "pregunta_texto": "¿Cuál es el área de un rectángulo de 5 cm de largo y 3 cm de ancho?",
                "type": "multiple_choice",
                "options": {
                    "A": "8 cm²",
                    "B": "15 cm²",
                    "C": "16 cm²",
                    "D": "20 cm²"
                },
                "opcion_a_texto": "8 cm²",
                "opcion_b_texto": "15 cm²",
                "opcion_c_texto": "16 cm²",
                "opcion_d_texto": "20 cm²",
                "correct_answer": "B",
                "difficulty": 2,
                "subject_id": "1",
                "topic": "Geometría",
                "explicacion_respuesta": "El área de un rectángulo se calcula multiplicando largo × ancho: 5 × 3 = 15 cm².",
                "error_comun": "Confundir área con perímetro o sumar en lugar de multiplicar."
            }
        ],
        2: [  # Lectura Crítica
            {
                "id": "4",
                "question_text": "¿Cuál es la idea principal del siguiente texto?\n'El cambio climático es uno de los desafíos más grandes de nuestro tiempo.'",
                "pregunta_texto": "¿Cuál es la idea principal del siguiente texto?\n'El cambio climático es uno de los desafíos más grandes de nuestro tiempo.'",
                "type": "multiple_choice",
                "options": {
                    "A": "El clima siempre cambia",
                    "B": "El cambio climático es un desafío importante",
                    "C": "No hay solución al cambio climático",
                    "D": "El cambio climático no existe"
                },
                "opcion_a_texto": "El clima siempre cambia",
                "opcion_b_texto": "El cambio climático es un desafío importante",
                "opcion_c_texto": "No hay solución al cambio climático",
                "opcion_d_texto": "El cambio climático no existe",
                "correct_answer": "B",
                "difficulty": 2,
                "subject_id": "2",
                "topic": "Comprensión de lectura",
                "explicacion_respuesta": "El texto establece claramente que el cambio climático es 'uno de los desafíos más grandes', indicando su importancia.",
                "error_comun": "No identificar la idea principal directamente expresada en el texto."
            }
        ],
        3: [  # Ciencias Naturales
            {
                "id": "5",
                "question_text": "¿Cuál es la fórmula química del agua?",
                "pregunta_texto": "¿Cuál es la fórmula química del agua?",
                "type": "multiple_choice",
                "options": {
                    "A": "H2O",
                    "B": "CO2",
                    "C": "O2",
                    "D": "H2O2"
                },
                "opcion_a_texto": "H2O",
                "opcion_b_texto": "CO2",
                "opcion_c_texto": "O2",
                "opcion_d_texto": "H2O2",
                "correct_answer": "A",
                "difficulty": 1,
                "subject_id": "3",
                "topic": "Química básica",
                "explicacion_respuesta": "El agua está compuesta por dos átomos de hidrógeno (H) y uno de oxígeno (O), por lo que su fórmula es H2O.",
                "error_comun": "Confundir con otras fórmulas químicas comunes como CO2 o O2."
            }
        ],
        4: [  # Sociales y Ciudadanas
            {
                "id": "6",
                "question_text": "¿En qué año se independizó Colombia?",
                "pregunta_texto": "¿En qué año se independizó Colombia?",
                "type": "multiple_choice",
                "options": {
                    "A": "1810",
                    "B": "1819",
                    "C": "1820",
                    "D": "1830"
                },
                "opcion_a_texto": "1810",
                "opcion_b_texto": "1819",
                "opcion_c_texto": "1820",
                "opcion_d_texto": "1830",
                "correct_answer": "B",
                "difficulty": 2,
                "subject_id": "4",
                "topic": "Historia de Colombia",
                "explicacion_respuesta": "Colombia logró su independencia definitiva en 1819 con la Batalla de Boyacá el 7 de agosto.",
                "error_comun": "Confundir con 1810, que fue el inicio del proceso independentista."
            }
        ],
        5: [  # Inglés
            {
                "id": "7",
                "question_text": "Choose the correct form: 'She _____ to school every day.'",
                "pregunta_texto": "Choose the correct form: 'She _____ to school every day.'",
                "type": "multiple_choice",
                "options": {
                    "A": "go",
                    "B": "goes",
                    "C": "going",
                    "D": "gone"
                },
                "opcion_a_texto": "go",
                "opcion_b_texto": "goes",
                "opcion_c_texto": "going",
                "opcion_d_texto": "gone",
                "correct_answer": "B",
                "difficulty": 1,
                "subject_id": "5",
                "topic": "Present simple",
                "explicacion_respuesta": "En presente simple, la tercera persona singular (she/he/it) requiere agregar 's' al verbo: 'goes'.",
                "error_comun": "No conjugar el verbo en tercera persona singular."
            }
        ]
    }

    # Get questions for the specified subject
    questions = real_questions.get(subject_id, [])

    # Apply limit
    limited_questions = questions[:limit] if limit else questions

    # Return questions array directly for frontend compatibility
    return limited_questions

# Submit answer endpoint
@app.post("/api/v1/diagnostic-public/diagnostic-questions/submit-answer")
async def submit_answer(request: Request):
    """Submit an answer for a diagnostic question"""
    try:
        body = await request.json()
        question_id = body.get('question_id')
        user_answer = body.get('user_answer')
        response_time_ms = body.get('response_time_ms', 0)
        test_id = body.get('test_id')

        print(f"DEBUG: Answer submitted - Question ID: {question_id}, Answer: {user_answer}, Time: {response_time_ms}ms")

        # Find the question to get the correct answer
        correct_answer = None
        question_data = None

        # Search through all subjects to find the question
        real_questions_data = REAL_ICFES_QUESTIONS if REAL_ICFES_QUESTIONS else {
            1: [  # Matemáticas
                {
                    "id": "1",
                    "question_text": "¿Cuál es el resultado de 2 + 2?",
                    "correct_answer": "B",
                    "explicacion_respuesta": "2 + 2 = 4. Esta es una operación básica de suma.",
                    "error_comun": "Confundir la suma con otras operaciones matemáticas."
                },
                {
                    "id": "2",
                    "question_text": "Si x + 5 = 12, ¿cuál es el valor de x?",
                    "correct_answer": "C",
                    "explicacion_respuesta": "Para resolver x + 5 = 12, restamos 5 de ambos lados: x = 12 - 5 = 7.",
                    "error_comun": "Sumar 5 en lugar de restar para despejar x."
                },
                {
                    "id": "3",
                    "question_text": "¿Cuál es el área de un rectángulo de 5 cm de largo y 3 cm de ancho?",
                    "correct_answer": "B",
                    "explicacion_respuesta": "El área de un rectángulo se calcula multiplicando largo × ancho: 5 × 3 = 15 cm².",
                    "error_comun": "Confundir área con perímetro o sumar en lugar de multiplicar."
                }
            ],
            2: [  # Lectura Crítica
                {
                    "id": "4",
                    "question_text": "¿Cuál es la idea principal del siguiente texto?",
                    "correct_answer": "B",
                    "explicacion_respuesta": "El texto establece claramente que el cambio climático es 'uno de los desafíos más grandes', indicando su importancia.",
                    "error_comun": "No identificar la idea principal directamente expresada en el texto."
                }
            ],
            3: [  # Ciencias Naturales
                {
                    "id": "5",
                    "question_text": "¿Cuál es la fórmula química del agua?",
                    "correct_answer": "A",
                    "explicacion_respuesta": "El agua está compuesta por dos átomos de hidrógeno (H) y uno de oxígeno (O), por lo que su fórmula es H2O.",
                    "error_comun": "Confundir con otras fórmulas químicas comunes como CO2 o O2."
                }
            ],
            4: [  # Sociales y Ciudadanas
                {
                    "id": "6",
                    "question_text": "¿En qué año se independizó Colombia?",
                    "correct_answer": "B",
                    "explicacion_respuesta": "Colombia logró su independencia definitiva en 1819 con la Batalla de Boyacá el 7 de agosto.",
                    "error_comun": "Confundir con 1810, que fue el inicio del proceso independentista."
                }
            ],
            5: [  # Inglés
                {
                    "id": "7",
                    "question_text": "Choose the correct form: 'She _____ to school every day.'",
                    "correct_answer": "B",
                    "explicacion_respuesta": "En presente simple, la tercera persona singular (she/he/it) requiere agregar 's' al verbo: 'goes'.",
                    "error_comun": "No conjugar el verbo en tercera persona singular."
                }
            ]
        }

        # Find the question
        for subject_questions in real_questions_data.values():
            for q in subject_questions:
                if q["id"] == question_id:
                    question_data = q
                    correct_answer = q["correct_answer"]
                    break
            if question_data:
                break

        if not question_data:
            return {
                "success": False,
                "error": f"Question with ID {question_id} not found"
            }

        # Check if answer is correct
        is_correct = user_answer.upper() == correct_answer.upper()

        # Return feedback
        feedback = {
            "success": True,
            "is_correct": is_correct,
            "correct_answer": correct_answer,
            "user_answer": user_answer,
            "response_time_ms": response_time_ms,
            "explicacion_respuesta": question_data.get("explicacion_respuesta", ""),
            "error_comun": question_data.get("error_comun", "") if not is_correct else None
        }

        print(f"DEBUG: Feedback generated: {feedback}")
        return feedback

    except Exception as e:
        print(f"ERROR: Submit answer failed: {e}")
        return {
            "success": False,
            "error": str(e)
        }

@app.get("/docs")
async def get_documentation():
    return {
        "message": "API Documentation",
        "swagger_ui": f"http://{HOST_IP}:4000/docs",
        "redoc": f"http://{HOST_IP}:4000/redoc"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=4000)
