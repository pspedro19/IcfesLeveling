import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';

/// A visual badge indicating that the user is currently in "Grace Mode"
/// (training mode without earning XP). It features a subtle animation.
class GraceModeBadge extends StatelessWidget {
  const GraceModeBadge({super.key});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: Colors.purple.withOpacity(0.2),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Colors.purple.withOpacity(0.5)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          const Icon(Icons.security, color: Colors.purpleAccent, size: 14),
          const SizedBox(width: 6),
          const Text(
            "MODO ENTRENAMIENTO",
            style: TextStyle(
              color: Colors.purpleAccent,
              fontSize: 10,
              fontWeight: FontWeight.bold,
              letterSpacing: 0.5,
            ),
          ),
        ],
      ),
    ).animate(onPlay: (c) => c.repeat(reverse: true))
     .shimmer(duration: 3.seconds, color: Colors.purpleAccent.withOpacity(0.2));
  }
}
