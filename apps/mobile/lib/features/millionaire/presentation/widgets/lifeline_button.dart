import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';

import '../../../../core/config/app_theme.dart';
import '../../data/models/millionaire_models.dart';

class LifelineButton extends StatelessWidget {
  final LifelineState lifeline;
  final bool isEnabled;
  final int userGold;
  final VoidCallback? onTap;

  const LifelineButton({
    super.key,
    required this.lifeline,
    required this.isEnabled,
    required this.userGold,
    this.onTap,
  });

  bool get _canAfford {
    if (lifeline.goldCost == 0) return true;
    return userGold >= lifeline.goldCost;
  }

  bool get _isAvailable => isEnabled && !lifeline.isUsed && _canAfford;

  Color get _backgroundColor {
    if (lifeline.isUsed) {
      return Colors.grey.shade800.withOpacity(0.5);
    }
    if (!_canAfford && lifeline.goldCost > 0) {
      return Colors.grey.shade700.withOpacity(0.5);
    }
    return AppTheme.bgElevated;
  }

  Color get _iconColor {
    if (lifeline.isUsed || !_canAfford) {
      return Colors.grey.shade500;
    }
    switch (lifeline.type) {
      case LifelineType.fiftyFifty:
        return AppTheme.accentCyan;
      case LifelineType.askAI:
        return AppTheme.secondaryGold;
      case LifelineType.skip:
        return AppTheme.successGreen;
    }
  }

  IconData get _icon {
    switch (lifeline.type) {
      case LifelineType.fiftyFifty:
        return Icons.exposure_minus_2_rounded;
      case LifelineType.askAI:
        return Icons.psychology_rounded;
      case LifelineType.skip:
        return Icons.skip_next_rounded;
    }
  }

  @override
  Widget build(BuildContext context) {
    Widget button = Container(
      width: 90,
      height: 80,
      decoration: BoxDecoration(
        color: _backgroundColor,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: _isAvailable ? _iconColor.withOpacity(0.5) : Colors.transparent,
          width: 2,
        ),
        boxShadow: _isAvailable
            ? [
                BoxShadow(
                  color: _iconColor.withOpacity(0.3),
                  blurRadius: 12,
                  spreadRadius: 0,
                ),
              ]
            : null,
      ),
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          onTap: _isAvailable ? onTap : null,
          borderRadius: BorderRadius.circular(16),
          child: Stack(
            children: [
              // Main content
              Center(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(
                      _icon,
                      size: 28,
                      color: _iconColor,
                    ),
                    const SizedBox(height: 4),
                    Text(
                      lifeline.displayName,
                      style: TextStyle(
                        color: lifeline.isUsed
                            ? Colors.grey.shade500
                            : AppTheme.textPrimary,
                        fontSize: 12,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                    if (lifeline.goldCost > 0) ...[
                      const SizedBox(height: 2),
                      Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Icon(
                            Icons.monetization_on,
                            size: 12,
                            color: _canAfford
                                ? AppTheme.secondaryGold
                                : Colors.grey.shade500,
                          ),
                          const SizedBox(width: 2),
                          Text(
                            '${lifeline.goldCost}',
                            style: TextStyle(
                              color: _canAfford
                                  ? AppTheme.secondaryGold
                                  : Colors.grey.shade500,
                              fontSize: 10,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ],
                      ),
                    ],
                  ],
                ),
              ),

              // Used overlay
              if (lifeline.isUsed)
                Positioned.fill(
                  child: Container(
                    decoration: BoxDecoration(
                      color: Colors.black.withOpacity(0.4),
                      borderRadius: BorderRadius.circular(16),
                    ),
                    child: const Center(
                      child: Icon(
                        Icons.check_circle,
                        color: Colors.grey,
                        size: 24,
                      ),
                    ),
                  ),
                ),
            ],
          ),
        ),
      ),
    );

    // Add pulse animation for available lifelines
    if (_isAvailable) {
      button = button
          .animate(onPlay: (controller) => controller.repeat(reverse: true))
          .shimmer(
            duration: 2000.ms,
            color: _iconColor.withOpacity(0.1),
          );
    }

    return button;
  }
}

/// Row of all lifeline buttons
class LifelineRow extends StatelessWidget {
  final List<LifelineState> lifelines;
  final bool isEnabled;
  final int userGold;
  final bool isLoadingHint;
  final Function(LifelineType) onLifelineUsed;

  const LifelineRow({
    super.key,
    required this.lifelines,
    required this.isEnabled,
    required this.userGold,
    required this.isLoadingHint,
    required this.onLifelineUsed,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 16),
      decoration: BoxDecoration(
        color: AppTheme.bgCard.withOpacity(0.8),
        borderRadius: BorderRadius.circular(20),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceEvenly,
        children: lifelines.map((lifeline) {
          // Show loading indicator for AI hint
          if (lifeline.type == LifelineType.askAI && isLoadingHint) {
            return SizedBox(
              width: 90,
              height: 80,
              child: Center(
                child: CircularProgressIndicator(
                  color: AppTheme.secondaryGold,
                  strokeWidth: 2,
                ),
              ),
            );
          }

          return LifelineButton(
            lifeline: lifeline,
            isEnabled: isEnabled,
            userGold: userGold,
            onTap: () => onLifelineUsed(lifeline.type),
          );
        }).toList(),
      ),
    ).animate().fadeIn(duration: 300.ms).slideY(begin: 0.2, end: 0);
  }
}
