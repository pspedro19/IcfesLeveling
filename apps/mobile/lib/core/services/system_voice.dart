import 'package:audioplayers/audioplayers.dart';
import 'package:flutter/foundation.dart';

/// La Voz del Sistema - Narrador epico del Modo Conquista
///
/// Reproduce frases pregrabadas que guian y motivan al usuario.
/// Inspirado en el Sistema de Solo Leveling.
class SystemVoice {
  static final SystemVoice _instance = SystemVoice._internal();
  factory SystemVoice() => _instance;
  SystemVoice._internal();

  final AudioPlayer _player = AudioPlayer();
  bool _isEnabled = true;
  double _volume = 1.0;

  /// Catalogo completo de frases del Sistema
  /// Key: ID de la frase, Value: Path del archivo de audio
  static const Map<String, String> _phrases = {
    // === ONBOARDING (5 frases) ===
    'onboard_found': 'audio/voice/sistema_te_encontro.wav',
    'onboard_eval_start': 'audio/voice/evaluacion_iniciada.wav',
    'onboard_calibrating': 'audio/voice/calibrando_rango.wav',
    'onboard_rank_assigned': 'audio/voice/rango_asignado.wav',
    'onboard_begin': 'audio/voice/entrenamiento_comienza.wav',

    // === SESION DIARIA (5 frases) ===
    'daily_welcome': 'audio/voice/bienvenido_cazador.wav',
    'daily_new_day': 'audio/voice/nuevo_dia.wav',
    'daily_select': 'audio/voice/selecciona_batalla.wav',
    'daily_mission_accept': 'audio/voice/mision_aceptada.wav',
    'daily_entering': 'audio/voice/entrando_dungeon.wav',

    // === COMBATE - RESPUESTAS (7 frases) ===
    'combat_correct': 'audio/voice/correcto.wav',
    'combat_power_up': 'audio/voice/poder_incrementado.wav',
    'combat_combo': 'audio/voice/combo_activado.wav',
    'combat_combo_5': 'audio/voice/excelente.wav',
    'combat_unstoppable': 'audio/voice/imparable.wav',
    'combat_wrong': 'audio/voice/respuesta_incorrecta.wav',
    'combat_analyze': 'audio/voice/analiza_error.wav',

    // === CORAZONES/MANA (3 frases) ===
    'hearts_reduced': 'audio/voice/mana_reducido.wav',
    'hearts_depleted': 'audio/voice/mana_agotado.wav',
    'hearts_restored': 'audio/voice/mana_restaurado.wav',

    // === RACHAS (4 frases) ===
    'streak_maintained': 'audio/voice/racha_mantenida.wav',
    'streak_impressive': 'audio/voice/dedicacion_notable.wav',
    'streak_warning': 'audio/voice/racha_peligro.wav',
    'streak_lost': 'audio/voice/racha_perdida.wav',

    // === LOGROS Y PROGRESION (5 frases) ===
    'progress_achievement': 'audio/voice/logro_desbloqueado.wav',
    'progress_level_up': 'audio/voice/nivel_alcanzado.wav',
    'progress_rank_up': 'audio/voice/rango_ascendido.wav',
    'progress_victory': 'audio/voice/victoria.wav',
    'progress_mission_complete': 'audio/voice/mision_completada.wav',

    // === ESPECIALES (3 frases) ===
    'special_watching': 'audio/voice/sistema_observa.wav',
    'special_power_grows': 'audio/voice/poder_crece.wav',
    'special_boss_awakened': 'audio/voice/boss_despertado.wav',
  };

  /// Reproduce una frase del Sistema
  ///
  /// [phraseKey] - ID de la frase a reproducir (ver catalogo arriba)
  ///
  /// Ejemplo:
  /// ```dart
  /// await SystemVoice().speak('combat_correct');
  /// ```
  Future<void> speak(String phraseKey) async {
    if (!_isEnabled) return;

    final path = _phrases[phraseKey];
    if (path == null) {
      debugPrint('SystemVoice: Phrase key "$phraseKey" not found');
      return;
    }

    try {
      // Detener audio anterior si existe
      await _player.stop();

      // Configurar volumen
      await _player.setVolume(_volume);

      // Reproducir nueva frase
      await _player.play(AssetSource(path));
    } catch (e) {
      debugPrint('SystemVoice error: $e');
    }
  }

  /// Reproduce una frase con delay previo
  ///
  /// Util para sincronizar con animaciones
  Future<void> speakWithDelay(String phraseKey, Duration delay) async {
    await Future.delayed(delay);
    await speak(phraseKey);
  }

  /// Habilita/deshabilita la voz del sistema
  void setEnabled(bool enabled) {
    _isEnabled = enabled;
  }

  /// Ajusta el volumen (0.0 - 1.0)
  void setVolume(double volume) {
    _volume = volume.clamp(0.0, 1.0);
  }

  /// Verifica si una frase existe en el catalogo
  bool hasPhrase(String phraseKey) {
    return _phrases.containsKey(phraseKey);
  }

  /// Libera recursos
  Future<void> dispose() async {
    await _player.dispose();
  }
}
