import '../config/environment.dart';

class ApiConstants {
  // Uses Environment config (dotenv in debug, compile-time in release)
  static String get baseUrl => Environment.apiUrl;

  /// WebSocket URL for real-time game features
  /// Converts API URL (http://host:4000) to WebSocket URL (ws://host:4002)
  static String get webSocketUrl {
    final apiUrl = baseUrl;
    String wsUrl = apiUrl.replaceFirst('http://', 'ws://').replaceFirst('https://', 'wss://');
    wsUrl = wsUrl.replaceFirst(':4000', ':4002').replaceFirst('/api/v1', '');
    if (!wsUrl.contains(':4002')) {
      final uri = Uri.parse(wsUrl);
      wsUrl = '${uri.scheme}://${uri.host}:4002';
    }
    return wsUrl;
  }

  static const Duration connectTimeout = Duration(seconds: 10);
  static const Duration receiveTimeout = Duration(seconds: 10);
  
  // Mobile Endpoints
  static const String mobilePrefix = '/mobile';

  // Auth endpoints
  static const String login = '/auth/login';
  static const String register = '/auth/register';
  static const String authMe = '/auth/me';
  static const String authRefresh = '/auth/refresh';

  // Questions endpoints
  static const String nextQuestion = '$mobilePrefix/questions/next';
  static const String batchQuestions = '$mobilePrefix/questions/batch';

  // Answers endpoints
  static const String submitAnswer = '$mobilePrefix/answers/submit';

  // Hearts endpoints
  static const String useHeart = '$mobilePrefix/hearts/use';
  static const String heartsStatus = '$mobilePrefix/hearts/status';
  static const String heartsRefill = '$mobilePrefix/hearts/refill';

  // Streak endpoints
  static const String extendStreak = '$mobilePrefix/streak/extend';
  static const String streakStatus = '$mobilePrefix/streak/status';
  static const String streakFreeze = '$mobilePrefix/streak/freeze';
  static const String streakRepair = '$mobilePrefix/streak/repair';

  // Mastery endpoints
  static const String masteryTopics = '$mobilePrefix/mastery/topics';
  static const String masteryWeakAreas = '$mobilePrefix/mastery/weak-areas';

  // Leagues endpoints
  static const String leaderboard = '$mobilePrefix/leagues/leaderboard';
  static const String leaguesCurrent = '$mobilePrefix/leagues/current';
  static const String leaguesJoin = '$mobilePrefix/leagues/join';
  static const String leaguesHistory = '$mobilePrefix/leagues/history';

  // Economy endpoints (not under mobile prefix - uses /economy/*)
  static const String economyShop = '/economy/shop';
  static const String economyBalance = '/economy/balance';
  static const String economyPurchase = '/economy/purchase';
  static const String economyInventory = '/economy/inventory';
  static const String economyTransactions = '/economy/transactions';
  static const String economyUseItem = '/economy/inventory/use';
  static const String economyEquipItem = '/economy/inventory/equip';

  // Store Power-ups endpoints
  static const String storePowerUps = '/store/power-ups';
  static const String storePowerUpsActive = '/store/power-ups/active';
  static const String storePowerUpsActivate = '/store/power-ups/activate';

  // Notifications endpoints
  static const String notificationsRegister = '$mobilePrefix/notifications/register';
  static const String notificationsPreferences = '$mobilePrefix/notifications/preferences';

  // Boss Raid endpoints (not under mobile prefix - uses /boss-raid/*)
  static const String bossRaidStatus = '/boss-raid/status';
  static const String bossRaidStart = '/boss-raid/start';
  static const String bossRaidSubmit = '/boss-raid/submit-answer';
  static const String bossRaidComplete = '/boss-raid/complete';
  static const String bossRaidLeaderboard = '/boss-raid/leaderboard';
  static const String bossRaidSession = '/boss-raid/session'; // + /{session_id}

  // Diagnostic endpoints (not under mobile prefix - uses /diagnostic/*)
  static const String quickDiagnosticStart = '/diagnostic/quick/start';
  static const String quickDiagnosticSubmit = '/diagnostic/quick/submit';
  static const String deepDiagnosticStart = '/diagnostic/deep/start'; // + /{subject_id}
  static const String deepDiagnosticSubmit = '/diagnostic/deep/submit';

  // Sync endpoints
  static const String syncState = '$mobilePrefix/sync/state';
  static const String syncAnswers = '$mobilePrefix/sync/answers';
  static const String syncStatus = '$mobilePrefix/sync/status';

  // XP/Progress endpoints
  static const String updateXp = '$mobilePrefix/progress/xp';

  // Achievements endpoints
  static const String achievements = '/achievements';
  static const String achievementsCheck = '/achievements/check';
  static const String achievementsRecent = '/achievements/recent';

  // Mastery endpoint (for sync)
  static const String mastery = '$mobilePrefix/mastery/update';

  // Analytics endpoint
  static const String analytics = '$mobilePrefix/analytics/event';

  // Study Plan endpoints
  static const String studyPlanCurrent = '/study-plans/current';

  // Video endpoints
  static const String videoTracking = '/videos/tracking';
  static const String videoProgress = '/videos/progress';

  // Dungeon endpoints
  static const String dungeonGates = '$mobilePrefix/dungeon/gates';
  static const String dungeonCurrentRun = '$mobilePrefix/dungeon/current-run';
  static const String dungeonRuns = '$mobilePrefix/dungeon/runs';
  static const String dungeonEncounters = '$mobilePrefix/dungeon/encounters';
  static const String dungeonSubmitAnswer = '$mobilePrefix/dungeon/submit-answer';
  static const String dungeonHistory = '$mobilePrefix/dungeon/history';

  // Spaced Repetition (SM-2) endpoints
  static const String spacedRepetitionDailyReviews = '/spaced-repetition/daily-reviews';
  static const String spacedRepetitionSubmitReview = '/spaced-repetition/review';
  static const String spacedRepetitionAnalytics = '/spaced-repetition/analytics';
  static const String spacedRepetitionCreateSchedule = '/spaced-repetition/schedule';
  static const String spacedRepetitionItems = '/spaced-repetition/items';
}
