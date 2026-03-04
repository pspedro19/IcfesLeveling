import 'dart:async';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../domain/entities/question.dart';
import '../../data/models/question_model.dart';
import '../../data/models/spaced_repetition_models.dart';
import '../../../../core/storage/question_cache.dart';
import '../../../../core/learning/domain/adaptive_engine.dart';
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
import 'spaced_repetition_provider.dart';

class PracticeState {
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

  PracticeState({
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
  });

  Question? get currentQuestion =>
      currentIndex < questions.length ? questions[currentIndex] : null;

  /// Get current combo level
  ComboLevel get comboLevel => ComboService.getComboLevel(comboCount);

  /// Get combo display configuration
  ComboDisplay get comboDisplay => ComboService.getComboDisplay(comboCount);

  PracticeState copyWith({
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
  }) {
    return PracticeState(
      questions: questions ?? this.questions,
      currentIndex: currentIndex ?? this.currentIndex,
      correctAnswers: correctAnswers ?? this.correctAnswers,
      totalXp: totalXp ?? this.totalXp,
      isFinished: isFinished ?? this.isFinished,
      selectedOptionId: selectedOptionId ?? this.selectedOptionId,
      isAnswerChecked: isAnswerChecked ?? this.isAnswerChecked,
      isCurrentCorrect: isCurrentCorrect ?? this.isCurrentCorrect,
      comboCount: comboCount ?? this.comboCount,
      maxCombo: maxCombo ?? this.maxCombo,
      isLoading: isLoading ?? this.isLoading,
      error: error ?? this.error,
      xpAwarded: xpAwarded ?? this.xpAwarded,
      lastBaseXp: lastBaseXp ?? this.lastBaseXp,
      lastBonusXp: lastBonusXp ?? this.lastBonusXp,
      totalBonusXp: totalBonusXp ?? this.totalBonusXp,
    );
  }

  int get accuracy => questions.isEmpty ? 0 : ((correctAnswers / questions.length) * 100).toInt();
}

class PracticeNotifier extends StateNotifier<PracticeState> {
  final QuestionCache _questionCache;
  final AdaptiveEngine _adaptiveEngine;
  final ApiClient _apiClient;
  final EngagementNotifier _engagementNotifier;
  final HeartsNotifier _heartsNotifier;
  final UserStatsNotifier _userStatsNotifier;
  final StreakNotifier _streakNotifier;
  final AudioService _audioService;
  final SpacedRepetitionNotifier _spacedRepetitionNotifier;
  Timer? _comboTimer;
  final Stopwatch _questionStopwatch = Stopwatch();
  static const _comboTimeoutSeconds = ComboService.comboTimeoutSeconds;

  /// Response time thresholds for SM-2 quality rating (in milliseconds)
  static const int _fastResponseThresholdMs = 5000; // 5 seconds = EASY
  static const int _slowResponseThresholdMs = 15000; // 15 seconds = HARD

  PracticeNotifier(
    this._questionCache,
    this._adaptiveEngine,
    this._apiClient,
    this._engagementNotifier,
    this._heartsNotifier,
    this._userStatsNotifier,
    this._streakNotifier,
    this._audioService,
    this._spacedRepetitionNotifier,
  ) : super(PracticeState());

  @override
  void dispose() {
    _comboTimer?.cancel();
    super.dispose();
  }

  Future<void> startSession({String? subjectId, Map<Subject, double>? currentMastery}) async {
    state = state.copyWith(isLoading: true, error: null);
    try {
      String? targetSubject = subjectId;
      
      if (targetSubject == null && currentMastery != null) {
        final subject = _adaptiveEngine.selectNextSubject(currentMastery);
        targetSubject = subject.name;
      }

      final cached = await _questionCache.getCachedQuestions(subjectId: targetSubject);
      var questions = cached.map((q) => QuestionModel.fromJson(q)).toList();
      
      if (questions.isEmpty) {
        // Try one more fetch directly if cache is empty
        await _questionCache.warmUp(_apiClient);
        final cachedRetry = await _questionCache.getCachedQuestions(subjectId: targetSubject);
        questions = cachedRetry.map((q) => QuestionModel.fromJson(q)).toList();
        
        if (questions.isEmpty) {
           throw Exception('No questions available. Please connect to internet to download content.');
        }
      }

      state = PracticeState(questions: questions, isLoading: false);
      _startComboTimer();
      _questionStopwatch.reset();
      _questionStopwatch.start();
    } catch (e) {
      state = state.copyWith(isLoading: false, error: e.toString());
    }
  }

  void selectOption(String optionId) {
    if (state.isAnswerChecked) return;
    AppHaptics.light();
    state = state.copyWith(selectedOptionId: optionId);
    _startComboTimer();
  }

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
    // Formula: XP_total = XP_base + min(combo, 15)
    final baseXp = isCorrect ? _calculateBaseXp(current) : 0;
    final bonusXp = isCorrect ? ComboService.calculateBonusXP(state.comboCount) : 0;
    final totalXpForQuestion = baseXp + bonusXp;

    // Sync with engagement providers (send total XP including bonus)
    if (isCorrect) {
      _engagementNotifier.addXp(totalXpForQuestion);
    } else {
      _heartsNotifier.useHeart();
    }

    // Update user stats for accuracy tracking
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

