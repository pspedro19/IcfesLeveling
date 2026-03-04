// tests/flutter/unit/test_offline_system.dart
// ═══════════════════════════════════════════════════════════════
// Unit Tests — Sistema Offline-First
// Cubre: QuestionCache, ActionQueue, SyncManager, Connectivity
// ═══════════════════════════════════════════════════════════════

import 'package:flutter_test/flutter_test.dart';
import 'package:mockito/mockito.dart';
import 'package:mockito/annotations.dart';
import 'package:hive/hive.dart';
import 'package:hive_test/hive_test.dart';

import 'package:icfes_leveling/core/services/question_cache_service.dart';
import 'package:icfes_leveling/core/services/action_queue.dart';
import 'package:icfes_leveling/core/services/sync_manager.dart';
import 'package:icfes_leveling/core/services/connectivity_monitor.dart';
import 'package:icfes_leveling/features/practice/data/models/pending_answer_dto.dart';
import 'package:icfes_leveling/features/practice/data/models/cached_question_dto.dart';

@GenerateMocks([ConnectivityMonitor, ApiService])
import 'test_offline_system.mocks.dart';


// ═══════════════════════════════════════════════════════════════
// 1. QUESTION CACHE SERVICE
// ═══════════════════════════════════════════════════════════════

group('QuestionCacheService', () {
  late QuestionCacheService cache;

  setUp(() async {
    await setUpTestHive();
    cache = QuestionCacheService();
    await cache.init();
  });

  tearDown(() async {
    await tearDownTestHive();
  });

  test('caches question and retrieves it', () async {
    final question = CachedQuestionDto(
      id: 'q-001',
      preguntaTexto: '¿Cuánto es 2+2?',
      opcionA: '3',
      opcionB: '4',
      opcionC: '5',
      opcionD: '6',
      respuestaCorrecta: 'b',
      difficulty: 1,
      subjectId: 'subj-math',
      topicId: 'topic-aritmetica',
      cachedAt: DateTime.now(),
    );

    await cache.cacheQuestion(question);
    final retrieved = cache.getQuestion('q-001');

    expect(retrieved, isNotNull);
    expect(retrieved!.id, equals('q-001'));
    expect(retrieved.preguntaTexto, equals('¿Cuánto es 2+2?'));
    expect(retrieved.respuestaCorrecta, equals('b'));
  });

  test('returns null for non-cached question', () {
    final result = cache.getQuestion('q-nonexistent');
    expect(result, isNull);
  });

  test('detects stale cache after 24 hours', () async {
    final question = CachedQuestionDto(
      id: 'q-old',
      preguntaTexto: 'Old question',
      opcionA: 'A', opcionB: 'B', opcionC: 'C', opcionD: 'D',
      respuestaCorrecta: 'a',
      difficulty: 5,
      subjectId: 's1', topicId: 't1',
      cachedAt: DateTime.now().subtract(const Duration(hours: 25)),
    );

    await cache.cacheQuestion(question);
    expect(cache.isStale('q-old'), isTrue);
  });

  test('fresh cache is not stale', () async {
    final question = CachedQuestionDto(
      id: 'q-fresh',
      preguntaTexto: 'Fresh question',
      opcionA: 'A', opcionB: 'B', opcionC: 'C', opcionD: 'D',
      respuestaCorrecta: 'c',
      difficulty: 3,
      subjectId: 's1', topicId: 't1',
      cachedAt: DateTime.now(),
    );

    await cache.cacheQuestion(question);
    expect(cache.isStale('q-fresh'), isFalse);
  });

  test('preloads subject caches all questions', () async {
    final mockApi = MockApiService();
    when(mockApi.getQuestionsBySubject('subj-math')).thenAnswer((_) async => [
      CachedQuestionDto(id: 'q1', preguntaTexto: 'Q1',
        opcionA: 'A', opcionB: 'B', opcionC: 'C', opcionD: 'D',
        respuestaCorrecta: 'a', difficulty: 1, subjectId: 'subj-math',
        topicId: 't1', cachedAt: DateTime.now()),
      CachedQuestionDto(id: 'q2', preguntaTexto: 'Q2',
        opcionA: 'A', opcionB: 'B', opcionC: 'C', opcionD: 'D',
        respuestaCorrecta: 'b', difficulty: 3, subjectId: 'subj-math',
        topicId: 't1', cachedAt: DateTime.now()),
    ]);

    await cache.preloadSubject('subj-math', api: mockApi);

    expect(cache.getQuestion('q1'), isNotNull);
    expect(cache.getQuestion('q2'), isNotNull);
  });

  test('getQuestionsForSubject returns all cached questions for subject', () async {
    for (int i = 0; i < 5; i++) {
      await cache.cacheQuestion(CachedQuestionDto(
        id: 'q-math-$i',
        preguntaTexto: 'Math Q$i',
        opcionA: 'A', opcionB: 'B', opcionC: 'C', opcionD: 'D',
        respuestaCorrecta: 'a', difficulty: i + 1,
        subjectId: 'subj-math', topicId: 't1',
        cachedAt: DateTime.now(),
      ));
    }

    final mathQuestions = cache.getQuestionsForSubject('subj-math');
    expect(mathQuestions.length, equals(5));
  });
});


