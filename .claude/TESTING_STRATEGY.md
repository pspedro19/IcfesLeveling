# TESTING_STRATEGY.md — ICFES Leveling

> Estrategia de testing, tipos de tests, y cobertura mínima requerida.

---

## 1. OVERVIEW

| Capa | Herramienta | Coverage Mínimo | Responsable |
|---|---|---|---|
| Backend Unit | pytest | 70% | Backend dev |
| Backend Integration | pytest + TestClient | Endpoints críticos | Backend dev |
| Game Engine | pytest | 100% de fórmulas | Backend dev |
| Anti-Gaming | pytest | 100% de reglas | Backend dev |
| IRT | pytest + NumPy | Datos sintéticos conocidos | Backend dev |
| Mobile Widget | flutter_test | Componentes críticos | Mobile dev |
| Mobile Integration | integration_test | Flujos principales | Mobile dev |
| E2E | Manual + Automation | Flujos completos | QA |

---

## 2. BACKEND UNIT TESTS

### 2.1 Game Engine Service (OBLIGATORIO 100%)

```python
# tests/test_game_engine_service.py

class TestXPCalculation:
    def test_new_question_correct_gives_10_xp(self):
        xp = GameEngineService.calculate_xp_for_answer(
            attempt_type="new", is_correct=True, streak_days=1
        )
        assert xp == 10

    def test_valid_review_correct_gives_5_xp(self):
        xp = GameEngineService.calculate_xp_for_answer(
            attempt_type="valid_review", is_correct=True, streak_days=1
        )
        assert xp == 5

    def test_invalid_repeat_gives_0_xp(self):
        xp = GameEngineService.calculate_xp_for_answer(
            attempt_type="invalid_repeat", is_correct=True, streak_days=1
        )
        assert xp == 0

    def test_incorrect_always_gives_0_xp(self):
        for attempt_type in ["new", "valid_review", "invalid_repeat"]:
            xp = GameEngineService.calculate_xp_for_answer(
                attempt_type=attempt_type, is_correct=False, streak_days=1
            )
            assert xp == 0

    def test_grace_mode_gives_0_xp(self):
        xp = GameEngineService.calculate_xp_for_answer(
            attempt_type="new", is_correct=True, streak_days=1, in_grace_mode=True
        )
        assert xp == 0

class TestLevelCalculation:
    def test_level_1_at_0_xp(self):
        assert GameEngineService.calculate_level_for_xp(0) == 1

    def test_level_2_at_100_xp(self):
        assert GameEngineService.calculate_level_for_xp(100) == 2

    def test_level_10_at_8100_xp(self):
        assert GameEngineService.calculate_level_for_xp(8100) == 10

    def test_xp_for_level_roundtrip(self):
        for level in range(1, 100):
            xp = GameEngineService.calculate_xp_for_level(level)
            assert GameEngineService.calculate_level_for_xp(xp) == level

class TestRankCalculation:
    @pytest.mark.parametrize("level,expected_rank", [
        (1, "E"), (14, "E"), (15, "D"), (29, "D"),
        (30, "C"), (49, "C"), (50, "B"), (59, "B"),
        (60, "A"), (69, "A"), (70, "S"), (79, "S"),
        (80, "SS"), (89, "SS"), (90, "SSS"), (100, "SSS"),
    ])
    def test_rank_thresholds(self, level, expected_rank):
        assert GameEngineService.calculate_rank(level) == expected_rank

class TestStreakMultiplier:
    @pytest.mark.parametrize("days,expected", [
        (0, 1.0), (1, 1.0), (6, 1.0),
        (7, 1.2), (13, 1.2),
        (14, 1.5), (29, 1.5),
        (30, 2.0), (100, 2.0),
    ])
    def test_multiplier_thresholds(self, days, expected):
        assert GameEngineService.get_streak_multiplier(days) == expected

class TestDamageCalculation:
    def test_incorrect_gives_0_damage(self):
        damage = GameEngineService.calculate_damage(
            user_power=10, user_wisdom=10, response_time_ms=5000,
            difficulty=5, combo_count=0, is_correct=False
        )
        assert damage == 0

    def test_fast_response_doubles_damage(self):
        base = GameEngineService.calculate_damage(
            user_power=10, user_wisdom=10, response_time_ms=25000,
            difficulty=1, combo_count=0, is_correct=True
        )
        fast = GameEngineService.calculate_damage(
            user_power=10, user_wisdom=10, response_time_ms=2000,
            difficulty=1, combo_count=0, is_correct=True
        )
        assert fast == base * 2

    def test_minimum_damage_is_1(self):
        damage = GameEngineService.calculate_damage(
            user_power=0, user_wisdom=0, response_time_ms=60000,
            difficulty=1, combo_count=0, is_correct=True
        )
        assert damage >= 1
```

