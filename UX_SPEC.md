# UX Specification: ICFES Leveling Mobile App

**Version:** 1.0
**Date:** 2026-02-19
**App Type:** Gamified educational mobile app (Flutter) for Colombian ICFES exam prep
**Aesthetic:** RPG / Anime (Solo Leveling style) -- dark backgrounds, neon accents, rank-based progression
**Backend:** FastAPI + PostgreSQL (Supabase)

---

## Summary

This document catalogs **18 UX gaps** between the intended user experience and the current implementation. Each gap includes the expected behavior, current implementation status, affected files, and priority classification.

### Priority Legend

| Priority | Meaning | Guideline |
|----------|---------|-----------|
| **P0** | Blocker -- security or data-loss risk | Must fix before any public release |
| **P1** | Important -- core UX loop is broken or missing | Fix in next sprint |
| **P2** | Nice-to-have -- polish, delight, or secondary features | Schedule when bandwidth allows |

### Status at a Glance

| # | Gap | Priority | Status |
|---|-----|----------|--------|
| 4 | FlutterSecureStorage for JWT | P0 | **Implemented** |
| 1 | Value Prop Slides (3 swipeable) | P1 | **Implemented** |
| 2 | Demo Mode (no backend) | P1 | **Implemented** |
| 5 | Post-Diagnostic Mission Screen | P1 | **Implemented** |
| 6 | Global AppBar with Hearts/Streak/Gold | P1 | **Partial** |
| 7 | Home Loss Alerts | P1 | **Implemented** |
| 10 | Store 3 Tabs | P1 | **Implemented** |
| 14 | Haptic Feedback | P1 | **Partial** |
| 15 | Sound Effects | P1 | **Partial** |
| 16 | Push Notifications | P1 | **Partial** |
| 17 | Retry with Exponential Backoff | P1 | **Implemented** |
| 3 | RPG Auth Aesthetics | P2 | **Partial** |
| 8 | Dungeon S-Map with 5 Nodes | P2 | **Implemented** |
| 9 | Boss Raid Visual Phases | P2 | **Partial** |
| 11 | Stats 3 Tabs | P2 | **Implemented** |
| 12 | Achievements 6 Categories + 4 Rarities | P2 | **Implemented** |
| 13 | Developer Mode (7 taps) | P2 | **Implemented** |
| 18 | Known Issues / Tech Debt Section | P2 | **Missing** |

**Totals:** 10 Implemented, 6 Partial, 2 Missing

---

## P0 -- Blockers

### Gap 4: FlutterSecureStorage for JWT Tokens

**What it should do:**
JWT access tokens and refresh tokens must be stored in `FlutterSecureStorage` (which uses the OS keychain/keystore), NOT in Hive or SharedPreferences. Tokens are sensitive credentials; storing them in plaintext local storage is a security vulnerability on rooted/jailbroken devices.

**Current Status: IMPLEMENTED**

The `AuthLocalDataSource` at `apps/mobile/lib/core/auth/data/datasources/auth_local_datasource.dart` already uses `FlutterSecureStorage` for token storage:
- `saveTokens()` writes to `_secureStorage.write(key: _tokenKey, ...)`
- `getAccessToken()` reads from `_secureStorage.read(key: _tokenKey)`
- `getRefreshToken()` reads from `_secureStorage.read(key: _refreshKey)`
- `clearTokens()` deletes from secure storage

The `ApiClient` at `apps/mobile/lib/core/network/api_client.dart` correctly initializes a `secureStorageProvider` of type `FlutterSecureStorage` and injects it into `AuthLocalDataSource`.

User profile data (non-sensitive) is cached in Hive, which is acceptable.

**Remaining Work:** None. Implementation is correct.

**Files:**
- `apps/mobile/lib/core/auth/data/datasources/auth_local_datasource.dart` -- tokens in FlutterSecureStorage, user cache in Hive
- `apps/mobile/lib/core/network/api_client.dart` -- provider wiring

---

## P1 -- Important

### Gap 1: Value Prop Slides (3 Swipeable)

**What it should look like:**
Before the onboarding flow begins, 3 swipeable full-screen slides introduce the app's value proposition:
1. "Sube tu Rango" -- rank progression visual (E to S)
2. "Compite en Ligas" -- weekly league leaderboard visual
3. "Domina cada Tema" -- radar chart mastery visual

Each slide has an animated illustration, a SKIP button (top right), dot indicators, and a SIGUIENTE/COMENZAR button. The last slide's button says "COMENZAR" and navigates to login.

**Current Status: IMPLEMENTED**

The file `apps/mobile/lib/features/onboarding/presentation/pages/value_prop_page.dart` contains a complete `ValuePropPage` with:
- `PageView.builder` with 3 slides matching the exact titles
- Custom animations per slide: `_RankAnimation` (rank hexagon with particles), `_LeagueAnimation` (leaderboard rows), `_MasteryAnimation` (radar chart via `RadarPainter`)
- SALTAR button (top right), animated dot indicators, SIGUIENTE/COMENZAR CTA
- On finish, calls `onboardingProvider.notifier.markValuePropSeen()` and navigates to login

