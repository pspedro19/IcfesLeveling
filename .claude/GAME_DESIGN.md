# GAME_DESIGN.md — ICFES Leveling Game Design Document

> Documento de diseño de juego con todas las fórmulas, constantes, y mecánicas. Fuente de verdad para balanceo.

---

## 1. FILOSOFÍA DE DISEÑO

### 1.1 Pilares
1. **Aprendizaje efectivo** — Cada mecánica de juego debe contribuir al aprendizaje real.
2. **Engagement sostenible** — Dopamina controlada, no adictiva.
3. **Progresión justa** — No pay-to-win; premium = comodidad, no ventaja académica.
4. **Accesibilidad** — Funciona offline en zonas rurales colombianas.

### 1.2 Temática RPG
- Estética: Anime/Manhwa estilo Solo Leveling.
- Narrativa: "Cazadores" que suben de rango enfrentando desafíos académicos.
- 5 clases de héroe según personalidad de aprendizaje.

---

## 2. FÓRMULAS CORE (GameEngineService)

### 2.1 XP por Respuesta

```python
# Constantes (GameEngineService — fuente única de verdad)
XP_NEW_QUESTION = 10        # Primera vez respondiendo esta pregunta
XP_VALID_REVIEW = 5         # Repaso válido (pasó suficiente tiempo)
XP_INVALID_REPEAT = 0       # Repetición inválida (anti-gaming)

# Condiciones para ganar XP:
#   1. Respuesta CORRECTA
#   2. NO está en grace mode (hearts > 0)
#   3. NO es invalid_repeat

# Fórmula Core (GameEngineService.calculate_xp_for_answer):
total_xp = base_xp × streak_multiplier
# Donde base_xp = 10 (new), 5 (valid_review), o 0 (invalid_repeat)

# Bonus ADICIONAL solo en Practice Mode (practice_service.py):
speed_bonus = 5 if time < 10s else (3 if time < 20s else 0)
difficulty_multiplier = 1.0 + ((difficulty - 5) / 10.0)
practice_xp = (base_xp + speed_bonus + streak_bonus) × difficulty_multiplier

# NOTA: speed_bonus y difficulty_multiplier NO están en GameEngineService,
# son específicos de practice_service.py
```

### 2.2 Multiplicadores de Racha

```python
STREAK_MULTIPLIERS = {
    (1, 6):    1.0,   # Sin bonus
    (7, 13):   1.2,   # +20%
    (14, 29):  1.5,   # +50%
    (30, ∞):   2.0,   # +100% (máximo)
}

def get_streak_multiplier(days: int) -> float:
    if days >= 30: return 2.0
    if days >= 14: return 1.5
    if days >= 7:  return 1.2
    return 1.0
```

### 2.3 Cálculo de Nivel

```python
# XP necesario para alcanzar nivel N
def xp_for_level(level: int) -> int:
    return (level - 1) ** 2 * 100

# Nivel actual dado XP total
def level_for_xp(xp: int) -> int:
    return floor(sqrt(xp / 100)) + 1

# Tabla de referencia:
# Nivel 1:   0 XP        Nivel 10:  8,100 XP
# Nivel 2:   100 XP      Nivel 20:  36,100 XP
# Nivel 3:   400 XP      Nivel 30:  84,100 XP
# Nivel 5:   1,600 XP    Nivel 50:  240,100 XP
# Nivel 7:   3,600 XP    Nivel 100: 980,100 XP
```

### 2.4 Sistema de Rangos

```python
RANK_THRESHOLDS = {
    "E":   (1, 14),
    "D":   (15, 29),
    "C":   (30, 49),
    "B":   (50, 59),
    "A":   (60, 69),
    "S":   (70, 79),
    "SS":  (80, 89),
    "SSS": (90, ∞),
}
```

### 2.5 Cálculo de Daño (Combate)

