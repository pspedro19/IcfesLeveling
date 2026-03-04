import '../../../../core/network/api_client.dart';
import '../../../../core/constants/api_constants.dart';
import '../models/shop_response_model.dart';
import '../../domain/repositories/shop_repository.dart';

/// Exception thrown when shop API operations fail
class ShopApiException implements Exception {
  final String message;
  final int? statusCode;
  final String? errorCode;

  ShopApiException(this.message, {this.statusCode, this.errorCode});

  @override
  String toString() => 'ShopApiException: $message (code: $statusCode)';
}

/// Remote data source for shop-related API calls
/// Handles all HTTP communication with the backend shop/economy endpoints
class ShopRemoteDataSource {
  final ApiClient _apiClient;

  ShopRemoteDataSource(this._apiClient);

  // ===== Core Shop Operations =====

  /// Fetch all available shop items
  Future<ShopResponseModel> getShopItems() async {
    try {
      final response = await _apiClient.get(ApiConstants.economyShop);

      if (response.statusCode == 200) {
        final responseData = response.data['data'] ?? response.data;
        return ShopResponseModel.fromJson(responseData);
      } else {
        throw ShopApiException(
          'Failed to load shop items',
          statusCode: response.statusCode,
        );
      }
    } catch (e) {
      if (e is ShopApiException) rethrow;
      throw ShopApiException('Network error while loading shop items: $e');
    }
  }

  /// Purchase an item from the shop
  ///
  /// [itemId] - The ID of the item to purchase
  /// [quantity] - Number of items to purchase
  /// [currency] - Currency type (gold or gems)
  Future<PurchaseResult> purchaseItem({
    required String itemId,
    required int quantity,
    required ShopCurrency currency,
  }) async {
    try {
      final response = await _apiClient.post(
        ApiConstants.economyPurchase,
        data: {
          'item_id': itemId,
          'quantity': quantity,
          'currency': currency.name,
        },
      );

      if (response.statusCode == 200 || response.statusCode == 201) {
        final responseData = response.data['data'] ?? response.data;
        return PurchaseResult(
          success: true,
          message: responseData['message'] ?? 'Purchase successful',
          newGoldBalance: responseData['new_gold_balance'] ??
              responseData['gold_balance'] ??
              responseData['balance'],
          newGemsBalance:
              responseData['new_gems_balance'] ?? responseData['gems_balance'],
          itemId: itemId,
          quantity: quantity,
          purchasedAt: DateTime.now(),
        );
      } else {
        final errorMessage =
            response.data['message'] ?? response.data['error'] ?? 'Purchase failed';
        return PurchaseResult(
          success: false,
          message: errorMessage,
        );
      }
    } catch (e) {
      return PurchaseResult(
        success: false,
        message: 'Network error during purchase: ${e.toString()}',
      );
    }
  }

  /// Get user's current balance
  Future<UserBalance> getBalance() async {
    try {
      final response = await _apiClient.get(ApiConstants.economyBalance);

      if (response.statusCode == 200) {
        final responseData = response.data['data'] ?? response.data;
        return UserBalance.fromJson(responseData);
      } else {
        throw ShopApiException(
          'Failed to fetch balance',
          statusCode: response.statusCode,
        );
      }
    } catch (e) {
      if (e is ShopApiException) rethrow;
      throw ShopApiException('Network error while fetching balance: $e');
    }
  }

  /// Get user's inventory
  ///
  /// [category] - Optional filter by category
  Future<UserInventory> getInventory({String? category}) async {
    try {
      final queryParams = <String, dynamic>{};
      if (category != null && category.isNotEmpty) {
        queryParams['category'] = category;
      }

      final response = await _apiClient.get(
        ApiConstants.economyInventory,
        queryParameters: queryParams.isNotEmpty ? queryParams : null,
      );

      if (response.statusCode == 200) {
        final responseData = response.data['data'] ?? response.data;
        return UserInventory.fromJson(responseData);
      } else {
        throw ShopApiException(
          'Failed to fetch inventory',
          statusCode: response.statusCode,
        );
      }
    } catch (e) {
      if (e is ShopApiException) rethrow;
      throw ShopApiException('Network error while fetching inventory: $e');
    }
  }

