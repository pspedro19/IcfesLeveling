# 🎮 GUÍA MULTIMEDIA COMPLETA — ICFES Leveling
## Sonido, Animaciones, Imágenes & UX Polish

> **Objetivo:** Que tu app se SIENTA premium aunque cueste $0 en assets.
> **Principio clave:** Un sonido bien elegido + una animación de 0.3s = la diferencia entre "app de universidad" y "app que la gente recomienda".

---

## PARTE 1: DISEÑO DE SONIDO (Audio Design)

### 1.1 Principios de Audio para Apps Educativas Gamificadas

El audio es el **50% de la experiencia emocional** de tu app. Duolingo gasta millones en esto. Tú puedes lograr el 80% del efecto con selección inteligente.

**Reglas de oro:**
- **Duración máxima:** Ningún sonido de feedback debe pasar de 1.5 segundos (excepto `battle_theme.mp3` y `victory.mp3`)
- **Formato:** MP3 a 128kbps es suficiente. NO uses WAV (archivos 10x más grandes sin beneficio perceptible en móvil)
- **Volumen consistente:** Normaliza TODOS los archivos a -14 LUFS (estándar streaming). Usa `ffmpeg` gratis:
  ```bash
  # Normalizar un archivo a -14 LUFS
  ffmpeg -i input.mp3 -af loudnorm=I=-14:TP=-1.5:LRA=11 output.mp3
  
  # Batch: normalizar todos los mp3 de una carpeta
  for f in *.mp3; do
    ffmpeg -i "$f" -af loudnorm=I=-14:TP=-1.5:LRA=11 "norm_$f"
    mv "norm_$f" "$f"
  done
  ```
- **Tonalidad consistente:** Todos los sonidos positivos en tonalidad mayor (Do mayor, Sol mayor). Sonidos negativos en menor o con disonancia. Esto es CRÍTICO para coherencia.
- **No competir con concentración:** El usuario está resolviendo preguntas ICFES. Los sonidos deben ser CORTOS y no intrusivos.

### 1.2 Guía Detallada por Cada Sonido

#### 🟢 GRUPO 1: Feedback Básico (Los más importantes — el usuario los oye 100+ veces)

| # | Archivo | Duración Ideal | Qué Buscar en Pixabay | Criterio de Selección |
|---|---------|---------------|----------------------|----------------------|
| 1 | `ding.mp3` | 0.3-0.5s | `"correct answer notification"` o `"success chime"` | Debe ser BRILLANTE y satisfactorio. Busca un "ding" con armónicos agudos, estilo xilófono o campana cristalina. **NO uses un "ding" de microondas.** Piensa en el sonido de Duolingo cuando aciertas. |
| 2 | `wrong.mp3` | 0.3-0.5s | `"wrong answer buzz"` o `"error tone gentle"` | Debe comunicar "incorrecto" sin ser AGRESIVO. Un buzzer suave de 2 notas descendentes es ideal. **Evita buzzers industriales o alarmas.** El usuario ya se siente mal por fallar, no lo castigues con audio feo. |
| 3 | `fanfare.mp3` | 1.0-2.0s | `"achievement fanfare short"` o `"level complete rpg"` | Trompetas cortas o sintetizador épico ascendente. Debe generar DOPAMINA. Este sonido es tu "premio gordo" — úsalo solo en momentos de logro real (completar lección, ganar batalla). |
| 4 | `tick.mp3` | 0.05-0.1s | `"ui tick"` o `"counter tick"` | ULTRA corto. Un "tik" seco. Se reproduce en loop rápido durante el conteo de XP. Si es largo, se superpone y suena horrible. Prueba reproduciéndolo 20 veces seguidas rápidamente — si suena limpio, es el correcto. |
| 5 | `levelup.mp3` | 1.0-1.5s | `"level up game sound"` o `"power up rpg"` | Escala ascendente con brillo. Tipo "ta-da-DA-DÁ!" con notas subiendo. Diferente a `fanfare.mp3` — este es más "personal" (tú subiste de nivel) vs fanfare que es más "evento completado". |
| 6 | `combo.mp3` | 0.3-0.5s | `"combo hit game"` o `"streak sound"` | Un golpe con eco o reverb corto. Algo que diga "¡seguiste acertando!". Un "punch" con chispa. |
| 7 | `coin.mp3` | 0.3-0.5s | `"coin collect game"` o `"gold coin pickup"` | El clásico sonido de moneda de Mario/Zelda pero en versión libre. Metálico, agudo, satisfactorio. De todos los sonidos, este es el MÁS estandarizado — el usuario espera exactamente este tipo de sonido. |
| 8 | `click.mp3` | 0.05-0.15s | `"button click soft"` o `"ui tap"` | Click mecánico suave. NO un click de mouse real. Piensa en "toque de pantalla táctil premium". Un "toc" sutil. |
| 9 | `whoosh.mp3` | 0.3-0.5s | `"whoosh transition"` o `"swipe sound"` | Aire pasando rápido. Para transiciones entre pantallas o cuando aparece un elemento. Suave, no violento. |

#### 🔥 GRUPO 2: Combos (Progresión ascendente — CRÍTICO para engagement)

**CONCEPTO CLAVE:** Los combos deben tener **progresión tonal ascendente**. Cada combo más alto = sonido más épico/agudo/rico.

| # | Archivo | Estrategia |
|---|---------|-----------|
| 10 | `combo_2.mp3` | **Base:** 2 notas rápidas ascendentes (Do-Mi). Simple, limpio. Buscar: `"double hit combo"` |
| 11 | `combo_3.mp3` | **Medio:** 3 notas ascendentes (Do-Mi-Sol). Más energía. Buscar: `"triple combo sound"` |
| 12 | `combo_5.mp3` | **Alto:** Acorde completo con brillo. Algo que diga "vas MUY bien". Buscar: `"combo streak game"` |
| 13 | `combo_fire.mp3` | **Fuego:** Sonido anterior + efecto de fuego/llama. Buscar: `"fire power up"` — mezcla un whoosh de fuego con un chime brillante |
| 14 | `combo_legendary.mp3` | **Legendario:** Mini-fanfare épica de 1-1.5s. Coro sintético o arpa mágica. El usuario debe SENTIR que hizo algo increíble. Buscar: `"legendary item rpg"` o `"epic reward game"` |

