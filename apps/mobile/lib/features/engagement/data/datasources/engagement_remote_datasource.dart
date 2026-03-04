import '../../../../core/network/api_client.dart';

class EngagementRemoteDataSource {
  final ApiClient _apiClient;

  EngagementRemoteDataSource(this._apiClient);

  Future<Map<String, dynamic>> getHeartStatus() async {
    final response = await _apiClient.get('/hearts/status');
    return response.data;
  }

  Future<Map<String, dynamic>> getStreakStatus() async {
    final response = await _apiClient.get('/streak/status');
    return response.data;
  }

  Future<void> joinLeague() async {
    await _apiClient.post('/leagues/join');
  }

  Future<List<dynamic>> getMasteryTopics() async {
    final response = await _apiClient.get('/mastery/topics');
    return response.data;
  }
}
