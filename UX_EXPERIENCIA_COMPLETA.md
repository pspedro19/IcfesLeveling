# EXPERIENCIA DE USUARIO COMPLETA — ICFES Leveling

> Documento exhaustivo de cada pantalla, cada interaccion, cada animacion.
> Describe lo que el usuario VE y SIENTE en cada momento.

---

## ARQUITECTURA VISUAL GLOBAL

- **Fondo base**: `#0A0A0A` (negro casi puro) en auth/onboarding, `#0F172A` (slate-900) en app principal
- **Cards**: `#1E293B` (slate-800), bordes redondeados 16px, elevacion 2-4
- **Tipografia**: Inter (Google Fonts). Titulos: blanco, weight 900, letterSpacing 2-4. Cuerpo: gris claro.
- **Idioma**: Espanol (Colombia). Todo en MAYUSCULAS con letterSpacing en labels.
- **Tema**: Dark only. Estetica RPG/anime oscuro estilo "Solo Leveling"
- **Animaciones**: `flutter_animate` — fadeIn, slideX, slideY, scale, shimmer encadenados

### Paleta de Colores Semantica

| Token | Hex | Uso |
|-------|-----|-----|
| `primaryPurple` | `#6366F1` | Acciones principales, bordes, ligas |
| `secondaryGold` | `#FFD700` | Recompensas, moneda, XP multiplicadores |
| `accentCyan` | `#22D3EE` | Barras XP, sync online |
| `dangerRed` | `#EF4444` | Corazones, errores, badge "NUEVO" |
| `successGreen` | `#22C55E` | Respuestas correctas, completado |
| `warningOrange` | `#F97316` | Racha, alertas de riesgo |

---

# FASE 1: PRIMER CONTACTO

## 1.1 Splash Screen (`/`)

**Duracion**: 2 segundos automaticos, sin interaccion del usuario.

**Lo que ve**: Fondo negro puro. En el centro, todo aparece junto con un fade-in + scale (de 0.8 a 1.0):
- Circulo de 120px con gradiente azul→purpura, sombra azul brillante (blur 30). Dentro: icono de escuela blanco (60px)
- **"ICFES LEVELING"** en blanco, 28px, ultra-bold, letterSpacing 4
- **"Despierta, Cazador."** en blanco semi-transparente, 16px, ligero
- Spinner circular azul claro (24px) girando abajo

**Logica invisible**: Durante esos 2 segundos, la app verifica JWT guardado contra el backend (timeout 3s). Decide:
- Primera vez → va a Onboarding
- Ya vio onboarding pero no loggeado → Login
- Loggeado sin diagnostico → Diagnostico rapido
- Loggeado con diagnostico → Home

---

## 1.2 Onboarding - Propuesta de Valor (`/onboarding`)

**3 slides deslizables** (PageView) con boton "SALTAR" arriba a la derecha en gris.

### Slide 1: "SUBE TU RANGO ICFES"
**Animacion central (280px)**: 3 circulos concentricos azules pulsando (escalas 1→1.1 en loops de 1s, 1.5s, 2s). En el centro, un circulo de 120px con borde azul y la letra **"E"** en blanco gigante (60px, italica, bold). 5 estrellitas azules flotan hacia arriba y desaparecen en loop.

**Texto**: *"Entrena como un cazador y escala desde el Rango-E hasta convertirte en un Maestro Rango-S."*

