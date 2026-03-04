import 'package:dio/dio.dart';

/// Service para interactuar con el sistema de progreso de nodos del backend
/// Endpoints alineados con: apps/backend/app/routes/node_progress.py
class NodeProgressApiService {
  final Dio _dio;

  NodeProgressApiService(this._dio);

  /// GET /api/v1/progress/kingdom/{kingdomId}
  /// Obtiene progreso de un reino con todos sus nodos
  Future<Map<String, dynamic>> getKingdomProgress(String kingdomId) async {
    final response = await _dio.get('/api/v1/progress/kingdom/$kingdomId');
    return response.data;
  }

  /// GET /api/v1/progress/node/{nodeId}
  /// Obtiene progreso de un nodo especifico
  Future<Map<String, dynamic>> getNodeProgress(String nodeId) async {
    final response = await _dio.get('/api/v1/progress/node/$nodeId');
    return response.data;
  }

  /// POST /api/v1/progress/node/{nodeId}/complete
  /// Actualiza progreso de nodo despues de completar sesion
  Future<Map<String, dynamic>> completeNode({
    required String nodeId,
    required String kingdomId,
    required double accuracy,
    List<String> questionsAnswered = const [],
  }) async {
    final response = await _dio.post(
      '/api/v1/progress/node/$nodeId/complete',
      data: {
        'kingdom_id': kingdomId,
        'accuracy': accuracy,
        'questions_answered': questionsAnswered,
      },
    );
    return response.data;
  }

  /// Alias para compatibilidad
  Future<Map<String, dynamic>> updateNodeProgress({
    required String nodeId,
    required String kingdomId,
    required double accuracy,
    List<String> questionsAnswered = const [],
  }) async {
    return completeNode(
      nodeId: nodeId,
      kingdomId: kingdomId,
      accuracy: accuracy,
      questionsAnswered: questionsAnswered,
    );
  }

  /// POST /api/v1/progress/node/{nodeId}/unlock
  /// Desbloquea un nodo
  Future<Map<String, dynamic>> unlockNode(String nodeId, String kingdomId) async {
    final response = await _dio.post(
      '/api/v1/progress/node/$nodeId/unlock',
      queryParameters: {'kingdom_id': kingdomId},
    );
    return response.data;
  }

  /// GET /api/v1/progress/node/{nodeId}/can-unlock
  /// Verifica si puede desbloquear un nodo
  Future<Map<String, dynamic>> checkCanUnlockNode(String nodeId) async {
    final response = await _dio.get('/api/v1/progress/node/$nodeId/can-unlock');
    return response.data;
  }

  /// Shortcut que retorna solo el boolean
  Future<bool> canUnlockNode(String nodeId) async {
    final response = await checkCanUnlockNode(nodeId);
    return response['data']?['can_unlock'] ?? response['can_unlock'] ?? false;
  }

  /// GET /api/v1/progress/kingdom/{kingdomId}/can-challenge-boss
  /// Verifica si puede retar al boss del reino
  Future<Map<String, dynamic>> checkCanChallengeBoss(String kingdomId) async {
    final response = await _dio.get('/api/v1/progress/kingdom/$kingdomId/can-challenge-boss');
    return response.data;
  }

  /// Shortcut que retorna solo el boolean
  Future<bool> canChallengeBoss(String kingdomId) async {
    final response = await checkCanChallengeBoss(kingdomId);
    return response['data']?['can_challenge'] ?? response['can_challenge'] ?? false;
  }

  /// POST /api/v1/progress/kingdom/{kingdomId}/diagnostic
  /// Marca el diagnostico del reino como completado
  Future<Map<String, dynamic>> completeDiagnostic({
    required String kingdomId,
    String initialRank = 'E',
  }) async {
    final response = await _dio.post(
      '/api/v1/progress/kingdom/$kingdomId/diagnostic',
      data: {'initial_rank': initialRank},
    );
    return response.data;
  }

  /// GET /api/v1/progress/all
  /// Obtiene progreso de todos los reinos
  Future<Map<String, dynamic>> getAllProgress() async {
    final response = await _dio.get('/api/v1/progress/all');
    return response.data;
  }
}
