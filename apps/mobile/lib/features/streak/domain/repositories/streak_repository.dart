import 'dart:async';

abstract class StreakRepository {
  Future<Map<String, dynamic>> repairStreak(String method);
}
