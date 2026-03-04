import 'dart:io';

import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:timezone/timezone.dart' as tz;
import 'package:timezone/data/latest.dart' as tz_data;

import 'notification_scheduler.dart';
import 'onboarding_service.dart' show sharedPreferencesProvider;

/// Keys for notification preferences storage
class NotificationKeys {
  static const String fcmToken = 'fcm_token';
  static const String notificationsEnabled = 'notifications_enabled';
  static const String lastStreakReminder = 'last_streak_reminder';
  static const String quietHoursEnabled = 'quiet_hours_enabled';
  // Granular notification settings
  static const String streakNotificationsEnabled = 'streak_notifications_enabled';
  static const String dailyQuestNotificationsEnabled = 'daily_quest_notifications_enabled';
  static const String leagueNotificationsEnabled = 'league_notifications_enabled';
  static const String bossRaidNotificationsEnabled = 'boss_raid_notifications_enabled';
  static const String achievementNotificationsEnabled = 'achievement_notifications_enabled';
  static const String dailyGoalNotificationsEnabled = 'daily_goal_notifications_enabled';
}

/// Notification channel IDs for Android
class NotificationChannels {
  static const String streakReminder = 'streak_reminder';
  static const String leagueReminder = 'league_reminder';
  static const String bossRaidReminder = 'boss_raid_reminder';
  static const String reEngagement = 're_engagement';
  static const String dailyQuest = 'daily_quest';
  static const String achievement = 'achievement';
  static const String dailyGoal = 'daily_goal';
  static const String general = 'general';
}

/// Notification IDs to allow cancellation and updates
class NotificationIds {
  static const int streak6pm = 1001;
  static const int streak9pm = 1002;
  static const int streak330am = 1003;
  static const int bossRaid = 2001;
  static const int leagueClosing = 3001;
  static const int reEngagement3days = 4001;
  static const int reEngagement7days = 4002;
  static const int reEngagement14days = 4003;
  // Daily quest notifications
  static const int dailyQuestMorning = 5001;
  static const int dailyQuestAfternoon = 5002;
  static const int dailyQuestEvening = 5003;
  // Daily goal notifications
  static const int dailyGoalReminder = 6001;
  static const int dailyGoalEndOfDay = 6002;
  // Achievement notifications
  static const int achievementBase = 7000; // Add achievement ID to get unique ID
}

/// Deep link routes for notification navigation
class NotificationRoutes {
  static const String home = '/home';
  static const String practice = '/practice';
  static const String leagues = '/leagues';
  static const String bossRaid = '/boss-raid';
  static const String studyPlan = '/study-plan';
  static const String profile = '/profile';
  static const String store = '/store';
  static const String dungeonMap = '/dungeon/map';
}

/// Callback type for navigation from notifications
typedef NotificationNavigationCallback = void Function(String route, Map<String, dynamic>? extras);

/// Callback type for analytics tracking
typedef NotificationAnalyticsCallback = void Function(String event, Map<String, dynamic> properties);

/// Service for managing push notifications (local and remote)
class NotificationService {
  final FlutterLocalNotificationsPlugin _localNotifications;
  final FirebaseMessaging? _firebaseMessaging;
  final SharedPreferences _prefs;
  final NotificationScheduler _scheduler;

  bool _isInitialized = false;

  /// Callback for handling navigation from notification taps
  NotificationNavigationCallback? onNavigate;

  /// Callback for analytics tracking
  NotificationAnalyticsCallback? onAnalyticsEvent;

  NotificationService({
    required SharedPreferences prefs,
    FlutterLocalNotificationsPlugin? localNotifications,
    FirebaseMessaging? firebaseMessaging,
    this.onNavigate,
    this.onAnalyticsEvent,
  })  : _prefs = prefs,
        _localNotifications = localNotifications ?? FlutterLocalNotificationsPlugin(),
        _firebaseMessaging = firebaseMessaging,
        _scheduler = NotificationScheduler();

  /// Check if the service is initialized
  bool get isInitialized => _isInitialized;

  /// Check if notifications are enabled by user
  bool get notificationsEnabled =>
      _prefs.getBool(NotificationKeys.notificationsEnabled) ?? true;

  /// Get stored FCM token
  String? get fcmToken => _prefs.getString(NotificationKeys.fcmToken);

  // Granular notification settings getters
  bool get streakNotificationsEnabled =>
      _prefs.getBool(NotificationKeys.streakNotificationsEnabled) ?? true;

