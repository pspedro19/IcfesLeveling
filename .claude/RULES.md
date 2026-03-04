# RULES.md — ICFES Leveling

> Reglas obligatorias para todo contribuidor del proyecto. Cualquier PR que viole estas reglas será rechazado.

---

## 1. REGLAS DE ARQUITECTURA

### 1.1 Monorepo
- Todo el código vive en un solo repositorio con estructura `apps/` y `database/`.
- **Nunca** crear servicios fuera de `apps/`.
- Cada servicio tiene su propio `Dockerfile` y se orquesta con `docker-compose.yml`.

### 1.2 Separación de Servicios
| Servicio | Puerto | Responsabilidad | Lenguaje |
|---|---|---|---|
| backend | 4000 | API REST principal, lógica de negocio | Python/FastAPI |
| ai-service | 8002 | Explicaciones AI, planes de estudio | Python/FastAPI |
| websocket | 4002 | Comunicación tiempo real (PvP) | Node.js |
| mobile | N/A | App cliente | Flutter/Dart |

### 1.3 Comunicación entre Servicios
- Mobile → Backend: **REST API únicamente** (Dio HTTP client).
- Mobile → WebSocket: **WebSocket** para PvP/tiempo real.
- Backend → AI Service: **HTTP interno** (red Docker).
- Backend → PostgreSQL/Redis/ClickHouse: **Drivers nativos** (SQLAlchemy, redis-py).
- **PROHIBIDO**: Comunicación directa Mobile → DB, Mobile → AI Service.

---

## 2. REGLAS DE BACKEND (Python/FastAPI)

### 2.1 Game Engine Service = Fuente Única de Verdad
- **TODA** fórmula de juego (XP, nivel, rango, daño, oro) DEBE estar en `game_engine_service.py`.
- Si existe una fórmula duplicada en otro archivo, es **legacy** y debe eliminarse.
- Nunca calcular XP, niveles o rangos fuera de `GameEngineService`.

### 2.2 Estructura de Archivos Backend
```
apps/backend/app/
├── core/          → Config, security, redis, middleware (NO lógica de negocio)
├── models/        → SQLAlchemy models SOLAMENTE (sin lógica)
├── routes/        → Endpoints FastAPI (validación + llamada a service)
├── services/      → TODA la lógica de negocio
├── schemas/       → Pydantic schemas (request/response)
└── tasks/         → Celery background tasks
```

### 2.3 Convenciones de Código Backend
- Python 3.11+ estricto.
- Type hints en **todas** las funciones (parámetros y retorno).
- Pydantic v2 para validación (NO usar dict sin tipado).
- SQLAlchemy 1.x query style actualmente (`db.query(Model).filter(...)`) — migración a 2.0 pendiente.
- Async/await para endpoints que lo requieran (sync Session también es válido actualmente).
- Imports relativos dentro del paquete `app` (ej: `from ..models.user import User`, `from .config import settings`).

### 2.4 Endpoints
- Prefijo: `/api/v1/` para todos los routers.
- Responses siempre con schema Pydantic definido.
- HTTP status codes correctos: 200 OK, 201 Created, 400 Bad Request, 401 Unauthorized, 404 Not Found.
- Paginación: `?page=1&per_page=20` (max 100).
- Todo endpoint protegido requiere `Depends(get_current_active_user)`.

### 2.5 Manejo de Errores
- Usar `HTTPException` de FastAPI (NO raise genérico).
- Logging con `structlog` o `logging` estándar (NO print statements).
- Sentry para error tracking en producción.
- Nunca exponer stack traces al cliente.

### 2.6 Base de Datos
- Migraciones con Alembic **siempre** (NO raw SQL para schema changes).
- UUIDs como primary keys (NO autoincrement integers).
- Timestamps con timezone: `DateTime(timezone=True)`.
- Soft deletes con `deleted_at` cuando aplique (NO hard delete de datos de usuario).
- Índices explícitos en columnas usadas en WHERE/JOIN.

---

## 3. REGLAS DE MOBILE (Flutter/Dart)

### 3.1 Arquitectura
- **Clean Architecture** por feature:
  ```
  features/<feature>/
  ├── data/           → Repositories, data sources, DTOs
  ├── domain/         → Entities, use cases, repository interfaces
  └── presentation/   → Pages, widgets, providers (Riverpod)
  ```
- Estado global con **Riverpod** (NO Provider, NO BLoC, NO GetX).
- Navegación con **GoRouter** exclusivamente.

### 3.2 Offline-First
- **TODA** feature debe funcionar offline con degradación graceful.
- Datos locales en **Hive** (NO SharedPreferences para datos complejos).
- Cola de acciones pendientes via `ActionQueue` + `SyncManager`.
- Sincronización FIFO al reconectar.

### 3.3 Convenciones Dart
- Null safety estricto (NO `!` innecesarios, usar `?.` y `??`).
- Widgets: `const` constructors siempre que sea posible.
- Archivos: `snake_case.dart`.
- Clases: `PascalCase`.
- Variables/funciones: `camelCase`.
- Máximo 300 líneas por archivo (refactorizar si se excede).

### 3.4 UI/UX
- Tema oscuro RPG como default.
- Animaciones con **Rive** o **Lottie** (NO animaciones custom complejas).
- DopamineEngine para feedback psicológico en todas las interacciones de juego.
- Soporte responsive: mínimo 320px ancho.

