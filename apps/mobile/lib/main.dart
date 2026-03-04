import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:hive_flutter/hive_flutter.dart';
import 'package:sentry_flutter/sentry_flutter.dart';
import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'core/config/app_theme.dart';
import 'core/config/routes.dart';
import 'core/config/environment.dart';
import 'core/network/api_client.dart';
import 'core/services/onboarding_service.dart';
import 'core/services/notification_service.dart';
import 'core/services/admob_service.dart';
import 'core/services/analytics_service.dart';
import 'core/sync/question_cache_service.dart';

/// Background message handler for Firebase Cloud Messaging
/// Must be a top-level function (not a class method)
@pragma('vm:entry-point')
Future<void> _firebaseMessagingBackgroundHandler(RemoteMessage message) async {
  // Initialize Firebase if needed (for background isolate)
  await Firebase.initializeApp();
  debugPrint('Handling background message: ${message.messageId}');
}

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // Initialize environment configuration (loads .env in debug mode)
  await Environment.initialize();

  // Initialize Hive for offline storage
  await Hive.initFlutter();

  // Initialize SharedPreferences for onboarding state
  final sharedPreferences = await SharedPreferences.getInstance();

  // Initialize Firebase for authentication (optional - skip if not configured)
  bool firebaseAvailable = false;
  try {
    await Firebase.initializeApp();
    firebaseAvailable = true;
    debugPrint('Firebase initialized successfully');
    // Initialize analytics after Firebase is ready
    AnalyticsService().initialize();
  } catch (e) {
    // Firebase not configured - social login will be disabled
    debugPrint('Firebase not configured - using email auth only');
  }

  // Initialize AdMob for rewarded ads (optional - skip if not configured)
  try {
    await AdMobService().initialize();
    debugPrint('AdMob initialized successfully');
  } catch (e) {
    debugPrint('AdMob init skipped: $e');
  }

  // Initialize NotificationService
  NotificationService? notificationService;
  try {
    FirebaseMessaging? messaging;
    if (firebaseAvailable) {
      messaging = FirebaseMessaging.instance;
      // Set up background message handler
      FirebaseMessaging.onBackgroundMessage(_firebaseMessagingBackgroundHandler);
    }
    notificationService = NotificationService(
      prefs: sharedPreferences,
      firebaseMessaging: messaging,
    );
    await notificationService.initialize();

    // Schedule weekly reminders on app start
    await notificationService.scheduleBossRaidReminder();
    await notificationService.scheduleLeagueReminder();

    debugPrint('NotificationService initialized successfully');
  } catch (e) {
    debugPrint('NotificationService initialization failed: $e');
  }

  // Initialize QuestionCacheService for offline question caching
  final questionCacheService = QuestionCacheService();
  try {
    await questionCacheService.init();
    debugPrint('QuestionCacheService initialized successfully');
  } catch (e) {
    debugPrint('QuestionCacheService initialization failed: $e');
  }

  // Create a ProviderContainer to manage our providers.
  final container = ProviderContainer(
    overrides: [
      // Override SharedPreferences provider with actual instance
      sharedPreferencesProvider.overrideWithValue(sharedPreferences),
      // Override NotificationService provider if available
      if (notificationService != null)
        notificationServiceProvider.overrideWithValue(notificationService),
      // Override QuestionCacheService provider with initialized instance
      questionCacheServiceProvider.overrideWithValue(questionCacheService),
    ],
  );

  // Initialize the SyncManager
  container.read(syncManagerProvider);

  // Initialize Sentry for crash reporting (only if DSN is configured)
  if (Environment.crashReportingEnabled) {
    await SentryFlutter.init(
      (options) {
        options.dsn = Environment.sentryDsn;
        options.tracesSampleRate = 0.3; // 30% of transactions for performance
        options.environment = Environment.currentEnv;
      },
      appRunner: () => runApp(
        UncontrolledProviderScope(
          container: container,
          child: const IcfesApp(),
        ),
      ),
    );
  } else {
    // Run without Sentry in development
    runApp(
      UncontrolledProviderScope(
        container: container,
        child: const IcfesApp(),
      ),
    );
  }
}

class IcfesApp extends ConsumerWidget {
  const IcfesApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final router = ref.watch(routerProvider);

    return MaterialApp.router(
      title: 'ICFES Leveling',
      debugShowCheckedModeBanner: false,  // Hide debug banner for cleaner UI
      theme: AppTheme.darkTheme,  // Apply our custom theme
      routerConfig: router,       // Connect GoRouter

      // Internationalization support (simplified for testing)
      localizationsDelegates: const [
        GlobalMaterialLocalizations.delegate,
        GlobalWidgetsLocalizations.delegate,
        GlobalCupertinoLocalizations.delegate,
      ],
      supportedLocales: const [Locale('es'), Locale('en')],
      locale: const Locale('es'), // Default to Spanish
    );
  }
}
