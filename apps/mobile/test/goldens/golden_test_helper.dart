import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:hive/hive.dart';
import 'package:mockito/mockito.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:google_fonts/google_fonts.dart';

import 'package:icfes_mobile/core/network/api_client.dart';
import 'package:icfes_mobile/core/config/app_theme.dart' show AppTheme;
import 'package:icfes_mobile/core/config/animation_config.dart';
import 'package:icfes_mobile/core/constants/api_constants.dart';
import 'package:icfes_mobile/core/auth/domain/entities/user.dart';
import 'package:icfes_mobile/core/storage/question_cache.dart';
import 'package:icfes_mobile/core/sync/connectivity_monitor.dart'
    show ConnectivityMonitor, connectivityMonitorProvider, connectivityProvider;
import 'package:icfes_mobile/core/providers/storage_providers.dart';
import 'package:icfes_mobile/core/services/onboarding_service.dart';
import 'package:icfes_mobile/core/services/notification_service.dart';
import 'package:icfes_mobile/features/auth/domain/repositories/auth_repository.dart';
import 'package:icfes_mobile/features/auth/presentation/providers/auth_provider.dart';

import '../mocks/mock_providers.dart';

// =============================================================================
// Mock Classes
// =============================================================================

/// Auth repository that returns a pre-configured user
class MockAuthRepository implements AuthRepository {
  final User? _user;

  MockAuthRepository({User? user}) : _user = user;

  @override
  Future<User?> getCurrentUser() async => _user;

  @override
  Future<User> login(String email, String password) async {
    return _user ?? createTestUser();
  }

  @override
  Future<User> register(String email, String password, String name) async {
    return createTestUser(email: email, name: name);
  }

  @override
  Future<void> logout() async {}

  @override
  Future<String?> getAccessToken() async => 'mock-token';

  @override
  Future<void> refreshToken() async {}
}

/// QuestionCache mock that does nothing
class MockQuestionCache extends Mock implements QuestionCache {
  @override
  Future<void> warmUp(ApiClient apiClient) async {}

  @override
  Future<void> init() async {}
}

/// ConnectivityMonitor that always reports online
class MockConnectivityMonitor extends ConnectivityMonitor {
  @override
  Stream<bool> get onConnectivityChanged => Stream.value(true);

  @override
  Future<bool> get isOnline async => true;
}

// =============================================================================
// Golden Test Size
// =============================================================================

/// Pixel 5 viewport size for consistent golden screenshots
const goldenSize = Size(412, 892);

// =============================================================================
// API Mock Setup
// =============================================================================

