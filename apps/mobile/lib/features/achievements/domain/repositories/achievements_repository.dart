import '../../data/models/achievement_model.dart';

/// Repository interface for achievements
abstract class AchievementsRepository {
  /// Get all achievements with their progress
  Future<AchievementsResponse> getAchievements();

  /// Get recently unlocked achievements
  Future<List<UnlockedAchievement>> getRecentUnlocks();

  /// Check and unlock any pending achievements
  Future<List<UnlockedAchievement>> checkAndUnlockAchievements();

  /// Get a specific achievement by ID
  Future<AchievementModel> getAchievementById(String id);

  /// Get achievements filtered by category
  Future<List<AchievementModel>> getAchievementsByCategory(AchievementCategory category);

  /// Get achievement completion percentage
  Future<double> getCompletionPercentage();

  /// Check if a specific achievement is unlocked
  Future<bool> isAchievementUnlocked(String achievementId);
}
