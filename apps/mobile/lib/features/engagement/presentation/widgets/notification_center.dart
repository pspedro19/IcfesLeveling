import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';

class NotificationCenter extends StatelessWidget {
  const NotificationCenter({super.key});

  @override
  Widget build(BuildContext context) {
    final notifications = [
      {"title": "¡Rango Subido!", "message": "Has alcanzado el Rango E en Matemáticas.", "time": "Hace 2m", "type": "rank"},
      {"title": "Misión Completada", "message": "Reclamaste 75 Gold por 'Persistencia'.", "time": "Hace 10m", "type": "mission"},
      {"title": "Liga en Riesgo", "message": "Estás a 2 puestos de la zona de descenso.", "time": "Hace 1h", "type": "alert"},
    ];

    return Container(
      decoration: BoxDecoration(
        color: const Color(0xFF1A1A1A),
        borderRadius: const BorderRadius.vertical(top: Radius.circular(32)),
        border: Border.all(color: Colors.white.withOpacity(0.1)),
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          const SizedBox(height: 12),
          Container(width: 40, height: 4, decoration: BoxDecoration(color: Colors.white24, borderRadius: BorderRadius.circular(2))),
          const SizedBox(height: 20),
          const Padding(
            padding: EdgeInsets.symmetric(horizontal: 24),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text("NOTIFICACIONES", style: TextStyle(color: Colors.white, fontWeight: FontWeight.w900, letterSpacing: 2)),
                Text("Limpiar", style: TextStyle(color: Colors.blue, fontSize: 12, fontWeight: FontWeight.bold)),
              ],
            ),
          ),
          const SizedBox(height: 20),
          Flexible(
            child: ListView.builder(
              shrinkWrap: true,
              padding: const EdgeInsets.symmetric(horizontal: 16),
              itemCount: notifications.length,
              itemBuilder: (context, index) {
                final note = notifications[index];
                return _NotificationItem(
                  title: note["title"]!,
                  message: note["message"]!,
                  time: note["time"]!,
                  type: note["type"]!,
                ).animate().fadeIn(delay: (index * 100).ms).slideY(begin: 0.1, end: 0);
              },
            ),
          ),
          const SizedBox(height: 40),
        ],
      ),
    );
  }
}

class _NotificationItem extends StatelessWidget {
  final String title;
  final String message;
  final String time;
  final String type;

  const _NotificationItem({required this.title, required this.message, required this.time, required this.type});

  @override
  Widget build(BuildContext context) {
    final color = type == 'rank' ? Colors.amber : (type == 'mission' ? Colors.blue : Colors.red);
    final icon = type == 'rank' ? Icons.trending_up : (type == 'mission' ? Icons.emoji_events : Icons.warning);

    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.02),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.white.withOpacity(0.05)),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            padding: const EdgeInsets.all(8),
            decoration: BoxDecoration(color: color.withOpacity(0.1), shape: BoxShape.circle),
            child: Icon(icon, color: color, size: 20),
          ),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(title, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 14)),
                    Text(time, style: const TextStyle(color: Colors.white38, fontSize: 10)),
                  ],
                ),
                const SizedBox(height: 4),
                Text(message, style: const TextStyle(color: Colors.white70, fontSize: 12)),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
