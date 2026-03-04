import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../features/auth/presentation/providers/auth_provider.dart';
import '../../features/engagement/presentation/providers/engagement_provider.dart';
import '../../shared/providers/balance_provider.dart';
import './psychological_triggers_service.dart';

/// Provider for psychological triggers service
final psychologicalTriggersServiceProvider = Provider<PsychologicalTriggersService>((ref) {
  return PsychologicalTriggersService();
});

/// Provider for loss aversion triggers
final lossAversionTriggersProvider = Provider<List<LossAversionTrigger>>((ref) {
  final service = ref.watch(psychologicalTriggersServiceProvider);
  final engagement = ref.watch(engagementProvider);
  final user = ref.watch(authProvider).user;

  return service.getLossAversionTriggers(
    currentStreak: engagement.streak,
    hearts: engagement.hearts,
    leaguePosition: engagement.leaguePosition,
    lastActivity: user?.lastActivityAt,
  );
});

/// Provider for social proof messages
final socialProofProvider = Provider<SocialProofData>((ref) {
  final service = ref.watch(psychologicalTriggersServiceProvider);
  final engagement = ref.watch(engagementProvider);

  final messages = service.getSocialProofMessages(
    percentile: engagement.percentile,
    usersAhead: engagement.usersAhead,
    streak: engagement.streak,
  );

  return SocialProofData(
    messages: messages,
    percentile: engagement.percentile,
    leagueRank: engagement.leagueName,
  );
});

/// Provider for optimized progress display
final optimizedProgressProvider = Provider<OptimizedProgress>((ref) {
  final service = ref.watch(psychologicalTriggersServiceProvider);
  final engagement = ref.watch(engagementProvider);

  return service.getOptimizedProgress(
    totalXp: engagement.totalXp,
    currentLevel: engagement.level,
    nextLevelXp: engagement.xpForNextLevel,
    achievements: engagement.achievementCount,
    totalAchievements: 50, // Total possible achievements
    avgMastery: engagement.averageMastery,
  );
});

/// Provider for endowed progress items
final endowedProgressProvider = Provider<List<EndowedProgressItem>>((ref) {
  final service = ref.watch(psychologicalTriggersServiceProvider);
  final user = ref.watch(authProvider).user;
  final engagement = ref.watch(engagementProvider);

  if (user == null) return [];

  return service.getEndowedProgress(
    createdAt: user.createdAt ?? DateTime.now(),
    totalXp: engagement.totalXp,
    currentStreak: engagement.streak,
  );
});

/// Variable reward state notifier
class VariableRewardNotifier extends StateNotifier<VariableReward?> {
  final PsychologicalTriggersService _service;

  VariableRewardNotifier(this._service) : super(null);

  /// Get variable reward for an action
  VariableReward getReward(String actionType, int baseReward) {
    final reward = _service.getVariableReward(
      actionType: actionType,
      baseReward: baseReward,
    );

    if (reward.hasBonus) {
      state = reward;
    }

    return reward;
  }

  /// Clear current reward
  void clearReward() {
    state = null;
  }
}

final variableRewardProvider = StateNotifierProvider<VariableRewardNotifier, VariableReward?>((ref) {
  final service = ref.watch(psychologicalTriggersServiceProvider);
  return VariableRewardNotifier(service);
});

/// Data class for social proof
class SocialProofData {
  final List<String> messages;
  final int percentile;
  final String? leagueRank;

  const SocialProofData({
    required this.messages,
    required this.percentile,
    this.leagueRank,
  });
}
