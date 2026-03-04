# CLAUDE.md — ICFES Leveling

> Contexto esencial para Claude Code. Lee esto ANTES de hacer cualquier cambio.

## Proyecto

**ICFES Leveling** es una plataforma movil gamificada para preparar estudiantes colombianos para el examen ICFES Saber 11. Combina testing adaptativo (IRT 3PL), mecanicas RPG/anime, y AI personalizada.

## Estructura del Monorepo

```
IcfesLeveling/
  apps/
    backend/         → FastAPI (Python 3.11+), puerto 4000
    mobile/          → Flutter/Dart (SDK >=3.0.0), app principal
    ai-service/      → FastAPI, explicaciones AI y planes de estudio
  database/
    allquestions/    → Excel fuente de preguntas ICFES
    migrations/      → Alembic migrations
  docker-compose.yml → Orquestacion de todos los servicios
  .claude/           → Specs detalladas (RULES.md, GAME_DESIGN.md, etc.)
```

## Servicios y Puertos

| Servicio | Puerto | Stack |
|----------|--------|-------|
| backend | 4000 | FastAPI + SQLAlchemy + PostgreSQL |
| websocket | 4002 | Node.js (PvP battles) |
| ai-service | 8002 | FastAPI + OpenAI/Claude |
| postgres | 5432 | PostgreSQL 16 |
| redis | 6379 | Cache + rate limiting |
| clickhouse | 8123 | Analytics |

## Reglas No Negociables

1. **GameEngineService es la unica fuente de verdad** para formulas de XP, nivel, rango, dano, oro (`apps/backend/app/services/game_engine_service.py`). NUNCA calcular estas formulas en otro lugar.

2. **ZERO mock data** — Toda pantalla debe conectar a endpoints reales con datos reales del seed. Nunca usar datos hardcodeados como placeholder.

3. **Anti-gaming obligatorio** — Tiempo minimo respuesta: 3s. XP cap: 500/hora. Rate limit: 60 req/min. Grace mode (0 corazones): juega sin XP.

4. **Offline-first** — Toda feature mobile debe funcionar offline con degradacion graceful. Hive para cache local, ActionQueue + SyncManager para sync.

5. **5 materias fijas**: Lectura Critica, Matematicas, Ciencias Naturales, Sociales y Ciudadanas, Ingles. No agregar ni eliminar sin rediseno del diagnostico.

6. **UUIDs como PK** — Nunca autoincrement. Timestamps con timezone UTC.

## Arquitectura Backend

```
apps/backend/app/
  core/       → Config, security, redis (NO logica de negocio)
  models/     → SQLAlchemy models (NO logica)
  routes/     → Endpoints FastAPI (validacion + llamada a service)
  services/   → TODA la logica de negocio
  schemas/    → Pydantic v2 schemas (request/response)
  middleware/ → Rate limiting, anti-gaming, security
  tasks/      → Background tasks (Celery)
  scripts/    → Data loading, seeding
```

- Prefijo API: `/api/v1/`
- Auth: JWT HS256, access 30min, refresh 7 dias
- Passwords: bcrypt cost 12
- Todo endpoint protegido: `Depends(get_current_active_user)`

## Arquitectura Mobile (Flutter)

```
apps/mobile/lib/
  core/
    config/      → Environment, themes
    network/     → ApiClient (Dio), interceptors
    services/    → Sound, notifications, sync
    storage/     → Hive boxes
  features/
    <feature>/
      data/          → Repositories impl, DTOs
      domain/        → Entities, repository interfaces
      presentation/  → Pages, widgets, providers (Riverpod)
  shared/
    providers/   → Auth, connectivity, theme
    widgets/     → Reusable components
```

- State: **Riverpod** exclusivamente (NO Provider, BLoC, GetX)
- Navigation: **GoRouter**
- HTTP: **Dio** con interceptors (auth, retry, logging)
- Storage: **Hive** (datos complejos), **FlutterSecureStorage** (tokens)
- Animaciones: **Lottie** + **flutter_animate**

