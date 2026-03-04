import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:icfes_mobile/features/leagues/presentation/providers/leagues_provider.dart';
import 'package:icfes_mobile/features/leagues/domain/repositories/leagues_repository.dart';
import 'package:icfes_mobile/features/leagues/data/models/leaderboard_response_model.dart';

// ---------------------------------------------------------------------------
// Fake repositories used across test groups
// ---------------------------------------------------------------------------

/// Returns a canned leaderboard response with two users.
class FakeLeaguesRepository implements LeaguesRepository {
  @override
  Future<LeaderboardResponseModel> getLeaderboard() async {
    return LeaderboardResponseModel(
      leaderboard: [
        LeagueUserModel(
          userId: 'user-1',
          name: 'Alice',
          xp: 1500,
          rank: 1,
          zone: 'promotion',
          isMe: false,
        ),
        LeagueUserModel(
          userId: 'user-2',
          name: 'Bob',
          xp: 900,
          rank: 2,
          zone: 'neutral',
          isMe: true,
        ),
      ],
      myRank: 2,
      myXp: 900,
      myZone: 'neutral',
      totalParticipants: 2,
    );
  }
}

/// Always throws when getLeaderboard is called.
class ErrorLeaguesRepository implements LeaguesRepository {
  final Object error;

  ErrorLeaguesRepository({this.error = 'Network error'});

  @override
  Future<LeaderboardResponseModel> getLeaderboard() async {
    throw Exception(error);
  }
}

// ---------------------------------------------------------------------------
// Helper: override the leagues provider with a given repository
// ---------------------------------------------------------------------------

