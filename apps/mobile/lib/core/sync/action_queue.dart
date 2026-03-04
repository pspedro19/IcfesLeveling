import 'dart:convert';
import 'dart:async';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:hive_flutter/hive_flutter.dart';
import 'sync_action.dart';
import '../network/api_client.dart';
import '../constants/api_constants.dart';
import '../utils/sync_logger.dart';

/// Extended action data stored in the queue
class QueuedAction {
  final SyncAction action;
  final int attempts;
  final String? lastError;
  final DateTime? lastAttemptTime;
  final bool isFailed;

  const QueuedAction({
    required this.action,
    this.attempts = 0,
    this.lastError,
    this.lastAttemptTime,
    this.isFailed = false,
  });

  Map<String, dynamic> toJson() => {
    'action': action.toJson(),
    'attempts': attempts,
    'lastError': lastError,
    'lastAttemptTime': lastAttemptTime?.toIso8601String(),
    'isFailed': isFailed,
  };

  factory QueuedAction.fromJson(Map<String, dynamic> json) {
    return QueuedAction(
      action: SyncAction.fromJson(json['action']),
      attempts: json['attempts'] ?? 0,
      lastError: json['lastError'],
      lastAttemptTime: json['lastAttemptTime'] != null
          ? DateTime.tryParse(json['lastAttemptTime'])
          : null,
      isFailed: json['isFailed'] ?? false,
    );
  }

  QueuedAction copyWith({
    SyncAction? action,
    int? attempts,
    String? lastError,
    DateTime? lastAttemptTime,
    bool? isFailed,
  }) {
    return QueuedAction(
      action: action ?? this.action,
      attempts: attempts ?? this.attempts,
      lastError: lastError ?? this.lastError,
      lastAttemptTime: lastAttemptTime ?? this.lastAttemptTime,
      isFailed: isFailed ?? this.isFailed,
    );
  }
}

class ActionQueue {
  static const _boxName = 'action_queue_v2';
  static const int maxRetries = 3;

  Box? _box;
  Completer<void>? _initCompleter;
  bool _isFlushing = false;

  Future<void> init() async {
    if (_box != null && _box!.isOpen) return;
    if (_initCompleter != null) return _initCompleter!.future;

    _initCompleter = Completer<void>();
    try {
      _box = await Hive.openBox(_boxName);
      _initCompleter!.complete();
    } catch (e) {
      _initCompleter!.completeError(e);
      _initCompleter = null;
      rethrow;
    }
  }

  Future<void> add(SyncAction action) async {
    await init();
    final queued = QueuedAction(action: action);
    await _box!.put(action.id, jsonEncode(queued.toJson()));
  }

  /// Get pending actions sorted by priority (lower priority number = processed first)
  /// Priority order: 1=Critical (answers), 2=High (XP/streak), 3=Medium, 4=Low
  Future<List<SyncAction>> getPending() async {
    await init();
    final actions = _box!.values
        .map((e) {
          final json = jsonDecode(e);
          // Handle both old and new format
          if (json.containsKey('action')) {
            return QueuedAction.fromJson(json);
          } else {
            return QueuedAction(action: SyncAction.fromJson(json));
          }
        })
        .where((q) => !q.action.isSynced && !q.isFailed)
        .map((q) => q.action)
        .toList();

    // Sort by priority (lower number = higher priority = processed first)
    actions.sort((a, b) => a.priority.compareTo(b.priority));

    SyncLogger.log('get_pending_sorted', data: {
      'count': actions.length,
      'priorities': actions.map((a) => '${a.type.name}:${a.priority}').toList(),
    });

    return actions;
  }

  /// Alias for getPending() - returns all pending sync actions
  Future<List<SyncAction>> getPendingActions() async {
    return getPending();
  }

  /// Get all failed actions for UI display
  Future<List<SyncAction>> getFailedActions() async {
    await init();
    return _box!.values
        .map((e) {
          final json = jsonDecode(e);
          if (json.containsKey('action')) {
            return QueuedAction.fromJson(json);
          } else {
            return QueuedAction(action: SyncAction.fromJson(json));
          }
        })
        .where((q) => q.isFailed)
        .map((q) => q.action)
        .toList();
  }

  /// Get detailed info about a failed action
  Future<QueuedAction?> getQueuedAction(String id) async {
    await init();
    final data = _box!.get(id);
    if (data == null) return null;

    final json = jsonDecode(data);
    if (json.containsKey('action')) {
      return QueuedAction.fromJson(json);
    } else {
      return QueuedAction(action: SyncAction.fromJson(json));
    }
  }

