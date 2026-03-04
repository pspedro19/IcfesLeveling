# DATA_MODELS.md — ICFES Leveling Data Models

> Especificación completa de los 140+ modelos de datos del sistema.

---

## CONVENCIONES

- **Primary Keys:** UUID v4 (NO autoincrement).
- **Timestamps:** `created_at`, `updated_at` con timezone (UTC).
- **Soft Deletes:** `deleted_at: DateTime | null` donde aplique.
- **Naming:** snake_case para columnas y tablas.
- **ORM:** SQLAlchemy 2.0 declarative style.
- **Migrations:** Alembic (NUNCA raw DDL).

---

## 1. CORE MODELS

### User
```
users
├── id: UUID (PK)
├── username: String(50), unique, not null
├── email: String(255), unique, not null
├── hashed_password: String(255), not null
├── display_name: String(100)
├── is_active: Boolean = true
├── is_admin: Boolean = false
│
├── # RPG Stats
├── level: Integer = 1
├── experience: Integer = 0
├── rank: String(10) = "E"          # E, D, C, B, A, S, SS, SSS
├── hp: Integer = 100
├── mp: Integer = 50
├── power: Integer = 10
├── wisdom: Integer = 10
├── speed: Integer = 10
│
├── # Economía
├── gold: Integer = 1000
├── orbs: Integer = 0
├── crystals: Integer = 0
│
├── # Racha
├── current_streak: Integer = 0
├── longest_streak: Integer = 0
├── previous_streak: Integer = 0
├── streak_lost_at: DateTime(tz)
├── last_activity_date: Date
├── daily_goal_xp: Integer = 20
├── streak_freeze_count: Integer = 0
│
├── # Corazones
├── hearts: Integer = 5
├── max_hearts: Integer = 5
├── hearts_last_regeneration: DateTime(tz)
├── unlimited_hearts_until: DateTime(tz)
│
├── # Ads
├── ads_watched_today: Integer = 0
├── ads_watched_date: Date
│
├── # Onboarding
├── onboarding_completed: Boolean = false
├── onboarding_preferences: JSON     # {goal, level, subjects, time}
├── projected_icfes_score: Integer   # 0-500
│
├── # Premium
├── premium_plan: String = "free"    # free, basic, premium, elite
├── premium_expires_at: DateTime(tz)
│
├── created_at: DateTime(tz)
└── updated_at: DateTime(tz)
```

### Subject
```
subjects
├── id: UUID (PK)
├── name: String(100), unique       # Matematicas, Lenguaje, etc.
├── description: Text
├── icon_url: String(500)
├── color: String(7)                # Hex color
├── order: Integer                  # Display order
├── is_active: Boolean = true
├── created_at: DateTime(tz)
└── updated_at: DateTime(tz)
```

### Topic
```
topics
├── id: UUID (PK)
├── subject_id: UUID (FK subjects)
├── name: String(200), not null
├── description: Text
├── order: Integer
├── prerequisite_topic_id: UUID (FK topics, nullable)
├── is_active: Boolean = true
├── created_at: DateTime(tz)
└── updated_at: DateTime(tz)
```

