import 'dart:async';
import 'dart:convert';
import 'dart:math';

import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:web_socket_channel/web_socket_channel.dart';
import 'package:web_socket_channel/status.dart' as ws_status;

import '../config/websocket_constants.dart';

/// Connection state for the WebSocket
enum WebSocketConnectionState {
  /// Not connected to the server
  disconnected,

  /// Attempting to connect
  connecting,

  /// Connected and ready
  connected,

  /// Connection lost, attempting to reconnect
  reconnecting,

  /// Authentication in progress
  authenticating,

  /// Authenticated and fully ready
  authenticated,

  /// Permanently failed (max retries exceeded)
  failed,
}

/// WebSocket error details
class WebSocketError {
  final String code;
  final String message;
  final dynamic data;
  final DateTime timestamp;

  WebSocketError({
    required this.code,
    required this.message,
    this.data,
    DateTime? timestamp,
  }) : timestamp = timestamp ?? DateTime.now();

  @override
  String toString() => 'WebSocketError($code): $message';
}

/// Game WebSocket Service for Conquest/Dungeon game server communication.
///
/// Provides real-time bidirectional communication with the game server for:
/// - Dungeon/conquest sessions
/// - Battle encounters and answers
/// - Real-time state updates
/// - Keep-alive ping/pong
///
/// Features:
/// - Automatic reconnection with exponential backoff
/// - Message queuing when disconnected
/// - Authentication support
/// - Connection state management
/// - Error handling and reporting
class GameWebSocketService {
  WebSocketChannel? _channel;
  StreamSubscription? _subscription;
  Timer? _pingTimer;
  Timer? _pongTimer;
  Timer? _reconnectTimer;

  final _messageController = StreamController<Map<String, dynamic>>.broadcast();
  final _connectionStateController =
      StreamController<WebSocketConnectionState>.broadcast();
  final _errorController = StreamController<WebSocketError>.broadcast();

  /// Queue for messages sent while disconnected
  final List<Map<String, dynamic>> _pendingMessages = [];

  /// Current connection state
  WebSocketConnectionState _connectionState =
      WebSocketConnectionState.disconnected;

  /// Number of reconnection attempts
  int _reconnectAttempts = 0;

  /// Current reconnection delay
  int _currentReconnectDelay = WsReconnectionConfig.initialDelayMs;

  /// Auth token for authentication
  String? _authToken;

  /// Current server URL
  String? _currentUrl;

  /// Whether auto-reconnect is enabled
  bool _autoReconnect = true;

  /// Last successful connection time
  DateTime? _lastConnectedAt;

  /// Stream of incoming messages from the server
  Stream<Map<String, dynamic>> get messages => _messageController.stream;

  /// Stream of connection state changes
  Stream<WebSocketConnectionState> get connectionStateStream =>
      _connectionStateController.stream;

  /// Stream of WebSocket errors
  Stream<WebSocketError> get errors => _errorController.stream;

  /// Whether currently connected to the server
  bool get isConnected =>
      _connectionState == WebSocketConnectionState.connected ||
      _connectionState == WebSocketConnectionState.authenticated;

  /// Whether currently authenticated
  bool get isAuthenticated =>
      _connectionState == WebSocketConnectionState.authenticated;

  /// Current connection state
  WebSocketConnectionState get connectionState => _connectionState;

  /// Number of pending messages in queue
  int get pendingMessageCount => _pendingMessages.length;

  /// Last successful connection time
  DateTime? get lastConnectedAt => _lastConnectedAt;

  /// Connect to the WebSocket server.
  ///
  /// [url] - Optional WebSocket URL. Defaults to configured server URL.
  /// [authToken] - Optional authentication token for secure connections.
  /// [autoReconnect] - Whether to automatically reconnect on disconnect.
  Future<void> connect({
    String? url,
    String? authToken,
    bool autoReconnect = true,
  }) async {
    // Prevent duplicate connections
    if (_connectionState == WebSocketConnectionState.connecting ||
        _connectionState == WebSocketConnectionState.reconnecting) {
      debugPrint('[WebSocket] Connection already in progress');
      return;
    }

    _currentUrl = url ?? WebSocketConfig.serverUrl;
    _authToken = authToken;
    _autoReconnect = autoReconnect;

    await _establishConnection();
  }

