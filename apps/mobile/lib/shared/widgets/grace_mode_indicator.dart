import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';

/// Indicador visual cuando el usuario esta en Grace Mode
class GraceModeIndicator extends StatelessWidget {
  const GraceModeIndicator({super.key});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [
            Colors.purple.withOpacity(0.3),
            Colors.indigo.withOpacity(0.3),
          ],
        ),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(
          color: Colors.purple.withOpacity(0.5),
          width: 1,
        ),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          const Icon(
            Icons.auto_awesome,
            color: Colors.purple,
            size: 18,
          ).animate(onPlay: (c) => c.repeat()).shimmer(
            duration: 2.seconds,
            color: Colors.white.withOpacity(0.3),
          ),
          const SizedBox(width: 8),
          const Text(
            'MODO GRACIA',
            style: TextStyle(
              color: Colors.purple,
              fontSize: 12,
              fontWeight: FontWeight.bold,
              letterSpacing: 1,
            ),
          ),
        ],
      ),
    );
  }
}