### Question
```
questions
├── id: UUID (PK)
├── topic_id: UUID (FK topics)
├── subject_id: UUID (FK subjects)
│
├── # Contenido (sistema dual)
├── pregunta_texto: Text
├── pregunta_imagen: String(500)
├── opcion_a_texto: Text
├── opcion_a_imagen: String(500)
├── opcion_b_texto: Text
├── opcion_b_imagen: String(500)
├── opcion_c_texto: Text
├── opcion_c_imagen: String(500)
├── opcion_d_texto: Text
├── opcion_d_imagen: String(500)
├── respuesta_correcta: String(1)   # a, b, c, d
│
├── # Legacy fields
├── question_text: Text
├── options: JSON
├── correct_answer: String(10)
├── explanation: Text
├── hint: Text
│
├── # Dificultad
├── difficulty: Integer              # 1-10
│
├── # Parámetros IRT
├── parametro_irt_a: Float = 1.0     # Discriminación (0.5-2.5)
├── parametro_irt_b: Float = 0.0     # Dificultad (-2 a +2)
├── parametro_irt_c: Float = 0.25    # Pseudo-adivinanza (0-0.25)
│
├── # Metadata ICFES
├── competencia: String(255)
├── componente: String(100)
├── proceso_cognitivo: String(50)
├── afirmacion: Text
├── evidencia: Text
│
├── # Gamificación
├── puntos_xp: Integer = 10
├── tags: ARRAY(String)
├── power_stats: JSON
│
├── created_at: DateTime(tz)
│
│   # NOTA: Los siguientes campos están comentados en el modelo actual
│   # (no existen en la tabla):
│   # is_active, updated_at, usage_count, average_response_time,
│   # last_used_at, image_url, options_images, validation_errors,
│   # is_validated, distractor_*_concepto, frecuencia_error_*,
│   # pista_1/2/3, explicacion_respuesta, error_comun

Índices (implícitos por FK):
  - idx_questions_subject: (subject_id)
  - idx_questions_topic: (topic_id)
```

---

## 2. GAMIFICATION MODELS

### Battle / BattleAnswer
```
battles
├── id: UUID (PK)
├── user_id: UUID (FK users)
├── opponent_id: UUID (FK users, nullable)   # null = PvE
├── status: String        # pending, active, completed
├── winner_id: UUID (FK users, nullable)
├── user_hp: Integer
├── opponent_hp: Integer
├── created_at / updated_at

battle_answers
├── id: UUID (PK)
├── battle_id: UUID (FK battles)
├── user_id: UUID (FK users)
├── question_id: UUID (FK questions)
├── selected_answer: String(1)
├── is_correct: Boolean
├── damage_dealt: Integer
├── time_spent_seconds: Integer
├── created_at
```

### Boss Raid Models
```
bosses
├── id: UUID (PK)
├── name: String(100)
├── subject_id: UUID (FK subjects)
├── hp: Integer = 10000
├── image_url: String(500)
├── active_from: DateTime(tz)
├── active_until: DateTime(tz)

boss_raid_sessions
├── id: UUID (PK)
├── boss_id: UUID (FK bosses)
├── user_id: UUID (FK users)
├── score: Integer = 0
├── damage_dealt: Integer = 0
├── combo_max: Integer = 0
├── rank: String(1)              # S, A, B, C
├── status: String               # active, completed
├── created_at / completed_at

boss_raid_answers
├── id: UUID (PK)
├── session_id: UUID (FK boss_raid_sessions)
├── question_id: UUID (FK questions)
├── selected_answer: String(1)
├── is_correct: Boolean
├── damage: Integer
├── combo_count: Integer
├── time_spent_seconds: Integer

boss_raid_leaderboard
├── id: UUID (PK)
├── boss_id: UUID (FK bosses)
├── user_id: UUID (FK users)
├── total_damage: Integer
├── rank: Integer
```

### Dungeon Models
```
dungeon_gates
├── id, name, min_level, subject_id, difficulty, rewards_json

dungeon_runs
├── id, gate_id, user_id, status, score, started_at, completed_at

dungeon_encounters
├── id, run_id, monster_id, question_id, result, damage

dungeon_monsters
├── id, name, hp, damage, image_url, rewards_json
```

### Shadow Army Models
```
shadow_soldiers, shadow_formations, shadow_battles,
shadow_extractions, shadow_abilities, user_shadow_stats
```

### Items / Inventory
```
items
├── id, name, description, type, rarity, price, currency, effects_json, image_url

user_items
├── id, user_id, item_id, quantity, equipped, acquired_at
```