  bool get dailyQuestNotificationsEnabled =>
      _prefs.getBool(NotificationKeys.dailyQuestNotificationsEnabled) ?? true;

  bool get leagueNotificationsEnabled =>
      _prefs.getBool(NotificationKeys.leagueNotificationsEnabled) ?? true;

  bool get bossRaidNotificationsEnabled =>
      _prefs.getBool(NotificationKeys.bossRaidNotificationsEnabled) ?? true;

  bool get achievementNotificationsEnabled =>
      _prefs.getBool(NotificationKeys.achievementNotificationsEnabled) ?? true;

  bool get dailyGoalNotificationsEnabled =>
      _prefs.getBool(NotificationKeys.dailyGoalNotificationsEnabled) ?? true;

  /// Initialize the notification service
  Future<void> initialize() async {
    if (_isInitialized) return;

    // Initialize timezone data for scheduling
    tz_data.initializeTimeZones();
    _scheduler.initialize();

    // Initialize local notifications
    await _initializeLocalNotifications();

    // Initialize Firebase Cloud Messaging if available
    await _initializeFirebaseMessaging();

    _isInitialized = true;
    debugPrint('NotificationService: Initialized successfully');
  }

  /// Initialize local notifications with Android and iOS settings
  Future<void> _initializeLocalNotifications() async {
    // Android settings
    const androidSettings = AndroidInitializationSettings('@mipmap/ic_launcher');

    // iOS settings
    const iosSettings = DarwinInitializationSettings(
      requestAlertPermission: true,
      requestBadgePermission: true,
      requestSoundPermission: true,
    );

    const initSettings = InitializationSettings(
      android: androidSettings,
      iOS: iosSettings,
    );

    await _localNotifications.initialize(
      initSettings,
      onDidReceiveNotificationResponse: _onNotificationTapped,
    );

    // Create notification channels for Android
    if (Platform.isAndroid) {
      await _createNotificationChannels();
    }

    // Request permissions on iOS
    if (Platform.isIOS) {
      await _localNotifications
          .resolvePlatformSpecificImplementation<IOSFlutterLocalNotificationsPlugin>()
          ?.requestPermissions(alert: true, badge: true, sound: true);
    }
  }

  /// Create Android notification channels
  Future<void> _createNotificationChannels() async {
    final androidPlugin = _localNotifications
        .resolvePlatformSpecificImplementation<AndroidFlutterLocalNotificationsPlugin>();

    if (androidPlugin == null) return;

    // Streak Reminder Channel - High importance for urgent notifications
    await androidPlugin.createNotificationChannel(
      const AndroidNotificationChannel(
        NotificationChannels.streakReminder,
        'Recordatorios de Racha',
        description: 'Notificaciones para proteger tu racha diaria',
        importance: Importance.high,
        enableVibration: true,
        playSound: true,
      ),
    );

    // League Reminder Channel
    await androidPlugin.createNotificationChannel(
      const AndroidNotificationChannel(
        NotificationChannels.leagueReminder,
        'Recordatorios de Liga',
        description: 'Notificaciones sobre el cierre de la liga semanal',
        importance: Importance.high,
        enableVibration: true,
        playSound: true,
      ),
    );

    // Boss Raid Channel
    await androidPlugin.createNotificationChannel(
      const AndroidNotificationChannel(
        NotificationChannels.bossRaidReminder,
        'Boss Raid',
        description: 'Notificaciones del evento Boss Raid semanal',
        importance: Importance.high,
        enableVibration: true,
        playSound: true,
      ),
    );

    // Re-engagement Channel - Lower importance
    await androidPlugin.createNotificationChannel(
      const AndroidNotificationChannel(
        NotificationChannels.reEngagement,
        'Vuelve a Jugar',
        description: 'Recordatorios para usuarios inactivos',
        importance: Importance.defaultImportance,
        enableVibration: false,
        playSound: true,
      ),
    );

    // Daily Quest Channel
    await androidPlugin.createNotificationChannel(
      const AndroidNotificationChannel(
        NotificationChannels.dailyQuest,
        'Misiones Diarias',
        description: 'Recordatorios para completar misiones diarias',
        importance: Importance.high,
        enableVibration: true,
        playSound: true,
      ),
    );

    // Achievement Channel
    await androidPlugin.createNotificationChannel(
      const AndroidNotificationChannel(
        NotificationChannels.achievement,
        'Logros',
        description: 'Notificaciones de logros desbloqueados',
        importance: Importance.high,
        enableVibration: true,
        playSound: true,
      ),
    );

    // Daily Goal Channel
    await androidPlugin.createNotificationChannel(
      const AndroidNotificationChannel(
        NotificationChannels.dailyGoal,
        'Meta Diaria',
        description: 'Recordatorios de meta diaria de XP',
        importance: Importance.defaultImportance,
        enableVibration: true,
        playSound: true,
      ),
    );

    // General Channel
    await androidPlugin.createNotificationChannel(
      const AndroidNotificationChannel(
        NotificationChannels.general,
        'General',
        description: 'Notificaciones generales de la aplicacion',
        importance: Importance.defaultImportance,
      ),
    );
  }

