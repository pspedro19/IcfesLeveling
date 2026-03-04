import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import '../../../core/config/animation_config.dart';
import '../../../core/services/psychological_triggers_service.dart';

/// Widget that displays loss aversion triggers as alerts
/// Shows streak at risk, low hearts, demotion risk, etc.
class LossAversionAlerts extends StatelessWidget {
  final List<LossAversionTrigger> triggers;
  final VoidCallback? onDismiss;
  final Function(LossAversionTrigger)? onTriggerTap;
  final bool compact;

  const LossAversionAlerts({
    super.key,
    required this.triggers,
    this.onDismiss,
    this.onTriggerTap,
    this.compact = false,
  });

  @override
  Widget build(BuildContext context) {
    if (triggers.isEmpty) return const SizedBox.shrink();

    // Sort by severity (high first)
    final sortedTriggers = List<LossAversionTrigger>.from(triggers)
      ..sort((a, b) {
        final severityOrder = {'high': 0, 'medium': 1, 'low': 2};
        return (severityOrder[a.severity] ?? 2).compareTo(severityOrder[b.severity] ?? 2);
      });

    if (compact) {
      return _buildCompactView(sortedTriggers);
    }

    return Column(
      children: sortedTriggers.asMap().entries.map((entry) {
        final index = entry.key;
        final trigger = entry.value;
        return Padding(
          padding: const EdgeInsets.only(bottom: 8),
          child: _LossAversionCard(
            trigger: trigger,
            onTap: () => onTriggerTap?.call(trigger),
          ).animate()
              .fadeIn(delay: (index * 100).ms)
              .slideX(begin: -0.1),
        );
      }).toList(),
    );
  }

  Widget _buildCompactView(List<LossAversionTrigger> triggers) {
    // Show only the most urgent trigger in compact mode
    final urgentTrigger = triggers.first;

    return GestureDetector(
      onTap: () => onTriggerTap?.call(urgentTrigger),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
        decoration: BoxDecoration(
          color: urgentTrigger.color.withOpacity(0.15),
          borderRadius: BorderRadius.circular(20),
          border: Border.all(color: urgentTrigger.color.withOpacity(0.3)),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(urgentTrigger.icon, color: urgentTrigger.color, size: 16)
                .animate(onPlay: AnimationConfig.infiniteAnimationsEnabled
                    ? (c) => c.repeat() : null)
                .shake(duration: 1000.ms, hz: 2),
            const SizedBox(width: 8),
            Flexible(
              child: Text(
                urgentTrigger.message,
                style: TextStyle(
                  color: urgentTrigger.color,
                  fontSize: 12,
                  fontWeight: FontWeight.w600,
                ),
                overflow: TextOverflow.ellipsis,
              ),
            ),
            if (triggers.length > 1) ...[
              const SizedBox(width: 8),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                decoration: BoxDecoration(
                  color: urgentTrigger.color.withOpacity(0.3),
                  borderRadius: BorderRadius.circular(10),
                ),
                child: Text(
                  "+${triggers.length - 1}",
                  style: TextStyle(
                    color: urgentTrigger.color,
                    fontSize: 10,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }
}


/// Individual loss aversion alert card
class _LossAversionCard extends StatelessWidget {
  final LossAversionTrigger trigger;
  final VoidCallback? onTap;

  const _LossAversionCard({
    required this.trigger,
    this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final isUrgent = trigger.severity == 'high';

    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          gradient: LinearGradient(
            colors: [
              trigger.color.withOpacity(0.15),
              trigger.color.withOpacity(0.05),
            ],
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
          ),
          borderRadius: BorderRadius.circular(16),
          border: Border.all(
            color: trigger.color.withOpacity(isUrgent ? 0.5 : 0.3),
            width: isUrgent ? 2 : 1,
          ),
          boxShadow: isUrgent
              ? [
                  BoxShadow(
                    color: trigger.color.withOpacity(0.2),
                    blurRadius: 10,
                    spreadRadius: 2,
                  ),
                ]
              : null,
        ),
        child: Row(
          children: [
            // Icon
            Container(
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: trigger.color.withOpacity(0.2),
                shape: BoxShape.circle,
              ),
              child: Icon(
                trigger.icon,
                color: trigger.color,
                size: 24,
              ),
            ).animate(onPlay: (AnimationConfig.infiniteAnimationsEnabled && isUrgent)
                    ? (c) => c.repeat() : null)
                .shake(duration: 1000.ms, hz: 2),

            const SizedBox(width: 16),

            // Content
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      if (isUrgent)
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                          margin: const EdgeInsets.only(right: 8),
                          decoration: BoxDecoration(
                            color: trigger.color,
                            borderRadius: BorderRadius.circular(4),
                          ),
                          child: const Text(
                            "URGENTE",
                            style: TextStyle(
                              color: Colors.white,
                              fontSize: 9,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ),
                      Expanded(
                        child: Text(
                          trigger.message,
                          style: TextStyle(
                            color: Colors.white,
                            fontSize: 14,
                            fontWeight: isUrgent ? FontWeight.bold : FontWeight.w500,
                          ),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 4),
                  Text(
                    trigger.action,
                    style: TextStyle(
                      color: trigger.color.withOpacity(0.8),
                      fontSize: 12,
                    ),
                  ),
                ],
              ),
            ),

            // Action indicator
            Icon(
              Icons.chevron_right,
              color: trigger.color.withOpacity(0.5),
            ),
          ],
        ),
      ),
    );
  }
}


/// Endowed Progress Widget - Shows what user has already "earned"
class EndowedProgressDisplay extends StatelessWidget {
  final List<EndowedProgressItem> endowments;
  final VoidCallback? onDismiss;

