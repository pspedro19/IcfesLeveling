/// App strings for the application.
///
/// This class provides static string constants used throughout the app.
/// For now using hardcoded Spanish strings until l10n is fully configured.
class AppStrings {
  AppStrings._();

  // ==========================================================================
  // STATIC STRINGS (for backward compatibility - use context.l10n instead)
  // ==========================================================================

  // App
  static const String appName = 'ICFES Leveling';

  // Home
  static const String welcomeBack = 'Bienvenido de vuelta';
  static const String dailyGoal = 'Meta Diaria';
  static const String continueStudying = 'Continuar Estudiando';

  // Practice
  static const String practice = 'Practica';
  static const String startPractice = 'Iniciar Practica';

  // Streak
  static const String streak = 'Racha';
  static const String streakLost = 'Racha Perdida';

  // Hearts
  static const String hearts = 'Vidas';
  static const String noHearts = 'Sin Vidas';

  // General
  static const String loading = 'Cargando...';
  static const String error = 'Error';
  static const String retry = 'Reintentar';
  static const String cancel = 'Cancelar';
  static const String confirm = 'Confirmar';
  static const String save = 'Guardar';
  static const String delete = 'Eliminar';

  // Feedback
  static const String excellent = 'Excelente!';
  static const String incorrect = 'Incorrecto';
  static const String correctWas = 'La respuesta correcta era: {answer}';
  static const String continueText = 'Continuar';

  // Results
  static const String sessionFinished = 'Sesion Terminada';
  static const String correctAnswers = 'Respuestas Correctas';
  static const String xpGained = 'XP Ganado';
  static const String maxCombo = 'Combo Maximo';
  static const String precision = 'Precision';
  static const String finish = 'Finalizar';

  // Additional getters (for backward compatibility)
  static String get welcome => 'Bienvenido!';
  static String get readyToLevelUp => 'Listo para subir de nivel?';
  static String get loadingQuestions => 'Cargando preguntas...';
  static String get close => 'Cerrar';
  static String get questionProgress => 'Pregunta {current} de {total}';
  static String get check => 'Verificar';
  static String get count => 'Cantidad';
  static String get selectSubject => 'Selecciona una materia';
  static String get startPracticeAction => 'Iniciar practica';
  static String get questionsCount => 'preguntas';
  static String get difficulty => 'Dificultad';

  // Settings
  static String get settings => 'Configuracion';
  static String get logout => 'Cerrar Sesion';
  static String get profile => 'Perfil de Cazador';

  // Shop
  static String get shop => 'TIENDA DEL SISTEMA';
  static String get featuredItems => 'ARTICULOS DESTACADOS';
  static String get yourInventory => 'TU INVENTARIO';
  static String get cost => 'Costo';
  static String get insufficientCoins => 'Monedas insuficientes';
  static String get buy => 'Comprar';

  // Offline
  static String get offline => 'Sin conexion';
  static String get online => 'En linea';
  static String get syncPending => 'Sincronizacion pendiente';
  static String get syncing => 'Sincronizando...';
  static String get syncComplete => 'Sincronizacion completada';
}

// Note: AppLocalizationsX extension temporarily disabled
// Will be restored when l10n is configured with Firebase project
