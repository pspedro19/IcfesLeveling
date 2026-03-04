import 'package:flutter/foundation.dart';

class SyncEvent {
  final DateTime timestamp;
  final String action;
  final Map<String, dynamic>? data;
  final bool success;
  final String? error;

  SyncEvent({
    required this.timestamp,
    required this.action,
    this.data,
    this.success = true,
    this.error,
  });

  @override
  String toString() => '${timestamp.toIso8601String()} | $action | Success: $success ${error ?? ''}';
}

class SyncLogger {
  static final List<SyncEvent> _events = [];
  
  static void log(String action, {Map<String, dynamic>? data, bool success = true, String? error}) {
    final event = SyncEvent(
      timestamp: DateTime.now(),
      action: action,
      data: data,
      success: success,
      error: error,
    );
    
    _events.add(event);
    
    // Print to console for development
    if (success) {
      debugPrint('✓ [Sync] $action');
    } else {
      debugPrint('✗ [Sync] $action: $error');
    }

    // Keep only last 100 events
    if (_events.length > 100) {
      _events.removeAt(0);
    }
  }
  
  static List<SyncEvent> export() => List.unmodifiable(_events);
  
  static void clear() => _events.clear();
}
