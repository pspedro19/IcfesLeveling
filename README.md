# 🎮 ICFES LEVELING - Videojuego Educativo MVP

Un videojuego RPG educativo inspirado en *Solo Leveling* para preparar el examen ICFES de Colombia. Los estudiantes combaten enemigos respondiendo preguntas académicas, ganan experiencia, suben de nivel y reciben explicaciones personalizadas de IA.

## 🚀 Características del MVP

### 🎯 Funcionalidades Principales
- **Sistema de Batallas**: Combate PvE con enemigos que representan preguntas académicas
- **Progresión RPG**: Niveles, experiencia, rangos (E a SSS), atributos (HP, MP, Poder, Sabiduría, Velocidad)
- **Economía del Juego**: Orbes (moneda soft), Cristales (moneda hard), ítems y equipamiento
- **Tutor IA**: Explicaciones personalizadas y planes de estudio con OpenAI
- **Misiones Diarias**: Sistema de quests para retención
- **Leaderboard**: Tabla de clasificación global
- **WebSocket en Tiempo Real**: Actualizaciones instantáneas de batallas

### 📚 Contenido Educativo
- **5 Materias**: Matemáticas, Lenguaje, Ciencias Naturales, Ciencias Sociales, Inglés
- **10 Temas**: Álgebra, Geometría, Comprensión Lectora, Física, etc.
- **10 Preguntas Sintéticas**: Con explicaciones y hints
- **Dificultad Adaptativa**: Basada en el rendimiento del estudiante

### 🏗️ Arquitectura Técnica
- **Frontend**: Next.js 14 + TypeScript + Tailwind CSS + Framer Motion
- **Backend**: FastAPI + SQLAlchemy + PostgreSQL
- **WebSocket**: Servicio dedicado para tiempo real
- **IA**: Servicio independiente con OpenAI + Redis cache
- **Base de Datos**: PostgreSQL + Redis + ClickHouse (analytics)
- **Orquestación**: Docker Compose

## 🛠️ Instalación y Configuración

### Prerrequisitos
- Docker y Docker Compose
- Git
- 4GB RAM mínimo
- Conexión a internet

### 1. Clonar el Repositorio
```bash
git clone <repository-url>
cd GAMEPLAY
```

### 2. Configurar Variables de Entorno
```bash
# Crear archivo .env en la raíz
cp .env.example .env

# Editar .env con tus configuraciones
OPENAI_API_KEY=tu_api_key_de_openai  # Opcional para desarrollo
```

### 3. Levantar el Sistema Completo
```bash
# Construir y levantar todos los servicios
docker-compose up --build -d

# Ver logs en tiempo real
docker-compose logs -f
```

### 4. Verificar que Todo Funcione
```bash
# Verificar servicios
docker-compose ps

# Verificar endpoints
curl http://localhost:8000/health  # Backend API
curl http://localhost:8002/health  # AI Service
```

## 🌐 Acceso a los Servicios

| Servicio | URL | Descripción |
|----------|-----|-------------|
| **Frontend** | http://localhost:3000 | Interfaz del videojuego |
| **Backend API** | http://localhost:8000 | API REST principal |
| **WebSocket** | ws://localhost:8001 | Conexiones en tiempo real |
| **AI Service** | http://localhost:8002 | Servicio de IA |
| **PostgreSQL** | localhost:5432 | Base de datos principal |
| **Redis** | localhost:6379 | Cache y sesiones |
| **ClickHouse** | localhost:8123 | Analytics |

## 🎮 Cómo Jugar

### 1. Registro e Inicio de Sesión
- Ve a http://localhost:3000
- Regístrate con un nuevo usuario
- Inicia sesión

### 2. Usuarios de Prueba Disponibles
```
Username: shadow_hunter
Password: password123
Level: 25, Rank: B

Username: math_master  
Password: password123
Level: 18, Rank: C

Username: newbie_student
Password: password123
Level: 1, Rank: E
```

### 3. Iniciar una Batalla
1. Ve al Dashboard
2. Selecciona "Iniciar Batalla"
3. Elige el tipo: Mazmorra, Torre, o PvP
4. Responde preguntas antes de que se agote el tiempo
5. Gana experiencia y orbes

### 4. Sistema de Combate
- **Tiempo**: 30 segundos por pregunta
- **Daño**: Basado en velocidad de respuesta y precisión
- **Críticos**: Respuestas correctas en < 3 segundos
- **Escudos**: Rachas de 3 aciertos protegen de un fallo

