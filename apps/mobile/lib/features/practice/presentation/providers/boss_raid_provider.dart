import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/network/api_client.dart';
import '../../data/datasources/boss_raid_remote_datasource.dart';
import '../../domain/repositories/boss_raid_repository.dart';
import '../../data/repositories/boss_raid_repository_impl.dart';
import '../../data/models/boss_raid_models.dart';
import '../../domain/entities/question.dart';

// ============================================================================
// PRESENTATION LAYER ENTITIES
// ============================================================================

/// Status of the current boss raid event
class BossRaidStatus {
  final bool isActive;
  final String bossName;
  final String? bossDescription;
  final int bossHp;
  final int bossCurrentHp;
  final int? timeRemainingSeconds;
  final double xpMultiplier;
  final int myDamageDealt;
  final int? myRank;

  BossRaidStatus({
    required this.isActive,
    required this.bossName,
    this.bossDescription,
    required this.bossHp,
    required this.bossCurrentHp,
    this.timeRemainingSeconds,
    this.xpMultiplier = 3.0,
    this.myDamageDealt = 0,
    this.myRank,
  });

  /// Formats the time remaining as "Xh Ym"
  String get formattedTimeRemaining {
    if (timeRemainingSeconds == null || timeRemainingSeconds! <= 0) {
      return 'Terminando...';
    }
    final hours = timeRemainingSeconds! ~/ 3600;
    final minutes = (timeRemainingSeconds! % 3600) ~/ 60;
    if (hours > 0) {
      return '${hours}h ${minutes}m';
    }
    return '${minutes}m';
  }

  double get hpPercentage => bossHp > 0 ? bossCurrentHp / bossHp : 0.0;
}

/// Result of submitting an answer in the boss battle
class BossRaidAnswerResult {
  final bool isCorrect;
  final String correctAnswerId;
  final int damageDealt;
  final int xpEarned;
  final int currentCombo;
  final int bossCurrentHp;
  final bool bossDefeated;

  BossRaidAnswerResult({
    required this.isCorrect,
    required this.correctAnswerId,
    required this.damageDealt,
    required this.xpEarned,
    required this.currentCombo,
    required this.bossCurrentHp,
    required this.bossDefeated,
  });

  factory BossRaidAnswerResult.fromResponse(BossRaidAnswerResponse response) {
    return BossRaidAnswerResult(
      isCorrect: response.correct,
      correctAnswerId: response.correctAnswerId,
      damageDealt: response.damageDealt,
      xpEarned: response.xpEarned,
      currentCombo: response.currentCombo,
      bossCurrentHp: response.bossCurrentHp,
      bossDefeated: response.bossDefeated,
    );
  }
}

/// Final results when raid is completed
class BossRaidResults {
  final bool bossDefeated;
  final int totalDamage;
  final int totalXp;
  final int correctAnswers;
  final int totalQuestions;
  final double accuracyPercentage;
  final int bestCombo;
  final int? rankInRaid;
  final List<RaidReward> rewards;
  final int sessionDurationSeconds;

  BossRaidResults({
    required this.bossDefeated,
    required this.totalDamage,
    required this.totalXp,
    required this.correctAnswers,
    required this.totalQuestions,
    required this.accuracyPercentage,
    required this.bestCombo,
    this.rankInRaid,
    required this.rewards,
    required this.sessionDurationSeconds,
  });

  factory BossRaidResults.fromResponse(BossRaidCompleteResponse response) {
    return BossRaidResults(
      bossDefeated: response.bossDefeated,
      totalDamage: response.totalDamage,
      totalXp: response.totalXp,
      correctAnswers: response.correctAnswers,
      totalQuestions: response.totalQuestions,
      accuracyPercentage: response.accuracyPercentage,
      bestCombo: response.bestCombo,
      rankInRaid: response.rankInRaid,
      rewards: response.rewards,
      sessionDurationSeconds: response.sessionDurationSeconds,
    );
  }

  String get formattedDuration {
    final minutes = sessionDurationSeconds ~/ 60;
    final seconds = sessionDurationSeconds % 60;
    return '${minutes.toString().padLeft(2, '0')}:${seconds.toString().padLeft(2, '0')}';
  }
}

// ============================================================================
// STATE CLASS
// ============================================================================

class BossRaidState {
  // Raid status
  final BossRaidStatus? status;

  // Session info
  final String? sessionId;
  final CurrentBossModel? boss;
  final List<Question>? questions;

  // Battle state
  final int currentQuestionIndex;
  final String? selectedAnswerId;
  final BossRaidAnswerResult? lastAnswerResult;
  final bool isAnswerSubmitted;

  // Cumulative battle stats
  final int totalDamageDealt;
  final int currentCombo;
  final int bestCombo;
  final int correctAnswers;
  final int totalXpEarned;

