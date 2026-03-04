import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';

class MissionCompleteToast extends StatelessWidget {
  final String title;
  final int reward;

  const MissionCompleteToast({super.key, required this.title, required this.reward});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
      decoration: BoxDecoration(
        gradient: LinearGradient(colors: [Colors.blue.shade900, Colors.black]),
        borderRadius: BorderRadius.circular(40),
        border: Border.all(color: Colors.blue.withOpacity(0.5)),
        boxShadow: [
          BoxShadow(color: Colors.blue.withOpacity(0.3), blurRadius: 20, spreadRadius: 2),
        ],
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          const Icon(Icons.celebration, color: Colors.blueAccent, size: 20),
          const SizedBox(width: 12),
          Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                "¡MISIÓN COMPLETADA!",
                style: const TextStyle(color: Colors.blueAccent, fontSize: 10, fontWeight: FontWeight.w900, letterSpacing: 1),
              ),
              Text(
                title,
                style: const TextStyle(color: Colors.white, fontSize: 14, fontWeight: FontWeight.bold),
              ),
            ],
          ),
          const SizedBox(width: 20),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
            decoration: BoxDecoration(color: Colors.white10, borderRadius: BorderRadius.circular(8)),
            child: Row(
              children: [
                const Icon(Icons.monetization_on, color: Colors.yellow, size: 14),
                const SizedBox(width: 4),
                Text("+$reward", style: const TextStyle(color: Colors.yellow, fontWeight: FontWeight.bold, fontSize: 12)),
              ],
            ),
          ),
        ],
      ),
    ).animate().fadeIn().slideY(begin: -0.5, end: 0);
  }
}
