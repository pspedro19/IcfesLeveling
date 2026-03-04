# API_SPEC.md — ICFES Leveling API Reference

> Especificacion completa de todos los endpoints del backend.

---

## BASE URL

```
Desarrollo: http://localhost:4000/api/v1
Produccion: https://api.icfesleveling.com/api/v1
```

## AUTENTICACION

Todos los endpoints protegidos requieren header:
```
Authorization: Bearer <access_token>
```

---

## TIER 1: ESSENTIAL

### Auth

| Metodo | Endpoint | Descripcion | Auth |
|---|---|---|---|
| POST | `/auth/register` | Registro con email/password | No |
| POST | `/auth/login` | Login -> access_token + refresh_token | No |
| POST | `/auth/refresh` | Renovar access_token con refresh_token | No |
| POST | `/auth/logout` | Revocar tokens | Si |
| POST | `/auth/social/google` | Login con Google (Firebase) | No |
| POST | `/auth/social/apple` | Login con Apple (Firebase) | No |
| GET | `/auth/me` | Perfil del usuario actual | Si |

**Register Request:**
```json
{
  "username": "string (3-50 chars, unique)",
  "email": "string (valid email, unique)",
  "password": "string (min 8 chars)",
  "display_name": "string (optional, max 100)"
}
```

**Login Response:**
```json
{
  "access_token": "string (JWT, 30 min)",
  "refresh_token": "string (JWT, 7 dias)",
  "token_type": "bearer",
  "user": { "id": "uuid", "username": "string", "level": 1, "rank": "E", ... }
}
```

### Questions

| Metodo | Endpoint | Descripcion | Auth |
|---|---|---|---|
| GET | `/questions/` | Listar preguntas (paginated) | Si |
| GET | `/questions/{id}` | Pregunta por ID | Si |
| GET | `/questions/by-subject/{subject_id}` | Preguntas por materia | Si |
| GET | `/questions/by-topic/{topic_id}` | Preguntas por tema | Si |
| GET | `/questions/adaptive` | Siguiente pregunta adaptativa (IRT) | Si |

**Adaptive Query Params:**
```
?subject_id=uuid          # Materia (opcional)
&exclude_ids=uuid,uuid    # Excluir preguntas ya respondidas
&difficulty_range=1,10    # Rango de dificultad
```

### Answers

| Metodo | Endpoint | Descripcion | Auth |
|---|---|---|---|
| POST | `/answers/submit` | Enviar respuesta con anti-gaming XP | Si |
| GET | `/answers/xp-preview/{question_id}` | Preview XP potencial antes de responder | Si |
| GET | `/answers/history` | Historial de respuestas (paginado) | Si |
| GET | `/answers/mastery/topics` | Mastery scores por todos los temas | Si |

**Submit Answer Request:**
```json
{
  "question_id": "uuid",
  "answer_id": "a|b|c|d",
  "time_spent_seconds": 15,
  "session_type": "practice|boss_raid|diagnostic",
  "session_id": "uuid (optional)"
}
```

**Submit Answer Response:**
```json
{
  "correct": true,
  "correct_answer_id": "b",
  "explanation": "string or null",
  "attempt_type": "new|valid_review|invalid_repeat",
  "xp_earned": 15,
  "xp_multiplier": 1.2,
  "hearts_remaining": 4,
  "in_grace_mode": false,
  "mastery_update": { "topic_id": "string", "old_score": 0.3, "new_score": 0.45 },
  "streak_update": { "current": 5, "extended": false, "daily_goal_met": true }
}
```

### Hearts

| Metodo | Endpoint | Descripcion | Auth |
|---|---|---|---|
| GET | `/hearts/status` | Estado actual de corazones (hearts, max, regen timer) | Si |
| POST | `/hearts/use` | Usar un corazon (reason + source_id) | Si |
| POST | `/hearts/refill` | Recargar corazones (method: gems, ad, gold) | Si |
| GET | `/hearts/grace-status` | Estado de Grace Mode | Si |
| POST | `/hearts/enter-grace-mode` | Entrar a Grace Mode (sin XP, sin corazones) | Si |
| POST | `/hearts/exit-grace-mode` | Salir de Grace Mode | Si |
| POST | `/hearts/restore-with-ad` | Restaurar 1 corazon por ad (max 3/dia) | Si |
| POST | `/hearts/refill-with-gold` | Recargar todos los corazones (150 gold) | Si |
| POST | `/hearts/grace-mode/enter` | Entrar Grace Mode (ruta alternativa) | Si |
| POST | `/hearts/grace-mode/exit` | Salir Grace Mode (ruta alternativa) | Si |
| POST | `/hearts/refill-verified` | Refill con verificacion server-side de AdMob | Si |
| POST | `/hearts/callback/admob` | Callback endpoint para AdMob SSV | No |