/// Configures FakeApiClient with mock responses for all commonly fetched endpoints.
void setupAllGoldenMocks(FakeApiClient fakeApiClient) {
  // Auth
  fakeApiClient.setMockResponse(ApiConstants.authMe, {
    'id': 'user-1',
    'email': 'hunter@icfes.co',
    'name': 'Hunter Pro',
    'xp': 2500,
    'daily_xp': 120,
    'streak': 7,
    'hearts': 5,
    'level': 5,
    'rank': 'D',
  }, statusCode: 200);

  // Hearts
  fakeApiClient.setMockResponse(ApiConstants.heartsStatus, {
    'current': 5,
    'max': 5,
  }, statusCode: 200);

  // Streak
  fakeApiClient.setMockResponse(ApiConstants.streakStatus, {
    'current_streak': 7,
    'longest_streak': 14,
    'multiplier': 1.2,
    'freezes_available': 1,
    'is_at_risk': false,
    'can_repair': false,
    'previous_streak': 7,
  }, statusCode: 200);

  // User cached profile
  fakeApiClient.setMockResponse('/users/cached/profile/me', {
    'questions_answered': 250,
    'correct_answers': 200,
    'experience': 2500,
    'streak_days': 7,
  }, statusCode: 200);

  // Study plan
  fakeApiClient.setMockResponse(ApiConstants.studyPlanCurrent, {
    'plan': null,
    'hasPlan': false,
    'message': 'No plan',
  }, statusCode: 200);

  // Boss raid
  fakeApiClient.setMockResponse(ApiConstants.bossRaidStatus, {
    'isActive': false,
    'currentBoss': null,
  }, statusCode: 200);

  // Leaderboard
  fakeApiClient.setMockResponse(ApiConstants.leaderboard, {
    'leaderboard': <Map<String, dynamic>>[
      {'user_id': 'u1', 'name': 'Dragon Slayer', 'xp': 5000, 'rank': 1, 'zone': 'promotion', 'is_me': false},
      {'user_id': 'u2', 'name': 'Shadow Mage', 'xp': 4200, 'rank': 2, 'zone': 'promotion', 'is_me': false},
      {'user_id': 'user-1', 'name': 'Hunter Pro', 'xp': 2500, 'rank': 3, 'zone': 'safe', 'is_me': true},
      {'user_id': 'u4', 'name': 'Ice Warrior', 'xp': 1800, 'rank': 4, 'zone': 'safe', 'is_me': false},
      {'user_id': 'u5', 'name': 'Fire Archer', 'xp': 1200, 'rank': 5, 'zone': 'demotion', 'is_me': false},
    ],
    'my_rank': 3,
    'my_xp': 2500,
    'my_zone': 'safe',
    'total_participants': 25,
  }, statusCode: 200);

  // Economy
  fakeApiClient.setMockResponse(ApiConstants.economyBalance, {
    'gold': 1500,
    'gems': 25,
    'crystals': 0,
  }, statusCode: 200);

  // Shop
  fakeApiClient.setMockResponse(ApiConstants.economyShop, {
    'items': <Map<String, dynamic>>[
      {'id': 'streak_freeze', 'name': 'Streak Freeze', 'description': 'Protege tu racha por 1 dia', 'price_gold': 200, 'category': 'utility'},
      {'id': 'xp_boost', 'name': 'XP Boost x2', 'description': 'Duplica XP por 30 min', 'price_gold': 500, 'category': 'boost', 'is_power_up': true, 'duration': 1800},
      {'id': 'heart_refill', 'name': 'Recarga Corazones', 'description': 'Restaura todos los corazones', 'price_gold': 150, 'category': 'utility'},
      {'id': 'rare_avatar', 'name': 'Avatar Legendario', 'description': 'Marco dorado exclusivo', 'price_gold': 1000, 'category': 'cosmetic'},
    ],
  }, statusCode: 200);

  // Inventory
  fakeApiClient.setMockResponse(ApiConstants.economyInventory, {
    'items': <Map<String, dynamic>>[],
  }, statusCode: 200);

  // Achievements
  fakeApiClient.setMockResponse(ApiConstants.achievements, {
    'achievements': <Map<String, dynamic>>[
      {'id': 'first_answer', 'name': 'Primera Respuesta', 'description': 'Responde tu primera pregunta', 'icon': 'star', 'category': 'general', 'rarity': 'common', 'requirement': {'type': 'questions_answered', 'target_value': 1}, 'unlocked_at': '2026-02-15T10:00:00Z', 'progress': 1.0},
      {'id': 'streak_7', 'name': 'Racha Semanal', 'description': 'Mantén una racha de 7 días', 'icon': 'fire', 'category': 'streak', 'rarity': 'rare', 'requirement': {'type': 'streak_days', 'target_value': 7}, 'unlocked_at': '2026-02-18T10:00:00Z', 'progress': 1.0},
      {'id': 'level_5', 'name': 'Nivel 5', 'description': 'Alcanza el nivel 5', 'icon': 'trophy', 'category': 'practice', 'rarity': 'rare', 'requirement': {'type': 'reach_level', 'target_value': 5}, 'unlocked_at': '2026-02-19T10:00:00Z', 'progress': 1.0},
      {'id': 'streak_30', 'name': 'Racha Mensual', 'description': 'Mantén una racha de 30 días', 'icon': 'fire', 'category': 'streak', 'rarity': 'epic', 'requirement': {'type': 'streak_days', 'target_value': 30}, 'progress': 0.23},
      {'id': 'level_10', 'name': 'Nivel 10', 'description': 'Alcanza el nivel 10', 'icon': 'trophy', 'category': 'practice', 'rarity': 'epic', 'requirement': {'type': 'reach_level', 'target_value': 10}, 'progress': 0.5},
    ],
    'total_unlocked': 3,
    'total_available': 5,
  }, statusCode: 200);

  // Achievements recent
  fakeApiClient.setMockResponse(ApiConstants.achievementsRecent, {
    'achievements': <Map<String, dynamic>>[],
  }, statusCode: 200);

  // Leagues current
  fakeApiClient.setMockResponse(ApiConstants.leaguesCurrent, {
    'name': 'LIGA DE BRONCE',
    'time_left': '2d 14h 22m',
    'position': 3,
  }, statusCode: 200);

  // Practice questions
  fakeApiClient.setMockResponse(ApiConstants.nextQuestion, {
    'id': 'q1',
    'subject_id': 'matematicas',
    'topic': 'Álgebra',
    'difficulty': 3,
    'text': '¿Cuál es el valor de x en 2x + 5 = 15?',
    'options': [
      {'id': 'a', 'text': '3'},
      {'id': 'b', 'text': '5'},
      {'id': 'c', 'text': '7'},
      {'id': 'd', 'text': '10'},
    ],
    'correct_option_id': 'b',
  }, statusCode: 200);

  // Batch questions
  fakeApiClient.setMockResponse(ApiConstants.batchQuestions, {
    'questions': <Map<String, dynamic>>[],
  }, statusCode: 200);

  // Notifications
  fakeApiClient.setMockResponse(ApiConstants.notificationsRegister, {
    'success': true,
  }, statusCode: 200);

  // Video tracking
  fakeApiClient.setMockResponse(ApiConstants.videoTracking, {
    'video_id': 'v1',
    'progress_percent': 0,
    'is_completed': false,
    'last_position_seconds': 0,
  }, statusCode: 200);

  // Mastery
  fakeApiClient.setMockResponse(ApiConstants.masteryTopics, {
    'topics': <Map<String, dynamic>>[],
  }, statusCode: 200);

  // Power-ups
  fakeApiClient.setMockResponse(ApiConstants.storePowerUps, {
    'power_ups': <Map<String, dynamic>>[],
  }, statusCode: 200);
  fakeApiClient.setMockResponse(ApiConstants.storePowerUpsActive, {
    'active': <Map<String, dynamic>>[],
  }, statusCode: 200);
}

