import 'dart:async';
import 'dart:math';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

/// Combo level thresholds and their associated effects
enum ComboLevel implements Comparable<ComboLevel> {
  none,      // < 2
  good,      // 2: "Bien!"
  excellent, // 3: "Excelente!" + sparkles
  unstoppable, // 5: "IMPARABLE!" + shake
  onFire,    // 7: "ON FIRE!" + flames
  legendary, // 10: "LEGENDARIO!" + explosion
  invincible; // 15+: "INVENCIBLE!" + glow

  @override
  int compareTo(ComboLevel other) => index.compareTo(other.index);

  bool operator >=(ComboLevel other) => index >= other.index;
  bool operator <=(ComboLevel other) => index <= other.index;
  bool operator >(ComboLevel other) => index > other.index;
  bool operator <(ComboLevel other) => index < other.index;
}

/// Display configuration for a combo level
class ComboDisplay {
  final ComboLevel level;
  final String text;
  final Color color;
  final IconData icon;
  final bool hasSparkles;
  final bool hasShake;
  final bool hasFlames;
  final bool hasExplosion;
  final bool hasGlow;

  const ComboDisplay({
    required this.level,
    required this.text,
    required this.color,
    required this.icon,
    this.hasSparkles = false,
    this.hasShake = false,
    this.hasFlames = false,
    this.hasExplosion = false,
    this.hasGlow = false,
  });
}

/// State class for combo tracking
class ComboState {
  final int currentCombo;
  final int maxCombo;
  final int totalBonusXp;
  final DateTime? lastAnswerTime;
  final bool isTimerActive;

  const ComboState({
    this.currentCombo = 0,
    this.maxCombo = 0,
    this.totalBonusXp = 0,
    this.lastAnswerTime,
    this.isTimerActive = false,
  });

  ComboState copyWith({
    int? currentCombo,
    int? maxCombo,
    int? totalBonusXp,
    DateTime? lastAnswerTime,
    bool? isTimerActive,
  }) {
    return ComboState(
      currentCombo: currentCombo ?? this.currentCombo,
      maxCombo: maxCombo ?? this.maxCombo,
      totalBonusXp: totalBonusXp ?? this.totalBonusXp,
      lastAnswerTime: lastAnswerTime ?? this.lastAnswerTime,
      isTimerActive: isTimerActive ?? this.isTimerActive,
    );
  }

  /// Get the current combo level
  ComboLevel get level => ComboService.getComboLevel(currentCombo);

  /// Get bonus XP for current combo
  int get bonusXp => ComboService.calculateBonusXP(currentCombo);
}

/// Service for managing combo streaks with XP bonuses
class ComboService {
  /// Combo reset timeout in seconds
  static const int comboTimeoutSeconds = 30;

  /// Maximum combo bonus (caps at 15)
  static const int maxComboBonus = 15;

  /// Calculate bonus XP based on combo count
  /// Formula: min(combo, 15)
  static int calculateBonusXP(int combo) {
    if (combo < 2) return 0;
    return min(combo, maxComboBonus);
  }

  /// Calculate total XP: base + combo bonus
  static int calculateTotalXP(int baseXp, int combo) {
    return baseXp + calculateBonusXP(combo);
  }

  /// Get combo level for a given combo count
  static ComboLevel getComboLevel(int combo) {
    if (combo >= 15) return ComboLevel.invincible;
    if (combo >= 10) return ComboLevel.legendary;
    if (combo >= 7) return ComboLevel.onFire;
    if (combo >= 5) return ComboLevel.unstoppable;
    if (combo >= 3) return ComboLevel.excellent;
    if (combo >= 2) return ComboLevel.good;
    return ComboLevel.none;
  }

