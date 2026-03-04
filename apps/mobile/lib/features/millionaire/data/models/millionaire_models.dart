// Millionaire Game Mode Models
// Based on LOGICA_DE_NEGOCIO.md specifications

import '../../../practice/domain/entities/question.dart';

/// Difficulty levels for the 15 questions in Millionaire mode
enum MillionaireDifficulty {
  easy,       // Questions 1-3: 5 XP base
  easyMedium, // Questions 4-6: 8 XP base
  medium,     // Questions 7-9: 12 XP base
  mediumHard, // Questions 10-12: 18 XP base
  hard,       // Questions 13-15: 25 XP base
}

/// Lifeline types available in Millionaire mode
enum LifelineType {
  fiftyFifty, // Free: Eliminates 2 incorrect options
  askAI,      // 50 Gold: Shows hint (not answer)
  skip,       // Free: Skip question without penalty
}

/// Checkpoint milestones that guarantee minimum rewards
class Checkpoint {
  final int questionNumber;
  final int guaranteedXp;
  final int guaranteedGold;

  const Checkpoint({
    required this.questionNumber,
    required this.guaranteedXp,
    required this.guaranteedGold,
  });

  static const List<Checkpoint> all = [
    Checkpoint(questionNumber: 5, guaranteedXp: 50, guaranteedGold: 10),
    Checkpoint(questionNumber: 10, guaranteedXp: 150, guaranteedGold: 30),
    Checkpoint(questionNumber: 15, guaranteedXp: 500, guaranteedGold: 100),
  ];

  static Checkpoint? getCheckpointAt(int questionNumber) {
    try {
      return all.firstWhere((c) => c.questionNumber == questionNumber);
    } catch (_) {
      return null;
    }
  }

  static Checkpoint? getLastReachedCheckpoint(int currentQuestion) {
    Checkpoint? lastCheckpoint;
    for (final checkpoint in all) {
      if (currentQuestion >= checkpoint.questionNumber) {
        lastCheckpoint = checkpoint;
      }
    }
    return lastCheckpoint;
  }
}

/// Prize tier for each question level
class PrizeTier {
  final int questionNumber;
  final int xpReward;
  final int goldReward;
  final MillionaireDifficulty difficulty;
  final bool isCheckpoint;

  const PrizeTier({
    required this.questionNumber,
    required this.xpReward,
    required this.goldReward,
    required this.difficulty,
    this.isCheckpoint = false,
  });

  static List<PrizeTier> get allTiers => [
    // Easy: 1-3 (5 XP base, cumulative gold)
    const PrizeTier(questionNumber: 1, xpReward: 5, goldReward: 1, difficulty: MillionaireDifficulty.easy),
    const PrizeTier(questionNumber: 2, xpReward: 5, goldReward: 2, difficulty: MillionaireDifficulty.easy),
    const PrizeTier(questionNumber: 3, xpReward: 5, goldReward: 3, difficulty: MillionaireDifficulty.easy),

    // Easy-Medium: 4-6 (8 XP base)
    const PrizeTier(questionNumber: 4, xpReward: 8, goldReward: 5, difficulty: MillionaireDifficulty.easyMedium),
    const PrizeTier(questionNumber: 5, xpReward: 8, goldReward: 10, difficulty: MillionaireDifficulty.easyMedium, isCheckpoint: true),
    const PrizeTier(questionNumber: 6, xpReward: 8, goldReward: 12, difficulty: MillionaireDifficulty.easyMedium),

    // Medium: 7-9 (12 XP base)
    const PrizeTier(questionNumber: 7, xpReward: 12, goldReward: 15, difficulty: MillionaireDifficulty.medium),
    const PrizeTier(questionNumber: 8, xpReward: 12, goldReward: 18, difficulty: MillionaireDifficulty.medium),
    const PrizeTier(questionNumber: 9, xpReward: 12, goldReward: 22, difficulty: MillionaireDifficulty.medium),

    // Medium-Hard: 10-12 (18 XP base)
    const PrizeTier(questionNumber: 10, xpReward: 18, goldReward: 30, difficulty: MillionaireDifficulty.mediumHard, isCheckpoint: true),
    const PrizeTier(questionNumber: 11, xpReward: 18, goldReward: 40, difficulty: MillionaireDifficulty.mediumHard),
    const PrizeTier(questionNumber: 12, xpReward: 18, goldReward: 50, difficulty: MillionaireDifficulty.mediumHard),

    // Hard: 13-15 (25 XP base)
    const PrizeTier(questionNumber: 13, xpReward: 25, goldReward: 65, difficulty: MillionaireDifficulty.hard),
    const PrizeTier(questionNumber: 14, xpReward: 25, goldReward: 80, difficulty: MillionaireDifficulty.hard),
    const PrizeTier(questionNumber: 15, xpReward: 25, goldReward: 100, difficulty: MillionaireDifficulty.hard, isCheckpoint: true),
  ];

  static PrizeTier getTier(int questionNumber) {
    return allTiers.firstWhere(
      (tier) => tier.questionNumber == questionNumber,
      orElse: () => allTiers.first,
    );
  }
}

/// State of a lifeline
class LifelineState {
  final LifelineType type;
  final bool isUsed;
  final int goldCost;

  const LifelineState({
    required this.type,
    this.isUsed = false,
    required this.goldCost,
  });

  LifelineState copyWith({bool? isUsed}) {
    return LifelineState(
      type: type,
      isUsed: isUsed ?? this.isUsed,
      goldCost: goldCost,
    );
  }

