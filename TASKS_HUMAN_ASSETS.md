# TAREAS PARA DESARROLLADOR HUMANO: Assets Visuales y Audio

**Proyecto:** ICFES Leveling - Modo Conquista
**Responsable:** Desarrollador Humano / Artista
**Herramientas:** ElevenLabs, Midjourney, DALL-E, Freesound, Epidemic Sound
**Fecha:** 29 de Diciembre, 2025

---

## Resumen de Entregables

| Categoria | Cantidad | Prioridad | Costo Estimado |
|-----------|----------|-----------|----------------|
| Voiceovers (Voz del Sistema) | 32 frases | CRITICA | $50-80 USD |
| Mapas de Reinos | 3 nuevos | ALTA | $30/mes Midjourney |
| Bosses | 3 nuevos | ALTA | Incluido |
| Monstruos por Reino | ~15 nuevos | MEDIA | Incluido |
| Musica | 6 tracks | MEDIA | $15/mes Epidemic |
| SFX | 15 efectos | ALTA | $0-20 USD |
| UI Icons | ~10 iconos | BAJA | Incluido |

**Total Estimado:** $100-150 USD

---

## FASE 1: CRITICA (Esta Semana)

### TAREA 1.1: Generar Voiceovers con ElevenLabs

**Prioridad:** CRITICA
**Herramienta:** ElevenLabs (https://elevenlabs.io)
**Costo:** ~$22/mes plan Creator

#### Configuracion de Voz

| Parametro | Valor Recomendado |
|-----------|-------------------|
| **Voz** | "Adam" o "Antoni" (masculina profunda) |
| **Idioma** | Espanol (Latinoamerica) |
| **Estabilidad** | 0.50 (balance dramatico) |
| **Claridad** | 0.75 (nitida pero no robotica) |
| **Estilo** | Authoritative, Epic, Neutral |

#### Frases a Generar (Prioridad 1 - 10 frases iniciales)

| # | ID | Frase Exacta | Archivo de Salida |
|---|----|--------------|--------------------|
| 1 | `combat_correct` | "Correcto." | `correcto.wav` |
| 2 | `combat_wrong` | "Respuesta incorrecta." | `respuesta_incorrecta.wav` |
| 3 | `combat_analyze` | "Analiza el error." | `analiza_error.wav` |
| 4 | `combat_combo` | "Combo activado." | `combo_activado.wav` |
| 5 | `combat_unstoppable` | "Imparable." | `imparable.wav` |
| 6 | `progress_victory` | "Victoria." | `victoria.wav` |
| 7 | `progress_mission_complete` | "Mision completada." | `mision_completada.wav` |
| 8 | `daily_welcome` | "Bienvenido de nuevo, Cazador." | `bienvenido_cazador.wav` |
| 9 | `hearts_depleted` | "Mana agotado." | `mana_agotado.wav` |
| 10 | `daily_entering` | "Entrando al Dungeon." | `entrando_dungeon.wav` |

#### Frases a Generar (Prioridad 2 - 12 frases adicionales)

| # | ID | Frase Exacta | Archivo de Salida |
|---|----|--------------|--------------------|
| 11 | `onboard_found` | "El Sistema te ha encontrado." | `sistema_te_encontro.wav` |
| 12 | `onboard_eval_start` | "Evaluacion de poder iniciada." | `evaluacion_iniciada.wav` |
| 13 | `onboard_calibrating` | "Calibrando rango de Cazador." | `calibrando_rango.wav` |
| 14 | `onboard_rank_assigned` | "Rango asignado." | `rango_asignado.wav` |
| 15 | `onboard_begin` | "Tu entrenamiento comienza ahora." | `entrenamiento_comienza.wav` |
| 16 | `progress_level_up` | "Nivel alcanzado." | `nivel_alcanzado.wav` |
| 17 | `progress_rank_up` | "Rango ascendido." | `rango_ascendido.wav` |
| 18 | `daily_new_day` | "Nuevo dia. Nueva oportunidad de ascender." | `nuevo_dia.wav` |
| 19 | `daily_select` | "Selecciona tu campo de batalla." | `selecciona_campo.wav` |
| 20 | `daily_mission_accept` | "Mision aceptada." | `mision_aceptada.wav` |
| 21 | `special_boss_awakened` | "El Boss ha despertado." | `boss_despertado.wav` |
| 22 | `special_power_grows` | "Tu poder crece." | `poder_crece.wav` |

#### Frases a Generar (Prioridad 3 - 10 frases restantes)

| # | ID | Frase Exacta | Archivo de Salida |
|---|----|--------------|--------------------|
| 23 | `combat_power_up` | "Poder incrementado." | `poder_incrementado.wav` |
| 24 | `combat_combo_5` | "Excelente." | `excelente.wav` |
| 25 | `hearts_reduced` | "Mana reducido." | `mana_reducido.wav` |
| 26 | `hearts_restored` | "Mana restaurado." | `mana_restaurado.wav` |
| 27 | `streak_maintained` | "Racha mantenida." | `racha_mantenida.wav` |
| 28 | `streak_impressive` | "Tu dedicacion es notable." | `dedicacion_notable.wav` |
| 29 | `streak_warning` | "Advertencia. Tu racha esta en peligro." | `racha_peligro.wav` |
| 30 | `streak_lost` | "Racha perdida. Pero tu poder permanece." | `racha_perdida.wav` |
| 31 | `progress_achievement` | "Logro desbloqueado." | `logro_desbloqueado.wav` |
| 32 | `special_watching` | "El Sistema te observa." | `sistema_observa.wav` |

#### Ubicacion de Archivos

```
apps/mobile/assets/audio/voice/
├── correcto.wav
├── respuesta_incorrecta.wav
├── analiza_error.wav
├── combo_activado.wav
├── imparable.wav
├── victoria.wav
├── mision_completada.wav
├── bienvenido_cazador.wav
├── mana_agotado.wav
├── entrando_dungeon.wav
├── sistema_te_encontro.wav
├── evaluacion_iniciada.wav
├── calibrando_rango.wav
├── rango_asignado.wav
├── entrenamiento_comienza.wav
├── nivel_alcanzado.wav
├── rango_ascendido.wav
├── nuevo_dia.wav
├── selecciona_campo.wav
├── mision_aceptada.wav
├── boss_despertado.wav
├── poder_crece.wav
├── poder_incrementado.wav
├── excelente.wav
├── mana_reducido.wav
├── mana_restaurado.wav
├── racha_mantenida.wav
├── dedicacion_notable.wav
├── racha_peligro.wav
├── racha_perdida.wav
├── logro_desbloqueado.wav
└── sistema_observa.wav
```

#### Especificaciones Tecnicas de Audio

| Parametro | Valor |
|-----------|-------|
| Formato | WAV (sin compresion) |
| Sample Rate | 44100 Hz |
| Bit Depth | 16-bit |
| Canales | Mono |
| Normalizacion | -3dB peak |
| Silencio inicial | 0ms |
| Silencio final | 100ms max |

---

### TAREA 1.2: Descargar/Crear SFX

**Prioridad:** ALTA
**Herramientas:** Freesound.org, Zapsplat.com, Audacity

#### SFX Requeridos

| # | Nombre | Descripcion | Duracion | Fuente Sugerida |
|---|--------|-------------|----------|-----------------|
| 1 | `correct_ding.wav` | Ding satisfactorio, tono alto, campanita | 0.3s | Freesound |
| 2 | `wrong_buzz.wav` | Buzz suave, NO punitivo, error gentil | 0.4s | Freesound |
| 3 | `enemy_hit.wav` | Impacto magico, slash + eco | 0.5s | Freesound |
| 4 | `player_hit.wav` | Impacto recibido, golpe sordo | 0.4s | Freesound |
| 5 | `combo_3.wav` | Energia media, whoosh ascendente | 0.6s | Freesound |
| 6 | `combo_5.wav` | Energia alta, flames + power up | 0.7s | Freesound |
| 7 | `combo_10.wav` | Explosion epica, maximo poder | 1.0s | Freesound |
| 8 | `heart_break.wav` | Cristal rompiendose, suave y triste | 0.5s | Freesound |
| 9 | `heart_restore.wav` | Restauracion magica, campanitas | 0.6s | Freesound |
| 10 | `xp_gain.wav` | Power up corto, monedas + brillo | 0.4s | Freesound |
| 11 | `level_up.wav` | Fanfarria corta, triunfante | 1.5s | Freesound |
| 12 | `star_ding.wav` | Estrella individual, tintinea | 0.3s | Freesound |
| 13 | `victory_fanfare.wav` | Fanfarria completa, orquestal | 3.0s | Epidemic Sound |
| 14 | `defeat_somber.wav` | Tono melancolico, no deprimente | 2.0s | Epidemic Sound |
| 15 | `button_tap.wav` | Click suave, UI feedback | 0.1s | Freesound |

#### Ubicacion de Archivos

```
apps/mobile/assets/audio/sfx/
├── correct_ding.wav
├── wrong_buzz.wav
├── enemy_hit.wav
├── player_hit.wav
├── combo_3.wav
├── combo_5.wav
├── combo_10.wav
├── heart_break.wav
├── heart_restore.wav
├── xp_gain.wav
├── level_up.wav
├── star_ding.wav
├── victory_fanfare.wav
├── defeat_somber.wav
└── button_tap.wav
```

---

## FASE 2: ALTA (Proxima Semana)

### TAREA 2.1: Generar Mapas de Reinos Faltantes

**Prioridad:** ALTA
**Herramienta:** Midjourney v6 ($30/mes plan Standard)
**Parametros:** `--ar 9:16 --v 6 --q 2`

#### Mapa 1: La Forja Atomica (Ciencias)

**Prompt:**
```
Fantasy RPG world map, isometric top-down view, dark mystical atmosphere.
Theme: Volcanic alchemical realm where science becomes magic.
Central element: An active volcano with a grand laboratory built into its crater,
with different biomes (jungle, arctic, desert) in each section, glowing chemical vials.
8 distinct node locations connected by glowing green and purple energy streams.
Color palette: Volcanic oranges and reds, bioluminescent greens and blues,
toxic purples, crystalline whites.
Style: Hand-painted digital art, dramatic biome contrast, 4K.
NO text, NO UI elements --ar 9:16 --v 6 --q 2
```

**Archivo de salida:** `apps/mobile/assets/images/maps/map_science.png`
**Resolucion:** 1080x1920 px minimo

---

#### Mapa 2: Las Ruinas del Imperio (Sociales)

**Prompt:**
```
Fantasy RPG world map, isometric top-down view, dark mystical atmosphere.
Theme: Fallen civilization with echoes of world history and cultures merged.
Central element: A grand colosseum in partial ruins at the center,
with a world map mosaic visible on its floor, Egyptian pyramids and Mayan temples around.
8 distinct node locations connected by glowing terracotta and gold stone pathways.
Color palette: Golden hour lighting, terracotta and sandstone,
bronze and marble accents, jungle greens encroaching on ancient stone.
Style: Hand-painted digital art, archaeological discovery feel, 4K.
NO text, NO UI elements --ar 9:16 --v 6 --q 2
```

**Archivo de salida:** `apps/mobile/assets/images/maps/map_social.png`
**Resolucion:** 1080x1920 px minimo

---

#### Mapa 3: El Archipielago de las Lenguas (Ingles)

**Prompt:**
```
Fantasy RPG world map, isometric top-down view, dark mystical atmosphere.
Theme: Floating island archipelago where language is power.
Central element: A grand lighthouse tower made of stacked oversized letters
on the main island, smaller islands with different linguistic themes, sailing ships.
8 distinct island nodes connected by glowing teal bridges made of words.
Color palette: Teal ocean waters, silver moonlight reflections,
warm island sunset accents, paper-white sails, ink-blue ocean depths.
Style: Hand-painted digital art, nautical fantasy academy feel, 4K.
NO text, NO UI elements --ar 9:16 --v 6 --q 2
```

**Archivo de salida:** `apps/mobile/assets/images/maps/map_english.png`
**Resolucion:** 1080x1920 px minimo

---

### TAREA 2.2: Generar Bosses Faltantes

**Prioridad:** ALTA
**Herramienta:** Midjourney v6
**Parametros:** `--ar 1:1 --v 6 --q 2`

#### Boss 1: Hidra del Laboratorio (Ciencias)

**Prompt:**
```
Epic fantasy boss creature, a three-headed hydra made of chemical elements,
each head representing biology (green, plant-like), chemistry (purple, crystalline),
and physics (blue, electric). Glowing veins of bioluminescent liquid,
laboratory equipment fused into its body, dark mystical atmosphere.
Solo Leveling art style, menacing but not horror, 4K detailed illustration.
Dark background, dramatic lighting --ar 1:1 --v 6 --q 2
```

**Archivo de salida:** `apps/mobile/assets/images/bosses/boss_science.png`
**Resolucion:** 512x512 px minimo

---

#### Boss 2: Titan de la Historia (Sociales)

**Prompt:**
```
Epic fantasy boss creature, a colossal titan made of ancient civilizations,
body composed of Roman columns, Egyptian hieroglyphics, Mayan calendar stones,
and Colombian pre-Columbian gold. Wearing a crown of historical monuments.
Holding a shield with a world map. Dark mystical atmosphere.
Solo Leveling art style, ancient and powerful, 4K detailed illustration.
Dark background, golden hour lighting --ar 1:1 --v 6 --q 2
```

**Archivo de salida:** `apps/mobile/assets/images/bosses/boss_social.png`
**Resolucion:** 512x512 px minimo

---

#### Boss 3: Fenix Poliglota (Ingles)

**Prompt:**
```
Epic fantasy boss creature, a majestic phoenix made entirely of letters and words,
feathers are pages from books in multiple languages, trail of glowing alphabet.
Wings spread wide with dictionary definitions flowing like fire.
Teal and silver color scheme with golden accents. Dark mystical atmosphere.
Solo Leveling art style, wise and powerful, 4K detailed illustration.
Dark oceanic background with moonlight --ar 1:1 --v 6 --q 2
```

**Archivo de salida:** `apps/mobile/assets/images/bosses/boss_english.png`
**Resolucion:** 512x512 px minimo

---

### TAREA 2.3: Obtener Musica de Fondo

**Prioridad:** MEDIA
**Herramienta:** Epidemic Sound ($15/mes) o Artlist

#### Tracks Requeridos

| # | Contexto | Estilo | BPM | Duracion | Archivo |
|---|----------|--------|-----|----------|---------|
| 1 | Portal de Reinos | Epico ambiental, misterioso | 60-80 | 90s loop | `portal_theme.mp3` |
| 2 | Mapa de Reino | Explorador, expectante | 70-90 | 60s loop | `kingdom_map.mp3` |
| 3 | Batalla Normal | Focus, concentracion, pulso | 90-110 | 120s loop | `battle_normal.mp3` |
| 4 | Batalla Boss | Epico intenso, orquestal | 120-140 | 90s loop | `battle_boss.mp3` |
| 5 | Victoria | Fanfarria triunfante | 100-120 | 30s no-loop | `victory.mp3` |
| 6 | Derrota | Melancolico esperanzador | 60-80 | 30s no-loop | `defeat.mp3` |

**Palabras clave para busqueda:**
- "Epic orchestral ambient"
- "Fantasy game exploration"
- "Focus study music minimal"
- "Boss battle orchestral"
- "Victory fanfare short"
- "Melancholic hope piano"

#### Ubicacion de Archivos

```
apps/mobile/assets/audio/music/
├── portal_theme.mp3
├── kingdom_map.mp3
├── battle_normal.mp3
├── battle_boss.mp3
├── victory.mp3
└── defeat.mp3
```

---

## FASE 3: MEDIA (Semana 3)

### TAREA 3.1: Generar Monstruos por Reino

**Prioridad:** MEDIA
**Herramienta:** Midjourney v6
**Cantidad:** 7 monstruos por reino faltante = 21 total

#### Ciencias - La Forja Atomica (7 monstruos)

| # | Nombre | Prompt Keywords | Archivo |
|---|--------|-----------------|---------|
| 1 | Slime Experimental | "Cute blob slime, green glowing, lab beaker texture" | `science_slime.png` |
| 2 | Bacteria Gigante | "Giant bacteria monster, microscope aesthetic, purple" | `science_bacteria.png` |
| 3 | Golem Alquimico | "Stone golem with chemical vials embedded, glowing" | `science_golem.png` |
| 4 | Automata de Engranajes | "Steampunk robot, gears and cogs, physics themed" | `science_automata.png` |
| 5 | Bestia del Pantano | "Swamp creature, ecosystem themed, moss and vines" | `science_swamp.png` |
| 6 | Elemental Molecular | "Floating molecule creature, atomic structure" | `science_molecular.png` |
| 7 | Espectro Electrico | "Electric ghost, lightning themed, blue energy" | `science_electric.png` |

#### Sociales - Las Ruinas del Imperio (7 monstruos)

| # | Nombre | Prompt Keywords | Archivo |
|---|--------|-----------------|---------|
| 1 | Esqueleto Soldado | "Skeleton warrior, ancient armor, torch" | `social_skeleton.png` |
| 2 | Conquistador Fantasma | "Ghost conquistador, Spanish armor, ethereal" | `social_conquistador.png` |
| 3 | Coloso de Piedra | "Stone colossus, ancient statue come alive" | `social_colossus.png` |
| 4 | Guardia de la Ley | "Armored guardian, scales of justice" | `social_guardian.png` |
| 5 | Faraon Resucitado | "Mummy pharaoh, Egyptian gold, glowing eyes" | `social_pharaoh.png` |
| 6 | Mercader Espectral | "Ghost merchant, coins and treasures" | `social_merchant.png` |
| 7 | General de las Eras | "Ancient general, mixed historical armors" | `social_general.png` |

#### Ingles - El Archipielago (7 monstruos)

| # | Nombre | Prompt Keywords | Archivo |
|---|--------|-----------------|---------|
| 1 | Loro Parlante | "Magical parrot, letters floating, colorful" | `english_parrot.png` |
| 2 | Gramatico Rigido | "Strict teacher creature, monocle, book" | `english_grammar.png` |
| 3 | Diccionario Viviente | "Living dictionary book, arms and legs" | `english_dictionary.png` |
| 4 | Lector de Mapas | "Navigator creature, compass, sea maps" | `english_navigator.png` |
| 5 | Reloj Parlante | "Talking clock creature, time themed" | `english_clock.png` |
| 6 | Camaleon Linguistico | "Chameleon with words on skin, colorful" | `english_chameleon.png` |
| 7 | Embajador Poliglota | "Elegant diplomat creature, multiple flags" | `english_ambassador.png` |

#### Ubicacion de Archivos

```
apps/mobile/assets/images/monsters/
├── science/
│   ├── science_slime.png
│   ├── science_bacteria.png
│   ├── science_golem.png
│   ├── science_automata.png
│   ├── science_swamp.png
│   ├── science_molecular.png
│   └── science_electric.png
├── social/
│   ├── social_skeleton.png
│   ├── social_conquistador.png
│   ├── social_colossus.png
│   ├── social_guardian.png
│   ├── social_pharaoh.png
│   ├── social_merchant.png
│   └── social_general.png
└── english/
    ├── english_parrot.png
    ├── english_grammar.png
    ├── english_dictionary.png
    ├── english_navigator.png
    ├── english_clock.png
    ├── english_chameleon.png
    └── english_ambassador.png
```

---

### TAREA 3.2: Crear UI Icons

**Prioridad:** BAJA
**Herramienta:** Midjourney o Figma

| # | Icono | Descripcion | Archivo |
|---|-------|-------------|---------|
| 1 | Corazon lleno | Cristal de corazon brillante | `heart_full.png` |
| 2 | Corazon vacio | Cristal de corazon apagado | `heart_empty.png` |
| 3 | Estrella llena | Estrella dorada brillante | `star_full.png` |
| 4 | Estrella vacia | Estrella gris apagada | `star_empty.png` |
| 5 | Moneda de oro | Moneda con simbolo de poder | `gold_coin.png` |
| 6 | XP orbe | Orbe azul de experiencia | `xp_orb.png` |
| 7 | Combo badge | Insignia de fuego para combos | `combo_badge.png` |
| 8 | Escudo | Escudo para defensa | `shield_icon.png` |
| 9 | Espada | Espada para ataque | `sword_icon.png` |
| 10 | Racha | Llama de racha | `streak_flame.png` |

---

## CHECKLIST FINAL

### Fase 1 (Esta Semana)
- [ ] Crear cuenta ElevenLabs
- [ ] Generar 10 voiceovers prioritarios
- [ ] Descargar 15 SFX de Freesound
- [ ] Editar y normalizar todos los audios
- [ ] Colocar en carpetas correctas

### Fase 2 (Proxima Semana)
- [ ] Crear cuenta Midjourney
- [ ] Generar 3 mapas de reinos
- [ ] Generar 3 bosses
- [ ] Suscribirse a Epidemic Sound
- [ ] Descargar 6 tracks de musica
- [ ] Generar 12 voiceovers adicionales

### Fase 3 (Semana 3)
- [ ] Generar 21 monstruos
- [ ] Crear 10 UI icons
- [ ] Generar 10 voiceovers restantes
- [ ] Revision final de todos los assets
- [ ] Optimizar tamanos de archivo

---

## NOTAS IMPORTANTES

1. **Consistencia de estilo:** Todos los assets visuales deben seguir el estilo "Solo Leveling" - oscuro, epico, con acentos de color neon.

2. **Formatos de archivo:**
   - Imagenes: PNG con transparencia donde aplique
   - Audio: WAV para voiceovers y SFX, MP3 para musica

3. **Resolucion de imagenes:**
   - Mapas: 1080x1920 px (9:16)
   - Bosses/Monstruos: 512x512 px minimo
   - UI Icons: 128x128 px

4. **Licencias:** Asegurarse de que todos los assets tengan licencia comercial.

5. **Backup:** Guardar archivos originales en alta resolucion antes de optimizar.

---

> **Documento de Tareas para Desarrollador Humano**
> Version 1.0 | 29 de Diciembre, 2025
