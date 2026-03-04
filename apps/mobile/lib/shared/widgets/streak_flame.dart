import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';

import '../../core/config/animation_config.dart';
import 'lottie_overlay.dart';

/// A widget that visually represents the user's current streak with a flame icon.
/// The size and color of the flame, as well as associated animations, change
/// based on the streak count. It also displays an XP multiplier and indicates
/// if the streak is frozen.
///
/// [count] The current number of days in the streak.
/// [multiplier] The XP multiplier associated with the current streak.
/// [isFrozen] A boolean indicating if the streak is currently protected by a freeze.
class StreakFlame extends StatelessWidget {
  final int count;
  final double multiplier;
  final bool isFrozen;

  const StreakFlame({
    super.key,
    required this.count,
    this.multiplier = 1.0,
    this.isFrozen = false,
  });

  @override
  Widget build(BuildContext context) {
    // Intensity levels based on streak count
    final bool isLarge = count >= 14 && count < 30;
    final bool isEpic = count >= 30;

    final Color flameColor = isFrozen
        ? Colors.blue.shade300
        : (isEpic ? Colors.deepOrangeAccent : (isLarge ? Colors.orangeAccent : Colors.orange));

    return Stack(
      clipBehavior: Clip.none,
      alignment: Alignment.center,
      children: [
        // Lottie fire for epic streaks (>=30 days)
        if (isEpic && !isFrozen)
          Positioned(
            top: -10,
            child: SizedBox(
              width: 60,
              height: 60,
              child: Lottie.asset(
                LottieAssets.fire,
                fit: BoxFit.contain,
                repeat: true,
                errorBuilder: (_, __, ___) => const SizedBox.shrink(),
              ),
            ),
          ),

        // Flame Icon with dynamic animation
        Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(
              isFrozen ? Icons.ac_unit : Icons.local_fire_department,
              color: flameColor,
              size: isEpic ? 42 : (isLarge ? 36 : 28),
            ).animate(onPlay: AnimationConfig.infiniteAnimationsEnabled
                 ? (c) => c.repeat(reverse: true) : null)
             .scale(
               begin: const Offset(1, 1),
               end: Offset(isEpic ? 1.2 : 1.1, isEpic ? 1.3 : 1.15),
               duration: (isEpic ? 600 : 1000).ms,
               curve: Curves.easeInOut
             )
             .shimmer(
               delay: 1.seconds,
               duration: 2.seconds,
               color: isFrozen ? Colors.white54 : (isEpic ? Colors.yellow : Colors.white24)
             ),
            
            Text(
              '$count',
              style: TextStyle(
                color: flameColor,
                fontWeight: FontWeight.w900,
                fontSize: 16,
              ),
            ),
          ],
        ),

        // Multiplier Bubble
        if (multiplier > 1.0 && !isFrozen)
          Positioned(
            top: -10,
            right: -20,
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(10),
                boxShadow: [
                  BoxShadow(color: flameColor.withOpacity(0.5), blurRadius: 10),
                ],
              ),
              child: Text(
                'x${multiplier.toStringAsFixed(1)}',
                style: const TextStyle(
                  color: Colors.black,
                  fontSize: 10,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ).animate(onPlay: AnimationConfig.infiniteAnimationsEnabled
                 ? (c) => c.repeat(reverse: true) : null)
             .moveY(begin: 0, end: -4, duration: 1.seconds),
          ),
          
        // Frozen Overlay
        if (isFrozen)
          const Positioned(
            top: -5,
            right: -5,
            child: Icon(Icons.shield, color: Colors.blue, size: 14),
          ).animate().fadeIn().scale(),
      ],
    );
  }
}
