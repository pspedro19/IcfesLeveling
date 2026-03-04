# SPEC.md — ICFES Leveling Technical Specification

> Especificación técnica completa del producto. Este documento define QUÉ hace el sistema.

---

## 1. VISIÓN DEL PRODUCTO

**ICFES Leveling** es una plataforma móvil gamificada para preparar estudiantes colombianos para el examen ICFES Saber 11. Combina testing adaptativo (IRT 3PL), mecánicas RPG, y AI personalizada para maximizar el aprendizaje y la retención.

### 1.1 Usuarios Objetivo
- Estudiantes colombianos de grado 10° y 11° (15-18 años).
- Estudiantes en preICFES y cursos preparatorios.
- Adultos repitiendo el examen.

### 1.2 Propuesta de Valor
- Diagnóstico adaptativo con IRT que identifica debilidades reales.
- Gamificación profunda (RPG) que mantiene engagement diario.
- Planes de estudio personalizados por AI.
- Sistema offline-first para zonas con conectividad limitada.
- Gratuito con modelo freemium.

---

## 2. FUNCIONALIDADES CORE

### 2.1 Onboarding (5 pasos)
| Paso | Input | Output |
|---|---|---|
| 1. Welcome | — | Pantalla de bienvenida |
| 2. Meta | Puntaje objetivo ICFES (0-500) | `onboarding_preferences.goal` |
| 3. Nivel | Principiante/Intermedio/Avanzado | `onboarding_preferences.level` |
| 4. Materias | Selección de materias de enfoque | `onboarding_preferences.subjects` |
| 5. Tiempo | Minutos disponibles por día | `onboarding_preferences.time` |

**Post-onboarding:** Diagnóstico Rápido automático.

### 2.2 Sistema de Diagnóstico

#### Diagnóstico Rápido (Onboarding)
- **Preguntas:** 15 (3 por materia: 1 fácil + 1 media + 1 difícil).
- **Tiempo límite:** 10 minutos.
- **Feedback:** SIN feedback inmediato (calibración pura).
- **Output:** theta, SE, percentil, rango (E-S), áreas débiles.
- **Endpoint:** `POST /diagnostic/quick/start` → `POST /diagnostic/quick/submit`.

#### Diagnóstico Profundo (por materia)
- **Preguntas:** 15-20 por materia.
- **Orden:** Dificultad creciente.
- **Output:** Mastery por tema, skill tree con desbloqueos.
- **Endpoint:** `POST /diagnostic/deep/start/{subject_id}` → `POST /diagnostic/deep/submit`.

#### Selección Adaptativa de Preguntas
- **Modelo:** IRT 3PL con estimación theta en tiempo real.
- **Flujo:** Pregunta inicial (θ=0) → respuesta → recalcula θ → selecciona siguiente pregunta con máxima información en θ actual.
- **Batch endpoint:** Devuelve siguiente pregunta óptima + metadata IRT.
- **Theta:** Actualización Bayesiana tras cada respuesta; SE target < 0.3 para convergencia.
- **Endpoints:**
  - `POST /diagnostic/adaptive/next-question` — Selecciona siguiente pregunta IRT-óptima.
  - `POST /diagnostic/adaptive/submit-answer` — Envía respuesta, recalcula θ, retorna nuevo estado.

#### Reevaluación Mensual
- Diagnóstico completo nuevo.
- Comparación con baseline anterior.
- Regeneración de plan de estudio.
- Actualización de puntaje proyectado.
- **Endpoint:** `POST /monthly-reassessment/start`.

### 2.3 Revelación de Resultados
Secuencia animada (4 segundos):
1. "EL SISTEMA TE HA EVALUADO..."
2. "CALCULANDO RANGO DE CAZADOR"
3. Radar chart animado (5 materias)
4. Letra de rango con animación escala
5. Áreas débiles priorizadas: HIGH (<0.4), MEDIUM (0.4-0.6), LOW (0.6-0.7)

---

## 3. MODOS DE JUEGO

### 3.1 Practice Mode
| Atributo | Valor |
|---|---|
| Preguntas | 15 por sesión |
| Selección | 60% falladas + 40% nuevas |
| Lifelines | 50/50, Ask AI, Skip (1 cada una) |
| XP correcta | base(10) + speed_bonus(0-5) + streak_bonus × difficulty |
| Speed bonus | <10s: +5 XP, <20s: +3 XP |
| Gold | 10 por correcta |
| Costo | 1 corazón por incorrecta |

