import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';

/// A banner widget displayed at the top of the screen to alert the user
/// that their daily streak is at risk of being broken. It features a warning icon
/// and encourages the user to practice.
///
/// [streakDays] The current number of days in the user's streak.
/// [onTap] Callback function to be executed when the banner is tapped,
/// typically navigating the user to a practice session.
class StreakAtRiskBanner extends StatelessWidget {
  final int streakDays;
  final VoidCallback onTap;

  const StreakAtRiskBanner({super.key, required this.streakDays, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      child: Container(
        width: double.infinity,
        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
        decoration: BoxDecoration(
          gradient: LinearGradient(
            colors: [Colors.red.shade900.withOpacity(0.8), Colors.red.shade600.withOpacity(0.8)],
          ),
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: Colors.redAccent.withOpacity(0.5)),
        ),
        child: Row(
          children: [
            const Icon(Icons.warning_amber_rounded, color: Colors.white, size: 28)
                .animate(onPlay: (c) => c.repeat(reverse: true))
                .scale(duration: 500.ms),
            const SizedBox(width: 16),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    "¡TU RACHA DE $streakDays DÍAS ESTÁ EN PELIGRO!",
                    style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w900, fontSize: 13),
                  ),
                  const Text(
                    "Practica ahora para no perder tu progreso.",
                    style: TextStyle(color: Colors.white70, fontSize: 12),
                  ),
                ],
              ),
            ),
            const Icon(Icons.chevron_right, color: Colors.white54),
          ],
        ),
      ),
    ).animate().slideY(begin: -1, end: 0).fadeIn();
  }
}
