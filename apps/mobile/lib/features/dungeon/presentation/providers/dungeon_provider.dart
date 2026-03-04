import 'dart:async';

import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/network/api_client.dart';
import '../../data/datasources/dungeon_remote_datasource.dart';
import '../../data/models/dungeon_models.dart';
import '../../data/repositories/dungeon_repository.dart';
import '../../data/services/dungeon_websocket_service.dart';
import '../../domain/entities/dungeon_gate.dart';
import '../../domain/entities/dungeon_node.dart';

// ============================================================================
// State Classes
// ============================================================================

/// State for the dungeon feature
class DungeonState {
  final List<DungeonGate> availableGates;
  final DungeonGate? currentGate;
  final List<DungeonNode> nodes;
  final String? currentRunId;
  final String? currentEncounterId;
  final DungeonEncounterModel? currentEncounter;
  final PlayerStatsModel? playerStats;
  final bool isLoading;
  final bool isSubmitting;
  final String? error;
  final int timeRemainingSeconds;
  final int comboCount;
  final WsConnectionState wsConnectionState;

  const DungeonState({
    this.availableGates = const [],
    this.currentGate,
    this.nodes = const [],
    this.currentRunId,
    this.currentEncounterId,
    this.currentEncounter,
    this.playerStats,
    this.isLoading = false,
    this.isSubmitting = false,
    this.error,
    this.timeRemainingSeconds = 0,
    this.comboCount = 0,
    this.wsConnectionState = WsConnectionState.disconnected,
  });

  /// Initial state with loading
  factory DungeonState.loading() => const DungeonState(isLoading: true);

  /// State with error
  factory DungeonState.error(String message) => DungeonState(error: message);

  /// Whether currently in a dungeon run
  bool get isInDungeon => currentRunId != null;

  /// Whether an encounter is active
  bool get hasActiveEncounter => currentEncounter != null;

  /// Current question in the encounter (if any)
  DungeonQuestionModel? get currentQuestion {
    if (currentEncounter == null) return null;
    final index = currentEncounter!.currentQuestionIndex;
    if (index >= 0 && index < currentEncounter!.questions.length) {
      return currentEncounter!.questions[index];
    }
    return null;
  }

  /// Create a copy with updated fields
  DungeonState copyWith({
    List<DungeonGate>? availableGates,
    DungeonGate? currentGate,
    bool clearCurrentGate = false,
    List<DungeonNode>? nodes,
    String? currentRunId,
    bool clearCurrentRunId = false,
    String? currentEncounterId,
    bool clearCurrentEncounterId = false,
    DungeonEncounterModel? currentEncounter,
    bool clearCurrentEncounter = false,
    PlayerStatsModel? playerStats,
    bool clearPlayerStats = false,
    bool? isLoading,
    bool? isSubmitting,
    String? error,
    bool clearError = false,
    int? timeRemainingSeconds,
    int? comboCount,
    WsConnectionState? wsConnectionState,
  }) {
    return DungeonState(
      availableGates: availableGates ?? this.availableGates,
      currentGate: clearCurrentGate ? null : (currentGate ?? this.currentGate),
      nodes: nodes ?? this.nodes,
      currentRunId: clearCurrentRunId ? null : (currentRunId ?? this.currentRunId),
      currentEncounterId: clearCurrentEncounterId ? null : (currentEncounterId ?? this.currentEncounterId),
      currentEncounter: clearCurrentEncounter ? null : (currentEncounter ?? this.currentEncounter),
      playerStats: clearPlayerStats ? null : (playerStats ?? this.playerStats),
      isLoading: isLoading ?? this.isLoading,
      isSubmitting: isSubmitting ?? this.isSubmitting,
      error: clearError ? null : (error ?? this.error),
      timeRemainingSeconds: timeRemainingSeconds ?? this.timeRemainingSeconds,
      comboCount: comboCount ?? this.comboCount,
      wsConnectionState: wsConnectionState ?? this.wsConnectionState,
    );
  }
}

// ============================================================================
// Notifier
// ============================================================================

/// StateNotifier for managing dungeon state
class DungeonNotifier extends StateNotifier<DungeonState> {
  final DungeonRepository _repository;
  final DungeonWebSocketService _wsService;

  StreamSubscription<DungeonWsEvent>? _wsEventSubscription;
  StreamSubscription<WsConnectionState>? _wsConnectionSubscription;
  Timer? _timeTimer;

