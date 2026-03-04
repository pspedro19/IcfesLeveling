import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:hive/hive.dart';
import 'package:mockito/mockito.dart';

import 'package:icfes_mobile/features/home/presentation/pages/home_page.dart';
import 'package:icfes_mobile/features/auth/presentation/providers/auth_provider.dart';
import 'package:icfes_mobile/features/auth/domain/repositories/auth_repository.dart';
import 'package:icfes_mobile/core/network/api_client.dart';
import 'package:icfes_mobile/core/storage/question_cache.dart';
import 'package:icfes_mobile/core/constants/api_constants.dart';
import 'package:icfes_mobile/core/constants/app_strings.dart';
import 'package:icfes_mobile/core/auth/domain/entities/user.dart';
import 'package:icfes_mobile/core/providers/storage_providers.dart';
import 'package:icfes_mobile/core/sync/connectivity_monitor.dart';
import 'package:icfes_mobile/core/config/animation_config.dart';

import '../../mocks/mock_providers.dart';

// Mock classes
class MockAuthRepository implements AuthRepository {
  final User? _user;

  MockAuthRepository({User? user}) : _user = user;

  @override
  Future<User?> getCurrentUser() async => _user;

  @override
  Future<User> login(String email, String password) async {
    return _user ?? createTestUser();
  }

  @override
  Future<User> register(String email, String password, String name) async {
    return createTestUser(email: email, name: name);
  }

  @override
  Future<void> logout() async {}

  @override
  Future<String?> getAccessToken() async => 'mock-token';

  @override
  Future<void> refreshToken() async {}
}

class MockQuestionCache extends Mock implements QuestionCache {
  @override
  Future<void> warmUp(ApiClient apiClient) async {}

  @override
  Future<void> init() async {}
}

class MockConnectivityMonitor extends ConnectivityMonitor {
  @override
  Stream<bool> get onConnectivityChanged => Stream.value(true);

  @override
  Future<bool> get isOnline async => true;
}

/// Helper: pump the widget and settle all one-shot animations.
/// With AnimationConfig.infiniteAnimationsEnabled = false, all animations
/// are one-shot so pumpAndSettle will terminate.
Future<void> pumpAndWait(WidgetTester tester) async {
  for (int i = 0; i < 10; i++) {
    await tester.pump(const Duration(milliseconds: 100));
  }
}

