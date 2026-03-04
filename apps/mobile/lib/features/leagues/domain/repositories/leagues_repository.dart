import '../../data/models/leaderboard_response_model.dart';

abstract class LeaguesRepository {
  Future<LeaderboardResponseModel> getLeaderboard();
}
