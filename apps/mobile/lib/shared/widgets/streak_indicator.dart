import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/config/app_theme.dart';
import '../providers/streak_provider.dart';

class StreakIndicator extends ConsumerWidget {
  const StreakIndicator({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final streakState = ref.watch(streakProvider);

    return streakState.when(
      data: (streak) => _buildIndicator(context, streak),
      loading: () => _buildSkeleton(),
      error: (_, __) => _buildIndicator(context, StreakState.empty()),
    );
  }

  Widget _buildIndicator(BuildContext context, StreakState streak) {
    final isAtRisk = streak.isAtRisk;
    final hasStreak = streak.current > 0;

    return GestureDetector(
      onTap: () => _showStreakDialog(context, streak),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
        decoration: BoxDecoration(
          color: isAtRisk
              ? AppTheme.warningOrange.withOpacity(0.2)
              : AppTheme.bgCard,
          borderRadius: BorderRadius.circular(20),
          border: isAtRisk
              ? Border.all(color: AppTheme.warningOrange, width: 1)
              : null,
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            // Icono de fuego
            Icon(
              hasStreak ? Icons.local_fire_department : Icons.local_fire_department_outlined,
              color: hasStreak ? AppTheme.warningOrange : AppTheme.textMuted,
              size: 20,
            ),
            const SizedBox(width: 4),
            // Contador
            Text(
              '${streak.current}',
              style: TextStyle(
                color: hasStreak ? AppTheme.warningOrange : AppTheme.textMuted,
                fontWeight: FontWeight.bold,
                fontSize: 14,
              ),
            ),
            // Multiplicador
            if (streak.multiplier > 1.0) ...[
              const SizedBox(width: 4),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 1),
                decoration: BoxDecoration(
                  color: AppTheme.warningOrange,
                  borderRadius: BorderRadius.circular(4),
                ),
                child: Text(
                  '${streak.multiplier}x',
                  style: const TextStyle(
                    color: Colors.white,
                    fontSize: 10,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
            ],
            // Indicador de peligro
            if (isAtRisk) ...[
              const SizedBox(width: 4),
              const Icon(
                Icons.warning_amber_rounded,
                color: AppTheme.warningOrange,
                size: 14,
              ),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildSkeleton() {
    return Container(
      width: 50,
      height: 28,
      decoration: BoxDecoration(
        color: AppTheme.bgCard,
        borderRadius: BorderRadius.circular(20),
      ),
    );
  }

  void _showStreakDialog(BuildContext context, StreakState streak) {
    showModalBottomSheet(
      context: context,
      backgroundColor: AppTheme.bgCard,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (context) => StreakDetailSheet(streak: streak),
    );
  }
}

class StreakDetailSheet extends ConsumerWidget {
  final StreakState streak;

  const StreakDetailSheet({super.key, required this.streak});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return Padding(
      padding: const EdgeInsets.all(24),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          // Handle
          Container(
            width: 40,
            height: 4,
            decoration: BoxDecoration(
              color: AppTheme.textMuted,
              borderRadius: BorderRadius.circular(2),
            ),
          ),
          const SizedBox(height: 24),

          // Icono grande de fuego
          Icon(
            Icons.local_fire_department,
            color: streak.current > 0 ? AppTheme.warningOrange : AppTheme.textMuted,
            size: 64,
          ),
          const SizedBox(height: 16),

          // Contador de racha
          Text(
            '${streak.current} días',
            style: const TextStyle(
              fontSize: 32,
              fontWeight: FontWeight.bold,
            ),
          ),

          // Mejor racha
          Text(
            'Mejor racha: ${streak.longest} días',
            style: const TextStyle(color: AppTheme.textSecondary),
          ),

          const SizedBox(height: 16),

          // Multiplicador actual
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: AppTheme.bgElevated,
              borderRadius: BorderRadius.circular(12),
            ),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                const Icon(Icons.trending_up, color: AppTheme.successGreen),
                const SizedBox(width: 8),
                Text(
                  'Multiplicador de XP: ${streak.multiplier}x',
                  style: const TextStyle(fontWeight: FontWeight.bold),
                ),
              ],
            ),
          ),

          const SizedBox(height: 16),

          // Progreso hacia siguiente multiplicador
          _buildMultiplierProgress(streak),

          const SizedBox(height: 24),

          // Streak Freeze
          if (streak.freezesAvailable > 0)
            _buildFreezeInfo(streak)
          else
            _buildBuyFreezeOption(context, ref),

          // Advertencia si está en riesgo
          if (streak.isAtRisk) ...[
            const SizedBox(height: 16),
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: AppTheme.warningOrange.withOpacity(0.2),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: AppTheme.warningOrange),
              ),
              child: Row(
                children: [
                  const Icon(Icons.warning_amber_rounded, color: AppTheme.warningOrange),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text(
                          '¡Tu racha está en peligro!',
                          style: TextStyle(fontWeight: FontWeight.bold),
                        ),
                        Text(
                          'Completa una lección antes de las 4:00 AM',
                          style: TextStyle(
                            color: AppTheme.textSecondary,
                            fontSize: 12,
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ],

          // Opción de reparar si se perdió recientemente
          if (streak.canRepair) ...[
            const SizedBox(height: 16),
            _buildRepairOption(context, ref, streak),
          ],

          const SizedBox(height: 24),
        ],
      ),
    );
  }

  Widget _buildMultiplierProgress(StreakState streak) {
    // Determinar próximo milestone
    int nextMilestone;
    if (streak.current < 7) {
      nextMilestone = 7;
    } else if (streak.current < 14) {
      nextMilestone = 14;
    } else if (streak.current < 30) {
      nextMilestone = 30;
    } else {
      // Ya tiene máximo multiplicador
      return const SizedBox.shrink();
    }

    final progress = streak.current / nextMilestone;

    return Column(
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text('Próximo multiplicador en $nextMilestone días'),
            Text('${streak.current}/$nextMilestone'),
          ],
        ),
        const SizedBox(height: 8),
        LinearProgressIndicator(
          value: progress,
          backgroundColor: AppTheme.bgElevated,
          valueColor: const AlwaysStoppedAnimation(AppTheme.warningOrange),
          borderRadius: BorderRadius.circular(4),
        ),
      ],
    );
  }

  Widget _buildFreezeInfo(StreakState streak) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: AppTheme.accentCyan.withOpacity(0.2),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Row(
        children: [
          const Icon(Icons.ac_unit, color: AppTheme.accentCyan),
          const SizedBox(width: 12),
          Text(
            '${streak.freezesAvailable} Streak Freeze disponible(s)',
            style: const TextStyle(fontWeight: FontWeight.bold),
          ),
        ],
      ),
    );
  }

  Widget _buildBuyFreezeOption(BuildContext context, WidgetRef ref) {
    return InkWell(
      onTap: () {
        Navigator.pop(context);
        // Navigate to shop
        // Using GoRouter if available, otherwise direct navigation
        Navigator.of(context).pushNamed('/shop');
      },
      borderRadius: BorderRadius.circular(12),
      child: Container(
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          border: Border.all(color: AppTheme.textMuted),
          borderRadius: BorderRadius.circular(12),
        ),
        child: Row(
          children: [
            const Icon(Icons.ac_unit, color: AppTheme.textMuted),
            const SizedBox(width: 12),
            const Expanded(
              child: Text('Comprar Streak Freeze'),
            ),
            const Icon(Icons.monetization_on, color: AppTheme.secondaryGold, size: 16),
            const SizedBox(width: 4),
            const Text('200', style: TextStyle(color: AppTheme.secondaryGold)),
            const Icon(Icons.chevron_right, color: AppTheme.textMuted),
          ],
        ),
      ),
    );
  }

  Widget _buildRepairOption(BuildContext context, WidgetRef ref, StreakState streak) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppTheme.primaryPurple.withOpacity(0.2),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppTheme.primaryPurple),
      ),
      child: Column(
        children: [
          Text(
            '¡Puedes recuperar tu racha de ${streak.previousStreak} días!',
            style: const TextStyle(fontWeight: FontWeight.bold),
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 8),
          Text(
            'Tienes ${_formatTime(streak.repairWindowRemaining!)} para repararla',
            style: const TextStyle(color: AppTheme.textSecondary, fontSize: 12),
          ),
          const SizedBox(height: 16),
          Row(
            children: [
              // Reparar con oro
              Expanded(
                child: ElevatedButton.icon(
                  onPressed: () => _repairWithGold(context, ref),
                  icon: const Icon(Icons.monetization_on, size: 16),
                  label: const Text('300 Oro'),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: AppTheme.secondaryGold,
                    foregroundColor: Colors.black,
                  ),
                ),
              ),
              const SizedBox(width: 12),
              // Reparar con ad
              Expanded(
                child: OutlinedButton.icon(
                  onPressed: () => _repairWithAd(context, ref),
                  icon: const Icon(Icons.play_circle_outline, size: 16),
                  label: const Text('Ver Ad'),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  String _formatTime(Duration duration) {
    final hours = duration.inHours;
    final minutes = duration.inMinutes % 60;
    if (hours > 0) return '${hours}h ${minutes}m';
    return '${minutes}m';
  }

  Future<void> _repairWithGold(BuildContext context, WidgetRef ref) async {
    Navigator.pop(context);

    // Call API to repair with gold
    final success = await ref.read(streakProvider.notifier).repairWithGold();

    if (context.mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(success ? '¡Racha recuperada!' : 'Oro insuficiente o error'),
          backgroundColor: success ? AppTheme.successGreen : AppTheme.dangerRed,
        ),
      );
    }
  }

  Future<void> _repairWithAd(BuildContext context, WidgetRef ref) async {
    Navigator.pop(context);

    // Show loading indicator
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('Cargando anuncio...'), duration: Duration(seconds: 1)),
    );

    // Call API to repair with ad
    final success = await ref.read(streakProvider.notifier).repairWithAd();

    if (context.mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(success ? '¡Racha recuperada!' : 'Error al recuperar racha'),
          backgroundColor: success ? AppTheme.successGreen : AppTheme.dangerRed,
        ),
      );
    }
  }
}
