import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/config/routes.dart';
import '../../../../core/services/onboarding_service.dart';
import '../providers/auth_provider.dart';

class SplashPage extends ConsumerStatefulWidget {
  const SplashPage({super.key});

  @override
  ConsumerState<SplashPage> createState() => _SplashPageState();
}

class _SplashPageState extends ConsumerState<SplashPage>
    with SingleTickerProviderStateMixin {
  late AnimationController _animationController;
  late Animation<double> _fadeAnimation;
  late Animation<double> _scaleAnimation;

  @override
  void initState() {
    super.initState();
    _setupAnimations();
    _handleNavigation();
  }

  void _setupAnimations() {
    _animationController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1500),
    );

    _fadeAnimation = Tween<double>(begin: 0.0, end: 1.0).animate(
      CurvedAnimation(
        parent: _animationController,
        curve: const Interval(0.0, 0.5, curve: Curves.easeOut),
      ),
    );

    _scaleAnimation = Tween<double>(begin: 0.8, end: 1.0).animate(
      CurvedAnimation(
        parent: _animationController,
        curve: const Interval(0.0, 0.5, curve: Curves.easeOut),
      ),
    );

    _animationController.forward();
  }

  @override
  void dispose() {
    _animationController.dispose();
    super.dispose();
  }

  Future<void> _handleNavigation() async {
    // Minimum splash duration for branding (2 seconds per spec)
    await Future.delayed(const Duration(seconds: 2));

    if (!mounted) return;

    // Get current states
    final authState = ref.read(authProvider);
    final onboardingState = ref.read(onboardingProvider);
    final isLoggedIn = authState.user != null;
    final diagnosticCompleted = authState.user?.diagnosticCompleted ?? false;

    String targetRoute;

    // Decision tree per LOGICA_DE_NEGOCIO.md
    if (onboardingState.isFirstRun) {
      // First time user -> Value Proposition (Step 2)
      targetRoute = AppRoutes.onboarding;
    } else if (!isLoggedIn) {
      // Returning user, not logged in -> Login
      targetRoute = AppRoutes.login;
    } else if (!onboardingState.isOnboardingComplete) {
      // Logged in but onboarding incomplete -> Resume onboarding
      targetRoute = _getResumeRoute(onboardingState.currentStep, diagnosticCompleted);
    } else {
      // Fully onboarded user -> Home
      targetRoute = AppRoutes.home;
    }

    if (mounted) {
      context.go(targetRoute);
    }
  }

  /// Get route to resume onboarding from current step
  String _getResumeRoute(OnboardingStep step, bool diagnosticCompleted) {
    switch (step) {
      case OnboardingStep.splash:
      case OnboardingStep.valueProp:
        return AppRoutes.onboarding;
      case OnboardingStep.signup:
        return AppRoutes.login;
      case OnboardingStep.diagnostic:
        return AppRoutes.diagnosticQuick;
      case OnboardingStep.results:
        return AppRoutes.resultsReveal;
      case OnboardingStep.firstMission:
        return AppRoutes.firstMission;
      case OnboardingStep.completed:
        return AppRoutes.home;
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;

    return Scaffold(
      backgroundColor: isDark ? const Color(0xFF0A0A0A) : Colors.white,
      body: AnimatedBuilder(
        animation: _animationController,
        builder: (context, child) {
          return Center(
            child: FadeTransition(
              opacity: _fadeAnimation,
              child: ScaleTransition(
                scale: _scaleAnimation,
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    // Logo placeholder - replace with actual logo
                    Container(
                      width: 120,
                      height: 120,
                      decoration: BoxDecoration(
                        shape: BoxShape.circle,
                        gradient: LinearGradient(
                          begin: Alignment.topLeft,
                          end: Alignment.bottomRight,
                          colors: [
                            Colors.blue.shade400,
                            Colors.purple.shade600,
                          ],
                        ),
                        boxShadow: [
                          BoxShadow(
                            color: Colors.blue.withOpacity(0.3),
                            blurRadius: 30,
                            spreadRadius: 5,
                          ),
                        ],
                      ),
                      child: const Icon(
                        Icons.school,
                        size: 60,
                        color: Colors.white,
                      ),
                    ),

                    const SizedBox(height: 32),

                    // App name with hunter theme
                    Text(
                      'ICFES LEVELING',
                      style: TextStyle(
                        fontWeight: FontWeight.w900,
                        fontSize: 28,
                        letterSpacing: 4,
                        color: isDark ? Colors.white : Colors.black87,
                      ),
                    ),

                    const SizedBox(height: 12),

                    // Tagline
                    Text(
                      'Despierta, Cazador.',
                      style: TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.w300,
                        letterSpacing: 2,
                        color: isDark ? Colors.white70 : Colors.black54,
                      ),
                    ),

                    const SizedBox(height: 48),

                    // Loading indicator
                    SizedBox(
                      width: 24,
                      height: 24,
                      child: CircularProgressIndicator(
                        strokeWidth: 2,
                        valueColor: AlwaysStoppedAnimation<Color>(
                          isDark ? Colors.blue.shade300 : Colors.blue.shade600,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ),
          );
        },
      ),
    );
  }
}