### 3.5 Networking
- **Dio** como único HTTP client.
- Interceptors para: auth token, retry, logging, error handling.
- Timeout: 30s connect, 60s receive.
- Retry: 3 intentos con backoff exponencial para errores 5xx.

---

## 4. REGLAS DE GAMIFICACIÓN

### 4.1 Economía
- **Nunca** dar recursos sin registrar transacción (`GoldTransaction`, `XPTransaction`).
- Gold inicial: 1000. No modificar sin aprobación.
- XP caps: máximo 500 XP/hora (anti-gaming).
- Toda compra requiere validación server-side (NO confiar en el cliente).

### 4.2 Anti-Gaming (Obligatorio)
- Tiempo mínimo de respuesta: **3 segundos** (rechazar si es menor).
- Rate limiting: **60 req/min** por usuario.
- Duplicados: misma pregunta en misma sesión = **rechazado**.
- Tipo de intento (`new`/`valid_review`/`invalid_repeat`) determina XP.
- Grace mode (0 corazones): juega pero **NO gana XP**.

### 4.3 IRT (Item Response Theory)
- Modelo **3PL** exclusivamente: `P(θ) = c + (1-c) / (1 + e^(-a(θ-b)))`.
- Parámetros: `a` (0.5-2.5), `b` (-2.0 a +2.0), `c` (0.0-0.25).
- Theta range: -3.0 a +3.0.
- Selección de preguntas por **máxima Fisher Information**.
- Nunca modificar parámetros IRT sin recalibración estadística.

---

## 5. REGLAS DE SEGURIDAD

### 5.1 Autenticación
- JWT con HS256 (mínimo 32 chars para secret).
- Access token: 30 min. Refresh token: 7 días.
- Passwords: bcrypt cost 12 en producción.
- Clock skew protection: rechazar tokens con `iat` > 30s en el futuro.
- Tokens revocados almacenados en `RevokedToken`.

### 5.2 Datos Sensibles
- **NUNCA** commitear credenciales, API keys, o secrets.
- Variables de entorno para toda configuración sensible.
- `.env` en `.gitignore` siempre.
- Credenciales de desarrollo documentadas SOLO en docker-compose (NO en código).

### 5.3 Validación
- Validar **TODO** input del usuario server-side (NO confiar en validación cliente).
- SQL injection: SQLAlchemy parameterized queries (NUNCA string interpolation).
- XSS: sanitizar todo output de texto libre.

---

## 6. REGLAS DE DATOS

### 6.1 Preguntas ICFES
- Fuente única: archivos Excel en `database/allquestions/`.
- Import via `import_icfes_excel.py` (NUNCA insertar preguntas manualmente en DB).
- Cada pregunta DEBE tener: texto, 4 opciones, respuesta correcta, materia, tema, dificultad.
- Dificultad: 1-10 (bajo=1, medio=5, alto=8, muy alto=10).
- Parámetros IRT iniciales: `a=1.0, b=0.0, c=0.25`.

### 6.2 Materias (5 fijas)
1. Lectura Crítica → "Lenguaje"
2. Matemáticas → "Matematicas"
3. Ciencias Naturales → "Ciencias Naturales"
4. Sociales y Ciudadanas → "Sociales"
5. Inglés → "Ingles"

**No agregar ni eliminar materias** sin rediseño del sistema de diagnóstico.

---

## 7. REGLAS DE GIT Y DEPLOY

### 7.1 Branching
- `main` → Producción (protegido).
- `develop` → Integración.
- `feature/<nombre>` → Features nuevas.
- `fix/<nombre>` → Bug fixes.
- `hotfix/<nombre>` → Fixes urgentes a producción.

### 7.2 Commits
- Formato: `tipo(scope): descripción`
- Tipos: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`, `perf`.
- Scope: `backend`, `mobile`, `ai`, `ws`, `db`, `docker`.
- Ejemplo: `feat(backend): add spaced repetition daily reviews endpoint`

### 7.3 Pull Requests
- Requiere al menos 1 review.
- CI debe pasar (tests + lint).
- No merge con conflictos.
- Squash merge preferido.

### 7.4 Docker
- Todo servicio debe arrancar con `docker-compose up`.
- Health checks obligatorios.
- Volúmenes nombrados para persistencia.
- Red `icfes_network` (bridge) para comunicación interna.

---

## 8. REGLAS DE TESTING

- Backend: pytest con coverage mínimo 70%.
- Endpoints: tests de integración con TestClient de FastAPI.
- Mobile: widget tests para componentes críticos.
- Game Engine: unit tests para TODAS las fórmulas (XP, nivel, rango, daño).
- Anti-gaming: tests específicos para cada regla.
- IRT: tests con datos sintéticos conocidos.

---

## 9. REGLAS DE DOCUMENTACIÓN

- Todo endpoint nuevo debe documentarse en su router (docstrings FastAPI).
- Cambios en modelos → actualizar `DOCUMENTACION_PROYECTO.md`.
- Cambios en fórmulas → actualizar `GAME_DESIGN.md`.
- Nuevas features → actualizar `SPEC.md`.
- **README.md** en cada carpeta `apps/<servicio>/`.
