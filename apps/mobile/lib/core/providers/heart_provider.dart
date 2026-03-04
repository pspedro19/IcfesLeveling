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
