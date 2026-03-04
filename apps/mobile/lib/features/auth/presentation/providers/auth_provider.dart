import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/network/api_client.dart';
import '../../../../core/auth/domain/entities/user.dart';
import '../../domain/repositories/auth_repository.dart';
import '../../domain/usecases/login_usecase.dart';
import '../../domain/usecases/register_usecase.dart';
import '../../domain/usecases/logout_usecase.dart';
import '../../data/repositories/auth_repository_impl.dart';
import '../../data/datasources/auth_remote_datasource.dart';
import '../../../../core/storage/question_cache.dart';
import '../../../../core/providers/storage_providers.dart';
import '../../../../core/services/firebase_auth_service.dart';
import '../../../../core/sync/question_cache_service.dart';

// Note: authLocalDataSourceProvider and apiClientProvider are defined in api_client.dart
// which is already imported above

// Core providers (apiClient, secureStorage, authLocalData) are now in core/network/api_client.dart

final authRemoteDataSourceProvider = Provider((ref) {
  final apiClient = ref.watch(apiClientProvider);
  return AuthRemoteDataSource(apiClient);
});

final authRepositoryProvider = Provider<AuthRepository>((ref) {
  final remote = ref.watch(authRemoteDataSourceProvider);
  final local = ref.watch(authLocalDataSourceProvider);
  return AuthRepositoryImpl(remote, local);
});

// Use Case Providers
final loginUseCaseProvider = Provider((ref) {
  final repo = ref.watch(authRepositoryProvider);
  return LoginUseCase(repo);
});

final registerUseCaseProvider = Provider((ref) {
  final repo = ref.watch(authRepositoryProvider);
  return RegisterUseCase(repo);
});

final logoutUseCaseProvider = Provider((ref) {
  final repo = ref.watch(authRepositoryProvider);
  return LogoutUseCase(repo);
});

// Auth State Provider
class AuthState {
  final User? user;
  final bool isLoading;
  final String? error;

  AuthState({this.user, this.isLoading = false, this.error});

  AuthState copyWith({User? user, bool? isLoading, String? error}) {
    return AuthState(
      user: user ?? this.user,
      isLoading: isLoading ?? this.isLoading,
      error: error ?? this.error,
    );
  }
}

class AuthNotifier extends StateNotifier<AuthState> {
  final LoginUseCase _loginUseCase;
  final RegisterUseCase _registerUseCase;
  final LogoutUseCase _logoutUseCase;
  final AuthRepository _repository;
  final ApiClient _apiClient;
  final QuestionCache _questionCache;
  final FirebaseAuthService _firebaseAuth;
  final QuestionCacheService _questionCacheService;

  AuthNotifier(
    this._loginUseCase,
    this._registerUseCase,
    this._logoutUseCase,
    this._repository,
    this._apiClient,
    this._questionCache,
    this._firebaseAuth,
    this._questionCacheService,
  ) : super(AuthState()) {
    _checkStatus();
  }

  Future<void> _checkStatus() async {
    state = state.copyWith(isLoading: true);
    try {
      // Timeout after 3 seconds if backend is not responding
      final user = await _repository.getCurrentUser()
          .timeout(const Duration(seconds: 3), onTimeout: () => null);
      state = state.copyWith(user: user, isLoading: false);
    } catch (e) {
      // Backend not available - show login page
      state = state.copyWith(user: null, isLoading: false);
    }
  }

  Future<void> login(String email, String password) async {
    state = state.copyWith(isLoading: true, error: null);
    try {
      final user = await _loginUseCase.execute(email, password);
      // FASE 1: Master Plan - Warm up cache on login
      await _questionCache.warmUp(_apiClient);
      // Precache questions for offline usage (non-blocking)
      _precacheQuestionsInBackground();
      state = state.copyWith(user: user, isLoading: false);
    } catch (e) {
      state = state.copyWith(isLoading: false, error: e.toString());
    }
  }