  /// Initialize Firebase Cloud Messaging
  Future<void> _initializeFirebaseMessaging() async {
    final messaging = _firebaseMessaging;
    if (messaging == null) {
      debugPrint('NotificationService: Firebase Messaging not available');
      return;
    }

    try {
      // Request permission
      final settings = await messaging.requestPermission(
        alert: true,
        badge: true,
        sound: true,
        provisional: false,
      );

      if (settings.authorizationStatus == AuthorizationStatus.authorized ||
          settings.authorizationStatus == AuthorizationStatus.provisional) {
        // Get FCM token
        final token = await messaging.getToken();
        if (token != null) {
          await _prefs.setString(NotificationKeys.fcmToken, token);
          debugPrint('NotificationService: FCM Token obtained');
        }

        // Listen for token refresh
        messaging.onTokenRefresh.listen((newToken) async {
          await _prefs.setString(NotificationKeys.fcmToken, newToken);
          debugPrint('NotificationService: FCM Token refreshed');
        });

        // Handle foreground messages
        FirebaseMessaging.onMessage.listen(_handleForegroundMessage);

        // Handle background message tap
        FirebaseMessaging.onMessageOpenedApp.listen(_handleMessageOpenedApp);
      }
    } catch (e) {
      debugPrint('NotificationService: Firebase Messaging init failed: $e');
    }
  }

  /// Handle notification tap - implements deep linking
  void _onNotificationTapped(NotificationResponse response) {
    debugPrint('NotificationService: Notification tapped: ${response.payload}');

    final payload = response.payload;
    if (payload == null || payload.isEmpty) return;

    // Track analytics
    _trackNotificationEvent('notification_opened', {
      'payload': payload,
      'action_id': response.actionId ?? 'tap',
    });

    // Parse payload and navigate
    final route = _getRouteFromPayload(payload);
    final extras = _getExtrasFromPayload(payload);

    if (onNavigate != null && route != null) {
      onNavigate!(route, extras);
    }
  }

  /// Get navigation route from payload
  String? _getRouteFromPayload(String payload) {
    switch (payload) {
      case 'streak_reminder_6pm':
      case 'streak_reminder_9pm':
      case 'streak_reminder_330am':
        return NotificationRoutes.practice;
      case 'boss_raid_start':
        return NotificationRoutes.bossRaid;
      case 'league_closing':
        return NotificationRoutes.leagues;
      case 're_engagement_3days':
      case 're_engagement_7days':
      case 're_engagement_14days':
        return NotificationRoutes.home;
      case 'daily_quest_morning':
      case 'daily_quest_afternoon':
      case 'daily_quest_evening':
        return NotificationRoutes.home;
      case 'daily_goal_reminder':
      case 'daily_goal_end_of_day':
        return NotificationRoutes.practice;
      default:
        // Check for achievement payloads
        if (payload.startsWith('achievement_')) {
          return NotificationRoutes.profile;
        }
        return NotificationRoutes.home;
    }
  }

  /// Get extra data from payload
  Map<String, dynamic>? _getExtrasFromPayload(String payload) {
    if (payload.startsWith('achievement_')) {
      final achievementId = payload.replaceFirst('achievement_', '');
      return {'achievement_id': achievementId, 'show_achievement': true};
    }
    return null;
  }

  /// Track notification analytics event
  void _trackNotificationEvent(String event, Map<String, dynamic> properties) {
    onAnalyticsEvent?.call(event, properties);
    debugPrint('NotificationService: Analytics - $event: $properties');
  }