### Streak

| Metodo | Endpoint | Descripcion | Auth |
|---|---|---|---|
| GET | `/streaks/status` | Estado de racha (current, longest, multiplier, can_repair) | Si |
| POST | `/streaks/extend` | Registrar XP ganado y extender racha si daily goal met | Si |
| POST | `/streaks/check` | Check y update streak basado en XP earned | Si |
| POST | `/streaks/buy-freeze` | Comprar streak freeze (200 gold, max 5) | Si |
| POST | `/streaks/repair` | Reparar racha perdida (24h window, 300 gold o ad) | Si |
| POST | `/streaks/freeze` | Usar streak freeze (item o gold) | Si |

**Streak Multipliers:**
- 1-6 dias: 1.0x
- 7-13 dias: 1.2x
- 14-29 dias: 1.3x
- 30-59 dias: 1.5x
- 60+ dias: 1.8x

### Mobile API (Offline-First)

| Metodo | Endpoint | Descripcion | Auth |
|---|---|---|---|
| GET | `/mobile/questions/next` | Siguiente pregunta adaptativa para mobile | Si |
| GET | `/mobile/questions/batch` | Batch de preguntas para cache offline (max 100) | Si |
| POST | `/mobile/answers/submit` | Enviar respuesta desde mobile | Si |
| POST | `/mobile/sync/answers` | Sincronizar respuestas offline | Si |
| POST | `/mobile/sync/state` | Reconciliar estado cliente/servidor | Si |
| GET | `/mobile/sync/status` | Estado actual de sincronizacion | Si |
| GET | `/mobile/hearts/status` | Estado corazones (mobile) | Si |
| POST | `/mobile/hearts/use` | Usar corazon (mobile) | Si |
| POST | `/mobile/hearts/refill` | Recargar corazones (mobile) | Si |
| GET | `/mobile/streak/status` | Estado racha (mobile) | Si |
| POST | `/mobile/streak/extend` | Extender racha (mobile) | Si |
| POST | `/mobile/streak/freeze` | Usar streak freeze (mobile) | Si |
| POST | `/mobile/streak/repair` | Reparar racha (mobile) | Si |
| GET | `/mobile/mastery/topics` | Mastery por temas (mobile) | Si |
| GET | `/mobile/mastery/weak-areas` | Areas debiles (mobile) | Si |
| GET | `/mobile/leagues/current` | Liga actual (mobile) | Si |
| GET | `/mobile/leagues/leaderboard` | Leaderboard liga (mobile) | Si |
| POST | `/mobile/leagues/join` | Unirse a liga (mobile) | Si |
| GET | `/mobile/leagues/history` | Historial ligas (mobile) | Si |
| POST | `/mobile/notifications/register` | Registrar device token (mobile) | Si |
| PUT | `/mobile/notifications/preferences` | Actualizar preferencias de notificaciones | Si |

### Onboarding

| Metodo | Endpoint | Descripcion | Auth |
|---|---|---|---|
| POST | `/onboarding/preferences` | Guardar preferencias de onboarding (Steps 2-5) | Si |
| GET | `/onboarding/preferences` | Obtener preferencias de onboarding actuales | Si |
| GET | `/onboarding/status` | Estado y proximo paso del onboarding | Si |

---

## TIER 2: GAMIFICATION

### Economy

| Metodo | Endpoint | Descripcion | Auth |
|---|---|---|---|
| GET | `/economy/balance` | Gold y gems del usuario | Si |
| GET | `/economy/status` | Estado economico completo (gold, orbs, crystals, XP, level, rank) | Si |
| GET | `/economy/shop` | Items disponibles en tienda con precios | Si |
| GET | `/economy/items/{item_id}` | Detalle de un item especifico | Si |
| GET | `/economy/prices` | Referencia rapida de precios | Si |
| POST | `/economy/purchase` | Comprar item (gold o gems) | Si |
| POST | `/economy/earn` | Otorgar moneda (quest, achievement, etc.) | Si |
| GET | `/economy/transactions/gold` | Historial transacciones de gold (paginado) | Si |
| POST | `/economy/gold/add` | Agregar gold con tracking de transaccion | Si |
| POST | `/economy/gold/spend` | Gastar gold con tracking de transaccion | Si |
| POST | `/economy/xp/add` | Agregar XP con logica de level-up | Si |
| POST | `/economy/rank/update` | Actualizar rank basado en mastery percentage | Si |