## Economia del Juego

| Moneda | Inicio | Fuente | Uso |
|--------|--------|--------|-----|
| Gold | 1000 | 10/correcta practice | Boss Raid (100), AI Hint (50), tienda |
| Orbs | 0 | difficulty x2 batallas | Items especiales |
| Crystals | 0 | Compra real ($) | Premium items |

## Corazones y Racha

- 5/5 corazones, -1 por incorrecta, grace mode a 0 (juega sin XP)
- Racha: multiplicadores XP — 7d=1.2x, 14d=1.5x, 30d=2.0x
- Streak Freeze: proteccion 1 dia inactividad

## Niveles y Rangos

```
XP para nivel N = (N-1)^2 x 100
Rangos: E(1-14), D(15-29), C(30-49), B(50-59), A(60-69), S(70-79), SS(80-89), SSS(90+)
```

## Comandos de Desarrollo

```bash
# Backend
docker compose up -d postgres redis backend
docker exec -it icfesleveling-backend-1 python -m pytest tests/ -v

# Mobile (Flutter 3.24.5 en C:\flutter_old_324)
cd apps/mobile
flutter pub get
flutter test test/unit/
flutter build apk --debug

# Verificar seed data
docker exec -it icfesleveling-backend-1 python -c "
from app.core.config import get_db_session
from app.models.question import Question
db = next(get_db_session())
print(f'Questions: {db.query(Question).count()}')
"
```

## Flujo de Datos: Pregunta → Respuesta

```
Mobile: tap opcion → ApiClient.post('/practice/answer', {...})
  → Backend: practice_router validates → practice_service.submit_answer()
    → game_engine_service.calculate_xp(difficulty, time, streak)
    → Anti-gaming checks (min 3s, no duplicates, XP cap)
    → Update: user.experience, user.gold, topic_mastery, practice_answer
  → Response: {is_correct, xp_earned, gold_earned, hearts_remaining, combo_count}
Mobile: update local state + Hive cache + play sound + show animation
```

## Archivos Criticos (Cambiar con Cuidado)

- `apps/backend/app/main.py` — Registro de TODOS los routers y middleware
- `apps/backend/app/services/game_engine_service.py` — Formulas del juego
- `apps/backend/app/models/user.py` — Modelo User (60+ columnas)
- `apps/backend/app/core/security.py` — JWT, auth, password hashing
- `apps/mobile/lib/core/network/api_client.dart` — HTTP client central
- `apps/mobile/lib/shared/providers/auth_provider.dart` — Estado de auth
- `apps/mobile/lib/core/config/app_theme.dart` — Tema RPG oscuro
- `docker-compose.yml` — Orquestacion de servicios

## Documentacion Detallada

Consultar `.claude/` para specs completas:
- `RULES.md` — Reglas obligatorias para contribuidores
- `GAME_DESIGN.md` — Formulas de balance, economia, progresion
- `MOBILE_SPEC.md` — Arquitectura Flutter, clean architecture
- `CODING_STANDARDS.md` — Convenciones de codigo
- `API_SPEC.md` — Referencia completa de endpoints
- `DATA_MODELS.md` — 140+ tablas del sistema
- `TESTING_STRATEGY.md` — Piramide de tests
- `DEPLOYMENT.md` — Docker, CI/CD, produccion

## Lo que NO Hacer

- NO calcular XP/niveles/rangos fuera de GameEngineService
- NO usar datos mock/hardcodeados en pantallas
- NO commitear credenciales, API keys, o .env
- NO agregar materias sin rediseno del diagnostico
- NO usar autoincrement IDs (siempre UUID v4)
- NO comunicar Mobile → DB directamente (siempre via API)
- NO usar print() en backend (usar logging)
- NO crear archivos innecesarios — editar existentes cuando sea posible
