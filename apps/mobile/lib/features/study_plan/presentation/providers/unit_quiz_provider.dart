import 'dart:async';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../practice/domain/entities/question.dart';
import '../../../practice/data/models/question_model.dart';
import '../../../../core/storage/question_cache.dart';
import '../../../../core/utils/app_haptics.dart';
import '../../../../core/network/api_client.dart';
import '../../../../core/constants/api_constants.dart';
import '../../../../shared/providers/hearts_provider.dart';
import '../../../../shared/providers/user_stats_provider.dart';
import '../../../../shared/providers/streak_provider.dart';
import '../../../engagement/presentation/providers/engagement_provider.dart';
import '../../../../core/providers/storage_providers.dart';
import '../../../../core/services/combo_service.dart';
import '../../../../core/services/audio_service.dart';

/// State for unit quiz session
class UnitQuizState {
  final String unitId;
  final String unitName;
  final List<Question> questions;
  final int currentIndex;
  final int correctAnswers;
  final int totalXp;
  final bool isFinished;
  final String? selectedOptionId;
  final bool isAnswerChecked;
  final bool isCurrentCorrect;
  final int comboCount;
  final int maxCombo;
  final bool isLoading;
  final String? error;
  final int xpAwarded;
  final int lastBaseXp;
  final int lastBonusXp;
  final int totalBonusXp;
  final double previousMastery;
  final double newMastery;

  UnitQuizState({
    this.unitId = '',
    this.unitName = '',
    this.questions = const [],
    this.currentIndex = 0,
    this.correctAnswers = 0,
    this.totalXp = 0,
    this.isFinished = false,
    this.selectedOptionId,
    this.isAnswerChecked = false,
    this.isCurrentCorrect = false,
    this.comboCount = 0,
    this.maxCombo = 0,
    this.isLoading = false,
    this.error,
    this.xpAwarded = 0,
    this.lastBaseXp = 0,
    this.lastBonusXp = 0,
    this.totalBonusXp = 0,
    this.previousMastery = 0.0,
    this.newMastery = 0.0,
  });

  Question? get currentQuestion =>
      currentIndex < questions.length ? questions[currentIndex] : null;

  /// Get current combo level
  ComboLevel get comboLevel => ComboService.getComboLevel(comboCount);

  /// Get combo display configuration
  ComboDisplay get comboDisplay => ComboService.getComboDisplay(comboCount);

  /// Calculate accuracy percentage
  int get accuracy => questions.isEmpty ? 0 : ((correctAnswers / questions.length) * 100).toInt();

  /// Calculate score string
  String get scoreText => '$correctAnswers/${questions.length}';

  /// Calculate stars based on accuracy (0-3 stars)
  int get stars {
    final acc = accuracy;
    if (acc >= 90) return 3;
    if (acc >= 70) return 2;
    if (acc >= 50) return 1;
    return 0;
  }

  /// Calculate mastery improvement
  double get masteryImprovement => newMastery - previousMastery;

  UnitQuizState copyWith({
    String? unitId,
    String? unitName,
    List<Question>? questions,
    int? currentIndex,
    int? correctAnswers,
    int? totalXp,
    bool? isFinished,
    String? selectedOptionId,
    bool? isAnswerChecked,
    bool? isCurrentCorrect,
    int? comboCount,
    int? maxCombo,
    bool? isLoading,
    String? error,
    int? xpAwarded,
    int? lastBaseXp,
    int? lastBonusXp,
    int? totalBonusXp,
    double? previousMastery,
    double? newMastery,
  }) {
    return UnitQuizState(
      unitId: unitId ?? this.unitId,
      unitName: unitName ?? this.unitName,
      questions: questions ?? this.questions,
      currentIndex: currentIndex ?? this.currentIndex,
      correctAnswers: correctAnswers ?? this.correctAnswers,
      totalXp: totalXp ?? this.totalXp,
      isFinished: isFinished ?? this.isFinished,
      selectedOptionId: selectedOptionId,
      isAnswerChecked: isAnswerChecked ?? this.isAnswerChecked,
      isCurrentCorrect: isCurrentCorrect ?? this.isCurrentCorrect,
      comboCount: comboCount ?? this.comboCount,
      maxCombo: maxCombo ?? this.maxCombo,
      isLoading: isLoading ?? this.isLoading,
      error: error,
      xpAwarded: xpAwarded ?? this.xpAwarded,
      lastBaseXp: lastBaseXp ?? this.lastBaseXp,
      lastBonusXp: lastBonusXp ?? this.lastBonusXp,
      totalBonusXp: totalBonusXp ?? this.totalBonusXp,
      previousMastery: previousMastery ?? this.previousMastery,
      newMastery: newMastery ?? this.newMastery,
    );
  }
}

/// Notifier for unit quiz state management
class UnitQuizNotifier extends StateNotifier<UnitQuizState> {
  final QuestionCache _questionCache;
  final ApiClient _apiClient;
  final EngagementNotifier _engagementNotifier;
  final HeartsNotifier _heartsNotifier;
  final UserStatsNotifier _userStatsNotifier;
  final StreakNotifier _streakNotifier;
  final AudioService _audioService;
  Timer? _comboTimer;
  final Stopwatch _questionStopwatch = Stopwatch();
  static const _comboTimeoutSeconds = ComboService.comboTimeoutSeconds;