### 3.2 Millionaire Mode (Quién Quiere Ser Millonario)
| Atributo | Valor |
|---|---|
| Preguntas | 15 dificultad progresiva |
| Partidas/día | Máximo 3 |
| Checkpoints | Pregunta 5, 10, 15 |
| Lifelines | 50/50 (gratis), AI Hint (50 gold), Skip (gratis) |
| Walk Away | En cualquier momento, conserva rewards acumulados |
| Estados | notStarted → playing → won/lost/walkingAway |

### 3.3 Boss Raid
| Atributo | Valor |
|---|---|
| Disponibilidad | Domingos 10AM-10PM (Colombia, UTC-5) |
| Costo | 100 gold entrada |
| Preguntas | 20 (70% materia del boss + 30% aleatorias) |
| Boss HP | 10,000 (todos los jugadores contribuyen) |
| Reset | Semanal (nuevo boss cada domingo) |
| XP | 30 por correcta (3x multiplier) |
| Daño | base(10) + combo_bonus(min(combo,10)×5) |
| Rangos | S(≥90%), A(≥80%), B(≥70%), C(<70%) |

### 3.4 Dungeon Mode
- DungeonGate: Portal de entrada (requiere nivel mínimo).
- DungeonRun: Sesión de mazmorra con encuentros.
- DungeonEncounter: Combates con monstruos.
- Node Progress: Mapa de conquista con prerequisitos.

### 3.5 PvP Battles
- Preguntas en tiempo real via WebSocket.
- Correcta = daño al oponente; incorrecta = daño recibido (difficulty × 5).
- Batalla termina cuando HP ≤ 0.
- Recompensas: XP + orbs basados en dificultad y velocidad.

### 3.6 Quizzes (Unit-Based)
| Atributo | Valor |
|---|---|
| Preguntas | 10 por unidad |
| Origen | Vinculadas al plan de estudio activo |
| Desbloqueo | Completar contenido de la unidad |
| Aprobación | ≥70% para marcar unidad como completada |
| XP | 15 por correcta + bonus por unidad perfecta |
| Reintentos | Ilimitados (mejora score, no repite XP) |

### 3.7 Training Zone
| Atributo | Valor |
|---|---|
| Enfoque | Práctica por materia específica |
| Preguntas | Selección adaptativa por mastery del tema |
| AI Explanations | Explicación automática tras respuesta incorrecta |
| Video Integration | Video recomendado post-error según tipo de fallo |
| Monthly Reports | Resumen mensual con evolución por tema, tiempo invertido, áreas mejoradas |
| Sesión | Sin límite de preguntas; el usuario decide cuándo terminar |

---

## 4. SISTEMAS DE PROGRESIÓN

### 4.1 Niveles y Rangos
```
XP para nivel N = (N-1)² × 100
Nivel = floor(sqrt(XP / 100)) + 1

Rangos:
  Nivel 1-14:   E    |  Nivel 60-69:  A
  Nivel 15-29:  D    |  Nivel 70-79:  S
  Nivel 30-49:  C    |  Nivel 80-89:  SS
  Nivel 50-59:  B    |  Nivel 90+:    SSS
```

### 4.2 Sistema de Corazones
- Inicio: 5/5 corazones.
- Incorrecta: -1 corazón (excepto grace mode).
- Grace mode (0 corazones): juega sin ganar XP.
- Recuperación: timer automático, ads (max 3/día), premium.

### 4.3 Racha (Streak)
- Días consecutivos con actividad.
- Multiplicadores XP: 1-6d=1.0x, 7-13d=1.2x, 14-29d=1.5x, 30+d=2.0x.
- Streak Freeze: protección automática por 1 día de inactividad.
- Meta diaria configurable: default 20 XP.

### 4.4 Mastery por Tema
```
Umbrales: LOCKED(0.0) → BEGINNER(0.3) → DEVELOPING(0.5) → PROFICIENT(0.7) → MASTER(0.9)
Learning rate correcta: +12% × (1.0 - actual)
Learning rate incorrecta: -6% × actual
Decay: 2%/día después de 3 días sin práctica (mínimo 10%, cap 30 días)
Prerequisitos: 60% mastery del tema anterior para desbloquear
```

