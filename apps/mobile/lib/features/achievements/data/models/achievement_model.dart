/// Achievement Model for ICFES Leveling
/// Represents achievements/badges that users can unlock

class AchievementModel {
  final String id;
  final String name;
  final String description;
  final String icon;
  final AchievementCategory category;
  final AchievementRarity rarity;
  final int xpReward;
  final int goldReward;
  final AchievementRequirement requirement;
  final bool isSecret;
  final DateTime? unlockedAt;
  final double progress; // 0.0 to 1.0

  const AchievementModel({
    required this.id,
    required this.name,
    required this.description,
    required this.icon,
    required this.category,
    required this.rarity,
    this.xpReward = 0,
    this.goldReward = 0,
    required this.requirement,
    this.isSecret = false,
    this.unlockedAt,
    this.progress = 0.0,
  });

  bool get isUnlocked => unlockedAt != null;

  factory AchievementModel.fromJson(Map<String, dynamic> json) {
    return AchievementModel(
      id: json['id'] ?? '',
      name: json['name'] ?? '',
      description: json['description'] ?? '',
      icon: json['icon'] ?? 'trophy',
      category: AchievementCategory.fromString(json['category'] ?? 'general'),
      rarity: AchievementRarity.fromString(json['rarity'] ?? 'common'),
      xpReward: json['xp_reward'] ?? 0,
      goldReward: json['gold_reward'] ?? 0,
      requirement: AchievementRequirement.fromJson(json['requirement'] ?? {}),
      isSecret: json['is_secret'] ?? false,
      unlockedAt: json['unlocked_at'] != null
          ? DateTime.parse(json['unlocked_at'])
          : null,
      progress: (json['progress'] ?? 0.0).toDouble(),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'name': name,
      'description': description,
      'icon': icon,
      'category': category.value,
      'rarity': rarity.value,
      'xp_reward': xpReward,
      'gold_reward': goldReward,
      'requirement': requirement.toJson(),
      'is_secret': isSecret,
      'unlocked_at': unlockedAt?.toIso8601String(),
      'progress': progress,
    };
  }

  AchievementModel copyWith({
    String? id,
    String? name,
    String? description,
    String? icon,
    AchievementCategory? category,
    AchievementRarity? rarity,
    int? xpReward,
    int? goldReward,
    AchievementRequirement? requirement,
    bool? isSecret,
    DateTime? unlockedAt,
    double? progress,
  }) {
    return AchievementModel(
      id: id ?? this.id,
      name: name ?? this.name,
      description: description ?? this.description,
      icon: icon ?? this.icon,
      category: category ?? this.category,
      rarity: rarity ?? this.rarity,
      xpReward: xpReward ?? this.xpReward,
      goldReward: goldReward ?? this.goldReward,
      requirement: requirement ?? this.requirement,
      isSecret: isSecret ?? this.isSecret,
      unlockedAt: unlockedAt ?? this.unlockedAt,
      progress: progress ?? this.progress,
    );
  }
}

/// Achievement categories
enum AchievementCategory {
  streak('streak', 'Rachas'),
  practice('practice', 'Practica'),
  mastery('mastery', 'Maestria'),
  social('social', 'Social'),
  special('special', 'Especial'),
  general('general', 'General');

  final String value;
  final String displayName;

  const AchievementCategory(this.value, this.displayName);

  static AchievementCategory fromString(String value) {
    return AchievementCategory.values.firstWhere(
      (e) => e.value == value,
      orElse: () => AchievementCategory.general,
    );
  }
}

/// Achievement rarity levels
enum AchievementRarity {
  common('common', 'Comun', 0xFF9E9E9E),
  rare('rare', 'Raro', 0xFF2196F3),
  epic('epic', 'Epico', 0xFF9C27B0),
  legendary('legendary', 'Legendario', 0xFFFF9800);

  final String value;
  final String displayName;
  final int colorValue;

  const AchievementRarity(this.value, this.displayName, this.colorValue);

  static AchievementRarity fromString(String value) {
    return AchievementRarity.values.firstWhere(
      (e) => e.value == value,
      orElse: () => AchievementRarity.common,
    );
  }
}

/// Achievement requirement definition
class AchievementRequirement {
  final String type; // streak_days, questions_answered, subjects_mastered, etc.
  final int targetValue;
  final String? subjectId; // Optional for subject-specific achievements
  final Map<String, dynamic>? extraConditions;

  const AchievementRequirement({
    required this.type,
    required this.targetValue,
    this.subjectId,
    this.extraConditions,
  });

  factory AchievementRequirement.fromJson(Map<String, dynamic> json) {
    return AchievementRequirement(
      type: json['type'] ?? 'unknown',
      targetValue: json['target_value'] ?? 0,
      subjectId: json['subject_id'],
      extraConditions: json['extra_conditions'],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'type': type,
      'target_value': targetValue,
      if (subjectId != null) 'subject_id': subjectId,
      if (extraConditions != null) 'extra_conditions': extraConditions,
    };
  }
}

/// Response model for achievements list
class AchievementsResponse {
  final List<AchievementModel> achievements;
  final int totalUnlocked;
  final int totalAvailable;

  const AchievementsResponse({
    required this.achievements,
    required this.totalUnlocked,
    required this.totalAvailable,
  });

  factory AchievementsResponse.fromJson(Map<String, dynamic> json) {
    final achievementsList = (json['achievements'] as List? ?? [])
        .map((a) => AchievementModel.fromJson(a))
        .toList();

    return AchievementsResponse(
      achievements: achievementsList,
      totalUnlocked: json['total_unlocked'] ??
          achievementsList.where((a) => a.isUnlocked).length,
      totalAvailable: json['total_available'] ?? achievementsList.length,
    );
  }
}

/// Recently unlocked achievement for notifications
class UnlockedAchievement {
  final AchievementModel achievement;
  final DateTime unlockedAt;
  final bool isNew;

  const UnlockedAchievement({
    required this.achievement,
    required this.unlockedAt,
    this.isNew = true,
  });

  factory UnlockedAchievement.fromJson(Map<String, dynamic> json) {
    return UnlockedAchievement(
      achievement: AchievementModel.fromJson(json['achievement'] ?? json),
      unlockedAt: DateTime.parse(json['unlocked_at'] ?? DateTime.now().toIso8601String()),
      isNew: json['is_new'] ?? true,
    );
  }
}
