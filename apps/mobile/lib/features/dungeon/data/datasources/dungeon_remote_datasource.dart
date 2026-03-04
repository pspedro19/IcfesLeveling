import '../../../../core/network/api_client.dart';
import '../../../../core/constants/api_constants.dart';
import '../models/dungeon_models.dart';

/// Remote data source for dungeon feature
/// Handles all API calls related to dungeons
class DungeonRemoteDataSource {
  final ApiClient _apiClient;

  DungeonRemoteDataSource(this._apiClient);

  /// Fetch all available dungeon gates
  /// Optional filters: gateType (normal, boss, seasonal), difficulty (D, C, B, A, S)
  Future<DungeonGatesResponse> getAvailableGates({
    String? gateType,
    String? difficulty,
  }) async {
    final queryParams = <String, dynamic>{};
    if (gateType != null) queryParams['type'] = gateType;
    if (difficulty != null) queryParams['difficulty'] = difficulty;

    final response = await _apiClient.get(
      ApiConstants.dungeonGates,
      queryParameters: queryParams.isNotEmpty ? queryParams : null,
    );

    if (response.statusCode == 200) {
      final data = response.data;
      // Handle both wrapped and unwrapped responses
      final responseData = data['data'] ?? data;
      return DungeonGatesResponse.fromJson(responseData);
    } else {
      throw DungeonApiException(
        'Failed to fetch dungeon gates',
        statusCode: response.statusCode,
      );
    }
  }

  /// Enter a specific dungeon gate and start a run
  Future<DungeonRunResponse> enterGate(String gateId) async {
    final response = await _apiClient.post(
      '${ApiConstants.dungeonGates}/$gateId/enter',
    );

    if (response.statusCode == 200 || response.statusCode == 201) {
      final data = response.data;
      final responseData = data['data'] ?? data;
      return DungeonRunResponse.fromJson(responseData);
    } else if (response.statusCode == 403) {
      throw DungeonLockedException('Gate is locked or requirements not met');
    } else if (response.statusCode == 409) {
      throw DungeonActiveRunException('You already have an active dungeon run');
    } else {
      throw DungeonApiException(
        'Failed to enter dungeon gate',
        statusCode: response.statusCode,
      );
    }
  }

  /// Get the current active dungeon run
  Future<DungeonRunResponse?> getCurrentRun() async {
    final response = await _apiClient.get(ApiConstants.dungeonCurrentRun);

    if (response.statusCode == 200) {
      final data = response.data;
      if (data == null || data['data'] == null) return null;
      return DungeonRunResponse.fromJson(data['data']);
    } else if (response.statusCode == 404) {
      return null; // No active run
    } else {
      throw DungeonApiException(
        'Failed to fetch current dungeon run',
        statusCode: response.statusCode,
      );
    }
  }

  /// Get questions for a specific encounter
  Future<DungeonEncounterModel> getEncounterQuestions(String encounterId) async {
    final response = await _apiClient.get(
      '${ApiConstants.dungeonEncounters}/$encounterId/questions',
    );

    if (response.statusCode == 200) {
      final data = response.data;
      final responseData = data['data'] ?? data;
      return DungeonEncounterModel.fromJson(responseData);
    } else {
      throw DungeonApiException(
        'Failed to fetch encounter questions',
        statusCode: response.statusCode,
      );
    }
  }

  /// Submit answer for current encounter question
  Future<EncounterResultModel> submitAnswer({
    required String encounterId,
    required String questionId,
    required String answerId,
    int? timeSpentSeconds,
  }) async {
    final response = await _apiClient.post(
      ApiConstants.dungeonSubmitAnswer,
      data: {
        'encounter_id': encounterId,
        'question_id': questionId,
        'answer_id': answerId,
        if (timeSpentSeconds != null) 'time_spent_seconds': timeSpentSeconds,
      },
    );

    if (response.statusCode == 200) {
      final data = response.data;
      final responseData = data['data'] ?? data;
      return EncounterResultModel.fromJson(responseData);
    } else {
      throw DungeonApiException(
        'Failed to submit answer',
        statusCode: response.statusCode,
      );
    }
  }

