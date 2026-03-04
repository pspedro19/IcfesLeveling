import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/config/app_theme.dart';
import '../../core/sync/connectivity_monitor.dart';
import '../../core/sync/action_queue.dart';

class OfflineBanner extends ConsumerWidget {
  const OfflineBanner({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final isOnline = ref.watch(connectivityProvider).valueOrNull ?? true; // Default to true if loading
    final pendingActions = ref.watch(pendingActionsCountProvider).valueOrNull ?? 0;

    if (isOnline && pendingActions == 0) {
      return const SizedBox.shrink();
    }

    return AnimatedContainer(
      duration: const Duration(milliseconds: 300),
      height: isOnline ? (pendingActions > 0 ? 40 : 0) : 40,
      color: isOnline ? AppTheme.accentCyan : AppTheme.warningOrange,
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          onTap: () => _showSyncDetails(context, ref),
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16),
            child: Row(
              children: [
                if (!isOnline) ...[
                  const Icon(Icons.cloud_off, size: 16, color: Colors.white),
                  const SizedBox(width: 8),
                  const Expanded(
                    child: Text(
                      'Sin conexión - Los cambios se guardarán localmente',
                      style: TextStyle(color: Colors.white, fontSize: 12),
                    ),
                  ),
                ] else if (pendingActions > 0) ...[
                  const SizedBox(
                    width: 16,
                    height: 16,
                    child: CircularProgressIndicator(
                      strokeWidth: 2,
                      valueColor: AlwaysStoppedAnimation(Colors.white),
                    ),
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      'Sincronizando $pendingActions cambio(s)...',
                      style: const TextStyle(color: Colors.white, fontSize: 12),
                    ),
                  ),
                ],
                const Icon(Icons.chevron_right, size: 16, color: Colors.white),
              ],
            ),
          ),
        ),
      ),
    );
  }

  void _showSyncDetails(BuildContext context, WidgetRef ref) {
    // TODO: Mostrar detalles de sincronización
  }
}
