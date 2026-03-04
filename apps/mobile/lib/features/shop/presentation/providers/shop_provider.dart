import 'dart:async';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/network/api_client.dart';
import '../../../../shared/providers/balance_provider.dart';
import '../../data/datasources/shop_remote_datasource.dart';
import '../../data/models/shop_response_model.dart';
import '../../domain/repositories/shop_repository.dart';
import '../../data/repositories/shop_repository_impl.dart';

// Data Layer Providers
final shopRemoteDataSourceProvider = Provider((ref) {
  final apiClient = ref.watch(apiClientProvider);
  return ShopRemoteDataSource(apiClient);
});

final shopRepositoryProvider = Provider<ShopRepository>((ref) {
  final remote = ref.watch(shopRemoteDataSourceProvider);
  return ShopRepositoryImpl(remote);
});

// Presentation Layer Entities
class ShopItem {
  final String id;
  final String name;
  final String description;
  final int priceGold;
  final int? priceGems;
  final String category;
  final bool isPowerUp;
  final int? duration;

  ShopItem({
    required this.id,
    required this.name,
    required this.description,
    required this.priceGold,
    this.priceGems,
    required this.category,
    this.isPowerUp = false,
    this.duration,
  });
}

/// Represents a power-up in the user's inventory
class OwnedPowerUp {
  final String id;
  final String name;
  final String type;
  final String description;
  final int quantity;
  final int? duration;

  OwnedPowerUp({
    required this.id,
    required this.name,
    required this.type,
    required this.description,
    required this.quantity,
    this.duration,
  });

  factory OwnedPowerUp.fromModel(PowerUpModel model) {
    return OwnedPowerUp(
      id: model.id,
      name: model.name,
      type: model.type,
      description: model.description,
      quantity: model.quantity,
      duration: model.duration,
    );
  }
}

/// Represents an active power-up with remaining time
class ActivePowerUp {
  final String id;
  final String name;
  final String type;
  final DateTime activatedAt;
  final DateTime expiresAt;
  final double multiplier;

  ActivePowerUp({
    required this.id,
    required this.name,
    required this.type,
    required this.activatedAt,
    required this.expiresAt,
    this.multiplier = 1.0,
  });

  factory ActivePowerUp.fromModel(ActivePowerUpModel model) {
    return ActivePowerUp(
      id: model.id,
      name: model.name,
      type: model.type,
      activatedAt: model.activatedAt,
      expiresAt: model.expiresAt,
      multiplier: model.multiplier,
    );
  }

  bool get isExpired => DateTime.now().isAfter(expiresAt);

  Duration get remainingTime {
    final remaining = expiresAt.difference(DateTime.now());
    return remaining.isNegative ? Duration.zero : remaining;
  }

  double get progressPercent {
    final total = expiresAt.difference(activatedAt).inSeconds;
    final remaining = remainingTime.inSeconds;
    if (total <= 0) return 0;
    return remaining / total;
  }

  String get formattedRemainingTime {
    final duration = remainingTime;
    if (duration.inHours > 0) {
      return '${duration.inHours}h ${duration.inMinutes.remainder(60)}m';
    } else if (duration.inMinutes > 0) {
      return '${duration.inMinutes}m ${duration.inSeconds.remainder(60)}s';
    } else {
      return '${duration.inSeconds}s';
    }
  }
}

class ShopState {
  final List<ShopItem> items;
  final List<String> inventory; // List of item IDs owned
  final bool isLoading;
  final String? error;
  final String? purchaseMessage; // Success/error message for purchases

  // Power-up specific state
  final List<OwnedPowerUp> ownedPowerUps;
  final List<ActivePowerUp> activePowerUps;
  final bool isLoadingPowerUps;
  final bool isActivatingPowerUp;
  final String? powerUpError;
  final String? activationSuccess;

  ShopState({
    this.items = const [],
    this.inventory = const [],
    this.isLoading = false,
    this.error,
    this.purchaseMessage,
    this.ownedPowerUps = const [],
    this.activePowerUps = const [],
    this.isLoadingPowerUps = false,
    this.isActivatingPowerUp = false,
    this.powerUpError,
    this.activationSuccess,
  });

