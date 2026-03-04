import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/network/api_client.dart';
import '../../../../core/constants/api_constants.dart';
import '../../../../shared/providers/balance_provider.dart';

/// State class for engagement data (XP focused)
class EngagementState {
  final int totalXp;
  final int dailyXp; // Track daily progress separately if needed
  final DateTime? lastActivityDate;
  final int hearts; // Current hearts count
  final int maxHearts; // Maximum hearts (usually 5)
  final bool isPremium; // If user has premium (unlimited hearts)
  final DateTime? nextHeartAt; // When next heart regenerates
  final bool graceModeActive; // If grace mode is active
  final int streak;
  final bool streakJustLost;
  final int previousStreak;
  final String? error; // Error message for user feedback
  final bool isLoading; // Loading state for async operations

  // Psychological triggers data
  final int level;
  final int xpForNextLevel;
  final int? leaguePosition;
  final String? leagueName;
  final int percentile;
  final int usersAhead;
  final int achievementCount;
  final double averageMastery;

  const EngagementState({
    this.totalXp = 0,
    this.dailyXp = 0,
    this.lastActivityDate,
    this.hearts = 5,
    this.maxHearts = 5,
    this.isPremium = false,
    this.nextHeartAt,
    this.graceModeActive = false,
    this.streak = 0,
    this.streakJustLost = false,
    this.previousStreak = 0,
    this.error,
    this.isLoading = false,
    this.level = 1,
    this.xpForNextLevel = 100,
    this.leaguePosition,
    this.leagueName,
    this.percentile = 50,
    this.usersAhead = 0,
    this.achievementCount = 0,
    this.averageMastery = 0.0,
  });

  EngagementState copyWith({
    int? totalXp,
    int? dailyXp,
    DateTime? lastActivityDate,
    int? hearts,
    int? maxHearts,
    bool? isPremium,
    DateTime? nextHeartAt,
    bool? graceModeActive,
    int? streak,
    bool? streakJustLost,
    int? previousStreak,
    String? error,
    bool? isLoading,
    bool clearError = false,
    int? level,
    int? xpForNextLevel,
    int? leaguePosition,
    String? leagueName,
    int? percentile,
    int? usersAhead,
    int? achievementCount,
    double? averageMastery,
  }) {
    return EngagementState(
      totalXp: totalXp ?? this.totalXp,
      dailyXp: dailyXp ?? this.dailyXp,
      lastActivityDate: lastActivityDate ?? this.lastActivityDate,
      hearts: hearts ?? this.hearts,
      maxHearts: maxHearts ?? this.maxHearts,
      isPremium: isPremium ?? this.isPremium,
      nextHeartAt: nextHeartAt ?? this.nextHeartAt,
      graceModeActive: graceModeActive ?? this.graceModeActive,
      streak: streak ?? this.streak,
      streakJustLost: streakJustLost ?? this.streakJustLost,
      previousStreak: previousStreak ?? this.previousStreak,
      error: clearError ? null : (error ?? this.error),
      isLoading: isLoading ?? this.isLoading,
      level: level ?? this.level,
      xpForNextLevel: xpForNextLevel ?? this.xpForNextLevel,
      leaguePosition: leaguePosition ?? this.leaguePosition,
      leagueName: leagueName ?? this.leagueName,
      percentile: percentile ?? this.percentile,
      usersAhead: usersAhead ?? this.usersAhead,
      achievementCount: achievementCount ?? this.achievementCount,
      averageMastery: averageMastery ?? this.averageMastery,
    );
  }

  /// Clear error state
  void clearError() {}

  /// Check if there's an active error
  bool get hasError => error != null;

  /// Get gold from balance provider (deprecated - use balanceProvider directly)
  @Deprecated('Use balanceProvider instead for gold')
  int get gold => 0;
}

/// Notifier for managing engagement XP state
class EngagementNotifier extends StateNotifier<EngagementState> {
  final ApiClient _apiClient;
  final Ref _ref;

  EngagementNotifier(this._apiClient, this._ref) : super(const EngagementState()) {
    fetchXp();
  }

  Future<void> fetchXp() async {
    state = state.copyWith(isLoading: true, clearError: true);
    try {
      final response = await _apiClient.get(ApiConstants.authMe);
      if (response.statusCode == 200 && response.data != null) {
        final data = response.data;
        final xp = data['xp'] ?? 0;
        final level = _calculateLevel(xp);
        final xpForNext = _calculateXpForNextLevel(level);

        state = state.copyWith(
          totalXp: xp,
          dailyXp: data['daily_xp'] ?? 0,
          level: level,
          xpForNextLevel: xpForNext,
          leaguePosition: data['league_position'],
          leagueName: data['league_name'],
          percentile: data['percentile'] ?? 50,
          usersAhead: data['users_ahead'] ?? 0,
          achievementCount: data['achievements_count'] ?? 0,
          averageMastery: (data['average_mastery'] ?? 0.0).toDouble(),
          isLoading: false,
        );
      } else {
        state = state.copyWith(isLoading: false);
      }
    } catch (e) {
      // On error, keep cached state but mark as not loading
      // Error is not shown to user for background refresh - only for explicit actions
      state = state.copyWith(isLoading: false);
    }
  }

  /// Calculate level from total XP using level² × 100 formula
  int _calculateLevel(int xp) {
    // XP needed = level² × 100
    // Solve for level: level = sqrt(xp / 100)
    if (xp <= 0) return 1;
    int level = 1;
    int totalXpNeeded = 0;
    while (true) {
      final xpForThisLevel = level * level * 100;
      if (totalXpNeeded + xpForThisLevel > xp) break;
      totalXpNeeded += xpForThisLevel;
      level++;
    }
    return level;
  }

