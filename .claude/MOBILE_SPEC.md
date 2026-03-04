# MOBILE_SPEC.md — ICFES Leveling Flutter App

> Especificación técnica de la aplicación móvil Flutter.

---

## 1. STACK

| Dependencia | Versión | Uso |
|---|---|---|
| Flutter SDK | ≥3.0 | Framework |
| Dart | 3.x | Lenguaje |
| Riverpod | ^2.5.0 | State management |
| Hive | ^2.2.3 | BD local offline |
| Dio | ^5.4.0 | HTTP client |
| GoRouter | ^13.0.0 | Navegación |
| Firebase Auth | ^5.3.4 | Social login |
| Sentry Flutter | ^8.0.0 | Error tracking |
| Rive | ^0.12 | Animaciones |
| Lottie | ^3.0 | Animaciones |
| youtube_player_flutter | 9.0.3 | Video player |

---

## 2. ARQUITECTURA

### 2.1 Clean Architecture por Feature

```
lib/
├── core/                           # Shared infrastructure
│   ├── config/
│   │   ├── routes.dart             # GoRouter (30+ rutas)
│   │   └── env.dart                # Variables de entorno
│   ├── learning/
│   │   └── domain/
│   │       └── adaptive_engine.dart # Motor adaptativo local
│   ├── network/
│   │   ├── dio_client.dart         # Configuración Dio
│   │   ├── auth_interceptor.dart   # Inject token
│   │   ├── retry_interceptor.dart  # Retry con backoff
│   │   └── error_interceptor.dart  # Error handling
│   └── theme/
│       ├── app_theme.dart          # Tema oscuro RPG
│       ├── app_colors.dart         # Colores
│       └── app_typography.dart     # Tipografía
│
├── features/
│   ├── auth/                       # Login, Register, Social
│   ├── onboarding/                 # 5 pasos + diagnóstico
│   ├── home/                       # Dashboard principal
│   ├── practice/                   # Sesiones práctica + Boss Raid
│   ├── millionaire/                # Modo Millonario
│   ├── diagnostic/                 # Diagnóstico profundo
│   ├── study_plan/                 # Plan de estudio
│   ├── mastery/                    # Tracking de mastery
│   ├── video/                      # Reproductor YouTube
│   ├── leagues/                    # Ligas semanales
│   ├── profile/                    # Perfil usuario
│   ├── shop/                       # Tienda virtual
│   ├── notifications/              # Push notifications
│   └── shell/                      # Bottom navigation
│
└── shared/
    ├── widgets/                    # Componentes reutilizables
    │   ├── rpg_button.dart
    │   ├── xp_bar.dart
    │   ├── heart_display.dart
    │   ├── streak_badge.dart
    │   ├── combo_overlay.dart
    │   └── loading_indicator.dart
    └── services/
        ├── sync_manager.dart
        ├── connectivity_monitor.dart
        ├── question_cache_service.dart
        └── dopamine_engine.dart
```

### 2.2 Cada Feature Sigue

```
features/<name>/
├── data/
│   ├── repositories/           # Implementación
│   │   └── <name>_repository_impl.dart
│   ├── datasources/
│   │   ├── <name>_remote_datasource.dart   # API calls
│   │   └── <name>_local_datasource.dart    # Hive
│   └── models/
│       └── <name>_dto.dart     # Data Transfer Objects
├── domain/
│   ├── entities/               # Modelos de dominio
│   ├── repositories/           # Interfaces
│   └── usecases/               # Lógica de negocio
└── presentation/
    ├── pages/                  # Pantallas completas
    ├── widgets/                # Widgets del feature
    └── providers/              # Riverpod providers
```

---

## 3. INICIALIZACIÓN

```dart
// main.dart - Orden de inicialización

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  
  // 1. Environment variables
  await Environment.init();
  
  // 2. Local database
  await Hive.initFlutter();
  // Registrar adaptadores Hive
  Hive.registerAdapter(CachedQuestionAdapter());
  Hive.registerAdapter(PendingAnswerAdapter());
  
  // 3. Shared preferences
  await SharedPreferences.getInstance();
  
  // 4. Firebase (social auth)
  await Firebase.initializeApp();
  
  // 5. Push notifications
  await NotificationService.init();
  
  // 6. Question cache
  await QuestionCacheService.init();
  
  // 7. Sync manager
  await SyncManager.init();
  
  // 8. Sentry error tracking
  await SentryFlutter.init(
    (options) {
      options.dsn = Env.sentryDsn;
      options.tracesSampleRate = 0.3;
    },
    appRunner: () => runApp(
      const ProviderScope(child: ICFESLevelingApp()),
    ),
  );
}
```

