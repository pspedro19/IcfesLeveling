import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';

import '../../../../core/config/app_theme.dart';
import '../../data/models/millionaire_models.dart';

class PrizeLadder extends StatelessWidget {
  final int currentQuestionIndex;
  final bool isExpanded;
  final VoidCallback? onToggle;

  const PrizeLadder({
    super.key,
    required this.currentQuestionIndex,
    this.isExpanded = false,
    this.onToggle,
  });

  @override
  Widget build(BuildContext context) {
    final tiers = PrizeTier.allTiers.reversed.toList();

    if (!isExpanded) {
      // Compact view - show only current and nearby questions
      return _buildCompactView(context, tiers);
    }

    return _buildExpandedView(context, tiers);
  }

  Widget _buildCompactView(BuildContext context, List<PrizeTier> tiers) {
    // Show current question, next 2 and previous 2
    final currentNum = currentQuestionIndex + 1;
    final visibleTiers = tiers.where((t) {
      final diff = (t.questionNumber - currentNum).abs();
      return diff <= 2 || t.isCheckpoint;
    }).toList();

    return GestureDetector(
      onTap: onToggle,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
        decoration: BoxDecoration(
          color: AppTheme.bgCard.withOpacity(0.9),
          borderRadius: BorderRadius.circular(12),
          border: Border.all(
            color: AppTheme.primaryPurple.withOpacity(0.3),
            width: 1,
          ),
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Text(
                  'Pregunta $currentNum/15',
                  style: const TextStyle(
                    color: AppTheme.textPrimary,
                    fontWeight: FontWeight.bold,
                    fontSize: 14,
                  ),
                ),
                const SizedBox(width: 8),
                Icon(
                  Icons.expand_more,
                  color: AppTheme.textSecondary,
                  size: 20,
                ),
              ],
            ),
            const SizedBox(height: 8),
            ...visibleTiers.take(5).map((tier) => _buildTierRow(tier, currentNum)),
          ],
        ),
      ).animate().fadeIn(duration: 200.ms),
    );
  }

  Widget _buildExpandedView(BuildContext context, List<PrizeTier> tiers) {
    final currentNum = currentQuestionIndex + 1;

    return GestureDetector(
      onTap: onToggle,
      child: Container(
        width: 160,
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topCenter,
            end: Alignment.bottomCenter,
            colors: [
              AppTheme.bgCard.withOpacity(0.95),
              AppTheme.bgDark.withOpacity(0.95),
            ],
          ),
          borderRadius: BorderRadius.circular(16),
          border: Border.all(
            color: AppTheme.primaryPurple.withOpacity(0.5),
            width: 2,
          ),
          boxShadow: [
            BoxShadow(
              color: AppTheme.primaryPurple.withOpacity(0.2),
              blurRadius: 20,
              spreadRadius: 2,
            ),
          ],
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Text(
                  'PREMIOS',
                  style: TextStyle(
                    color: AppTheme.secondaryGold,
                    fontWeight: FontWeight.bold,
                    fontSize: 12,
                    letterSpacing: 2,
                  ),
                ),
                Icon(
                  Icons.expand_less,
                  color: AppTheme.textSecondary,
                  size: 20,
                ),
              ],
            ),
            const Divider(color: AppTheme.bgElevated, height: 16),
            ...tiers.map((tier) => _buildTierRow(tier, currentNum)),
          ],
        ),
      ).animate().fadeIn(duration: 200.ms).scale(begin: const Offset(0.95, 0.95)),
    );
  }

  Widget _buildTierRow(PrizeTier tier, int currentQuestionNum) {
    final isCurrent = tier.questionNumber == currentQuestionNum;
    final isPast = tier.questionNumber < currentQuestionNum;
    final isCheckpoint = tier.isCheckpoint;

    Color textColor;
    Color bgColor;
    FontWeight weight;

    if (isCurrent) {
      textColor = Colors.white;
      bgColor = AppTheme.primaryPurple;
      weight = FontWeight.bold;
    } else if (isPast) {
      textColor = AppTheme.successGreen;
      bgColor = AppTheme.successGreen.withOpacity(0.1);
      weight = FontWeight.w500;
    } else {
      textColor = AppTheme.textSecondary;
      bgColor = Colors.transparent;
      weight = FontWeight.normal;
    }

    Widget row = Container(
      margin: const EdgeInsets.symmetric(vertical: 2),
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 6),
      decoration: BoxDecoration(
        color: bgColor,
        borderRadius: BorderRadius.circular(8),
        border: isCheckpoint
            ? Border.all(
                color: AppTheme.secondaryGold.withOpacity(isCurrent ? 1 : 0.5),
                width: 2,
              )
            : null,
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              if (isPast)
                const Icon(
                  Icons.check_circle,
                  color: AppTheme.successGreen,
                  size: 14,
                )
              else
                Text(
                  '${tier.questionNumber}',
                  style: TextStyle(
                    color: textColor,
                    fontWeight: weight,
                    fontSize: 12,
                  ),
                ),
              if (isCheckpoint) ...[
                const SizedBox(width: 4),
                Icon(
                  Icons.shield,
                  color: AppTheme.secondaryGold,
                  size: 12,
                ),
              ],
            ],
          ),
          Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(
                '${tier.goldReward}',
                style: TextStyle(
                  color: isPast
                      ? AppTheme.secondaryGold.withOpacity(0.7)
                      : isCurrent
                          ? AppTheme.secondaryGold
                          : textColor,
                  fontWeight: weight,
                  fontSize: 11,
                ),
              ),
              Icon(
                Icons.monetization_on,
                size: 12,
                color: isPast
                    ? AppTheme.secondaryGold.withOpacity(0.7)
                    : isCurrent
                        ? AppTheme.secondaryGold
                        : textColor.withOpacity(0.7),
              ),
            ],
          ),
        ],
      ),
    );

    if (isCurrent) {
      row = row
          .animate(onPlay: (controller) => controller.repeat(reverse: true))
          .shimmer(
            duration: 1500.ms,
            color: Colors.white.withOpacity(0.3),
          );
    }

    return row;
  }
}

/// Floating mini ladder for game screen
class FloatingPrizeLadder extends StatefulWidget {
  final int currentQuestionIndex;

  const FloatingPrizeLadder({
    super.key,
    required this.currentQuestionIndex,
  });

  @override
  State<FloatingPrizeLadder> createState() => _FloatingPrizeLadderState();
}

class _FloatingPrizeLadderState extends State<FloatingPrizeLadder> {
  bool _isExpanded = false;

  @override
  Widget build(BuildContext context) {
    return Positioned(
      top: 100,
      right: 16,
      child: PrizeLadder(
        currentQuestionIndex: widget.currentQuestionIndex,
        isExpanded: _isExpanded,
        onToggle: () => setState(() => _isExpanded = !_isExpanded),
      ),
    );
  }
}
