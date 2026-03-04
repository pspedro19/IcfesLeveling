/// Dungeon Models
/// Models for Dungeon feature matching backend API contract

import '../../domain/entities/dungeon_gate.dart';
import '../../domain/entities/dungeon_node.dart';
import '../../domain/entities/combat_state.dart';

/// Response when fetching available dungeon gates
class DungeonGatesResponse {
  final List<DungeonGateModel> gates;
  final int totalGates;

  DungeonGatesResponse({
    required this.gates,
    required this.totalGates,
  });

  factory DungeonGatesResponse.fromJson(Map<String, dynamic> json) {
    final gatesList = json['gates'] as List? ?? [];
    return DungeonGatesResponse(
      gates: gatesList.map((g) => DungeonGateModel.fromJson(g)).toList(),
      totalGates: json['total_gates'] ?? gatesList.length,
    );
  }
}

/// Model for DungeonGate from API
class DungeonGateModel {
  final String id;
  final String name;
  final String description;
  final String type;
  final String difficultyRank;
  final int recommendedLevel;
  final int totalRooms;
  final int timeLimitMinutes;
  final bool isLocked;
  final double completionPercentage;
  final String? subjectId;
  final String? subjectName;
  final int? requiredLevel;
  final List<String>? rewards;

  DungeonGateModel({
    required this.id,
    required this.name,
    required this.description,
    required this.type,
    required this.difficultyRank,
    required this.recommendedLevel,
    required this.totalRooms,
    required this.timeLimitMinutes,
    this.isLocked = false,
    this.completionPercentage = 0.0,
    this.subjectId,
    this.subjectName,
    this.requiredLevel,
    this.rewards,
  });

  factory DungeonGateModel.fromJson(Map<String, dynamic> json) {
    return DungeonGateModel(
      id: json['id'] ?? '',
      name: json['name'] ?? '',
      description: json['description'] ?? '',
      type: json['type'] ?? 'normal',
      difficultyRank: json['difficulty_rank'] ?? 'D',
      recommendedLevel: json['rec_level'] ?? json['recommended_level'] ?? 1,
      totalRooms: json['total_rooms'] ?? 5,
      timeLimitMinutes: json['time_limit'] ?? json['time_limit_minutes'] ?? 30,
      isLocked: json['is_locked'] ?? false,
      completionPercentage: (json['completion_percentage'] as num?)?.toDouble() ?? 0.0,
      subjectId: json['subject_id'],
      subjectName: json['subject_name'],
      requiredLevel: json['required_level'],
      rewards: (json['rewards'] as List?)?.map((e) => e.toString()).toList(),
    );
  }

  /// Convert to domain entity
  DungeonGate toEntity() {
    return DungeonGate(
      id: id,
      name: name,
      description: description,
      type: type,
      difficultyRank: difficultyRank,
      recommendedLevel: recommendedLevel,
      totalRooms: totalRooms,
      timeLimitMinutes: timeLimitMinutes,
      isLocked: isLocked,
      completionPercentage: completionPercentage,
    );
  }
}

/// Response when entering a dungeon gate
class DungeonRunResponse {
  final String runId;
  final String gateId;
  final String gateName;
  final List<DungeonNodeModel> nodes;
  final int totalRooms;
  final int timeLimitSeconds;
  final DateTime startedAt;
  final PlayerStatsModel playerStats;
  final DungeonEncounterModel? currentEncounter;

  DungeonRunResponse({
    required this.runId,
    required this.gateId,
    required this.gateName,
    required this.nodes,
    required this.totalRooms,
    required this.timeLimitSeconds,
    required this.startedAt,
    required this.playerStats,
    this.currentEncounter,
  });

  factory DungeonRunResponse.fromJson(Map<String, dynamic> json) {
    final nodesList = json['nodes'] as List? ?? [];
    return DungeonRunResponse(
      runId: json['run_id'] ?? '',
      gateId: json['gate_id'] ?? '',
      gateName: json['gate_name'] ?? '',
      nodes: nodesList.map((n) => DungeonNodeModel.fromJson(n)).toList(),
      totalRooms: json['total_rooms'] ?? nodesList.length,
      timeLimitSeconds: json['time_limit_seconds'] ?? 1800,
      startedAt: json['started_at'] != null
          ? DateTime.parse(json['started_at'])
          : DateTime.now(),
      playerStats: PlayerStatsModel.fromJson(json['player_stats'] ?? {}),
      currentEncounter: json['current_encounter'] != null
          ? DungeonEncounterModel.fromJson(json['current_encounter'])
          : null,
    );
  }
}