  /// Calculate XP needed for next level
  int _calculateXpForNextLevel(int level) {
    return (level + 1) * (level + 1) * 100;
  }

  /// Clear any error message
  void clearError() {
    state = state.copyWith(clearError: true);
  }

  void addXp(int xp, {String? source}) {
    state = state.copyWith(
      totalXp: state.totalXp + xp,
      dailyXp: state.dailyXp + xp,
      lastActivityDate: DateTime.now(),
    );
    // Optionally sync with backend
    _syncXp(xp, source: source);
  }

  /// Add gold to user's balance
  /// This now syncs with the global balance provider
  void addGold(int amount) {
    // Update balance provider (the single source of truth for gold)
    _ref.read(balanceProvider.notifier).addGold(amount);
    // Sync with backend
    _syncGold(amount);
  }

  /// Spend gold from user's balance
  /// Returns true if successful, false if insufficient balance
  bool spendGold(int amount) {
    final balanceState = _ref.read(balanceProvider);
    final currentGold = balanceState.maybeWhen(
      data: (balance) => balance.gold,
      orElse: () => 0,
    );

    if (currentGold < amount) return false;

    // Update balance provider
    _ref.read(balanceProvider.notifier).deductGold(amount);
    // Sync with backend
    _syncGold(-amount);
    return true;
  }

  /// Sync XP changes with backend (fire and forget)
  Future<void> _syncXp(int xp, {String? source}) async {
    try {
      await _apiClient.post(
        '/economy/xp/add',
        data: {
          'amount': xp,
          'source': source ?? 'practice',
        },
      );
    } catch (e) {
      // Silently fail - local state is updated, backend sync can retry later
    }
  }

  /// Sync gold changes with backend (fire and forget)
  Future<void> _syncGold(int amount) async {
    try {
      if (amount > 0) {
        await _apiClient.post(
          '/economy/gold/add',
          data: {'amount': amount},
        );
      } else {
        await _apiClient.post(
          '/economy/gold/spend',
          data: {'amount': amount.abs()},
        );
      }
      // Refresh balance to ensure sync
      _ref.read(balanceProvider.notifier).refresh();
    } catch (e) {
      // Silently fail - local state is updated, backend sync can retry later
    }
  }

  void activateGraceMode() {
    state = state.copyWith(graceModeActive: true);
  }

  Future<bool> repairStreakWithGold() async {
    state = state.copyWith(isLoading: true, clearError: true);
    try {
      final response = await _apiClient.post(
        ApiConstants.streakRepair,
        data: {'method': 'gold'},
      );

      if (response.statusCode == 200) {
        final data = response.data['data'];
        state = state.copyWith(
          streakJustLost: false,
          streak: data['current_streak'] ?? state.previousStreak,
          isLoading: false,
        );
        // Refresh balance after spending gold
        _ref.read(balanceProvider.notifier).refresh();
        return true;
      }
      state = state.copyWith(
        isLoading: false,
        error: 'No se pudo reparar la racha. Intenta de nuevo.',
      );
      return false;
    } catch (e) {
      state = state.copyWith(
        isLoading: false,
        error: 'Error de conexion. Verifica tu internet.',
      );
      return false;
    }
  }

  Future<bool> repairStreakWithAd() async {
    state = state.copyWith(isLoading: true, clearError: true);
    try {
      final response = await _apiClient.post(
        ApiConstants.streakRepair,
        data: {'method': 'ad'},
      );

      if (response.statusCode == 200) {
        final data = response.data['data'];
        state = state.copyWith(
          streakJustLost: false,
          streak: data['current_streak'] ?? state.previousStreak,
          isLoading: false,
        );
        return true;
      }
      state = state.copyWith(
        isLoading: false,
        error: 'No se pudo reparar la racha. Intenta de nuevo.',
      );
      return false;
    } catch (e) {
      state = state.copyWith(
        isLoading: false,
        error: 'Error de conexion. Verifica tu internet.',
      );
      return false;
    }
  }

  void dismissStreakLost() {
    state = state.copyWith(streakJustLost: false);
  }

  /// Check streak status on app start
  Future<void> checkStreakStatus() async {
    try {
      final response = await _apiClient.get(ApiConstants.authMe);
      if (response.statusCode == 200 && response.data != null) {
        final data = response.data;
        final currentStreak = data['streak'] ?? 0;
        final lastActivity = data['last_activity_date'] != null
            ? DateTime.tryParse(data['last_activity_date'])
            : null;

        // Check if streak was lost (more than 24 hours since last activity)
        bool streakLost = false;
        int previousStreak = state.streak;
        if (lastActivity != null && state.streak > 0) {
          final now = DateTime.now();
          final difference = now.difference(lastActivity);
          if (difference.inHours > 24) {
            streakLost = true;
            previousStreak = state.streak;
          }
        }

        state = state.copyWith(
          streak: currentStreak,
          streakJustLost: streakLost,
          previousStreak: streakLost ? previousStreak : state.previousStreak,
          totalXp: data['xp'] ?? state.totalXp,
          hearts: data['hearts'] ?? state.hearts,
          isPremium: data['is_premium'] ?? state.isPremium,
        );
      }
    } catch (e) {
      // Background check - don't show error to user, use cached state
      // This is intentional: streak check happens on app start and shouldn't block UX
    }
  }
}

final engagementProvider = StateNotifierProvider<EngagementNotifier, EngagementState>((ref) {
  final apiClient = ref.watch(apiClientProvider);
  return EngagementNotifier(apiClient, ref);
});
