import 'dart:async';
import 'package:flutter/foundation.dart';
import 'action_queue.dart';
import 'action_syncer.dart';
import 'sync_action.dart';
import 'connectivity_monitor.dart';
import 'conflict_resolver.dart';
import '../utils/sync_logger.dart';

/// Result of a sync operation with retry
class SyncResult {
  final bool success;
  final int attempts;
  final String? lastError;
  final dynamic serverResponse;

  const SyncResult({
    required this.success,
    required this.attempts,
    this.lastError,
    this.serverResponse,
  });
}

class SyncManager extends ChangeNotifier {
  final ActionQueue _queue;
  final ActionSyncer _syncer;
  final ConnectivityMonitor _connectivityMonitor;
  final ConflictResolver _conflictResolver;

  /// Maximum number of retry attempts
  static const int maxRetries = 3;

  /// Base delay for exponential backoff (in milliseconds)
  static const int baseDelayMs = 1000;

  bool _isSyncing = false;
  bool get isSyncing => _isSyncing;

  /// Alias for [isSyncing] - used by UI components like SyncStatusChip.
  bool get isProcessing => _isSyncing;

  /// Returns the count of pending actions in the queue.
  int get pendingCount => _queue.length;

  /// Returns true if there are failed actions that need attention
  bool get hasFailedActions => _queue.hasFailedActions;

  StreamSubscription? _connectivitySubscription;

  SyncManager(
    this._queue,
    this._syncer,
    this._connectivityMonitor, [
    ConflictResolver? conflictResolver,
  ]) : _conflictResolver = conflictResolver ?? ConflictResolver();

  void init() {
    _connectivitySubscription = _connectivityMonitor.onConnectivityChanged.listen((isOnline) {
      if (isOnline) {
        _startSync();
      }
    });
  }

  /// Process a single action with exponential backoff retry
  /// Delays: 1s, 2s, 4s (max 3 attempts)
  Future<SyncResult> processWithRetry(SyncAction action) async {
    int attempts = 0;
    String? lastError;
    dynamic serverResponse;

    while (attempts < maxRetries) {
      attempts++;

      try {
        SyncLogger.log('sync_attempt', data: {
          'action_id': action.id,
          'attempt': attempts,
          'type': action.type.name,
        });

        final response = await _syncer.syncWithResponse(action);
        serverResponse = response;

        // Check for conflicts in the response
        if (response != null && response is Map && response['conflict'] == true) {
          await _handleConflict(action, response);
        }

        SyncLogger.log('sync_success', data: {
          'action_id': action.id,
          'attempts': attempts,
        });

        return SyncResult(
          success: true,
          attempts: attempts,
          serverResponse: serverResponse,
        );
      } catch (e) {
        lastError = e.toString();
        SyncLogger.log('sync_attempt_failed', data: {
          'action_id': action.id,
          'attempt': attempts,
          'error': lastError,
        });

        if (attempts < maxRetries) {
          // Exponential backoff: 1s, 2s, 4s
          final delayMs = baseDelayMs * (1 << (attempts - 1));
          SyncLogger.log('sync_retry_scheduled', data: {
            'action_id': action.id,
            'delay_ms': delayMs,
            'next_attempt': attempts + 1,
          });
          await Future.delayed(Duration(milliseconds: delayMs));
        }
      }
    }

    // All retries exhausted
    await _queue.markFailed(action.id, lastError ?? 'Unknown error', attempts);

    return SyncResult(
      success: false,
      attempts: attempts,
      lastError: lastError,
    );
  }

  /// Handle conflict between client and server data
  Future<void> _handleConflict(SyncAction action, Map<dynamic, dynamic> serverResponse) async {
    final field = action.data['field'] as String?;
    if (field == null) return;

    final serverValue = serverResponse['server_value'];
    final clientValue = action.data['value'];

    final resolvedValue = await _conflictResolver.resolve(
      field,
      serverValue,
      clientValue,
      clientTimestamp: action.clientTimestamp,
      serverTimestamp: serverResponse['server_timestamp'] != null
          ? DateTime.tryParse(serverResponse['server_timestamp'])
          : null,
    );

    SyncLogger.log('conflict_resolved', data: {
      'field': field,
      'server_value': serverValue,
      'client_value': clientValue,
      'resolved_value': resolvedValue,
    });
  }

  Future<void> _startSync() async {
    if (_isSyncing) return;
    _isSyncing = true;
    notifyListeners();

    try {
      final pendingActions = await _queue.getPending();
      for (final action in pendingActions) {
        final result = await processWithRetry(action);
        if (result.success) {
          await _queue.markSynced(action.id);
        }
      }
    } finally {
      _isSyncing = false;
      notifyListeners();
    }
  }

  /// Force a manual sync attempt
  Future<void> forceSync() async {
    if (await _connectivityMonitor.isOnline) {
      await _startSync();
    }
  }

  /// Get list of failed actions for UI display
  Future<List<SyncAction>> getFailedActions() async {
    return _queue.getFailedActions();
  }

  /// Retry all failed actions
  Future<void> retryFailedActions() async {
    if (_isSyncing) return;

    final failedActions = await _queue.getFailedActions();
    if (failedActions.isEmpty) return;

    _isSyncing = true;
    notifyListeners();

    try {
      for (final action in failedActions) {
        // Reset attempts before retrying
        await _queue.resetAttempts(action.id);
        final result = await processWithRetry(action);
        if (result.success) {
          await _queue.markSynced(action.id);
        }
      }
    } finally {
      _isSyncing = false;
      notifyListeners();
    }
  }

  @override
  void dispose() {
    _connectivitySubscription?.cancel();
    super.dispose();
  }
}