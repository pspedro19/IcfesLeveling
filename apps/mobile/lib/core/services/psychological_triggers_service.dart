import 'package:flutter/material.dart';
import 'dart:math';

/// Psychological Triggers Service
/// Implements gamification psychology patterns for engagement:
/// - Variable Ratio Reinforcement (unpredictable rewards)
/// - Social Proof (rankings, peer comparison)
/// - Loss Aversion (streak protection, rank demotion warnings)
/// - Progress Illusion (optimized progress bars)
/// - Endowed Progress (start with something earned)
class PsychologicalTriggersService {
  static final PsychologicalTriggersService _instance = PsychologicalTriggersService._();
  factory PsychologicalTriggersService() => _instance;
  PsychologicalTriggersService._();

  final Random _random = Random();
  int _recentBonusCount = 0;
  DateTime _lastBonusTime = DateTime.now().subtract(const Duration(hours: 1));

  // =========================================================================
  // VARIABLE RATIO REINFORCEMENT
  // =========================================================================

  /// Apply variable ratio reinforcement to rewards
  /// Sometimes gives bonus rewards to create anticipation
  VariableReward getVariableReward({
    required String actionType,
    required int baseReward,
  }) {
    // Reset bonus count if more than 1 hour has passed
    if (DateTime.now().difference(_lastBonusTime).inHours >= 1) {
      _recentBonusCount = 0;
    }

    // Variable ratio schedule: roughly 1 in 5 actions gets bonus
    // But never more than 2 bonuses in recent period
    final bonusChance = _recentBonusCount < 2 ? 0.20 : 0.05;
    final isBonus = _random.nextDouble() < bonusChance;

    if (!isBonus) {
      return VariableReward(
        baseReward: baseReward,
        totalReward: baseReward,
        hasBonus: false,
      );
    }

    // Determine bonus type and amount
    final bonusRoll = _random.nextDouble();
    BonusType bonusType;
    int bonusAmount;
    String bonusMessage;

    if (bonusRoll < 0.5) {
      // Small XP bonus (50% of bonuses)
      bonusType = BonusType.xpBonus;
      bonusAmount = [5, 10, 15][_random.nextInt(3)];
      bonusMessage = "+$bonusAmount XP Bonus!";
    } else if (bonusRoll < 0.8) {
      // Gold bonus (30% of bonuses)
      bonusType = BonusType.goldBonus;
      bonusAmount = [5, 10, 25][_random.nextInt(3)];
      bonusMessage = "+$bonusAmount Oro encontrado!";
    } else {
      // Rare bonus (20% of bonuses)
      bonusType = BonusType.rareBonus;
      bonusAmount = [50, 100][_random.nextInt(2)];
      bonusMessage = "Cofre Legendario! +$bonusAmount XP";
    }

    _recentBonusCount++;
    _lastBonusTime = DateTime.now();

    return VariableReward(
      baseReward: baseReward,
      totalReward: baseReward + (bonusType == BonusType.xpBonus ? bonusAmount : 0),
      hasBonus: true,
      bonusType: bonusType,
      bonusAmount: bonusAmount,
      bonusMessage: bonusMessage,
      bonusAnimation: _getBonusAnimation(bonusType),
    );
  }

  String _getBonusAnimation(BonusType type) {
    switch (type) {
      case BonusType.xpBonus:
        return 'sparkle';
      case BonusType.goldBonus:
        return 'coin_shower';
      case BonusType.rareBonus:
        return 'chest_open';
    }
  }

  // =========================================================================
  // LOSS AVERSION
  // =========================================================================

