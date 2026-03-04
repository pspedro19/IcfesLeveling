import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';

import '../lottie_overlay.dart';

/// IncorrectAnswerOverlay - Visual feedback for incorrect answers
///
/// Animation timeline (800ms total):
/// - 0ms: Shake animation starts (3 cycles, 5px amplitude)
/// - 200ms: X mark fades in
/// - 400ms: Heart "crack" animation
/// - 600ms: Correct answer hint illuminates
/// - 800ms: Complete
class IncorrectAnswerOverlay extends StatelessWidget {
  final String correctAnswer;
  final bool showHeartBreak;

  const IncorrectAnswerOverlay({
    super.key,
    required this.correctAnswer,
    this.showHeartBreak = true,
  });

  @override
  Widget build(BuildContext context) {
    return Material(
      color: Colors.transparent,
      child: Stack(
        children: [
          // Red pulse background
          _RedPulse(),

          // Center content
          Center(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                // Shaking X mark
                _ShakingXMark(),

                const SizedBox(height: 16),

                // Heart crack animation
                if (showHeartBreak) ...[
                  _HeartCrack(),
                  const SizedBox(height: 16),
                ],

                // Correct answer hint
                _CorrectAnswerHint(correctAnswer: correctAnswer),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

/// Red pulse that appears on wrong answer
class _RedPulse extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Center(
      child: Container(
        width: 150,
        height: 150,
        decoration: BoxDecoration(
          shape: BoxShape.circle,
          gradient: RadialGradient(
            colors: [
              Colors.red.withOpacity(0.5),
              Colors.red.withOpacity(0.2),
              Colors.red.withOpacity(0.0),
            ],
            stops: const [0.0, 0.5, 1.0],
          ),
        ),
      )
          .animate()
          .scale(
            begin: const Offset(0.5, 0.5),
            end: const Offset(2.5, 2.5),
            duration: 300.ms,
            curve: Curves.easeOut,
          )
          .fadeOut(
            delay: 200.ms,
            duration: 300.ms,
          ),
    );
  }
}

/// X mark icon with shake animation + Lottie overlay
class _ShakingXMark extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: 120,
      height: 120,
      child: Stack(
        alignment: Alignment.center,
        children: [
          // Lottie wrongX behind the icon
          Lottie.asset(
            LottieAssets.wrongX,
            width: 120,
            height: 120,
            fit: BoxFit.contain,
            repeat: false,
            errorBuilder: (_, __, ___) => const SizedBox.shrink(),
          ),
          // Original icon fallback on top
          Container(
            width: 80,
            height: 80,
            decoration: BoxDecoration(
              color: Colors.red.shade600,
              shape: BoxShape.circle,
              boxShadow: [
                BoxShadow(
                  color: Colors.red.withOpacity(0.4),
                  blurRadius: 15,
                  spreadRadius: 3,
                ),
              ],
            ),
            child: const Icon(
              Icons.close,
              color: Colors.white,
              size: 48,
            ),
          )
              .animate()
              .fadeIn(duration: 100.ms)
              .shake(
                duration: 400.ms,
                hz: 6,
                offset: const Offset(5, 0),
                rotation: 0,
              )
              .scale(
                begin: const Offset(0.8, 0.8),
                end: const Offset(1.0, 1.0),
                duration: 150.ms,
                curve: Curves.easeOut,
              ),
        ],
      ),
    );
  }
}

/// Heart with crack animation
class _HeartCrack extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: 60,
      height: 60,
      child: Stack(
        alignment: Alignment.center,
        children: [
          // Faded heart background
          Icon(
            Icons.favorite,
            color: Colors.red.shade300,
            size: 50,
          )
              .animate()
              .fadeIn(
                delay: 300.ms,
                duration: 100.ms,
              )
              .scale(
                begin: const Offset(1.0, 1.0),
                end: const Offset(0.8, 0.8),
                delay: 400.ms,
                duration: 200.ms,
              ),

          // Crack effect (two halves separating)
          Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              // Left half
              ClipRect(
                child: Align(
                  alignment: Alignment.centerLeft,
                  widthFactor: 0.5,
                  child: Icon(
                    Icons.favorite,
                    color: Colors.red.shade700,
                    size: 50,
                  ),
                ),
              )
                  .animate()
                  .fadeIn(
                    delay: 400.ms,
                    duration: 50.ms,
                  )
                  .slideX(
                    begin: 0,
                    end: -0.15,
                    delay: 400.ms,
                    duration: 200.ms,
                    curve: Curves.easeOut,
                  )
                  .rotate(
                    begin: 0,
                    end: -0.05,
                    delay: 400.ms,
                    duration: 200.ms,
                  ),

              // Right half
              ClipRect(
                child: Align(
                  alignment: Alignment.centerRight,
                  widthFactor: 0.5,
                  child: Icon(
                    Icons.favorite,
                    color: Colors.red.shade700,
                    size: 50,
                  ),
                ),
              )
                  .animate()
                  .fadeIn(
                    delay: 400.ms,
                    duration: 50.ms,
                  )
                  .slideX(
                    begin: 0,
                    end: 0.15,
                    delay: 400.ms,
                    duration: 200.ms,
                    curve: Curves.easeOut,
                  )
                  .rotate(
                    begin: 0,
                    end: 0.05,
                    delay: 400.ms,
                    duration: 200.ms,
                  ),
            ],
          ),

