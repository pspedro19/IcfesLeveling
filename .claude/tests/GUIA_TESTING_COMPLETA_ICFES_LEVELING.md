# GUIA DE TESTING COMPLETA — ICFES Leveling

> **Objetivo:** Probar TODAS las funcionalidades UX de la app antes de publicarla.
> **Filosofia:** Primero automatiza lo que puedas, despues prueba manualmente lo visual/sensorial.
> **Estado actual:** 365 tests passing, 23 skipped, 1 flaky (heart_system Hive race condition)

---

# PARTE 0: HERRAMIENTAS Y SETUP

## 0.1 Stack de Testing para Flutter

| Herramienta | Para que | Estado |
|-------------|----------|--------|
| `flutter_test` | Unit tests + Widget tests | INSTALADO |
| `mockito` | Mocks para servicios (API, etc.) | INSTALADO |
| `hive_test` | Test helpers para Hive boxes | INSTALADO |
| `flutter_animate` | Animaciones (necesita `restartOnHotReload = false`) | INSTALADO |
| `fake_async` | Controlar timers (combos, countdown, etc.) | Viene con Flutter |
| `integration_test` | Tests E2E en dispositivo real/emulador | PENDIENTE |
| `golden_toolkit` | Comparar screenshots pixel a pixel | PENDIENTE |
| `adb` | Capturas de pantalla, logs, grabar pantalla | Requiere Android SDK |

### Dependencias actuales (pubspec.yaml dev_dependencies)

```yaml
dev_dependencies:
  flutter_test:
    sdk: flutter
  build_runner: ^2.4.8
  riverpod_generator: ^2.4.0
  retrofit_generator: ^8.1.0
  freezed: ^2.5.0
  json_serializable: ^6.7.0
  injectable_generator: ^2.4.0
  hive_generator: ^2.0.0
  mockito: ^5.4.4
  hive_test: ^1.0.1
  flutter_lints: ^3.0.0
  flutter_launcher_icons: ^0.14.1
  flutter_native_splash: ^2.4.0
```

## 0.2 Estructura REAL de carpetas de tests

```
apps/mobile/
├── test/
│   ├── mocks/
│   │   └── mock_providers.dart          # FakeApiClient, test helpers
│   ├── unit/
│   │   ├── heart_system_test.dart       # HeartSystem (5 pass, 1 flaky)
│   │   ├── sync_manager_test.dart       # SyncManager (20 pass)
│   │   └── providers/
│   │       ├── auth_provider_test.dart       # AuthNotifier (12 pass)
│   │       ├── boss_raid_provider_test.dart  # BossRaidNotifier (60+ pass)
│   │       ├── dungeon_provider_test.dart    # DungeonNotifier (20+ pass)
│   │       ├── engagement_provider_test.dart # EngagementNotifier (21 pass)
│   │       ├── leagues_provider_test.dart    # LeaguesNotifier (tests)
│   │       ├── practice_provider_test.dart   # PracticeNotifier (60+ pass)
│   │       ├── shop_provider_test.dart       # ShopNotifier (tests)
│   │       └── streak_provider_test.dart     # StreakNotifier (tests)
│   ├── widget/
│   │   ├── lottie_integration_test.dart      # Lottie system (34 pass)
│   │   └── pages/
│   │       ├── home_page_test.dart           # HomePage (23 skipped - animate timers)
│   │       └── login_page_test.dart          # LoginPage (tests pass)
│   └── widget_test.dart                      # Template smoke test (ignorar)
├── integration_test/                          # NO EXISTE AUN
└── maestro/                                   # NO EXISTE AUN
```

## 0.3 Nombres REALES de clases (vs la guia anterior)

| Guia anterior (INCORRECTO) | Codigo real (CORRECTO) | Ubicacion |
|---------------------------|----------------------|-----------|
| `ComboSystem` | `ComboNotifier` + `ComboService` | `lib/core/services/combo_service.dart` |
| `HeartSystem` | `HeartSystem` | `lib/core/services/heart_system.dart` |
| `calculateXP()` | `ComboService.calculateBonusXP()` | `lib/core/services/combo_service.dart` |
| `sm2Calculate()` | NO EXISTE en mobile | Backend responsibility |
| `SplashScreen` | `SplashPage` | `lib/features/onboarding/presentation/pages/splash_page.dart` |
| `OnboardingScreen` | Multiple pages: `GoalSelectionPage`, `WeakSubjectsPage`, etc. | `lib/features/onboarding/presentation/pages/` |
| `PracticeSessionScreen` | `PracticeSessionPage` | `lib/features/practice/presentation/pages/practice_session_page.dart` |
| `HomeScreen` | `HomePage` | `lib/features/home/presentation/pages/home_page.dart` |
| `ComboOverlay` | `ComboOverlay` | `lib/features/practice/presentation/widgets/combo_overlay.dart` |