  /// Handle foreground FCM message
  void _handleForegroundMessage(RemoteMessage message) {
    debugPrint('NotificationService: Foreground message received');

    // Show local notification for FCM messages received in foreground
    if (message.notification != null) {
      showNotification(
        title: message.notification!.title ?? 'ICFES Leveling',
        body: message.notification!.body ?? '',
        channelId: NotificationChannels.general,
      );
    }
  }

  /// Handle FCM message when app is opened from notification
  void _handleMessageOpenedApp(RemoteMessage message) {
    debugPrint('NotificationService: App opened from notification');
    // Handle deep linking based on message data
  }

  /// Show an immediate notification
  Future<void> showNotification({
    required String title,
    required String body,
    String channelId = NotificationChannels.general,
    String? payload,
    int? notificationId,
  }) async {
    if (!_isInitialized) {
      debugPrint('NotificationService: Not initialized, cannot show notification');
      return;
    }

    final androidDetails = AndroidNotificationDetails(
      channelId,
      _getChannelName(channelId),
      channelDescription: _getChannelDescription(channelId),
      importance: Importance.high,
      priority: Priority.high,
      showWhen: true,
    );

    const iosDetails = DarwinNotificationDetails(
      presentAlert: true,
      presentBadge: true,
      presentSound: true,
    );

    final details = NotificationDetails(
      android: androidDetails,
      iOS: iosDetails,
    );

    await _localNotifications.show(
      notificationId ?? DateTime.now().millisecondsSinceEpoch.remainder(100000),
      title,
      body,
      details,
      payload: payload,
    );
  }

  /// Schedule streak reminder notifications
  /// Called after each practice session to reschedule reminders
  Future<void> scheduleStreakReminder(int streakDays) async {
    if (!_isInitialized || !notificationsEnabled) return;

    // Cancel existing streak reminders
    await cancelStreakReminders();

    // Only schedule if user hasn't studied today (this should be checked by caller)
    // These notifications are for users who HAVEN'T completed their daily activity

    // 6:00 PM reminder - First warning
    final time6pm = _scheduler.getNextScheduledTime(18, 0);
    if (time6pm != null && !_scheduler.isInQuietHours(time6pm)) {
      await _scheduleNotification(
        id: NotificationIds.streak6pm,
        title: 'ICFES Leveling',
        body: '⚡ [SISTEMA] Tu racha de $streakDays dias esta en peligro. Mision disponible: 5 minutos.',
        scheduledTime: time6pm,
        channelId: NotificationChannels.streakReminder,
        payload: 'streak_reminder_6pm',
      );
    }

    // 9:00 PM reminder - Urgent warning
    final time9pm = _scheduler.getNextScheduledTime(21, 0);
    if (time9pm != null && !_scheduler.isInQuietHours(time9pm)) {
      await _scheduleNotification(
        id: NotificationIds.streak9pm,
        title: 'ICFES Leveling',
        body: '🔥 [ALERTA] Quedan 7 horas. Los Cazadores debiles pierden su racha esta noche.',
        scheduledTime: time9pm,
        channelId: NotificationChannels.streakReminder,
        payload: 'streak_reminder_9pm',
      );
    }

    // 3:30 AM reminder - Last chance (bypasses quiet hours for urgency)
    final time330am = _scheduler.getNextScheduledTime(3, 30);
    if (time330am != null) {
      await _scheduleNotification(
        id: NotificationIds.streak330am,
        title: 'ICFES Leveling',
        body: '💀 [URGENTE] 30 minutos para el reinicio. Tu racha de $streakDays dias desaparecera.',
        scheduledTime: time330am,
        channelId: NotificationChannels.streakReminder,
        payload: 'streak_reminder_330am',
      );
    }

    debugPrint('NotificationService: Streak reminders scheduled for $streakDays days');
  }

  /// Cancel all streak reminder notifications
  Future<void> cancelStreakReminders() async {
    await _localNotifications.cancel(NotificationIds.streak6pm);
    await _localNotifications.cancel(NotificationIds.streak9pm);
    await _localNotifications.cancel(NotificationIds.streak330am);
  }

  /// Schedule Boss Raid reminder for Sunday 10:00 AM
  Future<void> scheduleBossRaidReminder() async {
    if (!_isInitialized || !notificationsEnabled) return;

    // Cancel existing boss raid reminder
    await _localNotifications.cancel(NotificationIds.bossRaid);

    // Schedule for next Sunday at 10:00 AM
    final nextSunday = _scheduler.getNextSundayAt(10, 0);
    if (nextSunday != null) {
      await _scheduleNotification(
        id: NotificationIds.bossRaid,
        title: 'ICFES Leveling',
        body: '⚔️ [SISTEMA] El Boss Raid ha comenzado. Tienes 12 horas para demostrar tu rango, Cazador.',
        scheduledTime: nextSunday,
        channelId: NotificationChannels.bossRaidReminder,
        payload: 'boss_raid_start',
      );
      debugPrint('NotificationService: Boss Raid reminder scheduled for $nextSunday');
    }
  }

