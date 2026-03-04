import 'dart:async';

import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:icfes_mobile/features/dungeon/presentation/providers/dungeon_provider.dart';
import 'package:icfes_mobile/features/dungeon/data/repositories/dungeon_repository.dart';
import 'package:icfes_mobile/features/dungeon/data/datasources/dungeon_remote_datasource.dart';
import 'package:icfes_mobile/features/dungeon/data/models/dungeon_models.dart';
import 'package:icfes_mobile/features/dungeon/data/services/dungeon_websocket_service.dart';
import 'package:icfes_mobile/features/dungeon/domain/entities/dungeon_gate.dart';

// ============================================================================
// Fake Repository
// ============================================================================

/// Fake implementation of DungeonRepository that returns preset responses.
/// Each method can be configured to throw or to return a stub value.
class FakeDungeonRepository implements DungeonRepository {
  // Configurable return values
  List<DungeonGate> gatesToReturn = [];
  DungeonRunResponse? runResponseToReturn;
  DungeonEncounterModel? encounterToReturn;
  EncounterResultModel? answerResultToReturn;
  DungeonCompletionModel? completionToReturn;
  List<DungeonRunHistoryModel> historyToReturn = [];
  String hintToReturn = 'Hint text';

  // Configurable exceptions to throw
  Exception? gatesException;
  Exception? enterGateException;
  Exception? currentRunException;
  Exception? encounterException;
  Exception? submitAnswerException;

  // Call-tracking
  int getAvailableGatesCalls = 0;
  int enterGateCalls = 0;
  String? lastEnteredGateId;
  int submitAnswerCalls = 0;

  @override
  Future<List<DungeonGate>> getAvailableGates({
    String? gateType,
    String? difficulty,
  }) async {
    getAvailableGatesCalls++;
    if (gatesException != null) throw gatesException!;
    return gatesToReturn;
  }

  @override
  Future<DungeonRunResponse> enterGate(String gateId) async {
    enterGateCalls++;
    lastEnteredGateId = gateId;
    if (enterGateException != null) throw enterGateException!;
    return runResponseToReturn!;
  }

  @override
  Future<DungeonRunResponse?> getCurrentRun() async {
    if (currentRunException != null) throw currentRunException!;
    return runResponseToReturn;
  }

  @override
  Future<DungeonEncounterModel> getEncounterQuestions(
      String encounterId) async {
    if (encounterException != null) throw encounterException!;
    return encounterToReturn!;
  }

  @override
  Future<EncounterResultModel> submitAnswer({
    required String encounterId,
    required String questionId,
    required String answerId,
    int? timeSpentSeconds,
  }) async {
    submitAnswerCalls++;
    if (submitAnswerException != null) throw submitAnswerException!;
    return answerResultToReturn!;
  }

  @override
  Future<EncounterResultModel> submitAnswers(
    String encounterId,
    List<AnswerSubmission> answers,
  ) async {
    return answerResultToReturn!;
  }

  @override
  Future<DungeonCompletionModel> completeRun({
    required String runId,
    bool abandon = false,
  }) async {
    return completionToReturn!;
  }

  @override
  Future<List<DungeonRunHistoryModel>> getHistory({int limit = 10}) async {
    return historyToReturn;
  }

  @override
  Future<void> useItem({required String runId, required String itemId}) async {}

  @override
  Future<String> requestHint({
    required String encounterId,
    required String questionId,
  }) async {
    return hintToReturn;
  }
}

// ============================================================================
// Fake WebSocket Service
// ============================================================================

/// Fake implementation of DungeonWebSocketService that exposes
/// StreamControllers so tests can push events and connection-state changes
/// directly without a real WebSocket connection.
class FakeDungeonWebSocketService extends DungeonWebSocketService {
  final _fakeEventController =
      StreamController<DungeonWsEvent>.broadcast();
  final _fakeConnectionController =
      StreamController<WsConnectionState>.broadcast();

  WsConnectionState _fakeState = WsConnectionState.disconnected;

  @override
  Stream<DungeonWsEvent> get events => _fakeEventController.stream;

  @override
  Stream<WsConnectionState> get connectionState =>
      _fakeConnectionController.stream;

  @override
  WsConnectionState get currentState => _fakeState;

  @override
  bool get isConnected => _fakeState == WsConnectionState.connected;