## 📊 Datos Sintéticos Incluidos

### Usuarios de Ejemplo
- 5 usuarios con diferentes niveles y progreso
- Stats completos (HP, MP, atributos, monedas)
- Historial de batallas

### Contenido Educativo
- 5 materias con colores y descripciones
- 10 temas con niveles de dificultad
- 10 preguntas con opciones, explicaciones y hints
- Power stats para análisis

### Sistema de Juego
- 5 ítems diferentes (pociones, equipamiento, mascotas)
- 5 misiones diarias activas
- Leaderboard con rankings
- Explicaciones de IA pre-generadas

## 🔧 Desarrollo

### Estructura del Proyecto
```
GAMEPLAY/
├── apps/
│   ├── frontend/          # Next.js 14
│   ├── backend/           # FastAPI
│   ├── websocket/         # WebSocket server
│   └── ai-service/        # AI service
├── database/
│   └── init/              # SQL initialization
├── docker-compose.yml     # Orquestación
└── README.md
```

### Comandos de Desarrollo
```bash
# Ver logs de un servicio específico
docker-compose logs -f frontend

# Reiniciar un servicio
docker-compose restart backend

# Ejecutar comandos dentro de un contenedor
docker-compose exec backend python -c "print('Hello from backend')"

# Ver estadísticas de uso
docker-compose stats
```

### Debugging
```bash
# Ver logs de todos los servicios
docker-compose logs

# Ver logs de errores
docker-compose logs --tail=100 | grep ERROR

# Verificar conectividad entre servicios
docker-compose exec backend ping postgres
docker-compose exec backend ping redis
```

## 🧪 Testing

### Endpoints de Prueba
```bash
# Health checks
curl http://localhost:8000/health
curl http://localhost:8002/health

# Obtener materias
curl http://localhost:8000/subjects

# Obtener leaderboard
curl http://localhost:8000/leaderboard

# Obtener preguntas aleatorias (requiere auth)
curl -H "Authorization: Bearer <token>" http://localhost:8000/questions/random
```

### Datos de Prueba
- Usuarios pre-creados con diferentes niveles
- Preguntas de todas las materias
- Batallas completadas para análisis
- Items y misiones activas

## 📈 Métricas y Monitoreo

### Logs Estructurados
Todos los servicios usan `structlog` para logs JSON:
```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "level": "info",
  "event": "battle_created",
  "battle_id": "uuid",
  "user_id": "uuid",
  "battle_type": "dungeon"
}
```

### Métricas Clave
- Tiempo de respuesta de API (< 150ms p95)
- Latencia WebSocket (< 50ms p95)
- Tasa de acierto por materia
- Retención diaria de usuarios
- Progresión de niveles

## 🔒 Seguridad

### Implementado
- JWT tokens con expiración
- Hashing de contraseñas con bcrypt
- CORS configurado
- Rate limiting básico
- Validación de entrada con Pydantic

### Para Producción
- HTTPS obligatorio
- Rate limiting avanzado
- Monitoreo de seguridad
- Backups automáticos
- Auditoría de logs

## 🚀 Próximos Pasos

### Roadmap Post-MVP
1. **Clanes y Raids Cooperativos**
2. **Mercado de Skins (cosmético)**
3. **Battle Royale Académico**
4. **App Móvil Nativa**
5. **Analytics Avanzados**
6. **Gamificación Social**

### Optimizaciones
- CDN para assets estáticos
- Edge caching con Vercel
- Optimización de consultas SQL
- Compresión de WebSocket
- Lazy loading de componentes

## 🤝 Contribución

### Estándares de Código
- TypeScript strict mode
- Black para Python
- ESLint + Prettier para JS/TS
- Conventional commits
- Tests unitarios obligatorios

### Flujo de Trabajo
1. Fork del repositorio
2. Crear feature branch
3. Implementar cambios
4. Agregar tests
5. Pull request con descripción detallada

## 📞 Soporte

### Problemas Comunes
```bash
# Puerto ya en uso
docker-compose down
docker system prune -f
docker-compose up --build

# Problemas de base de datos
docker-compose down -v
docker-compose up --build

# Problemas de memoria
docker-compose down
docker system prune -a
```

### Contacto
- Issues: GitHub Issues
- Documentación: `/docs`
- API Docs: http://localhost:8000/docs

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver `LICENSE` para más detalles.

---

**¡Disfruta aprendiendo mientras combates enemigos académicos! 🎓⚔️** 