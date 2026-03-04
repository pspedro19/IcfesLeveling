import 'package:flutter/material.dart';

/// A modal bottom sheet used to offer the user options to repair a lost streak,
/// specifically when triggered from a context where the streak might still be repairable
/// within a limited time window.
///
/// [daysToRepair] The number of days the streak had accumulated.
/// [goldCost] The cost in gold to repair the streak.
/// [onRepair] Callback to repair the streak using in-game currency (gold).
/// [onRepairWithAd] Callback to repair the streak by watching a rewarded ad.
class StreakRepairModal extends StatelessWidget {
  final int daysToRepair;
  final int goldCost;
  final VoidCallback onRepair;
  final VoidCallback onRepairWithAd;

  const StreakRepairModal({
    super.key,
    required this.daysToRepair,
    required this.goldCost,
    required this.onRepair,
    required this.onRepairWithAd,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(24),
      decoration: const BoxDecoration(
        color: Color(0xFF1A1A1A),
        borderRadius: BorderRadius.vertical(top: Radius.circular(32)),
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          const Icon(Icons.build_circle, color: Colors.blue, size: 64),
          const SizedBox(height: 24),
          const Text(
            "REPARAR RACHA",
            style: TextStyle(color: Colors.white, fontSize: 22, fontWeight: FontWeight.bold, letterSpacing: 2),
          ),
          const SizedBox(height: 12),
          Text(
            "Recupera tu racha de $daysToRepair días antes de que desaparezca para siempre.",
            textAlign: TextAlign.center,
            style: const TextStyle(color: Colors.grey, fontSize: 16),
          ),
          const SizedBox(height: 32),
          
          ElevatedButton.icon(
            onPressed: onRepair,
            icon: const Icon(Icons.monetization_on, color: Colors.yellow),
            label: Text("PAGAR $goldCost ORO"),
            style: ElevatedButton.styleFrom(
              backgroundColor: Colors.amber.shade700,
              foregroundColor: Colors.white,
              minimumSize: const Size(double.infinity, 56),
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
            ),
          ),
          
          const SizedBox(height: 12),

          ElevatedButton.icon(
            onPressed: onRepairWithAd,
            icon: const Icon(Icons.ondemand_video),
            label: const Text("VER ANUNCIO"),
            style: ElevatedButton.styleFrom(
              backgroundColor: Colors.blue.shade700,
              foregroundColor: Colors.white,
              minimumSize: const Size(double.infinity, 56),
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
            ),
          ),

          const SizedBox(height: 12),
          
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text("CANCELAR", style: TextStyle(color: Colors.white24)),
          ),
          
          const SizedBox(height: 20),
        ],
      ),
    );
  }
}