### 4.5 Repetición Espaciada (SM-2)
```
Intervalos: AGAIN=1d, HARD=2d, GOOD=4d, EASY=7d
Easiness factor: inicial 2.5, mínimo 1.3, máximo 4.0
Fórmula: nuevo_intervalo = anterior × easiness_factor
Daily reviews: new + learning + review items (max 50)
```

### 4.6 Daily Challenges
- **Generación:** Basada en fecha (seed = YYYYMMDD); mismos challenges para todos.
- **Tipos:**
  - Responder N preguntas (ej: 20 preguntas).
  - Obtener X% accuracy en sesión (ej: 80%+).
  - Completar sesión de práctica completa.
  - Ganar N batallas PvP.
  - Estudiar N minutos.
- **Recompensas:** Gold + XP bonus; completar los 3 daily → chest reward.
- **Reset:** Diario a medianoche (Colombia, UTC-5).

### 4.7 Leagues (Detalle)
```
Divisiones (6):
  Bronce → Plata → Oro → Platino → Diamante → Leyenda

Grupos: ~30 usuarios por grupo, asignados por división actual.
Scoring: XP semanal acumulado.
Ciclo semanal:
  Lunes 00:00 (UTC-5): Inicia nueva semana de liga.
  Domingo 23:59 (UTC-5): Cierra semana.
  Lunes 00:01 (UTC-5): Procesa promociones/relegaciones.

Zonas:
  Promoción: Top 5 del grupo → ascienden a siguiente división.
  Neutral: Posiciones 6-25 → se mantienen.
  Relegación: Bottom 5 del grupo → descienden a división anterior.

Excepciones:
  Bronce bottom 5: Se mantienen (no hay división inferior).
  Leyenda top 5: Recompensa especial (no hay división superior).
```

---

## 5. ECONOMÍA VIRTUAL

### 5.1 Monedas
| Moneda | Inicio | Ganancia | Uso |
|---|---|---|---|
| Gold | 1000 | 10/correcta practice, difficulty×2 batallas | Boss Raid (100), AI Hint (50), tienda |
| Orbs | 0 | difficulty×2 batallas, ×4 critical hit | Items especiales |
| Crystals | 0 | Compra real ($) | Premium items, corazones ilimitados |

### 5.2 Planes Premium
| Plan | Precio | Features |
|---|---|---|
| free | $0 | Funcionalidad básica |
| basic | TBD | Sin anuncios + extras |
| premium | TBD | Corazones ilimitados + AI features |
| elite | TBD | Todo + features exclusivas |

### 5.3 Pasarelas de Pago
- Colombia: **Wompi** (principal).
- Internacional: **Stripe**.

---

## 6. LIGAS Y COMPETENCIA

### 6.1 Divisiones
Bronce → Plata → Oro → Platino → Diamante → Leyenda

### 6.2 Mecánica
- Grupos de ~30 usuarios por nivel similar.
- Ranking semanal por XP.
- Ascenso/descenso entre divisiones al final de cada semana.
- Leaderboard: global, weekly, subject, boss_raid.
- Cache Redis: 10 min TTL, top 50 + posición del usuario.

### 6.3 Algoritmo de Asignación de Grupos
1. Al inicio de semana, tomar todos los usuarios activos por división.
2. Ordenar aleatoriamente dentro de cada división.
3. Partir en grupos de ~30 (último grupo puede tener 20-35).
4. Usuarios nuevos entran en Bronce, grupo asignado al siguiente disponible.

### 6.4 Ciclo Semanal
```
Lunes 00:00 (UTC-5):
  1. Procesar resultados semana anterior.
  2. Top 5 de cada grupo → promover (excepto Leyenda).
  3. Bottom 5 de cada grupo → relegar (excepto Bronce).
  4. Reasignar grupos nuevos para la semana.
  5. Reset XP semanal a 0.
```

### 6.5 Zonas de Resultado
| Zona | Posiciones | Efecto |
|---|---|---|
| Promoción | 1-5 | Asciende una división + reward (gold + orbs) |
| Neutral | 6-25 | Se mantiene en división actual |
| Relegación | 26-30 | Desciende una división |

---

## 7. AI SERVICE

### 7.1 Explicaciones
- Modelo: GPT-3.5-turbo.
- Cache: Redis 30 días TTL.
- Fallback: Mock responses si no hay API key.