/// Model for DungeonNode from API
class DungeonNodeModel {
  final String id;
  final int roomNumber;
  final String type;
  final bool isCompleted;
  final bool isCurrent;
  final bool isLocked;
  final int stars;
  final String? enemyName;
  final String? enemyImageUrl;
  final int? enemyHp;

  DungeonNodeModel({
    required this.id,
    required this.roomNumber,
    required this.type,
    this.isCompleted = false,
    this.isCurrent = false,
    this.isLocked = true,
    this.stars = 0,
    this.enemyName,
    this.enemyImageUrl,
    this.enemyHp,
  });

  factory DungeonNodeModel.fromJson(Map<String, dynamic> json) {
    return DungeonNodeModel(
      id: json['id'] ?? '',
      roomNumber: json['room_number'] ?? 0,
      type: json['type'] ?? 'monster',
      isCompleted: json['is_completed'] ?? false,
      isCurrent: json['is_current'] ?? false,
      isLocked: json['is_locked'] ?? true,
      stars: json['stars'] ?? 0,
      enemyName: json['enemy_name'],
      enemyImageUrl: json['enemy_image_url'],
      enemyHp: json['enemy_hp'],
    );
  }

  /// Convert to domain entity
  DungeonNode toEntity() {
    return DungeonNode(
      id: id,
      roomNumber: roomNumber,
      type: type,
      isCompleted: isCompleted,
      isCurrent: isCurrent,
      isLocked: isLocked,
      stars: stars,
    );
  }
}

/// Player stats during dungeon run
class PlayerStatsModel {
  final int hp;
  final int maxHp;
  final int energy;
  final int maxEnergy;
  final int shield;
  final int comboCount;
  final int xpEarned;
  final int coinsEarned;

  PlayerStatsModel({
    required this.hp,
    required this.maxHp,
    this.energy = 100,
    this.maxEnergy = 100,
    this.shield = 0,
    this.comboCount = 0,
    this.xpEarned = 0,
    this.coinsEarned = 0,
  });

  factory PlayerStatsModel.fromJson(Map<String, dynamic> json) {
    return PlayerStatsModel(
      hp: json['hp'] ?? 100,
      maxHp: json['max_hp'] ?? 100,
      energy: json['energy'] ?? 100,
      maxEnergy: json['max_energy'] ?? 100,
      shield: json['shield'] ?? 0,
      comboCount: json['combo_count'] ?? 0,
      xpEarned: json['xp_earned'] ?? 0,
      coinsEarned: json['coins_earned'] ?? 0,
    );
  }
}

/// Current encounter in dungeon
class DungeonEncounterModel {
  final String encounterId;
  final String nodeId;
  final String type; // 'monster', 'boss', 'treasure', 'rest'
  final EnemyModel? enemy;
  final List<DungeonQuestionModel> questions;
  final int currentQuestionIndex;
  final int totalQuestions;

  DungeonEncounterModel({
    required this.encounterId,
    required this.nodeId,
    required this.type,
    this.enemy,
    required this.questions,
    this.currentQuestionIndex = 0,
    required this.totalQuestions,
  });

  factory DungeonEncounterModel.fromJson(Map<String, dynamic> json) {
    final questionsList = json['questions'] as List? ?? [];
    return DungeonEncounterModel(
      encounterId: json['encounter_id'] ?? '',
      nodeId: json['node_id'] ?? '',
      type: json['type'] ?? 'monster',
      enemy: json['enemy'] != null ? EnemyModel.fromJson(json['enemy']) : null,
      questions: questionsList.map((q) => DungeonQuestionModel.fromJson(q)).toList(),
      currentQuestionIndex: json['current_question_index'] ?? 0,
      totalQuestions: json['total_questions'] ?? questionsList.length,
    );
  }
}

/// Enemy model for dungeon encounters
class EnemyModel {
  final String id;
  final String name;
  final String? imageUrl;
  final int hp;
  final int maxHp;
  final int attackPower;
  final String difficulty;
  final String? description;

  EnemyModel({
    required this.id,
    required this.name,
    this.imageUrl,
    required this.hp,
    required this.maxHp,
    this.attackPower = 10,
    this.difficulty = 'normal',
    this.description,
  });

  factory EnemyModel.fromJson(Map<String, dynamic> json) {
    return EnemyModel(
      id: json['id'] ?? '',
      name: json['name'] ?? 'Unknown Enemy',
      imageUrl: json['image_url'],
      hp: json['hp'] ?? json['current_hp'] ?? 100,
      maxHp: json['max_hp'] ?? 100,
      attackPower: json['attack_power'] ?? 10,
      difficulty: json['difficulty'] ?? 'normal',
      description: json['description'],
    );
  }
}

