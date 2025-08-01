from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
import openai
import redis.asyncio as redis
import json
import hashlib
import structlog
import os
from dotenv import load_dotenv

load_dotenv()

# Configure logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

app = FastAPI(
    title="ICFES LEVELING AI Service",
    description="Servicio de IA para explicaciones y planes de estudio",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class ExplanationRequest(BaseModel):
    question_text: str
    correct_answer: str
    user_answer: str
    explanation: str
    subject: str
    topic: str

class StudyPlanRequest(BaseModel):
    user_id: str
    weak_subjects: list
    strong_subjects: list
    recent_performance: Dict[str, float]

class ExplanationResponse(BaseModel):
    explanation: str
    tips: list
    related_concepts: list
    difficulty_adjustment: Optional[str] = None

class StudyPlanResponse(BaseModel):
    plan: Dict[str, Any]
    recommendations: list
    estimated_improvement: float

class AIService:
    def __init__(self):
        self.openai_client = None
        self.redis_client = None
        self.setup_clients()
    
    def setup_clients(self):
        """Setup OpenAI and Redis clients"""
        # OpenAI setup
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            self.openai_client = openai.OpenAI(api_key=api_key)
            logger.info("OpenAI client initialized")
        else:
            logger.warning("OpenAI API key not found, using mock responses")
        
        # Redis setup
        redis_url = os.getenv("REDIS_URL", "redis://redis:6379")
        self.redis_client = redis.from_url(redis_url)
        logger.info("Redis client initialized")
    
    async def get_cached_response(self, cache_key: str) -> Optional[Dict]:
        """Get cached response from Redis"""
        try:
            cached = await self.redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
        except Exception as e:
            logger.error("Redis cache error", error=str(e))
        return None
    
    async def cache_response(self, cache_key: str, response: Dict, ttl_days: int = 30):
        """Cache response in Redis"""
        try:
            ttl_seconds = ttl_days * 24 * 60 * 60
            await self.redis_client.setex(cache_key, ttl_seconds, json.dumps(response))
        except Exception as e:
            logger.error("Redis cache error", error=str(e))
    
    def generate_cache_key(self, prompt: str) -> str:
        """Generate cache key for prompt"""
        return f"ai_cache:{hashlib.sha256(prompt.encode()).hexdigest()}"
    
    async def get_explanation(self, request: ExplanationRequest) -> ExplanationResponse:
        """Get AI explanation for wrong answer"""
        cache_key = self.generate_cache_key(
            f"explanation:{request.question_text}:{request.user_answer}:{request.correct_answer}"
        )
        
        # Check cache first
        cached = await self.get_cached_response(cache_key)
        if cached:
            logger.info("Using cached explanation")
            return ExplanationResponse(**cached)
        
        if not self.openai_client:
            # Mock response for development
            mock_response = {
                "explanation": f"La respuesta correcta es '{request.correct_answer}'. {request.explanation}",
                "tips": [
                    f"Revisa el tema de {request.topic}",
                    "Practica más ejercicios similares",
                    "Lee cuidadosamente la pregunta"
                ],
                "related_concepts": [request.topic],
                "difficulty_adjustment": "maintain"
            }
            await self.cache_response(cache_key, mock_response)
            return ExplanationResponse(**mock_response)
        
        try:
            prompt = f"""
            Eres un tutor experto en {request.subject}. El estudiante respondió incorrectamente a esta pregunta:
            
            Pregunta: {request.question_text}
            Respuesta del estudiante: {request.user_answer}
            Respuesta correcta: {request.correct_answer}
            Explicación oficial: {request.explanation}
            
            Proporciona:
            1. Una explicación clara y motivadora (máximo 3 líneas)
            2. 3 consejos prácticos para mejorar
            3. Conceptos relacionados que debe repasar
            4. Sugerencia de ajuste de dificultad (easier/maintain/harder)
            
            Responde en formato JSON:
            {{
                "explanation": "explicación aquí",
                "tips": ["consejo 1", "consejo 2", "consejo 3"],
                "related_concepts": ["concepto 1", "concepto 2"],
                "difficulty_adjustment": "easier/maintain/harder"
            }}
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300,
                temperature=0.7
            )
            
            content = response.choices[0].message.content
            # Try to parse JSON from response
            try:
                import re
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    ai_response = json.loads(json_match.group())
                else:
                    raise ValueError("No JSON found in response")
            except:
                # Fallback if JSON parsing fails
                ai_response = {
                    "explanation": content[:200] + "..." if len(content) > 200 else content,
                    "tips": ["Practica más", "Revisa el tema", "Lee con atención"],
                    "related_concepts": [request.topic],
                    "difficulty_adjustment": "maintain"
                }
            
            await self.cache_response(cache_key, ai_response)
            return ExplanationResponse(**ai_response)
            
        except Exception as e:
            logger.error("OpenAI API error", error=str(e))
            # Fallback response
            fallback = {
                "explanation": f"La respuesta correcta es '{request.correct_answer}'. {request.explanation}",
                "tips": ["Revisa el tema", "Practica más", "Lee cuidadosamente"],
                "related_concepts": [request.topic],
                "difficulty_adjustment": "maintain"
            }
            return ExplanationResponse(**fallback)
    
    async def generate_study_plan(self, request: StudyPlanRequest) -> StudyPlanResponse:
        """Generate personalized study plan"""
        cache_key = self.generate_cache_key(f"study_plan:{request.user_id}")
        
        # Check cache first
        cached = await self.get_cached_response(cache_key)
        if cached:
            logger.info("Using cached study plan")
            return StudyPlanResponse(**cached)
        
        if not self.openai_client:
            # Mock response for development
            mock_plan = {
                "plan": {
                    "daily_sessions": 3,
                    "session_duration": 30,
                    "focus_subjects": request.weak_subjects[:2],
                    "practice_subjects": request.strong_subjects[:1],
                    "weekly_goals": [
                        f"Completar 20 preguntas de {request.weak_subjects[0] if request.weak_subjects else 'Matemáticas'}",
                        "Mantener racha de 7 días",
                        "Subir 2 niveles"
                    ]
                },
                "recommendations": [
                    "Dedica más tiempo a los temas débiles",
                    "Practica con preguntas de mayor dificultad",
                    "Revisa las explicaciones cuando falles"
                ],
                "estimated_improvement": 15.5
            }
            await self.cache_response(cache_key, mock_plan)
            return StudyPlanResponse(**mock_plan)
        
        try:
            prompt = f"""
            Genera un plan de estudio personalizado para un estudiante con:
            
            Materias débiles: {', '.join(request.weak_subjects)}
            Materias fuertes: {', '.join(request.strong_subjects)}
            Rendimiento reciente: {request.recent_performance}
            
            Crea un plan que incluya:
            1. Sesiones diarias recomendadas
            2. Duración de cada sesión
            3. Enfoque en materias débiles
            4. Mantenimiento de materias fuertes
            5. Metas semanales específicas
            6. Recomendaciones personalizadas
            7. Estimación de mejora en puntos ICFES
            
            Responde en formato JSON:
            {{
                "plan": {{
                    "daily_sessions": 3,
                    "session_duration": 30,
                    "focus_subjects": ["materia1", "materia2"],
                    "practice_subjects": ["materia3"],
                    "weekly_goals": ["meta1", "meta2", "meta3"]
                }},
                "recommendations": ["rec1", "rec2", "rec3"],
                "estimated_improvement": 15.5
            }}
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
                temperature=0.7
            )
            
            content = response.choices[0].message.content
            try:
                import re
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    ai_response = json.loads(json_match.group())
                else:
                    raise ValueError("No JSON found in response")
            except:
                # Fallback
                ai_response = {
                    "plan": {
                        "daily_sessions": 3,
                        "session_duration": 30,
                        "focus_subjects": request.weak_subjects[:2],
                        "practice_subjects": request.strong_subjects[:1],
                        "weekly_goals": ["Completar 20 preguntas", "Mantener racha", "Subir niveles"]
                    },
                    "recommendations": ["Practica más", "Revisa temas débiles", "Mantén constancia"],
                    "estimated_improvement": 10.0
                }
            
            await self.cache_response(cache_key, ai_response)
            return StudyPlanResponse(**ai_response)
            
        except Exception as e:
            logger.error("OpenAI API error", error=str(e))
            fallback = {
                "plan": {
                    "daily_sessions": 2,
                    "session_duration": 25,
                    "focus_subjects": request.weak_subjects[:1],
                    "practice_subjects": [],
                    "weekly_goals": ["Practicar diariamente", "Revisar errores"]
                },
                "recommendations": ["Mantén constancia", "Revisa explicaciones"],
                "estimated_improvement": 5.0
            }
            return StudyPlanResponse(**fallback)

# Initialize AI service
ai_service = AIService()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "ai-service"}

@app.post("/explain", response_model=ExplanationResponse)
async def explain_wrong_answer(request: ExplanationRequest):
    """Get AI explanation for wrong answer"""
    try:
        explanation = await ai_service.get_explanation(request)
        return explanation
    except Exception as e:
        logger.error("Failed to get explanation", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to generate explanation")

@app.post("/study-plan", response_model=StudyPlanResponse)
async def generate_study_plan(request: StudyPlanRequest):
    """Generate personalized study plan"""
    try:
        plan = await ai_service.generate_study_plan(request)
        return plan
    except Exception as e:
        logger.error("Failed to generate study plan", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to generate study plan")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002) 