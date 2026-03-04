import '../../data/models/shop_response_model.dart';

/// Currency types supported in the shop
enum ShopCurrency { gold, gems }

/// Result of a purchase operation
class PurchaseResult {
  final bool success;
  final String? message;
  final int? newGoldBalance;
  final int? newGemsBalance;
  final String? itemId;
  final int? quantity;
  final DateTime? purchasedAt;

  const PurchaseResult({
    required this.success,
    this.message,
    this.newGoldBalance,
    this.newGemsBalance,
    this.itemId,
    this.quantity,
    this.purchasedAt,
  });

  factory PurchaseResult.fromJson(Map<String, dynamic> json) {
    return PurchaseResult(
      success: json['success'] ?? false,
      message: json['message'],
      newGoldBalance: json['new_gold_balance'] ?? json['gold_balance'],
      newGemsBalance: json['new_gems_balance'] ?? json['gems_balance'],
      itemId: json['item_id'],
      quantity: json['quantity'],
      purchasedAt: json['purchased_at'] != null
          ? DateTime.tryParse(json['purchased_at'])
          : null,
    );
  }
}

/// User balance information
class UserBalance {
  final int gold;
  final int gems;
  final DateTime? lastUpdated;

  const UserBalance({
    required this.gold,
    required this.gems,
    this.lastUpdated,
  });

  factory UserBalance.fromJson(Map<String, dynamic> json) {
    return UserBalance(
      gold: json['gold'] ?? json['balance'] ?? 0,
      gems: json['gems'] ?? 0,
      lastUpdated: json['last_updated'] != null
          ? DateTime.tryParse(json['last_updated'])
          : null,
    );
  }
}

/// Item in user's inventory
class InventoryItem {
  final String id;
  final String itemId;
  final String name;
  final String description;
  final String category;
  final int quantity;
  final bool isEquipped;
  final bool isActive;
  final DateTime? acquiredAt;
  final DateTime? expiresAt;
  final Map<String, dynamic>? metadata;

  const InventoryItem({
    required this.id,
    required this.itemId,
    required this.name,
    required this.description,
    required this.category,
    required this.quantity,
    this.isEquipped = false,
    this.isActive = false,
    this.acquiredAt,
    this.expiresAt,
    this.metadata,
  });

  factory InventoryItem.fromJson(Map<String, dynamic> json) {
    return InventoryItem(
      id: json['id'] ?? json['inventory_id'] ?? '',
      itemId: json['item_id'] ?? '',
      name: json['name'] ?? '',
      description: json['description'] ?? '',
      category: json['category'] ?? 'other',
      quantity: json['quantity'] ?? 1,
      isEquipped: json['is_equipped'] ?? false,
      isActive: json['is_active'] ?? false,
      acquiredAt: json['acquired_at'] != null
          ? DateTime.tryParse(json['acquired_at'])
          : null,
      expiresAt: json['expires_at'] != null
          ? DateTime.tryParse(json['expires_at'])
          : null,
      metadata: json['metadata'],
    );
  }

  /// Check if the item has expired
  bool get isExpired {
    if (expiresAt == null) return false;
    return DateTime.now().isAfter(expiresAt!);
  }

  /// Check if item is a consumable
  bool get isConsumable =>
      category == 'consumable' || category == 'powerup' || category == 'boost';
}

/// Transaction record for shop purchases
class ShopTransaction {
  final String id;
  final String itemId;
  final String itemName;
  final int quantity;
  final int amount;
  final ShopCurrency currency;
  final String transactionType;
  final DateTime createdAt;
  final String? status;

  const ShopTransaction({
    required this.id,
    required this.itemId,
    required this.itemName,
    required this.quantity,
    required this.amount,
    required this.currency,
    required this.transactionType,
    required this.createdAt,
    this.status,
  });

  factory ShopTransaction.fromJson(Map<String, dynamic> json) {
    return ShopTransaction(
      id: json['id'] ?? json['transaction_id'] ?? '',
      itemId: json['item_id'] ?? '',
      itemName: json['item_name'] ?? json['name'] ?? '',
      quantity: json['quantity'] ?? 1,
      amount: json['amount'] ?? json['price'] ?? 0,
      currency: _parseCurrency(json['currency']),
      transactionType: json['transaction_type'] ?? json['type'] ?? 'purchase',
      createdAt: json['created_at'] != null
          ? DateTime.tryParse(json['created_at']) ?? DateTime.now()
          : DateTime.now(),
      status: json['status'],
    );
  }

