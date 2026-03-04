import 'package:firebase_analytics/firebase_analytics.dart';
import 'package:flutter/foundation.dart';

/// Centralized analytics service for tracking user events.
///
/// Wraps Firebase Analytics with graceful fallback when Firebase
/// is not configured (e.g., development mode without google-services.json).
///
/// Events tracked:
/// - Practice sessions (start, complete, abandon)
/// - Diagnostic tests (start, complete)
/// - Gamification (level_up, streak_day, combo_milestone)
/// - Economy (purchase, reward)
/// - Social (boss_raid_join, league_promotion)
class AnalyticsService {
  static final AnalyticsService _instance = AnalyticsService._internal();
  factory AnalyticsService() => _instance;
  AnalyticsService._internal();

  FirebaseAnalytics? _analytics;
  bool _isAvailable = false;

  /// Initialize. Call after Firebase.initializeApp().
  void initialize() {
    try {
      _analytics = FirebaseAnalytics.instance;
      _isAvailable = true;
      debugPrint('AnalyticsService: initialized');
    } catch (e) {
      _isAvailable = false;
      debugPrint('AnalyticsService: Firebase Analytics unavailable — $e');
    }
  }

  /// Set user ID for all subsequent events.
  Future<void> setUserId(String userId) async {
    if (!_isAvailable) return;
    try {
      await _analytics!.setUserId(id: userId);
    } catch (e) {
      debugPrint('AnalyticsService: setUserId failed — $e');
    }
  }

  /// Set user properties (rank, level, league).
  Future<void> setUserProperties({
    String? rank,
    int? level,
    String? league,
  }) async {
    if (!_isAvailable) return;
    try {
      if (rank != null) {
        await _analytics!.setUserProperty(name: 'rank', value: rank);
      }
      if (level != null) {
        await _analytics!.setUserProperty(name: 'level', value: level.toString());
      }
      if (league != null) {
        await _analytics!.setUserProperty(name: 'league', value: league);
      }
    } catch (e) {
      debugPrint('AnalyticsService: setUserProperties failed — $e');
    }
  }

  /// Log screen view for automatic screen tracking.
  Future<void> logScreenView(String screenName) async {
    if (!_isAvailable) return;
    try {
      await _analytics!.logScreenView(screenName: screenName);
    } catch (e) {
      debugPrint('AnalyticsService: logScreenView failed — $e');
    }
  }

  // ==========================================
  // Practice Events
  // ==========================================

  Future<void> logPracticeStart({
    required String sessionType,
    String? subjectId,
    int? difficulty,
  }) async {
    await _logEvent('practice_start', {
      'session_type': sessionType,
      if (subjectId != null) 'subject_id': subjectId,
      if (difficulty != null) 'difficulty': difficulty,
    });
  }

  Future<void> logPracticeComplete({
    required String sessionType,
    required int correctAnswers,
    required int totalQuestions,
    required int xpEarned,
    required int goldEarned,
    required int maxCombo,
  }) async {
    await _logEvent('practice_complete', {
      'session_type': sessionType,
      'correct_answers': correctAnswers,
      'total_questions': totalQuestions,
      'xp_earned': xpEarned,
      'gold_earned': goldEarned,
      'max_combo': maxCombo,
      'accuracy': totalQuestions > 0
          ? (correctAnswers / totalQuestions * 100).round()
          : 0,
    });
  }

  // ==========================================
  // Diagnostic Events
  // ==========================================

  Future<void> logDiagnosticStart({required String type}) async {
    await _logEvent('diagnostic_start', {'type': type});
  }

  Future<void> logDiagnosticComplete({
    required String type,
    required int score,
    required String rank,
  }) async {
    await _logEvent('diagnostic_complete', {
      'type': type,
      'score': score,
      'rank': rank,
    });
  }

  // ==========================================
  // Gamification Events
  // ==========================================

  Future<void> logLevelUp({required int newLevel}) async {
    await _logEvent('level_up', {'level': newLevel});
  }

  Future<void> logStreakDay({required int streakDays}) async {
    await _logEvent('streak_day', {'streak_days': streakDays});
  }

  Future<void> logStreakLost({required int previousStreak}) async {
    await _logEvent('streak_lost', {'previous_streak': previousStreak});
  }

  Future<void> logComboMilestone({required int combo}) async {
    await _logEvent('combo_milestone', {'combo': combo});
  }

  // ==========================================
  // Economy Events
  // ==========================================

  Future<void> logPurchase({
    required String itemId,
    required String itemName,
    required int cost,
    required String currency,
  }) async {
    await _logEvent('purchase', {
      'item_id': itemId,
      'item_name': itemName,
      'cost': cost,
      'currency': currency,
    });
  }

  Future<void> logAdRewardEarned({required String rewardType}) async {
    await _logEvent('ad_reward_earned', {'reward_type': rewardType});
  }

  // ==========================================
  // Social Events
  // ==========================================

  Future<void> logBossRaidJoin({required String bossName}) async {
    await _logEvent('boss_raid_join', {'boss_name': bossName});
  }

  Future<void> logBossRaidComplete({
    required String bossName,
    required int damage,
    required bool victory,
  }) async {
    await _logEvent('boss_raid_complete', {
      'boss_name': bossName,
      'damage': damage,
      'victory': victory,
    });
  }

  Future<void> logLeaguePromotion({
    required String fromLeague,
    required String toLeague,
  }) async {
    await _logEvent('league_promotion', {
      'from_league': fromLeague,
      'to_league': toLeague,
    });
  }

  // ==========================================
  // Auth Events
  // ==========================================

  Future<void> logLogin({required String method}) async {
    if (!_isAvailable) return;
    try {
      await _analytics!.logLogin(loginMethod: method);
    } catch (e) {
      debugPrint('AnalyticsService: logLogin failed — $e');
    }
  }

  Future<void> logSignUp({required String method}) async {
    if (!_isAvailable) return;
    try {
      await _analytics!.logSignUp(signUpMethod: method);
    } catch (e) {
      debugPrint('AnalyticsService: logSignUp failed — $e');
    }
  }

  // ==========================================
  // Internal
  // ==========================================

  Future<void> _logEvent(String name, Map<String, Object> params) async {
    if (!_isAvailable) return;
    try {
      await _analytics!.logEvent(name: name, parameters: params);
    } catch (e) {
      debugPrint('AnalyticsService: $name failed — $e');
    }
  }
}