ProviderContainer _containerWith(LeaguesRepository repo) {
  return ProviderContainer(
    overrides: [
      leaguesRepositoryProvider.overrideWithValue(repo),
    ],
  );
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  // -------------------------------------------------------------------------
  group('LeagueState', () {
    test('has correct default values', () {
      final state = LeagueState();

      expect(state.name, equals('LIGA DE BRONCE'));
      expect(state.timeLeft, isNotEmpty);
      expect(state.users, isEmpty);
      expect(state.isLoading, isFalse);
      expect(state.error, isNull);
    });

    test('copyWith updates only the supplied fields', () {
      final original = LeagueState();

      final updated = original.copyWith(
        name: 'LIGA DE PLATA',
        isLoading: true,
      );

      expect(updated.name, equals('LIGA DE PLATA'));
      expect(updated.isLoading, isTrue);
      // Unchanged fields are preserved.
      expect(updated.timeLeft, equals(original.timeLeft));
      expect(updated.users, equals(original.users));
      expect(updated.error, isNull);
    });

    test('copyWith with no arguments returns equivalent state', () {
      final original = LeagueState(
        name: 'LIGA DE ORO',
        timeLeft: '1d 6h',
        isLoading: false,
        error: null,
      );

      final copy = original.copyWith();

      expect(copy.name, equals(original.name));
      expect(copy.timeLeft, equals(original.timeLeft));
      expect(copy.isLoading, equals(original.isLoading));
      expect(copy.error, equals(original.error));
    });

    test('copyWith can set users list', () {
      final user = LeagueUser(
        id: 'u1',
        name: 'Carol',
        xp: 200,
        rank: 3,
        zone: 'demotion',
      );

      final state = LeagueState().copyWith(users: [user]);

      expect(state.users.length, equals(1));
      expect(state.users.first.id, equals('u1'));
    });

    test('copyWith can set error', () {
      final state = LeagueState().copyWith(error: 'Something went wrong');

      expect(state.error, equals('Something went wrong'));
    });
  });

  // -------------------------------------------------------------------------
  group('LeagueUser', () {
    test('constructs with required fields', () {
      final user = LeagueUser(
        id: 'u42',
        name: 'Diana',
        xp: 750,
        rank: 5,
        zone: 'neutral',
      );

      expect(user.id, equals('u42'));
      expect(user.name, equals('Diana'));
      expect(user.xp, equals(750));
      expect(user.rank, equals(5));
      expect(user.zone, equals('neutral'));
    });

    test('isCurrentUser defaults to false', () {
      final user = LeagueUser(
        id: 'u1',
        name: 'Eve',
        xp: 100,
        rank: 10,
        zone: 'demotion',
      );

      expect(user.isCurrentUser, isFalse);
    });

    test('isCurrentUser can be set to true', () {
      final user = LeagueUser(
        id: 'u2',
        name: 'Frank',
        xp: 300,
        rank: 7,
        zone: 'neutral',
        isCurrentUser: true,
      );

      expect(user.isCurrentUser, isTrue);
    });

    test('different zone values are accepted', () {
      for (final zone in ['promotion', 'neutral', 'demotion']) {
        final user = LeagueUser(
          id: 'u-$zone',
          name: 'User $zone',
          xp: 500,
          rank: 1,
          zone: zone,
        );
        expect(user.zone, equals(zone));
      }
    });
  });

  // -------------------------------------------------------------------------
  group('LeaguesNotifier.fetchLeaderboard', () {
    test('loads users from the repository', () async {
      final container = _containerWith(FakeLeaguesRepository());
      addTearDown(container.dispose);

      // Explicitly call and await fetchLeaderboard (constructor fire-and-forgets it)
      final notifier = container.read(leaguesProvider.notifier);
      await notifier.fetchLeaderboard();

      final state = container.read(leaguesProvider);

      expect(state.isLoading, isFalse);
      expect(state.error, isNull);
      expect(state.users.length, equals(2));
    });

    test('maps LeagueUserModel fields to LeagueUser correctly', () async {
      final container = _containerWith(FakeLeaguesRepository());
      addTearDown(container.dispose);

      final notifier = container.read(leaguesProvider.notifier);
      await notifier.fetchLeaderboard();

      final users = container.read(leaguesProvider).users;

      // First user (Alice).
      final alice = users.firstWhere((u) => u.id == 'user-1');
      expect(alice.name, equals('Alice'));
      expect(alice.xp, equals(1500));
      expect(alice.rank, equals(1));
      expect(alice.zone, equals('promotion'));
      expect(alice.isCurrentUser, isFalse);

      // Second user (Bob, isMe == true).
      final bob = users.firstWhere((u) => u.id == 'user-2');
      expect(bob.name, equals('Bob'));
      expect(bob.xp, equals(900));
      expect(bob.rank, equals(2));
      expect(bob.zone, equals('neutral'));
      expect(bob.isCurrentUser, isTrue);
    });

    test('sets isLoading to false after successful fetch', () async {
      final container = _containerWith(FakeLeaguesRepository());
      addTearDown(container.dispose);

      final notifier = container.read(leaguesProvider.notifier);
      await notifier.fetchLeaderboard();

      expect(container.read(leaguesProvider).isLoading, isFalse);
    });

    test('sets error and clears isLoading on repository failure', () async {
      final container = _containerWith(
        ErrorLeaguesRepository(error: 'Network error'),
      );
      addTearDown(container.dispose);

      final notifier = container.read(leaguesProvider.notifier);
      await notifier.fetchLeaderboard();

      final state = container.read(leaguesProvider);

      expect(state.isLoading, isFalse);
      expect(state.error, isNotNull);
      expect(state.error, contains('Network error'));
    });

    test('error state leaves users list unchanged (empty initially)', () async {
      final container = _containerWith(ErrorLeaguesRepository());
      addTearDown(container.dispose);

      final notifier = container.read(leaguesProvider.notifier);
      await notifier.fetchLeaderboard();

      final state = container.read(leaguesProvider);

      expect(state.users, isEmpty);
      expect(state.error, isNotNull);
    });

    test('manual fetchLeaderboard call updates state', () async {
      final container = _containerWith(FakeLeaguesRepository());
      addTearDown(container.dispose);

      final notifier = container.read(leaguesProvider.notifier);
      await notifier.fetchLeaderboard();

      final state = container.read(leaguesProvider);
      expect(state.users.length, equals(2));
      expect(state.isLoading, isFalse);
      expect(state.error, isNull);
    });
  });

  // -------------------------------------------------------------------------
  group('LeaguesNotifier.joinLeague', () {
    test('does not throw', () async {
      final container = _containerWith(FakeLeaguesRepository());
      addTearDown(container.dispose);

      final notifier = container.read(leaguesProvider.notifier);
      await notifier.fetchLeaderboard();

      // Should complete without throwing.
      await expectLater(notifier.joinLeague(), completes);
    });

    test('does not alter the loaded users list', () async {
      final container = _containerWith(FakeLeaguesRepository());
      addTearDown(container.dispose);

      final notifier = container.read(leaguesProvider.notifier);
      await notifier.fetchLeaderboard();
      final usersBefore = container.read(leaguesProvider).users;

      await notifier.joinLeague();

      final usersAfter = container.read(leaguesProvider).users;
      expect(usersAfter.length, equals(usersBefore.length));
    });

    test('does not change isLoading', () async {
      final container = _containerWith(FakeLeaguesRepository());
      addTearDown(container.dispose);

      final notifier = container.read(leaguesProvider.notifier);
      await notifier.fetchLeaderboard();
      await notifier.joinLeague();

      expect(container.read(leaguesProvider).isLoading, isFalse);
    });

    test('does not set an error', () async {
      final container = _containerWith(FakeLeaguesRepository());
      addTearDown(container.dispose);

      final notifier = container.read(leaguesProvider.notifier);
      await notifier.fetchLeaderboard();
      await notifier.joinLeague();

      expect(container.read(leaguesProvider).error, isNull);
    });
  });
}
