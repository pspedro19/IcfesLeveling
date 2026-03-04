# ICFES Leveling - Backend API

Backend API para la plataforma de gamificación educativa ICFES Leveling. Proporciona servicios RESTful para la aplicación web y móvil con soporte offline-first y aprendizaje adaptativo.

## Stack Tecnológico

| Componente | Tecnología |
|------------|------------|
| Framework | FastAPI 0.100+ |
| ORM | SQLAlchemy 2.0 |
| Base de Datos | PostgreSQL 15 |
| Cache | Redis |
| Tareas Async | Celery |
| Auth | JWT (OAuth2) |
| Validación | Pydantic v2 |

## Estructura del Proyecto

```
apps/backend/
├── app/
│   ├── core/                    # Configuración central
│   │   ├── config.py            # Settings y variables de entorno
│   │   ├── database.py          # Conexión PostgreSQL
│   │   └── security.py          # JWT y autenticación
│   │
│   ├── models/                  # Modelos SQLAlchemy
│   │   ├── user.py              # Usuario y perfil
│   │   ├── question.py          # Preguntas ICFES
│   │   ├── mobile_offline.py    # Modelos para app móvil
│   │   └── ...
│   │
│   ├── schemas/                 # Schemas Pydantic
│   │   ├── mobile.py            # Schemas API móvil
│   │   └── ...
│   │
│   ├── routes/                  # Endpoints API
│   │   ├── auth.py              # Autenticación
│   │   ├── mobile_api.py        # API móvil completa
│   │   ├── questions.py         # CRUD preguntas
│   │   └── ...
│   │
│   ├── services/                # Lógica de negocio
│   │   ├── mobile_service.py    # Servicio móvil
│   │   └── ...
│   │
│   └── main.py                  # Punto de entrada
│
├── database/
│   ├── migrations/              # Migraciones SQL
│   │   └── 036-offline-adaptive-mobile.sql
│   └── init/                    # Scripts inicialización
│
├── requirements.txt
└── Dockerfile
```

## Configuración

### Variables de Entorno

```env
# Base de Datos (REQUIRED)
DATABASE_URL=postgresql://<user>:<password>@<host>:<port>/<database>
DB_HOST=postgres
DB_PORT=5432
DB_NAME=gameplay_db
DB_USER=gameplay
DB_PASSWORD=<your-secure-password>

# Redis
REDIS_URL=redis://localhost:6379/0

# JWT (REQUIRED - minimum 32 characters)
JWT_SECRET=<your-jwt-secret-min-32-chars>
SECRET_KEY=<your-secret-key-min-32-chars>
ACCESS_TOKEN_EXPIRE_MINUTES=30

# ClickHouse Analytics (optional)
CLICKHOUSE_HOST=clickhouse
CLICKHOUSE_PORT=9000
CLICKHOUSE_USER=default
CLICKHOUSE_PASSWORD=<your-clickhouse-password>
CLICKHOUSE_DATABASE=gameplay_analytics

# Payment Gateway (optional)
WOMPI_PUBLIC_KEY=<your-wompi-public-key>
WOMPI_PRIVATE_KEY=<your-wompi-private-key>
WOMPI_EVENT_SECRET=<your-wompi-event-secret>

# App
ENVIRONMENT=development
APP_VERSION=1.0.0
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:4000

# Importación automática (opcional)
AUTO_IMPORT_QUESTIONS=false
QUESTIONS_EXCEL_PATH=/app/questions.xlsx
ICFES_CATALOG_CSV_PATH=/app/01_icfes_topics_catalog.csv
```

> **IMPORTANT**: Never commit credentials to version control. Copy `.env.example` to `.env` and fill in your values.

### Instalación Local

```bash
# Clonar repositorio
cd apps/backend

# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# o: venv\Scripts\activate  # Windows

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar migraciones
psql -U postgres -d icfes_db -f database/migrations/036-offline-adaptive-mobile.sql

# Iniciar servidor
uvicorn app.main:app --reload --port 4000
```

### Docker

```bash
docker-compose up -d
```

## API Reference

### Autenticación

Todos los endpoints (excepto `/auth/*`) requieren JWT Bearer token:

```http
Authorization: Bearer <access_token>
```

#### Login
```http
POST /api/v1/auth/token
Content-Type: application/x-www-form-urlencoded

username=user@email.com&password=secret
```