  DungeonNotifier({
    required DungeonRepository repository,
    required DungeonWebSocketService wsService,
  })  : _repository = repository,
        _wsService = wsService,
        super(const DungeonState()) {
    _initWebSocketListeners();
  }

  /// Initialize WebSocket event listeners
  void _initWebSocketListeners() {
    _wsConnectionSubscription = _wsService.connectionState.listen((connectionState) {
      state = state.copyWith(wsConnectionState: connectionState);
    });

    _wsEventSubscription = _wsService.events.listen(_handleWsEvent);
  }

  /// Handle WebSocket events
  void _handleWsEvent(DungeonWsEvent event) {
    switch (event.type) {
      case DungeonWsEventType.encounterResult:
        final result = event.encounterResult;
        if (result != null) {
          _handleEncounterResult(result);
        }
        break;

      case DungeonWsEventType.newEncounter:
        final encounter = event.newEncounter;
        if (encounter != null) {
          state = state.copyWith(
            currentEncounter: encounter,
            currentEncounterId: encounter.encounterId,
          );
        }
        break;

      case DungeonWsEventType.statsUpdated:
        final stats = event.playerStats;
        if (stats != null) {
          state = state.copyWith(playerStats: stats);
        }
        break;

      case DungeonWsEventType.comboAchieved:
        final combo = event.comboCount;
        if (combo != null) {
          state = state.copyWith(comboCount: combo);
        }
        break;

      case DungeonWsEventType.dungeonCompleted:
      case DungeonWsEventType.dungeonFailed:
        _stopTimeTimer();
        state = state.copyWith(
          clearCurrentEncounter: true,
          clearCurrentEncounterId: true,
        );
        break;

      case DungeonWsEventType.error:
        final errorMessage = event.errorMessage;
        if (errorMessage != null) {
          state = state.copyWith(error: errorMessage);
        }
        break;

      default:
        break;
    }
  }

  /// Handle encounter result from WebSocket or API
  void _handleEncounterResult(EncounterResultModel result) {
    // Update player stats
    state = state.copyWith(
      playerStats: PlayerStatsModel(
        hp: result.playerCurrentHp,
        maxHp: state.playerStats?.maxHp ?? 100,
        energy: state.playerStats?.energy ?? 100,
        maxEnergy: state.playerStats?.maxEnergy ?? 100,
        comboCount: result.currentCombo,
        xpEarned: (state.playerStats?.xpEarned ?? 0) + result.xpEarned,
        coinsEarned: (state.playerStats?.coinsEarned ?? 0) + result.coinsEarned,
      ),
      comboCount: result.currentCombo,
      isSubmitting: false,
    );

    // Update node status if encounter completed
    if (result.encounterCompleted) {
      final updatedNodes = state.nodes.map((node) {
        if (node.id == state.currentEncounter?.nodeId) {
          return DungeonNode(
            id: node.id,
            roomNumber: node.roomNumber,
            type: node.type,
            isCompleted: true,
            isCurrent: false,
            isLocked: false,
            stars: result.starsEarned,
          );
        }
        if (result.nextNode != null && node.id == result.nextNode!.nodeId) {
          return DungeonNode(
            id: node.id,
            roomNumber: node.roomNumber,
            type: node.type,
            isCompleted: false,
            isCurrent: true,
            isLocked: false,
            stars: 0,
          );
        }
        return node;
      }).toList();

      state = state.copyWith(
        nodes: updatedNodes,
        clearCurrentEncounter: true,
        clearCurrentEncounterId: true,
      );
    }
  }

  /// Connect to WebSocket with auth token
  Future<void> connectWebSocket(String authToken) async {
    await _wsService.connect(authToken: authToken);
  }

  /// Disconnect from WebSocket
  Future<void> disconnectWebSocket() async {
    await _wsService.disconnect();
  }

  /// Load available dungeon gates from backend
  Future<void> loadGates({String? gateType, String? difficulty}) async {
    state = state.copyWith(isLoading: true, clearError: true);

    try {
      final gates = await _repository.getAvailableGates(
        gateType: gateType,
        difficulty: difficulty,
      );
      state = state.copyWith(
        availableGates: gates,
        isLoading: false,
      );
    } on DungeonApiException catch (e) {
      state = state.copyWith(
        isLoading: false,
        error: e.message,
      );
    } catch (e) {
      state = state.copyWith(
        isLoading: false,
        error: 'Failed to load dungeons: $e',
      );
    }
  }

