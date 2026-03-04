import 'dart:async';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/network/api_client.dart';
import '../../core/constants/api_constants.dart';
import '../../core/providers/offline_queue_provider.dart';
import 'balance_provider.dart';

class HeartsState {
  final int current;
  final int max;
  final Duration? nextRegenIn;
  final int adsWatchedToday;

  const HeartsState({
    required this.current,
    required this.max,
    this.nextRegenIn,
    this.adsWatchedToday = 0,
  });

  factory HeartsState.empty() {
    return const HeartsState(current: 0, max: 5);
  }

  HeartsState copyWith({
    int? current,
    int? max,
    Duration? nextRegenIn,
    int? adsWatchedToday,
  }) {
    return HeartsState(
      current: current ?? this.current,
      max: max ?? this.max,
      nextRegenIn: nextRegenIn ?? this.nextRegenIn,
      adsWatchedToday: adsWatchedToday ?? this.adsWatchedToday,
    );
  }
}

class HeartsNotifier extends StateNotifier<AsyncValue<HeartsState>> {
  final ApiClient _apiClient;
  final Ref _ref;
  Timer? _regenTimer;

  HeartsNotifier(this._apiClient, this._ref) : super(const AsyncValue.loading()) {
    fetchStatus();
  }

  @override
  void dispose() {
    _regenTimer?.cancel();
    super.dispose();
  }

  /// Starts a timer to auto-refresh hearts when regeneration is due
  void _startRegenTimer(Duration nextRegenIn) {
    _regenTimer?.cancel();
    _regenTimer = Timer(nextRegenIn, () {
      fetchStatus();
    });
  }

  Future<void> fetchStatus() async {
    try {
      final response = await _apiClient.get(ApiConstants.heartsStatus);
      if (response.statusCode == 200) {
        final data = response.data;
        final nextRegenIn = data['next_regen_in_seconds'] != null
            ? Duration(seconds: data['next_regen_in_seconds'])
            : null;

        state = AsyncValue.data(HeartsState(
          current: data['current'] ?? 5,
          max: data['max'] ?? 5,
          nextRegenIn: nextRegenIn,
          adsWatchedToday: data['ads_watched'] ?? 0,
        ));

        // Start timer to auto-refresh when regeneration is due
        if (nextRegenIn != null) {
          _startRegenTimer(nextRegenIn);
        }
      }
    } catch (e) {
      // If error, keep existing state or error if null
      if (state.value == null) {
        state = AsyncValue.error(e, StackTrace.current);
      }
    }
  }

  Future<void> useHeart() async {
    // Optimistic update
    state.whenData((value) async {
      if (value.current > 0) {
        state = AsyncValue.data(value.copyWith(current: value.current - 1));

        try {
          await _apiClient.post(ApiConstants.useHeart);
        } catch (e) {
          // Si falla por estar offline, encolar para sincronizar despues
          final queue = _ref.read(offlineQueueProvider);
          await queue.enqueueHeartUse();
        }
      }
    });
  }

  /// Set hearts count directly (used when backend returns updated count)
  void setHearts(int count) {
    state.whenData((value) {
      state = AsyncValue.data(value.copyWith(current: count));
    });
  }

  /// Refill hearts using gold
  /// Returns true if successful, false otherwise
  Future<bool> refillWithGold() async {
    try {
      final response = await _apiClient.post(
        ApiConstants.heartsRefill,
        data: {'method': 'gold'},
      );
      if (response.statusCode == 200) {
        await fetchStatus();

        // Refresh balance after spending gold
        _ref.read(balanceProvider.notifier).refresh();

        // If backend returns new balance, update it directly
        if (response.data['new_balance'] != null) {
          _ref.read(balanceProvider.notifier).setBalance(
            gold: response.data['new_balance']['gold'],
            gems: response.data['new_balance']['gems'],
          );
        }

        return true;
      }
      return false;
    } catch (e) {
      return false;
    }
  }

  /// Refill hearts by watching ad
  Future<bool> refillWithAd() async {
    try {
      final response = await _apiClient.post(
        ApiConstants.heartsRefill,
        data: {'method': 'ad'},
      );
      if (response.statusCode == 200) {
        await fetchStatus();
        return true;
      }
      return false;
    } catch (e) {
      return false;
    }
  }
}

final heartsProvider = StateNotifierProvider<HeartsNotifier, AsyncValue<HeartsState>>((ref) {
  final apiClient = ref.watch(apiClientProvider);
  return HeartsNotifier(apiClient, ref);
});
