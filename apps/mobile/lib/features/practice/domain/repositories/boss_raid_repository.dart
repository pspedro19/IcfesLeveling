import '../../data/models/boss_raid_models.dart';

abstract class BossRaidRepository {
  /// Get current boss raid status (is active, boss HP, time remaining, etc.)
  Future<BossRaidStatusModel> getStatus();

  /// Start a new raid session and get questions
  Future<BossRaidSessionModel> startRaid();

  /// Submit an answer during a raid battle
  /// Returns response with damage dealt, combo, and boss HP update
  Future<BossRaidAnswerResponse> submitAnswer({
    required String sessionId,
    required String questionId,
    required String answerId,
  });

  /// Complete the raid session and get final results
  Future<BossRaidCompleteResponse> completeRaid(String sessionId);
}
