import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';

class DailyMissionsList extends StatelessWidget {
  const DailyMissionsList({super.key});

  @override
  Widget build(BuildContext context) {
    final missions = [
      {"title": "Cazador Matutino", "desc": "Completa 5 preguntas antes de las 9 AM", "progress": 0.6, "reward": 50},
      {"title": "Maestro del Combo", "desc": "Alcanza un combo de x10", "progress": 0.0, "reward": 100},
      {"title": "Persistencia", "desc": "Practica por 15 minutos seguidos", "progress": 1.0, "reward": 75},
    ];

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          "MISIONES DIARIAS",
          style: TextStyle(color: Colors.blueAccent, fontWeight: FontWeight.bold, letterSpacing: 2, fontSize: 12),
        ).animate().fadeIn(),
        const SizedBox(height: 16),
        ...missions.asMap().entries.map((entry) {
          final index = entry.key;
          final mission = entry.value;
          return _MissionItem(
            title: mission["title"] as String,
            desc: mission["desc"] as String,
            progress: mission["progress"] as double,
            reward: mission["reward"] as int,
          ).animate().fadeIn(delay: (index * 150).ms).slideX(begin: 0.05, end: 0);
        }),
      ],
    );
  }
}

class _MissionItem extends StatelessWidget {
  final String title;
  final String desc;
  final double progress;
  final int reward;

  const _MissionItem({required this.title, required this.desc, required this.progress, required this.reward});

  @override
  Widget build(BuildContext context) {
    final isCompleted = progress >= 1.0;

    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: isCompleted ? Colors.blue.withOpacity(0.05) : Colors.white.withOpacity(0.02),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: isCompleted ? Colors.blue.withOpacity(0.3) : Colors.white.withOpacity(0.05)),
      ),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(8),
            decoration: BoxDecoration(
              color: isCompleted ? Colors.blue : Colors.white10,
              shape: BoxShape.circle,
            ),
            child: Icon(
              isCompleted ? Icons.check : Icons.assignment,
              color: isCompleted ? Colors.white : Colors.white54,
              size: 20,
            ),
          ),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  title,
                  style: TextStyle(
                    color: isCompleted ? Colors.blue : Colors.white,
                    fontWeight: FontWeight.bold,
                    fontSize: 14,
                  ),
                ),
                Text(desc, style: const TextStyle(color: Colors.white54, fontSize: 11)),
                const SizedBox(height: 8),
                ClipRRect(
                  borderRadius: BorderRadius.circular(4),
                  child: LinearProgressIndicator(
                    value: progress,
                    minHeight: 4,
                    backgroundColor: Colors.white.withOpacity(0.05),
                    valueColor: AlwaysStoppedAnimation<Color>(isCompleted ? Colors.blue : Colors.blueGrey),
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(width: 16),
          Column(
            children: [
              const Icon(Icons.monetization_on, color: Colors.yellow, size: 16),
              const SizedBox(height: 4),
              Text(
                "$reward",
                style: const TextStyle(color: Colors.yellow, fontWeight: FontWeight.bold, fontSize: 12),
              ),
            ],
          ),
        ],
      ),
    );
  }
}