  /// Check for and restore an existing dungeon run
  Future<void> checkCurrentRun() async {
    try {
      final currentRun = await _repository.getCurrentRun();
      if (currentRun != null) {
        _setupRunState(currentRun);
        if (_wsService.isConnected) {
          _wsService.joinDungeon(currentRun.runId);
        }
      }
    } catch (e) {
      debugPrint('Error checking current run: $e');
    }
  }

  /// Enter a dungeon gate
  Future<bool> enterGate(String gateId) async {
    state = state.copyWith(isLoading: true, clearError: true);

    try {
      final runResponse = await _repository.enterGate(gateId);
      _setupRunState(runResponse);

      // Join WebSocket room for real-time updates
      if (_wsService.isConnected) {
        _wsService.joinDungeon(runResponse.runId);
      }

      state = state.copyWith(isLoading: false);
      return true;
    } on DungeonLockedException catch (e) {
      state = state.copyWith(
        isLoading: false,
        error: e.message,
      );
      return false;
    } on DungeonActiveRunException catch (e) {
      state = state.copyWith(
        isLoading: false,
        error: e.message,
      );
      // Try to restore existing run
      await checkCurrentRun();
      return false;
    } on DungeonApiException catch (e) {
      state = state.copyWith(
        isLoading: false,
        error: e.message,
      );
      return false;
    } catch (e) {
      state = state.copyWith(
        isLoading: false,
        error: 'Failed to enter dungeon: $e',
      );
      return false;
    }
  }

  /// Setup state from a dungeon run response
  void _setupRunState(DungeonRunResponse runResponse) {
    final currentGate = state.availableGates.firstWhere(
      (g) => g.id == runResponse.gateId,
      orElse: () => DungeonGate(
        id: runResponse.gateId,
        name: runResponse.gateName,
        description: '',
        type: 'normal',
        difficultyRank: 'D',
        recommendedLevel: 1,
        totalRooms: runResponse.totalRooms,
        timeLimitMinutes: runResponse.timeLimitSeconds ~/ 60,
        isLocked: false,
        completionPercentage: 0.0,
        theme: 'math',
      ),
    );

    state = state.copyWith(
      currentGate: currentGate,
      currentRunId: runResponse.runId,
      nodes: runResponse.nodes.map((n) => n.toEntity()).toList(),
      playerStats: runResponse.playerStats,
      currentEncounter: runResponse.currentEncounter,
      currentEncounterId: runResponse.currentEncounter?.encounterId,
      timeRemainingSeconds: runResponse.timeLimitSeconds,
      comboCount: 0,
    );

    _startTimeTimer();
  }

  /// Start encounter for a specific node
  Future<bool> startEncounter(String nodeId) async {
    // Find the node
    final node = state.nodes.firstWhere(
      (n) => n.id == nodeId,
      orElse: () => throw StateError('Node not found'),
    );

    if (node.isLocked || node.isCompleted) {
      state = state.copyWith(error: 'Cannot start this encounter');
      return false;
    }

    state = state.copyWith(isLoading: true, clearError: true);

    try {
      // In a real implementation, this would be a separate API call
      // For now, we assume entering a gate includes the first encounter
      // or we need to fetch encounter details separately

      // If we have a current encounter from the run response, use it
      if (state.currentEncounter != null && state.currentEncounter!.nodeId == nodeId) {
        state = state.copyWith(isLoading: false);
        return true;
      }

      // Otherwise fetch the encounter
      final encounter = await _repository.getEncounterQuestions(nodeId);
      state = state.copyWith(
        currentEncounter: encounter,
        currentEncounterId: encounter.encounterId,
        isLoading: false,
      );
      return true;
    } on DungeonApiException catch (e) {
      state = state.copyWith(
        isLoading: false,
        error: e.message,
      );
      return false;
    } catch (e) {
      state = state.copyWith(
        isLoading: false,
        error: 'Failed to start encounter: $e',
      );
      return false;
    }
  }