  /// Internal method to establish WebSocket connection
  Future<void> _establishConnection() async {
    _updateConnectionState(WebSocketConnectionState.connecting);

    try {
      final uri = Uri.parse(_currentUrl!);
      debugPrint('[WebSocket] Connecting to: $_currentUrl');

      // Create WebSocket channel
      _channel = WebSocketChannel.connect(
        uri,
        protocols: ['icfes-game-v1'],
      );

      // Wait for connection with timeout
      await _channel!.ready.timeout(
        Duration(milliseconds: WsTimeoutConfig.connectionTimeoutMs),
        onTimeout: () {
          throw TimeoutException(
            'Connection timeout after ${WsTimeoutConfig.connectionTimeoutMs}ms',
          );
        },
      );

      _updateConnectionState(WebSocketConnectionState.connected);
      _lastConnectedAt = DateTime.now();
      _reconnectAttempts = 0;
      _currentReconnectDelay = WsReconnectionConfig.initialDelayMs;

      debugPrint('[WebSocket] Connected successfully');

      // Start listening to messages
      _subscription = _channel!.stream.listen(
        _handleMessage,
        onError: _handleError,
        onDone: _handleDisconnect,
        cancelOnError: false,
      );

      // Start ping timer
      _startPingTimer();

      // Authenticate if token provided
      if (_authToken != null) {
        await _authenticate();
      }

      // Send any pending messages
      _flushPendingMessages();
    } on TimeoutException catch (e) {
      debugPrint('[WebSocket] Connection timeout: $e');
      _handleConnectionFailure('timeout', e.message ?? 'Connection timeout');
    } on WebSocketChannelException catch (e) {
      debugPrint('[WebSocket] Connection failed: $e');
      _handleConnectionFailure('connection_failed', e.message ?? 'Unknown error');
    } catch (e) {
      debugPrint('[WebSocket] Unexpected error: $e');
      _handleConnectionFailure('unknown', e.toString());
    }
  }

  /// Handle connection failure and potentially retry
  void _handleConnectionFailure(String code, String message) {
    _emitError(code, message);
    _cleanup();

    if (_autoReconnect &&
        _reconnectAttempts < WsReconnectionConfig.maxReconnectAttempts) {
      _scheduleReconnect();
    } else {
      _updateConnectionState(WebSocketConnectionState.failed);
    }
  }

  /// Schedule a reconnection attempt
  void _scheduleReconnect() {
    _updateConnectionState(WebSocketConnectionState.reconnecting);
    _reconnectAttempts++;

    // Calculate delay with exponential backoff and jitter
    int delay = _currentReconnectDelay;
    if (WsReconnectionConfig.useExponentialBackoff) {
      delay = (_currentReconnectDelay * WsReconnectionConfig.backoffMultiplier)
          .round();
      delay = min(delay, WsReconnectionConfig.maxDelayMs);
      _currentReconnectDelay = delay;
    }

    // Add jitter
    final jitter =
        (delay * WsReconnectionConfig.jitterFactor * Random().nextDouble())
            .round();
    delay += jitter;

    debugPrint(
        '[WebSocket] Reconnecting in ${delay}ms (attempt $_reconnectAttempts)');

    _reconnectTimer?.cancel();
    _reconnectTimer = Timer(Duration(milliseconds: delay), () {
      _establishConnection();
    });
  }

  /// Authenticate the connection
  Future<void> _authenticate() async {
    _updateConnectionState(WebSocketConnectionState.authenticating);

    send({
      'type': WsOutgoingMessageType.authenticate,
      'token': _authToken,
    });

    // Wait for authentication response with timeout
    try {
      await messages
          .firstWhere(
            (msg) =>
                msg['type'] == WsIncomingMessageType.authenticated ||
                msg['type'] == WsIncomingMessageType.error,
          )
          .timeout(Duration(seconds: 10));
    } catch (e) {
      debugPrint('[WebSocket] Authentication timeout');
      _emitError('auth_timeout', 'Authentication timeout');
    }
  }

  /// Disconnect from the WebSocket server.
  ///
  /// [code] - Optional close code. Defaults to normal closure.
  /// [reason] - Optional close reason.
  void disconnect({int? code, String? reason}) {
    debugPrint('[WebSocket] Disconnecting...');
    _autoReconnect = false;
    _cleanup();
    _channel?.sink.close(code ?? ws_status.normalClosure, reason);
    _channel = null;
    _updateConnectionState(WebSocketConnectionState.disconnected);
  }

  /// Clean up resources
  void _cleanup() {
    _subscription?.cancel();
    _subscription = null;
    _pingTimer?.cancel();
    _pingTimer = null;
    _pongTimer?.cancel();
    _pongTimer = null;
    _reconnectTimer?.cancel();
    _reconnectTimer = null;
  }

  /// Send a raw message to the server
  void send(Map<String, dynamic> message) {
    if (!isConnected) {
      debugPrint('[WebSocket] Not connected, queueing message: ${message['type']}');
      _pendingMessages.add(message);
      return;
    }

    try {
      final jsonMessage = jsonEncode(message);
      _channel?.sink.add(jsonMessage);
      debugPrint('[WebSocket] Sent: ${message['type']}');
    } catch (e) {
      debugPrint('[WebSocket] Send error: $e');
      _emitError('send_failed', 'Failed to send message: $e');
      _pendingMessages.add(message);
    }
  }

