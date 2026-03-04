import '../../../../core/network/api_client.dart';
import '../../../../core/constants/api_constants.dart';
import '../models/boss_raid_models.dart';

class BossRaidRemoteDataSource {
  final ApiClient _apiClient;

  BossRaidRemoteDataSource(this._apiClient);

  Future<BossRaidStatusModel> getStatus() async {
    final response = await _apiClient.get(ApiConstants.bossRaidStatus);
    if (response.statusCode == 200) {
      return BossRaidStatusModel.fromJson(response.data['data']);
    } else {
      throw Exception('Failed to get boss raid status');
    }
  }

  Future<BossRaidSessionModel> startRaid() async {
    final response = await _apiClient.post(ApiConstants.bossRaidStart);
    if (response.statusCode == 200) {
      return BossRaidSessionModel.fromJson(response.data['data']);
    } else {
      throw Exception('Failed to start boss raid');
    }
  }

  /// Submit an answer during a boss raid battle
  /// Returns response with damage dealt, combo count, and updated boss HP
  Future<BossRaidAnswerResponse> submitAnswer({
    required String sessionId,
    required String questionId,
    required String answerId,
  }) async {
    final response = await _apiClient.post(
      ApiConstants.bossRaidSubmit,
      data: {
        'session_id': sessionId,
        'question_id': questionId,
        'answer_id': answerId,
      },
    );
    if (response.statusCode == 200) {
      return BossRaidAnswerResponse.fromJson(response.data['data']);
    } else {
      throw Exception('Failed to submit boss raid answer');
    }
  }

  Future<BossRaidCompleteResponse> completeRaid(String sessionId) async {
    final response = await _apiClient.post(
      ApiConstants.bossRaidComplete,
      data: {'session_id': sessionId},
    );
    if (response.statusCode == 200) {
      return BossRaidCompleteResponse.fromJson(response.data['data']);
    } else {
      throw Exception('Failed to complete boss raid');
    }
  }
}
