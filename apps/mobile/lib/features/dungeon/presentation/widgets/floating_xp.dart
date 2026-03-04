import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';

/// Texto de XP flotante que aparece al ganar puntos
class FloatingXP extends StatelessWidget {
  final int xp;

  const FloatingXP({
    super.key,
    required this.xp,
  });

  @override
  Widget build(BuildContext context) {
    return Text(
      '+$xp XP',
      style: const TextStyle(
        color: Colors.amber,
        fontSize: 24,
        fontWeight: FontWeight.bold,
        shadows: [
          Shadow(
            color: Colors.amber,
            blurRadius: 10,
          ),
        ],
      ),
    )
        .animate()
        .fadeIn(duration: 100.ms)
        .slideY(begin: 0, end: -1, duration: 800.ms, curve: Curves.easeOut)
        .fadeOut(delay: 600.ms, duration: 200.ms);
  }
}
