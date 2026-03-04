import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_animate/flutter_animate.dart';

import '../../core/providers/streak_provider.dart';

/// Widget que muestra la racha actual del usuario
class StreakWidget extends ConsumerWidget {
  final bool compact;

  const StreakWidget({
    super.key,
    this.compact = false,
  });

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final streak = ref.watch(currentStreakProvider);
    final multiplier = ref.watch(streakMultiplierProvider);
    final atRisk = ref.watch(streakAtRiskProvider);

    if (compact) {
      return _buildCompact(streak, atRisk);
    }

    return _buildFull(streak, multiplier, atRisk);
  }

  Widget _buildCompact(int streak, bool atRisk) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
      decoration: BoxDecoration(
        color: atRisk
            ? Colors.orange.withOpacity(0.2)
            : Colors.amber.withOpacity(0.2),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(
          color: atRisk ? Colors.orange : Colors.amber,
          width: 1,
        ),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(
            Icons.local_fire_department,
            color: atRisk ? Colors.orange : Colors.amber,
            size: 18,
          ),
          const SizedBox(width: 4),
          Text(
            '$streak',
            style: TextStyle(
              color: atRisk ? Colors.orange : Colors.amber,
              fontSize: 14,
              fontWeight: FontWeight.bold,
            ),
          ),
          if (atRisk) ...[
            const SizedBox(width: 4),
            const Icon(
              Icons.warning_amber,
              color: Colors.orange,
              size: 14,
            ).animate(onPlay: (c) => c.repeat()).shake(duration: 1.seconds),
          ],
        ],
      ),
    );
  }

  Widget _buildFull(int streak, double multiplier, bool atRisk) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: atRisk
              ? [Colors.orange.withOpacity(0.2), Colors.red.withOpacity(0.1)]
              : [Colors.amber.withOpacity(0.2), Colors.orange.withOpacity(0.1)],
        ),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: atRisk ? Colors.orange : Colors.amber,
          width: 2,
        ),
      ),
      child: Column(
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(
                Icons.local_fire_department,
                color: atRisk ? Colors.orange : Colors.amber,
                size: 32,
              ).animate(
                onPlay: (c) => c.repeat(),
              ).shimmer(duration: 2.seconds, color: Colors.white.withOpacity(0.3)),
              const SizedBox(width: 8),
              Text(
                '$streak',
                style: TextStyle(
                  color: Colors.white,
                  fontSize: 36,
                  fontWeight: FontWeight.bold,
                ),
              ),
              const SizedBox(width: 8),
              Text(
                'DIAS',
                style: TextStyle(
                  color: Colors.white70,
                  fontSize: 14,
                  fontWeight: FontWeight.w500,
                ),
              ),
            ],
          ),
          if (multiplier > 1.0) ...[
            const SizedBox(height: 8),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
              decoration: BoxDecoration(
                color: Colors.green.withOpacity(0.3),
                borderRadius: BorderRadius.circular(12),
              ),
              child: Text(
                '+${((multiplier - 1) * 100).toInt()}% XP Bonus',
                style: const TextStyle(
                  color: Colors.green,
                  fontSize: 12,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ),
          ],
          if (atRisk) ...[
            const SizedBox(height: 8),
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                const Icon(
                  Icons.warning_amber,
                  color: Colors.orange,
                  size: 16,
                ),
                const SizedBox(width: 4),
                const Text(
                  'Practica hoy para mantener tu racha!',
                  style: TextStyle(
                    color: Colors.orange,
                    fontSize: 12,
                  ),
                ),
              ],
            ).animate(onPlay: (c) => c.repeat()).fade(
              begin: 0.7,
              end: 1.0,
              duration: 800.ms,
            ),
          ],
        ],
      ),
    );
  }
}
