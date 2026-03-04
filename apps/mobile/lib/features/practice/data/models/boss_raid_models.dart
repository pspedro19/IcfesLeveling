/// Boss Raid Models
/// Models for Boss Raid feature matching backend API contract

/// Type alias for backwards compatibility
typedef BossRaidCompletionModel = BossRaidCompleteResponse;

class BossRaidStatusModel {
  final bool isActive;
  final DateTime startsAt;
  final DateTime endsAt;
  final CurrentBossModel? currentBoss; // Nullable when raid not active
  final double xpMultiplier;
  final int myDamageDealt;
  final int? myRank; // Nullable when user hasn't participated
  final int? timeRemainingSeconds; // Time remaining in seconds
  final DateTime? nextRaidAt; // When next raid starts (if not active)

  BossRaidStatusModel({
    required this.isActive,
    required this.startsAt,
    required this.endsAt,
    this.currentBoss,
    required this.xpMultiplier,
    required this.myDamageDealt,
    this.myRank,
    this.timeRemainingSeconds,
    this.nextRaidAt,
  });

  factory BossRaidStatusModel.fromJson(Map<String, dynamic> json) {
    return BossRaidStatusModel(
      isActive: json['is_active'] ?? false,
      startsAt: DateTime.parse(json['starts_at']),
      endsAt: DateTime.parse(json['ends_at']),
      currentBoss: json['current_boss'] != null
          ? CurrentBossModel.fromJson(json['current_boss'])
          : null,
      xpMultiplier: (json['xp_multiplier'] as num?)?.toDouble() ?? 3.0,
      myDamageDealt: json['my_damage_dealt'] ?? 0,
      myRank: json['my_rank'],
      timeRemainingSeconds: json['time_remaining_seconds'],
      nextRaidAt: json['next_raid_at'] != null
          ? DateTime.parse(json['next_raid_at'])
          : null,
    );
  }
}

class CurrentBossModel {
  final String id;
  final String name;
  final String? description;
  final String? subjectId;
  final String? subjectName;
  final int hp;
  final int currentHp;
  final String difficulty;
  final bool isDefeated;
  final DateTime? defeatedAt;

  CurrentBossModel({
    required this.id,
    required this.name,
    this.description,
    this.subjectId,
    this.subjectName,
    required this.hp,
    required this.currentHp,
    required this.difficulty,
    required this.isDefeated,
    this.defeatedAt,
  });

  factory CurrentBossModel.fromJson(Map<String, dynamic> json) {
    return CurrentBossModel(
      id: json['id'],
      name: json['name'],
      description: json['description'],
      subjectId: json['subject_id'],
      subjectName: json['subject_name'],
      hp: json['hp'],
      currentHp: json['current_hp'],
      difficulty: json['difficulty'] ?? 'medium',
      isDefeated: json['is_defeated'] ?? false,
      defeatedAt: json['defeated_at'] != null
          ? DateTime.parse(json['defeated_at'])
          : null,
    );
  }
}


class BossRaidSessionModel {
  final String sessionId;
  final CurrentBossModel boss;
  final List<RaidQuestionModel> questions;
  final int totalQuestions;
  final double xpMultiplier;
  final DateTime startedAt;

  BossRaidSessionModel({
    required this.sessionId,
    required this.boss,
    required this.questions,
    required this.totalQuestions,
    required this.xpMultiplier,
    required this.startedAt,
  });

  factory BossRaidSessionModel.fromJson(Map<String, dynamic> json) {
    var questionsList = json['questions'] as List;
    List<RaidQuestionModel> questions =
        questionsList.map((i) => RaidQuestionModel.fromJson(i)).toList();

    return BossRaidSessionModel(
      sessionId: json['session_id'],
      boss: CurrentBossModel.fromJson(json['boss']),
      questions: questions,
      totalQuestions: json['total_questions'],
      xpMultiplier: (json['xp_multiplier'] as num?)?.toDouble() ?? 3.0,
      startedAt: DateTime.parse(json['started_at']),
    );
  }
}

/// Question model specific to Boss Raid (matches backend RaidQuestion)
class RaidQuestionModel {
  final String id;
  final String text;
  final String? imageUrl;
  final List<RaidQuestionOption> options;

  RaidQuestionModel({
    required this.id,
    required this.text,
    this.imageUrl,
    required this.options,
  });

  factory RaidQuestionModel.fromJson(Map<String, dynamic> json) {
    var optionsList = json['options'] as List? ?? [];
    List<RaidQuestionOption> options =
        optionsList.map((i) => RaidQuestionOption.fromJson(i)).toList();

    return RaidQuestionModel(
      id: json['id'],
      text: json['text'] ?? '',
      imageUrl: json['image_url'],
      options: options,
    );
  }
}

class RaidQuestionOption {
  final String id;
  final String? text;
  final String? imageUrl;

  RaidQuestionOption({
    required this.id,
    this.text,
    this.imageUrl,
  });

  factory RaidQuestionOption.fromJson(Map<String, dynamic> json) {
    return RaidQuestionOption(
      id: json['id'],
      text: json['text'],
      imageUrl: json['image_url'],
    );
  }
}

/// Response model for submitting a Boss Raid answer
class BossRaidAnswerResponse {
  final bool correct;
  final String correctAnswerId;
  final int damageDealt;
  final int xpEarned;
  final int currentCombo;
  final int bossCurrentHp;
  final bool bossDefeated;

  BossRaidAnswerResponse({
    required this.correct,
    required this.correctAnswerId,
    required this.damageDealt,
    required this.xpEarned,
    required this.currentCombo,
    required this.bossCurrentHp,
    required this.bossDefeated,
  });

  factory BossRaidAnswerResponse.fromJson(Map<String, dynamic> json) {
    return BossRaidAnswerResponse(
      correct: json['correct'] ?? false,
      correctAnswerId: json['correct_answer_id'] ?? '',
      damageDealt: json['damage_dealt'] ?? 0,
      xpEarned: json['xp_earned'] ?? 0,
      currentCombo: json['current_combo'] ?? 0,
      bossCurrentHp: json['boss_current_hp'] ?? 0,
      bossDefeated: json['boss_defeated'] ?? false,
    );
  }
}

/// Response model for completing a Boss Raid
class BossRaidCompleteResponse {
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

  BossRaidCompleteResponse({
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

  factory BossRaidCompleteResponse.fromJson(Map<String, dynamic> json) {
    var rewardsList = json['rewards'] as List? ?? [];
    List<RaidReward> rewards =
        rewardsList.map((i) => RaidReward.fromJson(i)).toList();

    return BossRaidCompleteResponse(
      bossDefeated: json['boss_defeated'] ?? false,
      totalDamage: json['total_damage'] ?? 0,
      totalXp: json['total_xp'] ?? 0,
      correctAnswers: json['correct_answers'] ?? 0,
      totalQuestions: json['total_questions'] ?? 0,
      accuracyPercentage: (json['accuracy_percentage'] as num?)?.toDouble() ?? 0.0,
      bestCombo: json['best_combo'] ?? 0,
      rankInRaid: json['rank_in_raid'],
      rewards: rewards,
      sessionDurationSeconds: json['session_duration_seconds'] ?? 0,
    );
  }
}

class RaidReward {
  final String type;
  final int? amount;
  final String? name;

  RaidReward({
    required this.type,
    this.amount,
    this.name,
  });

  factory RaidReward.fromJson(Map<String, dynamic> json) {
    return RaidReward(
      type: json['type'],
      amount: json['amount'],
      name: json['name'],
    );
  }
}
