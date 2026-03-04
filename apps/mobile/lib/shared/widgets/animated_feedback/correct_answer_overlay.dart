import 'dart:math';
import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';

import '../lottie_overlay.dart';

/// CorrectAnswerOverlay - Visual celebration for correct answers
///
/// Animation timeline (600ms total):
/// - 0ms: Green glow starts expanding
/// - 150ms: Checkmark bounces in
/// - 300ms: "+XP" floats upward
/// - 400ms: Particles appear if combo >= 3
/// - 600ms: Complete
class CorrectAnswerOverlay extends StatelessWidget {
  final int xpEarned;
  final int combo;

  const CorrectAnswerOverlay({
    super.key,
    required this.xpEarned,
    required this.combo,
  });

  @override
  Widget build(BuildContext context) {
    return Material(
      color: Colors.transparent,
      child: Stack(
        children: [
          // Green glow expanding from center
          _ExpandingGlow(),

          // Center content
          Center(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                // Checkmark with bounce
                _BouncingCheckmark(),

                const SizedBox(height: 16),

                // XP floating up
                _FloatingXP(xpEarned: xpEarned),

                // Combo indicator
                if (combo >= 2) ...[
                  const SizedBox(height: 8),
                  _ComboIndicator(combo: combo),
                ],
              ],
            ),
          ),

          // Particles for high combos
          if (combo >= 3) _ParticleExplosion(),

          // Lottie star burst for combos >= 5
          if (combo >= 5)
            IgnorePointer(
              child: Center(
                child: Lottie.asset(
                  LottieAssets.starBurst,
                  width: 250,
                  height: 250,
                  repeat: false,
                  errorBuilder: (_, __, ___) => const SizedBox.shrink(),
                ),
              ),
            ),
        ],
      ),
    );
  }
}

/// Green glow that expands outward from center
class _ExpandingGlow extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Center(
      child: Container(
        width: 200,
        height: 200,
        decoration: BoxDecoration(
          shape: BoxShape.circle,
          gradient: RadialGradient(
            colors: [
              Colors.green.withOpacity(0.6),
              Colors.green.withOpacity(0.3),
              Colors.green.withOpacity(0.0),
            ],
            stops: const [0.0, 0.5, 1.0],
          ),
        ),
      )
          .animate()
          .scale(
            begin: const Offset(0.0, 0.0),
            end: const Offset(3.0, 3.0),
            duration: 400.ms,
            curve: Curves.easeOut,
          )
          .fadeOut(
            delay: 300.ms,
            duration: 300.ms,
          ),
    );
  }
}

/// Checkmark icon with bounce animation + Lottie overlay
class _BouncingCheckmark extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: 120,
      height: 120,
      child: Stack(
        alignment: Alignment.center,
        children: [
          // Lottie correctCheck behind the icon
          Lottie.asset(
            LottieAssets.correctCheck,
            width: 120,
            height: 120,
            fit: BoxFit.contain,
            repeat: false,
            errorBuilder: (_, __, ___) => const SizedBox.shrink(),
          ),
          // Semi-transparent icon so Lottie animation shows through
          Opacity(
            opacity: 0.85,
            child: Container(
              width: 80,
              height: 80,
              decoration: BoxDecoration(
                color: Colors.green,
                shape: BoxShape.circle,
                boxShadow: [
                  BoxShadow(
                    color: Colors.green.withOpacity(0.5),
                    blurRadius: 20,
                    spreadRadius: 5,
                  ),
                ],
              ),
              child: const Icon(
                Icons.check,
                color: Colors.white,
                size: 48,
              ),
            ),
          )
              .animate()
              .scale(
                begin: const Offset(0.0, 0.0),
                end: const Offset(1.0, 1.0),
                duration: 300.ms,
                curve: Curves.elasticOut,
                delay: 100.ms,
              )
              .shake(
                delay: 350.ms,
                duration: 100.ms,
                hz: 4,
                rotation: 0.05,
              ),
        ],
      ),
    );
  }
}

/// XP indicator that floats upward
class _FloatingXP extends StatelessWidget {
  final int xpEarned;

