import '../../../../core/network/api_client.dart';
import '../../../../core/constants/api_constants.dart';

class StreakRemoteDataSource {
  final ApiClient _apiClient;

  StreakRemoteDataSource(this._apiClient);

  Future<Map<String, dynamic>> repairStreak(String method) async {
    final response = await _apiClient.post(
      ApiConstants.streakRepair,
      data: {'method': method},
    );

    if (response.statusCode == 200) {
      final responseData = response.data['data'] ?? response.data;
      return responseData;
    } else {
      // In a real app, use a custom exception
      throw Exception('Failed to repair streak');
    }
  }
}
