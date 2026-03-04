import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../data/models/achievement_model.dart';
import '../../data/datasources/achievements_remote_datasource.dart';
import '../../data/repositories/achievements_repository_impl.dart';
import '../../domain/repositories/achievements_repository.dart';
import '../../../../core/network/api_client.dart';

/// State for achievements feature
class AchievementsState {
  final List<AchievementModel> achievements;
  final List<UnlockedAchievement> recentUnlocks;
  final int totalUnlocked;
  final int totalAvailable;
  final AchievementCategory? selectedCategory;
  final bool isLoading;
  final String? error;
  final List<UnlockedAchievement> pendingNotifications;

  const AchievementsState({
    this.achievements = const [],
    this.recentUnlocks = const [],
    this.totalUnlocked = 0,
    this.totalAvailable = 0,
    this.selectedCategory,
    this.isLoading = false,
    this.error,
    this.pendingNotifications = const [],
  });

  double get completionPercentage =>
      totalAvailable > 0 ? totalUnlocked / totalAvailable : 0.0;

  List<AchievementModel> get filteredAchievements {
    if (selectedCategory == null) return achievements;
    return achievements.where((a) => a.category == selectedCategory).toList();
  }

  List<AchievementModel> get unlockedAchievements =>
      achievements.where((a) => a.isUnlocked).toList();

  List<AchievementModel> get lockedAchievements =>
      achievements.where((a) => !a.isUnlocked).toList();

  Map<AchievementCategory, List<AchievementModel>> get achievementsByCategory {
    final map = <AchievementCategory, List<AchievementModel>>{};
    for (final achievement in achievements) {
      map.putIfAbsent(achievement.category, () => []).add(achievement);
    }
    return map;
  }

  AchievementsState copyWith({
    List<AchievementModel>? achievements,
    List<UnlockedAchievement>? recentUnlocks,
    int? totalUnlocked,
    int? totalAvailable,
    AchievementCategory? selectedCategory,
    bool clearCategory = false,
    bool? isLoading,
    String? error,
    bool clearError = false,
    List<UnlockedAchievement>? pendingNotifications,
  }) {
    return AchievementsState(
      achievements: achievements ?? this.achievements,
      recentUnlocks: recentUnlocks ?? this.recentUnlocks,
      totalUnlocked: totalUnlocked ?? this.totalUnlocked,
      totalAvailable: totalAvailable ?? this.totalAvailable,
      selectedCategory: clearCategory ? null : (selectedCategory ?? this.selectedCategory),
      isLoading: isLoading ?? this.isLoading,
      error: clearError ? null : (error ?? this.error),
      pendingNotifications: pendingNotifications ?? this.pendingNotifications,
    );
  }
}

/// Notifier for achievements state management
class AchievementsNotifier extends StateNotifier<AchievementsState> {
  final AchievementsRepository _repository;

  AchievementsNotifier(this._repository) : super(const AchievementsState());

  /// Load all achievements
  Future<void> loadAchievements() async {
    state = state.copyWith(isLoading: true, clearError: true);

    try {
      final response = await _repository.getAchievements();
      state = state.copyWith(
        achievements: response.achievements,
        totalUnlocked: response.totalUnlocked,
        totalAvailable: response.totalAvailable,
        isLoading: false,
      );
    } catch (e) {
      state = state.copyWith(
        isLoading: false,
        error: 'Error cargando logros: $e',
      );
    }
  }

  /// Check for new achievements and add to pending notifications
  Future<void> checkForNewAchievements() async {
    try {
      final unlocked = await _repository.checkAndUnlockAchievements();
      if (unlocked.isNotEmpty) {
        state = state.copyWith(
          pendingNotifications: [...state.pendingNotifications, ...unlocked],
        );
        // Refresh achievements list
        await loadAchievements();
      }
    } catch (e) {
      // Silently fail - don't interrupt user flow
    }
  }

  /// Load recent unlocks
  Future<void> loadRecentUnlocks() async {
    try {
      final recentUnlocks = await _repository.getRecentUnlocks();
      state = state.copyWith(recentUnlocks: recentUnlocks);
    } catch (e) {
      // Silent fail for non-critical operation
    }
  }

  /// Filter achievements by category
  void filterByCategory(AchievementCategory? category) {
    state = state.copyWith(
      selectedCategory: category,
      clearCategory: category == null,
    );
  }

  /// Clear filter
  void clearFilter() {
    state = state.copyWith(clearCategory: true);
  }

  /// Dismiss a pending notification
  void dismissNotification(UnlockedAchievement notification) {
    final updatedNotifications = state.pendingNotifications
        .where((n) => n.achievement.id != notification.achievement.id)
        .toList();
    state = state.copyWith(pendingNotifications: updatedNotifications);
  }

  /// Dismiss all pending notifications
  void dismissAllNotifications() {
    state = state.copyWith(pendingNotifications: []);
  }

  /// Get the next pending notification
  UnlockedAchievement? get nextNotification =>
      state.pendingNotifications.isNotEmpty
          ? state.pendingNotifications.first
          : null;

  /// Get achievement by ID from current state
  AchievementModel? getAchievementById(String id) {
    return state.achievements.where((a) => a.id == id).firstOrNull;
  }

  /// Refresh all data
  Future<void> refresh() async {
    await Future.wait([
      loadAchievements(),
      loadRecentUnlocks(),
    ]);
  }
}

// ==================== PROVIDERS ====================

/// Provider for API client (should be provided by app-level provider)
final achievementsApiClientProvider = Provider<ApiClient>((ref) {
  // This should be overridden at the app level with the actual ApiClient
  throw UnimplementedError('ApiClient provider must be overridden');
});

/// Provider for remote datasource
final achievementsRemoteDatasourceProvider =
    Provider<AchievementsRemoteDatasource>((ref) {
  final apiClient = ref.watch(achievementsApiClientProvider);
  return AchievementsRemoteDatasourceImpl(apiClient);
});

/// Provider for repository
final achievementsRepositoryProvider = Provider<AchievementsRepository>((ref) {
  final datasource = ref.watch(achievementsRemoteDatasourceProvider);
  return AchievementsRepositoryImpl(datasource);
});

/// Main achievements provider
final achievementsProvider =
    StateNotifierProvider<AchievementsNotifier, AchievementsState>((ref) {
  final repository = ref.watch(achievementsRepositoryProvider);
  return AchievementsNotifier(repository);
});

/// Provider for filtered achievements (convenience)
final filteredAchievementsProvider = Provider<List<AchievementModel>>((ref) {
  final state = ref.watch(achievementsProvider);
  return state.filteredAchievements;
});

/// Provider for unlocked count
final unlockedCountProvider = Provider<int>((ref) {
  return ref.watch(achievementsProvider).totalUnlocked;
});

/// Provider for completion percentage
final achievementCompletionProvider = Provider<double>((ref) {
  return ref.watch(achievementsProvider).completionPercentage;
});

/// Provider for pending notifications
final achievementNotificationsProvider =
    Provider<List<UnlockedAchievement>>((ref) {
  return ref.watch(achievementsProvider).pendingNotifications;
});

/// Provider for achievements grouped by category
final achievementsByCategoryProvider =
    Provider<Map<AchievementCategory, List<AchievementModel>>>((ref) {
  return ref.watch(achievementsProvider).achievementsByCategory;
});