  /// Precache questions for all areas in background
  /// This runs asynchronously and doesn't block login
  Future<void> _precacheQuestionsInBackground() async {
    try {
      await _questionCacheService.precacheAllAreas(_apiClient);
    } catch (e) {
      // Silent fail - caching is non-critical
      debugPrint('Background precaching failed: $e');
    }
  }

  Future<void> register(String email, String password, String name) async {
    state = state.copyWith(isLoading: true, error: null);
    try {
      final user = await _registerUseCase.execute(email, password, name);
      state = state.copyWith(user: user, isLoading: false);
    } catch (e) {
      state = state.copyWith(isLoading: false, error: e.toString());
    }
  }

  /// Register a new user and automatically login
  /// Used for guest registration flow
  Future<void> registerAndLogin(String email, String password, String name) async {
    state = state.copyWith(isLoading: true, error: null);
    try {
      // First register
      await _registerUseCase.execute(email, password, name);
      // Then login to get proper tokens
      final user = await _loginUseCase.execute(email, password);
      // Warm up cache on login
      await _questionCache.warmUp(_apiClient);
      state = state.copyWith(user: user, isLoading: false);
    } catch (e) {
      // If registration fails because user exists, try login
      if (e.toString().contains('ya existe')) {
        try {
          final user = await _loginUseCase.execute(email, password);
          await _questionCache.warmUp(_apiClient);
          state = state.copyWith(user: user, isLoading: false);
          return;
        } catch (loginError) {
          state = state.copyWith(isLoading: false, error: 'Error al iniciar sesión');
          return;
        }
      }
      state = state.copyWith(isLoading: false, error: 'Error al crear cuenta: ${e.toString()}');
    }
  }

  Future<void> logout() async {
    await _logoutUseCase.execute();
    state = AuthState();
  }

  /// Refresh user data from server
  Future<void> refreshUser() async {
    try {
      final user = await _repository.getCurrentUser();
      if (user != null) {
        state = state.copyWith(user: user);
      }
    } catch (e) {
      // Silent fail - keep current state
    }
  }

  /// Sign in with Google using Firebase
  Future<void> signInWithGoogle() async {
    state = state.copyWith(isLoading: true, error: null);
    try {
      final result = await _firebaseAuth.signInWithGoogle();

      if (!result.success) {
        state = state.copyWith(isLoading: false, error: result.error);
        return;
      }

      // Use Firebase result to register/login with backend
      await _handleSocialSignIn(result);
    } catch (e) {
      state = state.copyWith(isLoading: false, error: 'Error al iniciar sesión con Google');
    }
  }

  /// Sign in with Apple using Firebase
  Future<void> signInWithApple() async {
    state = state.copyWith(isLoading: true, error: null);
    try {
      final result = await _firebaseAuth.signInWithApple();

      if (!result.success) {
        state = state.copyWith(isLoading: false, error: result.error);
        return;
      }

      // Use Firebase result to register/login with backend
      await _handleSocialSignIn(result);
    } catch (e) {
      state = state.copyWith(isLoading: false, error: 'Error al iniciar sesión con Apple');
    }
  }

  /// Sign in as guest using Firebase anonymous auth
  Future<void> signInAsGuest() async {
    state = state.copyWith(isLoading: true, error: null);
    try {
      final result = await _firebaseAuth.signInAnonymously();

      if (!result.success) {
        state = state.copyWith(isLoading: false, error: result.error);
        return;
      }

      // Use Firebase result to register/login with backend
      await _handleSocialSignIn(result);
    } catch (e) {
      state = state.copyWith(isLoading: false, error: 'Error al crear cuenta de invitado');
    }
  }

