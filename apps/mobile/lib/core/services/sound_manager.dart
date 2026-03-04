import 'package:audioplayers/audioplayers.dart';
import 'package:flutter/services.dart';

class SoundManager {
  static final SoundManager _instance = SoundManager._internal();
  factory SoundManager() => _instance;
  SoundManager._internal();

  final AudioPlayer _sfxPlayer = AudioPlayer();
  final AudioPlayer _musicPlayer = AudioPlayer();

  // Settings
  bool _sfxEnabled = true;
  bool _musicEnabled = true;

  Future<void> init() async {
    // Preload sounds if necessary
    await AudioCache().loadAll([
      'sounds/click.mp3',
      'sounds/attack.mp3',
      'sounds/damage.mp3',
      'sounds/victory.mp3',
      'sounds/defeat.mp3',
      'sounds/battle_theme.mp3',
    ]);
  }

  // --- SFX ---
  Future<void> playClick() async {
    if (!_sfxEnabled) return;
    await _sfxPlayer.play(AssetSource('sounds/click.mp3'), mode: PlayerMode.lowLatency);
  }

  Future<void> playAttack() async {
    if (!_sfxEnabled) return;
    await _sfxPlayer.play(AssetSource('sounds/attack.mp3'));
    HapticFeedback.lightImpact();
  }

  Future<void> playDamage() async {
    if (!_sfxEnabled) return;
    await _sfxPlayer.play(AssetSource('sounds/damage.mp3'));
    HapticFeedback.heavyImpact();
  }

  Future<void> playVictory() async {
    if (!_sfxEnabled) return;
    await _sfxPlayer.play(AssetSource('sounds/victory.mp3'));
    HapticFeedback.mediumImpact();
  }

  Future<void> playDefeat() async {
    if (!_sfxEnabled) return;
    await _sfxPlayer.play(AssetSource('sounds/defeat.mp3'));
    HapticFeedback.mediumImpact();
  }

  // --- Music ---
  Future<void> playBattleMusic() async {
    if (!_musicEnabled) return;
    await _musicPlayer.play(AssetSource('sounds/battle_theme.mp3'));
    await _musicPlayer.setReleaseMode(ReleaseMode.loop);
  }

  Future<void> stopMusic() async {
    await _musicPlayer.stop();
  }

  // --- Settings ---
  void toggleSfx(bool enabled) => _sfxEnabled = enabled;
  void toggleMusic(bool enabled) {
    _musicEnabled = enabled;
    if (!enabled) stopMusic();
  }
}

// Global accessor
final soundManager = SoundManager();
