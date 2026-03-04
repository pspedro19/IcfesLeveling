import 'package:flutter/material.dart';

/// A modal bottom sheet displayed when the user's daily streak is lost.
/// It offers options to repair the streak using gold or by watching an advertisement,
/// or to simply acknowledge the loss and start a new streak.
///
/// [lostStreak] The number of days the streak had accumulated before being lost.
/// [onRepair] Callback to repair the streak using in-game currency (gold).
/// [onRepairWithAd] Callback to repair the streak by watching a rewarded ad.
/// [onRestart] Callback to acknowledge the loss and begin a new streak.
class StreakLostModal extends StatelessWidget {
  final int lostStreak;
  final VoidCallback onRepair;
  final VoidCallback onRepairWithAd;
  final VoidCallback onRestart;

  const StreakLostModal({
    super.key,
    required this.lostStreak,
    required this.onRepair,
    required this.onRepairWithAd,
    required this.onRestart,
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
          const Icon(Icons.local_fire_department, color: Colors.grey, size: 80),
          const SizedBox(height: 24),
          const Text(
            "RACHA PERDIDA",
            style: TextStyle(color: Colors.white, fontSize: 24, fontWeight: FontWeight.w900, letterSpacing: 2),
          ),
          const SizedBox(height: 12),
          Text(
            "Tu llama de $lostStreak días se ha apagado. Pero un verdadero cazador siempre puede reponerse.",
            textAlign: TextAlign.center,
            style: const TextStyle(color: Colors.grey, fontSize: 16),
          ),
          const SizedBox(height: 32),
          
          ElevatedButton(
            onPressed: onRepair,
            style: ElevatedButton.styleFrom(
              backgroundColor: Colors.amber.shade700,
              foregroundColor: Colors.white,
              minimumSize: const Size(double.infinity, 56),
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
            ),
            child: const Text("REPARAR RACHA (300 ORO)", style: TextStyle(fontWeight: FontWeight.bold)),
          ),
          
          const SizedBox(height: 12),

          ElevatedButton(
            onPressed: onRepairWithAd,
            style: ElevatedButton.styleFrom(
              backgroundColor: Colors.blue.shade700,
              foregroundColor: Colors.white,
              minimumSize: const Size(double.infinity, 56),
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
            ),
            child: const Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(Icons.ondemand_video),
                SizedBox(width: 8),
                Text("REPARAR CON ANUNCIO", style: TextStyle(fontWeight: FontWeight.bold)),
              ],
            ),
          ),
          
          const SizedBox(height: 12),
          
          OutlinedButton(
            onPressed: onRestart,
            style: OutlinedButton.styleFrom(
              foregroundColor: Colors.white38,
              side: const BorderSide(color: Colors.white10),
              minimumSize: const Size(double.infinity, 56),
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
            ),
            child: const Text("EMPEZAR DE NUEVO"),
          ),
          
          const SizedBox(height: 20),
        ],
      ),
    );
  }
}