  /// Check if there are any failed actions
  bool get hasFailedActions {
    if (_box == null || !_box!.isOpen) return false;

    for (final value in _box!.values) {
      try {
        final json = jsonDecode(value);
        if (json.containsKey('isFailed') && json['isFailed'] == true) {
          return true;
        }
      } catch (e) {
        // Skip invalid entries
      }
    }
    return false;
  }

  /// Mark an action as failed with error details
  Future<void> markFailed(String id, String error, int attempts) async {
    await init();
    final data = _box!.get(id);
    if (data == null) return;

    final json = jsonDecode(data);
    QueuedAction queued;

    if (json.containsKey('action')) {
      queued = QueuedAction.fromJson(json);
    } else {
      queued = QueuedAction(action: SyncAction.fromJson(json));
    }

    final updated = queued.copyWith(
      attempts: attempts,
      lastError: error,
      lastAttemptTime: DateTime.now(),
      isFailed: true,
    );

    await _box!.put(id, jsonEncode(updated.toJson()));

    SyncLogger.log('action_marked_failed', data: {
      'id': id,
      'attempts': attempts,
      'error': error,
    });
  }

  /// Reset attempts for an action (for retry)
  Future<void> resetAttempts(String id) async {
    await init();
    final data = _box!.get(id);
    if (data == null) return;

    final json = jsonDecode(data);
    QueuedAction queued;

    if (json.containsKey('action')) {
      queued = QueuedAction.fromJson(json);
    } else {
      queued = QueuedAction(action: SyncAction.fromJson(json));
    }

    final updated = queued.copyWith(
      attempts: 0,
      lastError: null,
      isFailed: false,
    );

    await _box!.put(id, jsonEncode(updated.toJson()));

    SyncLogger.log('action_attempts_reset', data: {'id': id});
  }

  Future<void> markSynced(String id) async {
    await init();
    await _box!.delete(id);
    SyncLogger.log('action_synced', data: {'id': id});
  }

  Future<void> clear() async {
    await init();
    await _box!.clear();
    SyncLogger.log('queue_cleared');
  }

  /// Returns the count of pending actions in the queue synchronously.
  /// Returns 0 if the box is not initialized.
  int get length {
    if (_box == null || !_box!.isOpen) return 0;
    return _box!.length;
  }

  /// Get count of failed actions
  int get failedCount {
    if (_box == null || !_box!.isOpen) return 0;

    int count = 0;
    for (final value in _box!.values) {
      try {
        final json = jsonDecode(value);
        if (json.containsKey('isFailed') && json['isFailed'] == true) {
          count++;
        }
      } catch (e) {
        // Skip invalid entries
      }
    }
    return count;
  }

  Future<void> flushQueue(ApiClient apiClient) async {
    if (_isFlushing) return;
    _isFlushing = true;
    SyncLogger.log('flush_queue_start');

    try {
      final pending = await getPending();
      for (final action in pending) {
        try {
          await _processAction(apiClient, action);
          await markSynced(action.id);
          SyncLogger.log('flush_queue_action_success', data: {'action_id': action.id, 'type': action.type.name});
        } catch (e) {
          SyncLogger.log('flush_queue_action_failed', error: e.toString(), data: {'action_id': action.id});
          // Continue to next action
        }
      }
    } finally {
      _isFlushing = false;
      SyncLogger.log('flush_queue_end');
    }
  }

  Future<void> _processAction(ApiClient apiClient, SyncAction action) {
    switch (action.type) {
      case SyncActionType.submitAnswer:
        return apiClient.post(ApiConstants.submitAnswer, data: action.data);
      case SyncActionType.useHeart:
        return apiClient.post(ApiConstants.useHeart, data: action.data);
      case SyncActionType.extendStreak:
        return apiClient.post(ApiConstants.extendStreak, data: action.data);
      case SyncActionType.updateState:
        return apiClient.post(ApiConstants.syncState, data: action.data);
      default:
        return Future.value();
    }
  }
}

// Singleton provider for the ActionQueue
final actionQueueProvider = Provider<ActionQueue>((ref) {
  return ActionQueue();
});

final pendingActionsCountProvider = FutureProvider<int>((ref) async {
  final queue = ref.watch(actionQueueProvider);
  final actions = await queue.getPending();
  return actions.length;
});
