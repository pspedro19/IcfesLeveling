import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// Keys for onboarding state persistence
class OnboardingKeys {
  static const String hasSeenValueProp = 'has_seen_value_prop';
  static const String hasCompletedOnboarding = 'has_completed_onboarding';
  static const String onboardingStep = 'onboarding_step';
  static const String devModeEnabled = 'dev_mode_enabled';
}

/// Onboarding steps enum
enum OnboardingStep {
  splash,      // Step 1: Initial splash
  valueProp,   // Step 2: Value proposition screens
  signup,      // Step 3: Quick signup
  diagnostic,  // Step 4: Quick diagnostic
  results,     // Step 5: Results reveal
  firstMission,// Step 6: First mission
  completed,   // Onboarding complete
}

/// Service to manage onboarding state
class OnboardingService {
  final SharedPreferences _prefs;

  OnboardingService(this._prefs);

  /// Check if this is a first run (never seen value prop)
  bool get isFirstRun => !(_prefs.getBool(OnboardingKeys.hasSeenValueProp) ?? false);

  /// Check if onboarding is complete
  bool get isOnboardingComplete =>
      _prefs.getBool(OnboardingKeys.hasCompletedOnboarding) ?? false;

  /// Get current onboarding step
  OnboardingStep get currentStep {
    final stepIndex = _prefs.getInt(OnboardingKeys.onboardingStep) ?? 0;
    if (stepIndex >= OnboardingStep.values.length) {
      return OnboardingStep.completed;
    }
    return OnboardingStep.values[stepIndex];
  }

  /// Check if developer mode is enabled
  bool get isDevModeEnabled => _prefs.getBool(OnboardingKeys.devModeEnabled) ?? false;

  /// Mark value proposition as seen
  Future<void> markValuePropSeen() async {
    await _prefs.setBool(OnboardingKeys.hasSeenValueProp, true);
    await _setStep(OnboardingStep.signup);
  }

  /// Update onboarding step
  Future<void> setStep(OnboardingStep step) async {
    await _setStep(step);
  }

  Future<void> _setStep(OnboardingStep step) async {
    await _prefs.setInt(OnboardingKeys.onboardingStep, step.index);
  }

  /// Mark onboarding as complete
  Future<void> completeOnboarding() async {
    await _prefs.setBool(OnboardingKeys.hasCompletedOnboarding, true);
    await _setStep(OnboardingStep.completed);
  }

  /// Enable developer mode
  Future<void> setDevMode(bool enabled) async {
    await _prefs.setBool(OnboardingKeys.devModeEnabled, enabled);
  }

  /// Reset onboarding state (for developer mode)
  Future<void> resetOnboarding() async {
    await _prefs.remove(OnboardingKeys.hasSeenValueProp);
    await _prefs.remove(OnboardingKeys.hasCompletedOnboarding);
    await _prefs.remove(OnboardingKeys.onboardingStep);
  }

  /// Full reset (clears all app data)
  Future<void> fullReset() async {
    // Keep dev mode setting
    final devMode = isDevModeEnabled;
    await _prefs.clear();
    await setDevMode(devMode);
  }

  /// Get route for current onboarding state
  String getRouteForCurrentState({required bool isLoggedIn, required bool diagnosticCompleted}) {
    // First run - show value proposition
    if (isFirstRun) {
      return '/onboarding';
    }

    // Not logged in - show login
    if (!isLoggedIn) {
      return '/login';
    }

    // Logged in but onboarding incomplete - continue from last step
    if (!isOnboardingComplete) {
      switch (currentStep) {
        case OnboardingStep.splash:
        case OnboardingStep.valueProp:
        case OnboardingStep.signup:
          // Already logged in, continue to diagnostic
          return '/diagnostic/quick';
        case OnboardingStep.diagnostic:
          return '/diagnostic/quick';
        case OnboardingStep.results:
          return '/diagnostic/results';
        case OnboardingStep.firstMission:
          return '/diagnostic/mission';
        case OnboardingStep.completed:
          return '/home';
      }
    }

    // Onboarding complete - go home
    return '/home';
  }
}

/// Provider for SharedPreferences
final sharedPreferencesProvider = Provider<SharedPreferences>((ref) {
  throw UnimplementedError('Must be overridden in main.dart');
});

/// Provider for OnboardingService
final onboardingServiceProvider = Provider<OnboardingService>((ref) {
  final prefs = ref.watch(sharedPreferencesProvider);
  return OnboardingService(prefs);
});

/// State notifier for onboarding state
class OnboardingState {
  final bool isFirstRun;
  final bool isOnboardingComplete;
  final OnboardingStep currentStep;
  final bool isDevModeEnabled;

  OnboardingState({
    required this.isFirstRun,
    required this.isOnboardingComplete,
    required this.currentStep,
    required this.isDevModeEnabled,
  });

  OnboardingState copyWith({
    bool? isFirstRun,
    bool? isOnboardingComplete,
    OnboardingStep? currentStep,
    bool? isDevModeEnabled,
  }) {
    return OnboardingState(
      isFirstRun: isFirstRun ?? this.isFirstRun,
      isOnboardingComplete: isOnboardingComplete ?? this.isOnboardingComplete,
      currentStep: currentStep ?? this.currentStep,
      isDevModeEnabled: isDevModeEnabled ?? this.isDevModeEnabled,
    );
  }
}

class OnboardingNotifier extends StateNotifier<OnboardingState> {
  final OnboardingService _service;

  OnboardingNotifier(this._service) : super(OnboardingState(
    isFirstRun: _service.isFirstRun,
    isOnboardingComplete: _service.isOnboardingComplete,
    currentStep: _service.currentStep,
    isDevModeEnabled: _service.isDevModeEnabled,
  ));

  Future<void> markValuePropSeen() async {
    await _service.markValuePropSeen();
    state = state.copyWith(
      isFirstRun: false,
      currentStep: OnboardingStep.signup,
    );
  }

  Future<void> setStep(OnboardingStep step) async {
    await _service.setStep(step);
    state = state.copyWith(currentStep: step);
  }

  Future<void> completeOnboarding() async {
    await _service.completeOnboarding();
    state = state.copyWith(
      isOnboardingComplete: true,
      currentStep: OnboardingStep.completed,
    );
  }

  Future<void> setDevMode(bool enabled) async {
    await _service.setDevMode(enabled);
    state = state.copyWith(isDevModeEnabled: enabled);
  }

  Future<void> resetOnboarding() async {
    await _service.resetOnboarding();
    state = OnboardingState(
      isFirstRun: true,
      isOnboardingComplete: false,
      currentStep: OnboardingStep.splash,
      isDevModeEnabled: state.isDevModeEnabled,
    );
  }

  Future<void> fullReset() async {
    await _service.fullReset();
    state = OnboardingState(
      isFirstRun: true,
      isOnboardingComplete: false,
      currentStep: OnboardingStep.splash,
      isDevModeEnabled: state.isDevModeEnabled,
    );
  }

  String getRouteForCurrentState({required bool isLoggedIn, required bool diagnosticCompleted}) {
    return _service.getRouteForCurrentState(
      isLoggedIn: isLoggedIn,
      diagnosticCompleted: diagnosticCompleted,
    );
  }
}

/// Provider for OnboardingNotifier
final onboardingProvider = StateNotifierProvider<OnboardingNotifier, OnboardingState>((ref) {
  final service = ref.watch(onboardingServiceProvider);
  return OnboardingNotifier(service);
});
