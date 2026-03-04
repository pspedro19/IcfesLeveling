import 'package:audioplayers/audioplayers.dart';

/// Types of sounds available in the app
enum SoundType {
  ding,       // Correct answer
  wrong,      // Incorrect answer
  fanfare,    // Lesson complete / major achievement
  tick,       // XP count-up
  levelUp,    // Level up celebration
  combo,      // Combo milestone
  coin,       // Gold/currency earned
  click,      // Button click
  whoosh,     // Transition/swipe
  attack,     // Battle sword swing
  victory,    // Victory celebration
  bossMusic,  // Boss raid background music
}

/// SoundService - Manages audio playback for gamified feedback
///
/// Handles preloading and playing of sound effects with proper
/// resource management and volume control.
class SoundService {
  static final SoundService _instance = SoundService._internal();
  factory SoundService() => _instance;
  SoundService._internal();

  final Map<SoundType, AudioPlayer> _players = {};
  bool _isInitialized = false;
  bool _enabled = true;
  double _volume = 0.5;

  /// Sound file mappings
  static const Map<SoundType, String> _soundPaths = {
    SoundType.ding: 'sounds/ding.mp3',
    SoundType.wrong: 'sounds/wrong.mp3',
    SoundType.fanfare: 'sounds/fanfare.mp3',
    SoundType.tick: 'sounds/tick.mp3',
    SoundType.levelUp: 'sounds/levelup.mp3',
    SoundType.combo: 'sounds/combo.mp3',
    SoundType.coin: 'sounds/coin.mp3',
    SoundType.click: 'sounds/click.mp3',
    SoundType.whoosh: 'sounds/whoosh.mp3',
    SoundType.attack: 'sounds/attack.mp3',
    SoundType.victory: 'sounds/victory.mp3',
    SoundType.bossMusic: 'sounds/boss_music.mp3',
  };

  bool get isEnabled => _enabled;
  double get volume => _volume;

  /// Enable or disable sound effects
  void setEnabled(bool enabled) {
    _enabled = enabled;
  }

  /// Set master volume (0.0 to 1.0)
  void setVolume(double volume) {
    _volume = volume.clamp(0.0, 1.0);
    for (final player in _players.values) {
      player.setVolume(_volume);
    }
  }

  /// Preload all common sounds for instant playback
  Future<void> preloadSounds() async {
    if (_isInitialized) return;

    try {
      // Preload essential sounds
      final essentialSounds = [
        SoundType.ding,
        SoundType.wrong,
        SoundType.tick,
      ];

      for (final soundType in essentialSounds) {
        await _preloadSound(soundType);
      }

      _isInitialized = true;
    } catch (e) {
      // Silently fail - sounds are not critical
      print('SoundService: Failed to preload sounds: $e');
    }
  }

  /// Preload a specific sound
  Future<void> _preloadSound(SoundType type) async {
    try {
      final path = _soundPaths[type];
      if (path == null) return;

      final player = AudioPlayer();
      await player.setSource(AssetSource(path));
      await player.setVolume(_volume);
      _players[type] = player;
    } catch (e) {
      // Individual sound preload failure is not critical
      print('SoundService: Failed to preload ${type.name}: $e');
    }
  }

  /// Play a sound effect
  /// Returns immediately - sound plays asynchronously
  void playSound(SoundType type) {
    if (!_enabled) return;

    _playSoundAsync(type);
  }

  /// Internal async sound playback
  Future<void> _playSoundAsync(SoundType type) async {
    try {
      // Check if we have a preloaded player
      AudioPlayer? player = _players[type];

      if (player != null) {
        // Use preloaded player
        await player.seek(Duration.zero);
        await player.resume();
      } else {
        // Lazy load and play
        final path = _soundPaths[type];
        if (path == null) return;

        player = AudioPlayer();
        await player.setVolume(_volume);
        await player.play(AssetSource(path));

        // Store for future use
        _players[type] = player;
      }
    } catch (e) {
      // Sound playback failure is not critical
      print('SoundService: Failed to play ${type.name}: $e');
    }
  }

  /// Play sound with custom volume
  void playSoundWithVolume(SoundType type, double volume) {
    if (!_enabled) return;

    _playSoundWithVolumeAsync(type, volume.clamp(0.0, 1.0));
  }

  Future<void> _playSoundWithVolumeAsync(SoundType type, double volume) async {
    try {
      final path = _soundPaths[type];
      if (path == null) return;

      final player = AudioPlayer();
      await player.setVolume(volume);
      await player.play(AssetSource(path));

      // Auto-dispose after playing
      player.onPlayerComplete.listen((_) {
        player.dispose();
      });
    } catch (e) {
      print('SoundService: Failed to play ${type.name}: $e');
    }
  }

  /// Stop all currently playing sounds
  Future<void> stopAll() async {
    for (final player in _players.values) {
      await player.stop();
    }
  }

  /// Dispose of all players
  Future<void> dispose() async {
    for (final player in _players.values) {
      await player.dispose();
    }
    _players.clear();
    _isInitialized = false;
  }

  /// Play tick sound for XP count-up animations
  /// Slightly randomized volume for more natural feel
  void playTickSound() {
    if (!_enabled) return;

    // Slight volume variation for natural feel
    final variation = 0.7 + (DateTime.now().millisecond % 30) / 100;
    playSoundWithVolume(SoundType.tick, _volume * variation);
  }

  /// Play combo sound with intensity based on combo level
  void playComboSound(int comboLevel) {
    if (!_enabled) return;

    // Higher combos get louder sounds
    final intensity = (comboLevel / 10).clamp(0.5, 1.0);
    playSoundWithVolume(SoundType.combo, _volume * intensity);
  }
}