**⚡ ALTERNATIVA RÁPIDA (si no encuentras progresión natural):**
Descarga UN sonido de combo bueno y usa `ffmpeg` para subir el pitch progresivamente:
```bash
# combo base
cp combo_base.mp3 combo_2.mp3

# combo_3: pitch +2 semitonos
ffmpeg -i combo_base.mp3 -af "asetrate=44100*1.122,aresample=44100" combo_3.mp3

# combo_5: pitch +4 semitonos  
ffmpeg -i combo_base.mp3 -af "asetrate=44100*1.26,aresample=44100" combo_5.mp3

# combo_fire: pitch +6 semitonos + reverb
ffmpeg -i combo_base.mp3 -af "asetrate=44100*1.414,aresample=44100,aecho=0.8:0.7:40:0.3" combo_fire.mp3

# combo_legendary: pitch +8 semitonos + más reverb + fade in
ffmpeg -i combo_base.mp3 -af "asetrate=44100*1.587,aresample=44100,aecho=0.8:0.88:60:0.4" combo_legendary.mp3
```
Esto crea una progresión audible clara con UN solo archivo fuente.

| 15 | `success.mp3` | = `ding.mp3` (cópialo) |
| 16 | `error.mp3` | = `wrong.mp3` (cópialo) |
| 17 | `level_up.mp3` | = `levelup.mp3` (cópialo) |
| 18 | `achievement.mp3` | Diferente a `fanfare.mp3`. Buscar: `"achievement unlock game"`. Un sonido de "desbloqueo" con efecto de apertura/revelación. Como abrir un cofre. |

#### ⚔️ GRUPO 3: Batalla (Inmersión RPG)

| # | Archivo | Duración | Estrategia |
|---|---------|----------|-----------|
| 19 | `attack.mp3` | 0.3-0.5s | Golpe de espada o impacto mágico. Buscar: `"sword slash game"` o `"magic attack rpg"`. Debe ser SATISFACTORIO — el usuario "ataca" al responder bien. |
| 20 | `damage.mp3` | 0.3-0.5s | Impacto recibido. Más grave que attack. Buscar: `"damage hit game"` o `"take damage rpg"`. Un "thud" con dolor sutil. |
| 21 | `victory.mp3` | 2.0-3.0s | MOMENTO ÉPICO. Fanfare de victoria de batalla. Buscar: `"victory fanfare rpg"` o `"battle won game"`. Trompetas, resolución musical ascendente. El usuario debe querer VOLVER a ganar. |
| 22 | `defeat.mp3` | 1.5-2.5s | Triste pero NO deprimente. Notas descendentes suaves. Buscar: `"game over gentle"` o `"defeat sad"`. Debe motivar a reintentar, no a cerrar la app. |
| 23 | `battle_theme.mp3` | 30-60s (LOOP) | Música de fondo durante batalla. **CRÍTICO:** Debe ser loopeable sin corte audible. Buscar: `"battle music loop rpg"` o `"combat theme game loop"`. Energética pero no distractora. Tempo ~120-140 BPM. |

**🎵 Para `battle_theme.mp3` — Recursos especiales:**
- **Pixabay Music** (no Sound Effects): https://pixabay.com/music/search/battle%20game/ — Canciones completas gratis
- **OpenGameArt Music**: https://opengameart.org/art-search-advanced?type=music — Filtrar por "battle" + licencia CC0
- **Incompetech (Kevin MacLeod)**: https://incompetech.com/music/royalty-free/music.html — Gratis con atribución CC-BY. Buscar "Epic", "Action". Artista legendario de música libre.

**Para hacer loop perfecto en `battle_theme.mp3`:**
```bash
# Cortar exactamente en un compás musical (ej: 32 segundos)
ffmpeg -i battle_raw.mp3 -ss 0 -t 32 -af "afade=t=out:st=31:d=1" battle_theme.mp3

# Verificar que loopea bien:
ffplay -loop 0 battle_theme.mp3
```

### 1.3 Herramienta de Procesamiento Batch

Script completo para procesar todos tus sonidos descargados:

```bash
#!/bin/bash
# process_sounds.sh — Normaliza y optimiza todos los sonidos
# Requiere: ffmpeg (sudo apt install ffmpeg)

SOUNDS_DIR="apps/mobile/assets/sounds"
cd "$SOUNDS_DIR"

echo "=== Procesando sonidos para ICFES Leveling ==="

for f in *.mp3; do
  echo "Procesando: $f"
  
  # 1. Normalizar volumen a -14 LUFS
  ffmpeg -y -i "$f" -af loudnorm=I=-14:TP=-1.5:LRA=11 -ar 44100 -b:a 128k "tmp_$f" 2>/dev/null
  
  # 2. Eliminar silencio al inicio y final
  ffmpeg -y -i "tmp_$f" -af "silenceremove=start_periods=1:start_silence=0.05:start_threshold=-50dB,areverse,silenceremove=start_periods=1:start_silence=0.05:start_threshold=-50dB,areverse" "clean_$f" 2>/dev/null
  
  mv "clean_$f" "$f"
  rm -f "tmp_$f"
done

echo "=== Listo! Todos los sonidos normalizados ==="
ls -la *.mp3
```

---

## PARTE 2: ANIMACIONES LOTTIE (Sí, VALE LA PENA integrarlas)

### 2.1 Por Qué SÍ Deberías Usar Lottie

Tu guía dice "Lottie no se usa, sáltalo". Esto es un ERROR para la percepción de calidad. Aquí va por qué:

| Sin Lottie | Con Lottie |
|-----------|-----------|
| Respuesta correcta → texto "¡Correcto!" estático | Respuesta correcta → ✨ estrella explotando + confetti animado |
| Level up → snackbar genérico | Level up → ⬆️ flecha dorada ascendiendo con partículas |
| Combo x5 → número cambia | Combo x5 → 🔥 llamas animadas rodeando el contador |
| Cargando → CircularProgressIndicator | Cargando → ⚔️ espadas cruzándose con brillo |
| Pantalla vacía → texto "No hay datos" | Pantalla vacía → 📚 libro abierto con páginas pasando |

**Lottie es GRATIS, pesa ~5-50KB por animación (vs 500KB+ un GIF), y corre a 60fps.** Ya tienes el paquete en `pubspec.yaml`. Solo necesitas los archivos JSON y 3-5 líneas de código Dart.

### 2.2 Las 10 Animaciones que TU APP Necesita (en orden de impacto)

Todas descargables gratis desde https://lottiefiles.com/free-animations