  const EndowedProgressDisplay({
    super.key,
    required this.endowments,
    this.onDismiss,
  });

  @override
  Widget build(BuildContext context) {
    if (endowments.isEmpty) return const SizedBox.shrink();

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [
            Colors.purple.withOpacity(0.15),
            Colors.blue.withOpacity(0.1),
          ],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.purple.withOpacity(0.3)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Text(
                "YA TIENES VENTAJA",
                style: TextStyle(
                  color: Colors.purple,
                  fontSize: 12,
                  fontWeight: FontWeight.bold,
                  letterSpacing: 1,
                ),
              ),
              if (onDismiss != null)
                GestureDetector(
                  onTap: onDismiss,
                  child: const Icon(Icons.close, color: Colors.white38, size: 18),
                ),
            ],
          ),
          const SizedBox(height: 12),
          ...endowments.asMap().entries.map((entry) {
            final index = entry.key;
            final item = entry.value;
            return Padding(
              padding: const EdgeInsets.only(bottom: 12),
              child: Row(
                children: [
                  Container(
                    padding: const EdgeInsets.all(8),
                    decoration: BoxDecoration(
                      color: item.color.withOpacity(0.2),
                      borderRadius: BorderRadius.circular(10),
                    ),
                    child: Icon(item.icon, color: item.color, size: 20),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          item.title,
                          style: const TextStyle(
                            color: Colors.white,
                            fontSize: 14,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                        Text(
                          item.description,
                          style: const TextStyle(
                            color: Colors.white54,
                            fontSize: 12,
                          ),
                        ),
                      ],
                    ),
                  ),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                    decoration: BoxDecoration(
                      color: item.color.withOpacity(0.2),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Text(
                      item.value,
                      style: TextStyle(
                        color: item.color,
                        fontSize: 11,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                ],
              ).animate()
                  .fadeIn(delay: (index * 150).ms)
                  .slideX(begin: 0.1),
            );
          }),
        ],
      ),
    );
  }
}


/// Variable Reward Popup - Shows bonus rewards
class VariableRewardPopup extends StatelessWidget {
  final VariableReward reward;
  final VoidCallback? onDismiss;

  const VariableRewardPopup({
    super.key,
    required this.reward,
    this.onDismiss,
  });

