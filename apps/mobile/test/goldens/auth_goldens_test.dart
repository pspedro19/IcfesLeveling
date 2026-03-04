import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'package:icfes_mobile/features/auth/presentation/pages/login_page.dart';
import 'package:icfes_mobile/core/services/onboarding_service.dart';
import 'package:icfes_mobile/core/network/api_client.dart';
import 'package:icfes_mobile/core/providers/storage_providers.dart';
import 'package:icfes_mobile/core/sync/connectivity_monitor.dart';
import 'package:icfes_mobile/features/auth/domain/repositories/auth_repository.dart';
import 'package:icfes_mobile/features/auth/presentation/providers/auth_provider.dart';

import '../mocks/mock_providers.dart';
import 'golden_test_helper.dart';

void main() {
  group('Auth Golden Tests', () {
    late FakeApiClient fakeApiClient;

    setUp(() async {
      await goldenSetUp();
      fakeApiClient = FakeApiClient();
      setupAllGoldenMocks(fakeApiClient);
    });

    tearDown(goldenTearDown);

    testWidgets('login_page_social golden', (tester) async {
      await tester.binding.setSurfaceSize(goldenSize);
      addTearDown(() => tester.binding.setSurfaceSize(null));

      final prefs = await SharedPreferences.getInstance();

      await tester.pumpWidget(
        ProviderScope(
          overrides: [
            apiClientProvider.overrideWithValue(fakeApiClient),
            // No user — login page should show unauthenticated state
            authRepositoryProvider.overrideWithValue(MockAuthRepository(user: null)),
            questionCacheProvider.overrideWithValue(MockQuestionCache()),
            connectivityMonitorProvider.overrideWithValue(MockConnectivityMonitor()),
            sharedPreferencesProvider.overrideWithValue(prefs),
          ],
          child: MaterialApp(
            theme: goldenDarkTheme,
            debugShowCheckedModeBanner: false,
            home: const LoginPage(),
          ),
        ),
      );

      await pumpAndWait(tester);

      await expectLater(
        find.byType(LoginPage),
        matchesGoldenFile('screenshots/login_page_social.png'),
      );
    });

    // Note: SplashPage golden is skipped because SplashPage._handleNavigation()
    // immediately triggers a 2s Future.delayed + GoRouter navigation in initState,
    // which is incompatible with golden tests (pending timer + no GoRouter).
  });
}
