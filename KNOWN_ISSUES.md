# Known Issues & Technical Debt

**Project:** IcfesLeveling (Flutter Mobile + FastAPI Backend)
**Last Updated:** 2026-02-19
**Purpose:** Track known issues, technical debt, and recently resolved items for the gamified ICFES exam prep platform.

---

## CRITICAL (Blocks Production)

These issues must be resolved before any production release.

- [x] **Test suite incompatible with backend** -- `.claude/tests/` test suite was using async SQLAlchemy but backend is sync. **FIXED**: Rewrote all 4 files (conftest.py, test_game_engine.py, test_anti_gaming_irt_hearts_mastery.py, test_full_user_flows.py) to use sync SQLAlchemy matching actual backend architecture.
- [ ] **JWT tokens stored insecurely** -- `FlutterSecureStorage` is not used for JWT token persistence. Tokens are currently stored in Hive, which is **not encrypted at rest**. On a rooted/jailbroken device, tokens can be extracted trivially. Must migrate token storage to `flutter_secure_storage` with platform keychain/keystore backing.
- [ ] **Missing sound asset files** -- 9 MP3 files are referenced in Dart code but do not exist at `apps/mobile/assets/sounds/`. The app will throw asset-loading exceptions or fail silently at runtime. Required files include battle sounds, UI feedback, level-up, and victory audio.
- [ ] **Missing Lottie animation files** -- Lottie animation JSON files are referenced in widget code but do not exist at `apps/mobile/assets/animations/`. Screens that depend on these animations (loading states, celebrations, streak indicators) will crash or render blank.
- [ ] **Firebase not configured** -- No `google-services.json` (Android) or `GoogleService-Info.plist` (iOS) present in the project. This means:
  - Push notifications will not work
  - Firebase Analytics will not collect data
  - Crashlytics will not report crashes
  - Remote Config will not be available
- [ ] **AdMob not configured** -- No valid AdMob app ID or ad unit IDs are set. Rewarded ad calls return `false`, which means the heart-restoration-via-ad flow is non-functional. Users who run out of hearts have no free recovery path.
- [ ] **Placeholder app icon** -- No custom icon exists at `apps/mobile/assets/icons/app_icon.png`. The app ships with the default Flutter placeholder icon on both Android and iOS.
- [ ] **No SSL certificates configured for production** -- HTTPS/TLS is not set up for backend services. API traffic between mobile client and server would be unencrypted in a production deployment without a reverse proxy or certificate configuration.
- [ ] **Hardcoded credentials in docker-compose.yml** -- Some database passwords and service credentials remain hardcoded in the Docker Compose configuration. Partially addressed but not fully migrated to environment variables or a secrets manager.

---

## HIGH (Affects User Experience)

These issues degrade the user experience and should be resolved before public beta.

- [ ] **No Value Prop slides before onboarding** -- New users go straight into onboarding without seeing value proposition slides explaining what the app does, its gamified approach, or how it helps with ICFES prep. First impressions suffer.
- [ ] **No Demo Mode** -- There is no offline or no-backend demo experience. If the server is unreachable or a user wants to try the app before signing up, they see errors instead of sample content.
- [ ] **No global AppBar with hearts/streak/gold** -- The persistent top bar showing the user's heart count, daily streak, and gold balance is missing across all screens. Users have no constant visibility into their key game resources.
- [ ] **No haptic feedback system** -- Taps, correct/incorrect answers, level-ups, and other interactions lack haptic feedback (vibration patterns). This reduces the tactile engagement expected in a gamified mobile app.
- [ ] **Home page missing contextual alerts** -- The home screen does not display contextual warnings such as:
  - Streak at risk (has not studied today)
  - Low hearts (1 or 0 remaining)
  - League demotion risk (near bottom of league)
  - Pending daily quests
- [ ] **Dungeon map lacks visual polish** -- The dungeon map is functional but does not render the intended S-shaped visual path with distinct node states (locked, available, completed, boss). Currently uses a simpler list or grid layout.
- [ ] **Boss Raid missing phase transitions** -- Boss Raid encounters are supposed to have visible phase transitions (Phase 1/2/3) with escalating difficulty and visual cues. Currently phases change internally but the UI does not reflect the transitions.
- [ ] **Store may lack proper 3-tab layout** -- The in-game store should have three distinct tabs: TIENDA (consumables), POWER-UPS (boosts), and INVENTARIO (owned items). The current implementation may not fully separate these sections.
- [ ] **Post-diagnostic "primera mision" screen missing** -- After completing the initial diagnostic test, users should see a narrative "first mission" screen that transitions them into the main game loop. This bridging screen does not exist.

---

## MEDIUM (Technical Debt)

These are code-quality and architecture issues that increase maintenance cost and risk of bugs.

