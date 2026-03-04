import '../../../../core/network/api_client.dart';
import '../models/achievement_model.dart';

/// Remote data source for achievements
abstract class AchievementsRemoteDatasource {
  /// Fetch all achievements for the current user
  Future<AchievementsResponse> getAchievements();

  /// Get recently unlocked achievements (for notifications)
  Future<List<UnlockedAchievement>> getRecentUnlocks();

  /// Check and unlock achievements based on current progress
  Future<List<UnlockedAchievement>> checkAchievements();

  /// Get achievement details by ID
  Future<AchievementModel> getAchievementById(String id);

  /// Get achievements by category
  Future<List<AchievementModel>> getAchievementsByCategory(AchievementCategory category);
}

/// Implementation of achievements remote datasource
class AchievementsRemoteDatasourceImpl implements AchievementsRemoteDatasource {
  final ApiClient _apiClient;

  AchievementsRemoteDatasourceImpl(this._apiClient);

  @override
  Future<AchievementsResponse> getAchievements() async {
    final response = await _apiClient.get('/achievements');
    final data = response.data as Map<String, dynamic>;
    return AchievementsResponse.fromJson(data);
  }

  @override
  Future<List<UnlockedAchievement>> getRecentUnlocks() async {
    final response = await _apiClient.get('/achievements/recent');
    final data = response.data as Map<String, dynamic>;
    final List<dynamic> achievements = data['achievements'] ?? [];
    return achievements.map((json) => UnlockedAchievement.fromJson(json)).toList();
  }

  @override
  Future<List<UnlockedAchievement>> checkAchievements() async {
    final response = await _apiClient.post('/achievements/check', data: {});
    final data = response.data as Map<String, dynamic>;
    final List<dynamic> unlocked = data['unlocked'] ?? [];
    return unlocked.map((json) => UnlockedAchievement.fromJson(json)).toList();
  }

  @override
  Future<AchievementModel> getAchievementById(String id) async {
    final response = await _apiClient.get('/achievements/$id');
    final data = response.data as Map<String, dynamic>;
    return AchievementModel.fromJson(data);
  }

  @override
  Future<List<AchievementModel>> getAchievementsByCategory(AchievementCategory category) async {
    final response = await _apiClient.get('/achievements/category/${category.value}');
    final data = response.data as Map<String, dynamic>;
    final List<dynamic> achievements = data['achievements'] ?? [];
    return achievements.map((json) => AchievementModel.fromJson(json)).toList();
  }
}
