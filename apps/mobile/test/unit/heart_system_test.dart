import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:hive/hive.dart';
import 'package:icfes_mobile/core/services/heart_system.dart';

void main() {
  late Directory tempDir;

  setUpAll(() {
    tempDir = Directory.systemTemp.createTempSync('hive_heart_test_');
    Hive.init(tempDir.path);
  });

  tearDownAll(() async {
    // Allow fire-and-forget _saveState calls to complete
    await Future.delayed(const Duration(milliseconds: 50));
    await Hive.close();
    if (tempDir.existsSync()) {
      tempDir.deleteSync(recursive: true);
    }
  });

  group('HeartSystem', () {
    late HeartSystem heartSystem;

    setUp(() async {
      heartSystem = HeartSystem();
      await heartSystem.initialize();
    });

    tearDown(() async {
      // Drain pending fire-and-forget saves before next test
      await Future.delayed(const Duration(milliseconds: 20));
      try {
        final box = Hive.box('heart_system');
        if (box.isOpen) await box.clear();
      } catch (_) {}
    });

    test('Initial state is correct', () {
      expect(heartSystem.hearts, 5);
      expect(heartSystem.mode, PracticeMode.normal);
      expect(heartSystem.isGraceMode, false);
    });

    test('Lose heart reduces count', () {
      heartSystem.loseHeart();
      expect(heartSystem.hearts, 4);
    });

    test('Lose heart at 0 does not go negative', () {
      for (int i = 0; i < 10; i++) {
        heartSystem.loseHeart();
      }
      expect(heartSystem.hearts, 0);
    });

    test('Grace Mode protects hearts', () {
      heartSystem.enterGraceMode();
      int heartsBefore = heartSystem.hearts;
      heartSystem.loseHeart();
      expect(heartSystem.hearts, heartsBefore);
    });

    test('Enter Grace Mode sets correct state', () {
      heartSystem.enterGraceMode();
      expect(heartSystem.isGraceMode, true);
      expect(heartSystem.mode, PracticeMode.grace);
      expect(heartSystem.xpMultiplier, 0.0);
    });

    test('Restore hearts via gold', () {
      // Drain hearts
      for (int i = 0; i < 5; i++) {
        heartSystem.loseHeart();
      }
      expect(heartSystem.hearts, 0);

      // Restore
      final remainingGold = heartSystem.restoreHeartsViaGold(200);
      expect(remainingGold, 50); // 200 - 150
      expect(heartSystem.hearts, 5);
    });
  });
}
