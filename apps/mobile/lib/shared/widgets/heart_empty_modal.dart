import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../features/engagement/presentation/providers/engagement_provider.dart';

/// A modal bottom sheet displayed when the user runs out of "Mana" (hearts).
/// It provides several options to the user, such as watching an ad to refill hearts,
/// entering grace mode to continue practicing without XP, or waiting for regeneration.
class HeartEmptyModal extends ConsumerWidget {
  const HeartEmptyModal({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    // Watch engagement provider for grace mode activation
    ref.watch(engagementProvider);

    return Container(
      padding: const EdgeInsets.all(24),
      decoration: const BoxDecoration(
        color: Color(0xFF1A1A1A),
        borderRadius: BorderRadius.only(
          topLeft: Radius.circular(32),
          topRight: Radius.circular(32),
        ),
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Container(
            width: 40,
            height: 4,
            decoration: BoxDecoration(
              color: Colors.white24,
              borderRadius: BorderRadius.circular(2),
            ),
          ),
          const SizedBox(height: 32),
          
          const Icon(Icons.heart_broken, color: Colors.red, size: 64),
          const SizedBox(height: 24),
          
          const Text(
            "¡TE HAS QUEDADO SIN MANA!",
            textAlign: TextAlign.center,
            style: TextStyle(
              color: Colors.white,
              fontSize: 22,
              fontWeight: FontWeight.w900,
              letterSpacing: 1,
            ),
          ),
          
          const SizedBox(height: 12),
          
          const Text(
            "Los cazadores necesitan energía para ganar XP y subir de rango. ¿Cómo quieres proceder?",
            textAlign: TextAlign.center,
            style: TextStyle(color: Colors.grey, fontSize: 16),
          ),
          
          const SizedBox(height: 32),
          
          // Option 1: Ads
          _ModalOption(
            icon: Icons.play_circle_outline,
            title: "VER ANUNCIO",
            subtitle: "Recupera 1 corazón (3 hoy)",
            color: Colors.green,
            onTap: () {
              // Trigger Ad Logic
              Navigator.pop(context);
            },
          ),
          
          const SizedBox(height: 16),
          
          // Option 2: Grace Mode
          _ModalOption(
            icon: Icons.security,
            title: "MODO ENTRENAMIENTO",
            subtitle: "Sigue practicando sin ganar XP ni Oro",
            color: Colors.purple,
            onTap: () {
              ref.read(engagementProvider.notifier).activateGraceMode();
              Navigator.pop(context);
            },
          ),
          
          const SizedBox(height: 16),
          
          // Option 3: Premium
          _ModalOption(
            icon: Icons.bolt,
            title: "MANA INFINITO",
            subtitle: "Desbloquea todo el potencial con Premium",
            color: Colors.blue,
            onTap: () {
              // Navigate to Shop/Premium
              Navigator.pop(context);
            },
          ),
          
          const SizedBox(height: 32),
          
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text("ESPERAR REGENERACIÓN", style: TextStyle(color: Colors.white38)),
          ),
          
          const SizedBox(height: 20),
        ],
      ),
    );
  }
}

/// A reusable option tile used within the [HeartEmptyModal] to present choices
/// to the user. Each option includes an icon, title, subtitle, and a tap handler.
///
/// [icon] The leading icon for the option.
/// [title] The main title text for the option.
/// [subtitle] A secondary, descriptive text for the option.
/// [color] The primary color associated with this option (used for icon and title).
/// [onTap] Callback function to be executed when the option tile is tapped.
class _ModalOption extends StatelessWidget {
  final IconData icon;
  final String title;
  final String subtitle;
  final Color color;
  final VoidCallback onTap;

  const _ModalOption({
    required this.icon,
    required this.title,
    required this.subtitle,
    required this.color,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(16),
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: Colors.white.withOpacity(0.05),
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: color.withOpacity(0.3)),
        ),
        child: Row(
          children: [
            Container(
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: color.withOpacity(0.1),
                shape: BoxShape.circle,
              ),
              child: Icon(icon, color: color, size: 24),
            ),
            const SizedBox(width: 16),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    title,
                    style: TextStyle(color: color, fontWeight: FontWeight.bold, letterSpacing: 1),
                  ),
                  Text(
                    subtitle,
                    style: const TextStyle(color: Colors.grey, fontSize: 12),
                  ),
                ],
              ),
            ),
            const Icon(Icons.chevron_right, color: Colors.white24),
          ],
        ),
      ),
    );
  }
}
