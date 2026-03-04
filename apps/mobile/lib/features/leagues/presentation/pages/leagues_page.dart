import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../providers/leagues_provider.dart';
import '../widgets/leaderboard_list.dart';

class LeaguesPage extends ConsumerWidget {
  const LeaguesPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(leaguesProvider);
    
    return Scaffold(
      backgroundColor: const Color(0xFF0A0A0A),
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        title: const Text(
          "LIGAS DE CAZADORES",
          style: TextStyle(color: Colors.white, fontWeight: FontWeight.w900, letterSpacing: 2),
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.info_outline, color: Colors.blue),
            onPressed: () {},
          ),
        ],
      ),
      body: Column(
        children: [
          // Current League Header
          _CurrentLeagueHeader(
            leagueName: state.name,
            rankIcon: Icons.shield,
            color: Colors.orangeAccent,
            timeLeft: state.timeLeft,
          ).animate().fadeIn().slideY(begin: -0.1, end: 0),
          
          const SizedBox(height: 20),
          
          // Leaderboard
          Expanded(
            child: Container(
              decoration: BoxDecoration(
                color: Colors.white.withOpacity(0.02),
                borderRadius: const BorderRadius.vertical(top: Radius.circular(32)),
                border: Border.all(color: Colors.white.withOpacity(0.05)),
              ),
              child: const LeaderboardList(),
            ),
          ),
        ],
      ),
    );
  }
}

class _CurrentLeagueHeader extends StatelessWidget {
  final String leagueName;
  final IconData rankIcon;
  final Color color;
  final String timeLeft;

  const _CurrentLeagueHeader({
    required this.leagueName,
    required this.rankIcon,
    required this.color,
    required this.timeLeft,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(24),
      margin: const EdgeInsets.symmetric(horizontal: 16),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [color.withOpacity(0.2), Colors.black],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(24),
        border: Border.all(color: color.withOpacity(0.3)),
      ),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: color.withOpacity(0.1),
              shape: BoxShape.circle,
              boxShadow: [BoxShadow(color: color.withOpacity(0.2), blurRadius: 20)],
            ),
            child: Icon(rankIcon, color: color, size: 40),
          ),
          const SizedBox(width: 20),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  leagueName,
                  style: TextStyle(color: color, fontSize: 20, fontWeight: FontWeight.w900, letterSpacing: 1),
                ),
                const SizedBox(height: 4),
                Text(
                  "Termina en: $timeLeft",
                  style: const TextStyle(color: Colors.white54, fontSize: 12),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
