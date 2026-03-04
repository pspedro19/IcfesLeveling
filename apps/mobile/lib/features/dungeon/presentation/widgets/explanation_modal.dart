import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';

/// Modal de Explicacion de Respuesta Incorrecta
///
/// Muestra la respuesta correcta y una explicacion detallada.
/// PRINCIPIO: "Siempre explicar errores"
class ExplanationModal extends StatelessWidget {
  final String correctAnswer;
  final String explanation;
  final String? videoUrl;
  final VoidCallback onContinue;

  const ExplanationModal({
    super.key,
    required this.correctAnswer,
    required this.explanation,
    this.videoUrl,
    required this.onContinue,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: const Color(0xFF1A1A2E),
        borderRadius: const BorderRadius.vertical(top: Radius.circular(24)),
        border: Border.all(
          color: Colors.amber.withOpacity(0.3),
          width: 1,
        ),
      ),
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Header con icono de libro
            Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(
                    color: Colors.amber.withOpacity(0.2),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: const Icon(
                    Icons.menu_book,
                    color: Colors.amber,
                    size: 24,
                  ),
                ),
                const SizedBox(width: 12),
                const Expanded(
                  child: Text(
                    'Analiza el Error',
                    style: TextStyle(
                      color: Colors.amber,
                      fontSize: 20,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
              ],
            ).animate().fadeIn(duration: 200.ms).slideY(begin: 0.1),

            const SizedBox(height: 20),

            // Respuesta correcta
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: Colors.green.withOpacity(0.15),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(
                  color: Colors.green.withOpacity(0.5),
                  width: 1,
                ),
              ),
              child: Row(
                children: [
                  const Icon(
                    Icons.check_circle,
                    color: Colors.green,
                    size: 24,
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text(
                          'Respuesta Correcta:',
                          style: TextStyle(
                            color: Colors.green,
                            fontSize: 12,
                            fontWeight: FontWeight.w500,
                          ),
                        ),
                        const SizedBox(height: 4),
                        Text(
                          correctAnswer,
                          style: const TextStyle(
                            color: Colors.white,
                            fontSize: 16,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ).animate().fadeIn(duration: 300.ms, delay: 100.ms).slideY(begin: 0.1),

            const SizedBox(height: 16),

            // Explicacion
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: Colors.white.withOpacity(0.05),
                borderRadius: BorderRadius.circular(12),
              ),
              child: Text(
                explanation,
                style: const TextStyle(
                  color: Colors.white70,
                  fontSize: 14,
                  height: 1.5,
                ),
              ),
            ).animate().fadeIn(duration: 300.ms, delay: 200.ms),

            // Video opcional
            if (videoUrl != null) ...[
              const SizedBox(height: 16),
              OutlinedButton.icon(
                onPressed: () {
                  // TODO: Abrir reproductor de video
                },
                icon: const Icon(Icons.play_circle_outline),
                label: const Text('Ver Video Explicativo'),
                style: OutlinedButton.styleFrom(
                  foregroundColor: Colors.cyan,
                  side: const BorderSide(color: Colors.cyan),
                  padding: const EdgeInsets.symmetric(
                    horizontal: 20,
                    vertical: 12,
                  ),
                ),
              ).animate().fadeIn(duration: 300.ms, delay: 300.ms),
            ],

            const SizedBox(height: 24),

            // Boton continuar
            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                onPressed: onContinue,
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.amber,
                  foregroundColor: Colors.black,
                  padding: const EdgeInsets.symmetric(vertical: 16),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                ),
                child: const Text(
                  'CONTINUAR',
                  style: TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
            ).animate().fadeIn(duration: 300.ms, delay: 400.ms).slideY(begin: 0.1),
          ],
        ),
      ),
    );
  }

  /// Muestra el modal como bottom sheet
  static Future<void> show({
    required BuildContext context,
    required String correctAnswer,
    required String explanation,
    String? videoUrl,
    required VoidCallback onContinue,
  }) {
    return showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      isDismissible: false,
      enableDrag: false,
      builder: (ctx) => ExplanationModal(
        correctAnswer: correctAnswer,
        explanation: explanation,
        videoUrl: videoUrl,
        onContinue: () {
          Navigator.pop(ctx);
          onContinue();
        },
      ),
    );
  }
}
