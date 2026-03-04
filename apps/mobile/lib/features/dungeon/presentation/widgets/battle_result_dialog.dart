import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:go_router/go_router.dart';

class BattleResultDialog extends StatelessWidget {
  final bool isVictory;
  final int xpEarned;
  final int goldEarned;

  const BattleResultDialog({
    super.key, 
    required this.isVictory,
    this.xpEarned = 0,
    this.goldEarned = 0,
  });

  @override
  Widget build(BuildContext context) {
    final color = isVictory ? Colors.amber : Colors.red;
    final title = isVictory ? "¡VICTORIA!" : "DERROTA";
    final icon = isVictory ? Icons.emoji_events : Icons.sentiment_very_dissatisfied;

    return Dialog(
      backgroundColor: Colors.transparent,
      child: Container(
        padding: const EdgeInsets.all(32),
        decoration: BoxDecoration(
          color: const Color(0xFF1E293B),
          borderRadius: BorderRadius.circular(24),
          border: Border.all(color: color.withOpacity(0.5), width: 2),
          gradient: LinearGradient(
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
            colors: [
              const Color(0xFF1E293B),
              isVictory ? const Color(0xFF2C1E0A) : const Color(0xFF2C0A0A),
            ],
          ),
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            // Icon Badge
            Container(
              padding: const EdgeInsets.all(20),
              decoration: BoxDecoration(
                color: color.withOpacity(0.2),
                shape: BoxShape.circle,
                boxShadow: [
                  BoxShadow(
                    color: color.withOpacity(0.4),
                    blurRadius: 30,
                    spreadRadius: 5,
                  )
                ],
              ),
              child: Icon(icon, size: 50, color: color),
            ).animate().scale(curve: Curves.elasticOut, duration: 1000.ms),

            const SizedBox(height: 24),
            Text(
              title,
              style: TextStyle(
                color: color,
                fontWeight: FontWeight.w900,
                fontSize: 28,
                letterSpacing: 2,
              ),
            ).animate().fadeIn().slideY(begin: 0.5),

            const SizedBox(height: 32),

            if (isVictory) ...[
              _RewardRow(label: "Experiencia", value: "+$xpEarned XP", icon: Icons.bolt, color: Colors.blue, delay: 200),
              const SizedBox(height: 12),
              _RewardRow(label: "Oro", value: "+$goldEarned", icon: Icons.monetization_on, color: Colors.amber, delay: 400),
            ] else 
              Text(
                "¡No te rindas! Estudia un poco más y vuelve a intentarlo.",
                textAlign: TextAlign.center,
                style: TextStyle(color: Colors.white.withOpacity(0.7)),
              ),

            const SizedBox(height: 40),

            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                onPressed: () => context.pop(),
                style: ElevatedButton.styleFrom(
                  backgroundColor: color,
                  foregroundColor: Colors.black, // High contrast text
                  padding: const EdgeInsets.symmetric(vertical: 16),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                ),
                child: const Text("CONTINUAR", style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _RewardRow extends StatelessWidget {
  final String label;
  final String value;
  final IconData icon;
  final Color color;
  final int delay;

  const _RewardRow({
    required this.label, 
    required this.value, 
    required this.icon, 
    required this.color,
    required this.delay,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.05),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Row(
        children: [
          Icon(icon, color: color, size: 20),
          const SizedBox(width: 12),
          Text(label, style: const TextStyle(color: Colors.white70)),
          const Spacer(),
          Text(
            value, 
            style: TextStyle(color: color, fontWeight: FontWeight.bold, fontSize: 16)
          ),
        ],
      ),
    ).animate().fadeIn(delay: delay.ms).slideX(begin: 0.2);
  }
}
