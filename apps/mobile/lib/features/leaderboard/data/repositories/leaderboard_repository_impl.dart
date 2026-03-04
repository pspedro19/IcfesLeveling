import '../../domain/repositories/leaderboard_repository.dart';
import '../../domain/entities/leaderboard_entry.dart';
import '../datasources/leaderboard_remote_datasource.dart';

class LeaderboardRepositoryImpl implements LeaderboardRepository {
  final LeaderboardRemoteDataSource _remoteDataSource;

  LeaderboardRepositoryImpl(this._remoteDataSource);

  @override
  Future<List<LeaderboardEntry>> getLeaderboard({int limit = 30}) {
    return _remoteDataSource.getLeaderboard(limit: limit);
  }

  @override
  Future<List<LeaderboardEntry>> getLeaderboardBySubject(String subjectId, {int limit = 30}) {
    return _remoteDataSource.getLeaderboard(limit: limit);
  }
}