  /// Schedule League closing reminder for Sunday 6:00 PM
  Future<void> scheduleLeagueReminder({int? currentRank}) async {
    if (!_isInitialized || !notificationsEnabled) return;

    // Cancel existing league reminder
    await _localNotifications.cancel(NotificationIds.leagueClosing);

    // Schedule for next Sunday at 6:00 PM
    final nextSunday = _scheduler.getNextSundayAt(18, 0);
    if (nextSunday != null) {
      final rankText = currentRank != null ? ' Posicion actual: #$currentRank. Top 10 ascienden.' : '';
      await _scheduleNotification(
        id: NotificationIds.leagueClosing,
        title: 'ICFES Leveling',
        body: '🏆 [SISTEMA] La Liga cierra en 6 horas.$rankText',
        scheduledTime: nextSunday,
        channelId: NotificationChannels.leagueReminder,
        payload: 'league_closing',
      );
      debugPrint('NotificationService: League reminder scheduled for $nextSunday');
    }
  }

  /// Schedule re-engagement notifications for inactive users
  Future<void> scheduleReEngagement(int daysInactive) async {
    if (!_isInitialized || !notificationsEnabled) return;

    // Cancel existing re-engagement notifications
    await cancelReEngagementNotifications();

    // 3 days inactive
    if (daysInactive < 3) {
      final time3days = _scheduler.addDaysToNow(3 - daysInactive);
      if (time3days != null && !_scheduler.isInQuietHours(time3days)) {
        await _scheduleNotification(
          id: NotificationIds.reEngagement3days,
          title: 'ICFES Leveling',
          body: '💀 [SISTEMA] Tu racha fue destruida. Pero tu Mastery permanece. ¿Vuelves al Dungeon?',
          scheduledTime: time3days,
          channelId: NotificationChannels.reEngagement,
          payload: 're_engagement_3days',
        );
      }
    }

    // 7 days inactive
    if (daysInactive < 7) {
      final time7days = _scheduler.addDaysToNow(7 - daysInactive);
      if (time7days != null && !_scheduler.isInQuietHours(time7days)) {
        await _scheduleNotification(
          id: NotificationIds.reEngagement7days,
          title: 'ICFES Leveling',
          body: '🌑 [SISTEMA] Un Cazador olvidado es un Cazador muerto. El Sistema te espera.',
          scheduledTime: time7days,
          channelId: NotificationChannels.reEngagement,
          payload: 're_engagement_7days',
        );
      }
    }

    // 14 days inactive
    if (daysInactive < 14) {
      final time14days = _scheduler.addDaysToNow(14 - daysInactive);
      if (time14days != null && !_scheduler.isInQuietHours(time14days)) {
        await _scheduleNotification(
          id: NotificationIds.reEngagement14days,
          title: 'ICFES Leveling',
          body: '⚰️ [SISTEMA] Tus habilidades se desvanecen en la oscuridad. Vuelve antes de que sea tarde.',
          scheduledTime: time14days,
          channelId: NotificationChannels.reEngagement,
          payload: 're_engagement_14days',
        );
      }
    }

    debugPrint('NotificationService: Re-engagement notifications scheduled');
  }

  /// Cancel all re-engagement notifications
  Future<void> cancelReEngagementNotifications() async {
    await _localNotifications.cancel(NotificationIds.reEngagement3days);
    await _localNotifications.cancel(NotificationIds.reEngagement7days);
    await _localNotifications.cancel(NotificationIds.reEngagement14days);
  }

  // ============================================================
  // DAILY QUEST NOTIFICATIONS
  // ============================================================

