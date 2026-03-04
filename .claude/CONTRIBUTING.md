# CONTRIBUTING.md — ICFES Leveling

> Guía para contribuidores del proyecto.

---

## 1. ANTES DE EMPEZAR

### Lectura Obligatoria
Antes de escribir código, lee estos documentos en orden:

1. **RULES.md** — Reglas no negociables del proyecto.
2. **SPEC.md** — Qué hace el sistema.
3. **ARCHITECTURE.md** — Por qué se tomaron las decisiones técnicas.
4. **CODING_STANDARDS.md** — Cómo escribir código en este proyecto.
5. **GAME_DESIGN.md** — Fórmulas y mecánicas de juego.

### Setup Local
```bash
git clone <repo>
cd icfes-leveling
cp .env.example .env
docker-compose up -d
# Verificar: curl http://localhost:4000/docs
```

---

## 2. FLUJO DE TRABAJO

### 2.1 Crear Feature

```bash
# 1. Actualizar develop
git checkout develop
git pull origin develop

# 2. Crear branch
git checkout -b feature/nombre-descriptivo

# 3. Desarrollar con commits atómicos
git add .
git commit -m "feat(backend): add daily reviews endpoint for spaced repetition"

# 4. Push
git push origin feature/nombre-descriptivo

# 5. Crear PR hacia develop
# - Título descriptivo
# - Descripción del cambio
# - Screenshots si hay cambios UI
# - Tests incluidos
```

### 2.2 Fix Bug

```bash
git checkout -b fix/descripcion-del-bug
# Desarrollar fix
git commit -m "fix(mobile): resolve race condition in offline sync"
# PR hacia develop
```

### 2.3 Hotfix (Producción)

```bash
git checkout -b hotfix/descripcion-urgente
# Desarrollar fix
git commit -m "fix(backend): patch XP overflow in boss raid"
# PR hacia main Y develop
```

---

## 3. COMMIT CONVENTIONS

### Formato
```
tipo(scope): descripción en imperativo

Cuerpo opcional explicando el "por qué".

Refs: #123
```

### Tipos
| Tipo | Uso |
|---|---|
| `feat` | Nueva funcionalidad |
| `fix` | Corrección de bug |
| `refactor` | Reestructuración sin cambio funcional |
| `docs` | Documentación |
| `test` | Tests |
| `chore` | Tareas de mantenimiento |
| `perf` | Mejoras de rendimiento |
| `ci` | CI/CD |
| `style` | Formato (no afecta lógica) |

### Scopes
`backend`, `mobile`, `ai`, `ws`, `db`, `docker`, `docs`, `api`

### Ejemplos
```
feat(backend): implement mastery decay system
fix(mobile): prevent double-tap on answer buttons
refactor(backend): consolidate XP logic into GameEngineService
docs(api): document boss raid endpoints
test(backend): add unit tests for IRT probability calculation
chore(docker): upgrade Redis to 7.2
perf(backend): add Redis cache to leaderboard queries
```

---

## 4. PULL REQUEST CHECKLIST

### Obligatorio
```
□ Branch actualizado con develop (no conflicts)
□ Código sigue CODING_STANDARDS.md
□ Type hints en todas las funciones (Python)
□ Null safety respetado (Dart)
□ Tests escritos para lógica nueva
□ Tests existentes pasando
□ Sin print() statements (usar logging)
□ Sin credenciales hardcodeadas
□ Sin TODO comments sin ticket asociado
```

### Si es Backend
```
□ Endpoint documentado con docstring
□ Pydantic schemas para request/response
□ Dependency injection para auth
□ Error handling con HTTPException
□ Migración Alembic incluida (si cambio de modelo)
□ Anti-gaming considerado
```

### Si es Mobile
```
□ Offline-first considerado
□ Widget con const constructor
□ Riverpod para estado (no setState directo)
□ Manejo de error/loading states
□ Responsive layout verificado
```

### Si Modifica Fórmulas
```
□ Cambio en GameEngineService (NO en otro lugar)
□ GAME_DESIGN.md actualizado
□ Unit tests para la nueva fórmula
□ Impacto en economía evaluado
```

---

## 5. DIRECTORIO DE ARCHIVOS CLAVE

Si necesitas modificar algo, estos son los archivos más importantes:

### Backend
| Para... | Editar... |
|---|---|
| Fórmulas de juego | `services/game_engine_service.py` |
| Nuevo endpoint | `routes/<tier>_<nombre>.py` |
| Nuevo modelo | `models/<nombre>.py` + `models/__init__.py` |
| Lógica de negocio | `services/<nombre>_service.py` |
| Configuración | `core/config.py` |
| Seguridad/Auth | `core/security.py` |
| Importar preguntas | `import_icfes_excel.py` |

### Mobile
| Para... | Editar... |
|---|---|
| Nueva pantalla | `features/<feature>/presentation/pages/` |
| Nuevo widget | `features/<feature>/presentation/widgets/` |
| Estado | `features/<feature>/presentation/providers/` |
| Navegación | `core/config/routes.dart` |
| Llamadas API | `features/<feature>/data/datasources/` |
| Tema visual | `core/theme/` |

### Infraestructura
| Para... | Editar... |
|---|---|
| Servicios Docker | `docker-compose.yml` |
| Migraciones BD | `database/migrations/` |
| Preguntas Excel | `database/allquestions/` |
| SQL inicial | `database/init/` |

---

## 6. COMUNICACIÓN

### Prioridades de Issue
| Label | Significado |
|---|---|
| `P0-critical` | Producción rota. Fix inmediato. |
| `P1-high` | Feature bloqueante. Esta semana. |
| `P2-medium` | Importante. Este sprint. |
| `P3-low` | Nice to have. Backlog. |

### Nomenclatura de Issues
```
[BACKEND] Descripción del problema
[MOBILE] Descripción del problema
[AI] Descripción del problema
[INFRA] Descripción del problema
[DOCS] Descripción del problema
```

---

## 7. REGLAS DE ORO

1. **GameEngineService es sagrado.** Toda fórmula va ahí. Sin excepciones.
2. **Offline-first no es opcional.** Todo feature mobile debe funcionar sin internet.
3. **Anti-gaming primero.** Antes de dar recompensas, verificar que no se explota.
4. **Tests para fórmulas.** Toda fórmula de XP/nivel/daño/mastery necesita test.
5. **No magic numbers.** Toda constante debe tener nombre descriptivo.
6. **Type hints siempre.** Python y Dart son tipados; úsalo.
7. **Documentar cambios.** Si cambias algo importante, actualiza los .md.
