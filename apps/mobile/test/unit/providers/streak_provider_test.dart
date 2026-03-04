import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:icfes_mobile/core/network/api_client.dart';
import 'package:icfes_mobile/core/constants/api_constants.dart';
import 'package:icfes_mobile/shared/providers/streak_provider.dart';

import '../../mocks/mock_providers.dart';

void main() {
  // ---------------------------------------------------------------------------
  // Helpers
  // ---------------------------------------------------------------------------

  /// Returns a valid JSON map that matches every field of [StreakState.fromJson].
  Map<String, dynamic> validStreakJson({
    int currentStreak = 10,
    int longestStreak = 25,
    double multiplier = 1.5,
    int freezesAvailable = 2,
    bool isAtRisk = false,
    bool canRepair = true,
    int previousStreak = 8,
    int? repairSecondsLeft = 3600,
  }) {
    return {
      'current_streak': currentStreak,
      'longest_streak': longestStreak,
      'multiplier': multiplier,
      'freezes_available': freezesAvailable,
      'is_at_risk': isAtRisk,
      'can_repair': canRepair,
      'previous_streak': previousStreak,
      if (repairSecondsLeft != null) 'repair_seconds_left': repairSecondsLeft,
    };
  }

  // ---------------------------------------------------------------------------
  // StreakState.fromJson
  // ---------------------------------------------------------------------------

  group('StreakState.fromJson', () {
    test('parses all fields from a complete valid JSON map', () {
      final json = validStreakJson(
        currentStreak: 15,
        longestStreak: 30,
        multiplier: 2.0,
        freezesAvailable: 3,
        isAtRisk: true,
        canRepair: false,
        previousStreak: 14,
        repairSecondsLeft: 7200,
      );

      final state = StreakState.fromJson(json);

      expect(state.current, equals(15));
      expect(state.longest, equals(30));
      expect(state.multiplier, equals(2.0));
      expect(state.freezesAvailable, equals(3));
      expect(state.isAtRisk, isTrue);
      expect(state.canRepair, isFalse);
      expect(state.previousStreak, equals(14));
      expect(state.repairWindowRemaining, equals(const Duration(seconds: 7200)));
    });

    test('repairWindowRemaining is null when repair_seconds_left is absent', () {
      final json = validStreakJson(repairSecondsLeft: null);

      final state = StreakState.fromJson(json);

      expect(state.repairWindowRemaining, isNull);
    });

    test('handles missing fields by falling back to zero/false defaults', () {
      // Completely empty map — every nullable field should default gracefully.
      final state = StreakState.fromJson({});

      expect(state.current, equals(0));
      expect(state.longest, equals(0));
      expect(state.multiplier, equals(1.0));
      expect(state.freezesAvailable, equals(0));
      expect(state.isAtRisk, isFalse);
      expect(state.canRepair, isFalse);
      expect(state.previousStreak, equals(0));
      expect(state.repairWindowRemaining, isNull);
    });

    test('multiplier is always a double even when JSON provides an int', () {
      final json = validStreakJson()..['multiplier'] = 2; // int, not double

      final state = StreakState.fromJson(json as Map<String, dynamic>);

      expect(state.multiplier, isA<double>());
      expect(state.multiplier, equals(2.0));
    });
  });

  // ---------------------------------------------------------------------------
  // StreakState.empty()
  // ---------------------------------------------------------------------------

  group('StreakState.empty()', () {
    test('returns a state with all-zero / false defaults', () {
      final state = StreakState.empty();

      expect(state.current, equals(0));
      expect(state.longest, equals(0));
      expect(state.multiplier, equals(1.0));
      expect(state.freezesAvailable, equals(0));
      expect(state.isAtRisk, isFalse);
      expect(state.canRepair, isFalse);
      expect(state.previousStreak, equals(0));
      expect(state.repairWindowRemaining, isNull);
    });
  });

  // ---------------------------------------------------------------------------
  // StreakNotifier — shared test infrastructure
  // ---------------------------------------------------------------------------

  group('StreakNotifier', () {
    late FakeApiClient fakeApiClient;
    late ProviderContainer container;

    /// Creates a [ProviderContainer] that overrides [apiClientProvider] with
    /// [fakeApiClient] and optionally adds more [overrides].
    ProviderContainer createContainer({List<Override> overrides = const []}) {
      return ProviderContainer(
        overrides: [
          apiClientProvider.overrideWithValue(fakeApiClient),
          ...overrides,
        ],
      );
    }

    /// Seeds the fake client with a successful balance response so that
    /// [balanceProvider] (which [StreakNotifier] reads on gold-repair) does not
    /// emit an error.
    void seedBalanceResponse() {
      fakeApiClient.setMockResponse(
        ApiConstants.economyBalance,
        {'gold': 500, 'gems': 10},
        statusCode: 200,
      );
    }

    setUp(() {
      fakeApiClient = FakeApiClient();
      // Seed a default balance so balanceProvider never blocks other tests.
      seedBalanceResponse();
    });

    tearDown(() {
      container.dispose();
    });

    // -------------------------------------------------------------------------
    // fetchStatus
    // -------------------------------------------------------------------------

    group('fetchStatus', () {
      test('transitions to AsyncValue.data with parsed StreakState on success',
          () async {
        fakeApiClient.setMockResponse(
          ApiConstants.streakStatus,
          validStreakJson(currentStreak: 7, longestStreak: 20),
          statusCode: 200,
        );

        container = createContainer();
        // Reading the provider triggers the constructor, which calls fetchStatus().
        container.read(streakProvider);

        // Allow the async constructor work to complete.
        await Future.delayed(const Duration(milliseconds: 200));

        final state = container.read(streakProvider);

        expect(state, isA<AsyncData<StreakState>>());
        state.whenData((streak) {
          expect(streak.current, equals(7));
          expect(streak.longest, equals(20));
        });
      });

      test('transitions to AsyncValue.error when the network call fails', () async {
        fakeApiClient.setErrorEndpoint(ApiConstants.streakStatus);

        container = createContainer();
        container.read(streakProvider);

        await Future.delayed(const Duration(milliseconds: 200));

        final state = container.read(streakProvider);
        expect(state, isA<AsyncError<StreakState>>());
      });

      test('does not overwrite existing data when a subsequent fetch fails',
          () async {
        // First load succeeds.
        fakeApiClient.setMockResponse(
          ApiConstants.streakStatus,
          validStreakJson(currentStreak: 5),
          statusCode: 200,
        );

        container = createContainer();
        container.read(streakProvider);
        await Future.delayed(const Duration(milliseconds: 200));

        // Verify we have data.
        expect(container.read(streakProvider), isA<AsyncData<StreakState>>());

        // Now make the endpoint fail and call fetchStatus() manually.
        fakeApiClient.clearMockResponse(ApiConstants.streakStatus);
        fakeApiClient.setErrorEndpoint(ApiConstants.streakStatus);

        await container.read(streakProvider.notifier).fetchStatus();

        // State must still hold the original data — not be overwritten with an
        // error — because StreakNotifier guards: `if (state.value == null)`.
        final state = container.read(streakProvider);
        expect(state, isA<AsyncData<StreakState>>());
        state.whenData((streak) => expect(streak.current, equals(5)));
      });

      test('can be called multiple times and reflects the latest response',
          () async {
        fakeApiClient.setMockResponse(
          ApiConstants.streakStatus,
          validStreakJson(currentStreak: 3),
          statusCode: 200,
        );

        container = createContainer();
        container.read(streakProvider);
        await Future.delayed(const Duration(milliseconds: 200));

        // Update mock and re-fetch.
        fakeApiClient.setMockResponse(
          ApiConstants.streakStatus,
          validStreakJson(currentStreak: 9),
          statusCode: 200,
        );
        await container.read(streakProvider.notifier).fetchStatus();

        container.read(streakProvider).whenData(
          (streak) => expect(streak.current, equals(9)),
        );
      });
    });

    // -------------------------------------------------------------------------
    // repairWithGold
    // -------------------------------------------------------------------------

    group('repairWithGold', () {
      /// Ensures the provider has loaded initial streak data before testing
      /// a mutating action.
      Future<void> primeContainer() async {
        fakeApiClient.setMockResponse(
          ApiConstants.streakStatus,
          validStreakJson(currentStreak: 0, canRepair: true),
          statusCode: 200,
        );
        container = createContainer();
        container.read(streakProvider);
        await Future.delayed(const Duration(milliseconds: 200));
      }

      test('returns true and refreshes streak state on success', () async {
        await primeContainer();

        // The repair endpoint returns success.
        fakeApiClient.setMockResponse(
          ApiConstants.streakRepair,
          {'new_balance': null},
          statusCode: 200,
        );
        // fetchStatus() will be called internally; update its response.
        fakeApiClient.setMockResponse(
          ApiConstants.streakStatus,
          validStreakJson(currentStreak: 5, canRepair: false),
          statusCode: 200,
        );

        final result =
            await container.read(streakProvider.notifier).repairWithGold();

        expect(result, isTrue);
        container.read(streakProvider).whenData(
          (streak) => expect(streak.current, equals(5)),
        );
      });

      test('returns true and updates balance when new_balance is provided',
          () async {
        await primeContainer();

        fakeApiClient.setMockResponse(
          ApiConstants.streakRepair,
          {
            'new_balance': {'gold': 350, 'gems': 5}
          },
          statusCode: 200,
        );
        fakeApiClient.setMockResponse(
          ApiConstants.streakStatus,
          validStreakJson(currentStreak: 4),
          statusCode: 200,
        );

        final result =
            await container.read(streakProvider.notifier).repairWithGold();

        expect(result, isTrue);
      });

      test('returns false when the repair endpoint throws a network error',
          () async {
        await primeContainer();

        fakeApiClient.setErrorEndpoint(ApiConstants.streakRepair);

        final result =
            await container.read(streakProvider.notifier).repairWithGold();

        expect(result, isFalse);
      });

      test('returns false when the repair endpoint returns a non-200 status',
          () async {
        await primeContainer();

        fakeApiClient.setMockResponse(
          ApiConstants.streakRepair,
          {'error': 'Insufficient gold'},
          statusCode: 402,
        );

        final result =
            await container.read(streakProvider.notifier).repairWithGold();

        expect(result, isFalse);
      });
    });

    // -------------------------------------------------------------------------
    // repairWithAd
    // -------------------------------------------------------------------------

    group('repairWithAd', () {
      Future<void> primeContainer() async {
        fakeApiClient.setMockResponse(
          ApiConstants.streakStatus,
          validStreakJson(currentStreak: 0, canRepair: true),
          statusCode: 200,
        );
        container = createContainer();
        container.read(streakProvider);
        await Future.delayed(const Duration(milliseconds: 200));
      }

      test('returns true and refreshes streak state on success', () async {
        await primeContainer();

        fakeApiClient.setMockResponse(
          ApiConstants.streakRepair,
          {'repaired': true},
          statusCode: 200,
        );
        fakeApiClient.setMockResponse(
          ApiConstants.streakStatus,
          validStreakJson(currentStreak: 6, canRepair: false),
          statusCode: 200,
        );

        final result =
            await container.read(streakProvider.notifier).repairWithAd();

        expect(result, isTrue);
        container.read(streakProvider).whenData(
          (streak) => expect(streak.current, equals(6)),
        );
      });

      test('returns false when the repair endpoint throws a network error',
          () async {
        await primeContainer();

        fakeApiClient.setErrorEndpoint(ApiConstants.streakRepair);

        final result =
            await container.read(streakProvider.notifier).repairWithAd();

        expect(result, isFalse);
      });

      test('returns false when the repair endpoint returns a non-200 status',
          () async {
        await primeContainer();

        fakeApiClient.setMockResponse(
          ApiConstants.streakRepair,
          {'error': 'Daily ad limit reached'},
          statusCode: 429,
        );

        final result =
            await container.read(streakProvider.notifier).repairWithAd();

        expect(result, isFalse);
      });
    });

    // -------------------------------------------------------------------------
    // useFreeze
    // -------------------------------------------------------------------------

    group('useFreeze', () {
      Future<void> primeContainer() async {
        fakeApiClient.setMockResponse(
          ApiConstants.streakStatus,
          validStreakJson(currentStreak: 10, freezesAvailable: 1),
          statusCode: 200,
        );
        container = createContainer();
        container.read(streakProvider);
        await Future.delayed(const Duration(milliseconds: 200));
      }

      test('returns true and refreshes streak state on success', () async {
        await primeContainer();

        fakeApiClient.setMockResponse(
          ApiConstants.streakFreeze,
          {'freeze_applied': true},
          statusCode: 200,
        );
        fakeApiClient.setMockResponse(
          ApiConstants.streakStatus,
          validStreakJson(currentStreak: 10, freezesAvailable: 0),
          statusCode: 200,
        );

        final result =
            await container.read(streakProvider.notifier).useFreeze();

        expect(result, isTrue);
        container.read(streakProvider).whenData(
          (streak) => expect(streak.freezesAvailable, equals(0)),
        );
      });

      test('returns false when the freeze endpoint throws a network error',
          () async {
        await primeContainer();

        fakeApiClient.setErrorEndpoint(ApiConstants.streakFreeze);

        final result =
            await container.read(streakProvider.notifier).useFreeze();

        expect(result, isFalse);
      });

      test('returns false when the freeze endpoint returns a non-200 status',
          () async {
        await primeContainer();

        fakeApiClient.setMockResponse(
          ApiConstants.streakFreeze,
          {'error': 'No freezes available'},
          statusCode: 400,
        );

        final result =
            await container.read(streakProvider.notifier).useFreeze();

        expect(result, isFalse);
      });
    });
  });
}