### Quests
```
quest_templates
├── id, name, description, type, requirements_json, rewards_json

daily_quests
├── id, template_id, date, is_active

user_quests
├── id, user_id, quest_id, progress, completed, completed_at

quest_rewards
├── id, quest_id, reward_type, amount
```

### Achievements
```
achievements
├── id, name, description, icon, category, requirement_json, reward_json

user_achievements
├── id, user_id, achievement_id, unlocked_at, progress
```

### Guilds
```
guilds
├── id, name, description, leader_id, level, xp, max_members

guild_members
├── id, guild_id, user_id, role, joined_at
```

---

## 3. LEARNING MODELS

### Practice Session
```
practice_sessions
├── id: UUID (PK)
├── user_id: UUID (FK users)
├── subject_id: UUID (FK subjects, nullable)
├── total_questions: Integer
├── correct_answers: Integer
├── xp_earned: Integer
├── gold_earned: Integer
├── started_at: DateTime(tz)
├── completed_at: DateTime(tz)
├── status: String               # active, completed, abandoned

practice_answers
├── id: UUID (PK)
├── session_id: UUID (FK practice_sessions)
├── question_id: UUID (FK questions)
├── selected_answer: String(1)
├── is_correct: Boolean
├── xp_earned: Integer
├── attempt_type: String          # new, valid_review, invalid_repeat
├── time_spent_seconds: Integer
├── created_at: DateTime(tz)

user_question_mastery
├── id: UUID (PK)
├── user_id: UUID (FK users)
├── question_id: UUID (FK questions)
├── total_attempts: Integer = 0
├── mastery_level: Float = 0.0    # 0.0 - 1.0
├── created_at / updated_at

practice_rewards
├── id: UUID (PK)
├── practice_session_id: UUID (FK practice_sessions)
├── user_id: UUID (FK users)
├── reward_type: String            # xp, gold, item, streak_bonus
├── reward_data: JSON              # {amount, item_id, multiplier}
├── created_at

Índices:
  - idx_question_mastery_user: (user_id, question_id) UNIQUE
  - idx_practice_rewards_session: (practice_session_id)
```

### Diagnostic
```
diagnostic_tests
├── id, user_id, type (quick/deep), subject_id, status, started_at, completed_at

diagnostic_test_answers
├── id, test_id, question_id, selected_answer, is_correct, time_spent

diagnostic_test_results
├── id, test_id, user_id, overall_rank, theta, standard_error,
│   percentile, subject_scores_json, weak_areas_json

diagnostic_error_patterns
├── id, test_id, subject_id, error_type, frequency, details_json
```

### Two-Phase Diagnostic
```
two_phase_diagnostics
├── id: UUID (PK)
├── user_id: UUID (FK users)
├── diagnostic_type: String        # quick, deep, monthly
├── subject_id: UUID (FK subjects)
├── status: String                 # pending, in_progress, completed
├── created_at / updated_at

two_phase_diagnostic_answers
├── id: UUID (PK)
├── diagnostic_id: UUID (FK two_phase_diagnostics)
├── question_id: UUID (FK questions)
├── answer_id: String(1)
├── was_correct: Boolean
├── created_at

user_engagement
├── id: UUID (PK)
├── user_id: UUID (FK users), unique
├── hearts: Integer = 5
├── grace_mode_active: Boolean = false
├── current_streak: Integer = 0
├── created_at / updated_at

question_attempts
├── id: UUID (PK)
├── user_id: UUID (FK users)
├── question_id: UUID (FK questions)
├── topic_id: UUID (FK topics)
├── was_correct: Boolean
├── attempt_type: String           # diagnostic, practice, review
├── created_at

topic_mastery (via TwoPhase)
├── id: UUID (PK)
├── user_id: UUID (FK users)
├── topic_id: UUID (FK topics)
├── mastery_score: Float = 0.0
├── questions_seen: Integer = 0
├── created_at / updated_at

Índices:
  - idx_twophase_user: (user_id)
  - idx_twophase_answers_diag: (diagnostic_id)
  - idx_engagement_user: (user_id) UNIQUE
  - idx_attempts_user_question: (user_id, question_id)
```