  static ShopCurrency _parseCurrency(dynamic value) {
    if (value == null) return ShopCurrency.gold;
    final str = value.toString().toLowerCase();
    if (str == 'gems' || str == 'gem') return ShopCurrency.gems;
    return ShopCurrency.gold;
  }
}

/// User inventory response containing all inventory items
class UserInventory {
  final List<InventoryItem> items;
  final int totalItems;

  const UserInventory({
    required this.items,
    this.totalItems = 0,
  });

  factory UserInventory.fromJson(Map<String, dynamic> json) {
    final itemsList = json['items'] ?? json['inventory'] ?? [];
    final items = (itemsList as List)
        .map((i) => InventoryItem.fromJson(i as Map<String, dynamic>))
        .toList();

    return UserInventory(
      items: items,
      totalItems: json['total'] ?? items.length,
    );
  }

  /// Get items by category
  List<InventoryItem> getByCategory(String category) {
    return items.where((item) => item.category == category).toList();
  }

  /// Get active power-ups
  List<InventoryItem> get activePowerUps {
    return items
        .where((item) =>
            item.isActive &&
            (item.category == 'powerup' || item.category == 'boost'))
        .toList();
  }

  /// Check if user has a specific item
  bool hasItem(String itemId) {
    return items.any((item) => item.itemId == itemId && item.quantity > 0);
  }
}

/// Transaction history response
class TransactionHistory {
  final List<ShopTransaction> transactions;
  final int total;
  final int page;
  final int pageSize;

  const TransactionHistory({
    required this.transactions,
    this.total = 0,
    this.page = 1,
    this.pageSize = 20,
  });

  factory TransactionHistory.fromJson(Map<String, dynamic> json) {
    final transactionsList = json['transactions'] ?? json['items'] ?? [];
    final transactions = (transactionsList as List)
        .map((t) => ShopTransaction.fromJson(t as Map<String, dynamic>))
        .toList();

    return TransactionHistory(
      transactions: transactions,
      total: json['total'] ?? transactions.length,
      page: json['page'] ?? 1,
      pageSize: json['page_size'] ?? json['limit'] ?? 20,
    );
  }
}

/// Abstract repository interface for shop operations
/// Following Clean Architecture principles
abstract class ShopRepository {
  /// Get all available shop items
  Future<ShopResponseModel> getShopItems();

  /// Purchase an item from the shop
  ///
  /// [itemId] - The ID of the item to purchase
  /// [quantity] - Number of items to purchase (default: 1)
  /// [currency] - Currency to use for purchase (default: gold)
  ///
  /// Returns [PurchaseResult] with success status and updated balances
  Future<PurchaseResult> purchaseItem({
    required String itemId,
    int quantity = 1,
    ShopCurrency currency = ShopCurrency.gold,
  });

  /// Get user's current balance (gold and gems)
  Future<UserBalance> getBalance();

  /// Get user's inventory items
  ///
  /// [category] - Optional filter by category
  Future<UserInventory> getInventory({String? category});

  /// Get user's transaction history
  ///
  /// [page] - Page number for pagination
  /// [pageSize] - Number of items per page
  Future<TransactionHistory> getTransactionHistory({
    int page = 1,
    int pageSize = 20,
  });

  /// Use/activate a consumable item from inventory
  ///
  /// [inventoryItemId] - The inventory ID of the item to use
  Future<bool> useItem(String inventoryItemId);

  /// Equip/unequip an item
  ///
  /// [inventoryItemId] - The inventory ID of the item
  /// [equip] - True to equip, false to unequip
  Future<bool> equipItem(String inventoryItemId, {bool equip = true});

  // ===== Power-Up Operations =====

  /// Get all available power-ups from the store
  Future<PowerUpsResponseModel> getPowerUps();

  /// Get currently active power-ups for the user
  Future<ActivePowerUpsResponseModel> getActivePowerUps();

  /// Activate a power-up from the user's inventory
  ///
  /// [powerUpId] - The ID of the power-up to activate
  /// Returns activation result with the activated power-up details
  Future<ActivatePowerUpResponseModel> activatePowerUp(String powerUpId);

  /// Purchase a power-up from the store
  ///
  /// [powerUpId] - The ID of the power-up to purchase
  /// [quantity] - Number of power-ups to purchase (default: 1)
  Future<bool> purchasePowerUp(String powerUpId, {int quantity = 1});
}