  /// Push a connection state into the stream (simulates WS lifecycle).
  void emitConnectionState(WsConnectionState state) {
    _fakeState = state;
    _fakeConnectionController.add(state);
  }

  /// Push an event into the stream (simulates incoming WS message).
  void emitEvent(DungeonWsEvent event) {
    _fakeEventController.add(event);
  }

  // Override network operations to be no-ops so tests never hit real sockets.
  @override
  Future<void> connect({required String authToken}) async {
    emitConnectionState(WsConnectionState.connected);
  }

  @override
  Future<void> disconnect() async {
    emitConnectionState(WsConnectionState.disconnected);
  }

  @override
  void joinDungeon(String runId) {}

  @override
  void leaveDungeon() {}

  @override
  void submitAnswer({
    required String encounterId,
    required String questionId,
    required String answerId,
    int? timeSpentSeconds,
  }) {}

  @override
  void useItem(String itemId) {}

  @override
  void requestHint({
    required String encounterId,
    required String questionId,
  }) {}

  @override
  void dispose() {
    _fakeEventController.close();
    _fakeConnectionController.close();
    // Do NOT call super.dispose() — the real implementation would try to close
    // the internal StreamControllers that were never created.
  }
}

// ============================================================================
// Helpers
// ============================================================================

/// Build a minimal [DungeonNotifier] backed by fakes and wrap it in a
/// [ProviderContainer] so that Riverpod lifecycle is handled correctly.
ProviderContainer _buildContainer({
  FakeDungeonRepository? repo,
  FakeDungeonWebSocketService? ws,
}) {
  final repository = repo ?? FakeDungeonRepository();
  final wsService = ws ?? FakeDungeonWebSocketService();

  // Wrap in a ProviderContainer that overrides the repository and WS service
  // so that dungeonNotifierProvider picks up the fakes automatically.
  final container = ProviderContainer(
    overrides: [
      dungeonRepositoryProvider.overrideWithValue(repository),
      dungeonWebSocketServiceProvider.overrideWithValue(wsService),
    ],
  );

  return container;
}

/// Convenience: read the notifier from a container.
DungeonNotifier _readNotifier(ProviderContainer c) =>
    c.read(dungeonNotifierProvider.notifier);

/// Convenience: read the current state from a container.
DungeonState _readState(ProviderContainer c) =>
    c.read(dungeonNotifierProvider);

/// Build a minimal [DungeonGate] for use in tests.
DungeonGate _makeGate({
  String id = 'gate-1',
  String name = 'Test Gate',
  String type = 'normal',
  String difficultyRank = 'D',
  bool isLocked = false,
  String theme = 'math',
}) {
  return DungeonGate(
    id: id,
    name: name,
    description: 'A test dungeon gate',
    type: type,
    difficultyRank: difficultyRank,
    recommendedLevel: 1,
    totalRooms: 5,
    timeLimitMinutes: 30,
    isLocked: isLocked,
    completionPercentage: 0.0,
    theme: theme,
  );
}

/// Build a minimal [DungeonRunResponse] for use in tests.
DungeonRunResponse _makeRunResponse({
  String runId = 'run-1',
  String gateId = 'gate-1',
  String gateName = 'Test Gate',
  DungeonEncounterModel? encounter,
}) {
  return DungeonRunResponse(
    runId: runId,
    gateId: gateId,
    gateName: gateName,
    nodes: [
      DungeonNodeModel(
        id: 'node-1',
        roomNumber: 1,
        type: 'monster',
        isCompleted: false,
        isCurrent: true,
        isLocked: false,
      ),
    ],
    totalRooms: 5,
    timeLimitSeconds: 1800,
    startedAt: DateTime.now(),
    playerStats: PlayerStatsModel(hp: 100, maxHp: 100),
    currentEncounter: encounter,
  );
}

/// Build a minimal [DungeonEncounterModel] carrying one question.
DungeonEncounterModel _makeEncounter({
  String encounterId = 'enc-1',
  String nodeId = 'node-1',
  int currentQuestionIndex = 0,
}) {
  return DungeonEncounterModel(
    encounterId: encounterId,
    nodeId: nodeId,
    type: 'monster',
    questions: [
      DungeonQuestionModel(
        id: 'q-1',
        text: 'What is 2 + 2?',
        options: [
          DungeonQuestionOption(id: 'a', text: '3'),
          DungeonQuestionOption(id: 'b', text: '4'),
          DungeonQuestionOption(id: 'c', text: '5'),
          DungeonQuestionOption(id: 'd', text: '6'),
        ],
      ),
    ],
    currentQuestionIndex: currentQuestionIndex,
    totalQuestions: 1,
  );
}

