import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/network/api_client.dart';
import '../../core/sync/action_queue.dart';
import '../../core/sync/sync_action.dart';

/// A comprehensive sync indicator widget that displays:
/// - Current sync status (syncing, pending, failed)
/// - Number of pending actions
/// - Button to force manual sync
/// - List of failed actions with retry option
class SyncIndicator extends ConsumerStatefulWidget {
  /// Whether to show in compact mode (just the chip)
  final bool compact;

  /// Whether to show failed actions list
  final bool showFailedActions;

  const SyncIndicator({
    super.key,
    this.compact = false,
    this.showFailedActions = true,
  });

  @override
  ConsumerState<SyncIndicator> createState() => _SyncIndicatorState();
}

class _SyncIndicatorState extends ConsumerState<SyncIndicator>
    with SingleTickerProviderStateMixin {
  late AnimationController _animationController;
  bool _isExpanded = false;

  @override
  void initState() {
    super.initState();
    _animationController = AnimationController(
      duration: const Duration(milliseconds: 1500),
      vsync: this,
    );
  }

  @override
  void dispose() {
    _animationController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final syncManager = ref.watch(syncManagerProvider);
    final isSyncing = syncManager.isProcessing;
    final pendingCount = syncManager.pendingCount;
    final hasFailedActions = syncManager.hasFailedActions;

    // Animate when syncing
    if (isSyncing) {
      _animationController.repeat();
    } else {
      _animationController.stop();
    }

    // Don't show if everything is synced and no failures
    if (pendingCount == 0 && !isSyncing && !hasFailedActions) {
      return const SizedBox.shrink();
    }

    if (widget.compact) {
      return _buildCompactIndicator(isSyncing, pendingCount, hasFailedActions);
    }

    return _buildFullIndicator(isSyncing, pendingCount, hasFailedActions);
  }

  Widget _buildCompactIndicator(bool isSyncing, int pendingCount, bool hasFailedActions) {
    Color bgColor;
    IconData icon;
    String text;

    if (isSyncing) {
      bgColor = Colors.blue;
      icon = Icons.sync;
      text = 'Sincronizando...';
    } else if (hasFailedActions) {
      bgColor = Colors.red;
      icon = Icons.error_outline;
      text = 'Error de sync';
    } else {
      bgColor = Colors.orange;
      icon = Icons.cloud_queue;
      text = '$pendingCount pendientes';
    }

    return GestureDetector(
      onTap: () => _showSyncDetails(context),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
        decoration: BoxDecoration(
          color: bgColor,
          borderRadius: BorderRadius.circular(20),
          boxShadow: [
            BoxShadow(
              color: bgColor.withOpacity(0.3),
              blurRadius: 8,
              offset: const Offset(0, 2),
            ),
          ],
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            if (isSyncing)
              RotationTransition(
                turns: _animationController,
                child: Icon(icon, size: 16, color: Colors.white),
              )
            else
              Icon(icon, size: 16, color: Colors.white),
            const SizedBox(width: 6),
            Text(
              text,
              style: const TextStyle(
                color: Colors.white,
                fontSize: 12,
                fontWeight: FontWeight.w600,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildFullIndicator(bool isSyncing, int pendingCount, bool hasFailedActions) {
    return Card(
      margin: const EdgeInsets.all(12),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          // Header
          ListTile(
            leading: _buildStatusIcon(isSyncing, hasFailedActions),
            title: Text(_getStatusTitle(isSyncing, pendingCount, hasFailedActions)),
            subtitle: Text(_getStatusSubtitle(isSyncing, pendingCount)),
            trailing: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                // Manual sync button
                IconButton(
                  icon: const Icon(Icons.refresh),
                  onPressed: isSyncing ? null : _forceSync,
                  tooltip: 'Forzar sincronizacion',
                ),
                // Expand/collapse button
                if (widget.showFailedActions && hasFailedActions)
                  IconButton(
                    icon: Icon(_isExpanded ? Icons.expand_less : Icons.expand_more),
                    onPressed: () => setState(() => _isExpanded = !_isExpanded),
                    tooltip: _isExpanded ? 'Ocultar detalles' : 'Ver detalles',
                  ),
              ],
            ),
          ),

          // Failed actions list (expandable)
          if (widget.showFailedActions && hasFailedActions && _isExpanded)
            _buildFailedActionsList(),
        ],
      ),
    );
  }

  Widget _buildStatusIcon(bool isSyncing, bool hasFailedActions) {
    if (isSyncing) {
      return RotationTransition(
        turns: _animationController,
        child: const Icon(Icons.sync, color: Colors.blue, size: 32),
      );
    } else if (hasFailedActions) {
      return const Icon(Icons.error_outline, color: Colors.red, size: 32);
    } else {
      return const Icon(Icons.cloud_queue, color: Colors.orange, size: 32);
    }
  }

  String _getStatusTitle(bool isSyncing, int pendingCount, bool hasFailedActions) {
    if (isSyncing) return 'Sincronizando...';
    if (hasFailedActions) return 'Error de sincronizacion';
    return '$pendingCount acciones pendientes';
  }

  String _getStatusSubtitle(bool isSyncing, int pendingCount) {
    if (isSyncing) return 'Por favor espera...';
    return 'Toca para sincronizar manualmente';
  }

  Widget _buildFailedActionsList() {
    return FutureBuilder<List<SyncAction>>(
      future: ref.read(syncManagerProvider).getFailedActions(),
      builder: (context, snapshot) {
        if (!snapshot.hasData || snapshot.data!.isEmpty) {
          return const SizedBox.shrink();
        }

        final failedActions = snapshot.data!;

        return Container(
          decoration: BoxDecoration(
            color: Colors.red.withOpacity(0.05),
            border: Border(
              top: BorderSide(color: Colors.red.withOpacity(0.2)),
            ),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Padding(
                padding: const EdgeInsets.all(12),
                child: Row(
                  children: [
                    const Icon(Icons.warning_amber, size: 16, color: Colors.red),
                    const SizedBox(width: 8),
                    Text(
                      '${failedActions.length} acciones fallidas',
                      style: const TextStyle(
                        fontWeight: FontWeight.w600,
                        color: Colors.red,
                      ),
                    ),
                    const Spacer(),
                    TextButton.icon(
                      onPressed: _retryAllFailed,
                      icon: const Icon(Icons.replay, size: 16),
                      label: const Text('Reintentar todo'),
                      style: TextButton.styleFrom(
                        foregroundColor: Colors.red,
                      ),
                    ),
                  ],
                ),
              ),
              ListView.builder(
                shrinkWrap: true,
                physics: const NeverScrollableScrollPhysics(),
                itemCount: failedActions.length.clamp(0, 5), // Show max 5
                itemBuilder: (context, index) {
                  final action = failedActions[index];
                  return _buildFailedActionTile(action);
                },
              ),
              if (failedActions.length > 5)
                Padding(
                  padding: const EdgeInsets.all(8),
                  child: Text(
                    '... y ${failedActions.length - 5} mas',
                    style: TextStyle(
                      color: Colors.grey[600],
                      fontSize: 12,
                    ),
                  ),
                ),
            ],
          ),
        );
      },
    );
  }

  Widget _buildFailedActionTile(SyncAction action) {
    return FutureBuilder<QueuedAction?>(
      future: ref.read(actionQueueProvider).getQueuedAction(action.id),
      builder: (context, snapshot) {
        final queuedAction = snapshot.data;
        final attempts = queuedAction?.attempts ?? 0;
        final lastError = queuedAction?.lastError ?? 'Error desconocido';

        return ListTile(
          dense: true,
          leading: Icon(
            _getActionIcon(action.type),
            size: 20,
            color: Colors.red[400],
          ),
          title: Text(
            _getActionTypeName(action.type),
            style: const TextStyle(fontSize: 14),
          ),
          subtitle: Text(
            'Intentos: $attempts - $lastError',
            style: TextStyle(fontSize: 11, color: Colors.grey[600]),
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
          ),
          trailing: IconButton(
            icon: const Icon(Icons.replay, size: 18),
            onPressed: () => _retryAction(action.id),
            tooltip: 'Reintentar',
          ),
        );
      },
    );
  }

  IconData _getActionIcon(SyncActionType type) {
    switch (type) {
      case SyncActionType.submitAnswer:
        return Icons.check_circle_outline;
      case SyncActionType.useHeart:
        return Icons.favorite_outline;
      case SyncActionType.extendStreak:
        return Icons.local_fire_department_outlined;
      case SyncActionType.updateState:
        return Icons.cloud_sync_outlined;
    }
  }

  String _getActionTypeName(SyncActionType type) {
    switch (type) {
      case SyncActionType.submitAnswer:
        return 'Enviar respuesta';
      case SyncActionType.useHeart:
        return 'Usar corazon';
      case SyncActionType.extendStreak:
        return 'Extender racha';
      case SyncActionType.updateState:
        return 'Actualizar estado';
    }
  }

  void _forceSync() {
    ref.read(syncManagerProvider).forceSync();
  }

  void _retryAllFailed() {
    ref.read(syncManagerProvider).retryFailedActions();
  }

  Future<void> _retryAction(String actionId) async {
    final queue = ref.read(actionQueueProvider);
    await queue.resetAttempts(actionId);
    ref.read(syncManagerProvider).forceSync();
  }

  void _showSyncDetails(BuildContext context) {
    showModalBottomSheet(
      context: context,
      builder: (context) => const SyncDetailsSheet(),
      isScrollControlled: true,
    );
  }
}