  /// Flush pending messages after reconnection
  void _flushPendingMessages() {
    if (_pendingMessages.isEmpty) return;

    debugPrint('[WebSocket] Flushing ${_pendingMessages.length} pending messages');

    final messages = List<Map<String, dynamic>>.from(_pendingMessages);
    _pendingMessages.clear();

    for (final message in messages) {
      send(message);
    }
  }

  // ============================================
  // Game Actions
  // ============================================

  /// Join a dungeon/conquest gate.
  ///
  /// [gateId] - The ID of the gate/dungeon to join.
  /// [userId] - The user's ID.
  /// [difficulty] - Optional difficulty level.
  void joinDungeon(
    String gateId,
    String userId, {
    String? difficulty,
    Map<String, dynamic>? metadata,
  }) {
    send({
      'type': WsOutgoingMessageType.joinDungeon,
      'gate_id': gateId,
      'user_id': userId,
      if (difficulty != null) 'difficulty': difficulty,
      if (metadata != null) 'metadata': metadata,
      'timestamp': DateTime.now().toIso8601String(),
    });
  }

  /// Submit an answer for the current battle encounter.
  ///
  /// [encounterId] - The ID of the current encounter.
  /// [userId] - The user's ID.
  /// [answers] - List of selected answer IDs/values.
  /// [timeSpentMs] - Time spent on this answer in milliseconds.
  void submitAnswer(
    String encounterId,
    String userId,
    List<String> answers, {
    int? timeSpentMs,
    Map<String, dynamic>? metadata,
  }) {
    send({
      'type': WsOutgoingMessageType.submitAnswer,
      'encounter_id': encounterId,
      'user_id': userId,
      'answers': answers,
      if (timeSpentMs != null) 'time_spent_ms': timeSpentMs,
      if (metadata != null) 'metadata': metadata,
      'timestamp': DateTime.now().toIso8601String(),
    });
  }

  /// Send a ping to keep the connection alive.
  void ping() {
    send({
      'type': WsOutgoingMessageType.ping,
      'timestamp': DateTime.now().toIso8601String(),
    });
  }

  /// Request current dungeon state.
  ///
  /// [dungeonId] - The ID of the dungeon session.
  void getDungeonState(String dungeonId) {
    send({
      'type': WsOutgoingMessageType.getDungeonState,
      'dungeon_id': dungeonId,
      'timestamp': DateTime.now().toIso8601String(),
    });
  }

  /// Leave the current dungeon.
  ///
  /// [dungeonId] - The ID of the dungeon session.
  /// [userId] - The user's ID.
  void leaveDungeon(String dungeonId, String userId) {
    send({
      'type': WsOutgoingMessageType.leaveDungeon,
      'dungeon_id': dungeonId,
      'user_id': userId,
      'timestamp': DateTime.now().toIso8601String(),
    });
  }

  /// Use an item during battle.
  ///
  /// [itemId] - The ID of the item to use.
  /// [userId] - The user's ID.
  /// [encounterId] - Optional encounter ID if using during encounter.
  void useItem(
    String itemId,
    String userId, {
    String? encounterId,
  }) {
    send({
      'type': WsOutgoingMessageType.useItem,
      'item_id': itemId,
      'user_id': userId,
      if (encounterId != null) 'encounter_id': encounterId,
      'timestamp': DateTime.now().toIso8601String(),
    });
  }

  /// Request a hint for the current encounter.
  ///
  /// [encounterId] - The ID of the current encounter.
  /// [userId] - The user's ID.
  void requestHint(String encounterId, String userId) {
    send({
      'type': WsOutgoingMessageType.requestHint,
      'encounter_id': encounterId,
      'user_id': userId,
      'timestamp': DateTime.now().toIso8601String(),
    });
  }

  // ============================================
  // Internal Handlers
  // ============================================

  /// Handle incoming WebSocket messages
  void _handleMessage(dynamic rawMessage) {
    try {
      final String messageString =
          rawMessage is String ? rawMessage : rawMessage.toString();
      final Map<String, dynamic> message = jsonDecode(messageString);

      debugPrint('[WebSocket] Received: ${message['type']}');

      // Handle internal messages
      final type = message['type'];

      switch (type) {
        case WsIncomingMessageType.pong:
          _handlePong();
          break;

        case WsIncomingMessageType.authenticated:
          _updateConnectionState(WebSocketConnectionState.authenticated);
          _messageController.add(message);
          break;

        case WsIncomingMessageType.error:
          _handleServerError(message);
          _messageController.add(message);
          break;

        default:
          // Forward all messages to stream
          _messageController.add(message);
      }
    } catch (e) {
      debugPrint('[WebSocket] Message parse error: $e');
      _emitError('parse_error', 'Failed to parse message: $e');
    }
  }

