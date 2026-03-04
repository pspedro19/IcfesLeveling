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

class YMLPlanRequest(BaseModel):
    user_id: str
    subject: str
    test_results: Dict[str, Any]  # Resultados del test diagnóstico
    weak_topics: list
    strong_topics: list

class YMLPlanResponse(BaseModel):
    plan_id: str
    subject: str
    units: list
    total_units: int
    estimated_duration: str
    difficulty_level: str

class PersonalityTestRequest(BaseModel):
    user_id: str
    answers: Dict[str, str]  # Respuestas del test

class PersonalityTestResponse(BaseModel):
    hero_class: str
    description: str
    avatar_url: str
    stats_boost: Dict[str, int]
    special_ability: str
    element: str
    cutscene_data: Dict[str, Any]

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
            except Exception:
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
            except Exception:
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

class YMLGenerator(AIService):
    def __init__(self):
        super().__init__()
        self.max_units = 8
        self.subjects = ['matematicas', 'lenguaje', 'ciencias', 'sociales', 'ingles']
    
    async def generate_yml_plan(self, request: YMLPlanRequest) -> YMLPlanResponse:
        """Generate YML study plan based on test results"""
        cache_key = self.generate_cache_key(f"yml_plan:{request.user_id}:{request.subject}")
        
        # Check cache first
        cached = await self.get_cached_response(cache_key)
        if cached:
            logger.info("Using cached YML plan")
            return YMLPlanResponse(**cached)
        
        if not self.openai_client:
            # Mock YML plan for development
            mock_units = [
                {
                    "unit_number": 1,
                    "unit_name": "Fundamentos Básicos",
                    "unit_description": "Conceptos fundamentales del tema",
                    "content": {
                        "videos": ["video1.mp4", "video2.mp4"],
                        "exercises": ["ejercicio1", "ejercicio2"],
                        "resources": ["pdf1.pdf", "pdf2.pdf"]
                    }
                }
            ] * min(8, len(request.weak_topics) + 2)
            
            mock_response = {
                "plan_id": f"plan_{request.user_id}_{request.subject}",
                "subject": request.subject,
                "units": mock_units,
                "total_units": len(mock_units),
                "estimated_duration": "4 semanas",
                "difficulty_level": "intermedio"
            }
            await self.cache_response(cache_key, mock_response)
            return YMLPlanResponse(**mock_response)
        
        try:
            prompt = f"""
            Genera un plan de estudio YML para {request.subject} basado en:
            
            Temas débiles: {', '.join(request.weak_topics)}
            Temas fuertes: {', '.join(request.strong_topics)}
            Resultados del test: {request.test_results}
            
            Crea exactamente 8 unidades máximo con:
            1. Nombre de unidad
            2. Descripción clara
            3. Contenido: videos, ejercicios, recursos
            4. Dificultad progresiva
            5. Enfoque en temas débiles
            
            Responde en formato JSON:
            {{
                "plan_id": "plan_id",
                "subject": "{request.subject}",
                "units": [
                    {{
                        "unit_number": 1,
                        "unit_name": "Nombre Unidad",
                        "unit_description": "Descripción",
                        "content": {{
                            "videos": ["video1.mp4"],
                            "exercises": ["ejercicio1"],
                            "resources": ["recurso1.pdf"]
                        }}
                    }}
                ],
                "total_units": 8,
                "estimated_duration": "4 semanas",
                "difficulty_level": "intermedio"
            }}
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000,
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
            except Exception:
                # Fallback
                ai_response = {
                    "plan_id": f"plan_{request.user_id}_{request.subject}",
                    "subject": request.subject,
                    "units": [
                        {
                            "unit_number": i,
                            "unit_name": f"Unidad {i}",
                            "unit_description": f"Descripción de unidad {i}",
                            "content": {
                                "videos": [f"video{i}.mp4"],
                                "exercises": [f"ejercicio{i}"],
                                "resources": [f"recurso{i}.pdf"]
                            }
                        } for i in range(1, 9)
                    ],
                    "total_units": 8,
                    "estimated_duration": "4 semanas",
                    "difficulty_level": "intermedio"
                }
            
            await self.cache_response(cache_key, ai_response)
            return YMLPlanResponse(**ai_response)
            
        except Exception as e:
            logger.error("OpenAI API error in YML generation", error=str(e))
            fallback = {
                "plan_id": f"plan_{request.user_id}_{request.subject}",
                "subject": request.subject,
                "units": [
                    {
                        "unit_number": i,
                        "unit_name": f"Unidad {i}",
                        "unit_description": f"Descripción de unidad {i}",
                        "content": {
                            "videos": [f"video{i}.mp4"],
                            "exercises": [f"ejercicio{i}"],
                            "resources": [f"recurso{i}.pdf"]
                        }
                    } for i in range(1, 9)
                ],
                "total_units": 8,
                "estimated_duration": "4 semanas",
                "difficulty_level": "intermedio"
            }
            return YMLPlanResponse(**fallback)

    async def analyze_personality(self, answers: Dict[str, str]) -> PersonalityTestResponse:
        """Analyze personality answers and assign hero class"""
        try:
            # Mapeo de respuestas a clases épicas
            class_weights = {
                "warrior": 0,
                "mage": 0,
                "archer": 0,
                "priest": 0,
                "assassin": 0
            }
            
            # Calcular pesos basado en respuestas
            for question_type, answer in answers.items():
                if question_type == "motivation":
                    if answer == "A": class_weights["warrior"] += 3; class_weights["mage"] += 2
                    elif answer == "B": class_weights["priest"] += 4
                    elif answer == "C": class_weights["warrior"] += 4; class_weights["archer"] += 3
                    elif answer == "D": class_weights["mage"] += 4; class_weights["assassin"] += 3
                    elif answer == "E": class_weights["assassin"] += 4; class_weights["mage"] += 3
                
                elif question_type == "learning_style":
                    if answer == "A": class_weights["archer"] += 4; class_weights["warrior"] += 3
                    elif answer == "B": class_weights["priest"] += 4
                    elif answer == "C": class_weights["warrior"] += 4; class_weights["archer"] += 3
                    elif answer == "D": class_weights["mage"] += 4; class_weights["assassin"] += 3
                    elif answer == "E": class_weights["assassin"] += 4; class_weights["mage"] += 3
                
                elif question_type == "subject_preference":
                    if answer == "A": class_weights["mage"] += 4; class_weights["archer"] += 3
                    elif answer == "B": class_weights["priest"] += 4
                    elif answer == "C": class_weights["archer"] += 4; class_weights["warrior"] += 3
                    elif answer == "D": class_weights["priest"] += 3
                    elif answer == "E": class_weights["assassin"] += 4
                
                elif question_type == "problem_solving":
                    if answer == "A": class_weights["warrior"] += 4
                    elif answer == "B": class_weights["priest"] += 4
                    elif answer == "C": class_weights["archer"] += 4; class_weights["mage"] += 3
                    elif answer == "D": class_weights["mage"] += 4; class_weights["assassin"] += 3
                    elif answer == "E": class_weights["assassin"] += 4
                
                elif question_type == "social_preference":
                    if answer == "A": class_weights["mage"] += 3; class_weights["assassin"] += 4
                    elif answer == "B": class_weights["priest"] += 4
                    elif answer == "C": class_weights["warrior"] += 4; class_weights["archer"] += 3
                    elif answer == "D": class_weights["mage"] += 4; class_weights["assassin"] += 3
                    elif answer == "E": class_weights["assassin"] += 4
            
            # Determinar clase con mayor peso
            max_weight = max(class_weights.values())
            assigned_class = [k for k, v in class_weights.items() if v == max_weight][0]
            
            # Mapear a datos de clase épica
            hero_classes = {
                "warrior": {
                    "hero_class": "Guerrero del Conocimiento",
                    "description": "Tu fuerza física se convierte en poder mental. Eres resistente y perseverante en el aprendizaje.",
                    "avatar_url": "/avatars/warrior-knowledge.png",
                    "stats_boost": {"power": 25, "hp": 30, "resistance": 15},
                    "special_ability": "Resistencia Mental: +30% HP en batallas largas",
                    "element": "Tierra",
                    "cutscene_data": {
                        "title": "¡Guerrero del Conocimiento!",
                        "subtitle": "Tu fuerza mental es legendaria",
                        "animation": "warrior_awakening",
                        "particles": ["earth", "strength"],
                        "sound_effect": "warrior_roar"
                    }
                },
                "mage": {
                    "hero_class": "Mago Cuántico",
                    "description": "Dominas las matemáticas con precisión mágica. Tu mente analítica te permite resolver problemas complejos.",
                    "avatar_url": "/avatars/mage-quantum.png",
                    "stats_boost": {"wisdom": 25, "mp": 30, "math_power": 20},
                    "special_ability": "Explicación Mágica: +50% precisión en matemáticas",
                    "element": "Fuego",
                    "cutscene_data": {
                        "title": "¡Mago Cuántico!",
                        "subtitle": "Las matemáticas son tu magia",
                        "animation": "mage_spellcasting",
                        "particles": ["fire", "magic"],
                        "sound_effect": "spell_cast"
                    }
                },
                "archer": {
                    "hero_class": "Arquero de la Sabiduría",
                    "description": "Velocidad y precisión en cada respuesta. Tu agilidad mental te permite responder rápidamente.",
                    "avatar_url": "/avatars/archer-wisdom.png",
                    "stats_boost": {"speed": 25, "agility": 20, "accuracy": 15},
                    "special_ability": "Tiro Crítico: +40% probabilidad de respuestas críticas",
                    "element": "Viento",
                    "cutscene_data": {
                        "title": "¡Arquero de la Sabiduría!",
                        "subtitle": "Tu precisión es mortal",
                        "animation": "archer_aiming",
                        "particles": ["wind", "speed"],
                        "sound_effect": "bow_release"
                    }
                },
                "priest": {
                    "hero_class": "Sacerdote del Aprendizaje",
                    "description": "Sanas las dudas con conocimiento sagrado. Tu sabiduría te permite explicar conceptos complejos.",
                    "avatar_url": "/avatars/priest-learning.png",
                    "stats_boost": {"wisdom": 30, "mp": 25, "healing": 20},
                    "special_ability": "Curación Mental: Recupera HP al explicar conceptos",
                    "element": "Luz",
                    "cutscene_data": {
                        "title": "¡Sacerdote del Aprendizaje!",
                        "subtitle": "Tu sabiduría sana las dudas",
                        "animation": "priest_healing",
                        "particles": ["light", "healing"],
                        "sound_effect": "healing_spell"
                    }
                },
                "assassin": {
                    "hero_class": "Asesino de la Lógica",
                    "description": "Encuentras la respuesta correcta con astucia. Tu precisión te permite identificar patrones ocultos.",
                    "avatar_url": "/avatars/assassin-logic.png",
                    "stats_boost": {"agility": 25, "speed": 20, "critical_chance": 20},
                    "special_ability": "Golpe Preciso: +60% daño crítico en respuestas correctas",
                    "element": "Sombra",
                    "cutscene_data": {
                        "title": "¡Asesino de la Lógica!",
                        "subtitle": "Tu astucia es tu arma",
                        "animation": "assassin_stealth",
                        "particles": ["shadow", "stealth"],
                        "sound_effect": "stealth_move"
                    }
                }
            }
            
            class_data = hero_classes[assigned_class]
            
            return PersonalityTestResponse(
                hero_class=class_data["hero_class"],
                description=class_data["description"],
                avatar_url=class_data["avatar_url"],
                stats_boost=class_data["stats_boost"],
                special_ability=class_data["special_ability"],
                element=class_data["element"],
                cutscene_data=class_data["cutscene_data"]
            )
            
        except Exception as e:
            logger.error(f"Error analyzing personality: {e}")
            raise HTTPException(status_code=500, detail="Error analyzing personality")

# Initialize AI service
ai_service = AIService()
yml_generator = YMLGenerator()

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

@app.post("/yml-plan", response_model=YMLPlanResponse)
async def generate_yml_plan(request: YMLPlanRequest):
    """Generate YML study plan based on test results"""
    return await yml_generator.generate_yml_plan(request)

@app.post("/personality-test", response_model=PersonalityTestResponse)
async def analyze_personality(request: PersonalityTestRequest):
    """Analyze personality and assign hero class"""
    try:
        # Lógica de IA para asignar clase basada en respuestas
        hero_class = await yml_generator.analyze_personality(request.answers)
        return hero_class
    except Exception as e:
        logger.error(f"Error analyzing personality: {e}")
        raise HTTPException(status_code=500, detail="Error analyzing personality")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002) 