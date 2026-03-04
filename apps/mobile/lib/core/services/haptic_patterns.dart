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