  /// Get loss aversion triggers - things user might lose
  List<LossAversionTrigger> getLossAversionTriggers({
    required int currentStreak,
    required int hearts,
    required int? leaguePosition,
    required DateTime? lastActivity,
  }) {
    final triggers = <LossAversionTrigger>[];

    // Streak at risk
    if (currentStreak >= 3) {
      final hoursUntilReset = _hoursUntilStreakReset();
      if (hoursUntilReset <= 8) {
        triggers.add(LossAversionTrigger(
          type: 'streak_risk',
          severity: hoursUntilReset <= 2 ? 'high' : 'medium',
          value: currentStreak,
          message: "Tu racha de $currentStreak dias se pierde en ${hoursUntilReset}h!",
          action: "Completa 1 leccion para protegerla",
          icon: Icons.local_fire_department,
          color: Colors.orange,
        ));
      }
    }

    // Low hearts
    if (hearts <= 1) {
      triggers.add(LossAversionTrigger(
        type: 'low_hearts',
        severity: 'medium',
        value: hearts,
        message: "Solo te queda $hearts corazon!",
        action: "Espera 30min o mira un anuncio",
        icon: Icons.favorite,
        color: Colors.red,
      ));
    }

    // League demotion risk
    if (leaguePosition != null && leaguePosition > 40) {
      triggers.add(LossAversionTrigger(
        type: 'demotion_risk',
        severity: leaguePosition > 45 ? 'high' : 'medium',
        value: leaguePosition,
        message: "Posicion #$leaguePosition - Riesgo de descenso!",
        action: "Gana XP para subir en la liga",
        icon: Icons.trending_down,
        color: Colors.red,
      ));
    }

    // Inactivity warning
    if (lastActivity != null) {
      final daysInactive = DateTime.now().difference(lastActivity).inDays;
      if (daysInactive >= 2) {
        triggers.add(LossAversionTrigger(
          type: 'inactivity',
          severity: 'low',
          value: daysInactive,
          message: "Llevas $daysInactive dias sin entrenar",
          action: "Tus habilidades se debilitan!",
          icon: Icons.access_time,
          color: Colors.grey,
        ));
      }
    }

    return triggers;
  }

  int _hoursUntilStreakReset() {
    final now = DateTime.now();
    final resetHour = 4; // 4 AM reset

    DateTime resetTime;
    if (now.hour >= resetHour) {
      // Reset is tomorrow
      resetTime = DateTime(now.year, now.month, now.day + 1, resetHour);
    } else {
      // Reset is today
      resetTime = DateTime(now.year, now.month, now.day, resetHour);
    }

    return resetTime.difference(now).inHours;
  }

  // =========================================================================
  // PROGRESS ILLUSION
  // =========================================================================

  /// Get optimized progress data with psychological enhancements
  OptimizedProgress getOptimizedProgress({
    required int totalXp,
    required int currentLevel,
    required int nextLevelXp,
    required int achievements,
    required int totalAchievements,
    required double avgMastery,
  }) {
    // Calculate level progress with psychological boost
    // Show at least 10% progress even if just started
    final levelProgressRaw = (totalXp % nextLevelXp) / nextLevelXp;
    final levelProgress = max(0.10, levelProgressRaw);

    // Achievement progress
    final achievementProgress = achievements / max(totalAchievements, 1);

    // Mastery with optimistic framing (show at least 15%)
    final masteryDisplay = max(avgMastery, 0.15);

    return OptimizedProgress(
      levelProgress: LevelProgress(
        currentLevel: currentLevel,
        xpInLevel: totalXp % nextLevelXp,
        xpNeeded: nextLevelXp,
        progressPercent: levelProgress * 100,
        displayPercent: levelProgress * 100,
        toNextLevel: nextLevelXp - (totalXp % nextLevelXp),
        message: _getLevelMessage(levelProgress),
      ),
      achievementsProgress: AchievementsProgress(
        earned: achievements,
        total: totalAchievements,
        progressPercent: achievementProgress * 100,
        nextAchievementHint: "Completa 5 lecciones mas para el siguiente logro!",
      ),
      masteryProgress: MasteryProgress(
        average: masteryDisplay * 100,
        displayMessage: _getMasteryMessage(masteryDisplay),
      ),
    );
  }

  String _getLevelMessage(double progress) {
    if (progress >= 0.9) return "Casi ahi! Un poco mas!";
    if (progress >= 0.7) return "Excelente progreso!";
    if (progress >= 0.5) return "Medio camino recorrido!";
    return "Buen comienzo!";
  }

  String _getMasteryMessage(double mastery) {
    if (mastery >= 0.8) return "Nivel Maestro";
    if (mastery >= 0.6) return "Nivel Avanzado";
    if (mastery >= 0.4) return "Nivel Intermedio";
    return "En progreso";
  }

  // =========================================================================
  // ENDOWED PROGRESS
  // =========================================================================