**Remaining Work:**
- The radar chart in `_MasteryAnimation` uses a simplified `RadarPainter` with hardcoded polygon vertices. Could be improved with proper 5-axis data-driven rendering.
- Consider adding Lottie or Rive animations for higher polish.

**Files:**
- `apps/mobile/lib/features/onboarding/presentation/pages/value_prop_page.dart`
- `apps/mobile/lib/core/services/onboarding_service.dart` (state management)

---

### Gap 2: Demo Mode (No Backend)

**What it should do:**
The login screen includes a "Modo Demo" button that lets the user explore the app without requiring a backend connection or Firebase. This is critical for:
- First-time users evaluating the app on flaky connections
- Developers testing UI without spinning up the backend
- App Store reviewers

The demo mode should create a local mock user with sample data (level 5, 1250 XP, rank E, 5 hearts, streak of 3).

**Current Status: IMPLEMENTED**

The `LoginPage` has a green "MODO DESARROLLADOR" button that calls `_handleGuestSignIn()`, which invokes `authProvider.notifier.enterDemoMode()`.

In `auth_provider.dart`, `enterDemoMode()`:
1. First tries to log in with a hardcoded demo account (`demo_hunter` / `Demo123#`) against the real backend (5s timeout)
2. If that fails, tries to register the demo account and then log in
3. If the backend is completely unavailable, falls back to `_enterLocalDemoMode()` which creates a local `User` object with mock data

**Remaining Work:**
- The button label says "MODO DESARROLLADOR" but should say "MODO DEMO" for end users. "Desarrollador" implies a hidden feature; "Demo" is user-friendly.
- The subtitle says "Explora la app sin conexion" -- consider "Explora sin cuenta ni conexion".
- When in local demo mode, screens that fetch from the backend will show errors. Need mock data providers or graceful empty states for: stats, achievements, dungeon, boss raid, study plan, leagues.
- Demo mode should be clearly indicated in the UI (e.g., a persistent banner: "Modo Demo -- Los datos no se guardan").

**Files:**
- `apps/mobile/lib/features/auth/presentation/pages/login_page.dart` -- button label and subtitle
- `apps/mobile/lib/features/auth/presentation/providers/auth_provider.dart` -- `enterDemoMode()` and `_enterLocalDemoMode()`
- Multiple feature providers need demo/offline fallbacks

---

### Gap 5: Post-Diagnostic Mission Screen

**What it should look like:**
After the diagnostic completes and results are revealed, the user sees a "Primera Mision Personalizada" screen. This screen:
- Shows "NUEVA MISION DISPONIBLE" (blue label)
- Displays "EL DESPERTAR DEL CAZADOR" (title)
- Has a mission card showing the user's weakest subject with reward indicators (+50 XP, +20 Oro)
- Primary CTA: "ACEPTAR MISION" (shimmering button) navigates to practice
- Secondary: "IR AL PANEL PRINCIPAL" navigates to home

This is a critical engagement moment -- the user has just finished the diagnostic and needs an immediate next action.

**Current Status: IMPLEMENTED**

The file `apps/mobile/lib/features/onboarding/presentation/pages/first_mission_page.dart` contains a complete `FirstMissionPage` with all the described elements:
- "NUEVA MISION DISPONIBLE" label
- "EL DESPERTAR DEL CAZADOR" title
- Mission card with "Mision de Calibracion" and reward indicators
- Shimmer animation on the "ACEPTAR MISION" button
- Secondary "IR AL PANEL PRINCIPAL" link
- Calls `onboardingProvider.notifier.completeOnboarding()` on either action

**Remaining Work:**
- The mission card hardcodes "Lectura Critica" as the weak subject. Should dynamically use the actual weakest subject from the diagnostic results.
- The reward amounts (+50 XP, +20 Oro) are hardcoded. Should reflect the actual first mission rewards from the backend.
- Missing accent marks in Spanish text ("Mision" should be "Mision" or ideally use the display text "MISION" which avoids the issue).

**Files:**
- `apps/mobile/lib/features/onboarding/presentation/pages/first_mission_page.dart`
- `apps/mobile/lib/features/onboarding/presentation/pages/results_reveal_page.dart` (navigation source)

---

### Gap 6: Global AppBar with Hearts / Streak / Gold

**What it should look like:**
A persistent AppBar (or status bar) on ALL main screens showing:
- Hearts count (e.g., heart icon + "4/5") -- tappable, opens hearts detail/refill modal
- Streak flame (fire icon + "7") -- tappable, shows streak calendar
- Gold balance (coin icon + "320") -- tappable, opens store

This provides constant awareness of the user's key currencies and creates urgency (low hearts = can't practice).

**Current Status: PARTIAL**