  ShopState copyWith({
    List<ShopItem>? items,
    List<String>? inventory,
    bool? isLoading,
    String? error,
    String? purchaseMessage,
    bool clearError = false,
    bool clearPurchaseMessage = false,
    List<OwnedPowerUp>? ownedPowerUps,
    List<ActivePowerUp>? activePowerUps,
    bool? isLoadingPowerUps,
    bool? isActivatingPowerUp,
    String? powerUpError,
    String? activationSuccess,
    bool clearPowerUpError = false,
    bool clearActivationSuccess = false,
  }) {
    return ShopState(
      items: items ?? this.items,
      inventory: inventory ?? this.inventory,
      isLoading: isLoading ?? this.isLoading,
      error: clearError ? null : (error ?? this.error),
      purchaseMessage: clearPurchaseMessage ? null : (purchaseMessage ?? this.purchaseMessage),
      ownedPowerUps: ownedPowerUps ?? this.ownedPowerUps,
      activePowerUps: activePowerUps ?? this.activePowerUps,
      isLoadingPowerUps: isLoadingPowerUps ?? this.isLoadingPowerUps,
      isActivatingPowerUp: isActivatingPowerUp ?? this.isActivatingPowerUp,
      powerUpError: clearPowerUpError ? null : (powerUpError ?? this.powerUpError),
      activationSuccess: clearActivationSuccess ? null : (activationSuccess ?? this.activationSuccess),
    );
  }

  /// Get shop items that are NOT power-ups (permanent items)
  List<ShopItem> get permanentItems =>
      items.where((item) => !item.isPowerUp && item.category != 'powerup' && item.category != 'consumable').toList();

  /// Get shop items that ARE power-ups/consumables
  List<ShopItem> get consumableItems =>
      items.where((item) => item.isPowerUp || item.category == 'powerup' || item.category == 'consumable').toList();

  /// Check if user has any active power-ups
  bool get hasActivePowerUps => activePowerUps.any((p) => !p.isExpired);

  /// Get active power-ups that haven't expired
  List<ActivePowerUp> get validActivePowerUps =>
      activePowerUps.where((p) => !p.isExpired).toList();
}

class ShopNotifier extends StateNotifier<ShopState> {
  final ShopRepository _shopRepository;
  final Ref _ref;
  Timer? _refreshTimer;

  ShopNotifier(this._shopRepository, this._ref) : super(ShopState()) {
    _initialize();
  }

  Future<void> _initialize() async {
    await fetchShopItems();
    await fetchActivePowerUps();
    await fetchOwnedPowerUps();
    _startRefreshTimer();
  }

  void _startRefreshTimer() {
    _refreshTimer?.cancel();
    // Refresh active power-ups every 30 seconds to update countdown timers
    _refreshTimer = Timer.periodic(const Duration(seconds: 30), (_) {
      _cleanupExpiredPowerUps();
    });
  }

  void _cleanupExpiredPowerUps() {
    final validPowerUps = state.activePowerUps.where((p) => !p.isExpired).toList();
    if (validPowerUps.length != state.activePowerUps.length) {
      state = state.copyWith(activePowerUps: validPowerUps);
    }
  }

  @override
  void dispose() {
    _refreshTimer?.cancel();
    super.dispose();
  }

  Future<void> fetchShopItems() async {
    state = state.copyWith(isLoading: true, clearError: true);
    try {
      final shopData = await _shopRepository.getShopItems();
      final items = shopData.items.map((itemModel) => ShopItem(
        id: itemModel.id,
        name: itemModel.name,
        description: itemModel.description,
        priceGold: itemModel.priceGold,
        priceGems: itemModel.priceGems,
        category: itemModel.category,
        isPowerUp: itemModel.isPowerUp,
        duration: itemModel.duration,
      )).toList();

      // Fetch user inventory
      await _fetchInventory();

      state = state.copyWith(isLoading: false, items: items);
    } catch (e) {
      state = state.copyWith(isLoading: false, error: e.toString());
    }
  }

  Future<void> _fetchInventory() async {
    try {
      final inventoryData = await _shopRepository.getInventory();
      final inventoryIds = inventoryData.items.map((item) => item.itemId).toList();
      state = state.copyWith(inventory: inventoryIds);
    } catch (e) {
      // Silent fail for inventory sync
      print('Failed to fetch inventory: $e');
    }
  }

