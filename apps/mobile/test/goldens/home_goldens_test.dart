import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:icfes_mobile/features/home/presentation/pages/home_page.dart';

import 'golden_test_helper.dart';

void main() {
  group('Home Golden Tests', () {
    setUp(() async {
      await goldenSetUp();
    });

    tearDown(goldenTearDown);

    testWidgets('home_page golden', (tester) async {
      await tester.binding.setSurfaceSize(goldenSize);
      addTearDown(() => tester.binding.setSurfaceSize(null));

      await tester.pumpWidget(
        buildGoldenApp(const HomePage()),
      );

      await pumpAndWait(tester);

      await expectLater(
        find.byType(HomePage),
        matchesGoldenFile('screenshots/home_page.png'),
      );
    });
  });
}