// =============================================================================
// Golden Theme (same as AppTheme.darkTheme but without GoogleFonts network fetch)
// =============================================================================

/// ThemeData identical to AppTheme.darkTheme but using the default font
/// instead of GoogleFonts.inter to avoid network requests in tests.
ThemeData get goldenDarkTheme {
  const textPrimary = Color(0xFFF8FAFC);
  const textSecondary = Color(0xFF94A3B8);
  const textMuted = Color(0xFF64748B);

  return ThemeData(
    useMaterial3: true,
    brightness: Brightness.dark,
    scaffoldBackgroundColor: AppTheme.bgDark,
    primaryColor: AppTheme.primaryPurple,
    colorScheme: const ColorScheme.dark(
      primary: AppTheme.primaryPurple,
      secondary: AppTheme.secondaryGold,
      surface: AppTheme.bgDark,
      error: AppTheme.dangerRed,
    ),
    // Use the same TextTheme styles but without GoogleFonts wrapper
    textTheme: const TextTheme(
      displayLarge: TextStyle(fontSize: 32, fontWeight: FontWeight.bold, color: textPrimary),
      displayMedium: TextStyle(fontSize: 24, fontWeight: FontWeight.bold, color: textPrimary),
      titleLarge: TextStyle(fontSize: 20, fontWeight: FontWeight.w600, color: textPrimary),
      titleMedium: TextStyle(fontSize: 16, fontWeight: FontWeight.w600, color: textPrimary),
      bodyLarge: TextStyle(fontSize: 16, color: textPrimary),
      bodyMedium: TextStyle(fontSize: 14, color: textSecondary),
      labelLarge: TextStyle(fontSize: 14, fontWeight: FontWeight.w600, color: textPrimary),
    ),
    cardTheme: CardThemeData(
      color: AppTheme.bgCard,
      elevation: 4,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
    ),
    elevatedButtonTheme: ElevatedButtonThemeData(
      style: ElevatedButton.styleFrom(
        backgroundColor: AppTheme.primaryPurple,
        foregroundColor: textPrimary,
        padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
        textStyle: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
      ),
    ),
    inputDecorationTheme: InputDecorationTheme(
      filled: true,
      fillColor: AppTheme.bgCard,
      border: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: BorderSide.none),
      focusedBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: const BorderSide(color: AppTheme.primaryPurple, width: 2)),
      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
    ),
    appBarTheme: const AppBarTheme(
      backgroundColor: AppTheme.bgDark,
      elevation: 0,
      centerTitle: true,
      iconTheme: IconThemeData(color: textPrimary),
      titleTextStyle: TextStyle(fontSize: 18, fontWeight: FontWeight.w600, color: textPrimary),
    ),
    bottomNavigationBarTheme: const BottomNavigationBarThemeData(
      backgroundColor: AppTheme.bgCard,
      selectedItemColor: AppTheme.primaryPurple,
      unselectedItemColor: textMuted,
      type: BottomNavigationBarType.fixed,
      elevation: 8,
    ),
  );
}

// =============================================================================
// Widget Builder
// =============================================================================