| # | Animación | Dónde se usa | Buscar en LottieFiles | Archivo sugerido | Tamaño aprox |
|---|-----------|-------------|----------------------|------------------|-------------|
| 1 | **Confetti / Celebración** | Respuesta correcta, completar lección, ganar batalla | `"confetti"` o `"celebration"` | `confetti.json` | ~15KB |
| 2 | **Fuego / Llamas** | Combo fire, racha activa | `"fire"` o `"flame loop"` | `fire.json` | ~20KB |
| 3 | **Estrella / Sparkle** | Ganar XP, achievement desbloqueado | `"star sparkle"` o `"star burst"` | `star_burst.json` | ~10KB |
| 4 | **Level Up / Flecha arriba** | Subir de nivel | `"level up"` o `"arrow up glow"` | `level_up.json` | ~12KB |
| 5 | **Checkmark animado** | Respuesta correcta (alternativa a confetti) | `"success check"` o `"checkmark animated"` | `correct_check.json` | ~8KB |
| 6 | **X / Cruz animada** | Respuesta incorrecta | `"error cross"` o `"wrong x"` | `wrong_x.json` | ~8KB |
| 7 | **Espadas cruzadas** | Inicio de batalla | `"swords crossed"` o `"battle start"` | `battle_start.json` | ~25KB |
| 8 | **Monedas cayendo** | Ganar oro | `"coins falling"` o `"gold coins"` | `coins.json` | ~18KB |
| 9 | **Loading RPG** | Pantallas de carga | `"loading game"` o `"loading sword"` | `loading.json` | ~15KB |
| 10 | **Corazón latiendo** | Sistema de vidas/corazones | `"heart beat"` o `"heart pulse"` | `heart_pulse.json` | ~10KB |

**Total: ~141KB** para transformar completamente la experiencia visual. Eso es menos que UNA foto de perfil.

### 2.3 Implementación en Flutter (Copy-Paste Ready)

#### Paso 1: Los archivos van en `apps/mobile/assets/animations/`

```
assets/
  animations/
    confetti.json
    fire.json
    star_burst.json
    level_up.json
    correct_check.json
    wrong_x.json
    battle_start.json
    coins.json
    loading.json
    heart_pulse.json
```

#### Paso 2: Verificar en `pubspec.yaml` (ya debería estar)

```yaml
flutter:
  assets:
    - assets/animations/
```

#### Paso 3: Widget reutilizable para toda la app

```dart
// lib/widgets/lottie_overlay.dart
import 'package:flutter/material.dart';
import 'package:lottie/lottie.dart';

/// Overlay animado que se muestra sobre el contenido y desaparece solo.
/// Úsalo para feedback visual instantáneo.
class LottieOverlay extends StatefulWidget {
  final String animationAsset; // ej: 'assets/animations/confetti.json'
  final double size;
  final Duration duration;
  final VoidCallback? onComplete;

  const LottieOverlay({
    super.key,
    required this.animationAsset,
    this.size = 200,
    this.duration = const Duration(milliseconds: 1500),
    this.onComplete,
  });

  @override
  State<LottieOverlay> createState() => _LottieOverlayState();
}

class _LottieOverlayState extends State<LottieOverlay>
    with SingleTickerProviderStateMixin {
  late final AnimationController _controller;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: widget.duration,
    );
    _controller.forward().then((_) {
      widget.onComplete?.call();
    });
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return IgnorePointer(
      child: Center(
        child: Lottie.asset(
          widget.animationAsset,
          controller: _controller,
          width: widget.size,
          height: widget.size,
          fit: BoxFit.contain,
        ),
      ),
    );
  }
}

/// Función helper para mostrar Lottie como overlay en cualquier pantalla
void showLottieOverlay(BuildContext context, String asset, {double size = 200}) {
  final overlay = OverlayEntry(
    builder: (context) => Positioned.fill(
      child: LottieOverlay(
        animationAsset: asset,
        size: size,
        onComplete: () {}, // Se remueve abajo
      ),
    ),
  );

  Overlay.of(context).insert(overlay);

  Future.delayed(const Duration(milliseconds: 1800), () {
    overlay.remove();
  });
}
```

#### Paso 4: Uso en tu código existente

```dart
// En el handler de respuesta correcta:
void onCorrectAnswer() {
  // Sonido
  soundService.play('ding.mp3');
  
  // Animación Lottie — UNA LÍNEA
  showLottieOverlay(context, 'assets/animations/correct_check.json');
  
  // Si es combo...
  if (currentCombo >= 5) {
    showLottieOverlay(context, 'assets/animations/fire.json', size: 300);
  }
}

// En level up:
void onLevelUp() {
  soundService.play('levelup.mp3');
  showLottieOverlay(context, 'assets/animations/level_up.json', size: 250);
}

// En ganar batalla:
void onBattleVictory() {
  soundService.play('victory.mp3');
  showLottieOverlay(context, 'assets/animations/confetti.json', size: 400);
}

// En ganar monedas:
void onGoldEarned() {
  soundService.play('coin.mp3');
  showLottieOverlay(context, 'assets/animations/coins.json');
}
```

### 2.4 Lottie Avanzado: Fuego Persistente en Rachas

Para el efecto de "fuego" que rodea el UI cuando tienes racha activa:

```dart
// Widget que muestra fuego continuo mientras hay racha
class StreakFireWidget extends StatelessWidget {
  final int streakCount;
  final Widget child;

  const StreakFireWidget({
    super.key,
    required this.streakCount,
    required this.child,
  });

  @override
  Widget build(BuildContext context) {
    if (streakCount < 3) return child;
    
    return Stack(
      children: [
        child,
        // Fuego en los bordes
        if (streakCount >= 3)
          Positioned(
            bottom: 0,
            left: 0,
            right: 0,
            child: Opacity(
              opacity: (streakCount / 10).clamp(0.3, 0.8),
              child: Lottie.asset(
                'assets/animations/fire.json',
                height: 60,
                fit: BoxFit.fitWidth,
                repeat: true, // Loop infinito
              ),
            ),
          ),
      ],
    );
  }
}
```

---

## PARTE 3: IMÁGENES Y ASSETS VISUALES

### 3.1 App Icon — Guía Profesional

Tu ícono es lo PRIMERO que ve el usuario en Play Store. Invierte 30 minutos aquí, no 15.

**Qué funciona en Play Store Colombia (educación + gaming):**
- Colores fuertes: azul oscuro + dorado, o morado + amarillo
- UN símbolo claro (libro + espada, cerebro + escudo, graduación + gaming)
- Texto MÍNIMO (máximo 2-3 letras, ej: "IL" de ICFES Leveling)
- Bordes redondeados (Android adaptive icon)

**Herramientas GRATIS para el ícono:**

| Herramienta | Nivel | URL |
|-------------|-------|-----|
| Canva (templates) | Fácil | https://www.canva.com/create/logos/ |
| Microsoft Designer | Fácil + AI | https://designer.microsoft.com/ |
| Figma (gratis) | Medio | https://www.figma.com |
| IconKitchen | Fácil (adaptive) | https://icon.kitchen |