### Mastery
```
topic_mastery
├── id: UUID (PK)
├── user_id: UUID (FK users)
├── topic_id: UUID (FK topics)
├── mastery_score: Float = 0.0     # 0.0 - 1.0
├── total_attempts: Integer = 0
├── correct_attempts: Integer = 0
├── last_practiced_at: DateTime(tz)
├── next_review_at: DateTime(tz)
├── easiness_factor: Float = 2.5
├── interval_days: Integer = 1
├── created_at / updated_at

Índices:
  - idx_mastery_user_topic: (user_id, topic_id) UNIQUE
  - idx_mastery_next_review: (next_review_at)
```

### Study Plans
```
study_plans
├── id, user_id, subject_id, title, type (basic/adaptive/ai),
│   content_json, total_units, current_unit, progress, is_active

plan_progress
├── id, plan_id, unit_number, progress, completed_at
```

---

## 4. ECONOMY & SOCIAL MODELS

### Payments
```
subscriptions
├── id, user_id, plan, status, started_at, expires_at, gateway

payments
├── id, user_id, subscription_id, amount, currency, status, gateway,
│   gateway_reference, created_at

invoices
├── id, payment_id, invoice_number, amount, pdf_url

coupons
├── id, code, discount_type, discount_value, max_uses, used_count,
│   valid_from, valid_until

coupon_usages
├── id, coupon_id, user_id, used_at
```

### Transactions
```
gold_transactions
├── id, user_id, amount, type (earn/spend), source, reference_id, created_at

xp_transactions
├── id, user_id, amount, source, reference_id, multiplier, created_at

currency_earnings
├── id: UUID (PK)
├── user_id: UUID (FK users)
├── currency_type: String          # gold, orbs, crystals
├── amount: Integer
├── source: String                 # practice, battle, quest, ad, purchase
├── created_at
```

### Store / Virtual Economy
```
store_transactions
├── id: UUID (PK)
├── user_id: UUID (FK users)
├── item_id: UUID (FK items)
├── transaction_type: String       # purchase, refund, gift
├── amount_spent: Integer
├── created_at

user_power_ups
├── id: UUID (PK)
├── user_id: UUID (FK users)
├── item_id: UUID (FK items)
├── is_active: Boolean = false
├── expires_at: DateTime(tz)
├── created_at

Índices:
  - idx_store_tx_user: (user_id)
  - idx_powerups_user_active: (user_id, is_active)
```

### Leagues
```
league_divisions
├── id: UUID (PK)
├── name: String(50)               # Bronze, Silver, Gold, Diamond, Champion
├── tier: Integer                  # 1-5
├── color_hex: String(7)           # #CD7F32, #C0C0C0, etc.
├── promotion_spots: Integer = 5
├── icon_url: String(500)
├── min_xp: Integer
├── order: Integer

league_weeks
├── id: UUID (PK)
├── week_number: Integer
├── year: Integer
├── week_start: DateTime(tz)
├── week_end: DateTime(tz)
├── is_active: Boolean = false

league_groups
├── id: UUID (PK)
├── league_week_id: UUID (FK league_weeks)
├── division_id: UUID (FK league_divisions)
├── group_number: Integer
├── max_members: Integer = 30

user_leagues
├── id: UUID (PK)
├── user_id: UUID (FK users)
├── league_group_id: UUID (FK league_groups)
├── weekly_xp: Integer = 0
├── current_rank: Integer

user_league_history
├── id: UUID (PK)
├── user_id: UUID (FK users)
├── league_week_id: UUID (FK league_weeks)
├── division_id: UUID (FK league_divisions)
├── final_rank: Integer
├── promoted: Boolean = false
├── relegated: Boolean = false

Índices:
  - idx_league_group_week: (league_week_id, division_id)
  - idx_user_league_group: (league_group_id, weekly_xp DESC)
  - idx_league_history_user: (user_id, league_week_id)
```