**Metodos de ComboNotifier (REALES):**
- `incrementCombo()` — NO `onCorrectAnswer()`
- `resetCombo()` — NO `onWrongAnswer()`

**Metodos de HeartSystem (REALES):**
- `loseHeart()` — NO `useHeart()`
- `restoreHeartViaAd()`
- `restoreHeartsViaGold(int cost)`
- `enterGraceMode()` / `exitGraceMode()`

## 0.4 Mock Infrastructure

La app tiene un sistema de mocks bien armado en `test/mocks/mock_providers.dart`:

- `FakeApiClient` — intercepta HTTP requests con `setMockResponse()`
- `createTestUser()` — factory de usuarios para tests
- `createTestContainer()` — crea ProviderContainer con overrides

---

# PARTE 1: TESTS QUE EXISTEN Y CORREN HOY

## 1.1 Correr todos los tests

```bash
cd apps/mobile

# TODOS los tests:
flutter test

# Con output expandido:
flutter test --reporter expanded

# Resultado esperado: 365+ pass, ~23 skip, 0-1 fail
```

## 1.2 Tests por modulo

```bash
# Providers (285 tests):
flutter test test/unit/providers/

# HeartSystem (5 pass + 1 flaky):
flutter test test/unit/heart_system_test.dart

# SyncManager (20 tests):
flutter test test/unit/sync_manager_test.dart

# Lottie animations (34 tests):
flutter test test/widget/lottie_integration_test.dart

# Login page:
flutter test test/widget/pages/login_page_test.dart

# Home page (23 skipped por flutter_animate timers):
flutter test test/widget/pages/home_page_test.dart
```

## 1.3 Issue conocido: heart_system_test flaky

El test `restoreHeartsViaGold restores hearts` falla intermitentemente por una race condition:
- `HeartSystem._saveState()` intenta escribir a un Hive box que ya se cerro en `tearDown`
- **Fix necesario**: agregar `await` a la operacion de restore antes de cerrar el box

## 1.4 Issue conocido: home_page_test skipped

23 tests estan marcados `skip: true` porque `flutter_animate` usa `Timer(0)` internos
que son incompatibles con `FakeAsync` pending timer checks. Los tests funcionan pero
`pumpAndSettle()` nunca termina por las animaciones en loop.

**Workaround**: usar `tester.pump()` en vez de `pumpAndSettle()` y verificar estado
despues de un numero finito de frames.

---

# PARTE 2: TESTS UNITARIOS A CREAR (Logica pura, sin UI)

Estos tests referencian las clases REALES del codigo.

## 2.1 Sistema de Combos (ComboService)

```dart
// test/unit/combo_service_test.dart
import 'package:flutter_test/flutter_test.dart';
import 'package:icfes_mobile/core/services/combo_service.dart';

void main() {
  group('ComboService', () {
    test('calculateBonusXP returns 0 for combo 0', () {
      expect(ComboService.calculateBonusXP(0), 0);
    });

    test('calculateBonusXP returns combo value for small combos', () {
      expect(ComboService.calculateBonusXP(5), 5);
    });

    test('calculateBonusXP caps at 15', () {
      expect(ComboService.calculateBonusXP(20), 15);
    });

    test('getComboLevel returns correct levels', () {
      expect(ComboService.getComboLevel(0), ComboLevel.none);
      expect(ComboService.getComboLevel(2), ComboLevel.good);
      expect(ComboService.getComboLevel(5), ComboLevel.unstoppable);
      expect(ComboService.getComboLevel(10), ComboLevel.legendary);
    });

    test('getComboDisplay returns Spanish text', () {
      expect(ComboService.getComboDisplay(2), contains('Bien'));
      expect(ComboService.getComboDisplay(5), contains('IMPARABLE'));
    });
  });

  group('ComboNotifier', () {
    test('incrementCombo increases count by 1', () {
      final notifier = ComboNotifier();
      notifier.incrementCombo();
      expect(notifier.debugState.count, 1);
    });

    test('resetCombo sets count to 0', () {
      final notifier = ComboNotifier();
      notifier.incrementCombo();
      notifier.incrementCombo();
      notifier.resetCombo();
      expect(notifier.debugState.count, 0);
    });
  });
}
```