**Proceso recomendado:**
1. Genera el concepto en Microsoft Designer o Canva con AI: prompt `"Mobile game icon, open book with a glowing sword, dark blue and gold, RPG style, flat design, app icon"`
2. Refina en Canva (quita elementos que sobran)
3. Exporta a 1024x1024 PNG con fondo sólido (NO transparente)
4. Pasa por IconKitchen para generar todos los tamaños Android adaptive

### 3.2 Splash Screen

```yaml
# En pubspec.yaml (flutter_native_splash)
flutter_native_splash:
  color: "#1A1A2E"  # Fondo oscuro RPG
  image: assets/icons/splash_logo.png  # Tu logo centrado, 400x400px
  android_12:
    color: "#1A1A2E"
    icon_background_color: "#1A1A2E"
    image: assets/icons/splash_icon.png  # 288x288px para Android 12+
```

### 3.3 Assets In-App que Necesitas

| Asset | Tamaño | Para qué | Dónde conseguir gratis |
|-------|--------|----------|----------------------|
| Avatares de personaje (5-10) | 128x128px | Perfil del usuario, sistema RPG | https://craftpix.net/freebies/ — buscar "character portrait" |
| Fondos de materia (5) | 400x200px | Headers de cada materia ICFES | Canva templates → gradientes temáticos |
| Íconos de materia (5) | 64x64px | Navegación, selección de materia | https://www.flaticon.com (gratis con atribución) |
| Monstruos/Enemigos (10-15) | 256x256px | Sistema de batalla RPG | https://craftpix.net/freebies/ → "monster sprite" |
| Items/Rewards (10) | 64x64px | Tienda, inventario, rewards | https://opengameart.org → buscar "RPG items" |
| Badges/Logros (10) | 128x128px | Sistema de achievements | Canva → buscar "badge template gaming" |
| Empty states (3) | 300x300px | Cuando no hay datos | https://undraw.co/illustrations (gratis, SVG) |

**Formato recomendado:** PNG para sprites con transparencia, WebP para fondos (50% menos peso).

### 3.4 Paleta de Colores Recomendada (Dark RPG Theme)

```dart
// lib/theme/app_colors.dart
class AppColors {
  // Fondos
  static const background = Color(0xFF0F0F1A);      // Negro azulado profundo
  static const surface = Color(0xFF1A1A2E);          // Panel oscuro  
  static const card = Color(0xFF16213E);             // Card elevado
  
  // Primarios
  static const primary = Color(0xFF4A90D9);          // Azul héroe
  static const primaryLight = Color(0xFF7EB8FF);     // Azul hover
  
  // Acentos por materia
  static const matematicas = Color(0xFF4CAF50);      // Verde
  static const lecturaCritica = Color(0xFFFF9800);   // Naranja
  static const ciencias = Color(0xFF2196F3);         // Azul
  static const sociales = Color(0xFFE91E63);         // Rosa
  static const ingles = Color(0xFF9C27B0);           // Morado
  
  // Feedback
  static const correct = Color(0xFF00E676);          // Verde neón
  static const incorrect = Color(0xFFFF1744);        // Rojo brillante
  static const gold = Color(0xFFFFD700);             // Oro
  static const xp = Color(0xFF7C4DFF);              // Morado XP
  
  // Combo progression
  static const combo2 = Color(0xFF4CAF50);           // Verde
  static const combo3 = Color(0xFFFF9800);           // Naranja
  static const combo5 = Color(0xFFFF5722);           // Rojo naranja
  static const comboFire = Color(0xFFFF1744);        // Rojo fuego
  static const comboLegendary = Color(0xFFFFD700);   // Dorado legendario
}
```

---

## PARTE 4: MICRO-ANIMACIONES FLUTTER (Sin Lottie)

Estas son animaciones que puedes hacer con Flutter puro y que marcan GRAN diferencia:

### 4.1 Shake en Respuesta Incorrecta

```dart
// Agita la tarjeta de pregunta cuando el usuario falla
class ShakeWidget extends StatefulWidget {
  final Widget child;
  final bool shake;
  
  const ShakeWidget({super.key, required this.child, this.shake = false});
  
  @override
  State<ShakeWidget> createState() => ShakeWidgetState();
}

class ShakeWidgetState extends State<ShakeWidget>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  late Animation<double> _animation;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      duration: const Duration(milliseconds: 500),
      vsync: this,
    );
    _animation = TweenSequence<double>([
      TweenSequenceItem(tween: Tween(begin: 0, end: -10), weight: 1),
      TweenSequenceItem(tween: Tween(begin: -10, end: 10), weight: 2),
      TweenSequenceItem(tween: Tween(begin: 10, end: -8), weight: 2),
      TweenSequenceItem(tween: Tween(begin: -8, end: 6), weight: 2),
      TweenSequenceItem(tween: Tween(begin: 6, end: 0), weight: 1),
    ]).animate(CurvedAnimation(parent: _controller, curve: Curves.easeOut));
  }

  void shake() => _controller.forward(from: 0);

  @override
  void didUpdateWidget(ShakeWidget old) {
    super.didUpdateWidget(old);
    if (widget.shake && !old.shake) shake();
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _animation,
      builder: (_, child) => Transform.translate(
        offset: Offset(_animation.value, 0),
        child: child,
      ),
      child: widget.child,
    );
  }
}
```

### 4.2 Pulse en Respuesta Correcta

```dart
// Efecto de "pulso" satisfactorio al acertar
class PulseWidget extends StatefulWidget {
  final Widget child;
  final bool pulse;
  
  const PulseWidget({super.key, required this.child, this.pulse = false});
  
  @override
  State<PulseWidget> createState() => _PulseWidgetState();
}

class _PulseWidgetState extends State<PulseWidget>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      duration: const Duration(milliseconds: 300),
      vsync: this,
      lowerBound: 1.0,
      upperBound: 1.15,
    );
  }

  @override
  void didUpdateWidget(PulseWidget old) {
    super.didUpdateWidget(old);
    if (widget.pulse && !old.pulse) {
      _controller.forward().then((_) => _controller.reverse());
    }
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return ScaleTransition(scale: _controller, child: widget.child);
  }
}
```

### 4.3 XP Counter Animated

```dart
// Contador de XP que sube animado (como Duolingo)
class AnimatedXPCounter extends StatelessWidget {
  final int targetXP;
  final Duration duration;

  const AnimatedXPCounter({
    super.key,
    required this.targetXP,
    this.duration = const Duration(milliseconds: 1200),
  });

  @override
  Widget build(BuildContext context) {
    return TweenAnimationBuilder<int>(
      tween: IntTween(begin: 0, end: targetXP),
      duration: duration,
      curve: Curves.easeOutCubic,
      builder: (_, value, __) => Text(
        '+$value XP',
        style: const TextStyle(
          fontSize: 32,
          fontWeight: FontWeight.bold,
          color: Color(0xFF7C4DFF),
          shadows: [Shadow(color: Color(0x807C4DFF), blurRadius: 12)],
        ),
      ),
    );
  }
}
```