  /// Schedule daily quest reminder notifications
  /// Called at app start or when daily quests refresh
  Future<void> scheduleDailyQuestReminders({int completedMissions = 0, int totalMissions = 3}) async {
    if (!_isInitialized || !notificationsEnabled || !dailyQuestNotificationsEnabled) return;

    // Cancel existing daily quest reminders
    await cancelDailyQuestReminders();

    // Track scheduling event
    _trackNotificationEvent('daily_quest_scheduled', {
      'completed': completedMissions,
      'total': totalMissions,
    });

    // If all missions completed, don't schedule reminders
    if (completedMissions >= totalMissions) {
      debugPrint('NotificationService: All daily quests completed, skipping reminders');
      return;
    }

    final remainingMissions = totalMissions - completedMissions;

    // 8:00 AM - Morning motivation
    final timeMorning = _scheduler.getNextScheduledTime(8, 0);
    if (timeMorning != null && !_scheduler.isInQuietHours(timeMorning)) {
      await _scheduleNotification(
        id: NotificationIds.dailyQuestMorning,
        title: 'ICFES Leveling',
        body: '🌅 [MISIONES] Nuevas misiones diarias disponibles. $remainingMissions misiones te esperan, Cazador.',
        scheduledTime: timeMorning,
        channelId: NotificationChannels.dailyQuest,
        payload: 'daily_quest_morning',
      );
    }

    // 2:00 PM - Afternoon reminder
    final timeAfternoon = _scheduler.getNextScheduledTime(14, 0);
    if (timeAfternoon != null && !_scheduler.isInQuietHours(timeAfternoon)) {
      await _scheduleNotification(
        id: NotificationIds.dailyQuestAfternoon,
        title: 'ICFES Leveling',
        body: '⚔️ [MISIONES] $remainingMissions misiones sin completar. Cada mision otorga Gold y XP.',
        scheduledTime: timeAfternoon,
        channelId: NotificationChannels.dailyQuest,
        payload: 'daily_quest_afternoon',
      );
    }

    // 8:00 PM - Evening urgency
    final timeEvening = _scheduler.getNextScheduledTime(20, 0);
    if (timeEvening != null && !_scheduler.isInQuietHours(timeEvening)) {
      await _scheduleNotification(
        id: NotificationIds.dailyQuestEvening,
        title: 'ICFES Leveling',
        body: '🌙 [ALERTA] $remainingMissions misiones expiran a medianoche. No pierdas tus recompensas.',
        scheduledTime: timeEvening,
        channelId: NotificationChannels.dailyQuest,
        payload: 'daily_quest_evening',
      );
    }

    debugPrint('NotificationService: Daily quest reminders scheduled ($remainingMissions remaining)');
  }

  /// Cancel all daily quest reminder notifications
  Future<void> cancelDailyQuestReminders() async {
    await _localNotifications.cancel(NotificationIds.dailyQuestMorning);
    await _localNotifications.cancel(NotificationIds.dailyQuestAfternoon);
    await _localNotifications.cancel(NotificationIds.dailyQuestEvening);
  }

  // ============================================================
  // DAILY GOAL NOTIFICATIONS
  // ============================================================

  /// Schedule daily goal reminder notifications
  Future<void> scheduleDailyGoalReminders({int currentXp = 0, int goalXp = 50}) async {
    if (!_isInitialized || !notificationsEnabled || !dailyGoalNotificationsEnabled) return;

    // Cancel existing daily goal reminders
    await cancelDailyGoalReminders();

    // If goal already achieved, don't schedule reminders
    if (currentXp >= goalXp) {
      debugPrint('NotificationService: Daily goal achieved, skipping reminders');
      return;
    }

    final remainingXp = goalXp - currentXp;
    final progressPercent = ((currentXp / goalXp) * 100).toInt();

    // 5:00 PM - Afternoon reminder
    final timeReminder = _scheduler.getNextScheduledTime(17, 0);
    if (timeReminder != null && !_scheduler.isInQuietHours(timeReminder)) {
      await _scheduleNotification(
        id: NotificationIds.dailyGoalReminder,
        title: 'ICFES Leveling',
        body: '🎯 [META] $progressPercent% completado. Faltan $remainingXp XP para tu meta diaria.',
        scheduledTime: timeReminder,
        channelId: NotificationChannels.dailyGoal,
        payload: 'daily_goal_reminder',
      );
    }

    // 10:30 PM - End of day urgency
    final timeEndOfDay = _scheduler.getNextScheduledTime(22, 30);
    if (timeEndOfDay != null) {
      await _scheduleNotification(
        id: NotificationIds.dailyGoalEndOfDay,
        title: 'ICFES Leveling',
        body: '⏰ [URGENTE] Solo faltan $remainingXp XP. Una sesion rapida y cumples tu meta.',
        scheduledTime: timeEndOfDay,
        channelId: NotificationChannels.dailyGoal,
        payload: 'daily_goal_end_of_day',
      );
    }

    debugPrint('NotificationService: Daily goal reminders scheduled ($remainingXp XP remaining)');
  }

