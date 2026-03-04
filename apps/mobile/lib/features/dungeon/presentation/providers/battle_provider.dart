import 'dart:async';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/network/api_client.dart';
import '../../../../core/services/sound_manager.dart';
import '../../../practice/domain/entities/question.dart';
import '../../data/datasources/dungeon_remote_datasource.dart';
import '../../data/models/dungeon_models.dart';

// ============================================================================
// BATTLE RESULT
// ============================================================================

/// Result of a completed battle
class BattleResult {
  final bool isVictory;
  final int xpEarned;
  final int goldEarned;
  final int correctAnswers;
  final int totalQuestions;
  final int bestCombo;
  final int starsEarned;
  final List<DungeonReward> rewards;

  BattleResult({
    required this.isVictory,
    required this.xpEarned,
    required this.goldEarned,
    required this.correctAnswers,
    required this.totalQuestions,
    required this.bestCombo,
    required this.starsEarned,
    required this.rewards,
  });

  double get accuracy =>
      totalQuestions > 0 ? (correctAnswers / totalQuestions) * 100 : 0;
}

// ============================================================================
// ANSWER RESULT
// ============================================================================

/// Result of submitting an answer
class AnswerResult {
  final bool isCorrect;
  final String correctAnswerId;
  final int damageDealt;
  final int damageTaken;
  final int xpEarned;
  final int currentCombo;
  final String? explanation;

  AnswerResult({
    required this.isCorrect,
    required this.correctAnswerId,
    required this.damageDealt,
    required this.damageTaken,
    required this.xpEarned,
    required this.currentCombo,
    this.explanation,
  });
}

// ============================================================================
// BATTLE STATE
// ============================================================================

class BattleState {
  // Session info
  final String? encounterId;
  final String? runId;
  final String theme;

  // Enemy info
  final String enemyName;
  final String? enemyImageUrl;
  final int enemyHp;
  final int enemyMaxHp;

  // Player info
  final int playerHp;
  final int playerMaxHp;

  // Questions
  final List<Question> questions;
  final int currentQuestionIndex;

  // Battle status
  final bool isAnswering;
  final bool isAnimating;
  final String? selectedAnswerId;
  final AnswerResult? lastAnswerResult;
  final int comboCount;
  final int bestCombo;
  final int totalXpEarned;
  final int correctAnswers;

  // UI State
  final bool isLoading;
  final String? error;
  final BattleResult? result;

  BattleState({
    this.encounterId,
    this.runId,
    this.theme = 'math',
    this.enemyName = 'Guardian',
    this.enemyImageUrl,
    this.enemyHp = 100,
    this.enemyMaxHp = 100,
    this.playerHp = 100,
    this.playerMaxHp = 100,
    this.questions = const [],
    this.currentQuestionIndex = 0,
    this.isAnswering = false,
    this.isAnimating = false,
    this.selectedAnswerId,
    this.lastAnswerResult,
    this.comboCount = 0,
    this.bestCombo = 0,
    this.totalXpEarned = 0,
    this.correctAnswers = 0,
    this.isLoading = false,
    this.error,
    this.result,
  });

  /// Current question being displayed
  Question? get currentQuestion {
    if (questions.isEmpty) return null;
    if (currentQuestionIndex >= questions.length) return null;
    return questions[currentQuestionIndex];
  }

  /// Total number of questions
  int get totalQuestions => questions.length;

  /// Progress through questions (0.0 to 1.0)
  double get questionProgress {
    if (totalQuestions == 0) return 0.0;
    return (currentQuestionIndex + 1) / totalQuestions;
  }

  /// Enemy HP percentage (0.0 to 1.0)
  double get enemyHpPercent =>
      enemyMaxHp > 0 ? (enemyHp / enemyMaxHp).clamp(0.0, 1.0) : 0.0;

  /// Player HP percentage (0.0 to 1.0)
  double get playerHpPercent =>
      playerMaxHp > 0 ? (playerHp / playerMaxHp).clamp(0.0, 1.0) : 0.0;

