# DEPLOYMENT.md — ICFES Leveling

> Guía de despliegue, infraestructura, y operaciones.

---

## 1. ENTORNOS

| Entorno | Propósito | URL |
|---|---|---|
| development | Local con Docker | localhost:4000 |
| staging | Pre-producción | staging-api.icfesleveling.com |
| production | Producción | api.icfesleveling.com |

---

## 2. DESARROLLO LOCAL

### 2.1 Requisitos
- Docker Desktop ≥ 24.0
- Docker Compose ≥ 2.20
- (Opcional) Python 3.11+ para desarrollo fuera de Docker
- (Opcional) Flutter SDK ≥ 3.0 para mobile

### 2.2 Setup Inicial

```bash
# 1. Clonar repositorio
git clone <repo-url>
cd icfes-leveling

# 2. Crear archivo .env desde template
cp .env.example .env
# Editar .env con valores locales

# 3. Levantar todos los servicios
docker-compose up -d

# 4. Verificar servicios
docker-compose ps
# Todos deben estar en estado "Up"

# 5. Verificar backend
curl http://localhost:4000/docs
# Debe mostrar Swagger UI
```

### 2.3 Docker Compose Services

```yaml
services:
  postgres:     # PostgreSQL 16 → puerto 5433
  pgadmin:      # pgAdmin4 → puerto 5050
  redis:        # Redis 7-alpine → puerto 6379
  clickhouse:   # ClickHouse → puerto 8123
  backend:      # FastAPI → puerto 4000
  websocket:    # Node.js → puerto 4002
  ai-service:   # FastAPI → puerto 8002
```

### 2.4 Credenciales Desarrollo

```bash
# PostgreSQL
POSTGRES_USER=gameplay
POSTGRES_PASSWORD=gameplay123
POSTGRES_DB=gameplay_db
POSTGRES_PORT=5433

# pgAdmin
PGADMIN_EMAIL=admin@icfes.com
PGADMIN_PASSWORD=admin123

# Redis
REDIS_URL=redis://redis:6379  # Sin password en dev

# JWT (desarrollo)
JWT_SECRET=dev-secret-key-minimum-32-characters-long
```

### 2.5 Importación de Preguntas

```bash
# Automática al iniciar (si configurado)
AUTO_IMPORT_QUESTIONS=true
QUESTIONS_EXCEL_PATH=/data/preguntas_icfes.xlsx
IMPORT_CLEAR_EXISTING=false

# Manual
docker-compose exec backend python -m app.import_icfes_excel
```

### 2.6 Comandos Útiles

```bash
# Logs de un servicio
docker-compose logs -f backend

# Reiniciar un servicio
docker-compose restart backend

# Shell dentro del container
docker-compose exec backend bash

# Ejecutar migraciones
docker-compose exec backend alembic upgrade head

# Crear nueva migración
docker-compose exec backend alembic revision --autogenerate -m "descripcion"

# Reset completo de BD
docker-compose down -v
docker-compose up -d
```

---

## 3. VARIABLES DE ENTORNO

### 3.1 Requeridas (Producción)

```bash
# Base de datos
DATABASE_URL=postgresql://user:password@host:5432/dbname

# Seguridad
JWT_SECRET=<min-32-chars-random-string>

# Redis
REDIS_URL=redis://:password@host:6379

# AI Service
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Pagos
WOMPI_PUBLIC_KEY=pub_...
WOMPI_PRIVATE_KEY=prv_...
WOMPI_EVENT_SECRET=...
STRIPE_SECRET_KEY=sk_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Sentry
SENTRY_DSN=https://...@sentry.io/...

# App
ENVIRONMENT=production
```

### 3.2 Opcionales

```bash
# Backend
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
REDIS_MAX_CONNECTIONS=100
APP_NAME="ICFES LEVELING API"

# Import
AUTO_IMPORT_QUESTIONS=false
QUESTIONS_EXCEL_PATH=/data/preguntas_icfes.xlsx

# ClickHouse
CLICKHOUSE_URL=http://clickhouse:8123
```

---

## 4. BASE DE DATOS

### 4.1 Migraciones

```bash
# Crear migración
alembic revision --autogenerate -m "add_mastery_decay_fields"

# Aplicar migraciones pendientes
alembic upgrade head

# Rollback última migración
alembic downgrade -1

# Ver estado
alembic current
alembic history
```

### 4.2 Backup

```bash
# Backup completo
pg_dump -h localhost -p 5433 -U gameplay gameplay_db > backup_$(date +%Y%m%d).sql

# Restore
psql -h localhost -p 5433 -U gameplay gameplay_db < backup_20260218.sql
```

### 4.3 Índices Recomendados

```sql
-- Queries más frecuentes
CREATE INDEX idx_practice_answers_session ON practice_answers(session_id);
CREATE INDEX idx_questions_subject_active ON questions(subject_id) WHERE is_active = true;
CREATE INDEX idx_topic_mastery_user ON topic_mastery(user_id);
CREATE INDEX idx_topic_mastery_review ON topic_mastery(next_review_at) WHERE next_review_at IS NOT NULL;
CREATE INDEX idx_user_question_history_user ON user_question_history(user_id, question_id);
CREATE INDEX idx_leaderboard_weekly ON leaderboard(type, period) WHERE type = 'weekly';
```

