# CODING_STANDARDS.md — ICFES Leveling

> Estándares de código obligatorios para backend (Python), mobile (Dart), y servicios auxiliares.

---

## 1. PYTHON (Backend + AI Service)

### 1.1 Estilo General
- **Python 3.11+** obligatorio.
- Formatter: **Black** (line length 88).
- Linter: **Ruff** o **flake8**.
- Import sorter: **isort** (compatible con Black).
- Type checker: **mypy** en modo estricto recomendado.

### 1.2 Type Hints
```python
# ✅ CORRECTO: Siempre type hints
async def get_user_mastery(user_id: UUID, topic_id: UUID) -> float:
    ...

def calculate_xp(base: int, multiplier: float, is_correct: bool) -> int:
    ...

# ❌ INCORRECTO: Sin type hints
async def get_user_mastery(user_id, topic_id):
    ...
```

### 1.3 Pydantic Schemas
```python
# ✅ CORRECTO: Pydantic v2 con model_config
class AnswerRequest(BaseModel):
    model_config = ConfigDict(strict=True)
    
    session_id: UUID
    question_id: UUID
    selected_answer: Literal["a", "b", "c", "d"]
    time_spent_seconds: int = Field(ge=0, le=600)

class AnswerResponse(BaseModel):
    is_correct: bool
    xp_earned: int
    gold_earned: int
    attempt_type: Literal["new", "valid_review", "invalid_repeat"]

# ❌ INCORRECTO: Dict sin tipado
def answer_question(data: dict) -> dict:
    ...
```

### 1.4 SQLAlchemy (Actualmente 1.x Query Style)
```python
# El codebase actualmente usa SQLAlchemy 1.x query style con Session sincrónica.
# Migración a 2.0 está pendiente.

# ✅ CORRECTO (actual): SQLAlchemy 1.x style
from sqlalchemy.orm import Session

def get_user(db: Session, user_id: UUID) -> User | None:
    return db.query(User).filter(User.id == user_id).first()

# Futuro (cuando se migre a 2.0):
# from sqlalchemy import select
# async def get_user(db: AsyncSession, user_id: UUID) -> User | None:
#     result = await db.execute(select(User).where(User.id == user_id))
#     return result.scalar_one_or_none()
```

### 1.5 Endpoints FastAPI
```python
# ✅ CORRECTO: Response model, status code, dependency injection
@router.post(
    "/practice/answer",
    response_model=AnswerResponse,
    status_code=status.HTTP_200_OK,
)
async def submit_answer(
    request: AnswerRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> AnswerResponse:
    return practice_service.process_answer(db, current_user, request)

# ❌ INCORRECTO: Sin response model, sin dependency injection
@router.post("/practice/answer")
async def submit_answer(request: dict):
    ...
```

### 1.6 Error Handling
```python
# ✅ CORRECTO: HTTPException con detalle
from fastapi import HTTPException, status

if user.hearts <= 0 and not user.is_grace_mode:
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="No hearts remaining. Wait for regeneration or watch an ad.",
    )

# ❌ INCORRECTO: Exception genérica o print
try:
    ...
except Exception as e:
    print(f"Error: {e}")  # NUNCA
    raise Exception("Something went wrong")  # NUNCA
```

### 1.7 Imports
```python
# ✅ CORRECTO: Relativos dentro del paquete app
from ..models.user import User
from ..services.game_engine_service import GameEngineService
from ..schemas.practice import AnswerRequest
from .config import settings
from .database import get_db

# ❌ INCORRECTO: Absolutos (no funcionan con la estructura actual)
from app.models.user import User
```

### 1.8 Docstrings
```python
# ✅ CORRECTO: Docstring en servicios públicos
async def process_answer(
    db: AsyncSession,
    user: User,
    request: AnswerRequest,
) -> AnswerResponse:
    """
    Process a practice answer submission.
    
    Validates anti-gaming rules, calculates XP/gold,
    updates mastery, and returns feedback.
    
    Raises:
        HTTPException 400: If session is not active or answer is duplicate.
        HTTPException 404: If question not found.
    """
    ...
```

### 1.9 Constantes
```python
# ✅ CORRECTO: Constantes en UPPER_SNAKE_CASE al inicio del archivo
XP_NEW_QUESTION = 10
XP_VALID_REVIEW = 5
XP_INVALID_REPEAT = 0
MAX_XP_PER_HOUR = 500

# ❌ INCORRECTO: Magic numbers en el código
if xp_earned > 500:  # ¿Qué es 500?
    ...
```

---

## 2. DART (Flutter Mobile)

### 2.1 Estilo General
- **Dart 3.x** con null safety estricto.
- Formatter: `dart format` (incluido en SDK).
- Linter: `flutter_lints` + reglas custom en `analysis_options.yaml`.
- Max 300 líneas por archivo.

### 2.2 Null Safety
```dart
// ✅ CORRECTO: Null-safe
final String? displayName = user.displayName;
final greeting = displayName ?? 'Cazador';

// ❌ INCORRECTO: Bang operator innecesario
final greeting = user.displayName!; // Puede crashear
```