  /// Fetch all power-ups owned by the user (inventory)
  Future<void> fetchOwnedPowerUps() async {
    state = state.copyWith(isLoadingPowerUps: true, clearPowerUpError: true);
    try {
      final response = await _shopRepository.getPowerUps();
      final powerUps = response.powerUps
          .map((model) => OwnedPowerUp.fromModel(model))
          .where((p) => p.quantity > 0)
          .toList();

      state = state.copyWith(
        isLoadingPowerUps: false,
        ownedPowerUps: powerUps,
      );
    } catch (e) {
      state = state.copyWith(
        isLoadingPowerUps: false,
        powerUpError: 'Error al cargar power-ups: ${e.toString()}',
      );
    }
  }

  /// Fetch currently active power-ups
  Future<void> fetchActivePowerUps() async {
    try {
      final response = await _shopRepository.getActivePowerUps();
      final activePowerUps = response.activePowerUps
          .map((model) => ActivePowerUp.fromModel(model))
          .where((p) => !p.isExpired)
          .toList();

      state = state.copyWith(activePowerUps: activePowerUps);
    } catch (e) {
      print('Failed to fetch active power-ups: $e');
      // Silent fail - don't show error for background refresh
    }
  }

  /// Activate a power-up from inventory
  Future<bool> activatePowerUp(String powerUpId) async {
    // Check if user owns this power-up
    final ownedPowerUp = state.ownedPowerUps.firstWhere(
      (p) => p.id == powerUpId,
      orElse: () => OwnedPowerUp(
        id: '',
        name: '',
        type: '',
        description: '',
        quantity: 0,
      ),
    );

    if (ownedPowerUp.id.isEmpty || ownedPowerUp.quantity <= 0) {
      state = state.copyWith(powerUpError: 'No tienes este power-up');
      return false;
    }

    // Check if same type is already active
    final existingActive = state.activePowerUps.firstWhere(
      (p) => p.type == ownedPowerUp.type && !p.isExpired,
      orElse: () => ActivePowerUp(
        id: '',
        name: '',
        type: '',
        activatedAt: DateTime.now(),
        expiresAt: DateTime.now(),
      ),
    );

    if (existingActive.id.isNotEmpty) {
      state = state.copyWith(
        powerUpError: 'Ya tienes un ${ownedPowerUp.name} activo',
      );
      return false;
    }

    state = state.copyWith(isActivatingPowerUp: true, clearPowerUpError: true, clearActivationSuccess: true);

    try {
      final response = await _shopRepository.activatePowerUp(powerUpId);

      if (response.success && response.activatedPowerUp != null) {
        final newActivePowerUp = ActivePowerUp.fromModel(response.activatedPowerUp!);

        // Update owned power-ups (decrease quantity)
        final updatedOwned = state.ownedPowerUps.map((p) {
          if (p.id == powerUpId) {
            return OwnedPowerUp(
              id: p.id,
              name: p.name,
              type: p.type,
              description: p.description,
              quantity: p.quantity - 1,
              duration: p.duration,
            );
          }
          return p;
        }).where((p) => p.quantity > 0).toList();

        state = state.copyWith(
          isActivatingPowerUp: false,
          activePowerUps: [...state.activePowerUps, newActivePowerUp],
          ownedPowerUps: updatedOwned,
          activationSuccess: '${ownedPowerUp.name} activado!',
        );
        return true;
      } else {
        state = state.copyWith(
          isActivatingPowerUp: false,
          powerUpError: response.message ?? 'Error al activar power-up',
        );
        return false;
      }
    } catch (e) {
      state = state.copyWith(
        isActivatingPowerUp: false,
        powerUpError: 'Error: ${e.toString()}',
      );
      return false;
    }
  }

