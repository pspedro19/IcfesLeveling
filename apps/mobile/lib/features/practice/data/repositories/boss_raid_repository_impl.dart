import '../../domain/repositories/boss_raid_repository.dart';
import '../datasources/boss_raid_remote_datasource.dart';
import '../models/boss_raid_models.dart';

class BossRaidRepositoryImpl implements BossRaidRepository {
  final BossRaidRemoteDataSource remoteDataSource;

  BossRaidRepositoryImpl(this.remoteDataSource);

  @override
  Future<BossRaidStatusModel> getStatus() async {
    return await remoteDataSource.getStatus();
  }

  @override
  Future<BossRaidSessionModel> startRaid() async {
    return await remoteDataSource.startRaid();
  }

  @override
  Future<BossRaidAnswerResponse> submitAnswer({
    required String sessionId,
    required String questionId,
    required String answerId,
  }) async {
    return await remoteDataSource.submitAnswer(
      sessionId: sessionId,
      questionId: questionId,
      answerId: answerId,
    );
  }

  @override
  Future<BossRaidCompleteResponse> completeRaid(String sessionId) async {
    return await remoteDataSource.completeRaid(sessionId);
  }
}