### 7.2 Planes de Estudio AI
- Modelos: GPT-3.5-turbo / Claude.
- Input: áreas débiles + catálogo ICFES + historial.
- Output: Plan YML con máximo 8 unidades.

### 7.3 Test de Personalidad
5 clases de héroe:
- Warrior (Guerrero del Conocimiento)
- Mage (Mago Cuántico)
- Archer (Arquero de la Sabiduría)
- Priest (Sacerdote del Aprendizaje)
- Assassin (Asesino de la Lógica)

---

## 8. RECOMENDACIONES DE VIDEO

### 8.1 Análisis de Error
| Tipo Error | Peso | Videos Recomendados |
|---|---|---|
| conceptual | 1.5 | explicación, tutorial, teoría |
| procedural | 1.2 | ejercicio resuelto, paso a paso |
| careless | 0.8 | repaso rápido, tips, resumen |

### 8.2 Ajuste de Dificultad
| Rendimiento | Ajuste |
|---|---|
| <30% (very_low) | -2 niveles |
| 30-50% (low) | -1 nivel |
| 50-70% (medium) | 0 (actual) |
| >70% (high) | +1 nivel |

### 8.3 Tracking
- YouTube player integrado (youtube_player_flutter).
- Auto-completado al 80% visto.
- Progreso persistido: watched_seconds, percentage.

---

## 9. ANÁLISIS DE DEBILIDADES

### 9.1 Clasificación
| Severidad | Criterio |
|---|---|
| CRITICAL | Accuracy < 40% |
| SIGNIFICANT | Accuracy 40-60% |
| TIME_INEFFICIENT | Respuesta > 120s |
| MINOR | Accuracy 60-70% |

### 9.2 Tipos
| Tipo | Descripción | Intervención |
|---|---|---|
| CONCEPTUAL_GAP | Error fundamental | Revisión teoría con videos |
| PROCEDURAL_SLOWNESS | Demasiado lento | Práctica de velocidad |
| SYSTEMATIC_ERROR | Mismo error 60%+ | Identificar distractor dominante |
| INCONSISTENT | Resultados variables | Más práctica general |

---

## 10. SISTEMA OFFLINE-FIRST

### 10.1 Componentes
- **Hive:** BD local NoSQL para cache.
- **ActionQueue:** Cola FIFO de acciones pendientes.
- **SyncManager:** Orquestador de sincronización.
- **ConnectivityMonitor:** Detector de estado de conexión.
- **PendingAnswerSync:** Respuestas esperando envío.

### 10.2 Flujo
1. Usuario responde sin conexión.
2. Respuesta → Hive + ActionQueue.
3. ConnectivityMonitor detecta reconexión.
4. SyncManager procesa ActionQueue en orden FIFO.
5. Backend procesa y retorna resultado.
6. Estado local actualizado.

### 10.3 Cache de Preguntas
- Pre-descarga por materia al iniciar.
- TTL configurable en Hive.
- Práctica 100% offline posible.
- Sync delta al reconectar.

---

## 11. NOTIFICACIONES

### 11.1 Push Notifications
- **Proveedor:** Firebase Cloud Messaging (FCM).
- **Plataformas:** Android (FCM nativo) + iOS (APNs via FCM).
- **Registro:** Device token enviado al backend en login; actualizado en cada app start.
- **Endpoint:** `POST /notifications/register-device` — registra/actualiza token FCM.

### 11.2 Tipos de Notificación
| Tipo | Trigger | Mensaje (ejemplo) |
|---|---|---|
| streak_reminder | 20:00 si no ha cumplido meta diaria | "No pierdas tu racha de X días!" |
| daily_challenge | 08:00 diario | "Tus retos diarios están listos" |
| boss_raid_starting | Domingo 09:45 (UTC-5) | "El Boss Raid comienza en 15 min" |
| league_promotion | Lunes post-procesamiento | "Ascendiste a [División]!" |
| inactivity | 48h sin actividad | "Te extrañamos, vuelve a practicar" |

### 11.3 Gestión de Tokens
- Múltiples dispositivos por usuario soportados.
- Token invalidado si FCM retorna error de registro.
- Cleanup automático de tokens inactivos (>90 días).

---

## 12. TIENDA Y POWER-UPS

