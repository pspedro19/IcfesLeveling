import 'dart:math' as math;
import '../utils/sync_logger.dart';

/// Resolves conflicts between client and server data during synchronization.
///
/// Conflict resolution strategy (LOGICA_DE_NEGOCIO.md):
/// - Merge XP: Sum both server and client XP (don't lose offline progress)
/// - Keep higher streak: Use max(server, client) for streak
/// - Union achievements: Combine both lists
/// - Server wins for: hearts, gold, premium_status, current_league
/// - Client wins for: learning data (mastery, answers, progress)
/// - Most recent timestamp wins for other fields
class ConflictResolver {
  /// Fields where we SUM the values (both server and client contribute)
  /// This prevents loss of offline XP progress
  static const List<String> mergeBySum = [
    'total_xp',
    'league_xp',
    'session_xp',
    'weekly_xp',
  ];

  /// Fields where we keep the MAXIMUM value
  /// Prevents losing streak progress
  static const List<String> mergeByMax = [
    'streak',
    'current_streak',
    'max_streak',
    'best_combo',
    'highest_score',
  ];

  /// Fields where we UNION the lists
  /// Ensures no achievements are lost
  static const List<String> mergeByUnion = [
    'achievements',
    'unlocked_achievements',
    'badges',
    'completed_lessons',
    'answered_questions',
  ];

  /// Fields where server value always takes precedence.
  /// These are critical for game integrity and preventing cheating.
  static const List<String> serverWins = [
    'hearts',
    'gold',
    'premium_status',
    'subscription_end',
    'current_league',
    'ban_status',
  ];

  /// Fields where client value always takes precedence.
  /// These represent learning progress that should not be lost.
  static const List<String> clientWins = [
    'mastery_updates',
    'answer_history',
    'practice_progress',
    'study_time',
    'notes',
    'bookmarks',
  ];

  /// Resolve a conflict between server and client values.
  ///
  /// Returns the resolved value based on the conflict resolution strategy:
  /// - [mergeBySum] fields: Sum both values (XP)
  /// - [mergeByMax] fields: Keep maximum (streak)
  /// - [mergeByUnion] fields: Union lists (achievements)
  /// - [serverWins] fields: Returns [serverValue]
  /// - [clientWins] fields: Returns [clientValue]
  /// - Other fields: Returns the value with the most recent timestamp
  Future<dynamic> resolve(
    String field,
    dynamic serverValue,
    dynamic clientValue, {
    DateTime? clientTimestamp,
    DateTime? serverTimestamp,
  }) async {
    SyncLogger.log('conflict_resolution_start', data: {
      'field': field,
      'server_value': serverValue?.toString(),
      'client_value': clientValue?.toString(),
    });

    dynamic resolvedValue;
    String strategy;

    // XP fields: Sum both values (LOGICA_DE_NEGOCIO.md: "Merge XP (sum both)")
    if (mergeBySum.contains(field)) {
      final serverNum = _toNum(serverValue);
      final clientNum = _toNum(clientValue);
      resolvedValue = serverNum + clientNum;
      strategy = 'merge_by_sum';
      SyncLogger.log('xp_merge', data: {
        'field': field,
        'server': serverNum,
        'client': clientNum,
        'merged': resolvedValue,
      });
    }
    // Streak fields: Keep maximum (LOGICA_DE_NEGOCIO.md: "Keep higher streak")
    else if (mergeByMax.contains(field)) {
      final serverNum = _toNum(serverValue);
      final clientNum = _toNum(clientValue);
      resolvedValue = math.max(serverNum, clientNum);
      strategy = 'merge_by_max';
      SyncLogger.log('streak_merge', data: {
        'field': field,
        'server': serverNum,
        'client': clientNum,
        'kept': resolvedValue,
      });
    }
    // Achievement fields: Union lists (LOGICA_DE_NEGOCIO.md: "Union achievements")
    else if (mergeByUnion.contains(field)) {
      resolvedValue = await mergeListFields(field,
        serverValue is List ? serverValue : null,
        clientValue is List ? clientValue : null,
      );
      strategy = 'merge_by_union';
    }
    // Server wins for critical game state
    else if (serverWins.contains(field)) {
      resolvedValue = serverValue;
      strategy = 'server_wins';
    }
    // Client wins for learning data
    else if (clientWins.contains(field)) {
      resolvedValue = clientValue;
      strategy = 'client_wins';
    }
    // Other fields: timestamp comparison
    else {
      resolvedValue = _resolveByTimestamp(
        serverValue,
        clientValue,
        clientTimestamp,
        serverTimestamp,
      );
      strategy = 'timestamp_comparison';
    }

    SyncLogger.log('conflict_resolution_complete', data: {
      'field': field,
      'strategy': strategy,
      'resolved_value': resolvedValue?.toString(),
    });

    return resolvedValue;
  }

