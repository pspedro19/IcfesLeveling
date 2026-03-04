import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/network/api_client.dart';
import '../../data/datasources/streak_remote_datasource.dart';
import '../../domain/repositories/streak_repository.dart';
import '../../data/repositories/streak_repository_impl.dart';

final streakRemoteDataSourceProvider = Provider((ref) {
  final apiClient = ref.watch(apiClientProvider);
  return StreakRemoteDataSource(apiClient);
});

final streakRepositoryProvider = Provider<StreakRepository>((ref) {
  final remote = ref.watch(streakRemoteDataSourceProvider);
  return StreakRepositoryImpl(remote);
});