- [x] **`routes/__init__.py` was out of sync with `main.py`** -- Fixed. The route registry module now exports all routers that `main.py` imports.
- [x] **Health check had hardcoded timestamp** -- Fixed. The `/health` endpoint now uses `datetime.utcnow()`.
- [ ] **TODO comments in cached route modules** -- Several route modules imported in `main.py` have TODO placeholders or incomplete implementations: `users_cached`, `questions_cached`, `battles_cached`, `icfes_catalog`. These need to be completed or removed.
- [x] **SpacedRepetitionService uses async methods on sync backend** -- Fixed. All methods converted from `async def` to `def`, `await` removed from service and route files.
- [x] **NotificationService uses async methods on sync backend** -- Fixed. All methods converted to sync.
- [x] **BossRaidService.start_raid_session was async** -- Fixed. Converted to sync, `await` removed from route.
- [x] **hearts_service.py had NotImplementedError** -- Fixed. Purchase method now performs full heart refill.
- [x] **wompi_service.py called nonexistent notification method** -- Fixed. Changed `send_notification` to `send_custom` with correct params.
- [ ] **ClickHouse analytics tables may not exist** -- ClickHouse integration is configured in code (`clickhouse_service.py`) but the initialization SQL scripts for creating the required analytics tables may not have been run. Queries will fail at runtime.
- [ ] **Duplicate route registrations for hearts** -- The hearts system has overlapping route paths: `grace-mode/enter` vs `enter-grace-mode`. One should be removed or aliased to avoid confusion and potential routing conflicts.
- [ ] **Media cache middleware commented out** -- The media caching middleware in `media_cache_middleware.py` is commented out for debugging purposes. This means image and media responses are not being cached, increasing load times and bandwidth usage.
- [ ] **Commented-out Question model columns** -- Several columns in the `Question` SQLAlchemy model are commented out, suggesting a pending database migration. These columns may be needed for features like multimedia questions, difficulty metadata, or competency tagging.
- [x] **Streak multiplier value inconsistency** -- Fixed. All services and tests now use GameEngineService values: 1.0x (<7d), 1.2x (7-13d), 1.5x (14-29d), 2.0x (30+d).
- [x] **Duplicate streak multiplier logic** -- Fixed. StreakService now aligned with GameEngineService (source of truth). MobileService was already correct.

---

## LOW (Nice to Have)

These are enhancements and polish items that would improve the product but are not blocking.

- [ ] **No Developer Mode easter egg** -- Spec calls for a hidden developer mode activated by tapping 7 times on the version number. Not yet implemented. Useful for QA and internal testing.
- [ ] **Achievement system lacks full categorization** -- The achievement system does not yet implement all 6 planned categories (Academic, Social, Consistency, Exploration, Competition, Special) with 4 rarity tiers (Common, Rare, Epic, Legendary).
- [ ] **Stats page missing advanced visualizations** -- The statistics screen is missing a study-activity heatmap (GitHub-style contribution grid) and a subject-competency radar chart for visual performance analysis.
- [ ] **RPG narrative flavor missing from auth screens** -- Login, signup, and password recovery screens use standard form UI without the RPG narrative framing (e.g., "Brave adventurer, enter your credentials to return to the realm...") called for in the design spec.
- [ ] **No retry with exponential backoff** -- API calls from the mobile client do not implement retry logic with exponential backoff (spec: 3 retries, 500ms initial delay, 2x multiplier). Failed requests surface errors immediately to the user.
- [ ] **Sentry DSN not configured** -- Sentry error tracking is integrated in code but no DSN is set. Production errors, crashes, and performance data are not being captured or reported.

---

## RECENTLY FIXED (This Session)

Items resolved during the current development session for reference and regression tracking.

- [x] **gunicorn added to requirements** -- Added `gunicorn` to both `apps/backend/requirements.txt` and `apps/ai-service/requirements.txt` so production Dockerfiles can use the WSGI server.
- [x] **WebSocket Dockerfile port corrected** -- Changed WebSocket service exposed port from `8001` to `4002` to match the deployment configuration and Nginx proxy rules.
- [x] **python-jose version aligned** -- Pinned `python-jose` to `>=3.5.0` across all services to ensure consistent JWT handling and avoid version mismatch bugs.
- [x] **YMLGenerator inherits from AIService** -- `YMLGenerator` now properly inherits from `AIService`, gaining access to shared cache methods and eliminating duplicated caching logic.
- [x] **Mock data removed from video_recommendations.py** -- Removed hardcoded mock video data from 6 endpoints in `video_recommendations.py`. Endpoints now query the database or return proper empty-state responses.
- [x] **Dev user mock removed from users_cached.py** -- Removed the dummy/dev user fallback that returned fake user data when the database was unreachable. Endpoints now return proper 401/404 errors.
- [x] **Dummy user creation removed from diagnostic_public_service.py** -- Removed auto-creation of throwaway user accounts during public diagnostic flow. The service now requires proper authentication or guest tokens.
- [x] **Mobile mock fallbacks removed** -- Removed hardcoded mock/fallback data from four mobile modules: `unit_repository`, `stats_provider`, `leagues`, and `millionaire`. These now properly call the backend API or surface errors.
- [x] **AdMob stub fixed** -- AdMob stub service now correctly returns `false` for `showRewardedAd()` instead of silently succeeding. UI properly shows "ad unavailable" messaging when AdMob is not configured.
- [x] **routes/__init__.py updated** -- Synchronized `routes/__init__.py` exports with all routers registered in `main.py`, resolving import mismatches.
- [x] **Health check uses dynamic timestamp** -- Replaced hardcoded timestamp string in `/health` endpoint with `datetime.utcnow()` for accurate server health reporting.
- [x] **deploy.sh health check port corrected** -- Updated deployment health check script from port `8000` to port `4000` to match the actual backend service port in production.