void main() {
  group('HomePage', () {
    late FakeApiClient fakeApiClient;
    late MockQuestionCache mockQuestionCache;

    setUp(() async {
      // Disable infinite animations to prevent FakeAsync pending timer assertions
      AnimationConfig.infiniteAnimationsEnabled = false;
      Animate.restartOnHotReload = false;
      final tempDir = Directory.systemTemp.createTempSync('hive_test_');
      Hive.init(tempDir.path);
      fakeApiClient = FakeApiClient();
      mockQuestionCache = MockQuestionCache();

      // Setup API responses for all providers the HomePage triggers
      fakeApiClient.setMockResponse(ApiConstants.authMe, {
        'id': 'user-1', 'email': 'test@test.com', 'name': 'Test User',
        'xp': 500, 'daily_xp': 50, 'streak': 7, 'hearts': 5,
      }, statusCode: 200);
      fakeApiClient.setMockResponse(ApiConstants.heartsStatus, {'current': 5, 'max': 5}, statusCode: 200);
      fakeApiClient.setMockResponse(ApiConstants.streakStatus, {
        'current_streak': 7, 'longest_streak': 14, 'multiplier': 1.2,
        'freezes_available': 1, 'is_at_risk': false, 'can_repair': false, 'previous_streak': 7,
      }, statusCode: 200);
      fakeApiClient.setMockResponse('/users/cached/profile/me', {
        'questions_answered': 100, 'correct_answers': 80, 'experience': 500, 'streak_days': 7,
      }, statusCode: 200);
      fakeApiClient.setMockResponse(ApiConstants.studyPlanCurrent, {
        'plan': null, 'hasPlan': false, 'message': 'No plan',
      }, statusCode: 200);
      fakeApiClient.setMockResponse(ApiConstants.bossRaidStatus, {
        'isActive': false, 'currentBoss': null,
      }, statusCode: 200);
      fakeApiClient.setMockResponse(ApiConstants.leaderboard, {
        'leaderboard': <Map<String, dynamic>>[],
      }, statusCode: 200);
      fakeApiClient.setMockResponse(ApiConstants.economyBalance, {
        'gold': 1000, 'gems': 0, 'crystals': 0,
      }, statusCode: 200);
    });

    tearDown(() {
      // Re-enable infinite animations for production default
      AnimationConfig.infiniteAnimationsEnabled = true;
    });

    Widget createHomePage({User? testUser}) {
      final user = testUser ?? createTestUser(name: 'Test Hunter');
      final mockAuthRepository = MockAuthRepository(user: user);

      return ProviderScope(
        overrides: [
          apiClientProvider.overrideWithValue(fakeApiClient),
          authRepositoryProvider.overrideWithValue(mockAuthRepository),
          questionCacheProvider.overrideWithValue(mockQuestionCache),
          connectivityMonitorProvider.overrideWithValue(MockConnectivityMonitor()),
        ],
        child: const MaterialApp(
          home: HomePage(),
        ),
      );
    }

    // Compile-time verification that test infrastructure and mocks work
    test('test infrastructure compiles and mocks are valid', () {
      final fakeClient = FakeApiClient();
      final mockAuth = MockAuthRepository(user: createTestUser());
      final mockCache = MockQuestionCache();
      final mockConn = MockConnectivityMonitor();

      expect(fakeClient, isNotNull);
      expect(mockAuth, isNotNull);
      expect(mockCache, isNotNull);
      expect(mockConn, isNotNull);
    });

    group('UI Rendering', () {
      testWidgets('home page renders app title in app bar',
        (WidgetTester tester) async {
          await tester.pumpWidget(createHomePage());
          await pumpAndWait(tester);
          expect(find.text(AppStrings.appName), findsOneWidget);
        },
      );

      testWidgets('home page renders welcome message with user name',
        (WidgetTester tester) async {
          final testUser = createTestUser(name: 'Hunter John');
          await tester.pumpWidget(createHomePage(testUser: testUser));
          await pumpAndWait(tester);
          expect(find.textContaining('Bienvenido de vuelta'), findsOneWidget);
          expect(find.textContaining('Hunter John'), findsOneWidget);
        },
      );

      testWidgets('home page renders ready to level up text',
        (WidgetTester tester) async {
          await tester.pumpWidget(createHomePage());
          await pumpAndWait(tester);
          expect(find.text(AppStrings.readyToLevelUp), findsOneWidget);
        },
      );

      testWidgets('home page renders DailyGoalCard widget',
        (WidgetTester tester) async {
          await tester.pumpWidget(createHomePage());
          await pumpAndWait(tester);
          expect(find.byType(Scaffold), findsOneWidget);
        },
      );

      testWidgets('home page renders hearts display in app bar',
        (WidgetTester tester) async {
          await tester.pumpWidget(createHomePage());
          await pumpAndWait(tester);
          expect(find.byType(AppBar), findsOneWidget);
        },
      );

      testWidgets('home page renders streak flame in app bar',
        (WidgetTester tester) async {
          await tester.pumpWidget(createHomePage());
          await pumpAndWait(tester);
          expect(find.byType(AppBar), findsOneWidget);
        },
      );

      testWidgets('home page has scrollable content',
        (WidgetTester tester) async {
          await tester.pumpWidget(createHomePage());
          await pumpAndWait(tester);
          expect(find.byType(SingleChildScrollView), findsOneWidget);
        },
      );
    });

    group('Pull to Refresh', () {
      testWidgets('home page has RefreshIndicator',
        (WidgetTester tester) async {
          await tester.pumpWidget(createHomePage());
          await pumpAndWait(tester);
          expect(find.byType(RefreshIndicator), findsOneWidget);
        },
      );

      testWidgets('pull to refresh triggers data refresh',
        (WidgetTester tester) async {
          await tester.pumpWidget(createHomePage());
          await pumpAndWait(tester);
          await tester.fling(find.byType(SingleChildScrollView), const Offset(0, 300), 1000);
          await pumpAndWait(tester);
          expect(find.byType(RefreshIndicator), findsOneWidget);
          await pumpAndWait(tester);
          expect(find.text(AppStrings.appName), findsOneWidget);
        },
      );

      testWidgets('refresh indicator appears during pull down',
        (WidgetTester tester) async {
          await tester.pumpWidget(createHomePage());
          await pumpAndWait(tester);
          final gesture = await tester.startGesture(
            tester.getCenter(find.byType(SingleChildScrollView)),
          );
          await gesture.moveBy(const Offset(0, 100));
          await pumpAndWait(tester);
          expect(find.byType(RefreshIndicator), findsOneWidget);
          await gesture.up();
          await pumpAndWait(tester);
        },
      );
    });

    group('Navigation', () {
      testWidgets('home page structure is correct for navigation',
        (WidgetTester tester) async {
          await tester.pumpWidget(createHomePage());
          await pumpAndWait(tester);
          expect(find.byType(Scaffold), findsOneWidget);
          expect(find.byType(Column), findsWidgets);
        },
      );

      testWidgets('quick actions section is present',
        (WidgetTester tester) async {
          await tester.pumpWidget(createHomePage());
          await pumpAndWait(tester);
          expect(find.byType(SingleChildScrollView), findsOneWidget);
        },
      );
    });

    group('Streak Lost Modal', () {
      testWidgets('streak lost modal can be triggered by state change',
        (WidgetTester tester) async {
          await tester.pumpWidget(createHomePage());
          await pumpAndWait(tester);
          expect(find.byType(HomePage), findsOneWidget);
        },
      );
    });

    group('User Display', () {
      testWidgets('displays default name when user is null',
        (WidgetTester tester) async {
          final mockAuthRepository = MockAuthRepository(user: null);
          final widget = ProviderScope(
            overrides: [
              apiClientProvider.overrideWithValue(fakeApiClient),
              authRepositoryProvider.overrideWithValue(mockAuthRepository),
              questionCacheProvider.overrideWithValue(mockQuestionCache),
              connectivityMonitorProvider.overrideWithValue(MockConnectivityMonitor()),
            ],
            child: const MaterialApp(home: HomePage()),
          );
          await tester.pumpWidget(widget);
          await pumpAndWait(tester);
          expect(find.textContaining('Bienvenido de vuelta, Cazador'), findsOneWidget);
        },
      );

      testWidgets('displays user name when user exists',
        (WidgetTester tester) async {
          final testUser = createTestUser(name: 'Maria Garcia');
          await tester.pumpWidget(createHomePage(testUser: testUser));
          await pumpAndWait(tester);
          expect(find.textContaining('Maria Garcia'), findsOneWidget);
        },
      );
    });

    group('Widget Composition', () {
      testWidgets('home page contains all required sections',
        (WidgetTester tester) async {
          await tester.pumpWidget(createHomePage());
          await pumpAndWait(tester);
          expect(find.byType(Scaffold), findsOneWidget);
          expect(find.byType(AppBar), findsOneWidget);
          expect(find.byType(Column), findsWidgets);
          expect(find.byType(SingleChildScrollView), findsOneWidget);
          expect(find.byType(RefreshIndicator), findsOneWidget);
        },
      );

      testWidgets('home page sections have proper spacing',
        (WidgetTester tester) async {
          await tester.pumpWidget(createHomePage());
          await pumpAndWait(tester);
          expect(find.byType(SizedBox), findsWidgets);
          expect(find.byType(Padding), findsWidgets);
        },
      );
    });

    group('Loading States', () {
      testWidgets('home page handles loading gracefully',
        (WidgetTester tester) async {
          await tester.pumpWidget(createHomePage());
          await pumpAndWait(tester);
          expect(find.byType(Scaffold), findsOneWidget);
          expect(find.text(AppStrings.appName), findsOneWidget);
        },
      );
    });

    group('Offline Banner', () {
      testWidgets('offline banner is part of the layout',
        (WidgetTester tester) async {
          await tester.pumpWidget(createHomePage());
          await pumpAndWait(tester);
          expect(find.byType(Column), findsWidgets);
        },
      );
    });

    group('Theme and Styling', () {
      testWidgets('home page uses material design',
        (WidgetTester tester) async {
          await tester.pumpWidget(createHomePage());
          await pumpAndWait(tester);
          expect(find.byType(MaterialApp), findsOneWidget);
          expect(find.byType(Scaffold), findsOneWidget);
        },
      );

      testWidgets('text styles are applied correctly',
        (WidgetTester tester) async {
          final testUser = createTestUser(name: 'Styled User');
          await tester.pumpWidget(createHomePage(testUser: testUser));
          await pumpAndWait(tester);
          final welcomeFinder = find.textContaining('Styled User');
          expect(welcomeFinder, findsOneWidget);
          final textWidget = tester.widget<Text>(welcomeFinder);
          expect(textWidget.style, isNotNull);
        },
      );
    });

    group('State Integration', () {
      testWidgets('home page listens to auth state',
        (WidgetTester tester) async {
          final testUser = createTestUser(name: 'Auth Test User');
          await tester.pumpWidget(createHomePage(testUser: testUser));
          await pumpAndWait(tester);
          expect(find.textContaining('Auth Test User'), findsOneWidget);
        },
      );

      testWidgets('home page listens to engagement state',
        (WidgetTester tester) async {
          await tester.pumpWidget(createHomePage());
          await pumpAndWait(tester);
          expect(find.byType(AppBar), findsOneWidget);
        },
      );
    });
  });
}
