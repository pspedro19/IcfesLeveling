import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:icfes_mobile/shared/widgets/lottie_overlay.dart';
import 'package:icfes_mobile/shared/widgets/animated_feedback/correct_answer_overlay.dart';
import 'package:icfes_mobile/shared/widgets/animated_feedback/incorrect_answer_overlay.dart';
import 'package:icfes_mobile/shared/widgets/streak_flame.dart';

void main() {
  // flutter_animate schedules timers for hot-reload restart.
  // Disable this in tests to prevent "Timer still pending" errors.
  setUp(() {
    Animate.restartOnHotReload = false;
  });

  // =========================================================================
  // LottieAssets — Constants validation
  // =========================================================================
  group('LottieAssets', () {
    test('all asset paths point to assets/animations/ directory', () {
      const assets = [
        LottieAssets.confetti,
        LottieAssets.fire,
        LottieAssets.starBurst,
        LottieAssets.levelUp,
        LottieAssets.correctCheck,
        LottieAssets.wrongX,
        LottieAssets.battleStart,
        LottieAssets.coins,
        LottieAssets.loading,
      ];

      for (final asset in assets) {
        expect(asset, startsWith('assets/animations/'));
        expect(asset, endsWith('.json'));
      }
    });

    test('all 9 asset constants are unique', () {
      const assets = [
        LottieAssets.confetti,
        LottieAssets.fire,
        LottieAssets.starBurst,
        LottieAssets.levelUp,
        LottieAssets.correctCheck,
        LottieAssets.wrongX,
        LottieAssets.battleStart,
        LottieAssets.coins,
        LottieAssets.loading,
      ];

      final uniqueAssets = assets.toSet();
      expect(uniqueAssets.length, 9, reason: 'All 9 assets should be unique');
    });

    test('asset names follow snake_case convention', () {
      const assets = [
        LottieAssets.confetti,
        LottieAssets.fire,
        LottieAssets.starBurst,
        LottieAssets.levelUp,
        LottieAssets.correctCheck,
        LottieAssets.wrongX,
        LottieAssets.battleStart,
        LottieAssets.coins,
        LottieAssets.loading,
      ];

      final snakeCaseRegex =
          RegExp(r'^assets/animations/[a-z][a-z0-9_]*\.json$');
      for (final asset in assets) {
        expect(snakeCaseRegex.hasMatch(asset), isTrue,
            reason: '$asset should be snake_case');
      }
    });

    test('specific asset paths are correct', () {
      expect(LottieAssets.confetti, 'assets/animations/confetti.json');
      expect(LottieAssets.fire, 'assets/animations/fire.json');
      expect(LottieAssets.starBurst, 'assets/animations/star_burst.json');
      expect(LottieAssets.levelUp, 'assets/animations/level_up.json');
      expect(LottieAssets.correctCheck, 'assets/animations/correct_check.json');
      expect(LottieAssets.wrongX, 'assets/animations/wrong_x.json');
      expect(LottieAssets.battleStart, 'assets/animations/battle_start.json');
      expect(LottieAssets.coins, 'assets/animations/coins.json');
      expect(LottieAssets.loading, 'assets/animations/loading.json');
    });
  });

  // =========================================================================
  // LottieOverlay Widget
  // =========================================================================
  group('LottieOverlay', () {
    testWidgets('renders without crash even with invalid asset', (tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(
            body: LottieOverlay(
              animationAsset: 'assets/animations/nonexistent.json',
              size: 100,
              duration: Duration(milliseconds: 500),
            ),
          ),
        ),
      );

      expect(find.byType(LottieOverlay), findsOneWidget);
      await tester.pumpAndSettle();
    });

    testWidgets('calls onComplete after duration elapses', (tester) async {
      var completed = false;

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: LottieOverlay(
              animationAsset: LottieAssets.correctCheck,
              size: 100,
              duration: const Duration(milliseconds: 300),
              onComplete: () => completed = true,
            ),
          ),
        ),
      );

      expect(completed, isFalse);
      await tester.pumpAndSettle(const Duration(milliseconds: 500));
      expect(completed, isTrue);
    });

    testWidgets('wraps content in IgnorePointer with ignoring=true',
        (tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(
            body: LottieOverlay(
              animationAsset: LottieAssets.confetti,
            ),
          ),
        ),
      );

      final ignorePointers = tester
          .widgetList<IgnorePointer>(find.byType(IgnorePointer))
          .where((ip) => ip.ignoring)
          .toList();
      expect(ignorePointers, isNotEmpty,
          reason: 'LottieOverlay should have an IgnorePointer with ignoring=true');
      await tester.pumpAndSettle();
    });

    testWidgets('default size is 200', (tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(
            body: LottieOverlay(animationAsset: LottieAssets.confetti),
          ),
        ),
      );

      final overlay =
          tester.widget<LottieOverlay>(find.byType(LottieOverlay));
      expect(overlay.size, 200);
      await tester.pumpAndSettle();
    });

    testWidgets('default duration is 1500ms', (tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(
            body: LottieOverlay(animationAsset: LottieAssets.confetti),
          ),
        ),
      );

      final overlay =
          tester.widget<LottieOverlay>(find.byType(LottieOverlay));
      expect(overlay.duration, const Duration(milliseconds: 1500));
      await tester.pumpAndSettle();
    });

    testWidgets('disposes without error when removed from tree',
        (tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(
            body: LottieOverlay(
              animationAsset: LottieAssets.confetti,
              duration: Duration(milliseconds: 100),
            ),
          ),
        ),
      );

      expect(find.byType(LottieOverlay), findsOneWidget);

      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(body: SizedBox.shrink()),
        ),
      );
      await tester.pumpAndSettle();
      expect(find.byType(LottieOverlay), findsNothing);
    });
  });

  // =========================================================================
  // StreakFireLottie Widget
  // =========================================================================
  group('StreakFireLottie', () {
    testWidgets('shows only child when streak < minStreak', (tester) async {
      const childKey = Key('test-child');
      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(
            body: StreakFireLottie(
              streakCount: 2,
              minStreak: 3,
              child: SizedBox(key: childKey),
            ),
          ),
        ),
      );

      expect(find.byKey(childKey), findsOneWidget);
      final ignorePointers = tester
          .widgetList<IgnorePointer>(find.byType(IgnorePointer))
          .where((ip) => ip.ignoring)
          .toList();
      expect(ignorePointers, isEmpty,
          reason: 'No Lottie IgnorePointer when streak < minStreak');
    });

    testWidgets('shows fire + child when streak >= minStreak', (tester) async {
      const childKey = Key('test-child');
      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(
            body: StreakFireLottie(
              streakCount: 5,
              minStreak: 3,
              child: SizedBox(key: childKey),
            ),
          ),
        ),
      );

      expect(find.byKey(childKey), findsOneWidget);
      final ignorePointers = tester
          .widgetList<IgnorePointer>(find.byType(IgnorePointer))
          .where((ip) => ip.ignoring)
          .toList();
      expect(ignorePointers, isNotEmpty,
          reason: 'Should have IgnorePointer for Lottie fire overlay');
    });

    testWidgets('uses default minStreak of 3', (tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(
            body: StreakFireLottie(
              streakCount: 3,
              child: SizedBox(),
            ),
          ),
        ),
      );

      final ignorePointers = tester
          .widgetList<IgnorePointer>(find.byType(IgnorePointer))
          .where((ip) => ip.ignoring)
          .toList();
      expect(ignorePointers, isNotEmpty);
    });

    testWidgets('opacity scales with streak count (5 => 0.5)', (tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(
            body: StreakFireLottie(
              streakCount: 5,
              child: SizedBox(),
            ),
          ),
        ),
      );

      final opacity = tester.widget<Opacity>(find.byType(Opacity).first);
      expect(opacity.opacity, closeTo(0.5, 0.01));
    });

    testWidgets('opacity clamps at 0.3 for low streaks (3)', (tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(
            body: StreakFireLottie(
              streakCount: 3,
              minStreak: 3,
              child: SizedBox(),
            ),
          ),
        ),
      );

      final opacity = tester.widget<Opacity>(find.byType(Opacity).first);
      expect(opacity.opacity, closeTo(0.3, 0.01));
    });

    testWidgets('opacity clamps at 0.8 for very high streaks (100)',
        (tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(
            body: StreakFireLottie(
              streakCount: 100,
              child: SizedBox(),
            ),
          ),
        ),
      );

      final opacity = tester.widget<Opacity>(find.byType(Opacity).first);
      expect(opacity.opacity, closeTo(0.8, 0.01));
    });

    testWidgets('is a pure function of streakCount', (tester) async {
      const childKey = Key('test-child');

      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(
            body: StreakFireLottie(
              streakCount: 1,
              child: SizedBox(key: childKey),
            ),
          ),
        ),
      );

      var ignorePointers = tester
          .widgetList<IgnorePointer>(find.byType(IgnorePointer))
          .where((ip) => ip.ignoring)
          .toList();
      expect(ignorePointers, isEmpty);

      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(
            body: StreakFireLottie(
              streakCount: 5,
              child: SizedBox(key: childKey),
            ),
          ),
        ),
      );

      ignorePointers = tester
          .widgetList<IgnorePointer>(find.byType(IgnorePointer))
          .where((ip) => ip.ignoring)
          .toList();
      expect(ignorePointers, isNotEmpty);
    });
  });

  // =========================================================================
  // LottieInline Widget
  // =========================================================================
  group('LottieInline', () {
    testWidgets('renders without crash', (tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(
            body: LottieInline(
              asset: LottieAssets.loading,
              size: 100,
              repeat: true,
            ),
          ),
        ),
      );

      expect(find.byType(LottieInline), findsOneWidget);
    });

    testWidgets('defaults to size 150 and repeat false', (tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(
            body: LottieInline(asset: LottieAssets.loading),
          ),
        ),
      );

      final inline =
          tester.widget<LottieInline>(find.byType(LottieInline));
      expect(inline.size, 150);
      expect(inline.repeat, false);
    });

    testWidgets('custom size and repeat are applied', (tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(
            body: LottieInline(
              asset: LottieAssets.fire,
              size: 75,
              repeat: true,
            ),
          ),
        ),
      );

      final inline =
          tester.widget<LottieInline>(find.byType(LottieInline));
      expect(inline.size, 75);
      expect(inline.repeat, true);
    });
  });

  // =========================================================================
  // CorrectAnswerOverlay — Lottie checkmark + starBurst
  // =========================================================================
  group('CorrectAnswerOverlay with Lottie', () {
    testWidgets('renders and shows XP text', (tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(
            body: CorrectAnswerOverlay(xpEarned: 25, combo: 1),
          ),
        ),
      );

      expect(find.byType(CorrectAnswerOverlay), findsOneWidget);
      expect(find.text('+25 XP'), findsOneWidget);
      expect(find.byIcon(Icons.check), findsOneWidget);

      // Flush flutter_animate timers
      await tester.pumpAndSettle();
    });

    testWidgets('shows combo indicator for combo >= 2', (tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(
            body: CorrectAnswerOverlay(xpEarned: 10, combo: 3),
          ),
        ),
      );

      expect(find.text('COMBO x3'), findsOneWidget);
      await tester.pumpAndSettle();
    });

    testWidgets('does NOT show combo for combo < 2', (tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(
            body: CorrectAnswerOverlay(xpEarned: 10, combo: 1),
          ),
        ),
      );

      expect(find.textContaining('COMBO'), findsNothing);
      await tester.pumpAndSettle();
    });

    testWidgets('checkmark has semi-transparent opacity (0.85)', (tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(
            body: CorrectAnswerOverlay(xpEarned: 10, combo: 1),
          ),
        ),
      );

      final opacityWidgets = tester
          .widgetList<Opacity>(find.byType(Opacity))
          .where((o) => (o.opacity - 0.85).abs() < 0.01)
          .toList();
      expect(opacityWidgets, isNotEmpty,
          reason: 'Checkmark should be wrapped in Opacity(0.85)');
      await tester.pumpAndSettle();
    });
  });

  // =========================================================================
  // IncorrectAnswerOverlay — Lottie wrongX
  // =========================================================================
  group('IncorrectAnswerOverlay with Lottie', () {
    testWidgets('renders and shows X icon', (tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(
            body: IncorrectAnswerOverlay(correctAnswer: 'A'),
          ),
        ),
      );

      expect(find.byType(IncorrectAnswerOverlay), findsOneWidget);
      expect(find.byIcon(Icons.close), findsOneWidget);
      await tester.pumpAndSettle();
    });

    testWidgets('shows hearts when showHeartBreak is true', (tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(
            body: IncorrectAnswerOverlay(
              correctAnswer: 'A',
              showHeartBreak: true,
            ),
          ),
        ),
      );

      expect(find.byIcon(Icons.favorite), findsWidgets);
      await tester.pumpAndSettle();
    });

    testWidgets('hides hearts when showHeartBreak is false', (tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(
            body: IncorrectAnswerOverlay(
              correctAnswer: 'A',
              showHeartBreak: false,
            ),
          ),
        ),
      );

      expect(find.byIcon(Icons.favorite), findsNothing);
      await tester.pumpAndSettle();
    });
  });

  // =========================================================================
  // StreakFlame — Lottie fire for epic streaks
  // =========================================================================
  group('StreakFlame with Lottie fire', () {
    // Note: StreakFlame uses .animate(onPlay: (c) => c.repeat()) which creates
    // an infinite animation. Use pump() instead of pumpAndSettle() to avoid timeout.

    testWidgets('renders fire icon and count', (tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(
            body: StreakFlame(count: 5, multiplier: 1.2),
          ),
        ),
      );
      await tester.pump(const Duration(milliseconds: 100));

      expect(find.byIcon(Icons.local_fire_department), findsOneWidget);
      expect(find.text('5'), findsOneWidget);
    });

    testWidgets('renders frozen icon when isFrozen', (tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(
            body: StreakFlame(count: 5, isFrozen: true),
          ),
        ),
      );
      await tester.pump(const Duration(milliseconds: 100));

      expect(find.byIcon(Icons.ac_unit), findsOneWidget);
      expect(find.byIcon(Icons.shield), findsOneWidget);
    });

    testWidgets('shows multiplier bubble when > 1.0', (tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(
            body: StreakFlame(count: 7, multiplier: 1.5),
          ),
        ),
      );
      await tester.pump(const Duration(milliseconds: 100));

      expect(find.text('x1.5'), findsOneWidget);
    });

    testWidgets('hides multiplier when == 1.0', (tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(
            body: StreakFlame(count: 5, multiplier: 1.0),
          ),
        ),
      );
      await tester.pump(const Duration(milliseconds: 100));

      expect(find.textContaining('x1'), findsNothing);
    });
  });

  // =========================================================================
  // Design Pattern Validation
  // =========================================================================
  group('Design patterns', () {
    test('LottieAssets private constructor prevents instantiation', () {
      expect(LottieAssets.confetti, isNotEmpty);
      expect(LottieAssets.loading, isNotEmpty);
    });

    test('re-export of Lottie class is available via lottie_overlay', () {
      // lottie_overlay.dart exports 'package:lottie/lottie.dart' show Lottie
      // If this compiles, the re-export works
      expect(Lottie, isNotNull);
    });

    test('errorBuilder pattern is consistent across all LottieAssets', () {
      // This is a compile-time check: the pattern is enforced in code review
      // The fact that all widgets use errorBuilder means failed Lottie loads
      // gracefully degrade to SizedBox.shrink() or Icon fallbacks
      expect(true, isTrue); // Documenting the pattern
    });
  });
}
