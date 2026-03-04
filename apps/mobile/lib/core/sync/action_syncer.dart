import 'sync_action.dart';
import '../network/api_client.dart';
import '../constants/api_constants.dart';
import '../utils/sync_logger.dart';

class ActionSyncer {
  final ApiClient _apiClient;

  ActionSyncer(this._apiClient);

  Future<bool> sync(SyncAction action) async {
    try {
      String endpoint = _getEndpoint(action.type);
      final response = await _apiClient.post(
        endpoint,
        data: action.data,
      );

      final success = response.statusCode == 200 || response.statusCode == 201;
      if (success) {
        SyncLogger.log('action_sync_success', data: {'type': action.type.name, 'id': action.id});
      }
      return success;
    } catch (e) {
      SyncLogger.log('action_sync_failed',
        data: {'type': action.type.name, 'id': action.id},
        success: false,
        error: e.toString()
      );
      return false;
    }
  }

  /// Sync action and return the server response for conflict resolution
  Future<dynamic> syncWithResponse(SyncAction action) async {
    String endpoint = _getEndpoint(action.type);
    final response = await _apiClient.post(
      endpoint,
      data: {
        ...action.data,
        'client_timestamp': action.clientTimestamp.toIso8601String(),
      },
    );

    if (response.statusCode == 200 || response.statusCode == 201) {
      SyncLogger.log('action_sync_success', data: {'type': action.type.name, 'id': action.id});
      return response.data;
    }

    throw Exception('Sync failed with status ${response.statusCode}');
  }

  String _getEndpoint(SyncActionType type) {
    switch (type) {
      case SyncActionType.submitAnswer:
        return ApiConstants.submitAnswer;
      case SyncActionType.useHeart:
        return ApiConstants.useHeart;
      case SyncActionType.extendStreak:
        return ApiConstants.extendStreak;
      case SyncActionType.updateState:
        return ApiConstants.syncState;
      case SyncActionType.updateXp:
        return ApiConstants.updateXp;
      case SyncActionType.unlockAchievement:
        return ApiConstants.achievements;
      case SyncActionType.updateMastery:
        return ApiConstants.mastery;
      case SyncActionType.analyticsEvent:
        return ApiConstants.analytics;
    }
  }
}