### Notifications
```
notifications
├── id, user_id, type, title, body, data_json, read, created_at

notification_history
├── id: UUID (PK)
├── user_id: UUID (FK users)
├── notification_type: String      # streak_reminder, league_update, achievement, system
├── title: String(200)
├── body: Text
├── sent_at: DateTime(tz)
├── read_at: DateTime(tz, nullable)

user_device_tokens
├── id: UUID (PK)
├── user_id: UUID (FK users)
├── device_token: String(500)
├── platform: String(20)           # android, ios, web
├── is_active: Boolean = true
├── created_at / updated_at

Índices:
  - idx_notif_history_user: (user_id, sent_at DESC)
  - idx_device_tokens_user: (user_id, is_active)
```

---

## 5. AUTH MODELS

```
revoked_tokens
├── id, jti: String (unique), revoked_at

refresh_tokens
├── id, user_id, token_hash, expires_at, created_at, revoked_at
```

---

## 6. MOBILE/OFFLINE MODELS

```
user_question_history
├── id, user_id, question_id, selected_answer, is_correct,
│   time_spent, attempt_type, session_type, created_at

pending_answer_sync
├── id, user_id, question_id, answer_data_json, created_at, synced_at

heart_transactions
├── id, user_id, amount, type (lose/recover/ad/premium), created_at

user_daily_activity
├── id, user_id, date, xp_earned, questions_answered,
│   correct_answers, time_spent_minutes, goal_met

streak_freezes
├── id, user_id, used_date, source (earned/purchased)

daily_challenges
├── id: UUID (PK)
├── challenge_date: Date
├── title: String(200)
├── challenge_type: String         # answer_count, accuracy, speed, streak
├── target_value: Integer          # e.g., 10 questions, 80% accuracy
├── reward_data: JSON
├── is_active: Boolean = true
├── created_at

user_daily_challenges
├── id: UUID (PK)
├── user_id: UUID (FK users)
├── challenge_id: UUID (FK daily_challenges)
├── current_progress: Integer = 0
├── is_completed: Boolean = false
├── completed_at: DateTime(tz, nullable)
├── created_at

Índices:
  - idx_daily_challenges_date: (challenge_date, is_active)
  - idx_user_challenges_user: (user_id, challenge_id) UNIQUE
  - idx_pending_sync_user: (user_id, synced_at)
```

---

## 7. TRAINING ZONE MODELS

```
training_zones
├── id: UUID (PK)
├── user_id: UUID (FK users)
├── subject_id: UUID (FK subjects)
├── current_month: Integer         # 1-12
├── preferred_mode: String         # practice, timed, review
├── daily_goal_questions: Integer = 10
├── created_at / updated_at

training_zone_questions
├── id: UUID (PK)
├── training_zone_id: UUID (FK training_zones)
├── question_id: UUID (FK questions)
├── user_id: UUID (FK users)
├── source_diagnostic_id: UUID (FK diagnostic_tests, nullable)
├── priority: Integer = 0
├── created_at

training_sessions
├── id: UUID (PK)
├── training_zone_id: UUID (FK training_zones)
├── user_id: UUID (FK users)
├── mode: String                   # practice, timed, review, adaptive
├── status: String                 # active, completed, abandoned
├── session_accuracy: Float = 0.0
├── total_questions: Integer = 0
├── correct_answers: Integer = 0
├── started_at: DateTime(tz)
├── completed_at: DateTime(tz, nullable)

training_attempts
├── id: UUID (PK)
├── training_session_id: UUID (FK training_sessions)
├── training_question_id: UUID (FK training_zone_questions)
├── question_id: UUID (FK questions)
├── user_id: UUID (FK users)
├── selected_answer: String(1)
├── is_correct: Boolean
├── time_spent_seconds: Integer
├── created_at

training_ai_explanations
├── id: UUID (PK)
├── training_attempt_id: UUID (FK training_attempts)
├── question_id: UUID (FK questions)
├── user_id: UUID (FK users)
├── explanation_text: Text
├── model_used: String(50)
├── created_at

training_video_recommendations
├── id: UUID (PK)
├── training_question_id: UUID (FK training_zone_questions)
├── youtube_video_id: UUID (FK youtube_videos, nullable)
├── relevance_score: Float = 0.0
├── created_at

monthly_training_reports
├── id: UUID (PK)
├── user_id: UUID (FK users)
├── subject_id: UUID (FK subjects)
├── report_month: Integer          # 1-12
├── report_year: Integer
├── total_sessions: Integer = 0
├── total_questions: Integer = 0
├── average_accuracy: Float = 0.0
├── mastery_delta: Float = 0.0
├── created_at

Índices:
  - idx_training_zone_user_subject: (user_id, subject_id) UNIQUE
  - idx_training_questions_zone: (training_zone_id)
  - idx_training_sessions_zone: (training_zone_id, status)
  - idx_training_attempts_session: (training_session_id)
  - idx_monthly_reports_user: (user_id, report_year, report_month)
```