---

## 5. REDIS

### 5.1 Configuración Producción

```bash
maxmemory 256mb
maxmemory-policy allkeys-lru
```

### 5.2 Keys Principales

```
# Cache
cache:leaderboard:global         TTL: 10 min
cache:leaderboard:weekly         TTL: 10 min
cache:user:{id}:streak           TTL: 5 min
cache:ai:explanation:{hash}      TTL: 30 días

# Sessions
session:{session_id}             TTL: 2 horas

# Rate limiting
ratelimit:{user_id}:{minute}     TTL: 60 sec

# Tokens revocados
revoked:{jti}                    TTL: 7 días
```

---

## 6. MONITORING

### 6.1 Health Checks

```bash
# Backend
GET /health → {"status": "ok", "db": "ok", "redis": "ok"}

# AI Service
GET /health → {"status": "ok"}

# Cada servicio en docker-compose tiene healthcheck configurado
```

### 6.2 Sentry

```python
# Backend: apps/backend/app/main.py
sentry_sdk.init(
    dsn=settings.SENTRY_DSN,
    environment=settings.ENVIRONMENT,
    traces_sample_rate=0.1,  # 10% de requests
)

# Mobile: apps/mobile/lib/main.dart
SentryFlutter.init(
    (options) {
        options.dsn = Env.sentryDsn;
        options.tracesSampleRate = 0.3;  # 30% sampling
    },
);
```

### 6.3 Logs

```python
# Estructura de logs recomendada
import logging

logger = logging.getLogger(__name__)

# En endpoints
logger.info("Practice session started", extra={
    "user_id": str(user.id),
    "session_id": str(session.id),
    "subject_id": str(request.subject_id),
})

# En errores
logger.error("Failed to process answer", extra={
    "user_id": str(user.id),
    "error": str(e),
}, exc_info=True)
```

---

## 7. MOBILE DEPLOYMENT

### 7.1 Android

```bash
# Build APK
cd apps/mobile
flutter build apk --release

# Build App Bundle (Play Store)
flutter build appbundle --release
```

### 7.2 iOS

```bash
cd apps/mobile
flutter build ios --release
# Abrir en Xcode para archive y upload
```

### 7.3 Environment Config

```dart
// apps/mobile/lib/core/config/env.dart
class Env {
  static const apiBaseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'http://localhost:4000/api/v1',
  );
  static const wsUrl = String.fromEnvironment(
    'WS_URL',
    defaultValue: 'ws://localhost:4002',
  );
}

// Build con environment
flutter build apk --dart-define=API_BASE_URL=https://api.icfesleveling.com/api/v1
```

---

## 8. CHECKLIST PRE-DEPLOY

```
□ Todas las migraciones aplicadas
□ Tests pasando (>70% coverage)
□ Variables de entorno configuradas
□ JWT_SECRET es único y >32 chars
□ Redis maxmemory configurado
□ Sentry DSN configurado
□ Health checks respondiendo
□ Backup de BD realizado
□ Import de preguntas verificado
□ Rate limiting activo
□ CORS configurado correctamente
□ HTTPS habilitado
```

---

## 9. MOBILE RELEASE CHECKLIST

### 9.1 Firebase Setup

```bash
# 1. Install Firebase CLI
npm install -g firebase-tools

# 2. Install FlutterFire CLI
dart pub global activate flutterfire_cli

# 3. Login to Firebase
firebase login

# 4. Configure project (generates firebase_options.dart + google-services.json)
cd apps/mobile
flutterfire configure --project=<your-firebase-project-id>
```

### 9.2 Android Keystore

```bash
# Generate release keystore (KEEP THIS SAFE — NEVER COMMIT)
keytool -genkey -v -keystore apps/mobile/android/app/release-keystore.jks \
  -keyalg RSA -keysize 2048 -validity 10000 \
  -alias icfes-leveling

# Create key.properties (NEVER COMMIT)
cat > apps/mobile/android/key.properties << 'EOF'
storePassword=<your-store-password>
keyPassword=<your-key-password>
keyAlias=icfes-leveling
storeFile=release-keystore.jks
EOF
```

### 9.3 AdMob IDs

Replace test IDs with production IDs in:
- `apps/mobile/android/app/src/main/AndroidManifest.xml` — App ID
- `apps/mobile/lib/core/services/admob_service.dart` — Ad unit IDs

Test App ID: `ca-app-pub-3940256099942544~3347511713`
Test Ad Unit: `ca-app-pub-3940256099942544/5224354917`

### 9.4 Pre-Release Verification

```bash
# Run automated checklist
bash scripts/setup-release.sh

# Run all tests
cd apps/mobile && flutter test

# Build release APK
flutter build apk --release \
  --dart-define=API_BASE_URL=https://api.icfesleveling.com/api/v1

# Build App Bundle (Google Play)
flutter build appbundle --release \
  --dart-define=API_BASE_URL=https://api.icfesleveling.com/api/v1
```

### 9.5 Files That Must NEVER Be Committed

```
apps/mobile/android/app/release-keystore.jks
apps/mobile/android/key.properties
apps/mobile/lib/firebase_options.dart
apps/mobile/android/app/google-services.json
apps/mobile/ios/Runner/GoogleService-Info.plist
.env
```

Ensure all of these are in `.gitignore`.