### 4.4 Progress Bar Animada con Glow

```dart
// Barra de progreso con efecto glow que se ilumina al avanzar
class GlowProgressBar extends StatelessWidget {
  final double progress; // 0.0 a 1.0
  final Color color;
  final double height;

  const GlowProgressBar({
    super.key,
    required this.progress,
    this.color = const Color(0xFF4A90D9),
    this.height = 12,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      height: height,
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(height / 2),
        color: Colors.white.withValues(alpha: 0.1),
      ),
      child: AnimatedFractionallySizedBox(
        duration: const Duration(milliseconds: 600),
        curve: Curves.easeOutCubic,
        alignment: Alignment.centerLeft,
        widthFactor: progress.clamp(0.0, 1.0),
        child: Container(
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(height / 2),
            color: color,
            boxShadow: [
              BoxShadow(
                color: color.withValues(alpha: 0.6),
                blurRadius: 8,
                spreadRadius: 1,
              ),
            ],
          ),
        ),
      ),
    );
  }
}
```

---

## PARTE 5: HAPTICS (Vibración) — El Ingrediente Secreto

La vibración táctil es GRATIS y TODOS los Android modernos la soportan. Combínala con sonido para feedback 10x más satisfactorio.

```dart
import 'package:flutter/services.dart';

class HapticsService {
  /// Respuesta correcta — vibración suave de éxito
  static void correct() => HapticFeedback.lightImpact();
  
  /// Respuesta incorrecta — vibración más fuerte
  static void wrong() => HapticFeedback.heavyImpact();
  
  /// Click de botón — vibración mínima
  static void tap() => HapticFeedback.selectionClick();
  
  /// Combo / Level up — patrón doble
  static Future<void> combo() async {
    HapticFeedback.mediumImpact();
    await Future.delayed(const Duration(milliseconds: 100));
    HapticFeedback.mediumImpact();
  }
  
  /// Victoria en batalla — patrón triple ascendente
  static Future<void> victory() async {
    HapticFeedback.lightImpact();
    await Future.delayed(const Duration(milliseconds: 80));
    HapticFeedback.mediumImpact();
    await Future.delayed(const Duration(milliseconds: 80));
    HapticFeedback.heavyImpact();
  }
}

// Uso combinado con sonido:
void onCorrectAnswer() {
  HapticsService.correct();       // Vibración
  soundService.play('ding.mp3');  // Sonido
  showLottieOverlay(context, 'assets/animations/correct_check.json'); // Visual
}
```

---

## PARTE 6: CHECKLIST DE CALIDAD MULTIMEDIA

### Antes de lanzar, verifica cada punto:

```
SONIDO:
[ ] Todos los 22 archivos MP3 existen en assets/sounds/
[ ] Todos normalizados a -14 LUFS
[ ] Ninguno > 1.5 segundos (excepto battle_theme, victory, defeat)
[ ] battle_theme.mp3 hace loop limpio (sin click al repetir)
[ ] Probé con audífonos Y sin audífonos (speaker)
[ ] El sonido de tick.mp3 no suena horrible al reproducirse 20x rápido
[ ] Los combos tienen progresión audible (cada uno suena "más épico")

ANIMACIONES LOTTIE (si las integras):
[ ] Archivos .json en assets/animations/ y declarados en pubspec.yaml
[ ] Ningún archivo Lottie > 100KB
[ ] Las animaciones no bloquean el UI (IgnorePointer)
[ ] Se remueven del overlay después de completarse

IMÁGENES:
[ ] App icon 1024x1024 PNG con fondo sólido
[ ] Splash screen configurado con flutter_native_splash
[ ] Imágenes comprimidas (usa: https://tinypng.com)
[ ] No hay imágenes > 500KB individuales en assets

HAPTICS:
[ ] Feedback táctil en respuesta correcta e incorrecta
[ ] Vibración en level up y achievements
[ ] NO vibración en cada tap de botón (solo selectionClick)

COHERENCIA:
[ ] Todos los sonidos tienen estilo similar (mismo "universo sonoro")
[ ] Los colores de feedback son consistentes (verde=bien, rojo=mal)
[ ] Las animaciones no duran más de 2 segundos para feedback
[ ] El battle_theme no compite en volumen con los sonidos de feedback
```

---

## PARTE 7: BÚSQUEDAS EXACTAS EN PIXABAY (Copy-Paste)

Para que no pierdas tiempo buscando, aquí las búsquedas exactas que mejores resultados dan:

| Archivo | Búsqueda en Pixabay Sound Effects | Backup en Freesound |
|---------|-----------------------------------|---------------------|
| `ding.mp3` | `correct notification` | `correct chime` filtrando CC0 |
| `wrong.mp3` | `wrong answer` | `error buzz short` |
| `fanfare.mp3` | `fanfare short game` | `fanfare trumpet` |
| `tick.mp3` | `tick clock single` | `tick single` (< 0.1s) |
| `levelup.mp3` | `level up game` | `powerup ascending` |
| `combo.mp3` | `combo hit` | `bonus game` |
| `coin.mp3` | `coin collect game` | `coin pickup` |
| `click.mp3` | `button click interface` | `click soft` |
| `whoosh.mp3` | `whoosh short` | `swipe whoosh` |
| `attack.mp3` | `sword slash` | `sword swing` |
| `damage.mp3` | `hit impact` | `punch impact` |
| `victory.mp3` | `victory fanfare game` | `victory trumpet` |
| `defeat.mp3` | `game over sad` | `lose game gentle` |
| `battle_theme.mp3` | Pixabay **Music** → `epic battle game` | OpenGameArt → battle loop |
| `achievement.mp3` | `unlock achievement` | `treasure chest open` |

---

## RESUMEN EJECUTIVO

| Área | Impacto en UX | Costo | Tiempo |
|------|--------------|-------|--------|
| 12 sonidos únicos bien elegidos | ⭐⭐⭐⭐⭐ | $0 | 45 min |
| Normalización + procesamiento audio | ⭐⭐⭐⭐ | $0 | 15 min |
| 5-10 animaciones Lottie | ⭐⭐⭐⭐⭐ | $0 | 30 min (descargar + integrar) |
| Micro-animaciones Flutter (shake, pulse) | ⭐⭐⭐⭐ | $0 | 20 min copiar código |
| Haptics (vibración) | ⭐⭐⭐⭐ | $0 | 10 min |
| App icon profesional | ⭐⭐⭐⭐⭐ | $0 | 30 min |
| Paleta de colores coherente | ⭐⭐⭐ | $0 | 15 min |
| **TOTAL** | **App que se siente $100K** | **$0** | **~3 horas** |

