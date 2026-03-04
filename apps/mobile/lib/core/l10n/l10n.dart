import 'package:flutter/material.dart';

/// Localization configuration and helper class.
/// Simplified version for testing without generated l10n.
class L10n {
  L10n._();

  /// List of supported locales in the app.
  static const List<Locale> supportedLocales = [
    Locale('es'), // Spanish - Primary
    Locale('en'), // English
  ];

  /// Check if a locale is supported by the app.
  static bool isSupported(Locale locale) {
    return supportedLocales.any((l) => l.languageCode == locale.languageCode);
  }

  /// Get the display name for a locale.
  static String getLocaleName(Locale locale) {
    switch (locale.languageCode) {
      case 'es':
        return 'Espanol';
      case 'en':
        return 'English';
      default:
        return locale.languageCode;
    }
  }

  /// Get the flag emoji for a locale.
  static String getLocaleFlag(Locale locale) {
    switch (locale.languageCode) {
      case 'es':
        return '🇨🇴';
      case 'en':
        return '🇺🇸';
      default:
        return '🌐';
    }
  }
}

/// Extension on BuildContext for convenient locale access.
extension L10nExtension on BuildContext {
  /// Get the current locale.
  Locale get locale => Localizations.localeOf(this);

  /// Check if current locale is Spanish.
  bool get isSpanish => locale.languageCode == 'es';

  /// Check if current locale is English.
  bool get isEnglish => locale.languageCode == 'en';
}
