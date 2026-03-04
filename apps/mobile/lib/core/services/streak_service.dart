import 'package:flutter/foundation.dart';
import 'package:hive/hive.dart';
import 'offline_action_queue.dart';

/// Servicio de Rachas (Local + Offline Sync)
///
/// Mantiene el estado local de la racha y sincroniza con el backend.
/// Usa OfflineActionQueue para persistir acciones cuando no hay conexion.
class StreakService extends ChangeNotifier {
  int _currentStreak = 0;
  int _longestStreak = 0;
  DateTime? _lastActivityDate;
  int _freezeCount = 0;
  double _multiplier = 1.0;
  OfflineActionQueue? _offlineQueue;

  // Getters
  int get currentStreak => _currentStreak;
  int get longestStreak => _longestStreak;
  DateTime? get lastActivityDate => _lastActivityDate;
  int get freezeCount => _freezeCount;
  double get multiplier => _multiplier;

  /// Hora de reset diario (4:00 AM hora local)
  static const int resetHour = 4;

  /// Configura la cola offline para sincronizacion
  void setOfflineQueue(OfflineActionQueue queue) {
    _offlineQueue = queue;
  }

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
  /// [xpEarned] cantidad de XP ganado para enviar al backend
  Future<void> recordActivity({int xpEarned = 20}) async {
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

    // Encolar para sincronizacion con backend
    if (_offlineQueue != null) {
      await _offlineQueue!.enqueueStreakExtend(xpEarned: xpEarned);
    }

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
