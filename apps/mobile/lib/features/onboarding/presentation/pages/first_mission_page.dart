import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../../core/config/routes.dart';
import '../../../../core/services/onboarding_service.dart';

class FirstMissionPage extends ConsumerWidget {
  const FirstMissionPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return Scaffold(
      backgroundColor: const Color(0xFF0A0A0A),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 32),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              const SizedBox(height: 60),

              const Text(
                "NUEVA MISION DISPONIBLE",
                textAlign: TextAlign.center,
                style: TextStyle(
                  color: Colors.blue,
                  fontSize: 14,
                  fontWeight: FontWeight.bold,
                  letterSpacing: 3,
                ),
              ).animate().fadeIn().slideY(begin: -0.2, end: 0),

              const SizedBox(height: 12),

              const Text(
                "EL DESPERTAR DEL CAZADOR",
                textAlign: TextAlign.center,
                style: TextStyle(
                  color: Colors.white,
                  fontSize: 28,
                  fontWeight: FontWeight.w900,
                  letterSpacing: 1,
                ),
              ).animate().fadeIn(delay: 300.ms),

              const SizedBox(height: 60),

              // Mission Card
              Container(
                padding: const EdgeInsets.all(24),
                decoration: BoxDecoration(
                  color: Colors.white.withOpacity(0.03),
                  borderRadius: BorderRadius.circular(20),
                  border: Border.all(color: Colors.blue.withOpacity(0.2)),
                  boxShadow: [
                    BoxShadow(color: Colors.blue.withOpacity(0.05), blurRadius: 20, spreadRadius: -5),
                  ],
                ),
                child: Column(
                  children: [
                    const Icon(Icons.assignment, color: Colors.blue, size: 48).animate().scale(delay: 600.ms),
                    const SizedBox(height: 20),
                    const Text(
                      "Mision de Calibracion",
                      style: TextStyle(color: Colors.white, fontSize: 20, fontWeight: FontWeight.bold),
                    ),
                    const SizedBox(height: 12),
                    const Text(
                      "El sistema ha detectado una debilidad en Lectura Critica. Completa tu primer entrenamiento para fortalecerte.",
                      textAlign: TextAlign.center,
                      style: TextStyle(color: Colors.grey, fontSize: 16, height: 1.4),
                    ),
                    const SizedBox(height: 32),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceAround,
                      children: [
                        _RewardIndicator(label: "+50 XP", icon: Icons.bolt, color: Colors.amber),
                        _RewardIndicator(label: "+20 Oro", icon: Icons.monetization_on, color: Colors.yellow),
                      ],
                    ),
                  ],
                ),
              ).animate().fadeIn(delay: 500.ms).scale(delay: 500.ms),

              const Spacer(),

              TextButton(
                onPressed: () => _finishOnboarding(context, ref, goToPractice: false),
                child: const Text(
                  "IR AL PANEL PRINCIPAL",
                  style: TextStyle(color: Colors.white38, letterSpacing: 1),
                ),
              ).animate().fadeIn(delay: 1500.ms),

              const SizedBox(height: 16),

              ElevatedButton(
                onPressed: () => _finishOnboarding(context, ref, goToPractice: true),
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.blue.shade700,
                  foregroundColor: Colors.white,
                  minimumSize: const Size(double.infinity, 64),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                  elevation: 10,
                  shadowColor: Colors.blue.withOpacity(0.4),
                ),
                child: const Text(
                  "ACEPTAR MISION",
                  style: TextStyle(fontSize: 20, fontWeight: FontWeight.w900, letterSpacing: 4),
                ),
              ).animate(onPlay: (c) => c.repeat(reverse: true))
               .shimmer(duration: 2.seconds, color: Colors.white24)
               .scale(begin: const Offset(1, 1), end: const Offset(1.02, 1.02), duration: 1.seconds),

              const SizedBox(height: 40),
            ],
          ),
        ),
      ),
    );
  }

  /// Complete onboarding and navigate to appropriate screen
  Future<void> _finishOnboarding(BuildContext context, WidgetRef ref, {required bool goToPractice}) async {
    // Mark onboarding as complete
    await ref.read(onboardingProvider.notifier).completeOnboarding();

    // Navigate to appropriate destination
    if (context.mounted) {
      context.go(goToPractice ? AppRoutes.practice : AppRoutes.home);
    }
  }
}

class _RewardIndicator extends StatelessWidget {
  final String label;
  final IconData icon;
  final Color color;

  const _RewardIndicator({required this.label, required this.icon, required this.color});

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Icon(icon, color: color, size: 20),
        const SizedBox(width: 8),
        Text(
          label,
          style: TextStyle(color: color, fontWeight: FontWeight.bold),
        ),
      ],
    );
  }
}
