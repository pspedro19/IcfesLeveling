# ICFES Leveling Platform

Sistema educativo gamificado para preparación de pruebas ICFES con IA, inspirado en Khan Academy, Coursera y Solo Leveling.

## Estado del Sistema

**Status**: ✅ 100% OPERACIONAL

- ✅ 1,058 preguntas con metadatos ICFES completos
- ✅ 193 videos educativos verificados y funcionando
- ✅ Sistema de recomendaciones con Claude AI
- ✅ Frontend con interfaz tipo Khan Academy
- ✅ Gamificación completa estilo Solo Leveling
- ✅ Sistema de progreso y persistencia

## Arquitectura

```
IcfesLeveling/
├── apps/
│   ├── backend/          # FastAPI + Python
│   │   ├── app/
│   │   │   ├── routes/   # Endpoints API
│   │   │   ├── models/   # Modelos SQLAlchemy
│   │   │   └── services/ # Lógica de negocio
│   │   └── requirements.txt
│   └── frontend/         # Next.js + React + TypeScript
│       ├── app/          # Páginas y componentes
│       ├── components/   # Componentes reutilizables
│       └── public/       # Assets estáticos
├── database/
│   ├── init/             # Scripts de inicialización SQL
│   └── seed_data/        # Datos de prueba y scripts Python
├── docker-compose.yml    # Configuración Docker
└── .env                  # Variables de entorno

```

## Stack Tecnológico

### Backend
- **Framework**: FastAPI (Python 3.11+)
- **Base de Datos**: PostgreSQL 15
- **ORM**: SQLAlchemy
- **Cache**: Redis
- **IA**: Claude AI API (Anthropic)
- **Autenticación**: JWT

### Frontend
- **Framework**: Next.js 14 (App Router)
- **UI**: React + TypeScript
- **Estilos**: TailwindCSS + Framer Motion
- **Estado**: React Context API
- **Multimedia**: YouTube Player API

### DevOps
- **Contenedores**: Docker + Docker Compose
- **Proxy**: Nginx
- **Monitoreo**: Logs centralizados

## Inicio Rápido

### Prerrequisitos

- Docker y Docker Compose instalados
- Git
- Puertos disponibles: 3002 (Frontend), 4000 (Backend), 5433 (PostgreSQL)

### Instalación y Despliegue

```bash
# 1. Clonar repositorio
git clone https://github.com/pspedro19/IcfesLeveling.git
cd IcfesLeveling

# 2. El archivo .env ya está configurado y listo para usar
# (Opcionalmente puedes editarlo si necesitas cambiar credenciales)

# 3. Levantar todos los servicios
docker-compose up -d

# 4. Esperar a que se complete la inicialización (2-3 minutos)
# Puedes monitorear el progreso con:
docker-compose logs -f

# 5. Verificar que todos los servicios estén healthy
docker-compose ps
```

### Servicios Disponibles

Una vez levantados, los servicios estarán disponibles en:

| Servicio | URL | Descripción |
|----------|-----|-------------|
| **Frontend** | http://localhost:4001 | Interfaz de usuario principal |
| **Backend API** | http://localhost:4000 | API REST (FastAPI) |
| **API Docs** | http://localhost:4000/docs | Documentación interactiva Swagger |
| **PgAdmin** | http://localhost:5050 | Administrador de PostgreSQL |
| **WebSocket** | ws://localhost:8001 | Servidor WebSocket en tiempo real |
| **AI Service** | http://localhost:8000 | Servicio de IA (Claude) |

### Verificación del Sistema