/// Question model for dungeon encounters
class DungeonQuestionModel {
  final String id;
  final String text;
  final String? imageUrl;
  final List<DungeonQuestionOption> options;
  final int? timeLimit;
  final int xpValue;
  final int damageValue;

  DungeonQuestionModel({
    required this.id,
    required this.text,
    this.imageUrl,
    required this.options,
    this.timeLimit,
    this.xpValue = 10,
    this.damageValue = 20,
  });

  factory DungeonQuestionModel.fromJson(Map<String, dynamic> json) {
    final optionsList = json['options'] as List? ?? [];
    return DungeonQuestionModel(
      id: json['id'] ?? '',
      text: json['text'] ?? json['pregunta_texto'] ?? '',
      imageUrl: json['image_url'] ?? json['pregunta_imagen'],
      options: optionsList.map((o) => DungeonQuestionOption.fromJson(o)).toList(),
      timeLimit: json['time_limit'],
      xpValue: json['xp_value'] ?? 10,
      damageValue: json['damage_value'] ?? 20,
    );
  }
}

/// Question option model
class DungeonQuestionOption {
  final String id;
  final String? text;
  final String? imageUrl;

  DungeonQuestionOption({
    required this.id,
    this.text,
    this.imageUrl,
  });

  factory DungeonQuestionOption.fromJson(Map<String, dynamic> json) {
    return DungeonQuestionOption(
      id: json['id'] ?? '',
      text: json['text'],
      imageUrl: json['image_url'],
    );
  }
}

/// Result of submitting answers to an encounter
class EncounterResultModel {
  final bool correct;
  final String correctAnswerId;
  final int damageDealt;
  final int damageTaken;
  final int xpEarned;
  final int coinsEarned;
  final int currentCombo;
  final bool enemyDefeated;
  final bool encounterCompleted;
  final int enemyCurrentHp;
  final int playerCurrentHp;
  final int starsEarned;
  final String? explanation;
  final NextNodeInfo? nextNode;

  EncounterResultModel({
    required this.correct,
    required this.correctAnswerId,
    required this.damageDealt,
    this.damageTaken = 0,
    required this.xpEarned,
    this.coinsEarned = 0,
    required this.currentCombo,
    required this.enemyDefeated,
    required this.encounterCompleted,
    required this.enemyCurrentHp,
    required this.playerCurrentHp,
    this.starsEarned = 0,
    this.explanation,
    this.nextNode,
  });

  factory EncounterResultModel.fromJson(Map<String, dynamic> json) {
    return EncounterResultModel(
      correct: json['correct'] ?? false,
      correctAnswerId: json['correct_answer_id'] ?? '',
      damageDealt: json['damage_dealt'] ?? 0,
      damageTaken: json['damage_taken'] ?? 0,
      xpEarned: json['xp_earned'] ?? 0,
      coinsEarned: json['coins_earned'] ?? 0,
      currentCombo: json['current_combo'] ?? 0,
      enemyDefeated: json['enemy_defeated'] ?? false,
      encounterCompleted: json['encounter_completed'] ?? false,
      enemyCurrentHp: json['enemy_current_hp'] ?? 0,
      playerCurrentHp: json['player_current_hp'] ?? 100,
      starsEarned: json['stars_earned'] ?? 0,
      explanation: json['explanation'],
      nextNode: json['next_node'] != null
          ? NextNodeInfo.fromJson(json['next_node'])
          : null,
    );
  }
}

/// Info about the next node after completing an encounter
class NextNodeInfo {
  final String nodeId;
  final int roomNumber;
  final String type;

  NextNodeInfo({
    required this.nodeId,
    required this.roomNumber,
    required this.type,
  });

  factory NextNodeInfo.fromJson(Map<String, dynamic> json) {
    return NextNodeInfo(
      nodeId: json['node_id'] ?? '',
      roomNumber: json['room_number'] ?? 0,
      type: json['type'] ?? 'monster',
    );
  }
}

/// Response when dungeon run is completed
class DungeonCompletionModel {
  final String runId;
  final bool success;
  final int totalXp;
  final int totalCoins;
  final int totalStars;
  final int roomsCleared;
  final int totalRooms;
  final int timeSpentSeconds;
  final double accuracyPercentage;
  final int bestCombo;
  final List<DungeonReward> rewards;
  final bool newAchievement;
  final String? achievementId;

