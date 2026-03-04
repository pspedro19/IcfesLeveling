import 'dart:async';

import 'package:flutter_test/flutter_test.dart';
import 'package:icfes_mobile/core/sync/sync_manager.dart';
import 'package:icfes_mobile/core/sync/action_queue.dart';
import 'package:icfes_mobile/core/sync/action_syncer.dart';
import 'package:icfes_mobile/core/sync/sync_action.dart';
import 'package:icfes_mobile/core/sync/connectivity_monitor.dart';

// ---------------------------------------------------------------------------
// Fake ActionQueue
// ---------------------------------------------------------------------------

/// In-memory ActionQueue that does NOT touch Hive.
/// Tracks which method calls were made so tests can assert on them.
class FakeActionQueue implements ActionQueue {
  final List<SyncAction> _pending;
  final List<SyncAction> _failed;

  /// Ids of actions that have been passed to [markSynced].
  final List<String> syncedIds = [];

  /// Calls recorded as (id, error, attempts).
  final List<({String id, String error, int attempts})> failedCalls = [];

  /// Ids of actions that have been passed to [resetAttempts].
  final List<String> resetIds = [];

  // --- configurable properties ------------------------------------------------

  @override
  int length;

  @override
  bool hasFailedActions;

  FakeActionQueue({
    List<SyncAction>? pending,
    List<SyncAction>? failed,
    this.length = 0,
    this.hasFailedActions = false,
  })  : _pending = pending ?? [],
        _failed = failed ?? [];

  @override
  Future<List<SyncAction>> getPending() async => List.unmodifiable(_pending);

  @override
  Future<List<SyncAction>> getPendingActions() async => getPending();

  @override
  Future<List<SyncAction>> getFailedActions() async =>
      List.unmodifiable(_failed);

  @override
  Future<void> markSynced(String id) async {
    syncedIds.add(id);
    _pending.removeWhere((a) => a.id == id);
  }

  @override
  Future<void> markFailed(String id, String error, int attempts) async {
    failedCalls.add((id: id, error: error, attempts: attempts));
  }

  @override
  Future<void> resetAttempts(String id) async {
    resetIds.add(id);
  }

  // --- methods SyncManager does not call in tested paths ----------------------

  @override
  Future<void> init() async {}

  @override
  Future<void> add(SyncAction action) async {}

  @override
  Future<void> clear() async {}

  @override
  int get failedCount => _failed.length;

  @override
  Future<QueuedAction?> getQueuedAction(String id) async => null;

  @override
  Future<void> flushQueue(dynamic apiClient) async {}

  // Intentionally leave the Hive-specific internals undefined; SyncManager
  // does not access them through this fake.
  @override
  dynamic noSuchMethod(Invocation invocation) => super.noSuchMethod(invocation);
}

// ---------------------------------------------------------------------------
// Fake ActionSyncer
// ---------------------------------------------------------------------------

/// Controls whether [syncWithResponse] succeeds or throws.
///
/// [failTimes] – how many times the call should throw before succeeding.
///              Set to a value >= [SyncManager.maxRetries] to exhaust all
///              retries permanently.
class FakeActionSyncer implements ActionSyncer {
  int failTimes;
  int callCount = 0;
  dynamic successResponse;

  FakeActionSyncer({this.failTimes = 0, this.successResponse});

  @override
  Future<dynamic> syncWithResponse(SyncAction action) async {
    callCount++;
    if (callCount <= failTimes) {
      throw Exception('simulated network error (call $callCount)');
    }
    return successResponse;
  }

  @override
  Future<bool> sync(SyncAction action) async {
    final resp = await syncWithResponse(action);
    return resp != null;
  }

  @override
  dynamic noSuchMethod(Invocation invocation) => super.noSuchMethod(invocation);
}

// ---------------------------------------------------------------------------
// Fake ConnectivityMonitor
// ---------------------------------------------------------------------------

class FakeConnectivityMonitor implements ConnectivityMonitor {
  bool _isOnline;
  final StreamController<bool> _controller =
      StreamController<bool>.broadcast();

  FakeConnectivityMonitor({bool isOnline = true}) : _isOnline = isOnline;

  @override
  Stream<bool> get onConnectivityChanged => _controller.stream;

  @override
  Future<bool> get isOnline async => _isOnline;

  /// Emit a connectivity event so [SyncManager.init] can react to it.
  void emitConnectivity(bool online) {
    _isOnline = online;
    _controller.add(online);
  }

  void dispose() => _controller.close();

