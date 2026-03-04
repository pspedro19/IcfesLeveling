import 'package:flutter/material.dart';
import 'package:lottie/lottie.dart';

// Re-export lottie so consumers only need to import this file
export 'package:lottie/lottie.dart' show Lottie;

/// Asset paths for all Lottie animations in the app.
class LottieAssets {
  const LottieAssets._();

  static const confetti = 'assets/animations/confetti.json';
  static const fire = 'assets/animations/fire.json';
  static const starBurst = 'assets/animations/star_burst.json';
  static const levelUp = 'assets/animations/level_up.json';
  static const correctCheck = 'assets/animations/correct_check.json';
  static const wrongX = 'assets/animations/wrong_x.json';
  static const battleStart = 'assets/animations/battle_start.json';
  static const coins = 'assets/animations/coins.json';
  static const loading = 'assets/animations/loading.json';
}

/// Overlay widget that plays a Lottie animation once and auto-disposes.
///
/// Usage:
/// ```dart
/// showLottieOverlay(context, LottieAssets.confetti);
/// ```
class LottieOverlay extends StatefulWidget {
  final String animationAsset;
  final double size;
  final Duration duration;
  final VoidCallback? onComplete;

  const LottieOverlay({
    super.key,
    required this.animationAsset,
    this.size = 200,
    this.duration = const Duration(milliseconds: 1500),
    this.onComplete,
  });

  @override
  State<LottieOverlay> createState() => _LottieOverlayState();
}

class _LottieOverlayState extends State<LottieOverlay>
    with SingleTickerProviderStateMixin {
  late final AnimationController _controller;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: widget.duration,
    );
    _controller.forward().then((_) {
      if (mounted) {
        widget.onComplete?.call();
      }
    });
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return IgnorePointer(
      child: Center(
        child: Lottie.asset(
          widget.animationAsset,
          controller: _controller,
          width: widget.size,
          height: widget.size,
          fit: BoxFit.contain,
          errorBuilder: (context, error, stackTrace) {
            return const SizedBox.shrink();
          },
        ),
      ),
    );
  }
}

/// Show a Lottie animation as a full-screen overlay that auto-removes.
///
/// Safe to call even if the widget is disposed before the animation completes.
///
/// Example:
/// ```dart
/// showLottieOverlay(context, LottieAssets.confetti, size: 300);
/// ```
void showLottieOverlay(
  BuildContext context,
  String asset, {
  double size = 200,
  Duration duration = const Duration(milliseconds: 1500),
}) {
  late OverlayEntry overlay;
  var removed = false;

  overlay = OverlayEntry(
    builder: (context) => Positioned.fill(
      child: LottieOverlay(
        animationAsset: asset,
        size: size,
        duration: duration,
        onComplete: () {
          if (!removed) {
            removed = true;
            overlay.remove();
          }
        },
      ),
    ),
  );

  Overlay.of(context).insert(overlay);
}

/// Widget that shows a looping Lottie fire animation behind [child]
/// when streak count is >= [minStreak].
class StreakFireLottie extends StatelessWidget {
  final int streakCount;
  final int minStreak;
  final Widget child;

  const StreakFireLottie({
    super.key,
    required this.streakCount,
    this.minStreak = 3,
    required this.child,
  });

  @override
  Widget build(BuildContext context) {
    if (streakCount < minStreak) return child;

    return Stack(
      children: [
        child,
        Positioned(
          bottom: 0,
          left: 0,
          right: 0,
          child: IgnorePointer(
            child: Opacity(
              opacity: (streakCount / 10).clamp(0.3, 0.8),
              child: Lottie.asset(
                LottieAssets.fire,
                height: 60,
                fit: BoxFit.fitWidth,
                repeat: true,
                errorBuilder: (_, __, ___) => const SizedBox.shrink(),
              ),
            ),
          ),
        ),
      ],
    );
  }
}

/// A centered Lottie animation widget for use inside existing layouts.
///
/// Unlike [showLottieOverlay] (which uses the Overlay system), this can be
/// placed directly in a Stack or Column. Wrap with [IgnorePointer] if placed
/// over interactive content.
class LottieInline extends StatelessWidget {
  final String asset;
  final double size;
  final bool repeat;

  const LottieInline({
    super.key,
    required this.asset,
    this.size = 150,
    this.repeat = false,
  });

  @override
  Widget build(BuildContext context) {
    return Lottie.asset(
      asset,
      width: size,
      height: size,
      fit: BoxFit.contain,
      repeat: repeat,
      errorBuilder: (_, __, ___) => const SizedBox.shrink(),
    );
  }
}