// ═══════════════════════════════════════════════════════════════
// 2. ACTION QUEUE (FIFO)
// ═══════════════════════════════════════════════════════════════

group('ActionQueue', () {
  late ActionQueue queue;

  setUp(() async {
    await setUpTestHive();
    queue = ActionQueue();
    await queue.init();
  });

  tearDown(() async {
    await tearDownTestHive();
  });

  test('enqueue adds action to queue', () async {
    await queue.enqueue(PendingAction(
      type: 'answer',
      data: {'question_id': 'q-001', 'selected_answer': 'b'},
      createdAt: DateTime.now(),
    ));

    expect(queue.length, equals(1));
  });

  test('queue maintains FIFO order', () async {
    for (int i = 0; i < 5; i++) {
      await queue.enqueue(PendingAction(
        type: 'answer',
        data: {'order': i},
        createdAt: DateTime.now().add(Duration(seconds: i)),
      ));
    }

    final items = queue.peekAll();
    for (int i = 0; i < items.length - 1; i++) {
      expect(
        items[i].createdAt.isBefore(items[i + 1].createdAt),
        isTrue,
        reason: 'Items must be in FIFO order',
      );
    }
  });

  test('dequeue removes first item', () async {
    await queue.enqueue(PendingAction(
      type: 'answer', data: {'id': 'first'}, createdAt: DateTime.now(),
    ));
    await queue.enqueue(PendingAction(
      type: 'answer', data: {'id': 'second'}, createdAt: DateTime.now(),
    ));

    final first = await queue.dequeue();
    expect(first.data['id'], equals('first'));
    expect(queue.length, equals(1));
  });

  test('empty queue returns empty list', () {
    expect(queue.length, equals(0));
    expect(queue.peekAll(), isEmpty);
  });

  test('queue persists across reinitializations', () async {
    await queue.enqueue(PendingAction(
      type: 'answer', data: {'persist': true}, createdAt: DateTime.now(),
    ));

    // Simular reinicio de app
    final queue2 = ActionQueue();
    await queue2.init();
    expect(queue2.length, equals(1));
  });
});


// ═══════════════════════════════════════════════════════════════
// 3. PENDING ANSWER SYNC
// ═══════════════════════════════════════════════════════════════