    // Fire and forget submission to backend
    _submitAnswer(
      current.id,
      state.selectedOptionId!,
      timeSpentSeconds,
      totalXpForQuestion,
      bonusXp,
      isCorrect,
      current.subjectId,
      current.topicId,
    );
  }

  /// Increment combo on correct answer and play appropriate sound
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

  Future<void> _submitAnswer(
    String questionId,
    String answerId,
    int timeSpentSeconds,
    int totalXp,
    int bonusXp,
    bool isCorrect,
    String subjectId,
    String topicId,
  ) async {
    final responseTimeMs = timeSpentSeconds * 1000;

    // Submit answer to backend
    try {
      final response = await _apiClient.post(
        ApiConstants.submitAnswer,
        data: {
          'question_id': questionId,
          'answer_id': answerId,
          'time_spent_seconds': timeSpentSeconds,
          'session_type': 'practice',
          'combo_count': state.comboCount,
          'bonus_xp': bonusXp,
          'total_xp': totalXp,
        },
      );

      // Sync hearts from backend response if available
      if (response.statusCode == 200 && response.data != null) {
        final data = response.data['data'] ?? response.data;
        final heartsRemaining = data['hearts_remaining'] as int?;

        // Sync hearts from backend
        if (heartsRemaining != null) {
          _heartsNotifier.setHearts(heartsRemaining);
        }
      }
    } catch (e) {
      // Offline queue should handle this via interceptor
      print('Failed to submit answer: $e');
    }

    // Submit to spaced repetition system (SM-2)
    // This tracks the question for future review based on performance
    _submitToSpacedRepetition(
      questionId: questionId,
      answerId: answerId,
      isCorrect: isCorrect,
      responseTimeMs: responseTimeMs,
      subjectId: subjectId,
      topicId: topicId,
    );
  }

  /// Submit answer to the spaced repetition (SM-2) system
  /// Determines review quality based on correctness and response time:
  /// - Incorrect = AGAIN (quality 0) - Reset interval, review soon
  /// - Correct + fast (<5s) = EASY (quality 5) - Increase interval significantly
  /// - Correct + normal (5-15s) = GOOD (quality 4) - Normal interval increase
  /// - Correct + slow (>15s) = HARD (quality 3) - Small interval increase
  void _submitToSpacedRepetition({
    required String questionId,
    required String answerId,
    required bool isCorrect,
    required int responseTimeMs,
    required String subjectId,
    required String topicId,
  }) {
    // Determine SM-2 review result based on correctness and response time
    final reviewResult = _determineReviewResult(
      isCorrect: isCorrect,
      responseTimeMs: responseTimeMs,
    );

    // Fire and forget - submit to spaced repetition service
    _spacedRepetitionNotifier.submitReviewWithResult(
      itemId: questionId, // Using questionId as itemId for practice questions
      result: reviewResult,
      responseTimeMs: responseTimeMs,
      selectedAnswer: answerId,
    );

    // If incorrect, ensure the question is added to the spaced repetition queue
    // for future review
    if (!isCorrect) {
      _spacedRepetitionNotifier.addItemForReview(
        questionId: questionId,
        subjectId: subjectId,
        topicId: topicId,
      );
    }
  }

  /// Determine the SM-2 review result based on answer correctness and response time
  ReviewResult _determineReviewResult({
    required bool isCorrect,
    required int responseTimeMs,
  }) {
    if (!isCorrect) {
      return ReviewResult.again;
    }

    // Correct answer - determine quality based on response time
    if (responseTimeMs < _fastResponseThresholdMs) {
      // Fast response = easy recall
      return ReviewResult.easy;
    } else if (responseTimeMs > _slowResponseThresholdMs) {
      // Slow response = difficult recall
      return ReviewResult.hard;
    } else {
      // Normal response time = good recall
      return ReviewResult.good;
    }
  }

  void nextQuestion() {
    if (state.currentIndex + 1 < state.questions.length) {
      state = state.copyWith(
        currentIndex: state.currentIndex + 1,
        isAnswerChecked: false,
        isCurrentCorrect: false,
        selectedOptionId: null,
      );
      _startComboTimer();
      // Reset stopwatch for next question
      _questionStopwatch.reset();
      _questionStopwatch.start();
    } else {
      _comboTimer?.cancel();
      state = state.copyWith(isFinished: true);
      // Notify streak provider that practice session is complete
      _streakNotifier.onPracticeCompleted();
    }
  }

  void _startComboTimer() {
    _comboTimer?.cancel();
    _comboTimer = Timer(const Duration(seconds: _comboTimeoutSeconds), () {
      if (state.comboCount > 0) {
        _resetCombo();
      }
    });
  }

  /// Calculate base XP for a question (without combo bonus)
  int _calculateBaseXp(Question question) {
    // Use the xpReward from the question object, with fallback logic
    if (question.xpReward > 0) {
      return question.xpReward;
    }

    // Fallback logic if xpReward is not set
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
}


final adaptiveEngineProvider = Provider((ref) => AdaptiveEngine());

final practiceProvider = StateNotifierProvider<PracticeNotifier, PracticeState>((ref) {
  final cache = ref.watch(questionCacheProvider);
  final engine = ref.watch(adaptiveEngineProvider);
  final apiClient = ref.watch(apiClientProvider);
  final engagement = ref.read(engagementProvider.notifier);
  final hearts = ref.read(heartsProvider.notifier);
  final userStats = ref.read(userStatsProvider.notifier);
  final streak = ref.read(streakProvider.notifier);
  final audioService = ref.watch(audioServiceProvider);
  final spacedRepetition = ref.read(spacedRepetitionProvider.notifier);
  return PracticeNotifier(
    cache,
    engine,
    apiClient,
    engagement,
    hearts,
    userStats,
    streak,
    audioService,
    spacedRepetition,
  );
});
