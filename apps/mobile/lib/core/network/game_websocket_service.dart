import 'dart:async';
import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:web_socket_channel/web_socket_channel.dart';
import 'package:web_socket_channel/status.dart' as status;
import '../config/environment.dart';
import '../auth/data/datasources/auth_local_datasource.dart';
import 'api_client.dart';

/// Connection state for the WebSocket
enum WebSocketConnectionState {
  disconnected,
  connecting,
  connected,
  authenticated,
  error,
}

/// WebSocket message types
class WebSocketMessageType {
  static const String welcome = 'welcome';
  static const String authenticate = 'authenticate';
  static const String authenticated = 'authenticated';
  static const String ping = 'ping';
  static const String pong = 'pong';
  static const String error = 'error';
  static const String subscribe = 'subscribe';
  static const String subscribed = 'subscribed';
  static const String joinDungeon = 'join_dungeon';
  static const String dungeonStarted = 'dungeon_started';
  static const String submitAnswer = 'submit_answer';
  static const String battleUpdate = 'battle_update';
  static const String echo = 'echo';
}

/// Error codes from the WebSocket server
class WebSocketErrorCode {
  static const String authRequired = 'AUTH_REQUIRED';
  static const String tokenExpired = 'TOKEN_EXPIRED';
  static const String invalidToken = 'INVALID_TOKEN';
  static const String invalidTokenType = 'INVALID_TOKEN_TYPE';
  static const String invalidClaims = 'INVALID_CLAIMS';
  static const String serverConfigError = 'SERVER_CONFIG_ERROR';
  static const String unauthorized = 'UNAUTHORIZED';
  static const String userMismatch = 'USER_MISMATCH';
  static const String authError = 'AUTH_ERROR';
}

/// Message received from WebSocket
class WebSocketMessage {
  final String type;
  final Map<String, dynamic> data;
  final String? code;
  final String? message;

  WebSocketMessage({
    required this.type,
    required this.data,
    this.code,
    this.message,
  });

  factory WebSocketMessage.fromJson(Map<String, dynamic> json) {
    return WebSocketMessage(
      type: json['type'] as String? ?? 'unknown',
      data: json,
      code: json['code'] as String?,
      message: json['message'] as String?,
    );
  }

  bool get isError => type == WebSocketMessageType.error;
  bool get isAuthError => isError && (
    code == WebSocketErrorCode.authRequired ||
    code == WebSocketErrorCode.tokenExpired ||
    code == WebSocketErrorCode.invalidToken ||
    code == WebSocketErrorCode.unauthorized
  );
}

/// Game WebSocket Service for real-time game features
///
/// Handles:
/// - Connection management with automatic reconnection
/// - JWT authentication on connect
/// - Dungeon/battle game actions
/// - Room subscriptions for real-time updates
class GameWebSocketService extends ChangeNotifier {
  final AuthLocalDataSource _authLocalDataSource;

  WebSocketChannel? _channel;
  StreamSubscription? _subscription;
  Timer? _pingTimer;
  Timer? _reconnectTimer;

  WebSocketConnectionState _connectionState = WebSocketConnectionState.disconnected;
  String? _clientId;
  String? _userId;
  String? _lastError;
  int _reconnectAttempts = 0;
  static const int _maxReconnectAttempts = 5;
  static const Duration _reconnectDelay = Duration(seconds: 3);
  static const Duration _pingInterval = Duration(seconds: 30);

  // Stream controllers for different event types
  final _messageController = StreamController<WebSocketMessage>.broadcast();
  final _dungeonEventController = StreamController<Map<String, dynamic>>.broadcast();
  final _battleEventController = StreamController<Map<String, dynamic>>.broadcast();
  final _errorController = StreamController<WebSocketMessage>.broadcast();

  GameWebSocketService(this._authLocalDataSource);

  // Public getters
  WebSocketConnectionState get connectionState => _connectionState;
  String? get clientId => _clientId;
  String? get userId => _userId;
  String? get lastError => _lastError;
  bool get isConnected => _connectionState == WebSocketConnectionState.connected ||
                          _connectionState == WebSocketConnectionState.authenticated;
  bool get isAuthenticated => _connectionState == WebSocketConnectionState.authenticated;

  // Streams
  Stream<WebSocketMessage> get messageStream => _messageController.stream;
  Stream<Map<String, dynamic>> get dungeonEvents => _dungeonEventController.stream;
  Stream<Map<String, dynamic>> get battleEvents => _battleEventController.stream;
  Stream<WebSocketMessage> get errorStream => _errorController.stream;