```python
def calculate_damage(user, time_seconds, difficulty, combo_count, is_correct):
    if not is_correct:
        return 0

    base = (user.power + user.wisdom) * 2

    # Time multiplier (respuesta rápida = más daño)
    if time_seconds < 3:    time_mult = 2.0
    elif time_seconds < 10: time_mult = 1.5
    elif time_seconds < 20: time_mult = 1.2
    else:                   time_mult = 1.0

    diff_mult = 1 + (difficulty - 1) * 0.1
    combo_mult = 1 + (combo_count * 0.1)

    total = base * time_mult * diff_mult * combo_mult
    return max(1, int(total))  # Mínimo 1 de daño
```

### 2.6 Ganancia de Oro

```python
# Practice Mode
GOLD_PER_CORRECT = 10

# Battle Mode
def battle_gold(difficulty, time_seconds, is_correct):
    if not is_correct:
        return 1  # Consolación
    
    base = difficulty * 2
    critical = time_seconds < 3  # Critical hit
    return base * 2 if critical else base
```

---

## 3. SISTEMA DE CORAZONES

```python
HEARTS_DEFAULT = 5
HEARTS_MAX = 5
HEARTS_LOSS_PER_INCORRECT = 1
HEARTS_ADS_MAX_PER_DAY = 3
HEARTS_REGEN_INTERVAL = "30 minutes"  # Timer automático

# Grace Mode
# Se activa cuando hearts == 0
# En grace mode:
#   - Puede seguir jugando
#   - NO pierde más corazones
#   - NO gana XP
#   - NO gana gold
#   - Feedback: "Modo gracia — recupera corazones para ganar XP"
```

---

## 4. SISTEMA DE RACHA

```python
# Campos usuario
current_streak: int = 0       # Días consecutivos
longest_streak: int = 0       # Record personal
previous_streak: int = 0      # Racha antes de perderla
streak_lost_at: datetime      # Cuándo se perdió

# Activación
# Una "actividad válida" es:
#   - Completar al menos 1 pregunta correcta
#   - Alcanzar daily_goal_xp (default 20 XP)

# Streak Freeze
streak_freeze_count: int = 0
# Si no hay actividad en un día:
#   - Si freeze_count > 0: usar 1 freeze, mantener streak
#   - Si freeze_count == 0: streak = 0, guardar en previous_streak

# Meta Diaria
daily_goal_xp: int = 20  # Configurable por usuario (10, 20, 30, 50)
```

---

## 5. MASTERY Y REPETICIÓN ESPACIADA

### 5.1 Mastery Score

```python
# Umbrales con nombres
MASTERY_LEVELS = {
    "LOCKED":      0.0,
    "BEGINNER":    0.3,
    "DEVELOPING":  0.5,
    "PROFICIENT":  0.7,
    "MASTER":      0.9,
}

# Actualización por respuesta
LEARNING_RATE_CORRECT = 0.12    # +12% × (1.0 - current)
LEARNING_RATE_INCORRECT = 0.06  # -6% × current

def update_mastery(current: float, is_correct: bool) -> float:
    if is_correct:
        return current + LEARNING_RATE_CORRECT * (1.0 - current)
    else:
        return current - LEARNING_RATE_INCORRECT * current

# Decay (sin práctica)
DECAY_START_DAYS = 3        # Empieza después de 3 días
DECAY_RATE_PER_DAY = 0.02   # 2% por día
DECAY_MINIMUM = 0.1         # Nunca baja de 10%
DECAY_CAP_DAYS = 30          # Máximo 30 días de decay (60% total)

def apply_decay(current: float, days_inactive: int) -> float:
    if days_inactive <= DECAY_START_DAYS:
        return current
    decay_days = min(days_inactive - DECAY_START_DAYS, DECAY_CAP_DAYS)
    decayed = current - (decay_days * DECAY_RATE_PER_DAY)
    return max(DECAY_MINIMUM, decayed)

# Prerequisitos
PREREQUISITE_THRESHOLD = 0.6  # 60% mastery del tema anterior
```

