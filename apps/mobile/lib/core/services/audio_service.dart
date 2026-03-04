import 'package:audioplayers/audioplayers.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

/// Service for managing audio playback in the app
/// Handles combo sounds, success/error feedback, and background audio
class AudioService {
  final AudioPlayer _comboPlayer;
  final AudioPlayer _feedbackPlayer;
  bool _isMuted = false;
  double _volume = 0.7;
  bool _isInitialized = false;

  AudioService()
      : _comboPlayer = AudioPlayer(),
        _feedbackPlayer = AudioPlayer();

  /// Initialize the audio service
  Future<void> initialize() async {
    if (_isInitialized) return;

    try {
      // Set audio context for mobile
      await _comboPlayer.setReleaseMode(ReleaseMode.stop);
      await _feedbackPlayer.setReleaseMode(ReleaseMode.stop);
      await _comboPlayer.setVolume(_volume);
      await _feedbackPlayer.setVolume(_volume);
      _isInitialized = true;
    } catch (e) {
      debugPrint('AudioService: Failed to initialize: $e');
    }
  }

  /// Dispose audio resources
  Future<void> dispose() async {
    await _comboPlayer.dispose();
    await _feedbackPlayer.dispose();
  }

  /// Set mute state
  void setMuted(bool muted) {
    _isMuted = muted;
  }

  /// Get current mute state
  bool get isMuted => _isMuted;

  /// Set volume (0.0 to 1.0)
  Future<void> setVolume(double volume) async {
    _volume = volume.clamp(0.0, 1.0);
    await _comboPlayer.setVolume(_volume);
    await _feedbackPlayer.setVolume(_volume);
  }

  /// Get current volume
  double get volume => _volume;

  /// Play combo sound based on combo level
  /// Available sounds: combo_2, combo_3, combo_5, combo_fire, combo_legendary
  Future<void> playComboSound(String soundId) async {
    if (_isMuted) return;

    try {
      await _comboPlayer.stop();
      final source = AssetSource('sounds/$soundId.mp3');
      await _comboPlayer.play(source);
    } catch (e) {
      // Gracefully handle missing audio files
      debugPrint('AudioService: Could not play combo sound $soundId: $e');
    }
  }

  /// Play success sound
  Future<void> playSuccess() async {
    if (_isMuted) return;

    try {
      await _feedbackPlayer.stop();
      final source = AssetSource('sounds/success.mp3');
      await _feedbackPlayer.play(source);
    } catch (e) {
      debugPrint('AudioService: Could not play success sound: $e');
    }
  }

  /// Play error sound
  Future<void> playError() async {
    if (_isMuted) return;

    try {
      await _feedbackPlayer.stop();
      final source = AssetSource('sounds/error.mp3');
      await _feedbackPlayer.play(source);
    } catch (e) {
      debugPrint('AudioService: Could not play error sound: $e');
    }
  }

  /// Play level up sound
  Future<void> playLevelUp() async {
    if (_isMuted) return;

    try {
      await _comboPlayer.stop();
      final source = AssetSource('sounds/level_up.mp3');
      await _comboPlayer.play(source);
    } catch (e) {
      debugPrint('AudioService: Could not play level up sound: $e');
    }
  }

  /// Play achievement unlocked sound
  Future<void> playAchievement() async {
    if (_isMuted) return;

    try {
      await _comboPlayer.stop();
      final source = AssetSource('sounds/achievement.mp3');
      await _comboPlayer.play(source);
    } catch (e) {
      debugPrint('AudioService: Could not play achievement sound: $e');
    }
  }

  /// Play button click sound
  Future<void> playClick() async {
    if (_isMuted) return;

    try {
      await _feedbackPlayer.stop();
      final source = AssetSource('sounds/click.mp3');
      await _feedbackPlayer.play(source);
    } catch (e) {
      debugPrint('AudioService: Could not play click sound: $e');
    }
  }

  /// Stop all sounds
  Future<void> stopAll() async {
    await _comboPlayer.stop();
    await _feedbackPlayer.stop();
  }
}

/// Provider for AudioService
final audioServiceProvider = Provider<AudioService>((ref) {
  final service = AudioService();

  // Initialize on creation
  service.initialize();

  // Dispose on ref disposal
  ref.onDispose(() {
    service.dispose();
  });

  return service;
});

/// Provider for mute state
final audioMutedProvider = StateProvider<bool>((ref) => false);

/// Provider for volume level
final audioVolumeProvider = StateProvider<double>((ref) => 0.7);