  /// Whether there are more questions
  bool get hasMoreQuestions =>
      questions.isNotEmpty && currentQuestionIndex < questions.length - 1;

  /// Whether the battle has ended (victory or defeat)
  bool get isBattleEnded => result != null;

  /// Whether the enemy is defeated
  bool get isEnemyDefeated => enemyHp <= 0;

  /// Whether the player is defeated
  bool get isPlayerDefeated => playerHp <= 0;

  BattleState copyWith({
    String? encounterId,
    String? runId,
    String? theme,
    String? enemyName,
    String? enemyImageUrl,
    int? enemyHp,
    int? enemyMaxHp,
    int? playerHp,
    int? playerMaxHp,
    List<Question>? questions,
    int? currentQuestionIndex,
    bool? isAnswering,
    bool? isAnimating,
    String? selectedAnswerId,
    AnswerResult? lastAnswerResult,
    int? comboCount,
    int? bestCombo,
    int? totalXpEarned,
    int? correctAnswers,
    bool? isLoading,
    String? error,
    BattleResult? result,
    bool clearSelectedAnswer = false,
    bool clearLastResult = false,
    bool clearError = false,
  }) {
    return BattleState(
      encounterId: encounterId ?? this.encounterId,
      runId: runId ?? this.runId,
      theme: theme ?? this.theme,
      enemyName: enemyName ?? this.enemyName,
      enemyImageUrl: enemyImageUrl ?? this.enemyImageUrl,
      enemyHp: enemyHp ?? this.enemyHp,
      enemyMaxHp: enemyMaxHp ?? this.enemyMaxHp,
      playerHp: playerHp ?? this.playerHp,
      playerMaxHp: playerMaxHp ?? this.playerMaxHp,
      questions: questions ?? this.questions,
      currentQuestionIndex: currentQuestionIndex ?? this.currentQuestionIndex,
      isAnswering: isAnswering ?? this.isAnswering,
      isAnimating: isAnimating ?? this.isAnimating,
      selectedAnswerId:
          clearSelectedAnswer ? null : selectedAnswerId ?? this.selectedAnswerId,
      lastAnswerResult:
          clearLastResult ? null : lastAnswerResult ?? this.lastAnswerResult,
      comboCount: comboCount ?? this.comboCount,
      bestCombo: bestCombo ?? this.bestCombo,
      totalXpEarned: totalXpEarned ?? this.totalXpEarned,
      correctAnswers: correctAnswers ?? this.correctAnswers,
      isLoading: isLoading ?? this.isLoading,
      error: clearError ? null : error ?? this.error,
      result: result ?? this.result,
    );
  }
}

// ============================================================================
// BATTLE NOTIFIER
// ============================================================================

class BattleNotifier extends StateNotifier<BattleState> {
  final DungeonRemoteDataSource _dataSource;
  Timer? _animationTimer;
  final Stopwatch _questionStopwatch = Stopwatch();

  BattleNotifier(this._dataSource) : super(BattleState());

  @override
  void dispose() {
    _animationTimer?.cancel();
    super.dispose();
  }

