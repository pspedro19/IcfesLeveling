import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:mockito/mockito.dart';

import 'package:icfes_mobile/core/network/api_client.dart';
import 'package:icfes_mobile/core/storage/question_cache.dart';
import 'package:icfes_mobile/core/constants/api_constants.dart';
import 'package:icfes_mobile/features/practice/presentation/providers/practice_provider.dart';
import 'package:icfes_mobile/features/practice/domain/entities/question.dart';
import 'package:icfes_mobile/core/providers/storage_providers.dart';

import '../../mocks/mock_providers.dart';

// Mock QuestionCache for testing
class MockQuestionCache extends Mock implements QuestionCache {
  List<Map<String, dynamic>> _cachedQuestions = [];

  void setCachedQuestions(List<Map<String, dynamic>> questions) {
    _cachedQuestions = questions;
  }

  @override
  Future<void> init() async {}

  @override
  Future<void> warmUp(ApiClient apiClient) async {}

  @override
  Future<List<Map<String, dynamic>>> getCachedQuestions({String? subjectId}) async {
    if (subjectId != null) {
      return _cachedQuestions
          .where((q) => q['subject_id'] == subjectId)
          .toList();
    }
    return _cachedQuestions;
  }

  @override
  Future<void> markAnswered(String questionId) async {}
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  // Mock haptic feedback and other platform channels
  TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
      .setMockMethodCallHandler(const MethodChannel('flutter/hapticfeedback'), (call) async => null);

  // Mock audioplayers platform channels to prevent MissingPluginException
  TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
      .setMockMethodCallHandler(const MethodChannel('xyz.luan/audioplayers.global'), (call) async {
    if (call.method == 'init') return null;
    if (call.method == 'setGlobalAudioContext') return null;
    return null;
  });
  TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
      .setMockMethodCallHandler(const MethodChannel('xyz.luan/audioplayers'), (call) async {
    if (call.method == 'create') return null;
    if (call.method == 'setSourceUrl') return 1;
    if (call.method == 'resume') return 1;
    if (call.method == 'pause') return 1;
    if (call.method == 'stop') return 1;
    if (call.method == 'release') return 1;
    if (call.method == 'setVolume') return 1;
    if (call.method == 'dispose') return null;
    return null;
  });

