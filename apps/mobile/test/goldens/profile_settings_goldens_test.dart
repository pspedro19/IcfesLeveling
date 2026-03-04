import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'package:icfes_mobile/features/profile/presentation/pages/profile_page.dart';
import 'package:icfes_mobile/features/settings/presentation/pages/settings_page.dart';
import 'package:icfes_mobile/core/services/onboarding_service.dart';
import 'package:icfes_mobile/core/services/notification_service.dart';
import 'package:icfes_mobile/core/network/api_client.dart';
import 'package:icfes_mobile/core/providers/storage_providers.dart';
import 'package:icfes_mobile/core/sync/connectivity_monitor.dart';
import 'package:icfes_mobile/features/auth/domain/repositories/auth_repository.dart';
import 'package:icfes_mobile/features/auth/presentation/providers/auth_provider.dart';

import '../mocks/mock_providers.dart';
import 'golden_test_helper.dart';

void main() {
  group('Profile & Settings Golden Tests', () {
    late FakeApiClient fakeApiClient;

    setUp(() async {
      await goldenSetUp();
      fakeApiClient = FakeApiClient();
      setupAllGoldenMocks(fakeApiClient);
    });

    tearDown(goldenTearDown);

    testWidgets('profile_page golden', (tester) async {
      await tester.binding.setSurfaceSize(goldenSize);
      addTearDown(() => tester.binding.setSurfaceSize(null));

      await tester.pumpWidget(
        buildGoldenApp(const ProfilePage()),
      );

      await pumpAndWait(tester);

      await expectLater(
        find.byType(ProfilePage),
        matchesGoldenFile('screenshots/profile_page.png'),
      );
    });

    testWidgets('settings_page golden', (tester) async {
      await tester.binding.setSurfaceSize(goldenSize);
      addTearDown(() => tester.binding.setSurfaceSize(null));

      final prefs = await SharedPreferences.getInstance();

      await tester.pumpWidget(
        ProviderScope(
          overrides: [
            apiClientProvider.overrideWithValue(fakeApiClient),
            authRepositoryProvider.overrideWithValue(
              MockAuthRepository(user: createTestUser(name: 'Hunter Pro')),
            ),
            questionCacheProvider.overrideWithValue(MockQuestionCache()),
            connectivityMonitorProvider.overrideWithValue(MockConnectivityMonitor()),
            sharedPreferencesProvider.overrideWithValue(prefs),
            // Override notificationServiceInitProvider to avoid Firebase
            notificationServiceInitProvider.overrideWith(
              (ref) async => NotificationService(prefs: prefs),
            ),
          ],
          child: MaterialApp(
            theme: goldenDarkTheme,
            debugShowCheckedModeBanner: false,
            home: const SettingsPage(),
          ),
        ),
      );

      await pumpAndWait(tester);

      await expectLater(
        find.byType(SettingsPage),
        matchesGoldenFile('screenshots/settings_page.png'),
      );
    });
  });
}