  UnitQuizNotifier(
    this._questionCache,
    this._apiClient,
    this._engagementNotifier,
    this._heartsNotifier,
    this._userStatsNotifier,
    this._streakNotifier,
    this._audioService,
  ) : super(UnitQuizState());

  @override
  void dispose() {
    _comboTimer?.cancel();
    super.dispose();
  }

  /// Start a quiz session for a specific unit
  Future<void> startQuiz({required String unitId}) async {
    state = state.copyWith(isLoading: true, error: null, unitId: unitId);

    try {
      // Fetch unit info and questions from backend
      String unitName = 'Unidad';
      double previousMastery = 0.0;

      try {
        final unitInfoResponse = await _apiClient.get(
          '${ApiConstants.mobilePrefix}/units/$unitId',
        );
        if (unitInfoResponse.statusCode == 200 && unitInfoResponse.data != null) {
          final data = unitInfoResponse.data['data'] ?? unitInfoResponse.data;
          unitName = data['name'] ?? data['unit_name'] ?? 'Unidad';
          previousMastery = (data['mastery'] ?? data['mastery_level'] ?? 0.0).toDouble();
        }
      } catch (_) {
        // Unit info fetch failed, continue with defaults
      }

      // Try to fetch unit-specific questions from backend
      List<Question> questions = [];

      try {
        final questionsResponse = await _apiClient.get(
          '${ApiConstants.mobilePrefix}/units/$unitId/questions',
        );

        if (questionsResponse.statusCode == 200 && questionsResponse.data != null) {
          final questionsData = questionsResponse.data['data'] ?? questionsResponse.data;
          if (questionsData is List) {
            questions = questionsData
                .map((q) => QuestionModel.fromJson(q as Map<String, dynamic>))
                .toList();
          }
        }
      } catch (e) {
        // Fallback to cached questions if API fails
        print('Failed to fetch unit questions from API: $e');
      }

      // If no questions from API, fallback to cache
      if (questions.isEmpty) {
        final cached = await _questionCache.getCachedQuestions(subjectId: unitId);
        questions = cached.map((q) => QuestionModel.fromJson(q)).toList();

        // If still empty, try warming up the cache
        if (questions.isEmpty) {
          await _questionCache.warmUp(_apiClient);
          final cachedRetry = await _questionCache.getCachedQuestions(subjectId: unitId);
          questions = cachedRetry.map((q) => QuestionModel.fromJson(q)).toList();
        }
      }

      // Limit to 10 questions per unit quiz
      if (questions.length > 10) {
        questions.shuffle();
        questions = questions.take(10).toList();
      }

      if (questions.isEmpty) {
        throw Exception('No hay preguntas disponibles para esta unidad.');
      }

      state = UnitQuizState(
        unitId: unitId,
        unitName: unitName,
        questions: questions,
        isLoading: false,
        previousMastery: previousMastery,
      );

      _startComboTimer();
      _questionStopwatch.reset();
      _questionStopwatch.start();
    } catch (e) {
      state = state.copyWith(isLoading: false, error: e.toString());
    }
  }

  /// Select an answer option
  void selectOption(String optionId) {
    if (state.isAnswerChecked) return;
    AppHaptics.light();
    state = state.copyWith(selectedOptionId: optionId);
    _startComboTimer();
  }

  /// Check the selected answer
  void checkAnswer() {
    final current = state.currentQuestion;
    if (current == null || state.selectedOptionId == null) return;

    _comboTimer?.cancel();
    _questionStopwatch.stop();
    final timeSpentSeconds = (_questionStopwatch.elapsedMilliseconds / 1000).ceil();

    final isCorrect = state.selectedOptionId == current.correctAnswer;

    if (isCorrect) {
      AppHaptics.success();
      _incrementCombo();
    } else {
      AppHaptics.error();
      _resetCombo();
    }

    // Calculate XP with combo bonus
    final baseXp = isCorrect ? _calculateBaseXp(current) : 0;
    final bonusXp = isCorrect ? ComboService.calculateBonusXP(state.comboCount) : 0;
    final totalXpForQuestion = baseXp + bonusXp;

    // Sync with engagement providers
    if (isCorrect) {
      _engagementNotifier.addXp(totalXpForQuestion);
    } else {
      _heartsNotifier.useHeart();
    }

    // Update user stats
    _userStatsNotifier.updateAfterAnswer(isCorrect);

    state = state.copyWith(
      isAnswerChecked: true,
      isCurrentCorrect: isCorrect,
      correctAnswers: isCorrect ? state.correctAnswers + 1 : state.correctAnswers,
      totalXp: state.totalXp + totalXpForQuestion,
      xpAwarded: totalXpForQuestion,
      lastBaseXp: baseXp,
      lastBonusXp: bonusXp,
      totalBonusXp: state.totalBonusXp + bonusXp,
    );

    // Submit answer to backend
    _submitAnswer(current.id, state.selectedOptionId!, timeSpentSeconds, totalXpForQuestion, bonusXp);
  }