### 5.2 Repetición Espaciada (SM-2 Mejorado)

```python
# Intervalos base por calidad de respuesta
INTERVALS = {
    "AGAIN": 1,   # Falló → 1 día
    "HARD":  2,   # Correcto con dificultad → 2 días
    "GOOD":  4,   # Correcto normal → 4 días
    "EASY":  7,   # Correcto fácil → 7 días
}

# Easiness factor
EF_INITIAL = 2.5
EF_MIN = 1.3
EF_MAX = 4.0

# Fórmula de nuevo intervalo
def next_interval(previous_interval, easiness_factor, quality):
    base = INTERVALS[quality]
    if previous_interval > 0:
        return int(previous_interval * easiness_factor)
    return base

# Prioridad de review
# 1. Días vencidos (high > medium > normal)
# 2. Mastery score (menor = mayor prioridad)
# 3. Easiness factor (menor = más difícil)
```

---

## 6. MODOS DE JUEGO — BALANCEO

### 6.1 Practice Mode

```python
PRACTICE_QUESTIONS = 15
PRACTICE_SELECTION = {
    "failed_questions": 0.60,  # 60% preguntas falladas
    "new_questions": 0.40,     # 40% preguntas nuevas
}
PRACTICE_LIFELINES = {
    "fifty_fifty": 1,  # Elimina 2 opciones (gratis)
    "ask_ai": 1,       # Pista AI (gratis)
    "skip": 1,         # Saltar sin penalidad (gratis)
}
```

### 6.2 Millionaire Mode

```python
MILLIONAIRE_QUESTIONS = 15
MILLIONAIRE_MAX_DAILY = 3
MILLIONAIRE_CHECKPOINTS = [5, 10, 15]
MILLIONAIRE_LIFELINES = {
    "fifty_fifty": {"cost": 0, "uses": 1},
    "ai_hint": {"cost": 50, "currency": "gold", "uses": 1},
    "skip": {"cost": 0, "uses": 1},
}
# Dificultad progresiva: pregunta N tiene difficulty ~= N
# Si pierde después de checkpoint, conserva rewards del checkpoint
```

### 6.3 Boss Raid

```python
BOSS_RAID_SCHEDULE = "Domingos 10:00-22:00 UTC-5"
BOSS_RAID_ENTRY_COST = 100  # gold
BOSS_RAID_QUESTIONS = 20
BOSS_RAID_HP = 10_000
BOSS_RAID_SUBJECT_RATIO = {
    "boss_subject": 0.70,  # 70% materia del boss
    "random": 0.30,        # 30% aleatorias
}
BOSS_RAID_XP_MULTIPLIER = 3  # 30 XP por correcta
BOSS_RAID_DAMAGE = {
    "base": 10,
    "combo_bonus": lambda combo: min(combo, 10) * 5,
}
BOSS_RAID_RANKS = {
    "S": {"threshold": 0.90, "gold": 500, "xp": 200, "title": "Cazador Legendario"},
    "A": {"threshold": 0.80, "gold": 300, "xp": 100, "title": "Cazador Elite"},
    "B": {"threshold": 0.70, "gold": 200, "xp": 50,  "title": None},
    "C": {"threshold": 0.00, "gold": 100, "xp": 0,   "title": None},
}
```

---

## 7. ECONOMÍA VIRTUAL

### 7.1 Fuentes de Ingreso

| Acción | Gold | Orbs | XP |
|---|---|---|---|
| Respuesta correcta (practice) | 10 | — | 10 + bonus |
| Respuesta correcta (battle) | difficulty×2 | difficulty×2 | 10 + bonus |
| Critical hit (<3s, battle) | difficulty×4 | difficulty×4 | 10 + bonus |
| Boss Raid correcta | — | — | 30 |
| Boss Raid rank S | 500 | — | 200 |
| Boss Raid rank A | 300 | — | 100 |
| Daily quest completada | variable | — | variable |
| Achievement desbloqueado | variable | — | variable |