  const _FloatingXP({required this.xpEarned});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      decoration: BoxDecoration(
        color: Colors.amber.shade600,
        borderRadius: BorderRadius.circular(20),
        boxShadow: [
          BoxShadow(
            color: Colors.amber.withOpacity(0.5),
            blurRadius: 10,
            spreadRadius: 2,
          ),
        ],
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          const Icon(
            Icons.star,
            color: Colors.white,
            size: 20,
          ),
          const SizedBox(width: 4),
          Text(
            '+$xpEarned XP',
            style: const TextStyle(
              color: Colors.white,
              fontSize: 18,
              fontWeight: FontWeight.bold,
            ),
          ),
        ],
      ),
    )
        .animate()
        .fadeIn(
          delay: 200.ms,
          duration: 150.ms,
        )
        .slideY(
          begin: 0.5,
          end: 0,
          delay: 200.ms,
          duration: 300.ms,
          curve: Curves.easeOut,
        )
        .then() // After appearing
        .slideY(
          begin: 0,
          end: -0.5,
          duration: 400.ms,
          curve: Curves.easeIn,
        )
        .fadeOut(
          duration: 200.ms,
        );
  }
}

/// Combo multiplier indicator
class _ComboIndicator extends StatelessWidget {
  final int combo;

  const _ComboIndicator({required this.combo});

  @override
  Widget build(BuildContext context) {
    // Color intensifies with higher combos
    final Color comboColor = combo >= 8
        ? Colors.purple
        : combo >= 5
            ? Colors.orange
            : Colors.blue;

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
      decoration: BoxDecoration(
        color: comboColor.withOpacity(0.9),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.white, width: 2),
      ),
      child: Text(
        'COMBO x$combo',
        style: const TextStyle(
          color: Colors.white,
          fontSize: 14,
          fontWeight: FontWeight.bold,
          letterSpacing: 1.2,
        ),
      ),
    )
        .animate()
        .fadeIn(
          delay: 300.ms,
          duration: 150.ms,
        )
        .scale(
          begin: const Offset(0.5, 0.5),
          end: const Offset(1.0, 1.0),
          delay: 300.ms,
          duration: 200.ms,
          curve: Curves.elasticOut,
        )
        .shimmer(
          delay: 400.ms,
          duration: 500.ms,
          color: Colors.white.withOpacity(0.3),
        );
  }
}

/// Particle explosion for high combos
class _ParticleExplosion extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Center(
      child: SizedBox(
        width: 300,
        height: 300,
        child: Stack(
          children: List.generate(12, (index) {
            final angle = (index * 30) * pi / 180;
            final random = Random(index);
            final distance = 100.0 + random.nextDouble() * 50;
            final size = 8.0 + random.nextDouble() * 8;
            final color = [
              Colors.green,
              Colors.amber,
              Colors.lime,
              Colors.yellow,
            ][index % 4];

            return Center(
              child: Container(
                width: size,
                height: size,
                decoration: BoxDecoration(
                  color: color,
                  shape: BoxShape.circle,
                  boxShadow: [
                    BoxShadow(
                      color: color.withOpacity(0.5),
                      blurRadius: 4,
                    ),
                  ],
                ),
              )
                  .animate()
                  .fadeIn(
                    delay: Duration(milliseconds: 350 + (index * 20)),
                    duration: 50.ms,
                  )
                  .custom(
                    delay: Duration(milliseconds: 350 + (index * 20)),
                    duration: 400.ms,
                    curve: Curves.easeOut,
                    builder: (context, value, child) {
                      return Transform.translate(
                        offset: Offset(
                          cos(angle) * distance * value,
                          sin(angle) * distance * value,
                        ),
                        child: Opacity(
                          opacity: 1 - value,
                          child: child,
                        ),
                      );
                    },
                  ),
            );
          }),
        ),
      ),
    );
  }
}

/// Standalone widget for use in existing layouts
class CorrectAnswerFeedback extends StatelessWidget {
  final int xpEarned;
  final int combo;
  final VoidCallback? onComplete;

  const CorrectAnswerFeedback({
    super.key,
    required this.xpEarned,
    required this.combo,
    this.onComplete,
  });

  @override
  Widget build(BuildContext context) {
    // Trigger completion callback
    if (onComplete != null) {
      Future.delayed(const Duration(milliseconds: 600), onComplete);
    }

    return CorrectAnswerOverlay(
      xpEarned: xpEarned,
      combo: combo,
    );
  }
}