  /// Purchase a power-up specifically
  Future<bool> purchasePowerUp(String powerUpId, {int quantity = 1}) async {
    final item = state.items.firstWhere(
      (i) => i.id == powerUpId,
      orElse: () => ShopItem(
        id: '',
        name: '',
        description: '',
        priceGold: 0,
        category: 'powerup',
      ),
    );

    // Check balance from balanceProvider
    final balanceState = _ref.read(balanceProvider);
    final currentGold = balanceState.maybeWhen(
      data: (balance) => balance.gold,
      orElse: () => 0,
    );

    final totalCost = item.priceGold * quantity;
    if (totalCost > currentGold) {
      state = state.copyWith(powerUpError: "Monedas insuficientes");
      return false;
    }

    state = state.copyWith(isLoadingPowerUps: true, clearPowerUpError: true);
    try {
      final success = await _shopRepository.purchasePowerUp(powerUpId, quantity: quantity);

      if (success) {
        state = state.copyWith(isLoadingPowerUps: false);

        // Deduct gold
        _ref.read(balanceProvider.notifier).deductGold(totalCost);

        await fetchOwnedPowerUps();
        return true;
      } else {
        state = state.copyWith(
          isLoadingPowerUps: false,
          powerUpError: 'Error al comprar power-up',
        );
        return false;
      }
    } catch (e) {
      state = state.copyWith(
        isLoadingPowerUps: false,
        powerUpError: e.toString(),
      );
      return false;
    }
  }

  /// Clear power-up error message
  void clearPowerUpError() {
    state = state.copyWith(clearPowerUpError: true);
  }

  /// Clear activation success message
  void clearActivationSuccess() {
    state = state.copyWith(clearActivationSuccess: true);
  }

  /// Purchase an item with gold using repository
  Future<bool> purchaseItem(String itemId, {int quantity = 1}) async {
    final item = state.items.firstWhere(
      (i) => i.id == itemId,
      orElse: () => ShopItem(id: '', name: '', description: '', priceGold: 0, category: 'default'),
    );

    if (item.id.isEmpty) {
      state = state.copyWith(error: "Articulo no encontrado");
      return false;
    }

    // Check balance from balanceProvider
    final balanceState = _ref.read(balanceProvider);
    final currentGold = balanceState.maybeWhen(
      data: (balance) => balance.gold,
      orElse: () => 0,
    );

    final totalCost = item.priceGold * quantity;
    if (totalCost > currentGold) {
      state = state.copyWith(error: "Oro insuficiente");
      return false;
    }

    state = state.copyWith(isLoading: true, clearError: true, clearPurchaseMessage: true);

    try {
      final result = await _shopRepository.purchaseItem(
        itemId: itemId,
        quantity: quantity,
        currency: ShopCurrency.gold,
      );

      if (result.success) {
        // Update balance from result or deduct optimistically
        if (result.newGoldBalance != null || result.newGemsBalance != null) {
          _ref.read(balanceProvider.notifier).setBalance(
            gold: result.newGoldBalance,
            gems: result.newGemsBalance,
          );
        } else {
          // Optimistic deduction
          _ref.read(balanceProvider.notifier).deductGold(totalCost);
        }

        // Refresh inventory to show new item
        await _fetchInventory();

        state = state.copyWith(
          isLoading: false,
          purchaseMessage: quantity > 1
              ? '${item.name} x$quantity comprado!'
              : '${item.name} comprado!',
        );

        return true;
      } else {
        state = state.copyWith(
          isLoading: false,
          error: result.message ?? 'Error en la compra',
        );
        return false;
      }
    } catch (e) {
      state = state.copyWith(isLoading: false, error: _formatError(e));
      // Refresh balance to ensure consistency
      _ref.read(balanceProvider.notifier).refresh();
      return false;
    }
  }

  /// Format error message for display
  String _formatError(dynamic error) {
    if (error is ShopApiException) {
      return error.message;
    }
    final errorStr = error.toString();
    if (errorStr.startsWith('Exception: ')) {
      return errorStr.substring(11);
    }
    return errorStr;
  }

