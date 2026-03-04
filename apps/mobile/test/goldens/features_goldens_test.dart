import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:icfes_mobile/features/leagues/presentation/pages/leagues_page.dart';
import 'package:icfes_mobile/features/achievements/presentation/pages/achievements_page.dart';
import 'package:icfes_mobile/features/achievements/presentation/providers/achievements_provider.dart';
import 'package:icfes_mobile/features/shop/presentation/pages/shop_page.dart';

import '../mocks/mock_providers.dart';
import 'golden_test_helper.dart';

void main() {
  group('Features Golden Tests', () {
    late FakeApiClient fakeApiClient;

    setUp(() async {
      await goldenSetUp();
      fakeApiClient = FakeApiClient();
      setupAllGoldenMocks(fakeApiClient);
    });

    tearDown(goldenTearDown);

    testWidgets('leagues_page golden', (tester) async {
      await tester.binding.setSurfaceSize(goldenSize);
      addTearDown(() => tester.binding.setSurfaceSize(null));

      await tester.pumpWidget(
        buildGoldenApp(const LeaguesPage(), fakeApiClient: fakeApiClient),
      );

      // Extra pumps for leaderboard data to load
      await pumpAndWait(tester);
      await pumpAndWait(tester);

      await expectLater(
        find.byType(LeaguesPage),
        matchesGoldenFile('screenshots/leagues_page.png'),
      );
    });

    testWidgets('achievements_page golden', (tester) async {
      await tester.binding.setSurfaceSize(goldenSize);
      addTearDown(() => tester.binding.setSurfaceSize(null));

      await tester.pumpWidget(
        buildGoldenApp(
          const AchievementsPage(),
          fakeApiClient: fakeApiClient,
          extraOverrides: [
            // AchievementsPage uses its own achievementsApiClientProvider
            achievementsApiClientProvider.overrideWithValue(fakeApiClient),
          ],
        ),
      );

      // Extra pumps for achievements data to load
      await pumpAndWait(tester);
      await pumpAndWait(tester);

      await expectLater(
        find.byType(AchievementsPage),
        matchesGoldenFile('screenshots/achievements_page.png'),
      );
    });

    testWidgets('shop_page golden', (tester) async {
      await tester.binding.setSurfaceSize(goldenSize);
      addTearDown(() => tester.binding.setSurfaceSize(null));

      await tester.pumpWidget(
        buildGoldenApp(const ShopPage(), fakeApiClient: fakeApiClient),
      );

      // Extra pumps for shop items and balance to load
      await pumpAndWait(tester);
      await pumpAndWait(tester);

      await expectLater(
        find.byType(ShopPage),
        matchesGoldenFile('screenshots/shop_page.png'),
      );
    });
  });
}
