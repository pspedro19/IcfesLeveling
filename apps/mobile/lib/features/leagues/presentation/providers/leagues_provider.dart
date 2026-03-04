import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/network/api_client.dart';
import '../../data/datasources/leagues_remote_datasource.dart';
import '../../domain/repositories/leagues_repository.dart';
import '../../data/repositories/leagues_repository_impl.dart';

// Data Layer Providers
final leaguesRemoteDataSourceProvider = Provider((ref) {
  final apiClient = ref.watch(apiClientProvider);
  return LeaguesRemoteDataSource(apiClient);
});

final leaguesRepositoryProvider = Provider<LeaguesRepository>((ref) {
  final remote = ref.watch(leaguesRemoteDataSourceProvider);
  return LeaguesRepositoryImpl(remote);
});


// Presentation Layer Entities
class LeagueUser {
  final String id;
  final String name;
  final int xp;
  final int rank;
  final String zone; // Added zone field
  final bool isCurrentUser;

  LeagueUser({
    required this.id,
    required this.name,
    required this.xp,
    required this.rank,
    required this.zone,
    this.isCurrentUser = false,
  });
}

class LeagueState {
  final String name;
  final String timeLeft;
  final List<LeagueUser> users;
  final bool isLoading;
  final String? error;

  LeagueState({
    this.name = "LIGA DE BRONCE",
    this.timeLeft = "2d 14h 22m",
    this.users = const [],
    this.isLoading = false,
    this.error,
  });

  LeagueState copyWith({
    String? name,
    String? timeLeft,
    List<LeagueUser>? users,
    bool? isLoading,
    String? error,
  }) {
    return LeagueState(
      name: name ?? this.name,
      timeLeft: timeLeft ?? this.timeLeft,
      users: users ?? this.users,
      isLoading: isLoading ?? this.isLoading,
      error: error ?? this.error,
    );
  }
}

class LeaguesNotifier extends StateNotifier<LeagueState> {
  final LeaguesRepository _leaguesRepository;

  LeaguesNotifier(this._leaguesRepository) : super(LeagueState()) {
    fetchLeaderboard();
  }

  Future<void> fetchLeaderboard() async {
    state = state.copyWith(isLoading: true, error: null);
    try {
      final leaderboardData = await _leaguesRepository.getLeaderboard();
      
      final users = leaderboardData.leaderboard.map((userModel) => LeagueUser(
        id: userModel.userId,
        name: userModel.name,
        xp: userModel.xp,
        rank: userModel.rank,
        zone: userModel.zone, // Map the zone field
        isCurrentUser: userModel.isMe,
      )).toList();

      state = state.copyWith(
        isLoading: false,
        users: users,
        // In a real app, we'd also update league name and time left
      );
    } catch (e) {
      state = state.copyWith(isLoading: false, error: e.toString());
    }
  }

  Future<void> joinLeague() async {
    // Placeholder for API call
  }
}

final leaguesProvider = StateNotifierProvider<LeaguesNotifier, LeagueState>((ref) {
  final repo = ref.watch(leaguesRepositoryProvider);
  return LeaguesNotifier(repo);
});
