# GLOSSARY.md — ICFES Leveling

> Glosario de términos del proyecto. Referencia rápida para todo el equipo.

---

## Términos del Dominio (ICFES)

| Término | Definición |
|---|---|
| **ICFES** | Instituto Colombiano para la Evaluación de la Educación. Organismo que administra el examen Saber 11. |
| **Saber 11** | Examen nacional colombiano obligatorio para estudiantes de grado 11. Evalúa 5 áreas. Puntaje 0-500. |
| **Competencia** | Habilidad evaluada dentro de una materia (ej: interpretación, argumentación). |
| **Componente** | Sub-área dentro de una materia (ej: álgebra, geometría dentro de Matemáticas). |
| **Proceso cognitivo** | Nivel de pensamiento requerido (ej: comprensión, análisis, evaluación). |
| **Afirmación** | Declaración de lo que el estudiante debe saber/hacer. |
| **Evidencia** | Indicador observable de que el estudiante cumple la afirmación. |

## Términos Técnicos (IRT)

| Término | Definición |
|---|---|
| **IRT** | Item Response Theory. Marco estadístico para medir habilidad latente. |
| **3PL** | Three-Parameter Logistic model. Modelo IRT con discriminación, dificultad, y pseudo-adivinanza. |
| **Theta (θ)** | Habilidad estimada del estudiante. Rango: -3.0 a +3.0. |
| **Parámetro a** | Discriminación. Qué tan bien diferencia una pregunta entre alumnos. Rango: 0.5-2.5. |
| **Parámetro b** | Dificultad de la pregunta. Rango: -2.0 a +2.0. |
| **Parámetro c** | Pseudo-adivinanza. Probabilidad de acertar al azar. Rango: 0.0-0.25. |
| **Fisher Information** | Métrica que indica cuánta información provee una pregunta en un theta dado. Se usa para selección óptima. |
| **MLE** | Maximum Likelihood Estimation. Método para estimar theta. |
| **SE** | Standard Error. Incertidumbre en la estimación de theta. |

## Términos de Gamificación

| Término | Definición |
|---|---|
| **XP** | Experience Points. Puntos de experiencia que determinan el nivel. |
| **Gold** | Moneda principal del juego. Se gana jugando. |
| **Orbs** | Moneda secundaria. Se gana en batallas. |
| **Crystals** | Moneda premium. Se compra con dinero real. |
| **Hearts** | Corazones/vidas. Se pierden al responder incorrectamente. Máximo 5. |
| **Grace Mode** | Estado cuando hearts = 0. Puede jugar pero no gana XP. |
| **Streak** | Racha de días consecutivos activos. |
| **Streak Freeze** | Protección que evita perder la racha por 1 día de inactividad. |
| **Combo** | Respuestas correctas consecutivas dentro de una sesión. |
| **Critical Hit** | Respuesta correcta en menos de 3 segundos. Doble recompensa. |
| **Mastery** | Score 0.0-1.0 que indica dominio de un tema. |
| **Decay** | Reducción automática de mastery por inactividad (2%/día después de 3 días). |
| **Rank** | Rango del jugador basado en nivel. E → D → C → B → A → S → SS → SSS. |

## Términos de Arquitectura

| Término | Definición |
|---|---|
| **GameEngineService** | Servicio central que contiene TODAS las fórmulas de juego. Fuente única de verdad. |
| **Anti-Gaming** | Sistema que previene explotación de mecánicas (farming XP, repetición). |
| **Attempt Type** | Clasificación de un intento: `new`, `valid_review`, `invalid_repeat`. |
| **Offline-First** | Patrón donde la app funciona sin internet y sincroniza al reconectar. |
| **ActionQueue** | Cola FIFO de acciones pendientes de sincronizar con el servidor. |
| **SyncManager** | Orquestador que procesa ActionQueue cuando hay conexión. |
| **DopamineEngine** | Sistema de feedback psicológico para engagement (recompensas variables, combos, etc.). |
| **SM-2** | SuperMemo 2. Algoritmo de repetición espaciada para optimizar retención. |
| **Easiness Factor** | Factor que ajusta intervalos de repetición. Mayor = más fácil = intervalos más largos. |

## Términos de Modos de Juego

| Término | Definición |
|---|---|
| **Practice** | Modo principal. 15 preguntas adaptativas con feedback inmediato. |
| **Millionaire** | Modo "Quién Quiere Ser Millonario". 15 preguntas progresivas con checkpoints. |
| **Boss Raid** | Evento semanal (domingos). Boss con 10,000 HP. Todos contribuyen daño. |
| **Dungeon** | Exploración con encuentros. Requiere nivel mínimo. |
| **PvP Battle** | Batalla 1v1 en tiempo real via WebSocket. |
| **Lifeline** | Ayuda en sesión: 50/50, Ask AI, Skip. |
| **Walk Away** | Retirarse en Millionaire conservando recompensas acumuladas. |
| **Checkpoint** | Puntos seguros en Millionaire (preguntas 5, 10, 15). |

## Términos de Infraestructura

| Término | Definición |
|---|---|
| **Monorepo** | Repositorio único con todos los servicios (`apps/backend`, `apps/mobile`, etc.). |
| **Tier** | Agrupación lógica de routers en el backend (1-8 por prioridad). |
| **Celery** | Sistema de tareas en background para Python (daily quests, leaderboard reset). |
| **Alembic** | Herramienta de migraciones SQL para SQLAlchemy. |
| **Hive** | Base de datos local NoSQL para Flutter (cache offline). |
| **Riverpod** | State management framework para Flutter. |
| **GoRouter** | Navigation framework para Flutter con deep linking. |
| **Wompi** | Pasarela de pagos colombiana. |
