import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';

/// Overlay displayed when video reaches completion threshold
///
/// Shows a celebratory animation with options to continue watching
/// or go back to the previous screen.
class VideoCompletionOverlay extends StatelessWidget {
  final VoidCallback onContinue;
  final VoidCallback onGoBack;

  const VideoCompletionOverlay({
    super.key,
    required this.onContinue,
    required this.onGoBack,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Material(
      color: Colors.black87,
      child: SafeArea(
        child: Center(
          child: Padding(
            padding: const EdgeInsets.all(32),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                // Animated success icon
                _buildAnimatedIcon()
                    .animate()
                    .scale(
                      begin: const Offset(0.5, 0.5),
                      end: const Offset(1.0, 1.0),
                      duration: 500.ms,
                      curve: Curves.elasticOut,
                    ),
                const SizedBox(height: 24),

                // Title
                Text(
                  'Video Completado!',
                  style: theme.textTheme.headlineMedium?.copyWith(
                    color: Colors.white,
                    fontWeight: FontWeight.bold,
                  ),
                )
                    .animate()
                    .fadeIn(delay: 200.ms, duration: 400.ms)
                    .slideY(begin: 0.3, end: 0),

                const SizedBox(height: 12),

                // XP reward
                Container(
                  padding:
                      const EdgeInsets.symmetric(horizontal: 20, vertical: 10),
                  decoration: BoxDecoration(
                    gradient: LinearGradient(
                      colors: [
                        Colors.amber.shade600,
                        Colors.orange.shade700,
                      ],
                    ),
                    borderRadius: BorderRadius.circular(20),
                    boxShadow: [
                      BoxShadow(
                        color: Colors.amber.withOpacity(0.4),
                        blurRadius: 12,
                        offset: const Offset(0, 4),
                      ),
                    ],
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      const Icon(Icons.star, color: Colors.white, size: 24),
                      const SizedBox(width: 8),
                      const Text(
                        '+10 XP',
                        style: TextStyle(
                          color: Colors.white,
                          fontWeight: FontWeight.bold,
                          fontSize: 18,
                        ),
                      ),
                    ],
                  ),
                )
                    .animate()
                    .fadeIn(delay: 400.ms, duration: 400.ms)
                    .scale(
                      begin: const Offset(0.8, 0.8),
                      end: const Offset(1.0, 1.0),
                      delay: 400.ms,
                    ),

                const SizedBox(height: 24),

                // Description
                Text(
                  'Has visto mas del 80% del video.\nSigue asi con tu estudio!',
                  textAlign: TextAlign.center,
                  style: theme.textTheme.bodyLarge?.copyWith(
                    color: Colors.white70,
                    height: 1.5,
                  ),
                )
                    .animate()
                    .fadeIn(delay: 500.ms, duration: 400.ms),

                const SizedBox(height: 32),

                // Action buttons
                Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    // Continue watching button
                    OutlinedButton.icon(
                      onPressed: onContinue,
                      icon: const Icon(Icons.play_arrow),
                      label: const Text('Seguir viendo'),
                      style: OutlinedButton.styleFrom(
                        foregroundColor: Colors.white,
                        side: const BorderSide(color: Colors.white54),
                        padding: const EdgeInsets.symmetric(
                          horizontal: 20,
                          vertical: 12,
                        ),
                      ),
                    )
                        .animate()
                        .fadeIn(delay: 600.ms, duration: 400.ms)
                        .slideX(begin: -0.2, end: 0),

                    const SizedBox(width: 16),

                    // Go back button
                    ElevatedButton.icon(
                      onPressed: onGoBack,
                      icon: const Icon(Icons.check),
                      label: const Text('Listo'),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: Colors.green,
                        foregroundColor: Colors.white,
                        padding: const EdgeInsets.symmetric(
                          horizontal: 24,
                          vertical: 12,
                        ),
                        elevation: 4,
                      ),
                    )
                        .animate()
                        .fadeIn(delay: 600.ms, duration: 400.ms)
                        .slideX(begin: 0.2, end: 0),
                  ],
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildAnimatedIcon() {
    return Stack(
      alignment: Alignment.center,
      children: [
        // Outer glow
        Container(
          width: 120,
          height: 120,
          decoration: BoxDecoration(
            shape: BoxShape.circle,
            gradient: RadialGradient(
              colors: [
                Colors.green.withOpacity(0.3),
                Colors.green.withOpacity(0.0),
              ],
            ),
          ),
        )
            .animate(onPlay: (controller) => controller.repeat())
            .scale(
              begin: const Offset(0.9, 0.9),
              end: const Offset(1.1, 1.1),
              duration: 1500.ms,
            )
            .then()
            .scale(
              begin: const Offset(1.1, 1.1),
              end: const Offset(0.9, 0.9),
              duration: 1500.ms,
            ),

        // Inner circle
        Container(
          width: 80,
          height: 80,
          decoration: BoxDecoration(
            shape: BoxShape.circle,
            gradient: LinearGradient(
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
              colors: [
                Colors.green.shade400,
                Colors.green.shade700,
              ],
            ),
            boxShadow: [
              BoxShadow(
                color: Colors.green.withOpacity(0.5),
                blurRadius: 20,
                spreadRadius: 2,
              ),
            ],
          ),
          child: const Icon(
            Icons.check,
            color: Colors.white,
            size: 48,
          ),
        ),

        // Sparkles
        ..._buildSparkles(),
      ],
    );
  }

  List<Widget> _buildSparkles() {
    final sparkles = <Widget>[];
    final positions = [
      const Offset(-50, -40),
      const Offset(50, -35),
      const Offset(-45, 45),
      const Offset(55, 40),
      const Offset(0, -55),
      const Offset(-60, 0),
    ];

    for (var i = 0; i < positions.length; i++) {
      sparkles.add(
        Positioned(
          left: 60 + positions[i].dx,
          top: 60 + positions[i].dy,
          child: Icon(
            Icons.star,
            color: Colors.amber.shade300,
            size: 12,
          )
              .animate(
                onPlay: (controller) => controller.repeat(),
                delay: Duration(milliseconds: i * 200),
              )
              .fadeIn(duration: 300.ms)
              .then()
              .fadeOut(duration: 300.ms),
        ),
      );
    }

    return sparkles;
  }
}