**Shop Categories:** STREAK, BOOST, HEARTS, AVATAR, TITLE, THEME, BUNDLE, SPECIAL

### Achievements

| Metodo | Endpoint | Descripcion | Auth |
|---|---|---|---|
| GET | `/achievements/` | Todos los logros | Si |
| GET | `/achievements/unlocked` | Logros desbloqueados | Si |

### Leaderboard

| Metodo | Endpoint | Descripcion | Auth |
|---|---|---|---|
| GET | `/leaderboard/global` | Top 50 global | Si |
| GET | `/leaderboard/weekly` | Top 50 semanal | Si |
| GET | `/leaderboard/subject/{id}` | Top por materia | Si |
| GET | `/leaderboard/boss-raid` | Top Boss Raid | Si |

### Practice (Millonario Mode)

| Metodo | Endpoint | Descripcion | Auth |
|---|---|---|---|
| POST | `/practice/start` | Iniciar sesion de practica (practice, failed_questions, boss_battle) | Si |
| GET | `/practice/history/me` | Historial de sesiones de practica | Si |
| GET | `/practice/{session_id}` | Estado actual de la sesion | Si |
| GET | `/practice/{session_id}/question` | Obtener pregunta actual | Si |
| POST | `/practice/{session_id}/answer` | Responder pregunta de la sesion | Si |
| POST | `/practice/{session_id}/lifeline/fifty-fifty` | Usar comodin 50/50 (1 por sesion) | Si |
| POST | `/practice/{session_id}/lifeline/ask-ai` | Usar comodin IA (pista, 1 por sesion) | Si |
| POST | `/practice/{session_id}/lifeline/skip` | Saltar pregunta (1 por sesion) | Si |
| POST | `/practice/{session_id}/complete` | Finalizar sesion y obtener resultados | Si |

**Start Request:**
```json
{
  "session_type": "practice|failed_questions|boss_battle",
  "subject_id": "uuid (optional)",
  "topic_id": "uuid (optional)",
  "difficulty": 5,
  "max_questions": 15
}
```

### Battles

| Metodo | Endpoint | Descripcion | Auth |
|---|---|---|---|
| POST | `/battles/` | Crear batalla PvP | Si |
| POST | `/battles/{id}/answer` | Responder en batalla | Si |
| GET | `/battles/history` | Historial batallas | Si |

### Quests

| Metodo | Endpoint | Descripcion | Auth |
|---|---|---|---|
| GET | `/quests/daily` | Misiones diarias activas con progreso | Si |
| POST | `/quests/{quest_id}/complete` | Completar mision y recibir recompensa | Si |
| GET | `/quests/progress` | Progreso general de quests | Si |
| POST | `/quests/update-progress` | Actualizar progreso (quest_type + value) | Si |

### Notifications

| Metodo | Endpoint | Descripcion | Auth |
|---|---|---|---|
| POST | `/notifications/register` | Registrar device token FCM | Si |
| DELETE | `/notifications/unregister` | Desregistrar device token | Si |
| GET | `/notifications/preferences` | Obtener preferencias de notificacion | Si |
| PUT | `/notifications/preferences` | Actualizar preferencias de notificacion | Si |
| GET | `/notifications/devices` | Dispositivos registrados del usuario | Si |
| POST | `/notifications/test` | Enviar notificacion de prueba | Si |

**Notification Preferences:**
- streak_reminder_6pm, streak_reminder_9pm, streak_reminder_330am
- hearts_refilled, league_updates, boss_raid_starting
- quiet_hours_start, quiet_hours_end

---

## TIER 3: DIAGNOSTIC

### Two-Phase Diagnostic (IRT-Based)

#### Quick Diagnostic (15 preguntas, 3 por materia)

| Metodo | Endpoint | Descripcion | Auth |
|---|---|---|---|
| POST | `/diagnostic/quick/start` | Iniciar diagnostico rapido | Si |
| POST | `/diagnostic/quick/submit` | Enviar respuestas diagnostico rapido | Si |
| POST | `/diagnostic/quick/submit-irt` | Enviar con analisis IRT completo (theta, SE, percentile) | Si |