The `HomePage` has an `AppBar` with `HeartsDisplay` and `StreakFlame` in the `actions` area. However:
- Gold balance is NOT shown in the AppBar on any screen.
- Only the Home screen shows these widgets. Other screens (Stats, Achievements, Dungeon, Practice, etc.) do not show the global status bar.
- The shared widgets exist: `apps/mobile/lib/shared/widgets/hearts_display.dart`, `streak_flame.dart`, `gold_indicator.dart`, `heart_indicator.dart`

**Required Changes:**
1. Create a shared `GameAppBar` or `GameScaffold` widget that wraps every main screen with hearts, streak, and gold.
2. Alternatively, add the indicators to the `ShellRoute` scaffold so they appear on all tabbed screens.
3. The gold indicator (`gold_indicator.dart`) exists but is not used in any AppBar.

**Files:**
- `apps/mobile/lib/shared/widgets/hearts_display.dart` -- exists
- `apps/mobile/lib/shared/widgets/streak_flame.dart` -- exists
- `apps/mobile/lib/shared/widgets/gold_indicator.dart` -- exists but unused in AppBar
- `apps/mobile/lib/core/config/routes.dart` -- ShellRoute scaffold (add global AppBar here)
- `apps/mobile/lib/features/home/presentation/pages/home_page.dart` -- currently has partial implementation
- **New:** `apps/mobile/lib/shared/widgets/game_app_bar.dart` or integrate into existing shell

---

### Gap 7: Home Loss Alerts

**What it should look like:**
The home screen shows contextual, urgent alert banners based on the user's state:
- **Streak at risk:** "Tu racha de 7 dias se pierde en X horas" (orange banner, tappable to practice)
- **Low hearts:** "Solo te quedan 2 corazones" (red banner, tappable to store)
- **League demotion risk:** "Estas en zona de descenso" (yellow banner, tappable to leagues)
- **Social proof:** "El 72% de cazadores en tu liga ya practicaron hoy" (blue banner)

These banners use loss aversion psychology to drive engagement.

**Current Status: IMPLEMENTED**

The `HomePage` integrates three psychological trigger systems:
1. `lossAversionTriggersProvider` -- renders `LossAversionAlerts` widget (from `apps/mobile/lib/shared/widgets/psychological/loss_aversion_alerts.dart`) with handlers for streak_risk, low_hearts, demotion_risk, and inactivity
2. `socialProofProvider` -- renders `SocialProofBanner` with percentile and league rank
3. `endowedProgressProvider` -- renders `EndowedProgressDisplay` for new users

The `_handleTriggerAction` method routes each trigger type to the correct screen (practice, store, leagues).

**Remaining Work:**
- Verify that `loss_aversion_alerts.dart` renders visually distinct banners per type (colors, icons, urgency levels).
- The `psychological_triggers_provider.dart` service needs to be connected to real backend data (currently may use static/demo data).
- Test that alerts dismiss correctly and don't reappear after the user takes action.

**Files:**
- `apps/mobile/lib/features/home/presentation/pages/home_page.dart` -- integration
- `apps/mobile/lib/shared/widgets/psychological/loss_aversion_alerts.dart` -- alert UI
- `apps/mobile/lib/core/services/psychological_triggers_provider.dart` -- data source

---

### Gap 10: Store 3 Tabs: TIENDA / POWER-UPS / INVENTARIO

**What it should look like:**
The store screen has 3 tabs:
1. **TIENDA** -- browse and purchase items with gold (streak freeze, heart refill, XP boost, hint tokens, shield, double coins, time freeze)
2. **POWER-UPS** -- view active power-ups with remaining duration
3. **INVENTARIO** -- grid of owned items with quantity badges

Each item card shows: icon, name, description, price, and a buy button. Items have rarity tiers (colors).

**Current Status: IMPLEMENTED**

The `ShopPage` at `apps/mobile/lib/features/shop/presentation/pages/shop_page.dart` has:
- `TabController(length: 3)` with 3 tabs
- Imports for `inventory_grid.dart`, `active_powerups_card.dart`, `powerup_inventory.dart`
- Category icon mapping for all item types: streak_freeze, hearts, xp_boost, hint_token, shield, double_coins, time_freezer
- Gold balance display from `balanceProvider`

**Remaining Work:**
- Verify tab labels match spec ("TIENDA" / "POWER-UPS" / "INVENTARIO").
- Confirm the buy flow works end-to-end with the backend `/economy/purchase` endpoint.
- Add haptic feedback on purchase.
- Add purchase confirmation dialog ("Comprar X por Y oro?").

**Files:**
- `apps/mobile/lib/features/shop/presentation/pages/shop_page.dart`
- `apps/mobile/lib/features/shop/presentation/widgets/inventory_grid.dart`
- `apps/mobile/lib/features/shop/presentation/widgets/active_powerups_card.dart`
- `apps/mobile/lib/features/shop/presentation/widgets/powerup_inventory.dart`
- `apps/mobile/lib/features/shop/presentation/providers/shop_provider.dart`

---

### Gap 14: Haptic Feedback

