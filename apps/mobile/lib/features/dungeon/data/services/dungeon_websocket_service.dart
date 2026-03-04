import 'dart:async';
import 'dart:convert';
import 'dart:math';

import 'package:flutter/foundation.dart';
import 'package:web_socket_channel/web_socket_channel.dart';

import '../../../../core/config/websocket_constants.dart';
import '../models/dungeon_models.dart';

/// WebSocket event types received from server
enum DungeonWsEventType {
  dungeonStarted,
  battleUpdate,
  encounterResult,
  newEncounter,
  dungeonCompleted,
  dungeonFailed,
  statsUpdated,
  comboAchieved,
  bossAppeared,
  achievementUnlocked,
  itemUsed,
  hintProvided,
  authenticated,
  error,
  pong,
}

/// WebSocket event from dungeon server
class DungeonWsEvent {
  final DungeonWsEventType type;
  final Map<String, dynamic> data;
  final DateTime timestamp;

  DungeonWsEvent({
    required this.type,
    required this.data,
    DateTime? timestamp,
  }) : timestamp = timestamp ?? DateTime.now();

  factory DungeonWsEvent.fromJson(Map<String, dynamic> json) {
    final typeStr = json['type'] as String? ?? '';
    final type = _parseEventType(typeStr);
    return DungeonWsEvent(
      type: type,
      data: json['data'] as Map<String, dynamic>? ?? {},
      timestamp: json['timestamp'] != null
          ? DateTime.tryParse(json['timestamp'])
          : null,
    );
  }

  static DungeonWsEventType _parseEventType(String type) {
    switch (type) {
      case WsIncomingMessageType.dungeonStarted:
        return DungeonWsEventType.dungeonStarted;
      case WsIncomingMessageType.battleUpdate:
        return DungeonWsEventType.battleUpdate;
      case WsIncomingMessageType.encounterResult:
        return DungeonWsEventType.encounterResult;
      case WsIncomingMessageType.newEncounter:
        return DungeonWsEventType.newEncounter;
      case WsIncomingMessageType.dungeonCompleted:
        return DungeonWsEventType.dungeonCompleted;
      case WsIncomingMessageType.dungeonFailed:
        return DungeonWsEventType.dungeonFailed;
      case WsIncomingMessageType.statsUpdated:
        return DungeonWsEventType.statsUpdated;
      case WsIncomingMessageType.comboAchieved:
        return DungeonWsEventType.comboAchieved;
      case WsIncomingMessageType.bossAppeared:
        return DungeonWsEventType.bossAppeared;
      case WsIncomingMessageType.achievementUnlocked:
        return DungeonWsEventType.achievementUnlocked;
      case WsIncomingMessageType.itemUsed:
        return DungeonWsEventType.itemUsed;
      case WsIncomingMessageType.hintProvided:
        return DungeonWsEventType.hintProvided;
      case WsIncomingMessageType.authenticated:
        return DungeonWsEventType.authenticated;
      case WsIncomingMessageType.pong:
        return DungeonWsEventType.pong;
      case WsIncomingMessageType.error:
      default:
        return DungeonWsEventType.error;
    }
  }
}

/// Connection state for WebSocket
enum WsConnectionState {
  disconnected,
  connecting,
  connected,
  reconnecting,
  failed,
}

/// WebSocket service for real-time dungeon game updates
class DungeonWebSocketService {
  WebSocketChannel? _channel;
  StreamSubscription? _subscription;
  Timer? _pingTimer;
  Timer? _reconnectTimer;

  final _eventController = StreamController<DungeonWsEvent>.broadcast();
  final _connectionStateController = StreamController<WsConnectionState>.broadcast();

  WsConnectionState _connectionState = WsConnectionState.disconnected;
  int _reconnectAttempts = 0;
  String? _authToken;
  String? _currentRunId;

  /// Stream of dungeon events from server
  Stream<DungeonWsEvent> get events => _eventController.stream;

  /// Stream of connection state changes
  Stream<WsConnectionState> get connectionState => _connectionStateController.stream;

  /// Current connection state
  WsConnectionState get currentState => _connectionState;

