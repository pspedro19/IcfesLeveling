import 'package:flutter/material.dart';
import 'promotion_zone_glow.dart';

class LeaderboardItem extends StatelessWidget {
  final int rank;
  final String name;
  final int xp;
  final bool isUser;
  final RankStatus status;

  const LeaderboardItem({
    super.key,
    required this.rank,
    required this.name,
    required this.xp,
    required this.isUser,
    required this.status,
  });

  @override
  Widget build(BuildContext context) {
    final isTop5 = rank <= 5;
    final statusColor = status == RankStatus.promotion 
        ? Colors.green 
        : (status == RankStatus.relegation ? Colors.red : Colors.grey);

    Widget content = Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      decoration: BoxDecoration(
        color: isUser ? Colors.blue.withOpacity(0.1) : Colors.white.withOpacity(0.01),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: isUser ? Colors.blue.withOpacity(0.5) : Colors.white.withOpacity(0.05)),
      ),
      child: Row(
        children: [
          SizedBox(
            width: 30,
            child: Text(
              "$rank",
              style: TextStyle(
                color: rank <= 3 ? Colors.amber : Colors.white54,
                fontWeight: FontWeight.bold,
                fontSize: 16,
              ),
            ),
          ),
          const SizedBox(width: 12),
          CircleAvatar(
            radius: 18,
            backgroundColor: Colors.grey.shade800,
            child: const Icon(Icons.person, color: Colors.white24, size: 20),
          ),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  name,
                  style: TextStyle(
                    color: isUser ? Colors.white : Colors.white70,
                    fontWeight: isUser ? FontWeight.w900 : FontWeight.bold,
                  ),
                ),
                if (isUser)
                  const Text("TÚ", style: TextStyle(color: Colors.blue, fontSize: 10, fontWeight: FontWeight.bold)),
              ],
            ),
          ),
          Column(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Text(
                "$xp XP",
                style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
              ),
              Container(
                width: 4,
                height: 4,
                decoration: BoxDecoration(color: statusColor, shape: BoxShape.circle),
              ),
            ],
          ),
        ],
      ),
    );

    if (isTop5) {
      return PromotionZoneGlow(
        glowColor: Colors.greenAccent,
        child: content,
      );
    }
    
    return content;
  }
}

enum RankStatus { promotion, stable, relegation }