  /// Convert dynamic value to number for arithmetic operations
  num _toNum(dynamic value) {
    if (value == null) return 0;
    if (value is num) return value;
    if (value is String) return num.tryParse(value) ?? 0;
    return 0;
  }

  /// Resolve conflict using timestamp comparison.
  /// If timestamps are unavailable, defaults to server value.
  dynamic _resolveByTimestamp(
    dynamic serverValue,
    dynamic clientValue,
    DateTime? clientTimestamp,
    DateTime? serverTimestamp,
  ) {
    // If no timestamps available, prefer server (safer)
    if (clientTimestamp == null && serverTimestamp == null) {
      return serverValue;
    }

    // If only client timestamp available, use client value
    if (serverTimestamp == null) {
      return clientValue;
    }

    // If only server timestamp available, use server value
    if (clientTimestamp == null) {
      return serverValue;
    }

    // Compare timestamps - most recent wins
    if (clientTimestamp.isAfter(serverTimestamp)) {
      return clientValue;
    } else {
      return serverValue;
    }
  }

  /// Merge list-type fields intelligently.
  /// Useful for fields like answer_history where we want to keep all entries.
  Future<List<dynamic>> mergeListFields(
    String field,
    List<dynamic>? serverList,
    List<dynamic>? clientList,
  ) async {
    final merged = <dynamic>{};

    // Add all server items
    if (serverList != null) {
      merged.addAll(serverList);
    }

    // Add client items (duplicates handled by Set)
    if (clientList != null) {
      merged.addAll(clientList);
    }

    SyncLogger.log('list_merge_complete', data: {
      'field': field,
      'server_count': serverList?.length ?? 0,
      'client_count': clientList?.length ?? 0,
      'merged_count': merged.length,
    });

    return merged.toList();
  }

  /// Merge map-type fields with conflict resolution per key.
  Future<Map<String, dynamic>> mergeMapFields(
    String field,
    Map<String, dynamic>? serverMap,
    Map<String, dynamic>? clientMap, {
    DateTime? clientTimestamp,
    DateTime? serverTimestamp,
  }) async {
    final merged = <String, dynamic>{};

    // Start with server values
    if (serverMap != null) {
      merged.addAll(serverMap);
    }

    // Override with client values for client-wins fields
    if (clientMap != null) {
      for (final entry in clientMap.entries) {
        final subField = '$field.${entry.key}';
        if (clientWins.any((f) => subField.startsWith(f))) {
          merged[entry.key] = entry.value;
        } else if (!serverWins.any((f) => subField.startsWith(f))) {
          // For non-critical fields, use timestamp
          if (clientTimestamp != null &&
              (serverTimestamp == null || clientTimestamp.isAfter(serverTimestamp))) {
            merged[entry.key] = entry.value;
          }
        }
      }
    }

    return merged;
  }

  /// Check if a field should use server value
  bool isServerWinsField(String field) => serverWins.contains(field);

  /// Check if a field should use client value
  bool isClientWinsField(String field) => clientWins.contains(field);
}