---

## 8. VIDEO SYSTEM MODELS

```
youtube_catalog
├── id: UUID (PK)
├── uuid: UUID, unique
├── youtube_id: String(20)         # YouTube video ID
├── title: String(500)
├── codigo_tema: String(50)
├── area_evaluada: String(100)
├── duration_seconds: Integer
├── created_at / updated_at

video_stats
├── video_id: UUID (PK, FK youtube_catalog)
├── ctr_7d: Float = 0.0           # Click-through rate last 7 days
├── completion_rate_7d: Float = 0.0
├── total_views: Integer = 0
├── updated_at

student_video_interactions
├── id: UUID (PK)
├── student_id: UUID (FK users)
├── video_id: UUID (FK youtube_catalog)
├── total_watch_seconds: Integer = 0
├── improvement_delta: Float = 0.0
├── last_watched_at: DateTime(tz)
├── created_at

video_tracking
├── id: UUID (PK)
├── user_id: UUID (FK users)
├── plan_id: UUID (FK study_plans, nullable)
├── unit_number: Integer
├── youtube_url: String(500)
├── watch_percentage: Float = 0.0
├── completed: Boolean = false
├── created_at / updated_at

youtube_videos
├── id: UUID (PK)
├── video_id: String(20)           # YouTube video ID
├── title: String(500)
├── subject: String(100)
├── topic: String(200)
├── quality_score: Float = 0.0
├── created_at

youtube_links
├── id: UUID (PK)
├── codigo_tema: String(50)
├── area_evaluada: String(100)
├── tema_principal: String(200)
├── youtube_url: String(500)
├── estado: String                 # active, inactive, broken
├── created_at / updated_at

question_video_recommendations
├── id: UUID (PK)
├── uuid: UUID, unique
├── question_id: UUID (FK questions)
├── video_id: UUID (FK youtube_catalog)
├── total_score: Float = 0.0       # Combined relevance score
├── created_at

Índices:
  - idx_youtube_catalog_id: (youtube_id) UNIQUE
  - idx_video_stats_ctr: (ctr_7d DESC)
  - idx_student_video_student: (student_id, video_id) UNIQUE
  - idx_video_tracking_user_plan: (user_id, plan_id)
  - idx_youtube_links_tema: (codigo_tema)
  - idx_question_video_rec: (question_id, total_score DESC)
```

---

## 9. ERROR / SYSTEM HEALTH MODELS

