import 'dart:math';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../../../../core/network/api_client.dart';
import '../../../../shared/providers/balance_provider.dart';
import '../../../practice/data/models/question_model.dart';
import '../../../practice/domain/entities/question.dart';
import '../../../engagement/presentation/providers/engagement_provider.dart';
import '../../data/models/millionaire_models.dart';

/// Provider for Millionaire game state
final millionaireProvider =
    StateNotifierProvider<MillionaireNotifier, MillionaireGameState>((ref) {
  final apiClient = ref.watch(apiClientProvider);
  final engagementNotifier = ref.read(engagementProvider.notifier);
  return MillionaireNotifier(apiClient, engagementNotifier, ref);
});

class MillionaireNotifier extends StateNotifier<MillionaireGameState> {
  final ApiClient _apiClient;
  final EngagementNotifier _engagementNotifier;
  final Ref _ref;
  final Random _random = Random();

  static const String _gamesPlayedKey = 'millionaire_games_played';
  static const String _lastGameDateKey = 'millionaire_last_game_date';

  MillionaireNotifier(this._apiClient, this._engagementNotifier, this._ref)
      : super(const MillionaireGameState()) {
    _loadGameCount();
  }

  /// Load today's game count from local storage
  Future<void> _loadGameCount() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final lastDateStr = prefs.getString(_lastGameDateKey);
      final today = DateTime.now();
      final todayStr = '${today.year}-${today.month}-${today.day}';

      int gamesPlayed = 0;
      if (lastDateStr == todayStr) {
        gamesPlayed = prefs.getInt(_gamesPlayedKey) ?? 0;
      } else {
        // Reset counter for new day
        await prefs.setInt(_gamesPlayedKey, 0);
        await prefs.setString(_lastGameDateKey, todayStr);
      }

