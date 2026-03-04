# Conquest Mode: Documento Maestro de Producto y Desarrollo

**Estado:** Desarrollo Activo (Core Funcional, Features de Polishing pendientes)
**Version:** 3.0
**Fecha:** 29 de Diciembre, 2025
**Audiencia:** Desarrolladores, Diseñadores, Product Managers

Este documento es la referencia definitiva para el "Modo Conquista", el RPG educativo de ICFES Leveling inspirado en *Solo Leveling*. Contiene vision de producto, arquitectura tecnica, gap analysis y roadmap de implementacion.

---

## Tabla de Contenidos

1. [Vision y Principios Fundamentales](#1-vision-y-principios-fundamentales)
2. [Diseno de los 5 Reinos](#2-diseno-de-los-5-reinos)
3. [Estructura de Nodos por Reino](#3-estructura-de-nodos-por-reino)
4. [Flujo UX Completo del Modo Conquista](#4-flujo-ux-completo-del-modo-conquista)
5. [Sistema de Combate](#5-sistema-de-combate)
6. [Timelines de Feedback Dopaminergico](#6-timelines-de-feedback-dopaminergico)
7. [La Voz del Sistema](#7-la-voz-del-sistema)
8. [Diseno de Audio y Haptics](#8-diseno-de-audio-y-haptics)
9. [Sistemas de Progresion](#9-sistemas-de-progresion)
10. [Arquitectura Tecnica Actual](#10-arquitectura-tecnica-actual)
11. [Gap Analysis: Lo Implementado vs Lo Faltante](#11-gap-analysis-lo-implementado-vs-lo-faltante)
12. [Especificaciones de Base de Datos](#12-especificaciones-de-base-de-datos)
13. [Anti-Patterns a Evitar](#13-anti-patterns-a-evitar)
14. [Roadmap de Implementacion](#14-roadmap-de-implementacion)
15. [Assets Requeridos](#15-assets-requeridos)

---

## 1. Vision y Principios Fundamentales

### 1.1 Que es el Modo Conquista

El Modo Conquista es el **core gameplay loop** de ICFES Leveling. NO es un juego de trivia simple, sino una experiencia RPG single-player donde el usuario "conquista" territorios educativos respondiendo preguntas. Cada area del ICFES es un Reino con su propia estetica, enemigos y jefe final.

### 1.2 Los 3 Pilares del Modo Conquista

| Pilar | Descripcion | Implementacion |
|-------|-------------|----------------|
| **Narrativa Inmersiva** | "Despierta como un Cazador de Rango-E y escala hasta convertirte en S-Rank". Cada sesion de estudio es una mision en un mundo de fantasia oscura. | Dialogo del Sistema, nombres tematicos, progresion de rango visible |
| **Audio Dopaminergico** | Feedback sonoro inmediato y satisfactorio. Una "Voz del Sistema" guia y motiva con frases epicas, creando una experiencia emocionalmente resonante. | SoundManager con voiceover, SFX sincronizados, haptics |
| **Gamificacion Educativa** | Aprender es ganar XP. Equivocarse tiene un costo (corazones), pero el aprendizaje NUNCA se bloquea gracias al **Grace Mode**. | Sistema de corazones, explicaciones, modo practica |

### 1.3 Diferenciadores Clave vs Competencia

| Aspecto | Triviador | Duolingo | ICFES Leveling (Conquista) |
|---------|-----------|----------|----------------------------|
| **Bloqueo por vidas** | Si | Si (2h espera) | **NO** - Grace Mode permite continuar |
| **Explicaciones** | No | Parcial | **SI** - Siempre con explicacion detallada |
| **Offline** | No | Parcial | **100%** - Cola de sincronizacion |
| **Narrador con voz** | Perdido (queja #1) | No | **SI** - "La Voz del Sistema" |
| **Graficos** | 3D (rechazado) | 2D | **2D hand-painted** |
| **Enfoque** | Entretenimiento | Idiomas | **ICFES Colombia** |

### 1.4 Principio Etico Fundamental

> **"Nunca bloquear el aprendizaje."**

Si el usuario se queda sin corazones, puede seguir practicando en **Grace Mode** sin ganar XP ni Oro. La penalizacion es economica, no educativa.

---

## 2. Diseno de los 5 Reinos

### 2.1 Portal Central (Hub)

La navegacion parte de un Portal Central que muestra los 5 Reinos. Cada Reino representa un area del ICFES.

```
+-------------------------------------------------------------------------+
|                      PANTALLA PRINCIPAL: PORTAL DE REINOS               |
+-------------------------------------------------------------------------+
|                                                                         |
|                           TORRE CENTRAL                                 |
|                         (Tu rango global: C-Rank)                       |
|                         (Puntaje proyectado: 340)                       |
|                                                                         |
|           +-----------+                       +-----------+             |
|           |  [MATE]   |                       | [LECTURA] |             |
|           |  C-Rank   |                       |  B-Rank   |             |
|           |   45%     |                       |   62%     |             |
|           +-----------+                       +-----------+             |
|                                                                         |
|                            +-----------+                                |
|                            | [CIENCIAS]|                                |
|                            |  D-Rank   |                                |
|                            |   28%     |                                |
|                            +-----------+                                |
|                                                                         |
|           +-----------+                       +-----------+             |
|           | [SOCIALES]|                       | [INGLES]  |             |
|           |  C-Rank   |                       |  B-Rank   |             |
|           |   51%     |                       |   58%     |             |
|           +-----------+                       +-----------+             |
|                                                                         |
|  [!] "El Sistema recomienda: CIENCIAS (area mas debil)"                 |
|                                                                         |
|  [Racha: 7 dias]  [Corazones: 5/5]  [Oro: 1,250]  [Nivel: 12]           |
|                                                                         |
+-------------------------------------------------------------------------+
```

### 2.2 Los 5 Reinos: Definicion Completa

| Reino | Area ICFES | Tema Visual | Paleta de Colores | Boss Final | Ambiente Sonoro |
|-------|------------|-------------|-------------------|------------|-----------------|
| **La Espira del Calculo** | Matematicas | Torres de cristal flotantes, runas numericas brillando, geometria sagrada | Cyan + Dorado + Azul profundo | Dragon del Calculo | Mistico, cristalino |
| **La Biblioteca del Saber** | Lectura Critica | Biblioteca infinita, bosque de libros vivientes, pergaminos flotantes | Ambar + Sepia + Borgoña | Esfinge de las Letras | Paginas susurrando, madera |
| **La Forja Atomica** | Ciencias Naturales | Volcan-laboratorio, biomas contrastantes (jungla/artico/desierto), cristales de elementos | Verde neon + Purpura + Naranja volcanico | Hidra del Laboratorio | Burbujas, fuego, naturaleza |
| **Las Ruinas del Imperio** | Sociales y Ciudadanas | Civilizaciones caidas fusionadas (egipcia, romana, precolombina), monumentos cubiertos de vegetacion | Terracota + Oro antiguo + Verde selva | Titan de la Historia | Viento en ruinas, ecos |
| **El Archipielago de las Lenguas** | Ingles | Islas flotantes conectadas por puentes de letras, faros con alfabetos, barcos con velas de paginas | Teal oceanico + Plata lunar + Blanco niebla | Fenix Poliglota | Oceanico, gaviota, campanas |

### 2.3 Prompts para Generacion de Mapas (Midjourney/DALL-E)

**Prompt Base (usar para todos):**
```
Fantasy RPG world map for educational mobile game, top-down isometric view,
dark mystical atmosphere with glowing pathways connecting 8-10 nodes,
foggy borders, hand-painted digital art style similar to mobile strategy games,
4K detailed illustration, dramatic lighting with magical glow effects,
muted color palette with selective vibrant accents on interactive areas,
ethereal mist surrounding the edges, NO text, NO UI elements,
just the illustrated map with clear node positions --ar 9:16 --v 6
```

**Matematicas - La Espira del Calculo:**
```
Fantasy RPG world map, isometric top-down view, dark mystical atmosphere.
Theme: Ancient mathematical civilization of crystalline towers and geometric magic.
Central element: A massive floating tower made of interconnected geometric shapes
(pyramids, spheres, cubes, dodecahedrons) with soft glowing mathematical symbols.
8 distinct node locations connected by glowing cyan energy pathways.
Color palette: Deep midnight blue background, cyan and gold glows,
purple crystal accents, white starlight particles.
Style: Hand-painted digital art, mobile game aesthetic, 4K.
```

**Lectura - La Biblioteca del Saber:**
```
Fantasy RPG world map, isometric top-down view, dark mystical atmosphere.
Theme: Infinite library realm where knowledge takes physical form.
Central element: A grand library spire with impossibly tall bookshelves
spiraling upward into clouds, with floating books orbiting the structure.
8 distinct node locations connected by glowing amber pathways made of flowing ink.
Color palette: Warm sepia and amber tones, candlelight orange glows,
deep burgundy shadows, golden page edges.
Style: Hand-painted digital art, cozy yet mysterious, 4K.
```

**Ciencias - La Forja Atomica:**
```
Fantasy RPG world map, isometric top-down view, dark mystical atmosphere.
Theme: Volcanic alchemical realm where science becomes magic.
Central element: An active volcano with a grand laboratory built into its crater,
with different biomes (jungle, arctic, desert) in each section.
8 distinct node locations connected by glowing green and purple energy streams.
Color palette: Volcanic oranges and reds, bioluminescent greens and blues,
toxic purples, crystalline whites.
Style: Hand-painted digital art, dramatic biome contrast, 4K.
```

**Sociales - Las Ruinas del Imperio:**
```
Fantasy RPG world map, isometric top-down view, dark mystical atmosphere.
Theme: Fallen civilization with echoes of world history and cultures merged.
Central element: A grand colosseum in partial ruins at the center,
with a world map mosaic visible on its floor, pyramids and temples around.
8 distinct node locations connected by glowing terracotta and gold stone pathways.
Color palette: Golden hour lighting, terracotta and sandstone,
bronze and marble accents, jungle greens encroaching on ancient stone.
Style: Hand-painted digital art, archaeological discovery feel, 4K.
```

**Ingles - El Archipielago de las Lenguas:**
```
Fantasy RPG world map, isometric top-down view, dark mystical atmosphere.
Theme: Floating island archipelago where language is power.
Central element: A grand lighthouse tower made of stacked oversized letters
on the main island, smaller islands with different linguistic themes.
8 distinct island nodes connected by glowing teal bridges made of words.
Color palette: Teal ocean waters, silver moonlight reflections,
warm island sunset accents, paper-white sails, ink-blue ocean depths.
Style: Hand-painted digital art, nautical fantasy academy feel, 4K.
```

---

## 3. Estructura de Nodos por Reino

Cada Reino tiene **8 nodos** (7 subtemas + 1 Boss Final) conectados en un arbol de progresion. El usuario debe completar nodos basicos para desbloquear avanzados.

### 3.1 Estructura General de Arbol

```
                    +---------------------+
                    |   BOSS FINAL        |
                    |   (Desbloquea al    |
                    |   80% del Reino)    |
                    +----------+----------+
                               |
              +----------------+----------------+
              |                |                |
       +------v------+  +------v------+  +------v------+
       |   NODO 5    |  |   NODO 6    |  |   NODO 7    |
       |  Avanzado   |  |  Avanzado   |  |  Avanzado   |
       +------+------+  +------+------+  +------+------+
              |                |                |
              +----------------+----------------+
                               |
              +----------------+----------------+
              |                |                |
       +------v------+  +------v------+  +------v------+
       |   NODO 2    |  |   NODO 3    |  |   NODO 4    |
       | Intermedio  |  | Intermedio  |  | Intermedio  |
       +------+------+  +------+------+  +------+------+
              |                |                |
              +----------------+----------------+
                               |
                        +------v------+
                        |   NODO 1    |
                        |   Basico    |
                        |  (Entrada)  |
                        +------+------+
                               |
                        +------v------+
                        |   PORTAL    |
                        | (Diagnostico|
                        |  del area)  |
                        +-------------+
```

### 3.2 Nodos Detallados por Reino

#### La Espira del Calculo (Matematicas)

| Nodo | Subtema ICFES | Requisito Desbloqueo | Min. Preguntas | Monstruo Guardian |
|------|---------------|----------------------|----------------|-------------------|
| Portal | Diagnostico Inicial | Siempre abierto | 15-18 | Tutorial (sin daño) |
| Nodo 1 | Aritmetica y Operaciones | Completar diagnostico | 50+ | Golem de Piedra |
| Nodo 2 | Algebra Basica | Aritmetica 50% | 50+ | Elemental de Cristal |
| Nodo 3 | Geometria Euclidiana | Aritmetica 50% | 50+ | Guardian Angular |
| Nodo 4 | Estadistica Descriptiva | Aritmetica 50% | 50+ | Oraculo de Datos |
| Nodo 5 | Algebra Avanzada y Funciones | Algebra Basica 70% | 50+ | Mago de Ecuaciones |
| Nodo 6 | Trigonometria | Geometria 60% + Algebra 60% | 50+ | Serpiente Sinusoidal |
| Nodo 7 | Calculo y Limites | Funciones 80% | 50+ | Espectro del Infinito |
| Boss | Dragon del Calculo | 80% Reino completado | 20 | Dragon del Calculo |

#### La Biblioteca del Saber (Lectura Critica)

| Nodo | Subtema ICFES | Requisito Desbloqueo | Min. Preguntas | Monstruo Guardian |
|------|---------------|----------------------|----------------|-------------------|
| Portal | Diagnostico Inicial | Siempre abierto | 15-18 | Libro Animado |
| Nodo 1 | Comprension Literal | Completar diagnostico | 50+ | Duende Lector |
| Nodo 2 | Vocabulario en Contexto | Literal 50% | 50+ | Espiritu del Diccionario |
| Nodo 3 | Identificacion de Ideas Principales | Literal 50% | 50+ | Guardian del Indice |
| Nodo 4 | Inferencia y Deduccion | Ideas Principales 60% | 50+ | Sombra del Subtexto |
| Nodo 5 | Analisis de Argumentos | Inferencia 70% | 50+ | Abogado Espectral |
| Nodo 6 | Evaluacion Critica | Analisis 70% | 50+ | Juez de Pergaminos |
| Nodo 7 | Sintesis y Comparacion | Evaluacion 75% | 50+ | Bibliotecario Ancestral |
| Boss | Esfinge de las Letras | 80% Reino completado | 20 | Esfinge de las Letras |

#### La Forja Atomica (Ciencias Naturales)

| Nodo | Subtema ICFES | Requisito Desbloqueo | Min. Preguntas | Monstruo Guardian |
|------|---------------|----------------------|----------------|-------------------|
| Portal | Diagnostico Inicial | Siempre abierto | 15-18 | Slime Experimental |
| Nodo 1 | Biologia Celular y Organismos | Completar diagnostico | 50+ | Bacteria Gigante |
| Nodo 2 | Quimica: Materia y Reacciones | Completar diagnostico | 50+ | Golem Alquimico |
| Nodo 3 | Fisica: Mecanica Basica | Completar diagnostico | 50+ | Automata de Engranajes |
| Nodo 4 | Biologia Avanzada: Ecosistemas | Bio Basica 60% | 50+ | Bestia del Pantano |
| Nodo 5 | Quimica Avanzada: Enlace y Estequiometria | Quim Basica 60% | 50+ | Elemental Molecular |
| Nodo 6 | Fisica Avanzada: Energia y Ondas | Fis Basica 60% | 50+ | Espectro Electrico |
| Nodo 7 | Ciencia Integrada | 2 de 3 avanzados 70% | 50+ | Quimera del Laboratorio |
| Boss | Hidra del Laboratorio | 80% Reino completado | 20 | Hidra del Laboratorio |

#### Las Ruinas del Imperio (Sociales y Ciudadanas)

| Nodo | Subtema ICFES | Requisito Desbloqueo | Min. Preguntas | Monstruo Guardian |
|------|---------------|----------------------|----------------|-------------------|
| Portal | Diagnostico Inicial | Siempre abierto | 15-18 | Esqueleto Soldado |
| Nodo 1 | Historia de Colombia | Completar diagnostico | 50+ | Conquistador Fantasma |
| Nodo 2 | Geografia Fisica y Humana | Completar diagnostico | 50+ | Coloso de Piedra |
| Nodo 3 | Constitucion y Ciudadania | Completar diagnostico | 50+ | Guardia de la Ley |
| Nodo 4 | Historia Universal | Historia Colombia 60% | 50+ | Faraon Resucitado |
| Nodo 5 | Economia Basica | Geografia 60% | 50+ | Mercader Espectral |
| Nodo 6 | Competencias Ciudadanas | Constitucion 70% | 50+ | Senador Corrupto |
| Nodo 7 | Integracion Socio-Historica | 2 de 3 avanzados 70% | 50+ | General de las Eras |
| Boss | Titan de la Historia | 80% Reino completado | 20 | Titan de la Historia |

#### El Archipielago de las Lenguas (Ingles)

| Nodo | Subtema ICFES | Requisito Desbloqueo | Min. Preguntas | Monstruo Guardian |
|------|---------------|----------------------|----------------|-------------------|
| Portal | Diagnostico Inicial | Siempre abierto | 15-18 | Loro Parlante |
| Nodo 1 | Grammar Fundamentals | Completar diagnostico | 50+ | Gramatico Rigido |
| Nodo 2 | Core Vocabulary | Completar diagnostico | 50+ | Diccionario Viviente |
| Nodo 3 | Reading Comprehension Basic | Grammar 50% | 50+ | Lector de Mapas |
| Nodo 4 | Grammar Advanced: Tenses & Modals | Grammar Basics 70% | 50+ | Reloj Parlante |
| Nodo 5 | Contextual Vocabulary | Vocabulary 70% | 50+ | Camaleón Linguistico |
| Nodo 6 | Critical Reading & Inference | Reading 70% | 50+ | Detective Bilingue |
| Nodo 7 | Integrated English Skills | 2 de 3 avanzados 70% | 50+ | Embajador Poliglota |
| Boss | Fenix Poliglota | 80% Reino completado | 20 | Fenix Poliglota |

### 3.3 Mecanica de Desbloqueo

```python
def can_unlock_node(user_id: str, node_id: str) -> bool:
    node = get_node(node_id)
    user_progress = get_user_kingdom_progress(user_id, node.kingdom_id)

    # El Portal siempre esta abierto
    if node.is_portal:
        return True

    # Nodos basicos: requieren diagnostico completado
    if node.tier == 1:
        return user_progress.diagnostic_completed

    # Nodos intermedios y avanzados: verificar prerrequisitos
    for prereq in node.prerequisites:
        prereq_progress = get_user_node_progress(user_id, prereq.node_id)
        if prereq_progress.mastery_percent < prereq.required_percent:
            return False

    return True

def can_challenge_boss(user_id: str, kingdom_id: str) -> bool:
    kingdom_progress = get_user_kingdom_progress(user_id, kingdom_id)
    return kingdom_progress.overall_mastery >= 0.80  # 80% del reino
```

---

## 4. Flujo UX Completo del Modo Conquista

### 4.1 Flujo Principal: Portal -> Reino -> Nodo -> Batalla

```
[Portal de Reinos]
       |
       v
[Seleccionar Reino] --> Voz: "Entrando al Dungeon..."
       |
       v
[Mapa del Reino] --> Muestra nodos desbloqueados/bloqueados
       |
       v
[Seleccionar Nodo] --> Voz: "Mision aceptada."
       |
       v
[Pantalla Pre-Batalla] --> Info del monstruo, preguntas restantes
       |
       v
[Batalla (Loop de Preguntas)]
       |
       +-- Pregunta mostrada
       |      |
       |      v
       |   Seleccionar respuesta
       |      |
       |      v
       |   Tocar "ATACAR"
       |      |
       |      v
       |   Validacion servidor
       |      |
       |      +-- Correcta --> Feedback positivo --> Dano al enemigo
       |      |
       |      +-- Incorrecta --> Feedback negativo --> Explicacion --> Dano al jugador
       |      |
       |      v
       |   Siguiente pregunta (si hay mas)
       |
       v
[Resultado de Batalla]
       |
       +-- Victoria --> XP, Oro, Estrellas, posible subida de nivel/rango
       |
       +-- Derrota --> XP parcial, sin Oro, opcion de reintentar
```

### 4.2 Pantalla Pre-Batalla

```
+---------------------------------------------+
|  LA ESPIRA DEL CALCULO                      |
|  Nodo 3: Geometria Euclidiana               |
+---------------------------------------------+
|                                             |
|         [Imagen del Monstruo]               |
|         GUARDIAN ANGULAR                    |
|         Nivel 15                            |
|                                             |
|  Preguntas: 10-15                           |
|  Dificultad: Media                          |
|  Recompensa: ~100 XP, ~50 Oro               |
|                                             |
|  Tu progreso en este nodo: 35% (2/3 *)      |
|                                             |
|  +---------------------------------------+  |
|  |        [INICIAR BATALLA]              |  |
|  +---------------------------------------+  |
|                                             |
|  [< Volver al Mapa]                         |
+---------------------------------------------+
```

### 4.3 Pantalla de Batalla (Durante Combate)

```
+---------------------------------------------+
|  GEOMETRIA       Pregunta 5/12    [30s]     |
|  [Corazones: 4]  [Combo: x3]   [+25 XP]     |
+---------------------------------------------+
|                                             |
|  +------------------+  +------------------+ |
|  | [HP Jugador]     |  | [HP Enemigo]     | |
|  | ||||||||....     |  | ||||||........   | |
|  | Cazador (Tu)     |  | Guardian Angular | |
|  +------------------+  +------------------+ |
|                                             |
+---------------------------------------------+
|                                             |
|  En un triangulo rectangulo, si los        |
|  catetos miden 3 y 4, el valor de la       |
|  hipotenusa es:                             |
|                                             |
|  +-------------------+  +-------------------+|
|  | A) 5              |  | B) 6              ||
|  +-------------------+  +-------------------+|
|                                             |
|  +-------------------+  +-------------------+|
|  | C) 7              |  | D) 12             ||
|  +-------------------+  +-------------------+|
|                                             |
|  [Barra de tiempo: ================----]    |
|                                             |
|  [Pista: 50 Oro]                            |
|                                             |
+---------------------------------------------+
```

---

## 5. Sistema de Combate

### 5.1 Mecanica de Dano (Server-Side)

El calculo de dano es **autoritativo del servidor**. El cliente solo visualiza.

```python
# dungeon_service.py

def calculate_combat_result(
    user_id: str,
    encounter_id: str,
    question_id: str,
    selected_answer: str,
    time_spent_seconds: int
) -> CombatResult:

    question = get_question(question_id)
    is_correct = question.correct_answer == selected_answer

    # Dano base del jugador
    BASE_PLAYER_DAMAGE = 50
    # Dano base del enemigo
    BASE_ENEMY_DAMAGE = 20

    if is_correct:
        # Bonus por velocidad (responder en menos de 10s)
        speed_bonus = max(0, (30 - time_spent_seconds) / 30) * 0.3  # Hasta 30% bonus
        combo_bonus = min(current_combo * 0.05, 0.5)  # Hasta 50% por combo

        damage_to_enemy = int(BASE_PLAYER_DAMAGE * (1 + speed_bonus + combo_bonus))
        damage_to_player = 0
        new_combo = current_combo + 1
        xp_earned = question.xp_value * (1 + combo_bonus)
    else:
        damage_to_enemy = 0
        damage_to_player = BASE_ENEMY_DAMAGE
        new_combo = 0  # Combo se rompe
        xp_earned = 0  # No XP por respuesta incorrecta

    # Aplicar dano
    encounter.enemy_hp -= damage_to_enemy
    run.player_hp -= damage_to_player

    # Verificar fin de batalla
    enemy_defeated = encounter.enemy_hp <= 0
    player_defeated = run.player_hp <= 0

    return CombatResult(
        is_correct=is_correct,
        correct_answer_id=question.correct_answer,
        explanation=question.explanation,  # CRITICO: siempre incluir
        damage_dealt=damage_to_enemy,
        damage_taken=damage_to_player,
        enemy_current_hp=max(0, encounter.enemy_hp),
        player_current_hp=max(0, run.player_hp),
        current_combo=new_combo,
        xp_earned=int(xp_earned),
        enemy_defeated=enemy_defeated,
        player_defeated=player_defeated
    )
```

### 5.2 Sistema de Corazones

| Aspecto | Valor | Notas |
|---------|-------|-------|
| Corazones maximos | 5 | Igual que Duolingo |
| Regeneracion | 1 cada 4 horas | Mas generoso que Duolingo (2h) |
| Perdida por error | 1 corazon | Solo en modo normal |
| Recarga con Oro | 150 Oro = 5 corazones | Opcion de pago |
| Recarga con Ad | 1 corazon | Maximo 3/dia |

### 5.3 Grace Mode (Diferenciador Clave)

Cuando los corazones llegan a 0, NO se bloquea al usuario. Se ofrece:

```
+---------------------------------------------+
|                                             |
|         [Corazon Roto]                      |
|         MANA AGOTADO                        |
|                                             |
|   Has usado todos tus corazones.            |
|   Pero un Cazador no se rinde.              |
|                                             |
|  +---------------------------------------+  |
|  |  [Video] Ver anuncio (+1 corazon)     |  |
|  +---------------------------------------+  |
|                                             |
|  +---------------------------------------+  |
|  |  [Oro] Recargar (150 Oro)             |  |
|  +---------------------------------------+  |
|                                             |
|  +---------------------------------------+  |
|  |  [Reloj] Esperar (proximo: 2h 15m)    |  |
|  +---------------------------------------+  |
|                                             |
|         --- o ---                           |
|                                             |
|  +---------------------------------------+  |
|  |  [Fantasma] MODO GRACIA               |  |
|  |  Practica sin ganar XP ni Oro         |  |
|  |  (Sigue aprendiendo sin penalizacion) |  |
|  +---------------------------------------+  |
|                                             |
+---------------------------------------------+
```

**Implementacion:**

```dart
enum PracticeMode { normal, grace }

class HeartSystem {
  int hearts = 5;
  PracticeMode mode = PracticeMode.normal;
  DateTime lastHeartRegenTime;

  void onWrongAnswer() {
    if (mode == PracticeMode.normal) {
      hearts = max(0, hearts - 1);
      if (hearts == 0) {
        // NO bloquear, mostrar opciones
        _showHeartDepletedDialog();
      }
    }
    // En Grace Mode: sin penalizacion de corazones
  }

  void enterGraceMode() {
    mode = PracticeMode.grace;
    // Las recompensas se desactivan pero el juego continua
  }

  int getXPMultiplier() {
    return mode == PracticeMode.grace ? 0 : 1;
  }

  int getGoldMultiplier() {
    return mode == PracticeMode.grace ? 0 : 1;
  }
}
```

---

## 6. Timelines de Feedback Dopaminergico

### 6.1 Regla de los 600ms

Todo feedback sensorial debe completarse en **600ms** para sentirse instantaneo pero no abrupto.

### 6.2 Timeline: Respuesta Correcta

| Tiempo | Accion Visual | Accion Audio | Accion Haptic |
|--------|---------------|--------------|---------------|
| T+0ms | Opcion seleccionada -> VERDE + glow border | - | - |
| T+50ms | - | SFX: "ding" satisfactorio | Doble pulso rapido |
| T+100ms | Checkmark (check) bounce-in | Voz: "Correcto." | - |
| T+150ms | "+{XP} XP" flota hacia arriba | - | - |
| T+200ms | Si combo >= 3: Badge "COMBO x{N}" aparece | Voz: "Combo activado." (si aplica) | Triple pulso |
| T+300ms | Barra de HP enemigo baja con animacion | SFX: impacto/dano | - |
| T+400ms | Avatar enemigo hace "shake" horizontal | - | - |
| T+600ms | Transicion a siguiente pregunta | - | - |

**Implementacion Flutter:**

```dart
Future<void> _onCorrectAnswer(AnswerResult result) async {
  // T+0ms: Visual verde
  setState(() => _answerState = AnswerState.correct);

  // T+50ms: Audio + Haptic
  await Future.delayed(const Duration(milliseconds: 50));
  HapticFeedback.mediumImpact();
  _soundManager.playSFX('correct_ding');
  _systemVoice.speak('correcto');

  // T+100ms: Checkmark + XP float
  await Future.delayed(const Duration(milliseconds: 50));
  _showFloatingXP(result.xpEarned);

  // T+200ms: Combo badge si aplica
  await Future.delayed(const Duration(milliseconds: 100));
  if (result.currentCombo >= 3) {
    _showComboBadge(result.currentCombo);
    if (result.currentCombo == 3) {
      _systemVoice.speak('combo_activado');
    } else if (result.currentCombo >= 10) {
      _systemVoice.speak('imparable');
    }
  }

  // T+300ms: Dano al enemigo
  await Future.delayed(const Duration(milliseconds: 100));
  _soundManager.playSFX('enemy_hit');
  _animateEnemyHP(result.enemyCurrentHp);

  // T+400ms: Enemy shake
  await Future.delayed(const Duration(milliseconds: 100));
  _shakeEnemy();

  // T+600ms: Next question
  await Future.delayed(const Duration(milliseconds: 200));
  _loadNextQuestion();
}
```

### 6.3 Timeline: Respuesta Incorrecta

| Tiempo | Accion Visual | Accion Audio | Accion Haptic |
|--------|---------------|--------------|---------------|
| T+0ms | Opcion seleccionada -> ROJO + shake horizontal | - | - |
| T+50ms | - | SFX: "wrong" suave (no punitivo) | Impacto fuerte |
| T+100ms | X mark aparece | Voz: "Respuesta incorrecta." | - |
| T+150ms | Respuesta correcta se ilumina en VERDE | - | - |
| T+200ms | Corazon se "quiebra" con animacion, contador baja | SFX: cristal rompiendose | - |
| T+300ms | Combo badge desaparece (si habia) | - | - |
| T+400ms | Modal de explicacion slide-up desde abajo | Voz: "Analiza el error." | - |
| T+800ms | Boton "Continuar" aparece en el modal | - | - |

**Implementacion Flutter:**

```dart
Future<void> _onWrongAnswer(AnswerResult result) async {
  // T+0ms: Visual rojo + shake
  setState(() => _answerState = AnswerState.wrong);
  _shakeSelectedOption();

  // T+50ms: Audio + Haptic
  await Future.delayed(const Duration(milliseconds: 50));
  HapticFeedback.heavyImpact();
  _soundManager.playSFX('wrong_buzz');
  _systemVoice.speak('respuesta_incorrecta');

  // T+150ms: Mostrar respuesta correcta
  await Future.delayed(const Duration(milliseconds: 100));
  _highlightCorrectAnswer(result.correctAnswerId);

  // T+200ms: Perder corazon
  await Future.delayed(const Duration(milliseconds: 50));
  _soundManager.playSFX('heart_break');
  _animateHeartLoss();

  // T+300ms: Reset combo visual
  await Future.delayed(const Duration(milliseconds: 100));
  _hideCombo();

  // T+400ms: Mostrar explicacion
  await Future.delayed(const Duration(milliseconds: 100));
  _systemVoice.speak('analiza_error');
  _showExplanationModal(result.explanation);
}
```

### 6.4 Timeline: Victoria de Batalla

| Tiempo | Accion Visual | Accion Audio | Accion Haptic |
|--------|---------------|--------------|---------------|
| T+0ms | Pantalla hace fade a overlay oscuro | - | - |
| T+200ms | Enemigo hace animacion de "derrota" (desvanece) | SFX: explosion/derrota | - |
| T+400ms | - | Musica: Fanfarria de victoria | Triple pulso ascendente |
| T+600ms | Confetti explosion | - | - |
| T+800ms | "VICTORIA" bounce-in grande | Voz: "Victoria." | - |
| T+1000ms | XP counter count-up animado | SFX: coins/xp | - |
| T+1200ms | Estrellas aparecen una por una | SFX: star ding x3 | Pulso por estrella |
| T+1500ms | Oro counter count-up | - | - |
| T+2000ms | Stats adicionales fade-in | - | - |
| T+2500ms | Boton "Continuar" aparece | Voz: "Mision completada." | - |

---

## 7. La Voz del Sistema

### 7.1 Especificaciones de Voz

| Aspecto | Especificacion |
|---------|----------------|
| **Tono** | Profundo, autoritario pero no amenazante |
| **Estilo** | Similar al Sistema de Solo Leveling (neutro, informativo, epico) |
| **Idioma** | Español neutro latinoamericano (Colombia/Mexico) |
| **Genero** | Masculina grave O femenina profunda (testear con usuarios) |
| **Generacion** | ElevenLabs (recomendado) o actor de voz profesional |

### 7.2 Catalogo Completo de Frases

#### Onboarding (5 frases)
| ID | Frase | Contexto de Uso |
|----|-------|-----------------|
| `onboard_found` | "El Sistema te ha encontrado." | Primera vez que abre la app |
| `onboard_eval_start` | "Evaluacion de poder iniciada." | Inicio de diagnostico |
| `onboard_calibrating` | "Calibrando rango de Cazador..." | Procesando resultados |
| `onboard_rank_assigned` | "Rango asignado: {Rango}." | Revelar rango inicial |
| `onboard_begin` | "Tu entrenamiento comienza ahora." | Fin del onboarding |

#### Sesion Diaria (5 frases)
| ID | Frase | Contexto de Uso |
|----|-------|-----------------|
| `daily_welcome` | "Bienvenido de nuevo, Cazador." | Abrir la app (usuario existente) |
| `daily_new_day` | "Nuevo dia. Nueva oportunidad de ascender." | Primer login del dia |
| `daily_select` | "Selecciona tu campo de batalla." | Pantalla de seleccion de modo |
| `daily_mission_accept` | "Mision aceptada." | Iniciar cualquier practica |
| `daily_entering` | "Entrando al Dungeon..." | Entrar a un Reino |

#### Combate - Respuestas (7 frases)
| ID | Frase | Contexto de Uso |
|----|-------|-----------------|
| `combat_correct` | "Correcto." | Respuesta correcta |
| `combat_power_up` | "Poder incrementado." | Ganar XP significativo |
| `combat_combo` | "Combo activado." | Combo alcanza 3 |
| `combat_combo_5` | "Excelente." | Combo alcanza 5 |
| `combat_unstoppable` | "Imparable." | Combo alcanza 10+ |
| `combat_wrong` | "Respuesta incorrecta." | Respuesta incorrecta |
| `combat_analyze` | "Analiza el error." | Despues de incorrecta, antes de explicacion |

#### Corazones/Mana (3 frases)
| ID | Frase | Contexto de Uso |
|----|-------|-----------------|
| `hearts_reduced` | "Mana reducido." | Perder un corazon |
| `hearts_depleted` | "Mana agotado." | Llegar a 0 corazones |
| `hearts_restored` | "Mana restaurado." | Recuperar corazones |

#### Rachas (4 frases)
| ID | Frase | Contexto de Uso |
|----|-------|-----------------|
| `streak_maintained` | "Racha de {N} dias." | Mantener racha |
| `streak_impressive` | "Tu dedicacion es notable." | Racha >= 7 dias |
| `streak_warning` | "Advertencia: Tu racha esta en peligro." | Notificacion push |
| `streak_lost` | "Racha perdida. Pero tu poder permanece." | Perder racha |

#### Logros y Progresion (5 frases)
| ID | Frase | Contexto de Uso |
|----|-------|-----------------|
| `progress_achievement` | "Logro desbloqueado." | Desbloquear cualquier badge |
| `progress_level_up` | "Nivel alcanzado: {N}." | Subir de nivel |
| `progress_rank_up` | "Rango ascendido: {Rango}." | Subir de rango |
| `progress_victory` | "Victoria." | Ganar cualquier batalla |
| `progress_mission_complete` | "Mision completada." | Completar sesion de practica |

#### Especiales (3 frases)
| ID | Frase | Contexto de Uso |
|----|-------|-----------------|
| `special_watching` | "El Sistema te observa." | Easter egg aleatorio |
| `special_power_grows` | "Tu poder crece." | Progreso significativo |
| `special_boss_awakened` | "El Boss ha despertado." | Desbloquear Boss de Reino |

### 7.3 Implementacion de SystemVoice

```dart
class SystemVoice {
  final AudioPlayer _player = AudioPlayer();
  bool _isEnabled = true;

  static const Map<String, String> _phrases = {
    // Onboarding
    'onboard_found': 'assets/audio/voice/sistema_te_encontro.wav',
    'onboard_eval_start': 'assets/audio/voice/evaluacion_iniciada.wav',
    'onboard_calibrating': 'assets/audio/voice/calibrando_rango.wav',
    'onboard_rank_assigned': 'assets/audio/voice/rango_asignado.wav',
    'onboard_begin': 'assets/audio/voice/entrenamiento_comienza.wav',

    // Combate
    'combat_correct': 'assets/audio/voice/correcto.wav',
    'combat_combo': 'assets/audio/voice/combo_activado.wav',
    'combat_unstoppable': 'assets/audio/voice/imparable.wav',
    'combat_wrong': 'assets/audio/voice/respuesta_incorrecta.wav',
    'combat_analyze': 'assets/audio/voice/analiza_error.wav',

    // Progresion
    'progress_victory': 'assets/audio/voice/victoria.wav',
    'progress_level_up': 'assets/audio/voice/nivel_alcanzado.wav',
    'progress_rank_up': 'assets/audio/voice/rango_ascendido.wav',
    'progress_mission_complete': 'assets/audio/voice/mision_completada.wav',

    // Corazones
    'hearts_depleted': 'assets/audio/voice/mana_agotado.wav',

    // Especiales
    'special_boss_awakened': 'assets/audio/voice/boss_despertado.wav',
  };

  Future<void> speak(String phraseKey) async {
    if (!_isEnabled) return;

    final path = _phrases[phraseKey];
    if (path == null) {
      debugPrint('SystemVoice: Phrase key "$phraseKey" not found');
      return;
    }

    try {
      await _player.stop();
      await _player.play(AssetSource(path));
    } catch (e) {
      debugPrint('SystemVoice error: $e');
    }
  }

  void setEnabled(bool enabled) {
    _isEnabled = enabled;
  }
}
```

---

## 8. Diseno de Audio y Haptics

### 8.1 Musica por Contexto

| Contexto | Estilo Musical | BPM | Duracion Loop | Instrumentacion |
|----------|----------------|-----|---------------|-----------------|
| Portal de Reinos | Epico ambiental | 60-80 | 90s | Cuerdas, coro suave, synths atmosfericos |
| Mapa de Reino | Misterioso explorador | 70-90 | 60s | Flauta, arpa, percusion suave |
| Batalla Normal | Focus concentrado | 90-110 | 120s | Piano minimal, ambient pads, pulso suave |
| Batalla Boss | Intenso epico | 120-140 | 90s | Orquesta completa, coro, drums sinteticos |
| Victoria | Celebracion triunfante | 100-120 | 30s (no loop) | Fanfarria, cuerdas ascendentes |
| Derrota | Reflexivo esperanzador | 60-80 | 30s (no loop) | Piano solo, cuerdas suaves |

### 8.2 Efectos de Sonido (SFX) Requeridos

| Categoria | Nombre Archivo | Descripcion | Duracion |
|-----------|----------------|-------------|----------|
| **Respuestas** | `correct_ding.wav` | Ding satisfactorio, tono alto | 0.3s |
| | `wrong_buzz.wav` | Buzz suave, no punitivo | 0.4s |
| **Combate** | `enemy_hit.wav` | Impacto magico al enemigo | 0.5s |
| | `player_hit.wav` | Impacto recibido | 0.4s |
| | `combo_3.wav` | Energia media, whoosh | 0.6s |
| | `combo_5.wav` | Energia alta, flames | 0.7s |
| | `combo_10.wav` | Explosion epica | 1.0s |
| **Corazones** | `heart_break.wav` | Cristal rompiendose suave | 0.5s |
| | `heart_restore.wav` | Restauracion magica | 0.6s |
| **Progresion** | `xp_gain.wav` | Power up corto | 0.4s |
| | `level_up.wav` | Fanfarria corta | 1.5s |
| | `rank_up.wav` | Fanfarria mayor, epica | 2.5s |
| | `star_ding.wav` | Estrella individual | 0.3s |
| **Victoria/Derrota** | `victory_fanfare.wav` | Fanfarria completa | 3.0s |
| | `defeat_somber.wav` | Tono melancolico | 2.0s |
| **UI** | `button_tap.wav` | Click suave | 0.1s |
| | `button_confirm.wav` | Confirmacion | 0.2s |
| | `navigation.wav` | Transicion entre pantallas | 0.3s |

### 8.3 Patrones de Haptic Feedback

```dart
class HapticPatterns {
  /// Respuesta correcta: doble pulso rapido
  static void correctAnswer() {
    HapticFeedback.mediumImpact();
    Future.delayed(const Duration(milliseconds: 50), () {
      HapticFeedback.mediumImpact();
    });
  }

  /// Respuesta incorrecta: impacto fuerte unico
  static void wrongAnswer() {
    HapticFeedback.heavyImpact();
  }

  /// Combo milestone: patron escalado
  static void comboMilestone() async {
    HapticFeedback.lightImpact();
    await Future.delayed(const Duration(milliseconds: 30));
    HapticFeedback.mediumImpact();
    await Future.delayed(const Duration(milliseconds: 30));
    HapticFeedback.heavyImpact();
  }

  /// Subir de nivel: escalada dramatica
  static void levelUp() async {
    for (var i = 0; i < 3; i++) {
      HapticFeedback.lightImpact();
      await Future.delayed(const Duration(milliseconds: 50));
    }
    HapticFeedback.heavyImpact();
  }

  /// Subir de rango: patron maximo
  static void rankUp() async {
    for (var i = 0; i < 4; i++) {
      HapticFeedback.mediumImpact();
      await Future.delayed(const Duration(milliseconds: 100));
    }
    await Future.delayed(const Duration(milliseconds: 200));
    HapticFeedback.heavyImpact();
    await Future.delayed(const Duration(milliseconds: 50));
    HapticFeedback.heavyImpact();
  }

  /// Estrella ganada
  static void starEarned() {
    HapticFeedback.selectionClick();
  }
}
```

---

## 9. Sistemas de Progresion

### 9.1 Sistema de Rangos Hunter

| Rango | Mastery Global | Puntaje ICFES Estimado | Color Aura | Beneficios Desbloqueados |
|-------|----------------|------------------------|------------|--------------------------|
| E-Rank | 0-35% | 200-280 | Gris | Acceso basico |
| D-Rank | 35-50% | 280-320 | Bronce | Liga Bronce disponible |
| C-Rank | 50-65% | 320-380 | Verde | Cosmeticos intermedios |
| B-Rank | 65-80% | 380-420 | Azul | Liga Plata disponible |
| A-Rank | 80-90% | 420-470 | Purpura | Cosmeticos avanzados |
| S-Rank | 90-100% | 470-500 | Dorado | Titulo "S-Rank Hunter", Liga Diamante |

### 9.2 Sistema de Niveles

```python
def calculate_level(total_xp: int) -> int:
    """Calcula el nivel basado en XP total acumulado"""
    # Formula: XP requerido = 100 * nivel^1.5
    level = 1
    xp_for_next = 100
    remaining_xp = total_xp

    while remaining_xp >= xp_for_next:
        remaining_xp -= xp_for_next
        level += 1
        xp_for_next = int(100 * (level ** 1.5))

    return level

def xp_for_level(level: int) -> int:
    """XP necesario para alcanzar un nivel especifico"""
    return int(100 * (level ** 1.5))

# Ejemplo de progresion:
# Nivel 1 -> 2: 100 XP
# Nivel 2 -> 3: 283 XP
# Nivel 5 -> 6: 1,118 XP
# Nivel 10 -> 11: 3,162 XP
```

### 9.3 Sistema de Rachas (Streaks)

| Aspecto | Configuracion | Notas |
|---------|---------------|-------|
| Meta diaria minima | 20 XP | ~2-3 preguntas |
| Hora de reset | 4:00 AM (zona local) | Protege a nocturnos |
| Streak Freeze | 200 Oro | Maximo 5 acumulables |
| Streak Repair | 300 Oro o 1 Ad | Ventana de 24h |
| Multiplicador 7 dias | 1.2x XP | |
| Multiplicador 14 dias | 1.3x XP | |
| Multiplicador 30 dias | 1.5x XP | |
| Multiplicador 60+ dias | 1.8x XP | |

### 9.4 Sistema de Estrellas por Nodo

Cada nodo otorga 1-3 estrellas basado en rendimiento:

| Estrellas | Requisito | Recompensa Bonus |
|-----------|-----------|------------------|
| 1 Estrella | Completar el nodo (cualquier precision) | XP base |
| 2 Estrellas | >= 70% precision | +25% XP |
| 3 Estrellas | >= 90% precision | +50% XP + Badge "Perfecto" |

### 9.5 Economia (Oro)

#### Fuentes de Oro

| Fuente | Cantidad | Frecuencia |
|--------|----------|------------|
| Victoria en nodo | 25-50 | Por nodo |
| Combo x5+ | +5 por combo | Durante batalla |
| Primera victoria del dia | +25 bonus | 1/dia |
| Racha mantenida | +5 por dia de racha | Diario |
| Subir de nivel | +25 | Por nivel |
| Subir de rango | +100 | Por rango |
| Completar Reino (80%) | +200 | Por reino |

#### Usos del Oro

| Item | Costo | Efecto |
|------|-------|--------|
| Recargar 5 corazones | 150 | Restaura todos los corazones |
| Streak Freeze | 200 | Protege racha por 1 dia |
| Streak Repair | 300 | Restaura racha perdida (24h) |
| Pista en pregunta | 50 | Elimina 2 opciones incorrectas |
| Avatar Comun | 250 | Cosmetico |
| Avatar Raro | 500 | Cosmetico |
| Avatar Epico | 1,000 | Cosmetico |

---

## 10. Arquitectura Tecnica Actual

### 10.1 Diagrama de Arquitectura

```
+-------------------------------------------------------------------------+
|                            MOBILE (Flutter)                              |
+-------------------------------------------------------------------------+
|  Presentation Layer                                                      |
|  +------------------+  +------------------+  +------------------+        |
|  | DungeonMapPage   |  | BattlePage       |  | ResultsPage      |        |
|  +--------+---------+  +--------+---------+  +--------+---------+        |
|           |                     |                     |                  |
|  +--------v---------+  +--------v---------+  +--------v---------+        |
|  | DungeonProvider  |  | BattleProvider   |  | ResultsProvider  |        |
|  +--------+---------+  +--------+---------+  +--------+---------+        |
|           |                     |                     |                  |
|  +--------v---------------------v---------------------v---------+        |
|  |                    Data Layer                                |        |
|  |  +------------------+  +------------------+  +-------------+  |        |
|  |  | DungeonRemote    |  | DungeonWebSocket |  | Hive (Local)|  |        |
|  |  | DataSource       |  | Service          |  | Storage     |  |        |
|  |  +--------+---------+  +--------+---------+  +-------------+  |        |
|  +-----------|---------------------|-----------------------------+        |
+--------------|---------------------|-------------------------------------+
               |                     |
               | REST API            | WebSocket
               |                     |
+--------------|---------------------|-------------------------------------+
|              v                     v                                     |
|  +------------------+    +------------------+                            |
|  | FastAPI Routes   |    | WebSocket Server |                            |
|  | (dungeons.py)    |    | (main.py)        |                            |
|  +--------+---------+    +--------+---------+                            |
|           |                       |                                      |
|           +-----------+-----------+                                      |
|                       |                                                  |
|           +-----------v-----------+                                      |
|           |   DungeonService      |                                      |
|           |   (dungeon_service.py)|                                      |
|           +-----------+-----------+                                      |
|                       |                                                  |
|           +-----------v-----------+                                      |
|           |   SQLAlchemy Models   |                                      |
|           |   (dungeon.py)        |                                      |
|           +-----------+-----------+                                      |
|                       |                                                  |
|           +-----------v-----------+                                      |
|           |   PostgreSQL          |                                      |
|           +----------------------+                                       |
|                                                                          |
|                          BACKEND (Python/FastAPI)                        |
+--------------------------------------------------------------------------+
```

### 10.2 Archivos Clave del Proyecto

#### Frontend (Flutter)
| Archivo | Ubicacion | Funcion |
|---------|-----------|---------|
| `battle_provider.dart` | `apps/mobile/lib/features/dungeon/presentation/providers/` | State management de batalla con Riverpod |
| `battle_page.dart` | `apps/mobile/lib/features/dungeon/presentation/pages/` | UI de combate estilo Pokemon |
| `dungeon_map_page.dart` | `apps/mobile/lib/features/dungeon/presentation/pages/` | Mapa del reino con nodos |
| `dungeon_websocket_service.dart` | `apps/mobile/lib/features/dungeon/data/services/` | Comunicacion WebSocket |
| `dungeon_models.dart` | `apps/mobile/lib/features/dungeon/data/models/` | DTOs para API |
| `sound_manager.dart` | `apps/mobile/lib/core/services/` | Reproduccion de audio |

#### Backend (Python)
| Archivo | Ubicacion | Funcion |
|---------|-----------|---------|
| `dungeon_service.py` | `apps/backend/app/services/` | Logica de negocio de dungeons |
| `dungeon.py` | `apps/backend/app/models/` | Modelos SQLAlchemy |
| `dungeons.py` | `apps/backend/app/routes/` | Endpoints REST |
| `main.py` | `apps/backend/app/` | WebSocket server integration |

### 10.3 Flujo de Datos: Envio de Respuesta

1. **Usuario toca "ATACAR"**
2. **BattleProvider** llama a `submitAnswer()`
3. **DungeonRemoteDataSource** envia HTTP POST o WebSocket message:
```json
{
  "encounter_id": "enc_abc123",
  "question_id": "q_xyz789",
  "answer_id": "opt_B",
  "time_spent_seconds": 12
}
```
4. **DungeonService** (backend) procesa:
   - Obtiene pregunta de DB
   - Verifica respuesta correcta
   - Calcula dano y XP
   - Actualiza HP en DB
   - Retorna resultado
5. **Respuesta del servidor:**
```json
{
  "correct": true,
  "correct_answer_id": "opt_B",
  "explanation": "Usando el teorema de Pitagoras...",
  "damage_dealt": 65,
  "damage_taken": 0,
  "enemy_current_hp": 35,
  "player_current_hp": 100,
  "current_combo": 4,
  "xp_earned": 15,
  "enemy_defeated": false
}
```
6. **BattleProvider** actualiza estado
7. **BattlePage** renderiza feedback visual/audio

---

## 11. Gap Analysis: Lo Implementado vs Lo Faltante

### 11.1 Resumen de Estado

| Categoria | Implementado | Parcial | No Implementado |
|-----------|--------------|---------|-----------------|
| Core Gameplay | Mapas, Batallas | Temas (2 de 5) | - |
| Audio | SFX basicos | - | Voz del Sistema, Musica contextual |
| Feedback | Animaciones basicas | Timelines | Haptics, Explicaciones |
| Progresion | - | - | Rangos, Niveles, Rachas, Economia |
| Offline | - | - | Cola de sincronizacion |
| UX Critico | - | - | Grace Mode |

### 11.2 Gap #1: Voz del Sistema [CRITICO]

**Estado Actual:** `SoundManager` reproduce SFX pero NO voiceover.

**Impacto:** 80%+ de usuarios de Triviador se quejaron de perder el narrador. Es el diferenciador emocional #1.

**Solucion:**
1. Generar 10 frases iniciales con ElevenLabs (~$22/mes)
2. Crear clase `SystemVoice` (ver seccion 7.3)
3. Integrar en `BattleProvider` y `DungeonProvider`

**Archivos a modificar:**
- Crear: `apps/mobile/lib/core/services/system_voice.dart`
- Modificar: `apps/mobile/lib/features/dungeon/presentation/providers/battle_provider.dart`

### 11.3 Gap #2: Offline-First Queue [CRITICO]

**Estado Actual:** La app depende 100% de conexion. Si se pierde internet en batalla, el progreso se pierde.

**Impacto:** En Colombia (buses, metro, zonas rurales), esto es inaceptable.

**Solucion:**
```dart
// offline_action_queue.dart
class OfflineActionQueue {
  final Box<PendingAction> _queue = Hive.box('pending_actions');
  final ConnectivityService _connectivity;

  Future<void> enqueue(GameAction action) async {
    if (await _connectivity.isOnline) {
      // Enviar inmediatamente
      await _sendToServer(action);
    } else {
      // Guardar localmente
      await _queue.add(PendingAction(
        type: action.type,
        payload: action.toJson(),
        timestamp: DateTime.now(),
      ));
    }
  }

  Future<void> syncWhenOnline() async {
    for (final action in _queue.values.toList()) {
      try {
        await _sendToServer(action.toGameAction());
        await action.delete();
      } catch (e) {
        // Mantener en cola si falla
        debugPrint('Sync failed for action: $e');
      }
    }
  }
}
```

**Archivos a crear:**
- `apps/mobile/lib/core/services/offline_action_queue.dart`
- `apps/mobile/lib/core/models/pending_action.dart`

### 11.4 Gap #3: Grace Mode [CRITICO]

**Estado Actual:** No existe sistema de corazones ni Grace Mode.

**Impacto:** Sin esto, la app bloquea el aprendizaje como Duolingo (diferenciador perdido).

**Solucion:**
```dart
// heart_system.dart
class HeartSystem extends ChangeNotifier {
  int _hearts = 5;
  static const int maxHearts = 5;
  static const Duration regenTime = Duration(hours: 4);
  DateTime? _lastHeartLostAt;
  PracticeMode _mode = PracticeMode.normal;

  int get hearts => _hearts;
  PracticeMode get mode => _mode;

  void loseHeart() {
    if (_mode == PracticeMode.grace) return;

    _hearts = max(0, _hearts - 1);
    _lastHeartLostAt = DateTime.now();
    notifyListeners();
  }

  void enterGraceMode() {
    _mode = PracticeMode.grace;
    notifyListeners();
  }

  void exitGraceMode() {
    _mode = PracticeMode.normal;
    notifyListeners();
  }

  double get xpMultiplier => _mode == PracticeMode.grace ? 0.0 : 1.0;
  double get goldMultiplier => _mode == PracticeMode.grace ? 0.0 : 1.0;
}
```

### 11.5 Gap #4: Explicaciones de Errores [CRITICO]

**Estado Actual:** El servidor retorna `correct: true/false` pero NO `explanation`.

**Impacto:** Sin explicaciones, no hay aprendizaje real. Solo trivia.

**Solucion Backend:**
```python
# dungeon_service.py - modificar submit_encounter_answers()

def submit_answer(self, encounter_id: str, question_id: str, answer_id: str, time_spent: int):
    question = self.db.query(Question).filter(Question.id == question_id).first()
    is_correct = question.correct_answer == answer_id

    return {
        "correct": is_correct,
        "correct_answer_id": question.correct_answer,
        "explanation": question.explanation,  # <-- AGREGAR ESTO
        "video_url": question.video_url,       # <-- OPCIONAL: video explicativo
        # ... resto de campos
    }
```

**Solucion Frontend:**
```dart
// battle_provider.dart - modificar _onWrongAnswer()

void _showExplanationModal(AnswerResult result) {
  // Mostrar bottom sheet con explicacion
  showModalBottomSheet(
    context: context,
    builder: (ctx) => ExplanationModal(
      correctAnswer: result.correctAnswerId,
      explanation: result.explanation ?? 'Sin explicacion disponible',
      videoUrl: result.videoUrl,
    ),
  );
}
```

### 11.6 Gap #5: Arte Faltante [IMPORTANTE]

**Estado Actual:** Solo existen mapas para "math" y "reading". Faltan 3.

**Impacto:** Solo 40% del contenido visual esta listo.

**Solucion:** Usar los prompts de la seccion 2.3 para generar los 3 mapas restantes.

### 11.7 Gap #6: Timelines de Feedback [IMPORTANTE]

**Estado Actual:** `BattlePage` tiene animaciones pero no siguen el timeline de 600ms.

**Impacto:** El "juice" del juego se siente desconectado y menos satisfactorio.

**Solucion:** Implementar las funciones `_onCorrectAnswer()` y `_onWrongAnswer()` de la seccion 6.

### 11.8 Gap #7: Sistema de Rachas [MEDIO]

**Estado Actual:** No implementado.

**Impacto:** Sin rachas, no hay retencion diaria.

**Solucion Backend (PostgreSQL):**
```sql
CREATE TABLE user_streaks (
  user_id UUID PRIMARY KEY REFERENCES users(id),
  current_streak INT DEFAULT 0,
  longest_streak INT DEFAULT 0,
  last_activity_date DATE,
  streak_multiplier DECIMAL(3,2) DEFAULT 1.00,
  freeze_count INT DEFAULT 0,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);
```

### 11.9 Gap #8: Economia [MEDIO]

**Estado Actual:** Las batallas otorgan "Oro" pero no se puede gastar en nada.

**Impacto:** La moneda del juego no tiene valor.

**Solucion Backend (PostgreSQL):**
```sql
CREATE TABLE user_economy (
  user_id UUID PRIMARY KEY REFERENCES users(id),
  gold INT DEFAULT 100,
  total_xp INT DEFAULT 0,
  level INT DEFAULT 1,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE shop_items (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name VARCHAR(100) NOT NULL,
  description TEXT,
  type VARCHAR(50) NOT NULL, -- 'streak_freeze', 'hearts', 'avatar', 'hint'
  cost_gold INT NOT NULL,
  effect JSONB,
  is_active BOOLEAN DEFAULT TRUE
);

CREATE TABLE user_inventory (
  user_id UUID REFERENCES users(id),
  item_id UUID REFERENCES shop_items(id),
  quantity INT DEFAULT 1,
  acquired_at TIMESTAMP DEFAULT NOW(),
  PRIMARY KEY (user_id, item_id)
);
```

---

## 12. Especificaciones de Base de Datos

### 12.1 Tablas Existentes (Ya Implementadas)

```sql
-- dungeon_gates: Portales/Reinos disponibles
CREATE TABLE dungeon_gates (
  id UUID PRIMARY KEY,
  name VARCHAR(200) NOT NULL,
  description TEXT,
  gate_type VARCHAR(50) NOT NULL,  -- 'math', 'reading', 'science', 'social', 'english'
  difficulty_rank VARCHAR(10) NOT NULL,
  subject_id UUID REFERENCES subjects(id),
  recommended_level INT DEFAULT 1,
  total_rooms INT DEFAULT 8,
  time_limit_minutes INT DEFAULT 60,
  entry_cost_orbs INT DEFAULT 0,
  base_experience_reward INT DEFAULT 100,
  base_orb_reward INT DEFAULT 50,
  is_active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP DEFAULT NOW()
);

-- dungeon_runs: Sesiones activas de juego
CREATE TABLE dungeon_runs (
  id UUID PRIMARY KEY,
  gate_id UUID REFERENCES dungeon_gates(id),
  user_id UUID REFERENCES users(id),
  status VARCHAR(20) DEFAULT 'in_progress',
  current_room INT DEFAULT 1,
  start_time TIMESTAMP DEFAULT NOW(),
  completion_time TIMESTAMP,
  total_damage_dealt INT DEFAULT 0,
  total_damage_taken INT DEFAULT 0,
  questions_answered INT DEFAULT 0,
  questions_correct INT DEFAULT 0,
  experience_gained INT DEFAULT 0,
  orbs_gained INT DEFAULT 0
);

-- dungeon_encounters: Cada combate individual
CREATE TABLE dungeon_encounters (
  id UUID PRIMARY KEY,
  dungeon_run_id UUID REFERENCES dungeon_runs(id),
  room_number INT NOT NULL,
  encounter_type VARCHAR(50) NOT NULL,
  enemy_name VARCHAR(200),
  enemy_level INT,
  questions_faced JSONB DEFAULT '[]',
  answers_given JSONB DEFAULT '[]',
  encounter_won BOOLEAN DEFAULT FALSE,
  damage_dealt INT DEFAULT 0,
  damage_taken INT DEFAULT 0,
  experience_gained INT DEFAULT 0
);

-- dungeon_monsters: Configuracion de enemigos
CREATE TABLE dungeon_monsters (
  id UUID PRIMARY KEY,
  name VARCHAR(200) NOT NULL,
  monster_type VARCHAR(50) NOT NULL,
  rank VARCHAR(10) NOT NULL,
  level INT DEFAULT 1,
  health INT DEFAULT 100,
  attack INT DEFAULT 10,
  preferred_subjects JSONB DEFAULT '[]',
  question_difficulty VARCHAR(20) DEFAULT 'medium',
  questions_per_encounter INT DEFAULT 10,
  is_boss BOOLEAN DEFAULT FALSE,
  is_active BOOLEAN DEFAULT TRUE
);
```

### 12.2 Tablas Nuevas Requeridas

```sql
-- user_streaks: Sistema de rachas
CREATE TABLE user_streaks (
  user_id UUID PRIMARY KEY REFERENCES users(id),
  current_streak INT DEFAULT 0,
  longest_streak INT DEFAULT 0,
  last_activity_date DATE,
  streak_multiplier DECIMAL(3,2) DEFAULT 1.00,
  freeze_count INT DEFAULT 0,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- user_economy: Economia del jugador
CREATE TABLE user_economy (
  user_id UUID PRIMARY KEY REFERENCES users(id),
  gold INT DEFAULT 100,
  total_xp INT DEFAULT 0,
  level INT DEFAULT 1,
  rank VARCHAR(10) DEFAULT 'E',
  hearts INT DEFAULT 5,
  last_heart_regen TIMESTAMP DEFAULT NOW(),
  is_grace_mode BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- user_kingdom_progress: Progreso por reino
CREATE TABLE user_kingdom_progress (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id),
  kingdom_id UUID REFERENCES dungeon_gates(id),
  diagnostic_completed BOOLEAN DEFAULT FALSE,
  overall_mastery DECIMAL(5,2) DEFAULT 0.00,
  rank VARCHAR(10) DEFAULT 'E',
  boss_defeated BOOLEAN DEFAULT FALSE,
  total_stars INT DEFAULT 0,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(user_id, kingdom_id)
);

-- user_node_progress: Progreso por nodo
CREATE TABLE user_node_progress (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id),
  node_id VARCHAR(100) NOT NULL,  -- 'math_node_1', 'reading_node_3', etc.
  kingdom_id UUID REFERENCES dungeon_gates(id),
  mastery_percent DECIMAL(5,2) DEFAULT 0.00,
  stars_earned INT DEFAULT 0,
  times_completed INT DEFAULT 0,
  best_accuracy DECIMAL(5,2) DEFAULT 0.00,
  questions_seen JSONB DEFAULT '[]',
  is_unlocked BOOLEAN DEFAULT FALSE,
  unlocked_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(user_id, node_id)
);

-- shop_items: Items de la tienda
CREATE TABLE shop_items (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name VARCHAR(100) NOT NULL,
  description TEXT,
  type VARCHAR(50) NOT NULL,
  cost_gold INT NOT NULL,
  effect JSONB,
  is_active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP DEFAULT NOW()
);

-- user_inventory: Inventario del jugador
CREATE TABLE user_inventory (
  user_id UUID REFERENCES users(id),
  item_id UUID REFERENCES shop_items(id),
  quantity INT DEFAULT 1,
  acquired_at TIMESTAMP DEFAULT NOW(),
  PRIMARY KEY (user_id, item_id)
);

-- offline_sync_queue: Cola de acciones offline (backend)
CREATE TABLE offline_sync_queue (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id),
  action_type VARCHAR(50) NOT NULL,
  payload JSONB NOT NULL,
  client_timestamp TIMESTAMP NOT NULL,
  server_received_at TIMESTAMP DEFAULT NOW(),
  processed BOOLEAN DEFAULT FALSE,
  processed_at TIMESTAMP,
  error_message TEXT
);
```

---

## 13. Anti-Patterns a Evitar

### 13.1 Anti-Patterns de Triviador (Evitar)

| Anti-Pattern | Por Que Fallo | Nuestra Solucion |
|--------------|---------------|------------------|
| Graficos 3D confusos | Mareos, distraccion, app pesada | 2D hand-painted, dark theme |
| Requiere internet siempre | Imposible en buses/zonas rurales | Offline-first con sync queue |
| Bots disfrazados de usuarios | "No tiene gracia", se siente fake | Single-player puro, competencia en ligas con usuarios reales |
| Preguntas diferentes en duelo | "Es una estafa" | Conquest es single-player |
| No poder salir de partidas | 30 min atrapado | Guardar progreso en cualquier momento |
| Perdida de cuentas | Anos de progreso perdidos | Google + Apple + recovery codes |
| Interfaz confusa | Menus poco intuitivos | Maximo 2 taps para cualquier accion |
| Sin narrador | 80% de quejas post-update | Voz del Sistema epica |
| Preguntas con errores | Frustacion educativa | Sistema de reporte + validacion previa |
| Solo Espana | Contenido irrelevante | Colombia-first |
| Publicidad intrusiva | Interrumpe gameplay | Solo rewarded ads opcionales |
| Texto ilegible | Problemas de accesibilidad | Fuente grande, configurable |

### 13.2 Anti-Patterns de Duolingo (Evitar)

| Anti-Pattern | Por Que Fallo | Nuestra Solucion |
|--------------|---------------|------------------|
| 2h regeneracion de vidas | Muy punitivo | 4h regeneracion |
| 0 vidas = bloqueo total | Frustra el aprendizaje | Grace Mode |
| Notificaciones culposas | "Me sentire triste si no practicas" | Tono epico, motivador |
| Sin explicaciones detalladas | No hay aprendizaje real | Explicacion siempre disponible |
| Lecciones lineales fijas | No respeta nivel del usuario | Adaptativo con SM-2 |

### 13.3 Principios Inviolables

| Principio | Implementacion |
|-----------|----------------|
| **Nunca pagar para aprender mejor** | Premium = conveniencia, no ventaja educativa |
| **Nunca interrumpir gameplay con ads** | Solo rewarded ads despues de sesiones |
| **Nunca bloquear por falta de vidas** | Grace Mode siempre disponible |
| **Siempre explicar errores** | Cada respuesta incorrecta tiene explicacion |
| **Siempre funcionar offline** | Queue de sincronizacion |

---

## 14. Roadmap de Implementacion

### 14.1 Prioridad 1: Criticos (Semana 1-2)

| # | Tarea | Esfuerzo | Archivos Clave |
|---|-------|----------|----------------|
| 1.1 | Implementar `SystemVoice` con 10 frases | 2 dias | `system_voice.dart` (crear), `battle_provider.dart` |
| 1.2 | Implementar `OfflineActionQueue` con Hive | 3 dias | `offline_action_queue.dart` (crear), `pending_action.dart` |
| 1.3 | Implementar `HeartSystem` con Grace Mode | 2 dias | `heart_system.dart` (crear), `battle_provider.dart` |
| 1.4 | Agregar `explanation` a respuestas del servidor | 1 dia | `dungeon_service.py`, `battle_provider.dart` |
| 1.5 | Crear modal de explicacion en UI | 1 dia | `explanation_modal.dart` (crear), `battle_page.dart` |

### 14.2 Prioridad 2: Importantes (Semana 3-4)

| # | Tarea | Esfuerzo | Archivos Clave |
|---|-------|----------|----------------|
| 2.1 | Generar 3 mapas faltantes (Ciencias, Sociales, Ingles) | 2 dias | Assets en `assets/images/` |
| 2.2 | Implementar timelines de feedback dopaminergico | 2 dias | `battle_page.dart`, `haptic_patterns.dart` |
| 2.3 | Agregar 10 frases adicionales de voz | 1 dia | `assets/audio/voice/` |
| 2.4 | Implementar sistema de rachas (backend) | 2 dias | `streak_service.py`, tablas SQL |
| 2.5 | Implementar UI de rachas | 1 dia | `home_page.dart`, `streak_widget.dart` |

### 14.3 Prioridad 3: Medio (Semana 5-6)

| # | Tarea | Esfuerzo | Archivos Clave |
|---|-------|----------|----------------|
| 3.1 | Implementar economia (tablas + servicio) | 2 dias | `economy_service.py`, tablas SQL |
| 3.2 | Crear tienda basica | 2 dias | `shop_page.dart`, `shop_service.py` |
| 3.3 | Sistema de niveles y XP | 1 dia | `level_service.py`, `user_economy` tabla |
| 3.4 | Sistema de rangos | 1 dia | `rank_service.py` |
| 3.5 | Progreso por nodo persistente | 2 dias | `user_node_progress` tabla, `node_progress_service.py` |

### 14.4 Plan Semanal Inmediato (Semana 1)

**Lunes-Martes:**
- Generar 10 voiceovers con ElevenLabs
- Crear `SystemVoice.dart` e integrarlo

**Miercoles:**
- Implementar Grace Mode
- Modificar `DungeonService` para retornar `explanation`

**Jueves-Viernes:**
- Implementar `OfflineActionQueue` con Hive
- Crear modal de explicacion

**Sabado-Domingo:**
- Testing de integracion
- Generar 1 mapa adicional (Ciencias)

---

## 15. Assets Requeridos

### 15.1 Estructura de Carpetas de Audio

```
assets/audio/
├── music/
│   ├── portal_theme_loop.mp3         # 90s, epico ambiental
│   ├── kingdom_selection.mp3         # 60s, misterioso
│   ├── battle_normal.mp3             # 120s, focus concentrado
│   ├── battle_boss.mp3               # 90s, intenso epico
│   ├── victory_fanfare.mp3           # 3s
│   └── defeat_somber.mp3             # 2s
│
├── sfx/
│   ├── correct_ding.wav              # 0.3s
│   ├── wrong_buzz.wav                # 0.4s
│   ├── enemy_hit.wav                 # 0.5s
│   ├── combo_3.wav                   # 0.6s
│   ├── combo_5.wav                   # 0.7s
│   ├── combo_10.wav                  # 1.0s
│   ├── heart_break.wav               # 0.5s
│   ├── xp_gain.wav                   # 0.4s
│   ├── level_up.wav                  # 1.5s
│   ├── star_ding.wav                 # 0.3s
│   ├── button_tap.wav                # 0.1s
│   └── button_confirm.wav            # 0.2s
│
└── voice/
    ├── sistema_te_encontro.wav
    ├── rango_asignado.wav
    ├── correcto.wav
    ├── respuesta_incorrecta.wav
    ├── analiza_error.wav
    ├── combo_activado.wav
    ├── imparable.wav
    ├── victoria.wav
    ├── mision_completada.wav
    ├── nivel_alcanzado.wav
    ├── rango_ascendido.wav
    ├── bienvenido_cazador.wav
    ├── entrando_dungeon.wav
    ├── mana_agotado.wav
    └── boss_despertado.wav
```

### 15.2 Assets Visuales Requeridos

```
assets/images/
├── maps/
│   ├── map_math.png                  # Existente
│   ├── map_reading.png               # Existente
│   ├── map_science.png               # FALTA
│   ├── map_social.png                # FALTA
│   └── map_english.png               # FALTA
│
├── bosses/
│   ├── boss_math.png                 # Dragon del Calculo
│   ├── boss_reading.png              # Esfinge de las Letras
│   ├── boss_science.png              # Hidra del Laboratorio (FALTA)
│   ├── boss_social.png               # Titan de la Historia (FALTA)
│   └── boss_english.png              # Fenix Poliglota (FALTA)
│
├── monsters/
│   ├── math/                         # Monstruos de matematicas
│   ├── reading/                      # Monstruos de lectura
│   ├── science/                      # Monstruos de ciencias (FALTA)
│   ├── social/                       # Monstruos de sociales (FALTA)
│   └── english/                      # Monstruos de ingles (FALTA)
│
├── ui/
│   ├── heart_full.png
│   ├── heart_empty.png
│   ├── heart_break_anim/             # Sprites de animacion
│   ├── combo_badge.png
│   ├── star_full.png
│   ├── star_empty.png
│   └── xp_icon.png
│
└── avatars/
    └── hero_avatar.png               # Avatar del jugador
```

### 15.3 Costos Estimados

| Categoria | Items | Fuente Recomendada | Costo Estimado |
|-----------|-------|-------------------|----------------|
| Voiceover inicial (10 frases) | 10 WAV | ElevenLabs | $20-30 |
| Voiceover completo (32 frases) | 32 WAV | ElevenLabs | $50-80 |
| Musica (7 tracks) | 7 MP3 | Epidemic Sound | $15/mes |
| SFX (15 efectos) | 15 WAV | Freesound + Edicion | $0-20 |
| Mapas (3 faltantes) | 3 PNG 4K | Midjourney | $30/mes |
| Monstruos (15 faltantes) | 15 PNG | Midjourney | Incluido arriba |

**Total estimado MVP:** $100-150 USD

---

## Apendice: Checklist de Implementacion

### Fase 1: Criticos
- [ ] `SystemVoice` creado e integrado
- [ ] 10 frases de voz generadas
- [ ] `OfflineActionQueue` implementado
- [ ] `HeartSystem` con Grace Mode
- [ ] Explicaciones en respuestas del servidor
- [ ] Modal de explicacion en UI

### Fase 2: Importantes
- [ ] 3 mapas faltantes generados
- [ ] Timelines de feedback implementados
- [ ] `HapticPatterns` implementado
- [ ] Sistema de rachas backend
- [ ] UI de rachas

### Fase 3: Medio
- [ ] Tablas de economia creadas
- [ ] Servicio de economia
- [ ] Tienda basica
- [ ] Sistema de niveles
- [ ] Sistema de rangos
- [ ] Progreso por nodo persistente

---

> **Documento Maestro del Modo Conquista - ICFES Leveling**
> Version 3.0 | 29 de Diciembre, 2025
>
> *"El Sistema te observa, Cazador. Tu entrenamiento comienza ahora."*