```bash
# Verificar estado de todos los servicios (deben mostrar "healthy")
docker-compose ps

# Verificar salud del backend
curl http://localhost:4000/health

# Verificar base de datos
docker exec icfes_postgres psql -U gameplay -d gameplay_db -c "SELECT COUNT(*) FROM questions;"
# Debería mostrar: 1058 preguntas

# Verificar videos en catálogo
docker exec icfes_postgres psql -U gameplay -d gameplay_db -c "SELECT COUNT(*) FROM youtube_catalog;"
# Debería mostrar: 193 videos

# Ver logs de un servicio específico
docker-compose logs -f backend    # Backend logs
docker-compose logs -f frontend   # Frontend logs
```

### Detener y Reiniciar Servicios

```bash
# Detener todos los servicios
docker-compose down

# Reiniciar todos los servicios
docker-compose restart

# Reiniciar un servicio específico
docker-compose restart backend
docker-compose restart frontend

# Reconstruir y levantar (si hay cambios en código)
docker-compose up -d --build
```

### Acceso por Defecto

**Credenciales de PgAdmin:**
- Email: `admin@icfes.com`
- Contraseña: `admin123`

**Base de datos PostgreSQL:**
- Host: `postgres`
- Puerto: `5432` (interno) / `5433` (externo)
- Usuario: `gameplay`
- Contraseña: `gameplay123`
- Base de datos: `gameplay_db`

### Solución de Problemas

**Si un servicio no inicia correctamente:**

```bash
# Ver logs del servicio problemático
docker-compose logs backend

# Reiniciar el servicio
docker-compose restart backend

# Si persiste, reconstruir
docker-compose up -d --build backend
```

**Si el frontend muestra errores de compilación:**

```bash
# Limpiar caché y reconstruir
docker-compose down
docker volume prune -f
docker-compose up -d --build frontend
```

**Si la base de datos no tiene datos:**

```bash
# Verificar que la inicialización se completó
docker-compose logs postgres | grep "database system is ready"

# Si es necesario, reiniciar servicios
docker-compose restart postgres
sleep 10
docker-compose restart backend
```

## Características Principales

### 1. Sistema de Diagnóstico Adaptativo

- Test inicial de 20 preguntas por materia
- Selección inteligente basada en competencias ICFES
- Análisis de resultados con IA
- Identificación de áreas débiles
- Asignación de rango (E → S)

**URL**: `/diagnostic-test`

### 2. Recomendaciones con Claude AI

- Análisis de preguntas falladas
- Cruce con catálogo de 193 videos verificados
- Generación de plan de estudio personalizado
- Organización en unidades por prioridad
- Justificación pedagógica de cada video

**URL**: `/claude-study-plan`

### 3. Interfaz Khan Academy

- Videos organizados por unidades
- Barra de progreso visual
- Sistema de XP por video completado
- Thumbnails automáticos de YouTube
- Reproductor seguro con manejo de errores

### 4. Gamificación Solo Leveling

- **Sistema de Rangos**: E → D → C → B → A → S → SS → SSS
- **Experiencia (XP)**: Por actividades completadas
- **Clases de Héroe**: Mago, Guerrero, Asesino, Tanque
- **Estadísticas**: HP, MP, Power, Wisdom, Speed, Resistance
- **Monedas**: Credits y Gems
- **Logros**: Sistema de achievements

### 5. Dashboard de Estudiante

- Estadísticas personales
- Historial de tests
- Progreso por materia
- Racha de estudio
- Próximos objetivos

**URL**: `/student-dashboard`

## API Endpoints

### Autenticación

```
POST /api/v1/auth/login              # Login
POST /api/v1/auth/register           # Registro
GET  /api/v1/auth/me                 # Usuario actual
```

### Diagnóstico

```
GET  /api/v1/diagnostic/test-questions/{subject_id}    # Obtener preguntas
POST /api/v1/diagnostic/submit                         # Enviar respuestas
GET  /api/v1/diagnostic/results/{test_id}             # Ver resultados
```

### Recomendaciones

```
POST /api/v1/intelligent-recommendations/generate      # Generar plan con Claude AI
GET  /api/v1/intelligent-recommendations/{plan_id}    # Obtener plan
POST /api/v1/intelligent-recommendations/complete     # Marcar video completado
```