  /// Submit an answer for the current question
  Future<EncounterResultModel?> submitAnswer({
    required String answerId,
    int? timeSpentSeconds,
  }) async {
    if (state.currentEncounterId == null || state.currentQuestion == null) {
      state = state.copyWith(error: 'No active encounter');
      return null;
    }

    state = state.copyWith(isSubmitting: true, clearError: true);

    try {
      // Use WebSocket if connected for real-time feedback
      if (_wsService.isConnected) {
        _wsService.submitAnswer(
          encounterId: state.currentEncounterId!,
          questionId: state.currentQuestion!.id,
          answerId: answerId,
          timeSpentSeconds: timeSpentSeconds,
        );
        // Result will come via WebSocket event
        return null;
      }

      // Fall back to REST API
      final result = await _repository.submitAnswer(
        encounterId: state.currentEncounterId!,
        questionId: state.currentQuestion!.id,
        answerId: answerId,
        timeSpentSeconds: timeSpentSeconds,
      );

      _handleEncounterResult(result);
      return result;
    } on DungeonApiException catch (e) {
      state = state.copyWith(
        isSubmitting: false,
        error: e.message,
      );
      return null;
    } catch (e) {
      state = state.copyWith(
        isSubmitting: false,
        error: 'Failed to submit answer: $e',
      );
      return null;
    }
  }

  /// Submit multiple answers at once
  Future<EncounterResultModel?> submitAnswers(List<AnswerSubmission> answers) async {
    if (state.currentEncounterId == null) {
      state = state.copyWith(error: 'No active encounter');
      return null;
    }

    state = state.copyWith(isSubmitting: true, clearError: true);

    try {
      final result = await _repository.submitAnswers(
        state.currentEncounterId!,
        answers,
      );

      _handleEncounterResult(result);
      return result;
    } on DungeonApiException catch (e) {
      state = state.copyWith(
        isSubmitting: false,
        error: e.message,
      );
      return null;
    } catch (e) {
      state = state.copyWith(
        isSubmitting: false,
        error: 'Failed to submit answers: $e',
      );
      return null;
    }
  }

  /// Use an item during the run
  Future<void> useItem(String itemId) async {
    if (state.currentRunId == null) {
      state = state.copyWith(error: 'No active run');
      return;
    }

    try {
      if (_wsService.isConnected) {
        _wsService.useItem(itemId);
      } else {
        await _repository.useItem(
          runId: state.currentRunId!,
          itemId: itemId,
        );
      }
    } on DungeonApiException catch (e) {
      state = state.copyWith(error: e.message);
    } catch (e) {
      state = state.copyWith(error: 'Failed to use item: $e');
    }
  }

  /// Request a hint for the current question
  Future<String?> requestHint() async {
    if (state.currentEncounterId == null || state.currentQuestion == null) {
      state = state.copyWith(error: 'No active question');
      return null;
    }

    try {
      if (_wsService.isConnected) {
        _wsService.requestHint(
          encounterId: state.currentEncounterId!,
          questionId: state.currentQuestion!.id,
        );
        // Hint will come via WebSocket event
        return null;
      }

      return await _repository.requestHint(
        encounterId: state.currentEncounterId!,
        questionId: state.currentQuestion!.id,
      );
    } on DungeonApiException catch (e) {
      state = state.copyWith(error: e.message);
      return null;
    } catch (e) {
      state = state.copyWith(error: 'Failed to get hint: $e');
      return null;
    }
  }

  /// Complete the current dungeon run
  Future<DungeonCompletionModel?> completeDungeon() async {
    if (state.currentRunId == null) {
      state = state.copyWith(error: 'No active run');
      return null;
    }

    state = state.copyWith(isLoading: true, clearError: true);

    try {
      final result = await _repository.completeRun(runId: state.currentRunId!);
      _cleanupRunState();
      state = state.copyWith(isLoading: false);
      return result;
    } on DungeonApiException catch (e) {
      state = state.copyWith(
        isLoading: false,
        error: e.message,
      );
      return null;
    } catch (e) {
      state = state.copyWith(
        isLoading: false,
        error: 'Failed to complete dungeon: $e',
      );
      return null;
    }
  }

  /// Abandon the current dungeon run
  Future<DungeonCompletionModel?> abandonDungeon() async {
    if (state.currentRunId == null) {
      state = state.copyWith(error: 'No active run');
      return null;
    }

    state = state.copyWith(isLoading: true, clearError: true);

    try {
      final result = await _repository.completeRun(
        runId: state.currentRunId!,
        abandon: true,
      );
      _cleanupRunState();
      state = state.copyWith(isLoading: false);
      return result;
    } on DungeonApiException catch (e) {
      state = state.copyWith(
        isLoading: false,
        error: e.message,
      );
      return null;
    } catch (e) {
      state = state.copyWith(
        isLoading: false,
        error: 'Failed to abandon dungeon: $e',
      );
      return null;
    }
  }