  /// Whether currently connected
  bool get isConnected => _connectionState == WsConnectionState.connected;

  /// Connect to WebSocket server
  Future<void> connect({required String authToken}) async {
    if (_connectionState == WsConnectionState.connected ||
        _connectionState == WsConnectionState.connecting) {
      return;
    }

    _authToken = authToken;
    _setConnectionState(WsConnectionState.connecting);

    try {
      final uri = Uri.parse(WebSocketConfig.serverUrl);
      _channel = WebSocketChannel.connect(uri);

      _subscription = _channel!.stream.listen(
        _onMessage,
        onError: _onError,
        onDone: _onDone,
      );

      // Authenticate after connection
      _authenticate(authToken);
      _setConnectionState(WsConnectionState.connected);
      _reconnectAttempts = 0;
      _startPingTimer();
    } catch (e) {
      debugPrint('WebSocket connection error: $e');
      _setConnectionState(WsConnectionState.failed);
      _scheduleReconnect();
    }
  }

  /// Disconnect from WebSocket server
  Future<void> disconnect() async {
    _stopPingTimer();
    _reconnectTimer?.cancel();
    _subscription?.cancel();
    await _channel?.sink.close(WsCloseCode.normalClosure);
    _channel = null;
    _setConnectionState(WsConnectionState.disconnected);
    _currentRunId = null;
  }

  /// Join a dungeon run
  void joinDungeon(String runId) {
    _currentRunId = runId;
    _send({
      'type': WsOutgoingMessageType.joinDungeon,
      'data': {'run_id': runId},
    });
  }

  /// Leave current dungeon
  void leaveDungeon() {
    if (_currentRunId != null) {
      _send({
        'type': WsOutgoingMessageType.leaveDungeon,
        'data': {'run_id': _currentRunId},
      });
      _currentRunId = null;
    }
  }

  /// Submit answer via WebSocket for real-time feedback
  void submitAnswer({
    required String encounterId,
    required String questionId,
    required String answerId,
    int? timeSpentSeconds,
  }) {
    _send({
      'type': WsOutgoingMessageType.submitAnswer,
      'data': {
        'run_id': _currentRunId,
        'encounter_id': encounterId,
        'question_id': questionId,
        'answer_id': answerId,
        if (timeSpentSeconds != null) 'time_spent_seconds': timeSpentSeconds,
      },
    });
  }

  /// Request current dungeon state
  void getDungeonState() {
    if (_currentRunId != null) {
      _send({
        'type': WsOutgoingMessageType.getDungeonState,
        'data': {'run_id': _currentRunId},
      });
    }
  }

  /// Use an item during dungeon
  void useItem(String itemId) {
    if (_currentRunId != null) {
      _send({
        'type': WsOutgoingMessageType.useItem,
        'data': {
          'run_id': _currentRunId,
          'item_id': itemId,
        },
      });
    }
  }

  /// Request hint for current question
  void requestHint({
    required String encounterId,
    required String questionId,
  }) {
    _send({
      'type': WsOutgoingMessageType.requestHint,
      'data': {
        'run_id': _currentRunId,
        'encounter_id': encounterId,
        'question_id': questionId,
      },
    });
  }

  /// Send ping to keep connection alive
  void _ping() {
    _send({'type': WsOutgoingMessageType.ping});
  }

  /// Authenticate the connection
  void _authenticate(String token) {
    _send({
      'type': WsOutgoingMessageType.authenticate,
      'data': {'token': token},
    });
  }

  /// Send a message to the server
  void _send(Map<String, dynamic> message) {
    if (_channel != null && _connectionState == WsConnectionState.connected) {
      try {
        _channel!.sink.add(jsonEncode(message));
      } catch (e) {
        debugPrint('WebSocket send error: $e');
      }
    }
  }

  /// Handle incoming message
  void _onMessage(dynamic message) {
    try {
      final data = jsonDecode(message as String) as Map<String, dynamic>;
      final event = DungeonWsEvent.fromJson(data);

      // Handle pong internally
      if (event.type == DungeonWsEventType.pong) {
        return;
      }

      _eventController.add(event);
    } catch (e) {
      debugPrint('WebSocket message parse error: $e');
    }
  }