  /// Enter demo mode - tries to connect to backend, falls back to local if unavailable
  /// This allows testing with real backend connection when available
  Future<void> enterDemoMode() async {
    state = state.copyWith(isLoading: true, error: null);

    // Use username (not email) for login since backend uses OAuth2PasswordRequestForm
    const demoUsername = 'demo_hunter';
    const demoEmail = 'demo@test.com';
    const demoPassword = 'Demo123#';
    const demoName = 'Cazador Demo';

    try {
      // Try to login with existing demo account first (using username)
      final user = await _loginUseCase.execute(demoUsername, demoPassword)
          .timeout(const Duration(seconds: 5));
      await _questionCache.warmUp(_apiClient);
      state = state.copyWith(user: user, isLoading: false);
      return;
    } catch (e) {
      // Login failed - try to register demo user
      try {
        await _registerUseCase.execute(demoEmail, demoPassword, demoName)
            .timeout(const Duration(seconds: 5));
        // Then login to get tokens (using username derived from email)
        final user = await _loginUseCase.execute(demoUsername, demoPassword)
            .timeout(const Duration(seconds: 5));
        await _questionCache.warmUp(_apiClient);
        state = state.copyWith(user: user, isLoading: false);
        return;
      } catch (registerError) {
        // Backend not available - fall back to local demo mode
        _enterLocalDemoMode();
      }
    }
  }

  /// Fallback to local demo user when backend is unavailable
  void _enterLocalDemoMode() {
    final demoUser = User(
      id: 'demo-local-${DateTime.now().millisecondsSinceEpoch}',
      email: 'demo@icfesleveling.app',
      name: 'Cazador Demo (Offline)',
      level: 5,
      xp: 1250,
      rank: 'E',
      hearts: 5,
      currentStreak: 3,
      diagnosticCompleted: false,
      completedDeepDiagnostics: [],
    );
    state = state.copyWith(user: demoUser, isLoading: false);
  }

  /// Handle social sign-in result - create/login user on backend
  Future<void> _handleSocialSignIn(SocialSignInResult result) async {
    final email = result.email ?? '${result.provider}_user@icfesleveling.app';
    final name = result.displayName ?? 'Cazador ${result.provider}';
    // Use Firebase ID token as password (unique per user)
    final password = result.firebaseIdToken?.substring(0, 32) ?? DateTime.now().millisecondsSinceEpoch.toString();

    try {
      // Try to register first
      await _registerUseCase.execute(email, password, name);
      // Then login
      final user = await _loginUseCase.execute(email, password);
      await _questionCache.warmUp(_apiClient);
      state = state.copyWith(user: user, isLoading: false);
    } catch (e) {
      // If registration fails (user exists), try login
      if (e.toString().contains('ya existe')) {
        try {
          final user = await _loginUseCase.execute(email, password);
          await _questionCache.warmUp(_apiClient);
          state = state.copyWith(user: user, isLoading: false);
          return;
        } catch (loginError) {
          // Password might be different - need backend OAuth support
          state = state.copyWith(
            isLoading: false,
            error: 'Esta cuenta ya existe con otro método de inicio de sesión.',
          );
          return;
        }
      }
      state = state.copyWith(isLoading: false, error: 'Error al crear cuenta');
    }
  }

  @override
  void dispose() {
    // Cleanup any resources if needed
    super.dispose();
  }
}

final authProvider = StateNotifierProvider<AuthNotifier, AuthState>((ref) {
  final login = ref.watch(loginUseCaseProvider);
  final register = ref.watch(registerUseCaseProvider);
  final logout = ref.watch(logoutUseCaseProvider);
  final repo = ref.watch(authRepositoryProvider);
  final apiClient = ref.watch(apiClientProvider);
  final questionCache = ref.watch(questionCacheProvider);
  final firebaseAuth = ref.watch(firebaseAuthServiceProvider);
  final questionCacheService = ref.watch(questionCacheServiceProvider);
  return AuthNotifier(
    login,
    register,
    logout,
    repo,
    apiClient,
    questionCache,
    firebaseAuth,
    questionCacheService,
  );
});
