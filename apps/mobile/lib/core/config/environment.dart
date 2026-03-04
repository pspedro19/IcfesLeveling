import 'package:flutter/foundation.dart';
import 'package:flutter_dotenv/flutter_dotenv.dart';

/// Environment configuration for the app.
///
/// Uses a hybrid approach:
/// - In debug mode: loads from .env file (easier development switching)
/// - In release mode: uses compile-time constants (more secure)
class Environment {
  static bool _initialized = false;

  /// Initialize environment configuration
  /// Call this in main() before runApp()
  static Future<void> initialize() async {
    if (_initialized) return;

    if (kDebugMode) {
      try {
        await dotenv.load(fileName: '.env');
      } catch (e) {
        // .env file not found - will use defaults
        debugPrint('Warning: .env file not found, using defaults');
      }
    }

    _initialized = true;
  }

  /// Get a value from environment
  /// Note: In release mode, use specific getters (apiUrl, sentryDsn, etc.)
  /// which can use compile-time String.fromEnvironment with literal keys.
  /// This method only works fully in debug mode with dotenv.
  static String get(String key, {String defaultValue = ''}) {
    if (kDebugMode && dotenv.isInitialized) {
      return dotenv.get(key, fallback: defaultValue);
    }
    // In release mode, return default since we can't use String.fromEnvironment
    // with a dynamic key. Use specific typed getters instead.
    return defaultValue;
  }

  /// Get bool value from environment
  static bool getBool(String key, {bool defaultValue = false}) {
    final value = get(key, defaultValue: defaultValue.toString()).toLowerCase();
    return value == 'true' || value == '1' || value == 'yes';
  }

  // ============================================
  // Strongly-typed environment accessors
  // ============================================

  /// API base URL
  static String get apiUrl {
    // First check runtime dotenv, then compile-time, then default
    if (kDebugMode && dotenv.isInitialized) {
      final dotenvValue = dotenv.get('API_URL', fallback: '');
      if (dotenvValue.isNotEmpty) return dotenvValue;
    }

    const compileTime = String.fromEnvironment('API_URL');
    if (compileTime.isNotEmpty) return compileTime;

    return 'http://localhost:4000/api/v1';
  }

  /// Sentry DSN for crash reporting
  static String get sentryDsn {
    if (kDebugMode && dotenv.isInitialized) {
      final dotenvValue = dotenv.get('SENTRY_DSN', fallback: '');
      if (dotenvValue.isNotEmpty) return dotenvValue;
    }

    const compileTime = String.fromEnvironment('SENTRY_DSN');
    return compileTime;
  }

  /// Current environment (development, staging, production)
  static String get currentEnv {
    if (kDebugMode && dotenv.isInitialized) {
      final dotenvValue = dotenv.get('ENV', fallback: '');
      if (dotenvValue.isNotEmpty) return dotenvValue;
    }

    const compileTime = String.fromEnvironment('ENV');
    if (compileTime.isNotEmpty) return compileTime;

    return kReleaseMode ? 'production' : 'development';
  }

  /// Whether we're in production
  static bool get isProduction => currentEnv == 'production';

  /// Whether we're in development
  static bool get isDevelopment => currentEnv == 'development';

  /// Whether analytics are enabled
  static bool get analyticsEnabled {
    if (isProduction) return true; // Always on in production
    return getBool('ENABLE_ANALYTICS', defaultValue: false);
  }

  /// Whether crash reporting is enabled
  static bool get crashReportingEnabled {
    return sentryDsn.isNotEmpty;
  }

  /// Whether debug mode is enabled
  static bool get debugMode {
    if (kReleaseMode) return false; // Never in release
    return getBool('DEBUG_MODE', defaultValue: true);
  }
}
