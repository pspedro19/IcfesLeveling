import 'dart:io';
import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:integration_test/integration_test.dart';
import 'package:go_router/go_router.dart';
import 'dart:ui' as ui;
import 'package:icfes_mobile/main.dart' as app;

/// Directory on the device to save screenshots.
const _screenshotDir = '/sdcard/Download/icfes_screenshots';

void main() {
  final binding = IntegrationTestWidgetsFlutterBinding.ensureInitialized();

  /// Pump [count] frames with [interval] between each.
  /// Unlike pumpAndSettle, this does NOT wait for animations to stop,
  /// so pages with infinite/repeating animations won't cause timeouts.
  Future<void> pumpFrames(
    WidgetTester tester, {
    int count = 30,
    Duration interval = const Duration(milliseconds: 100),
  }) async {
    for (int i = 0; i < count; i++) {
      await tester.pump(interval);
    }
  }

  /// Navigate to [path] using GoRouter from the current widget tree.
  void navigateTo(WidgetTester tester, String path) {
    final scaffolds = find.byType(Scaffold);
    if (scaffolds.evaluate().isNotEmpty) {
      final element = tester.element(scaffolds.first);
      GoRouter.of(element).go(path);
    }
  }

  /// Take a screenshot and save it to the device filesystem as PNG.
  /// Also stores in binding.reportData for driver-based retrieval.
  Future<void> screenshot(WidgetTester tester, String name) async {
    // Store in binding for driver retrieval (if using flutter drive)
    await binding.takeScreenshot(name);

    // Also save directly to device filesystem
    try {
      final dir = Directory(_screenshotDir);
      if (!dir.existsSync()) {
        dir.createSync(recursive: true);
      }

      // Get the screenshot bytes from reportData
      final data = binding.reportData;
      if (data != null && data.containsKey(name)) {
        final bytes = data[name];
        if (bytes is List<int>) {
          final file = File('${dir.path}/$name.png');
          file.writeAsBytesSync(bytes);
          debugPrint('Screenshot saved: ${file.path}');
        }
      }
    } catch (e) {
      debugPrint('Failed to save screenshot $name to device: $e');
    }
  }

  group('Screenshot Tour', () {
    testWidgets('capture all screens', (tester) async {
      // Create screenshot directory
      try {
        Directory(_screenshotDir).createSync(recursive: true);
      } catch (_) {}

      // ========================================
      // 1. Launch the full app
      // ========================================
      app.main();

      // Wait for splash screen (2s delay) + initialization
      await pumpFrames(tester, count: 60, interval: const Duration(milliseconds: 100));

      // ========================================
      // 01. LOGIN PAGE
      // ========================================
      navigateTo(tester, '/login');
      await pumpFrames(tester, count: 40);
      await screenshot(tester, '01_login_page');

      // ========================================
      // 02. ENTER DEMO MODE (offline fallback)
      // ========================================
      final demoButton = find.text('MODO DESARROLLADOR');
      if (demoButton.evaluate().isNotEmpty) {
        await tester.tap(demoButton);
        // Wait for demo mode: tries backend (5s timeout) then falls back to local
        await pumpFrames(tester, count: 80, interval: const Duration(milliseconds: 100));
      }
      // Demo user has diagnosticCompleted=false, so lands on diagnostic
      await screenshot(tester, '02_after_demo_login');

      // ========================================
      // 03. HOME PAGE
      // ========================================
      navigateTo(tester, '/home');
      await pumpFrames(tester, count: 30);
      await screenshot(tester, '03_home_page');

      // ========================================
      // 04. LEAGUES PAGE (BottomNav tab 1)
      // ========================================
      navigateTo(tester, '/leagues');
      await pumpFrames(tester, count: 30);
      await screenshot(tester, '04_leagues_page');

      // ========================================
      // 05. STUDY PLAN PAGE (BottomNav tab 2)
      // ========================================
      navigateTo(tester, '/study-plan');
      await pumpFrames(tester, count: 30);
      await screenshot(tester, '05_study_plan_page');

      // ========================================
      // 06. PROFILE PAGE (BottomNav tab 3)
      // ========================================
      navigateTo(tester, '/profile');
      await pumpFrames(tester, count: 30);
      await screenshot(tester, '06_profile_page');

      // ========================================
      // 07. SETTINGS PAGE
      // ========================================
      navigateTo(tester, '/settings');
      await pumpFrames(tester, count: 30);
      await screenshot(tester, '07_settings_page');

      // ========================================
      // 08. SHOP PAGE
      // ========================================
      navigateTo(tester, '/store');
      await pumpFrames(tester, count: 30);
      await screenshot(tester, '08_shop_page');

      // ========================================
      // 09. ACHIEVEMENTS PAGE
      // ========================================
      navigateTo(tester, '/achievements');
      await pumpFrames(tester, count: 30);
      await screenshot(tester, '09_achievements_page');

      // ========================================
      // 10. PRACTICE (Subject Selection)
      // ========================================
      navigateTo(tester, '/practice');
      await pumpFrames(tester, count: 30);
      await screenshot(tester, '10_practice_page');

      // ========================================
      // 11. BOSS RAID PAGE
      // ========================================
      navigateTo(tester, '/boss-raid');
      await pumpFrames(tester, count: 30);
      await screenshot(tester, '11_boss_raid_page');

      // ========================================
      // 12. STATS PAGE
      // ========================================
      navigateTo(tester, '/stats');
      await pumpFrames(tester, count: 30);
      await screenshot(tester, '12_stats_page');

      // ========================================
      // 13. DUNGEON MAP PAGE
      // ========================================
      navigateTo(tester, '/dungeon/map');
      await pumpFrames(tester, count: 30);
      await screenshot(tester, '13_dungeon_map_page');

      // ========================================
      // 14. MILLIONAIRE PAGE
      // ========================================
      navigateTo(tester, '/millionaire');
      await pumpFrames(tester, count: 30);
      await screenshot(tester, '14_millionaire_page');

      debugPrint('=== ALL SCREENSHOTS CAPTURED ===');
      debugPrint('Pull from device with: adb pull $_screenshotDir .');
    });
  });
}