### 2.2 Anti-Gaming Tests (OBLIGATORIO 100%)

```python
# tests/test_anti_gaming.py

class TestAttemptType:
    def test_first_attempt_is_new(self):
        result = determine_attempt_type(user_id, question_id, topic_id)
        assert result == "new"

    def test_repeat_same_day_is_invalid(self):
        # After answering, same day
        result = determine_attempt_type(user_id, question_id, topic_id)
        assert result == "invalid_repeat"

    def test_review_after_min_days_is_valid(self):
        # mastery=0.5 → min_days=3, wait 3 days
        result = determine_attempt_type(user_id, question_id, topic_id)
        assert result == "valid_review"

    def test_high_mastery_requires_more_days(self):
        # mastery=1.0 → min_days=7
        ...

class TestRateLimiting:
    def test_rejects_under_3_seconds(self):
        response = client.post("/practice/answer", ...)
        # Immediate second request
        response2 = client.post("/practice/answer", ...)
        assert response2.status_code == 429

    def test_xp_cap_per_hour(self):
        # Submit 60 correct answers in 1 hour
        # After 500 XP, no more XP awarded
        ...
```

### 2.3 IRT Tests

```python
# tests/test_irt.py

class TestIRT3PL:
    def test_probability_at_theta_equals_b(self):
        """When theta == b, probability should be ~(1+c)/2"""
        p = irt_probability(theta=0.0, a=1.0, b=0.0, c=0.25)
        assert abs(p - 0.625) < 0.01

    def test_high_theta_high_probability(self):
        p = irt_probability(theta=3.0, a=1.0, b=0.0, c=0.0)
        assert p > 0.95

    def test_low_theta_approaches_c(self):
        p = irt_probability(theta=-3.0, a=1.0, b=0.0, c=0.25)
        assert abs(p - 0.25) < 0.05

    def test_fisher_information_peaks_near_b(self):
        info_at_b = fisher_information(theta=0.0, a=1.0, b=0.0, c=0.0)
        info_far = fisher_information(theta=2.0, a=1.0, b=0.0, c=0.0)
        assert info_at_b > info_far

    def test_theta_to_rank_conversion(self):
        assert theta_to_rank(-2.0) == "E"
        assert theta_to_rank(-1.0) == "D"
        assert theta_to_rank(0.0) == "C"
        assert theta_to_rank(0.7) == "B"
        assert theta_to_rank(1.2) == "A"
        assert theta_to_rank(2.0) == "S"
```

### 2.4 Mastery Tests