Response:
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer"
}
```

---

## Mobile API (`/api/v1/mobile`)

API diseñada para la aplicación Flutter con soporte offline-first.

### Preguntas

#### Obtener siguiente pregunta adaptativa
```http
GET /api/v1/mobile/questions/next?subject_id={uuid}
```

Response:
```json
{
  "question": {
    "id": "uuid",
    "text": "¿Cuál es la capital de Colombia?",
    "image_url": null,
    "topic_id": "uuid",
    "topic_name": "Geografía",
    "subject_id": "uuid",
    "subject_name": "Ciencias Sociales",
    "difficulty": "medium",
    "options": [
      {"id": "A", "text": "Bogotá", "image_url": null},
      {"id": "B", "text": "Medellín", "image_url": null},
      {"id": "C", "text": "Cali", "image_url": null},
      {"id": "D", "text": "Barranquilla", "image_url": null}
    ]
  },
  "cached_count": 45
}
```

#### Obtener lote para cache offline
```http
GET /api/v1/mobile/questions/batch?limit=50&subject_id={uuid}
```

Response:
```json
{
  "questions": [...],
  "total": 50
}
```

### Respuestas

#### Enviar respuesta
```http
POST /api/v1/mobile/answers/submit
Content-Type: application/json

{
  "question_id": "uuid",
  "answer_id": "A",
  "time_spent_seconds": 45,
  "session_type": "practice"
}
```

Response:
```json
{
  "correct": true,
  "correct_answer_id": "A",
  "explanation": "Bogotá es la capital...",
  "xp_earned": 10,
  "hearts_remaining": 5,
  "mastery_update": {
    "topic_id": "uuid",
    "old_score": 0.6,
    "new_score": 0.65
  },
  "streak_update": {
    "current": 7,
    "extended": false,
    "daily_goal_met": true
  }
}
```

### Sincronización Offline

#### Sincronizar respuestas offline
```http
POST /api/v1/mobile/sync/answers
Content-Type: application/json

{
  "actions": [
    {
      "id": "uuid",
      "question_id": "uuid",
      "answer_id": "B",
      "was_correct": false,
      "time_spent_seconds": 30,
      "session_type": "practice",
      "client_timestamp": "2025-12-27T10:30:00Z"
    }
  ]
}
```

Response:
```json
{
  "synced_count": 1,
  "failed": [],
  "server_state": {
    "xp": 1500,
    "level": 5,
    "hearts": 4,
    "streak": 7,
    "last_activity_date": "2025-12-27"
  }
}
```

#### Reconciliar estado
```http
POST /api/v1/mobile/sync/state
Content-Type: application/json

{
  "hearts": 3,
  "streak": 5,
  "last_activity_date": "2025-12-27",
  "today_xp": 50
}
```

Response:
```json
{
  "server_state": {...},
  "conflicts": [
    {
      "field": "hearts",
      "client_value": 3,
      "server_value": 4,
      "resolution": "server"
    }
  ]
}
```

### Corazones (Vidas)

#### Estado de corazones
```http
GET /api/v1/mobile/hearts/status
```

Response:
```json
{
  "hearts": 4,
  "max_hearts": 5,
  "next_regen_at": "2025-12-27T14:30:00Z",
  "unlimited_until": null,
  "is_unlimited": false
}
```

#### Usar corazón
```http
POST /api/v1/mobile/hearts/use
Content-Type: application/json

{
  "reason": "wrong_answer",
  "source_id": "question-uuid"
}
```

#### Recargar corazones
```http
POST /api/v1/mobile/hearts/refill
Content-Type: application/json

{
  "method": "gems",
  "gems_spent": 50
}
```

### Rachas (Streaks)

#### Estado de racha
```http
GET /api/v1/mobile/streak/status
```

Response:
```json
{
  "current": 7,
  "longest": 15,
  "today_xp": 50,
  "daily_goal": 20,
  "goal_met": true,
  "last_activity_date": "2025-12-27",
  "freezes_available": 2,
  "at_risk": false
}
```

#### Extender racha
```http
POST /api/v1/mobile/streak/extend
Content-Type: application/json

