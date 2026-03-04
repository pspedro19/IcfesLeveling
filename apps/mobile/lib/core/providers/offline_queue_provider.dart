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