  /// Get WebSocket URL from environment
  String get _wsUrl {
    // Get API URL and convert to WebSocket URL
    final apiUrl = Environment.apiUrl;
    // Replace http with ws and adjust port
    String wsUrl = apiUrl.replaceFirst('http://', 'ws://').replaceFirst('https://', 'wss://');
    // Replace API port (4000) with WebSocket port (4002)
    wsUrl = wsUrl.replaceFirst(':4000', ':4002').replaceFirst('/api/v1', '');
    // If no port specified, add default WebSocket port
    if (!wsUrl.contains(':4002')) {
      final uri = Uri.parse(wsUrl);
      wsUrl = '${uri.scheme}://${uri.host}:4002';
    }
    return wsUrl;
  }

  /// Connect to the WebSocket server
  Future<void> connect() async {
    if (_connectionState == WebSocketConnectionState.connecting ||
        _connectionState == WebSocketConnectionState.connected ||
        _connectionState == WebSocketConnectionState.authenticated) {
      debugPrint('GameWebSocket: Already connected or connecting');
      return;
    }

    _setConnectionState(WebSocketConnectionState.connecting);
    _lastError = null;

    try {
      final wsUrl = _wsUrl;
      debugPrint('GameWebSocket: Connecting to $wsUrl');

      _channel = WebSocketChannel.connect(Uri.parse(wsUrl));

      _subscription = _channel!.stream.listen(
        _onMessage,
        onError: _onError,
        onDone: _onDone,
      );

      // Wait briefly for welcome message
      await Future.delayed(const Duration(milliseconds: 500));

      if (_connectionState == WebSocketConnectionState.connecting) {
        _setConnectionState(WebSocketConnectionState.connected);
        _startPingTimer();
        _reconnectAttempts = 0;

        // Auto-authenticate if we have a token
        await _autoAuthenticate();
      }

    } catch (e) {
      debugPrint('GameWebSocket: Connection error: $e');
      _lastError = e.toString();
      _setConnectionState(WebSocketConnectionState.error);
      _scheduleReconnect();
    }
  }

  /// Disconnect from the WebSocket server
  Future<void> disconnect() async {
    debugPrint('GameWebSocket: Disconnecting');
    _cancelTimers();
    _reconnectAttempts = _maxReconnectAttempts; // Prevent auto-reconnect

    await _subscription?.cancel();
    _subscription = null;

    await _channel?.sink.close(status.goingAway);
    _channel = null;

    _clientId = null;
    _userId = null;
    _setConnectionState(WebSocketConnectionState.disconnected);
  }

  /// Authenticate with JWT token
  Future<void> authenticate(String token) async {
    if (!isConnected) {
      debugPrint('GameWebSocket: Cannot authenticate - not connected');
      return;
    }

    _send({
      'type': WebSocketMessageType.authenticate,
      'token': token,
    });
  }

  /// Auto-authenticate using stored token
  Future<void> _autoAuthenticate() async {
    final token = await _authLocalDataSource.getAccessToken();
    if (token != null && token.isNotEmpty) {
      debugPrint('GameWebSocket: Auto-authenticating with stored token');
      await authenticate(token);
    } else {
      debugPrint('GameWebSocket: No stored token for auto-authentication');
    }
  }

  /// Send ping to keep connection alive
  void ping() {
    _send({'type': WebSocketMessageType.ping});
  }

  /// Subscribe to a room for real-time updates
  void subscribeToRoom(String room) {
    if (!isAuthenticated && room != 'global') {
      debugPrint('GameWebSocket: Cannot subscribe to $room - not authenticated');
      return;
    }

    _send({
      'type': WebSocketMessageType.subscribe,
      'room': room,
    });
  }

  /// Join a dungeon
  void joinDungeon({required String gateId, required String userId}) {
    if (!isAuthenticated) {
      debugPrint('GameWebSocket: Cannot join dungeon - not authenticated');
      _errorController.add(WebSocketMessage(
        type: WebSocketMessageType.error,
        data: {},
        code: WebSocketErrorCode.unauthorized,
        message: 'Authentication required to join dungeon',
      ));
      return;
    }

    _send({
      'type': WebSocketMessageType.joinDungeon,
      'gate_id': gateId,
      'user_id': userId,
    });
  }

  /// Submit an answer during battle/encounter
  void submitAnswer({
    required String encounterId,
    required String oderId,
    required List<String> answers,
  }) {
    if (!isAuthenticated) {
      debugPrint('GameWebSocket: Cannot submit answer - not authenticated');
      _errorController.add(WebSocketMessage(
        type: WebSocketMessageType.error,
        data: {},
        code: WebSocketErrorCode.unauthorized,
        message: 'Authentication required to submit answer',
      ));
      return;
    }

    _send({
      'type': WebSocketMessageType.submitAnswer,
      'encounter_id': encounterId,
      'user_id': oderId,
      'answers': answers,
    });
  }

  /// Send raw message
  void _send(Map<String, dynamic> data) {
    if (_channel == null) {
      debugPrint('GameWebSocket: Cannot send - not connected');
      return;
    }

    try {
      final message = jsonEncode(data);
      _channel!.sink.add(message);
      debugPrint('GameWebSocket: Sent ${data['type']}');
    } catch (e) {
      debugPrint('GameWebSocket: Send error: $e');
    }
  }

