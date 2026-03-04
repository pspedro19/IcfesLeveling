import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_animate/flutter_animate.dart';
import '../providers/shop_provider.dart';

/// Widget that displays currently active power-ups with countdown timers
class ActivePowerupsCard extends ConsumerStatefulWidget {
  const ActivePowerupsCard({super.key});

  @override
  ConsumerState<ActivePowerupsCard> createState() => _ActivePowerupsCardState();
}

class _ActivePowerupsCardState extends ConsumerState<ActivePowerupsCard> {
  Timer? _countdownTimer;

  @override
  void initState() {
    super.initState();
    // Update UI every second for countdown timers
    _countdownTimer = Timer.periodic(const Duration(seconds: 1), (_) {
      if (mounted) {
        setState(() {});
      }
    });
  }

  @override
  void dispose() {
    _countdownTimer?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final activePowerUps = ref.watch(activePowerUpsProvider);

    if (activePowerUps.isEmpty) {
      return const SizedBox.shrink();
    }

    return Container(
      margin: const EdgeInsets.only(bottom: 20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                padding: const EdgeInsets.all(6),
                decoration: BoxDecoration(
                  color: Colors.green.withOpacity(0.2),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: const Icon(
                  Icons.flash_on,
                  color: Colors.greenAccent,
                  size: 16,
                ),
              ),
              const SizedBox(width: 8),
              const Text(
                "POWER-UPS ACTIVOS",
                style: TextStyle(
                  color: Colors.greenAccent,
                  fontWeight: FontWeight.bold,
                  letterSpacing: 2,
                  fontSize: 12,
                ),
              ),
              const SizedBox(width: 8),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                decoration: BoxDecoration(
                  color: Colors.greenAccent.withOpacity(0.2),
                  borderRadius: BorderRadius.circular(10),
                ),
                child: Text(
                  '${activePowerUps.length}',
                  style: const TextStyle(
                    color: Colors.greenAccent,
                    fontWeight: FontWeight.bold,
                    fontSize: 12,
                  ),
                ),
              ),
            ],
          ).animate().fadeIn().slideX(begin: -0.1),
          const SizedBox(height: 12),
          SizedBox(
            height: 100,
            child: ListView.builder(
              scrollDirection: Axis.horizontal,
              itemCount: activePowerUps.length,
              itemBuilder: (context, index) {
                final powerUp = activePowerUps[index];
                return _ActivePowerUpTile(
                  powerUp: powerUp,
                  index: index,
                );
              },
            ),
          ),
        ],
      ),
    );
  }
}

class _ActivePowerUpTile extends StatelessWidget {
  final ActivePowerUp powerUp;
  final int index;

  const _ActivePowerUpTile({
    required this.powerUp,
    required this.index,
  });

  IconData _getIconForType(String type) {
    switch (type) {
      case 'xp_boost':
        return Icons.trending_up;
      case 'hint_token':
        return Icons.lightbulb;
      case 'streak_freeze':
        return Icons.ac_unit;
      case 'double_coins':
        return Icons.monetization_on;
      case 'shield':
        return Icons.shield;
      case 'time_freezer':
        return Icons.timer_off;
      default:
        return Icons.flash_on;
    }
  }

  Color _getColorForType(String type) {
    switch (type) {
      case 'xp_boost':
        return Colors.purpleAccent;
      case 'hint_token':
        return Colors.amber;
      case 'streak_freeze':
        return Colors.cyanAccent;
      case 'double_coins':
        return Colors.yellow;
      case 'shield':
        return Colors.blueAccent;
      case 'time_freezer':
        return Colors.tealAccent;
      default:
        return Colors.greenAccent;
    }
  }

