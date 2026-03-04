import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/config/app_theme.dart';
import '../../../../shared/providers/user_stats_provider.dart';
import '../../../leagues/presentation/providers/leagues_provider.dart';

class WeeklyStats extends ConsumerWidget {
  const WeeklyStats({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final leagueState = ref.watch(leaguesProvider);
    final userStatsAsync = ref.watch(userStatsProvider);

    // Find current user in the leaderboard to get XP
    final myStats = leagueState.users.firstWhere(
      (u) => u.isCurrentUser,
      orElse: () => LeagueUser(id: '', name: '', xp: 0, rank: 0, zone: '', isCurrentUser: true),
    );

    final int xpGained = myStats.xp;

    // Get real stats from user profile
    final userStats = userStatsAsync.valueOrNull;
    final int questionsAnswered = userStats?.questionsAnswered ?? 0;
    final double accuracy = userStats?.accuracy ?? 0.0;

    return Card(
      elevation: 2,
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Resumen de la Semana',
              style: Theme.of(context).textTheme.titleLarge,
            ),
            const SizedBox(height: 16),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceAround,
              children: [
                _buildStatItem(
                  context,
                  label: 'XP Ganado',
                  value: xpGained.toString(),
                  icon: Icons.star_rounded,
                  color: AppTheme.accentCyan,
                ),
                _buildStatItem(
                  context,
                  label: 'Preguntas',
                  value: questionsAnswered.toString(), // Estimated
                  icon: Icons.question_answer_rounded,
                  color: AppTheme.primaryPurple,
                ),
                _buildStatItem(
                  context,
                  label: 'Precisión',
                  value: '${(accuracy * 100).toInt()}%',
                  icon: Icons.check_circle_rounded,
                  color: AppTheme.successGreen,
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildStatItem(
    BuildContext context, {
    required String label,
    required String value,
    required IconData icon,
    required Color color,
  }) {
    return Column(
      children: [
        Icon(icon, color: color, size: 28),
        const SizedBox(height: 8),
        Text(
          value,
          style: Theme.of(context).textTheme.titleLarge?.copyWith(
                fontWeight: FontWeight.bold,
              ),
        ),
        const SizedBox(height: 4),
        Text(
          label,
          style: Theme.of(context).textTheme.bodySmall?.copyWith(
                color: AppTheme.textSecondary,
              ),
        ),
      ],
    );
  }
}
