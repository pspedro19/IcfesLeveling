import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/network/api_client.dart';
import '../../core/constants/api_constants.dart';
import '../../core/services/notification_service.dart';
import 'balance_provider.dart';

class StreakState {
  final int current;
  final int longest;
  final double multiplier;
  final int freezesAvailable;
  final bool isAtRisk;
  final bool canRepair;
  final int previousStreak;
  final Duration? repairWindowRemaining;

  const StreakState({
    required this.current,
    required this.longest,
    required this.multiplier,
    required this.freezesAvailable,
    required this.isAtRisk,
    required this.canRepair,
    required this.previousStreak,
    this.repairWindowRemaining,
  });

  factory StreakState.empty() {
    return const StreakState(
      current: 0,
      longest: 0,
      multiplier: 1.0,
      freezesAvailable: 0,
      isAtRisk: false,
      canRepair: false,
      previousStreak: 0,
    );
  }

  factory StreakState.fromJson(Map<String, dynamic> json) {
    return StreakState(
      current: json['current_streak'] ?? 0,
      longest: json['longest_streak'] ?? 0,
      multiplier: (json['multiplier'] ?? 1.0).toDouble(),
      freezesAvailable: json['freezes_available'] ?? 0,
      isAtRisk: json['is_at_risk'] ?? false,
      canRepair: json['can_repair'] ?? false,
      previousStreak: json['previous_streak'] ?? 0,
      repairWindowRemaining: json['repair_seconds_left'] != null
          ? Duration(seconds: json['repair_seconds_left'])
          : null,
    );
  }
}

class StreakNotifier extends StateNotifier<AsyncValue<StreakState>> {
  final ApiClient _apiClient;
  final NotificationService? _notificationService;
  final Ref _ref;

  StreakNotifier(this._apiClient, this._notificationService, this._ref) : super(const AsyncValue.loading()) {
    fetchStatus();
  }

  Future<void> fetchStatus() async {
    try {
      final response = await _apiClient.get(ApiConstants.streakStatus);
      if (response.statusCode == 200 && response.data != null) {
        final data = response.data is Map<String, dynamic>
            ? response.data as Map<String, dynamic>
            : Map<String, dynamic>.from(response.data as Map);
        final streakState = StreakState.fromJson(data);
        state = AsyncValue.data(streakState);

        // Schedule streak reminders if user has an active streak
        if (streakState.current > 0) {
          _scheduleStreakReminders(streakState.current);
        }
      }
    } catch (e) {
      if (state.value == null) {
        state = AsyncValue.error(e, StackTrace.current);
      }
    }
  }

  /// Schedule streak reminder notifications
  void _scheduleStreakReminders(int streakDays) {
    if (_notificationService == null) return;

    try {
      _notificationService!.scheduleStreakReminder(streakDays);
    } catch (e) {
      debugPrint('Failed to schedule streak reminders: $e');
    }
  }

  /// Called after completing a practice session to update reminders
  Future<void> onPracticeCompleted() async {
    // Cancel streak reminders since user has practiced today
    if (_notificationService != null) {
      await _notificationService!.cancelStreakReminders();
    }

    // Refresh streak status
    await fetchStatus();
  }

  /// Repair streak using gold
  /// Returns true if successful, false otherwise
  Future<bool> repairWithGold() async {
    try {
      final response = await _apiClient.post(
        ApiConstants.streakRepair,
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

  /// Repair streak by watching ad
  Future<bool> repairWithAd() async {
    try {
      final response = await _apiClient.post(
        ApiConstants.streakRepair,
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

  /// Use a streak freeze
  Future<bool> useFreeze() async {
    try {
      final response = await _apiClient.post(ApiConstants.streakFreeze);
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

final streakProvider = StateNotifierProvider<StreakNotifier, AsyncValue<StreakState>>((ref) {
  final apiClient = ref.watch(apiClientProvider);

  // Get notification service (may be null if not initialized)
  NotificationService? notificationService;
  try {
    notificationService = ref.watch(notificationServiceProvider);
  } catch (e) {
    // NotificationService not available
    debugPrint('NotificationService not available for StreakNotifier');
  }

  return StreakNotifier(apiClient, notificationService, ref);
});