  /// Move to the next question
  void nextQuestion() {
    if (state.currentIndex + 1 < state.questions.length) {
      state = state.copyWith(
        currentIndex: state.currentIndex + 1,
        isAnswerChecked: false,
        isCurrentCorrect: false,
        selectedOptionId: null,
      );
      _startComboTimer();
      _questionStopwatch.reset();
      _questionStopwatch.start();
    } else {
      _finishQuiz();
    }
  }

  /// Finish the quiz and calculate final results
  void _finishQuiz() {
    _comboTimer?.cancel();

    // Calculate new mastery based on performance
    final accuracy = state.correctAnswers / state.questions.length;
    final masteryGain = accuracy * 0.2; // Max 20% mastery gain per quiz
    final newMastery = (state.previousMastery + masteryGain).clamp(0.0, 1.0);

    state = state.copyWith(
      isFinished: true,
      newMastery: newMastery,
    );

    // Notify streak provider
    _streakNotifier.onPracticeCompleted();

    // Submit quiz results to backend
    _submitQuizResults();
  }

  /// Retry the quiz
  void retryQuiz() {
    final unitId = state.unitId;
    state = UnitQuizState();
    startQuiz(unitId: unitId);
  }

  /// Increment combo on correct answer
  void _incrementCombo() {
    final newCombo = state.comboCount + 1;
    final newMaxCombo = newCombo > state.maxCombo ? newCombo : state.maxCombo;

    state = state.copyWith(
      comboCount: newCombo,
      maxCombo: newMaxCombo,
    );

    // Play combo sound based on level
    final soundId = ComboService.getSoundForCombo(newCombo);
    if (soundId != null) {
      _audioService.playComboSound(soundId);
    }
  }

  /// Reset combo on wrong answer or timeout
  void _resetCombo() {
    state = state.copyWith(comboCount: 0);
  }

  /// Start/restart the combo timer
  void _startComboTimer() {
    _comboTimer?.cancel();
    _comboTimer = Timer(const Duration(seconds: _comboTimeoutSeconds), () {
      if (state.comboCount > 0) {
        _resetCombo();
      }
    });
  }

  /// Calculate base XP for a question
  int _calculateBaseXp(Question question) {
    if (question.xpReward > 0) {
      return question.xpReward;
    }

    switch (question.attemptType) {
      case AttemptType.validReview:
        return 5;
      case AttemptType.invalidRepeat:
        return 0;
      case AttemptType.newQuestion:
      default:
        return 10;
    }
  }

  /// Submit answer to backend
  Future<void> _submitAnswer(
    String questionId,
    String answerId,
    int timeSpentSeconds,
    int totalXp,
    int bonusXp,
  ) async {
    try {
      final response = await _apiClient.post(
        ApiConstants.submitAnswer,
        data: {
          'question_id': questionId,
          'answer_id': answerId,
          'time_spent_seconds': timeSpentSeconds,
          'session_type': 'unit_quiz',
          'unit_id': state.unitId,
          'combo_count': state.comboCount,
          'bonus_xp': bonusXp,
          'total_xp': totalXp,
        },
      );

      if (response.statusCode == 200 && response.data != null) {
        final data = response.data['data'] ?? response.data;
        final heartsRemaining = data['hearts_remaining'] as int?;
        if (heartsRemaining != null) {
          _heartsNotifier.setHearts(heartsRemaining);
        }
      }
    } catch (e) {
      // Offline queue should handle this via interceptor
      print('Failed to submit answer: $e');
    }
  }

  /// Submit quiz results to backend
  Future<void> _submitQuizResults() async {
    try {
      await _apiClient.post(
        '${ApiConstants.mobilePrefix}/units/${state.unitId}/quiz-complete',
        data: {
          'correct_answers': state.correctAnswers,
          'total_questions': state.questions.length,
          'total_xp': state.totalXp,
          'total_bonus_xp': state.totalBonusXp,
          'max_combo': state.maxCombo,
          'accuracy': state.accuracy,
          'new_mastery': state.newMastery,
        },
      );
    } catch (e) {
      print('Failed to submit quiz results: $e');
    }
  }
}

/// Provider for unit quiz state
final unitQuizProvider = StateNotifierProvider.autoDispose<UnitQuizNotifier, UnitQuizState>((ref) {
  final cache = ref.watch(questionCacheProvider);
  final apiClient = ref.watch(apiClientProvider);
  final engagement = ref.read(engagementProvider.notifier);
  final hearts = ref.read(heartsProvider.notifier);
  final userStats = ref.read(userStatsProvider.notifier);
  final streak = ref.read(streakProvider.notifier);
  final audioService = ref.watch(audioServiceProvider);

  return UnitQuizNotifier(
    cache,
    apiClient,
    engagement,
    hearts,
    userStats,
    streak,
    audioService,
  );
});