  String get displayName {
    switch (type) {
      case LifelineType.fiftyFifty:
        return '50:50';
      case LifelineType.askAI:
        return 'Pista IA';
      case LifelineType.skip:
        return 'Saltar';
    }
  }

  String get icon {
    switch (type) {
      case LifelineType.fiftyFifty:
        return '1/2';
      case LifelineType.askAI:
        return 'AI';
      case LifelineType.skip:
        return '>>';
    }
  }
}

/// Millionaire question with eliminated options tracking
class MillionaireQuestion {
  final Question question;
  final int questionNumber;
  final PrizeTier prizeTier;
  final List<String> eliminatedOptions;
  final String? aiHint;

  const MillionaireQuestion({
    required this.question,
    required this.questionNumber,
    required this.prizeTier,
    this.eliminatedOptions = const [],
    this.aiHint,
  });

  MillionaireQuestion copyWith({
    List<String>? eliminatedOptions,
    String? aiHint,
  }) {
    return MillionaireQuestion(
      question: question,
      questionNumber: questionNumber,
      prizeTier: prizeTier,
      eliminatedOptions: eliminatedOptions ?? this.eliminatedOptions,
      aiHint: aiHint ?? this.aiHint,
    );
  }

  List<Option> get availableOptions {
    return question.options
        .where((opt) => !eliminatedOptions.contains(opt.id))
        .toList();
  }
}

/// Game session state
enum MillionaireGameStatus {
  notStarted,
  playing,
  won,
  lost,
  walkingAway, // Player chose to leave with current earnings
}

/// Complete game session state
class MillionaireGameState {
  final MillionaireGameStatus status;
  final List<MillionaireQuestion> questions;
  final int currentQuestionIndex;
  final List<LifelineState> lifelines;
  final int earnedXp;
  final int earnedGold;
  final Checkpoint? lastCheckpoint;
  final int gamesPlayedToday;
  final DateTime? lastGameDate;
  final String? selectedAnswer;
  final bool isAnswerRevealed;
  final bool isLoadingHint;
  final String? errorMessage;

  const MillionaireGameState({
    this.status = MillionaireGameStatus.notStarted,
    this.questions = const [],
    this.currentQuestionIndex = 0,
    this.lifelines = const [],
    this.earnedXp = 0,
    this.earnedGold = 0,
    this.lastCheckpoint,
    this.gamesPlayedToday = 0,
    this.lastGameDate,
    this.selectedAnswer,
    this.isAnswerRevealed = false,
    this.isLoadingHint = false,
    this.errorMessage,
  });

  /// Entry cost in gold to play (LOGICA_DE_NEGOCIO.md)
  static const int entryCostGold = 100;

  static const int maxGamesPerDay = 3;

  MillionaireQuestion? get currentQuestion {
    if (currentQuestionIndex < questions.length) {
      return questions[currentQuestionIndex];
    }
    return null;
  }

  bool get canPlay => gamesPlayedToday < maxGamesPerDay;

  int get remainingGames => maxGamesPerDay - gamesPlayedToday;

  bool get isLastQuestion => currentQuestionIndex == 14; // 0-indexed

  LifelineState? getLifeline(LifelineType type) {
    try {
      return lifelines.firstWhere((l) => l.type == type);
    } catch (_) {
      return null;
    }
  }

  bool isLifelineAvailable(LifelineType type) {
    final lifeline = getLifeline(type);
    return lifeline != null && !lifeline.isUsed;
  }

  MillionaireGameState copyWith({
    MillionaireGameStatus? status,
    List<MillionaireQuestion>? questions,
    int? currentQuestionIndex,
    List<LifelineState>? lifelines,
    int? earnedXp,
    int? earnedGold,
    Checkpoint? lastCheckpoint,
    int? gamesPlayedToday,
    DateTime? lastGameDate,
    String? selectedAnswer,
    bool? isAnswerRevealed,
    bool? isLoadingHint,
    String? errorMessage,
    bool clearSelectedAnswer = false,
    bool clearLastCheckpoint = false,
    bool clearErrorMessage = false,
  }) {
    return MillionaireGameState(
      status: status ?? this.status,
      questions: questions ?? this.questions,
      currentQuestionIndex: currentQuestionIndex ?? this.currentQuestionIndex,
      lifelines: lifelines ?? this.lifelines,
      earnedXp: earnedXp ?? this.earnedXp,
      earnedGold: earnedGold ?? this.earnedGold,
      lastCheckpoint: clearLastCheckpoint ? null : (lastCheckpoint ?? this.lastCheckpoint),
      gamesPlayedToday: gamesPlayedToday ?? this.gamesPlayedToday,
      lastGameDate: lastGameDate ?? this.lastGameDate,
      selectedAnswer: clearSelectedAnswer ? null : (selectedAnswer ?? this.selectedAnswer),
      isAnswerRevealed: isAnswerRevealed ?? this.isAnswerRevealed,
      isLoadingHint: isLoadingHint ?? this.isLoadingHint,
      errorMessage: clearErrorMessage ? null : (errorMessage ?? this.errorMessage),
    );
  }
}

/// Result of a completed game
class MillionaireResult {
  final bool isWin;
  final int questionsAnswered;
  final int totalXp;
  final int totalGold;
  final Checkpoint? reachedCheckpoint;
  final int correctAnswers;

  const MillionaireResult({
    required this.isWin,
    required this.questionsAnswered,
    required this.totalXp,
    required this.totalGold,
    this.reachedCheckpoint,
    required this.correctAnswers,
  });
}
