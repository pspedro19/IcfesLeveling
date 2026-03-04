import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';

import '../../../core/services/sound_service.dart';
import '../../../core/utils/app_haptics.dart';

/// XPCounter - Animated count-up display for XP earned
///
/// Features:
/// - Smooth count-up animation from 0 to target value
/// - Optional "tick tick tick" sound during count-up
/// - Subtle haptic feedback on milestones
/// - Glow effect that intensifies as value increases
class XPCounter extends StatefulWidget {
  final int targetValue;
  final Duration delay;
  final Duration countDuration;
  final bool playTickSound;
  final bool enableHaptics;
  final TextStyle? textStyle;

  const XPCounter({
    super.key,
    required this.targetValue,
    this.delay = Duration.zero,
    this.countDuration = const Duration(milliseconds: 1000),
    this.playTickSound = true,
    this.enableHaptics = true,
    this.textStyle,
  });

  @override
  State<XPCounter> createState() => _XPCounterState();
}

class _XPCounterState extends State<XPCounter>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  late Animation<double> _animation;
  int _displayValue = 0;
  int _lastTickValue = 0;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      duration: widget.countDuration,
      vsync: this,
    );

    _animation = Tween<double>(
      begin: 0,
      end: widget.targetValue.toDouble(),
    ).animate(CurvedAnimation(
      parent: _controller,
      curve: Curves.easeOutCubic,
    ));

    _animation.addListener(_onAnimationUpdate);

    // Start animation after delay
    Future.delayed(widget.delay, () {
      if (mounted) {
        _controller.forward();
      }
    });
  }

  void _onAnimationUpdate() {
    final newValue = _animation.value.round();
    if (newValue != _displayValue) {
      setState(() {
        _displayValue = newValue;
      });

      // Play tick sounds at intervals
      if (widget.playTickSound) {
        final tickInterval = widget.targetValue > 100 ? 10 : 5;
        if (newValue ~/ tickInterval > _lastTickValue ~/ tickInterval) {
          _lastTickValue = newValue;
          SoundService().playTickSound();
        }
      }

      // Haptic feedback at 25%, 50%, 75%, 100%
      if (widget.enableHaptics) {
        final percentage = newValue / widget.targetValue;
        if (_isAtMilestone(percentage)) {
          AppHaptics.xpTickPattern();
        }
      }
    }
  }

  bool _isAtMilestone(double percentage) {
    const milestones = [0.25, 0.5, 0.75, 1.0];
    for (final milestone in milestones) {
      final prevPercentage = (_displayValue - 1) / widget.targetValue;
      if (prevPercentage < milestone && percentage >= milestone) {
        return true;
      }
    }
    return false;
  }

  @override
  void dispose() {
    _animation.removeListener(_onAnimationUpdate);
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    // Glow intensity increases with progress
    final progress = _displayValue / widget.targetValue;
    final glowIntensity = 0.2 + (progress * 0.6);

    return AnimatedBuilder(
      animation: _animation,
      builder: (context, child) {
        return Container(
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
          decoration: BoxDecoration(
            color: Colors.amber.shade800.withOpacity(0.3),
            borderRadius: BorderRadius.circular(20),
            border: Border.all(
              color: Colors.amber.shade400.withOpacity(0.5 + (progress * 0.5)),
              width: 2,
            ),
            boxShadow: [
              BoxShadow(
                color: Colors.amber.withOpacity(glowIntensity),
                blurRadius: 15 + (progress * 10),
                spreadRadius: progress * 3,
              ),
            ],
          ),
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              _XPIcon(progress: progress),
              const SizedBox(width: 12),
              TweenAnimationBuilder<double>(
                tween: Tween(begin: 0.9, end: 1.0 + (progress * 0.1)),
                duration: const Duration(milliseconds: 100),
                builder: (context, scale, child) {
                  return Transform.scale(
                    scale: scale,
                    child: Text(
                      '+$_displayValue XP',
                      style: widget.textStyle ??
                          TextStyle(
                            color: Colors.amber.shade300,
                            fontSize: 28,
                            fontWeight: FontWeight.bold,
                            shadows: [
                              Shadow(
                                color: Colors.amber.withOpacity(0.5),
                                blurRadius: 10,
                              ),
                            ],
                          ),
                    ),
                  );
                },
              ),
            ],
          ),
        );
      },
    )
        .animate()
        .fadeIn(
          delay: widget.delay,
          duration: 200.ms,
        )
        .scale(
          begin: const Offset(0.8, 0.8),
          end: const Offset(1.0, 1.0),
          delay: widget.delay,
          duration: 300.ms,
          curve: Curves.easeOut,
        );
  }
}