### Slide 2: "COMPITE EN LIGAS SEMANALES"
**Animacion central**: Simulacion de leaderboard con 4 filas. La fila 2 (tu) esta resaltada en ambar. Cada fila muestra ranking (#1-#4), avatar circular, barra de nombre, y XP (400, 300, 200, 100). Las filas entran deslizandose desde la derecha con 150ms de retraso escalonado.

**Texto**: *"Demuestra quien es el mejor en grupos de 30 cazadores. Sube de liga cada semana!"*

### Slide 3: "DOMINA CADA TEMA"
**Animacion central**: Grafico de radar/pentagono con 4 anillos concentricos purpura, 5 ejes, y un poligono purpura relleno representando maestria. Shimmer perpetuo cada 3s.

**Texto**: *"El Sistema rastrea tu progreso en tiempo real. Identifica tus debilidades y conquistalas."*

### Navegacion
- 3 puntos indicadores: activo = 24px azul expandido, inactivos = 8px gris
- Paginas 1-2: boton **"SIGUIENTE"** azul
- Pagina 3: boton **"COMENZAR"** azul con shimmer perpetuo blanco
- Ambos llevan al Login

---

## 1.3 Onboarding Extendido (5 pasos con barra de progreso)

### Paso 2/5: Seleccion de Meta (`/onboarding/goal`)

Barra de progreso de 5 segmentos (2 activos azul, 3 gris).

**"CUAL ES TU OBJETIVO?"** — 3 tarjetas seleccionables:

| Icono | Opcion | Efecto |
|-------|--------|--------|
| trending_up | **"Mejorar mi puntaje ICFES"** | Seleccion directa |
| school | **"Aprobar un examen especifico"** | Muestra selector de fecha del examen |
| fitness_center | **"Solo practicar y aprender"** | Seleccion directa |

Tarjeta seleccionada: fondo azul 15%, borde azul 2px, sombra azul, checkmark azul. No seleccionada: gris oscuro, borde gris.

### Paso 3/5: Nivel Actual (`/onboarding/level`)

**"CUAL ES TU NIVEL ACTUAL?"** — 3 opciones con gradientes propios:

- **BASICO** (verde): *"Estoy empezando o necesito repasar conceptos fundamentales"*
- **INTERMEDIO** (naranja): *"Tengo conocimientos pero quiero mejorar en areas especificas"*
- **AVANZADO** (purpura): *"Domino la mayoria de temas, busco perfeccionar detalles"*

Cada tarjeta seleccionada tiene gradiente del color correspondiente con sombra brillante.

### Paso 4/5: Materias Debiles (`/onboarding/subjects`)

**"EN QUE MATERIAS QUIERES MEJORAR?"** — Multi-select (1 a 3). Badge de conteo: "0/3" rojo → "2/3" verde.

5 chips con Wrap layout:

| Materia | Icono | Color |
|---------|-------|-------|
| Matematicas | calculate | `#4CAF50` verde |
| Lectura Critica | menu_book | `#2196F3` azul |
| Ciencias Naturales | science | `#9C27B0` purpura |
| Sociales y Ciudadanas | public | `#FF9800` naranja |
| Ingles | language | `#E91E63` rosa |

Chip seleccionado: gradiente del color, borde 2px, sombra, checkmark. Limite: maximo 3.

Nota informativa azul: *"Te daremos mas practica en estas materias para que mejores rapidamente."*

### Paso 5/5: Tiempo de Estudio (`/onboarding/study-time`)

**"CUANTO TIEMPO PUEDES ESTUDIAR AL DIA?"** — 3 opciones:

| Icono | Tiempo | Badge XP | Descripcion |
|-------|--------|----------|-------------|
| timer | **10 MINUTOS** | +50 XP/dia (verde) | *"Perfecto para dias ocupados"* |
| hourglass_bottom | **20 MINUTOS** | +100 XP/dia (azul) | *"Balance ideal entre estudio y vida"* |
| rocket_launch | **30+ MINUTOS** | +200 XP/dia (purpura) | *"Progreso acelerado para cazadores dedicados"* |

Caja naranja de **"BONUS DE RACHA"**: icono fuego + *"Estudia cada dia para mantener tu racha y ganar XP extra!"*

Boton final: **"COMENZAR AVENTURA"** en verde → envia preferencias al backend → va al Diagnostico.

---

# FASE 2: AUTENTICACION

## 2.1 Login (`/login`)

**Fondo**: Negro con circulo azul 5% opacidad pulsando (escala 1→1.2 en 3s loop) arriba a la derecha.

**Contenido** (todo con animaciones escalonadas fadeIn + slide):

1. Icono de huella digital (64px) en circulo con borde azul — escala elastica al aparecer
2. **"EL SISTEMA TE BUSCA"** — blanco, 24px, ultra-bold
3. *"Inicia sesion para registrar tu progreso y reclamar tus recompensas de cazador."*

### Vista Social (por defecto)
- **"CONTINUAR CON GOOGLE"** — boton blanco con icono G
- **"CONTINUAR CON APPLE"** — boton blanco con icono Apple
- Divisor con **"O"**
- **"CONTINUAR CON EMAIL"** — boton azul → expande el formulario de email

### Vista Email (al tocar "Continuar con Email")
- Boton "Volver" arriba
- Campo Email (fondo gris oscuro, borde gris→azul al focus→rojo en error)
- Campo Contrasena (con toggle de visibilidad ojo/ojo tachado)
- Boton **"INICIAR SESION"** azul
- Link **"No tienes cuenta? Registrate"** → push a /register

### Modo Desarrollador
- Boton verde: **"MODO DESARROLLADOR"** con icono play
- *"Explora la app sin conexion"*
- Crea usuario offline: "Cazador Demo (Offline)", nivel 5, 1250 XP, rango E, 5 corazones, racha 3 dias

### Overlay de Carga
Fondo negro 70% + spinner azul + **"Conectando con el Sistema..."**

### Terminos
*"Al continuar, aceptas nuestros Terminos de Servicio y Politica de Privacidad."* (links azules subrayados)

---

## 2.2 Registro (`/register`)

AppBar transparente con flecha blanca de retorno.

1. **"UNETE A LA CACERIA"** — 28px, ultra-bold
2. *"Crea tu cuenta de cazador para comenzar."*
3. Campo **"Nombre de Cazador"**
4. Campo **"Correo Electronico"**
5. Campo **"Contrasena"** (siempre oculta, sin toggle)
6. Boton **"DESPERTAR"** azul con escala al aparecer

Al registrar exitosamente → directo al diagnostico rapido.

---

# FASE 3: DIAGNOSTICO INICIAL

## 3.1 Intro del Diagnostico (`/diagnostic`)

Centro de pantalla, todo centrado verticalmente:

1. Circulo con gradiente azul→purpura + icono rayo (50px) — escala elastica + shimmer perpetuo
2. **"EVALUACION DE PODER INICIAL"** — 24px, ultra-bold, letterSpacing 2
3. *"El Sistema medira tu fuerza actual, Cazador."*

3 tarjetas informativas con iconos:
- quiz: **"15 preguntas mixtas"**
- timer: **"~5 minutos"**
- lightbulb: **"Responde lo mejor que puedas"**

Nota azul: *"No hay respuestas incorrectas. El objetivo es calibrar tu nivel inicial."*

- Boton **"INICIAR EVALUACION"** con flecha → inicia diagnostico
- Link *"Omitir por ahora"* → va al home directamente

---

## 3.2 Diagnostico Rapido (`/diagnostic/quick`)

### AppBar
- X para cerrar a la izquierda
- Centro: **"CALIBRACION DEL SISTEMA"** (12px, bold, letterSpacing 2)
- Barra de progreso lineal debajo (6px, azul sobre gris)

### Pregunta
- **"PREGUNTA X DE 15"** en azul
- Caja de pregunta con fondo blanco 3% — texto 20px, altura de linea 1.6
- Cada pregunta nueva anima con fadeIn + slideX desde la derecha
- Opciones (A, B, C, D) como botones con borde gris, chevron derecho
- **SIN feedback** — no se muestra si es correcta o incorrecta
- Pista inferior: *"Responde con sinceridad. No hay feedback inmediato en esta fase."*

Al responder la pregunta 15 → envia todas las respuestas → va a resultados.

---

## 3.3 Revelacion de Resultados (`/diagnostic/results`)

### Fase 1: Secuencia Cinematica (4 segundos)

Pantalla negra pura. Secuencia temporal:
- 0s: **"EL SISTEMA TE HA EVALUADO..."** fade-in (blanco, letterSpacing 4)
- 1.5s: **"CALCULANDO RANGO DE CAZADOR"** fade-in (azul, letterSpacing 2)
- 2s: textos empiezan a desaparecer
- 4s: **FLASH BLANCO** — toda la pantalla se vuelve blanca por 200ms y luego desaparece instantaneamente

### Fase 2: Resultados (aparecen despues del flash)

Todo fade-in 800ms:

1. **"TUS ESTADISTICAS"** — blanco 70%, letterSpacing 4
2. **"CAZADOR REGISTRADO"** — azul, 24px, ultra-bold + shimmer
3. **Radar Chart** (300x300px): 5 anillos concentricos blancos + poligono azul animado que crece desde el centro hacia afuera durante 2 segundos. Etiquetas: **MAT, LEC, CIEN, SOC, ING**
4. **Indicador de Rango**: caja azul 10% con borde azul 30%
   - "RANGO INICIAL" en blanco 54%
   - La **letra del rango** (ej: "E") en blanco 72px ultra-bold italica — rebota con Curves.bounceOut al aparecer
5. Boton **"COMENZAR ENTRENAMIENTO"** azul

---

## 3.4 Primera Mision (`/diagnostic/mission`)

1. **"NUEVA MISION DISPONIBLE"** — azul, letterSpacing 3
2. **"EL DESPERTAR DEL CAZADOR"** — 28px, ultra-bold

**Tarjeta de mision** (borde azul 20%, sombra):
- Icono assignment (48px, azul)
- **"Mision de Calibracion"**
- *"El sistema ha detectado una debilidad en Lectura Critica. Completa tu primer entrenamiento para fortalecerte."*
- Recompensas: **+50 XP** (ambar) + **+20 Oro** (amarillo)

Dos opciones:
- **"ACEPTAR MISION"** — boton GIGANTE azul (64px alto), ultra-bold, letterSpacing 4, con shimmer perpetuo y pulso de escala 1→1.02. Este boton **respira** continuamente → va a Practica
- *"IR AL PANEL PRINCIPAL"* — link discreto → va al Home

---

# FASE 4: SHELL PRINCIPAL (Navegacion Persistente)

## 4.1 Estructura del Shell

### AppBar Global (siempre visible)
- Titulo: icono escuela + "ICFES"
- Derecha: 3 indicadores en pildora:

#### Indicador de Corazones
Pildora con icono corazon + "4/5". Si 0 corazones: fondo rojo 20%, borde rojo, pulso de escala. Si corazones ≤ 1: icono pulsa 1→1.2 cada 500ms. Si hay regeneracion: muestra timer "28m" debajo.

**Al tocar** → Bottom sheet con 5 corazones grandes (llenos=rojo, vacios=gris), timer de regeneracion, opciones de recarga (ver anuncio gratis, pagar 150 Oro).

#### Indicador de Racha
Pildora con icono fuego + numero. Naranja si tiene racha, gris si 0. Si racha en riesgo: fondo naranja 20%, borde naranja, icono warning. Si multiplicador > 1x: badge naranja "1.5x".

**Al tocar** → Bottom sheet con fuego grande (64px), dias de racha (32px bold), mejor racha, multiplicador actual, progreso hacia siguiente hito (7→14→30 dias), opciones de Streak Freeze y reparacion.

La llama escala segun la racha:
- 0-13 dias: 28px naranja
- 14-29 dias: 36px naranja con shimmer
- 30+ dias: 42px rojo profundo + animacion Lottie de fuego + bubble flotante "x2.0"
- Congelada: snowflake azul en vez de fuego

#### Indicador de Oro
Pildora con icono moneda dorada + balance formateado (1234 → "1.2K"). Borde dorado 50%. Shimmer al cargar.

**Al tocar** → Bottom sheet con moneda grande (48px), balance (36px dorado), info de para que sirve (tienda, corazones, racha), boton actualizar.

### Bottom Navigation (4 tabs)
| Tab | Icono | Label | Ruta |
|-----|-------|-------|------|
| Inicio | home | Inicio | `/home` |
| Ligas | emoji_events | Ligas | `/leagues` |
| Plan | menu_book | Plan | `/study-plan` |
| Perfil | person | Perfil | `/profile` |

Seleccionado: purpura lleno. No seleccionado: gris outlined. Fondo: slate-800. Elevacion 8.

---

## 4.2 Banner Offline

**Online sin pendientes**: invisible (0px).

**Offline**: barra naranja 40px: icono cloud_off + *"Sin conexion - Los cambios se guardaran localmente"*

**Sincronizando**: barra cyan 40px: spinner + *"Sincronizando N cambio(s)..."*

Transicion animada (300ms) entre estados.

---

# FASE 5: HOME SCREEN (`/home`)

## Lo que ve el usuario al abrir la app cada dia:

### Bienvenida
- **"Bienvenido de vuelta, {nombre}"** — 24px bold
- *"Listo para subir de nivel?"* — 16px

### Alertas de Perdida (sistema psicologico)

Aparecen tarjetas de alerta segun condiciones:

| Trigger | Condicion | Severidad | Mensaje | Color |
|---------|-----------|-----------|---------|-------|
| Racha en riesgo | racha ≥ 3 Y faltan ≤ 8h para las 4AM | ALTA si ≤ 2h | *"Tu racha de N dias se pierde en Xh!"* | Naranja |
| Pocos corazones | corazones ≤ 1 | MEDIA | *"Solo te queda N corazon!"* | Rojo |
| Riesgo descenso | posicion liga > 40 | ALTA si > 45 | *"Posicion #N - Riesgo de descenso!"* | Rojo |
| Inactividad | ≥ 2 dias sin actividad | BAJA | *"Llevas N dias sin entrenar"* | Gris |

**Alta severidad**: borde 2px con glow, badge "URGENTE", icono TIEMBLA con shake perpetuo. Toda la tarjeta tiene sombra brillante.

**Si hay > 2 alertas**: se compacta en una sola fila mostrando solo la mas urgente + badge "+N".

### Banner de Prueba Social

Caja azul 10% con icono de grupo:
- Mensajes tipo: *"Tu racha te pone entre los mas constantes"*, *"Solo N Cazadores te superan"*
- Badge de percentil: "Top 30%" en azul/verde/ambar segun posicion

### Progreso Dotado (solo usuarios nuevos, dias 0-7)

Panel purpura con borde purpura: **"YA TIENES VENTAJA"**
- Items: "Pack de Bienvenida" (purpura), "Tu Viaje Comenzo" (azul, 10% del camino), "Racha Protegida" (naranja si tiene racha ≥ 1)
- Truco psicologico: la barra de progreso siempre muestra minimo 10% aunque sea 0 real

### Tarjeta de Meta Diaria

**"Meta Diaria"** — barra de progreso cyan sobre gris. Meta: 100 XP/dia.
- Completada: *"Meta completada! Excelente trabajo!"*
- Incompleta: *"Gana N XP mas para completar tu meta y mantener tu racha."*

### Tarjeta Continuar Estudiando

Solo aparece si tiene plan activo. Muestra:
- Icono de materia en su color
- **"Continuar Estudiando"** + nombre de materia en color
- Badge de progreso "%"
- Nombre de unidad actual
- Barra de progreso en color de materia
- Toca → va al plan de estudio

Plan completado 100%: tarjeta verde con trofeo: *"Plan Completado! Has completado {materia}. Sigue asi!"*

### Banner Boss Raid

Solo visible si hay raid activa. Tarjeta con borde purpura, gradiente purpura→oscuro:
- Icono fuego rojo (40px) + **"Jefe de Incursion Activo!"**
- *"Derrota a '{nombre}' con otros estudiantes!"*
- Timer: *"N restantes"*
- Toca → va a Boss Raid

### Tarjeta Modo Conquista

Siempre visible. Gradiente purpura profundo con sombra:
- Icono castillo ambar + **"MODO CONQUISTA"** (ambar, letterSpacing)
- *"Conquista territorios y aprende"*
- Toca → va al mapa de mazmorra

### Acciones Rapidas (grid 2x2)

| Posicion | Icono | Label | Color | Extra |
|----------|-------|-------|-------|-------|
| Arriba-izq | play_circle_fill | **Practica** | Verde | — |
| Arriba-der | diamond | **Millonario** | Dorado | Badge rojo "NUEVO" |
| Abajo-izq | menu_book | **Mi Plan** | Purpura | — |
| Abajo-der | emoji_events | **Ligas** | Cyan | — |

Cada tarjeta: Card con icono 32px + label. AspectRatio 1.8 (tarjetas anchas).

### Resumen Semanal

**"Resumen de la Semana"** — 3 estadisticas en fila:
- Estrella cyan: **"XP Ganado"** + valor
- Pregunta purpura: **"Preguntas"** + valor
- Check verde: **"Precision"** + porcentaje

---

## 5.1 Modal de Racha Perdida (auto-aparece)

Se dispara automaticamente si el usuario perdio su racha. Bottom sheet oscuro (#1A1A1A) con esquinas redondeadas 32px:

1. Icono fuego GRIS (80px) — llama apagada
2. **"RACHA PERDIDA"** — 24px ultra-bold
3. *"Tu llama de N dias se ha apagado. Pero un verdadero cazador siempre puede reponerse."*
4. Boton ambar: **"REPARAR RACHA (300 ORO)"**
5. Boton azul: **"REPARAR CON ANUNCIO"** (icono video)
6. Boton outline: *"EMPEZAR DE NUEVO"* (descarta, racha = 0)

## 5.2 Modal Corazones Agotados (aparece al intentar practicar sin corazones)

Bottom sheet oscuro con borde rojo y sombra roja:

1. Icono corazon roto rojo (64px) con shake
2. **"TE HAS QUEDADO SIN MANA!"** — rojo, 22px ultra-bold
3. *"Los cazadores necesitan energia para ganar XP y subir de rango."*

4 opciones:
- Verde: **"VER ANUNCIO"** — *"+1 corazon (N restantes hoy)"*
- Purpura: **"MODO ENTRENAMIENTO"** — *"Sigue practicando sin ganar XP ni Oro"*
- Azul: **"MANA INFINITO"** — *"Desbloquea todo el potencial con Premium"*
- Link: *"ESPERAR REGENERACION"* — *"Proximo corazon en Xh Ym"*

---

# FASE 6: PRACTICA (`/practice`)

## 6.1 Seleccion de Materia

AppBar: **"Elige un Area"**. Lista de 5 materias como ListTiles con Card.

**Gate**: Si no has completado el diagnostico profundo de esa materia, te redirige primero al diagnostico profundo.

## 6.2 Sesion de Practica (`/practice/session/:subjectId`)

### AppBar
- X para cerrar
- Barra de progreso horizontal (gris → verde)

### Area de Pregunta
- **"Pregunta N de 20"** (pequeno)
- Texto de la pregunta en caja (fondo blanco 3%, borde blanco 5%, esquinas 16px)
- Cada pregunta nueva anima con fadeIn + slideX

### Badge Anti-Gaming
Junto a la pregunta, si la pregunta es repetida:
- **"0 XP (REPETIDA)"** — badge rojo (pregunta ya respondida recientemente)
- **"5 XP (REPASO)"** — badge naranja (repaso valido)

### Opciones de Respuesta (A, B, C, D)
Cada una es un `PressableScale` (se encoge al presionar):
- No seleccionada: borde gris 2px
- Seleccionada: borde azul 2px, fondo azul 10%, circulo de letra lleno azul
- Deshabilitadas despues de verificar

### Boton "VERIFICAR"
- Gris deshabilitado si no hay seleccion
- Azul activo si hay opcion seleccionada
- 56px alto, esquinas 16px

### Al Verificar Respuesta Correcta

**Todo esto pasa simultaneamente en <1 segundo:**

1. **Vibracion**: patron de exito (light impact)
2. **Overlay de Respuesta Correcta** (fullscreen, 600ms, no bloquea taps):
   - Glow verde expandiendose (circulo 200px → escala 3x)
   - Checkmark rebotando con escala elastica (80px circulo verde con check blanco)
   - Si hay Lottie `correct_check.json`: animacion sobre el checkmark
   - **"+N XP"** flotando hacia arriba en pildora ambar con estrella
   - Si combo ≥ 2: pildora "COMBO xN" aparece (azul/naranja/purpura segun nivel)
   - Si combo ≥ 3: **EXPLOSION DE PARTICULAS** — 12 circulos (verde, ambar, lima, amarillo) radiando desde el centro en angulos de 30°
   - Si combo ≥ 5: animacion Lottie `starBurst` (250px) en el centro

3. **Feedback Overlay** (slide-up desde abajo, elasticOut):
   - Fondo verde 95%
   - Lottie correctCheck + icono check_circle
   - Texto del combo (ej: "IMPARABLE!") o "Excelente!"
   - Desglose XP: "+15 XP" con detalle "10 + 5 bonus" si hay combo
   - Boton blanco **"CONTINUAR"**

4. **Combo Overlay** (esquina superior derecha):
   - Fondo negro 90%, borde 3px del color del combo, sombra brillante
   - Icono pulsando (escala 1→1.2 en 500ms loop)
   - Texto del combo + "COMBO xN" italica
   - Badge "+N XP BONUS" en ambar

5. **Recompensa Variable** (20% probabilidad):
   - Popup centrado con fondo negro 54%
   - Bonus aleatorio: +5/10/15 XP (50%), +5/10/25 Oro (30%), o Cofre Legendario +50/100 XP (20%)
   - Icono pulsando con shimmer, se autodescarta en 2.5s

### Al Verificar Respuesta Incorrecta

1. **Vibracion**: patron de error (heavy impact) + 200ms despues: patron corazon perdido
2. **Overlay Incorrecto** (fullscreen, 800ms):
   - Pulso rojo expandiendose
   - X roja temblando (shake horizontal 6hz)
   - **Corazon que se parte**: corazon rojo aparece, se divide en 2 mitades que se separan con rotacion, luego "-1" negro aparece desde arriba
   - Pista de respuesta correcta: caja verde oscuro: *"Respuesta: {correcta}"* con icono bombilla (fade-in a 600ms)

3. **Feedback Overlay** (slide-up, rojo):
   - "Incorrecto" con X roja
   - *"La respuesta era: {respuesta correcta}"*
   - Boton blanco **"CONTINUAR"**

4. Se pierde 1 corazon (se llama `useHeart()`)

### Sistema de Combos (compartido en todos los modos)

| Combo | Nivel | Texto | Color | Icono | Efectos |
|-------|-------|-------|-------|-------|---------|
| 1 | ninguno | — | gris | bolt | nada |
| 2 | good | "Bien!" | Azul | thumb_up | — |
| 3-4 | excellent | "Excelente!" | Verde | auto_awesome | shimmer de chispas |
| 5-6 | unstoppable | "IMPARABLE!" | Naranja | bolt | shake |
| 7-9 | onFire | "ON FIRE!" | Rojo profundo | fuego | llamas + shake |
| 10-14 | legendary | "LEGENDARIO!" | Dorado | trofeo | explosion + chispas |
| 15+ | invincible | "INVENCIBLE!" | Purpura/Magenta | escudo | glow + chispas + llamas |

**Timer de combo**: 30 segundos. Si pasan 30s sin actividad, el combo se resetea a 0.

**Formula XP**: `XP Total = XP Base + min(combo, 15)`

### Repaso Espaciado (SM-2)

Cada respuesta se procesa con el algoritmo SM-2:
- Respuesta < 5 segundos: EASY (intervalo sube mucho)
- 5-15 segundos: GOOD (intervalo normal)
- > 15 segundos: HARD (intervalo sube poco)
- Incorrecta: AGAIN (resetea intervalo, reprogramar pronto)

## 6.3 Resultados de Practica

1. Vibracion de celebracion
2. Confetti emoji gigante (100px)
3. **"SESION TERMINADA!"** — 32px bold

Estadisticas (aparecen con delay 500ms):
- Respuestas correctas: "14/20"
- XP Ganado: "+{N}" en naranja (contador animado de 0 al total en 1 segundo)
- Si bonus: *"Incluye +N XP de combo"* en naranja claro italica
- Mejor combo: "7" en rojo profundo
- Precision: "70%"

Boton azul **"TERMINAR"** con sombra glow (60px alto, PressableScale)

---

# FASE 7: MODO MILLONARIO (`/millionaire`)

## 7.1 Pantalla de Inicio

**Fondo**: gradiente oscuro triple (#1a1a2e → #16213e → bgDark)

- Icono diamante dorado (64px) con shimmer perpetuo
- **"MODO MILLONARIO"** — dorado, 28px bold, letterSpacing 3
- *"Quien quiere ser millonario?"* — italica

### Tarjeta de Reglas (borde purpura)
- 15 preguntas de dificultad progresiva
- Facil → Media → Dificil
- Checkpoints aseguran recompensas minimas
- Si fallas, ganas lo del ultimo checkpoint
- Limite: 3 partidas por dia

### Tarjeta de Checkpoints (borde dorado)
| Pregunta | XP | Oro |
|----------|----|-----|
| 5 | 50 | 10 |
| 10 | 150 | 30 |
| 15 | 500 | 100 |

### Tarjeta de Comodines (borde cyan)
- **50:50** — Elimina 2 opciones incorrectas (Gratis)
- **Pista IA** — Muestra una pista, no la respuesta (50 Oro)
- **Saltar** — Salta sin penalizacion (Gratis)

Badge de partidas: "Partidas disponibles: N/3" (verde) o "Sin partidas hoy. Vuelve manana!" (rojo)

**Costo de entrada**: 100 Oro. Boton dorado **"INICIAR JUEGO"**.

## 7.2 Pantalla de Juego

### Barra superior
- X para salir (muestra dialogo de confirmacion: pierdes todo el progreso)
- Badge XP cyan: "+N XP" acumulado
- Balance de Oro actual

### Banner de Premio
**"Premio: +N XP"** (cyan) + **"+N Oro"** (dorado). Si es checkpoint: badge dorado "CHECKPOINT" con escudo.

### Tarjeta de Pregunta

**Header**: "Pregunta N/15" (purpura) + dificultad coloreada:
- Facil → verde
- Facil-Media → cyan
- Media → naranja
- Media-Dificil → rojo naranja
- Dificil → rojo

Texto de pregunta en caja con borde purpura y glow. Si hay pista IA activa: caja dorada con bombilla + texto italica.

### Opciones (A, B, C, D) con animacion escalonada (100ms por opcion)
- No seleccionada: bgCard, borde bgElevated
- Seleccionada: borde purpura + glow + circulo purpura
- **Despues de revelar** (1.5 segundos de pausa dramatica):
  - Correcta: verde con check + trofeo dorado + shake
  - Incorrecta (la tuya): roja con X
  - Otras: descoloridas
  - Eliminadas (50:50): texto tachado, gris

### Escalera de Premios Flotante (derecha)
- Compacta por defecto (muestra pregunta actual + cercanas + checkpoints)
- Toca para expandir: 160px con las 15 preguntas
- Pregunta actual: resaltada purpura con shimmer
- Completadas: verde con check
- Checkpoints: borde dorado de escudo

Todas las 15 preguntas con recompensas:

| Q# | XP | Oro | Dificultad | Checkpoint |
|----|----|-----|------------|------------|
| 1-3 | 5 | 1-3 | Facil | |
| 4-6 | 8 | 5-12 | Facil-Media | Q5: 50XP/10Oro |
| 7-9 | 12 | 15-22 | Media | |
| 10-12 | 18 | 30-50 | Media-Dificil | Q10: 150XP/30Oro |
| 13-15 | 25 | 65-100 | Dificil | Q15: 500XP/100Oro |

### Barra de Comodines (abajo)
3 botones de 90x80px con borde coloreado y shimmer:
- Usados: gris oscuro con checkmark
- Disponibles: coloreados con glow
- "Pista IA" muestra costo "50" con moneda

**"Retirarse"** — aparece despues de pregunta 1. Dialogo: puedes llevarte lo ganado o seguir jugando.

## 7.3 Resultados

**Victoria** (15/15): circulo dorado/naranja con trofeo, **"FELICIDADES!"**, recompensas completas
**Derrota**: circulo rojo con carita triste, **"Fin del Juego"**, ganas hasta el ultimo checkpoint
**Retiro**: circulo cyan/purpura con alcancia, **"Te Retiraste"**, conservas lo ganado

Tarjeta de recompensas (borde purpura): columna XP + columna Oro con animacion de escala.
Boton **"JUGAR DE NUEVO"** (solo si quedan partidas) o mensaje de limite diario.

---

# FASE 8: MAZMORRAS / MODO CONQUISTA

## 8.1 Mapa de Mazmorra (`/dungeon/map`)

**Fondo**: azul muy oscuro (#0F172A) con imagen de mapa tematica (oscurecida 50%). Fallback: fondo solido con icono mapa fantasma.

### Header (slide-in desde arriba)
Panel semi-transparente negro:
- Nombre de la puerta en MAYUSCULAS
- Badge azul: "RANK {D/C/B/A/S}"
- Reloj + "N min" de limite de tiempo
- Circulo de progreso verde (porcentaje completado)

### Mapa de Nodos (300x500px, camino en S)

5 nodos posicionados en S:
```
        [4-BOSS]        (125, 20)  — arriba centro
   [3]                  (50, 120)  — izquierda
              [2]       (200, 220) — derecha
   [1]                  (50, 320)  — izquierda
        [0-INICIO]      (125, 420) — abajo centro
```

Lineas de conexion:
- Completadas: azul 50%, 4px
- Bloqueadas: gris 20%, 2px

### Nodo Individual

Tipos y colores:
- **Combate** (default): azul, icono escudo
- **Tesoro**: ambar, icono inventario
- **Boss** (nodo 5): rojo, icono fuego, escala 1.3x mas grande

Estados:
- **Bloqueado**: gris, icono candado, sin sombra
- **Disponible/Actual**: borde blanco 3px, sombra del color con glow (blur 15, spread 2). Si es el nodo actual: pulso de escala 1→1.1 perpetuo + badge rojo **"BATTLE!"** debajo
- **Completado**: icono check blanco + fila de 1-3 estrellas debajo (ambar=ganadas, gris=no ganadas)

**Al tocar nodo disponible** → Dialogo Pre-Batalla

## 8.2 Dialogo Pre-Batalla

Caja oscura (#1E293B) con esquinas 24px:
- Circulo enemigo rojo (80px) con icono triangulo + escala elastica
- **"GUARDIAN GEOMETRICO"** — 18px bold
- *"Nivel 5 • Matematicas"*
- Recompensas: "150 XP" (ambar) + "50 Gold" (amarillo) + "Item?" (purpura)
- Botones: *"Huir"* (discreto) | **"ATACAR!"** (rojo, 2x tamaño)

## 8.3 Batalla (`/dungeon/battle`)

**Carga**: animacion Lottie battleStart (150px) + *"Preparando batalla..."*

### Zona de Combate (mitad superior)

**Enemigo** (arriba-derecha):
- Barra HP roja + nombre
- Avatar 150x150 con borde rojo. Idle: pulso escala 1→1.05. Golpeado: shake 500ms

**Jugador** (abajo-izquierda):
- Barra HP verde + "Cazador (Tu)"
- Avatar 120x120 azul. Golpeado: shake 500ms

**Numeros de dano** (centro, al responder):
- Correcto: **"-{dano}"** en naranja (48px bold italica) flota hacia arriba
- Incorrecto: **"MISS"** en rojo, misma animacion

### Panel de Pregunta (mitad inferior)

Panel oscuro (#1E293B) con esquinas 30px arriba:
- Si combo > 1: **"COMBO xN!"** ambar con bounceOut
- "Pregunta N/total" + texto de pregunta
- **Grid 2x2 de opciones** (colores: azul, purpura, naranja, teal)
  - Seleccionada: 30% opacidad + borde 2px
  - Correcta revelada: verde lleno + check
  - Incorrecta revelada: rojo + X
- Boton **"ATACAR"** (verde) o **"SIGUIENTE"** (azul) o **"FINALIZAR"**

### Sonido
- Inicio: musica de batalla (loop)
- Correcto: sonido de ataque
- Incorrecto: sonido de dano
- Victoria: fanfare de victoria + parar musica
- Derrota: sonido de derrota + parar musica

## 8.4 Resultado de Batalla

**Victoria**: fondo calido oscuro (#2C1E0A), borde ambar, trofeo con glow ambar
- **"VICTORIA!"** ambar ultra-bold
- "+N XP" (azul, retraso 200ms) + "+N Gold" (ambar, retraso 400ms)
- Oro = 25 base + (correctas × 5) + (mejor combo × 2)
- Estrellas: ≥90% = 3★, ≥70% = 2★, ≥50% = 1★

**Derrota**: fondo rojo oscuro (#2C0A0A), carita triste roja
- **"DERROTA"** — *"No te rindas! Estudia un poco mas y vuelve a intentarlo."*
- XP = mitad del acumulado. Oro = 0.

---

# FASE 9: BOSS RAID (Evento Multijugador)

## 9.1 Pagina de Boss Raid (`/boss-raid`)

**Fondo**: negro (#0A0A0A) con gradiente radial purpura desde arriba + shimmer pulsante purpura cada 4 segundos. Atmosfera dramatica.

### Visual del Boss (180x180)
- Circulo con borde purpura 2px + sombra purpura (blur 40, spread 10)
- Icono cerebro purpura (100px) cuando activo, gris cuando inactivo
- Label **"S-RANK BOSS"** en rojo (letterSpacing 4, ultra-bold) — con shake + fadeIn
- Nombre del boss (24px ultra-bold)

### Badge Timer
Esquina superior: fondo rojo 15%, borde rojo 50%, icono timer + countdown en monospace rojo. Pulso sutil cada segundo.

### Tarjeta de Estado del Boss
- Indicador de **FASE** (1/2/3 segun HP restante: >66% = F1, 33-66% = F2, <33% = F3)
- Barra HP (12px): color transiciona rojo→naranja→amarillo al bajar + shimmer perpetuo
- Stats: Dano total (rojo), Mi dano (cyan), XP Bonus "{multiplier}x" (ambar)
- Si hay ranking: badge ambar "Puesto #N en la Raid"

### Boton de Entrada
70px alto, fondo rojo oscuro, borde rojo:
**"ENTRAR A LA MAZMORRA"** con icono rayo (28px)
Pulso perpetuo + shimmer rojo

**Inactivo**: reloj gris + *"La Raid no esta activa"* + *"Vuelve pronto"*

## 9.2 Batalla de Boss Raid (`/boss-raid/battle/:sessionId`)

**Fondo animado**: gradiente radial rojo→purpura→negro + shimmer rojo perpetuo. **Screen shake** al hacer dano (sin(value × π × 4) × 5 pixeles, 500ms).

### Boss (arriba)
Circulo 100px con gradiente rojo→purpura, borde rojo 3px, sombra roja
- Animacion idle: pulso 1→1.05 cada 2s
- Al golpear: filtro rojo + escala a 0.9x

### Barra HP Global (24px alto)
- Fill proporcional con gradiente del color
- Color: rojo (>50%) → naranja (25-50%) → amarillo (<25%)
- Glow en el color actual
- Shimmer blanco perpetuo
- Texto centrado: "{actual} / {max} HP"

### Numeros de Dano Flotantes
- Normal: "-{dano}" rojo 24px, flota hacia arriba
- Critico (combo ≥ 3): "-{dano}" amarillo 32px, escala a 1.3x
- Posicion aleatoria ±50px del centro del boss

### Stats de Batalla (3 badges horizontales)
- COMBO: "xN" (blanco→naranja→amarillo segun nivel, pulso al incrementar)
- DANO: total acumulado (rojo)
- XP: "+N" (cyan)

### Timer de Batalla (arriba derecha)
- Normal: fondo blanco 10%, texto blanco
- Ultimo minuto: fondo rojo 30%, texto rojo, **pulso de escala** 1→1.05 cada 500ms

**Concepto clave**: El Boss es compartido entre TODOS los jugadores. El dano se acumula globalmente. Si abandonas, el boss conserva el dano recibido.

---

# FASE 10: PLAN DE ESTUDIO (Videoteca tipo Coursera)

## 10.1 Creacion del Plan

**Sin plan**: pantalla con:
- Icono libro (80px gris)
- *"Comienza tu aventura"* / *"Crea un plan de estudio personalizado"*
- Boton **"Crear Mi Plan"** → bottom sheet con 5 materias ICFES

| ID | Materia | Icono | Color |
|----|---------|-------|-------|
| math | Matematicas | calculate | #3B82F6 azul |
| reading | Lectura Critica | menu_book | #A855F7 purpura |
| science | Ciencias Naturales | science | #22C55E verde |
| social | Sociales | public | #F97316 naranja |
| english | Ingles | language | #EC4899 rosa |

Al seleccionar → POST a `/study-plans/generate-adaptive` (usa datos del diagnostico). Backend genera plan con IA (Claude opcionalmente) con unidades personalizadas.

## 10.2 Vista del Plan (`/study-plan`)

### Header (SliverAppBar 200px)
Gradiente del color de la materia (30% → negro). Muestra:
- Badge con nombre de materia en MAYUSCULAS
- Titulo del plan (24px bold)
- Tiempo estimado + "X/Y unidades"

### Tarjeta de Progreso General
Gradiente del color de la materia:
- **"Progreso General"** + badge porcentaje
- Barra de progreso con glow (12px)
- 3 stats: Unidades completadas (verde check) | Pendientes (naranja reloj) | Peso ICFES % (estrella dorada)

### Tarjeta "CONTINUAR ESTUDIANDO" (resaltada)
Tarjeta con gradiente, boton play PULSANTE (escala 1→1.1 loop):
- **"CONTINUAR ESTUDIANDO"** en color de materia
- Nombre de la unidad
- Mini barra de progreso
- Toca → detalle de la unidad actual

### Lista de Unidades (SliverList, animacion escalonada 50ms)

Cada `_UnitCard`:

**Icono izquierdo** (circulo 44x44):
- Completada: circulo verde + check blanco
- Bloqueada: circulo gris + candado
- En progreso/disponible: circulo coloreado + numero de unidad

**Contenido**:
- Nombre de unidad (bold o gris si bloqueada)
- Descripcion (1 linea, truncada)
- Barra de progreso + chips: "{videos}/3 videos" (play icon) + "{ejercicios}/10 ejercicios" (edit icon)
- Badge cyan **"IA"** (auto_awesome) si la unidad fue recomendada por IA

**Estados**:
- **Bloqueada**: fondo semi-transparente, todo al 38% opacidad, candado en vez de chevron
- **En progreso**: card normal, borde coloreado si es la actual
- **Completada**: borde verde 40%

## 10.3 Detalle de Unidad (`/study-plan/unit/:unitId`)

### Header (SliverAppBar 200px)
Gradiente purpura → oscuro:
- Badge "UNIDAD N"
- Nombre (24px bold)
- Descripcion (2 lineas)
- Tiempo estimado + badge de prioridad (alta=rojo, media=naranja, baja=verde)

### Tarjeta de Progreso (animada)
Porcentaje se cuenta de 0 al valor real en 800ms (easeOutCubic):
- Color cambia: purpura (<50%), naranja (50-80%), verde (≥80%)
- Barra principal (12px animada)
- 3 mini-barras (6px): Videos (cyan 30% peso) | Ejercicios (verde 50% peso) | Lecturas (naranja 20% peso)

### Seccion VIDEOS (icono cyan)

Cada `UnitVideo` como tarjeta horizontal:

**Izquierda (120x90px)**: Thumbnail de YouTube. Si ya visto: overlay verde con check_circle. Badge de duracion abajo-derecha.

**Centro**: Badge "REQUERIDO" naranja si aplica. Titulo (2 lineas max). Canal en gris. Objetivo de aprendizaje en italica si existe.

**Derecha**: play_arrow cyan (no visto) o replay verde (ya visto)

**Datos del video**:
- `youtubeId`, `title`, `channelName`, `thumbnailUrl`
- `relevanceScore` (0-1, del matching semantico del backend)
- `learningObjective` (por que este video es relevante)
- `isRequired`, `watchProgress` (0-100)

**Toca** → va al reproductor de video

### Seccion EJERCICIOS (icono verde)

Cada ejercicio: icono quiz (verde check si completado) + titulo + "N preguntas" + dificultad (facil=verde, medio=naranja, dificil=rojo). Si completado: estrella dorada + "Puntuacion: N%".

### Seccion LECTURAS (icono naranja)

Cada lectura: icono libro + titulo + "N min" con reloj. Toca → modal DraggableScrollableSheet (70% → 95%) con titulo, *"N min de lectura"*, contenido completo (16px, linea 1.6), boton verde **"Marcar como leido"**.

### Boton de Quiz
Gradiente purpura: **"Iniciar Quiz de la Unidad"** → va al quiz

### Temas
- "Temas a enfocarse" — chips purpura
- "Areas a mejorar" — chips naranja

## 10.4 Reproductor de Video (`/video/:videoId`)

### Tecnologia
YouTube embebido con `youtube_player_flutter`. Autoplay, subtitulos en espanol, controles visibles.

### Layout (portrait)
1. AppBar: flecha atras + titulo (truncado) + badge verde "Completado" si aplica
2. **Reproductor YouTube** (16:9)
3. **Indicador de Progreso Personalizado** (barra de 6px):
   - Track gris
   - Fill con gradiente (purpura o verde si completado) + glow
   - **Marca ambar al 80%** (linea vertical de 2x10px) — umbral de completado
   - Debajo: porcentaje actual (coloreado) + "80% para completar" (ambar) + estado ("En progreso" o "Completado")
4. **Panel de Informacion** (scrollable):
   - Titulo (bold)
   - 3 stats: "Tiempo visto" (play icon) + "Duracion" (timer) + "Progreso" (pie chart, verde si completado)
   - Si completado: badge verde gradiente: *"Video Completado ✓ +10 XP ★"*
   - Si no completado: barra de progreso hacia 80%: *"Mira N% mas para completar y ganar XP"*
   - Descripcion del video
   - **"Consejos de estudio"** (tarjeta ambar):
     - *"Toma notas mientras ves el video para reforzar el aprendizaje"*
     - *"Puedes ajustar la velocidad de reproduccion segun tu necesidad"*
     - *"Ver el 80% del video marca este contenido como completado"*

### Pantalla Completa
Al tocar fullscreen: barra de estado desaparece, orientacion se bloquea en landscape, AppBar/progreso/info desaparecen.

### Controles del Player
- Posicion actual + barra de progreso arrastrable + duracion restante
- Popup velocidad: 0.5x / 0.75x / **1.0x (Normal)** / 1.25x / 1.5x / 2.0x
- Boton fullscreen

### Tracking de Progreso
- Guarda progreso cada **10 segundos** (si cambio ≥ 5 segundos)
- Al pausar: guarda inmediatamente
- Al salir de la app: guarda inmediatamente
- **Umbral de completado: 80%** del video → marca como completado + overlay de celebracion

### Overlay de Completado (al alcanzar 80%)

Overlay fullscreen negro 87%:
- Icono de exito animado: glow verde radial pulsante (0.9→1.1), circulo verde con check, 6 estrellas ambar flotantes
- **"Video Completado!"** (fadeIn + slideY)
- Badge dorado/naranja: **"★ +10 XP"** (scale + fadeIn)
- *"Has visto mas del 80% del video. Sigue asi con tu estudio!"*
- Dos botones: *"Seguir viendo"* (outline) | **"Listo"** (verde, guarda y vuelve atras)

---

# FASE 11: LIGAS (`/leagues`)

### Header de Liga Actual

Gradiente del color de la liga (20% → negro), borde coloreado 30%, esquinas 24px:
- Circulo con icono escudo en color de la liga (40px)
- Nombre de liga (ej: **"LIGA DE BRONCE"**) — coloreado, 20px ultra-bold
- *"Termina en: 2d 14h 22m"* — countdown

### Leaderboard (30 jugadores)

Lista con pull-to-refresh (naranja). Cada entrada anima con fadeIn + slideX (50ms escalonado).

**Fila de jugador**:
- Numero de ranking (ambar si ≤ 3, gris sino)
- Avatar circular gris
- Nombre (ultra-bold si eres tu) + label **"TU"** en azul si eres tu
- XP + punto de estado

**Zonas**:
- **Promocion** (top 5): punto verde + `PromotionZoneGlow` — borde verde shimmer pulsante cada 2s
- **Segura**: punto gris
- **Descenso**: punto rojo

**Tu fila**: fondo azul 10%, borde azul 50%

---

# FASE 12: TIENDA (`/store`)

### AppBar
- **"TIENDA DEL SISTEMA"** ultra-bold
- Badge power-ups activos (verde, shimmer)
- Badge de Oro (dorado, shimmer)

### 3 Tabs: TIENDA | POWER-UPS | INVENTARIO

## Tab TIENDA

### Seccion CONSUMIBLES (scroll horizontal, items 140px ancho)
Tarjetas con gradiente del color del item, borde coloreado, glow si puedes comprarlo:
- Icono + badge de duracion ("2h", "24h")
- Nombre (2 lineas max)
- Costo con moneda (dorado si alcanza, gris si no)

### Seccion ARTICULOS PERMANENTES (grid 2 columnas)
Tarjetas con icono grande (48px) + nombre + costo. "Oro insuficiente" en rojo si no alcanza.

### Items Disponibles

| Item | Icono | Color |
|------|-------|-------|
| Congelar Racha | snowflake (ac_unit) | Cyan |
| Corazones | corazon | Rojo |
| Impulso XP | trending_up | Purpura |
| Token de Pista | bombilla | Ambar |
| Escudo | shield | Azul |
| Monedas Dobles | moneda | Amarillo |
| Congelador de Tiempo | timer_off | Teal |

### Dialogo de Compra
- Nombre + descripcion + duracion + costo vs saldo
- Si no alcanza: warning rojo "Oro insuficiente"
- Boton "Comprar" (azul si alcanza, gris si no) con vibracion

## Tab POWER-UPS

### Power-ups Activos (scroll horizontal, 140px ancho)
Tarjeta con gradiente + shimmer perpetuo:
- Icono + nombre + multiplicador "x2.0" si aplica
- Barra de progreso (4px) con glow
- Countdown: "1h 30m" normal, o rojo con shake si < 5 minutos

### Inventario de Power-ups (grid 2 columnas)
Tarjeta con icono + cantidad "x3" + nombre + boton **"ACTIVAR"** coloreado.
- Activando: spinner en el boton
- Ya activo: error "Ya tienes un {nombre} activo"
- Sin stock: deshabilitado gris

## Tab INVENTARIO
Grid 4 columnas: slots con icono (24px) + badge "xN" abajo-derecha. Inventario vacio: *"Inventario vacio"*.

---

# FASE 13: ESTADISTICAS (`/stats`)

### 3 Tabs: RESUMEN | MATERIAS | PLAN

## Tab RESUMEN

**Tarjeta de Nivel** (gradiente purpura→azul, sombra purpura):
- Circulo de nivel (80px, gradiente ambar→naranja): "Nivel" + numero
- XP total (22px bold) + barra hacia siguiente nivel + "N XP para nivel M+1"

**Stats Rapidas** (3 tarjetas):
- Racha Actual (fuego naranja) + "Max: N"
- Precision (check verde) + "correctas/total"
- Dias Estudio (calendario azul) + "Nh total"

**Grafico Semanal**: 7 barras verticales (32px ancho) con gradiente purpura, la de hoy con borde blanco. Labels: Lun/Mar/Mie/Jue/Vie/Sab/Dom.

**Heatmap Anual** (estilo GitHub): 52 semanas × 7 dias, 5 niveles de intensidad (blanco 5% → verde brillante). Labels de meses en espanol. Al tocar un dia: dialogo con fecha + conteo de actividad + desglose. Leyenda: "Menos" → "Mas".

## Tab MATERIAS

**Radar Chart** (250px): pentagono con tu nivel (azul) vs promedio nacional (gris). Leyenda coloreada.

**Materias a Mejorar** (trending_down rojo): listado de materias debiles.
**Tus Fortalezas** (trending_up verde): listado de materias fuertes.

**SubjectMasteryCard**: icono coloreado + nombre + badge (Fortaleza/Debilidad/Promedio) + barra de progreso con marca vertical del promedio nacional + "Precision: X%" + "vs Nacional: +X%/-X%"

**Al tocar materia** → bottom sheet con:
- Icono grande + nombre
- 3 stats: Dominio% | Precision% | Preguntas N
- Comparacion vs promedio nacional (+X% arriba / -X% abajo)
- Top 5 temas con porcentaje de maestria

## Tab PLAN

**Tarjeta Progreso del Plan** (gradiente azul→purpura o verde si completado):
- Icono libro/trofeo + titulo + nombre del plan
- Circulo de progreso (60px) con porcentaje
- Barra lineal (10px)
- 3 stats: Unidades X/Y | Videos X/Y | Quizzes X/Y
- Boton: "Continuar Estudiando" o "Ver Resumen"

**Progreso por Unidad**: lista con circulos de estado (check/candado/numero) + nombre + conteo videos + estado quiz ("Pendiente" gris / "X%" verde) + barra de progreso.

**Sin plan**: icono libro gris 64px + *"No tienes un plan de estudio activo"* + boton "Iniciar Diagnostico".

---

# FASE 14: LOGROS (`/achievements`)

### 6 Tabs: Todos | Rachas | Practica | Maestria | Social | Especial

### Header de Progreso
Gradiente ambar→naranja, sombra ambar:
- "Progreso Total" + "desbloqueados/total" (headline)
- Circulo de progreso (70px) con porcentaje
- 4 badges de rareza: Comun (gris) | Raro (azul) | Epico (purpura) | Legendario (naranja) con conteo X/Y

### Grid de Badges (3 columnas)

**Desbloqueado**: gradiente de color de rareza, borde coloreado 3px, sombra brillante. Icono blanco centrado. Nombre debajo en bold.

**Bloqueado**: gris oscuro, borde gris. Icono gris. Si tiene progreso: `CircularProgressIndicator` sobre el icono. Porcentaje debajo en color de rareza.

**Secreto bloqueado**: overlay negro 54% + icono candado. Nombre: "???".

### Al tocar badge → Bottom Sheet de Detalle
- Badge grande (120px) con glow de rareza
- Pildora de rareza (COMUN/RARO/EPICO/LEGENDARIO)
- Nombre + descripcion
- Si bloqueado: barra de progreso + hint (ej: *"Mantiene una racha de 30 dias"*)
- Si desbloqueado: badge verde *"Desbloqueado hace 3 dias"*
- Recompensas: "+N XP" (purpura) + "+N Oro" (ambar)

### Animacion de Desbloqueo (overlay fullscreen, 3 segundos)
- Fondo negro 87% + 20 particulas flotantes del color de rareza
- **"LOGRO DESBLOQUEADO"** (letterSpacing 4)
- Badge pulsante con glow oscilante (0.3→0.6 opacidad, 30→50 blur)
- Badge escala 0→1.3→1.0 con bounceOut
- Nombre (28px bold) slide-in desde abajo
- Pills de recompensa
- *"Toca para continuar"*

---

# FASE 15: PERFIL (`/profile`)

- Avatar circular azul (radius 50) con icono persona
- Nombre (24px bold) + email (gris)
- Lista: **Clase** (placeholder "Cazador Rango E") | **Estadisticas y Progreso** → /stats | **Logros** → /achievements | **Configuracion** → /settings | **Cerrar Sesion** (rojo con confirmacion)

---

# FASE 16: CONFIGURACION (`/settings`)

### Seccion CUENTA: nombre + email

### Seccion APLICACION:
- Notificaciones (toggle, navega a pagina de notificaciones granulares)
- Tema oscuro (switch siempre ON, TODO)

### Pagina de Notificaciones Granulares:
Toggle maestro + toggles individuales:
- Racha diaria (naranja)
- Misiones diarias (azul)
- Meta diaria XP (verde)
- Liga semanal (ambar)
- Boss Raid (rojo)
- Logros desbloqueados (purpura)

### Seccion MODO DESARROLLADOR (oculta):
- Se activa tocando 7 veces "v1.0.0" (despues de 4 toques: *"X toques mas para modo desarrollador"*)
- Reiniciar Onboarding, Reinicio Completo, Estado Actual (debug), Desactivar

### Seccion SESION:
- Cerrar Sesion (rojo)

---

# SISTEMAS TRANSVERSALES INVISIBLES

## Sistema de Dopamina
- **Loss Aversion**: alertas urgentes con shake, glows rojos, timers
- **Social Proof**: comparacion con otros jugadores
- **Endowed Progress**: progreso "regalado" para nuevos (min 10% en barras)
- **Variable Rewards**: bonus aleatorios (20% prob) con popup sorpresa
- **Combo System**: progresion visual/sonora/haptica por respuestas consecutivas

## Offline-First
- Cola de acciones offline, sync automatico al reconectar
- Cache de preguntas en Hive (almacenamiento local)
- Interceptor que encola requests fallidos

## Anti-Gaming
- Preguntas repetidas: 0 XP (REPETIDA) o 5 XP (REPASO)
- Detectado por el backend y mostrado con badge inline

## Haptics (Vibracion)
- Correcto: lightImpact
- Incorrecto: heavyImpact + heartLostPattern
- Combo ≥ 3: comboPattern
- Victoria: patron triple ascendente
- Botones: selectionClick

## Retry con Backoff
- 3 reintentos, 500ms inicial, backoff exponencial
- En todas las llamadas de red
