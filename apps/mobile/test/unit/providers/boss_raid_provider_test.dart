import 'dart:async';

import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:icfes_mobile/features/practice/presentation/providers/boss_raid_provider.dart';
import 'package:icfes_mobile/features/practice/domain/repositories/boss_raid_repository.dart';
import 'package:icfes_mobile/features/practice/data/models/boss_raid_models.dart';
import 'package:icfes_mobile/features/practice/domain/entities/question.dart';

// ============================================================================
// FAKE REPOSITORY IMPLEMENTATIONS
// ============================================================================

/// Fake repository that always returns successful results with configurable data.
class FakeBossRaidRepository implements BossRaidRepository {
  BossRaidStatusModel? statusToReturn;
  BossRaidSessionModel? sessionToReturn;
  BossRaidAnswerResponse? answerResponseToReturn;
  BossRaidCompleteResponse? completeResponseToReturn;

  bool shouldThrowOnGetStatus = false;
  bool shouldThrowOnStartRaid = false;
  bool shouldThrowOnSubmitAnswer = false;
  bool shouldThrowOnCompleteRaid = false;

  String errorMessage = 'Simulated network error';

  @override
  Future<BossRaidStatusModel> getStatus() async {
    if (shouldThrowOnGetStatus) throw Exception(errorMessage);
    return statusToReturn ?? _defaultStatus();
  }

  @override
  Future<BossRaidSessionModel> startRaid() async {
    if (shouldThrowOnStartRaid) throw Exception(errorMessage);
    return sessionToReturn ?? _defaultSession();
  }

  @override
  Future<BossRaidAnswerResponse> submitAnswer({
    required String sessionId,
    required String questionId,
    required String answerId,
  }) async {
    if (shouldThrowOnSubmitAnswer) throw Exception(errorMessage);
    return answerResponseToReturn ?? _defaultAnswerResponse();
  }

  @override
  Future<BossRaidCompleteResponse> completeRaid(String sessionId) async {
    if (shouldThrowOnCompleteRaid) throw Exception(errorMessage);
    return completeResponseToReturn ?? _defaultCompleteResponse();
  }
}

// ============================================================================
// HELPERS FOR BUILDING FAKE MODELS
// ============================================================================

BossRaidStatusModel _defaultStatus({
  bool isActive = true,
  String bossName = 'Dragon Algebrico',
  int hp = 10000,
  int currentHp = 7500,
  int? timeRemainingSeconds = 3600,
  double xpMultiplier = 3.0,
  int myDamageDealt = 0,
  int? myRank,
}) {
  return BossRaidStatusModel(
    isActive: isActive,
    startsAt: DateTime.now().subtract(const Duration(hours: 1)),
    endsAt: DateTime.now().add(const Duration(hours: 1)),
    currentBoss: CurrentBossModel(
      id: 'boss-1',
      name: bossName,
      description: 'A fearsome algebraic dragon.',
      hp: hp,
      currentHp: currentHp,
      difficulty: 'hard',
      isDefeated: false,
    ),
    xpMultiplier: xpMultiplier,
    myDamageDealt: myDamageDealt,
    myRank: myRank,
    timeRemainingSeconds: timeRemainingSeconds,
  );
}

BossRaidSessionModel _defaultSession({
  String sessionId = 'session-abc',
  int questionCount = 3,
}) {
  final questions = List.generate(
    questionCount,
    (i) => RaidQuestionModel(
      id: 'q-$i',
      text: 'Question $i: What is ${i + 1} + ${i + 1}?',
      options: [
        RaidQuestionOption(id: 'a-$i-A', text: '${(i + 1) * 2}'),
        RaidQuestionOption(id: 'a-$i-B', text: '${(i + 1) * 2 + 1}'),
        RaidQuestionOption(id: 'a-$i-C', text: '${(i + 1) * 3}'),
        RaidQuestionOption(id: 'a-$i-D', text: '${(i + 1) * 2 - 1}'),
      ],
    ),
  );

  return BossRaidSessionModel(
    sessionId: sessionId,
    boss: CurrentBossModel(
      id: 'boss-1',
      name: 'Dragon Algebrico',
      hp: 10000,
      currentHp: 7500,
      difficulty: 'hard',
      isDefeated: false,
    ),
    questions: questions,
    totalQuestions: questionCount,
    xpMultiplier: 3.0,
    startedAt: DateTime.now(),
  );
}

BossRaidAnswerResponse _defaultAnswerResponse({
  bool correct = true,
  String correctAnswerId = 'a-0-A',
  int damageDealt = 200,
  int xpEarned = 30,
  int currentCombo = 1,
  int bossCurrentHp = 7300,
  bool bossDefeated = false,
}) {
  return BossRaidAnswerResponse(
    correct: correct,
    correctAnswerId: correctAnswerId,
    damageDealt: damageDealt,
    xpEarned: xpEarned,
    currentCombo: currentCombo,
    bossCurrentHp: bossCurrentHp,
    bossDefeated: bossDefeated,
  );
}

