import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/config/app_theme.dart';
import '../../../engagement/presentation/providers/engagement_provider.dart';

class DailyGoalCard extends ConsumerWidget {
  const DailyGoalCard({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final engagementState = ref.watch(engagementProvider);
    final int xpGoal = 100; // Default daily goal
    final int currentXp = engagementState.totalXp;
    final double progress = (currentXp / xpGoal).clamp(0.0, 1.0);

    return Card(
      elevation: 2,
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Meta Diaria',
              style: Theme.of(context).textTheme.titleLarge,
            ),
            const SizedBox(height: 8),
            Text(
              progress >= 1.0
                  ? '¡Meta completada! ¡Excelente trabajo!'
                  : 'Gana ${xpGoal - currentXp} XP más para completar tu meta y mantener tu racha.',
              style: Theme.of(context).textTheme.bodyMedium,
            ),
            const SizedBox(height: 16),
            Row(
              children: [
                Expanded(
                  child: ClipRRect(
                    borderRadius: BorderRadius.circular(8),
                    child: LinearProgressIndicator(
                      value: progress,
                      minHeight: 12,
                      backgroundColor: AppTheme.bgElevated,
                      valueColor: const AlwaysStoppedAnimation<Color>(AppTheme.accentCyan),
                    ),
                  ),
                ),
                const SizedBox(width: 16),
                Text(
                  '${(progress * 100).toInt()}%',
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                        color: AppTheme.accentCyan,
                        fontWeight: FontWeight.bold,
                      ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

