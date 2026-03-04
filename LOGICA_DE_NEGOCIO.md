# 🎮 ICFES LEVELING - LÓGICA DE NEGOCIO COMPLETA

> **Versión:** 2.0 (Production Ready)  
> **Estado:** ✅ Corregido y Balanceado  
> **Última actualización:** Diciembre 2024

---

## 📋 TABLA DE CONTENIDOS

1. [Visión y Propuesta de Valor](#1-visión-y-propuesta-de-valor)
2. [Arquitectura de Usuario](#2-arquitectura-de-usuario)
3. [Flujo de Onboarding (6 Pasos)](#3-flujo-de-onboarding-6-pasos)
4. [Sistema de Diagnóstico (Dos Fases)](#4-sistema-de-diagnóstico-dos-fases)
5. [Ciclo de Práctica Diaria](#5-ciclo-de-práctica-diaria)
6. [Sistema de Corazones (Mana)](#6-sistema-de-corazones-mana)
7. [Sistema de Rachas (Streaks)](#7-sistema-de-rachas-streaks)
8. [Sistema de XP y Niveles](#8-sistema-de-xp-y-niveles)
9. [Sistema de Ligas (Rankings)](#9-sistema-de-ligas-rankings)
10. [Sistema de Combos](#10-sistema-de-combos)
11. [Boss Raid Semanal](#11-boss-raid-semanal)
12. [Economía del Oro](#12-economía-del-oro)
13. [Motor de Aprendizaje Adaptativo](#13-motor-de-aprendizaje-adaptativo)
14. [Sistema de Explicaciones](#14-sistema-de-explicaciones)
15. [Notificaciones Push](#15-notificaciones-push)
16. [Dopamine Engine (Animaciones)](#16-dopamine-engine-animaciones)
17. [Sincronización Offline](#17-sincronización-offline)
18. [Fallback Matrix](#18-fallback-matrix)
19. [Modelo de Monetización](#19-modelo-de-monetización)
20. [KPIs y Métricas de Éxito](#20-kpis-y-métricas-de-éxito)
21. [Roadmap de Desarrollo](#21-roadmap-de-desarrollo)

---

## 1. VISIÓN Y PROPUESTA DE VALOR

### 1.1 ¿Qué es ICFES Leveling?

ICFES Leveling es una **plataforma educativa gamificada** que transforma la preparación para el examen ICFES Saber 11 en una experiencia de juego RPG inspirada en Solo Leveling.

### 1.2 Problema que Resolvemos

| Problema Actual | Nuestra Solución |
|-----------------|------------------|
| Estudiar para el ICFES es aburrido | Gamificación que hace adictivo el aprendizaje |
| No hay feedback de progreso real | Sistema de rangos y predicción de puntaje |
| Materiales genéricos para todos | Aprendizaje adaptativo personalizado |
| Requiere internet constante | Funciona 100% offline |
| Costoso (preICFES, tutores) | Modelo freemium accesible |

### 1.3 Público Objetivo

| Segmento | Edad | Necesidad | Tamaño Mercado |
|----------|------|-----------|----------------|
| **Estudiantes 10°-11°** | 15-18 | Prepararse de forma entretenida | ~1.2M/año |
| **Repitentes universitarios** | 18-25 | Mejorar puntaje para mejor U | ~200K/año |
| **Colegios (B2B)** | N/A | Herramienta de preparación masiva | ~13K colegios |

### 1.4 Áreas ICFES Soportadas

```
📐 MATEMÁTICAS
   └── Álgebra, Geometría, Estadística, Trigonometría, Cálculo

📖 LECTURA CRÍTICA
   └── Comprensión literal, Inferencia, Evaluación crítica

🔬 CIENCIAS NATURALES
   └── Física, Química, Biología

🌍 SOCIALES Y CIUDADANAS
   └── Historia, Geografía, Competencias ciudadanas

🇬🇧 INGLÉS
   └── Grammar, Vocabulary, Reading comprehension
```

### 1.5 Diferenciadores Clave

| Nosotros | Competencia |
|----------|-------------|
| Diagnóstico en 5 min (no 5 horas) | Tests largos que aburren |
| Nunca bloqueas completamente | Sin corazones = no puedes usar |
| 4h regeneración (humano) | 2h regeneración (frustración) |
| Anti-gaming integrado | Farming de XP fácil |
| Offline-first real | "Offline" que no funciona |
| Estética Solo Leveling | UI genérica educativa |

---

## 2. ARQUITECTURA DE USUARIO

### 2.1 Estados del Usuario

```
┌─────────────────────────────────────────────────────────────────────┐
│                    CICLO DE VIDA DEL USUARIO                        │
└─────────────────────────────────────────────────────────────────────┘

    [NUEVO]
       │
       ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   ONBOARDING │────▶│    ACTIVO    │────▶│   ENGAGED    │
│   (Día 0)    │     │  (D1-D7)     │     │   (D7+)      │
└──────────────┘     └──────────────┘     └──────────────┘
                            │                    │
                            ▼                    ▼
                     ┌──────────────┐     ┌──────────────┐
                     │   EN RIESGO  │◀───▶│  POWER USER  │
                     │  (3d inact)  │     │  (30d streak)│
                     └──────────────┘     └──────────────┘
                            │
                            ▼
                     ┌──────────────┐     ┌──────────────┐
                     │   INACTIVO   │────▶│   CHURNED    │
                     │  (7d inact)  │     │  (30d inact) │
                     └──────────────┘     └──────────────┘
```

### 2.2 Modelo de Datos del Usuario

```sql
-- Usuario principal
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    avatar_url VARCHAR(500),
    
    -- Gamificación
    level INTEGER DEFAULT 1,
    total_xp INTEGER DEFAULT 0,
    gold INTEGER DEFAULT 0,
    
    -- Corazones (Mana)
    hearts INTEGER DEFAULT 5,
    last_heart_regen TIMESTAMPTZ DEFAULT NOW(),
    ads_watched_today INTEGER DEFAULT 0,
    ads_watched_date DATE DEFAULT CURRENT_DATE,
    
    -- Racha
    current_streak INTEGER DEFAULT 0,
    longest_streak INTEGER DEFAULT 0,
    last_activity_date DATE,
    streak_freeze_count INTEGER DEFAULT 0,
    
    -- Estado
    hunter_rank VARCHAR(10) DEFAULT 'E-Rank',
    projected_icfes_score INTEGER DEFAULT 0,
    onboarding_completed BOOLEAN DEFAULT FALSE,
    
    -- Timezone
    timezone VARCHAR(50) DEFAULT 'America/Bogota',
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Mastery por tema
CREATE TABLE user_topic_mastery (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    topic_id UUID REFERENCES topics(id),
    area VARCHAR(50) NOT NULL,
    
    mastery_score FLOAT DEFAULT 0.0,  -- 0.0 a 1.0
    questions_seen INTEGER DEFAULT 0,
    questions_correct INTEGER DEFAULT 0,
    last_practiced TIMESTAMPTZ,
    
    -- Diagnóstico
    diagnostic_completed BOOLEAN DEFAULT FALSE,
    initial_mastery FLOAT,
    
    UNIQUE(user_id, topic_id)
);

-- Historial de respuestas
CREATE TABLE user_answer_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    question_id UUID REFERENCES questions(id),
    session_id UUID,
    
    selected_option INTEGER NOT NULL,
    is_correct BOOLEAN NOT NULL,
    time_spent_seconds INTEGER NOT NULL,
    
    -- Anti-gaming
    is_new_question BOOLEAN NOT NULL,
    is_valid_review BOOLEAN NOT NULL,
    xp_earned INTEGER DEFAULT 0,
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## 3. FLUJO DE ONBOARDING (6 PASOS)

### 3.1 Objetivo del Onboarding

- **Tiempo total:** < 8 minutos
- **Tasa de conversión target:** > 70%
- **Resultado:** Usuario enganchado con primera sesión completada

### 3.2 Flujo Detallado

```
╔═══════════════════════════════════════════════════════════════════════╗
║  PASO 1: SPLASH (2 segundos)                                          ║
╠═══════════════════════════════════════════════════════════════════════╣
║                                                                       ║
║                    [Logo Animado - Rive]                              ║
║                                                                       ║
║                    "Despierta, Cazador."                              ║
║                                                                       ║
║  Técnico:                                                             ║
║  • Verificar auth token en background                                 ║
║  • Precargar assets del onboarding                                    ║
║  • Detectar timezone del dispositivo                                  ║
║                                                                       ║
╚═══════════════════════════════════════════════════════════════════════╝
                                   │
                                   ▼
╔═══════════════════════════════════════════════════════════════════════╗
║  PASO 2: VALUE PROPOSITION (3 pantallas, ~15 segundos)                ║
╠═══════════════════════════════════════════════════════════════════════╣
║                                                                       ║
║  Pantalla 2.1:                                                        ║
║  ┌─────────────────────────────────────────────────────────────────┐  ║
║  │                                                                 │  ║
║  │                    [Ilustración: Cazador]                       │  ║
║  │                                                                 │  ║
║  │         "Sube de Rango preparándote para el ICFES"              │  ║
║  │                                                                 │  ║
║  │         De E-Rank a S-Rank. Tu camino comienza hoy.             │  ║
║  │                                                                 │  ║
║  │                       [●○○]                                     │  ║
║  │                                                                 │  ║
║  └─────────────────────────────────────────────────────────────────┘  ║
║                                                                       ║
║  Pantalla 2.2:                                                        ║
║  ┌─────────────────────────────────────────────────────────────────┐  ║
║  │                                                                 │  ║
║  │                    [Ilustración: Ligas]                         │  ║
║  │                                                                 │  ║
║  │         "Compite en Ligas con otros Cazadores"                  │  ║
║  │                                                                 │  ║
║  │         Demuestra quién es el más fuerte cada semana.           │  ║
║  │                                                                 │  ║
║  │                       [○●○]                                     │  ║
║  │                                                                 │  ║
║  └─────────────────────────────────────────────────────────────────┘  ║
║                                                                       ║
║  Pantalla 2.3:                                                        ║
║  ┌─────────────────────────────────────────────────────────────────┐  ║
║  │                                                                 │  ║
║  │                    [Ilustración: S-Rank]                        │  ║
║  │                                                                 │  ║
║  │         "Domina cada tema hasta alcanzar el Rango S"            │  ║
║  │                                                                 │  ║
║  │         El Sistema adaptará tu entrenamiento.                   │  ║
║  │                                                                 │  ║
║  │                       [○○●]                                     │  ║
║  │                                                                 │  ║
║  │              ┌─────────────────────────┐                        │  ║
║  │              │       COMENZAR          │                        │  ║
║  │              └─────────────────────────┘                        │  ║
║  └─────────────────────────────────────────────────────────────────┘  ║
║                                                                       ║
║  Técnico:                                                             ║
║  • Skip button visible después de 2s                                  ║
║  • Swipe horizontal o tap para avanzar                                ║
║  • Analytics: track cuántos skipean                                   ║
║                                                                       ║
╚═══════════════════════════════════════════════════════════════════════╝
                                   │
                                   ▼
╔═══════════════════════════════════════════════════════════════════════╗
║  PASO 3: QUICK SIGNUP (~30 segundos)                                  ║
╠═══════════════════════════════════════════════════════════════════════╣
║                                                                       ║
║  ┌─────────────────────────────────────────────────────────────────┐  ║
║  │                                                                 │  ║
║  │                 Únete a los Cazadores                           │  ║
║  │                                                                 │  ║
║  │  ┌─────────────────────────────────────────────────────────┐   │  ║
║  │  │  🔵  Continuar con Google                               │   │  ║
║  │  └─────────────────────────────────────────────────────────┘   │  ║
║  │                                                                 │  ║
║  │  ┌─────────────────────────────────────────────────────────┐   │  ║
║  │  │  ⚫  Continuar con Apple                                │   │  ║
║  │  └─────────────────────────────────────────────────────────┘   │  ║
║  │                                                                 │  ║
║  │  ───────────────────── o ─────────────────────                  │  ║
║  │                                                                 │  ║
║  │  ┌─────────────────────────────────────────────────────────┐   │  ║
║  │  │  📧  Usar correo electrónico                            │   │  ║
║  │  └─────────────────────────────────────────────────────────┘   │  ║
║  │                                                                 │  ║
║  │  Al continuar, aceptas los Términos del Sistema                 │  ║
║  │                                                                 │  ║
║  └─────────────────────────────────────────────────────────────────┘  ║
║                                                                       ║
║  Técnico:                                                             ║
║  • 1-tap signup preferido (Google/Apple)                              ║
║  • Email como fallback                                                ║
║  • No pedir nombre todavía (reducir fricción)                         ║
║  • Crear usuario en estado "onboarding_incomplete"                    ║
║                                                                       ║
╚═══════════════════════════════════════════════════════════════════════╝
                                   │
                                   ▼
╔═══════════════════════════════════════════════════════════════════════╗
║  PASO 4: QUICK DIAGNOSTIC (~5 minutos)                                ║
╠═══════════════════════════════════════════════════════════════════════╣
║                                                                       ║
║  INTRO (5 segundos):                                                  ║
║  ┌─────────────────────────────────────────────────────────────────┐  ║
║  │                                                                 │  ║
║  │         ⚡ EVALUACIÓN DE PODER INICIAL ⚡                        │  ║
║  │                                                                 │  ║
║  │    "El Sistema medirá tu fuerza actual, Cazador."               │  ║
║  │                                                                 │  ║
║  │    📊 15 preguntas                                              │  ║
║  │    ⏱️ ~5 minutos                                                │  ║
║  │    💡 Responde lo mejor que puedas                              │  ║
║  │                                                                 │  ║
║  │              ┌─────────────────────────┐                        │  ║
║  │              │    INICIAR EVALUACIÓN   │                        │  ║
║  │              └─────────────────────────┘                        │  ║
║  │                                                                 │  ║
║  └─────────────────────────────────────────────────────────────────┘  ║
║                                                                       ║
║  DURANTE EL DIAGNÓSTICO:                                              ║
║  ┌─────────────────────────────────────────────────────────────────┐  ║
║  │                                                                 │  ║
║  │    [████████████░░░░░░░░]  8/15                                 │  ║
║  │                                                                 │  ║
║  │    [Pregunta de Matemáticas - Media]                            │  ║
║  │                                                                 │  ║
║  │    Si f(x) = 2x + 3, ¿cuál es f(5)?                             │  ║
║  │                                                                 │  ║
║  │    ○ A) 10                                                      │  ║
║  │    ○ B) 13                                                      │  ║
║  │    ○ C) 15                                                      │  ║
║  │    ○ D) 8                                                       │  ║
║  │                                                                 │  ║
║  │              ┌─────────────────────────┐                        │  ║
║  │              │       CONFIRMAR         │                        │  ║
║  │              └─────────────────────────┘                        │  ║
║  │                                                                 │  ║
║  └─────────────────────────────────────────────────────────────────┘  ║
║                                                                       ║
║  REGLAS DEL QUICK DIAGNOSTIC:                                         ║
║  • 15 preguntas totales (3 por área × 5 áreas)                        ║
║  • Distribución por área: 1 fácil + 1 media + 1 difícil               ║
║  • SIN feedback de correcto/incorrecto (evita frustración)            ║
║  • Mide tiempo de respuesta (indica confianza)                        ║
║  • No consume corazones                                               ║
║  • No otorga XP                                                       ║
║                                                                       ║
║  Distribución:                                                        ║
║  ┌────────────────────┬─────────┬─────────────────────────┐           ║
║  │ Área               │ Preguntas│ Dificultad             │           ║
║  ├────────────────────┼─────────┼─────────────────────────┤           ║
║  │ Matemáticas        │ 3       │ 1 Fácil, 1 Media, 1 Dif │           ║
║  │ Lectura Crítica    │ 3       │ 1 Fácil, 1 Media, 1 Dif │           ║
║  │ Ciencias Naturales │ 3       │ 1 Fácil, 1 Media, 1 Dif │           ║
║  │ Sociales           │ 3       │ 1 Fácil, 1 Media, 1 Dif │           ║
║  │ Inglés             │ 3       │ 1 Fácil, 1 Media, 1 Dif │           ║
║  ├────────────────────┼─────────┼─────────────────────────┤           ║
║  │ TOTAL              │ 15      │ ~5 minutos              │           ║
║  └────────────────────┴─────────┴─────────────────────────┘           ║
║                                                                       ║
╚═══════════════════════════════════════════════════════════════════════╝
                                   │
                                   ▼
╔═══════════════════════════════════════════════════════════════════════╗
║  PASO 5: RESULTS REVEAL (~30 segundos)                                ║
╠═══════════════════════════════════════════════════════════════════════╣
║                                                                       ║
║  SECUENCIA DE ANIMACIÓN (3 segundos):                                 ║
║  T+0ms:    Pantalla fade a negro                                      ║
║  T+500ms:  Partículas de energía aparecen                             ║
║  T+1000ms: "DESPERTAR COMPLETADO" aparece con glow                    ║
║  T+1500ms: Rango E-RANK se revela con shake                           ║
║  T+2000ms: Número de puntaje hace count-up                            ║
║  T+2500ms: Radar chart se dibuja                                      ║
║  T+3000ms: Botón aparece                                              ║
║                                                                       ║
║  PANTALLA FINAL:                                                      ║
║  ┌─────────────────────────────────────────────────────────────────┐  ║
║  │                                                                 │  ║
║  │              ⚔️ DESPERTAR COMPLETADO ⚔️                          │  ║
║  │                                                                 │  ║
║  │  ┌───────────────────────────────────────────────────────────┐ │  ║
║  │  │                                                           │ │  ║
║  │  │                    TU RANGO INICIAL                       │ │  ║
║  │  │                                                           │ │  ║
║  │  │                      【 E-RANK 】                          │ │  ║
║  │  │                                                           │ │  ║
║  │  │              Puntaje ICFES Proyectado: ~280                │ │  ║
║  │  │                                                           │ │  ║
║  │  └───────────────────────────────────────────────────────────┘ │  ║
║  │                                                                 │  ║
║  │                    [RADAR CHART]                                │  ║
║  │                                                                 │  ║
║  │                    Matemáticas                                  │  ║
║  │                         ▲                                       │  ║
║  │                    80  /|\                                      │  ║
║  │                   60  / | \                                     │  ║
║  │                  40  /  ●  \    ● = Tu nivel                    │  ║
║  │                 20  /   |   \   ○ = Promedio nacional           │  ║
║  │        Inglés ◄────┼────┼────┼────► Lectura                     │  ║
║  │                 20  \   |   /                                   │  ║
║  │                  40  \  |  /                                    │  ║
║  │                   60  \ | /                                     │  ║
║  │                    80  \|/                                      │  ║
║  │                         ▼                                       │  ║
║  │            Sociales ◄───┼───► Ciencias                          │  ║
║  │                                                                 │  ║
║  │  ┌───────────────────────────────────────────────────────────┐ │  ║
║  │  │  ⚠️ DEBILIDAD DETECTADA: MATEMÁTICAS                      │ │  ║
║  │  │                                                           │ │  ║
║  │  │  "Tu primera misión: Conquistar el Reino de los Números"  │ │  ║
║  │  └───────────────────────────────────────────────────────────┘ │  ║
║  │                                                                 │  ║
║  │              ┌─────────────────────────┐                        │  ║
║  │              │   COMENZAR ENTRENAMIENTO │                       │  ║
║  │              └─────────────────────────┘                        │  ║
║  │                                                                 │  ║
║  └─────────────────────────────────────────────────────────────────┘  ║
║                                                                       ║
║  CÁLCULO DEL RANGO INICIAL:                                           ║
║  ┌────────────────┬─────────────────┬───────────────────┐             ║
║  │ % Correctas    │ Rango           │ Puntaje Proyectado│             ║
║  ├────────────────┼─────────────────┼───────────────────┤             ║
║  │ 0% - 35%       │ E-Rank          │ 200-280           │             ║
║  │ 35% - 50%      │ D-Rank          │ 280-320           │             ║
║  │ 50% - 65%      │ C-Rank          │ 320-380           │             ║
║  │ 65% - 80%      │ B-Rank          │ 380-420           │             ║
║  │ 80% - 90%      │ A-Rank          │ 420-470           │             ║
║  │ 90% - 100%     │ S-Rank          │ 470-500           │             ║
║  └────────────────┴─────────────────┴───────────────────┘             ║
║                                                                       ║
╚═══════════════════════════════════════════════════════════════════════╝
                                   │
                                   ▼
╔═══════════════════════════════════════════════════════════════════════╗
║  PASO 6: FIRST MISSION (~2 minutos)                                   ║
╠═══════════════════════════════════════════════════════════════════════╣
║                                                                       ║
║  OPCIÓN A: Deep Diagnostic del área más débil                         ║
║  ┌─────────────────────────────────────────────────────────────────┐  ║
║  │                                                                 │  ║
║  │    ⚔️ DUNGEON: REINO DE LOS NÚMEROS ⚔️                          │  ║
║  │                                                                 │  ║
║  │    "Antes de entrar, el Sistema debe calibrar                   │  ║
║  │     tu poder en esta área con más detalle."                     │  ║
║  │                                                                 │  ║
║  │    📊 18 preguntas                                              │  ║
║  │    ⏱️ ~12 minutos                                               │  ║
║  │                                                                 │  ║
║  │              ┌─────────────────────────┐                        │  ║
║  │              │   INICIAR CALIBRACIÓN   │                        │  ║
║  │              └─────────────────────────┘                        │  ║
║  │                                                                 │  ║
║  │              [Saltar por ahora]                                 │  ║
║  │                                                                 │  ║
║  └─────────────────────────────────────────────────────────────────┘  ║
║                                                                       ║
║  OPCIÓN B: Primera lección corta (si skipea diagnóstico)              ║
║  ┌─────────────────────────────────────────────────────────────────┐  ║
║  │                                                                 │  ║
║  │    🎯 PRIMERA MISIÓN                                            │  ║
║  │                                                                 │  ║
║  │    "Completa tu primera lección de 5 preguntas"                 │  ║
║  │                                                                 │  ║
║  │    📊 5 preguntas fáciles                                       │  ║
║  │    ⏱️ ~2 minutos                                                │  ║
║  │    ⚡ +50 XP de bienvenida                                      │  ║
║  │                                                                 │  ║
║  │              ┌─────────────────────────┐                        │  ║
║  │              │      COMENZAR           │                        │  ║
║  │              └─────────────────────────┘                        │  ║
║  │                                                                 │  ║
║  └─────────────────────────────────────────────────────────────────┘  ║
║                                                                       ║
║  AL TERMINAR:                                                         ║
║  • Celebración con confetti                                           ║
║  • "¡Primera misión completada!"                                      ║
║  • Marcar onboarding_completed = true                                 ║
║  • Mostrar tutorial de Home (tooltips opcionales)                     ║
║  • Push notification scheduled: "Vuelve mañana para tu racha"         ║
║                                                                       ║
╚═══════════════════════════════════════════════════════════════════════╝
```

### 3.3 Métricas del Onboarding

| Transición | Target | Alerta |
|------------|--------|--------|
| Splash → Value Prop | 95% | <90% |
| Value Prop → Signup | 80% | <70% |
| Signup → Diagnostic | 85% | <75% |
| Diagnostic → Results | 90% | <80% |
| Results → First Mission | 75% | <65% |
| **TOTAL (Instala → Completa)** | **>70%** | **<60%** |

---

## 4. SISTEMA DE DIAGNÓSTICO (DOS FASES)

### 4.1 Por qué Dos Fases

| Problema del diagnóstico largo | Nuestra solución |
|--------------------------------|------------------|
| 225 preguntas = 5 horas | Quick: 15 preguntas = 5 min |
| Usuario abandona antes de empezar | Engagement inmediato |
| Calibración gruesa inicial | Deep diagnostic cuando entra a cada área |
| No hay second chance | Calibración progresiva |

### 4.2 Fase 1: Quick Diagnostic

**Cuándo:** Paso 4 del onboarding (obligatorio)

```
┌─────────────────────────────────────────────────────────────────────┐
│                      QUICK DIAGNOSTIC                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  OBJETIVO: Calibración gruesa + detectar área más débil             │
│                                                                     │
│  PREGUNTAS: 15 totales                                              │
│  ├── Matemáticas:     3 (1 fácil + 1 media + 1 difícil)            │
│  ├── Lectura:         3 (1 fácil + 1 media + 1 difícil)            │
│  ├── Ciencias:        3 (1 fácil + 1 media + 1 difícil)            │
│  ├── Sociales:        3 (1 fácil + 1 media + 1 difícil)            │
│  └── Inglés:          3 (1 fácil + 1 media + 1 difícil)            │
│                                                                     │
│  TIEMPO: ~5 minutos                                                 │
│                                                                     │
│  FEEDBACK: NINGUNO (no mostrar correcto/incorrecto)                 │
│                                                                     │
│  OUTPUT:                                                            │
│  ├── Rango inicial (E-Rank a S-Rank)                               │
│  ├── Puntaje ICFES proyectado                                       │
│  ├── Score por área (% correctas)                                   │
│  ├── Área más débil identificada                                    │
│  └── Radar chart vs promedio nacional                               │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 4.3 Fase 2: Deep Diagnostic (Por Área)

**Cuándo:** Primera vez que el usuario entra a un "Dungeon" (área)

```
┌─────────────────────────────────────────────────────────────────────┐
│                      DEEP DIAGNOSTIC                                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  OBJETIVO: Calibración detallada por subtema                        │
│                                                                     │
│  TRIGGER: Primera vez que entra a cada área                         │
│                                                                     │
│  UI: "El Sistema debe calibrar tu poder en esta área..."            │
│                                                                     │
│  DISTRIBUCIÓN POR ÁREA:                                             │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │ MATEMÁTICAS (18 preguntas, ~12 min)                          │   │
│  ├──────────────────────────────────────────────────────────────┤   │
│  │ Subtema                │ Preguntas │ Distribución            │   │
│  │ ───────────────────────┼───────────┼──────────────────────── │   │
│  │ Álgebra y funciones    │ 4         │ 1F + 2M + 1D            │   │
│  │ Geometría              │ 4         │ 1F + 2M + 1D            │   │
│  │ Estadística            │ 4         │ 1F + 2M + 1D            │   │
│  │ Aritmética             │ 3         │ 1F + 1M + 1D            │   │
│  │ Cálculo                │ 3         │ 1F + 1M + 1D            │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │ LECTURA CRÍTICA (15 preguntas, ~15 min)                      │   │
│  ├──────────────────────────────────────────────────────────────┤   │
│  │ Subtema                │ Preguntas │ Distribución            │   │
│  │ ───────────────────────┼───────────┼──────────────────────── │   │
│  │ Comprensión literal    │ 5         │ 2F + 2M + 1D            │   │
│  │ Inferencia             │ 5         │ 1F + 2M + 2D            │   │
│  │ Evaluación crítica     │ 5         │ 1F + 2M + 2D            │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │ CIENCIAS NATURALES (18 preguntas, ~12 min)                   │   │
│  ├──────────────────────────────────────────────────────────────┤   │
│  │ Subtema                │ Preguntas │ Distribución            │   │
│  │ ───────────────────────┼───────────┼──────────────────────── │   │
│  │ Física                 │ 6         │ 2F + 2M + 2D            │   │
│  │ Química                │ 6         │ 2F + 2M + 2D            │   │
│  │ Biología               │ 6         │ 2F + 2M + 2D            │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │ SOCIALES (15 preguntas, ~10 min)                             │   │
│  ├──────────────────────────────────────────────────────────────┤   │
│  │ Subtema                │ Preguntas │ Distribución            │   │
│  │ ───────────────────────┼───────────┼──────────────────────── │   │
│  │ Historia               │ 5         │ 2F + 2M + 1D            │   │
│  │ Geografía              │ 5         │ 2F + 2M + 1D            │   │
│  │ Competencias ciudadanas│ 5         │ 2F + 2M + 1D            │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │ INGLÉS (15 preguntas, ~10 min)                               │   │
│  ├──────────────────────────────────────────────────────────────┤   │
│  │ Subtema                │ Preguntas │ Distribución            │   │
│  │ ───────────────────────┼───────────┼──────────────────────── │   │
│  │ Grammar                │ 5         │ 2F + 2M + 1D            │   │
│  │ Vocabulary in context  │ 5         │ 2F + 2M + 1D            │   │
│  │ Reading comprehension  │ 5         │ 1F + 2M + 2D            │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  OUTPUT:                                                            │
│  ├── TopicMasteryMap detallado por subtema                         │
│  ├── Skill Tree del área desbloqueado                              │
│  ├── Ruta de aprendizaje personalizada                             │
│  └── Subtema más débil identificado                                │
│                                                                     │
│  FEEDBACK: NINGUNO durante el diagnóstico                           │
│                                                                     │
│  OPCIÓN SKIP: Disponible pero no recomendada                        │
│  └── Si skipea: mastery inicial = 0.3 para todos los subtemas      │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 4.4 Algoritmo de Calibración de Mastery

```dart
/// Calcula el mastery inicial basado en correctitud y tiempo
double calculateInitialMastery({
  required bool correct,
  required int timeSpentSeconds,
  required int expectedTimeSeconds,  // Tiempo promedio para esa dificultad
}) {
  if (!correct) {
    return 0.2;  // Incorrecto = conocimiento muy bajo
  }
  
  final timeRatio = timeSpentSeconds / expectedTimeSeconds;
  
  if (timeRatio < 0.5) {
    // Muy rápido + correcto = alta confianza
    return 0.8;
  } else if (timeRatio < 1.0) {
    // Tiempo normal + correcto = buena confianza
    return 0.6;
  } else if (timeRatio < 2.0) {
    // Un poco lento + correcto = conocimiento presente pero no dominado
    return 0.4;
  } else {
    // Muy lento + correcto = conocimiento frágil (quizás adivinó)
    return 0.3;
  }
}
```

---

## 5. CICLO DE PRÁCTICA DIARIA

### 5.1 Flujo de una Sesión de Práctica

```
┌─────────────────────────────────────────────────────────────────────┐
│                    CICLO DE PRÁCTICA DIARIA                         │
└─────────────────────────────────────────────────────────────────────┘

                          ┌─────────────┐
                          │    HOME     │
                          │  Dashboard  │
                          └──────┬──────┘
                                 │
            ┌────────────────────┼────────────────────┐
            │                    │                    │
            ▼                    ▼                    ▼
    ┌───────────────┐    ┌───────────────┐    ┌───────────────┐
    │   PRÁCTICA    │    │    LIGAS      │    │   PERFIL      │
    │   (Dungeons)  │    │   (Rankings)  │    │   (Stats)     │
    └───────┬───────┘    └───────────────┘    └───────────────┘
            │
            ▼
    ┌───────────────────────────────────────────────────────────┐
    │                 SELECCIÓN DE ÁREA                         │
    │                                                           │
    │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐     │
    │  │  MATE   │  │ LECTURA │  │ CIENCIAS│  │SOCIALES │     │
    │  │  📐     │  │   📖    │  │   🔬    │  │   🌍    │     │
    │  └─────────┘  └─────────┘  └─────────┘  └─────────┘     │
    │                     ┌─────────┐                          │
    │                     │ INGLÉS  │                          │
    │                     │   🇬🇧   │                          │
    │                     └─────────┘                          │
    └───────────────────────────────────────────────────────────┘
            │
            ▼
    ┌───────────────────────────────────────────────────────────┐
    │              ¿PRIMERA VEZ EN ESTA ÁREA?                   │
    │                                                           │
    │         SÍ                              NO                │
    │          │                               │                │
    │          ▼                               ▼                │
    │  ┌───────────────┐              ┌───────────────┐        │
    │  │    DEEP       │              │   SELECCIÓN   │        │
    │  │  DIAGNOSTIC   │              │   DE LECCIÓN  │        │
    │  │  (15-18 preg) │              │               │        │
    │  └───────────────┘              └───────────────┘        │
    └───────────────────────────────────────────────────────────┘
            │
            ▼
    ┌───────────────────────────────────────────────────────────┐
    │                  SESIÓN DE PRÁCTICA                       │
    │                                                           │
    │  ┌─────────────────────────────────────────────────────┐ │
    │  │                                                     │ │
    │  │    Pregunta 7 de 15           ❤️ 4    🔥 12        │ │
    │  │                                                     │ │
    │  │    [████████████░░░░░░░░]                           │ │
    │  │                                                     │ │
    │  │    Si f(x) = 2x + 3, ¿cuál es f(5)?                │ │
    │  │                                                     │ │
    │  │    ○ A) 10                                         │ │
    │  │    ● B) 13  ← [SELECCIONADO]                       │ │
    │  │    ○ C) 15                                         │ │
    │  │    ○ D) 8                                          │ │
    │  │                                                     │ │
    │  │                ⚡ COMBO 3x                          │ │
    │  │                                                     │ │
    │  │    ┌─────────────────────────────────────────────┐ │ │
    │  │    │              COMPROBAR                      │ │ │
    │  │    └─────────────────────────────────────────────┘ │ │
    │  │                                                     │ │
    │  └─────────────────────────────────────────────────────┘ │
    │                                                           │
    │  LÓGICA:                                                  │
    │  • Pregunta seleccionada por algoritmo SM-2 adaptativo   │
    │  • Timer corriendo en background (para analytics)         │
    │  • No hay timer visible (reduce ansiedad)                 │
    │  • Combo visible si >= 2                                  │
    │                                                           │
    └───────────────────────────────────────────────────────────┘
            │
            ├─────────────────────────────────────────┐
            │                                         │
            ▼                                         ▼
    ┌───────────────┐                        ┌───────────────┐
    │   CORRECTO    │                        │  INCORRECTO   │
    │               │                        │               │
    │  ✓ +10 XP     │                        │  ✗ -1 ❤️      │
    │  ✓ Combo +1   │                        │  ✗ Combo = 0  │
    │  ✓ Mastery ↑  │                        │  ✗ Mastery ↓  │
    └───────────────┘                        └───────────────┘
            │                                         │
            │                                         ▼
            │                                ┌───────────────┐
            │                                │  EXPLICACIÓN  │
            │                                │               │
            │                                │  "La respuesta│
            │                                │   correcta es │
            │                                │   B porque... │
            │                                │               │
            │                                │  📺 Ver video │
            │                                └───────────────┘
            │                                         │
            └─────────────────────────────────────────┘
                                 │
                                 ▼
                        ┌───────────────┐
                        │  ¿CORAZONES   │
                        │    = 0?       │
                        └───────┬───────┘
                                │
            ┌───────────────────┼───────────────────┐
            │                   │                   │
            ▼                   ▼                   ▼
    ┌───────────────┐   ┌───────────────┐   ┌───────────────┐
    │   CONTINUAR   │   │  GRACE MODE   │   │   RECUPERAR   │
    │   (Corazones  │   │  (Practica    │   │   CORAZONES   │
    │    > 0)       │   │   sin XP)     │   │   (Ad/Espera) │
    └───────────────┘   └───────────────┘   └───────────────┘
            │
            ▼
    ┌───────────────────────────────────────────────────────────┐
    │                 ¿LECCIÓN TERMINADA?                       │
    │                 (15 preguntas o usuario sale)             │
    └───────────────────────────────────────────────────────────┘
            │
            ▼
    ┌───────────────────────────────────────────────────────────┐
    │                PANTALLA DE RESULTADOS                     │
    │                                                           │
    │  ┌─────────────────────────────────────────────────────┐ │
    │  │                                                     │ │
    │  │                      🎊                             │ │
    │  │                                                     │ │
    │  │           ¡LECCIÓN COMPLETADA!                      │ │
    │  │                                                     │ │
    │  │  ─────────────────────────────────────────────────  │ │
    │  │  Respuestas Correctas           12/15              │ │
    │  │  ─────────────────────────────────────────────────  │ │
    │  │  XP Ganado                     +120 ⚡              │ │
    │  │  ─────────────────────────────────────────────────  │ │
    │  │  Combo Máximo                    5x 🔥             │ │
    │  │  ─────────────────────────────────────────────────  │ │
    │  │  Oro Ganado                     +10 🪙             │ │
    │  │  ─────────────────────────────────────────────────  │ │
    │  │                                                     │ │
    │  │  ⭐⭐⭐ (3 estrellas)                               │ │
    │  │                                                     │ │
    │  │    ┌─────────────────────────────────────────────┐ │ │
    │  │    │              FINALIZAR                      │ │ │
    │  │    └─────────────────────────────────────────────┘ │ │
    │  │                                                     │ │
    │  └─────────────────────────────────────────────────────┘ │
    │                                                           │
    │  ESTRELLAS:                                               │
    │  ⭐⭐⭐ = 80%+ correctas (12+/15)                         │
    │  ⭐⭐☆ = 60-79% correctas (9-11/15)                       │
    │  ⭐☆☆ = 40-59% correctas (6-8/15)                         │
    │  (Sin estrellas si <40%)                                  │
    │                                                           │
    └───────────────────────────────────────────────────────────┘
```

### 5.2 Preguntas por Lección

| Tipo de Lección | Preguntas | Tiempo Estimado |
|-----------------|-----------|-----------------|
| Lección Normal | 15 | ~8-10 min |
| Repaso Rápido | 10 | ~5 min |
| Boss Raid | 20 | ~25 min |
| Deep Diagnostic | 15-18 | ~10-15 min |

---

## 6. SISTEMA DE CORAZONES (MANA)

### 6.1 Configuración Base

| Parámetro | Valor | Justificación |
|-----------|-------|---------------|
| **Máximo** | 5 | Equilibrio entre presión y generosidad |
| **Regeneración** | 1 cada 4 horas | 20h para full (no frustrante) |
| **Pérdida** | 1 por error | Consecuencia tangible |
| **Recuperación por Ad** | +1 | Máx 3 ads/día |
| **Recuperación por Repaso** | +1 | Ilimitado |

### 6.2 Flujo de Decisión de Corazones

```
┌─────────────────────────────────────────────────────────────────────┐
│                     RESPUESTA INCORRECTA                            │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │   hearts = hearts - 1 │
                    └───────────┬───────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │    ¿hearts == 0?      │
                    └───────────┬───────────┘
                                │
            ┌───────────────────┼───────────────────┐
            │ NO                │                   │ SÍ
            ▼                   │                   ▼
    ┌───────────────┐           │           ┌───────────────┐
    │   Continuar   │           │           │   OPCIONES    │
    │   sesión      │           │           │   DE RECARGA  │
    └───────────────┘           │           └───────┬───────┘
                                │                   │
                                │   ┌───────────────┼───────────────┐
                                │   │               │               │
                                │   ▼               ▼               ▼
                                │ ┌─────────┐ ┌─────────┐ ┌─────────────┐
                                │ │  VER    │ │ ESPERAR │ │   GRACE     │
                                │ │ANUNCIO  │ │  4H     │ │   MODE      │
                                │ │(si <3)  │ │         │ │             │
                                │ └────┬────┘ └────┬────┘ └──────┬──────┘
                                │      │           │             │
                                │      ▼           ▼             ▼
                                │  +1 ❤️       +1 ❤️ auto    Practica
                                │                             sin XP
                                │                             sin Oro
                                │                             SÍ Mastery
                                └───────────────────────────────────────
```

### 6.3 Grace Mode (Modo Entrenamiento)

**Propósito:** Nunca bloquear completamente al usuario motivado.

```
┌─────────────────────────────────────────────────────────────────────┐
│                         GRACE MODE                                  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ACTIVACIÓN: Automática cuando hearts == 0                          │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │                                                               │ │
│  │   ⚠️ MODO ENTRENAMIENTO ACTIVO                                │ │
│  │                                                               │ │
│  │   Tu Mana se ha agotado. Puedes seguir entrenando            │ │
│  │   pero no ganarás XP ni Oro hasta regenerar.                  │ │
│  │                                                               │ │
│  │   ✅ Cuenta para Mastery personal                             │ │
│  │   ✅ Actualiza tu progreso de tema                            │ │
│  │   ❌ No ganas XP                                              │ │
│  │   ❌ No ganas Oro                                             │ │
│  │   ❌ No cuenta para la Liga                                   │ │
│  │                                                               │ │
│  │   ⏰ Próximo Mana en: 2h 34m                                  │ │
│  │                                                               │ │
│  │   ┌─────────────────┐  ┌─────────────────────────────┐       │ │
│  │   │  VER ANUNCIO    │  │   ENTRENAR SIN RANGO       │       │ │
│  │   │  (+1 Mana)      │  │                             │       │ │
│  │   └─────────────────┘  └─────────────────────────────┘       │ │
│  │                                                               │ │
│  └───────────────────────────────────────────────────────────────┘ │
│                                                                     │
│  BENEFICIO ÉTICO:                                                   │
│  • Usuario motivado nunca está completamente bloqueado              │
│  • Aprendizaje real continúa (mastery)                              │
│  • Solo se pierde la parte "competitiva" (XP/Liga)                  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 6.4 Validación de Anuncios (Anti-Fraud)

```dart
class AdRewardService {
  static const int maxAdsPerDay = 3;
  
  Future<bool> canWatchAd(String userId) async {
    final user = await getUser(userId);
    final today = DateTime.now().toDateOnly();
    
    // Reset contador si es nuevo día
    if (user.adsWatchedDate != today) {
      await resetAdsCounter(userId, today);
      return true;
    }
    
    return user.adsWatchedToday < maxAdsPerDay;
  }
  
  Future<void> rewardAdWatch(String userId, String adId) async {
    // 1. Verificar que el ad fue completado (callback del ad network)
    final adCompleted = await verifyAdCompletion(adId);
    if (!adCompleted) {
      // Guardar reward pendiente para entrega posterior
      await queuePendingReward(userId, RewardType.heart, 1);
      return;
    }
    
    // 2. Otorgar corazón
    await incrementHearts(userId, 1);
    
    // 3. Incrementar contador de ads
    await incrementAdsWatched(userId);
    
    // 4. Log para analytics
    await logEvent('ad_reward_granted', {userId, adId});
  }
}
```

### 6.5 Regeneración de Corazones

```dart
class HeartRegenerationService {
  static const Duration regenInterval = Duration(hours: 4);
  static const int maxHearts = 5;
  
  /// Llamado cada vez que se abre la app o cada minuto
  Future<int> calculateCurrentHearts(User user) async {
    if (user.hearts >= maxHearts) {
      return maxHearts;
    }
    
    final now = DateTime.now();
    final timeSinceLastRegen = now.difference(user.lastHeartRegen);
    final heartsToRegenerate = timeSinceLastRegen.inMinutes ~/ regenInterval.inMinutes;
    
    if (heartsToRegenerate > 0) {
      final newHearts = min(user.hearts + heartsToRegenerate, maxHearts);
      final leftoverMinutes = timeSinceLastRegen.inMinutes % regenInterval.inMinutes;
      final newLastRegen = now.subtract(Duration(minutes: leftoverMinutes));
      
      await updateUser(user.id, {
        'hearts': newHearts,
        'last_heart_regen': newLastRegen,
      });
      
      return newHearts;
    }
    
    return user.hearts;
  }
  
  /// Retorna tiempo hasta próximo corazón
  Duration timeUntilNextHeart(User user) {
    if (user.hearts >= maxHearts) {
      return Duration.zero;
    }
    
    final timeSinceLastRegen = DateTime.now().difference(user.lastHeartRegen);
    final minutesUntilNext = regenInterval.inMinutes - 
        (timeSinceLastRegen.inMinutes % regenInterval.inMinutes);
    
    return Duration(minutes: minutesUntilNext);
  }
}
```

---

## 7. SISTEMA DE RACHAS (STREAKS)

### 7.1 Configuración Base

| Parámetro | Valor | Justificación |
|-----------|-------|---------------|
| **Meta diaria** | 20 XP | ~2-3 preguntas correctas |
| **Reset del día** | 4:00 AM local | Protege estudiantes nocturnos |
| **Streak Freeze costo** | 200 Oro | Protege 1 día automáticamente |
| **Streak Repair costo** | 300 Oro o 1 Ad | Ventana de 24h |

### 7.2 Lógica de Timezone (4:00 AM)

```dart
class StreakService {
  static const int dayResetHour = 4; // 4:00 AM
  
  /// Calcula la fecha "de estudio" considerando el reset a las 4 AM
  Date getStudyDate(DateTime timestamp, String timezone) {
    final localTime = timestamp.toTimezone(timezone);
    
    // Si es antes de las 4 AM, cuenta como el día anterior
    if (localTime.hour < dayResetHour) {
      return localTime.subtract(Duration(days: 1)).toDateOnly();
    }
    
    return localTime.toDateOnly();
  }
  
  /// Calcula deadline para mantener racha
  DateTime getStreakDeadline(DateTime now, String timezone) {
    final localNow = now.toTimezone(timezone);
    
    if (localNow.hour < dayResetHour) {
      // Deadline es hoy a las 4 AM
      return DateTime(localNow.year, localNow.month, localNow.day, dayResetHour)
          .toTimezone(timezone);
    } else {
      // Deadline es mañana a las 4 AM
      return DateTime(localNow.year, localNow.month, localNow.day + 1, dayResetHour)
          .toTimezone(timezone);
    }
  }
  
  /// Verifica si la racha está en peligro
  bool isStreakAtRisk(User user) {
    final todayStudyDate = getStudyDate(DateTime.now(), user.timezone);
    return user.lastActivityDate != todayStudyDate && user.currentStreak > 0;
  }
}
```

### 7.3 Streak Freeze (Protección Automática)

```
┌─────────────────────────────────────────────────────────────────────┐
│                       STREAK FREEZE                                 │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  COSTO: 200 Oro                                                     │
│  DURACIÓN: Protege 1 día de inactividad                             │
│  ACTIVACIÓN: AUTOMÁTICA si el usuario no estudia                    │
│                                                                     │
│  FLUJO:                                                             │
│                                                                     │
│      Usuario tiene Streak Freeze en inventario                      │
│                           │                                         │
│                           ▼                                         │
│      Pasa 4:00 AM sin haber ganado 20 XP                           │
│                           │                                         │
│                           ▼                                         │
│      ┌─────────────────────────────────────────┐                   │
│      │  Sistema consume Streak Freeze          │                   │
│      │  automáticamente                        │                   │
│      └─────────────────────────────────────────┘                   │
│                           │                                         │
│                           ▼                                         │
│      Racha se mantiene (no aumenta)                                 │
│      streak_freeze_count -= 1                                       │
│                           │                                         │
│                           ▼                                         │
│      Notificación: "❄️ Tu Streak Freeze te salvó"                  │
│                                                                     │
│  LÍMITE: Usuario puede tener máximo 5 Streak Freeze acumulados      │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 7.4 Streak Repair (Recuperación de Racha)

```
┌─────────────────────────────────────────────────────────────────────┐
│                       STREAK REPAIR                                 │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  VENTANA: 24 horas después de perder la racha                       │
│  COSTO: 300 Oro O ver 1 anuncio                                     │
│                                                                     │
│  FLUJO:                                                             │
│                                                                     │
│      Usuario perdió racha (pasó 4 AM sin freeze)                    │
│                           │                                         │
│                           ▼                                         │
│      streak_lost_at = timestamp actual                              │
│      current_streak = 0 (temporal)                                  │
│      recoverable_streak = valor anterior                            │
│                           │                                         │
│                           ▼                                         │
│      Usuario abre app dentro de 24h                                 │
│                           │                                         │
│                           ▼                                         │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                                                             │   │
│  │   💔 ¡Tu racha de 12 días se perdió!                        │   │
│  │                                                             │   │
│  │   Pero aún puedes recuperarla:                              │   │
│  │                                                             │   │
│  │   ⏰ Tiempo restante: 18h 42m                               │   │
│  │                                                             │   │
│  │   ┌─────────────────┐  ┌─────────────────┐                 │   │
│  │   │  REPARAR (300🪙) │  │  VER ANUNCIO    │                 │   │
│  │   └─────────────────┘  └─────────────────┘                 │   │
│  │                                                             │   │
│  │   [Aceptar pérdida]                                         │   │
│  │                                                             │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  SI REPARA:                                                         │
│      current_streak = recoverable_streak                            │
│      (racha restaurada al valor anterior)                           │
│                                                                     │
│  SI NO REPARA (pasan 24h o acepta pérdida):                         │
│      current_streak = 0                                             │
│      recoverable_streak = null                                      │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 7.5 Multiplicadores de Racha

| Días de Racha | Multiplicador XP | Bonus Especial |
|---------------|------------------|----------------|
| 1-6 días | 1.0× | — |
| 7-13 días | 1.2× | +50 Oro al día 7 |
| 14-29 días | 1.5× | +100 Oro al día 14 |
| 30-59 días | 1.8× | +200 Oro + Badge al día 30 |
| 60+ días | 2.0× | +500 Oro + Badge Épico al día 60 |

---

## 8. SISTEMA DE XP Y NIVELES

### 8.1 Fuentes de XP (Simplificado)

```
┌─────────────────────────────────────────────────────────────────────┐
│                    SISTEMA DE XP SIMPLIFICADO                       │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  REGLA FUNDAMENTAL:                                                 │
│  Solo hay XP por aprendizaje NUEVO o VÁLIDO                        │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ ACCIÓN                          │ XP      │ CONDICIÓN       │   │
│  ├─────────────────────────────────┼─────────┼─────────────────│   │
│  │ Pregunta NUEVA correcta         │ +10     │ Nunca respondida│   │
│  │ Repaso VÁLIDO correcto          │ +5      │ Ver fórmula*    │   │
│  │ Repetición inválida correcta    │ 0       │ Anti-farming    │   │
│  │ Cualquier respuesta incorrecta  │ 0       │ —               │   │
│  ├─────────────────────────────────┼─────────┼─────────────────│   │
│  │ Lección completada (3 ⭐)        │ +15     │ 80%+ correctas  │   │
│  │ Lección completada (2 ⭐)        │ +10     │ 60-79%          │   │
│  │ Lección completada (1 ⭐)        │ +5      │ 40-59%          │   │
│  ├─────────────────────────────────┼─────────┼─────────────────│   │
│  │ Boss Raid                       │ ×3      │ Multiplicador   │   │
│  │ Racha activa                    │ ×1.2-2.0│ Según días      │   │
│  └─────────────────────────────────┴─────────┴─────────────────┘   │
│                                                                     │
│  * FÓRMULA DE REPASO VÁLIDO:                                        │
│                                                                     │
│    Un repaso es válido si:                                          │
│    días_desde_último >= ceil(mastery × 7)                           │
│                                                                     │
│    Ejemplo:                                                         │
│    - mastery = 0.5 → necesita 4 días para ser válido                │
│    - mastery = 0.8 → necesita 6 días para ser válido                │
│    - mastery = 1.0 → necesita 7 días para ser válido                │
│                                                                     │
│  PROPÓSITO:                                                         │
│  Evitar que usuarios farmeen XP repitiendo preguntas fáciles        │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 8.2 Algoritmo Anti-Gaming

```dart
class XPCalculator {
  static const int xpNewQuestion = 10;
  static const int xpValidReview = 5;
  static const int xpInvalidRepeat = 0;
  
  Future<int> calculateXP({
    required String userId,
    required String questionId,
    required bool correct,
  }) async {
    if (!correct) return 0;
    
    final history = await getQuestionHistory(userId, questionId);
    
    // CASO 1: Pregunta nueva
    if (history == null) {
      return xpNewQuestion;
    }
    
    // CASO 2: Ya respondida - verificar si es repaso válido
    final daysSinceLastAttempt = DateTime.now()
        .difference(history.lastAttempt)
        .inDays;
    
    final topicMastery = await getTopicMastery(userId, history.topicId);
    final minDaysRequired = (topicMastery * 7).ceil();
    
    if (daysSinceLastAttempt >= minDaysRequired) {
      return xpValidReview;  // Repaso válido
    }
    
    return xpInvalidRepeat;  // Repetición inválida = 0 XP
  }
}
```

### 8.3 Progresión de Niveles

```dart
class LevelSystem {
  /// Fórmula simplificada: XP necesario = nivel² × 100
  static int xpRequiredForLevel(int level) {
    return level * level * 100;
  }
  
  /// XP total acumulado para alcanzar un nivel
  static int totalXPForLevel(int level) {
    int total = 0;
    for (int i = 1; i < level; i++) {
      total += xpRequiredForLevel(i);
    }
    return total;
  }
  
  /// Calcular nivel actual dado XP total
  static int calculateLevel(int totalXP) {
    int level = 1;
    int xpUsed = 0;
    
    while (xpUsed + xpRequiredForLevel(level) <= totalXP) {
      xpUsed += xpRequiredForLevel(level);
      level++;
    }
    
    return level;
  }
}

// TABLA DE REFERENCIA:
// Nivel 1:   0 XP (inicio)
// Nivel 2:   100 XP
// Nivel 5:   1,000 XP total
// Nivel 10:  4,500 XP total
// Nivel 20:  19,000 XP total
// Nivel 50:  120,000 XP total
```

---

## 9. SISTEMA DE LIGAS (RANKINGS)

### 9.1 Estructura de Divisiones

```
┌─────────────────────────────────────────────────────────────────────┐
│                    SISTEMA DE LIGAS SEMANAL                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  DIVISIONES (6 tiers):                                              │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ Tier │ División     │ Color     │ Requisito de Entrada      │   │
│  ├──────┼──────────────┼───────────┼───────────────────────────│   │
│  │  1   │ 🥉 Bronze    │ #CD7F32   │ Nuevo usuario             │   │
│  │  2   │ 🥈 Silver    │ #C0C0C0   │ Top 10 en Bronze          │   │
│  │  3   │ 🥇 Gold      │ #FFD700   │ Top 10 en Silver          │   │
│  │  4   │ 💎 Platinum  │ #E5E4E2   │ Top 10 en Gold            │   │
│  │  5   │ 💠 Diamond   │ #B9F2FF   │ Top 10 en Platinum        │   │
│  │  6   │ ⚔️ S-Rank    │ #B829DD   │ Top 10 en Diamond         │   │
│  └──────┴──────────────┴───────────┴───────────────────────────┘   │
│                                                                     │
│  MECÁNICA:                                                          │
│  • Grupos de 30 usuarios (no 50)                                    │
│  • Ciclo: Lunes 00:00 → Domingo 23:59 (hora Colombia)              │
│  • Top 10 (33%) suben de división                                   │
│  • Bottom 5 (17%) bajan de división                                 │
│  • Middle 15 (50%) se mantienen                                     │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────┐      │
│  │                                                          │      │
│  │    GRUPO DE LIGA (30 usuarios)                           │      │
│  │                                                          │      │
│  │    ┌──────────────────────────────┐ ← Top 10             │      │
│  │    │  1. María      2,450 XP  ⬆️  │   ASCIENDEN          │      │
│  │    │  2. Carlos     2,180 XP  ⬆️  │                      │      │
│  │    │  3. Ana        1,990 XP  ⬆️  │                      │      │
│  │    │  ...                         │                      │      │
│  │    │  10. Pedro     1,200 XP  ⬆️  │                      │      │
│  │    ├──────────────────────────────┤ ← Middle 15          │      │
│  │    │  11. Luis      1,150 XP  ➡️  │   SE MANTIENEN       │      │
│  │    │  ...                         │                      │      │
│  │    │  25. Sofia       450 XP  ➡️  │                      │      │
│  │    ├──────────────────────────────┤ ← Bottom 5           │      │
│  │    │  26. Juan        380 XP  ⬇️  │   DESCIENDEN         │      │
│  │    │  27. Rosa        290 XP  ⬇️  │                      │      │
│  │    │  28. David       150 XP  ⬇️  │                      │      │
│  │    │  29. Elena        80 XP  ⬇️  │                      │      │
│  │    │  30. Miguel       20 XP  ⬇️  │                      │      │
│  │    └──────────────────────────────┘                      │      │
│  │                                                          │      │
│  └──────────────────────────────────────────────────────────┘      │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 9.2 Jobs del Sistema de Ligas

```dart
class LeagueJobs {
  /// JOB 1: Ejecutar cada lunes a las 00:00 COT
  /// Asigna usuarios a grupos nuevos
  Future<void> weeklyLeagueAssignment() async {
    final activeUsers = await getActiveUsersLastWeek();
    
    for (final division in Division.values) {
      final usersInDivision = activeUsers
          .where((u) => u.currentDivision == division)
          .toList();
      
      // Shuffle para aleatorizar grupos
      usersInDivision.shuffle(Random());
      
      // Crear grupos de 30
      for (var i = 0; i < usersInDivision.length; i += 30) {
        final groupUsers = usersInDivision.sublist(
          i, 
          min(i + 30, usersInDivision.length),
        );
        
        final group = await createLeagueGroup(
          division: division,
          weekStart: DateTime.now(),
        );
        
        for (final user in groupUsers) {
          await assignUserToGroup(user.id, group.id);
        }
      }
    }
  }
  
  /// JOB 2: Ejecutar cada domingo a las 23:59 COT
  /// Procesa resultados y promociones/relegaciones
  Future<void> weeklyLeagueProcess() async {
    final groups = await getActiveLeagueGroups();
    
    for (final group in groups) {
      final rankings = await getRankingsByXP(group.id);
      
      // Top 10 ascienden
      for (int i = 0; i < 10 && i < rankings.length; i++) {
        await promoteUser(rankings[i].userId);
        await sendNotification(
          rankings[i].userId,
          '⬆️ [SISTEMA] Ascendiste a Liga ${getNextDivision(group.division)}',
        );
      }
      
      // Bottom 5 descienden
      final total = rankings.length;
      for (int i = max(0, total - 5); i < total; i++) {
        await relegateUser(rankings[i].userId);
        await sendNotification(
          rankings[i].userId,
          '⬇️ [SISTEMA] Descendiste. Entrena más duro.',
        );
      }
      
      // Recompensas
      await distributeLeagueRewards(group.id, rankings);
    }
    
    // Marcar semana como procesada
    await markWeekProcessed();
  }
}
```

### 9.3 Recompensas de Liga

| Posición | Oro | XP Bonus |
|----------|-----|----------|
| 1° lugar | 150 | +100 |
| 2° lugar | 100 | +75 |
| 3° lugar | 75 | +50 |
| Top 10 | 50 | +25 |
| Top 15 | 25 | +10 |
| Resto | 10 | 0 |

---

## 10. SISTEMA DE COMBOS

### 10.1 Mecánica de Combos

```
┌─────────────────────────────────────────────────────────────────────┐
│                      SISTEMA DE COMBOS                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  REGLA: Respuestas correctas consecutivas                           │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ Correctas │ Combo │ UI Feedback          │ Bonus XP         │   │
│  │ Seguidas  │       │                      │                  │   │
│  ├───────────┼───────┼──────────────────────┼──────────────────│   │
│  │ 1         │ —     │ Solo "+10 XP"        │ 0                │   │
│  │ 2         │ 2×    │ "¡Bien!"             │ +2 XP por combo  │   │
│  │ 3         │ 3×    │ "¡Excelente!" ✨      │ +3 XP            │   │
│  │ 5         │ 5×    │ "¡IMPARABLE!" 💥     │ +5 XP + shake    │   │
│  │ 7         │ 7×    │ "🔥 ON FIRE!"        │ +7 XP + flames   │   │
│  │ 10        │ 10×   │ "⚡ LEGENDARIO!"     │ +10 XP + explosion│  │
│  │ 15+       │ 15×+  │ "👑 INVENCIBLE!"     │ +15 XP + glow    │   │
│  └───────────┴───────┴──────────────────────┴──────────────────┘   │
│                                                                     │
│  RESET:                                                             │
│  • Respuesta incorrecta → combo = 0                                 │
│  • Timeout 30s sin responder → combo = 0                            │
│  • Salir de la sesión → combo = 0                                   │
│                                                                     │
│  MULTIPLICADOR DE COMBO (XP extra):                                 │
│  XP_bonus = min(combo, 15)                                          │
│                                                                     │
│  EJEMPLO:                                                           │
│  Pregunta correcta con combo 7:                                     │
│  Base: 10 XP + Combo bonus: 7 XP = 17 XP total                     │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 10.2 Feedback Visual de Combos

```dart
class ComboFeedback {
  static ComboDisplay getComboDisplay(int combo) {
    if (combo < 2) {
      return ComboDisplay.none;
    }
    
    return ComboDisplay(
      text: combo >= 15 ? '👑 INVENCIBLE!' :
            combo >= 10 ? '⚡ LEGENDARIO!' :
            combo >= 7  ? '🔥 ON FIRE!' :
            combo >= 5  ? '¡IMPARABLE!' :
            combo >= 3  ? '¡Excelente!' :
            '¡Bien!',
      showNumber: true,
      comboNumber: combo,
      animation: combo >= 10 ? Animation.explosion :
                 combo >= 7  ? Animation.flames :
                 combo >= 5  ? Animation.shake :
                 combo >= 3  ? Animation.sparkles :
                 Animation.none,
      sound: combo >= 10 ? Sound.combo_legendary :
             combo >= 7  ? Sound.combo_fire :
             combo >= 5  ? Sound.combo_5 :
             combo >= 3  ? Sound.combo_3 :
             Sound.combo_2,
    );
  }
}
```

---

## 11. BOSS RAID SEMANAL

### 11.1 Concepto

```
┌─────────────────────────────────────────────────────────────────────┐
│                       BOSS RAID SEMANAL                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ¿QUÉ ES?                                                           │
│  Mini-simulacro temático que otorga XP multiplicado.                │
│  Es el "evento especial" que define posiciones finales de liga.     │
│                                                                     │
│  DISPONIBILIDAD:                                                    │
│  • Cada domingo de 10:00 AM a 10:00 PM (hora Colombia)              │
│  • 12 horas de ventana                                              │
│  • 1 intento por semana                                             │
│                                                                     │
│  FORMATO:                                                           │
│  • 20 preguntas                                                     │
│  • ~25 minutos                                                      │
│  • Tema rotativo por semana                                         │
│                                                                     │
│  COSTO DE ENTRADA:                                                  │
│  • 100 Oro                                                          │
│  • O GRATIS si racha >= 5 días                                      │
│                                                                     │
│  MULTIPLICADOR XP:                                                  │
│  • Todo el XP ganado en Boss Raid es ×3                             │
│                                                                     │
│  ROTACIÓN DE TEMAS:                                                 │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ Semana │ Tema            │ Boss                            │   │
│  ├────────┼─────────────────┼─────────────────────────────────│   │
│  │ 1      │ Matemáticas     │ 🐉 Dragón del Cálculo           │   │
│  │ 2      │ Lectura Crítica │ 🦁 Esfinge de las Letras        │   │
│  │ 3      │ Ciencias        │ 🐙 Hidra del Laboratorio        │   │
│  │ 4      │ Sociales        │ 🗿 Titán de la Historia         │   │
│  │ 5      │ Inglés          │ 🦅 Fénix Políglota              │   │
│  │ 6      │ Mixto           │ 👑 Rey Sombra (todas las áreas) │   │
│  └────────┴─────────────────┴─────────────────────────────────┘   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 11.2 Mecánica de HP del Boss

```
┌─────────────────────────────────────────────────────────────────────┐
│                    DURANTE EL BOSS RAID                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                                                             │   │
│  │   ⚔️ BOSS RAID: DRAGÓN DEL CÁLCULO ⚔️                       │   │
│  │                                                             │   │
│  │   [═══════════════════════════════════════════════════════] │   │
│  │   HP: ████████████████████████░░░░░░ 75/100                │   │
│  │                                                             │   │
│  │   ┌───────────────────────────────────────────────────┐    │   │
│  │   │                                                   │    │   │
│  │   │              [Imagen del Boss]                    │    │   │
│  │   │                  🐉                               │    │   │
│  │   │                                                   │    │   │
│  │   └───────────────────────────────────────────────────┘    │   │
│  │                                                             │   │
│  │   Pregunta 5 de 20                                         │   │
│  │                                                             │   │
│  │   Si log₂(x) = 5, ¿cuál es el valor de x?                  │   │
│  │                                                             │   │
│  │   ○ A) 10                                                  │   │
│  │   ○ B) 25                                                  │   │
│  │   ● C) 32   ← SELECCIONADO                                 │   │
│  │   ○ D) 64                                                  │   │
│  │                                                             │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  MECÁNICA DE DAÑO:                                                  │
│  • Respuesta correcta → Boss pierde 5 HP                           │
│  • Respuesta incorrecta → Boss contraataca (efecto visual)         │
│  • Boss "derrotado" si HP llega a 0 (máximo 20 correctas)          │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 11.3 Recompensas de Boss Raid

| Correctas | Rango | Oro | XP (×3) | Badge |
|-----------|-------|-----|---------|-------|
| 18-20 | S-Rank Hunter | 200 | 600 | ⚔️ S-Rank Hunter |
| 15-17 | A-Rank Hunter | 100 | 450 | ⚔️ A-Rank Hunter |
| 12-14 | B-Rank | 75 | 360 | — |
| 8-11 | C-Rank | 50 | 270 | — |
| <8 | Participación | 25 | 150 | — |

---

## 12. ECONOMÍA DEL ORO

### 12.1 Fuentes de Oro (Ingresos)

| Fuente | Oro | Frecuencia |
|--------|-----|------------|
| Lección 3⭐ | +15 | Por lección |
| Lección 2⭐ | +10 | Por lección |
| Lección 1⭐ | +5 | Por lección |
| Racha 7 días | +50 | Semanal |
| Racha 14 días | +100 | Quincenal |
| Racha 30 días | +200 | Mensual |
| Ascenso de Liga | +100 | Por ascenso |
| Top 1 Liga | +150 | Semanal |
| Top 2-3 Liga | +75-100 | Semanal |
| Boss Raid S-Rank | +200 | Semanal |
| Logro desbloqueado | +25-100 | Variable |

### 12.2 Usos del Oro (Gastos)

| Item | Costo | Efecto |
|------|-------|--------|
| Streak Freeze | 200 | Protege racha 1 día |
| Streak Repair | 300 | Recupera racha perdida |
| Hint (Pista) | 50 | Pista antes de responder |
| Poción de Energía | 150 | Mana infinito por 1h |
| Entrada Boss Raid | 100 | Acceso al evento |
| Avatar Común | 250 | Cosmético |
| Avatar Raro | 500 | Cosmético |
| Avatar Épico | 1000 | Cosmético |
| Marco de perfil | 300 | Cosmético |

### 12.3 Balance Económico Target

```
USUARIO ACTIVO PROMEDIO (por día):

INGRESOS:
├── 2-3 lecciones completas    = 25-45 Oro
├── Bonus de racha (si aplica) = 0-50 Oro (promedio ~7)
└── Liga semanal (prorrateado) = ~10 Oro/día
TOTAL INGRESO: ~50-100 Oro/día

GASTOS:
├── Hints ocasionales          = 0-50 Oro
├── Streak Freeze (1/semana)   = ~29 Oro/día prorrateado
└── Cosméticos (ocasional)     = ~10 Oro/día
TOTAL GASTO: ~40-90 Oro/día

BALANCE: Usuario acumula lentamente (+10-20/día)
         → Puede comprar Avatar Épico cada ~2 meses de juego activo
```

---

## 13. MOTOR DE APRENDIZAJE ADAPTATIVO

### 13.1 Algoritmo SM-2 Simplificado

```dart
class AdaptiveLearningEngine {
  /// Prioridad de una pregunta/tema para el usuario
  /// Valor más alto = más urgente de practicar
  static double calculatePriority({
    required double topicMastery,
    required int daysSinceLastPractice,
  }) {
    // Curva de olvido de Ebbinghaus simplificada
    // e^(-t/7) donde t = días desde última práctica
    final forgettingFactor = exp(-daysSinceLastPractice / 7.0);
    
    // Retención estimada
    final estimatedRetention = topicMastery * forgettingFactor;
    
    // Prioridad = qué tan probable es que necesite refuerzo
    // 1.0 = máxima prioridad, 0.0 = no necesita práctica
    return 1.0 - estimatedRetention;
  }
  
  /// Selecciona la siguiente pregunta óptima
  Future<Question> getNextQuestion(String userId, String area) async {
    // 1. Obtener mastery map del usuario para el área
    final masteryMap = await getUserMasteryMap(userId, area);
    final lastPracticed = await getLastPracticedDates(userId, area);
    
    // 2. Calcular prioridades
    final priorities = <String, double>{};
    for (final topic in masteryMap.keys) {
      final days = lastPracticed[topic]?.inDays ?? 30;
      priorities[topic] = calculatePriority(
        topicMastery: masteryMap[topic]!,
        daysSinceLastPractice: days,
      );
    }
    
    // 3. Seleccionar tema con mayor prioridad
    final sortedTopics = priorities.entries.toList()
      ..sort((a, b) => b.value.compareTo(a.value));
    
    final targetTopic = sortedTopics.first.key;
    final topicMastery = masteryMap[targetTopic]!;
    
    // 4. Seleccionar dificultad basada en mastery
    final difficulty = selectDifficulty(topicMastery);
    
    // 5. Obtener pregunta no respondida de ese tema/dificultad
    return await getUnseenQuestion(
      userId: userId,
      topic: targetTopic,
      difficulty: difficulty,
    );
  }
  
  /// Selecciona dificultad basada en mastery actual
  static Difficulty selectDifficulty(double mastery) {
    if (mastery < 0.4) return Difficulty.easy;
    if (mastery < 0.7) return Difficulty.medium;
    return Difficulty.hard;
  }
}
```

### 13.2 Actualización de Mastery

```dart
class MasteryUpdater {
  /// Actualiza el mastery después de responder
  static double updateMastery({
    required double currentMastery,
    required bool correct,
    required int timeSpentSeconds,
    required int expectedTimeSeconds,
  }) {
    double delta;
    
    if (correct) {
      final timeRatio = timeSpentSeconds / expectedTimeSeconds;
      
      if (timeRatio < 0.5) {
        delta = 0.15;  // Muy rápido = alta confianza
      } else if (timeRatio < 1.0) {
        delta = 0.10;  // Tiempo normal
      } else if (timeRatio < 2.0) {
        delta = 0.05;  // Un poco lento
      } else {
        delta = 0.02;  // Muy lento (quizás adivinó)
      }
    } else {
      delta = -0.15;  // Penalización por error
    }
    
    return (currentMastery + delta).clamp(0.0, 1.0);
  }
}
```

---

## 14. SISTEMA DE EXPLICACIONES

### 14.1 Tiers de Explicación

```
┌─────────────────────────────────────────────────────────────────────┐
│                  SISTEMA DE EXPLICACIONES (TIERED)                  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  TIER 1: EXPLICACIÓN BASE (Siempre disponible, gratis)              │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                                                             │   │
│  │  La respuesta correcta es B) 13                             │   │
│  │                                                             │   │
│  │  Explicación:                                               │   │
│  │  Para encontrar f(5), sustituimos x = 5 en la función:      │   │
│  │  f(5) = 2(5) + 3 = 10 + 3 = 13                             │   │
│  │                                                             │   │
│  │  Recuerda: Para evaluar una función, reemplaza la           │   │
│  │  variable por el valor dado y realiza las operaciones.      │   │
│  │                                                             │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  TIER 2: HINT (50 Oro, antes de responder)                          │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                                                             │   │
│  │  💡 Pista (50 🪙):                                          │   │
│  │                                                             │   │
│  │  "Recuerda que f(x) significa sustituir x por el valor      │   │
│  │   que te dan. En este caso, x = 5."                         │   │
│  │                                                             │   │
│  │  ┌─────────────────┐                                       │   │
│  │  │  DESBLOQUEAR    │                                       │   │
│  │  └─────────────────┘                                       │   │
│  │                                                             │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  TIER 3: VIDEO EXTERNO (Gratis, post-respuesta)                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                                                             │   │
│  │  📺 Ver video explicativo                                   │   │
│  │                                                             │   │
│  │  "Evaluación de funciones - Julio Profe"                    │   │
│  │  Duración: 8:32                                             │   │
│  │                                                             │   │
│  │  ┌─────────────────┐                                       │   │
│  │  │  ABRIR VIDEO    │ → Abre YouTube                        │   │
│  │  └─────────────────┘                                       │   │
│  │                                                             │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  TIER 4: MINI-LECCIÓN INTERACTIVA (v2.0+, Premium)                  │
│  └── Contenido interactivo paso a paso                              │
│  └── Solo después de validar Product-Market Fit                     │
│                                                                     │
│  FALLBACK SI VIDEO NO DISPONIBLE:                                   │
│  "📜 Registro en mantenimiento. Consulta la explicación base."      │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 15. NOTIFICACIONES PUSH

### 15.1 Notificaciones de Racha

| Hora | Trigger | Copy |
|------|---------|------|
| 6:00 PM | No ha estudiado hoy | "⚡ [SISTEMA] Tu racha de {streak} días está en peligro. Misión disponible: 5 minutos." |
| 9:00 PM | Sigue sin estudiar | "🔥 [ALERTA] Quedan 7 horas. Los Cazadores débiles pierden su racha esta noche." |
| 3:30 AM | Última oportunidad | "💀 [URGENTE] 30 minutos para el reinicio. Tu racha de {streak} días desaparecerá." |

### 15.2 Notificaciones de Liga

| Trigger | Copy |
|---------|------|
| Domingo 10:00 AM | "⚔️ [SISTEMA] El Boss Raid ha comenzado. Tienes 12 horas para demostrar tu rango, Cazador." |
| Domingo 6:00 PM | "🏆 [SISTEMA] La Liga cierra en 6 horas. Posición actual: #{rank}. Top 10 ascienden." |
| Ascenso | "⬆️ [SISTEMA] Has ascendido a Liga {nueva}. Tu poder crece, Cazador." |
| Descenso | "⬇️ [SISTEMA] Has descendido a Liga {nueva}. Entrena más duro." |
| Safe | "🛡️ [SISTEMA] Te mantuviste en Liga {liga}. Posición final: #{rank}." |

### 15.3 Notificaciones de Re-engagement

| Días Inactivo | Copy |
|---------------|------|
| 3 días | "💀 [SISTEMA] Tu racha fue destruida. Pero tu Mastery permanece. ¿Vuelves al Dungeon?" |
| 7 días | "🌑 [SISTEMA] Un Cazador olvidado es un Cazador muerto. El Sistema te espera." |
| 14 días | "⚰️ [SISTEMA] Tus habilidades se desvanecen en la oscuridad. Vuelve antes de que sea tarde." |

### 15.4 Configuración de Notificaciones

```dart
class NotificationConfig {
  static const int maxPerDay = 3;
  static const int quietHoursStart = 23; // 11 PM
  static const int quietHoursEnd = 7;     // 7 AM
  static const Duration minBetween = Duration(hours: 2);
  
  // Excepción: última oportunidad de racha a las 3:30 AM
  static const bool allowUrgentStreak = true;
}
```

---

## 16. DOPAMINE ENGINE (ANIMACIONES)

### 16.1 Feedback de Respuesta Correcta

```
TIMELINE (600ms total):

T+0ms:    Opción seleccionada cambia a VERDE
          Border glow verde se expande
          
T+50ms:   Haptic feedback: DOBLE PULSO (success pattern)
          Sound: "ding.mp3" (tono ascendente)
          
T+100ms:  Checkmark (✓) aparece con bounce animation
          "+10 XP" text floats up con fade
          
T+300ms:  Progress bar avanza con ease-out
          Si combo >= 3: partículas de sparkle
          
T+400ms:  Combo counter incrementa con scale animation
          Si combo >= 5: screen shake sutil
          Si combo >= 7: flame particles
          
T+600ms:  Slide transition a siguiente pregunta
```

### 16.2 Feedback de Respuesta Incorrecta

```
TIMELINE (800ms total):

T+0ms:    Opción seleccionada cambia a ROJO
          Horizontal shake (3 ciclos, 5px)
          
T+50ms:   Haptic feedback: HEAVY IMPACT
          Sound: "wrong.mp3" (tono descendente)
          
T+100ms:  X mark aparece
          Corazón en header hace "crack" animation
          
T+150ms:  Respuesta correcta se ilumina en VERDE
          
T+200ms:  Heart counter: -1 con scale down/up
          
T+400ms:  Explanation card slides up desde bottom
          
T+800ms:  Esperando input de usuario para continuar
```

### 16.3 Celebración de Lección Completa

```
TIMELINE (3000ms total):

T+0ms:    Screen fade a dark overlay (50% opacity)

T+200ms:  Mascota/Boss entra desde bottom (Rive animation)

T+400ms:  Mascota hace celebration dance

T+500ms:  Haptic: TRIPLE PULSE (celebration pattern)
          Sound: "fanfare.mp3"

T+600ms:  Confetti explosion desde top (Lottie)

T+800ms:  "¡LECCIÓN COMPLETADA!" text bounce-in

T+1000ms: XP counter hace count-up animation (0 → final)
          Sound: "tick tick tick" durante count-up

T+1200ms: Stars aparecen one-by-one con pop animation
          ⭐ ... ⭐⭐ ... ⭐⭐⭐

T+1500ms: Gold counter count-up

T+2000ms: Stats adicionales fade-in

T+2500ms: Botón "CONTINUAR" fade-in

T+3000ms: Idle state, esperando input
```

---

## 17. SINCRONIZACIÓN OFFLINE

### 17.1 Arquitectura Offline-First

```
┌─────────────────────────────────────────────────────────────────────┐
│                   SINCRONIZACIÓN OFFLINE-FIRST                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  PRINCIPIO: El dispositivo es la fuente de verdad temporal         │
│             El servidor es la fuente de verdad final               │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                      DISPOSITIVO                            │   │
│  │                                                             │   │
│  │  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    │   │
│  │  │   HIVE      │    │   ACTION    │    │   SYNC      │    │   │
│  │  │   (Cache)   │◀──▶│   QUEUE     │◀──▶│   MANAGER   │    │   │
│  │  └─────────────┘    └─────────────┘    └──────┬──────┘    │   │
│  │                                               │            │   │
│  └───────────────────────────────────────────────┼────────────┘   │
│                                                  │                 │
│                                                  ▼                 │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                      SERVIDOR                               │   │
│  │                                                             │   │
│  │  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    │   │
│  │  │  FASTAPI    │◀──▶│  POSTGRES   │◀──▶│   REDIS     │    │   │
│  │  └─────────────┘    └─────────────┘    └─────────────┘    │   │
│  │                                                             │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  DATOS CACHEADOS OFFLINE:                                           │
│  • 50 preguntas por área (250 total)                               │
│  • Historial de respuestas pendientes                               │
│  • Estado de corazones, racha, XP                                   │
│  • Mastery map del usuario                                          │
│  • Explicaciones Tier 1                                             │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 17.2 Action Queue (Cola de Acciones)

```dart
class ActionQueue {
  /// Guarda acción para sincronizar después
  Future<void> enqueue(SyncAction action) async {
    final queuedAction = QueuedAction(
      id: uuid(),
      action: action,
      timestamp: DateTime.now(),  // Timestamp original
      attempts: 0,
    );
    
    await _hive.put(queuedAction.id, queuedAction);
  }
  
  /// Procesa cola cuando hay conexión
  Future<void> processQueue() async {
    final actions = await _hive.values.toList()
      ..sort((a, b) => a.timestamp.compareTo(b.timestamp));
    
    for (final queued in actions) {
      try {
        await _api.sync(queued.action);
        await _hive.delete(queued.id);
      } catch (e) {
        queued.attempts++;
        if (queued.attempts >= 3) {
          // Log error, no eliminar (para retry manual)
          await logSyncError(queued);
        }
      }
    }
  }
}
```

### 17.3 Resolución de Conflictos

```dart
class ConflictResolver {
  /// El servidor siempre gana para datos críticos
  static final serverWins = ['hearts', 'gold', 'streak', 'league_xp'];
  
  /// El cliente gana para datos de progreso de aprendizaje
  static final clientWins = ['mastery_updates', 'answer_history'];
  
  Future<void> resolve(String field, dynamic serverValue, dynamic clientValue) async {
    if (serverWins.contains(field)) {
      await updateLocal(field, serverValue);
    } else if (clientWins.contains(field)) {
      await updateServer(field, clientValue);
    } else {
      // Default: último timestamp gana
      await resolveByTimestamp(field, serverValue, clientValue);
    }
  }
}
```

---

## 18. FALLBACK MATRIX

### 18.1 Errores de Red

| Escenario | Comportamiento | UI Message |
|-----------|----------------|------------|
| Sin conexión al iniciar | Modo offline con cache | "🌑 Sin conexión. Modo Entrenamiento Activo." |
| Pierde conexión mid-session | Guarda en queue, continúa | (Sin mensaje - transparente) |
| Ad falla mid-watch | Server retiene reward | "⚡ Transmisión interrumpida. Tu Mana llegará pronto." |
| Sync conflict en Mana | Server wins | "🔄 Sincronizando con el Sistema..." |
| API timeout | Retry con backoff | "⏳ Conectando con el Sistema..." |

### 18.2 Errores de Contenido

| Escenario | Comportamiento | UI Message |
|-----------|----------------|------------|
| YouTube link roto | Mostrar Tier 1 | "📜 Registro en mantenimiento." |
| Imagen no carga | Placeholder | (Icono de imagen rota) |
| Pregunta sin explicación | Solo mostrar respuesta | "La respuesta correcta es: [X]" |
| Área sin preguntas cached | Bloquear área offline | "⚠️ Necesitas conexión para esta área." |

### 18.3 Errores de Estado

| Escenario | Comportamiento | UI Message |
|-----------|----------------|------------|
| 0 Mana + 0 Gold + 0 Ads | Solo Grace Practice | "⏳ Mana agotado. Entrena sin rango." |
| JWT expirado | Refresh silencioso | "🔐 Reconectando..." |
| Diagnostic timeout | Guardar progreso parcial | "💾 Progreso guardado." |
| Liga no procesada | Mantener posición anterior | "🛡️ Resultados en proceso." |

---

## 19. MODELO DE MONETIZACIÓN

### 19.1 Planes de Suscripción

| Plan | Precio (COP) | Características |
|------|--------------|-----------------|
| **Gratis** | $0 | 5 corazones (4h regen), Grace Mode, Ads para recover, Ligas básicas |
| **Premium** | $29,900/mes | Corazones ilimitados, Sin ads, XP ×1.5, Hints gratis, Boss Raid gratis |
| **Elite** | $49,900/mes | Todo Premium + XP ×2.0, Análisis detallado, Tutorías IA, Avatares exclusivos |

### 19.2 Compras In-App

| Item | Precio |
|------|--------|
| 500 Oro | $9,900 |
| 1,200 Oro | $19,900 |
| 3,000 Oro | $39,900 |
| 5 Streak Freeze | $14,900 |

### 19.3 B2B (Colegios)

```
PLAN INSTITUCIONAL:
• $15,000 COP/estudiante/año
• Dashboard de profesor
• Reportes mensuales por curso
• Soporte prioritario
• Descuentos:
  - 50-100 estudiantes: 10%
  - 100-500 estudiantes: 20%
  - 500+ estudiantes: 30%
```

---

## 20. KPIs Y MÉTRICAS DE ÉXITO

### 20.1 Métricas de Retención

| Métrica | Target | Alerta |
|---------|--------|--------|
| D1 Retention | >60% | <50% |
| D7 Retention | >40% | <30% |
| D30 Retention | >20% | <15% |
| Onboarding Completion | >70% | <60% |

### 20.2 Métricas de Engagement

| Métrica | Target | Alerta |
|---------|--------|--------|
| Session Length | >8 min | <5 min |
| Sessions/Day | >1.5 | <1.0 |
| Questions/Session | >15 | <10 |
| Streak >7 days | >25% users | <15% |

### 20.3 Métricas de Aprendizaje

| Métrica | Target | Alerta |
|---------|--------|--------|
| Mastery Improvement | +15% en 2 semanas | <10% |
| Area Completion | >20% completan 1 área | <10% |
| Diagnostic Score Improvement | +10% en 1 mes | <5% |

### 20.4 Métricas de Negocio

| Métrica | Target |
|---------|--------|
| Premium Conversion | 5-8% |
| Monthly Churn | <5% |
| CAC | <$10 USD |
| LTV | >$50 USD |

---

## 21. ROADMAP DE DESARROLLO

### Semana 1-2: Foundation
- [ ] HeartSystem con 4h regeneration + Grace Mode
- [ ] StreakSystem con 4AM logic + Freeze/Repair
- [ ] Hive persistence
- [ ] SyncManager base
- [ ] Unit tests

### Semana 3-4: Adaptive Core
- [ ] Quick Diagnostic (15 preguntas)
- [ ] Deep Diagnostic por área
- [ ] TopicMasteryMap
- [ ] Algoritmo SM-2
- [ ] Anti-gaming validation

### Semana 5-6: Social Layer
- [ ] League system (grupos de 30)
- [ ] Weekly reset jobs
- [ ] Leaderboard UI
- [ ] Push notifications
- [ ] Boss Raid básico

### Semana 7-8: Polish
- [ ] Onboarding 6 pasos completo
- [ ] Animaciones Rive/Lottie
- [ ] Fallback handling
- [ ] Beta test 50 usuarios
- [ ] Store submission

---

## CHECKLIST PRE-DESARROLLO

### Blockers Críticos
- [ ] BD de preguntas estructurada (área + subtema + dificultad)
- [ ] 15 preguntas Quick Diagnostic
- [ ] 81 preguntas Deep Diagnostic (15-18 × 5 áreas)
- [ ] Explicaciones Tier 1 para todas las preguntas
- [ ] FastAPI backend operativo
- [ ] PostgreSQL schema listo

### Puede Esperar
- [ ] Assets Rive/Lottie (Semana 7)
- [ ] Copy de notificaciones (Semana 5)
- [ ] Links de YouTube (v1.2)

---

*"El Sistema te observa, Cazador. Tu entrenamiento comienza ahora."*

# 🎮 ICFES LEVELING - SUPLEMENTO DE LÓGICA DE NEGOCIO

> **Complemento de:** ICFES_LEVELING_LOGICA_NEGOCIO_v2.md  
> **Versión:** 3.0 FINAL  
> **Contiene:** Secciones adicionales no incluidas en v2

---

## TABLA DE CONTENIDOS SUPLEMENTO

1. [Modo Millonario y Comodines](#1-modo-millonario-y-comodines)
2. [Sistema de Videos y Contenido](#2-sistema-de-videos-y-contenido)
3. [Plan de Estudio con IA (Claude)](#3-plan-de-estudio-con-ia-claude)
4. [Árbol de Maestría (Mastery Tree)](#4-árbol-de-maestría-mastery-tree)
5. [Sistema Anti-Gaming Detallado](#5-sistema-anti-gaming-detallado)
6. [Triggers Psicológicos](#6-triggers-psicológicos)
7. [Dopamine Engine (Timelines de Animación)](#7-dopamine-engine-timelines-de-animación)
8. [Arquitectura Técnica Completa](#8-arquitectura-técnica-completa)
9. [Apéndices Técnicos](#9-apéndices-técnicos)

---

## 1. MODO MILLONARIO Y COMODINES

### 1.1 Concepto

El Modo Millonario es una variante de práctica inspirada en "¿Quién quiere ser millonario?" con dificultad progresiva y comodines estratégicos.

```
╔═══════════════════════════════════════════════════════════════════════╗
║                                                                       ║
║                    🎯 MODO MILLONARIO 🎯                              ║
║                                                                       ║
║  15 preguntas con dificultad creciente                                ║
║  ¡Llega a la cima para ganar el premio máximo!                        ║
║                                                                       ║
║  ┌───────────────────────────────────────────────────────────────┐    ║
║  │   15. ████████████████████████████████  🏆 500 XP + 100 Oro   │    ║
║  │   14. ███████████████████████████████░                        │    ║
║  │   13. ██████████████████████████████░░                        │    ║
║  │   12. █████████████████████████████░░░                        │    ║
║  │   11. ████████████████████████████░░░░                        │    ║
║  │   10. ███████████████████████████░░░░░  🔒 Checkpoint         │    ║
║  │    9. ██████████████████████████░░░░░░                        │    ║
║  │    8. █████████████████████████░░░░░░░                        │    ║
║  │    7. ████████████████████████░░░░░░░░                        │    ║
║  │    6. ███████████████████████░░░░░░░░░                        │    ║
║  │    5. ██████████████████████░░░░░░░░░░  🔒 Checkpoint         │    ║
║  │    4. █████████████████████░░░░░░░░░░░                        │    ║
║  │    3. ████████████████████░░░░░░░░░░░░                        │    ║
║  │    2. ███████████████████░░░░░░░░░░░░░                        │    ║
║  │    1. ██████████████████░░░░░░░░░░░░░░  ← AQUÍ ESTÁS          │    ║
║  └───────────────────────────────────────────────────────────────┘    ║
║                                                                       ║
║  COMODINES DISPONIBLES:                                               ║
║   [50:50]    [🤖 IA]    [⏭️ Skip]                                     ║
║    Gratis    50 Oro      Gratis                                       ║
║                                                                       ║
╚═══════════════════════════════════════════════════════════════════════╝
```

### 1.2 Dificultad Progresiva

| Pregunta | Dificultad | XP Base |
|----------|------------|---------|
| 1-3 | Fácil | 5 XP |
| 4-6 | Fácil-Media | 8 XP |
| 7-9 | Media | 12 XP |
| 10-12 | Media-Difícil | 18 XP |
| 13-15 | Difícil | 25 XP |

**Checkpoints (Seguros):**
- Pregunta 5: Garantiza 50 XP + 10 Oro
- Pregunta 10: Garantiza 150 XP + 30 Oro
- Pregunta 15: Premio máximo 500 XP + 100 Oro

### 1.3 Sistema de Comodines

#### 50:50 (Gratis, 1 por partida)
```
FUNCIONAMIENTO:
- Elimina 2 opciones incorrectas
- Deja la correcta + 1 incorrecta aleatoria
- Disponible OFFLINE ✅
- Algoritmo local (no requiere API)
```

#### 🤖 Preguntar a la IA (50 Oro, 1 por partida)
```
FUNCIONAMIENTO:
- Claude analiza la pregunta
- Da una PISTA (no la respuesta directa)
- Máximo 2 oraciones
- Disponible SOLO ONLINE ❌

PROMPT:
"Eres un tutor ICFES. Da una pista para esta pregunta 
sin revelar la respuesta. Máximo 2 oraciones."

EJEMPLO DE PISTA:
"Recuerda que f(x) significa sustituir x por el valor 
dado. Calcula 2 × 5 primero y luego suma 3."
```

#### ⏭️ Saltar Pregunta (Gratis, 1 por partida)
```
FUNCIONAMIENTO:
- Pasa a la siguiente pregunta sin responder
- NO cuenta como incorrecta
- NO pierdes corazón
- NO ganas XP por esa pregunta
- Para ganar premio máximo necesitas 15 CORRECTAS
- Disponible OFFLINE ✅
```

### 1.4 Diferencia: Modo Normal vs Millonario

| Aspecto | Modo Normal | Modo Millonario |
|---------|-------------|-----------------|
| Dificultad | Adaptativa al mastery | Progresiva fija (1→15) |
| Comodines | No disponibles | 3 comodines |
| Pérdida corazones | Sí (-1 por error) | Sí (-1 por error) |
| Checkpoints | No | Sí (5 y 10) |
| Premio máximo | ~150 XP | 500 XP + 100 Oro |
| Frecuencia | Ilimitado | 3 veces/día |
| Anti-gaming | Activo | No (preguntas fijas) |

---

## 2. SISTEMA DE VIDEOS Y CONTENIDO

### 2.1 Arquitectura de Contenido (Tiers)

```
TIER 1: EXPLICACIÓN TEXTUAL (Siempre disponible, gratis)
├── Texto de 2-3 párrafos
├── Puede incluir imagen/diagrama
├── Disponible OFFLINE ✅
└── Almacenada en BD con cada pregunta

TIER 2: HINT PRE-RESPUESTA (50 Oro)
├── Pista antes de responder (en Modo Normal)
├── No revela respuesta, guía razonamiento
├── Disponible OFFLINE ✅ (hints pre-cargados)
└── En Millonario es el comodín IA

TIER 3: VIDEO EXTERNO (Gratis, post-respuesta)
├── Link a YouTube curado
├── Dos modos de reproducción:
│   ├── "Ver en YouTube" → Abre app de YouTube
│   └── "Ver aquí" → Reproductor embebido
├── Disponible ONLINE ONLY ❌
└── Validación semanal de links funcionales

TIER 4: MINI-LECCIÓN INTERACTIVA (v2.0+, Premium)
├── Contenido interactivo paso a paso
└── Solo después de validar PMF
```

### 2.2 Catálogo de Fuentes de Video

| Fuente | Áreas | Idioma | Calidad |
|--------|-------|--------|---------|
| Julio Profe | Matemáticas, Física | Español | ⭐⭐⭐⭐⭐ |
| Khan Academy | Todas | Español | ⭐⭐⭐⭐⭐ |
| Unicoos | Matemáticas, Física, Química | Español | ⭐⭐⭐⭐ |
| Profe en c@sa | Ciencias | Español | ⭐⭐⭐⭐ |
| Academia Play | Historia, Sociales | Español | ⭐⭐⭐⭐ |

### 2.3 Integración de Videos en Plan de Estudio

```
FLUJO DE LECCIÓN CON VIDEO:

1. Usuario entra a lección del día
          │
          ▼
2. Muestra video recomendado
   ┌─────────────────────────────────┐
   │ 📺 "Ecuaciones de primer grado" │
   │     Julio Profe · 15:32         │
   │                                 │
   │  [Ver en YouTube] [Ver aquí]   │
   └─────────────────────────────────┘
          │
          ▼
3. Tracking de progreso (si ve embebido)
   ├── 0-79%: No desbloquea quiz
   └── 80%+: Desbloquea quiz (+10 XP por ver)
          │
          ▼
4. Quiz de verificación
   ├── 10 preguntas del tema del video
   └── 70%+ correctas = +15 XP
```

### 2.4 Fallback si Video No Disponible

```dart
class VideoFallbackService {
  Future<Widget> getVideoContent(String videoUrl) async {
    try {
      final isAvailable = await checkVideoAvailability(videoUrl);
      
      if (isAvailable) {
        return VideoPlayer(url: videoUrl);
      } else {
        return FallbackExplanation(
          message: "📜 Registro en mantenimiento.",
          showTextExplanation: true,
        );
      }
    } catch (e) {
      return OfflineMessage(
        message: "📶 Video disponible solo online.",
      );
    }
  }
}
```

---

## 3. PLAN DE ESTUDIO CON IA (CLAUDE)

### 3.1 Concepto

Una vez completado el Deep Diagnostic, **Claude 3.5 Sonnet** genera un Plan de Estudio Personalizado.

### 3.2 Características del Plan

- **Generación:** Automática por IA basada en diagnóstico
- **Frecuencia:** Plan semanal con actividades diarias
- **Regeneración:** Cada 30 días o con cambios significativos
- **Personalización:** Usuario puede ajustar intensidad

### 3.3 Estructura del Plan

```
╔═══════════════════════════════════════════════════════════════════════╗
║              📋 TU PLAN DE ATAQUE - SEMANA 1                          ║
╠═══════════════════════════════════════════════════════════════════════╣
║                                                                       ║
║  Meta: Subir 50 puntos en Matemáticas                                 ║
║  Tiempo sugerido: 30 min/día                                          ║
║                                                                       ║
║  ─────────────────────────────────────────────────────────────────    ║
║                                                                       ║
║  LUNES - Álgebra Básica                                               ║
║  ┌─────────────────────────────────────────────────────────────────┐  ║
║  │  📺 Video: "Ecuaciones de primer grado" (15 min)                │  ║
║  │     → Julio Profe                                               │  ║
║  │  📝 Quiz: 10 preguntas de práctica                              │  ║
║  │     → Desbloquea al ver 80% del video                           │  ║
║  │  🎯 Meta: 70% de precisión                                      │  ║
║  └─────────────────────────────────────────────────────────────────┘  ║
║                                                                       ║
║  MARTES - Álgebra Intermedia                                          ║
║  ┌─────────────────────────────────────────────────────────────────┐  ║
║  │  📺 Video: "Sistemas de ecuaciones" (20 min)                    │  ║
║  │  📝 Quiz: 10 preguntas + 5 repaso de ayer                       │  ║
║  │  🎯 Meta: 75% de precisión                                      │  ║
║  └─────────────────────────────────────────────────────────────────┘  ║
║                                                                       ║
╚═══════════════════════════════════════════════════════════════════════╝
```

### 3.4 Prompt para Generación (Claude API)

```
Eres un tutor experto en preparación ICFES para estudiantes colombianos.

CONTEXTO DEL ESTUDIANTE:
- Rango actual: {hunter_rank}
- Puntaje proyectado: {projected_score}
- Meta del usuario: {user_goal}
- Tiempo disponible: {minutes_per_day} minutos/día
- Área más débil: {weakest_area}
- Subtemas débiles: {weak_subtopics}
- Días hasta ICFES: {days_until_exam}

CATÁLOGO DE VIDEOS DISPONIBLES:
{video_catalog_json}

GENERA un plan de estudio para las próximas 4 semanas que incluya:
1. Actividades diarias (video + quiz)
2. Priorización de debilidades detectadas
3. Repaso espaciado de temas ya dominados (cada 5-7 días)
4. Metas de precisión progresivas (60% → 80%)
5. Tiempo realista por actividad

Responde SOLO en JSON con este formato:
{
  "weeks": [
    {
      "week_number": 1,
      "focus_area": "Álgebra",
      "days": [
        {
          "day": "Lunes",
          "activities": [
            {
              "type": "video",
              "title": "...",
              "source": "Julio Profe",
              "url": "...",
              "duration_minutes": 15
            },
            {
              "type": "quiz",
              "topic_id": "algebra_ecuaciones",
              "question_count": 10,
              "target_accuracy": 0.70
            }
          ]
        }
      ]
    }
  ]
}
```

### 3.5 Triggers de Regeneración

| Evento | Acción |
|--------|--------|
| Pasaron 30 días | Regenerar plan completo |
| Mastery subió >15% en un área | Regenerar esa semana |
| Mastery bajó >10% en un área | Agregar refuerzo urgente |
| Usuario solicita manualmente | Regenerar plan |
| Días hasta ICFES < 30 | Cambiar a modo intensivo |

---

## 4. ÁRBOL DE MAESTRÍA (MASTERY TREE)

### 4.1 Visualización

El Árbol de Maestría es un mapa estelar donde cada nodo es un tema.

```
                     CÁLCULO (🔒)
                         │
              ┌──────────┴──────────┐
              │                     │
         ÁLGEBRA II (⭐)      GEOMETRÍA II (🔒)
              │                     │
      ┌───────┴───────┐            │
      │               │            │
 ÁLGEBRA I (🌟)  FUNCIONES (⭐)  GEOMETRÍA I (🌟)
      │               │            │
      └───────┬───────┴────────────┘
              │
         ARITMÉTICA (🌟)
              │
      ┌───────┴───────┐
      │               │
 ESTADÍSTICA (⭐)  PROBABILIDAD (🔒)
```

### 4.2 Estados de los Nodos

| Estado | Icono | Mastery | Color | Acción |
|--------|-------|---------|-------|--------|
| Bloqueado | 🔒 | N/A | Gris | Completar prerequisitos |
| Nuevo | ⚪ | 0% | Blanco | Hacer diagnóstico |
| En progreso | ⭐ | 1-79% | Azul | Seguir practicando |
| Dominado | 🌟 | 80-100% | Dorado | Mantenimiento |
| Decayendo | 💀 | Bajando | Rojo | Repaso urgente |

### 4.3 Mecánica de Decay (Olvido)

```dart
double calculateDecay(double currentMastery, int daysSinceLastPractice) {
  if (daysSinceLastPractice <= 3) {
    return 0;  // Grace period
  }
  
  // Decay: pierde ~20% en 14 días sin practicar
  final decayFactor = 0.02 * (daysSinceLastPractice - 3);
  final decayedMastery = currentMastery * (1 - decayFactor);
  
  return max(0.3, decayedMastery);  // Nunca baja de 0.3
}
```

### 4.4 Desbloqueo de Nodos

```dart
bool isTopicUnlocked(String userId, String topicId) {
  final topic = getTopic(topicId);
  
  if (topic.prerequisites.isEmpty) {
    return true;
  }
  
  // Prerequisitos deben tener mastery >= 0.5
  for (final prereqId in topic.prerequisites) {
    final prereqMastery = getUserTopicMastery(userId, prereqId);
    if (prereqMastery < 0.5) {
      return false;
    }
  }
  
  return true;
}
```

---

## 5. SISTEMA ANTI-GAMING DETALLADO

### 5.1 Regla Principal

**Solo hay XP por aprendizaje NUEVO o REPASO VÁLIDO.**

```
┌─────────────────────────────────────────────────────────────────────┐
│                     VALIDACIÓN DE XP                                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  PREGUNTA NUEVA (nunca respondida)                                  │
│  └── Correcta → +10 XP ✅                                           │
│  └── Incorrecta → 0 XP                                              │
│                                                                     │
│  REPASO VÁLIDO                                                      │
│  └── Condición: días_desde_último >= ceil(mastery × 7)              │
│  └── Correcta → +5 XP ✅                                            │
│  └── Incorrecta → 0 XP                                              │
│                                                                     │
│  REPETICIÓN INVÁLIDA (muy pronto)                                   │
│  └── Correcta → 0 XP ❌                                             │
│  └── Incorrecta → 0 XP                                              │
│  └── Mensaje: "Espera X días más para ganar XP"                     │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 5.2 Fórmula de Repaso Válido

```dart
bool isValidReview(double topicMastery, int daysSinceLastAttempt) {
  // mastery 0.3 → 3 días
  // mastery 0.5 → 4 días
  // mastery 0.8 → 6 días
  // mastery 1.0 → 7 días
  final minDaysRequired = (topicMastery * 7).ceil();
  
  return daysSinceLastAttempt >= minDaysRequired;
}
```

### 5.3 Detección de Comportamiento Sospechoso

```dart
class SuspiciousActivityDetector {
  static Future<List<Alert>> analyzeSession(String sessionId) async {
    final answers = await getSessionAnswers(sessionId);
    final alerts = <Alert>[];
    
    // Check 1: Respuestas muy rápidas (< 3 seg)
    final fastAnswers = answers.where((a) => a.timeSpent < 3).length;
    if (fastAnswers > answers.length * 0.5) {
      alerts.add(Alert(
        type: 'suspicious_timing',
        message: 'Respuestas muy rápidas: ${fastAnswers}/${answers.length}',
      ));
    }
    
    // Check 2: Patrón de respuestas (ABABAB o AAAA)
    final pattern = answers.map((a) => a.selectedOption).join('');
    if (hasRepeatingPattern(pattern)) {
      alerts.add(Alert(
        type: 'pattern_detected',
        message: 'Patrón detectado: $pattern',
      ));
    }
    
    // Check 3: 100% en preguntas difíciles
    final hardQuestions = answers.where((a) => a.difficulty == 'hard');
    final hardCorrect = hardQuestions.where((a) => a.isCorrect).length;
    if (hardQuestions.length >= 5 && hardCorrect == hardQuestions.length) {
      alerts.add(Alert(
        type: 'unrealistic_accuracy',
        message: '100% en preguntas difíciles',
      ));
    }
    
    return alerts;
  }
}
```

---

## 6. TRIGGERS PSICOLÓGICOS

### 6.1 Matriz de Técnicas

| Técnica | Implementación | Efecto |
|---------|----------------|--------|
| **Aversión a pérdida** | Racha en riesgo, descenso liga | Miedo > deseo de ganar |
| **Recompensas variables** | XP varía, cofres misteriosos | Dopamina por incertidumbre |
| **Prueba social** | Leaderboards, rankings | Competencia social |
| **Escasez** | Raids limitados, 3 ads/día | FOMO |
| **Progreso visible** | Barras, radares, estrellas | Deseo de completar |
| **Compromiso** | Racha acumulada, tiempo invertido | Costo hundido |
| **Reciprocidad** | Oro de bienvenida | Obligación de devolver |
| **Inmediatez** | Feedback instantáneo | Gratificación inmediata |

### 6.2 Loop Principal (Diario)

```
TRIGGER → Notificación / Widget / Racha en riesgo
    │
    ▼
ACCIÓN → Abrir app, completar lección, ganar 20 XP
    │
    ▼
RECOMPENSA VARIABLE → XP, Oro, Combo, Racha, Level up
    │
    ▼
INVERSIÓN → Tiempo invertido, racha acumulada
    │
    └───────► Vuelve al TRIGGER mañana
```

### 6.3 Loop Semanal (Competencia)

```
TRIGGER → Inicio de semana, posición en liga
    │
    ▼
ACCIÓN → Acumular XP, participar en Boss Raid
    │
    ▼
RECOMPENSA → Ascenso de liga, Oro, Badge
    │
    ▼
INVERSIÓN → Posición ganada, reputación
    │
    └───────► Nueva semana, nuevo grupo
```

---

## 7. DOPAMINE ENGINE (TIMELINES DE ANIMACIÓN)

### 7.1 Respuesta Correcta (600ms)

```
T+0ms:    Opción → VERDE + border glow
T+50ms:   Haptic: DOBLE PULSO | Sound: "ding.mp3"
T+100ms:  Checkmark (✓) bounce | "+10 XP" floats up
T+200ms:  Si combo ≥3: Badge "COMBO x{N}" + sparkles
T+300ms:  Progress bar avanza | Si combo ≥5: screen shake
T+400ms:  Combo counter scale animation
T+600ms:  Slide a siguiente pregunta
```

### 7.2 Respuesta Incorrecta (800ms)

```
T+0ms:    Opción → ROJO + horizontal shake
T+50ms:   Haptic: HEAVY IMPACT | Sound: "wrong.mp3"
T+100ms:  X mark | Corazón "crack" animation
T+150ms:  Opción CORRECTA se ilumina VERDE
T+200ms:  Heart counter: 5 → 4 | Combo reset
T+400ms:  Explanation card slides up
T+800ms:  Botón "Continuar" aparece
```

### 7.3 Lección Completa (3000ms)

```
T+0ms:    Screen fade a overlay oscuro
T+200ms:  Mascota entra desde bottom (bounce)
T+400ms:  Mascota celebration dance
T+500ms:  Haptic: TRIPLE PULSE | Sound: "fanfare.mp3"
T+600ms:  Confetti explosion (Lottie)
T+800ms:  "¡LECCIÓN COMPLETADA!" bounce-in
T+1000ms: XP counter count-up (0 → final)
T+1200ms: Stars aparecen: ⭐ ... ⭐⭐ ... ⭐⭐⭐
T+1500ms: Gold counter count-up
T+2000ms: Stats adicionales fade-in
T+2500ms: Botón "CONTINUAR" aparece
```

### 7.4 Haptic Patterns

```dart
class HapticPatterns {
  static const correctAnswer = [
    Pulse(intensity: 0.6, duration: 30),
    Pause(duration: 50),
    Pulse(intensity: 0.8, duration: 30),
  ];
  
  static const wrongAnswer = [
    Pulse(intensity: 1.0, duration: 100),
  ];
  
  static const comboMilestone = [
    Pulse(0.4, 20), Pause(30),
    Pulse(0.6, 20), Pause(30),
    Pulse(0.8, 20),
  ];
  
  static const lessonComplete = [
    Pulse(0.8, 50), Pause(100),
    Pulse(0.8, 50), Pause(100),
    Pulse(1.0, 100),
  ];
}
```

---

## 8. ARQUITECTURA TÉCNICA COMPLETA

### 8.1 Stack Tecnológico

| Capa | Tecnología |
|------|------------|
| Mobile | Flutter 3.x |
| State | Riverpod 2.x |
| Local DB | Hive |
| Backend | FastAPI (Python) |
| Database | PostgreSQL |
| Cache | Redis |
| Auth | Firebase Auth |
| Analytics | Firebase Analytics |
| Push | Firebase Cloud Messaging |
| Ads | Google AdMob |
| AI | Claude 3.5 Sonnet |

### 8.2 Estructura de Carpetas Flutter

```
lib/
├── core/
│   ├── config/
│   ├── constants/
│   ├── errors/
│   ├── network/
│   ├── storage/
│   ├── sync/
│   └── utils/
│
├── features/
│   ├── auth/
│   ├── onboarding/
│   ├── practice/
│   ├── diagnostic/
│   ├── engagement/
│   ├── leagues/
│   ├── shop/
│   ├── profile/
│   └── study_plan/
│
├── shared/
│   ├── providers/
│   └── widgets/
│
├── app.dart
└── main.dart
```

### 8.3 Sincronización Offline-First

```
DISPOSITIVO                          SERVIDOR
┌───────────────────┐               ┌───────────────────┐
│      HIVE         │               │    POSTGRESQL     │
│   (Cache local)   │               │   (Fuente final)  │
└─────────┬─────────┘               └─────────┬─────────┘
          │                                   │
          ▼                                   │
┌───────────────────┐                         │
│   ACTION QUEUE    │─────── HTTP ───────────►│
│  (Cola de sync)   │                         │
└───────────────────┘                         │
          │                                   │
          ▼                                   │
┌───────────────────┐                         │
│   SYNC MANAGER    │◄───── Resolve ──────────┘
│ (Conflict resolve)│
└───────────────────┘
```

**Reglas de Conflicto:**
- Server wins: hearts, gold, premium_status, league_xp
- Client wins: mastery_updates, answer_history
- Last write wins: settings, preferences

---

## 9. APÉNDICES TÉCNICOS

### 9.1 Constantes del Sistema

```dart
abstract class GameConstants {
  // Hearts
  static const maxHearts = 5;
  static const heartRegenMinutes = 240;  // 4 horas
  static const maxAdsPerDay = 3;
  static const heartRefillCostGold = 150;
  
  // Streak
  static const dailyXPGoal = 20;
  static const streakResetHour = 4;  // 4:00 AM
  static const streakFreezeCost = 200;
  static const streakRepairCost = 300;
  static const streakRepairWindowHours = 24;
  
  // XP
  static const xpNewQuestion = 10;
  static const xpValidReview = 5;
  static const xpLesson3Stars = 15;
  static const xpLesson2Stars = 10;
  static const xpLesson1Stars = 5;
  
  // Combo
  static const maxComboBonus = 15;
  static const comboTimeoutSeconds = 30;
  
  // Lessons
  static const questionsPerLesson = 15;
  static const questionsPerQuickDiag = 15;
  static const questionsPerBossRaid = 20;
  
  // Leagues
  static const leagueGroupSize = 30;
  static const leaguePromotionCount = 10;
  static const leagueRelegationCount = 5;
  
  // Boss Raid
  static const bossRaidEntryCost = 100;
  static const bossRaidFreeStreakDays = 5;
  static const bossRaidXPMultiplier = 3.0;
  
  // Millionaire
  static const millionaireMaxDaily = 3;
  static const millionaireAICost = 50;
}
```

### 9.2 Endpoints API Principales

```yaml
# Auth
POST /auth/login
POST /auth/google
POST /auth/apple
POST /auth/guest

# Practice
GET  /questions
POST /answers/submit

# Diagnostic
POST /diagnostic/quick/start
POST /diagnostic/quick/submit
POST /diagnostic/deep/start
POST /diagnostic/deep/submit

# Engagement
GET  /hearts/status
POST /hearts/refill
GET  /streak/status
POST /streak/repair

# Leagues
GET  /leagues/current
GET  /leagues/leaderboard

# Boss Raid
GET  /boss-raid/status
POST /boss-raid/join

# Study Plan
GET  /study-plan
POST /study-plan/generate

# Sync
POST /sync/batch
```

### 9.3 Providers Riverpod Principales

```dart
// Auth
final authProvider = StateNotifierProvider<AuthNotifier, AuthState>(...);
final currentUserProvider = Provider<User?>(...);

// Engagement
final heartsProvider = StateNotifierProvider<HeartsNotifier, HeartsState>(...);
final streakProvider = StateNotifierProvider<StreakNotifier, StreakState>(...);
final engagementProvider = StateNotifierProvider<EngagementNotifier, EngagementState>(...);

// Practice
final practiceProvider = StateNotifierProvider.autoDispose<PracticeNotifier, PracticeState>(...);
final comboProvider = StateNotifierProvider.autoDispose<ComboNotifier, ComboState>(...);

// Leagues
final leaguesProvider = StateNotifierProvider<LeaguesNotifier, LeaguesState>(...);
final bossRaidProvider = StateNotifierProvider.autoDispose<BossRaidNotifier, BossRaidState>(...);

// Connectivity
final connectivityProvider = StreamProvider<ConnectivityResult>(...);
final isOnlineProvider = Provider<bool>(...);
```

---

## ROADMAP DE DESARROLLO (8 SEMANAS)

### Semana 1-2: Foundation
- [ ] Setup Flutter + FastAPI + PostgreSQL
- [ ] Auth completo (Google, Apple, Email, Guest)
- [ ] HeartSystem con 4h regeneration
- [ ] StreakSystem con 4AM logic
- [ ] Sync offline básico

### Semana 3-4: Core Learning
- [ ] Quick Diagnostic (15 preguntas)
- [ ] Deep Diagnostic por área
- [ ] Algoritmo SM-2 adaptativo
- [ ] Anti-gaming validation
- [ ] Modo Millonario + comodines

### Semana 5-6: Social Layer
- [ ] League system completo
- [ ] Weekly jobs (assign + process)
- [ ] Boss Raid
- [ ] Push notifications

### Semana 7-8: Polish & Launch
- [ ] Onboarding completo (6 pasos)
- [ ] Animaciones Rive/Lottie
- [ ] Plan de estudio con IA
- [ ] Beta test 50 usuarios
- [ ] Store submission

---

**Este documento complementa ICFES_LEVELING_LOGICA_NEGOCIO_v2.md**

*"El Sistema te observa, Cazador."*