  /// Submit multiple answers for an encounter (batch submit)
  Future<EncounterResultModel> submitAnswers({
    required String encounterId,
    required List<AnswerSubmission> answers,
  }) async {
    final response = await _apiClient.post(
      '${ApiConstants.dungeonEncounters}/$encounterId/submit',
      data: {
        'answers': answers.map((a) => a.toJson()).toList(),
      },
    );

    if (response.statusCode == 200) {
      final data = response.data;
      final responseData = data['data'] ?? data;
      return EncounterResultModel.fromJson(responseData);
    } else {
      throw DungeonApiException(
        'Failed to submit answers',
        statusCode: response.statusCode,
      );
    }
  }

  /// Complete or abandon a dungeon run
  Future<DungeonCompletionModel> completeRun({
    required String runId,
    bool abandon = false,
  }) async {
    final endpoint = abandon
        ? '${ApiConstants.dungeonRuns}/$runId/abandon'
        : '${ApiConstants.dungeonRuns}/$runId/complete';

    final response = await _apiClient.post(endpoint);

    if (response.statusCode == 200) {
      final data = response.data;
      final responseData = data['data'] ?? data;
      return DungeonCompletionModel.fromJson(responseData);
    } else {
      throw DungeonApiException(
        abandon ? 'Failed to abandon dungeon run' : 'Failed to complete dungeon run',
        statusCode: response.statusCode,
      );
    }
  }

  /// Get dungeon run history
  Future<List<DungeonRunHistoryModel>> getHistory({int limit = 10, int offset = 0}) async {
    final response = await _apiClient.get(
      ApiConstants.dungeonHistory,
      queryParameters: {
        'limit': limit,
        'offset': offset,
      },
    );

    if (response.statusCode == 200) {
      final data = response.data;
      final responseData = data['data'] ?? data;
      final historyList = responseData['runs'] as List? ?? responseData as List? ?? [];
      return historyList.map((h) => DungeonRunHistoryModel.fromJson(h)).toList();
    } else {
      throw DungeonApiException(
        'Failed to fetch dungeon history',
        statusCode: response.statusCode,
      );
    }
  }

  /// Use an item during dungeon run
  Future<void> useItem({
    required String runId,
    required String itemId,
  }) async {
    final response = await _apiClient.post(
      '${ApiConstants.dungeonRuns}/$runId/use-item',
      data: {'item_id': itemId},
    );

    if (response.statusCode != 200) {
      throw DungeonApiException(
        'Failed to use item',
        statusCode: response.statusCode,
      );
    }
  }

  /// Request a hint for current encounter
  Future<String> requestHint({
    required String encounterId,
    required String questionId,
  }) async {
    final response = await _apiClient.post(
      '${ApiConstants.dungeonEncounters}/$encounterId/hint',
      data: {'question_id': questionId},
    );

    if (response.statusCode == 200) {
      final data = response.data;
      return data['data']?['hint'] ?? data['hint'] ?? '';
    } else {
      throw DungeonApiException(
        'Failed to get hint',
        statusCode: response.statusCode,
      );
    }
  }
}

/// Helper class for batch answer submission
class AnswerSubmission {
  final String questionId;
  final String answerId;
  final int? timeSpentSeconds;

  AnswerSubmission({
    required this.questionId,
    required this.answerId,
    this.timeSpentSeconds,
  });

  Map<String, dynamic> toJson() => {
    'question_id': questionId,
    'answer_id': answerId,
    if (timeSpentSeconds != null) 'time_spent_seconds': timeSpentSeconds,
  };
}

/// Base exception for dungeon API errors
class DungeonApiException implements Exception {
  final String message;
  final int? statusCode;

  DungeonApiException(this.message, {this.statusCode});

  @override
  String toString() => 'DungeonApiException: $message (status: $statusCode)';
}

/// Exception when dungeon gate is locked
class DungeonLockedException extends DungeonApiException {
  DungeonLockedException(super.message);
}

/// Exception when user already has an active run
class DungeonActiveRunException extends DungeonApiException {
  DungeonActiveRunException(super.message);
}