### 2.3 Widgets
```dart
// ✅ CORRECTO: Const constructors, keys
class MasteryCard extends StatelessWidget {
  const MasteryCard({
    super.key,
    required this.topicName,
    required this.score,
  });

  final String topicName;
  final double score;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Column(
        children: [
          Text(topicName),
          LinearProgressIndicator(value: score),
        ],
      ),
    );
  }
}

// ❌ INCORRECTO: Sin const, sin key, lógica en build
class MasteryCard extends StatelessWidget {
  String topicName;  // No final
  double score;

  @override
  Widget build(BuildContext context) {
    // ❌ Lógica de negocio en build
    final level = score > 0.7 ? 'Master' : 'Beginner';
    ...
  }
}
```

### 2.4 Riverpod Providers
```dart
// ✅ CORRECTO: Provider con tipo explícito
final userProvider = FutureProvider<User>((ref) async {
  final api = ref.read(apiServiceProvider);
  return api.getCurrentUser();
});

final streakProvider = StateNotifierProvider<StreakNotifier, StreakState>((ref) {
  return StreakNotifier(ref.read(apiServiceProvider));
});

// ❌ INCORRECTO: Provider sin tipo
final userProvider = FutureProvider((ref) async {
  ...
});
```

### 2.5 Naming Conventions
```dart
// Archivos: snake_case.dart
practice_session_page.dart
game_engine_service.dart

// Clases: PascalCase
class PracticeSessionPage extends ConsumerWidget {}
class GameEngineService {}

// Variables/funciones: camelCase
final currentStreak = user.currentStreak;
void calculateDamage() {}

// Constantes: camelCase con k prefix o UPPER_SNAKE_CASE
const kMaxHearts = 5;
const Duration kAnimationDuration = Duration(milliseconds: 300);
```

### 2.6 Arquitectura por Feature
```
features/practice/
├── data/
│   ├── repositories/
│   │   └── practice_repository_impl.dart
│   ├── datasources/
│   │   ├── practice_remote_datasource.dart
│   │   └── practice_local_datasource.dart
│   └── models/
│       └── practice_answer_dto.dart
├── domain/
│   ├── entities/
│   │   └── practice_session.dart
│   ├── repositories/
│   │   └── practice_repository.dart
│   └── usecases/
│       └── submit_answer_usecase.dart
└── presentation/
    ├── pages/
    │   └── practice_session_page.dart
    ├── widgets/
    │   ├── question_card.dart
    │   └── feedback_overlay.dart
    └── providers/
        └── practice_providers.dart
```

---

## 3. SQL / DATABASE

### 3.1 Naming
```sql
-- Tablas: plural snake_case
users, questions, practice_sessions

-- Columnas: singular snake_case
user_id, created_at, mastery_score

-- Índices: idx_{tabla}_{columnas}
idx_questions_subject_id
idx_mastery_user_topic

-- Foreign keys: fk_{tabla}_{referencia}
fk_practice_answers_session_id
```

### 3.2 Migrations (Alembic)
```python
# ✅ CORRECTO: Migración descriptiva
"""Add mastery decay fields to topic_mastery

Revision ID: abc123
"""
def upgrade():
    op.add_column('topic_mastery', sa.Column('decay_applied_at', sa.DateTime(timezone=True)))

def downgrade():
    op.drop_column('topic_mastery', 'decay_applied_at')

# ❌ INCORRECTO: Migración sin downgrade o descripción
```

---

## 4. DOCKER / INFRA

### 4.1 Dockerfiles
- Multi-stage builds para producción.
- Non-root user.
- `.dockerignore` actualizado.
- Health checks en docker-compose.

### 4.2 Environment Variables
```bash
# ✅ CORRECTO: Nombre descriptivo, prefijado
DATABASE_URL=postgresql://user:pass@host:5432/db
JWT_SECRET=min-32-characters-long-secret-key
REDIS_URL=redis://redis:6379
OPENAI_API_KEY=sk-...

# ❌ INCORRECTO: Nombres ambiguos
DB=postgresql://...
SECRET=abc123  # Muy corto
KEY=sk-...     # ¿Qué key?
```

---

## 5. GIT

### 5.1 Commit Messages
```bash
# Formato: tipo(scope): descripción
feat(backend): add spaced repetition daily reviews endpoint
fix(mobile): resolve offline sync race condition
refactor(backend): consolidate XP calculation in GameEngineService
docs(api): update diagnostic endpoints documentation
test(backend): add anti-gaming unit tests
chore(docker): upgrade PostgreSQL to 16.2
perf(backend): add Redis cache to leaderboard queries

# Tipos permitidos:
# feat, fix, refactor, docs, test, chore, perf, ci, style
```

### 5.2 Branch Names
```bash
# Formato: tipo/descripción-corta
feature/boss-raid-leaderboard
fix/heart-regeneration-timer
refactor/game-engine-consolidation
```
