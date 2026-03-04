import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/network/api_client.dart';
import '../../core/constants/api_constants.dart';

/// State class for user balance (gold and gems)
class BalanceState {
  final int gold;
  final int gems;
  final bool isLoading;
  final String? error;

  const BalanceState({
    required this.gold,
    required this.gems,
    this.isLoading = false,
    this.error,
  });

  factory BalanceState.empty() {
    return const BalanceState(gold: 0, gems: 0);
  }

  BalanceState copyWith({
    int? gold,
    int? gems,
    bool? isLoading,
    String? error,
    bool clearError = false,
  }) {
    return BalanceState(
      gold: gold ?? this.gold,
      gems: gems ?? this.gems,
      isLoading: isLoading ?? this.isLoading,
      error: clearError ? null : (error ?? this.error),
    );
  }

  bool get hasError => error != null;
}

/// Notifier for managing user balance state
class BalanceNotifier extends StateNotifier<AsyncValue<BalanceState>> {
  final ApiClient _apiClient;

  BalanceNotifier(this._apiClient) : super(const AsyncValue.loading()) {
    fetchBalance();
  }

  /// Fetch balance from the backend
  Future<void> fetchBalance() async {
    try {
      final response = await _apiClient.get(ApiConstants.economyBalance);
      if (response.statusCode == 200) {
        final data = response.data;
        // Handle both {gold, gems} and {balance: {gold, gems}} response formats
        final balanceData = data['balance'] ?? data;
        state = AsyncValue.data(BalanceState(
          gold: balanceData['gold'] ?? balanceData['balance'] ?? 0,
          gems: balanceData['gems'] ?? 0,
        ));
      }
    } catch (e) {
      // If we have existing data, keep it; otherwise show error
      if (state.value == null) {
        state = AsyncValue.error(e, StackTrace.current);
      }
    }
  }

  /// Refresh balance - for pull-to-refresh or manual refresh
  Future<void> refresh() async {
    await fetchBalance();
  }

  /// Deduct gold after a purchase (optimistic update)
  void deductGold(int amount) {
    state.whenData((balance) {
      if (balance.gold >= amount) {
        state = AsyncValue.data(balance.copyWith(gold: balance.gold - amount));
      }
    });
  }

  /// Add gold (after earning from quests, achievements, etc.)
  void addGold(int amount) {
    state.whenData((balance) {
      state = AsyncValue.data(balance.copyWith(gold: balance.gold + amount));
    });
  }

  /// Deduct gems after a purchase (optimistic update)
  void deductGems(int amount) {
    state.whenData((balance) {
      if (balance.gems >= amount) {
        state = AsyncValue.data(balance.copyWith(gems: balance.gems - amount));
      }
    });
  }

  /// Add gems
  void addGems(int amount) {
    state.whenData((balance) {
      state = AsyncValue.data(balance.copyWith(gems: balance.gems + amount));
    });
  }

  /// Set balance directly (used when backend returns updated balance)
  void setBalance({int? gold, int? gems}) {
    state.whenData((balance) {
      state = AsyncValue.data(balance.copyWith(
        gold: gold ?? balance.gold,
        gems: gems ?? balance.gems,
      ));
    });
  }
}

/// Main balance provider
final balanceProvider = StateNotifierProvider<BalanceNotifier, AsyncValue<BalanceState>>((ref) {
  final apiClient = ref.watch(apiClientProvider);
  return BalanceNotifier(apiClient);
});

/// Convenience provider for just gold value
final goldProvider = Provider<int>((ref) {
  final balanceState = ref.watch(balanceProvider);
  return balanceState.maybeWhen(
    data: (balance) => balance.gold,
    orElse: () => 0,
  );
});

/// Convenience provider for just gems value
final gemsProvider = Provider<int>((ref) {
  final balanceState = ref.watch(balanceProvider);
  return balanceState.maybeWhen(
    data: (balance) => balance.gems,
    orElse: () => 0,
  );
});