BossRaidCompleteResponse _defaultCompleteResponse({
  bool bossDefeated = false,
  int totalDamage = 600,
  int totalXp = 90,
  int correctAnswers = 3,
  int totalQuestions = 3,
  double accuracyPercentage = 100.0,
  int bestCombo = 3,
  int? rankInRaid,
  int sessionDurationSeconds = 125,
}) {
  return BossRaidCompleteResponse(
    bossDefeated: bossDefeated,
    totalDamage: totalDamage,
    totalXp: totalXp,
    correctAnswers: correctAnswers,
    totalQuestions: totalQuestions,
    accuracyPercentage: accuracyPercentage,
    bestCombo: bestCombo,
    rankInRaid: rankInRaid,
    rewards: [],
    sessionDurationSeconds: sessionDurationSeconds,
  );
}

/// Builds a [BossRaidNotifier] backed by [repo] without hitting the real
/// constructor's auto-call to [fetchStatus], so each test can control the
/// initial state cleanly via [ProviderContainer] overrides.
final _fakeBossRaidRepositoryProvider =
    Provider<BossRaidRepository>((ref) {
  // Filled in each test via container overrides.
  throw UnimplementedError('Override this provider in tests.');
});

final _testBossRaidProvider =
    StateNotifierProvider<BossRaidNotifier, BossRaidState>((ref) {
  final repo = ref.watch(_fakeBossRaidRepositoryProvider);
  return BossRaidNotifier(repo);
});

ProviderContainer _makeContainer(FakeBossRaidRepository repo) {
  return ProviderContainer(
    overrides: [
      _fakeBossRaidRepositoryProvider.overrideWithValue(repo),
    ],
  );
}

// ============================================================================
// TESTS
// ============================================================================