#### Deep Diagnostic (15-20 preguntas por materia)

| Metodo | Endpoint | Descripcion | Auth |
|---|---|---|---|
| POST | `/diagnostic/deep/start/{subject_id}` | Iniciar diagnostico profundo por materia | Si |
| POST | `/diagnostic/deep/submit` | Enviar respuestas diagnostico profundo | Si |

#### Adaptive Diagnostic (Seleccion adaptativa por IRT)

| Metodo | Endpoint | Descripcion | Auth |
|---|---|---|---|
| POST | `/diagnostic/adaptive/next-question` | Siguiente pregunta optima (Fisher information) | Si |
| POST | `/diagnostic/adaptive/submit-answer` | Enviar respuesta y obtener theta actualizado | Si |
| POST | `/diagnostic/adaptive/batch-questions` | Batch de preguntas ordenadas por informacion | Si |

#### IRT Calculation

| Metodo | Endpoint | Descripcion | Auth |
|---|---|---|---|
| GET | `/diagnostic/irt/calculate-theta` | Recalcular theta desde respuestas almacenadas | Si |

**Quick Diagnostic Result:**
```json
{
  "completed": true,
  "correct": 10,
  "total": 15,
  "rank": "C",
  "theta": 0.15,
  "weak_areas": [
    { "subject": "Lenguaje", "score": 0.33, "priority": "HIGH" }
  ]
}
```

**IRT-Enhanced Result (submit-irt):**
```json
{
  "irt_metrics": {
    "theta_estimate": 0.15,
    "standard_error": 0.45,
    "confidence_interval_95": [-0.73, 1.03],
    "percentile": 56,
    "theta_progression": [{"question": 1, "theta": 0.0, "se": 1.0}],
    "subject_abilities": { "math_uuid": { "theta": 0.3, "se": 0.5 } }
  }
}
```

### Diagnostic Public (No Auth)

| Metodo | Endpoint | Descripcion | Auth |
|---|---|---|---|
| GET | `/diagnostic-public/subjects` | Materias disponibles para diagnostico publico | No |
| POST | `/diagnostic-public/start` | Iniciar diagnostico publico | No |
| POST | `/diagnostic-public/answer` | Enviar respuesta individual | No |
| POST | `/diagnostic-public/complete` | Completar diagnostico publico | No |

### Monthly Reassessment

| Metodo | Endpoint | Descripcion | Auth |
|---|---|---|---|
| GET | `/monthly-reassessment/eligibility/{subject_id}` | Verificar elegibilidad para reevaluacion | Si |
| POST | `/monthly-reassessment/create` | Crear reevaluacion mensual | Si |
| GET | `/monthly-reassessment/{test_id}/questions` | Obtener preguntas de reevaluacion | Si |
| POST | `/monthly-reassessment/{test_id}/submit` | Enviar respuestas de reevaluacion | Si |
| GET | `/monthly-reassessment/user-reassessments` | Todas las reevaluaciones del usuario | Si |
| GET | `/monthly-reassessment/summary/{subject_id}` | Resumen de reevaluaciones por materia | Si |
| GET | `/monthly-reassessment/available-subjects` | Materias disponibles para reevaluacion | Si |
| GET | `/monthly-reassessment/config/{subject_name}` | Configuracion de reevaluacion por materia | No |

### Verified Image Diagnostic

| Metodo | Endpoint | Descripcion | Auth |
|---|---|---|---|
| GET | `/verified-image-diagnostic/subjects` | Materias con preguntas de imagenes verificadas | No |
| GET | `/verified-image-diagnostic/questions/{subject_id}` | Preguntas verificadas para diagnostico (max 20) | No |
| GET | `/verified-image-diagnostic/test-summary` | Resumen de disponibilidad de test | No |
| POST | `/verified-image-diagnostic/refresh-cache` | Forzar refresh del cache de verificacion | No |

---

## TIER 4: STUDY PLANS & RECOMMENDATIONS

### Study Plans

