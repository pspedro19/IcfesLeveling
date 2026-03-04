import 'package:uuid/uuid.dart';

/// Sync action types with their priority levels
/// Lower number = higher priority (processed first)
/// Based on LOGICA_DE_NEGOCIO.md specification
enum SyncActionType {
  submitAnswer,      // Priority 1: Critical - Answer submissions
  updateXp,          // Priority 2: High - XP/progress updates
  extendStreak,      // Priority 3: High - Streak updates
  useHeart,          // Priority 3: High - Heart usage
  unlockAchievement, // Priority 4: Medium - Achievement unlocks
  updateMastery,     // Priority 4: Medium - Mastery updates
  analyticsEvent,    // Priority 5: Low - Analytics events
  updateState,       // Priority 5: Low - General state sync
}

/// Priority levels for sync actions (LOGICA_DE_NEGOCIO.md)
class SyncPriority {
  static const int critical = 1;  // Answer submissions
  static const int high = 2;      // XP, streak, hearts
  static const int medium = 3;    // Achievements, mastery
  static const int low = 4;       // Analytics, state

  /// Get priority for action type
  static int forType(SyncActionType type) {
    switch (type) {
      case SyncActionType.submitAnswer:
        return critical;
      case SyncActionType.updateXp:
      case SyncActionType.extendStreak:
      case SyncActionType.useHeart:
        return high;
      case SyncActionType.unlockAchievement:
      case SyncActionType.updateMastery:
        return medium;
      case SyncActionType.analyticsEvent:
      case SyncActionType.updateState:
        return low;
    }
  }
}

class SyncAction {
  final String id;
  final SyncActionType type;
  final Map<String, dynamic> data;
  final DateTime clientTimestamp;
  final int retryCount;
  final bool isSynced;
  final int priority; // Added for priority queue

  SyncAction({
    String? id,
    required this.type,
    required this.data,
    DateTime? clientTimestamp,
    this.retryCount = 0,
    this.isSynced = false,
    int? priority,
  })  : id = id ?? const Uuid().v4(),
        clientTimestamp = clientTimestamp ?? DateTime.now(),
        priority = priority ?? SyncPriority.forType(type);

  Map<String, dynamic> toJson() => {
    'id': id,
    'type': type.index,
    'data': data,
    'clientTimestamp': clientTimestamp.toIso8601String(),
    'retryCount': retryCount,
    'isSynced': isSynced,
    'priority': priority,
  };

  factory SyncAction.fromJson(Map<String, dynamic> json) {
    DateTime parsedTimestamp;
    try {
      parsedTimestamp = DateTime.parse(json['clientTimestamp']);
    } catch (e) {
      parsedTimestamp = DateTime.now(); // Fallback seguro
    }

    final typeIndex = json['type'] ?? 0;
    final actionType = (typeIndex >= 0 && typeIndex < SyncActionType.values.length)
        ? SyncActionType.values[typeIndex]
        : SyncActionType.updateState;

    return SyncAction(
      id: json['id'],
      type: actionType,
      data: Map<String, dynamic>.from(json['data'] ?? {}),
      clientTimestamp: parsedTimestamp,
      retryCount: json['retryCount'] ?? 0,
      isSynced: json['isSynced'] ?? false,
      priority: json['priority'] ?? SyncPriority.forType(actionType),
    );
  }

  /// Create copy with updated fields
  SyncAction copyWith({
    String? id,
    SyncActionType? type,
    Map<String, dynamic>? data,
    DateTime? clientTimestamp,
    int? retryCount,
    bool? isSynced,
    int? priority,
  }) {
    return SyncAction(
      id: id ?? this.id,
      type: type ?? this.type,
      data: data ?? this.data,
      clientTimestamp: clientTimestamp ?? this.clientTimestamp,
      retryCount: retryCount ?? this.retryCount,
      isSynced: isSynced ?? this.isSynced,
      priority: priority ?? this.priority,
    );
  }
}