  // UI state
  final bool isLoading;
  final bool isSubmittingAnswer;
  final String? error;

  // Results
  final BossRaidResults? results;
  final bool isCompleted;

  BossRaidState({
    this.status,
    this.sessionId,
    this.boss,
    this.questions,
    this.currentQuestionIndex = 0,
    this.selectedAnswerId,
    this.lastAnswerResult,
    this.isAnswerSubmitted = false,
    this.totalDamageDealt = 0,
    this.currentCombo = 0,
    this.bestCombo = 0,
    this.correctAnswers = 0,
    this.totalXpEarned = 0,
    this.isLoading = false,
    this.isSubmittingAnswer = false,
    this.error,
    this.results,
    this.isCompleted = false,
  });

  /// Current question being displayed
  Question? get currentQuestion {
    if (questions == null || questions!.isEmpty) return null;
    if (currentQuestionIndex >= questions!.length) return null;
    return questions![currentQuestionIndex];
  }

  /// Total number of questions in the raid
  int get totalQuestions => questions?.length ?? 0;

  /// Progress through the questions (0.0 to 1.0)
  double get progress {
    if (totalQuestions == 0) return 0.0;
    return (currentQuestionIndex + 1) / totalQuestions;
  }

  /// Whether there are more questions
  bool get hasMoreQuestions {
    if (questions == null) return false;
    return currentQuestionIndex < questions!.length - 1;
  }

  /// Current boss HP (updated after each answer)
  int get bossCurrentHp => lastAnswerResult?.bossCurrentHp ?? boss?.currentHp ?? 0;

  /// Boss max HP
  int get bossMaxHp => boss?.hp ?? status?.bossHp ?? 0;

  /// HP percentage
  double get bossHpPercentage => bossMaxHp > 0 ? bossCurrentHp / bossMaxHp : 0.0;

  /// Whether the boss has been defeated
  bool get isBossDefeated => lastAnswerResult?.bossDefeated ?? false;

  BossRaidState copyWith({
    BossRaidStatus? status,
    String? sessionId,
    CurrentBossModel? boss,
    List<Question>? questions,
    int? currentQuestionIndex,
    String? selectedAnswerId,
    BossRaidAnswerResult? lastAnswerResult,
    bool? isAnswerSubmitted,
    int? totalDamageDealt,
    int? currentCombo,
    int? bestCombo,
    int? correctAnswers,
    int? totalXpEarned,
    bool? isLoading,
    bool? isSubmittingAnswer,
    String? error,
    BossRaidResults? results,
    bool? isCompleted,
    bool clearQuestions = false,
    bool clearError = false,
    bool clearAnswer = false,
    bool clearResults = false,
  }) {
    return BossRaidState(
      status: status ?? this.status,
      sessionId: sessionId ?? this.sessionId,
      boss: boss ?? this.boss,
      questions: clearQuestions ? null : questions ?? this.questions,
      currentQuestionIndex: currentQuestionIndex ?? this.currentQuestionIndex,
      selectedAnswerId: clearAnswer ? null : selectedAnswerId ?? this.selectedAnswerId,
      lastAnswerResult: clearAnswer ? null : lastAnswerResult ?? this.lastAnswerResult,
      isAnswerSubmitted: clearAnswer ? false : isAnswerSubmitted ?? this.isAnswerSubmitted,
      totalDamageDealt: totalDamageDealt ?? this.totalDamageDealt,
      currentCombo: currentCombo ?? this.currentCombo,
      bestCombo: bestCombo ?? this.bestCombo,
      correctAnswers: correctAnswers ?? this.correctAnswers,
      totalXpEarned: totalXpEarned ?? this.totalXpEarned,
      isLoading: isLoading ?? this.isLoading,
      isSubmittingAnswer: isSubmittingAnswer ?? this.isSubmittingAnswer,
      error: clearError ? null : error ?? this.error,
      results: clearResults ? null : results ?? this.results,
      isCompleted: isCompleted ?? this.isCompleted,
    );
  }
}

// ============================================================================
// DATA LAYER PROVIDERS
// ============================================================================

final bossRaidRemoteDataSourceProvider = Provider.autoDispose((ref) {
  final apiClient = ref.watch(apiClientProvider);
  return BossRaidRemoteDataSource(apiClient);
});

final bossRaidRepositoryProvider = Provider.autoDispose<BossRaidRepository>((ref) {
  final remote = ref.watch(bossRaidRemoteDataSourceProvider);
  return BossRaidRepositoryImpl(remote);
});

// ============================================================================
// NOTIFIER
// ============================================================================

class BossRaidNotifier extends StateNotifier<BossRaidState> {
  final BossRaidRepository _repository;

  BossRaidNotifier(this._repository) : super(BossRaidState()) {
    fetchStatus();
  }

