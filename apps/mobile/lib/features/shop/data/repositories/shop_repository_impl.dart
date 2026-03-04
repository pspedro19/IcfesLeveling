import '../../domain/repositories/shop_repository.dart';
import '../datasources/shop_remote_datasource.dart';
import '../models/shop_response_model.dart';

/// Implementation of ShopRepository that delegates to remote data source
/// Handles error handling and data transformation between layers
class ShopRepositoryImpl implements ShopRepository {
  final ShopRemoteDataSource remoteDataSource;

  ShopRepositoryImpl(this.remoteDataSource);

  // ===== Core Shop Operations =====

  @override
  Future<ShopResponseModel> getShopItems() async {
    try {
      return await remoteDataSource.getShopItems();
    } on ShopApiException {
      rethrow;
    } catch (e) {
      throw ShopApiException('Failed to get shop items: $e');
    }
  }

  @override
  Future<PurchaseResult> purchaseItem({
    required String itemId,
    int quantity = 1,
    ShopCurrency currency = ShopCurrency.gold,
  }) async {
    try {
      return await remoteDataSource.purchaseItem(
        itemId: itemId,
        quantity: quantity,
        currency: currency,
      );
    } on ShopApiException {
      rethrow;
    } catch (e) {
      return PurchaseResult(
        success: false,
        message: 'Unexpected error during purchase: $e',
      );
    }
  }

  @override
  Future<UserBalance> getBalance() async {
    try {
      return await remoteDataSource.getBalance();
    } on ShopApiException {
      rethrow;
    } catch (e) {
      throw ShopApiException('Failed to get balance: $e');
    }
  }

  @override
  Future<UserInventory> getInventory({String? category}) async {
    try {
      return await remoteDataSource.getInventory(category: category);
    } on ShopApiException {
      rethrow;
    } catch (e) {
      throw ShopApiException('Failed to get inventory: $e');
    }
  }

  @override
  Future<TransactionHistory> getTransactionHistory({
    int page = 1,
    int pageSize = 20,
  }) async {
    try {
      return await remoteDataSource.getTransactionHistory(
        page: page,
        pageSize: pageSize,
      );
    } on ShopApiException {
      rethrow;
    } catch (e) {
      throw ShopApiException('Failed to get transaction history: $e');
    }
  }

  @override
  Future<bool> useItem(String inventoryItemId) async {
    try {
      return await remoteDataSource.useItem(inventoryItemId);
    } on ShopApiException {
      rethrow;
    } catch (e) {
      throw ShopApiException('Failed to use item: $e');
    }
  }

  @override
  Future<bool> equipItem(String inventoryItemId, {bool equip = true}) async {
    try {
      return await remoteDataSource.equipItem(inventoryItemId, equip: equip);
    } on ShopApiException {
      rethrow;
    } catch (e) {
      throw ShopApiException('Failed to ${equip ? 'equip' : 'unequip'} item: $e');
    }
  }

  // ===== Power-Up Operations =====

  @override
  Future<PowerUpsResponseModel> getPowerUps() async {
    try {
      return await remoteDataSource.getPowerUps();
    } on ShopApiException {
      rethrow;
    } catch (e) {
      throw ShopApiException('Failed to get power-ups: $e');
    }
  }

  @override
  Future<ActivePowerUpsResponseModel> getActivePowerUps() async {
    try {
      return await remoteDataSource.getActivePowerUps();
    } on ShopApiException {
      rethrow;
    } catch (e) {
      throw ShopApiException('Failed to get active power-ups: $e');
    }
  }

  @override
  Future<ActivatePowerUpResponseModel> activatePowerUp(String powerUpId) async {
    try {
      return await remoteDataSource.activatePowerUp(powerUpId);
    } on ShopApiException {
      rethrow;
    } catch (e) {
      throw ShopApiException('Failed to activate power-up: $e');
    }
  }

  @override
  Future<bool> purchasePowerUp(String powerUpId, {int quantity = 1}) async {
    try {
      return await remoteDataSource.purchasePowerUp(powerUpId, quantity: quantity);
    } on ShopApiException {
      rethrow;
    } catch (e) {
      throw ShopApiException('Failed to purchase power-up: $e');
    }
  }
}