```
error_logs
├── id: UUID (PK)
├── error_id: String, unique
├── endpoint: String(500)
├── method: String(10)             # GET, POST, PUT, DELETE
├── error_type: String(100)        # ValueError, TimeoutError, etc.
├── error_message: Text
├── stack_trace: Text
├── user_id: UUID (FK users, nullable)
├── created_at

error_patterns
├── id: UUID (PK)
├── pattern_id: String, unique
├── endpoint_pattern: String(500)
├── error_type_pattern: String(100)
├── occurrence_count: Integer = 0
├── first_seen: DateTime(tz)
├── last_seen: DateTime(tz)
├── is_resolved: Boolean = false

system_health
├── id: UUID (PK)
├── health_id: String, unique
├── service_name: String(100)      # database, redis, ai-service, etc.
├── status: String                 # healthy, degraded, down
├── response_time_avg: Float       # ms
├── checked_at: DateTime(tz)

recovery_actions
├── id: UUID (PK)
├── action_id: String, unique
├── action_type: String(100)       # restart, cache_clear, reconnect
├── target_service: String(100)
├── execution_status: String       # pending, running, completed, failed
├── triggered_at: DateTime(tz)
├── completed_at: DateTime(tz, nullable)

Índices:
  - idx_error_logs_endpoint: (endpoint, created_at DESC)
  - idx_error_patterns_type: (error_type_pattern, occurrence_count DESC)
  - idx_system_health_service: (service_name, checked_at DESC)
  - idx_recovery_actions_status: (execution_status, triggered_at DESC)
```

---

## RELACIONES CLAVE

```
# Core Learning
User ──< PracticeSession ──< PracticeAnswer >── Question
User ──< PracticeSession ──< PracticeReward
User ──< UserQuestionMastery >── Question
User ──< DiagnosticTest ──< DiagnosticTestAnswer >── Question
User ──< TopicMastery >── Topic >── Subject
User ──< StudyPlan ──< PlanProgress
Question >── Topic >── Subject

# Two-Phase Diagnostic
User ──< TwoPhaseDiagnostic ──< TwoPhaseDiagnosticAnswer >── Question
User ──  UserEngagement
User ──< QuestionAttempt >── Question
User ──< QuestionAttempt >── Topic

# Training Zone
User ──< TrainingZone >── Subject
TrainingZone ──< TrainingZoneQuestion >── Question
TrainingZone ──< TrainingSession ──< TrainingAttempt >── Question
TrainingAttempt ──< TrainingAIExplanation
TrainingZoneQuestion ──< TrainingVideoRecommendation >── YoutubeVideo
User ──< MonthlyTrainingReport >── Subject

# Gamification
User ──< Battle ──< BattleAnswer >── Question
User ──< BossRaidSession ──< BossRaidAnswer >── Question
User ──< DungeonRun ──< DungeonEncounter >── Question
User ──< UserItem >── Item
User ──< UserPowerUp >── Item
User ──< UserQuest >── DailyQuest >── QuestTemplate
User ──< UserAchievement >── Achievement
User ──< GuildMember >── Guild

# Economy & Social
User ──< Subscription ──< Payment
User ──< GoldTransaction
User ──< XPTransaction
User ──< CurrencyEarning
User ──< StoreTransaction >── Item
User ──< HeartTransaction

# Leagues & Challenges
User ──< UserLeague >── LeagueGroup >── LeagueWeek
LeagueGroup >── LeagueDivision
User ──< UserLeagueHistory >── LeagueWeek
User ──< UserDailyChallenge >── DailyChallenge

# Mobile/Offline & Notifications
User ──< UserDailyActivity
User ──< PendingAnswerSync
User ──< UserDeviceToken
User ──< NotificationHistory

# Video System
YoutubeCatalog ──  VideoStats
User ──< StudentVideoInteraction >── YoutubeCatalog
User ──< VideoTracking >── StudyPlan
Question ──< QuestionVideoRecommendation >── YoutubeCatalog
YoutubeLink ── (codigo_tema) ── Topic

# System Health
ErrorLog >── User (optional)
ErrorPattern ── (tracks) ── ErrorLog
SystemHealth ── (monitors) ── Service
RecoveryAction ── (targets) ── Service
```