  /// Start a new battle encounter
  /// [encounterId] - The ID of the encounter/node to battle
  Future<void> startBattle(String encounterId) async {
    state = BattleState(isLoading: true, encounterId: encounterId);

    try {
      // Fetch encounter questions from the backend
      final encounter = await _dataSource.getEncounterQuestions(encounterId);

      // Convert dungeon questions to practice Question entities for reuse
      final questions = encounter.questions.map((q) => Question(
        id: q.id,
        subjectId: 'dungeon',
        topicId: 'battle',
        text: q.text,
        imageUrl: q.imageUrl,
        options: q.options
            .map((o) => Option(
                  id: o.id,
                  text: o.text ?? '',
                  imageUrl: o.imageUrl,
                ))
            .toList(),
        correctAnswer: '', // Server will reveal on submit
        xpReward: q.xpValue,
        difficulty: 'medium',
      )).toList();

      // Extract enemy info
      final enemy = encounter.enemy;

      // Extract theme from encounter metadata or default to math
      // In real implementation, the encounter response would include the theme
      final theme = encounterId.contains('math') ? 'math' 
                  : encounterId.contains('reading') ? 'reading'
                  : encounterId.contains('science') ? 'science'
                  : encounterId.contains('social') ? 'social'
                  : encounterId.contains('english') ? 'english'
                  : 'math';

      state = state.copyWith(
        isLoading: false,
        encounterId: encounter.encounterId,
        theme: theme,
        enemyName: enemy?.name ?? 'Guardian',
        enemyImageUrl: enemy?.imageUrl,
        enemyHp: enemy?.hp ?? 100,
        enemyMaxHp: enemy?.maxHp ?? 100,
        playerHp: 100, // Will be updated from run state if needed
        playerMaxHp: 100,
        questions: questions,
        currentQuestionIndex: 0,
        clearError: true,
      );

      // Start the question timer
      _questionStopwatch.reset();
      _questionStopwatch.start();

      // Play battle music
      soundManager.playBattleMusic();
    } catch (e) {
      state = state.copyWith(
        isLoading: false,
        error: 'Error al iniciar la batalla: ${e.toString()}',
      );
    }
  }

  /// Select an answer option (before submitting)
  void selectAnswer(String answerId) {
    if (state.isAnswering || state.isAnimating || state.isBattleEnded) return;
    state = state.copyWith(selectedAnswerId: answerId);
  }

  /// Submit the selected answer
  Future<void> submitAnswer() async {
    if (state.encounterId == null ||
        state.currentQuestion == null ||
        state.selectedAnswerId == null ||
        state.isAnswering ||
        state.isBattleEnded) {
      return;
    }

    state = state.copyWith(isAnswering: true, clearError: true);
    _questionStopwatch.stop();
    final timeSpent = (_questionStopwatch.elapsedMilliseconds / 1000).ceil();

    try {
      final response = await _dataSource.submitAnswer(
        encounterId: state.encounterId!,
        questionId: state.currentQuestion!.id,
        answerId: state.selectedAnswerId!,
        timeSpentSeconds: timeSpent,
      );

      final answerResult = AnswerResult(
        isCorrect: response.correct,
        correctAnswerId: response.correctAnswerId,
        damageDealt: response.damageDealt,
        damageTaken: response.damageTaken,
        xpEarned: response.xpEarned,
        currentCombo: response.currentCombo,
        explanation: response.explanation,
      );

      // Update combo tracking
      final newBestCombo = response.currentCombo > state.bestCombo
          ? response.currentCombo
          : state.bestCombo;

      // Play sound effects
      if (response.correct) {
        soundManager.playAttack();
      } else {
        soundManager.playDamage();
      }

      state = state.copyWith(
        isAnswering: false,
        isAnimating: true,
        lastAnswerResult: answerResult,
        enemyHp: response.enemyCurrentHp,
        playerHp: response.playerCurrentHp,
        comboCount: response.currentCombo,
        bestCombo: newBestCombo,
        totalXpEarned: state.totalXpEarned + response.xpEarned,
        correctAnswers: response.correct
            ? state.correctAnswers + 1
            : state.correctAnswers,
      );

      // Check for battle end conditions
      if (response.enemyDefeated) {
        await _handleVictory(response.starsEarned);
      } else if (response.playerCurrentHp <= 0) {
        await _handleDefeat();
      } else {
        // Animation delay before allowing next action
        _animationTimer?.cancel();
        _animationTimer = Timer(const Duration(milliseconds: 1200), () {
          if (mounted) {
            state = state.copyWith(isAnimating: false);
          }
        });
      }
    } catch (e) {
      state = state.copyWith(
        isAnswering: false,
        error: 'Error al enviar respuesta: ${e.toString()}',
      );
    }
  }

