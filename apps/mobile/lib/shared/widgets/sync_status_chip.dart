import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/network/api_client.dart';

/// A small chip widget that displays the current synchronization status of the application.
/// It shows if data is currently being synchronized, or if there are pending items
/// to be synchronized when offline.
///
/// This widget observes the [syncManagerProvider] for its state.
class SyncStatusChip extends ConsumerWidget {
  const SyncStatusChip({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final syncManager = ref.watch(syncManagerProvider);
    final isSyncing = syncManager.isProcessing;
    final pendingCount = syncManager.pendingCount;

    if (pendingCount == 0 && !isSyncing) return const SizedBox.shrink();

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
      decoration: BoxDecoration(
        color: isSyncing ? Colors.blue : Colors.orange,
        borderRadius: BorderRadius.circular(20),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          if (isSyncing)
            const SizedBox(
              width: 12,
              height: 12,
              child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
            )
          else
            const Icon(Icons.sync_problem, size: 14, color: Colors.white),
          const SizedBox(width: 8),
          Text(
            isSyncing ? 'Sincronizando...' : '$pendingCount pendientes',
            style: const TextStyle(color: Colors.white, fontSize: 12, fontWeight: FontWeight.bold),
          ),
        ],
      ),
    );
  }
}
