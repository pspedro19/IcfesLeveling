import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';

class PromotionZoneGlow extends StatelessWidget {
  final Widget child;
  final bool isActive;
  final Color glowColor;

  const PromotionZoneGlow({
    super.key,
    required this.child,
    this.isActive = true,
    this.glowColor = Colors.greenAccent,
  });

  @override
  Widget build(BuildContext context) {
    if (!isActive) return child;

    return Stack(
      children: [
        Positioned.fill(
          child: Container(
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(16),
              boxShadow: [
                BoxShadow(
                  color: glowColor.withOpacity(0.1),
                  blurRadius: 20,
                  spreadRadius: -2,
                ),
              ],
            ),
          ).animate(onPlay: (c) => c.repeat(reverse: true))
           .shimmer(duration: 2.seconds, color: glowColor.withOpacity(0.2)),
        ),
        child,
      ],
    );
  }
}