  /// Move to the next question
  void nextQuestion() {
    if (state.isAnimating || state.isBattleEnded) return;

    if (state.hasMoreQuestions) {
      state = state.copyWith(
        currentQuestionIndex: state.currentQuestionIndex + 1,
        clearSelectedAnswer: true,
        clearLastResult: true,
        isAnimating: false,
      );

      // Reset timer for next question
      _questionStopwatch.reset();
      _questionStopwatch.start();
    } else {
      // No more questions - complete the battle based on HP
      if (state.enemyHp <= 0) {
        _handleVictory(_calculateStars());
      } else if (state.playerHp <= 0) {
        _handleDefeat();
      } else {
        // Draw or time-based end - treat as victory if enemy HP < player HP
        if (state.enemyHpPercent < state.playerHpPercent) {
          _handleVictory(_calculateStars());
        } else {
          _handleDefeat();
        }
      }
    }
  }

  /// Handle victory
  Future<void> _handleVictory([int starsEarned = 0]) async {
    soundManager.playVictory();
    soundManager.stopMusic();

    final result = BattleResult(
      isVictory: true,
      xpEarned: state.totalXpEarned,
      goldEarned: _calculateGold(true),
      correctAnswers: state.correctAnswers,
      totalQuestions: state.totalQuestions,
      bestCombo: state.bestCombo,
      starsEarned: starsEarned > 0 ? starsEarned : _calculateStars(),
      rewards: [],
    );

    state = state.copyWith(
      isLoading: false,
      isAnimating: false,
      result: result,
    );
  }

  /// Handle defeat
  Future<void> _handleDefeat() async {
    soundManager.playDefeat();
    soundManager.stopMusic();

    final result = BattleResult(
      isVictory: false,
      xpEarned: state.totalXpEarned ~/ 2, // Half XP on defeat
      goldEarned: 0,
      correctAnswers: state.correctAnswers,
      totalQuestions: state.totalQuestions,
      bestCombo: state.bestCombo,
      starsEarned: 0,
      rewards: [],
    );

    state = state.copyWith(
      isLoading: false,
      isAnimating: false,
      result: result,
    );
  }

  /// Calculate stars based on performance
  int _calculateStars() {
    if (state.totalQuestions == 0) return 0;
    final accuracy = state.correctAnswers / state.totalQuestions;
    if (accuracy >= 0.9) return 3;
    if (accuracy >= 0.7) return 2;
    if (accuracy >= 0.5) return 1;
    return 0;
  }

  /// Calculate gold earned
  int _calculateGold(bool isVictory) {
    if (!isVictory) return 0;
    // Base gold + bonus for accuracy
    final baseGold = 25;
    final accuracyBonus = (state.correctAnswers * 5);
    final comboBonus = state.bestCombo * 2;
    return baseGold + accuracyBonus + comboBonus;
  }

  /// Surrender the battle
  Future<void> surrender() async {
    soundManager.stopMusic();

    final result = BattleResult(
      isVictory: false,
      xpEarned: 0,
      goldEarned: 0,
      correctAnswers: state.correctAnswers,
      totalQuestions: state.totalQuestions,
      bestCombo: state.bestCombo,
      starsEarned: 0,
      rewards: [],
    );

    state = state.copyWith(result: result);
  }

  /// Reset battle state
  void reset() {
    _animationTimer?.cancel();
    soundManager.stopMusic();
    state = BattleState();
  }
}

// ============================================================================
// PROVIDERS
// ============================================================================

/// Provider for the dungeon remote data source
final dungeonRemoteDataSourceProvider = Provider.autoDispose((ref) {
  final apiClient = ref.watch(apiClientProvider);
  return DungeonRemoteDataSource(apiClient);
});

/// Main battle provider
final battleProvider =
    StateNotifierProvider.autoDispose<BattleNotifier, BattleState>((ref) {
  final dataSource = ref.watch(dungeonRemoteDataSourceProvider);
  return BattleNotifier(dataSource);
});

/// Provider for the encounter ID passed to the battle page
final battleEncounterIdProvider = StateProvider<String?>((ref) => null);