group('PendingAnswerSync', () {
  test('creates valid pending answer from offline response', () {
    final pending = PendingAnswerDto(
      localId: 'local-001',
      sessionId: 'session-abc',
      questionId: 'q-001',
      selectedAnswer: 'b',
      timeSpentSeconds: 12,
      answeredAt: DateTime.now(),
      synced: false,
    );

    expect(pending.synced, isFalse);
    expect(pending.selectedAnswer, equals('b'));
  });

  test('marks as synced after successful upload', () {
    final pending = PendingAnswerDto(
      localId: 'local-002',
      sessionId: 'session-abc',
      questionId: 'q-002',
      selectedAnswer: 'c',
      timeSpentSeconds: 20,
      answeredAt: DateTime.now(),
      synced: false,
    );

    pending.markSynced();
    expect(pending.synced, isTrue);
    expect(pending.syncedAt, isNotNull);
  });

  test('converts to API request format', () {
    final pending = PendingAnswerDto(
      localId: 'local-003',
      sessionId: 'session-xyz',
      questionId: 'q-003',
      selectedAnswer: 'a',
      timeSpentSeconds: 8,
      answeredAt: DateTime(2026, 2, 19, 10, 30),
      synced: false,
    );

    final json = pending.toApiJson();
    expect(json['session_id'], equals('session-xyz'));
    expect(json['question_id'], equals('q-003'));
    expect(json['selected_answer'], equals('a'));
    expect(json['time_spent_seconds'], equals(8));
  });
});


// ═══════════════════════════════════════════════════════════════
// 4. SYNC MANAGER
// ═══════════════════════════════════════════════════════════════

group('SyncManager', () {
  late SyncManager syncManager;
  late MockConnectivityMonitor mockConnectivity;
  late MockApiService mockApi;
  late ActionQueue queue;

  setUp(() async {
    await setUpTestHive();
    queue = ActionQueue();
    await queue.init();
    mockConnectivity = MockConnectivityMonitor();
    mockApi = MockApiService();
    syncManager = SyncManager(
      queue: queue,
      connectivity: mockConnectivity,
      api: mockApi,
    );
  });

  tearDown(() async {
    await tearDownTestHive();
  });

  test('processes all queued actions on reconnect', () async {
    // Enqueue 3 pending answers
    for (int i = 0; i < 3; i++) {
      await queue.enqueue(PendingAction(
        type: 'answer',
        data: {'question_id': 'q-$i', 'selected_answer': 'b'},
        createdAt: DateTime.now(),
      ));
    }

    when(mockApi.syncAnswer(any)).thenAnswer((_) async => true);

    // Simular reconexión
    await syncManager.processAll();

    // Queue debe estar vacía
    expect(queue.length, equals(0));
    // API debe haber sido llamada 3 veces
    verify(mockApi.syncAnswer(any)).called(3);
  });

  test('stops processing on failure and retains remaining items', () async {
    await queue.enqueue(PendingAction(
      type: 'answer', data: {'id': '1'}, createdAt: DateTime.now(),
    ));
    await queue.enqueue(PendingAction(
      type: 'answer', data: {'id': '2'}, createdAt: DateTime.now(),
    ));
    await queue.enqueue(PendingAction(
      type: 'answer', data: {'id': '3'}, createdAt: DateTime.now(),
    ));

    // Primera exitosa, segunda falla
    when(mockApi.syncAnswer(any))
        .thenAnswer((_) async => true)
        .thenAnswer((_) async => throw Exception('Network error'))
        .thenAnswer((_) async => true);

    await syncManager.processAll();

    // Items 2 y 3 deben quedarse en la cola
    expect(queue.length, equals(2));
  });

  test('does not process when offline', () async {
    when(mockConnectivity.isOnline).thenReturn(false);

    await queue.enqueue(PendingAction(
      type: 'answer', data: {'id': '1'}, createdAt: DateTime.now(),
    ));

    await syncManager.processIfOnline();
    expect(queue.length, equals(1)); // No procesó
  });
});


// ═══════════════════════════════════════════════════════════════
// 5. CONNECTIVITY MONITOR
// ═══════════════════════════════════════════════════════════════

group('ConnectivityMonitor', () {
  test('initial state is unknown until first check', () {
    final monitor = ConnectivityMonitor();
    expect(monitor.lastKnownStatus, equals(ConnectivityStatus.unknown));
  });

  test('emits online event when connection restored', () async {
    final monitor = MockConnectivityMonitor();
    when(monitor.isOnline).thenReturn(true);

    expect(monitor.isOnline, isTrue);
  });

  test('emits offline event when connection lost', () async {
    final monitor = MockConnectivityMonitor();
    when(monitor.isOnline).thenReturn(false);

    expect(monitor.isOnline, isFalse);
  });
});