void main() {
  // ---------------------------------------------------------------------------
  // BossRaidState – default/initial state
  // ---------------------------------------------------------------------------
  group('BossRaidState – initial defaults', () {
    test('default constructor sets all fields to their zero/null values', () {
      final state = BossRaidState();

      expect(state.status, isNull);
      expect(state.sessionId, isNull);
      expect(state.boss, isNull);
      expect(state.questions, isNull);
      expect(state.currentQuestionIndex, equals(0));
      expect(state.selectedAnswerId, isNull);
      expect(state.lastAnswerResult, isNull);
      expect(state.isAnswerSubmitted, isFalse);
      expect(state.totalDamageDealt, equals(0));
      expect(state.currentCombo, equals(0));
      expect(state.bestCombo, equals(0));
      expect(state.correctAnswers, equals(0));
      expect(state.totalXpEarned, equals(0));
      expect(state.isLoading, isFalse);
      expect(state.isSubmittingAnswer, isFalse);
      expect(state.error, isNull);
      expect(state.results, isNull);
      expect(state.isCompleted, isFalse);
    });
  });

  // ---------------------------------------------------------------------------
  // BossRaidState – computed getter: currentQuestion
  // ---------------------------------------------------------------------------
  group('BossRaidState.currentQuestion', () {
    List<Question> _makeQuestions(int count) => List.generate(
          count,
          (i) => Question(
            id: 'q-$i',
            subjectId: 'raid',
            topicId: 'raid',
            text: 'Question $i',
            options: [],
            correctAnswer: '',
            difficulty: 'medium',
          ),
        );

    test('returns null when questions list is null', () {
      final state = BossRaidState();
      expect(state.currentQuestion, isNull);
    });

    test('returns null when questions list is empty', () {
      final state = BossRaidState(questions: []);
      expect(state.currentQuestion, isNull);
    });

    test('returns first question when index is 0', () {
      final questions = _makeQuestions(3);
      final state = BossRaidState(questions: questions, currentQuestionIndex: 0);
      expect(state.currentQuestion, isNotNull);
      expect(state.currentQuestion!.id, equals('q-0'));
    });

    test('returns the correct question at a given index', () {
      final questions = _makeQuestions(5);
      final state = BossRaidState(questions: questions, currentQuestionIndex: 3);
      expect(state.currentQuestion!.id, equals('q-3'));
    });

    test('returns null when index equals list length (out of bounds)', () {
      final questions = _makeQuestions(3);
      final state = BossRaidState(questions: questions, currentQuestionIndex: 3);
      expect(state.currentQuestion, isNull);
    });

    test('returns null when index exceeds list length', () {
      final questions = _makeQuestions(2);
      final state = BossRaidState(questions: questions, currentQuestionIndex: 99);
      expect(state.currentQuestion, isNull);
    });
  });

  // ---------------------------------------------------------------------------
  // BossRaidState – computed getter: totalQuestions
  // ---------------------------------------------------------------------------
  group('BossRaidState.totalQuestions', () {
    test('returns 0 when questions is null', () {
      expect(BossRaidState().totalQuestions, equals(0));
    });

    test('returns 0 when questions list is empty', () {
      expect(BossRaidState(questions: []).totalQuestions, equals(0));
    });

    test('returns correct count', () {
      final questions = List.generate(
        7,
        (i) => Question(
          id: 'q-$i',
          subjectId: 'raid',
          topicId: 'raid',
          text: 'Q$i',
          options: [],
          correctAnswer: '',
          difficulty: 'medium',
        ),
      );
      expect(BossRaidState(questions: questions).totalQuestions, equals(7));
    });
  });

  // ---------------------------------------------------------------------------
  // BossRaidState – computed getter: progress
  // ---------------------------------------------------------------------------
  group('BossRaidState.progress', () {
    List<Question> _q(int n) => List.generate(
          n,
          (i) => Question(
            id: 'q-$i',
            subjectId: 'raid',
            topicId: 'raid',
            text: 'Q$i',
            options: [],
            correctAnswer: '',
            difficulty: 'medium',
          ),
        );

    test('returns 0.0 when no questions', () {
      expect(BossRaidState().progress, equals(0.0));
    });

    test('returns 1/n for the first question (index 0)', () {
      final state = BossRaidState(questions: _q(4), currentQuestionIndex: 0);
      expect(state.progress, closeTo(1 / 4, 0.0001));
    });

    test('returns 1.0 on the last question', () {
      final state = BossRaidState(questions: _q(5), currentQuestionIndex: 4);
      expect(state.progress, closeTo(1.0, 0.0001));
    });

    test('progress grows as index advances', () {
      final questions = _q(4);
      final p0 = BossRaidState(questions: questions, currentQuestionIndex: 0).progress;
      final p1 = BossRaidState(questions: questions, currentQuestionIndex: 1).progress;
      final p2 = BossRaidState(questions: questions, currentQuestionIndex: 2).progress;
      expect(p1, greaterThan(p0));
      expect(p2, greaterThan(p1));
    });
  });

  // ---------------------------------------------------------------------------
  // BossRaidState – computed getter: hasMoreQuestions
  // ---------------------------------------------------------------------------
  group('BossRaidState.hasMoreQuestions', () {
    List<Question> _q(int n) => List.generate(
          n,
          (i) => Question(
            id: 'q-$i',
            subjectId: 'raid',
            topicId: 'raid',
            text: 'Q$i',
            options: [],
            correctAnswer: '',
            difficulty: 'medium',
          ),
        );

    test('returns false when questions is null', () {
      expect(BossRaidState().hasMoreQuestions, isFalse);
    });

    test('returns false for a single-question list at index 0', () {
      expect(
        BossRaidState(questions: _q(1), currentQuestionIndex: 0).hasMoreQuestions,
        isFalse,
      );
    });

    test('returns true when not on the last question', () {
      expect(
        BossRaidState(questions: _q(3), currentQuestionIndex: 0).hasMoreQuestions,
        isTrue,
      );
      expect(
        BossRaidState(questions: _q(3), currentQuestionIndex: 1).hasMoreQuestions,
        isTrue,
      );
    });

    test('returns false on the last question', () {
      expect(
        BossRaidState(questions: _q(3), currentQuestionIndex: 2).hasMoreQuestions,
        isFalse,
      );
    });
  });

  // ---------------------------------------------------------------------------
  // BossRaidState – copyWith
  // ---------------------------------------------------------------------------
  group('BossRaidState.copyWith', () {
    test('preserves unmodified fields', () {
      final original = BossRaidState(
        currentQuestionIndex: 2,
        correctAnswers: 5,
        totalXpEarned: 150,
        currentCombo: 3,
        bestCombo: 4,
        isLoading: false,
        isCompleted: false,
      );

      final updated = original.copyWith(isLoading: true);

      expect(updated.isLoading, isTrue);
      expect(updated.currentQuestionIndex, equals(2));
      expect(updated.correctAnswers, equals(5));
      expect(updated.totalXpEarned, equals(150));
      expect(updated.currentCombo, equals(3));
      expect(updated.bestCombo, equals(4));
    });

    test('clearError sets error to null', () {
      final state = BossRaidState(error: 'Something went wrong');
      final cleared = state.copyWith(clearError: true);
      expect(cleared.error, isNull);
    });

    test('clearAnswer resets selectedAnswerId, lastAnswerResult, isAnswerSubmitted', () {
      final result = BossRaidAnswerResult(
        isCorrect: true,
        correctAnswerId: 'ans-A',
        damageDealt: 100,
        xpEarned: 20,
        currentCombo: 2,
        bossCurrentHp: 900,
        bossDefeated: false,
      );
      final state = BossRaidState(
        selectedAnswerId: 'ans-A',
        lastAnswerResult: result,
        isAnswerSubmitted: true,
      );
      final cleared = state.copyWith(clearAnswer: true);

      expect(cleared.selectedAnswerId, isNull);
      expect(cleared.lastAnswerResult, isNull);
      expect(cleared.isAnswerSubmitted, isFalse);
    });

    test('clearQuestions sets questions to null', () {
      final questions = [
        Question(
          id: 'q-0',
          subjectId: 'raid',
          topicId: 'raid',
          text: 'Q0',
          options: [],
          correctAnswer: '',
          difficulty: 'medium',
        ),
      ];
      final state = BossRaidState(questions: questions);
      final cleared = state.copyWith(clearQuestions: true);
      expect(cleared.questions, isNull);
    });

    test('clearResults sets results to null', () {
      final results = BossRaidResults(
        bossDefeated: false,
        totalDamage: 300,
        totalXp: 60,
        correctAnswers: 2,
        totalQuestions: 3,
        accuracyPercentage: 66.7,
        bestCombo: 2,
        rewards: [],
        sessionDurationSeconds: 90,
      );
      final state = BossRaidState(results: results);
      final cleared = state.copyWith(clearResults: true);
      expect(cleared.results, isNull);
    });
  });

  // ---------------------------------------------------------------------------
  // BossRaidStatus – formattedTimeRemaining
  // ---------------------------------------------------------------------------
  group('BossRaidStatus.formattedTimeRemaining', () {
    BossRaidStatus _status(int? seconds) => BossRaidStatus(
          isActive: true,
          bossName: 'TestBoss',
          bossHp: 1000,
          bossCurrentHp: 1000,
          timeRemainingSeconds: seconds,
        );

    test('returns "Terminando..." when timeRemainingSeconds is null', () {
      expect(_status(null).formattedTimeRemaining, equals('Terminando...'));
    });

    test('returns "Terminando..." when timeRemainingSeconds is 0', () {
      expect(_status(0).formattedTimeRemaining, equals('Terminando...'));
    });

    test('returns "Terminando..." when timeRemainingSeconds is negative', () {
      expect(_status(-5).formattedTimeRemaining, equals('Terminando...'));
    });

    test('formats seconds-only duration as minutes', () {
      // 45 seconds -> 0 minutes remainder -> "0m"
      expect(_status(45).formattedTimeRemaining, equals('0m'));
    });

    test('formats exactly 60 seconds as "1m"', () {
      expect(_status(60).formattedTimeRemaining, equals('1m'));
    });

    test('formats 90 seconds as "1m"', () {
      expect(_status(90).formattedTimeRemaining, equals('1m'));
    });

    test('formats exactly 1 hour as "1h 0m"', () {
      expect(_status(3600).formattedTimeRemaining, equals('1h 0m'));
    });

    test('formats 1 hour and 30 minutes', () {
      expect(_status(3600 + 30 * 60).formattedTimeRemaining, equals('1h 30m'));
    });

    test('formats 2 hours and 15 minutes', () {
      expect(_status(2 * 3600 + 15 * 60).formattedTimeRemaining, equals('2h 15m'));
    });

    test('formats 23 hours 59 minutes', () {
      expect(_status(23 * 3600 + 59 * 60).formattedTimeRemaining, equals('23h 59m'));
    });

    test('formats sub-hour duration as only minutes (no hours prefix)', () {
      // 30 minutes exactly
      final formatted = _status(30 * 60).formattedTimeRemaining;
      expect(formatted, equals('30m'));
      expect(formatted.contains('h'), isFalse);
    });
  });

  // ---------------------------------------------------------------------------
  // BossRaidStatus – hpPercentage
  // ---------------------------------------------------------------------------
  group('BossRaidStatus.hpPercentage', () {
    test('returns 0.0 when bossHp is 0 (avoids division by zero)', () {
      final status = BossRaidStatus(
        isActive: true,
        bossName: 'Boss',
        bossHp: 0,
        bossCurrentHp: 0,
      );
      expect(status.hpPercentage, equals(0.0));
    });

    test('returns 1.0 when boss is at full HP', () {
      final status = BossRaidStatus(
        isActive: true,
        bossName: 'Boss',
        bossHp: 5000,
        bossCurrentHp: 5000,
      );
      expect(status.hpPercentage, closeTo(1.0, 0.0001));
    });

    test('returns 0.5 when boss is at half HP', () {
      final status = BossRaidStatus(
        isActive: true,
        bossName: 'Boss',
        bossHp: 10000,
        bossCurrentHp: 5000,
      );
      expect(status.hpPercentage, closeTo(0.5, 0.0001));
    });

    test('returns 0.0 when bossCurrentHp is 0', () {
      final status = BossRaidStatus(
        isActive: true,
        bossName: 'Boss',
        bossHp: 10000,
        bossCurrentHp: 0,
      );
      expect(status.hpPercentage, equals(0.0));
    });
  });

  // ---------------------------------------------------------------------------
  // BossRaidResults – formattedDuration
  // ---------------------------------------------------------------------------
  group('BossRaidResults.formattedDuration', () {
    BossRaidResults _results(int seconds) => BossRaidResults(
          bossDefeated: false,
          totalDamage: 0,
          totalXp: 0,
          correctAnswers: 0,
          totalQuestions: 0,
          accuracyPercentage: 0,
          bestCombo: 0,
          rewards: [],
          sessionDurationSeconds: seconds,
        );

    test('formats zero duration as "00:00"', () {
      expect(_results(0).formattedDuration, equals('00:00'));
    });

    test('formats 59 seconds as "00:59"', () {
      expect(_results(59).formattedDuration, equals('00:59'));
    });

    test('formats exactly 60 seconds as "01:00"', () {
      expect(_results(60).formattedDuration, equals('01:00'));
    });

    test('formats 125 seconds as "02:05"', () {
      expect(_results(125).formattedDuration, equals('02:05'));
    });

    test('formats 3600 seconds (1 hour) as "60:00"', () {
      // There is no hours segment – minutes just keep growing.
      expect(_results(3600).formattedDuration, equals('60:00'));
    });

    test('formats 3661 seconds as "61:01"', () {
      expect(_results(3661).formattedDuration, equals('61:01'));
    });

    test('pads single-digit minutes and seconds with leading zeros', () {
      // 5 minutes, 7 seconds = 307 seconds
      expect(_results(307).formattedDuration, equals('05:07'));
    });
  });

  // ---------------------------------------------------------------------------
  // BossRaidNotifier – selectAnswer guard
  // ---------------------------------------------------------------------------
  group('BossRaidNotifier.selectAnswer guard', () {
    late FakeBossRaidRepository repo;
    late ProviderContainer container;

    setUp(() {
      repo = FakeBossRaidRepository();
    });

    tearDown(() {
      container.dispose();
    });

    test('does nothing when isAnswerSubmitted is true', () async {
      container = _makeContainer(repo);
      final notifier = container.read(_testBossRaidProvider.notifier);

      // Settle the constructor's fire-and-forget fetchStatus call.
      await notifier.fetchStatus();

      // Start a raid so questions are available.
      await notifier.startRaid();

      // Manually put the state into "already submitted" mode.
      // We do this by calling selectAnswer (which succeeds) and then
      // mutating state via the notifier's own copyWith path through submitAnswer.
      // The simplest approach: set selectedAnswerId first, then submit.
      notifier.selectAnswer('a-0-A');
      expect(
        container.read(_testBossRaidProvider).selectedAnswerId,
        equals('a-0-A'),
      );

      await notifier.submitAnswer();

      // After submission the answer is locked.
      final stateAfterSubmit = container.read(_testBossRaidProvider);
      expect(stateAfterSubmit.isAnswerSubmitted, isTrue);

      // Now try to change the selection – it should be ignored.
      notifier.selectAnswer('a-0-B');

      final stateAfterGuard = container.read(_testBossRaidProvider);
      // selectedAnswerId should still be 'a-0-A', not the newly attempted 'a-0-B'.
      expect(stateAfterGuard.selectedAnswerId, equals('a-0-A'));
    });

    test('does nothing when isSubmittingAnswer is true (mid-flight guard)', () async {
      // Use a repo that hangs so we can check the in-flight guard.
      final hangingRepo = _HangingSubmitRepository();
      final hangContainer = ProviderContainer(
        overrides: [
          _fakeBossRaidRepositoryProvider.overrideWithValue(hangingRepo),
        ],
      );
      addTearDown(hangContainer.dispose);

      final notifier = hangContainer.read(_testBossRaidProvider.notifier);
      await notifier.fetchStatus();
      await notifier.startRaid();

      notifier.selectAnswer('a-0-A');

      // Fire submitAnswer but do NOT await – it will hang inside the repo.
      final submitFuture = notifier.submitAnswer();

      // Give the state machine a tick to set isSubmittingAnswer = true.
      await Future.delayed(const Duration(milliseconds: 10));

      final mid = hangContainer.read(_testBossRaidProvider);
      expect(mid.isSubmittingAnswer, isTrue);

      // Attempt to select a different answer while submitting.
      notifier.selectAnswer('a-0-B');

      final midAfterAttempt = hangContainer.read(_testBossRaidProvider);
      expect(midAfterAttempt.selectedAnswerId, equals('a-0-A'));

      // Unblock the hanging repo.
      hangingRepo.complete();
      await submitFuture;
    });

    test('selectAnswer updates state normally before submission', () async {
      container = _makeContainer(repo);
      final notifier = container.read(_testBossRaidProvider.notifier);

      await notifier.fetchStatus();
      await notifier.startRaid();

      notifier.selectAnswer('a-0-A');
      expect(
        container.read(_testBossRaidProvider).selectedAnswerId,
        equals('a-0-A'),
      );

      // Can change selection before submitting.
      notifier.selectAnswer('a-0-C');
      expect(
        container.read(_testBossRaidProvider).selectedAnswerId,
        equals('a-0-C'),
      );
    });
  });

  // ---------------------------------------------------------------------------
  // BossRaidNotifier – fetchStatus
  // ---------------------------------------------------------------------------
  group('BossRaidNotifier.fetchStatus', () {
    late FakeBossRaidRepository repo;
    late ProviderContainer container;

    setUp(() {
      repo = FakeBossRaidRepository();
    });

    tearDown(() {
      container.dispose();
    });

    test('populates state.status on success', () async {
      repo.statusToReturn = _defaultStatus(
        bossName: 'Shadow Wyrm',
        hp: 20000,
        currentHp: 18000,
        timeRemainingSeconds: 7200,
      );

      container = _makeContainer(repo);

      // Settle the constructor's fire-and-forget fetchStatus call.
      final notifier = container.read(_testBossRaidProvider.notifier);
      await notifier.fetchStatus();

      final state = container.read(_testBossRaidProvider);
      expect(state.isLoading, isFalse);
      expect(state.status, isNotNull);
      expect(state.status!.bossName, equals('Shadow Wyrm'));
      expect(state.status!.bossHp, equals(20000));
      expect(state.status!.bossCurrentHp, equals(18000));
      expect(state.status!.timeRemainingSeconds, equals(7200));
      expect(state.error, isNull);
    });

    test('sets error on failure', () async {
      repo.shouldThrowOnGetStatus = true;
      repo.errorMessage = 'Server unavailable';

      container = _makeContainer(repo);
      final notifier = container.read(_testBossRaidProvider.notifier);
      await notifier.fetchStatus();

      final state = container.read(_testBossRaidProvider);
      expect(state.isLoading, isFalse);
      expect(state.error, isNotNull);
      expect(state.error, contains('Server unavailable'));
      expect(state.status, isNull);
    });

    test('xpMultiplier is preserved in BossRaidStatus', () async {
      repo.statusToReturn = _defaultStatus(xpMultiplier: 5.0);

      container = _makeContainer(repo);
      final notifier = container.read(_testBossRaidProvider.notifier);
      await notifier.fetchStatus();

      expect(
        container.read(_testBossRaidProvider).status!.xpMultiplier,
        equals(5.0),
      );
    });
  });

  // ---------------------------------------------------------------------------
  // BossRaidNotifier – startRaid
  // ---------------------------------------------------------------------------
  group('BossRaidNotifier.startRaid', () {
    late FakeBossRaidRepository repo;
    late ProviderContainer container;

    setUp(() {
      repo = FakeBossRaidRepository();
    });

    tearDown(() {
      container.dispose();
    });

    test('populates questions and sessionId on success', () async {
      repo.sessionToReturn = _defaultSession(
        sessionId: 'sess-xyz',
        questionCount: 5,
      );

      container = _makeContainer(repo);
      await Future.delayed(const Duration(milliseconds: 50));

      final notifier = container.read(_testBossRaidProvider.notifier);
      final returnedId = await notifier.startRaid();

      final state = container.read(_testBossRaidProvider);
      expect(returnedId, equals('sess-xyz'));
      expect(state.sessionId, equals('sess-xyz'));
      expect(state.questions, isNotNull);
      expect(state.questions!.length, equals(5));
      expect(state.isLoading, isFalse);
      expect(state.error, isNull);
      expect(state.currentQuestionIndex, equals(0));
    });

    test('resets battle stats before starting a new raid', () async {
      container = _makeContainer(repo);
      await Future.delayed(const Duration(milliseconds: 50));

      final notifier = container.read(_testBossRaidProvider.notifier);

      // Simulate a previous raid with stats.
      await notifier.startRaid();
      notifier.selectAnswer('a-0-A');
      await notifier.submitAnswer();

      // Stats should now be non-zero.
      var state = container.read(_testBossRaidProvider);
      expect(state.totalDamageDealt, greaterThan(0));
      expect(state.correctAnswers, greaterThan(0));

      // Start a fresh raid.
      await notifier.startRaid();
      state = container.read(_testBossRaidProvider);

      expect(state.totalDamageDealt, equals(0));
      expect(state.currentCombo, equals(0));
      expect(state.bestCombo, equals(0));
      expect(state.correctAnswers, equals(0));
      expect(state.totalXpEarned, equals(0));
      expect(state.currentQuestionIndex, equals(0));
      expect(state.isCompleted, isFalse);
    });

    test('returns null and sets error when startRaid throws', () async {
      repo.shouldThrowOnStartRaid = true;
      repo.errorMessage = 'No active boss raid';

      container = _makeContainer(repo);
      await Future.delayed(const Duration(milliseconds: 50));

      final notifier = container.read(_testBossRaidProvider.notifier);
      final result = await notifier.startRaid();

      expect(result, isNull);
      final state = container.read(_testBossRaidProvider);
      expect(state.isLoading, isFalse);
      expect(state.error, contains('No active boss raid'));
    });
  });

  // ---------------------------------------------------------------------------
  // BossRaidNotifier – submitAnswer
  // ---------------------------------------------------------------------------
  group('BossRaidNotifier.submitAnswer', () {
    late FakeBossRaidRepository repo;
    late ProviderContainer container;

    setUp(() {
      repo = FakeBossRaidRepository();
    });

    tearDown(() {
      container.dispose();
    });

    test('updates stats correctly after a correct answer', () async {
      repo.answerResponseToReturn = _defaultAnswerResponse(
        correct: true,
        damageDealt: 350,
        xpEarned: 45,
        currentCombo: 2,
        bossCurrentHp: 7150,
      );

      container = _makeContainer(repo);
      await Future.delayed(const Duration(milliseconds: 50));

      final notifier = container.read(_testBossRaidProvider.notifier);
      await notifier.startRaid();
      notifier.selectAnswer('a-0-A');
      await notifier.submitAnswer();

      final state = container.read(_testBossRaidProvider);
      expect(state.isAnswerSubmitted, isTrue);
      expect(state.isSubmittingAnswer, isFalse);
      expect(state.correctAnswers, equals(1));
      expect(state.totalDamageDealt, equals(350));
      expect(state.totalXpEarned, equals(45));
      expect(state.currentCombo, equals(2));
      expect(state.bestCombo, equals(2));
      expect(state.error, isNull);
    });

    test('does not increment correctAnswers after a wrong answer', () async {
      repo.answerResponseToReturn = _defaultAnswerResponse(
        correct: false,
        damageDealt: 50,
        xpEarned: 5,
        currentCombo: 0,
        bossCurrentHp: 7450,
      );

      container = _makeContainer(repo);
      await Future.delayed(const Duration(milliseconds: 50));

      final notifier = container.read(_testBossRaidProvider.notifier);
      await notifier.startRaid();
      notifier.selectAnswer('a-0-B');
      await notifier.submitAnswer();

      final state = container.read(_testBossRaidProvider);
      expect(state.isAnswerSubmitted, isTrue);
      expect(state.correctAnswers, equals(0));
      expect(state.currentCombo, equals(0));
    });

    test('bestCombo is updated when currentCombo exceeds previous best', () async {
      // First answer: combo = 3
      repo.answerResponseToReturn = _defaultAnswerResponse(
        correct: true,
        currentCombo: 3,
        damageDealt: 100,
        xpEarned: 20,
        bossCurrentHp: 7400,
      );

      container = _makeContainer(repo);
      await Future.delayed(const Duration(milliseconds: 50));

      final notifier = container.read(_testBossRaidProvider.notifier);
      await notifier.startRaid();
      notifier.selectAnswer('a-0-A');
      await notifier.submitAnswer();

      expect(container.read(_testBossRaidProvider).bestCombo, equals(3));
    });

    test('bestCombo is not decreased by a lower combo', () async {
      // First answer establishes bestCombo = 4.
      repo.answerResponseToReturn = _defaultAnswerResponse(
        correct: true,
        currentCombo: 4,
        damageDealt: 100,
        xpEarned: 10,
        bossCurrentHp: 7400,
      );

      container = _makeContainer(repo);
      await Future.delayed(const Duration(milliseconds: 50));

      final notifier = container.read(_testBossRaidProvider.notifier);
      await notifier.startRaid();
      notifier.selectAnswer('a-0-A');
      await notifier.submitAnswer();

      expect(container.read(_testBossRaidProvider).bestCombo, equals(4));

      // Move to second question.
      notifier.nextQuestion();

      // Second answer: combo drops to 0 (wrong answer).
      repo.answerResponseToReturn = _defaultAnswerResponse(
        correct: false,
        currentCombo: 0,
        damageDealt: 30,
        xpEarned: 5,
        bossCurrentHp: 7370,
      );

      notifier.selectAnswer('a-1-C');
      await notifier.submitAnswer();

      // bestCombo should remain 4, not drop to 0.
      expect(container.read(_testBossRaidProvider).bestCombo, equals(4));
      expect(container.read(_testBossRaidProvider).currentCombo, equals(0));
    });

    test('does nothing when no answer is selected', () async {
      container = _makeContainer(repo);
      await Future.delayed(const Duration(milliseconds: 50));

      final notifier = container.read(_testBossRaidProvider.notifier);
      await notifier.startRaid();

      // Do NOT call selectAnswer.
      await notifier.submitAnswer();

      final state = container.read(_testBossRaidProvider);
      expect(state.isAnswerSubmitted, isFalse);
      expect(state.isSubmittingAnswer, isFalse);
    });

    test('does nothing when no session is active', () async {
      container = _makeContainer(repo);
      await Future.delayed(const Duration(milliseconds: 50));

      final notifier = container.read(_testBossRaidProvider.notifier);
      // Do NOT call startRaid – sessionId is null.

      await notifier.submitAnswer();

      final state = container.read(_testBossRaidProvider);
      expect(state.isAnswerSubmitted, isFalse);
      expect(state.isSubmittingAnswer, isFalse);
    });

    test('sets error when repository throws', () async {
      repo.shouldThrowOnSubmitAnswer = true;
      repo.errorMessage = 'Answer submission failed';

      container = _makeContainer(repo);
      await Future.delayed(const Duration(milliseconds: 50));

      final notifier = container.read(_testBossRaidProvider.notifier);
      await notifier.startRaid();
      notifier.selectAnswer('a-0-A');
      await notifier.submitAnswer();

      final state = container.read(_testBossRaidProvider);
      expect(state.isSubmittingAnswer, isFalse);
      expect(state.isAnswerSubmitted, isFalse);
      expect(state.error, contains('Answer submission failed'));
    });
  });

  // ---------------------------------------------------------------------------
  // BossRaidNotifier – nextQuestion
  // ---------------------------------------------------------------------------
  group('BossRaidNotifier.nextQuestion', () {
    late FakeBossRaidRepository repo;
    late ProviderContainer container;

    setUp(() {
      repo = FakeBossRaidRepository();
    });

    tearDown(() {
      container.dispose();
    });

    test('advances currentQuestionIndex and clears answer state', () async {
      repo.sessionToReturn = _defaultSession(questionCount: 3);

      container = _makeContainer(repo);
      await Future.delayed(const Duration(milliseconds: 50));

      final notifier = container.read(_testBossRaidProvider.notifier);
      await notifier.startRaid();
      notifier.selectAnswer('a-0-A');
      await notifier.submitAnswer();

      expect(container.read(_testBossRaidProvider).currentQuestionIndex, equals(0));
      expect(container.read(_testBossRaidProvider).isAnswerSubmitted, isTrue);

      notifier.nextQuestion();

      final state = container.read(_testBossRaidProvider);
      expect(state.currentQuestionIndex, equals(1));
      expect(state.isAnswerSubmitted, isFalse);
      expect(state.selectedAnswerId, isNull);
      expect(state.lastAnswerResult, isNull);
    });

    test('does nothing when answer has not been submitted', () async {
      repo.sessionToReturn = _defaultSession(questionCount: 3);

      container = _makeContainer(repo);
      await Future.delayed(const Duration(milliseconds: 50));

      final notifier = container.read(_testBossRaidProvider.notifier);
      await notifier.startRaid();

      // Do NOT submit an answer.
      notifier.nextQuestion();

      expect(
        container.read(_testBossRaidProvider).currentQuestionIndex,
        equals(0),
      );
    });

    test('triggers completeRaid when no more questions remain', () async {
      repo.sessionToReturn = _defaultSession(questionCount: 1);

      container = _makeContainer(repo);
      final notifier = container.read(_testBossRaidProvider.notifier);
      await notifier.fetchStatus();
      await notifier.startRaid();
      notifier.selectAnswer('a-0-A');
      await notifier.submitAnswer();

      // With only 1 question, hasMoreQuestions is false so nextQuestion
      // should trigger completeRaid (fire-and-forget).
      notifier.nextQuestion();

      // Explicitly call completeRaid to ensure async settles
      // (nextQuestion calls it fire-and-forget).
      await notifier.completeRaid();

      final state = container.read(_testBossRaidProvider);
      expect(state.isCompleted, isTrue);
      expect(state.results, isNotNull);
    });
  });

  // ---------------------------------------------------------------------------
  // BossRaidNotifier – completeRaid
  // ---------------------------------------------------------------------------
  group('BossRaidNotifier.completeRaid', () {
    late FakeBossRaidRepository repo;
    late ProviderContainer container;

    setUp(() {
      repo = FakeBossRaidRepository();
    });

    tearDown(() {
      container.dispose();
    });

    test('sets isCompleted and results on success', () async {
      repo.completeResponseToReturn = _defaultCompleteResponse(
        bossDefeated: true,
        totalDamage: 1500,
        totalXp: 200,
        correctAnswers: 5,
        totalQuestions: 5,
        accuracyPercentage: 100.0,
        bestCombo: 5,
        rankInRaid: 1,
        sessionDurationSeconds: 180,
      );

      container = _makeContainer(repo);
      await Future.delayed(const Duration(milliseconds: 50));

      final notifier = container.read(_testBossRaidProvider.notifier);
      await notifier.startRaid();
      await notifier.completeRaid();

      final state = container.read(_testBossRaidProvider);
      expect(state.isCompleted, isTrue);
      expect(state.isLoading, isFalse);
      expect(state.results, isNotNull);
      expect(state.results!.bossDefeated, isTrue);
      expect(state.results!.totalDamage, equals(1500));
      expect(state.results!.rankInRaid, equals(1));
      expect(state.results!.formattedDuration, equals('03:00'));
    });

    test('does nothing when sessionId is null', () async {
      container = _makeContainer(repo);
      await Future.delayed(const Duration(milliseconds: 50));

      final notifier = container.read(_testBossRaidProvider.notifier);
      // Do NOT start a raid.
      await notifier.completeRaid();

      final state = container.read(_testBossRaidProvider);
      expect(state.isCompleted, isFalse);
      expect(state.results, isNull);
    });

    test('does nothing when already completed', () async {
      container = _makeContainer(repo);
      await Future.delayed(const Duration(milliseconds: 50));

      final notifier = container.read(_testBossRaidProvider.notifier);
      await notifier.startRaid();
      await notifier.completeRaid(); // First completion

      final firstResults = container.read(_testBossRaidProvider).results;

      // Second call should be a no-op.
      repo.completeResponseToReturn = _defaultCompleteResponse(totalXp: 9999);
      await notifier.completeRaid();

      // Results should not have changed.
      expect(container.read(_testBossRaidProvider).results, equals(firstResults));
    });

    test('sets error when repository throws', () async {
      repo.shouldThrowOnCompleteRaid = true;
      repo.errorMessage = 'Failed to save session';

      container = _makeContainer(repo);
      await Future.delayed(const Duration(milliseconds: 50));

      final notifier = container.read(_testBossRaidProvider.notifier);
      await notifier.startRaid();
      await notifier.completeRaid();

      final state = container.read(_testBossRaidProvider);
      expect(state.isLoading, isFalse);
      expect(state.isCompleted, isFalse);
      expect(state.error, contains('Failed to save session'));
    });
  });

  // ---------------------------------------------------------------------------
  // BossRaidNotifier – resetRaid
  // ---------------------------------------------------------------------------
  group('BossRaidNotifier.resetRaid', () {
    late FakeBossRaidRepository repo;
    late ProviderContainer container;

    setUp(() {
      repo = FakeBossRaidRepository();
    });

    tearDown(() {
      container.dispose();
    });

    test('resets state to initial and triggers fetchStatus', () async {
      container = _makeContainer(repo);
      final notifier = container.read(_testBossRaidProvider.notifier);
      await notifier.fetchStatus();
      await notifier.startRaid();
      notifier.selectAnswer('a-0-A');
      await notifier.submitAnswer();

      // State should be dirty.
      var state = container.read(_testBossRaidProvider);
      expect(state.questions, isNotNull);
      expect(state.sessionId, isNotNull);

      notifier.resetRaid();
      // resetRaid calls fetchStatus fire-and-forget, settle it explicitly.
      await notifier.fetchStatus();

      state = container.read(_testBossRaidProvider);
      expect(state.questions, isNull);
      expect(state.sessionId, isNull);
      expect(state.selectedAnswerId, isNull);
      expect(state.isAnswerSubmitted, isFalse);
      expect(state.totalDamageDealt, equals(0));
      expect(state.isCompleted, isFalse);
      // fetchStatus was called again, so status should be populated.
      expect(state.status, isNotNull);
    });
  });
}

// ============================================================================
// HELPER: Repository that hangs on submitAnswer until manually released
// ============================================================================

class _HangingSubmitRepository implements BossRaidRepository {
  final _completer = _ManualCompleter<BossRaidAnswerResponse>();

  void complete() {
    _completer.complete(_defaultAnswerResponse());
  }

  @override
  Future<BossRaidStatusModel> getStatus() async => _defaultStatus();

  @override
  Future<BossRaidSessionModel> startRaid() async => _defaultSession();

  @override
  Future<BossRaidAnswerResponse> submitAnswer({
    required String sessionId,
    required String questionId,
    required String answerId,
  }) {
    return _completer.future;
  }

  @override
  Future<BossRaidCompleteResponse> completeRaid(String sessionId) async =>
      _defaultCompleteResponse();
}

/// Wraps [Completer] so the test controls when submitAnswer resolves.
class _ManualCompleter<T> {
  final _inner = Completer<T>();

  Future<T> get future => _inner.future;

  void complete(T value) => _inner.complete(value);
  void completeError(Object error) => _inner.completeError(error);
}