  @override
  Widget build(BuildContext context) {
    final color = _getColorForType(powerUp.type);
    final icon = _getIconForType(powerUp.type);
    final isExpiring = powerUp.remainingTime.inMinutes < 5;

    return Container(
      width: 140,
      margin: const EdgeInsets.only(right: 12),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [
            color.withOpacity(0.15),
            color.withOpacity(0.05),
          ],
        ),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: color.withOpacity(0.3),
          width: 1.5,
        ),
        boxShadow: [
          BoxShadow(
            color: color.withOpacity(0.2),
            blurRadius: 12,
            spreadRadius: -2,
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Row(
            children: [
              Container(
                padding: const EdgeInsets.all(6),
                decoration: BoxDecoration(
                  color: color.withOpacity(0.2),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Icon(icon, color: color, size: 18),
              )
                  .animate(
                    onPlay: (controller) => controller.repeat(),
                  )
                  .shimmer(
                    duration: const Duration(seconds: 2),
                    color: color.withOpacity(0.3),
                  ),
              const SizedBox(width: 8),
              Expanded(
                child: Text(
                  powerUp.name,
                  style: TextStyle(
                    color: color,
                    fontWeight: FontWeight.bold,
                    fontSize: 11,
                  ),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
              ),
            ],
          ),
          const Spacer(),
          // Multiplier badge if applicable
          if (powerUp.multiplier > 1.0)
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
              decoration: BoxDecoration(
                color: color.withOpacity(0.2),
                borderRadius: BorderRadius.circular(6),
              ),
              child: Text(
                'x${powerUp.multiplier.toStringAsFixed(1)}',
                style: TextStyle(
                  color: color,
                  fontWeight: FontWeight.bold,
                  fontSize: 10,
                ),
              ),
            ),
          const SizedBox(height: 6),
          // Progress bar
          Stack(
            children: [
              Container(
                height: 4,
                decoration: BoxDecoration(
                  color: Colors.white.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(2),
                ),
              ),
              FractionallySizedBox(
                widthFactor: powerUp.progressPercent.clamp(0.0, 1.0),
                child: Container(
                  height: 4,
                  decoration: BoxDecoration(
                    gradient: LinearGradient(
                      colors: [color, color.withOpacity(0.6)],
                    ),
                    borderRadius: BorderRadius.circular(2),
                    boxShadow: [
                      BoxShadow(
                        color: color.withOpacity(0.5),
                        blurRadius: 4,
                      ),
                    ],
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 6),
          // Countdown timer
          Row(
            children: [
              Icon(
                Icons.timer,
                size: 12,
                color: isExpiring ? Colors.redAccent : Colors.white54,
              ),
              const SizedBox(width: 4),
              Text(
                powerUp.formattedRemainingTime,
                style: TextStyle(
                  color: isExpiring ? Colors.redAccent : Colors.white70,
                  fontSize: 11,
                  fontWeight: isExpiring ? FontWeight.bold : FontWeight.normal,
                ),
              ),
            ],
          )
              .animate(
                target: isExpiring ? 1 : 0,
              )
              .shake(
                hz: 2,
                curve: Curves.easeInOut,
              ),
        ],
      ),
    )
        .animate(delay: Duration(milliseconds: index * 100))
        .fadeIn()
        .slideX(begin: 0.2);
  }
}

/// Compact version for displaying in other parts of the app
class ActivePowerUpsBadge extends ConsumerWidget {
  const ActivePowerUpsBadge({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final activePowerUps = ref.watch(activePowerUpsProvider);

    if (activePowerUps.isEmpty) {
      return const SizedBox.shrink();
    }

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: Colors.greenAccent.withOpacity(0.1),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Colors.greenAccent.withOpacity(0.3)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          const Icon(
            Icons.flash_on,
            color: Colors.greenAccent,
            size: 14,
          ),
          const SizedBox(width: 4),
          Text(
            '${activePowerUps.length}',
            style: const TextStyle(
              color: Colors.greenAccent,
              fontWeight: FontWeight.bold,
              fontSize: 12,
            ),
          ),
        ],
      ),
    )
        .animate(onPlay: (c) => c.repeat(reverse: true))
        .shimmer(duration: const Duration(seconds: 2));
  }
}

/// Mini indicator showing active power-up icons
class ActivePowerUpsIndicator extends ConsumerWidget {
  final int maxVisible;

  const ActivePowerUpsIndicator({
    super.key,
    this.maxVisible = 3,
  });

  IconData _getIconForType(String type) {
    switch (type) {
      case 'xp_boost':
        return Icons.trending_up;
      case 'hint_token':
        return Icons.lightbulb;
      case 'streak_freeze':
        return Icons.ac_unit;
      case 'double_coins':
        return Icons.monetization_on;
      case 'shield':
        return Icons.shield;
      case 'time_freezer':
        return Icons.timer_off;
      default:
        return Icons.flash_on;
    }
  }

  Color _getColorForType(String type) {
    switch (type) {
      case 'xp_boost':
        return Colors.purpleAccent;
      case 'hint_token':
        return Colors.amber;
      case 'streak_freeze':
        return Colors.cyanAccent;
      case 'double_coins':
        return Colors.yellow;
      case 'shield':
        return Colors.blueAccent;
      case 'time_freezer':
        return Colors.tealAccent;
      default:
        return Colors.greenAccent;
    }
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final activePowerUps = ref.watch(activePowerUpsProvider);

    if (activePowerUps.isEmpty) {
      return const SizedBox.shrink();
    }

    final visiblePowerUps = activePowerUps.take(maxVisible).toList();
    final remainingCount = activePowerUps.length - visiblePowerUps.length;

    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        ...visiblePowerUps.asMap().entries.map((entry) {
          final powerUp = entry.value;
          final color = _getColorForType(powerUp.type);
          final icon = _getIconForType(powerUp.type);

          return Container(
            margin: EdgeInsets.only(left: entry.key > 0 ? -8 : 0),
            padding: const EdgeInsets.all(4),
            decoration: BoxDecoration(
              color: color.withOpacity(0.2),
              borderRadius: BorderRadius.circular(6),
              border: Border.all(color: color.withOpacity(0.5)),
            ),
            child: Icon(icon, color: color, size: 12),
          )
              .animate(
                onPlay: (controller) => controller.repeat(reverse: true),
              )
              .scale(
                begin: const Offset(1.0, 1.0),
                end: const Offset(1.1, 1.1),
                duration: const Duration(seconds: 1),
              );
        }),
        if (remainingCount > 0)
          Container(
            margin: const EdgeInsets.only(left: -8),
            padding: const EdgeInsets.all(4),
            decoration: BoxDecoration(
              color: Colors.white.withOpacity(0.1),
              borderRadius: BorderRadius.circular(6),
              border: Border.all(color: Colors.white24),
            ),
            child: Text(
              '+$remainingCount',
              style: const TextStyle(
                color: Colors.white70,
                fontSize: 10,
                fontWeight: FontWeight.bold,
              ),
            ),
          ),
      ],
    );
  }
}