  /// Purchase an item with gems using repository
  Future<bool> purchaseItemWithGems(String itemId, {int quantity = 1}) async {
    final item = state.items.firstWhere(
      (i) => i.id == itemId,
      orElse: () => ShopItem(id: '', name: '', description: '', priceGold: 0, category: 'default'),
    );

    if (item.id.isEmpty || item.priceGems == null) {
      state = state.copyWith(error: "Articulo no disponible para gemas");
      return false;
    }

    // Check gems balance
    final balanceState = _ref.read(balanceProvider);
    final currentGems = balanceState.maybeWhen(
      data: (balance) => balance.gems,
      orElse: () => 0,
    );

    final totalCost = item.priceGems! * quantity;
    if (totalCost > currentGems) {
      state = state.copyWith(error: "Gemas insuficientes");
      return false;
    }

    state = state.copyWith(isLoading: true, clearError: true, clearPurchaseMessage: true);

    try {
      final result = await _shopRepository.purchaseItem(
        itemId: itemId,
        quantity: quantity,
        currency: ShopCurrency.gems,
      );

      if (result.success) {
        // Update balance from result or deduct optimistically
        if (result.newGoldBalance != null || result.newGemsBalance != null) {
          _ref.read(balanceProvider.notifier).setBalance(
            gold: result.newGoldBalance,
            gems: result.newGemsBalance,
          );
        } else {
          // Optimistic deduction
          _ref.read(balanceProvider.notifier).deductGems(totalCost);
        }

        // Refresh inventory to show new item
        await _fetchInventory();

        state = state.copyWith(
          isLoading: false,
          purchaseMessage: quantity > 1
              ? '${item.name} x$quantity comprado!'
              : '${item.name} comprado!',
        );

        return true;
      } else {
        state = state.copyWith(
          isLoading: false,
          error: result.message ?? 'Error en la compra',
        );
        return false;
      }
    } catch (e) {
      state = state.copyWith(isLoading: false, error: _formatError(e));
      _ref.read(balanceProvider.notifier).refresh();
      return false;
    }
  }

  /// Clear error message
  void clearError() {
    state = state.copyWith(clearError: true);
  }

  /// Clear purchase message
  void clearPurchaseMessage() {
    state = state.copyWith(clearPurchaseMessage: true);
  }

  /// Refresh shop data
  Future<void> refresh() async {
    await Future.wait([
      fetchShopItems(),
      fetchActivePowerUps(),
      fetchOwnedPowerUps(),
    ]);
    // Also refresh balance
    _ref.read(balanceProvider.notifier).refresh();
  }

  /// Check if user owns an item
  bool ownsItem(String itemId) {
    return state.inventory.contains(itemId);
  }

  /// Get count of an item in inventory
  int getItemCount(String itemId) {
    return state.inventory.where((id) => id == itemId).length;
  }
}

final shopProvider = StateNotifierProvider<ShopNotifier, ShopState>((ref) {
  final repo = ref.watch(shopRepositoryProvider);
  return ShopNotifier(repo, ref);
});

/// Provider for user's gold balance (convenience accessor)
final shopUserGoldProvider = Provider<int>((ref) {
  return ref.watch(goldProvider);
});

/// Provider for user's gems balance (convenience accessor)
final shopUserGemsProvider = Provider<int>((ref) {
  return ref.watch(gemsProvider);
});

// ===== Power-Up Specific Providers =====

/// Provider for active power-ups list
final activePowerUpsProvider = Provider<List<ActivePowerUp>>((ref) {
  return ref.watch(shopProvider).validActivePowerUps;
});

/// Provider for owned power-ups list
final ownedPowerUpsProvider = Provider<List<OwnedPowerUp>>((ref) {
  return ref.watch(shopProvider).ownedPowerUps;
});

/// Provider to check if a specific power-up type is active
final isPowerUpActiveProvider = Provider.family<bool, String>((ref, powerUpType) {
  final activePowerUps = ref.watch(activePowerUpsProvider);
  return activePowerUps.any((p) => p.type == powerUpType && !p.isExpired);
});

/// Provider to check if user has any active XP boost
final hasActiveXpBoostProvider = Provider<bool>((ref) {
  return ref.watch(isPowerUpActiveProvider('xp_boost'));
});

/// Provider to check if user has any active streak freeze
final hasActiveStreakFreezeProvider = Provider<bool>((ref) {
  return ref.watch(isPowerUpActiveProvider('streak_freeze'));
});

/// Provider for power-up loading state
final powerUpLoadingProvider = Provider<bool>((ref) {
  final state = ref.watch(shopProvider);
  return state.isLoadingPowerUps || state.isActivatingPowerUp;
});

/// Provider for current XP multiplier based on active power-ups
final xpMultiplierProvider = Provider<double>((ref) {
  final activePowerUps = ref.watch(activePowerUpsProvider);
  final xpBoosts = activePowerUps.where((p) => p.type == 'xp_boost' && !p.isExpired);
  if (xpBoosts.isEmpty) return 1.0;
  // Return the highest multiplier if multiple boosts are active
  return xpBoosts.map((p) => p.multiplier).reduce((a, b) => a > b ? a : b);
});
