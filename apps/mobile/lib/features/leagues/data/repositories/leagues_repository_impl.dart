import '../../domain/repositories/leagues_repository.dart';
import '../datasources/leagues_remote_datasource.dart';
import '../models/leaderboard_response_model.dart';

class LeaguesRepositoryImpl implements LeaguesRepository {
  final LeaguesRemoteDataSource remoteDataSource;

  LeaguesRepositoryImpl(this.remoteDataSource);

  @override
  Future<LeaderboardResponseModel> getLeaderboard() async {
    try {
      return await remoteDataSource.getLeaderboard();
    } catch (e) {
      // In a real app, handle exceptions gracefully (e.g., wrap in a Failure object)
      rethrow;
    }
  }
}