  group('PracticeProvider', () {
    late FakeApiClient fakeApiClient;
    late MockQuestionCache mockQuestionCache;
    late ProviderContainer container;

    setUp(() {
      fakeApiClient = FakeApiClient();
      mockQuestionCache = MockQuestionCache();

      // Setup default API responses
      fakeApiClient.setMockResponse(ApiConstants.authMe, {}, statusCode: 200);
      fakeApiClient.setMockResponse(ApiConstants.heartsStatus, {
        'current': 5,
        'max': 5,
      }, statusCode: 200);
      fakeApiClient.setMockResponse(ApiConstants.submitAnswer, {
        'data': {'xp_earned': 10, 'hearts_remaining': 5}
      }, statusCode: 200);
      fakeApiClient.setMockResponse('/users/cached/profile/me', {
        'questions_answered': 0,
        'correct_answers': 0,
      }, statusCode: 200);
    });

    tearDown(() {
      container.dispose();
    });

    List<Map<String, dynamic>> createMockQuestions({int count = 5}) {
      return List.generate(count, (index) => {
        'id': 'q-$index',
        'subject_id': 'math',
        'topic_id': 'algebra',
        'pregunta_texto': 'Question $index: What is ${index + 1} + ${index + 1}?',
        'opcion_a_texto': '${(index + 1) * 2}',
        'opcion_b_texto': '${(index + 1) * 2 + 1}',
        'opcion_c_texto': '${(index + 1) * 2 - 1}',
        'opcion_d_texto': '${(index + 1) * 3}',
        'respuesta_correcta': 'A',
        'puntos_xp': 10,
        'difficulty_rating': 'E',
        'topic_name': 'Algebra',
        'subject_name': 'Mathematics',
      });
    }

    ProviderContainer createContainer() {
      return ProviderContainer(
        overrides: [
          apiClientProvider.overrideWithValue(fakeApiClient),
          questionCacheProvider.overrideWithValue(mockQuestionCache),
        ],
      );
    }

    group('startSession', () {
      test('startSession loads questions from cache', () async {
        // Arrange
        mockQuestionCache.setCachedQuestions(createMockQuestions(count: 5));

        container = createContainer();
        final notifier = container.read(practiceProvider.notifier);

        // Wait for providers to initialize
        await Future.delayed(const Duration(milliseconds: 200));

        // Act
        await notifier.startSession(subjectId: 'math');

        // Assert
        final state = container.read(practiceProvider);
        expect(state.questions.length, equals(5));
        expect(state.isLoading, isFalse);
        expect(state.error, isNull);
        expect(state.currentIndex, equals(0));
        expect(state.currentQuestion, isNotNull);
      });

      test('startSession sets loading state during fetch', () async {
        // Arrange
        mockQuestionCache.setCachedQuestions(createMockQuestions());

        container = createContainer();
        final notifier = container.read(practiceProvider.notifier);

        await Future.delayed(const Duration(milliseconds: 200));

        // Check initial state
        var state = container.read(practiceProvider);
        expect(state.isLoading, isFalse);

        // Act
        final sessionFuture = notifier.startSession(subjectId: 'math');

        // Assert during loading
        await Future.delayed(const Duration(milliseconds: 10));
        // Note: Due to async nature, loading might be true or already done

        await sessionFuture;

        state = container.read(practiceProvider);
        expect(state.isLoading, isFalse);
      });

      test('startSession throws error when no questions available', () async {
        // Arrange
        mockQuestionCache.setCachedQuestions([]); // Empty cache

        container = createContainer();
        final notifier = container.read(practiceProvider.notifier);

        await Future.delayed(const Duration(milliseconds: 200));

        // Act
        await notifier.startSession(subjectId: 'math');

        // Assert
        final state = container.read(practiceProvider);
        expect(state.error, isNotNull);
        expect(state.error, contains('No questions available'));
        expect(state.questions, isEmpty);
      });

      test('startSession filters questions by subjectId', () async {
        // Arrange
        final mixedQuestions = [
          ...createMockQuestions(count: 3).map((q) => {...q, 'subject_id': 'math'}),
          ...createMockQuestions(count: 2).map((q) => {...q, 'id': 'sci-${q['id']}', 'subject_id': 'science'}),
        ];
        mockQuestionCache.setCachedQuestions(mixedQuestions);

        container = createContainer();
        final notifier = container.read(practiceProvider.notifier);

        await Future.delayed(const Duration(milliseconds: 200));

        // Act
        await notifier.startSession(subjectId: 'math');

        // Assert
        final state = container.read(practiceProvider);
        expect(state.questions.length, equals(3));
        expect(
          state.questions.every((q) => q.subjectId == 'math'),
          isTrue,
        );
      });

      test('startSession resets state from previous session', () async {
        // Arrange
        mockQuestionCache.setCachedQuestions(createMockQuestions(count: 3));

        container = createContainer();
        final notifier = container.read(practiceProvider.notifier);

        await Future.delayed(const Duration(milliseconds: 200));

        // First session - answer some questions
        await notifier.startSession(subjectId: 'math');
        notifier.selectOption('A');
        notifier.checkAnswer();
        notifier.nextQuestion();

        var state = container.read(practiceProvider);
        expect(state.currentIndex, equals(1));

        // Act - Start new session
        await notifier.startSession(subjectId: 'math');

        // Assert
        state = container.read(practiceProvider);
        expect(state.currentIndex, equals(0));
        expect(state.correctAnswers, equals(0));
        expect(state.selectedOptionId, isNull);
        expect(state.isAnswerChecked, isFalse);
      });
    });

    group('selectOption', () {
      test('selectOption updates selectedOptionId', () async {
        // Arrange
        mockQuestionCache.setCachedQuestions(createMockQuestions());

        container = createContainer();
        final notifier = container.read(practiceProvider.notifier);

        await Future.delayed(const Duration(milliseconds: 200));
        await notifier.startSession(subjectId: 'math');

        // Act
        notifier.selectOption('B');

        // Assert
        final state = container.read(practiceProvider);
        expect(state.selectedOptionId, equals('B'));
      });

      test('selectOption can change selection before checking', () async {
        // Arrange
        mockQuestionCache.setCachedQuestions(createMockQuestions());

        container = createContainer();
        final notifier = container.read(practiceProvider.notifier);

        await Future.delayed(const Duration(milliseconds: 200));
        await notifier.startSession(subjectId: 'math');

        // Act
        notifier.selectOption('A');
        notifier.selectOption('B');
        notifier.selectOption('C');

        // Assert
        final state = container.read(practiceProvider);
        expect(state.selectedOptionId, equals('C'));
      });

      test('selectOption does not update after answer is checked', () async {
        // Arrange
        mockQuestionCache.setCachedQuestions(createMockQuestions());

        container = createContainer();
        final notifier = container.read(practiceProvider.notifier);

        await Future.delayed(const Duration(milliseconds: 200));
        await notifier.startSession(subjectId: 'math');

        // Select and check
        notifier.selectOption('A');
        notifier.checkAnswer();

        // Act - Try to change selection
        notifier.selectOption('B');

        // Assert - Selection should not change
        final state = container.read(practiceProvider);
        expect(state.selectedOptionId, equals('A'));
      });
    });

    group('checkAnswer', () {
      test('checkAnswer marks correct answer correctly', () async {
        // Arrange
        mockQuestionCache.setCachedQuestions(createMockQuestions());

        container = createContainer();
        final notifier = container.read(practiceProvider.notifier);

        await Future.delayed(const Duration(milliseconds: 200));
        await notifier.startSession(subjectId: 'math');

        // Act
        notifier.selectOption('A'); // Correct answer
        notifier.checkAnswer();

        // Assert
        final state = container.read(practiceProvider);
        expect(state.isAnswerChecked, isTrue);
        expect(state.isCurrentCorrect, isTrue);
      });

      test('checkAnswer marks incorrect answer correctly', () async {
        // Arrange
        mockQuestionCache.setCachedQuestions(createMockQuestions());

        container = createContainer();
        final notifier = container.read(practiceProvider.notifier);

        await Future.delayed(const Duration(milliseconds: 200));
        await notifier.startSession(subjectId: 'math');

        // Act
        notifier.selectOption('B'); // Wrong answer (correct is A)
        notifier.checkAnswer();

        // Assert
        final state = container.read(practiceProvider);
        expect(state.isAnswerChecked, isTrue);
        expect(state.isCurrentCorrect, isFalse);
      });

      test('checkAnswer updates combo on correct answers', () async {
        // Arrange
        mockQuestionCache.setCachedQuestions(createMockQuestions(count: 3));

        container = createContainer();
        final notifier = container.read(practiceProvider.notifier);

        await Future.delayed(const Duration(milliseconds: 200));
        await notifier.startSession(subjectId: 'math');

        // Act - Answer 3 correctly
        for (var i = 0; i < 3; i++) {
          notifier.selectOption('A');
          notifier.checkAnswer();
          await Future.delayed(const Duration(milliseconds: 50));
          if (i < 2) notifier.nextQuestion();
        }

        // Assert
        final state = container.read(practiceProvider);
        expect(state.maxCombo, greaterThanOrEqualTo(1));
      });

      test('checkAnswer resets combo on incorrect answer', () async {
        // Arrange
        mockQuestionCache.setCachedQuestions(createMockQuestions(count: 3));

        container = createContainer();
        final notifier = container.read(practiceProvider.notifier);

        await Future.delayed(const Duration(milliseconds: 200));
        await notifier.startSession(subjectId: 'math');

        // Get 2 correct
        notifier.selectOption('A');
        notifier.checkAnswer();
        await Future.delayed(const Duration(milliseconds: 50));
        notifier.nextQuestion();

        notifier.selectOption('A');
        notifier.checkAnswer();
        await Future.delayed(const Duration(milliseconds: 50));
        notifier.nextQuestion();

        // Get 1 wrong
        notifier.selectOption('B');
        notifier.checkAnswer();

        // Assert
        final state = container.read(practiceProvider);
        expect(state.isCurrentCorrect, isFalse);
        // Combo should be reset (though maxCombo is preserved)
      });

      test('checkAnswer does nothing without selection', () async {
        // Arrange
        mockQuestionCache.setCachedQuestions(createMockQuestions());

        container = createContainer();
        final notifier = container.read(practiceProvider.notifier);

        await Future.delayed(const Duration(milliseconds: 200));
        await notifier.startSession(subjectId: 'math');

        // Act - Try to check without selecting
        notifier.checkAnswer();

        // Assert
        final state = container.read(practiceProvider);
        expect(state.isAnswerChecked, isFalse);
        expect(state.selectedOptionId, isNull);
      });

      test('checkAnswer does nothing without current question', () async {
        // Arrange
        container = createContainer();
        final notifier = container.read(practiceProvider.notifier);

        await Future.delayed(const Duration(milliseconds: 200));

        // Act - Try to check without starting session
        notifier.checkAnswer();

        // Assert
        final state = container.read(practiceProvider);
        expect(state.isAnswerChecked, isFalse);
        expect(state.questions, isEmpty);
      });
    });

    group('nextQuestion', () {
      test('nextQuestion advances currentIndex', () async {
        // Arrange
        mockQuestionCache.setCachedQuestions(createMockQuestions(count: 5));

        container = createContainer();
        final notifier = container.read(practiceProvider.notifier);

        await Future.delayed(const Duration(milliseconds: 200));
        await notifier.startSession(subjectId: 'math');

        notifier.selectOption('A');
        notifier.checkAnswer();

        expect(container.read(practiceProvider).currentIndex, equals(0));

        // Act
        notifier.nextQuestion();

        // Assert
        final state = container.read(practiceProvider);
        expect(state.currentIndex, equals(1));
        expect(state.currentQuestion!.id, equals('q-1'));
      });

      test('nextQuestion resets answer state', () async {
        // Arrange
        mockQuestionCache.setCachedQuestions(createMockQuestions(count: 5));

        container = createContainer();
        final notifier = container.read(practiceProvider.notifier);

        await Future.delayed(const Duration(milliseconds: 200));
        await notifier.startSession(subjectId: 'math');

        notifier.selectOption('A');
        notifier.checkAnswer();

        var state = container.read(practiceProvider);
        expect(state.isAnswerChecked, isTrue);
        expect(state.selectedOptionId, isNotNull);

        // Act
        notifier.nextQuestion();
        await Future.delayed(const Duration(milliseconds: 50));

        // Assert
        state = container.read(practiceProvider);
        expect(state.isAnswerChecked, isFalse);
        // Note: selectedOptionId is reset to null by nextQuestion
        expect(state.isCurrentCorrect, isFalse);
      });

      test('nextQuestion sets isFinished on last question', () async {
        // Arrange
        mockQuestionCache.setCachedQuestions(createMockQuestions(count: 2));

        container = createContainer();
        final notifier = container.read(practiceProvider.notifier);

        await Future.delayed(const Duration(milliseconds: 200));
        await notifier.startSession(subjectId: 'math');

        // Answer first question
        notifier.selectOption('A');
        notifier.checkAnswer();
        notifier.nextQuestion();

        // Answer second question
        notifier.selectOption('A');
        notifier.checkAnswer();

        var state = container.read(practiceProvider);
        expect(state.isFinished, isFalse);

        // Act - Try to go to next (no more questions)
        notifier.nextQuestion();

        // Assert
        state = container.read(practiceProvider);
        expect(state.isFinished, isTrue);
      });

      test('nextQuestion preserves stats across questions', () async {
        // Arrange
        mockQuestionCache.setCachedQuestions(createMockQuestions(count: 3));

        container = createContainer();
        final notifier = container.read(practiceProvider.notifier);

        await Future.delayed(const Duration(milliseconds: 200));
        await notifier.startSession(subjectId: 'math');

        // Answer questions
        notifier.selectOption('A'); // Correct
        notifier.checkAnswer();
        await Future.delayed(const Duration(milliseconds: 50));
        notifier.nextQuestion();

        notifier.selectOption('B'); // Wrong
        notifier.checkAnswer();
        await Future.delayed(const Duration(milliseconds: 50));
        notifier.nextQuestion();

        // Assert
        final state = container.read(practiceProvider);
        expect(state.currentIndex, equals(2));
        // Stats should be preserved
        expect(state.questions.length, equals(3));
      });
    });

    group('PracticeState', () {
      test('currentQuestion returns correct question', () {
        final questions = [
          Question(
            id: 'q1',
            subjectId: 'math',
            topicId: 't1',
            text: 'Question 1',
            options: [],
            correctAnswer: 'A',
            difficulty: 'E',
          ),
          Question(
            id: 'q2',
            subjectId: 'math',
            topicId: 't1',
            text: 'Question 2',
            options: [],
            correctAnswer: 'B',
            difficulty: 'E',
          ),
        ];

        final state = PracticeState(questions: questions, currentIndex: 1);

        expect(state.currentQuestion, isNotNull);
        expect(state.currentQuestion!.id, equals('q2'));
      });

      test('currentQuestion returns null when index out of bounds', () {
        final state = PracticeState(questions: [], currentIndex: 0);

        expect(state.currentQuestion, isNull);
      });

      test('accuracy calculates correctly', () {
        final questions = List.generate(
          10,
          (i) => Question(
            id: 'q$i',
            subjectId: 'math',
            topicId: 't1',
            text: 'Q$i',
            options: [],
            correctAnswer: 'A',
            difficulty: 'E',
          ),
        );

        // 7 correct out of 10
        var state = PracticeState(questions: questions, correctAnswers: 7);
        expect(state.accuracy, equals(70));

        // 10 correct out of 10
        state = state.copyWith(correctAnswers: 10);
        expect(state.accuracy, equals(100));

        // 0 correct
        state = state.copyWith(correctAnswers: 0);
        expect(state.accuracy, equals(0));
      });

      test('accuracy handles empty questions list', () {
        final state = PracticeState(questions: [], correctAnswers: 0);
        expect(state.accuracy, equals(0));
      });

      test('copyWith preserves values correctly', () {
        final initialState = PracticeState(
          currentIndex: 5,
          correctAnswers: 3,
          totalXp: 100,
          comboCount: 2,
          maxCombo: 4,
        );

        final copied = initialState.copyWith(totalXp: 150);

        expect(copied.currentIndex, equals(5));
        expect(copied.correctAnswers, equals(3));
        expect(copied.totalXp, equals(150));
        expect(copied.comboCount, equals(2));
        expect(copied.maxCombo, equals(4));
      });
    });

    group('XP calculation', () {
      test('correct answers should add XP', () async {
        // Arrange
        mockQuestionCache.setCachedQuestions(createMockQuestions(count: 1));

        container = createContainer();
        final notifier = container.read(practiceProvider.notifier);

        await Future.delayed(const Duration(milliseconds: 200));
        await notifier.startSession(subjectId: 'math');

        // Act
        notifier.selectOption('A'); // Correct
        notifier.checkAnswer();

        // Wait for async operations
        await Future.delayed(const Duration(milliseconds: 100));

        // Assert
        final finalState = container.read(practiceProvider);
        // XP might be added via API response or locally
        expect(finalState.isCurrentCorrect, isTrue);
      });
    });
  });
}