| Metodo | Endpoint | Descripcion | Auth |
|---|---|---|---|
| POST | `/study-plans/generate/{subject_id}` | Plan basico por materia | Si |
| POST | `/study-plans/generate-adaptive` | Plan adaptativo integrado con catalogo ICFES | Si |
| POST | `/study-plans/generate-ai-comprehensive` | Plan AI personalizado completo | Si |
| GET | `/study-plans/` | Todos los planes del usuario | Si |
| GET | `/study-plans/current` | Plan activo actual del usuario | Si |
| GET | `/study-plans/{plan_id}` | Detalle completo de un plan | Si |
| GET | `/study-plans/plans/{plan_id}` | Alias: detalle de plan | Si |
| GET | `/study-plans/{plan_id}/adaptive` | Alias: plan adaptativo | Si |
| POST | `/study-plans/{plan_id}/units/{unit_number}/progress` | Actualizar progreso de unidad | Si |
| POST | `/study-plans/plans/{plan_id}/progress` | Alias: actualizar progreso | Si |
| POST | `/study-plans/plans/{plan_id}/weighted-progress` | Progreso ponderado (videos, exercises, readings) | Si |
| GET | `/study-plans/plans/{plan_id}/statistics` | Estadisticas del plan | Si |
| POST | `/study-plans/{plan_id}/complete` | Marcar plan como completado | Si |
| DELETE | `/study-plans/{plan_id}` | Eliminar plan (marcar inactivo) | Si |
| GET | `/study-plans/recommendations/{subject_id}` | Recomendaciones de estudio por materia | Si |
| GET | `/study-plans/real-time-progress` | Progreso en tiempo real (orbs, rank, units) | Si |
| GET | `/study-plans/subjects/available` | Materias disponibles para generar planes | Si |

### Spaced Repetition (SM-2)

| Metodo | Endpoint | Descripcion | Auth |
|---|---|---|---|
| POST | `/spaced-repetition/schedule` | Crear horario de repaso espaciado para plan | Si |
| GET | `/spaced-repetition/daily-reviews` | Items de repaso del dia (ordenados por prioridad) | Si |
| POST | `/spaced-repetition/review/{item_id}` | Enviar resultado de revision (again/hard/good/easy) | Si |
| GET | `/spaced-repetition/analytics` | Analiticas de retencion (curvas de olvido) | Si |
| GET | `/spaced-repetition/stats` | Estadisticas generales del usuario | Si |
| GET | `/spaced-repetition/due-count` | Conteo rapido de items pendientes (para badges) | Si |

**Daily Reviews Query:**
```
GET /spaced-repetition/daily-reviews?date=2026-02-19&max_reviews=50
```

### Quizzes (Unit Quizzes)

| Metodo | Endpoint | Descripcion | Auth |
|---|---|---|---|
| POST | `/quiz/unit/{unit_id}` | Generar quiz contextualizado para unidad | Si |
| POST | `/quiz/{quiz_id}/answer` | Enviar respuesta de quiz con feedback IA | Si |
| POST | `/quiz/{quiz_id}/complete` | Completar quiz y generar retroalimentacion | Si |
| GET | `/quiz/{quiz_id}` | Obtener quiz especifico | Si |
| GET | `/quiz/` | Listar quizzes del usuario (paginado) | Si |
| GET | `/quiz/{quiz_id}/progress` | Progreso actual del quiz | Si |
| DELETE | `/quiz/{quiz_id}` | Eliminar quiz (solo en progreso) | Si |
| GET | `/quiz/unit/{unit_id}/stats` | Estadisticas de quizzes para una unidad | Si |

---

## TIER 5: VIDEO & CONTENT

### Videos

| Metodo | Endpoint | Descripcion | Auth |
|---|---|---|---|
| POST | `/videos/tracking` | Crear registro de tracking de video | Si |
| POST | `/videos/progress` | Actualizar progreso de visualizacion | Si |
| GET | `/video-recommendations/{question_id}` | Videos recomendados post-error | Si |
| GET | `/videos/by-topic/{topic_id}` | Videos por tema | Si |

### Images

| Metodo | Endpoint | Descripcion | Auth |
|---|---|---|---|
| GET | `/images/{path}` | Servir imagenes de preguntas (static files) | No |

---

## TIER 6: SOCIAL & COMPETITIVE

### Boss Raid (Weekly Event)

| Metodo | Endpoint | Descripcion | Auth |
|---|---|---|---|
| GET | `/boss-raid/status` | Estado del raid (activo Domingos 10AM-10PM COT) | Opcional |
| POST | `/boss-raid/start` | Iniciar sesion de raid (20 preguntas) | Si |
| POST | `/boss-raid/submit-answer` | Enviar respuesta (damage + combo + 3x XP) | Si |
| POST | `/boss-raid/complete` | Finalizar raid y recibir recompensas | Si |
| GET | `/boss-raid/leaderboard` | Top participantes por damage (max 100) | Opcional |
| GET | `/boss-raid/session/{session_id}` | Estado de sesion (para resumir) | Si |

