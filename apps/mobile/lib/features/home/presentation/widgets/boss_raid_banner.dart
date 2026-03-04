import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../../core/config/app_theme.dart';
import '../../../practice/presentation/providers/boss_raid_provider.dart';

class BossRaidBanner extends ConsumerWidget {
  const BossRaidBanner({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final bossState = ref.watch(bossRaidProvider);
    final status = bossState.status;

    if (status == null || !status.isActive) {
      return const SizedBox.shrink();
    }

    // Use real time from API
    final String timeRemaining = status.formattedTimeRemaining;

    return Card(
      elevation: 4,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
        side: const BorderSide(color: AppTheme.primaryPurple, width: 1),
      ),
      child: InkWell(
        onTap: () {
          // Navigate to the boss raid screen
           context.go('/boss-raid');
        },
        borderRadius: BorderRadius.circular(16),
        child: Container(
          padding: const EdgeInsets.all(16.0),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(16),
            gradient: LinearGradient(
              colors: [
                AppTheme.primaryPurple.withOpacity(0.5),
                AppTheme.bgCard,
              ],
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
            ),
          ),
          child: Row(
            children: [
              const Icon(Icons.whatshot_rounded, color: AppTheme.dangerRed, size: 40),
              const SizedBox(width: 16),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      '¡Jefe de Incursión Activo!',
                      style: Theme.of(context).textTheme.titleLarge?.copyWith(
                            color: AppTheme.textPrimary,
                          ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      '¡Derrota a "${status.bossName}" con otros estudiantes!',
                      style: Theme.of(context).textTheme.bodyMedium,
                    ),
                    const SizedBox(height: 8),
                     Row(
                       children: [
                         const Icon(Icons.timer_outlined, size: 14, color: AppTheme.textSecondary),
                         const SizedBox(width: 4),
                         Text(
                           '$timeRemaining restantes',
                           style: const TextStyle(
                            color: AppTheme.textSecondary,
                            fontSize: 12,
                           ),
                         ),
                       ],
                     ),
                  ],
                ),
              ),
              const Icon(Icons.arrow_forward_ios, color: AppTheme.textSecondary),
            ],
          ),
        ),
      ),
    );
  }
}