  /// Cancel all daily goal reminder notifications
  Future<void> cancelDailyGoalReminders() async {
    await _localNotifications.cancel(NotificationIds.dailyGoalReminder);
    await _localNotifications.cancel(NotificationIds.dailyGoalEndOfDay);
  }

  // ============================================================
  // ACHIEVEMENT NOTIFICATIONS
  // ============================================================

  /// Show an achievement unlocked notification immediately
  Future<void> showAchievementNotification({
    required String achievementId,
    required String achievementName,
    String? description,
    int? xpReward,
  }) async {
    if (!_isInitialized || !notificationsEnabled || !achievementNotificationsEnabled) return;

    final xpText = xpReward != null ? ' +$xpReward XP' : '';
    final descText = description ?? 'Has desbloqueado un nuevo logro';

    await showNotification(
      title: '🏆 $achievementName',
      body: '$descText$xpText',
      channelId: NotificationChannels.achievement,
      payload: 'achievement_$achievementId',
      notificationId: NotificationIds.achievementBase + achievementId.hashCode.abs() % 1000,
    );

    // Track achievement notification
    _trackNotificationEvent('achievement_notification_shown', {
      'achievement_id': achievementId,
      'achievement_name': achievementName,
      'xp_reward': xpReward,
    });

    debugPrint('NotificationService: Achievement notification shown for $achievementName');
  }

  // ============================================================
  // GRANULAR NOTIFICATION SETTINGS
  // ============================================================

  /// Set streak notifications enabled
  Future<void> setStreakNotificationsEnabled(bool enabled) async {
    await _prefs.setBool(NotificationKeys.streakNotificationsEnabled, enabled);
    if (!enabled) {
      await cancelStreakReminders();
    }
    _trackNotificationEvent('notification_setting_changed', {
      'setting': 'streak',
      'enabled': enabled,
    });
  }

  /// Set daily quest notifications enabled
  Future<void> setDailyQuestNotificationsEnabled(bool enabled) async {
    await _prefs.setBool(NotificationKeys.dailyQuestNotificationsEnabled, enabled);
    if (!enabled) {
      await cancelDailyQuestReminders();
    }
    _trackNotificationEvent('notification_setting_changed', {
      'setting': 'daily_quest',
      'enabled': enabled,
    });
  }

  /// Set league notifications enabled
  Future<void> setLeagueNotificationsEnabled(bool enabled) async {
    await _prefs.setBool(NotificationKeys.leagueNotificationsEnabled, enabled);
    if (!enabled) {
      await _localNotifications.cancel(NotificationIds.leagueClosing);
    }
    _trackNotificationEvent('notification_setting_changed', {
      'setting': 'league',
      'enabled': enabled,
    });
  }

  /// Set boss raid notifications enabled
  Future<void> setBossRaidNotificationsEnabled(bool enabled) async {
    await _prefs.setBool(NotificationKeys.bossRaidNotificationsEnabled, enabled);
    if (!enabled) {
      await _localNotifications.cancel(NotificationIds.bossRaid);
    }
    _trackNotificationEvent('notification_setting_changed', {
      'setting': 'boss_raid',
      'enabled': enabled,
    });
  }

  /// Set achievement notifications enabled
  Future<void> setAchievementNotificationsEnabled(bool enabled) async {
    await _prefs.setBool(NotificationKeys.achievementNotificationsEnabled, enabled);
    _trackNotificationEvent('notification_setting_changed', {
      'setting': 'achievement',
      'enabled': enabled,
    });
  }

  /// Set daily goal notifications enabled
  Future<void> setDailyGoalNotificationsEnabled(bool enabled) async {
    await _prefs.setBool(NotificationKeys.dailyGoalNotificationsEnabled, enabled);
    if (!enabled) {
      await cancelDailyGoalReminders();
    }
    _trackNotificationEvent('notification_setting_changed', {
      'setting': 'daily_goal',
      'enabled': enabled,
    });
  }

  // ============================================================
  // ANALYTICS TRACKING
  // ============================================================

  /// Track when a notification is scheduled
  void trackNotificationScheduled(String notificationType, {Map<String, dynamic>? extras}) {
    _trackNotificationEvent('notification_scheduled', {
      'type': notificationType,
      ...?extras,
    });
  }