> **La diferencia entre una app que el usuario abre una vez y una que abre todos los días
> NO es el contenido — es cómo se SIENTE usarla.**
>
> Sonido + Animación + Haptics = la tríada de la retención.

---

## PARTE 8: CHECKLIST COMPLETA DE LANZAMIENTO (Verificada 19-Feb-2026)

### ESTADO ACTUAL DEL PROYECTO: ~78%

```
BACKEND (FastAPI)      ████████████████████░  95%   373/373 tests passing
MOBILE CODE (Flutter)  ████████████████████░  95%   Todas las pantallas hechas
MOBILE ASSETS          ██░░░░░░░░░░░░░░░░░░  10%   Faltan iconos, sonidos, animaciones
FIREBASE               ░░░░░░░░░░░░░░░░░░░░   0%   Config files no existen
INFRAESTRUCTURA        ████████████████████░  90%   Docker, CI/CD, Nginx listos
PLAY STORE             ██░░░░░░░░░░░░░░░░░░  10%   Listing no preparado
TESTS BACKEND          ████████████████████  100%   373/373 passing
TESTS MOBILE           ██████████████░░░░░░  70%   119 tests, faltan más
```

---

### TAREA POR TAREA — ESTADO VERIFICADO

#### BLOQUE A: ASSETS MULTIMEDIA (Tu trabajo manual — ~3 horas)

##### A1. App Icon — FALTA
- **Estado:** `assets/icons/` NO EXISTE (la carpeta está vacía)
- **pubspec.yaml** ya lo referencia en línea 115: `image_path: "assets/icons/app_icon.png"`
- **Qué hacer:**
  1. Crear el ícono 1024x1024 con las herramientas de la Parte 3.1 de este documento
  2. Guardar como `apps/mobile/assets/icons/app_icon.png`
  3. Crear versión foreground 512x512 en `apps/mobile/assets/icons/app_icon_foreground.png`
  4. Ejecutar: `cd apps/mobile && dart run flutter_launcher_icons`
- **Verificación:** `ls apps/mobile/android/app/src/main/res/mipmap-*` muestra iconos generados

##### A2. Splash Screen — FALTA
- **Estado:** `assets/icons/splash_logo.png` NO EXISTE
- **pubspec.yaml** ya lo referencia en línea 122
- **Qué hacer:**
  1. Crear logo 400x400 PNG con fondo transparente (tu logo centrado)
  2. Guardar como `apps/mobile/assets/icons/splash_logo.png`
  3. Ejecutar: `cd apps/mobile && dart run flutter_native_splash:create`