/// Bottom sheet with detailed sync information
class SyncDetailsSheet extends ConsumerWidget {
  const SyncDetailsSheet({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final syncManager = ref.watch(syncManagerProvider);
    final isSyncing = syncManager.isProcessing;
    final pendingCount = syncManager.pendingCount;

    return DraggableScrollableSheet(
      initialChildSize: 0.5,
      minChildSize: 0.25,
      maxChildSize: 0.85,
      expand: false,
      builder: (context, scrollController) {
        return Container(
          decoration: BoxDecoration(
            color: Theme.of(context).scaffoldBackgroundColor,
            borderRadius: const BorderRadius.vertical(top: Radius.circular(20)),
          ),
          child: Column(
            children: [
              // Handle bar
              Container(
                margin: const EdgeInsets.symmetric(vertical: 12),
                width: 40,
                height: 4,
                decoration: BoxDecoration(
                  color: Colors.grey[400],
                  borderRadius: BorderRadius.circular(2),
                ),
              ),
              // Title
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 16),
                child: Row(
                  children: [
                    const Text(
                      'Estado de Sincronizacion',
                      style: TextStyle(
                        fontSize: 20,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const Spacer(),
                    IconButton(
                      onPressed: () => Navigator.pop(context),
                      icon: const Icon(Icons.close),
                    ),
                  ],
                ),
              ),
              const Divider(),
              // Content
              Expanded(
                child: ListView(
                  controller: scrollController,
                  padding: const EdgeInsets.all(16),
                  children: [
                    // Status card
                    _buildStatusCard(isSyncing, pendingCount),
                    const SizedBox(height: 16),
                    // Actions
                    Row(
                      children: [
                        Expanded(
                          child: ElevatedButton.icon(
                            onPressed: isSyncing
                                ? null
                                : () => ref.read(syncManagerProvider).forceSync(),
                            icon: const Icon(Icons.sync),
                            label: const Text('Sincronizar ahora'),
                          ),
                        ),
                        const SizedBox(width: 12),
                        Expanded(
                          child: OutlinedButton.icon(
                            onPressed: () => ref.read(syncManagerProvider).retryFailedActions(),
                            icon: const Icon(Icons.replay),
                            label: const Text('Reintentar fallidos'),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 24),
                    // Failed actions
                    const Text(
                      'Acciones con error',
                      style: TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                    const SizedBox(height: 12),
                    const SyncIndicator(
                      compact: false,
                      showFailedActions: true,
                    ),
                  ],
                ),
              ),
            ],
          ),
        );
      },
    );
  }

  Widget _buildStatusCard(bool isSyncing, int pendingCount) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Row(
          children: [
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: isSyncing ? Colors.blue.withOpacity(0.1) : Colors.orange.withOpacity(0.1),
                borderRadius: BorderRadius.circular(12),
              ),
              child: Icon(
                isSyncing ? Icons.sync : Icons.cloud_queue,
                color: isSyncing ? Colors.blue : Colors.orange,
                size: 32,
              ),
            ),
            const SizedBox(width: 16),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    isSyncing ? 'Sincronizando' : 'Pendiente',
                    style: const TextStyle(
                      fontSize: 18,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  Text(
                    '$pendingCount acciones en cola',
                    style: TextStyle(color: Colors.grey[600]),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
