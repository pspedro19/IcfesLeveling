import 'dart:math';
import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';

import '../lottie_overlay.dart';
import 'xp_counter.dart';

/// LessonCompleteOverlay - Full celebration screen for lesson completion
///
/// Animation timeline (3000ms total):
/// - 0ms: Fade to dark overlay
/// - 200ms: Confetti explosion starts
/// - 500ms: "LECCION COMPLETADA!" bounces in
/// - 1000ms: XP counter starts counting up
/// - 1500ms: Stars appear one by one (500ms each)
/// - 2500ms: Gold counter appears
/// - 3000ms: Sequence complete, ready for user interaction
class LessonCompleteOverlay extends StatefulWidget {
  final int totalXP;
  final int stars; // 0-3
  final int gold;
  final VoidCallback? onComplete;

  const LessonCompleteOverlay({
    super.key,
    required this.totalXP,
    required this.stars,
    required this.gold,
    this.onComplete,
  });

  @override
  State<LessonCompleteOverlay> createState() => _LessonCompleteOverlayState();
}

class _LessonCompleteOverlayState extends State<LessonCompleteOverlay> {
  bool _showContinueButton = false;

  @override
  void initState() {
    super.initState();
    // Show continue button after all animations
    Future.delayed(const Duration(milliseconds: 3000), () {
      if (mounted) {
        setState(() {
          _showContinueButton = true;
        });
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    return Material(
      color: Colors.transparent,
      child: Stack(
        children: [
          // Dark overlay
          _DarkOverlay(),

          // Lottie confetti (full-screen, behind everything else)
          Positioned.fill(
            child: IgnorePointer(
              child: Lottie.asset(
                LottieAssets.confetti,
                fit: BoxFit.cover,
                repeat: false,
                errorBuilder: (_, __, ___) => const SizedBox.shrink(),
              ),
            ),
          ),

          // Programmatic confetti fallback
          _ConfettiExplosion(),

          // Main content
          SafeArea(
            child: Center(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  const Spacer(flex: 2),

                  // Trophy icon
                  _TrophyIcon(),

                  const SizedBox(height: 24),

                  // Title
                  _BounceInTitle(),

                  const SizedBox(height: 32),

                  // XP Counter
                  XPCounter(
                    targetValue: widget.totalXP,
                    delay: const Duration(milliseconds: 1000),
                  ),

                  const SizedBox(height: 24),

                  // Stars
                  _StarsRow(stars: widget.stars),

                  const SizedBox(height: 24),

                  // Gold with Lottie coins
                  if (widget.gold > 0) ...[
                    SizedBox(
                      width: 80,
                      height: 80,
                      child: Lottie.asset(
                        LottieAssets.coins,
                        repeat: false,
                        errorBuilder: (_, __, ___) => const SizedBox.shrink(),
                      ),
                    ),
                    _GoldEarned(gold: widget.gold),
                  ],

                  const Spacer(flex: 1),

                  // Continue button
                  if (_showContinueButton)
                    _ContinueButton(onTap: widget.onComplete),

                  const SizedBox(height: 32),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}

/// Dark semi-transparent overlay
class _DarkOverlay extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Container(
      color: Colors.black,
    )
        .animate()
        .fadeIn(
          duration: 200.ms,
          curve: Curves.easeOut,
        )
        .callback(
          callback: (_) {},
          delay: 200.ms,
        );
  }
}

/// Confetti particle explosion
class _ConfettiExplosion extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Stack(
      children: List.generate(30, (index) {
        final random = Random(index);
        final startX = random.nextDouble() * MediaQuery.of(context).size.width;
        final colors = [
          Colors.amber,
          Colors.green,
          Colors.blue,
          Colors.purple,
          Colors.pink,
          Colors.orange,
        ];
        final color = colors[random.nextInt(colors.length)];
        final size = 8.0 + random.nextDouble() * 12;
        final delay = 200 + random.nextInt(300);
        final fallDuration = 2000 + random.nextInt(1000);

        return Positioned(
          left: startX,
          top: -20,
          child: Container(
            width: size,
            height: size,
            decoration: BoxDecoration(
              color: color,
              borderRadius: random.nextBool()
                  ? BorderRadius.circular(2)
                  : BorderRadius.circular(size / 2),
            ),
          )
              .animate()
              .fadeIn(
                delay: Duration(milliseconds: delay),
                duration: 50.ms,
              )
              .slideY(
                begin: 0,
                end: MediaQuery.of(context).size.height / size,
                delay: Duration(milliseconds: delay),
                duration: Duration(milliseconds: fallDuration),
                curve: Curves.easeIn,
              )
              .rotate(
                begin: 0,
                end: random.nextDouble() * 2 - 1,
                delay: Duration(milliseconds: delay),
                duration: Duration(milliseconds: fallDuration),
              )
              .slideX(
                begin: 0,
                end: (random.nextDouble() - 0.5) * 2,
                delay: Duration(milliseconds: delay),
                duration: Duration(milliseconds: fallDuration),
              ),
        );
      }),
    );
  }
}

/// Trophy icon with glow
class _TrophyIcon extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        shape: BoxShape.circle,
        gradient: RadialGradient(
          colors: [
            Colors.amber.shade400.withOpacity(0.3),
            Colors.amber.shade600.withOpacity(0.1),
            Colors.transparent,
          ],
        ),
      ),
      child: Icon(
        Icons.emoji_events,
        size: 80,
        color: Colors.amber.shade400,
      ),
    )
        .animate()
        .fadeIn(
          delay: 300.ms,
          duration: 200.ms,
        )
        .scale(
          begin: const Offset(0.5, 0.5),
          end: const Offset(1.0, 1.0),
          delay: 300.ms,
          duration: 400.ms,
          curve: Curves.elasticOut,
        )
        .shimmer(
          delay: 600.ms,
          duration: 1000.ms,
          color: Colors.white.withOpacity(0.3),
        );
  }
}

/// Bouncing title text
class _BounceInTitle extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Text(
          'LECCION',
          style: TextStyle(
            fontSize: 32,
            fontWeight: FontWeight.w900,
            color: Colors.white,
            letterSpacing: 4,
            shadows: [
              Shadow(
                color: Colors.amber.withOpacity(0.5),
                blurRadius: 10,
              ),
            ],
          ),
        ),
        Text(
          'COMPLETADA!',
          style: TextStyle(
            fontSize: 36,
            fontWeight: FontWeight.w900,
            color: Colors.amber.shade400,
            letterSpacing: 2,
            shadows: [
              Shadow(
                color: Colors.amber.withOpacity(0.8),
                blurRadius: 15,
              ),
            ],
          ),
        ),
      ],
    )
        .animate()
        .fadeIn(
          delay: 500.ms,
          duration: 200.ms,
        )
        .slideY(
          begin: -0.5,
          end: 0,
          delay: 500.ms,
          duration: 400.ms,
          curve: Curves.bounceOut,
        );
  }
}

