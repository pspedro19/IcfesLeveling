/// Progreso global del usuario
class UserProgress {
  final int level;
  final String rank;
  final int totalXp;
  final int gold;
  final int hearts;
  final bool isGraceMode;
  final int currentStreak;
  final double streakMultiplier;
  final Map<String, KingdomProgress> kingdoms;

  UserProgress({
    required this.level,
    required this.rank,
    required this.totalXp,
    required this.gold,
    required this.hearts,
    required this.isGraceMode,
    required this.currentStreak,
    required this.streakMultiplier,
    required this.kingdoms,
  });

  factory UserProgress.fromJson(Map<String, dynamic> json) {
    final kingdomsMap = <String, KingdomProgress>{};
    final kingdomsJson = json['kingdoms'] as Map<String, dynamic>? ?? {};

    kingdomsJson.forEach((key, value) {
      kingdomsMap[key] = KingdomProgress.fromJson(value);
    });

    return UserProgress(
      level: json['level'] ?? 1,
      rank: json['rank'] ?? 'E',
      totalXp: json['total_xp'] ?? 0,
      gold: json['gold'] ?? 100,
      hearts: json['hearts'] ?? 5,
      isGraceMode: json['is_grace_mode'] ?? false,
      currentStreak: json['current_streak'] ?? 0,
      streakMultiplier: (json['streak_multiplier'] ?? 1.0).toDouble(),
      kingdoms: kingdomsMap,
    );
  }
}

/// Progreso en un reino especifico
class KingdomProgress {
  final String kingdomId;
  final double overallMastery;
  final String rank;
  final bool diagnosticCompleted;
  final bool bossDefeated;
  final int totalStars;
  final Map<String, NodeProgress> nodes;

  KingdomProgress({
    required this.kingdomId,
    required this.overallMastery,
    required this.rank,
    required this.diagnosticCompleted,
    required this.bossDefeated,
    required this.totalStars,
    required this.nodes,
  });

  factory KingdomProgress.fromJson(Map<String, dynamic> json) {
    final nodesMap = <String, NodeProgress>{};
    final nodesJson = json['nodes'] as Map<String, dynamic>? ?? {};

    nodesJson.forEach((key, value) {
      nodesMap[key] = NodeProgress.fromJson(value);
    });

    return KingdomProgress(
      kingdomId: json['kingdom_id'] ?? '',
      overallMastery: (json['overall_mastery'] ?? 0.0).toDouble(),
      rank: json['rank'] ?? 'E',
      diagnosticCompleted: json['diagnostic_completed'] ?? false,
      bossDefeated: json['boss_defeated'] ?? false,
      totalStars: json['total_stars'] ?? 0,
      nodes: nodesMap,
    );
  }
}

/// Progreso en un nodo especifico
class NodeProgress {
  final String nodeId;
  final double masteryPercent;
  final int starsEarned;
  final int timesCompleted;
  final double bestAccuracy;
  final bool isUnlocked;
  final DateTime? unlockedAt;

  NodeProgress({
    required this.nodeId,
    required this.masteryPercent,
    required this.starsEarned,
    required this.timesCompleted,
    required this.bestAccuracy,
    required this.isUnlocked,
    this.unlockedAt,
  });

  factory NodeProgress.fromJson(Map<String, dynamic> json) {
    return NodeProgress(
      nodeId: json['node_id'] ?? '',
      masteryPercent: (json['mastery_percent'] ?? 0.0).toDouble(),
      starsEarned: json['stars_earned'] ?? 0,
      timesCompleted: json['times_completed'] ?? 0,
      bestAccuracy: (json['best_accuracy'] ?? 0.0).toDouble(),
      isUnlocked: json['is_unlocked'] ?? false,
      unlockedAt: json['unlocked_at'] != null 
          ? DateTime.parse(json['unlocked_at']) 
          : null,
    );
  }
}