  /// Get display configuration for a combo count
  static ComboDisplay getComboDisplay(int combo) {
    final level = getComboLevel(combo);

    switch (level) {
      case ComboLevel.invincible:
        return const ComboDisplay(
          level: ComboLevel.invincible,
          text: 'INVENCIBLE!',
          color: Color(0xFFE040FB), // Purple/Magenta
          icon: Icons.shield,
          hasGlow: true,
          hasSparkles: true,
          hasFlames: true,
        );
      case ComboLevel.legendary:
        return const ComboDisplay(
          level: ComboLevel.legendary,
          text: 'LEGENDARIO!',
          color: Color(0xFFFFD700), // Gold
          icon: Icons.emoji_events,
          hasExplosion: true,
          hasSparkles: true,
        );
      case ComboLevel.onFire:
        return const ComboDisplay(
          level: ComboLevel.onFire,
          text: 'ON FIRE!',
          color: Color(0xFFFF5722), // Deep Orange/Red
          icon: Icons.local_fire_department,
          hasFlames: true,
          hasShake: true,
        );
      case ComboLevel.unstoppable:
        return const ComboDisplay(
          level: ComboLevel.unstoppable,
          text: 'IMPARABLE!',
          color: Color(0xFFFF9800), // Orange
          icon: Icons.bolt,
          hasShake: true,
        );
      case ComboLevel.excellent:
        return const ComboDisplay(
          level: ComboLevel.excellent,
          text: 'Excelente!',
          color: Color(0xFF4CAF50), // Green
          icon: Icons.auto_awesome,
          hasSparkles: true,
        );
      case ComboLevel.good:
        return const ComboDisplay(
          level: ComboLevel.good,
          text: 'Bien!',
          color: Color(0xFF2196F3), // Blue
          icon: Icons.thumb_up,
        );
      case ComboLevel.none:
      default:
        return const ComboDisplay(
          level: ComboLevel.none,
          text: '',
          color: Colors.grey,
          icon: Icons.bolt,
        );
    }
  }

  /// Get the sound identifier for a combo level
  static String? getSoundForCombo(int combo) {
    final level = getComboLevel(combo);
    switch (level) {
      case ComboLevel.invincible:
      case ComboLevel.legendary:
        return 'combo_legendary';
      case ComboLevel.onFire:
        return 'combo_fire';
      case ComboLevel.unstoppable:
        return 'combo_5';
      case ComboLevel.excellent:
        return 'combo_3';
      case ComboLevel.good:
        return 'combo_2';
      case ComboLevel.none:
        return null;
    }
  }
}

/// Riverpod notifier for combo state management
class ComboNotifier extends StateNotifier<ComboState> {
  Timer? _comboResetTimer;
  final void Function(String soundId)? _onPlaySound;

  ComboNotifier({void Function(String soundId)? onPlaySound})
      : _onPlaySound = onPlaySound,
        super(const ComboState());

  @override
  void dispose() {
    _comboResetTimer?.cancel();
    super.dispose();
  }

  /// Increment combo on correct answer
  void incrementCombo() {
    _cancelTimer();

    final newCombo = state.currentCombo + 1;
    final newMaxCombo = max(newCombo, state.maxCombo);
    final bonusXp = ComboService.calculateBonusXP(newCombo);

    state = state.copyWith(
      currentCombo: newCombo,
      maxCombo: newMaxCombo,
      totalBonusXp: state.totalBonusXp + bonusXp,
      lastAnswerTime: DateTime.now(),
      isTimerActive: true,
    );

    // Play sound for new combo level
    final soundId = ComboService.getSoundForCombo(newCombo);
    if (soundId != null && _onPlaySound != null) {
      _onPlaySound!(soundId);
    }

    _startComboTimer();
  }

  /// Reset combo on wrong answer
  void resetCombo() {
    _cancelTimer();
    state = state.copyWith(
      currentCombo: 0,
      lastAnswerTime: null,
      isTimerActive: false,
    );
  }

  /// Reset entire combo state for new session
  void resetSession() {
    _cancelTimer();
    state = const ComboState();
  }

  /// Restart the combo timer (e.g., when user interacts)
  void restartTimer() {
    if (state.currentCombo > 0) {
      _cancelTimer();
      _startComboTimer();
    }
  }

  void _startComboTimer() {
    _comboResetTimer = Timer(
      const Duration(seconds: ComboService.comboTimeoutSeconds),
      () {
        if (state.currentCombo > 0) {
          state = state.copyWith(
            currentCombo: 0,
            isTimerActive: false,
          );
        }
      },
    );
  }

  void _cancelTimer() {
    _comboResetTimer?.cancel();
    _comboResetTimer = null;
  }

  /// Get current bonus XP
  int get currentBonusXp => ComboService.calculateBonusXP(state.currentCombo);

  /// Get combo display for current state
  ComboDisplay get currentDisplay =>
      ComboService.getComboDisplay(state.currentCombo);
}

/// Provider for combo service
final comboProvider = StateNotifierProvider<ComboNotifier, ComboState>((ref) {
  return ComboNotifier();
});

/// Provider for combo service with audio support
final comboWithAudioProvider = StateNotifierProvider.family<ComboNotifier, ComboState, void Function(String)?>(
  (ref, onPlaySound) {
    return ComboNotifier(onPlaySound: onPlaySound);
  },
);