**What it should do:**
Vibration/haptic feedback synchronized with game events:
- **Correct answer:** double pulse (light + medium, 50ms apart)
- **Wrong answer:** single heavy impact
- **Combo milestone (3, 5, 10):** ascending "power up" pattern (light > medium > heavy)
- **Level up:** dramatic escalade (3x light + heavy)
- **Rank up:** epic pattern (4x medium + 2x heavy)
- **Button tap:** selection click
- **Victory:** celebratory pattern (medium + medium + heavy)
- **Heart lost:** heavy impact "pain"

**Current Status: PARTIAL**

The file `apps/mobile/lib/core/services/haptic_patterns.dart` defines a complete `HapticPatterns` class with static methods for all the specified patterns:
- `correctAnswer()`, `wrongAnswer()`, `comboMilestone()`, `levelUp()`, `rankUp()`, `starEarned()`, `victory()`, `defeat()`, `heartLost()`, `buttonTap()`, `confirm()`, `notification()`

All patterns use `HapticFeedback` from `flutter/services.dart`.

**Remaining Work:**
- The `HapticPatterns` class exists but is NOT integrated into the UI flows. Need to call these methods from:
  - `apps/mobile/lib/features/dungeon/presentation/pages/battle_page.dart` (correct/wrong answer, combo)
  - `apps/mobile/lib/features/practice/presentation/pages/boss_raid_battle_page.dart` (attacks, victory)
  - `apps/mobile/lib/shared/widgets/question_card.dart` (answer selection)
  - `apps/mobile/lib/features/engagement/presentation/widgets/mission_complete_toast.dart` (level up)
  - `apps/mobile/lib/shared/widgets/pressable_scale.dart` (button tap)
