import '../../../../core/network/api_client.dart';
import '../models/leaderboard_response_model.dart';
import '../../../../core/constants/api_constants.dart';

class LeaguesRemoteDataSource {
  final ApiClient _apiClient;

  LeaguesRemoteDataSource(this._apiClient);

  Future<LeaderboardResponseModel> getLeaderboard() async {
    try {
      final response = await _apiClient.get(ApiConstants.leaderboard);

      if (response.statusCode == 200) {
        final responseData = response.data['data'] ?? response.data;
        return LeaderboardResponseModel.fromJson(responseData);
      } else {
        throw Exception('Failed to load leaderboard');
      }
    } catch (e) {
      rethrow;
    }
  }
}