### 12.1 Items de Tienda
| Categoría | Items | Moneda |
|---|---|---|
| Cosméticos | Avatares, marcos, títulos | Gold / Orbs |
| Power-ups | XP Boost, Shield, Time Extension | Gold |
| Protección | Streak Freeze (extra) | Gold (500) / Crystals |
| Consumibles | Corazón extra, pista AI | Gold |

### 12.2 Power-ups
| Power-up | Efecto | Duración | Costo |
|---|---|---|---|
| XP Boost | 2x XP en toda actividad | 30 minutos | 200 gold |
| Shield | Previene pérdida de corazón (1 uso) | Hasta activarse | 150 gold |
| Time Extension | +30s en preguntas cronometradas | 1 sesión | 100 gold |

### 12.3 Mecánica de Activación
- Power-up comprado → inventario del usuario.
- Activación manual antes/durante sesión.
- Timer inicia al activar (no al comprar).
- Expiración: notificación 5 min antes de terminar.
- Máximo 1 power-up activo del mismo tipo simultáneamente.

### 12.4 Fuentes de Moneda
| Fuente | Gold | Orbs | Crystals |
|---|---|---|---|
| Pregunta correcta (practice) | 10 | — | — |
| Batalla PvP ganada | 20 | difficulty×2 | — |
| Boss Raid (rank S) | 200 | 50 | — |
| Daily challenges (3/3) | 100 | 10 | — |
| Promoción de liga | 150 | 25 | — |
| Compra real ($) | — | — | Según paquete |

---

## 13. GUILDAS Y SOCIAL

### 13.1 Guildas Escolares
- **Auto-detección:** Por dominio de email o código de institución en onboarding.
- **Creación manual:** Cualquier usuario puede crear guilda (costo: 500 gold).
- **Miembros:** Máximo 50 por guilda.
- **Roles:** Líder, Oficial, Miembro.

### 13.2 Rankings de Guilda
| Ranking | Métrica | Periodo |
|---|---|---|
| XP total | Suma XP de miembros | Semanal |
| Raid damage | Daño combinado en Boss Raid | Por raid |
| Actividad | Miembros activos / total | Semanal |

### 13.3 Torneos de Guilda
- Guilda vs Guilda: XP acumulado en periodo de 3 días.
- Matchmaking por tamaño similar (±10 miembros).
- Rewards distribuidos a todos los miembros de la guilda ganadora.

### 13.4 Chat de Guilda
- Mensajes de texto en tiempo real (WebSocket).
- Mensajes del sistema: logros de miembros, resultados de torneos.
- Moderación: líder/oficial puede silenciar miembros.

### 13.5 Rankings Escolares
- Ranking nacional de colegios por XP promedio de estudiantes.
- Mínimo 10 estudiantes activos para aparecer en ranking.
- Actualización semanal.

---

## 14. PERSONALIDAD Y CLASES DE HÉROE

### 14.1 Test de Personalidad
- **Preguntas:** 5 preguntas situacionales (estilo de aprendizaje).
- **Momento:** Durante onboarding (después de paso 5, antes de diagnóstico).
- **Cada pregunta** tiene 5 opciones, cada una mapeada a una clase.
- **Resultado:** Clase con mayor puntaje acumulado.
- **Empate:** Se resuelve por prioridad: Warrior > Mage > Archer > Priest > Assassin.

### 14.2 Clases de Héroe
| Clase | Nombre | Stat Boost |
|---|---|---|
| Warrior | Guerrero del Conocimiento | +10% XP en practice, +5% HP en batallas |
| Mage | Mago Cuántico | +15% efectividad AI hints, -10% cooldown lifelines |
| Archer | Arquero de la Sabiduría | +10% gold ganado, +5% accuracy bonus XP |
| Priest | Sacerdote del Aprendizaje | +1 corazón máximo (6 total), +10% recuperación corazones |
| Assassin | Asesino de la Lógica | +20% speed bonus XP, +10% daño en Boss Raid |

### 14.3 Habilidades de Clase
| Clase | Habilidad | Efecto | Cooldown |
|---|---|---|---|
| Warrior | Knowledge Shield | Bloquea 1 respuesta incorrecta | 24h |
| Mage | Quantum Insight | Revela tema de la pregunta | 12h |
| Archer | Precision Shot | 2x XP en siguiente correcta | 8h |
| Priest | Healing Light | Recupera 2 corazones | 12h |
| Assassin | Shadow Step | Salta pregunta sin penalización | 8h |