/// Stars appearing one by one
class _StarsRow extends StatelessWidget {
  final int stars;

  const _StarsRow({required this.stars});

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.center,
      children: List.generate(3, (index) {
        final isEarned = index < stars;
        final delay = 1500 + (index * 300); // Each star 300ms apart

        return Padding(
          padding: const EdgeInsets.symmetric(horizontal: 8),
          child: _AnimatedStar(
            isEarned: isEarned,
            delay: Duration(milliseconds: delay),
            index: index,
          ),
        );
      }),
    );
  }
}

class _AnimatedStar extends StatelessWidget {
  final bool isEarned;
  final Duration delay;
  final int index;

  const _AnimatedStar({
    required this.isEarned,
    required this.delay,
    required this.index,
  });

  @override
  Widget build(BuildContext context) {
    final baseSize = 50.0;
    // Middle star is slightly larger
    final size = index == 1 ? baseSize * 1.2 : baseSize;

    return Container(
      width: size,
      height: size,
      decoration: BoxDecoration(
        shape: BoxShape.circle,
        boxShadow: isEarned
            ? [
                BoxShadow(
                  color: Colors.amber.withOpacity(0.5),
                  blurRadius: 15,
                  spreadRadius: 2,
                ),
              ]
            : null,
      ),
      child: Icon(
        isEarned ? Icons.star : Icons.star_border,
        size: size,
        color: isEarned ? Colors.amber.shade400 : Colors.grey.shade600,
      ),
    )
        .animate()
        .fadeIn(
          delay: delay,
          duration: 100.ms,
        )
        .scale(
          begin: const Offset(0.0, 0.0),
          end: const Offset(1.0, 1.0),
          delay: delay,
          duration: 300.ms,
          curve: Curves.elasticOut,
        )
        .rotate(
          begin: 0.3,
          end: 0,
          delay: delay,
          duration: 300.ms,
        );
  }
}