  /// Handle incoming message
  void _onMessage(dynamic message) {
    try {
      final data = jsonDecode(message as String) as Map<String, dynamic>;
      final wsMessage = WebSocketMessage.fromJson(data);

      debugPrint('GameWebSocket: Received ${wsMessage.type}');

      // Handle specific message types
      switch (wsMessage.type) {
        case WebSocketMessageType.welcome:
          _clientId = data['client_id'] as String?;
          debugPrint('GameWebSocket: Welcome received, client_id: $_clientId');
          break;

        case WebSocketMessageType.authenticated:
          _userId = data['user_id'] as String?;
          _setConnectionState(WebSocketConnectionState.authenticated);
          debugPrint('GameWebSocket: Authenticated as user: $_userId');
          break;

        case WebSocketMessageType.pong:
          // Connection is alive
          break;

        case WebSocketMessageType.error:
          _lastError = wsMessage.message;
          _errorController.add(wsMessage);

          // Handle auth errors
          if (wsMessage.isAuthError) {
            if (wsMessage.code == WebSocketErrorCode.tokenExpired) {
              // Token expired - could trigger token refresh
              debugPrint('GameWebSocket: Token expired');
            }
            _setConnectionState(WebSocketConnectionState.connected);
          }
          break;

        case WebSocketMessageType.dungeonStarted:
          _dungeonEventController.add(data['data'] as Map<String, dynamic>? ?? {});
          break;

        case WebSocketMessageType.battleUpdate:
          _battleEventController.add(data['data'] as Map<String, dynamic>? ?? {});
          break;

        case WebSocketMessageType.subscribed:
          debugPrint('GameWebSocket: Subscribed to room: ${data['room']}');
          break;
      }

      // Broadcast all messages
      _messageController.add(wsMessage);

    } catch (e) {
      debugPrint('GameWebSocket: Error parsing message: $e');
    }
  }

  /// Handle connection error
  void _onError(dynamic error) {
    debugPrint('GameWebSocket: Error: $error');
    _lastError = error.toString();
    _setConnectionState(WebSocketConnectionState.error);
    _scheduleReconnect();
  }

  /// Handle connection closed
  void _onDone() {
    debugPrint('GameWebSocket: Connection closed');
    _cancelTimers();
    _setConnectionState(WebSocketConnectionState.disconnected);
    _scheduleReconnect();
  }

  /// Set connection state and notify listeners
  void _setConnectionState(WebSocketConnectionState state) {
    if (_connectionState != state) {
      _connectionState = state;
      notifyListeners();
    }
  }

  /// Start ping timer to keep connection alive
  void _startPingTimer() {
    _pingTimer?.cancel();
    _pingTimer = Timer.periodic(_pingInterval, (_) {
      if (isConnected) {
        ping();
      }
    });
  }

  /// Cancel all timers
  void _cancelTimers() {
    _pingTimer?.cancel();
    _pingTimer = null;
    _reconnectTimer?.cancel();
    _reconnectTimer = null;
  }

  /// Schedule reconnection attempt
  void _scheduleReconnect() {
    if (_reconnectAttempts >= _maxReconnectAttempts) {
      debugPrint('GameWebSocket: Max reconnect attempts reached');
      return;
    }

    _reconnectTimer?.cancel();
    _reconnectTimer = Timer(_reconnectDelay * (_reconnectAttempts + 1), () {
      _reconnectAttempts++;
      debugPrint('GameWebSocket: Reconnect attempt $_reconnectAttempts/$_maxReconnectAttempts');
      connect();
    });
  }

  /// Reset reconnection attempts (call after successful manual connect)
  void resetReconnectAttempts() {
    _reconnectAttempts = 0;
  }

  @override
  void dispose() {
    _cancelTimers();
    _subscription?.cancel();
    _channel?.sink.close();
    _messageController.close();
    _dungeonEventController.close();
    _battleEventController.close();
    _errorController.close();
    super.dispose();
  }
}

/// Provider for GameWebSocketService
final gameWebSocketServiceProvider = ChangeNotifierProvider<GameWebSocketService>((ref) {
  final authLocal = ref.watch(authLocalDataSourceProvider);
  final service = GameWebSocketService(authLocal);

  // Auto-connect when provider is created
  service.connect();

  ref.onDispose(() {
    service.disconnect();
  });

  return service;
});

/// Provider for WebSocket connection state
final webSocketConnectionStateProvider = Provider<WebSocketConnectionState>((ref) {
  final service = ref.watch(gameWebSocketServiceProvider);
  return service.connectionState;
});

/// Provider to check if WebSocket is authenticated
final webSocketIsAuthenticatedProvider = Provider<bool>((ref) {
  final service = ref.watch(gameWebSocketServiceProvider);
  return service.isAuthenticated;
});
