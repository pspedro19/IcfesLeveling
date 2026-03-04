import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:go_router/go_router.dart';
import '../../../../core/config/routes.dart';

/// Step 4 intro screen: Prepares user for quick diagnostic
/// Per LOGICA_DE_NEGOCIO.md: Shows evaluation preview before starting
class DiagnosticIntroPage extends StatelessWidget {
  const DiagnosticIntroPage({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0A0A0A),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            children: [
              const Spacer(),

              // Lightning icon with glow effect
              Container(
                width: 100,
                height: 100,
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
                      color: Colors.blue.withOpacity(0.4),
                      blurRadius: 30,
                      spreadRadius: 5,
                    ),
                  ],
                ),
                child: const Icon(
                  Icons.bolt,
                  size: 50,
                  color: Colors.white,
                ),
              ).animate()
                .scale(duration: 600.ms, curve: Curves.elasticOut)
                .then()
                .shimmer(duration: 1500.ms, color: Colors.white.withOpacity(0.3)),

              const SizedBox(height: 40),

              // Title
              const Text(
                "EVALUACIÓN DE PODER INICIAL",
                textAlign: TextAlign.center,
                style: TextStyle(
                  color: Colors.white,
                  fontSize: 24,
                  fontWeight: FontWeight.w900,
                  letterSpacing: 2,
                ),
              ).animate().fadeIn(delay: 200.ms).slideY(begin: 0.3),

              const SizedBox(height: 16),

              // Subtitle
              Text(
                "El Sistema medirá tu fuerza actual, Cazador.",
                textAlign: TextAlign.center,
                style: TextStyle(
                  color: Colors.white.withOpacity(0.7),
                  fontSize: 16,
                  fontWeight: FontWeight.w300,
                  letterSpacing: 1,
                ),
              ).animate().fadeIn(delay: 400.ms),

              const SizedBox(height: 48),

              // Info cards
              _InfoCard(
                icon: Icons.quiz_outlined,
                text: "15 preguntas mixtas",
                delay: 500,
              ),
              const SizedBox(height: 12),
              _InfoCard(
                icon: Icons.timer_outlined,
                text: "~5 minutos",
                delay: 600,
              ),
              const SizedBox(height: 12),
              _InfoCard(
                icon: Icons.lightbulb_outline,
                text: "Responde lo mejor que puedas",
                delay: 700,
              ),

              const SizedBox(height: 24),

              // Additional note
              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: Colors.blue.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(
                    color: Colors.blue.withOpacity(0.2),
                  ),
                ),
                child: Row(
                  children: [
                    Icon(
                      Icons.info_outline,
                      color: Colors.blue.shade300,
                      size: 20,
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Text(
                        "No hay respuestas incorrectas. El objetivo es calibrar tu nivel inicial.",
                        style: TextStyle(
                          color: Colors.white.withOpacity(0.8),
                          fontSize: 13,
                          height: 1.4,
                        ),
                      ),
                    ),
                  ],
                ),
              ).animate().fadeIn(delay: 800.ms),

              const Spacer(),

              // Start button
              SizedBox(
                width: double.infinity,
                height: 56,
                child: ElevatedButton(
                  onPressed: () => context.go(AppRoutes.diagnosticQuick),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.blue.shade600,
                    foregroundColor: Colors.white,
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(16),
                    ),
                    elevation: 0,
                  ),
                  child: const Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Text(
                        "INICIAR EVALUACIÓN",
                        style: TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.bold,
                          letterSpacing: 2,
                        ),
                      ),
                      SizedBox(width: 8),
                      Icon(Icons.arrow_forward, size: 20),
                    ],
                  ),
                ),
              ).animate().fadeIn(delay: 1000.ms).slideY(begin: 0.3),

              const SizedBox(height: 16),

              // Skip option (optional, for returning users)
              TextButton(
                onPressed: () => context.go(AppRoutes.home),
                child: Text(
                  "Omitir por ahora",
                  style: TextStyle(
                    color: Colors.white.withOpacity(0.4),
                    fontSize: 14,
                  ),
                ),
              ).animate().fadeIn(delay: 1200.ms),

              const SizedBox(height: 20),
            ],
          ),
        ),
      ),
    );
  }
}

class _InfoCard extends StatelessWidget {
  final IconData icon;
  final String text;
  final int delay;

  const _InfoCard({
    required this.icon,
    required this.text,
    required this.delay,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.03),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: Colors.white.withOpacity(0.08),
        ),
      ),
      child: Row(
        children: [
          Container(
            width: 40,
            height: 40,
            decoration: BoxDecoration(
              color: Colors.blue.withOpacity(0.1),
              borderRadius: BorderRadius.circular(10),
            ),
            child: Icon(
              icon,
              color: Colors.blue.shade300,
              size: 22,
            ),
          ),
          const SizedBox(width: 16),
          Text(
            text,
            style: const TextStyle(
              color: Colors.white,
              fontSize: 16,
              fontWeight: FontWeight.w500,
            ),
          ),
        ],
      ),
    ).animate().fadeIn(delay: Duration(milliseconds: delay)).slideX(begin: 0.1);
  }
}
