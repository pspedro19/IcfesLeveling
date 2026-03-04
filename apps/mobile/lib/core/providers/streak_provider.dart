import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../services/streak_service.dart';
import 'offline_queue_provider.dart';

/// Provider para el sistema de rachas
final streakServiceProvider = ChangeNotifierProvider<StreakService>((ref) {
  final streakService = StreakService();

  // Conectar con offline queue
  final offlineQueue = ref.watch(offlineQueueProvider);
  streakService.setOfflineQueue(offlineQueue);

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
