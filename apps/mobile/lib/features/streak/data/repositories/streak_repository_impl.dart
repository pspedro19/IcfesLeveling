import '../../domain/repositories/streak_repository.dart';
import '../datasources/streak_remote_datasource.dart';

class StreakRepositoryImpl implements StreakRepository {
  final StreakRemoteDataSource remoteDataSource;

  StreakRepositoryImpl(this.remoteDataSource);

  @override
  Future<Map<String, dynamic>> repairStreak(String method) async {
    try {
      return await remoteDataSource.repairStreak(method);
    } catch (e) {
      rethrow;
    }
  }
}
