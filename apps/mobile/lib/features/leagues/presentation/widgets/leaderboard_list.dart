import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_animate/flutter_animate.dart';
import '../providers/leagues_provider.dart';
import 'leaderboard_item.dart';

class LeaderboardList extends ConsumerWidget {
  const LeaderboardList({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(leaguesProvider);
    
    if (state.isLoading) {
      return const Center(child: CircularProgressIndicator());
    }
    
    if (state.error != null) {
      return Center(child: Text(state.error!, style: const TextStyle(color: Colors.red)));
    }

    return RefreshIndicator(
      onRefresh: () async {
        await ref.read(leaguesProvider.notifier).fetchLeaderboard();
      },
      color: Colors.orangeAccent,
      backgroundColor: Colors.black,
      child: ListView.builder(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 24),
        itemCount: state.users.length,
        itemBuilder: (context, index) {
          final user = state.users[index];

          RankStatus status;
          switch (user.zone) {
            case 'promotion':
              status = RankStatus.promotion;
              break;
            case 'relegation':
              status = RankStatus.relegation;
              break;
            case 'safe':
            default:
              status = RankStatus.stable;
              break;
          }
          
          return LeaderboardItem(
            rank: user.rank,
            name: user.name,
            xp: user.xp,
            isUser: user.isCurrentUser,
            status: status,
          ).animate().fadeIn(delay: (index * 50).ms).slideX(begin: 0.1, end: 0);
        },
      ),
    );
  }
}