## 2.2 Sistema de Corazones (HeartSystem)

```dart
// test/unit/heart_system_test.dart (ACTUALIZADO)
import 'package:flutter_test/flutter_test.dart';
import 'package:hive_test/hive_test.dart';
import 'package:icfes_mobile/core/services/heart_system.dart';

void main() {
  setUp(() async {
    await setUpHiveTest();
  });

  tearDown(() async {
    // Wait for any pending async operations before closing boxes
    await Future.delayed(const Duration(milliseconds: 50));
    await tearDownHiveTest();
  });

  group('HeartSystem', () {
    test('starts with 5 hearts', () async {
      final hearts = await HeartSystem.initialize();
      expect(hearts.currentHearts, 5);
    });

    test('loseHeart decreases by 1', () async {
      final hearts = await HeartSystem.initialize();
      await hearts.loseHeart();
      expect(hearts.currentHearts, 4);
    });

    test('cannot go below 0', () async {
      final hearts = await HeartSystem.initialize();
      for (int i = 0; i < 10; i++) {
        await hearts.loseHeart();
      }
      expect(hearts.currentHearts, 0);
      expect(hearts.hasHearts, false);
    });

    test('restoreHeartViaAd adds 1 heart', () async {
      final hearts = await HeartSystem.initialize();
      await hearts.loseHeart(); // 4
      await hearts.loseHeart(); // 3
      await hearts.restoreHeartViaAd();
      expect(hearts.currentHearts, 4);
    });

    test('grace mode allows playing with 0 hearts', () async {
      final hearts = await HeartSystem.initialize();
      for (int i = 0; i < 5; i++) await hearts.loseHeart();
      expect(hearts.hasHearts, false);
      hearts.enterGraceMode();
      expect(hearts.isInGraceMode, true);
    });
  });
}
```

---

# PARTE 3: WIDGET TESTS A CREAR

## 3.1 Splash Page

```dart
// test/widget/pages/splash_page_test.dart
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:icfes_mobile/features/onboarding/presentation/pages/splash_page.dart';

void main() {
  setUp(() {
    Animate.restartOnHotReload = false;
  });

  group('SplashPage', () {
    testWidgets('renders without crash', (tester) async {
      await tester.pumpWidget(const MaterialApp(home: SplashPage()));
      await tester.pump();
      // SplashPage should render some content
      expect(find.byType(SplashPage), findsOneWidget);
    });
  });
}
```

## 3.2 Practice Session Page

```dart
// test/widget/pages/practice_session_page_test.dart
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:icfes_mobile/features/practice/presentation/pages/practice_session_page.dart';
import '../../mocks/mock_providers.dart';

void main() {
  setUp(() {
    Animate.restartOnHotReload = false;
  });

  group('PracticeSessionPage', () {
    testWidgets('renders loading state initially', (tester) async {
      final container = createTestContainer();

      await tester.pumpWidget(
        UncontrolledProviderScope(
          container: container,
          child: const MaterialApp(
            home: PracticeSessionPage(subjectId: 'math'),
          ),
        ),
      );
      await tester.pump();

      // Should show some loading indicator
      expect(find.byType(CircularProgressIndicator), findsOneWidget);
    });
  });
}
```

---

# PARTE 4: INTEGRATION TESTS (Requieren emulador — PENDIENTES)

> **Estado:** NO implementados aun. Requiere:
> 1. Android SDK configurado con `flutter doctor` OK
> 2. Emulador corriendo o dispositivo conectado
> 3. Crear carpeta `integration_test/`

### Setup cuando esten listos:

```bash
# Crear directorio
mkdir -p apps/mobile/integration_test

# Correr:
cd apps/mobile
flutter test integration_test/
```

### Flujos prioritarios a testear:

1. **Login flow** — app abre -> splash -> login -> home
2. **Practice flow** — seleccionar materia -> responder preguntas -> ver resultado
3. **Video flow** — tocar video -> ver thumbnail -> abrir YouTube -> marcar como visto

---

# PARTE 5: TESTING MANUAL CHECKLIST

## 5.1 Checklist de Sonido

