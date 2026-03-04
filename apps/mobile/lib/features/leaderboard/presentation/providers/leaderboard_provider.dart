import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../domain/entities/leaderboard_entry.dart';
import '../../domain/repositories/leaderboard_repository.dart';
import '../../data/repositories/leaderboard_repository_impl.dart';
import '../../data/datasources/leaderboard_remote_datasource.dart';
import '../../../../core/network/api_client.dart';

class LeaderboardState {
  final List<LeaderboardEntry> entries;
  final String leagueName;
  final int leagueTier;
  final bool isLoading;
  final String? error;

  LeaderboardState({
    this.entries = const [],
    this.leagueName = 'Bronce',
    this.leagueTier = 1,
    this.isLoading = false,
    this.error,
  });

  LeaderboardState copyWith({
    List<LeaderboardEntry>? entries,
    String? leagueName,
    int? leagueTier,
    bool? isLoading,
    String? error,
  }) {
    return LeaderboardState(
      entries: entries ?? this.entries,
      leagueName: leagueName ?? this.leagueName,
      leagueTier: leagueTier ?? this.leagueTier,
      isLoading: isLoading ?? this.isLoading,
      error: error ?? this.error,
    );
  }
}

final leaderboardRemoteDataSourceProvider = Provider((ref) {
  final apiClient = ref.watch(apiClientProvider);
  return LeaderboardRemoteDataSource(apiClient);
});

final leaderboardRepositoryProvider = Provider<LeaderboardRepository>((ref) {
  final remoteDataSource = ref.watch(leaderboardRemoteDataSourceProvider);
  return LeaderboardRepositoryImpl(remoteDataSource);
});

class LeaderboardNotifier extends StateNotifier<LeaderboardState> {
  final LeaderboardRepository _repository;

  LeaderboardNotifier(this._repository) : super(LeaderboardState());

  Future<void> fetchLeaderboard() async {
    state = state.copyWith(isLoading: true, error: null);
    try {
      final entries = await _repository.getLeaderboard();

      state = state.copyWith(
        entries: entries,
        isLoading: false,
      );
    } catch (e) {
      state = state.copyWith(isLoading: false, error: e.toString());
    }
  }

  Future<void> fetchLeaderboardBySubject(String subjectId) async {
    state = state.copyWith(isLoading: true, error: null);
    try {
      final entries = await _repository.getLeaderboardBySubject(subjectId);

      state = state.copyWith(
        entries: entries,
        isLoading: false,
      );
    } catch (e) {
      state = state.copyWith(isLoading: false, error: e.toString());
    }
  }

  @override
  void dispose() {
    // Cleanup any resources if needed
    super.dispose();
  }
}

final leaderboardProvider = StateNotifierProvider<LeaderboardNotifier, LeaderboardState>((ref) {
  final repository = ref.watch(leaderboardRepositoryProvider);
  return LeaderboardNotifier(repository);
});