### Unit Bosses (Study Plan Bosses)

| Metodo | Endpoint | Descripcion | Auth |
|---|---|---|---|
| POST | `/bosses/{unit_number}/start` | Iniciar batalla de boss tematico | Si |
| GET | `/bosses/{battle_id}/questions` | Obtener 20 preguntas de alta dificultad | Si |
| POST | `/bosses/{battle_id}/complete` | Completar batalla y obtener recompensas/certificado | Si |
| GET | `/bosses/certificates` | Certificados de dominio del usuario | Si |
| GET | `/bosses/certificates/{certificate_id}` | Certificado especifico | Si |
| GET | `/bosses/available` | Unidades disponibles para enfrentar bosses | Si |
| GET | `/bosses/progress` | Progreso general de bosses (defeated, certificates) | Si |

### Leagues

| Metodo | Endpoint | Descripcion | Auth |
|---|---|---|---|
| GET | `/leagues/current` | Liga actual (division, rank, zone, weekly_xp) | Si |
| GET | `/leagues/leaderboard` | Leaderboard del grupo actual (con zonas) | Si |
| POST | `/leagues/join` | Unirse a liga (auto-join a Bronze) | Si |
| GET | `/leagues/history` | Historial de ligas (ultimas 10 semanas) | Si |

**League Zones (30 participantes por grupo):**
- Promotion: Top 10 (posiciones 1-10, 33%)
- Safe: Medio 15 (posiciones 11-25, 50%)
- Relegation: Bottom 5 (posiciones 26-30, 17%)

### Store

| Metodo | Endpoint | Descripcion | Auth |
|---|---|---|---|
| GET | `/store/items` | Items disponibles (filtro opcional por tipo) | Si |
| GET | `/store/cosmetics` | Items cosmeticos | Si |
| GET | `/store/power-ups` | Power-ups disponibles | Si |
| POST | `/store/purchase` | Comprar item | Si |
| GET | `/store/inventory` | Inventario completo + moneda del usuario | Si |
| GET | `/store/currency` | Moneda actual del usuario (orbs, crystals) | Si |
| GET | `/store/transactions` | Historial de transacciones | Si |
| GET | `/store/power-ups/active` | Power-ups activos del usuario | Si |
| POST | `/store/power-ups/activate` | Activar un power-up | Si |
| GET | `/store/earnings` | Resumen de ganancias de moneda | Si |
| POST | `/store/earn/unit-completion` | Ganar orbs por completar unidad | Si |
| POST | `/store/earn/achievement` | Ganar crystals por logro | Si |
| GET | `/store/power-ups/effects/{quiz_id}` | Efectos de power-ups activos en quiz | Si |

### Guilds (School-Based)

| Metodo | Endpoint | Descripcion | Auth |
|---|---|---|---|
| POST | `/guilds/auto-detect-school` | Auto-detectar escuela y crear/unirse a gremio | No |
| GET | `/guilds/user-guild/{user_id}` | Informacion del gremio del usuario | No |
| GET | `/guilds/{guild_id}/members` | Miembros del gremio | No |
| GET | `/guilds/school-rankings` | Rankings de escuelas (periodo: weekly, monthly, all_time) | No |
| GET | `/guilds/tournaments/available` | Torneos disponibles | No |
| POST | `/guilds/tournaments/{tournament_id}/join` | Unirse a torneo | No |
| GET | `/guilds/tournaments/{tournament_id}/participants` | Participantes del torneo | No |
| POST | `/guilds/{guild_id}/chat/send` | Enviar mensaje al chat del gremio | No |
| GET | `/guilds/{guild_id}/chat` | Mensajes del chat del gremio | No |
| GET | `/guilds/{guild_id}/statistics` | Estadisticas detalladas del gremio | No |
| GET | `/guilds/schools/{school_name}/statistics` | Estadisticas de escuela | No |
| GET | `/guilds/search` | Buscar gremios (por escuela, ciudad, nombre) | No |
| GET | `/guilds/tournaments/search` | Buscar torneos (por tipo, estado) | No |
| POST | `/guilds/update-rankings` | Actualizar rankings (admin) | No |
| GET | `/guilds/user/{user_id}/school-info` | Info de escuela del usuario | No |

