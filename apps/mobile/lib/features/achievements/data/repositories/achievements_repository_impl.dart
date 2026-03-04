import '../../domain/repositories/achievements_repository.dart';
import '../datasources/achievements_remote_datasource.dart';
import '../models/achievement_model.dart';

/// Implementation of achievements repository
class AchievementsRepositoryImpl implements AchievementsRepository {
  final AchievementsRemoteDatasource _remoteDatasource;

  // Cache for achievements
  AchievementsResponse? _cachedAchievements;
  DateTime? _cacheTime;
  static const _cacheDuration = Duration(minutes: 5);

  AchievementsRepositoryImpl(this._remoteDatasource);

  bool get _isCacheValid =>
      _cachedAchievements != null &&
      _cacheTime != null &&
      DateTime.now().difference(_cacheTime!) < _cacheDuration;

  @override
  Future<AchievementsResponse> getAchievements() async {
    if (_isCacheValid) {
      return _cachedAchievements!;
    }

    final response = await _remoteDatasource.getAchievements();
    _cachedAchievements = response;
    _cacheTime = DateTime.now();
    return response;
  }

  @override
  Future<List<UnlockedAchievement>> getRecentUnlocks() async {
    return await _remoteDatasource.getRecentUnlocks();
  }

  @override
  Future<List<UnlockedAchievement>> checkAndUnlockAchievements() async {
    final unlocked = await _remoteDatasource.checkAchievements();

    // Invalidate cache if new achievements were unlocked
    if (unlocked.isNotEmpty) {
      _cachedAchievements = null;
      _cacheTime = null;
    }

    return unlocked;
  }

  @override
  Future<AchievementModel> getAchievementById(String id) async {
    // Try to get from cache first
    if (_isCacheValid) {
      final cached = _cachedAchievements!.achievements
          .where((a) => a.id == id)
          .firstOrNull;
      if (cached != null) return cached;
    }

    return await _remoteDatasource.getAchievementById(id);
  }

  @override
  Future<List<AchievementModel>> getAchievementsByCategory(
      AchievementCategory category) async {
    // Try to filter from cache first
    if (_isCacheValid) {
      return _cachedAchievements!.achievements
          .where((a) => a.category == category)
          .toList();
    }

    return await _remoteDatasource.getAchievementsByCategory(category);
  }

  @override
  Future<double> getCompletionPercentage() async {
    final achievements = await getAchievements();
    if (achievements.totalAvailable == 0) return 0.0;
    return achievements.totalUnlocked / achievements.totalAvailable;
  }

  @override
  Future<bool> isAchievementUnlocked(String achievementId) async {
    final achievement = await getAchievementById(achievementId);
    return achievement.isUnlocked;
  }

  /// Clear the cache (useful after significant user actions)
  void clearCache() {
    _cachedAchievements = null;
    _cacheTime = null;
  }
}