  @override
  Widget build(BuildContext context) {
    if (!reward.hasBonus) return const SizedBox.shrink();

    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [
            _getBonusColor().withOpacity(0.3),
            _getBonusColor().withOpacity(0.1),
          ],
          begin: Alignment.topCenter,
          end: Alignment.bottomCenter,
        ),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: _getBonusColor().withOpacity(0.5), width: 2),
        boxShadow: [
          BoxShadow(
            color: _getBonusColor().withOpacity(0.4),
            blurRadius: 20,
            spreadRadius: 5,
          ),
        ],
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          // Animated icon
          Icon(
            _getBonusIcon(),
            color: _getBonusColor(),
            size: 48,
          ).animate(onPlay: AnimationConfig.infiniteAnimationsEnabled
                  ? (c) => c.repeat(reverse: true) : null)
              .scale(duration: 500.ms, begin: const Offset(1, 1), end: const Offset(1.2, 1.2))
              .shimmer(duration: 1000.ms, color: Colors.white.withOpacity(0.5)),

          const SizedBox(height: 16),

          // Bonus message
          Text(
            reward.bonusMessage ?? "Bonus!",
            style: TextStyle(
              color: _getBonusColor(),
              fontSize: 20,
              fontWeight: FontWeight.bold,
            ),
            textAlign: TextAlign.center,
          ).animate()
              .fadeIn()
              .scale(begin: const Offset(0.5, 0.5)),

          const SizedBox(height: 8),

          // Amount
          if (reward.bonusAmount != null)
            Text(
              "+${reward.bonusAmount}",
              style: const TextStyle(
                color: Colors.white,
                fontSize: 36,
                fontWeight: FontWeight.w900,
              ),
            ).animate()
                .fadeIn(delay: 200.ms)
                .slideY(begin: 0.5),

          const SizedBox(height: 16),

          // Dismiss button
          TextButton(
            onPressed: onDismiss ?? () => Navigator.of(context).pop(),
            child: const Text(
              "Continuar",
              style: TextStyle(color: Colors.white70),
            ),
          ),
        ],
      ),
    ).animate()
        .fadeIn()
        .scale(begin: const Offset(0.8, 0.8));
  }

  Color _getBonusColor() {
    switch (reward.bonusType) {
      case BonusType.xpBonus:
        return Colors.blue;
      case BonusType.goldBonus:
        return Colors.amber;
      case BonusType.rareBonus:
        return Colors.purple;
      default:
        return Colors.blue;
    }
  }

  IconData _getBonusIcon() {
    switch (reward.bonusType) {
      case BonusType.xpBonus:
        return Icons.star;
      case BonusType.goldBonus:
        return Icons.monetization_on;
      case BonusType.rareBonus:
        return Icons.card_giftcard;
      default:
        return Icons.star;
    }
  }
}


/// Social Proof Banner - Shows what others are achieving
class SocialProofBanner extends StatelessWidget {
  final List<String> messages;
  final int percentile;
  final String? leagueRank;

  const SocialProofBanner({
    super.key,
    required this.messages,
    required this.percentile,
    this.leagueRank,
  });

  @override
  Widget build(BuildContext context) {
    if (messages.isEmpty) return const SizedBox.shrink();

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      decoration: BoxDecoration(
        color: Colors.blue.withOpacity(0.1),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Colors.blue.withOpacity(0.2)),
      ),
      child: Row(
        children: [
          Icon(
            Icons.groups,
            color: Colors.blue.withOpacity(0.7),
            size: 20,
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  messages.first,
                  style: const TextStyle(
                    color: Colors.white70,
                    fontSize: 13,
                  ),
                ),
                if (leagueRank != null)
                  Text(
                    "Liga: $leagueRank",
                    style: const TextStyle(
                      color: Colors.blue,
                      fontSize: 11,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
              ],
            ),
          ),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
            decoration: BoxDecoration(
              color: _getPercentileColor(percentile).withOpacity(0.2),
              borderRadius: BorderRadius.circular(12),
            ),
            child: Text(
              "Top ${100 - percentile}%",
              style: TextStyle(
                color: _getPercentileColor(percentile),
                fontSize: 11,
                fontWeight: FontWeight.bold,
              ),
            ),
          ),
        ],
      ),
    );
  }

  Color _getPercentileColor(int percentile) {
    if (percentile >= 90) return Colors.amber;
    if (percentile >= 70) return Colors.green;
    if (percentile >= 50) return Colors.blue;
    return Colors.orange;
  }
}