{
  "xp_earned": 10,
  "activity_date": "2025-12-27"
}
```

#### Usar freeze de racha
```http
POST /api/v1/mobile/streak/freeze
```

### Ligas

#### Liga actual
```http
GET /api/v1/mobile/leagues/current
```

Response:
```json
{
  "division": {
    "id": "uuid",
    "name": "Plata",
    "tier": 2,
    "color": "#C0C0C0"
  },
  "group_id": "uuid",
  "rank": 5,
  "weekly_xp": 450,
  "week_ends_at": "2025-12-29T23:59:59Z",
  "promotion_threshold": 10,
  "relegation_threshold": 25,
  "participants": 30
}
```

#### Leaderboard
```http
GET /api/v1/mobile/leagues/leaderboard?limit=30
```

Response:
```json
{
  "leaderboard": [
    {
      "user_id": "uuid",
      "name": "Player1",
      "avatar_url": null,
      "xp": 800,
      "rank": 1,
      "is_me": false
    }
  ],
  "my_rank": 5,
  "my_xp": 450,
  "total_participants": 30
}
```

#### Unirse a liga
```http
POST /api/v1/mobile/leagues/join
```

#### Historial de ligas
```http
GET /api/v1/mobile/leagues/history
```

### Maestría por Tema

#### Obtener maestría
```http
GET /api/v1/mobile/mastery/topics?subject_id={uuid}
```

Response:
```json
{
  "topics": [
    {
      "id": "uuid",
      "name": "Álgebra",
      "subject_id": "uuid",
      "subject_name": "Matemáticas",
      "mastery_score": 0.75,
      "questions_seen": 50,
      "questions_correct": 38,
      "last_practiced_at": "2025-12-27T10:00:00Z",
      "status": "practiced"
    }
  ]
}
```

#### Áreas débiles
```http
GET /api/v1/mobile/mastery/weak-areas
```

Response:
```json
{
  "weak_areas": [
    {
      "topic_id": "uuid",
      "topic_name": "Trigonometría",
      "subject_id": "uuid",
      "subject_name": "Matemáticas",
      "mastery_score": 0.35,
      "priority": "high",
      "suggested_practice": 10
    }
  ]
}
```

### Notificaciones Push

#### Registrar dispositivo
```http
POST /api/v1/mobile/notifications/register
Content-Type: application/json

{
  "token": "fcm-token-here",
  "platform": "android",
  "device_info": {
    "model": "Pixel 7",
    "os_version": "14"
  }
}
```

#### Actualizar preferencias
```http
PUT /api/v1/mobile/notifications/preferences
Content-Type: application/json

{
  "streak_reminder": true,
  "streak_at_risk": true,
  "daily_goal_reminder": true,
  "league_updates": true,
  "new_content": false,
  "quiet_hours_start": "22:00",
  "quiet_hours_end": "08:00"
}
```

---

## Modelos de Base de Datos

### Modelos Mobile Offline (`mobile_offline.py`)

| Modelo | Descripción |
|--------|-------------|
| `UserQuestionHistory` | Historial de respuestas del usuario |
| `UserTopicMastery` | Puntuación de maestría por tema |
| `PendingAnswerSync` | Cola de sincronización offline |
| `HeartTransaction` | Transacciones de corazones |
| `UserDailyActivity` | Actividad diaria del usuario |
| `StreakFreeze` | Freezes de racha usados |
| `LeagueDivision` | Divisiones de liga (Bronce→Diamante) |
| `LeagueWeek` | Semanas de competición |
| `LeagueGroup` | Grupos de 30 usuarios |
| `UserLeague` | Participación en liga actual |
| `UserLeagueHistory` | Historial de ligas |
| `DailyChallenge` | Desafíos diarios |
| `UserDailyChallenge` | Progreso en desafíos |
| `UserDeviceToken` | Tokens FCM/APNs |
| `NotificationHistory` | Historial de notificaciones |

### Motor de Aprendizaje Adaptativo

El sistema usa una función SQL para seleccionar preguntas:

```sql
-- Prioridades de selección:
-- 1. 60% - Áreas débiles (mastery_score < 0.6)
-- 2. 25% - Repaso espaciado (no vistas en 7+ días)
-- 3. 15% - Preguntas nuevas
```

---

## Códigos de Error

| Código | Significado |
|--------|-------------|
| `HEARTS_EMPTY` | Sin corazones disponibles |
| `NO_FREEZES` | Sin freezes de racha |
| `NOT_IN_LEAGUE` | Usuario no está en liga |
| `ALREADY_SYNCED` | Acción ya sincronizada |

---

## Health Checks

```http
GET /health
GET /api/v1/health
```

---

## Desarrollo

### Ejecutar Tests
```bash
pytest tests/ -v
```

### Formateo
```bash
black app/
isort app/
```

### Linting
```bash
flake8 app/
mypy app/
```

---

## Arquitectura

```
┌─────────────────┐     ┌─────────────────┐
│   Flutter App   │────▶│   FastAPI       │
│   (Offline)     │     │   Backend       │
└────────┬────────┘     └────────┬────────┘
         │                       │
         │ Sync                  │
         │                       ▼
         │              ┌─────────────────┐
         │              │   PostgreSQL    │
         │              │   + Redis       │
         │              └─────────────────┘
         │
         ▼
┌─────────────────┐
│   Hive Cache    │
│   (Local)       │
└─────────────────┘
```

---

## Licencia

Propietario - ICFES Leveling © 2025