  /// Handle WebSocket errors
  void _handleError(dynamic error) {
    debugPrint('[WebSocket] Stream error: $error');
    _emitError('stream_error', error.toString());
  }

  /// Handle WebSocket disconnect
  void _handleDisconnect() {
    debugPrint('[WebSocket] Connection closed');
    _cleanup();

    if (_autoReconnect &&
        _reconnectAttempts < WsReconnectionConfig.maxReconnectAttempts) {
      _scheduleReconnect();
    } else {
      _updateConnectionState(WebSocketConnectionState.disconnected);
    }
  }

  /// Handle server-side error messages
  void _handleServerError(Map<String, dynamic> message) {
    final errorMessage = message['message'] ?? 'Unknown server error';
    final errorCode = message['code'] ?? 'server_error';
    _emitError(errorCode.toString(), errorMessage.toString(), data: message['data']);
  }

  /// Handle pong response
  void _handlePong() {
    _pongTimer?.cancel();
    debugPrint('[WebSocket] Pong received');
  }

  /// Start the ping timer for keep-alive
  void _startPingTimer() {
    _pingTimer?.cancel();
    _pingTimer = Timer.periodic(
      Duration(milliseconds: WsTimeoutConfig.pingIntervalMs),
      (_) {
        if (isConnected) {
          ping();
          _startPongTimer();
        }
      },
    );
  }

  /// Start pong timeout timer
  void _startPongTimer() {
    _pongTimer?.cancel();
    _pongTimer = Timer(
      Duration(milliseconds: WsTimeoutConfig.pongTimeoutMs),
      () {
        debugPrint('[WebSocket] Pong timeout - connection may be dead');
        _emitError('pong_timeout', 'No pong response received');
        // Force reconnection
        _handleDisconnect();
      },
    );
  }

  /// Update connection state and notify listeners
  void _updateConnectionState(WebSocketConnectionState newState) {
    if (_connectionState != newState) {
      _connectionState = newState;
      _connectionStateController.add(newState);
      debugPrint('[WebSocket] State changed: $newState');
    }
  }

  /// Emit an error event
  void _emitError(String code, String message, {dynamic data}) {
    final error = WebSocketError(
      code: code,
      message: message,
      data: data,
    );
    _errorController.add(error);
  }

  /// Dispose of the service and clean up resources
  void dispose() {
    disconnect();
    _messageController.close();
    _connectionStateController.close();
    _errorController.close();
  }
}

// ============================================
// Riverpod Providers
// ============================================

/// Provider for the GameWebSocketService singleton
final gameWebSocketProvider = Provider<GameWebSocketService>((ref) {
  final service = GameWebSocketService();

  // Dispose when provider is disposed
  ref.onDispose(() {
    service.dispose();
  });

  return service;
});

/// Provider for WebSocket connection state
final webSocketConnectionStateProvider =
    StreamProvider<WebSocketConnectionState>((ref) {
  final service = ref.watch(gameWebSocketProvider);
  return service.connectionStateStream;
});

/// Provider for WebSocket messages stream
final webSocketMessagesProvider =
    StreamProvider<Map<String, dynamic>>((ref) {
  final service = ref.watch(gameWebSocketProvider);
  return service.messages;
});

/// Provider for WebSocket errors stream
final webSocketErrorsProvider = StreamProvider<WebSocketError>((ref) {
  final service = ref.watch(gameWebSocketProvider);
  return service.errors;
});

/// Provider to check if WebSocket is connected
final isWebSocketConnectedProvider = Provider<bool>((ref) {
  final connectionState = ref.watch(webSocketConnectionStateProvider);
  return connectionState.when(
    data: (state) =>
        state == WebSocketConnectionState.connected ||
        state == WebSocketConnectionState.authenticated,
    loading: () => false,
    error: (_, __) => false,
  );
});

/// Provider for filtered dungeon messages
final dungeonMessagesProvider =
    StreamProvider<Map<String, dynamic>>((ref) {
  final service = ref.watch(gameWebSocketProvider);
  return service.messages.where((msg) {
    final type = msg['type'];
    return type == WsIncomingMessageType.dungeonStarted ||
        type == WsIncomingMessageType.battleUpdate ||
        type == WsIncomingMessageType.encounterResult ||
        type == WsIncomingMessageType.newEncounter ||
        type == WsIncomingMessageType.dungeonCompleted ||
        type == WsIncomingMessageType.dungeonFailed ||
        type == WsIncomingMessageType.bossAppeared ||
        type == WsIncomingMessageType.comboAchieved;
  });
});

/// Provider for battle update messages specifically
final battleUpdateProvider = StreamProvider<Map<String, dynamic>>((ref) {
  final service = ref.watch(gameWebSocketProvider);
  return service.messages
      .where((msg) => msg['type'] == WsIncomingMessageType.battleUpdate);
});
