import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';

/// Badge animado que muestra el combo actual
class ComboBadge extends StatelessWidget {
  final int combo;

  const ComboBadge({
    super.key,
    required this.combo,
  });

  @override
  Widget build(BuildContext context) {
    if (combo < 3) return const SizedBox.shrink();

    // Determinar color basado en combo
    Color comboColor;
    String comboText;

    if (combo >= 10) {
      comboColor = Colors.purple;
      comboText = 'IMPARABLE';
    } else if (combo >= 5) {
      comboColor = Colors.orange;
      comboText = 'EN FUEGO';
    } else {
      comboColor = Colors.cyan;
      comboText = 'COMBO';
    }

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [
            comboColor.withOpacity(0.8),
            comboColor.withOpacity(0.5),
          ],
        ),
        borderRadius: BorderRadius.circular(20),
        boxShadow: [
          BoxShadow(
            color: comboColor.withOpacity(0.5),
            blurRadius: 10,
            spreadRadius: 2,
          ),
        ],
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          const Icon(
            Icons.flash_on,
            color: Colors.white,
            size: 20,
          ),
          const SizedBox(width: 4),
          Text(
            '$comboText x$combo',
            style: const TextStyle(
              color: Colors.white,
              fontSize: 14,
              fontWeight: FontWeight.bold,
            ),
          ),
        ],
      ),
    )
        .animate(onPlay: (c) => c.repeat(reverse: true))
        .scale(begin: const Offset(1, 1), end: const Offset(1.05, 1.05), duration: 500.ms);
  }
}
