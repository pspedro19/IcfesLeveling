import 'package:flutter/material.dart';

import '../utils/app_haptics.dart';
import 'sound_service.dart';
import '../../shared/widgets/animated_feedback/correct_answer_overlay.dart';
import '../../shared/widgets/animated_feedback/incorrect_answer_overlay.dart';
import '../../shared/widgets/animated_feedback/lesson_complete_overlay.dart';
import '../../shared/widgets/lottie_overlay.dart';

/// DopamineEngine - Orchestrates satisfying feedback animations and sounds
///
/// This engine provides carefully timed sequences of visual, audio, and haptic
/// feedback designed to create a rewarding experience for the user.
///
/// Timeline specifications:
/// - Correct answer: 600ms total
/// - Incorrect answer: 800ms total
/// - Lesson complete: 3000ms total
class DopamineEngine {
  static final DopamineEngine _instance = DopamineEngine._internal();
  factory DopamineEngine() => _instance;
  DopamineEngine._internal();

  bool _isInitialized = false;

  /// Initialize the engine and preload sounds
  Future<void> initialize() async {
    if (_isInitialized) return;
    await SoundService().preloadSounds();
    _isInitialized = true;
  }

  /// Timeline for correct answer (600ms total)
  ///
  /// 0ms: Green glow starts expanding
  /// 50ms: Success haptic (double pulse)
  /// 100ms: "Ding" sound plays
  /// 150ms: Checkmark bounces in (+ Lottie correctCheck)
  /// 300ms: "+XP" floats upward
  /// 400ms: Particles appear if combo >= 3
  /// 600ms: Sequence complete
  static Future<void> playCorrectAnswerSequence(
    BuildContext context, {
    required int xpEarned,
    required int combo,
    required String correctOptionId,
  }) async {
    final overlayEntry = OverlayEntry(
      builder: (context) => CorrectAnswerOverlay(
        xpEarned: xpEarned,
        combo: combo,
      ),
    );

    Overlay.of(context).insert(overlayEntry);

    // 50ms - Haptic feedback
    await Future.delayed(const Duration(milliseconds: 50));
    await AppHaptics.successPattern();

    // 100ms - Sound
    await Future.delayed(const Duration(milliseconds: 50));
    SoundService().playSound(SoundType.ding);

    // Combo haptic if applicable
    if (combo >= 3) {
      await Future.delayed(const Duration(milliseconds: 200));
      await AppHaptics.comboPattern(combo);
    }

    // Wait for animation to complete (600ms total)
    await Future.delayed(Duration(milliseconds: combo >= 3 ? 350 : 450));

    // Safe removal — guard against disposed context
    if (context.mounted) {
      overlayEntry.remove();
    }
  }

  /// Show correct answer overlay and return immediately (for integration with existing flow)
  static void showCorrectAnswerOverlay(
    BuildContext context, {
    required int xpEarned,
    required int combo,
  }) {
    AppHaptics.successPattern();
    SoundService().playSound(SoundType.ding);

    if (combo >= 3) {
      Future.delayed(const Duration(milliseconds: 100), () {
        AppHaptics.comboPattern(combo);
      });
    }
  }

  /// Timeline for incorrect answer (800ms total)
  ///
  /// 0ms: Shake animation starts (3 cycles, 5px amplitude)
  /// 50ms: Heavy impact haptic
  /// 100ms: "Wrong" sound plays
  /// 200ms: X mark fades in (+ Lottie wrongX)
  /// 400ms: Heart "crack" animation
  /// 600ms: Correct answer illuminates
  /// 800ms: Sequence complete
  static Future<void> playIncorrectAnswerSequence(
    BuildContext context, {
    required String correctAnswer,
    VoidCallback? onHighlightCorrect,
  }) async {
    final overlayEntry = OverlayEntry(
      builder: (context) => IncorrectAnswerOverlay(
        correctAnswer: correctAnswer,
      ),
    );

    Overlay.of(context).insert(overlayEntry);

    // 50ms - Haptic feedback
    await Future.delayed(const Duration(milliseconds: 50));
    await AppHaptics.errorPattern();

    // 100ms - Sound
    await Future.delayed(const Duration(milliseconds: 50));
    SoundService().playSound(SoundType.wrong);

    // 600ms - Highlight correct answer callback
    await Future.delayed(const Duration(milliseconds: 500));
    onHighlightCorrect?.call();

    // Wait for animation to complete (800ms total)
    await Future.delayed(const Duration(milliseconds: 200));

    // Safe removal — guard against disposed context
    if (context.mounted) {
      overlayEntry.remove();
    }
  }

  /// Show incorrect answer overlay (for integration with existing flow)
  static void showIncorrectAnswerOverlay(BuildContext context) {
    AppHaptics.errorPattern();
    SoundService().playSound(SoundType.wrong);
  }

  /// Timeline for lesson complete celebration (3000ms total)
  ///
  /// 0ms: Fade to dark overlay
  /// 200ms: Confetti explosion starts (+ Lottie confetti)
  /// 400ms: Triple haptic pulse
  /// 500ms: "LECCION COMPLETADA!" bounces in
  /// 600ms: Fanfare sound
  /// 1000ms: XP counter starts counting up
  /// 1500ms: Stars appear one by one (500ms each)
  /// 2500ms: Gold counter appears (+ Lottie coins)
  /// 3000ms: Sequence complete
  static Future<void> playLessonCompleteSequence(
    BuildContext context, {
    required int totalXP,
    required int stars,
    required int gold,
    VoidCallback? onComplete,
  }) async {
    late final OverlayEntry overlayEntry;
    overlayEntry = OverlayEntry(
      builder: (ctx) => LessonCompleteOverlay(
        totalXP: totalXP,
        stars: stars,
        gold: gold,
        onComplete: () {
          overlayEntry.remove();
          onComplete?.call();
        },
      ),
    );

    Overlay.of(context).insert(overlayEntry);

    // 400ms - Celebration haptic
    await Future.delayed(const Duration(milliseconds: 400));
    await AppHaptics.celebrationPattern();

    // 600ms - Fanfare
    await Future.delayed(const Duration(milliseconds: 200));
    SoundService().playSound(SoundType.fanfare);

    // 1000ms - Start tick sounds for counter
    await Future.delayed(const Duration(milliseconds: 400));

    // Play tick sounds during count-up
    const tickDuration = 1000;
    const tickInterval = tickDuration ~/ 10;
    for (int i = 0; i < 10; i++) {
      await Future.delayed(const Duration(milliseconds: tickInterval));
      SoundService().playSound(SoundType.tick);
    }

    // 2500ms - Level up sound and animation if applicable
    await Future.delayed(const Duration(milliseconds: 500));
    if (stars >= 3) {
      SoundService().playSound(SoundType.levelUp);
      await AppHaptics.celebrationPattern();
      if (context.mounted) {
        showLottieOverlay(context, LottieAssets.levelUp, size: 250);
      }
    }

    // Overlay is removed when user taps "CONTINUAR" (via onComplete above)
  }

  /// Quick feedback for button presses
  static void buttonPress() {
    AppHaptics.light();
  }

  /// Feedback for important actions
  static void importantAction() {
    AppHaptics.medium();
  }
}