### 7.2 Sumideros (Gastos)

| Item | Costo | Moneda |
|---|---|---|
| Boss Raid entrada | 100 | Gold |
| AI Hint (Millionaire) | 50 | Gold |
| Items tienda | variable | Gold/Orbs |
| Streak freeze | variable | Gold |
| Premium items | variable | Crystals |

### 7.3 Inflación Control
- XP cap: 500/hora.
- Gold por práctica: fijo 10 (no escala con nivel).
- Boss Raid: 1 vez por semana.
- Millionaire: 3 veces por día.
- Ads para corazones: 3/día.

---

## 8. ANTI-GAMING

### 8.1 Clasificación de Intentos

```python
def determine_attempt_type(user_id, question_id, topic_id):
    last = get_last_attempt(user_id, question_id)
    
    if not last:
        return "new"  # 10 XP
    
    mastery = get_mastery(user_id, topic_id)
    min_days = max(1, int(mastery * 7))
    # mastery 0.0 → 1 día
    # mastery 0.5 → 3 días
    # mastery 1.0 → 7 días
    
    days_since = (now() - last.created_at).days
    
    if days_since >= min_days:
        return "valid_review"    # 5 XP
    else:
        return "invalid_repeat"  # 0 XP
```

### 8.2 Protecciones

| Protección | Valor | Acción |
|---|---|---|
| Tiempo mínimo respuesta | 3 segundos | Rechazar request |
| Rate limiting | 60 req/min | HTTP 429 |
| Duplicados en sesión | Misma pregunta | Rechazar |
| XP cap por hora | 500 XP | Silencioso (no dar más XP) |
| Grace mode | 0 corazones | XP = 0 |

---

## 9. IRT 3PL

### 9.1 Modelo

```
P(θ) = c + (1 - c) / (1 + e^(-a(θ - b)))

a: discriminación (0.5 - 2.5)
b: dificultad (-2.0 a +2.0)
c: pseudo-adivinanza (0.0 - 0.25)
θ: habilidad del estudiante (-3.0 a +3.0)
```

### 9.2 Selección de Preguntas

```
I(θ) = a² × P(θ) × Q(θ) × [1 - c + c × Q(θ)]² / [1 - c]²

Seleccionar pregunta con máximo I(θ) en theta actual.
```

### 9.3 Conversiones

```
Theta → Rango:
  θ < -1.5:          E
  -1.5 ≤ θ < -0.5:   D
  -0.5 ≤ θ < +0.5:   C
  +0.5 ≤ θ < +1.0:   B
  +1.0 ≤ θ < +1.5:   A
  θ ≥ +1.5:           S

Theta → Percentil:
  percentil = clamp(norm.cdf(θ) × 100, 1, 99)
```

---

## 10. DOPAMINE ENGINE (Mobile)

```dart
Mecánicas de engagement psicológico:
  1. Variable Rewards    — Recompensas no predecibles
  2. Loss Aversion       — Miedo a perder racha
  3. Social Proof        — Leaderboard y ligas
  4. Immediate Feedback  — Animaciones instantáneas
  5. Combo System        — Visual a partir de combo >= 2
  6. Progress Visibility — Barras de mastery, XP, nivel
  7. Achievement Unlocks — Notificaciones de logros
```

---

## 11. LIGAS

```python
DIVISIONS = ["Bronce", "Plata", "Oro", "Platino", "Diamante", "Leyenda"]
GROUP_SIZE = 30  # Usuarios por grupo
METRIC = "weekly_xp"
PROMOTION_SLOTS = 5    # Top 5 asciende
RELEGATION_SLOTS = 5   # Bottom 5 desciende
SEASON = "weekly"       # Reset cada lunes
```
