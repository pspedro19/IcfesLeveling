import 'package:flutter/foundation.dart';
import 'package:dio/dio.dart';
import 'offline_action_queue.dart';

/// Servicio de Sincronizacion Offline
///
/// Conecta el OfflineActionQueue con los endpoints del backend.
/// Maneja el envio de cada tipo de accion a su endpoint correspondiente.
class OfflineSyncService {
  final Dio _dio;
  final OfflineActionQueue _queue;

  OfflineSyncService(this._dio, this._queue) {
    // Configurar el callback para enviar acciones
    _queue.onSendAction = _sendAction;
  }

  /// Envia una accion al endpoint correspondiente
  Future<bool> _sendAction(PendingAction action) async {
    try {
      switch (action.type) {
        case GameActionType.heartUse:
          return await _sendHeartUse(action);
        case GameActionType.streakUpdate:
          return await _sendStreakUpdate(action);
        case GameActionType.nodeComplete:
          return await _sendNodeComplete(action);
        case GameActionType.nodeUnlock:
          return await _sendNodeUnlock(action);
        case GameActionType.purchaseItem:
          return await _sendPurchase(action);
        case GameActionType.answerSubmission:
          return await _sendAnswerSubmission(action);
        case GameActionType.battleComplete:
          return await _sendBattleComplete(action);
        case GameActionType.xpGain:
          return await _sendXpGain(action);
        case GameActionType.goldTransaction:
          return await _sendGoldTransaction(action);
        case GameActionType.achievementUnlock:
          return await _sendAchievementUnlock(action);
      }
    } catch (e) {
      debugPrint('OfflineSyncService: Error sending ${action.type}: $e');
      return false;
    }
  }

  Future<bool> _sendHeartUse(PendingAction action) async {
    final response = await _dio.post('/api/v1/hearts/use');
    return response.statusCode == 200;
  }

  Future<bool> _sendStreakUpdate(PendingAction action) async {
    final response = await _dio.post(
      '/api/v1/streak/extend',
      data: {
        'xp_earned': action.payload['xp_earned'] ?? 20,
        'activity_date': action.payload['activity_date'],
      },
    );
    return response.statusCode == 200;
  }

  Future<bool> _sendNodeComplete(PendingAction action) async {
    final nodeId = action.payload['node_id'];
    final response = await _dio.post(
      '/api/v1/progress/node/$nodeId/complete',
      data: {
        'kingdom_id': action.payload['kingdom_id'],
        'accuracy': action.payload['accuracy'],
        'questions_answered': action.payload['questions_answered'] ?? [],
      },
    );
    return response.statusCode == 200;
  }

  Future<bool> _sendNodeUnlock(PendingAction action) async {
    final nodeId = action.payload['node_id'];
    final response = await _dio.post(
      '/api/v1/progress/node/$nodeId/unlock',
      queryParameters: {'kingdom_id': action.payload['kingdom_id']},
    );
    return response.statusCode == 200;
  }

  Future<bool> _sendPurchase(PendingAction action) async {
    final response = await _dio.post(
      '/api/v1/economy/purchase',
      data: {
        'item_id': action.payload['item_id'],
        'quantity': action.payload['quantity'] ?? 1,
        'currency': action.payload['currency'] ?? 'gold',
      },
    );
    return response.statusCode == 200;
  }

  Future<bool> _sendAnswerSubmission(PendingAction action) async {
    final response = await _dio.post(
      '/api/v1/answers/submit',
      data: {
        'encounter_id': action.payload['encounter_id'],
        'question_id': action.payload['question_id'],
        'answer_id': action.payload['answer_id'],
        'time_spent_seconds': action.payload['time_spent_seconds'],
      },
    );
    return response.statusCode == 200;
  }

  Future<bool> _sendBattleComplete(PendingAction action) async {
    final response = await _dio.post(
      '/api/v1/battles/complete',
      data: {
        'run_id': action.payload['run_id'],
        'victory': action.payload['victory'],
        'xp_earned': action.payload['xp_earned'],
        'gold_earned': action.payload['gold_earned'],
        'stars_earned': action.payload['stars_earned'],
      },
    );
    return response.statusCode == 200;
  }

  Future<bool> _sendXpGain(PendingAction action) async {
    final response = await _dio.post(
      '/api/v1/streak/extend',
      data: {
        'xp_earned': action.payload['amount'] ?? 0,
      },
    );
    return response.statusCode == 200;
  }

  Future<bool> _sendGoldTransaction(PendingAction action) async {
    final response = await _dio.post(
      '/api/v1/economy/earn',
      queryParameters: {
        'amount': action.payload['amount'],
        'source': action.payload['source'] ?? 'offline_sync',
        'currency_type': 'gold',
      },
    );
    return response.statusCode == 200;
  }

  Future<bool> _sendAchievementUnlock(PendingAction action) async {
    final response = await _dio.post(
      '/api/v1/achievements/unlock',
      data: {
        'achievement_id': action.payload['achievement_id'],
      },
    );
    return response.statusCode == 200;
  }

  /// Fuerza sincronizacion manual
  Future<void> forceSync() async {
    await _queue.syncPendingActions();
  }
}