  /// Handle WebSocket error
  void _onError(dynamic error) {
    debugPrint('WebSocket error: $error');
    _eventController.add(DungeonWsEvent(
      type: DungeonWsEventType.error,
      data: {'message': error.toString()},
    ));
    _scheduleReconnect();
  }

  /// Handle WebSocket close
  void _onDone() {
    debugPrint('WebSocket connection closed');
    _stopPingTimer();
    if (_connectionState != WsConnectionState.disconnected) {
      _setConnectionState(WsConnectionState.disconnected);
      _scheduleReconnect();
    }
  }

  /// Update connection state
  void _setConnectionState(WsConnectionState state) {
    _connectionState = state;
    _connectionStateController.add(state);
  }

  /// Start ping timer
  void _startPingTimer() {
    _stopPingTimer();
    _pingTimer = Timer.periodic(
      const Duration(milliseconds: WsTimeoutConfig.pingIntervalMs),
      (_) => _ping(),
    );
  }

  /// Stop ping timer
  void _stopPingTimer() {
    _pingTimer?.cancel();
    _pingTimer = null;
  }

  /// Schedule reconnection with exponential backoff
  void _scheduleReconnect() {
    if (_reconnectAttempts >= WsReconnectionConfig.maxReconnectAttempts) {
      _setConnectionState(WsConnectionState.failed);
      return;
    }

    _setConnectionState(WsConnectionState.reconnecting);
    _reconnectTimer?.cancel();

    // Calculate delay with exponential backoff and jitter
    int delay = WsReconnectionConfig.initialDelayMs;
    if (WsReconnectionConfig.useExponentialBackoff) {
      delay = (delay * pow(WsReconnectionConfig.backoffMultiplier, _reconnectAttempts)).toInt();
      delay = min(delay, WsReconnectionConfig.maxDelayMs);
    }

    // Add jitter
    final jitter = (delay * WsReconnectionConfig.jitterFactor * (Random().nextDouble() - 0.5)).toInt();
    delay += jitter;

    _reconnectTimer = Timer(Duration(milliseconds: delay), () {
      _reconnectAttempts++;
      if (_authToken != null) {
        connect(authToken: _authToken!);
      }
    });
  }

  /// Dispose of resources
  void dispose() {
    disconnect();
    _eventController.close();
    _connectionStateController.close();
  }
}

/// Typed event helpers for common dungeon events
extension DungeonWsEventExtensions on DungeonWsEvent {
  /// Get encounter result from event data
  EncounterResultModel? get encounterResult {
    if (type != DungeonWsEventType.encounterResult) return null;
    try {
      return EncounterResultModel.fromJson(data);
    } catch (_) {
      return null;
    }
  }

  /// Get new encounter from event data
  DungeonEncounterModel? get newEncounter {
    if (type != DungeonWsEventType.newEncounter) return null;
    try {
      return DungeonEncounterModel.fromJson(data);
    } catch (_) {
      return null;
    }
  }

  /// Get player stats from event data
  PlayerStatsModel? get playerStats {
    if (type != DungeonWsEventType.statsUpdated) return null;
    try {
      return PlayerStatsModel.fromJson(data);
    } catch (_) {
      return null;
    }
  }

  /// Get completion result from event data
  DungeonCompletionModel? get completionResult {
    if (type != DungeonWsEventType.dungeonCompleted &&
        type != DungeonWsEventType.dungeonFailed) return null;
    try {
      return DungeonCompletionModel.fromJson(data);
    } catch (_) {
      return null;
    }
  }

  /// Get combo count from event data
  int? get comboCount {
    if (type != DungeonWsEventType.comboAchieved) return null;
    return data['combo_count'] as int?;
  }

  /// Get hint text from event data
  String? get hint {
    if (type != DungeonWsEventType.hintProvided) return null;
    return data['hint'] as String?;
  }

  /// Get error message from event data
  String? get errorMessage {
    if (type != DungeonWsEventType.error) return null;
    return data['message'] as String?;
  }
}
