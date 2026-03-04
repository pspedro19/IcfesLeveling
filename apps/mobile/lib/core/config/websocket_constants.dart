/// WebSocket configuration constants for the Conquest/Dungeon game server.
///
/// This file contains all WebSocket-related constants including:
/// - Server URLs for different environments
/// - Message type constants for both incoming and outgoing messages
/// - Reconnection and timeout settings
library;

import 'package:flutter/foundation.dart';
import 'package:flutter_dotenv/flutter_dotenv.dart';

/// WebSocket server configuration
class WebSocketConfig {
  WebSocketConfig._();

  /// Get the WebSocket URL based on environment
  static String get serverUrl {
    if (kDebugMode && dotenv.isInitialized) {
      final dotenvValue = dotenv.get('WS_URL', fallback: '');
      if (dotenvValue.isNotEmpty) return dotenvValue;
    }

    const compileTime = String.fromEnvironment('WS_URL');
    if (compileTime.isNotEmpty) return compileTime;

    // Default local development server
    return 'ws://localhost:4002';
  }

  /// Production WebSocket URL
  static const String productionUrl = 'wss://api.icfesleveling.com/ws';

  /// Staging WebSocket URL
  static const String stagingUrl = 'wss://staging-api.icfesleveling.com/ws';

  /// Local development WebSocket URL
  static const String localUrl = 'ws://localhost:4002';

  /// Android emulator localhost URL (10.0.2.2 maps to host machine)
  static const String androidEmulatorUrl = 'ws://10.0.2.2:4002';

  /// iOS simulator localhost URL
  static const String iosSimulatorUrl = 'ws://localhost:4002';
}

/// Outgoing message types (client -> server)
class WsOutgoingMessageType {
  WsOutgoingMessageType._();

  /// Join a dungeon/conquest gate
  static const String joinDungeon = 'join_dungeon';

  /// Submit answer for a battle encounter
  static const String submitAnswer = 'submit_answer';

  /// Ping to keep connection alive
  static const String ping = 'ping';

  /// Request current dungeon state
  static const String getDungeonState = 'get_dungeon_state';

  /// Leave the current dungeon
  static const String leaveDungeon = 'leave_dungeon';

  /// Use an item during battle
  static const String useItem = 'use_item';

  /// Request hint for current encounter
  static const String requestHint = 'request_hint';

  /// Authenticate the connection
  static const String authenticate = 'authenticate';
}

/// Incoming message types (server -> client)
class WsIncomingMessageType {
  WsIncomingMessageType._();

  /// Dungeon session has started
  static const String dungeonStarted = 'dungeon_started';

  /// Battle state update (damage, health, etc.)
  static const String battleUpdate = 'battle_update';

  /// Error occurred
  static const String error = 'error';

  /// Pong response to ping
  static const String pong = 'pong';

  /// Encounter completed (correct/incorrect answer)
  static const String encounterResult = 'encounter_result';

  /// New encounter started
  static const String newEncounter = 'new_encounter';

  /// Dungeon completed (all encounters done)
  static const String dungeonCompleted = 'dungeon_completed';

  /// Dungeon failed (out of health/time)
  static const String dungeonFailed = 'dungeon_failed';

  /// Item used successfully
  static const String itemUsed = 'item_used';

  /// Hint provided
  static const String hintProvided = 'hint_provided';

  /// Connection authenticated
  static const String authenticated = 'authenticated';

  /// Player stats updated
  static const String statsUpdated = 'stats_updated';

  /// Combo achieved
  static const String comboAchieved = 'combo_achieved';

  /// Boss appeared
  static const String bossAppeared = 'boss_appeared';

  /// Achievement unlocked
  static const String achievementUnlocked = 'achievement_unlocked';
}

/// Reconnection settings
class WsReconnectionConfig {
  WsReconnectionConfig._();

  /// Initial delay before first reconnection attempt (milliseconds)
  static const int initialDelayMs = 1000;

  /// Maximum delay between reconnection attempts (milliseconds)
  static const int maxDelayMs = 30000;

  /// Multiplier for exponential backoff
  static const double backoffMultiplier = 1.5;

  /// Maximum number of reconnection attempts before giving up
  static const int maxReconnectAttempts = 10;

  /// Whether to use exponential backoff for reconnection
  static const bool useExponentialBackoff = true;

  /// Jitter factor to add randomness to delays (0.0 to 1.0)
  static const double jitterFactor = 0.2;
}

/// Timeout settings
class WsTimeoutConfig {
  WsTimeoutConfig._();

  /// Connection timeout (milliseconds)
  static const int connectionTimeoutMs = 10000;

  /// Ping interval to keep connection alive (milliseconds)
  static const int pingIntervalMs = 30000;

  /// Pong timeout - disconnect if no pong received (milliseconds)
  static const int pongTimeoutMs = 10000;

  /// Message send timeout (milliseconds)
  static const int sendTimeoutMs = 5000;
}

/// WebSocket close codes
class WsCloseCode {
  WsCloseCode._();

  /// Normal closure
  static const int normalClosure = 1000;

  /// Going away (e.g., server shutdown)
  static const int goingAway = 1001;

  /// Protocol error
  static const int protocolError = 1002;

  /// Unsupported data
  static const int unsupportedData = 1003;

  /// No status received
  static const int noStatusReceived = 1005;

  /// Abnormal closure
  static const int abnormalClosure = 1006;

  /// Invalid frame payload data
  static const int invalidPayload = 1007;

  /// Policy violation
  static const int policyViolation = 1008;

  /// Message too big
  static const int messageToBig = 1009;

  /// Missing extension
  static const int missingExtension = 1010;

  /// Internal error
  static const int internalError = 1011;

  /// Service restart
  static const int serviceRestart = 1012;

  /// Try again later
  static const int tryAgainLater = 1013;

  /// Authentication failed (custom code)
  static const int authenticationFailed = 4001;

  /// Session expired (custom code)
  static const int sessionExpired = 4002;

  /// Rate limited (custom code)
  static const int rateLimited = 4003;
}