  /// Cleanup run state when leaving dungeon
  void _cleanupRunState() {
    _stopTimeTimer();
    _wsService.leaveDungeon();
    state = state.copyWith(
      clearCurrentGate: true,
      clearCurrentRunId: true,
      clearCurrentEncounter: true,
      clearCurrentEncounterId: true,
      clearPlayerStats: true,
      nodes: [],
      comboCount: 0,
      timeRemainingSeconds: 0,
    );
  }

  /// Start the countdown timer
  void _startTimeTimer() {
    _stopTimeTimer();
    _timeTimer = Timer.periodic(const Duration(seconds: 1), (_) {
      if (state.timeRemainingSeconds > 0) {
        state = state.copyWith(
          timeRemainingSeconds: state.timeRemainingSeconds - 1,
        );
      } else {
        _timeTimer?.cancel();
        // Time's up - dungeon failed
      }
    });
  }

  /// Stop the countdown timer
  void _stopTimeTimer() {
    _timeTimer?.cancel();
    _timeTimer = null;
  }

  /// Get dungeon history
  Future<List<DungeonRunHistoryModel>> getHistory({int limit = 10}) async {
    try {
      return await _repository.getHistory(limit: limit);
    } catch (e) {
      debugPrint('Error fetching dungeon history: $e');
      return [];
    }
  }

  /// Clear error state
  void clearError() {
    state = state.copyWith(clearError: true);
  }

  @override
  void dispose() {
    _stopTimeTimer();
    _wsEventSubscription?.cancel();
    _wsConnectionSubscription?.cancel();
    super.dispose();
  }
}

// ============================================================================
// Providers
// ============================================================================

/// Provider for DungeonRemoteDataSource
final dungeonRemoteDataSourceProvider = Provider<DungeonRemoteDataSource>((ref) {
  final apiClient = ref.watch(apiClientProvider);
  return DungeonRemoteDataSource(apiClient);
});

/// Provider for DungeonRepository
final dungeonRepositoryProvider = Provider<DungeonRepository>((ref) {
  final remoteDataSource = ref.watch(dungeonRemoteDataSourceProvider);
  return DungeonRepositoryImpl(remoteDataSource);
});

/// Provider for DungeonWebSocketService
final dungeonWebSocketServiceProvider = Provider<DungeonWebSocketService>((ref) {
  final service = DungeonWebSocketService();
  ref.onDispose(() => service.dispose());
  return service;
});

/// Provider for DungeonNotifier
final dungeonNotifierProvider = StateNotifierProvider<DungeonNotifier, DungeonState>((ref) {
  final repository = ref.watch(dungeonRepositoryProvider);
  final wsService = ref.watch(dungeonWebSocketServiceProvider);
  return DungeonNotifier(
    repository: repository,
    wsService: wsService,
  );
});

// ============================================================================
// Convenience Providers (for backward compatibility)
// ============================================================================

/// Provider for current dungeon gate
final currentGateProvider = Provider<DungeonGate?>((ref) {
  return ref.watch(dungeonNotifierProvider).currentGate;
});

/// Provider for dungeon nodes
final dungeonNodesProvider = Provider<List<DungeonNode>>((ref) {
  return ref.watch(dungeonNotifierProvider).nodes;
});

/// Provider for available gates
final availableGatesProvider = Provider<List<DungeonGate>>((ref) {
  return ref.watch(dungeonNotifierProvider).availableGates;
});

/// Provider for current encounter
final currentEncounterProvider = Provider<DungeonEncounterModel?>((ref) {
  return ref.watch(dungeonNotifierProvider).currentEncounter;
});

/// Provider for player stats
final dungeonPlayerStatsProvider = Provider<PlayerStatsModel?>((ref) {
  return ref.watch(dungeonNotifierProvider).playerStats;
});

/// Provider for loading state
final dungeonLoadingProvider = Provider<bool>((ref) {
  return ref.watch(dungeonNotifierProvider).isLoading;
});

/// Provider for error state
final dungeonErrorProvider = Provider<String?>((ref) {
  return ref.watch(dungeonNotifierProvider).error;
});

/// Provider for time remaining
final dungeonTimeRemainingProvider = Provider<int>((ref) {
  return ref.watch(dungeonNotifierProvider).timeRemainingSeconds;
});

/// Provider for combo count
final dungeonComboProvider = Provider<int>((ref) {
  return ref.watch(dungeonNotifierProvider).comboCount;
});

/// Provider for WebSocket connection state
final dungeonWsConnectionProvider = Provider<WsConnectionState>((ref) {
  return ref.watch(dungeonNotifierProvider).wsConnectionState;
});
