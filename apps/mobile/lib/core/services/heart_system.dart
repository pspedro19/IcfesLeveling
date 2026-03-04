import 'dart:math';
import 'package:flutter/foundation.dart';
import 'package:hive/hive.dart';

import 'admob_service.dart';

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
  Box? _box;

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
    _box = await Hive.openBox('heart_system');

    _hearts = _box!.get('hearts', defaultValue: maxHearts);
    _lastHeartRegenAt = DateTime.parse(
      _box!.get('lastHeartRegenAt', defaultValue: DateTime.now().toIso8601String())
    );
    _adsWatchedToday = _box!.get('adsWatchedToday', defaultValue: 0);
    _lastAdWatchDate = DateTime.parse(
      _box!.get('lastAdWatchDate', defaultValue: DateTime.now().toIso8601String())
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

    // Show rewarded ad via AdMob
    // AdMob integration requires google_mobile_ads package and ad unit ID
    // For now, mark as not available until AdMob is configured
    final adShown = await _showRewardedAd();
    if (!adShown) {
      debugPrint('HeartSystem: Ad not available');
      return false;
    }

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

  /// Show a rewarded ad. Returns true if the ad was watched successfully.
  /// Uses AdMobService singleton for ad loading and display.
  Future<bool> _showRewardedAd() async {
    try {
      final admob = AdMobService();
      return await admob.showRewardedAd();
    } catch (e) {
      debugPrint('HeartSystem: Ad show failed — $e');
      return false;
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
    final box = _box;
    if (box == null || !box.isOpen) return;
    await box.put('hearts', _hearts);
    await box.put('lastHeartRegenAt', _lastHeartRegenAt.toIso8601String());
    await box.put('adsWatchedToday', _adsWatchedToday);
    await box.put('lastAdWatchDate', _lastAdWatchDate.toIso8601String());
  }
}