---

## 4. NAVEGACIÓN

### 4.1 Rutas

```dart
// Shell Route (con Bottom Navigation)
ShellRoute(
  builder: (context, state, child) => MainShell(child: child),
  routes: [
    GoRoute(path: '/home',       builder: HomePage),
    GoRoute(path: '/leagues',    builder: LeaguesPage),
    GoRoute(path: '/study-plan', builder: StudyPlanPage),
    GoRoute(path: '/profile',    builder: ProfilePage),
  ],
)

// Rutas Públicas (sin auth)
/splash
/onboarding/welcome
/onboarding/goal
/onboarding/level
/onboarding/subjects
/onboarding/time
/login
/register
/diagnostic

// Rutas Protegidas (requieren auth)
/practice/session
/practice/results
/millionaire
/boss-raid
/mastery
/mastery/:topicId
/shop
/video/:videoId
/settings
```

### 4.2 Guards

```dart
redirect: (context, state) {
  final isAuthenticated = ref.read(authProvider).isAuthenticated;
  final onboardingComplete = ref.read(authProvider).onboardingComplete;
  
  if (!isAuthenticated) return '/login';
  if (!onboardingComplete) return '/onboarding/welcome';
  return null;
}
```

---

## 5. NETWORKING

### 5.1 Dio Configuration

```dart
final dio = Dio(BaseOptions(
  baseUrl: Env.apiBaseUrl,
  connectTimeout: const Duration(seconds: 30),
  receiveTimeout: const Duration(seconds: 60),
  headers: {'Content-Type': 'application/json'},
));

// Interceptors (orden importa)
dio.interceptors.addAll([
  AuthInterceptor(tokenProvider),    // Inject Bearer token
  RetryInterceptor(maxRetries: 3),   // Retry 5xx con backoff
  LogInterceptor(),                  // Debug logging
  ErrorInterceptor(),                // Map errors
]);
```

### 5.2 Auth Interceptor

```dart
class AuthInterceptor extends Interceptor {
  @override
  void onRequest(RequestOptions options, handler) {
    final token = tokenProvider.accessToken;
    if (token != null) {
      options.headers['Authorization'] = 'Bearer $token';
    }
    handler.next(options);
  }

  @override
  void onError(DioException err, handler) async {
    if (err.response?.statusCode == 401) {
      // Intentar refresh token
      final refreshed = await tokenProvider.refresh();
      if (refreshed) {
        // Reintentar request original
        final retryResponse = await dio.fetch(err.requestOptions);
        return handler.resolve(retryResponse);
      }
      // Refresh falló → logout
      tokenProvider.logout();
    }
    handler.next(err);
  }
}
```

---

## 6. OFFLINE-FIRST

### 6.1 Question Cache

```dart
class QuestionCacheService {
  late Box<CachedQuestion> _box;
  
  Future<void> init() async {
    _box = await Hive.openBox<CachedQuestion>('questions_cache');
  }
  
  // Pre-descargar preguntas por materia
  Future<void> preloadSubject(String subjectId) async {
    final questions = await api.getQuestionsBySubject(subjectId);
    for (final q in questions) {
      await _box.put(q.id, CachedQuestion.fromApi(q));
    }
  }
  
  // Obtener pregunta (cache first)
  CachedQuestion? getQuestion(String id) => _box.get(id);
  
  // Verificar freshness
  bool isStale(String id) {
    final cached = _box.get(id);
    if (cached == null) return true;
    return DateTime.now().difference(cached.cachedAt).inHours > 24;
  }
}
```

### 6.2 Action Queue