  /// Track when a notification is shown
  void trackNotificationShown(String notificationType, {Map<String, dynamic>? extras}) {
    _trackNotificationEvent('notification_shown', {
      'type': notificationType,
      ...?extras,
    });
  }

  /// Track when a notification is dismissed
  void trackNotificationDismissed(String notificationType, {Map<String, dynamic>? extras}) {
    _trackNotificationEvent('notification_dismissed', {
      'type': notificationType,
      ...?extras,
    });
  }

  /// Schedule a notification at a specific time
  Future<void> _scheduleNotification({
    required int id,
    required String title,
    required String body,
    required tz.TZDateTime scheduledTime,
    required String channelId,
    String? payload,
  }) async {
    final androidDetails = AndroidNotificationDetails(
      channelId,
      _getChannelName(channelId),
      channelDescription: _getChannelDescription(channelId),
      importance: Importance.high,
      priority: Priority.high,
      showWhen: true,
    );

    const iosDetails = DarwinNotificationDetails(
      presentAlert: true,
      presentBadge: true,
      presentSound: true,
    );

    final details = NotificationDetails(
      android: androidDetails,
      iOS: iosDetails,
    );

    await _localNotifications.zonedSchedule(
      id,
      title,
      body,
      scheduledTime,
      details,
      androidScheduleMode: AndroidScheduleMode.exactAllowWhileIdle,
      uiLocalNotificationDateInterpretation:
          UILocalNotificationDateInterpretation.absoluteTime,
      payload: payload,
    );
  }

  /// Enable or disable notifications
  Future<void> setNotificationsEnabled(bool enabled) async {
    await _prefs.setBool(NotificationKeys.notificationsEnabled, enabled);

    if (!enabled) {
      // Cancel all scheduled notifications
      await _localNotifications.cancelAll();
    }
  }

  /// Cancel all notifications
  Future<void> cancelAllNotifications() async {
    await _localNotifications.cancelAll();
  }

  /// Get pending notifications (for debugging)
  Future<List<PendingNotificationRequest>> getPendingNotifications() async {
    return await _localNotifications.pendingNotificationRequests();
  }

  /// Get channel name by ID
  String _getChannelName(String channelId) {
    switch (channelId) {
      case NotificationChannels.streakReminder:
        return 'Recordatorios de Racha';
      case NotificationChannels.leagueReminder:
        return 'Recordatorios de Liga';
      case NotificationChannels.bossRaidReminder:
        return 'Boss Raid';
      case NotificationChannels.reEngagement:
        return 'Vuelve a Jugar';
      case NotificationChannels.dailyQuest:
        return 'Misiones Diarias';
      case NotificationChannels.achievement:
        return 'Logros';
      case NotificationChannels.dailyGoal:
        return 'Meta Diaria';
      default:
        return 'General';
    }
  }

  /// Get channel description by ID
  String _getChannelDescription(String channelId) {
    switch (channelId) {
      case NotificationChannels.streakReminder:
        return 'Notificaciones para proteger tu racha diaria';
      case NotificationChannels.leagueReminder:
        return 'Notificaciones sobre el cierre de la liga semanal';
      case NotificationChannels.bossRaidReminder:
        return 'Notificaciones del evento Boss Raid semanal';
      case NotificationChannels.reEngagement:
        return 'Recordatorios para usuarios inactivos';
      case NotificationChannels.dailyQuest:
        return 'Recordatorios para completar misiones diarias';
      case NotificationChannels.achievement:
        return 'Notificaciones de logros desbloqueados';
      case NotificationChannels.dailyGoal:
        return 'Recordatorios de meta diaria de XP';
      default:
        return 'Notificaciones generales de la aplicacion';
    }
  }
}

/// Provider for NotificationService
final notificationServiceProvider = Provider<NotificationService>((ref) {
  throw UnimplementedError('Must be overridden in main.dart with SharedPreferences');
});

/// Provider for initializing notification service
final notificationServiceInitProvider = FutureProvider<NotificationService>((ref) async {
  final prefs = ref.watch(sharedPreferencesProvider);
  FirebaseMessaging? messaging;

  try {
    messaging = FirebaseMessaging.instance;
  } catch (e) {
    debugPrint('Firebase Messaging not available');
  }

  final service = NotificationService(
    prefs: prefs,
    firebaseMessaging: messaging,
  );

  await service.initialize();
  return service;
});
