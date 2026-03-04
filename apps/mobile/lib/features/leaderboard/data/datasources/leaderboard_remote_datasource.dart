import '../../../../core/network/api_client.dart';
import '../../../../core/constants/api_constants.dart';
import '../models/leaderboard_entry_model.dart';

class LeaderboardRemoteDataSource {
  final ApiClient _apiClient;

  LeaderboardRemoteDataSource(this._apiClient);

  Future<List<LeaderboardEntryModel>> getLeaderboard({int limit = 30}) async {
    final response = await _apiClient.get(
      ApiConstants.leaderboard,
      queryParameters: {'limit': limit},
    );

    if (response.statusCode == 200 && response.data != null) {
      final List data = (response.data as Map)['leaderboard'];
      return data.map((json) => LeaderboardEntryModel.fromJson(json)).toList();
    } else {
      throw Exception('Failed to load leaderboard');
    }
  }
}