```
[ ] ding.mp3        — Respuesta correcta
[ ] wrong.mp3       — Respuesta incorrecta
[ ] fanfare.mp3     — Completar leccion
[ ] tick.mp3        — Conteo de XP
[ ] levelup.mp3     — Subir de nivel
[ ] combo.mp3       — Golpe de combo
[ ] coin.mp3        — Ganar oro
[ ] click.mp3       — Tocar boton
[ ] whoosh.mp3      — Transicion

NOTA: Los MP3s aun NO estan en assets/sounds/
Usar scripts/setup-sound-assets.sh para generarlos
```

## 5.2 Checklist de Animaciones Lottie (34 tests automatizados)

```
[x] confetti.json      — TESTEADO automaticamente
[x] fire.json          — TESTEADO (StreakFireLottie widget)
[x] star_burst.json    — TESTEADO
[x] level_up.json      — TESTEADO
[x] correct_check.json — TESTEADO
[x] wrong_x.json       — TESTEADO
[x] battle_start.json  — TESTEADO
[x] coins.json         — TESTEADO
[x] loading.json       — TESTEADO

Verificar manualmente en dispositivo real:
[ ] Animaciones no causan lag/stuttering
[ ] fire.json no consume bateria excesiva en loop
```

## 5.3 Checklist Offline-First

```
[ ] App abre sin internet (muestra datos cacheados)
[ ] Banner naranja aparece: "Sin conexion"
[ ] Puedes responder preguntas offline (cache de Hive)
[ ] Las respuestas se encolan localmente
[ ] Al reconectar -> sync
[ ] XP y progreso se actualizan correctamente post-sync
```

## 5.4 Checklist Pre-Lanzamiento

```
TIER 1 — BLOQUEANTES (si falla -> NO publiques):
[ ] App abre sin crash en 3 dispositivos distintos
[ ] Login funciona (email + Google)
[ ] Las preguntas cargan del backend
[ ] Responder pregunta correcta -> XP sube
[ ] Responder pregunta incorrecta -> corazon baja
[ ] 0 corazones -> no puede practicar (muestra modal)
[ ] Cerrar sesion funciona
[ ] Datos persisten al cerrar y abrir la app

TIER 2 — IMPORTANTES:
[ ] Diagnostico 15 preguntas -> resultados
[ ] Combos suben y bajan correctamente
[ ] Video: thumbnail -> abrir YouTube -> marcar visto -> +10 XP
[ ] Ligas muestran leaderboard
[ ] Plan de estudio se crea y muestra unidades

TIER 3 — NICE TO HAVE:
[ ] Todas las animaciones Lottie se ven
[ ] Modo offline funciona y sincroniza
[ ] Boss Raid multijugador conecta
[ ] Notificaciones push llegan
[ ] Performance >= 60 FPS constante
```

---

# PARTE 6: COMANDOS RAPIDOS

```bash
# ============================================
# CORRER TESTS
# ============================================

cd apps/mobile

# TODOS (resultado esperado: 365+ pass, ~23 skip, 0-1 fail):
flutter test

# Solo providers (rapido, 285 tests):
flutter test test/unit/providers/

# Solo lottie (34 tests):
flutter test test/widget/lottie_integration_test.dart

# Solo login widget:
flutter test test/widget/pages/login_page_test.dart

# Con cobertura:
flutter test --coverage
# Genera: coverage/lcov.info

# ============================================
# COMPATIBILIDAD FLUTTER 3.41.1
# ============================================

# Fixes aplicados:
# - intl: ^0.20.2 (requerido por flutter_localizations)
# - google_fonts: ^8.0.0 (FontWeight constant map fix)
# - CardTheme -> CardThemeData en app_theme.dart
# - skip: String -> skip: bool en testWidgets()
# - hive_test: ^1.0.1 agregado a dev_dependencies
```

---

# PARTE 7: QUE FALTA POR IMPLEMENTAR

| Item | Prioridad | Esfuerzo |
|------|-----------|----------|
| Fix heart_system_test race condition | Alta | 30 min |
| Unskip home_page_tests (usar pump() en vez de pumpAndSettle()) | Media | 1 hora |
| Widget test para SplashPage | Media | 30 min |
| Widget test para PracticeSessionPage | Media | 1 hora |
| Widget test para ComboOverlay | Media | 30 min |
| Integration tests (requiere emulador) | Baja (pre-release) | 3 horas |
| Golden tests (screenshots) | Baja | 2 horas |
| Maestro E2E tests | Baja (pre-release) | 3 horas |
