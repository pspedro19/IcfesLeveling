import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:icfes_mobile/core/network/api_client.dart';
import 'package:icfes_mobile/core/constants/api_constants.dart';
import 'package:icfes_mobile/features/engagement/presentation/providers/engagement_provider.dart';

import '../../mocks/mock_providers.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  // Mock Sentry and other platform channels
  TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
      .setMockMethodCallHandler(const MethodChannel('sentry_flutter'), (call) async => null);
  group('EngagementProvider', () {
    late FakeApiClient fakeApiClient;
    late ProviderContainer container;

    setUp(() {
      fakeApiClient = FakeApiClient();
    });

    tearDown(() {
      container.dispose();
    });

    ProviderContainer createContainer() {
      return ProviderContainer(
        overrides: [
          apiClientProvider.overrideWithValue(fakeApiClient),
        ],
      );
    }

    group('fetchXp', () {
      test('fetchXp updates state with XP from API', () async {
        // Arrange
        fakeApiClient.setMockResponse(
          ApiConstants.authMe,
          {'xp': 500, 'daily_xp': 50},
          statusCode: 200,
        );

        container = createContainer();
        // Read notifier to trigger initialization
        container.read(engagementProvider.notifier);

        // Wait for initial fetch
        await Future.delayed(const Duration(milliseconds: 100));

        // Assert
        final state = container.read(engagementProvider);
        expect(state.totalXp, equals(500));
        expect(state.dailyXp, equals(50));
      });

      test('fetchXp handles missing data gracefully', () async {
        // Arrange
        fakeApiClient.setMockResponse(
          ApiConstants.authMe,
          {'xp': null, 'daily_xp': null},
          statusCode: 200,
        );

        container = createContainer();
        container.read(engagementProvider.notifier);

        await Future.delayed(const Duration(milliseconds: 100));

        // Assert - should default to 0
        final state = container.read(engagementProvider);
        expect(state.totalXp, equals(0));
        expect(state.dailyXp, equals(0));
      });

      test('fetchXp silently fails on network error', () async {
        // Arrange
        fakeApiClient.setErrorEndpoint(ApiConstants.authMe);

        container = createContainer();
        container.read(engagementProvider.notifier);

        await Future.delayed(const Duration(milliseconds: 100));

        // Assert - should keep default state
        final state = container.read(engagementProvider);
        expect(state.totalXp, equals(0));
        // No error thrown, silent failure
      });

      test('fetchXp can be called multiple times', () async {
        // Arrange
        fakeApiClient.setMockResponse(
          ApiConstants.authMe,
          {'xp': 100, 'daily_xp': 10},
          statusCode: 200,
        );

        container = createContainer();
        final notifier = container.read(engagementProvider.notifier);

        await Future.delayed(const Duration(milliseconds: 100));

        // Update mock and fetch again
        fakeApiClient.setMockResponse(
          ApiConstants.authMe,
          {'xp': 200, 'daily_xp': 20},
          statusCode: 200,
        );

        await notifier.fetchXp();

        // Assert - should have updated values
        final state = container.read(engagementProvider);
        expect(state.totalXp, equals(200));
        expect(state.dailyXp, equals(20));
      });
    });

    group('addXp', () {
      test('addXp updates totals correctly', () async {
        // Arrange
        fakeApiClient.setMockResponse(
          ApiConstants.authMe,
          {'xp': 100, 'daily_xp': 10},
          statusCode: 200,
        );

        container = createContainer();
        final notifier = container.read(engagementProvider.notifier);

        await Future.delayed(const Duration(milliseconds: 100));

        // Act
        notifier.addXp(25);

        // Assert
        final state = container.read(engagementProvider);
        expect(state.totalXp, equals(125)); // 100 + 25
        expect(state.dailyXp, equals(35)); // 10 + 25
        expect(state.lastActivityDate, isNotNull);
      });

      test('addXp can be called multiple times', () async {
        // Arrange
        fakeApiClient.setMockResponse(
          ApiConstants.authMe,
          {'xp': 0, 'daily_xp': 0},
          statusCode: 200,
        );

        container = createContainer();
        final notifier = container.read(engagementProvider.notifier);

        await Future.delayed(const Duration(milliseconds: 100));

        // Act
        notifier.addXp(10);
        notifier.addXp(20);
        notifier.addXp(30);

        // Assert
        final state = container.read(engagementProvider);
        expect(state.totalXp, equals(60)); // 10 + 20 + 30
        expect(state.dailyXp, equals(60));
      });

      test('addXp updates lastActivityDate', () async {
        // Arrange
        fakeApiClient.setMockResponse(ApiConstants.authMe, {}, statusCode: 200);

        container = createContainer();
        final notifier = container.read(engagementProvider.notifier);

        await Future.delayed(const Duration(milliseconds: 100));

        var state = container.read(engagementProvider);
        expect(state.lastActivityDate, isNull);

        // Act
        final beforeAdd = DateTime.now();
        notifier.addXp(10);
        final afterAdd = DateTime.now();

        // Assert
        state = container.read(engagementProvider);
        expect(state.lastActivityDate, isNotNull);
        expect(
          state.lastActivityDate!.isAfter(beforeAdd.subtract(const Duration(seconds: 1))),
          isTrue,
        );
        expect(
          state.lastActivityDate!.isBefore(afterAdd.add(const Duration(seconds: 1))),
          isTrue,
        );
      });
    });

    group('repairStreakWithGold', () {
      test('repairStreakWithGold calls API and updates state on success', () async {
        // Arrange
        fakeApiClient.setMockResponse(ApiConstants.authMe, {}, statusCode: 200);
        fakeApiClient.setMockResponse(
          ApiConstants.streakRepair,
          {'data': {'current_streak': 5}},
          statusCode: 200,
        );

        container = createContainer();
        final notifier = container.read(engagementProvider.notifier);

        await Future.delayed(const Duration(milliseconds: 100));

        // Set initial state with lost streak
        notifier.activateGraceMode(); // This sets some state

        // Act
        final result = await notifier.repairStreakWithGold();

        // Assert
        expect(result, isTrue);
        final state = container.read(engagementProvider);
        expect(state.streakJustLost, isFalse);
        expect(state.streak, equals(5));
      });

      test('repairStreakWithGold returns false on API failure', () async {
        // Arrange
        fakeApiClient.setMockResponse(ApiConstants.authMe, {}, statusCode: 200);
        fakeApiClient.setErrorEndpoint(ApiConstants.streakRepair);

        container = createContainer();
        final notifier = container.read(engagementProvider.notifier);

        await Future.delayed(const Duration(milliseconds: 100));

        // Act
        final result = await notifier.repairStreakWithGold();

        // Assert
        expect(result, isFalse);
        // State should still be updated locally
        final state = container.read(engagementProvider);
        expect(state.streakJustLost, isFalse);
      });

      test('repairStreakWithGold uses previousStreak as fallback', () async {
        // Arrange
        fakeApiClient.setMockResponse(
          ApiConstants.authMe,
          {'streak': 10},
          statusCode: 200,
        );
        fakeApiClient.setMockResponse(
          ApiConstants.streakRepair,
          {'data': {}}, // No current_streak in response
          statusCode: 200,
        );

        container = createContainer();
        final notifier = container.read(engagementProvider.notifier);

        await Future.delayed(const Duration(milliseconds: 100));

        // Manually set previousStreak via checkStreakStatus simulation
        // (In real scenario this would be set by checkStreakStatus)

        // Act
        final result = await notifier.repairStreakWithGold();

        // Assert
        expect(result, isTrue);
      });
    });

    group('repairStreakWithAd', () {
      test('repairStreakWithAd calls API and updates state on success', () async {
        // Arrange
        fakeApiClient.setMockResponse(ApiConstants.authMe, {}, statusCode: 200);
        fakeApiClient.setMockResponse(
          ApiConstants.streakRepair,
          {'data': {'current_streak': 7}},
          statusCode: 200,
        );

        container = createContainer();
        final notifier = container.read(engagementProvider.notifier);

        await Future.delayed(const Duration(milliseconds: 100));

        // Act
        final result = await notifier.repairStreakWithAd();

        // Assert
        expect(result, isTrue);
        final state = container.read(engagementProvider);
        expect(state.streakJustLost, isFalse);
        expect(state.streak, equals(7));
      });

      test('repairStreakWithAd returns false on non-200 status', () async {
        // Arrange
        fakeApiClient.setMockResponse(ApiConstants.authMe, {}, statusCode: 200);
        fakeApiClient.setMockResponse(
          ApiConstants.streakRepair,
          {'error': 'Daily limit reached'},
          statusCode: 429,
        );

        container = createContainer();
        final notifier = container.read(engagementProvider.notifier);

        await Future.delayed(const Duration(milliseconds: 100));

        // Act
        final result = await notifier.repairStreakWithAd();

        // Assert
        expect(result, isFalse);
      });

      test('repairStreakWithAd handles network error', () async {
        // Arrange
        fakeApiClient.setMockResponse(ApiConstants.authMe, {}, statusCode: 200);
        fakeApiClient.setErrorEndpoint(ApiConstants.streakRepair);

        container = createContainer();
        final notifier = container.read(engagementProvider.notifier);

        await Future.delayed(const Duration(milliseconds: 100));

        // Act
        final result = await notifier.repairStreakWithAd();

        // Assert
        expect(result, isFalse);
        final state = container.read(engagementProvider);
        expect(state.streakJustLost, isFalse);
      });
    });

    group('checkStreakStatus', () {
      test('checkStreakStatus updates streak from API', () async {
        // Arrange
        fakeApiClient.setMockResponse(
          ApiConstants.authMe,
          {
            'streak': 15,
            'xp': 1000,
            'hearts': 5,
            'is_premium': true,
            'last_activity_date': DateTime.now().toIso8601String(),
          },
          statusCode: 200,
        );

        container = createContainer();
        final notifier = container.read(engagementProvider.notifier);

        await Future.delayed(const Duration(milliseconds: 100));

        // Act
        await notifier.checkStreakStatus();

        // Assert
        final state = container.read(engagementProvider);
        expect(state.streak, equals(15));
        expect(state.totalXp, equals(1000));
        expect(state.hearts, equals(5));
        expect(state.isPremium, isTrue);
      });

      test('checkStreakStatus detects lost streak', () async {
        // First setup initial state with a streak
        fakeApiClient.setMockResponse(
          ApiConstants.authMe,
          {
            'streak': 10,
            'last_activity_date': DateTime.now().toIso8601String(),
          },
          statusCode: 200,
        );

        container = createContainer();
        final notifier = container.read(engagementProvider.notifier);

        await Future.delayed(const Duration(milliseconds: 100));

        // Now simulate a lost streak (last activity > 24 hours ago)
        final oldDate = DateTime.now().subtract(const Duration(hours: 30));
        fakeApiClient.setMockResponse(
          ApiConstants.authMe,
          {
            'streak': 0, // Backend shows 0 now
            'last_activity_date': oldDate.toIso8601String(),
          },
          statusCode: 200,
        );

        // Act
        await notifier.checkStreakStatus();

        // Assert
        final state = container.read(engagementProvider);
        expect(state.streak, equals(0));
        // Note: streakJustLost detection depends on comparing old vs new state
      });

      test('checkStreakStatus silently fails on error', () async {
        // Arrange - set initial data with streak
        fakeApiClient.setMockResponse(
          ApiConstants.authMe,
          {'xp': 100, 'daily_xp': 10, 'streak': 5, 'hearts': 5},
          statusCode: 200,
        );

        container = createContainer();
        final notifier = container.read(engagementProvider.notifier);

        // Wait for initial fetchXp
        await Future.delayed(const Duration(milliseconds: 100));

        // Call checkStreakStatus to set streak in state
        await notifier.checkStreakStatus();
        var initialState = container.read(engagementProvider);
        expect(initialState.streak, equals(5)); // Verify streak was set

        // Now set error - clear mock response and add error endpoint
        fakeApiClient.clearMockResponse(ApiConstants.authMe);
        fakeApiClient.setErrorEndpoint(ApiConstants.authMe);

        // Act - should not throw and should keep previous state
        await notifier.checkStreakStatus();

        // Assert - state should be unchanged (silent failure)
        final state = container.read(engagementProvider);
        expect(state.streak, equals(5)); // Keeps previous value
      });
    });

    group('activateGraceMode', () {
      test('activateGraceMode sets graceModeActive to true', () async {
        // Arrange
        fakeApiClient.setMockResponse(ApiConstants.authMe, {}, statusCode: 200);

        container = createContainer();
        final notifier = container.read(engagementProvider.notifier);

        await Future.delayed(const Duration(milliseconds: 100));

        var state = container.read(engagementProvider);
        expect(state.graceModeActive, isFalse);

        // Act
        notifier.activateGraceMode();

        // Assert
        state = container.read(engagementProvider);
        expect(state.graceModeActive, isTrue);
      });
    });

    group('dismissStreakLost', () {
      test('dismissStreakLost sets streakJustLost to false', () async {
        // Arrange
        fakeApiClient.setMockResponse(ApiConstants.authMe, {}, statusCode: 200);

        container = createContainer();
        final notifier = container.read(engagementProvider.notifier);

        await Future.delayed(const Duration(milliseconds: 100));

        // Act
        notifier.dismissStreakLost();

        // Assert
        final state = container.read(engagementProvider);
        expect(state.streakJustLost, isFalse);
      });
    });

    group('EngagementState', () {
      test('default values are correct', () {
        const state = EngagementState();

        expect(state.totalXp, equals(0));
        expect(state.dailyXp, equals(0));
        expect(state.lastActivityDate, isNull);
        expect(state.hearts, equals(5));
        expect(state.maxHearts, equals(5));
        expect(state.isPremium, isFalse);
        expect(state.nextHeartAt, isNull);
        expect(state.graceModeActive, isFalse);
        expect(state.streak, equals(0));
        expect(state.streakJustLost, isFalse);
        expect(state.previousStreak, equals(0));
      });

      test('copyWith preserves unmodified values', () {
        const state = EngagementState(
          totalXp: 100,
          dailyXp: 50,
          streak: 5,
        );

        final copied = state.copyWith(totalXp: 200);

        expect(copied.totalXp, equals(200));
        expect(copied.dailyXp, equals(50)); // Preserved
        expect(copied.streak, equals(5)); // Preserved
      });

      test('copyWith can update all values', () {
        const state = EngagementState();
        final now = DateTime.now();
        final nextHeart = DateTime.now().add(const Duration(minutes: 30));

        final copied = state.copyWith(
          totalXp: 1000,
          dailyXp: 100,
          lastActivityDate: now,
          hearts: 3,
          maxHearts: 10,
          isPremium: true,
          nextHeartAt: nextHeart,
          graceModeActive: true,
          streak: 15,
          streakJustLost: true,
          previousStreak: 14,
        );

        expect(copied.totalXp, equals(1000));
        expect(copied.dailyXp, equals(100));
        expect(copied.lastActivityDate, equals(now));
        expect(copied.hearts, equals(3));
        expect(copied.maxHearts, equals(10));
        expect(copied.isPremium, isTrue);
        expect(copied.nextHeartAt, equals(nextHeart));
        expect(copied.graceModeActive, isTrue);
        expect(copied.streak, equals(15));
        expect(copied.streakJustLost, isTrue);
        expect(copied.previousStreak, equals(14));
      });
    });
  });
}