### Contenido

```
GET  /api/v1/subjects                           # Listar materias
GET  /api/v1/subjects/{subject_id}/topics      # Temas por materia
GET  /api/v1/questions/search                  # Buscar preguntas
```

Ver documentación completa en: http://localhost:3001/docs

## Base de Datos

### Tablas Principales

- **users**: Usuarios del sistema
- **subjects**: Materias (Matemáticas, Lectura, Ciencias, etc.)
- **topics**: Temas por materia
- **questions**: Preguntas con metadatos ICFES
- **diagnostic_tests**: Tests diagnósticos
- **diagnostic_test_answers**: Respuestas de tests
- **youtube_catalog**: Catálogo de videos educativos
- **ai_study_plans**: Planes generados por Claude AI
- **study_plan_progress**: Progreso de estudiantes

### Metadatos ICFES en Preguntas

Cada pregunta incluye:
- `competencia`: Competencia ICFES evaluada
- `componente`: Componente específico
- `afirmacion`: Afirmación que evalúa
- `evidencia`: Evidencia de aprendizaje
- `clave_respuesta`: Respuesta correcta

Esto permite matching inteligente con videos relevantes.

## Sistema de Videos

### Catálogo Verificado

- **193 videos activos** con IDs válidos de YouTube
- **11 videos inactivos** detectados automáticamente
- Organización por:
  - Materia ICFES
  - Competencia
  - Componente
  - Nivel de dificultad

### Canales Educativos

- Khan Academy en Español
- Educatina
- Matemáticas profe Alex
- Ciencia para todos
- Y más...

### SafeYouTubePlayer

Componente React que:
- Detecta videos no disponibles
- Muestra mensaje explicativo
- Ofrece alternativas
- Reporta errores al backend

## Flujo de Usuario Completo

### 1. Registro/Login
```
/login → /student-dashboard
```

### 2. Diagnóstico
```
/diagnostic-test → Seleccionar materia → Responder 20 preguntas → /diagnostic-test/results
```

### 3. Recomendaciones IA
```
/diagnostic-test/results → "Generar Plan" → Claude AI analiza → /claude-study-plan
```

### 4. Estudio
```
/claude-study-plan → Ver videos por unidad → Completar videos → Ganar XP → Subir de nivel
```

### 5. Progreso
```
/student-dashboard → Ver estadísticas → Próximo diagnóstico → Mejora continua
```

## Configuración

### Variables de Entorno (.env)

```env
# Base de Datos
DATABASE_URL=postgresql://postgres:postgres123@postgres:5432/icfes_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres123
POSTGRES_DB=icfes_db

# Backend
BACKEND_PORT=3001
FRONTEND_URL=http://localhost:3002

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:3001
NEXT_PUBLIC_WS_URL=ws://localhost:3001

# Claude AI
ANTHROPIC_API_KEY=tu_api_key_aqui

# Redis
REDIS_URL=redis://redis:6379

# JWT
SECRET_KEY=tu_secret_key_seguro
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
```

### Puerto Personalizado

Para cambiar puertos, editar `docker-compose.yml`:

```yaml
services:
  frontend:
    ports:
      - "3002:3000"  # Cambiar 3002 por el puerto deseado

  backend:
    ports:
      - "3001:8000"  # Cambiar 3001 por el puerto deseado
```

## Desarrollo

### Backend Local

```bash
cd apps/backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Frontend Local

```bash
cd apps/frontend
npm install
npm run dev
```

### Base de Datos Local

```bash
# Conectar a PostgreSQL
docker exec -it icfes_postgres psql -U postgres -d icfes_db