/// Wraps [child] in a ProviderScope + MaterialApp with the dark theme at golden size.
///
/// [overrides] are additional provider overrides merged with the defaults.
/// By default, overrides: apiClientProvider, authRepositoryProvider,
/// questionCacheProvider, connectivityMonitorProvider, sharedPreferencesProvider.
Widget buildGoldenApp(
  Widget child, {
  FakeApiClient? fakeApiClient,
  User? testUser,
  List<Override> extraOverrides = const [],
}) {
  final apiClient = fakeApiClient ?? FakeApiClient();
  if (fakeApiClient == null) {
    setupAllGoldenMocks(apiClient);
  }

  final user = testUser ?? createTestUser(
    name: 'Hunter Pro',
    level: 5,
    xp: 2500,
    rank: 'D',
    hearts: 5,
    currentStreak: 7,
    diagnosticCompleted: true,
  );

  return ProviderScope(
    overrides: [
      apiClientProvider.overrideWithValue(apiClient),
      authRepositoryProvider.overrideWithValue(MockAuthRepository(user: user)),
      questionCacheProvider.overrideWithValue(MockQuestionCache()),
      connectivityMonitorProvider.overrideWithValue(MockConnectivityMonitor()),
      // Override connectivityProvider (StreamProvider) to avoid platform channel errors
      connectivityProvider.overrideWith((ref) => Stream.value(true)),
      ...extraOverrides,
    ],
    child: MaterialApp(
      theme: goldenDarkTheme,
      debugShowCheckedModeBanner: false,
      home: child,
    ),
  );
}

// =============================================================================
// Helpers
// =============================================================================

/// Pumps the widget 10 times with 100ms intervals to settle animations
Future<void> pumpAndWait(WidgetTester tester) async {
  for (int i = 0; i < 10; i++) {
    await tester.pump(const Duration(milliseconds: 100));
  }
}

/// Common setUp for all golden tests: disable animations, init Hive, disable Google Fonts network
Future<void> goldenSetUp() async {
  AnimationConfig.infiniteAnimationsEnabled = false;
  Animate.restartOnHotReload = false;
  // Prevent google_fonts from trying to fetch fonts over network in tests
  GoogleFonts.config.allowRuntimeFetching = false;

  // Suppress RenderFlex overflow errors (cosmetic issues, not test failures)
  _originalOnError = FlutterError.onError;
  FlutterError.onError = _suppressOverflowErrors;

  // Mock audioplayers platform channels (method + event channels)
  const globalChannel = MethodChannel('xyz.luan/audioplayers.global');
  const playerChannel = MethodChannel('xyz.luan/audioplayers');
  TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
      .setMockMethodCallHandler(globalChannel, (call) async => 1);
  TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
      .setMockMethodCallHandler(playerChannel, (call) async => 1);

  // Mock audioplayers event channels (stream-based)
  // Global events channel
  const globalEventsChannel = EventChannel('xyz.luan/audioplayers.global/events');
  TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
      .setMockStreamHandler(globalEventsChannel, MockStreamHandler.inline(
        onListen: (args, sink) {},
        onCancel: (args) {},
      ));
  // Per-player event channels (audioplayers creates dynamic channels with player IDs)
  // Use allMessagesHandler to intercept all unhandled audioplayer channels
  final messenger = TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger;
  messenger.allMessagesHandler = (channel, handler, message) async {
    // For audioplayer per-player event channels, return empty success envelope
    if (channel.startsWith('xyz.luan/audioplayers/events/')) {
      return const StandardMethodCodec().encodeSuccessEnvelope(null);
    }
    // For path_provider_windows channels
    if (channel.startsWith('plugins.flutter.io/path_provider')) {
      return handler?.call(message);
    }
    // Delegate to registered handler or return null
    if (handler != null) {
      return handler(message);
    }
    return null;
  };

  // Mock path_provider platform channel (used by SoundService for temp dir)
  const pathProviderChannel = MethodChannel('plugins.flutter.io/path_provider');
  TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
      .setMockMethodCallHandler(pathProviderChannel, (call) async {
        if (call.method == 'getTemporaryDirectory') {
          return Directory.systemTemp.path;
        }
        if (call.method == 'getApplicationDocumentsDirectory') {
          return Directory.systemTemp.path;
        }
        return null;
      });

  SharedPreferences.setMockInitialValues({
    'has_completed_onboarding': true,
    'has_seen_value_prop': true,
    'onboarding_step': OnboardingStep.completed.index,
  });
  final tempDir = Directory.systemTemp.createTempSync('golden_test_');
  Hive.init(tempDir.path);
}

/// Common tearDown: re-enable animations, restore error handler
void goldenTearDown() {
  AnimationConfig.infiniteAnimationsEnabled = true;
  FlutterError.onError = _originalOnError;
  // Reset the allMessagesHandler to avoid leaking between test groups
  TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
      .allMessagesHandler = null;
}

void Function(FlutterErrorDetails)? _originalOnError;

/// Suppress overflow errors that are cosmetic and don't affect golden screenshots
void _suppressOverflowErrors(FlutterErrorDetails details) {
  final message = details.toString();
  // Suppress RenderFlex overflow errors — these are visual warnings, not test failures
  if (message.contains('overflowed by') && message.contains('RenderFlex')) {
    return;
  }
  // Suppress audioplayer MissingPluginException errors (dynamic event channels)
  if (message.contains('MissingPluginException') && message.contains('audioplayers')) {
    return;
  }
  // Forward all other errors to the original handler
  _originalOnError?.call(details);
}

