import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../auth/presentation/providers/auth_provider.dart';
import '../../../engagement/presentation/providers/engagement_provider.dart';
import '../../../../core/config/routes.dart';
import '../../../../core/constants/app_strings.dart';

class SplashPage extends ConsumerStatefulWidget {
  const SplashPage({super.key});

  @override
  ConsumerState<SplashPage> createState() => _SplashPageState();
}

class _SplashPageState extends ConsumerState<SplashPage> {
  @override
  void initState() {
    super.initState();
    _handleNavigation();
  }

  Future<void> _handleNavigation() async {
    // Check streak status on app start
    ref.read(engagementProvider.notifier).checkStreakStatus();
    
    // Artificial delay for splash visibility as per requirements (3s total)
    await Future.delayed(const Duration(seconds: 3));
    
    if (!mounted) return;
    
    final authState = ref.read(authProvider);
    final isLoggedIn = authState.user != null;
    final hasCompletedOnboarding = authState.user?.diagnosticCompleted ?? false;

    if (isLoggedIn) {
      if (hasCompletedOnboarding) {
        context.go(AppRoutes.home);
      } else {
        context.go(AppRoutes.onboarding);
      }
    } else {
      context.go(AppRoutes.onboarding);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0A0A0A), // Dark Solo Leveling theme
      body: Stack(
        children: [
          // Background Glow
          Center(
            child: Container(
              width: 200,
              height: 200,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                boxShadow: [
                  BoxShadow(
                    color: Colors.blue.withOpacity(0.2),
                    blurRadius: 100,
                    spreadRadius: 50,
                  ),
                ],
              ),
            ).animate(onPlay: (controller) => controller.repeat(reverse: true))
             .scale(begin: const Offset(0.8, 0.8), end: const Offset(1.2, 1.2), duration: 2.seconds, curve: Curves.easeInOut),
          ),
          
          Center(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                // Logo Placeholder with Blue Glow
                Container(
                  padding: const EdgeInsets.all(20),
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    border: Border.all(color: Colors.blue.withOpacity(0.5), width: 2),
                    boxShadow: [
                      BoxShadow(
                        color: Colors.blue.withOpacity(0.3),
                        blurRadius: 20,
                        spreadRadius: 5,
                      ),
                    ],
                  ),
                  child: const Icon(
                    Icons.bolt, // Placeholder for Solo Leveling type logo
                    size: 80,
                    color: Colors.white,
                  ),
                ).animate()
                 .fadeIn(duration: 800.ms)
                 .scale(delay: 200.ms),
                 
                const SizedBox(height: 40),
                
                // App Name
                Text(
                  AppStrings.appName.toUpperCase(),
                  style: const TextStyle(
                    color: Colors.white,
                    fontSize: 28,
                    fontWeight: FontWeight.w900,
                    letterSpacing: 4,
                  ),
                ).animate()
                 .fadeIn(delay: 500.ms, duration: 800.ms)
                 .shimmer(delay: 1500.ms, duration: 2.seconds, color: Colors.blue.withOpacity(0.5)),

                const SizedBox(height: 16),
                
                // Thematic Text
                Text(
                  "DESPIERTA, CAZADOR",
                  style: TextStyle(
                    color: Colors.blue.shade300,
                    fontSize: 16,
                    fontWeight: FontWeight.w500,
                    letterSpacing: 8,
                  ),
                ).animate()
                 .fadeIn(delay: 1500.ms, duration: 1.seconds)
                 .blurXY(begin: 10, end: 0, delay: 1500.ms, duration: 1.seconds),
              ],
            ),
          ),
          
          // Bottom loading indicator (subtle)
          Positioned(
            bottom: 50,
            left: 0,
            right: 0,
            child: Center(
              child: SizedBox(
                width: 40,
                height: 2,
                child: const LinearProgressIndicator(
                  backgroundColor: Colors.transparent,
                  valueColor: AlwaysStoppedAnimation<Color>(Colors.blue),
                ),
              ).animate().fadeIn(delay: 2.seconds),
            ),
          ),
        ],
      ),
    );
  }
}