  /// Get endowed progress - start user with something already earned
  List<EndowedProgressItem> getEndowedProgress({
    required DateTime createdAt,
    required int totalXp,
    required int currentStreak,
  }) {
    final endowments = <EndowedProgressItem>[];
    final daysSinceSignup = DateTime.now().difference(createdAt).inDays;

    // New user bonus - "Welcome package"
    if (daysSinceSignup <= 7 && totalXp < 500) {
      endowments.add(EndowedProgressItem(
        type: 'welcome_bonus',
        title: 'Pack de Bienvenida',
        description: 'Ya tienes ventaja! Completaste el primer paso.',
        value: '3 corazones extra',
        visual: 'gift_box',
        icon: Icons.card_giftcard,
        color: Colors.purple,
      ));
    }

    // Show progress as already started
    if (daysSinceSignup <= 14) {
      endowments.add(EndowedProgressItem(
        type: 'progress_started',
        title: 'Tu Viaje Comenzo',
        description: 'Ya recorriste el 10% del camino hacia Rango S',
        value: '10% completado',
        visual: 'progress_bar_started',
        icon: Icons.rocket_launch,
        color: Colors.blue,
      ));
    }

    // Streak protection endowment
    if (currentStreak >= 1) {
      endowments.add(EndowedProgressItem(
        type: 'streak_protection',
        title: 'Racha Protegida',
        description: 'Tu racha de $currentStreak dias es un tesoro. No la pierdas!',
        value: '$currentStreak dias',
        visual: 'shield_glow',
        icon: Icons.shield,
        color: Colors.orange,
      ));
    }

    return endowments;
  }

  // =========================================================================
  // SOCIAL PROOF MESSAGES
  // =========================================================================

  /// Generate social proof messages
  List<String> getSocialProofMessages({
    required int percentile,
    required int usersAhead,
    required int streak,
  }) {
    final messages = <String>[];

    if (percentile >= 80) {
      messages.add("Estas en el top ${100 - percentile}% de Cazadores!");
    } else if (percentile >= 50) {
      messages.add("Solo $usersAhead Cazadores te superan");
    }

    if (streak >= 7) {
      messages.add("Tu racha de $streak dias supera al 90% de usuarios");
    } else if (streak >= 3) {
      messages.add("Tu racha te pone entre los mas constantes");
    }

    if (messages.isEmpty) {
      messages.add("Muchos Cazadores estan entrenando ahora!");
    }

    return messages;
  }
}


// ============================================
// DATA CLASSES
// ============================================

enum BonusType { xpBonus, goldBonus, rareBonus }

class VariableReward {
  final int baseReward;
  final int totalReward;
  final bool hasBonus;
  final BonusType? bonusType;
  final int? bonusAmount;
  final String? bonusMessage;
  final String? bonusAnimation;

  const VariableReward({
    required this.baseReward,
    required this.totalReward,
    required this.hasBonus,
    this.bonusType,
    this.bonusAmount,
    this.bonusMessage,
    this.bonusAnimation,
  });
}

class LossAversionTrigger {
  final String type;
  final String severity;
  final int value;
  final String message;
  final String action;
  final IconData icon;
  final Color color;

  const LossAversionTrigger({
    required this.type,
    required this.severity,
    required this.value,
    required this.message,
    required this.action,
    required this.icon,
    required this.color,
  });

  bool get isUrgent => severity == 'high';
}

class OptimizedProgress {
  final LevelProgress levelProgress;
  final AchievementsProgress achievementsProgress;
  final MasteryProgress masteryProgress;

  const OptimizedProgress({
    required this.levelProgress,
    required this.achievementsProgress,
    required this.masteryProgress,
  });
}

class LevelProgress {
  final int currentLevel;
  final int xpInLevel;
  final int xpNeeded;
  final double progressPercent;
  final double displayPercent;
  final int toNextLevel;
  final String message;

  const LevelProgress({
    required this.currentLevel,
    required this.xpInLevel,
    required this.xpNeeded,
    required this.progressPercent,
    required this.displayPercent,
    required this.toNextLevel,
    required this.message,
  });
}

class AchievementsProgress {
  final int earned;
  final int total;
  final double progressPercent;
  final String nextAchievementHint;

  const AchievementsProgress({
    required this.earned,
    required this.total,
    required this.progressPercent,
    required this.nextAchievementHint,
  });
}

class MasteryProgress {
  final double average;
  final String displayMessage;

  const MasteryProgress({
    required this.average,
    required this.displayMessage,
  });
}

class EndowedProgressItem {
  final String type;
  final String title;
  final String description;
  final String value;
  final String visual;
  final IconData icon;
  final Color color;

  const EndowedProgressItem({
    required this.type,
    required this.title,
    required this.description,
    required this.value,
    required this.visual,
    required this.icon,
    required this.color,
  });
}