      state = state.copyWith(
        gamesPlayedToday: gamesPlayed,
        lastGameDate: today,
      );
    } catch (e) {
      // Silently fail, use default values
    }
  }

  /// Increment game count and save to storage
  Future<void> _incrementGameCount() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final today = DateTime.now();
      final todayStr = '${today.year}-${today.month}-${today.day}';

      final newCount = state.gamesPlayedToday + 1;
      await prefs.setInt(_gamesPlayedKey, newCount);
      await prefs.setString(_lastGameDateKey, todayStr);

      state = state.copyWith(
        gamesPlayedToday: newCount,
        lastGameDate: today,
      );
    } catch (e) {
      // Silently fail
    }
  }

  /// Start a new Millionaire game session
  /// Requires 100 gold entry cost (LOGICA_DE_NEGOCIO.md)
  Future<bool> startGame() async {
    if (!state.canPlay) {
      state = state.copyWith(
        errorMessage: 'Has alcanzado el limite de ${MillionaireGameState.maxGamesPerDay} partidas diarias',
      );
      return false;
    }

    // Check if user has enough gold for entry cost (100 gold)
    final balanceState = _ref.read(balanceProvider);
    final currentGold = balanceState.maybeWhen(
      data: (balance) => balance.gold,
      orElse: () => 0,
    );

    if (currentGold < MillionaireGameState.entryCostGold) {
      state = state.copyWith(
        errorMessage: 'Necesitas ${MillionaireGameState.entryCostGold} oro para jugar. Tienes $currentGold oro.',
      );
      return false;
    }

    // Deduct entry cost
    _engagementNotifier.spendGold(MillionaireGameState.entryCostGold);

    state = state.copyWith(
      status: MillionaireGameStatus.playing,
      currentQuestionIndex: 0,
      earnedXp: 0,
      earnedGold: 0,
      clearLastCheckpoint: true,
      clearSelectedAnswer: true,
      clearErrorMessage: true,
      isAnswerRevealed: false,
      lifelines: [
        const LifelineState(type: LifelineType.fiftyFifty, goldCost: 0),
        const LifelineState(type: LifelineType.askAI, goldCost: 50),
        const LifelineState(type: LifelineType.skip, goldCost: 0),
      ],
    );

    // Load questions for all 15 levels
    try {
      final questions = await _loadQuestions();
      if (questions.isEmpty) {
        // Refund entry cost if questions fail to load
        _engagementNotifier.addGold(MillionaireGameState.entryCostGold);
        state = state.copyWith(
          status: MillionaireGameStatus.notStarted,
          errorMessage: 'Error al cargar preguntas. Se ha devuelto tu oro.',
        );
        return false;
      }

      state = state.copyWith(questions: questions);
      await _incrementGameCount();
      return true;
    } catch (e) {
      // Refund entry cost on error
      _engagementNotifier.addGold(MillionaireGameState.entryCostGold);
      state = state.copyWith(
        status: MillionaireGameStatus.notStarted,
        errorMessage: 'No se pudo iniciar el juego. Intenta de nuevo.',
      );
      return false;
    }
  }

  /// Load 15 questions with progressive difficulty
  Future<List<MillionaireQuestion>> _loadQuestions() async {
    final List<MillionaireQuestion> millionaireQuestions = [];

    // Define difficulty ranges for each tier
    final difficultyMap = {
      MillionaireDifficulty.easy: ['E', 'F'], // Easy difficulties
      MillionaireDifficulty.easyMedium: ['D', 'E'],
      MillionaireDifficulty.medium: ['C', 'D'],
      MillionaireDifficulty.mediumHard: ['B', 'C'],
      MillionaireDifficulty.hard: ['A', 'B'],
    };

    for (int i = 1; i <= 15; i++) {
      final tier = PrizeTier.getTier(i);
      final difficulties = difficultyMap[tier.difficulty] ?? ['C'];
      final difficultyParam = difficulties.join(',');

      try {
        // Fetch question from backend with appropriate difficulty
        final response = await _apiClient.get(
          '/practice/questions',
          queryParameters: {
            'limit': 1,
            'difficulty': difficultyParam,
            'random': true,
          },
        );

        if (response.statusCode == 200 && response.data != null) {
          final questionsData = response.data['questions'] as List? ?? [];
          if (questionsData.isNotEmpty) {
            final question = QuestionModel.fromJson(questionsData.first);
            millionaireQuestions.add(MillionaireQuestion(
              question: question,
              questionNumber: i,
              prizeTier: tier,
            ));
            continue;
          }
        }
      } catch (e) {
        // Propagate error — no mock questions in production
        rethrow;
      }
    }

    return millionaireQuestions;
  }

  /// Create a mock question for testing/fallback
  MillionaireQuestion _createMockQuestion(int number, PrizeTier tier) {
    final mockQuestion = Question(
      id: 'mock_$number',
      subjectId: 'general',
      topicId: 'general',
      text: 'Pregunta de prueba nivel $number - ${tier.difficulty.name}',
      options: [
        Option(id: 'A', text: 'Opcion A (Correcta)'),
        Option(id: 'B', text: 'Opcion B'),
        Option(id: 'C', text: 'Opcion C'),
        Option(id: 'D', text: 'Opcion D'),
      ],
      correctAnswer: 'A',
      difficulty: tier.difficulty.name,
      xpReward: tier.xpReward,
    );

    return MillionaireQuestion(
      question: mockQuestion,
      questionNumber: number,
      prizeTier: tier,
    );
  }

  /// Submit answer for current question
  Future<void> submitAnswer(String answerId) async {
    if (state.status != MillionaireGameStatus.playing ||
        state.currentQuestion == null) {
      return;
    }

    state = state.copyWith(
      selectedAnswer: answerId,
      isAnswerRevealed: true,
    );

    // Wait for animation
    await Future.delayed(const Duration(milliseconds: 1500));

    final currentQ = state.currentQuestion!;
    final isCorrect = answerId == currentQ.question.correctAnswer;

    if (isCorrect) {
      _handleCorrectAnswer();
    } else {
      _handleIncorrectAnswer();
    }
  }

  /// Handle correct answer
  void _handleCorrectAnswer() {
    final currentQ = state.currentQuestion!;
    final tier = currentQ.prizeTier;

    final newXp = state.earnedXp + tier.xpReward;
    final newGold = state.earnedGold + tier.goldReward;

    // Check for checkpoint
    final checkpoint = Checkpoint.getCheckpointAt(currentQ.questionNumber);

    if (currentQ.questionNumber == 15) {
      // Won the game!
      _finishGame(MillionaireGameStatus.won, newXp, newGold, checkpoint);
    } else {
      // Move to next question
      state = state.copyWith(
        currentQuestionIndex: state.currentQuestionIndex + 1,
        earnedXp: newXp,
        earnedGold: newGold,
        lastCheckpoint: checkpoint ?? state.lastCheckpoint,
        clearSelectedAnswer: true,
        isAnswerRevealed: false,
      );
    }
  }

  /// Handle incorrect answer
  void _handleIncorrectAnswer() {
    final checkpoint = state.lastCheckpoint;
    final finalXp = checkpoint?.guaranteedXp ?? 0;
    final finalGold = checkpoint?.guaranteedGold ?? 0;

    _finishGame(MillionaireGameStatus.lost, finalXp, finalGold, checkpoint);
  }

  /// Finish the game and award rewards
  void _finishGame(
    MillionaireGameStatus status,
    int xp,
    int gold,
    Checkpoint? checkpoint,
  ) {
    state = state.copyWith(
      status: status,
      earnedXp: xp,
      earnedGold: gold,
      lastCheckpoint: checkpoint,
    );

    // Award XP and Gold through engagement system
    if (xp > 0) {
      _engagementNotifier.addXp(xp, source: 'millionaire');
    }
    if (gold > 0) {
      _engagementNotifier.addGold(gold);
    }
  }

  /// Walk away with current earnings
  void walkAway() {
    if (state.status != MillionaireGameStatus.playing) return;

    _finishGame(
      MillionaireGameStatus.walkingAway,
      state.earnedXp,
      state.earnedGold,
      state.lastCheckpoint,
    );
  }

  /// Use 50:50 lifeline - eliminates 2 wrong options
  bool useFiftyFifty() {
    if (!state.isLifelineAvailable(LifelineType.fiftyFifty) ||
        state.currentQuestion == null) {
      return false;
    }

    final currentQ = state.currentQuestion!;
    final wrongOptions = currentQ.question.options
        .where((opt) => opt.id != currentQ.question.correctAnswer)
        .toList();

    // Randomly select 2 wrong options to eliminate
    wrongOptions.shuffle(_random);
    final toEliminate = wrongOptions.take(2).map((o) => o.id).toList();

    // Update lifeline state
    final updatedLifelines = state.lifelines.map((l) {
      if (l.type == LifelineType.fiftyFifty) {
        return l.copyWith(isUsed: true);
      }
      return l;
    }).toList();

    // Update current question with eliminated options
    final updatedQuestions = List<MillionaireQuestion>.from(state.questions);
    updatedQuestions[state.currentQuestionIndex] =
        currentQ.copyWith(eliminatedOptions: toEliminate);

    state = state.copyWith(
      lifelines: updatedLifelines,
      questions: updatedQuestions,
    );

    return true;
  }

  /// Use Ask AI lifeline - shows a hint (costs 50 gold)
  Future<bool> useAskAI() async {
    if (!state.isLifelineAvailable(LifelineType.askAI) ||
        state.currentQuestion == null) {
      return false;
    }

    // Check if user has enough gold (using balance provider)
    final balanceState = _ref.read(balanceProvider);
    final currentGold = balanceState.maybeWhen(
      data: (balance) => balance.gold,
      orElse: () => 0,
    );
    if (currentGold < 50) {
      return false;
    }

    state = state.copyWith(isLoadingHint: true);

    // Deduct gold
    _engagementNotifier.spendGold(50);

    // Update lifeline state
    final updatedLifelines = state.lifelines.map((l) {
      if (l.type == LifelineType.askAI) {
        return l.copyWith(isUsed: true);
      }
      return l;
    }).toList();

    // Generate or fetch hint
    String hint;
    try {
      final response = await _apiClient.post(
        '/ai/hint',
        data: {
          'question_id': state.currentQuestion!.question.id,
          'question_text': state.currentQuestion!.question.text,
        },
      );

      if (response.statusCode == 200 && response.data?['hint'] != null) {
        hint = response.data['hint'];
      } else {
        hint = _generateLocalHint();
      }
    } catch (e) {
      hint = _generateLocalHint();
    }

    // Update current question with hint
    final updatedQuestions = List<MillionaireQuestion>.from(state.questions);
    updatedQuestions[state.currentQuestionIndex] =
        state.currentQuestion!.copyWith(aiHint: hint);

    state = state.copyWith(
      lifelines: updatedLifelines,
      questions: updatedQuestions,
      isLoadingHint: false,
    );

    return true;
  }

  /// Generate a local hint when API is not available
  String _generateLocalHint() {
    final hints = [
      'Piensa en los conceptos fundamentales de este tema.',
      'Descarta las opciones que parezcan muy extremas.',
      'Busca la respuesta mas equilibrada y logica.',
      'Recuerda lo que has estudiado sobre este tema.',
      'Una de las opciones tiene una pista en su redaccion.',
    ];
    return hints[_random.nextInt(hints.length)];
  }

  /// Use Skip lifeline - skip current question without penalty
  bool useSkip() {
    if (!state.isLifelineAvailable(LifelineType.skip) ||
        state.currentQuestion == null) {
      return false;
    }

    // Update lifeline state
    final updatedLifelines = state.lifelines.map((l) {
      if (l.type == LifelineType.skip) {
        return l.copyWith(isUsed: true);
      }
      return l;
    }).toList();

    if (state.currentQuestionIndex >= 14) {
      // Can't skip the last question, just mark as used
      state = state.copyWith(lifelines: updatedLifelines);
      return false;
    }

    // Move to next question without earning rewards for this one
    state = state.copyWith(
      lifelines: updatedLifelines,
      currentQuestionIndex: state.currentQuestionIndex + 1,
      clearSelectedAnswer: true,
      isAnswerRevealed: false,
    );

    return true;
  }

  /// Reset game state for new game
  void resetGame() {
    state = state.copyWith(
      status: MillionaireGameStatus.notStarted,
      questions: [],
      currentQuestionIndex: 0,
      earnedXp: 0,
      earnedGold: 0,
      clearLastCheckpoint: true,
      clearSelectedAnswer: true,
      isAnswerRevealed: false,
      lifelines: [],
    );
  }

  /// Get result summary
  MillionaireResult getResult() {
    return MillionaireResult(
      isWin: state.status == MillionaireGameStatus.won,
      questionsAnswered: state.currentQuestionIndex + 1,
      totalXp: state.earnedXp,
      totalGold: state.earnedGold,
      reachedCheckpoint: state.lastCheckpoint,
      correctAnswers: state.status == MillionaireGameStatus.won
          ? 15
          : state.currentQuestionIndex,
    );
  }
}
