import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';

/// A small visual indicator (a snowflake icon) that signifies the user's
/// streak is currently protected by a "freeze" item. It features a subtle animation.
class StreakFreezeIndicator extends StatelessWidget {
  const StreakFreezeIndicator({super.key});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(4),
      decoration: BoxDecoration(
        color: Colors.blue.withOpacity(0.2),
        shape: BoxShape.circle,
        border: Border.all(color: Colors.blue.withOpacity(0.5)),
      ),
      child: const Icon(Icons.ac_unit, color: Colors.blueAccent, size: 12),
    ).animate(onPlay: (c) => c.repeat(reverse: true))
     .shimmer(duration: 2.seconds);
  }
}