### Dungeons (Solo Leveling-Inspired)

| Metodo | Endpoint | Descripcion | Auth |
|---|---|---|---|
| GET | `/dungeons/gates` | Portales disponibles (filtro por tipo y dificultad) | Si |
| POST | `/dungeons/{gate_id}/enter` | Entrar a portal e iniciar run | Si |
| GET | `/dungeons/encounters/{encounter_id}/questions` | Preguntas del encuentro | Si |
| POST | `/dungeons/encounters/{encounter_id}/submit` | Enviar respuestas del encuentro | Si |
| GET | `/dungeons/history` | Historial de runs del usuario | Si |
| GET | `/dungeons/{gate_id}/leaderboard` | Leaderboard del portal | Opcional |

### Premium

| Metodo | Endpoint | Descripcion | Auth |
|---|---|---|---|
| GET | `/premium/plans` | Planes premium disponibles (basic, premium, elite) | No |
| POST | `/premium/create-checkout-session` | Crear sesion de pago Wompi | Si |
| POST | `/premium/webhook/wompi` | Webhook para eventos de pago Wompi | No |
| GET | `/premium/status` | Estado premium del usuario (plan, features, expires) | Si |
| POST | `/premium/activate` | Activar plan premium | Si |

---

## TIER 7: AI & ASSETS

| Metodo | Endpoint | Descripcion | Auth |
|---|---|---|---|
| POST | `/ai/explain` | Explicacion AI de pregunta | Si |
| POST | `/ai/tips` | Tips personalizados | Si |
| POST | `/ai/chat` | Chat con tutor AI (context-aware) | Si |
| POST | `/ai/hint` | Hint para pregunta especifica | Si |
| GET | `/subjects/` | Materias con conteo de preguntas | Si |

---

## TIER 8: ANALYTICS & DASHBOARD

### Mastery

| Metodo | Endpoint | Descripcion | Auth |
|---|---|---|---|
| GET | `/mastery/topics` | Mastery por temas (filtrable por materia) | Si |
| GET | `/mastery/weak-areas` | Lista priorizada de areas debiles | Si |
| GET | `/mastery/radar-chart` | Datos para radar chart (5 materias) | Si |

---

## CODIGOS DE ERROR

| Codigo | Significado |
|---|---|
| 400 | Bad Request - Input invalido |
| 401 | Unauthorized - Token invalido o expirado |
| 403 | Forbidden - Sin permisos |
| 404 | Not Found - Recurso no existe |
| 409 | Conflict - Duplicado (e.g. username, DUPLICATE_SUBMISSION) |
| 422 | Validation Error - Pydantic |
| 429 | Too Many Requests - Rate limited |
| 500 | Internal Server Error |

**Error Response Format:**
```json
{
  "detail": "Descripcion del error",
  "error_code": "HEARTS_DEPLETED",
  "status_code": 400
}
```

**Common Error Codes:**
- `HEARTS_EMPTY` - No hearts available
- `HEARTS_AVAILABLE` - Cannot enter Grace Mode with hearts
- `DUPLICATE_SUBMISSION` - Answer already submitted
- `TOO_FAST` - Anti-gaming: answer too fast (<3s)
- `INSUFFICIENT_FUNDS` - Not enough gold/gems
- `ITEM_NOT_FOUND` - Shop item doesn't exist
- `NO_FREEZES` - No streak freezes available
- `NOT_ENOUGH_GOLD` - Insufficient gold
- `NO_STREAK_TO_REPAIR` - No streak to repair
- `STREAK_REPAIR_EXPIRED` - 24h repair window passed
- `RAID_NOT_ACTIVE` - Boss Raid only on Sundays 10AM-10PM COT
- `BOSS_ALREADY_DEFEATED` - Weekly boss already defeated
- `DIAGNOSTIC_COMPLETED` - Diagnostic already submitted

---

## RATE LIMITING

- Global: 60 requests/minuto por usuario.
- General endpoints: 100 requests/minuto.
- Anti-gaming: Respuestas con <3s entre intentos son rechazadas.
- XP cap: 500 XP/hora maximo.
- Boss Raid: 1 sesion activa a la vez.
- Millionaire: Maximo 3 partidas/dia.
- Onboarding: 10 requests/minuto.