  DungeonCompletionModel({
    required this.runId,
    required this.success,
    required this.totalXp,
    required this.totalCoins,
    required this.totalStars,
    required this.roomsCleared,
    required this.totalRooms,
    required this.timeSpentSeconds,
    required this.accuracyPercentage,
    required this.bestCombo,
    required this.rewards,
    this.newAchievement = false,
    this.achievementId,
  });

  factory DungeonCompletionModel.fromJson(Map<String, dynamic> json) {
    final rewardsList = json['rewards'] as List? ?? [];
    return DungeonCompletionModel(
      runId: json['run_id'] ?? '',
      success: json['success'] ?? false,
      totalXp: json['total_xp'] ?? 0,
      totalCoins: json['total_coins'] ?? 0,
      totalStars: json['total_stars'] ?? 0,
      roomsCleared: json['rooms_cleared'] ?? 0,
      totalRooms: json['total_rooms'] ?? 0,
      timeSpentSeconds: json['time_spent_seconds'] ?? 0,
      accuracyPercentage: (json['accuracy_percentage'] as num?)?.toDouble() ?? 0.0,
      bestCombo: json['best_combo'] ?? 0,
      rewards: rewardsList.map((r) => DungeonReward.fromJson(r)).toList(),
      newAchievement: json['new_achievement'] ?? false,
      achievementId: json['achievement_id'],
    );
  }
}

/// Reward earned in dungeon
class DungeonReward {
  final String type; // 'xp', 'coins', 'item', 'badge'
  final int? amount;
  final String? itemId;
  final String? name;
  final String? description;
  final String? imageUrl;

  DungeonReward({
    required this.type,
    this.amount,
    this.itemId,
    this.name,
    this.description,
    this.imageUrl,
  });

  factory DungeonReward.fromJson(Map<String, dynamic> json) {
    return DungeonReward(
      type: json['type'] ?? 'xp',
      amount: json['amount'],
      itemId: json['item_id'],
      name: json['name'],
      description: json['description'],
      imageUrl: json['image_url'],
    );
  }
}

/// Dungeon run history entry
class DungeonRunHistoryModel {
  final String runId;
  final String gateId;
  final String gateName;
  final String difficultyRank;
  final bool completed;
  final int starsEarned;
  final int xpEarned;
  final int roomsCleared;
  final int totalRooms;
  final DateTime startedAt;
  final DateTime? completedAt;
  final int durationSeconds;

  DungeonRunHistoryModel({
    required this.runId,
    required this.gateId,
    required this.gateName,
    required this.difficultyRank,
    required this.completed,
    required this.starsEarned,
    required this.xpEarned,
    required this.roomsCleared,
    required this.totalRooms,
    required this.startedAt,
    this.completedAt,
    required this.durationSeconds,
  });

  factory DungeonRunHistoryModel.fromJson(Map<String, dynamic> json) {
    return DungeonRunHistoryModel(
      runId: json['run_id'] ?? '',
      gateId: json['gate_id'] ?? '',
      gateName: json['gate_name'] ?? '',
      difficultyRank: json['difficulty_rank'] ?? 'D',
      completed: json['completed'] ?? false,
      starsEarned: json['stars_earned'] ?? 0,
      xpEarned: json['xp_earned'] ?? 0,
      roomsCleared: json['rooms_cleared'] ?? 0,
      totalRooms: json['total_rooms'] ?? 0,
      startedAt: json['started_at'] != null
          ? DateTime.parse(json['started_at'])
          : DateTime.now(),
      completedAt: json['completed_at'] != null
          ? DateTime.parse(json['completed_at'])
          : null,
      durationSeconds: json['duration_seconds'] ?? 0,
    );
  }
}

/// Extension to convert CombatState for WebSocket updates
extension CombatStateModelExt on CombatState {
  static CombatState fromJson(Map<String, dynamic> json) {
    return CombatState(
      runId: json['run_id'] ?? '',
      currentTurn: json['current_turn'] ?? 1,
      playerHp: json['player_hp'] ?? 100,
      playerMaxHp: json['player_max_hp'] ?? 100,
      playerEnergy: json['player_energy'] ?? 100,
      enemyName: json['enemy_name'] ?? 'Unknown',
      enemyImageUrl: json['enemy_image_url'] ?? '',
      enemyHp: json['enemy_hp'] ?? 100,
      enemyMaxHp: json['enemy_max_hp'] ?? 100,
      isPlayerTurn: json['is_player_turn'] ?? true,
      isAnimating: json['is_animating'] ?? false,
      lastActionText: json['last_action_text'],
      comboCounter: json['combo_counter'] ?? 0,
    );
  }
}