```dart
class ActionQueue {
  late Box<PendingAction> _box;
  
  // Agregar acción pendiente (offline)
  Future<void> enqueue(PendingAction action) async {
    await _box.add(action);
  }
  
  // Procesar cola (cuando hay conexión)
  Future<void> processAll() async {
    final pending = _box.values.toList()
      ..sort((a, b) => a.createdAt.compareTo(b.createdAt)); // FIFO
    
    for (final action in pending) {
      try {
        await _processAction(action);
        await action.delete(); // Remover de cola
      } catch (e) {
        // Si falla, dejar en cola para siguiente intento
        break;
      }
    }
  }
}
```

### 6.3 Sync Manager

```dart
class SyncManager {
  final ConnectivityMonitor _connectivity;
  final ActionQueue _queue;
  
  void init() {
    _connectivity.onStatusChange.listen((status) {
      if (status == ConnectivityStatus.online) {
        _queue.processAll();
      }
    });
  }
}
```

---

## 7. DOPAMINE ENGINE

```dart
class DopamineEngine {
  /// Variable rewards: Recompensas no predecibles
  static Widget variableRewardPopup(int xp, int gold, {bool isCritical = false}) {
    // Popup con animación de escala + partículas
    // Si critical: efecto dorado extra
  }
  
  /// Loss aversion: Alerta de pérdida de racha
  static Widget streakWarning(int currentStreak) {
    // "¡Tu racha de {n} días está en peligro!"
    // Animación shake + color rojo
  }
  
  /// Combo overlay: Aparece en combo >= 2
  static Widget comboOverlay(int comboCount) {
    // "COMBO x{n}" con escala elástica
    // Colores escalando: blanco → amarillo → naranja → rojo
  }
  
  /// Feedback inmediato: Resultado de respuesta
  static Widget answerFeedback({
    required bool isCorrect,
    required int xpEarned,
    required int goldEarned,
    required String attemptType,
  }) {
    // ✅ Verde + confetti + "+15 XP"
    // ❌ Rojo + shake + "-1 ❤️"
    // Si attemptType == "invalid_repeat": badge "0 XP (REPETIDA)"
  }
}
```

---

## 8. SCREENS PRINCIPALES

### 8.1 Home Dashboard
- Avatar del usuario con nivel y rango.
- Barra de XP hacia siguiente nivel.
- Corazones + timer de regeneración.
- Racha actual con multiplicador.
- Botones de acción: Practice, Millionaire, Boss Raid.
- Daily quests progreso.
- Recommended next action.

### 8.2 Practice Session
- Pregunta con 4 opciones.
- Timer visible.
- Combo counter.
- Lifelines (3 botones).
- Progreso (N/15).
- Hearts display.
- Anti-gaming badge si aplica.

### 8.3 Results Screen
- Score: N/15 correctas.
- XP total ganado (desglosado).
- Gold ganado.
- Mastery changes (topics affected).
- "Continuar" o "Ver errores".

### 8.4 Millionaire
- Escalera de premios (15 niveles).
- Checkpoints destacados (5, 10, 15).
- Lifelines en header.
- Walk Away button.
- Animación de premio al avanzar.

### 8.5 Boss Raid
- Boss visual con HP bar.
- 3 fases visuales según HP.
- Combo counter.
- Damage per answer.
- Timer hasta cierre.
- Leaderboard sidebar.

---

## 9. TEMA VISUAL

### 9.1 Colores (Tema Oscuro RPG)

```dart
// Primary
primaryDark:   #1A1A2E   // Background principal
primaryMid:    #16213E   // Cards y surfaces
primaryLight:  #0F3460   // Accents
accent:        #E94560   // CTAs y highlights

// Rangos
rankE:   #808080  // Gris
rankD:   #4CAF50  // Verde
rankC:   #2196F3  // Azul
rankB:   #9C27B0  // Púrpura
rankA:   #FF9800  // Naranja
rankS:   #FFD700  // Dorado
rankSS:  #FF4444  // Rojo
rankSSS: #FF00FF  // Magenta + glow

// Feedback
correct:   #4CAF50
incorrect: #F44336
warning:   #FF9800
info:      #2196F3
```

### 9.2 Animaciones
- Transiciones de página: slide + fade (300ms).
- Botones: scale on tap (100ms).
- XP gain: count up animation (500ms).
- Level up: full screen celebration (2s).
- Combo: elastic scale + particles.
- Boss damage: shake + flash.
