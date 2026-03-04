# tests/shared/test_runner_configs.md
# ═══════════════════════════════════════════════════════════════
# Configuraciones para ejecutar toda la suite de tests
# ═══════════════════════════════════════════════════════════════

## 1. PYTEST CONFIGURATION (Backend)

### pytest.ini
```ini
[pytest]
testpaths = tests/backend
python_files = test_*.py
python_classes = Test*
python_functions = test_*
asyncio_mode = auto
markers =
    slow: marks tests as slow (deselect with '-m "not slow"')
    integration: marks integration tests
    e2e: marks end-to-end tests
addopts =
    -v
    --tb=short
    --cov=app
    --cov-report=term-missing
    --cov-report=html:htmlcov
    --cov-fail-under=70
    -x  # Stop on first failure
```

### requirements-test.txt
```
pytest==8.0+
pytest-asyncio==0.23+
pytest-cov==4.1+
pytest-mock==3.12+
httpx==0.27+
aiosqlite==0.20+
factory-boy==3.3+
faker==22.0+
freezegun==1.3+
```

### Comandos de ejecución
```bash
# Todos los tests
pytest

# Solo unit tests
pytest tests/backend/unit/ -v

# Solo integration tests
pytest tests/backend/integration/ -v -m integration

# Solo Game Engine (requiere 100% coverage)
pytest tests/backend/unit/test_game_engine.py -v --cov=app.services.game_engine_service --cov-fail-under=100

# Solo Anti-Gaming (requiere 100% coverage)
pytest tests/backend/unit/test_anti_gaming_irt_hearts_mastery.py::TestAttemptTypeClassification -v

# Solo IRT
pytest tests/backend/unit/test_anti_gaming_irt_hearts_mastery.py::TestIRT3PL -v

# Con reporte HTML
pytest --cov-report=html && open htmlcov/index.html

# Parallel execution
pytest -n auto  # Requiere pytest-xdist
```

---

## 2. FLUTTER TEST CONFIGURATION

### analysis_options.yaml (test additions)
```yaml
analyzer:
  exclude:
    - "**/*.g.dart"
    - "**/*.freezed.dart"
    - "**/*.mocks.dart"
  errors:
    unused_import: warning
    unnecessary_null_comparison: warning
```

### Comandos de ejecución
```bash
# Widget tests
flutter test test/

# Con coverage
flutter test --coverage
genhtml coverage/lcov.info -o coverage/html
open coverage/html/index.html

# Solo un archivo
flutter test test/widget/test_all_screens.dart

# Integration tests (requiere emulador o device)
flutter test integration_test/e2e_full_user_journey_test.dart

# E2E en device específico
flutter test integration_test/ -d <device_id>

# Con verbose output
flutter test --reporter expanded

# Solo tests de offline
flutter test test/unit/test_offline_system.dart -v
```

---

## 3. CI/CD PIPELINE

### .github/workflows/test.yml
```yaml
name: Test Suite

on:
  push:
    branches: [develop, main]
  pull_request:
    branches: [develop, main]

jobs:
  # ─── BACKEND TESTS ─────────────────────────
  backend-unit:
    name: "Backend Unit Tests"
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
          POSTGRES_DB: test_db
        ports: ["5432:5432"]
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      redis:
        image: redis:7-alpine
        ports: ["6379:6379"]
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: "pip"

      - name: Install dependencies
        run: |
          cd apps/backend
          pip install -r requirements.txt
          pip install -r requirements-test.txt

      - name: Run unit tests
        run: |
          cd apps/backend
          pytest tests/unit/ -v --cov=app --cov-report=xml --cov-fail-under=70
        env:
          DATABASE_URL: postgresql+asyncpg://test:test@localhost:5432/test_db
          JWT_SECRET: test-secret-key-minimum-32-characters-long-for-ci
          REDIS_URL: redis://localhost:6379
          ENVIRONMENT: test

      - name: Run integration tests
        run: |
          cd apps/backend
          pytest tests/integration/ -v --cov-append --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          file: apps/backend/coverage.xml
          flags: backend

  # ─── GAME ENGINE 100% COVERAGE ─────────────
  game-engine-coverage:
    name: "Game Engine 100% Coverage"
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: |
          cd apps/backend
          pip install -r requirements.txt
          pip install -r requirements-test.txt

      - name: Game Engine must have 100% coverage
        run: |
          cd apps/backend
          pytest tests/unit/test_game_engine.py -v \
            --cov=app.services.game_engine_service \
            --cov-fail-under=100

  # ─── FLUTTER TESTS ─────────────────────────
  flutter-tests:
    name: "Flutter Widget & Unit Tests"
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: subosito/flutter-action@v2
        with:
          flutter-version: "3.24.0"
          channel: "stable"
          cache: true

      - name: Install dependencies
        run: |
          cd apps/mobile
          flutter pub get

      - name: Analyze code
        run: |
          cd apps/mobile
          flutter analyze --no-fatal-infos

      - name: Run widget tests
        run: |
          cd apps/mobile
          flutter test --coverage

      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          file: apps/mobile/coverage/lcov.info
          flags: flutter

  # ─── FLUTTER E2E (on device) ───────────────
  flutter-e2e:
    name: "Flutter E2E Tests"
    runs-on: macos-latest
    needs: [backend-unit, flutter-tests]
    steps:
      - uses: actions/checkout@v4
      - uses: subosito/flutter-action@v2
        with:
          flutter-version: "3.24.0"

      - name: Start iOS Simulator
        run: |
          UDID=$(xcrun simctl list devices | grep "iPhone 15" | head -1 | grep -o '[A-F0-9\-]\{36\}')
          xcrun simctl boot "$UDID"

      - name: Run E2E tests
        run: |
          cd apps/mobile
          flutter test integration_test/e2e_full_user_journey_test.dart \
            --timeout 300s
```

---

## 4. TEST EXECUTION ORDER (Recomendado)

```
Paso 1: Unit tests (más rápidos, sin dependencias)
  pytest tests/backend/unit/ -v
  flutter test test/unit/

Paso 2: Widget tests (Flutter rendering)
  flutter test test/widget/

Paso 3: Integration tests (requieren DB + Redis)
  pytest tests/backend/integration/ -v

Paso 4: E2E tests (requieren backend + emulador)
  docker-compose up -d postgres redis backend
  flutter test integration_test/

Paso 5: Verificación de coverage
  pytest --cov-report=html
  flutter test --coverage && genhtml coverage/lcov.info -o coverage/html
```

---

## 5. RESUMEN DE COVERAGE TARGETS

| Componente | Mínimo | Ideal | Obligatorio |
|---|---|---|---|
| GameEngineService | 100% | 100% | ✅ Sí |
| Anti-Gaming | 100% | 100% | ✅ Sí |
| IRT Engine | 90% | 100% | ✅ Sí |
| Mastery Service | 90% | 100% | ✅ Sí |
| Spaced Repetition | 85% | 95% | ✅ Sí |
| Hearts Service | 90% | 100% | ✅ Sí |
| Auth Flow | 80% | 90% | ✅ Sí |
| Practice Flow | 80% | 90% | ✅ Sí |
| Boss Raid Flow | 75% | 85% | No |
| Backend General | 70% | 85% | ✅ Sí |
| Flutter Widgets | 60% | 80% | No |
| Offline System | 80% | 90% | ✅ Sí |
| E2E Flows | N/A | 5 flows | No |
