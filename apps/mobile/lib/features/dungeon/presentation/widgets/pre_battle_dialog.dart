import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:go_router/go_router.dart';
import '../../../../core/config/routes.dart';
import '../../domain/entities/dungeon_node.dart';

class PreBattleDialog extends StatelessWidget {
  final DungeonNode node;

  const PreBattleDialog({super.key, required this.node});

  @override
  Widget build(BuildContext context) {
    return Dialog(
      backgroundColor: Colors.transparent,
      child: Container(
        padding: const EdgeInsets.all(24),
        decoration: BoxDecoration(
          color: const Color(0xFF1E293B),
          borderRadius: BorderRadius.circular(24),
          border: Border.all(color: Colors.white.withOpacity(0.1)),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withOpacity(0.5),
              blurRadius: 20,
              offset: const Offset(0, 10),
            ),
          ],
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            // Enemy Preview
            Container(
              width: 80,
              height: 80,
              decoration: BoxDecoration(
                color: Colors.red.withOpacity(0.1),
                shape: BoxShape.circle,
                border: Border.all(color: Colors.red.withOpacity(0.5), width: 2),
              ),
              child: const Icon(Icons.change_history, size: 40, color: Colors.red),
            ).animate().scale(curve: Curves.elasticOut, duration: 800.ms),

            const SizedBox(height: 16),
            const Text(
              "GUARDIAN GEOMÉTRICO",
              style: TextStyle(
                color: Colors.white,
                fontWeight: FontWeight.bold,
                fontSize: 18,
                letterSpacing: 1,
              ),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 8),
            Text(
              "Nivel 5 • Matemáticas",
              style: TextStyle(color: Colors.white.withOpacity(0.5), fontSize: 14),
            ),

            const SizedBox(height: 24),

            // Loot Preview
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Colors.black.withOpacity(0.2),
                borderRadius: BorderRadius.circular(12),
              ),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                children: [
                  _LootItem(icon: Icons.bolt, color: Colors.amber, label: "150 XP"),
                  _LootItem(icon: Icons.monetization_on, color: Colors.yellow, label: "50 Gold"),
                  _LootItem(icon: Icons.backpack, color: Colors.purple, label: "Item?"),
                ],
              ),
            ),

            const SizedBox(height: 32),

            // Buttons
            Row(
              children: [
                Expanded(
                  child: TextButton(
                    onPressed: () => context.pop(),
                    child: Text("Huir", style: TextStyle(color: Colors.white.withOpacity(0.5))),
                  ),
                ),
                Expanded(
                  flex: 2,
                  child: ElevatedButton(
                    onPressed: () {
                      context.pop(); // Close dialog
                      context.push(AppRoutes.dungeonBattle);
                    },
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.red.shade700,
                      foregroundColor: Colors.white,
                      padding: const EdgeInsets.symmetric(vertical: 16),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(16),
                      ),
                      elevation: 4,
                    ),
                    child: const Text("¡ATACAR!", style: TextStyle(fontWeight: FontWeight.bold, letterSpacing: 1)),
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    ).animate().fadeIn().slideY(begin: 0.2, curve: Curves.easeOut);
  }
}

class _LootItem extends StatelessWidget {
  final IconData icon;
  final Color color;
  final String label;

  const _LootItem({required this.icon, required this.color, required this.label});

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Icon(icon, color: color, size: 20),
        const SizedBox(height: 4),
        Text(
          label,
          style: TextStyle(color: Colors.white.withOpacity(0.8), fontSize: 12, fontWeight: FontWeight.w500),
        ),
      ],
    );
  }
}