/// Gold earned indicator
class _GoldEarned extends StatelessWidget {
  final int gold;

  const _GoldEarned({required this.gold});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 10),
      decoration: BoxDecoration(
        color: Colors.amber.shade700.withOpacity(0.3),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(
          color: Colors.amber.shade400,
          width: 2,
        ),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Container(
            width: 24,
            height: 24,
            decoration: BoxDecoration(
              color: Colors.amber.shade600,
              shape: BoxShape.circle,
              border: Border.all(color: Colors.amber.shade300, width: 2),
            ),
            child: const Center(
              child: Text(
                'G',
                style: TextStyle(
                  color: Colors.white,
                  fontWeight: FontWeight.bold,
                  fontSize: 12,
                ),
              ),
            ),
          ),
          const SizedBox(width: 8),
          Text(
            '+$gold',
            style: TextStyle(
              color: Colors.amber.shade300,
              fontSize: 20,
              fontWeight: FontWeight.bold,
            ),
          ),
        ],
      ),
    )
        .animate()
        .fadeIn(
          delay: 2500.ms,
          duration: 200.ms,
        )
        .slideY(
          begin: 0.5,
          end: 0,
          delay: 2500.ms,
          duration: 300.ms,
          curve: Curves.easeOut,
        );
  }
}

/// Continue button
class _ContinueButton extends StatelessWidget {
  final VoidCallback? onTap;

  const _ContinueButton({this.onTap});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 48, vertical: 16),
        decoration: BoxDecoration(
          gradient: LinearGradient(
            colors: [
              Colors.green.shade400,
              Colors.green.shade600,
            ],
          ),
          borderRadius: BorderRadius.circular(30),
          boxShadow: [
            BoxShadow(
              color: Colors.green.withOpacity(0.4),
              blurRadius: 15,
              spreadRadius: 2,
              offset: const Offset(0, 5),
            ),
          ],
        ),
        child: const Text(
          'CONTINUAR',
          style: TextStyle(
            color: Colors.white,
            fontSize: 18,
            fontWeight: FontWeight.bold,
            letterSpacing: 2,
          ),
        ),
      ),
    )
        .animate()
        .fadeIn(
          duration: 300.ms,
        )
        .slideY(
          begin: 0.5,
          end: 0,
          duration: 300.ms,
          curve: Curves.easeOut,
        )
        .then()
        .shimmer(
          duration: 1500.ms,
          color: Colors.white.withOpacity(0.2),
        )
        .then()
        .animate(
          onPlay: (controller) => controller.repeat(),
        )
        .scale(
          begin: const Offset(1.0, 1.0),
          end: const Offset(1.03, 1.03),
          duration: 800.ms,
        )
        .then()
        .scale(
          begin: const Offset(1.03, 1.03),
          end: const Offset(1.0, 1.0),
          duration: 800.ms,
        );
  }
}
