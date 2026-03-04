import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

class AppTheme {
  // Colores principales del juego
  static const Color primaryPurple = Color(0xFF6366F1);  // Indigo
  static const Color secondaryGold = Color(0xFFFFD700);  // Gold para rewards
  static const Color accentCyan = Color(0xFF22D3EE);     // Cyan para XP
  static const Color dangerRed = Color(0xFFEF4444);      // Rojo para corazones
  static const Color successGreen = Color(0xFF22C55E);   // Verde para correcto
  static const Color warningOrange = Color(0xFFF97316); // Naranja para streaks

  // Colores de fondo
  static const Color bgDark = Color(0xFF0F172A);        // Slate 900
  static const Color bgCard = Color(0xFF1E293B);        // Slate 800
  static const Color bgElevated = Color(0xFF334155);    // Slate 700

  // Colores de texto
  static const Color textPrimary = Color(0xFFF8FAFC);   // Slate 50
  static const Color textSecondary = Color(0xFF94A3B8); // Slate 400
  static const Color textMuted = Color(0xFF64748B);     // Slate 500

  // Colores por materia ICFES
  static const Map<String, Color> subjectColors = {
    'matematicas': Color(0xFF3B82F6),      // Blue
    'lenguaje': Color(0xFFA855F7),         // Purple
    'ciencias_naturales': Color(0xFF22C55E), // Green
    'ciencias_sociales': Color(0xFFF97316),  // Orange
    'ingles': Color(0xFFEC4899),           // Pink
  };

  // Colores de liga
  static const Map<String, Color> leagueColors = {
    'bronce': Color(0xFFCD7F32),
    'plata': Color(0xFFC0C0C0),
    'oro': Color(0xFFFFD700),
    'diamante': Color(0xFFB9F2FF),
    'obsidiana': Color(0xFF1A1A2E),
  };

  static ThemeData get darkTheme {
    return ThemeData(
      useMaterial3: true,
      brightness: Brightness.dark,
      scaffoldBackgroundColor: bgDark,
      primaryColor: primaryPurple,
      colorScheme: const ColorScheme.dark(
        primary: primaryPurple,
        secondary: secondaryGold,
        surface: bgDark,
        error: dangerRed,
      ),
      textTheme: GoogleFonts.interTextTheme(
        const TextTheme(
          displayLarge: TextStyle(
            fontSize: 32,
            fontWeight: FontWeight.bold,
            color: textPrimary,
          ),
          displayMedium: TextStyle(
            fontSize: 24,
            fontWeight: FontWeight.bold,
            color: textPrimary,
          ),
          titleLarge: TextStyle(
            fontSize: 20,
            fontWeight: FontWeight.w600,
            color: textPrimary,
          ),
          titleMedium: TextStyle(
            fontSize: 16,
            fontWeight: FontWeight.w600,
            color: textPrimary,
          ),
          bodyLarge: TextStyle(
            fontSize: 16,
            color: textPrimary,
          ),
          bodyMedium: TextStyle(
            fontSize: 14,
            color: textSecondary,
          ),
          labelLarge: TextStyle(
            fontSize: 14,
            fontWeight: FontWeight.w600,
            color: textPrimary,
          ),
        ),
      ),
      cardTheme: CardThemeData(
        color: bgCard,
        elevation: 4,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(16),
        ),
      ),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: primaryPurple,
          foregroundColor: textPrimary,
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(12),
          ),
          textStyle: const TextStyle(
            fontSize: 16,
            fontWeight: FontWeight.w600,
          ),
        ),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: bgCard,
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: BorderSide.none,
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: primaryPurple, width: 2),
        ),
        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
      ),
      appBarTheme: const AppBarTheme(
        backgroundColor: bgDark,
        elevation: 0,
        centerTitle: true,
        iconTheme: IconThemeData(color: textPrimary),
        titleTextStyle: TextStyle(
          fontSize: 18,
          fontWeight: FontWeight.w600,
          color: textPrimary,
        ),
      ),
      bottomNavigationBarTheme: const BottomNavigationBarThemeData(
        backgroundColor: bgCard,
        selectedItemColor: primaryPurple,
        unselectedItemColor: textMuted,
        type: BottomNavigationBarType.fixed,
        elevation: 8,
      ),
    );
  }
}
