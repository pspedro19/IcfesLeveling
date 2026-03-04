import 'package:dio/dio.dart';

/// Service para interactuar con el sistema de corazones del backend
/// Endpoints alineados con: apps/backend/app/routes/hearts.py
class HeartsApiService {
  final Dio _dio;

  HeartsApiService(this._dio);

  /// GET /api/v1/hearts/status
  /// Obtiene el estado actual de corazones
  Future<Map<String, dynamic>> getHeartStatus() async {
    final response = await _dio.get('/api/v1/hearts/status');
    return response.data;
  }

  /// POST /api/v1/hearts/use
  /// Usa un corazon (por respuesta incorrecta, etc)
  Future<Map<String, dynamic>> useHeart({
    required String reason,
    String? sourceId,
  }) async {
    final response = await _dio.post(
      '/api/v1/hearts/use',
      data: {
        'reason': reason,
        if (sourceId != null) 'source_id': sourceId,
      },
    );
    return response.data;
  }

  /// POST /api/v1/hearts/refill
  /// Recarga corazones con oro (method: 'gold') o anuncio (method: 'ad')
  Future<Map<String, dynamic>> refillHearts(String method) async {
    final response = await _dio.post(
      '/api/v1/hearts/refill',
      data: {'method': method},
    );
    return response.data;
  }

  /// Shortcut: Recarga corazones con oro
  Future<Map<String, dynamic>> rechargeWithGold() async {
    return refillHearts('gold');
  }

  /// Shortcut: Recarga corazon con anuncio
  Future<Map<String, dynamic>> rechargeWithAd() async {
    return refillHearts('ad');
  }

  /// POST /api/v1/hearts/refill-verified
  /// Recarga con verificacion server-side de AdMob
  Future<Map<String, dynamic>> refillWithVerifiedAd({
    required String keyId,
    required String signature,
    required int timestamp,
    String? customData,
  }) async {
    final response = await _dio.post(
      '/api/v1/hearts/refill-verified',
      data: {
        'key_id': keyId,
        'signature': signature,
        'reward_item': 'heart',
        'reward_amount': 1,
        'timestamp': timestamp,
        if (customData != null) 'custom_data': customData,
      },
    );
    return response.data;
  }

  /// GET /api/v1/hearts/grace-status
  /// Obtiene el estado del Grace Mode
  Future<Map<String, dynamic>> getGraceStatus() async {
    final response = await _dio.get('/api/v1/hearts/grace-status');
    return response.data;
  }

  /// POST /api/v1/hearts/enter-grace-mode
  /// Entra en Grace Mode (practica sin recompensas)
  Future<Map<String, dynamic>> enterGraceMode() async {
    final response = await _dio.post('/api/v1/hearts/enter-grace-mode');
    return response.data;
  }

  /// POST /api/v1/hearts/exit-grace-mode
  /// Sale de Grace Mode
  Future<Map<String, dynamic>> exitGraceMode() async {
    final response = await _dio.post('/api/v1/hearts/exit-grace-mode');
    return response.data;
  }
}