class _XPIcon extends StatelessWidget {
  final double progress;

  const _XPIcon({required this.progress});

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 40,
      height: 40,
      decoration: BoxDecoration(
        shape: BoxShape.circle,
        gradient: RadialGradient(
          colors: [
            Colors.amber.shade400,
            Colors.amber.shade700,
          ],
        ),
        boxShadow: [
          BoxShadow(
            color: Colors.amber.withOpacity(0.3 + (progress * 0.4)),
            blurRadius: 8,
            spreadRadius: progress * 2,
          ),
        ],
      ),
      child: Icon(
        Icons.star,
        color: Colors.white,
        size: 24,
      ),
    )
        .animate(
          onPlay: (controller) => controller.repeat(),
        )
        .rotate(
          begin: 0,
          end: 0.1,
          duration: 500.ms,
        )
        .then()
        .rotate(
          begin: 0.1,
          end: -0.1,
          duration: 1000.ms,
        )
        .then()
        .rotate(
          begin: -0.1,
          end: 0,
          duration: 500.ms,
        );
  }
}

/// Simple inline XP indicator for use in other widgets
class InlineXPIndicator extends StatelessWidget {
  final int value;
  final bool showPlus;
  final double fontSize;

  const InlineXPIndicator({
    super.key,
    required this.value,
    this.showPlus = true,
    this.fontSize = 14,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: Colors.amber.shade700.withOpacity(0.3),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: Colors.amber.shade400.withOpacity(0.5),
          width: 1,
        ),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(
            Icons.star,
            color: Colors.amber.shade400,
            size: fontSize,
          ),
          const SizedBox(width: 4),
          Text(
            showPlus ? '+$value' : '$value',
            style: TextStyle(
              color: Colors.amber.shade300,
              fontSize: fontSize,
              fontWeight: FontWeight.bold,
            ),
          ),
        ],
      ),
    );
  }
}

/// Animated XP bubble that floats up and fades
class FloatingXPBubble extends StatelessWidget {
  final int value;
  final Duration delay;

  const FloatingXPBubble({
    super.key,
    required this.value,
    this.delay = Duration.zero,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
      decoration: BoxDecoration(
        color: Colors.amber.shade600.withOpacity(0.9),
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(
            color: Colors.amber.withOpacity(0.4),
            blurRadius: 8,
          ),
        ],
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          const Icon(
            Icons.star,
            color: Colors.white,
            size: 16,
          ),
          const SizedBox(width: 4),
          Text(
            '+$value',
            style: const TextStyle(
              color: Colors.white,
              fontSize: 16,
              fontWeight: FontWeight.bold,
            ),
          ),
        ],
      ),
    )
        .animate()
        .fadeIn(
          delay: delay,
          duration: 100.ms,
        )
        .slideY(
          begin: 0,
          end: -1.5,
          delay: delay,
          duration: 800.ms,
          curve: Curves.easeOut,
        )
        .scale(
          begin: const Offset(1.0, 1.0),
          end: const Offset(0.8, 0.8),
          delay: delay + 400.ms,
          duration: 400.ms,
        )
        .fadeOut(
          delay: delay + 500.ms,
          duration: 300.ms,
        );
  }
}
