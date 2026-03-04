import 'package:dio/dio.dart';

/// Service para interactuar con el sistema de rachas del backend
/// Endpoints alineados con: apps/backend/app/routes/streak.py
class StreakApiService {
  final Dio _dio;

  StreakApiService(this._dio);

  /// GET /api/v1/streak/status
  /// Obtiene el estado actual de la racha con multiplicador
  Future<Map<String, dynamic>> getStreakStatus() async {
    final response = await _dio.get('/api/v1/streak/status');
    return response.data;
  }

  /// POST /api/v1/streak/extend
  /// Registra XP ganado y extiende la racha si se cumple la meta diaria
  Future<Map<String, dynamic>> extendStreak({
    required int xpEarned,
    DateTime? activityDate,
  }) async {
    final response = await _dio.post(
      '/api/v1/streak/extend',
      data: {
        'xp_earned': xpEarned,
        if (activityDate != null)
          'activity_date': activityDate.toIso8601String().split('T')[0],
      },
    );
    return response.data;
  }

  /// Alias para recordActivity - llama a extend con XP minimo
  Future<Map<String, dynamic>> recordActivity({int xpEarned = 20}) async {
    return extendStreak(xpEarned: xpEarned);
  }

  /// POST /api/v1/streak/freeze
  /// Usa un streak freeze para proteger la racha
  /// method: 'item' (usar existente) o 'gold' (comprar con 200 oro)
  Future<Map<String, dynamic>> useFreeze({String method = 'item'}) async {
    final response = await _dio.post(
      '/api/v1/streak/freeze',
      data: {
        'method': method,
        if (method == 'gold') 'gold_cost': 200,
      },
    );
    return response.data;
  }

  /// Compra un streak freeze con oro (200 gold)
  Future<Map<String, dynamic>> purchaseFreeze() async {
    return useFreeze(method: 'gold');
  }

  /// POST /api/v1/streak/repair
  /// Repara racha perdida dentro de ventana de 24h
  /// method: 'gold' (300 oro) o 'ad' (1 por dia)
  Future<Map<String, dynamic>> repairStreak(String method) async {
    final response = await _dio.post(
      '/api/v1/streak/repair',
      data: {'method': method},
    );
    return response.data;
  }
}
