import 'package:flutter/services.dart';

/// AppHaptics - Haptic feedback patterns for gamified interactions
///
/// Provides various haptic feedback patterns optimized for different
/// types of user interactions in the app.
class AppHaptics {
  static bool _enabled = true;

  static void setEnabled(bool enabled) => _enabled = enabled;
  static bool get isEnabled => _enabled;

  /// Light impact for subtle taps (options, non-primary buttons)
  static void light() {
    if (!_enabled) return;
    HapticFeedback.lightImpact();
  }

  /// Medium impact for primary actions (main buttons, tab changes)
  static void medium() {
    if (!_enabled) return;
    HapticFeedback.mediumImpact();
  }

  /// Heavy impact for critical or physical actions
  static void heavy() {
    if (!_enabled) return;
    HapticFeedback.heavyImpact();
  }

  /// Selection click for list items
  static void selectionClick() {
    if (!_enabled) return;
    HapticFeedback.selectionClick();
  }

  /// Success pattern: double light pulse (legacy alias)
  static Future<void> success() async {
    await successPattern();
  }

  /// Error pattern: heavy impact (legacy alias)
  static Future<void> error() async {
    await errorPattern();
  }

  /// Celebration pattern (legacy alias)
  static Future<void> celebration() async {
    await celebrationPattern();
  }

  // ============================================
  // DOPAMINE ENGINE SPECIFIC PATTERNS
  // ============================================

  /// Success pattern: Double pulse for correct answers
  /// Creates a satisfying "ding-ding" feel
  /// Duration: ~100ms
  static Future<void> successPattern() async {
    if (!_enabled) return;

    // First pulse - light
    HapticFeedback.lightImpact();
    await Future.delayed(const Duration(milliseconds: 60));

    // Second pulse - medium (slightly stronger)
    HapticFeedback.mediumImpact();
  }

  /// Error pattern: Heavy single impact for wrong answers
  /// Creates a "thud" feel that indicates failure
  /// Duration: immediate
  static Future<void> errorPattern() async {
    if (!_enabled) return;

    // Single heavy impact
    HapticFeedback.heavyImpact();
  }

  /// Celebration pattern: Triple pulse for major achievements
  /// Creates a "ta-da-da!" fanfare feel
  /// Duration: ~300ms
  static Future<void> celebrationPattern() async {
    if (!_enabled) return;

    // First pulse
    HapticFeedback.mediumImpact();
    await Future.delayed(const Duration(milliseconds: 100));

    // Second pulse (slightly delayed)
    HapticFeedback.mediumImpact();
    await Future.delayed(const Duration(milliseconds: 100));

    // Third pulse (strongest - climax)
    HapticFeedback.heavyImpact();
  }

  /// Combo pattern: Escalating pulses based on combo level
  /// Higher combos get more intense haptic feedback
  /// Duration: varies by level (50-200ms)
  static Future<void> comboPattern(int level) async {
    if (!_enabled) return;

    if (level < 3) {
      // No special feedback for combos below 3
      return;
    } else if (level < 5) {
      // Combo 3-4: Double medium pulse
      HapticFeedback.mediumImpact();
      await Future.delayed(const Duration(milliseconds: 50));
      HapticFeedback.mediumImpact();
    } else if (level < 8) {
      // Combo 5-7: Triple escalating pulse
      HapticFeedback.lightImpact();
      await Future.delayed(const Duration(milliseconds: 40));
      HapticFeedback.mediumImpact();
      await Future.delayed(const Duration(milliseconds: 40));
      HapticFeedback.heavyImpact();
    } else {
      // Combo 8+: Rapid fire celebration
      for (int i = 0; i < 4; i++) {
        HapticFeedback.heavyImpact();
        await Future.delayed(const Duration(milliseconds: 50));
      }
    }
  }

  /// Streak pattern: Special pattern for streak milestones
  /// Duration: ~200ms
  static Future<void> streakPattern() async {
    if (!_enabled) return;

    // "Whoosh" feel - light to heavy
    HapticFeedback.lightImpact();
    await Future.delayed(const Duration(milliseconds: 80));
    HapticFeedback.mediumImpact();
    await Future.delayed(const Duration(milliseconds: 80));
    HapticFeedback.heavyImpact();
  }

  /// Level up pattern: Big celebratory feedback
  /// Duration: ~400ms
  static Future<void> levelUpPattern() async {
    if (!_enabled) return;

    // Build-up
    HapticFeedback.lightImpact();
    await Future.delayed(const Duration(milliseconds: 100));
    HapticFeedback.mediumImpact();
    await Future.delayed(const Duration(milliseconds: 100));

    // Climax - double heavy
    HapticFeedback.heavyImpact();
    await Future.delayed(const Duration(milliseconds: 80));
    HapticFeedback.heavyImpact();
  }

  /// Heart lost pattern: Sad/negative feedback
  /// Duration: immediate
  static Future<void> heartLostPattern() async {
    if (!_enabled) return;

    // Vibrate for a "crack" feeling
    HapticFeedback.vibrate();
  }

  /// Gold earned pattern: Satisfying coin feel
  /// Duration: ~60ms
  static Future<void> goldPattern() async {
    if (!_enabled) return;

    // Quick double tap like coins
    HapticFeedback.selectionClick();
    await Future.delayed(const Duration(milliseconds: 30));
    HapticFeedback.selectionClick();
  }

  /// XP tick pattern: For count-up animations
  /// Very subtle feedback
  static void xpTickPattern() {
    if (!_enabled) return;
    HapticFeedback.selectionClick();
  }

  /// Star earned pattern: For when stars appear
  /// Duration: immediate
  static void starPattern() {
    if (!_enabled) return;
    HapticFeedback.lightImpact();
  }
}