  @override
  dynamic noSuchMethod(Invocation invocation) => super.noSuchMethod(invocation);
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/// Creates a basic [SyncAction] for use in tests.
SyncAction makeAction({
  String? id,
  SyncActionType type = SyncActionType.submitAnswer,
  Map<String, dynamic>? data,
}) {
  return SyncAction(
    id: id ?? 'test-action-${DateTime.now().microsecondsSinceEpoch}',
    type: type,
    data: data ?? {'question_id': 'q1', 'answer': 'A'},
  );
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

void main() {
  // -------------------------------------------------------------------------
  // 1. Initial state
  // -------------------------------------------------------------------------
  group('SyncManager – initial state', () {
    test('isSyncing is false on construction', () {
      final queue = FakeActionQueue(length: 0);
      final syncer = FakeActionSyncer();
      final monitor = FakeConnectivityMonitor();

      final manager = SyncManager(queue, syncer, monitor);

      expect(manager.isSyncing, isFalse);
      expect(manager.isProcessing, isFalse); // alias

      manager.dispose();
      monitor.dispose();
    });

    test('pendingCount delegates to queue.length', () {
      final queue = FakeActionQueue(length: 7);
      final syncer = FakeActionSyncer();
      final monitor = FakeConnectivityMonitor();

      final manager = SyncManager(queue, syncer, monitor);

      expect(manager.pendingCount, 7);

      manager.dispose();
      monitor.dispose();
    });

    test('hasFailedActions delegates to queue.hasFailedActions', () {
      final queue = FakeActionQueue(hasFailedActions: true);
      final syncer = FakeActionSyncer();
      final monitor = FakeConnectivityMonitor();

      final manager = SyncManager(queue, syncer, monitor);

      expect(manager.hasFailedActions, isTrue);

      manager.dispose();
      monitor.dispose();
    });

    test('hasFailedActions is false when queue reports no failures', () {
      final queue = FakeActionQueue(hasFailedActions: false);
      final syncer = FakeActionSyncer();
      final monitor = FakeConnectivityMonitor();

      final manager = SyncManager(queue, syncer, monitor);

      expect(manager.hasFailedActions, isFalse);

      manager.dispose();
      monitor.dispose();
    });
  });

  // -------------------------------------------------------------------------
  // 2. processWithRetry
  // -------------------------------------------------------------------------
  group('SyncManager – processWithRetry', () {
    test('returns success=true and attempts=1 when syncer succeeds first try',
        () async {
      final action = makeAction(id: 'a1');
      final queue = FakeActionQueue();
      final syncer = FakeActionSyncer(failTimes: 0, successResponse: {'ok': true});
      final monitor = FakeConnectivityMonitor();

      final manager = SyncManager(queue, syncer, monitor);
      final result = await manager.processWithRetry(action);

      expect(result.success, isTrue);
      expect(result.attempts, 1);
      expect(result.lastError, isNull);
      expect(result.serverResponse, {'ok': true});
      // markFailed must NOT have been called
      expect(queue.failedCalls, isEmpty);

      manager.dispose();
      monitor.dispose();
    });

    test('retries on transient failure and succeeds on second attempt',
        () async {
      final action = makeAction(id: 'a2');
      final queue = FakeActionQueue();
      // Fail once, then succeed
      final syncer = FakeActionSyncer(failTimes: 1);
      final monitor = FakeConnectivityMonitor();

      final manager = SyncManager(queue, syncer, monitor);

      // Override the delay to 0 ms so tests run quickly.
      // processWithRetry uses Future.delayed internally; we rely on fake async.
      final result = await manager.processWithRetry(action);

      expect(result.success, isTrue);
      expect(result.attempts, 2);
      expect(syncer.callCount, 2);
      expect(queue.failedCalls, isEmpty);

      manager.dispose();
      monitor.dispose();
    });

    test('retries on two transient failures and succeeds on third attempt',
        () async {
      final action = makeAction(id: 'a3');
      final queue = FakeActionQueue();
      final syncer = FakeActionSyncer(failTimes: 2);
      final monitor = FakeConnectivityMonitor();

      final manager = SyncManager(queue, syncer, monitor);
      final result = await manager.processWithRetry(action);

      expect(result.success, isTrue);
      expect(result.attempts, 3);
      expect(syncer.callCount, 3);
      expect(queue.failedCalls, isEmpty);

      manager.dispose();
      monitor.dispose();
    });

    test(
        'returns success=false after maxRetries (3) and records failure in queue',
        () async {
      final action = makeAction(id: 'a4');
      final queue = FakeActionQueue();
      // Always fails
      final syncer =
          FakeActionSyncer(failTimes: SyncManager.maxRetries + 99);
      final monitor = FakeConnectivityMonitor();

      final manager = SyncManager(queue, syncer, monitor);
      final result = await manager.processWithRetry(action);

      expect(result.success, isFalse);
      expect(result.attempts, SyncManager.maxRetries);
      expect(result.lastError, isNotNull);
      expect(result.lastError, contains('simulated network error'));

      // queue.markFailed must have been called exactly once
      expect(queue.failedCalls.length, 1);
      expect(queue.failedCalls.first.id, 'a4');
      expect(queue.failedCalls.first.attempts, SyncManager.maxRetries);
      expect(queue.failedCalls.first.error, contains('simulated network error'));

      manager.dispose();
      monitor.dispose();
    });

    test('syncer is called exactly maxRetries times when all attempts fail',
        () async {
      final action = makeAction(id: 'a5');
      final queue = FakeActionQueue();
      final syncer = FakeActionSyncer(failTimes: 999);
      final monitor = FakeConnectivityMonitor();

      final manager = SyncManager(queue, syncer, monitor);
      await manager.processWithRetry(action);

      expect(syncer.callCount, SyncManager.maxRetries);

      manager.dispose();
      monitor.dispose();
    });

    test('returns serverResponse from syncer on success', () async {
      final action = makeAction(id: 'a6');
      final queue = FakeActionQueue();
      final expected = {'status': 'ok', 'xp_awarded': 100};
      final syncer = FakeActionSyncer(successResponse: expected);
      final monitor = FakeConnectivityMonitor();

      final manager = SyncManager(queue, syncer, monitor);
      final result = await manager.processWithRetry(action);

      expect(result.serverResponse, expected);

      manager.dispose();
      monitor.dispose();
    });
  });

  // -------------------------------------------------------------------------
  // 3. forceSync
  // -------------------------------------------------------------------------
  group('SyncManager – forceSync', () {
    test('starts sync and marks actions synced when device is online', () async {
      final action = makeAction(id: 'fs1');
      final queue = FakeActionQueue(pending: [action]);
      final syncer = FakeActionSyncer(failTimes: 0);
      final monitor = FakeConnectivityMonitor(isOnline: true);

      final manager = SyncManager(queue, syncer, monitor);
      await manager.forceSync();

      expect(queue.syncedIds, contains('fs1'));
      expect(syncer.callCount, 1);

      manager.dispose();
      monitor.dispose();
    });

    test('does NOT sync when device is offline', () async {
      final action = makeAction(id: 'fs2');
      final queue = FakeActionQueue(pending: [action]);
      final syncer = FakeActionSyncer();
      final monitor = FakeConnectivityMonitor(isOnline: false);

      final manager = SyncManager(queue, syncer, monitor);
      await manager.forceSync();

      expect(queue.syncedIds, isEmpty);
      expect(syncer.callCount, 0);

      manager.dispose();
      monitor.dispose();
    });

    test('syncs multiple pending actions in order when online', () async {
      final a1 = makeAction(id: 'fs3-a');
      final a2 = makeAction(id: 'fs3-b');
      final queue = FakeActionQueue(pending: [a1, a2]);
      final syncer = FakeActionSyncer();
      final monitor = FakeConnectivityMonitor(isOnline: true);

      final manager = SyncManager(queue, syncer, monitor);
      await manager.forceSync();

      expect(queue.syncedIds, containsAll(['fs3-a', 'fs3-b']));
      expect(syncer.callCount, 2);

      manager.dispose();
      monitor.dispose();
    });

    test('isSyncing returns to false after forceSync completes', () async {
      final queue = FakeActionQueue(pending: [makeAction()]);
      final syncer = FakeActionSyncer();
      final monitor = FakeConnectivityMonitor(isOnline: true);

      final manager = SyncManager(queue, syncer, monitor);

      expect(manager.isSyncing, isFalse);
      final future = manager.forceSync();
      // isSyncing may be true during the operation; after awaiting it must be false.
      await future;
      expect(manager.isSyncing, isFalse);

      manager.dispose();
      monitor.dispose();
    });

    test('forceSync does not sync if already syncing', () async {
      // Two concurrent forceSyncs: the second should be a no-op.
      final a1 = makeAction(id: 'fs4-a');
      final queue = FakeActionQueue(pending: [a1]);
      final syncer = FakeActionSyncer();
      final monitor = FakeConnectivityMonitor(isOnline: true);

      final manager = SyncManager(queue, syncer, monitor);

      // Launch both without awaiting so they overlap.
      final first = manager.forceSync();
      final second = manager.forceSync(); // should return immediately

      await Future.wait([first, second]);

      // The action should only be synced once.
      expect(queue.syncedIds.where((id) => id == 'fs4-a').length, 1);

      manager.dispose();
      monitor.dispose();
    });

    test('failed actions are recorded in queue when sync fails', () async {
      final action = makeAction(id: 'fs5');
      final queue = FakeActionQueue(pending: [action]);
      final syncer = FakeActionSyncer(failTimes: 999); // always fails
      final monitor = FakeConnectivityMonitor(isOnline: true);

      final manager = SyncManager(queue, syncer, monitor);
      await manager.forceSync();

      expect(queue.failedCalls.length, 1);
      expect(queue.failedCalls.first.id, 'fs5');
      // It was NOT marked synced
      expect(queue.syncedIds, isEmpty);

      manager.dispose();
      monitor.dispose();
    });
  });

  // -------------------------------------------------------------------------
  // 4. State change notifications (notifyListeners)
  // -------------------------------------------------------------------------
  group('SyncManager – state change notifications', () {
    test('notifyListeners is called when sync begins and ends', () async {
      final action = makeAction(id: 'nl1');
      final queue = FakeActionQueue(pending: [action]);
      final syncer = FakeActionSyncer();
      final monitor = FakeConnectivityMonitor(isOnline: true);

      final manager = SyncManager(queue, syncer, monitor);

      final notificationStates = <bool>[];
      manager.addListener(() {
        notificationStates.add(manager.isSyncing);
      });

      await manager.forceSync();

      // Expect at least two notifications: one when sync starts (true)
      // and one when sync ends (false).
      expect(notificationStates.length, greaterThanOrEqualTo(2));
      expect(notificationStates.first, isTrue,
          reason: 'First notification should set isSyncing=true');
      expect(notificationStates.last, isFalse,
          reason: 'Last notification should set isSyncing=false');

      manager.dispose();
      monitor.dispose();
    });

    test('listeners are NOT fired when forceSync is skipped offline', () async {
      final queue = FakeActionQueue(pending: [makeAction()]);
      final syncer = FakeActionSyncer();
      final monitor = FakeConnectivityMonitor(isOnline: false);

      final manager = SyncManager(queue, syncer, monitor);

      int notifyCount = 0;
      manager.addListener(() => notifyCount++);

      await manager.forceSync();

      expect(notifyCount, 0,
          reason: 'No notifications should fire when offline and sync is skipped');

      manager.dispose();
      monitor.dispose();
    });

    test('connectivity event triggers sync and notifies listeners', () async {
      final action = makeAction(id: 'nl3');
      final queue = FakeActionQueue(pending: [action]);
      final syncer = FakeActionSyncer();
      final monitor = FakeConnectivityMonitor(isOnline: false);

      final manager = SyncManager(queue, syncer, monitor);
      manager.init(); // subscribe to connectivity stream

      final notificationStates = <bool>[];
      manager.addListener(() {
        notificationStates.add(manager.isSyncing);
      });

      // Simulate the device coming online
      monitor.emitConnectivity(true);

      // Wait for the async sync to complete
      await Future.delayed(Duration.zero);
      // Give the sync loop time to finish processing the pending action
      await Future.delayed(const Duration(milliseconds: 50));

      expect(notificationStates, isNotEmpty,
          reason: 'Connectivity event should trigger sync and notify listeners');
      expect(notificationStates.last, isFalse,
          reason: 'isSyncing must be false after sync completes');
      expect(queue.syncedIds, contains('nl3'));

      manager.dispose();
      monitor.dispose();
    });

    test('listener added and removed does not receive further notifications',
        () async {
      final queue = FakeActionQueue(pending: [makeAction()]);
      final syncer = FakeActionSyncer();
      final monitor = FakeConnectivityMonitor(isOnline: true);

      final manager = SyncManager(queue, syncer, monitor);

      int countWhileAttached = 0;
      void listener() => countWhileAttached++;

      manager.addListener(listener);
      await manager.forceSync();
      final countAfterFirstSync = countWhileAttached;

      // Remove listener and sync again
      manager.removeListener(listener);
      await manager.forceSync();

      expect(countAfterFirstSync, greaterThan(0),
          reason: 'Listener should have been called during first sync');
      expect(countWhileAttached, equals(countAfterFirstSync),
          reason: 'Listener must NOT be called after removal');

      manager.dispose();
      monitor.dispose();
    });
  });
}