  /// Fetch current boss raid status
  Future<void> fetchStatus() async {
    state = state.copyWith(isLoading: true, clearError: true);
    try {
      final statusModel = await _repository.getStatus();
      final status = BossRaidStatus(
        isActive: statusModel.isActive,
        bossName: statusModel.currentBoss?.name ?? 'Boss',
        bossDescription: statusModel.currentBoss?.description,
        bossHp: statusModel.currentBoss?.hp ?? 0,
        bossCurrentHp: statusModel.currentBoss?.currentHp ?? 0,
        timeRemainingSeconds: statusModel.timeRemainingSeconds,
        xpMultiplier: statusModel.xpMultiplier,
        myDamageDealt: statusModel.myDamageDealt,
        myRank: statusModel.myRank,
      );
      state = state.copyWith(isLoading: false, status: status);
    } catch (e) {
      state = state.copyWith(isLoading: false, error: e.toString());
    }
  }

  /// Start a new raid session
  Future<String?> startRaid() async {
    state = state.copyWith(
      isLoading: true,
      clearError: true,
      clearQuestions: true,
      clearResults: true,
      isCompleted: false,
      currentQuestionIndex: 0,
      totalDamageDealt: 0,
      currentCombo: 0,
      bestCombo: 0,
      correctAnswers: 0,
      totalXpEarned: 0,
    );

    try {
      final sessionModel = await _repository.startRaid();

      // Map data model to presentation entity
      final questions = sessionModel.questions.map((q) => Question.fromModel(q)).toList();

      state = state.copyWith(
        isLoading: false,
        sessionId: sessionModel.sessionId,
        boss: sessionModel.boss,
        questions: questions,
      );

      return sessionModel.sessionId;
    } catch (e) {
      state = state.copyWith(isLoading: false, error: e.toString());
      return null;
    }
  }

  /// Select an answer option (before submitting)
  void selectAnswer(String answerId) {
    if (state.isAnswerSubmitted || state.isSubmittingAnswer) return;
    state = state.copyWith(selectedAnswerId: answerId);
  }

  /// Submit the selected answer
  Future<void> submitAnswer() async {
    if (state.sessionId == null ||
        state.currentQuestion == null ||
        state.selectedAnswerId == null ||
        state.isAnswerSubmitted ||
        state.isSubmittingAnswer) {
      return;
    }

    state = state.copyWith(isSubmittingAnswer: true, clearError: true);

    try {
      final response = await _repository.submitAnswer(
        sessionId: state.sessionId!,
        questionId: state.currentQuestion!.id,
        answerId: state.selectedAnswerId!,
      );

      final result = BossRaidAnswerResult.fromResponse(response);

      // Update combo tracking
      final newBestCombo = result.currentCombo > state.bestCombo
          ? result.currentCombo
          : state.bestCombo;

      state = state.copyWith(
        isSubmittingAnswer: false,
        isAnswerSubmitted: true,
        lastAnswerResult: result,
        totalDamageDealt: state.totalDamageDealt + result.damageDealt,
        currentCombo: result.currentCombo,
        bestCombo: newBestCombo,
        correctAnswers: result.isCorrect
            ? state.correctAnswers + 1
            : state.correctAnswers,
        totalXpEarned: state.totalXpEarned + result.xpEarned,
      );

      // Auto-complete if boss is defeated
      if (result.bossDefeated) {
        await Future.delayed(const Duration(milliseconds: 1500));
        await completeRaid();
      }
    } catch (e) {
      state = state.copyWith(
        isSubmittingAnswer: false,
        error: e.toString(),
      );
    }
  }

  /// Move to the next question
  void nextQuestion() {
    if (!state.isAnswerSubmitted) return;

    if (state.hasMoreQuestions) {
      state = state.copyWith(
        currentQuestionIndex: state.currentQuestionIndex + 1,
        clearAnswer: true,
      );
    } else {
      // No more questions, complete the raid
      completeRaid();
    }
  }

  /// Complete the raid session and get results
  Future<void> completeRaid() async {
    if (state.sessionId == null || state.isCompleted) return;

    state = state.copyWith(isLoading: true, clearError: true);

    try {
      final response = await _repository.completeRaid(state.sessionId!);
      final results = BossRaidResults.fromResponse(response);

      state = state.copyWith(
        isLoading: false,
        results: results,
        isCompleted: true,
      );
    } catch (e) {
      state = state.copyWith(
        isLoading: false,
        error: e.toString(),
      );
    }
  }

  /// Reset state to allow starting a new raid
  void resetRaid() {
    state = BossRaidState();
    fetchStatus();
  }
}

// ============================================================================
// MAIN PROVIDER
// ============================================================================

final bossRaidProvider = StateNotifierProvider.autoDispose<BossRaidNotifier, BossRaidState>((ref) {
  final repo = ref.watch(bossRaidRepositoryProvider);
  return BossRaidNotifier(repo);
});