- **Verificación:** App muestra splash oscuro (#0A0A0A) con logo al abrir

##### A3. Sonidos (22 MP3s) — FALTA
- **Estado:** `assets/sounds/` tiene SOLO `.gitkeep` (0 archivos de audio)
- **SoundService** ya existe en `lib/core/services/sound_service.dart` (194 líneas) con fallback graceful — NO crashea si faltan archivos
- **Qué hacer:** Descargar de Pixabay (ver Parte 1.2 de este documento) y guardar en `apps/mobile/assets/sounds/`:
  ```
  GRUPO 1 (Feedback básico — 9 archivos):
  [ ] ding.mp3          — respuesta correcta
  [ ] wrong.mp3         — respuesta incorrecta
  [ ] fanfare.mp3       — completar lección/batalla
  [ ] tick.mp3          — conteo de XP
  [ ] levelup.mp3       — subir de nivel
  [ ] combo.mp3         — combo hit
  [ ] coin.mp3          — ganar moneda
  [ ] click.mp3         — tap botón
  [ ] whoosh.mp3        — transición pantallas

  GRUPO 2 (Combos — 5 archivos):
  [ ] combo_2.mp3       — combo x2
  [ ] combo_3.mp3       — combo x3
  [ ] combo_5.mp3       — combo x5
  [ ] combo_fire.mp3    — combo fuego
  [ ] combo_legendary.mp3 — combo legendario

  GRUPO 3 (Extras — 4 archivos):
  [ ] success.mp3       — copia de ding.mp3
  [ ] error.mp3         — copia de wrong.mp3
  [ ] level_up.mp3      — copia de levelup.mp3
  [ ] achievement.mp3   — desbloqueo logro

  GRUPO 4 (Batalla — 5 archivos):
  [ ] attack.mp3        — ataque exitoso
  [ ] damage.mp3        — recibir daño
  [ ] victory.mp3       — ganar batalla
  [ ] defeat.mp3        — perder batalla
  [ ] battle_theme.mp3  — música de fondo batalla (loop 30-60s)
  ```
- **Después de descargar:** Ejecutar script de normalización de la Parte 1.3
- **Verificación:** App reproduce sonido al responder pregunta correcta

##### A4. Animaciones Lottie (10 JSON) — FALTA
- **Estado:** `assets/animations/` NO EXISTE (directorio vacío)
- **Dependencia:** `lottie: ^3.0.0` YA está en pubspec.yaml (línea 39)
- **Widget LottieOverlay:** AÚN NO creado — copiar código de Parte 2.3 de este documento
- **Qué hacer:** Descargar de https://lottiefiles.com/free-animations:
  ```
  [ ] confetti.json       — celebración respuesta correcta
  [ ] fire.json           — combo fire, racha activa
  [ ] star_burst.json     — ganar XP, achievement
  [ ] level_up.json       — subir de nivel
  [ ] correct_check.json  — checkmark animado (respuesta correcta)
  [ ] wrong_x.json        — X animada (respuesta incorrecta)
  [ ] battle_start.json   — inicio de batalla
  [ ] coins.json          — ganar oro
  [ ] loading.json        — pantallas de carga
  [ ] heart_pulse.json    — sistema de corazones
  ```
  Guardar en `apps/mobile/assets/animations/`
- **Después:** Crear `lib/widgets/lottie_overlay.dart` (código en Parte 2.3)
- **Verificación:** Respuesta correcta muestra animación de confetti/check

---

#### BLOQUE B: CONFIGURACIÓN EXTERNA (Tu trabajo en consolas web — ~2.5 horas)

##### B1. Firebase Setup — FALTA
- **Estado:**
  - `google-services.json` NO EXISTE en `android/app/`
  - `firebase_options.dart` NO EXISTE en `lib/`
  - Dependencias YA están en pubspec.yaml: `firebase_core`, `firebase_auth`, `firebase_messaging`
  - La app funciona SIN Firebase (email auth + demo mode) pero Google/Apple Sign-In NO funcionan
- **Qué hacer:**
  1. Ir a https://console.firebase.google.com
  2. Crear proyecto "icfes-leveling"
  3. Agregar app Android con package `com.icfesleveling.icfes_mobile`
  4. Descargar `google-services.json` → `apps/mobile/android/app/`
  5. Agregar app iOS (si aplica), descargar `GoogleService-Info.plist`
  6. Instalar FlutterFire CLI: `dart pub global activate flutterfire_cli`
  7. Ejecutar: `cd apps/mobile && flutterfire configure`
  8. Habilitar proveedores de auth: Email/Password, Google, Apple
  9. Habilitar Cloud Messaging (para push notifications)
- **Verificación:** `flutter build apk --debug` sin errores de Firebase. Login con Google funciona.

##### B2. Privacy Policy + Terms of Service — FALTA
- **Estado:**
  - La app muestra texto "Al continuar, aceptas nuestros Términos de Servicio y Política de Privacidad" (login_page.dart:222) pero NO hay link clickeable
  - NO existen documentos reales (ni HTML, ni MD, ni URLs)
  - **OBLIGATORIO para Play Store** — Google rechaza apps sin privacy policy
- **Qué hacer:**
  1. **Opción rápida (GitHub Pages — GRATIS):**
     - Crear `docs/privacy-policy.md` y `docs/terms-of-service.md` en el repo
     - Activar GitHub Pages en Settings → Pages → Source: main, /docs
     - URLs serán: `https://tuusuario.github.io/IcfesLeveling/privacy-policy`
  2. **Contenido mínimo obligatorio para Colombia:**
     - Quién recopila los datos (tu nombre/empresa)
     - Qué datos recopilas (email, progreso de estudio, scores)
     - Para qué (personalizar experiencia de aprendizaje)
     - Cómo se protegen (cifrado, JWT, no venta a terceros)
     - Derechos del usuario (acceso, rectificación, supresión — Ley 1581 de 2012)
     - Contacto para solicitudes de datos
  3. **Actualizar login_page.dart** para que el texto sea clickeable con `url_launcher`
  4. **Agregar URL en Play Console** → App Content → Privacy Policy
- **Verificación:** Tap en "Política de Privacidad" abre browser con la página

##### B3. Provisionar SSL Certificate — NO VERIFICABLE (servidor)
- **Estado:**
  - Nginx config YA tiene paths de Let's Encrypt configurados para `api.icfesleveling.com`
  - Certificados NO provisionados (necesitan dominio + servidor activo)
- **Qué hacer (en el servidor):**
  ```bash
  # 1. Instalar certbot
  sudo apt install certbot python3-certbot-nginx

  # 2. Obtener certificado
  sudo certbot --nginx -d api.icfesleveling.com

  # 3. Verificar auto-renovación
  sudo certbot renew --dry-run

  # 4. Agregar cron para renovación
  echo "0 3 * * * certbot renew --quiet" | sudo crontab -
  ```
- **Prerequisito:** DNS de `api.icfesleveling.com` apuntando al servidor
- **Verificación:** `curl https://api.icfesleveling.com/health` retorna 200

##### B4. Remover .env del Git — FALTA (SEGURIDAD)
- **Estado:** `.env` ESTÁ tracked en git (confirmado con `git ls-files .env`)
- **Riesgo:** Credenciales de desarrollo expuestas en historial
- **Qué hacer:**
  ```bash
  # 1. Remover del tracking (NO borra el archivo local)
  git rm --cached .env

  # 2. Verificar que .gitignore ya lo incluye (sí lo tiene)
  grep "^\.env$" .gitignore

  # 3. Commit
  git commit -m "Remove .env from tracking (security)"

  # 4. IMPORTANTE: Rotar estos secretos en producción:
  #    - JWT_SECRET → generar nuevo: python -c "import secrets; print(secrets.token_urlsafe(64))"
  #    - SECRET_KEY → generar nuevo
  #    - DATABASE_URL password → cambiar en PostgreSQL
  ```
- **Verificación:** `git ls-files .env` no retorna nada

---

#### BLOQUE C: TAREAS YA COMPLETADAS

##### C1. Wompi Pagos Reales — YA HECHO
- **Estado:** `apps/backend/app/services/wompi_service.py` (561 líneas) con implementación REAL
- **Incluye:**
  - Llamadas reales a `https://production.wompi.co/v1`
  - Creación de links de pago
  - Webhooks con verificación de firma HMAC-SHA256
  - 3 planes: Basic (29,900 COP), Premium (49,900 COP), Elite (99,900 COP)
  - Activación automática de suscripción al pagar
- **Requiere:** Variables de entorno `WOMPI_PUBLIC_KEY`, `WOMPI_PRIVATE_KEY`, `WOMPI_EVENT_SECRET`

##### C2. Sentry Crash Reporting — YA HECHO
- **Mobile:** `sentry_flutter: ^8.0.0` en pubspec.yaml
- **Backend:** `sentry-sdk[fastapi]>=1.40.0` en requirements.txt
- **Requiere:** `SENTRY_DSN` en variables de entorno (opcional, no crashea sin él)

##### C3. Android Release Signing — YA CONFIGURADO
- **Estado:** `android/app/build.gradle` tiene signing config con `key.properties`
- **Minification:** enabled, **Shrink resources:** enabled
- **key.properties** correctamente en `.gitignore`
- **Falta:** Generar el keystore real para producción:
  ```bash
  cd apps/mobile/android
  keytool -genkey -v -keystore release-keystore.jks -keyalg RSA -keysize 2048 -validity 10000 -alias upload

  # Crear key.properties:
  echo "storePassword=TU_PASSWORD
  keyPassword=TU_PASSWORD
  keyAlias=upload
  storeFile=../release-keystore.jks" > key.properties
  ```

##### C4. Sound Service con Fallback — YA HECHO
- **Estado:** `lib/core/services/sound_service.dart` (194 líneas) con try-catch en:
  - Preload (no crashea si falta archivo)
  - Playback (no interrumpe si falla)
  - Lazy-loading (intenta cargar on-demand)
- **Solo falta:** Los archivos MP3 reales (ver A3)

##### C5. Tests Backend — YA HECHO
- **Estado:** 373/373 tests passing
- **Cobertura:** auth, diagnostic, study plans, practice, hearts, streak, economy, boss raid, leagues, mastery, middleware, personality, scheduled tasks, health, e2e flows

##### C6. Tests Mobile — PARCIAL (119 tests existen)
- **Estado:** 7 archivos de test, ~119 test cases reales
- **Archivos existentes:**
  - `test/widget/pages/login_page_test.dart` — 23 tests (UI rendering, interactions, loading, errors)
  - `test/widget/pages/home_page_test.dart` — 22 tests (UI, pull-to-refresh, navigation, state)
  - `test/unit/providers/auth_provider_test.dart` — 15 tests (AuthState, AuthNotifier)
  - `test/unit/providers/practice_provider_test.dart` — 29 tests (sessions, answers, combos, XP)
  - `test/unit/providers/engagement_provider_test.dart` — 23 tests (XP, streak, grace mode, hearts)
  - `test/unit/heart_system_test.dart` — 7 tests (hearts, grace mode — 1 test incompleto)
  - `test/widget_test.dart` — 4 tests (boilerplate Flutter)
- **Falta:** Tests para boss_raid, leagues, diagnostic, streak_provider, sound_service, sync_manager

##### C7. Infraestructura Docker/CI/CD — YA HECHO
- Docker Compose dev + prod con resource limits, log rotation
- 5 GitHub Actions workflows (backend-ci, deploy-prod, flutter-ci, release-android, release-ios)
- Nginx con SSL config, security headers, rate limiting
- Scripts: deploy.sh, backup.sh, restore.sh
- Alembic migrations configurado con 15+ migraciones
- .env.example + .env.production.example documentados

---

#### BLOQUE D: MEJORAS POST-LANZAMIENTO (Opcionales)

##### D1. AdMob Rewarded Ads — PARCIAL
- **Backend:** `apps/backend/app/services/admob_service.py` (211 líneas) con Server-Side Verification REAL
- **Mobile:** NO configurado — falta:
  1. Agregar `google_mobile_ads: ^5.1.0` a pubspec.yaml
  2. Crear `lib/core/services/admob_service.dart` con:
     - `initialize()` → `MobileAds.instance.initialize()`
     - `showRewardedAd()` → cargar, mostrar, callback onRewarded
  3. Agregar AdMob App ID en `AndroidManifest.xml`:
     ```xml
     <meta-data android:name="com.google.android.gms.ads.APPLICATION_ID"
                android:value="ca-app-pub-XXXXXXXXXXXXXXXX~XXXXXXXXXX"/>
     ```
  4. Conectar botones "VER ANUNCIO" en streak_repair y heart_refill
- **Tiempo:** ~4 horas

##### D2. Firebase Analytics — FALTA
- **Estado:** NO está en pubspec.yaml (usa Sentry en su lugar)
- **Qué hacer (si quieres analytics además de crash reporting):**
  1. Agregar `firebase_analytics: ^11.0.0` a pubspec.yaml
  2. Crear `lib/core/services/analytics_service.dart`
  3. Eventos clave: `practice_complete`, `diagnostic_complete`, `level_up`, `purchase`, `streak_day`
- **Tiempo:** ~2 horas

##### D3. Push Notifications (FCM) — PARCIAL
- **Dependencias:** `firebase_messaging: ^15.0.0` y `flutter_local_notifications: ^17.0.0` YA en pubspec.yaml
- **Backend:** `notification_service.py` existe con lógica de envío
- **Falta:** Firebase config (ver B1) — sin `google-services.json` no funcionan
- **Tiempo:** 30 min después de completar B1

##### D4. Prometheus + Grafana — PARCIAL
- **Backend:** `prometheus-client==0.19.0` instalado en requirements.txt
- **Falta:** Agregar servicios prometheus + grafana a docker-compose.prod.yml
- **Tiempo:** ~3 horas

##### D5. Más Tests Mobile — PARCIAL
- **Faltan tests para:** boss_raid, leagues, diagnostic flow, streak_provider, sound_service, sync_manager
- **Tiempo:** ~4 horas

---

#### BLOQUE E: PLAY STORE (Después de completar A y B)

##### E1. Generar AAB Firmado
```bash
cd apps/mobile

# 1. Asegurar que assets existen
ls assets/icons/app_icon.png
ls assets/sounds/ding.mp3
ls assets/animations/confetti.json

# 2. Generar iconos y splash
dart run flutter_launcher_icons
dart run flutter_native_splash:create

# 3. Build release
flutter build appbundle --release

# 4. El AAB estará en:
# build/app/outputs/bundle/release/app-release.aab
```

##### E2. Preparar Listing de Play Store
```
[ ] Feature Graphic (1024x500 PNG) — banner principal
[ ] Ícono ya generado por flutter_launcher_icons
[ ] 4-8 Screenshots de la app (1080x1920 o 1920x1080)
    - Pantalla de login/onboarding
    - Diagnóstico en progreso
    - Sesión de práctica con combo
    - Boss Raid
    - Leaderboard/Leagues
    - Perfil con stats
    - Plan de estudio
    - Tienda
[ ] Descripción corta (80 chars):
    "Prepara el ICFES jugando: RPG educativo con IA y planes personalizados"
[ ] Descripción larga (4000 chars): Features, cómo funciona, materias cubiertas
[ ] Categoría: Education
[ ] Content rating: IARC (completar cuestionario en Play Console)
[ ] Data safety form: Qué datos recopilas y cómo
[ ] Privacy Policy URL: (de B2)
[ ] Target audience: 13+ (estudiantes ICFES)
[ ] Países: Colombia (principal), luego expandir
```

---

### RESUMEN FINAL — RUTA CRÍTICA A PLAY STORE

```
DÍA 1 (3 horas TU trabajo manual):
  ├── A1. Crear app icon (30 min)
  ├── A2. Crear splash logo (15 min)
  ├── A3. Descargar 22 sonidos de Pixabay (45 min)
  ├── A4. Descargar 10 animaciones de LottieFiles (30 min)
  └── B4. git rm --cached .env (5 min)

DÍA 2 (2.5 horas configuración):
  ├── B1. Firebase Console setup (1 hora)
  ├── B2. Privacy Policy + Terms en GitHub Pages (1 hora)
  └── E1. flutter build appbundle --release (30 min)

DÍA 3 (3 horas Play Store):
  ├── E2. Screenshots + Feature Graphic (1.5 horas)
  ├── E2. Llenar listing en Play Console (1 hora)
  └── E2. Submit para revisión (30 min)

TOTAL: ~8.5 horas en 3 días → APP EN PLAY STORE
```

**Lo que NO te bloquea para lanzar (hacer después):**
- AdMob (D1) — lanzar sin ads, agregar en update
- Firebase Analytics (D2) — Sentry ya cubre crash reporting
- Más tests mobile (D5) — 119 tests ya existen
- Prometheus/Grafana (D4) — health checks ya funcionan