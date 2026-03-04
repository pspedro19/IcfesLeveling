import 'package:dio/dio.dart';

/// Service para interactuar con el sistema de economia del backend
/// Endpoints alineados con: apps/backend/app/routes/economy.py
class EconomyApiService {
  final Dio _dio;

  EconomyApiService(this._dio);

  /// GET /api/v1/economy/balance
  /// Obtiene el balance de oro y gemas del usuario
  Future<Map<String, dynamic>> getBalance() async {
    final response = await _dio.get('/api/v1/economy/balance');
    return response.data;
  }

  /// Alias para compatibilidad
  Future<Map<String, dynamic>> getEconomyStatus() async {
    return getBalance();
  }

  /// GET /api/v1/economy/shop
  /// Obtiene los items disponibles en la tienda con precios
  Future<Map<String, dynamic>> getShop() async {
    final response = await _dio.get('/api/v1/economy/shop');
    return response.data;
  }

  /// GET /api/v1/economy/items/{itemId}
  /// Obtiene detalles de un item especifico
  Future<Map<String, dynamic>> getItemDetails(String itemId) async {
    final response = await _dio.get('/api/v1/economy/items/$itemId');
    return response.data;
  }

  /// GET /api/v1/economy/prices
  /// Obtiene referencia rapida de precios
  Future<Map<String, dynamic>> getPrices() async {
    final response = await _dio.get('/api/v1/economy/prices');
    return response.data;
  }

  /// POST /api/v1/economy/purchase
  /// Compra un item de la tienda
  Future<Map<String, dynamic>> purchaseItem({
    required String itemId,
    int quantity = 1,
    String currency = 'gold', // 'gold' o 'gems'
  }) async {
    final response = await _dio.post(
      '/api/v1/economy/purchase',
      data: {
        'item_id': itemId,
        'quantity': quantity,
        'currency': currency,
      },
    );
    return response.data;
  }

  /// Shortcut: Gasta oro en un item
  Future<Map<String, dynamic>> spendGold(int amount, String itemId) async {
    return purchaseItem(itemId: itemId, currency: 'gold');
  }

  /// POST /api/v1/economy/earn
  /// Otorga moneda al usuario (recompensas)
  Future<Map<String, dynamic>> earnCurrency({
    required int amount,
    required String source,
    String currencyType = 'gold', // 'gold' o 'gems'
  }) async {
    final response = await _dio.post(
      '/api/v1/economy/earn',
      queryParameters: {
        'amount': amount,
        'source': source,
        'currency_type': currencyType,
      },
    );
    return response.data;
  }

  /// Shortcut: Agrega oro al usuario
  Future<Map<String, dynamic>> addGold(int amount, String source) async {
    return earnCurrency(amount: amount, source: source, currencyType: 'gold');
  }

  /// Shortcut: Agrega gemas al usuario
  Future<Map<String, dynamic>> addGems(int amount, String source) async {
    return earnCurrency(amount: amount, source: source, currencyType: 'gems');
  }
}
