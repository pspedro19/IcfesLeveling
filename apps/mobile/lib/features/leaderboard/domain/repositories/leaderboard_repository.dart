import '../entities/leaderboard_entry.dart';

abstract class LeaderboardRepository {
  Future<List<LeaderboardEntry>> getLeaderboard({int limit = 30});
  Future<List<LeaderboardEntry>> getLeaderboardBySubject(String subjectId, {int limit = 30});
}
