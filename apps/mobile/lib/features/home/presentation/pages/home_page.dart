import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/config/routes.dart';
import '../../../engagement/presentation/providers/engagement_provider.dart';
import '../../../auth/presentation/providers/auth_provider.dart';
import '../../../../shared/widgets/hearts_display.dart';
import '../../../../shared/widgets/streak_flame.dart';
import '../../../../shared/widgets/streak_lost_modal.dart';
import '../../../../core/constants/app_strings.dart';
import '../../../../core/services/psychological_triggers_provider.dart';
import '../../../../shared/widgets/psychological/loss_aversion_alerts.dart';

import '../widgets/daily_goal_card.dart';
import '../widgets/continue_studying_card.dart';
import '../widgets/boss_raid_banner.dart';
import '../widgets/quick_actions.dart';
import '../widgets/weekly_stats.dart';
import '../../../../shared/widgets/offline_banner.dart';


class HomePage extends ConsumerWidget {
  const HomePage({super.key});

  /// Handle trigger action based on type
  void _handleTriggerAction(BuildContext context, WidgetRef ref, dynamic trigger) {
    switch (trigger.type) {
      case 'streak_risk':
        // Navigate to practice to save streak
        context.push(AppRoutes.practice);
        break;
      case 'low_hearts':
        // Show hearts modal or navigate to shop
        context.push(AppRoutes.store);
        break;
      case 'demotion_risk':
        // Navigate to leaderboard
        context.push(AppRoutes.leagues);
        break;
      case 'inactivity':
        // Navigate to practice
        context.push(AppRoutes.practice);
        break;
    }
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final user = ref.watch(authProvider).user;
    final engagement = ref.watch(engagementProvider);
    final lossAversionTriggers = ref.watch(lossAversionTriggersProvider);
    final socialProof = ref.watch(socialProofProvider);
    final endowedProgress = ref.watch(endowedProgressProvider);

    ref.listen<EngagementState>(engagementProvider, (previous, next) {
      if (next.streakJustLost && (previous?.streakJustLost == false || previous == null)) {
        showModalBottomSheet(
          context: context,
          isScrollControlled: true,
          backgroundColor: Colors.transparent,
          builder: (modalContext) => StreakLostModal(
            lostStreak: next.previousStreak,
            onRepair: () {
              Navigator.pop(modalContext);
              ref.read(engagementProvider.notifier).repairStreakWithGold();
            },
            onRepairWithAd: () {
              Navigator.pop(modalContext);
              ref.read(engagementProvider.notifier).repairStreakWithAd();
            },
            onRestart: () {
              Navigator.pop(modalContext);
              ref.read(engagementProvider.notifier).dismissStreakLost();
            },
          ),
        );
      }
    });

    return Scaffold(
      appBar: AppBar(
        title: const Text(AppStrings.appName),
        actions: [
          Padding(
            padding: const EdgeInsets.only(right: 8.0),
            child: Row(
              children: [
                const HeartsDisplay(),
                const SizedBox(width: 8),
                StreakFlame(count: engagement.streak),
              ],
            ),
          ),
        ],
      ),
      body: Column(
        children: [
          const OfflineBanner(),
          Expanded(
            child: RefreshIndicator(
              onRefresh: () async {
                // Refresh all home page data in parallel
                await Future.wait([
                  ref.read(engagementProvider.notifier).fetchXp(),
                  ref.read(engagementProvider.notifier).checkStreakStatus(),
                  ref.read(authProvider.notifier).refreshUser(),
                ]);
              },
              child: SingleChildScrollView(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('${AppStrings.welcomeBack}, ${user?.name ?? "Cazador"}',
                      style: Theme.of(context).textTheme.headlineMedium),
                    const SizedBox(height: 8),
                    Text(AppStrings.readyToLevelUp,
                      style: Theme.of(context).textTheme.bodyLarge),
                    const SizedBox(height: 16),

                    // Loss Aversion Alerts (urgent first)
                    if (lossAversionTriggers.isNotEmpty) ...[
                      LossAversionAlerts(
                        triggers: lossAversionTriggers,
                        compact: lossAversionTriggers.length > 2,
                        onTriggerTap: (trigger) {
                          _handleTriggerAction(context, ref, trigger);
                        },
                      ),
                      const SizedBox(height: 16),
                    ],

                    // Social Proof Banner
                    if (socialProof.messages.isNotEmpty) ...[
                      SocialProofBanner(
                        messages: socialProof.messages,
                        percentile: socialProof.percentile,
                        leagueRank: socialProof.leagueRank,
                      ),
                      const SizedBox(height: 16),
                    ],

                    // Endowed Progress (for new users)
                    if (endowedProgress.isNotEmpty) ...[
                      EndowedProgressDisplay(
                        endowments: endowedProgress,
                      ),
                      const SizedBox(height: 16),
                    ],

                    // Daily Goal Card
                    const DailyGoalCard(),
                    const SizedBox(height: 16),
                    const ContinueStudyingCard(),
                    const SizedBox(height: 16),
                  const BossRaidBanner(),
                    const SizedBox(height: 16),
                    // Conquest Mode Entry
                    GestureDetector(
                      onTap: () => context.push(AppRoutes.dungeonMap),
                      child: Container(
                        padding: const EdgeInsets.all(16),
                        decoration: BoxDecoration(
                          gradient: LinearGradient(
                            colors: [Color(0xFF6A1B9A), Color(0xFF4A148C)], // Purple gradient
                            begin: Alignment.topLeft,
                            end: Alignment.bottomRight,
                          ),
                          borderRadius: BorderRadius.circular(16),
                          boxShadow: [
                            BoxShadow(
                              color: Color(0xFF6A1B9A).withOpacity(0.4),
                              blurRadius: 10,
                              offset: Offset(0, 4),
                            ),
                          ],
                        ),
                        child: Row(
                          children: [
                            Container(
                              padding: const EdgeInsets.all(12),
                              decoration: BoxDecoration(
                                color: Colors.white.withOpacity(0.1),
                                shape: BoxShape.circle,
                              ),
                              child: const Icon(Icons.castle, color: Colors.amber, size: 28),
                            ),
                            const SizedBox(width: 16),
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  const Text(
                                    'MODO CONQUISTA',
                                    style: TextStyle(
                                      color: Colors.amber,
                                      fontSize: 12,
                                      fontWeight: FontWeight.bold,
                                      letterSpacing: 1,
                                    ),
                                  ),
                                  const SizedBox(height: 4),
                                  const Text(
                                    'Conquista territorios y aprende',
                                    style: TextStyle(
                                      color: Colors.white,
                                      fontSize: 16,
                                      fontWeight: FontWeight.bold,
                                    ),
                                  ),
                                ],
                              ),
                            ),
                            const Icon(Icons.arrow_forward_ios, color: Colors.white70),
                          ],
                        ),
                      ),
                    ),
                    const SizedBox(height: 24),
                    const QuickActions(),
                    const SizedBox(height: 24),
                    const WeeklyStats(),
                  ],
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}