# Ejecutar queries
SELECT COUNT(*) FROM questions;
SELECT * FROM subjects;
```

## Scripts Útiles

### Importar Preguntas desde Excel

```bash
docker exec icfes_backend python /app/database/init/97-comprehensive-data-loader.py
```

### Limpiar Videos Inválidos

```bash
docker exec icfes_backend python /app/database/seed_data/clean_fake_videos_final.py
```

### Verificar Estado del Sistema

```bash
docker exec icfes_backend python /app/database/seed_data/check_database_status.py
```

### Actualizar Metadatos ICFES

```bash
docker exec icfes_backend python /app/database/seed_data/update_icfes_fields.py
```

## Resolución de Problemas

### Error: Puerto ya en uso

```bash
# Cambiar puertos en docker-compose.yml
# O detener servicio que usa el puerto
sudo lsof -i :3002  # Ver qué usa el puerto
sudo kill -9 <PID>  # Matar proceso
```

### Error: Base de datos no inicializa

```bash
# Ver logs
docker-compose logs postgres

# Reiniciar desde cero
docker-compose down -v
docker-compose up -d
```

### Error: Frontend no conecta con Backend

```bash
# Verificar NEXT_PUBLIC_API_URL en .env
# Verificar CORS en backend
# Reiniciar servicios
docker-compose restart backend frontend
```

### Error: Videos no cargan

```bash
# Verificar catálogo
docker exec icfes_postgres psql -U postgres -d icfes_db -c "SELECT COUNT(*) FROM youtube_catalog WHERE is_active = true;"

# Limpiar videos inválidos
docker exec icfes_backend python /app/database/seed_data/clean_fake_videos_final.py
```

## Contribución

### Estructura de Commits

```
feat: Nueva característica
fix: Corrección de bug
docs: Documentación
style: Formato de código
refactor: Refactorización
test: Tests
chore: Mantenimiento
```

### Pull Requests

1. Fork del repositorio
2. Crear rama: `git checkout -b feature/nueva-funcionalidad`
3. Commit: `git commit -m "feat: agregar nueva funcionalidad"`
4. Push: `git push origin feature/nueva-funcionalidad`
5. Crear Pull Request

## Testing

```bash
# Backend tests
cd apps/backend
pytest

# Frontend tests
cd apps/frontend
npm test

# E2E tests
npm run test:e2e
```

## Deployment

### Producción con Docker

```bash
# Build para producción
docker-compose -f docker-compose.prod.yml up -d

# Variables de entorno de producción
cp .env.example .env.prod
# Editar .env.prod con valores reales
```

### Servicios en la Nube

- **Backend**: AWS ECS, Google Cloud Run, Railway
- **Frontend**: Vercel, Netlify, AWS Amplify
- **Base de Datos**: AWS RDS, Google Cloud SQL
- **Cache**: AWS ElastiCache, Redis Cloud
- **CDN**: Cloudflare, AWS CloudFront

## Licencia

MIT License - Ver LICENSE file

## Soporte

- **Issues**: GitHub Issues
- **Documentación**: `/docs` en este repositorio
- **API Docs**: http://localhost:3001/docs

## Roadmap

### Fase 1 (Completado)
- ✅ Sistema de diagnóstico
- ✅ Recomendaciones con IA
- ✅ Catálogo de videos
- ✅ Gamificación básica

### Fase 2 (En Progreso)
- [ ] Sistema de battles PvP
- [ ] Marketplace de items
- [ ] Foro de estudiantes
- [ ] App móvil

### Fase 3 (Futuro)
- [ ] Certificaciones oficiales
- [ ] Integración con instituciones
- [ ] Analytics avanzado con ML
- [ ] Realidad aumentada

## Créditos

Desarrollado con:
- FastAPI (Backend)
- Next.js (Frontend)
- PostgreSQL (Database)
- Claude AI (Recomendaciones)
- YouTube API (Videos educativos)

Inspirado en Khan Academy, Coursera y Solo Leveling.

---

**Estado**: ✅ Sistema completo y funcional - Listo para producción

**Última actualización**: 2025-10-21
