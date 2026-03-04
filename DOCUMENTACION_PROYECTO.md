# ICFES Leveling - Documentacion Tecnica Completa

> Plataforma gamificada de preparacion para el examen ICFES Saber 11 (Colombia)
> Ultima actualizacion: 2026-02-18

---

## TABLA DE CONTENIDOS

1. [Arquitectura General](#1-arquitectura-general)
2. [Stack Tecnologico](#2-stack-tecnologico)
3. [Infraestructura (Docker)](#3-infraestructura-docker)
4. [Backend - FastAPI](#4-backend---fastapi)
5. [Modelos de Datos (60+ modelos)](#5-modelos-de-datos)
6. [Sistema de Autenticacion](#6-sistema-de-autenticacion)
7. [Game Engine Service (Fuente Unica de Verdad)](#7-game-engine-service)
8. [Sistema Anti-Gaming](#8-sistema-anti-gaming)
9. [Carga de Preguntas (Seed/Excel)](#9-carga-de-preguntas)
10. [Modelo IRT 3PL (Testing Adaptativo)](#10-modelo-irt-3pl)
11. [Sistema de Diagnostico](#11-sistema-de-diagnostico)
12. [Modos de Juego](#12-modos-de-juego)
13. [Sistema de Corazones](#13-sistema-de-corazones)
14. [Sistema de Racha (Streak)](#14-sistema-de-racha)
15. [Mastery y Repeticion Espaciada](#15-mastery-y-repeticion-espaciada)
16. [Planes de Estudio](#16-planes-de-estudio)
17. [Recomendaciones de Video](#17-recomendaciones-de-video)
18. [Analisis de Debilidades](#18-analisis-de-debilidades)
19. [Ligas y Leaderboard](#19-ligas-y-leaderboard)
20. [Economia Virtual](#20-economia-virtual)
21. [AI Service (Microservicio)](#21-ai-service)
22. [App Mobile - Flutter](#22-app-mobile---flutter)
23. [Sistema Offline-First](#23-sistema-offline-first)
24. [Flujo Completo del Usuario](#24-flujo-completo-del-usuario)

---

## 1. ARQUITECTURA GENERAL

```
                    ┌─────────────────────────────────────────────┐
                    │              MONOREPO STRUCTURE              │
                    ├─────────────────────────────────────────────┤
                    │                                             │
                    │  apps/                                      │
                    │  ├── backend/       → FastAPI (Python)      │
                    │  ├── ai-service/    → FastAPI (Python)      │
                    │  ├── mobile/        → Flutter (Dart)        │
                    │  ├── frontend/      → Next.js (DEPRECATED)  │
                    │  └── websocket/     → Node.js               │
                    │                                             │
                    │  database/                                  │
                    │  ├── init/          → SQL scripts            │
                    │  ├── migrations/    → Alembic                │
                    │  └── allquestions/  → Excel seed files       │
                    │                                             │
                    │  docker-compose.yml → 7 servicios            │
                    └─────────────────────────────────────────────┘
```

### Comunicacion entre servicios:

```
  Flutter App (Mobile)
       │
       ├──── REST API ──────→ Backend (FastAPI :4000)
       │                          │
       │                          ├──→ PostgreSQL 16 (:5433)
       │                          ├──→ Redis 7 (:6379)
       │                          ├──→ ClickHouse (:8123)
       │                          └──→ AI Service (:8002)
       │
       └──── WebSocket ─────→ WebSocket Server (:4002)
```

---

## 2. STACK TECNOLOGICO

### Backend
| Tecnologia | Version | Uso |
|---|---|---|
| Python | 3.11+ | Runtime |
| FastAPI | 0.104+ | Framework REST API |
| SQLAlchemy | 2.0 | ORM |
| Alembic | - | Migraciones DB |
| Pydantic | 2.0 | Validacion/Settings |
| Celery | - | Tareas en background |
| python-jose | - | JWT tokens |
| passlib/bcrypt | - | Hashing passwords |
| NumPy/SciPy/Pandas | - | Calculos IRT y estadisticos |
| Sentry | - | Error tracking |

### Base de Datos
| Tecnologia | Version | Uso |
|---|---|---|
| PostgreSQL | 16 | BD principal |
| Redis | 7-alpine | Cache (LRU, 256MB max) |
| ClickHouse | - | Analytics/time-series |

### Mobile
| Tecnologia | Version | Uso |
|---|---|---|
| Flutter | SDK >=3.0 | Framework mobile |
| Dart | 3.x | Lenguaje |
| Riverpod | ^2.5.0 | State management |
| Hive | ^2.2.3 | BD local offline |
| Dio | ^5.4.0 | HTTP client |
| GoRouter | ^13.0.0 | Navegacion |
| Firebase Auth | ^5.3.4 | Social login (Google/Apple) |
| Sentry Flutter | ^8.0.0 | Error tracking |
| Rive/Lottie | ^0.12/^3.0 | Animaciones |
| youtube_player_flutter | 9.0.3 | Reproductor video |

### AI Service
| Tecnologia | Uso |
|---|---|
| OpenAI GPT-3.5-turbo | Explicaciones AI + generacion planes |
| Anthropic Claude | Generacion planes de estudio |
| Redis | Cache de respuestas AI (30 dias TTL) |

### Pagos
| Tecnologia | Uso |
|---|---|
| Wompi | Gateway Colombia |
| Stripe | Gateway internacional |

---

## 3. INFRAESTRUCTURA (Docker)

**Archivo:** `docker-compose.yml` (263 lineas)

```yaml
Servicios:
  postgres:     PostgreSQL 16 - Puerto 5433:5432
  pgadmin:      pgAdmin4 - Puerto 5050:80
  redis:        Redis 7-alpine - Puerto 6379 (maxmemory 256mb, LRU)
  clickhouse:   ClickHouse - Puerto 8123
  backend:      FastAPI - Puerto 4000:8000
  websocket:    Node.js - Puerto 4002
  ai-service:   FastAPI - Puerto 8002

Red: icfes_network (bridge)
Volumenes: postgres_data, redis_data, clickhouse_data
```

**Credenciales por defecto (desarrollo):**
- PostgreSQL: `gameplay / gameplay123 / gameplay_db`
- pgAdmin: `admin@icfes.com / admin123`
- Redis: sin password

---

## 4. BACKEND - FastAPI

**Archivo principal:** `apps/backend/app/main.py` (541 lineas)

### Startup (Lifespan Manager)
Al iniciar el backend ejecuta automaticamente:

1. **Verificar estructura DB** (Alembic migrations)
2. **Importar preguntas desde Excel** (si `AUTO_IMPORT_QUESTIONS=true`)
   - Lee `QUESTIONS_EXCEL_PATH`
   - Reintentos: 3 con backoff exponencial
3. **Cargar catalogo ICFES** desde CSV
4. **Cargar YouTube links** para recomendaciones de video
5. **Iniciar Celery tasks** (daily quests, leaderboard, session cleanup)
6. **Inicializar Sentry** (error tracking)

### Organizacion de Routers (10 tiers)

```python
# TIER 1: ESSENTIAL
auth, questions, hearts, streak, mobile_api, sync, node_progress

# TIER 2: GAMIFICATION
economy, achievements, leaderboard, notifications, quests, answers, battles, practice

# TIER 3: DIAGNOSTIC
diagnostic_public, diagnostic_two_phase, monthly_reassessment, verified_image_diagnostic

# TIER 4: STUDY PLANS & RECOMMENDATIONS
personality, recommendations, claude_study_plan_generator,
integrated_study_plan_api, study_plans, quizzes, spaced_repetition

# TIER 4b: AI & INTELLIGENT
ai

# TIER 5: VIDEO & CONTENT
videos, video_recommendations, youtube_api

# TIER 6: SOCIAL & COMPETITIVE
guilds, leagues, store, boss_raid, bosses, premium_simple, dungeons

# TIER 7: AI & ASSETS
ai_tips, images_api, dynamic_subjects, subjects_with_count,
dynamic_images_api, image_required_questions, images

# TIER 8: ANALYTICS & DASHBOARD
analytics_advanced, student_dashboard, mastery, advanced_stats
```

### Configuracion (`apps/backend/app/core/config.py`)

```python
class Settings(BaseSettings):
    # Requeridos (validados)
    DATABASE_URL: str          # Obligatorio
    JWT_SECRET: str            # Obligatorio, min 32 chars

    # JWT
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Redis
    REDIS_URL: str = "redis://redis:6379"
    REDIS_MAX_CONNECTIONS: int = 100

    # Pagos (Colombia)
    WOMPI_PUBLIC_KEY, WOMPI_PRIVATE_KEY, WOMPI_EVENT_SECRET

    # App
    APP_NAME: str = "ICFES LEVELING API"
    ENVIRONMENT: str = "development"
```

---

## 5. MODELOS DE DATOS

**Archivo:** `apps/backend/app/models/__init__.py` (178 lineas)

### Catalogo completo de modelos (60+):

#### Core
| Modelo | Descripcion |
|---|---|
| `User` | Usuario con stats RPG, economia, streak, corazones, premium |
| `Subject` | 5 materias ICFES |
| `SubjectConfig` | Config dinamica por materia |
| `Topic` | Temas dentro de cada materia |
| `Question` | Preguntas con IRT, opciones, imagenes, metadata ICFES |

#### Gamificacion
| Modelo | Descripcion |
|---|---|
| `Battle`, `BattleAnswer` | Batallas PvP/PvE |
| `DungeonGate`, `DungeonRun`, `DungeonEncounter`, `DungeonMonster` | Sistema mazmorra |
| `Boss`, `BossRaidSession`, `BossRaidAnswer`, `BossRaidLeaderboard` | Raid de jefes |
| `ShadowSoldier`, `ShadowFormation`, `ShadowBattle`, `ShadowExtraction`, `ShadowAbility`, `UserShadowStats` | Ejercito sombra |
| `Item`, `UserItem` | Inventario |
| `DailyQuest`, `UserQuest` | Misiones diarias |
| `QuestTemplate`, `QuestReward` | Plantillas de quest |
| `Achievement`, `UserAchievement` | Logros |
| `Guild`, `GuildMember` | Gremios |
| `Certificate` | Certificados |

#### Aprendizaje
| Modelo | Descripcion |
|---|---|
| `PracticeSession`, `PracticeAnswer`, `UserQuestionMastery`, `PracticeReward` | Sesiones practica |
| `DiagnosticTest`, `DiagnosticTestAnswer`, `DiagnosticTestResult` | Diagnostico |
| `DiagnosticTestAnalytics`, `DiagnosticImprovementTracking`, `DiagnosticErrorPattern` | Analytics diagnostico |
| `TwoPhaseDignostic`, `TwoPhaseDiagnosticAnswer` | Diagnostico 2 fases |
| `TopicMastery`, `QuestionAttempt`, `UserEngagement` | Mastery tracking |
| `StudyPlan`, `PlanProgress` | Planes de estudio |
| `Quiz`, `QuizAnswer` | Quizzes |
| `VideoTracking` | Seguimiento videos |
| `YoutubeVideo`, `YouTubeLinks` | Videos YouTube |
| `UserYMLPlan` | Planes en formato YML |

#### Economia y Social
| Modelo | Descripcion |
|---|---|
| `Subscription`, `Payment`, `Invoice`, `PaymentMethod` | Suscripciones/pagos |
| `Coupon`, `CouponUsage` | Cupones descuento |
| `StoreTransaction`, `UserPowerUp`, `CurrencyEarning` | Tienda virtual |
| `Leaderboard` | Tabla de posiciones |
| `Notification`, `NotificationType`, `NotificationPriority` | Notificaciones |
| `GoldTransaction`, `XPTransaction` | Transacciones economia |

#### Mobile/Offline
| Modelo | Descripcion |
|---|---|
| `UserQuestionHistory` | Historial respuestas |
| `UserTopicMastery` | Mastery por tema |
| `PendingAnswerSync` | Respuestas pendientes sync |
| `HeartTransaction` | Transacciones corazones |
| `UserDailyActivity` | Actividad diaria |
| `StreakFreeze` | Congelamiento racha |
| `LeagueDivision`, `LeagueWeek`, `LeagueGroup`, `UserLeague`, `UserLeagueHistory` | Ligas |
| `DailyChallenge`, `UserDailyChallenge` | Retos diarios |
| `UserDeviceToken`, `NotificationHistory` | Push notifications |

#### Auth
| Modelo | Descripcion |
|---|---|
| `RevokedToken` | Tokens revocados |
| `RefreshToken` | Refresh tokens |

#### Misc
| Modelo | Descripcion |
|---|---|
| `UserProfile` | Perfil extendido |
| `HeroClass` | 5 clases RPG |
| `PersonalityQuestion` | Test personalidad |
| `AIExplanation` | Explicaciones AI |
| `MentorSession`, `RealMentor` | Mentores |
| `PredictiveAnalytics` | Predicciones |
| `UserKingdomProgress`, `UserNodeProgress` | Modo conquista |

### Modelo User (detalle)

**Archivo:** `apps/backend/app/models/user.py` (132 lineas)

```python
class User(Base):
    # Identificacion
    id: UUID (primary key)
    username: String(50), unique
    email: String(255), unique
    hashed_password: String(255)
    display_name: String(100)

    # Stats RPG
    level: Integer = 1
    experience: Integer = 0
    rank: String(10) = "E"        # E, D, C, B, A, S, SS, SSS
    hp: Integer = 100
    mp: Integer = 50
    power: Integer = 10
    wisdom: Integer = 10
    speed: Integer = 10

    # Economia
    gold: Integer = 1000          # Moneda principal
    orbs: Integer = 0             # Moneda secundaria
    crystals: Integer = 0         # Moneda premium

    # Racha
    current_streak: Integer = 0
    longest_streak: Integer = 0
    previous_streak: Integer = 0
    streak_lost_at: DateTime
    last_activity_date: Date
    daily_goal_xp: Integer = 20
    streak_freeze_count: Integer = 0

    # Corazones
    hearts: Integer = 5
    max_hearts: Integer = 5
    hearts_last_regeneration: DateTime
    unlimited_hearts_until: DateTime

    # Ads
    ads_watched_today: Integer = 0    # Max 3/dia para recuperar corazones
    ads_watched_date: Date

    # Onboarding
    onboarding_completed: Boolean = False
    onboarding_preferences: JSON      # goal, level, subjects, time
    projected_icfes_score: Integer     # Puntaje proyectado (0-500)

    # Premium
    premium_plan: String = "free"     # free, basic, premium, elite
    premium_expires_at: DateTime
    is_admin: Boolean = False

    # Metodo principal XP
    def add_experience(xp_amount):
        new_level = GameEngineService.calculate_level_for_xp(self.experience)
```

### Modelo Question (detalle)

**Archivo:** `apps/backend/app/models/question.py` (357 lineas)

```python
class Question(Base):
    # Identificacion
    id: UUID
    topic_id: UUID (FK topics)
    subject_id: UUID (FK subjects)

    # Contenido (sistema dual: nuevos + legacy)
    pregunta_texto: Text              # Texto de la pregunta
    pregunta_imagen: String(500)      # URL imagen
    opcion_a_texto/imagen: Text/String  # Opcion A
    opcion_b_texto/imagen: Text/String  # Opcion B
    opcion_c_texto/imagen: Text/String  # Opcion C
    opcion_d_texto/imagen: Text/String  # Opcion D
    respuesta_correcta: String(1)     # a, b, c, d

    # Legacy
    question_text, options, correct_answer, explanation, hint

    # Dificultad
    difficulty: Integer (1-10)

    # Parametros IRT
    parametro_irt_a: Float = 1.0      # Discriminacion (0.5-2.5)
    parametro_irt_b: Float = 0.0      # Dificultad (-2 a +2)
    parametro_irt_c: Float = 0.25     # Pseudo-adivinanza (0-0.25)

    # Metadata ICFES
    competencia: String(255)
    componente: String(100)
    proceso_cognitivo: String(50)
    afirmacion: Text
    evidencia: Text

    # Gamificacion
    puntos_xp: Integer = 10
    tags: ARRAY(String)
    power_stats: JSON
```

---

## 6. SISTEMA DE AUTENTICACION

**Archivo:** `apps/backend/app/core/security.py` (157 lineas)

### JWT Token System

```
Algoritmo: HS256
Access Token:  30 min expiracion
Refresh Token: 7 dias expiracion
Password Hash: bcrypt (cost 12 en produccion)
```

### Estructura del Token

```python
{
    "sub": user_id,           # Subject (UUID del usuario)
    "exp": expiration,        # Expiracion
    "jti": random_16_bytes,   # JWT ID para revocacion
    "iat": issued_at,         # Momento de emision
    "type": "access|refresh"  # Tipo de token
}
```

### Proteccion contra clock skew

En produccion, verifica que el `iat` no sea mas de 30 segundos en el futuro.

### Dependencies de FastAPI

```python
get_current_user(token)           # Requiere autenticacion
get_current_active_user(user)     # Requiere usuario activo
get_current_user_optional(token)  # Opcional (endpoints publicos/privados)
```

### Tokens revocados

Modelo `RevokedToken` almacena JTIs de tokens invalidados (logout).

---

## 7. GAME ENGINE SERVICE (Fuente Unica de Verdad)

**Archivo:** `apps/backend/app/services/game_engine_service.py` (298 lineas)

Este servicio centraliza TODA la logica de juego. Cualquier otra formula en el codebase es legacy.

### XP por Respuesta

```python
XP_NEW_QUESTION = 10        # Pregunta nueva
XP_VALID_REVIEW = 5         # Repaso valido
XP_INVALID_REPEAT = 0       # Repeticion invalida (anti-gaming)

# Solo se gana XP si:
# 1. La respuesta es correcta
# 2. No esta en grace mode
# 3. No es una repeticion invalida
```

### Multiplicadores de Racha

```python
Dias 1-6:    1.0x (sin bonus)
Dias 7-13:   1.2x
Dias 14-29:  1.5x
Dias 30+:    2.0x (maximo)

# Formula final: base_xp × streak_multiplier
```

### Calculo de Nivel

```python
# XP necesario para nivel N = (N-1)^2 × 100
# Formula inversa: nivel = floor(sqrt(XP / 100)) + 1

# Ejemplos:
# Nivel 1:  0-99 XP
# Nivel 2:  100-399 XP
# Nivel 3:  400-899 XP
# Nivel 5:  1600-2499 XP
# Nivel 10: 8100+ XP
# Nivel 50: 240100+ XP
```

### Sistema de Rangos

```python
Nivel 1-14:   Rango E
Nivel 15-29:  Rango D
Nivel 30-49:  Rango C
Nivel 50-59:  Rango B
Nivel 60-69:  Rango A
Nivel 70-79:  Rango S
Nivel 80-89:  Rango SS
Nivel 90+:    Rango SSS
```

### Calculo de Dano (Combate)

```python
base_damage = (user_power + user_wisdom) × 2

time_multiplier:
  < 3 segundos:  2.0x
  < 10 segundos: 1.5x
  < 20 segundos: 1.2x
  >= 20 segundos: 1.0x

difficulty_multiplier = 1 + (difficulty - 1) × 0.1
combo_multiplier = 1 + (combo_count × 0.1)

total_damage = base × time × difficulty × combo
# Minimo 1 de dano si es correcto, 0 si es incorrecto
```

### Ganancia de Orbs (Gold)

```python
Correcto: difficulty × 2 orbs
Correcto + Critical Hit (< 3s): difficulty × 4 orbs
Incorrecto: 1 orb
```

---

## 8. SISTEMA ANTI-GAMING

### Determinacion de Tipo de Intento

```python
def determine_attempt_type(user_id, question_id, topic_id):
    # 1. Buscar ultimo intento del usuario para esta pregunta
    last_attempt = UserQuestionHistory.filter(user_id, question_id).last()

    if no last_attempt:
        return "new"          # Primera vez → 10 XP

    # 2. Consultar mastery del tema
    mastery_score = UserTopicMastery.get(user_id, topic_id)

    # 3. Calcular dias minimos para repaso valido
    min_days = max(1, int(mastery_score × 7))
    # mastery 0.0 → 1 dia | mastery 0.5 → 3 dias | mastery 1.0 → 7 dias

    days_since = (now - last_attempt.created_at).days

    if days_since >= min_days:
        return "valid_review"   # Repaso valido → 5 XP
    else:
        return "invalid_repeat" # Repeticion → 0 XP
```

### Protecciones Adicionales

- **Tiempo minimo de respuesta**: 3 segundos (middleware anti_gaming)
- **Rate limiting**: 60 requests/minuto por usuario
- **Prevencion duplicados**: Misma pregunta en misma sesion = rechazado
- **Cap de XP por hora**: 500 XP maximo
- **Grace mode**: Usuarios sin corazones no ganan XP

---

## 9. CARGA DE PREGUNTAS

**Archivo:** `apps/backend/app/import_icfes_excel.py` (642 lineas)

### Pipeline: Excel → PostgreSQL

```
  Excel (.xlsx)
      │
      ▼
  ICFESExcelImporter
      │
      ├── 1. Leer Excel con pandas
      ├── 2. Normalizar headers (sin tildes, snake_case)
      ├── 3. Mapear materias:
      │       "Lectura Critica" → "Lenguaje"
      │       "Ciencias Naturales" → "Ciencias Naturales"
      │       "Sociales y Ciudadanas" → "Sociales"
      │       "Matematicas" → "Matematicas"
      │       "Ingles" → "Ingles"
      ├── 4. Auto-crear Subject/Topic si no existen
      ├── 5. Normalizar rutas imagenes → /mathimg/<filename>
      ├── 6. Mapear dificultad:
      │       "bajo" → 1, "medio" → 5, "alto" → 8, "muy alto" → 10
      ├── 7. Construir power_stats JSON y tags array
      ├── 8. Validar cada pregunta (contenido, opciones, respuesta)
      └── 9. Commit a PostgreSQL (batch)
```

### Activacion Automatica

```bash
# Variables de entorno en docker-compose o .env
AUTO_IMPORT_QUESTIONS=true
QUESTIONS_EXCEL_PATH=/data/preguntas_icfes.xlsx
IMPORT_CLEAR_EXISTING=false
```

Se ejecuta al iniciar el backend con 3 reintentos y backoff exponencial.

### Flujo al Mobile

```
PostgreSQL → API REST → Dio (Flutter) → Hive (cache local)
                                            │
                                            ▼
                                      Offline available
```

---

## 10. MODELO IRT 3PL

### Formula

```
P(θ) = c + (1 - c) / (1 + e^(-a(θ - b)))

Donde:
  θ (theta) = Habilidad del estudiante (-3.0 a +3.0)
  a = Discriminacion (0.5 - 2.5) → Que tan bien diferencia
  b = Dificultad (-2.0 a +2.0) → Dificultad de la pregunta
  c = Pseudo-adivinanza (0.0 - 0.25) → Probabilidad de acertar al azar
```

### Fisher Information (seleccion optima de preguntas)

```
I(θ) = a² × P(θ) × Q(θ) × [1 - c + c × Q(θ)]² / [1 - c]²

Donde:
  Q(θ) = 1 - P(θ)

Se selecciona la pregunta con maximo I(θ) en el theta actual del estudiante.
```

### Estimacion de Theta

```python
# Estimacion Maxima Verosimilitud (MLE)
theta_inicial = log(p / (1 - p))  # donde p = correctas/total
# Rango: -3.0 a +3.0 (se ajusta iterativamente)
```

### Conversion Theta → Rango

```python
θ < -1.5  → Rango E
-1.5 a -0.5 → Rango D
-0.5 a +0.5 → Rango C
+0.5 a +1.0 → Rango B
+1.0 a +1.5 → Rango A
θ > +1.5  → Rango S
```

### Conversion a Percentil

```python
percentil = norm.cdf(theta) × 100  # Distribucion normal estandar
# Clamped a rango 1-99
```

---

## 11. SISTEMA DE DIAGNOSTICO

### Fase 1: Diagnostico Rapido (Onboarding)

**Backend:** `apps/backend/app/routes/diagnostic_two_phase.py`
**Mobile:** `apps/mobile/lib/features/onboarding/presentation/pages/quick_diagnostic_page.dart`

```
POST /diagnostic/quick/start
  → Selecciona 15 preguntas (3 por materia)
  → Distribucion: 1 facil + 1 media + 1 dificil por materia
  → Limite: 10 minutos
  → SIN feedback inmediato (calibracion pura)

POST /diagnostic/quick/submit
  → Calcula correctas por materia
  → Estima theta (IRT)
  → Identifica areas debiles (score < 0.7)
  → Retorna: rank, theta, percentil, areas_debiles
```

### Fase 2: Diagnostico Profundo (por materia)

```
POST /diagnostic/deep/start/{subject_id}
  → 15-20 preguntas para esa materia especifica
  → Ordenadas por dificultad creciente

POST /diagnostic/deep/submit
  → Mastery por tema: correctas / total
  → Genera skill tree con desbloqueos
  → Actualiza TopicMastery en BD
```

### Revelacion de Resultados (Mobile)

**Archivo:** `apps/mobile/lib/features/onboarding/presentation/pages/results_reveal_page.dart`

```
Secuencia visual (4 segundos):
  1. "EL SISTEMA TE HA EVALUADO..."
  2. "CALCULANDO RANGO DE CAZADOR"
  3. Radar chart animado (5 materias)
  4. Letra de rango grande con animacion escala
  5. Lista de areas debiles por prioridad:
     - HIGH:   score < 0.4
     - MEDIUM: score 0.4-0.6
     - LOW:    score 0.6-0.7
```

### Reevaluacion Mensual

```
POST /monthly-reassessment/start
  → Nuevo diagnostico completo
  → Compara con baseline anterior
  → Identifica mejoras
  → Regenera plan de estudio
```

---

## 12. MODOS DE JUEGO

### 12.1 Practice Mode (Sesion de Practica)

**Backend:** `apps/backend/app/services/practice_service.py` (406 lineas)
**Mobile:** `apps/mobile/lib/features/practice/presentation/pages/practice_session_page.dart`

```
Configuracion:
  - 15 preguntas por sesion (configurable)
  - Seleccion inteligente: 60% falladas + 40% nuevas
  - 3 lifelines (una vez cada una):
    • 50/50: Elimina 2 opciones incorrectas
    • Ask AI: Pista de AI (no la respuesta)
    • Skip: Saltar sin penalidad

XP por respuesta correcta:
  base(10) + speed_bonus(0-5) + streak_bonus × difficulty_multiplier

Speed bonus:
  < 10s: +5 XP
  < 20s: +3 XP

Gold: 10 por respuesta correcta

UI Elements:
  - DopamineEngine (feedback psicologico)
  - ComboOverlay (aparece en combo >= 2)
  - FeedbackOverlay con desglose XP
  - AntiGamingBadge: "0 XP (REPETIDA)" o "5 XP (REPASO)"
  - VariableRewardPopup (recompensas variables)
```

### 12.2 Millionaire Mode (Quien Quiere Ser Millonario)

**Mobile:** `apps/mobile/lib/features/millionaire/presentation/pages/millionaire_page.dart` (1109 lineas)

```
Reglas:
  - 15 preguntas de dificultad progresiva
  - Maximo 3 partidas por dia
  - 3 estados: notStarted → playing → won/lost/walkingAway

Checkpoints (XP + Gold garantizados):
  Pregunta 5, 10, 15 son checkpoints
  Si pierdes, conservas rewards del ultimo checkpoint

3 Lifelines:
  - 50:50 (gratis): Elimina 2 opciones
  - AI Hint (50 gold): Pista de AI
  - Skip (gratis): Salta la pregunta

Walk Away:
  - Puedes retirarte en cualquier momento
  - Dialog de confirmacion muestra recompensas acumuladas
  - Conservas todo lo ganado hasta ese punto

UI:
  - Escalera de premios progresiva
  - Pantalla de resultado animada con escala elastica
  - Efecto shimmer en premios
```

### 12.3 Boss Raid (Raid de Jefe Semanal)

**Backend:** `apps/backend/app/services/boss_raid_service.py`
**Mobile:** `apps/mobile/lib/features/practice/presentation/pages/boss_raid_page.dart` (516 lineas)

```
Disponibilidad: Domingos 10 AM - 10 PM (Colombia)
Costo entrada: 100 gold
Preguntas: 20 (70% materia del boss + 30% aleatorias)

Boss:
  HP inicial: 10,000
  Derrotado cuando HP <= 0
  Todos los jugadores contribuyen dano
  Reset semanal (nuevo boss cada domingo)

Dano:
  base = 10 por correcta
  combo_bonus = min(combo, 10) × 5
  total = base + combo_bonus (0 si incorrecta)

XP: 10 × 3 = 30 XP por correcta (3x multiplier)

Rangos y Recompensas:
  S-Rank (>=90%): 500 gold + 200 XP + "Cazador Legendario"
  A-Rank (>=80%): 300 gold + 100 XP + "Cazador Elite"
  B-Rank (>=70%): 200 gold + 50 XP
  C-Rank (<70%):  100 gold + 0 XP

Badges especiales:
  Combo Master: 10+ combo
  Perfect: 100% en 10+ preguntas

UI:
  - Boss visual S-RANK con brillo purpura y animacion shake
  - Barra HP con progresion de color (rojo→naranja→amarillo)
  - 3 fases visuales (>66%, 33-66%, <33% HP)
  - Timer badge con animacion pulsante
  - Leaderboard top 50
```

### 12.4 Dungeon Mode (Mazmorra/Conquista)

**Modelos:** `DungeonGate`, `DungeonRun`, `DungeonEncounter`, `DungeonMonster`

```
Estructura:
  - DungeonGate: Portal de entrada (requiere nivel minimo)
  - DungeonRun: Sesion de mazmorra
  - DungeonEncounter: Encuentros con monstruos
  - DungeonMonster: Enemigos con HP, dano, recompensas

Node Progress (Conquista):
  - UserKingdomProgress: Progreso general del reino
  - UserNodeProgress: Progreso por nodo en el mapa
  - Nodos se desbloquean al completar prerequisitos
```

### 12.5 PvP Battles (Batallas)

**Backend:** `apps/backend/app/routes/battles.py`

```
Sistema de combate:
  - Preguntas en tiempo real
  - Cada respuesta correcta = dano al oponente
  - Respuesta incorrecta = dano recibido (difficulty × 5)
  - HP del usuario vs HP del enemigo
  - Batalla termina cuando HP <= 0

Recompensas:
  - XP basado en dificultad y velocidad
  - Orbs (gold): difficulty × 2
  - Critical hit (< 3s): orbs × 2
  - Level up: +10 HP max (cap 150), +5 MP max (cap 75)
```

---

## 13. SISTEMA DE CORAZONES

```python
# Valores por defecto
hearts: 5
max_hearts: 5

# Perdida
respuesta_incorrecta (no grace mode): -1 corazon
respuesta_incorrecta (grace mode): 0 (sin perdida)

# Grace Mode
Se activa automaticamente cuando hearts = 0
En grace mode: no se pierden corazones pero no se gana XP

# Recuperacion
1. Esperar regeneracion automatica (timer)
2. Ver anuncios: max 3 por dia (ads_watched_today)
3. Comprar corazones ilimitados (premium)
   unlimited_hearts_until: DateTime

# Transacciones
HeartTransaction: registra cada cambio de corazones
```

---

## 14. SISTEMA DE RACHA (Streak)

```python
# Campos del usuario
current_streak: dias consecutivos activo
longest_streak: record personal
previous_streak: racha antes de perderla
streak_lost_at: cuando se perdio
last_activity_date: ultima actividad

# Streak Freeze
streak_freeze_count: congelamientos disponibles
# Si un dia no entras, se usa un freeze automaticamente
# Si no hay freeze disponible, streak se reinicia a 0

# Multiplicadores XP (aplicados por GameEngineService)
1-6 dias:   1.0x
7-13 dias:  1.2x
14-29 dias: 1.5x
30+ dias:   2.0x

# Meta diaria
daily_goal_xp: 20 (configurable por usuario)
```

---

## 15. MASTERY Y REPETICION ESPACIADA

### Mastery Service

**Archivo:** `apps/backend/app/services/mastery_service.py`

```python
# Umbrales de Mastery
LOCKED = 0.0          # No iniciado
BEGINNER = 0.3        # Recien empezando
DEVELOPING = 0.5      # En progreso
PROFICIENT = 0.7      # Buen entendimiento
MASTER = 0.9          # Dominado

# Tasas de aprendizaje
LEARNING_RATE_CORRECT = 0.12    # +12% × (1.0 - actual) por correcta
LEARNING_RATE_INCORRECT = 0.06  # -6% × actual por incorrecta

# Sistema de Decay (sin practica)
DECAY_START_DAYS = 3            # Inicia decay despues de 3 dias
DECAY_RATE_PER_DAY = 0.02       # 2% por dia
DECAY_MINIMUM = 0.1             # Nunca baja de 10%
DECAY_CAP_DAYS = 30             # Maximo 60% decay total

# Prerequisitos
# Topic B requiere 60% mastery de Topic A para desbloquearse
```

### Repeticion Espaciada (SM-2 Mejorado)

**Archivo:** `apps/backend/app/services/spaced_repetition_service.py`

```python
# Intervalos base
AGAIN (failed):  1 dia
HARD:            2 dias
GOOD:            4 dias
EASY:            7 dias

# Factor de facilidad
EASINESS_FACTOR_INITIAL = 2.5
EASINESS_FACTOR_MIN = 1.3

# Formula: nuevo_intervalo = intervalo_anterior × easiness_factor
# Rango easiness: 1.3 a 4.0

# Reviews diarios
GET /spaced/daily-reviews?date=YYYY-MM-DD&max_reviews=50
  → new_items: preguntas nuevas
  → learning_items: en proceso de aprendizaje
  → review_items: requieren repaso

# Prioridad:
  1. Dias vencidos (high > medium > normal)
  2. Mastery score (menor = mayor prioridad)
  3. Easiness factor
```

---

## 16. PLANES DE ESTUDIO

**Backend:** `apps/backend/app/services/unified_study_plan_service.py`

### Generacion

```
POST /study-plans/generate/{subject_id}
  → Plan basico por materia

POST /study-plans/generate-adaptive
  → Integra: areas debiles + catalogo ICFES + historial

POST /study-plans/generate-ai-comprehensive
  → Plan AI (GPT/Claude) con recomendaciones personalizadas
```

### Estructura del Plan

```json
{
  "title": "Plan Matematicas - Nivel C",
  "subject": "Matematicas",
  "total_units": 8,
  "units": [
    {
      "unit_number": 1,
      "name": "Algebra Basica",
      "topics": [
        { "name": "Ecuaciones lineales", "difficulty": 3, "questions": 15 }
      ],
      "recommendations": {
        "priority": "high",
        "weak_areas": ["ecuaciones", "funciones"],
        "focus_topics": ["algebra basica"],
        "study_time": "45 min/dia"
      },
      "progress": 0.0,
      "unlocked": true
    }
  ],
  "difficulty_curve": "adaptive",
  "icfes_weight": 0.20,
  "exam_sections": ["Razonamiento Cuantitativo"]
}
```

### Cronograma Semanal

```python
WeeklyScheduleGenerator:
  - 7 dias con daily_study_minutes objetivo
  - Distribucion: 2 repasos + 2 temas nuevos + practica/dia
  - Ajuste urgencia si fecha examen < 30 dias (2x intensidad)

  Morning: Repaso espaciado (alta prioridad)
  Afternoon: Aprendizaje nuevos temas
  Evening: Sesion practica + reto
```

---

## 17. RECOMENDACIONES DE VIDEO

**Backend:** `apps/backend/app/services/video_recommendation_service.py`
**Mobile:** `apps/mobile/lib/features/video/presentation/pages/video_player_page.dart`

### Analisis de Patron de Error

```python
ERROR_PATTERN_WEIGHTS = {
    "conceptual": 1.5,    # Error fundamental → Videos teoria
    "procedural": 1.2,    # Error de proceso → Tutoriales paso a paso
    "careless": 0.8,      # Error por descuido → Videos repaso rapido
}

VIDEO_TYPE_FOR_ERROR = {
    "conceptual": ["explicacion", "tutorial", "teoria"],
    "procedural": ["ejercicio_resuelto", "paso_a_paso", "practica"],
    "careless": ["repaso_rapido", "tips", "resumen"],
}
```

### Ajuste de Dificultad

```python
DIFFICULTY_ADJUSTMENT = {
    "very_low" (< 30%):  -2  # Videos mas faciles
    "low" (30-50%):       -1
    "medium" (50-70%):     0  # Nivel actual
    "high" (> 70%):       +1  # Videos mas avanzados
}
```

### Respuesta de Recomendacion

```json
{
  "error_analysis": {
    "error_type": "conceptual",
    "performance_level": "low",
    "target_difficulty": 3
  },
  "primary_video": { "..." },
  "alternative_videos": ["4 videos mas"],
  "prerequisite_videos": ["videos de conceptos base"],
  "related_topic_videos": ["videos de contexto amplio"],
  "learning_path": {
    "order": ["video_ids en secuencia"],
    "estimated_time": 45
  },
  "motivational_message": "Sigue asi, vas mejorando!"
}
```

### Tracking de Video (Mobile)

```
- YouTube integration (youtube_player_flutter)
- Auto-completado a 80% visto
- Progreso: watched_seconds, percentage
- Soporte fullscreen con manejo orientacion
- Guardado automatico al ir a background
```

---

## 18. ANALISIS DE DEBILIDADES

**Backend:** `apps/backend/app/services/weakness_analysis_service.py`

### Clasificacion de Severidad

```python
CRITICAL:           Accuracy < 40%
SIGNIFICANT:        Accuracy 40-60%
TIME_INEFFICIENT:   Respuestas lentas (> 120s)
MINOR:              Accuracy 60-70%
```

### Tipos de Debilidad

```python
CONCEPTUAL_GAP:           Error fundamental → Necesita revision teoria
PROCEDURAL_SLOWNESS:      Demasiado lento → Necesita practica velocidad
SYSTEMATIC_ERROR:         Mismo error repetido (60%+ misma opcion)
INCONSISTENT_PERFORMANCE: Resultados variables
```

### Intervenciones Recomendadas

```python
# Brecha conceptual:
  needs_concept_review: True
  recommended_action: "Revisar conceptos base con videos teoria"

# Lentitud procedimental:
  needs_speed_practice: True
  estimated_sessions_needed: int

# Error sistematico:
  has_systematic_error: True
  dominant_distractor: str  # Opcion incorrecta mas seleccionada
```

### Umbrales

```python
accuracy_thresholds = { 'critical': 40, 'significant': 60, 'minor': 70 }
time_thresholds = { 'slow': 120, 'very_slow': 180 }  # segundos
min_attempts_for_analysis = 3
analysis_period_days = 90
systematic_error_threshold = 0.6  # 60% misma respuesta incorrecta
```

---

## 19. LIGAS Y LEADERBOARD

### Estructura de Ligas

```python
LeagueDivision:   Bronce, Plata, Oro, Platino, Diamante, Leyenda
LeagueWeek:       Semana competitiva activa
LeagueGroup:      Grupo de ~30 usuarios por nivel similar
UserLeague:       Posicion del usuario en su grupo actual
UserLeagueHistory: Historial de ligas anteriores
```

### Leaderboard

```python
# Tipos
- global: Top general por XP
- weekly: Top de la semana
- subject: Top por materia
- boss_raid: Top por raid (dano total)

# Cache: Redis 10 min TTL
# Top 50 + posicion del usuario actual
```

---

## 20. ECONOMIA VIRTUAL

### Monedas

```
Gold (Principal):
  - Inicio: 1000
  - Gana: 10 por respuesta correcta en practice
  - Gasta: Boss Raid (100), AI Hint en Millionaire (50), Items tienda

Orbs (Secundaria):
  - Gana: difficulty × 2 por correcta en batallas
  - Uso: Items especiales

Crystals (Premium):
  - Obtencion: Compra real ($)
  - Uso: Items premium, corazones ilimitados
```

### Tienda

```python
StoreTransaction: Registro de compras
UserPowerUp: Power-ups activos del usuario
CurrencyEarning: Historial de ganancias

GoldTransaction: Cada movimiento de gold
XPTransaction: Cada movimiento de XP
```

### Planes Premium

```python
free:    Funcionalidad basica
basic:   Sin anuncios + extras
premium: Corazones ilimitados + AI features
elite:   Todo + features exclusivas
```

---

## 21. AI SERVICE (Microservicio)

**Archivo:** `apps/ai-service/main.py` (692 lineas)

### Endpoints

```python
# Explicaciones AI
POST /ai/explain
  → GPT-3.5-turbo genera explicacion de la respuesta
  → Cache Redis 30 dias TTL
  → Mock responses si no hay OPENAI_API_KEY

# Generador de Planes YML
POST /ai/generate-study-plan
  → Genera plan de estudio en formato YML
  → Maximo 8 unidades
  → Personalizado por debilidades del usuario

# Test de Personalidad
POST /ai/personality-test
  → 5 clases de heroe:
    Warrior (Guerrero del Conocimiento)
    Mage (Mago Cuantico)
    Archer (Arquero de la Sabiduria)
    Priest (Sacerdote del Aprendizaje)
    Assassin (Asesino de la Logica)
  → Puntuacion ponderada por respuestas
```

---

## 22. APP MOBILE - FLUTTER

**Archivo:** `apps/mobile/pubspec.yaml` (128 lineas)
**Entry point:** `apps/mobile/lib/main.dart` (148 lineas)

### Arquitectura por Feature (Clean Architecture)

```
lib/
├── core/
│   ├── config/
│   │   ├── routes.dart        → GoRouter con 30+ rutas
│   │   └── env.dart           → Configuracion ambiente
│   ├── learning/
│   │   └── domain/
│   │       └── adaptive_engine.dart  → Motor adaptativo
│   ├── network/               → Dio interceptors
│   └── theme/                 → Tema oscuro RPG
│
├── features/
│   ├── auth/                  → Login, Register, Social Sign-In
│   ├── onboarding/            → 5 pasos + diagnostico rapido
│   ├── home/                  → Dashboard principal
│   ├── practice/              → Sesiones practica + Boss Raid
│   ├── millionaire/           → Modo Millonario
│   ├── diagnostic/            → Diagnostico profundo
│   ├── study_plan/            → Plan de estudio
│   ├── mastery/               → Tracking de mastery
│   ├── video/                 → Reproductor YouTube
│   ├── leagues/               → Ligas semanales
│   ├── profile/               → Perfil usuario
│   ├── shop/                  → Tienda virtual
│   ├── notifications/         → Push notifications
│   └── shell/                 → Bottom navigation (4 tabs)
│
└── shared/
    ├── widgets/               → Componentes reutilizables
    └── services/              → Servicios compartidos
```

### Inicializacion (main.dart)

```dart
1. Environment.init()          → Carga .env
2. Hive.initFlutter()          → BD local
3. SharedPreferences.init()    → Preferencias
4. Firebase.initializeApp()    → Auth social (opcional)
5. NotificationService.init()  → Push notifications
6. QuestionCacheService.init() → Cache preguntas
7. SyncManager.init()          → Sincronizacion offline
8. Sentry.init()               → Error tracking (30% sampling)
```

### Navegacion (routes.dart)

```dart
ShellRoute (MainShell):
  /home          → Home/Dashboard
  /leagues       → Ligas
  /study-plan    → Plan de estudio
  /profile       → Perfil

Rutas publicas:
  /splash, /onboarding/*, /login, /register, /diagnostic

Rutas protegidas:
  /practice/*, /millionaire, /boss-raid, /mastery, /shop, /video/*

Auth redirect: Si no autenticado → /login
Onboarding: Si no completado → /onboarding/welcome
```

### DopamineEngine

```dart
Sistema de engagement psicologico:
  - Recompensas variables (no predecibles)
  - Loss aversion (evitar perder racha)
  - Social proof (leaderboard)
  - Feedback inmediato (animaciones)
  - Combo visual (aparece en combo >= 2)
```

---

## 23. SISTEMA OFFLINE-FIRST

### Componentes

```dart
Hive:               BD local NoSQL para cache de preguntas y respuestas
ActionQueue:        Cola de acciones pendientes de sincronizar
SyncManager:        Orquestador de sincronizacion
ConnectivityMonitor: Detecta estado de conexion
PendingAnswerSync:  Respuestas que esperan ser enviadas al server
```

### Flujo Offline

```
1. Usuario responde pregunta SIN conexion
2. Respuesta se guarda en Hive + ActionQueue
3. PendingAnswerSync registra la accion pendiente
4. ConnectivityMonitor detecta reconexion
5. SyncManager procesa ActionQueue en orden FIFO
6. Envia cada PendingAnswerSync al backend
7. Backend procesa y retorna resultado
8. Se actualiza estado local
```

### Cache de Preguntas

```dart
QuestionCacheService:
  - Pre-descarga preguntas por materia al iniciar
  - Cache en Hive con TTL configurable
  - Permite practicar 100% offline
  - Sync delta al reconectar
```

---

## 24. FLUJO COMPLETO DEL USUARIO

```
INICIO: Usuario abre la app por primera vez
  │
  ▼
1. ONBOARDING (5 pasos)
   ├── Welcome screen
   ├── Seleccionar meta (puntaje objetivo ICFES)
   ├── Nivel actual (principiante/intermedio/avanzado)
   ├── Materias de enfoque
   └── Tiempo disponible por dia
  │
  ▼
2. DIAGNOSTICO RAPIDO (15 preguntas)
   ├── 3 por materia (facil + media + dificil)
   ├── Sin feedback inmediato
   ├── IRT scoring: theta, SE, percentil
   └── Resultado: Rango E-S + areas debiles
  │
  ▼
3. REVELACION DE RESULTADOS (animado)
   ├── "EL SISTEMA TE HA EVALUADO..."
   ├── Radar chart 5 materias
   ├── Rango grande animado
   └── Areas debiles priorizadas
  │
  ▼
4. GENERACION PLAN DE ESTUDIO
   ├── Input: areas debiles del diagnostico
   ├── Catalogo ICFES + historial
   ├── AI genera plan personalizado
   └── Output: unidades con videos, ejercicios
  │
  ▼
5. LOOP DIARIO DE PRACTICA
   │
   ├── a) Obtener siguiente pregunta (motor adaptativo)
   │      ├── Prioridad: temas debiles → nuevos → repaso espaciado
   │      ├── Dificultad: personalizada por rango + tasa exito
   │      └── IRT: maximizar informacion en theta actual
   │
   ├── b) Responder pregunta
   │      ├── Verificar correctitud
   │      ├── Analizar patron error (conceptual/procedimental/descuido)
   │      ├── Tracking tiempo
   │      ├── Anti-gaming check (tipo intento)
   │      └── XP + gold + mastery update
   │
   ├── c) Si incorrecta → Recomendacion video
   │      ├── Tipo error → tipo video
   │      ├── Ajuste dificultad por rendimiento
   │      ├── Videos prerequisito si brecha conceptual
   │      └── Path de aprendizaje sugerido
   │
   ├── d) Ver video (opcional)
   │      ├── YouTube player integrado
   │      ├── Auto-completado a 80% visto
   │      └── Progreso guardado automaticamente
   │
   └── e) Continuar hasta completar sesion
         └── Actualizar mastery + next_review_at
  │
  ▼
6. MODOS DE JUEGO (engagement)
   ├── Practice: 15 preguntas adaptativas
   ├── Millionaire: 15 progresivas, 3/dia
   ├── Boss Raid: Domingos, 20 preguntas, 3x XP
   ├── Dungeon: Exploracion con monstruos
   └── PvP: Batallas tiempo real
  │
  ▼
7. MASTERY TRACKING (continuo)
   ├── Score update por cada respuesta
   ├── Decay si no practica (2%/dia despues de 3 dias)
   ├── SM-2 repaso espaciado (1/2/4/7 dias)
   ├── Prerequisitos: 60% mastery para desbloquear
   └── Analisis debilidades periodico
  │
  ▼
8. LIGAS SEMANALES
   ├── Grupos de ~30 usuarios
   ├── Ranking por XP semanal
   ├── Ascenso/descenso entre divisiones
   └── Bronce → Plata → Oro → Platino → Diamante → Leyenda
  │
  ▼
9. REEVALUACION MENSUAL
   ├── Nuevo diagnostico completo
   ├── Comparacion con baseline
   ├── Ajuste de plan de estudio
   └── Actualizacion de puntaje proyectado ICFES
```

---

## ARCHIVOS CLAVE DE REFERENCIA

| Archivo | Lineas | Responsabilidad |
|---|---|---|
| `apps/backend/app/main.py` | 541 | Entry point, routers, startup |
| `apps/backend/app/core/config.py` | 359 | Configuracion Pydantic |
| `apps/backend/app/core/security.py` | 157 | JWT, bcrypt, auth dependencies |
| `apps/backend/app/core/redis_cache.py` | 128 | Redis cache + decorator |
| `apps/backend/app/models/__init__.py` | 178 | Export 60+ modelos |
| `apps/backend/app/models/user.py` | 132 | Modelo usuario RPG |
| `apps/backend/app/models/question.py` | 357 | Modelo pregunta IRT |
| `apps/backend/app/services/game_engine_service.py` | 298 | Fuente unica mecanicas juego |
| `apps/backend/app/services/practice_service.py` | 406 | Logica sesiones practica |
| `apps/backend/app/services/boss_raid_service.py` | ~300 | Logica boss raid |
| `apps/backend/app/services/mastery_service.py` | ~250 | Mastery + decay |
| `apps/backend/app/services/spaced_repetition_service.py` | ~300 | SM-2 repaso espaciado |
| `apps/backend/app/services/weakness_analysis_service.py` | ~200 | Analisis debilidades |
| `apps/backend/app/services/video_recommendation_service.py` | ~300 | Recomendaciones video |
| `apps/backend/app/services/unified_study_plan_service.py` | ~400 | Planes estudio |
| `apps/backend/app/import_icfes_excel.py` | 642 | Importador Excel |
| `apps/ai-service/main.py` | 692 | Microservicio AI |
| `apps/mobile/lib/main.dart` | 148 | Entry point Flutter |
| `apps/mobile/lib/core/config/routes.dart` | 376 | Navegacion GoRouter |
| `apps/mobile/pubspec.yaml` | 128 | Dependencias Flutter |
| `docker-compose.yml` | 263 | Infraestructura Docker |

---

*Documentacion generada automaticamente a partir del analisis del codigo fuente.*