```python
# tests/test_mastery.py

class TestMasteryUpdate:
    def test_correct_increases_mastery(self):
        new = update_mastery(current=0.5, is_correct=True)
        assert new > 0.5

    def test_incorrect_decreases_mastery(self):
        new = update_mastery(current=0.5, is_correct=False)
        assert new < 0.5

    def test_mastery_approaches_1_asymptotically(self):
        score = 0.0
        for _ in range(100):
            score = update_mastery(score, is_correct=True)
        assert score > 0.95
        assert score <= 1.0

    def test_decay_starts_after_3_days(self):
        original = 0.8
        assert apply_decay(original, days_inactive=2) == original
        assert apply_decay(original, days_inactive=4) < original

    def test_decay_never_below_minimum(self):
        assert apply_decay(0.5, days_inactive=100) >= 0.1

    def test_prerequisite_blocks_below_threshold(self):
        # Topic B requires 60% mastery of Topic A
        ...
```

---

## 3. BACKEND INTEGRATION TESTS

```python
# tests/integration/test_practice_flow.py

class TestPracticeFlow:
    async def test_complete_practice_session(self, client, auth_headers):
        # 1. Start session
        start = await client.post("/practice/start", headers=auth_headers)
        assert start.status_code == 201
        session_id = start.json()["session_id"]

        # 2. Answer 15 questions
        for i in range(15):
            answer = await client.post("/practice/answer", json={
                "session_id": session_id,
                "question_id": questions[i].id,
                "selected_answer": "a",
                "time_spent_seconds": 15,
            }, headers=auth_headers)
            assert answer.status_code == 200

        # 3. End session
        end = await client.post("/practice/end", json={
            "session_id": session_id,
        }, headers=auth_headers)
        assert end.status_code == 200
        assert end.json()["total_questions"] == 15

# tests/integration/test_diagnostic_flow.py
# tests/integration/test_boss_raid_flow.py
# tests/integration/test_auth_flow.py
```

---

## 4. MOBILE TESTS

### 4.1 Widget Tests
```dart
// test/features/practice/presentation/widgets/question_card_test.dart

void main() {
  testWidgets('QuestionCard displays question text', (tester) async {
    await tester.pumpWidget(MaterialApp(
      home: QuestionCard(
        question: mockQuestion,
        onAnswerSelected: (_) {},
      ),
    ));

    expect(find.text('¿Cuál es el valor de x?'), findsOneWidget);
    expect(find.text('A'), findsOneWidget);
    expect(find.text('B'), findsOneWidget);
    expect(find.text('C'), findsOneWidget);
    expect(find.text('D'), findsOneWidget);
  });

  testWidgets('QuestionCard calls callback on answer tap', (tester) async {
    String? selectedAnswer;
    await tester.pumpWidget(MaterialApp(
      home: QuestionCard(
        question: mockQuestion,
        onAnswerSelected: (answer) => selectedAnswer = answer,
      ),
    ));

    await tester.tap(find.text('B'));
    expect(selectedAnswer, equals('b'));
  });
}
```

### 4.2 Provider Tests
```dart
// test/features/practice/presentation/providers/practice_provider_test.dart

void main() {
  test('practice session starts with 0 correct answers', () {
    final container = ProviderContainer();
    final state = container.read(practiceProvider);
    expect(state.correctAnswers, equals(0));
  });
}
```

---

## 5. TEST DATA

### 5.1 Fixtures
```python
# tests/conftest.py

@pytest.fixture
def sample_user():
    return User(
        id=uuid4(), username="test_user", email="test@test.com",
        level=1, experience=0, rank="E", hearts=5, gold=1000,
    )

@pytest.fixture
def sample_question():
    return Question(
        id=uuid4(), difficulty=5,
        parametro_irt_a=1.0, parametro_irt_b=0.0, parametro_irt_c=0.25,
        respuesta_correcta="b",
    )
```

---

## 6. CI/CD PIPELINE

```yaml
# .github/workflows/test.yml
on: [push, pull_request]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16
      redis:
        image: redis:7-alpine
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
      - run: pip install -r requirements-test.txt
      - run: pytest --cov=app --cov-report=xml --cov-fail-under=70
      - uses: codecov/codecov-action@v4

  mobile-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: subosito/flutter-action@v2
      - run: flutter test --coverage
```
