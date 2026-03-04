import 'package:flutter/foundation.dart';
import 'package:timezone/timezone.dart' as tz;

/// Scheduler for calculating notification times with timezone support
/// Handles America/Bogota timezone and quiet hours logic
class NotificationScheduler {
  static const String _bogotaTimezone = 'America/Bogota';

  /// Quiet hours configuration
  /// 11 PM to 7 AM - no notifications except urgent streak reminders
  static const int quietHoursStart = 23; // 11 PM
  static const int quietHoursEnd = 7;    // 7 AM

  /// Streak reset hour (4 AM Bogota time)
  static const int streakResetHour = 4;

  tz.Location? _bogotaLocation;

  /// Initialize the scheduler with timezone data
  void initialize() {
    try {
      _bogotaLocation = tz.getLocation(_bogotaTimezone);
      debugPrint('NotificationScheduler: Timezone initialized to $_bogotaTimezone');
    } catch (e) {
      debugPrint('NotificationScheduler: Failed to load timezone: $e');
      // Fallback to UTC-5 offset
      _bogotaLocation = null;
    }
  }

  /// Get current time in Bogota timezone
  tz.TZDateTime get nowInBogota {
    if (_bogotaLocation != null) {
      return tz.TZDateTime.now(_bogotaLocation!);
    }
    // Fallback: UTC-5 approximation for Bogota
    final utcNow = DateTime.now().toUtc();
    return tz.TZDateTime.utc(
      utcNow.year,
      utcNow.month,
      utcNow.day,
      utcNow.hour - 5,
      utcNow.minute,
      utcNow.second,
    );
  }

  /// Check if a given time is within quiet hours
  /// Quiet hours: 11 PM - 7 AM (except urgent streak reminders)
  bool isInQuietHours(tz.TZDateTime time) {
    final hour = time.hour;
    // Quiet hours: 23:00 to 06:59
    return hour >= quietHoursStart || hour < quietHoursEnd;
  }

  /// Get the next scheduled time for a given hour and minute
  /// If the time has passed today, schedules for tomorrow
  /// Returns null if unable to calculate
  tz.TZDateTime? getNextScheduledTime(int hour, int minute) {
    if (_bogotaLocation == null) {
      debugPrint('NotificationScheduler: Timezone not initialized');
      return null;
    }

    final now = nowInBogota;
    var scheduledTime = tz.TZDateTime(
      _bogotaLocation!,
      now.year,
      now.month,
      now.day,
      hour,
      minute,
    );

    // If the time has already passed today, schedule for tomorrow
    if (scheduledTime.isBefore(now)) {
      scheduledTime = scheduledTime.add(const Duration(days: 1));
    }

    return scheduledTime;
  }

  /// Get the next Sunday at a specific time
  /// Used for Boss Raid and League reminders
  tz.TZDateTime? getNextSundayAt(int hour, int minute) {
    if (_bogotaLocation == null) {
      debugPrint('NotificationScheduler: Timezone not initialized');
      return null;
    }

    final now = nowInBogota;
    var scheduledTime = tz.TZDateTime(
      _bogotaLocation!,
      now.year,
      now.month,
      now.day,
      hour,
      minute,
    );

    // Calculate days until next Sunday (Sunday = 7 in DateTime)
    int daysUntilSunday = DateTime.sunday - now.weekday;
    if (daysUntilSunday <= 0) {
      // If today is Sunday and time has passed, or we're past Sunday
      if (daysUntilSunday == 0 && scheduledTime.isAfter(now)) {
        // Today is Sunday and time hasn't passed yet
        return scheduledTime;
      }
      daysUntilSunday += 7; // Schedule for next Sunday
    }

    scheduledTime = scheduledTime.add(Duration(days: daysUntilSunday));
    return scheduledTime;
  }

  /// Add days to current time at a reasonable notification hour (10 AM)
  /// Used for re-engagement notifications
  tz.TZDateTime? addDaysToNow(int days) {
    if (_bogotaLocation == null) {
      debugPrint('NotificationScheduler: Timezone not initialized');
      return null;
    }

    final now = nowInBogota;
    final scheduledTime = tz.TZDateTime(
      _bogotaLocation!,
      now.year,
      now.month,
      now.day + days,
      10, // 10 AM - good time for re-engagement
      0,
    );

    return scheduledTime;
  }

  /// Get time until streak reset (4 AM Bogota)
  Duration getTimeUntilStreakReset() {
    final now = nowInBogota;
    var resetTime = tz.TZDateTime(
      _bogotaLocation!,
      now.year,
      now.month,
      now.day,
      streakResetHour,
      0,
    );

    // If reset time has passed today, calculate for tomorrow
    if (resetTime.isBefore(now)) {
      resetTime = resetTime.add(const Duration(days: 1));
    }

    return resetTime.difference(now);
  }

  /// Check if streak is in danger (less than 8 hours until reset)
  bool isStreakInDanger() {
    final timeUntilReset = getTimeUntilStreakReset();
    return timeUntilReset.inHours < 8;
  }

  /// Check if this is the last chance for streak (less than 1 hour until reset)
  bool isStreakLastChance() {
    final timeUntilReset = getTimeUntilStreakReset();
    return timeUntilReset.inMinutes < 60;
  }

  /// Get day of week in Bogota timezone (1 = Monday, 7 = Sunday)
  int getDayOfWeek() {
    return nowInBogota.weekday;
  }

  /// Check if today is Sunday (Boss Raid / League closing day)
  bool isSunday() {
    return getDayOfWeek() == DateTime.sunday;
  }

  /// Check if it's the start of a new week (Monday)
  bool isStartOfWeek() {
    return getDayOfWeek() == DateTime.monday;
  }

  /// Format time for debugging
  String formatTime(tz.TZDateTime time) {
    return '${time.year}-${time.month.toString().padLeft(2, '0')}-${time.day.toString().padLeft(2, '0')} '
        '${time.hour.toString().padLeft(2, '0')}:${time.minute.toString().padLeft(2, '0')} '
        '(${_bogotaTimezone})';
  }

  /// Get the timezone location (for external use)
  tz.Location? get location => _bogotaLocation;

  /// Create a TZDateTime from components
  tz.TZDateTime? createDateTime({
    required int year,
    required int month,
    required int day,
    required int hour,
    required int minute,
    int second = 0,
  }) {
    if (_bogotaLocation == null) return null;
    return tz.TZDateTime(
      _bogotaLocation!,
      year,
      month,
      day,
      hour,
      minute,
      second,
    );
  }
}