- Add a user preference toggle (Settings > Haptic Feedback on/off).
- Test on physical Android and iOS devices (haptics don't work on simulators).

**Files:**
- `apps/mobile/lib/core/services/haptic_patterns.dart` -- patterns defined
- Integration needed in battle, practice, question card, and button widgets

---

### Gap 15: Sound Effects

**What it should do:**
Sound effects for key game events, managed by a `SoundService` singleton:
- `ding.mp3` -- correct answer
- `wrong.mp3` -- incorrect answer
- `fanfare.mp3` -- major achievement / lesson complete
- `tick.mp3` -- XP count-up animation
- `levelup.mp3` -- level up celebration
- `combo.mp3` -- combo milestone
- `coin.mp3` -- gold/currency earned
- `click.mp3` -- button click
- `whoosh.mp3` -- transition / swipe

The service preloads essential sounds on startup and supports enable/disable toggle and volume control.

**Current Status: PARTIAL**

The `SoundService` at `apps/mobile/lib/core/services/sound_service.dart` is fully implemented:
- Singleton pattern with `_instance`
- 9 `SoundType` enum values matching the spec
- `_soundPaths` mapping each type to an asset path
- `preloadSounds()` for essential sounds (ding, wrong, tick)
- `playSound()`, `playTickSound()`, `playComboSound()` with intensity
- Volume control and enable/disable toggle

**However**, the `assets/sounds/` directory only contains `.gitkeep` -- no actual MP3 files exist.

**Remaining Work:**
1. **Add 9 MP3 files** to `apps/mobile/assets/sounds/`:
   - `ding.mp3`, `wrong.mp3`, `fanfare.mp3`, `tick.mp3`, `levelup.mp3`, `combo.mp3`, `coin.mp3`, `click.mp3`, `whoosh.mp3`
   - Use royalty-free game sound effects (e.g., from freesound.org, mixkit.co, or generate with jsfxr.app)
   - Keep files small (< 50KB each, mono, 22kHz)
2. Register assets in `pubspec.yaml` under `flutter > assets`.
3. Integrate `SoundService.playSound()` calls into battle, practice, and navigation flows (similar to haptic integration).
4. Add sound enable/disable toggle in Settings page.

**Files:**
- `apps/mobile/lib/core/services/sound_service.dart` -- service implemented
- `apps/mobile/assets/sounds/` -- **missing all 9 MP3 files**
- `apps/mobile/pubspec.yaml` -- verify asset registration

---

### Gap 16: Push Notifications (Specific Triggers)

**What it should do:**
Push notifications for specific game events:
- **Streak at risk:** 3 escalating reminders (6PM, 9PM, 3:30AM) with RPG copy
- **Boss Raid start:** Sunday 10AM ("El Boss Raid ha comenzado")
- **League closing:** Sunday 6PM ("La Liga cierra en 6 horas")
- **Re-engagement:** 3-day, 7-day, 14-day inactivity reminders
- **Daily quest reminders:** Morning, afternoon, evening
- **Daily goal reminders:** Afternoon and end-of-day
- **Achievement unlocked:** Immediate notification

Requires Firebase Cloud Messaging (FCM) for remote push and `flutter_local_notifications` for scheduled local notifications.

**Current Status: PARTIAL**

The `NotificationService` at `apps/mobile/lib/core/services/notification_service.dart` is extensively implemented (1000+ lines):
- All notification channels created for Android (streak, league, boss_raid, re_engagement, daily_quest, achievement, daily_goal, general)
- `scheduleStreakReminder()` with 3 timed reminders and RPG copy
- `scheduleBossRaidReminder()` for Sunday 10AM
- `scheduleLeagueReminder()` for Sunday 6PM
- `scheduleReEngagement()` for 3/7/14 day inactivity
- `scheduleDailyQuestReminders()` with morning/afternoon/evening
- `scheduleDailyGoalReminders()` with afternoon and end-of-day
- `showAchievementNotification()` for immediate display
- Deep linking via payload parsing (`_getRouteFromPayload`)
- Granular per-category enable/disable settings
- FCM integration with token management, foreground handling, and `onMessageOpenedApp`
- `NotificationScheduler` for timezone-aware scheduling
- Notification settings page exists at `apps/mobile/lib/features/settings/presentation/pages/notification_settings_page.dart`

**Remaining Work:**
1. **Firebase project must be configured** with `google-services.json` (Android) and `GoogleService-Info.plist` (iOS) -- these are environment-specific and may not be in the repo.
2. The `notificationServiceProvider` throws `UnimplementedError` and must be overridden in `main.dart` with the `SharedPreferences` instance.
3. Verify that `FirebaseMessaging.instance` is available at runtime (depends on Firebase initialization in `main.dart`).
4. Backend needs to send FCM push notifications server-side for real-time events (boss raid start, achievement unlock). Currently the backend has a generic notification endpoint but may not send FCM messages.
5. Test notification permissions flow on iOS (requires physical device).
6. Verify quiet hours logic works correctly across timezones.

**Files:**
- `apps/mobile/lib/core/services/notification_service.dart` -- comprehensive implementation
- `apps/mobile/lib/core/services/notification_scheduler.dart` -- scheduling logic
- `apps/mobile/lib/features/settings/presentation/pages/notification_settings_page.dart` -- user settings UI
- `apps/mobile/lib/main.dart` -- Firebase initialization and provider override needed
- Backend: `apps/backend/app/services/notification_service.dart` -- server-side FCM sending

---

### Gap 17: Retry with Exponential Backoff

**What it should do:**
All API calls should retry up to 3 times with exponential backoff:
- 1st retry: 500ms delay
- 2nd retry: 1000ms delay
- 3rd retry: 2000ms delay

Only retry on transient errors (timeouts, 5xx, 429, socket errors). Never retry on 4xx client errors or cancellations.

**Current Status: IMPLEMENTED**

The `RetryInterceptor` at `apps/mobile/lib/core/network/interceptors/retry_interceptor.dart` implements this exactly:
- `maxRetries: 3`, `initialDelay: Duration(milliseconds: 500)`, `backoffFactor: 2.0`
- Retryable status codes: `{408, 429, 500, 502, 503, 504}`
- Retries on: `connectionTimeout`, `sendTimeout`, `receiveTimeout`, `connectionError`, `SocketException`
- Does NOT retry on: `cancel`, 4xx errors
- `_calculateDelay()` implements exponential backoff: `initialDelay * (backoffFactor ^ retryCount)`
- Debug logging shows retry count and delay
- Integrated into `ApiClient` interceptor chain

The `ApiClient` at `apps/mobile/lib/core/network/api_client.dart` includes the interceptor:
```dart
RetryInterceptor(
  dio: _dio,
  maxRetries: 3,
  initialDelay: const Duration(milliseconds: 500),
),
```

**Remaining Work:** None. Implementation matches spec exactly.

**Files:**
- `apps/mobile/lib/core/network/interceptors/retry_interceptor.dart`
- `apps/mobile/lib/core/network/api_client.dart`

---

## P2 -- Nice-to-Have

### Gap 3: RPG Auth Aesthetics

**What it should look like:**
The auth screens should feel like entering a game world:
- **Login page:** Title reads "EL SISTEMA TE BUSCA" with fingerprint icon, hunter metaphors in subtitles, "DESPERTAR" as the primary action label
- **Register page:** Title reads "UNETE A LA CACERIA", field labels use hunter terminology ("Nombre de Cazador"), register button says "DESPERTAR"
- **Visual:** Dark background (0xFF0A0A0A), animated blue accent circles, shimmer effects

**Current Status: PARTIAL**

The `LoginPage` already has:
- "EL SISTEMA TE BUSCA" title (line 121)
- Fingerprint icon in a circular border (line 110-115)
- "Conectando con el Sistema..." loading text
- "Inicia sesion para registrar tu progreso y reclamar tus recompensas de cazador" subtitle
- Dark background with animated blue accent circles
- Social login buttons (Google, Apple) + email form

The `RegisterPage` already has:
- "UNETE A LA CACERIA" title
- "Nombre de Cazador" field label
- "DESPERTAR" button label
- Dark background with animations

**Remaining Work:**
- The login page's email login button says "INICIAR SESION" instead of "DESPERTAR" -- change to match the RPG theme.
- The email form fields use generic labels ("Email", "Contrasena") -- consider "Correo del Cazador" and "Clave Secreta" for thematic consistency.
- The demo mode button says "MODO DESARROLLADOR" -- should say "MODO DEMO" or "EXPLORAR SIN CUENTA".

**Files:**
- `apps/mobile/lib/features/auth/presentation/pages/login_page.dart`
- `apps/mobile/lib/features/auth/presentation/pages/register_page.dart`

---

### Gap 8: Dungeon S-Map with 5 Nodes

**What it should look like:**
A visual S-shaped map with 5 nodes from bottom to top:
- **Node types:** Combat (shield icon, blue), Treasure (chest icon, amber), Boss (fire icon, red, 1.3x scale)
- **Node states:**
  - Locked: grey, lock icon, no glow
  - Active/Current: pulsing glow, "BATTLE!" label below
  - Completed: check icon, 1-3 star rating below
- **Connections:** Lines between nodes -- blue (completed), grey dashed (locked)
- **Header:** Gate name, difficulty rank badge, timer, completion percentage
- **Background:** Theme-based image (dark dungeon aesthetic)

**Current Status: IMPLEMENTED**

The `DungeonMapPage` at `apps/mobile/lib/features/dungeon/presentation/pages/dungeon_map_page.dart` implements all of this:
- S-shaped positions via `_getNodePosition()`: Bottom(125,420) > Left(50,320) > Right(200,220) > Left(50,120) > Top(125,20)
- `_DungeonNodeWidget` handles all node types with correct colors and icons (boss=red/fire, treasure=amber/chest, combat=blue/shield)
- Lock state shows grey with lock icon
- Current node has white border, glow, scale animation, and "BATTLE!" label
- Completed nodes show check icon and 1-3 star rating
- `DungeonPathPainter` draws connection lines (blue=completed, grey=locked)
- `_MapHeader` shows gate name, rank badge, timer, and completion percentage
- Background image with theme-based path and dark overlay
- `PreBattleDialog` shows on tap for unlocked nodes

**Remaining Work:**
- The path lines are straight (`canvas.drawLine`), not curved S-shaped beziers. Consider using `Path` with `quadraticBezierTo` for a smoother S-curve.
- The background image reference `assets/images/map_${gate?.theme ?? 'default'}.png` may not have actual image assets. Falls back to a plain dark container.
- Add scroll support if the map needs more than 5 nodes.

**Files:**
- `apps/mobile/lib/features/dungeon/presentation/pages/dungeon_map_page.dart`
- `apps/mobile/lib/features/dungeon/domain/entities/dungeon_node.dart`
- `apps/mobile/lib/features/dungeon/domain/entities/dungeon_gate.dart`
- `apps/mobile/lib/features/dungeon/presentation/widgets/pre_battle_dialog.dart`

---

### Gap 9: Boss Raid Visual Phases 1/2/3

**What it should look like:**
The Boss Raid battle has 3 visual phases as the boss's HP decreases:
- **Phase 1 (100%-66% HP):** Normal background, standard boss aura
- **Phase 2 (66%-33% HP):** Purple shimmer background intensifies, boss becomes more aggressive visually
- **Phase 3 (33%-0% HP):** Maximum visual intensity, screen shake, desperate boss animation

The game mechanics (questions, damage calculation) exist; what's missing is the visual phase transitions.

**Current Status: PARTIAL**

The `BossRaidPage` at `apps/mobile/lib/features/practice/presentation/pages/boss_raid_page.dart` has:
- A purple radial gradient background with shimmer animation
- Boss visual with name and rank ("S-RANK BOSS")
- Boss status card showing HP bar, user damage, and rank
- Shake animation on the boss visual
- Timer badge for active raids

A separate `BossRaidBattlePage` exists at `apps/mobile/lib/features/practice/presentation/pages/boss_raid_battle_page.dart` for the actual question-answering phase.

**Remaining Work:**
- No phase-based visual transitions exist. The background, shimmer intensity, and boss visual remain static regardless of HP percentage.
- Add a `_currentPhase` computed from `bossCurrentHp / bossHp` ratio.
- Phase 2: Increase shimmer frequency, change gradient to deeper purple, add particle effects.
- Phase 3: Add screen shake (using `Animate.shake()`), red tint overlay, boss "enraged" icon change, pulsing HP bar.
- Play escalating haptic patterns at phase transitions.
- Play sound effects at phase transitions.

**Files:**
- `apps/mobile/lib/features/practice/presentation/pages/boss_raid_page.dart`
- `apps/mobile/lib/features/practice/presentation/pages/boss_raid_battle_page.dart`
- `apps/mobile/lib/features/practice/presentation/providers/boss_raid_provider.dart`

---

### Gap 11: Stats 3 Tabs: RESUMEN / MATERIAS / PLAN

**What it should look like:**
Stats screen with 3 tabs:
1. **RESUMEN:** Level card (gradient, circular level indicator), quick stats (streak, accuracy, study days), weekly XP chart, annual activity heatmap
2. **MATERIAS:** Radar chart "you vs national average" (blue polygon vs grey polygon), weaknesses section (red), strengths section (green), all subjects list with mastery cards
3. **PLAN:** Study plan progress card, unit-by-unit progress list

**Current Status: IMPLEMENTED**

The `StatsPage` at `apps/mobile/lib/features/stats/presentation/pages/stats_page.dart` implements all 3 tabs:

**Resumen tab:**
- Level card with gradient (purple to blue), circular level indicator, XP progress bar
- Quick stats row: streak (orange), accuracy (green), study days (blue)
- Weekly chart widget
- Annual activity heatmap from `ActivityHeatmap` widget

**Materias tab:**
- "Comparacion con Promedio Nacional" header
- `SubjectRadarChart` widget with "Tu nivel" vs "Promedio nacional" legend
- Weaknesses section with red icon ("Materias a Mejorar")
- Strengths section with green icon ("Tus Fortalezas")
- All subjects list with `SubjectMasteryCard` cards
- Subject detail modal with mastery %, accuracy %, questions count, national comparison

**Plan tab:**
- `StudyPlanProgressCard` with "View Plan" action
- Unit-by-unit progress list (`UnitProgressItem`)
- Empty state with "Iniciar Diagnostico" CTA when no plan exists

**Remaining Work:**
- Verify `SubjectRadarChart` renders a proper 5-axis radar chart (not just the simplified painter from value props).
- The heatmap depends on `state.heatmapData` -- verify the backend returns this data from the `advanced_stats` endpoint.
- Tab labels use sentence case ("Resumen", "Materias", "Plan") -- spec says uppercase but sentence case is acceptable.

**Files:**
- `apps/mobile/lib/features/stats/presentation/pages/stats_page.dart`
- `apps/mobile/lib/features/stats/presentation/widgets/subject_mastery_card.dart`
- `apps/mobile/lib/features/stats/presentation/widgets/weekly_chart.dart`
- `apps/mobile/lib/features/stats/presentation/widgets/study_plan_progress_card.dart`
- `apps/mobile/lib/features/stats/presentation/providers/stats_provider.dart`
- `apps/mobile/lib/features/profile/presentation/widgets/activity_heatmap.dart`

---

### Gap 12: Achievements 6 Categories + 4 Rarities

**What it should look like:**
Achievements screen with:
- **6 category tabs:** Todos, Racha, Practica, Dominio, Social, Especial (scrollable)
- **4 rarity tiers:** Comun (grey), Raro (blue), Epico (purple), Legendario (gold) -- each with distinct color coding
- **Grid layout:** 3-column grid of achievement badges
- **Progress header:** Unlocked count, completion percentage (circular), rarity breakdown
- **Badge detail modal:** Full-screen bottom sheet with achievement description, progress, rewards

**Current Status: IMPLEMENTED**

The `AchievementsPage` at `apps/mobile/lib/features/achievements/presentation/pages/achievements_page.dart` implements everything:
- `TabController(length: 6)` with tabs: Todos, Racha, Practica, Dominio, Social, Especial (via `AchievementCategory` enum)
- Category filtering via `achievementsProvider.notifier.filterByCategory()`
- 3-column `SliverGrid` with `AchievementBadge` widgets
- Progress header with gradient card showing: unlocked/total count, circular progress indicator, rarity breakdown (Comun, Raro, Epico, Legendario)
- `AchievementDetailModal` for tap-to-detail
- Empty state for categories with no achievements
- `AchievementModel` has `rarity` field with `AchievementRarity` enum (common, rare, epic, legendary) with `colorValue` and `displayName`
- `AchievementUnlockAnimation` widget for unlock celebrations

**Remaining Work:**
- Verify rarity color values are visually distinct and match the RPG theme.
- Test grid layout on different screen sizes (small phones may need 2-column layout).
- Badge visual: locked achievements should be greyed out with a lock overlay.

**Files:**
- `apps/mobile/lib/features/achievements/presentation/pages/achievements_page.dart`
- `apps/mobile/lib/features/achievements/presentation/widgets/achievement_badge.dart`
- `apps/mobile/lib/features/achievements/presentation/widgets/achievement_detail_modal.dart`
- `apps/mobile/lib/features/achievements/presentation/widgets/achievement_unlock_animation.dart`
- `apps/mobile/lib/features/achievements/data/models/achievement_model.dart`
- `apps/mobile/lib/features/achievements/presentation/providers/achievements_provider.dart`

---

### Gap 13: Developer Mode (7 Taps)

**What it should do:**
Easter egg in Settings: tapping the version number 7 times activates Developer Mode. Features:
- Reset onboarding (return to first-run state)
- Full data wipe (clear all local storage)
- Debug state view (current onboarding step, first run flag, completion flag, diagnostic status)
- Deactivate dev mode option

Countdown feedback starts at tap 4 ("3 toques mas...").

**Current Status: IMPLEMENTED**

The `SettingsPage` at `apps/mobile/lib/features/settings/presentation/pages/settings_page.dart` implements the complete feature:
- `_versionTapCount` counter on the "v1.0.0" text at the bottom of the page
- At tap 4+: Shows remaining count via SnackBar ("X toques mas para modo desarrollador")
- At tap 7: Calls `onboardingProvider.notifier.setDevMode(true)` and shows "Modo Desarrollador activado"
- Dev mode section (only visible when `isDevMode` is true):
  - "Reiniciar Onboarding" with confirmation dialog -- calls `resetOnboarding()` and navigates to splash
  - "Reinicio Completo" with warning dialog -- calls `logout()` + `fullReset()` and navigates to splash
  - "Estado Actual" showing: current step, first run, complete, diagnostic status
  - "Desactivar Modo Dev" button

**Remaining Work:** None. Implementation is complete and well-designed.

**Files:**
- `apps/mobile/lib/features/settings/presentation/pages/settings_page.dart`
- `apps/mobile/lib/core/services/onboarding_service.dart` -- `setDevMode()`, `resetOnboarding()`, `fullReset()`

---

### Gap 18: Known Issues / Tech Debt Section

**What it should be:**
A living document (`KNOWN_ISSUES.md`) in the project root that tracks:
- Known bugs and their workarounds
- Missing features or incomplete implementations
- Technical debt items (hardcoded values, TODO comments, deprecated patterns)
- Performance concerns
- Security items to address before release

This helps new contributors understand what's broken and what's intentional.

**Current Status: MISSING**

No `KNOWN_ISSUES.md` file exists in the project root.

**Required Action:**
Create `KNOWN_ISSUES.md` covering at minimum:
- Sound asset files missing (Gap 15)
- Haptic feedback not integrated into UI flows (Gap 14)
- Demo mode shows errors on data-dependent screens (Gap 2)
- Global AppBar only on Home screen (Gap 6)
- Boss Raid missing visual phase transitions (Gap 9)
- Firebase project configuration required for push notifications (Gap 16)
- Hardcoded demo credentials in auth provider
- Missing background map images for dungeon themes

**Files:**
- `KNOWN_ISSUES.md` -- to be created at project root

---

## Appendix A: File Index

All file paths are relative to `apps/mobile/lib/`.

| Area | Key Files |
|------|-----------|
| **Auth** | `features/auth/presentation/pages/login_page.dart`, `register_page.dart`, `providers/auth_provider.dart` |
| **Auth Storage** | `core/auth/data/datasources/auth_local_datasource.dart` |
| **Onboarding** | `features/onboarding/presentation/pages/value_prop_page.dart`, `first_mission_page.dart`, `quick_diagnostic_page.dart`, `results_reveal_page.dart` |
| **Home** | `features/home/presentation/pages/home_page.dart`, `widgets/daily_goal_card.dart`, `boss_raid_banner.dart`, `quick_actions.dart` |
| **Dungeon** | `features/dungeon/presentation/pages/dungeon_map_page.dart`, `battle_page.dart`, `providers/dungeon_provider.dart` |
| **Boss Raid** | `features/practice/presentation/pages/boss_raid_page.dart`, `boss_raid_battle_page.dart`, `providers/boss_raid_provider.dart` |
| **Store/Shop** | `features/shop/presentation/pages/shop_page.dart`, `widgets/inventory_grid.dart`, `powerup_inventory.dart` |
| **Stats** | `features/stats/presentation/pages/stats_page.dart`, `widgets/subject_mastery_card.dart`, `weekly_chart.dart` |
| **Achievements** | `features/achievements/presentation/pages/achievements_page.dart`, `widgets/achievement_badge.dart`, `achievement_detail_modal.dart` |
| **Settings** | `features/settings/presentation/pages/settings_page.dart`, `notification_settings_page.dart` |
| **Network** | `core/network/api_client.dart`, `interceptors/retry_interceptor.dart`, `auth_interceptor.dart`, `offline_interceptor.dart` |
| **Services** | `core/services/haptic_patterns.dart`, `sound_service.dart`, `notification_service.dart`, `notification_scheduler.dart` |
| **Shared Widgets** | `shared/widgets/hearts_display.dart`, `streak_flame.dart`, `gold_indicator.dart`, `psychological/loss_aversion_alerts.dart` |
| **Routing** | `core/config/routes.dart` |

## Appendix B: Implementation Roadmap

### Sprint 1 (Immediate)
1. Integrate haptic patterns into battle/practice/question flows (Gap 14)
2. Add 9 MP3 sound files and integrate SoundService (Gap 15)
3. Create shared GameAppBar and deploy to all screens (Gap 6)
4. Create `KNOWN_ISSUES.md` (Gap 18)

### Sprint 2 (Next)
1. Fix Demo Mode label and add offline fallbacks for all screens (Gap 2)
2. Complete Firebase/FCM setup for push notifications (Gap 16)
3. Dynamic first mission based on diagnostic results (Gap 5)

### Sprint 3 (Polish)
1. Boss Raid visual phases (Gap 9)
2. RPG auth aesthetics refinement (Gap 3)
3. Dungeon map bezier curves and background assets (Gap 8)
4. Radar chart improvements for stats and value props (Gap 11)