// ============================================================================
// Tests
// ============================================================================

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  // --------------------------------------------------------------------------
  // DungeonState — factory constructors
  // --------------------------------------------------------------------------
  group('DungeonState factory constructors', () {
    test('default constructor produces clean initial state', () {
      const state = DungeonState();

      expect(state.availableGates, isEmpty);
      expect(state.currentGate, isNull);
      expect(state.nodes, isEmpty);
      expect(state.currentRunId, isNull);
      expect(state.currentEncounterId, isNull);
      expect(state.currentEncounter, isNull);
      expect(state.playerStats, isNull);
      expect(state.isLoading, isFalse);
      expect(state.isSubmitting, isFalse);
      expect(state.error, isNull);
      expect(state.timeRemainingSeconds, equals(0));
      expect(state.comboCount, equals(0));
      expect(state.wsConnectionState, equals(WsConnectionState.disconnected));
    });

    test('DungeonState.loading() sets isLoading to true and clears error', () {
      final state = DungeonState.loading();

      expect(state.isLoading, isTrue);
      expect(state.error, isNull);
      // All other fields retain defaults
      expect(state.availableGates, isEmpty);
      expect(state.currentRunId, isNull);
    });

    test('DungeonState.error(msg) stores the message and is not loading', () {
      const message = 'Something went wrong';
      final state = DungeonState.error(message);

      expect(state.error, equals(message));
      expect(state.isLoading, isFalse);
      // Other fields are at their defaults
      expect(state.availableGates, isEmpty);
      expect(state.currentRunId, isNull);
    });

    test('DungeonState.error preserves default field values', () {
      final state = DungeonState.error('oops');

      expect(state.comboCount, equals(0));
      expect(state.timeRemainingSeconds, equals(0));
      expect(state.wsConnectionState, equals(WsConnectionState.disconnected));
    });
  });

  // --------------------------------------------------------------------------
  // DungeonState — computed getters
  // --------------------------------------------------------------------------
  group('DungeonState computed getters', () {
    group('isInDungeon', () {
      test('returns false when currentRunId is null', () {
        const state = DungeonState();
        expect(state.isInDungeon, isFalse);
      });

      test('returns true when currentRunId is set', () {
        const state = DungeonState(currentRunId: 'run-abc');
        expect(state.isInDungeon, isTrue);
      });
    });

    group('hasActiveEncounter', () {
      test('returns false when currentEncounter is null', () {
        const state = DungeonState();
        expect(state.hasActiveEncounter, isFalse);
      });

      test('returns true when currentEncounter is set', () {
        final encounter = _makeEncounter();
        final state = DungeonState(currentEncounter: encounter);
        expect(state.hasActiveEncounter, isTrue);
      });
    });

    group('currentQuestion', () {
      test('returns null when no encounter is active', () {
        const state = DungeonState();
        expect(state.currentQuestion, isNull);
      });

      test('returns the question at currentQuestionIndex 0', () {
        final encounter = _makeEncounter(currentQuestionIndex: 0);
        final state = DungeonState(currentEncounter: encounter);

        expect(state.currentQuestion, isNotNull);
        expect(state.currentQuestion!.id, equals('q-1'));
        expect(state.currentQuestion!.text, equals('What is 2 + 2?'));
      });

      test('returns null when currentQuestionIndex is out of bounds', () {
        final encounter = _makeEncounter(
          currentQuestionIndex: 99, // far beyond the single question
        );
        final state = DungeonState(currentEncounter: encounter);

        expect(state.currentQuestion, isNull);
      });

      test('returns null when encounter has no questions', () {
        final emptyEncounter = DungeonEncounterModel(
          encounterId: 'enc-empty',
          nodeId: 'node-1',
          type: 'monster',
          questions: [],
          currentQuestionIndex: 0,
          totalQuestions: 0,
        );
        final state = DungeonState(currentEncounter: emptyEncounter);

        expect(state.currentQuestion, isNull);
      });
    });
  });

  // --------------------------------------------------------------------------
  // DungeonGate entity
  // --------------------------------------------------------------------------
  group('DungeonGate entity', () {
    test('can be constructed with required fields', () {
      final gate = _makeGate();

      expect(gate.id, equals('gate-1'));
      expect(gate.name, equals('Test Gate'));
      expect(gate.type, equals('normal'));
      expect(gate.difficultyRank, equals('D'));
      expect(gate.recommendedLevel, equals(1));
      expect(gate.totalRooms, equals(5));
      expect(gate.timeLimitMinutes, equals(30));
    });

    test('isLocked defaults to false', () {
      const gate = DungeonGate(
        id: 'g',
        name: 'G',
        description: '',
        type: 'normal',
        difficultyRank: 'D',
        recommendedLevel: 1,
        totalRooms: 5,
        timeLimitMinutes: 30,
      );
      expect(gate.isLocked, isFalse);
    });

    test('completionPercentage defaults to 0', () {
      const gate = DungeonGate(
        id: 'g',
        name: 'G',
        description: '',
        type: 'normal',
        difficultyRank: 'D',
        recommendedLevel: 1,
        totalRooms: 5,
        timeLimitMinutes: 30,
      );
      expect(gate.completionPercentage, equals(0.0));
    });

    test('theme defaults to "math"', () {
      const gate = DungeonGate(
        id: 'g',
        name: 'G',
        description: '',
        type: 'normal',
        difficultyRank: 'D',
        recommendedLevel: 1,
        totalRooms: 5,
        timeLimitMinutes: 30,
        // theme deliberately omitted
      );
      expect(gate.theme, equals('math'));
    });

    test('can be constructed with explicit non-default theme', () {
      final gate = _makeGate(theme: 'science');
      expect(gate.theme, equals('science'));
    });

    test('accepts all supported theme values', () {
      for (final theme in ['math', 'reading', 'science', 'social', 'english']) {
        final gate = _makeGate(theme: theme);
        expect(gate.theme, equals(theme));
      }
    });

    test('isLocked can be set to true explicitly', () {
      final gate = _makeGate(isLocked: true);
      expect(gate.isLocked, isTrue);
    });

    test('supports value equality via Freezed', () {
      final a = _makeGate(id: 'x', theme: 'math');
      final b = _makeGate(id: 'x', theme: 'math');
      expect(a, equals(b));
    });

    test('instances with different fields are not equal', () {
      final a = _makeGate(id: 'x', theme: 'math');
      final b = _makeGate(id: 'y', theme: 'math');
      expect(a, isNot(equals(b)));
    });
  });

  // --------------------------------------------------------------------------
  // DungeonState.copyWith — clearError flag
  // --------------------------------------------------------------------------
  group('DungeonState.copyWith', () {
    test('clearError flag sets error to null', () {
      final withError = DungeonState.error('network failure');
      expect(withError.error, isNotNull);

      final cleared = withError.copyWith(clearError: true);
      expect(cleared.error, isNull);
    });

    test('setting error via copyWith overwrites previous error', () {
      final first = DungeonState.error('first');
      final second = first.copyWith(error: 'second');
      expect(second.error, equals('second'));
    });

    test('copyWith preserves unspecified fields', () {
      const original = DungeonState(
        currentRunId: 'run-99',
        comboCount: 5,
        timeRemainingSeconds: 120,
      );
      final copy = original.copyWith(comboCount: 7);

      expect(copy.currentRunId, equals('run-99'));
      expect(copy.comboCount, equals(7));
      expect(copy.timeRemainingSeconds, equals(120));
    });

    test('clearCurrentRunId removes run id', () {
      const state = DungeonState(currentRunId: 'run-1');
      final cleared = state.copyWith(clearCurrentRunId: true);
      expect(cleared.currentRunId, isNull);
    });

    test('clearCurrentEncounter removes encounter', () {
      final encounter = _makeEncounter();
      final state = DungeonState(currentEncounter: encounter);
      final cleared = state.copyWith(clearCurrentEncounter: true);
      expect(cleared.currentEncounter, isNull);
    });
  });

  // --------------------------------------------------------------------------
  // DungeonNotifier.clearError
  // --------------------------------------------------------------------------
  group('DungeonNotifier.clearError', () {
    late FakeDungeonRepository fakeRepo;
    late FakeDungeonWebSocketService fakeWs;
    late ProviderContainer container;

    setUp(() {
      fakeRepo = FakeDungeonRepository();
      fakeWs = FakeDungeonWebSocketService();
      container = _buildContainer(repo: fakeRepo, ws: fakeWs);
    });

    tearDown(() {
      container.dispose();
    });

    test('clears a pre-existing error via copyWith', () async {
      // Seed error state by making loadGates throw.
      fakeRepo.gatesException = DungeonApiException('connection refused');
      await _readNotifier(container).loadGates();

      var state = _readState(container);
      expect(state.error, equals('connection refused'));

      // Act
      _readNotifier(container).clearError();

      // Assert
      state = _readState(container);
      expect(state.error, isNull);
    });

    test('clearError is idempotent when there is no error', () {
      // Notifier starts with no error.
      var state = _readState(container);
      expect(state.error, isNull);

      // Calling clearError when no error is present should not throw and
      // state should remain consistent.
      _readNotifier(container).clearError();

      state = _readState(container);
      expect(state.error, isNull);
    });

    test('clearError does not affect other state fields', () async {
      // Put some meaningful values into state via loadGates success.
      fakeRepo.gatesToReturn = [_makeGate(id: 'g1'), _makeGate(id: 'g2')];
      await _readNotifier(container).loadGates();

      // Manually inject an error through the notifier's copyWith path.
      // The cleanest way without exposing internals is to trigger a second
      // loadGates that fails so we have gates + error together.
      // To achieve this, we override the gates list then set an exception.
      fakeRepo.gatesException = DungeonApiException('intermittent');
      await _readNotifier(container).loadGates();

      var state = _readState(container);
      // Gates from the first successful call are still in state.
      expect(state.availableGates, hasLength(2));
      expect(state.error, isNotNull);

      // Act
      _readNotifier(container).clearError();

      // Assert — error gone, gates preserved
      state = _readState(container);
      expect(state.error, isNull);
      expect(state.availableGates, hasLength(2));
    });
  });

  // --------------------------------------------------------------------------
  // DungeonNotifier.loadGates
  // --------------------------------------------------------------------------
  group('DungeonNotifier.loadGates', () {
    late FakeDungeonRepository fakeRepo;
    late FakeDungeonWebSocketService fakeWs;
    late ProviderContainer container;

    setUp(() {
      fakeRepo = FakeDungeonRepository();
      fakeWs = FakeDungeonWebSocketService();
      container = _buildContainer(repo: fakeRepo, ws: fakeWs);
    });

    tearDown(() {
      container.dispose();
    });

    test('populates availableGates on success', () async {
      fakeRepo.gatesToReturn = [
        _makeGate(id: 'g1', name: 'Gate Alpha'),
        _makeGate(id: 'g2', name: 'Gate Beta'),
      ];

      await _readNotifier(container).loadGates();

      final state = _readState(container);
      expect(state.availableGates, hasLength(2));
      expect(state.availableGates[0].id, equals('g1'));
      expect(state.availableGates[1].id, equals('g2'));
      expect(state.isLoading, isFalse);
      expect(state.error, isNull);
    });

    test('sets error on DungeonApiException', () async {
      fakeRepo.gatesException = DungeonApiException('server error');

      await _readNotifier(container).loadGates();

      final state = _readState(container);
      expect(state.error, equals('server error'));
      expect(state.isLoading, isFalse);
    });

    test('sets error message on generic exception', () async {
      fakeRepo.gatesException = Exception('timeout');

      await _readNotifier(container).loadGates();

      final state = _readState(container);
      expect(state.error, isNotNull);
      expect(state.error, contains('Failed to load dungeons'));
      expect(state.isLoading, isFalse);
    });

    test('clears previous error before fetching', () async {
      // First call fails
      fakeRepo.gatesException = DungeonApiException('first error');
      await _readNotifier(container).loadGates();
      expect(_readState(container).error, isNotNull);

      // Second call succeeds
      fakeRepo.gatesException = null;
      fakeRepo.gatesToReturn = [_makeGate()];
      await _readNotifier(container).loadGates();

      final state = _readState(container);
      expect(state.error, isNull);
      expect(state.availableGates, hasLength(1));
    });
  });

  // --------------------------------------------------------------------------
  // DungeonNotifier WebSocket connection-state propagation
  // --------------------------------------------------------------------------
  group('DungeonNotifier WebSocket connection-state propagation', () {
    late FakeDungeonWebSocketService fakeWs;
    late ProviderContainer container;

    setUp(() {
      fakeWs = FakeDungeonWebSocketService();
      container = _buildContainer(ws: fakeWs);
    });

    tearDown(() {
      container.dispose();
    });

    test('initial wsConnectionState is disconnected', () {
      final state = _readState(container);
      expect(state.wsConnectionState, equals(WsConnectionState.disconnected));
    });

    test('emitting connected state updates wsConnectionState', () async {
      // Force notifier creation (subscribes to streams) BEFORE emitting.
      _readNotifier(container);

      fakeWs.emitConnectionState(WsConnectionState.connected);
      await Future.delayed(const Duration(milliseconds: 10));

      final state = _readState(container);
      expect(state.wsConnectionState, equals(WsConnectionState.connected));
    });

    test('emitting reconnecting state is reflected', () async {
      _readNotifier(container);

      fakeWs.emitConnectionState(WsConnectionState.reconnecting);
      await Future.delayed(const Duration(milliseconds: 10));

      expect(
        _readState(container).wsConnectionState,
        equals(WsConnectionState.reconnecting),
      );
    });

    test('emitting failed state is reflected', () async {
      _readNotifier(container);

      fakeWs.emitConnectionState(WsConnectionState.failed);
      await Future.delayed(const Duration(milliseconds: 10));

      expect(
        _readState(container).wsConnectionState,
        equals(WsConnectionState.failed),
      );
    });
  });

  // --------------------------------------------------------------------------
  // DungeonNotifier WebSocket event handling
  // --------------------------------------------------------------------------
  group('DungeonNotifier WebSocket event handling', () {
    late FakeDungeonWebSocketService fakeWs;
    late ProviderContainer container;

    setUp(() {
      fakeWs = FakeDungeonWebSocketService();
      container = _buildContainer(ws: fakeWs);
    });

    tearDown(() {
      container.dispose();
    });

    test('comboAchieved event updates comboCount', () async {
      // Force notifier creation (subscribes to streams) BEFORE emitting.
      _readNotifier(container);

      fakeWs.emitEvent(DungeonWsEvent(
        type: DungeonWsEventType.comboAchieved,
        data: {'combo_count': 7},
      ));
      await Future.delayed(const Duration(milliseconds: 10));

      expect(_readState(container).comboCount, equals(7));
    });

    test('error event stores error message', () async {
      _readNotifier(container);

      fakeWs.emitEvent(DungeonWsEvent(
        type: DungeonWsEventType.error,
        data: {'message': 'WS server error'},
      ));
      await Future.delayed(const Duration(milliseconds: 10));

      expect(_readState(container).error, equals('WS server error'));
    });

    test('newEncounter event updates currentEncounter', () async {
      _readNotifier(container);

      final encounterData = {
        'encounter_id': 'enc-ws',
        'node_id': 'node-1',
        'type': 'monster',
        'questions': [],
        'current_question_index': 0,
        'total_questions': 0,
      };

      fakeWs.emitEvent(DungeonWsEvent(
        type: DungeonWsEventType.newEncounter,
        data: encounterData,
      ));
      await Future.delayed(const Duration(milliseconds: 10));

      final state = _readState(container);
      expect(state.currentEncounter, isNotNull);
      expect(state.currentEncounter!.encounterId, equals('enc-ws'));
      expect(state.currentEncounterId, equals('enc-ws'));
    });

    test('dungeonCompleted event clears currentEncounter', () async {
      _readNotifier(container);

      // First place an encounter into state via a newEncounter event.
      fakeWs.emitEvent(DungeonWsEvent(
        type: DungeonWsEventType.newEncounter,
        data: {
          'encounter_id': 'enc-temp',
          'node_id': 'node-1',
          'type': 'monster',
          'questions': [],
          'current_question_index': 0,
          'total_questions': 0,
        },
      ));
      await Future.delayed(const Duration(milliseconds: 10));
      expect(_readState(container).currentEncounter, isNotNull);

      // Now complete the dungeon.
      fakeWs.emitEvent(DungeonWsEvent(
        type: DungeonWsEventType.dungeonCompleted,
        data: {},
      ));
      await Future.delayed(const Duration(milliseconds: 10));

      final state = _readState(container);
      expect(state.currentEncounter, isNull);
      expect(state.currentEncounterId, isNull);
    });

    test('dungeonFailed event clears currentEncounter', () async {
      _readNotifier(container);

      fakeWs.emitEvent(DungeonWsEvent(
        type: DungeonWsEventType.newEncounter,
        data: {
          'encounter_id': 'enc-fail',
          'node_id': 'node-1',
          'type': 'monster',
          'questions': [],
          'current_question_index': 0,
          'total_questions': 0,
        },
      ));
      await Future.delayed(const Duration(milliseconds: 10));
      expect(_readState(container).currentEncounter, isNotNull);

      fakeWs.emitEvent(DungeonWsEvent(
        type: DungeonWsEventType.dungeonFailed,
        data: {},
      ));
      await Future.delayed(const Duration(milliseconds: 10));

      expect(_readState(container).currentEncounter, isNull);
    });
  });

  // --------------------------------------------------------------------------
  // DungeonNotifier.enterGate
  // --------------------------------------------------------------------------
  group('DungeonNotifier.enterGate', () {
    late FakeDungeonRepository fakeRepo;
    late FakeDungeonWebSocketService fakeWs;
    late ProviderContainer container;

    setUp(() {
      fakeRepo = FakeDungeonRepository();
      fakeWs = FakeDungeonWebSocketService();
      container = _buildContainer(repo: fakeRepo, ws: fakeWs);
    });

    tearDown(() {
      container.dispose();
    });

    test('returns true and sets currentRunId on success', () async {
      fakeRepo.runResponseToReturn = _makeRunResponse(runId: 'run-xyz');

      final result = await _readNotifier(container).enterGate('gate-1');

      expect(result, isTrue);
      final state = _readState(container);
      expect(state.currentRunId, equals('run-xyz'));
      expect(state.isLoading, isFalse);
      expect(state.error, isNull);
      expect(state.isInDungeon, isTrue);
    });

    test('returns false and sets error on DungeonLockedException', () async {
      fakeRepo.enterGateException = DungeonLockedException('gate locked');

      final result = await _readNotifier(container).enterGate('gate-1');

      expect(result, isFalse);
      final state = _readState(container);
      expect(state.error, equals('gate locked'));
      expect(state.isLoading, isFalse);
    });

    test('returns false and sets error on DungeonActiveRunException', () async {
      // To avoid checkCurrentRun calling getCurrentRun and crashing, we
      // return null (no existing run).
      fakeRepo.runResponseToReturn = null;
      fakeRepo.enterGateException =
          DungeonActiveRunException('active run exists');

      final result = await _readNotifier(container).enterGate('gate-1');

      expect(result, isFalse);
      final state = _readState(container);
      expect(state.error, equals('active run exists'));
    });

    test('returns false and sets error on generic exception', () async {
      fakeRepo.enterGateException = Exception('network timeout');

      final result = await _readNotifier(container).enterGate('gate-1');

      expect(result, isFalse);
      expect(_readState(container).error, contains('Failed to enter dungeon'));
    });

    test('sets nodes from run response', () async {
      fakeRepo.runResponseToReturn = _makeRunResponse();

      await _readNotifier(container).enterGate('gate-1');

      final state = _readState(container);
      expect(state.nodes, hasLength(1));
      expect(state.nodes.first.id, equals('node-1'));
    });

    test('sets timeRemainingSeconds from run response', () async {
      fakeRepo.runResponseToReturn = _makeRunResponse();
      // _makeRunResponse uses timeLimitSeconds: 1800

      await _readNotifier(container).enterGate('gate-1');

      expect(_readState(container).timeRemainingSeconds, equals(1800));
    });

    test('sets currentEncounter when run response includes one', () async {
      final encounter = _makeEncounter(encounterId: 'enc-first');
      fakeRepo.runResponseToReturn =
          _makeRunResponse(encounter: encounter);

      await _readNotifier(container).enterGate('gate-1');

      final state = _readState(container);
      expect(state.currentEncounter, isNotNull);
      expect(state.currentEncounter!.encounterId, equals('enc-first'));
      expect(state.hasActiveEncounter, isTrue);
    });
  });
}