          // "-1" indicator
          Positioned(
            bottom: 0,
            right: 0,
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
              decoration: BoxDecoration(
                color: Colors.black.withOpacity(0.7),
                borderRadius: BorderRadius.circular(8),
              ),
              child: const Text(
                '-1',
                style: TextStyle(
                  color: Colors.red,
                  fontSize: 12,
                  fontWeight: FontWeight.bold,
                ),
              ),
            )
                .animate()
                .fadeIn(
                  delay: 500.ms,
                  duration: 100.ms,
                )
                .slideY(
                  begin: -0.5,
                  end: 0,
                  delay: 500.ms,
                  duration: 150.ms,
                ),
          ),
        ],
      ),
    );
  }
}

/// Hint showing the correct answer
class _CorrectAnswerHint extends StatelessWidget {
  final String correctAnswer;

  const _CorrectAnswerHint({required this.correctAnswer});

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 24),
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      decoration: BoxDecoration(
        color: Colors.green.shade700.withOpacity(0.9),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: Colors.green.shade300,
          width: 2,
        ),
        boxShadow: [
          BoxShadow(
            color: Colors.green.withOpacity(0.3),
            blurRadius: 10,
            spreadRadius: 2,
          ),
        ],
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          const Icon(
            Icons.lightbulb_outline,
            color: Colors.white,
            size: 20,
          ),
          const SizedBox(width: 8),
          Flexible(
            child: Text(
              'Respuesta: $correctAnswer',
              style: const TextStyle(
                color: Colors.white,
                fontSize: 14,
                fontWeight: FontWeight.w500,
              ),
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
            ),
          ),
        ],
      ),
    )
        .animate()
        .fadeIn(
          delay: 600.ms,
          duration: 150.ms,
        )
        .slideY(
          begin: 0.3,
          end: 0,
          delay: 600.ms,
          duration: 200.ms,
          curve: Curves.easeOut,
        )
        .shimmer(
          delay: 700.ms,
          duration: 400.ms,
          color: Colors.white.withOpacity(0.2),
        );
  }
}

/// Standalone widget for use in existing layouts
class IncorrectAnswerFeedback extends StatelessWidget {
  final String correctAnswer;
  final bool showHeartBreak;
  final VoidCallback? onComplete;

  const IncorrectAnswerFeedback({
    super.key,
    required this.correctAnswer,
    this.showHeartBreak = true,
    this.onComplete,
  });

  @override
  Widget build(BuildContext context) {
    // Trigger completion callback
    if (onComplete != null) {
      Future.delayed(const Duration(milliseconds: 800), onComplete);
    }

    return IncorrectAnswerOverlay(
      correctAnswer: correctAnswer,
      showHeartBreak: showHeartBreak,
    );
  }
}

/// Shake effect that can be applied to any widget
class ShakeEffect extends StatelessWidget {
  final Widget child;
  final Duration delay;

  const ShakeEffect({
    super.key,
    required this.child,
    this.delay = Duration.zero,
  });

  @override
  Widget build(BuildContext context) {
    return child.animate().shake(
          delay: delay,
          duration: 400.ms,
          hz: 6,
          offset: const Offset(5, 0),
          rotation: 0,
        );
  }
}