  /// Get transaction history
  ///
  /// [page] - Page number for pagination
  /// [pageSize] - Number of items per page
  Future<TransactionHistory> getTransactionHistory({
    int page = 1,
    int pageSize = 20,
  }) async {
    try {
      final response = await _apiClient.get(
        ApiConstants.economyTransactions,
        queryParameters: {
          'page': page,
          'page_size': pageSize,
        },
      );

      if (response.statusCode == 200) {
        final responseData = response.data['data'] ?? response.data;
        return TransactionHistory.fromJson(responseData);
      } else {
        throw ShopApiException(
          'Failed to fetch transaction history',
          statusCode: response.statusCode,
        );
      }
    } catch (e) {
      if (e is ShopApiException) rethrow;
      throw ShopApiException('Network error while fetching transactions: $e');
    }
  }

  /// Use/activate a consumable item
  ///
  /// [inventoryItemId] - The inventory ID of the item to use
  Future<bool> useItem(String inventoryItemId) async {
    try {
      final response = await _apiClient.post(
        ApiConstants.economyUseItem,
        data: {
          'inventory_item_id': inventoryItemId,
        },
      );

      return response.statusCode == 200 || response.statusCode == 201;
    } catch (e) {
      throw ShopApiException('Failed to use item: $e');
    }
  }

  /// Equip or unequip an item
  ///
  /// [inventoryItemId] - The inventory ID of the item
  /// [equip] - True to equip, false to unequip
  Future<bool> equipItem(String inventoryItemId, {bool equip = true}) async {
    try {
      final response = await _apiClient.post(
        ApiConstants.economyEquipItem,
        data: {
          'inventory_item_id': inventoryItemId,
          'equip': equip,
        },
      );

      return response.statusCode == 200 || response.statusCode == 201;
    } catch (e) {
      throw ShopApiException('Failed to ${equip ? 'equip' : 'unequip'} item: $e');
    }
  }

  // ===== Power-Up Operations =====

  /// Fetch all power-ups available in the store
  Future<PowerUpsResponseModel> getPowerUps() async {
    try {
      final response = await _apiClient.get(ApiConstants.storePowerUps);

      if (response.statusCode == 200) {
        final responseData = response.data['data'] ?? response.data;
        return PowerUpsResponseModel.fromJson(responseData);
      } else {
        throw ShopApiException(
          'Failed to load power-ups',
          statusCode: response.statusCode,
        );
      }
    } catch (e) {
      if (e is ShopApiException) rethrow;
      throw ShopApiException('Network error while loading power-ups: $e');
    }
  }

  /// Fetch currently active power-ups for the user
  Future<ActivePowerUpsResponseModel> getActivePowerUps() async {
    try {
      final response = await _apiClient.get(ApiConstants.storePowerUpsActive);

      if (response.statusCode == 200) {
        final responseData = response.data['data'] ?? response.data;
        return ActivePowerUpsResponseModel.fromJson(responseData);
      } else {
        throw ShopApiException(
          'Failed to load active power-ups',
          statusCode: response.statusCode,
        );
      }
    } catch (e) {
      if (e is ShopApiException) rethrow;
      throw ShopApiException('Network error while loading active power-ups: $e');
    }
  }

  /// Activate a power-up from the user's inventory
  Future<ActivatePowerUpResponseModel> activatePowerUp(String powerUpId) async {
    try {
      final response = await _apiClient.post(
        ApiConstants.storePowerUpsActivate,
        data: {'power_up_id': powerUpId},
      );

      if (response.statusCode == 200 || response.statusCode == 201) {
        final responseData = response.data['data'] ?? response.data;
        return ActivatePowerUpResponseModel.fromJson(responseData);
      } else {
        throw ShopApiException(
          response.data['message'] ?? 'Failed to activate power-up',
          statusCode: response.statusCode,
        );
      }
    } catch (e) {
      if (e is ShopApiException) rethrow;
      throw ShopApiException('Failed to activate power-up: $e');
    }
  }

  /// Purchase a power-up from the store
  Future<bool> purchasePowerUp(String powerUpId, {int quantity = 1}) async {
    try {
      final response = await _apiClient.post(
        ApiConstants.economyPurchase,
        data: {
          'item_id': powerUpId,
          'item_type': 'power_up',
          'quantity': quantity,
        },
      );

      if (response.statusCode == 200 || response.statusCode == 201) {
        return response.data['success'] ?? true;
      } else {
        throw ShopApiException(
          response.data['message'] ?? 'Failed to purchase power-up',
          statusCode: response.statusCode,
        );
      }
    } catch (e) {
      if (e is ShopApiException) rethrow;
      throw ShopApiException('Failed to purchase power-up: $e');
    }
  }
}
