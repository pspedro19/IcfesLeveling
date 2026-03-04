# TASKS: Gemini - Frontend & APIs (Flutter/Riverpod)

**Proyecto:** ICFES Leveling - Conquest Mode
**Asignado a:** Gemini (Frontend Developer)
**Referencia:** CONQUEST_MODE_LOGIC.md v3.0
**Fecha:** 29 de Diciembre, 2025

---

## Resumen Ejecutivo

Este documento contiene todas las tareas de frontend para implementar el Modo Conquista. Incluye nuevos servicios, widgets, providers, y la integracion con los endpoints del backend.

**Stack Tecnologico:**
- Flutter 3.x
- Riverpod para state management
- Hive para almacenamiento offline
- audioplayers para audio
- flutter_animate para animaciones
- WebSocket para comunicacion en tiempo real

---

## Tabla de Contenidos

1. [Servicios Core](#1-servicios-core)
2. [Providers (Riverpod)](#2-providers-riverpod)
3. [Widgets y Componentes UI](#3-widgets-y-componentes-ui)
4. [Integracion API](#4-integracion-api)
5. [Modelos de Datos](#5-modelos-de-datos)
6. [Assets y Recursos](#6-assets-y-recursos)
7. [Testing](#7-testing)

---

## 1. Servicios Core

### 1.1 SystemVoice Service [CRITICO - PRIORIDAD 1]

**Archivo:** `apps/mobile/lib/core/services/system_voice.dart`

**Descripcion:** Servicio que reproduce las frases de "La Voz del Sistema" (narrador estilo Solo Leveling).

```dart
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
```

**Integracion con BattleProvider:**

```dart
// En battle_provider.dart, agregar:

import 'package:icfes_leveling/core/services/system_voice.dart';

class BattleNotifier extends StateNotifier<BattleState> {
  final SystemVoice _systemVoice = SystemVoice();

  // En respuesta correcta:
  Future<void> _handleCorrectAnswer(AnswerResult result) async {
    // T+50ms: Voz del sistema
    await Future.delayed(const Duration(milliseconds: 50));
    await _systemVoice.speak('combat_correct');

    // Si hay combo milestone
    if (result.currentCombo == 3) {
      await Future.delayed(const Duration(milliseconds: 150));
      await _systemVoice.speak('combat_combo');
    } else if (result.currentCombo == 5) {
      await Future.delayed(const Duration(milliseconds: 150));
      await _systemVoice.speak('combat_combo_5');
    } else if (result.currentCombo >= 10) {
      await Future.delayed(const Duration(milliseconds: 150));
      await _systemVoice.speak('combat_unstoppable');
    }
  }

  // En respuesta incorrecta:
  Future<void> _handleWrongAnswer(AnswerResult result) async {
    await Future.delayed(const Duration(milliseconds: 50));
    await _systemVoice.speak('combat_wrong');

    await Future.delayed(const Duration(milliseconds: 350));
    await _systemVoice.speak('combat_analyze');
  }

  // En victoria:
  Future<void> _handleVictory() async {
    await Future.delayed(const Duration(milliseconds: 800));
    await _systemVoice.speak('progress_victory');

    await Future.delayed(const Duration(milliseconds: 1700));
    await _systemVoice.speak('progress_mission_complete');
  }
}
```

---

### 1.2 HeartSystem Service [CRITICO - PRIORIDAD 1]

**Archivo:** `apps/mobile/lib/core/services/heart_system.dart`

**Descripcion:** Sistema de corazones con Grace Mode (diferenciador clave vs Duolingo).

```dart
import 'dart:math';
import 'package:flutter/foundation.dart';
import 'package:hive/hive.dart';

/// Modos de practica disponibles
enum PracticeMode {
  /// Modo normal: ganas XP y Oro, pierdes corazones
  normal,

  /// Modo gracia: puedes practicar sin ganar recompensas
  /// Se activa cuando los corazones llegan a 0
  grace,
}

/// Sistema de Corazones con Grace Mode
///
/// PRINCIPIO FUNDAMENTAL: "Nunca bloquear el aprendizaje"
///
/// Cuando los corazones llegan a 0, el usuario puede:
/// 1. Ver un anuncio para recuperar 1 corazon
/// 2. Pagar 150 Oro para recargar todos
/// 3. Esperar 4 horas por regeneracion
/// 4. Entrar en GRACE MODE (practica sin recompensas)
class HeartSystem extends ChangeNotifier {
  static const int maxHearts = 5;
  static const Duration regenTime = Duration(hours: 4);
  static const int heartRechargeGoldCost = 150;
  static const int maxAdsPerDay = 3;

  int _hearts = 5;
  PracticeMode _mode = PracticeMode.normal;
  DateTime _lastHeartLostAt = DateTime.now();
  DateTime _lastHeartRegenAt = DateTime.now();
  int _adsWatchedToday = 0;
  DateTime _lastAdWatchDate = DateTime.now();

  // Getters
  int get hearts => _hearts;
  PracticeMode get mode => _mode;
  bool get isGraceMode => _mode == PracticeMode.grace;
  bool get hasHearts => _hearts > 0;
  int get adsRemainingToday => max(0, maxAdsPerDay - _adsWatchedToday);

  /// Tiempo restante para el proximo corazon
  Duration get timeUntilNextHeart {
    if (_hearts >= maxHearts) return Duration.zero;

    final elapsed = DateTime.now().difference(_lastHeartRegenAt);
    final remaining = regenTime - elapsed;
    return remaining.isNegative ? Duration.zero : remaining;
  }

  /// Inicializa el sistema cargando datos de Hive
  Future<void> initialize() async {
    final box = await Hive.openBox('heart_system');

    _hearts = box.get('hearts', defaultValue: maxHearts);
    _lastHeartRegenAt = DateTime.parse(
      box.get('lastHeartRegenAt', defaultValue: DateTime.now().toIso8601String())
    );
    _adsWatchedToday = box.get('adsWatchedToday', defaultValue: 0);
    _lastAdWatchDate = DateTime.parse(
      box.get('lastAdWatchDate', defaultValue: DateTime.now().toIso8601String())
    );

    // Reset ads si es un nuevo dia
    _checkDailyAdReset();

    // Regenerar corazones pendientes
    _regenerateHearts();

    notifyListeners();
  }

  /// Pierde un corazon por respuesta incorrecta
  ///
  /// Solo aplica en modo NORMAL, no en GRACE MODE
  void loseHeart() {
    if (_mode == PracticeMode.grace) {
      debugPrint('HeartSystem: Grace mode - no heart lost');
      return;
    }

    _hearts = max(0, _hearts - 1);
    _lastHeartLostAt = DateTime.now();

    if (_hearts == 0) {
      debugPrint('HeartSystem: Hearts depleted - show recovery options');
      // El UI debe mostrar el dialogo de opciones
    }

    _saveState();
    notifyListeners();
  }

  /// Entra en Grace Mode (practica sin recompensas)
  void enterGraceMode() {
    _mode = PracticeMode.grace;
    _saveState();
    notifyListeners();
  }

  /// Sale de Grace Mode (cuando tiene corazones)
  void exitGraceMode() {
    if (_hearts > 0) {
      _mode = PracticeMode.normal;
      _saveState();
      notifyListeners();
    }
  }

  /// Restaura corazones via anuncio
  ///
  /// Retorna true si fue exitoso
  Future<bool> restoreHeartViaAd() async {
    _checkDailyAdReset();

    if (_adsWatchedToday >= maxAdsPerDay) {
      debugPrint('HeartSystem: Daily ad limit reached');
      return false;
    }

    // TODO: Integrar con AdMob
    // Aqui iria la logica de mostrar el anuncio rewarded

    _hearts = min(maxHearts, _hearts + 1);
    _adsWatchedToday++;

    if (_hearts > 0 && _mode == PracticeMode.grace) {
      _mode = PracticeMode.normal;
    }

    _saveState();
    notifyListeners();
    return true;
  }

  /// Restaura todos los corazones via Oro
  ///
  /// [currentGold] - Oro actual del usuario
  /// Retorna el nuevo balance de oro si fue exitoso, null si fallo
  int? restoreHeartsViaGold(int currentGold) {
    if (currentGold < heartRechargeGoldCost) {
      debugPrint('HeartSystem: Not enough gold');
      return null;
    }

    _hearts = maxHearts;
    _lastHeartRegenAt = DateTime.now();

    if (_mode == PracticeMode.grace) {
      _mode = PracticeMode.normal;
    }

    _saveState();
    notifyListeners();

    return currentGold - heartRechargeGoldCost;
  }

  /// Multiplicador de XP basado en el modo
  ///
  /// En Grace Mode: 0x (no ganas XP)
  /// En Normal: 1x
  double get xpMultiplier => _mode == PracticeMode.grace ? 0.0 : 1.0;

  /// Multiplicador de Oro basado en el modo
  double get goldMultiplier => _mode == PracticeMode.grace ? 0.0 : 1.0;

  /// Regenera corazones basado en tiempo transcurrido
  void _regenerateHearts() {
    if (_hearts >= maxHearts) return;

    final now = DateTime.now();
    final elapsed = now.difference(_lastHeartRegenAt);
    final heartsToRegen = elapsed.inMinutes ~/ regenTime.inMinutes;

    if (heartsToRegen > 0) {
      _hearts = min(maxHearts, _hearts + heartsToRegen);
      _lastHeartRegenAt = now;

      if (_hearts > 0 && _mode == PracticeMode.grace) {
        _mode = PracticeMode.normal;
      }

      _saveState();
    }
  }

  /// Reset del contador de anuncios diarios
  void _checkDailyAdReset() {
    final now = DateTime.now();
    final lastAdDay = DateTime(_lastAdWatchDate.year, _lastAdWatchDate.month, _lastAdWatchDate.day);
    final today = DateTime(now.year, now.month, now.day);

    if (today.isAfter(lastAdDay)) {
      _adsWatchedToday = 0;
      _lastAdWatchDate = now;
    }
  }

  /// Guarda el estado en Hive
  Future<void> _saveState() async {
    final box = await Hive.openBox('heart_system');
    await box.put('hearts', _hearts);
    await box.put('lastHeartRegenAt', _lastHeartRegenAt.toIso8601String());
    await box.put('adsWatchedToday', _adsWatchedToday);
    await box.put('lastAdWatchDate', _lastAdWatchDate.toIso8601String());
  }
}
```

---

### 1.3 OfflineActionQueue Service [CRITICO - PRIORIDAD 1]

**Archivo:** `apps/mobile/lib/core/services/offline_action_queue.dart`

**Descripcion:** Cola de acciones offline para sincronizar cuando hay conexion.

```dart
import 'package:flutter/foundation.dart';
import 'package:hive/hive.dart';
import 'package:connectivity_plus/connectivity_plus.dart';

/// Tipos de acciones que pueden ser encoladas
enum GameActionType {
  answerSubmission,    // Envio de respuesta
  battleComplete,      // Batalla completada
  xpGain,             // Ganancia de XP
  goldTransaction,    // Transaccion de oro
  streakUpdate,       // Actualizacion de racha
  achievementUnlock,  // Desbloqueo de logro
}

/// Accion pendiente de sincronizar
@HiveType(typeId: 10)
class PendingAction extends HiveObject {
  @HiveField(0)
  final String id;

  @HiveField(1)
  final GameActionType type;

  @HiveField(2)
  final Map<String, dynamic> payload;

  @HiveField(3)
  final DateTime timestamp;

  @HiveField(4)
  int retryCount;

  PendingAction({
    required this.id,
    required this.type,
    required this.payload,
    required this.timestamp,
    this.retryCount = 0,
  });

  Map<String, dynamic> toJson() => {
    'id': id,
    'type': type.name,
    'payload': payload,
    'timestamp': timestamp.toIso8601String(),
    'retry_count': retryCount,
  };
}

/// Cola de Acciones Offline
///
/// Permite que el juego funcione sin conexion y sincroniza
/// cuando vuelve a estar online.
///
/// PRINCIPIO: 100% offline-first para Colombia (buses, metro, zonas rurales)
class OfflineActionQueue extends ChangeNotifier {
  late Box<PendingAction> _queue;
  bool _isInitialized = false;
  bool _isSyncing = false;

  final Connectivity _connectivity = Connectivity();

  /// Callback para enviar acciones al servidor
  Future<bool> Function(PendingAction action)? onSendAction;

  /// Inicializa la cola
  Future<void> initialize() async {
    if (_isInitialized) return;

    // Registrar adapter de Hive
    if (!Hive.isAdapterRegistered(10)) {
      Hive.registerAdapter(PendingActionAdapter());
    }

    _queue = await Hive.openBox<PendingAction>('offline_queue');
    _isInitialized = true;

    // Escuchar cambios de conectividad
    _connectivity.onConnectivityChanged.listen((result) {
      if (result != ConnectivityResult.none) {
        syncPendingActions();
      }
    });

    // Intentar sync inicial
    syncPendingActions();
  }

  /// Cantidad de acciones pendientes
  int get pendingCount => _queue.length;

  /// Verifica si esta online
  Future<bool> get isOnline async {
    final result = await _connectivity.checkConnectivity();
    return result != ConnectivityResult.none;
  }

  /// Encola una accion para sincronizar
  ///
  /// Si esta online, intenta enviar inmediatamente.
  /// Si esta offline, guarda para enviar despues.
  Future<void> enqueue(GameActionType type, Map<String, dynamic> payload) async {
    final action = PendingAction(
      id: DateTime.now().millisecondsSinceEpoch.toString(),
      type: type,
      payload: payload,
      timestamp: DateTime.now(),
    );

    if (await isOnline && onSendAction != null) {
      // Intentar enviar inmediatamente
      final success = await onSendAction!(action);
      if (success) {
        debugPrint('OfflineQueue: Action sent immediately');
        return;
      }
    }

    // Guardar para despues
    await _queue.put(action.id, action);
    debugPrint('OfflineQueue: Action queued (${_queue.length} pending)');
    notifyListeners();
  }

  /// Encola un envio de respuesta
  Future<void> enqueueAnswerSubmission({
    required String encounterId,
    required String questionId,
    required String answerId,
    required int timeSpentSeconds,
  }) async {
    await enqueue(GameActionType.answerSubmission, {
      'encounter_id': encounterId,
      'question_id': questionId,
      'answer_id': answerId,
      'time_spent_seconds': timeSpentSeconds,
    });
  }

  /// Encola una batalla completada
  Future<void> enqueueBattleComplete({
    required String runId,
    required bool victory,
    required int xpEarned,
    required int goldEarned,
    required int starsEarned,
  }) async {
    await enqueue(GameActionType.battleComplete, {
      'run_id': runId,
      'victory': victory,
      'xp_earned': xpEarned,
      'gold_earned': goldEarned,
      'stars_earned': starsEarned,
    });
  }

  /// Sincroniza todas las acciones pendientes
  Future<void> syncPendingActions() async {
    if (_isSyncing || onSendAction == null) return;
    if (!await isOnline) return;
    if (_queue.isEmpty) return;

    _isSyncing = true;
    debugPrint('OfflineQueue: Starting sync of ${_queue.length} actions');

    final actions = _queue.values.toList();

    for (final action in actions) {
      try {
        final success = await onSendAction!(action);

        if (success) {
          await _queue.delete(action.id);
          debugPrint('OfflineQueue: Synced action ${action.id}');
        } else {
          action.retryCount++;
          if (action.retryCount >= 3) {
            // Descartar despues de 3 intentos fallidos
            await _queue.delete(action.id);
            debugPrint('OfflineQueue: Discarded action after 3 retries');
          }
        }
      } catch (e) {
        debugPrint('OfflineQueue: Sync error: $e');
        action.retryCount++;
      }
    }

    _isSyncing = false;
    notifyListeners();
    debugPrint('OfflineQueue: Sync complete (${_queue.length} remaining)');
  }

  /// Limpia la cola (usar con cuidado)
  Future<void> clearQueue() async {
    await _queue.clear();
    notifyListeners();
  }
}
```

---

### 1.4 HapticPatterns Service [IMPORTANTE - PRIORIDAD 2]

**Archivo:** `apps/mobile/lib/core/services/haptic_patterns.dart`

**Descripcion:** Patrones de vibracion para feedback tactil.

```dart
import 'package:flutter/services.dart';

/// Patrones de Feedback Haptico
///
/// Crea una experiencia tactil satisfactoria sincronizada con
/// las acciones del juego.
class HapticPatterns {
  /// Respuesta correcta: doble pulso rapido
  ///
  /// Timing: T+0ms light, T+50ms medium
  static Future<void> correctAnswer() async {
    HapticFeedback.mediumImpact();
    await Future.delayed(const Duration(milliseconds: 50));
    HapticFeedback.mediumImpact();
  }

  /// Respuesta incorrecta: impacto fuerte unico
  static void wrongAnswer() {
    HapticFeedback.heavyImpact();
  }

  /// Combo milestone (3, 5, 10): patron escalado
  ///
  /// Crea una sensacion de "power up" ascendente
  static Future<void> comboMilestone() async {
    HapticFeedback.lightImpact();
    await Future.delayed(const Duration(milliseconds: 30));
    HapticFeedback.mediumImpact();
    await Future.delayed(const Duration(milliseconds: 30));
    HapticFeedback.heavyImpact();
  }

  /// Subir de nivel: escalada dramatica
  static Future<void> levelUp() async {
    for (var i = 0; i < 3; i++) {
      HapticFeedback.lightImpact();
      await Future.delayed(const Duration(milliseconds: 50));
    }
    HapticFeedback.heavyImpact();
  }

  /// Subir de rango: patron maximo epico
  static Future<void> rankUp() async {
    for (var i = 0; i < 4; i++) {
      HapticFeedback.mediumImpact();
      await Future.delayed(const Duration(milliseconds: 100));
    }
    await Future.delayed(const Duration(milliseconds: 200));
    HapticFeedback.heavyImpact();
    await Future.delayed(const Duration(milliseconds: 50));
    HapticFeedback.heavyImpact();
  }

  /// Estrella ganada: pulso suave de celebracion
  static void starEarned() {
    HapticFeedback.selectionClick();
  }

  /// Victoria de batalla: patron celebratorio
  static Future<void> victory() async {
    HapticFeedback.mediumImpact();
    await Future.delayed(const Duration(milliseconds: 100));
    HapticFeedback.mediumImpact();
    await Future.delayed(const Duration(milliseconds: 100));
    HapticFeedback.heavyImpact();
  }

  /// Derrota: pulso melancolico
  static void defeat() {
    HapticFeedback.mediumImpact();
  }

  /// Perder corazon: impacto de "dolor"
  static void heartLost() {
    HapticFeedback.heavyImpact();
  }

  /// Tap de boton normal
  static void buttonTap() {
    HapticFeedback.selectionClick();
  }

  /// Confirmacion de accion
  static void confirm() {
    HapticFeedback.lightImpact();
  }

  /// Notificacion/Alerta
  static Future<void> notification() async {
    HapticFeedback.lightImpact();
    await Future.delayed(const Duration(milliseconds: 100));
    HapticFeedback.lightImpact();
  }
}
```

---

### 1.5 StreakService (Local) [MEDIO - PRIORIDAD 3]

**Archivo:** `apps/mobile/lib/core/services/streak_service.dart`

**Descripcion:** Manejo local de rachas con sincronizacion.

```dart
import 'package:flutter/foundation.dart';
import 'package:hive/hive.dart';

/// Servicio de Rachas (Local)
///
/// Mantiene el estado local de la racha y sincroniza con el backend.
class StreakService extends ChangeNotifier {
  int _currentStreak = 0;
  int _longestStreak = 0;
  DateTime? _lastActivityDate;
  int _freezeCount = 0;
  double _multiplier = 1.0;

  // Getters
  int get currentStreak => _currentStreak;
  int get longestStreak => _longestStreak;
  DateTime? get lastActivityDate => _lastActivityDate;
  int get freezeCount => _freezeCount;
  double get multiplier => _multiplier;

  /// Hora de reset diario (4:00 AM hora local)
  static const int resetHour = 4;

  /// Inicializa desde Hive
  Future<void> initialize() async {
    final box = await Hive.openBox('streak_data');

    _currentStreak = box.get('currentStreak', defaultValue: 0);
    _longestStreak = box.get('longestStreak', defaultValue: 0);
    _freezeCount = box.get('freezeCount', defaultValue: 0);

    final lastActivity = box.get('lastActivityDate');
    if (lastActivity != null) {
      _lastActivityDate = DateTime.parse(lastActivity);
    }

    _updateMultiplier();
    _checkStreakStatus();

    notifyListeners();
  }

  /// Registra actividad del dia
  ///
  /// Llamar cuando el usuario gana XP (minimo 20 XP para contar)
  Future<void> recordActivity() async {
    final today = _getStreakDay(DateTime.now());

    if (_lastActivityDate != null) {
      final lastDay = _getStreakDay(_lastActivityDate!);

      if (today.isAfter(lastDay)) {
        final daysDiff = today.difference(lastDay).inDays;

        if (daysDiff == 1) {
          // Dia consecutivo - incrementar racha
          _currentStreak++;
          if (_currentStreak > _longestStreak) {
            _longestStreak = _currentStreak;
          }
        } else if (daysDiff > 1) {
          // Se perdio la racha
          if (_freezeCount > 0) {
            // Usar freeze si hay disponible
            _freezeCount--;
          } else {
            _currentStreak = 1; // Empezar de nuevo
          }
        }
      }
      // Si es el mismo dia, no hacer nada
    } else {
      // Primera actividad
      _currentStreak = 1;
    }

    _lastActivityDate = DateTime.now();
    _updateMultiplier();
    await _saveState();
    notifyListeners();
  }

  /// Compra un Streak Freeze (200 Oro)
  ///
  /// Maximo 5 acumulables
  bool purchaseFreeze() {
    if (_freezeCount >= 5) return false;

    _freezeCount++;
    _saveState();
    notifyListeners();
    return true;
  }

  /// Usa un Streak Freeze para proteger la racha
  bool useFreeze() {
    if (_freezeCount <= 0) return false;

    _freezeCount--;
    _saveState();
    notifyListeners();
    return true;
  }

  /// Verifica si la racha esta en peligro
  bool get isStreakAtRisk {
    if (_lastActivityDate == null) return false;

    final today = _getStreakDay(DateTime.now());
    final lastDay = _getStreakDay(_lastActivityDate!);

    return today.isAfter(lastDay) && _currentStreak > 0;
  }

  /// Actualiza el multiplicador basado en la racha
  void _updateMultiplier() {
    if (_currentStreak >= 60) {
      _multiplier = 1.8;
    } else if (_currentStreak >= 30) {
      _multiplier = 1.5;
    } else if (_currentStreak >= 14) {
      _multiplier = 1.3;
    } else if (_currentStreak >= 7) {
      _multiplier = 1.2;
    } else {
      _multiplier = 1.0;
    }
  }

  /// Obtiene el "dia de racha" (considera reset a las 4am)
  DateTime _getStreakDay(DateTime dateTime) {
    if (dateTime.hour < resetHour) {
      return DateTime(dateTime.year, dateTime.month, dateTime.day - 1);
    }
    return DateTime(dateTime.year, dateTime.month, dateTime.day);
  }

  /// Verifica el estado de la racha
  void _checkStreakStatus() {
    if (_lastActivityDate == null) return;

    final today = _getStreakDay(DateTime.now());
    final lastDay = _getStreakDay(_lastActivityDate!);
    final daysDiff = today.difference(lastDay).inDays;

    if (daysDiff > 1 && _freezeCount == 0) {
      // Racha perdida
      _currentStreak = 0;
      _updateMultiplier();
    }
  }

  /// Guarda el estado en Hive
  Future<void> _saveState() async {
    final box = await Hive.openBox('streak_data');
    await box.put('currentStreak', _currentStreak);
    await box.put('longestStreak', _longestStreak);
    await box.put('freezeCount', _freezeCount);
    if (_lastActivityDate != null) {
      await box.put('lastActivityDate', _lastActivityDate!.toIso8601String());
    }
  }
}
```

---

## 2. Providers (Riverpod)

### 2.1 Heart System Provider

**Archivo:** `apps/mobile/lib/core/providers/heart_provider.dart`

```dart
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../services/heart_system.dart';

/// Provider para el sistema de corazones
final heartSystemProvider = ChangeNotifierProvider<HeartSystem>((ref) {
  final heartSystem = HeartSystem();
  // Inicializar asincrono
  heartSystem.initialize();
  return heartSystem;
});

/// Provider para verificar si tiene corazones
final hasHeartsProvider = Provider<bool>((ref) {
  return ref.watch(heartSystemProvider).hasHearts;
});

/// Provider para el modo actual (normal/grace)
final practiceModeProvider = Provider<PracticeMode>((ref) {
  return ref.watch(heartSystemProvider).mode;
});

/// Provider para el multiplicador de XP
final xpMultiplierProvider = Provider<double>((ref) {
  return ref.watch(heartSystemProvider).xpMultiplier;
});
```

### 2.2 Streak Provider

**Archivo:** `apps/mobile/lib/core/providers/streak_provider.dart`

```dart
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../services/streak_service.dart';

/// Provider para el sistema de rachas
final streakServiceProvider = ChangeNotifierProvider<StreakService>((ref) {
  final streakService = StreakService();
  streakService.initialize();
  return streakService;
});

/// Provider para la racha actual
final currentStreakProvider = Provider<int>((ref) {
  return ref.watch(streakServiceProvider).currentStreak;
});

/// Provider para el multiplicador de racha
final streakMultiplierProvider = Provider<double>((ref) {
  return ref.watch(streakServiceProvider).multiplier;
});

/// Provider para verificar si la racha esta en riesgo
final streakAtRiskProvider = Provider<bool>((ref) {
  return ref.watch(streakServiceProvider).isStreakAtRisk;
});
```

### 2.3 Offline Queue Provider

**Archivo:** `apps/mobile/lib/core/providers/offline_queue_provider.dart`

```dart
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../services/offline_action_queue.dart';

/// Provider para la cola offline
final offlineQueueProvider = ChangeNotifierProvider<OfflineActionQueue>((ref) {
  final queue = OfflineActionQueue();
  queue.initialize();
  return queue;
});

/// Provider para la cantidad de acciones pendientes
final pendingActionsCountProvider = Provider<int>((ref) {
  return ref.watch(offlineQueueProvider).pendingCount;
});
```

### 2.4 Economy Provider

**Archivo:** `apps/mobile/lib/core/providers/economy_provider.dart`

```dart
import 'package:flutter_riverpod/flutter_riverpod.dart';

/// Estado de la economia del usuario
class UserEconomy {
  final int gold;
  final int totalXp;
  final int level;
  final String rank;

  const UserEconomy({
    this.gold = 100,
    this.totalXp = 0,
    this.level = 1,
    this.rank = 'E',
  });

  UserEconomy copyWith({
    int? gold,
    int? totalXp,
    int? level,
    String? rank,
  }) {
    return UserEconomy(
      gold: gold ?? this.gold,
      totalXp: totalXp ?? this.totalXp,
      level: level ?? this.level,
      rank: rank ?? this.rank,
    );
  }
}

/// Notifier para la economia
class EconomyNotifier extends StateNotifier<UserEconomy> {
  EconomyNotifier() : super(const UserEconomy());

  void addGold(int amount) {
    state = state.copyWith(gold: state.gold + amount);
  }

  void spendGold(int amount) {
    if (state.gold >= amount) {
      state = state.copyWith(gold: state.gold - amount);
    }
  }

  void addXp(int amount) {
    final newXp = state.totalXp + amount;
    final newLevel = _calculateLevel(newXp);
    final newRank = _calculateRank(newLevel);

    state = state.copyWith(
      totalXp: newXp,
      level: newLevel,
      rank: newRank,
    );
  }

  int _calculateLevel(int xp) {
    int level = 1;
    int xpForNext = 100;
    int remaining = xp;

    while (remaining >= xpForNext) {
      remaining -= xpForNext;
      level++;
      xpForNext = (100 * (level * 1.5)).toInt();
    }

    return level;
  }

  String _calculateRank(int level) {
    if (level >= 50) return 'S';
    if (level >= 40) return 'A';
    if (level >= 30) return 'B';
    if (level >= 20) return 'C';
    if (level >= 10) return 'D';
    return 'E';
  }

  void setFromServer(UserEconomy economy) {
    state = economy;
  }
}

/// Provider de economia
final economyProvider = StateNotifierProvider<EconomyNotifier, UserEconomy>((ref) {
  return EconomyNotifier();
});

/// Provider de oro
final goldProvider = Provider<int>((ref) {
  return ref.watch(economyProvider).gold;
});

/// Provider de nivel
final levelProvider = Provider<int>((ref) {
  return ref.watch(economyProvider).level;
});

/// Provider de rango
final rankProvider = Provider<String>((ref) {
  return ref.watch(economyProvider).rank;
});
```

---

## 3. Widgets y Componentes UI

### 3.1 ExplanationModal [CRITICO]

**Archivo:** `apps/mobile/lib/features/dungeon/presentation/widgets/explanation_modal.dart`

```dart
import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';

/// Modal de Explicacion de Respuesta Incorrecta
///
/// Muestra la respuesta correcta y una explicacion detallada.
/// PRINCIPIO: "Siempre explicar errores"
class ExplanationModal extends StatelessWidget {
  final String correctAnswer;
  final String explanation;
  final String? videoUrl;
  final VoidCallback onContinue;

  const ExplanationModal({
    super.key,
    required this.correctAnswer,
    required this.explanation,
    this.videoUrl,
    required this.onContinue,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: const Color(0xFF1A1A2E),
        borderRadius: const BorderRadius.vertical(top: Radius.circular(24)),
        border: Border.all(
          color: Colors.amber.withOpacity(0.3),
          width: 1,
        ),
      ),
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Header con icono de libro
            Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(
                    color: Colors.amber.withOpacity(0.2),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: const Icon(
                    Icons.menu_book,
                    color: Colors.amber,
                    size: 24,
                  ),
                ),
                const SizedBox(width: 12),
                const Expanded(
                  child: Text(
                    'Analiza el Error',
                    style: TextStyle(
                      color: Colors.amber,
                      fontSize: 20,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
              ],
            ).animate().fadeIn(duration: 200.ms).slideY(begin: 0.1),

            const SizedBox(height: 20),

            // Respuesta correcta
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: Colors.green.withOpacity(0.15),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(
                  color: Colors.green.withOpacity(0.5),
                  width: 1,
                ),
              ),
              child: Row(
                children: [
                  const Icon(
                    Icons.check_circle,
                    color: Colors.green,
                    size: 24,
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text(
                          'Respuesta Correcta:',
                          style: TextStyle(
                            color: Colors.green,
                            fontSize: 12,
                            fontWeight: FontWeight.w500,
                          ),
                        ),
                        const SizedBox(height: 4),
                        Text(
                          correctAnswer,
                          style: const TextStyle(
                            color: Colors.white,
                            fontSize: 16,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ).animate().fadeIn(duration: 300.ms, delay: 100.ms).slideY(begin: 0.1),

            const SizedBox(height: 16),

            // Explicacion
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: Colors.white.withOpacity(0.05),
                borderRadius: BorderRadius.circular(12),
              ),
              child: Text(
                explanation,
                style: const TextStyle(
                  color: Colors.white70,
                  fontSize: 14,
                  height: 1.5,
                ),
              ),
            ).animate().fadeIn(duration: 300.ms, delay: 200.ms),

            // Video opcional
            if (videoUrl != null) ...[
              const SizedBox(height: 16),
              OutlinedButton.icon(
                onPressed: () {
                  // TODO: Abrir reproductor de video
                },
                icon: const Icon(Icons.play_circle_outline),
                label: const Text('Ver Video Explicativo'),
                style: OutlinedButton.styleFrom(
                  foregroundColor: Colors.cyan,
                  side: const BorderSide(color: Colors.cyan),
                  padding: const EdgeInsets.symmetric(
                    horizontal: 20,
                    vertical: 12,
                  ),
                ),
              ).animate().fadeIn(duration: 300.ms, delay: 300.ms),
            ],

            const SizedBox(height: 24),

            // Boton continuar
            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                onPressed: onContinue,
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.amber,
                  foregroundColor: Colors.black,
                  padding: const EdgeInsets.symmetric(vertical: 16),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                ),
                child: const Text(
                  'CONTINUAR',
                  style: TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
            ).animate().fadeIn(duration: 300.ms, delay: 400.ms).slideY(begin: 0.1),
          ],
        ),
      ),
    );
  }

  /// Muestra el modal como bottom sheet
  static Future<void> show({
    required BuildContext context,
    required String correctAnswer,
    required String explanation,
    String? videoUrl,
    required VoidCallback onContinue,
  }) {
    return showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      isDismissible: false,
      enableDrag: false,
      builder: (ctx) => ExplanationModal(
        correctAnswer: correctAnswer,
        explanation: explanation,
        videoUrl: videoUrl,
        onContinue: () {
          Navigator.pop(ctx);
          onContinue();
        },
      ),
    );
  }
}
```

### 3.2 HeartDepletedDialog [CRITICO]

**Archivo:** `apps/mobile/lib/features/dungeon/presentation/widgets/heart_depleted_dialog.dart`

```dart
import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/providers/heart_provider.dart';
import '../../../../core/providers/economy_provider.dart';
import '../../../../core/services/heart_system.dart';

/// Dialogo cuando se agotan los corazones
///
/// Ofrece opciones:
/// 1. Ver anuncio (+1 corazon)
/// 2. Pagar con Oro (150 Oro = 5 corazones)
/// 3. Esperar regeneracion
/// 4. GRACE MODE (practica sin recompensas)
class HeartDepletedDialog extends ConsumerWidget {
  const HeartDepletedDialog({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final heartSystem = ref.watch(heartSystemProvider);
    final gold = ref.watch(goldProvider);
    final adsRemaining = heartSystem.adsRemainingToday;
    final timeUntilNext = heartSystem.timeUntilNextHeart;

    return Dialog(
      backgroundColor: Colors.transparent,
      child: Container(
        padding: const EdgeInsets.all(24),
        decoration: BoxDecoration(
          color: const Color(0xFF1A1A2E),
          borderRadius: BorderRadius.circular(24),
          border: Border.all(
            color: Colors.red.withOpacity(0.5),
            width: 2,
          ),
          boxShadow: [
            BoxShadow(
              color: Colors.red.withOpacity(0.3),
              blurRadius: 20,
              spreadRadius: 5,
            ),
          ],
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            // Icono de corazon roto
            const Icon(
              Icons.heart_broken,
              color: Colors.red,
              size: 64,
            ).animate().shake(duration: 500.ms),

            const SizedBox(height: 16),

            // Titulo
            const Text(
              'MANA AGOTADO',
              style: TextStyle(
                color: Colors.red,
                fontSize: 24,
                fontWeight: FontWeight.bold,
                letterSpacing: 2,
              ),
            ).animate().fadeIn(),

            const SizedBox(height: 8),

            const Text(
              'Has usado todos tus corazones.\nPero un Cazador no se rinde.',
              textAlign: TextAlign.center,
              style: TextStyle(
                color: Colors.white70,
                fontSize: 14,
              ),
            ).animate().fadeIn(delay: 100.ms),

            const SizedBox(height: 24),

            // Opcion 1: Ver anuncio
            if (adsRemaining > 0)
              _buildOptionButton(
                icon: Icons.play_circle_filled,
                iconColor: Colors.green,
                title: 'Ver Anuncio',
                subtitle: '+1 corazon (${adsRemaining} restantes hoy)',
                onTap: () async {
                  final success = await heartSystem.restoreHeartViaAd();
                  if (success && context.mounted) {
                    Navigator.pop(context, 'ad');
                  }
                },
              ).animate().fadeIn(delay: 200.ms).slideX(begin: -0.1),

            const SizedBox(height: 12),

            // Opcion 2: Pagar con Oro
            _buildOptionButton(
              icon: Icons.monetization_on,
              iconColor: Colors.amber,
              title: 'Recargar (150 Oro)',
              subtitle: gold >= 150 ? 'Restaura 5 corazones' : 'Oro insuficiente',
              enabled: gold >= 150,
              onTap: () {
                final newGold = heartSystem.restoreHeartsViaGold(gold);
                if (newGold != null) {
                  ref.read(economyProvider.notifier).spendGold(150);
                  Navigator.pop(context, 'gold');
                }
              },
            ).animate().fadeIn(delay: 300.ms).slideX(begin: -0.1),

            const SizedBox(height: 12),

            // Opcion 3: Esperar
            _buildOptionButton(
              icon: Icons.access_time,
              iconColor: Colors.blue,
              title: 'Esperar',
              subtitle: 'Proximo corazon en ${_formatDuration(timeUntilNext)}',
              onTap: () {
                Navigator.pop(context, 'wait');
              },
            ).animate().fadeIn(delay: 400.ms).slideX(begin: -0.1),

            const SizedBox(height: 24),

            // Separador con "o"
            Row(
              children: [
                Expanded(child: Divider(color: Colors.white24)),
                const Padding(
                  padding: EdgeInsets.symmetric(horizontal: 16),
                  child: Text(
                    'o',
                    style: TextStyle(color: Colors.white54),
                  ),
                ),
                Expanded(child: Divider(color: Colors.white24)),
              ],
            ),

            const SizedBox(height: 24),

            // Opcion 4: GRACE MODE (destacada)
            Container(
              width: double.infinity,
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  colors: [
                    Colors.purple.withOpacity(0.3),
                    Colors.indigo.withOpacity(0.3),
                  ],
                ),
                borderRadius: BorderRadius.circular(16),
                border: Border.all(
                  color: Colors.purple.withOpacity(0.5),
                  width: 2,
                ),
              ),
              child: Material(
                color: Colors.transparent,
                child: InkWell(
                  onTap: () {
                    heartSystem.enterGraceMode();
                    Navigator.pop(context, 'grace');
                  },
                  borderRadius: BorderRadius.circular(16),
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: Row(
                      children: [
                        Container(
                          padding: const EdgeInsets.all(12),
                          decoration: BoxDecoration(
                            color: Colors.purple.withOpacity(0.3),
                            borderRadius: BorderRadius.circular(12),
                          ),
                          child: const Icon(
                            Icons.auto_awesome,
                            color: Colors.purple,
                            size: 28,
                          ),
                        ),
                        const SizedBox(width: 16),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: const [
                              Text(
                                'MODO GRACIA',
                                style: TextStyle(
                                  color: Colors.purple,
                                  fontSize: 18,
                                  fontWeight: FontWeight.bold,
                                ),
                              ),
                              SizedBox(height: 4),
                              Text(
                                'Practica sin ganar XP ni Oro\n(Sigue aprendiendo sin penalizacion)',
                                style: TextStyle(
                                  color: Colors.white70,
                                  fontSize: 12,
                                ),
                              ),
                            ],
                          ),
                        ),
                        const Icon(
                          Icons.arrow_forward_ios,
                          color: Colors.purple,
                          size: 20,
                        ),
                      ],
                    ),
                  ),
                ),
              ),
            ).animate().fadeIn(delay: 500.ms).scale(begin: const Offset(0.95, 0.95)),
          ],
        ),
      ),
    );
  }

  Widget _buildOptionButton({
    required IconData icon,
    required Color iconColor,
    required String title,
    required String subtitle,
    required VoidCallback onTap,
    bool enabled = true,
  }) {
    return Opacity(
      opacity: enabled ? 1.0 : 0.5,
      child: Container(
        width: double.infinity,
        decoration: BoxDecoration(
          color: Colors.white.withOpacity(0.05),
          borderRadius: BorderRadius.circular(12),
          border: Border.all(
            color: Colors.white.withOpacity(0.1),
          ),
        ),
        child: Material(
          color: Colors.transparent,
          child: InkWell(
            onTap: enabled ? onTap : null,
            borderRadius: BorderRadius.circular(12),
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Row(
                children: [
                  Icon(icon, color: iconColor, size: 28),
                  const SizedBox(width: 16),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          title,
                          style: const TextStyle(
                            color: Colors.white,
                            fontSize: 16,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                        Text(
                          subtitle,
                          style: TextStyle(
                            color: Colors.white.withOpacity(0.6),
                            fontSize: 12,
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }

  String _formatDuration(Duration duration) {
    final hours = duration.inHours;
    final minutes = duration.inMinutes % 60;
    if (hours > 0) {
      return '${hours}h ${minutes}m';
    }
    return '${minutes}m';
  }
}
```

### 3.3 StreakWidget [IMPORTANTE]

**Archivo:** `apps/mobile/lib/shared/widgets/streak_widget.dart`

```dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_animate/flutter_animate.dart';

import '../../core/providers/streak_provider.dart';

/// Widget que muestra la racha actual del usuario
class StreakWidget extends ConsumerWidget {
  final bool compact;

  const StreakWidget({
    super.key,
    this.compact = false,
  });

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final streak = ref.watch(currentStreakProvider);
    final multiplier = ref.watch(streakMultiplierProvider);
    final atRisk = ref.watch(streakAtRiskProvider);

    if (compact) {
      return _buildCompact(streak, atRisk);
    }

    return _buildFull(streak, multiplier, atRisk);
  }

  Widget _buildCompact(int streak, bool atRisk) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
      decoration: BoxDecoration(
        color: atRisk
            ? Colors.orange.withOpacity(0.2)
            : Colors.amber.withOpacity(0.2),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(
          color: atRisk ? Colors.orange : Colors.amber,
          width: 1,
        ),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(
            Icons.local_fire_department,
            color: atRisk ? Colors.orange : Colors.amber,
            size: 18,
          ),
          const SizedBox(width: 4),
          Text(
            '$streak',
            style: TextStyle(
              color: atRisk ? Colors.orange : Colors.amber,
              fontSize: 14,
              fontWeight: FontWeight.bold,
            ),
          ),
          if (atRisk) ...[
            const SizedBox(width: 4),
            const Icon(
              Icons.warning_amber,
              color: Colors.orange,
              size: 14,
            ).animate(onPlay: (c) => c.repeat()).shake(duration: 1.seconds),
          ],
        ],
      ),
    );
  }

  Widget _buildFull(int streak, double multiplier, bool atRisk) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: atRisk
              ? [Colors.orange.withOpacity(0.2), Colors.red.withOpacity(0.1)]
              : [Colors.amber.withOpacity(0.2), Colors.orange.withOpacity(0.1)],
        ),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: atRisk ? Colors.orange : Colors.amber,
          width: 2,
        ),
      ),
      child: Column(
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(
                Icons.local_fire_department,
                color: atRisk ? Colors.orange : Colors.amber,
                size: 32,
              ).animate(
                onPlay: (c) => c.repeat(),
              ).shimmer(duration: 2.seconds, color: Colors.white.withOpacity(0.3)),
              const SizedBox(width: 8),
              Text(
                '$streak',
                style: TextStyle(
                  color: Colors.white,
                  fontSize: 36,
                  fontWeight: FontWeight.bold,
                ),
              ),
              const SizedBox(width: 8),
              Text(
                'DIAS',
                style: TextStyle(
                  color: Colors.white70,
                  fontSize: 14,
                  fontWeight: FontWeight.w500,
                ),
              ),
            ],
          ),
          if (multiplier > 1.0) ...[
            const SizedBox(height: 8),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
              decoration: BoxDecoration(
                color: Colors.green.withOpacity(0.3),
                borderRadius: BorderRadius.circular(12),
              ),
              child: Text(
                '+${((multiplier - 1) * 100).toInt()}% XP Bonus',
                style: const TextStyle(
                  color: Colors.green,
                  fontSize: 12,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ),
          ],
          if (atRisk) ...[
            const SizedBox(height: 8),
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                const Icon(
                  Icons.warning_amber,
                  color: Colors.orange,
                  size: 16,
                ),
                const SizedBox(width: 4),
                const Text(
                  'Practica hoy para mantener tu racha!',
                  style: TextStyle(
                    color: Colors.orange,
                    fontSize: 12,
                  ),
                ),
              ],
            ).animate(onPlay: (c) => c.repeat()).fade(
              begin: 0.7,
              end: 1.0,
              duration: 800.ms,
            ),
          ],
        ],
      ),
    );
  }
}
```

### 3.4 GraceModeIndicator [CRITICO]

**Archivo:** `apps/mobile/lib/shared/widgets/grace_mode_indicator.dart`

```dart
import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';

/// Indicador visual cuando el usuario esta en Grace Mode
class GraceModeIndicator extends StatelessWidget {
  const GraceModeIndicator({super.key});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [
            Colors.purple.withOpacity(0.3),
            Colors.indigo.withOpacity(0.3),
          ],
        ),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(
          color: Colors.purple.withOpacity(0.5),
          width: 1,
        ),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          const Icon(
            Icons.auto_awesome,
            color: Colors.purple,
            size: 18,
          ).animate(onPlay: (c) => c.repeat()).shimmer(
            duration: 2.seconds,
            color: Colors.white.withOpacity(0.3),
          ),
          const SizedBox(width: 8),
          const Text(
            'MODO GRACIA',
            style: TextStyle(
              color: Colors.purple,
              fontSize: 12,
              fontWeight: FontWeight.bold,
              letterSpacing: 1,
            ),
          ),
        ],
      ),
    );
  }
}
```

### 3.5 ComboBadge [IMPORTANTE]

**Archivo:** `apps/mobile/lib/features/dungeon/presentation/widgets/combo_badge.dart`

```dart
import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';

/// Badge animado que muestra el combo actual
class ComboBadge extends StatelessWidget {
  final int combo;

  const ComboBadge({
    super.key,
    required this.combo,
  });

  @override
  Widget build(BuildContext context) {
    if (combo < 3) return const SizedBox.shrink();

    // Determinar color basado en combo
    Color comboColor;
    String comboText;

    if (combo >= 10) {
      comboColor = Colors.purple;
      comboText = 'IMPARABLE';
    } else if (combo >= 5) {
      comboColor = Colors.orange;
      comboText = 'EN FUEGO';
    } else {
      comboColor = Colors.cyan;
      comboText = 'COMBO';
    }

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [
            comboColor.withOpacity(0.8),
            comboColor.withOpacity(0.5),
          ],
        ),
        borderRadius: BorderRadius.circular(20),
        boxShadow: [
          BoxShadow(
            color: comboColor.withOpacity(0.5),
            blurRadius: 10,
            spreadRadius: 2,
          ),
        ],
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          const Icon(
            Icons.flash_on,
            color: Colors.white,
            size: 20,
          ),
          const SizedBox(width: 4),
          Text(
            '$comboText x$combo',
            style: const TextStyle(
              color: Colors.white,
              fontSize: 14,
              fontWeight: FontWeight.bold,
            ),
          ),
        ],
      ),
    )
        .animate(onPlay: (c) => c.repeat(reverse: true))
        .scale(begin: const Offset(1, 1), end: const Offset(1.05, 1.05), duration: 500.ms);
  }
}
```

### 3.6 FloatingXP Widget

**Archivo:** `apps/mobile/lib/features/dungeon/presentation/widgets/floating_xp.dart`

```dart
import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';

/// Texto de XP flotante que aparece al ganar puntos
class FloatingXP extends StatelessWidget {
  final int xp;

  const FloatingXP({
    super.key,
    required this.xp,
  });

  @override
  Widget build(BuildContext context) {
    return Text(
      '+$xp XP',
      style: const TextStyle(
        color: Colors.amber,
        fontSize: 24,
        fontWeight: FontWeight.bold,
        shadows: [
          Shadow(
            color: Colors.amber,
            blurRadius: 10,
          ),
        ],
      ),
    )
        .animate()
        .fadeIn(duration: 100.ms)
        .slideY(begin: 0, end: -1, duration: 800.ms, curve: Curves.easeOut)
        .fadeOut(delay: 600.ms, duration: 200.ms);
  }
}
```

---

## 4. Integracion API

### 4.1 HeartsApiService

**Archivo:** `apps/mobile/lib/core/api/hearts_api_service.dart`

```dart
import 'package:dio/dio.dart';

class HeartsApiService {
  final Dio _dio;

  HeartsApiService(this._dio);

  /// Obtiene el estado actual de corazones
  Future<Map<String, dynamic>> getHeartStatus() async {
    final response = await _dio.get('/api/v1/hearts/status');
    return response.data;
  }

  /// Registra perdida de corazon
  Future<Map<String, dynamic>> loseHeart() async {
    final response = await _dio.post('/api/v1/hearts/lose');
    return response.data;
  }

  /// Recarga corazones con oro
  Future<Map<String, dynamic>> rechargeWithGold() async {
    final response = await _dio.post('/api/v1/hearts/recharge/gold');
    return response.data;
  }

  /// Recarga corazon con anuncio
  Future<Map<String, dynamic>> rechargeWithAd(String adRewardToken) async {
    final response = await _dio.post(
      '/api/v1/hearts/recharge/ad',
      data: {'reward_token': adRewardToken},
    );
    return response.data;
  }

  /// Entra en grace mode
  Future<Map<String, dynamic>> enterGraceMode() async {
    final response = await _dio.post('/api/v1/hearts/grace-mode/enter');
    return response.data;
  }

  /// Sale de grace mode
  Future<Map<String, dynamic>> exitGraceMode() async {
    final response = await _dio.post('/api/v1/hearts/grace-mode/exit');
    return response.data;
  }
}
```

### 4.2 EconomyApiService

**Archivo:** `apps/mobile/lib/core/api/economy_api_service.dart`

```dart
import 'package:dio/dio.dart';

class EconomyApiService {
  final Dio _dio;

  EconomyApiService(this._dio);

  /// Obtiene el estado de la economia del usuario
  Future<Map<String, dynamic>> getEconomyStatus() async {
    final response = await _dio.get('/api/v1/economy/status');
    return response.data;
  }

  /// Agrega oro al usuario
  Future<Map<String, dynamic>> addGold(int amount, String source) async {
    final response = await _dio.post(
      '/api/v1/economy/gold/add',
      data: {'amount': amount, 'source': source},
    );
    return response.data;
  }

  /// Gasta oro
  Future<Map<String, dynamic>> spendGold(int amount, String item) async {
    final response = await _dio.post(
      '/api/v1/economy/gold/spend',
      data: {'amount': amount, 'item': item},
    );
    return response.data;
  }

  /// Agrega XP
  Future<Map<String, dynamic>> addXp(int amount, String source) async {
    final response = await _dio.post(
      '/api/v1/economy/xp/add',
      data: {'amount': amount, 'source': source},
    );
    return response.data;
  }

  /// Obtiene historial de transacciones
  Future<List<Map<String, dynamic>>> getTransactionHistory({
    int limit = 50,
    int offset = 0,
  }) async {
    final response = await _dio.get(
      '/api/v1/economy/transactions',
      queryParameters: {'limit': limit, 'offset': offset},
    );
    return List<Map<String, dynamic>>.from(response.data['transactions']);
  }
}
```

### 4.3 StreakApiService

**Archivo:** `apps/mobile/lib/core/api/streak_api_service.dart`

```dart
import 'package:dio/dio.dart';

class StreakApiService {
  final Dio _dio;

  StreakApiService(this._dio);

  /// Obtiene el estado actual de la racha
  Future<Map<String, dynamic>> getStreakStatus() async {
    final response = await _dio.get('/api/v1/streaks/status');
    return response.data;
  }

  /// Registra actividad del dia
  Future<Map<String, dynamic>> recordActivity() async {
    final response = await _dio.post('/api/v1/streaks/activity');
    return response.data;
  }

  /// Usa un streak freeze
  Future<Map<String, dynamic>> useFreeze() async {
    final response = await _dio.post('/api/v1/streaks/freeze/use');
    return response.data;
  }

  /// Compra un streak freeze
  Future<Map<String, dynamic>> purchaseFreeze() async {
    final response = await _dio.post('/api/v1/streaks/freeze/purchase');
    return response.data;
  }

  /// Repara racha perdida
  Future<Map<String, dynamic>> repairStreak(String method) async {
    final response = await _dio.post(
      '/api/v1/streaks/repair',
      data: {'method': method}, // 'gold' o 'ad'
    );
    return response.data;
  }
}
```

### 4.4 NodeProgressApiService

**Archivo:** `apps/mobile/lib/core/api/node_progress_api_service.dart`

```dart
import 'package:dio/dio.dart';

class NodeProgressApiService {
  final Dio _dio;

  NodeProgressApiService(this._dio);

  /// Obtiene progreso de un reino
  Future<Map<String, dynamic>> getKingdomProgress(String kingdomId) async {
    final response = await _dio.get('/api/v1/progress/kingdom/$kingdomId');
    return response.data;
  }

  /// Obtiene progreso de un nodo
  Future<Map<String, dynamic>> getNodeProgress(String nodeId) async {
    final response = await _dio.get('/api/v1/progress/node/$nodeId');
    return response.data;
  }

  /// Actualiza progreso de nodo
  Future<Map<String, dynamic>> updateNodeProgress({
    required String nodeId,
    required double masteryPercent,
    required int starsEarned,
  }) async {
    final response = await _dio.post(
      '/api/v1/progress/node/$nodeId',
      data: {
        'mastery_percent': masteryPercent,
        'stars_earned': starsEarned,
      },
    );
    return response.data;
  }

  /// Verifica si puede desbloquear un nodo
  Future<bool> canUnlockNode(String nodeId) async {
    final response = await _dio.get('/api/v1/progress/node/$nodeId/can-unlock');
    return response.data['can_unlock'] ?? false;
  }

  /// Verifica si puede retar al boss
  Future<bool> canChallengeBoss(String kingdomId) async {
    final response = await _dio.get('/api/v1/progress/kingdom/$kingdomId/can-challenge-boss');
    return response.data['can_challenge'] ?? false;
  }
}
```

---

## 5. Modelos de Datos

### 5.1 AnswerResult Model (Actualizado)

**Archivo:** `apps/mobile/lib/features/dungeon/data/models/answer_result.dart`

```dart
/// Resultado de una respuesta enviada al servidor
class AnswerResult {
  final bool isCorrect;
  final String correctAnswerId;
  final String? explanation;  // CRITICO: siempre incluir
  final String? videoUrl;     // Opcional: video explicativo
  final int damageDealt;
  final int damageTaken;
  final int enemyCurrentHp;
  final int playerCurrentHp;
  final int currentCombo;
  final int xpEarned;
  final int goldEarned;
  final bool enemyDefeated;
  final bool playerDefeated;

  AnswerResult({
    required this.isCorrect,
    required this.correctAnswerId,
    this.explanation,
    this.videoUrl,
    required this.damageDealt,
    required this.damageTaken,
    required this.enemyCurrentHp,
    required this.playerCurrentHp,
    required this.currentCombo,
    required this.xpEarned,
    this.goldEarned = 0,
    required this.enemyDefeated,
    required this.playerDefeated,
  });

  factory AnswerResult.fromJson(Map<String, dynamic> json) {
    return AnswerResult(
      isCorrect: json['correct'] ?? false,
      correctAnswerId: json['correct_answer_id'] ?? '',
      explanation: json['explanation'],
      videoUrl: json['video_url'],
      damageDealt: json['damage_dealt'] ?? 0,
      damageTaken: json['damage_taken'] ?? 0,
      enemyCurrentHp: json['enemy_current_hp'] ?? 0,
      playerCurrentHp: json['player_current_hp'] ?? 0,
      currentCombo: json['current_combo'] ?? 0,
      xpEarned: json['xp_earned'] ?? 0,
      goldEarned: json['gold_earned'] ?? 0,
      enemyDefeated: json['enemy_defeated'] ?? false,
      playerDefeated: json['player_defeated'] ?? false,
    );
  }
}
```

### 5.2 UserProgress Model

**Archivo:** `apps/mobile/lib/core/models/user_progress.dart`

```dart
/// Progreso global del usuario
class UserProgress {
  final int level;
  final String rank;
  final int totalXp;
  final int gold;
  final int hearts;
  final bool isGraceMode;
  final int currentStreak;
  final double streakMultiplier;
  final Map<String, KingdomProgress> kingdoms;

  UserProgress({
    required this.level,
    required this.rank,
    required this.totalXp,
    required this.gold,
    required this.hearts,
    required this.isGraceMode,
    required this.currentStreak,
    required this.streakMultiplier,
    required this.kingdoms,
  });

  factory UserProgress.fromJson(Map<String, dynamic> json) {
    final kingdomsMap = <String, KingdomProgress>{};
    final kingdomsJson = json['kingdoms'] as Map<String, dynamic>? ?? {};

    kingdomsJson.forEach((key, value) {
      kingdomsMap[key] = KingdomProgress.fromJson(value);
    });

    return UserProgress(
      level: json['level'] ?? 1,
      rank: json['rank'] ?? 'E',
      totalXp: json['total_xp'] ?? 0,
      gold: json['gold'] ?? 100,
      hearts: json['hearts'] ?? 5,
      isGraceMode: json['is_grace_mode'] ?? false,
      currentStreak: json['current_streak'] ?? 0,
      streakMultiplier: (json['streak_multiplier'] ?? 1.0).toDouble(),
      kingdoms: kingdomsMap,
    );
  }
}

/// Progreso en un reino especifico
class KingdomProgress {
  final String kingdomId;
  final double overallMastery;
  final String rank;
  final bool diagnosticCompleted;
  final bool bossDefeated;
  final int totalStars;
  final Map<String, NodeProgress> nodes;

  KingdomProgress({
    required this.kingdomId,
    required this.overallMastery,
    required this.rank,
    required this.diagnosticCompleted,
    required this.bossDefeated,
    required this.totalStars,
    required this.nodes,
  });

  factory KingdomProgress.fromJson(Map<String, dynamic> json) {
    final nodesMap = <String, NodeProgress>{};
    final nodesJson = json['nodes'] as Map<String, dynamic>? ?? {};

    nodesJson.forEach((key, value) {
      nodesMap[key] = NodeProgress.fromJson(value);
    });

    return KingdomProgress(
      kingdomId: json['kingdom_id'] ?? '',
      overallMastery: (json['overall_mastery'] ?? 0.0).toDouble(),
      rank: json['rank'] ?? 'E',
      diagnosticCompleted: json['diagnostic_completed'] ?? false,
      bossDefeated: json['boss_defeated'] ?? false,
      totalStars: json['total_stars'] ?? 0,
      nodes: nodesMap,
    );
  }
}

/// Progreso en un nodo especifico
class NodeProgress {
  final String nodeId;
  final double masteryPercent;
  final int starsEarned;
  final int timesCompleted;
  final double bestAccuracy;
  final bool isUnlocked;
  final DateTime? unlockedAt;

  NodeProgress({
    required this.nodeId,
    required this.masteryPercent,
    required this.starsEarned,
    required this.timesCompleted,
    required this.bestAccuracy,
    required this.isUnlocked,
    this.unlockedAt,
  });

  factory NodeProgress.fromJson(Map<String, dynamic> json) {
    return NodeProgress(
      nodeId: json['node_id'] ?? '',
      masteryPercent: (json['mastery_percent'] ?? 0.0).toDouble(),
      starsEarned: json['stars_earned'] ?? 0,
      timesCompleted: json['times_completed'] ?? 0,
      bestAccuracy: (json['best_accuracy'] ?? 0.0).toDouble(),
      isUnlocked: json['is_unlocked'] ?? false,
      unlockedAt: json['unlocked_at'] != null
          ? DateTime.parse(json['unlocked_at'])
          : null,
    );
  }
}
```

---

## 6. Assets y Recursos

### 6.1 Estructura de Assets de Audio

```
assets/audio/
├── voice/                    # Voiceovers del Sistema
│   ├── sistema_te_encontro.wav
│   ├── evaluacion_iniciada.wav
│   ├── calibrando_rango.wav
│   ├── rango_asignado.wav
│   ├── entrenamiento_comienza.wav
│   ├── bienvenido_cazador.wav
│   ├── nuevo_dia.wav
│   ├── selecciona_batalla.wav
│   ├── mision_aceptada.wav
│   ├── entrando_dungeon.wav
│   ├── correcto.wav
│   ├── poder_incrementado.wav
│   ├── combo_activado.wav
│   ├── excelente.wav
│   ├── imparable.wav
│   ├── respuesta_incorrecta.wav
│   ├── analiza_error.wav
│   ├── mana_reducido.wav
│   ├── mana_agotado.wav
│   ├── mana_restaurado.wav
│   ├── racha_mantenida.wav
│   ├── dedicacion_notable.wav
│   ├── racha_peligro.wav
│   ├── racha_perdida.wav
│   ├── logro_desbloqueado.wav
│   ├── nivel_alcanzado.wav
│   ├── rango_ascendido.wav
│   ├── victoria.wav
│   ├── mision_completada.wav
│   ├── sistema_observa.wav
│   ├── poder_crece.wav
│   └── boss_despertado.wav
│
├── sfx/                      # Efectos de sonido
│   ├── correct_ding.wav
│   ├── wrong_buzz.wav
│   ├── enemy_hit.wav
│   ├── player_hit.wav
│   ├── combo_3.wav
│   ├── combo_5.wav
│   ├── combo_10.wav
│   ├── heart_break.wav
│   ├── heart_restore.wav
│   ├── xp_gain.wav
│   ├── level_up.wav
│   ├── rank_up.wav
│   ├── star_ding.wav
│   ├── victory_fanfare.wav
│   ├── defeat_somber.wav
│   ├── button_tap.wav
│   └── button_confirm.wav
│
└── music/                    # Musica de fondo
    ├── portal_theme_loop.mp3
    ├── kingdom_selection.mp3
    ├── battle_normal.mp3
    ├── battle_boss.mp3
    ├── victory_fanfare.mp3
    └── defeat_somber.mp3
```

### 6.2 Actualizar pubspec.yaml

```yaml
# Agregar a pubspec.yaml:

flutter:
  assets:
    - assets/audio/voice/
    - assets/audio/sfx/
    - assets/audio/music/
    - assets/images/maps/
    - assets/images/bosses/
    - assets/images/monsters/
    - assets/images/ui/

dependencies:
  # Audio
  audioplayers: ^5.2.1

  # Animaciones
  flutter_animate: ^4.2.0

  # Almacenamiento offline
  hive: ^2.2.3
  hive_flutter: ^1.1.0

  # Conectividad
  connectivity_plus: ^5.0.2

  # State management
  flutter_riverpod: ^2.4.9

  # HTTP
  dio: ^5.4.0

  # WebSocket
  web_socket_channel: ^2.4.0

dev_dependencies:
  # Generador de adapters Hive
  hive_generator: ^2.0.1
  build_runner: ^2.4.8
```

---

## 7. Testing

### 7.1 Tests Unitarios Requeridos

```dart
// test/core/services/heart_system_test.dart

import 'package:flutter_test/flutter_test.dart';
import 'package:icfes_leveling/core/services/heart_system.dart';

void main() {
  group('HeartSystem', () {
    late HeartSystem heartSystem;

    setUp(() {
      heartSystem = HeartSystem();
    });

    test('starts with max hearts', () {
      expect(heartSystem.hearts, equals(HeartSystem.maxHearts));
    });

    test('loses heart on wrong answer in normal mode', () {
      heartSystem.loseHeart();
      expect(heartSystem.hearts, equals(4));
    });

    test('does not lose heart in grace mode', () {
      heartSystem.enterGraceMode();
      heartSystem.loseHeart();
      expect(heartSystem.hearts, equals(5));
    });

    test('xp multiplier is 0 in grace mode', () {
      heartSystem.enterGraceMode();
      expect(heartSystem.xpMultiplier, equals(0.0));
    });

    test('gold multiplier is 0 in grace mode', () {
      heartSystem.enterGraceMode();
      expect(heartSystem.goldMultiplier, equals(0.0));
    });
  });
}
```

```dart
// test/core/services/streak_service_test.dart

import 'package:flutter_test/flutter_test.dart';
import 'package:icfes_leveling/core/services/streak_service.dart';

void main() {
  group('StreakService', () {
    late StreakService streakService;

    setUp(() {
      streakService = StreakService();
    });

    test('starts with 0 streak', () {
      expect(streakService.currentStreak, equals(0));
    });

    test('multiplier is 1.0 at start', () {
      expect(streakService.multiplier, equals(1.0));
    });

    test('multiplier increases at 7 days', () {
      // Simular 7 dias de racha
      for (var i = 0; i < 7; i++) {
        streakService.recordActivity();
      }
      expect(streakService.multiplier, equals(1.2));
    });
  });
}
```

---

## 8. Checklist de Implementacion

### Fase 1: Servicios Core [CRITICO]
- [ ] `SystemVoice` creado
- [ ] `HeartSystem` con Grace Mode
- [ ] `OfflineActionQueue` con Hive
- [ ] `HapticPatterns` implementado

### Fase 2: Providers [CRITICO]
- [ ] `heartSystemProvider`
- [ ] `streakServiceProvider`
- [ ] `offlineQueueProvider`
- [ ] `economyProvider`

### Fase 3: Widgets UI [CRITICO]
- [ ] `ExplanationModal`
- [ ] `HeartDepletedDialog`
- [ ] `GraceModeIndicator`
- [ ] `ComboBadge`
- [ ] `FloatingXP`
- [ ] `StreakWidget`

### Fase 4: Integracion API [IMPORTANTE]
- [ ] `HeartsApiService`
- [ ] `EconomyApiService`
- [ ] `StreakApiService`
- [ ] `NodeProgressApiService`

### Fase 5: Integracion BattlePage [IMPORTANTE]
- [ ] Timelines de feedback (600ms rule)
- [ ] Sincronizacion audio + haptics + visual
- [ ] Mostrar explicacion en respuestas incorrectas
- [ ] Manejar perdida de corazones
- [ ] Mostrar combo badges

### Fase 6: Testing [MEDIO]
- [ ] Tests unitarios para HeartSystem
- [ ] Tests unitarios para StreakService
- [ ] Tests de integracion para OfflineQueue

---

## Notas Finales

### Prioridades de Implementacion

1. **CRITICO (Semana 1):** SystemVoice, HeartSystem, ExplanationModal
2. **IMPORTANTE (Semana 2):** Timelines, OfflineQueue, Haptics
3. **MEDIO (Semana 3):** Streaks UI, Economy integration

### Dependencias con Backend (Claude)

Los siguientes endpoints deben estar listos antes de integrar:
- `GET /api/v1/hearts/status`
- `POST /api/v1/hearts/lose`
- `POST /api/v1/hearts/recharge/*`
- `GET /api/v1/economy/status`
- `POST /api/v1/economy/gold/*`
- `POST /api/v1/economy/xp/add`
- `GET /api/v1/streaks/status`
- `POST /api/v1/streaks/activity`

### Dependencias con Assets (Humano)

Los siguientes assets deben estar listos:
- 32 archivos de voiceover en `assets/audio/voice/`
- 15 archivos SFX en `assets/audio/sfx/`
- 6 archivos de musica en `assets/audio/music/`

---

> **Documento de Tareas Frontend - ICFES Leveling**
> Para: Gemini (Frontend Developer)
> Version: 1.0 | 29 de Diciembre, 2025
