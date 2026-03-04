import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/providers/heart_provider.dart';
import '../../../../core/providers/economy_provider.dart';
import '../../../../core/services/heart_system.dart';

/// Dialogo cuando se agotan los corazones
///
/// Ofrece opciones:
/// 1. Ver anuncio (+1 corazon)
/// 2. Pagar con Oro (150 Oro = 5 corazones)
/// 3. Esperar regeneracion
/// 4. GRACE MODE (practica sin recompensas)
class HeartDepletedDialog extends ConsumerWidget {
  const HeartDepletedDialog({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final heartSystem = ref.watch(heartSystemProvider);
    final gold = ref.watch(goldProvider);
    final adsRemaining = heartSystem.adsRemainingToday;
    final timeUntilNext = heartSystem.timeUntilNextHeart;

    return Dialog(
      backgroundColor: Colors.transparent,
      child: Container(
        padding: const EdgeInsets.all(24),
        decoration: BoxDecoration(
          color: const Color(0xFF1A1A2E),
          borderRadius: BorderRadius.circular(24),
          border: Border.all(
            color: Colors.red.withOpacity(0.5),
            width: 2,
          ),
          boxShadow: [
            BoxShadow(
              color: Colors.red.withOpacity(0.3),
              blurRadius: 20,
              spreadRadius: 5,
            ),
          ],
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            // Icono de corazon roto
            const Icon(
              Icons.heart_broken,
              color: Colors.red,
              size: 64,
            ).animate().shake(duration: 500.ms),

            const SizedBox(height: 16),

            // Titulo
            const Text(
              'MANA AGOTADO',
              style: TextStyle(
                color: Colors.red,
                fontSize: 24,
                fontWeight: FontWeight.bold,
                letterSpacing: 2,
              ),
            ).animate().fadeIn(),

            const SizedBox(height: 8),

            const Text(
              'Has usado todos tus corazones.\nPero un Cazador no se rinde.',
              textAlign: TextAlign.center,
              style: TextStyle(
                color: Colors.white70,
                fontSize: 14,
              ),
            ).animate().fadeIn(delay: 100.ms),

            const SizedBox(height: 24),

            // Opcion 1: Ver anuncio
            if (adsRemaining > 0)
              _buildOptionButton(
                icon: Icons.play_circle_filled,
                iconColor: Colors.green,
                title: 'Ver Anuncio',
                subtitle: '+1 corazon (${adsRemaining} restantes hoy)',
                onTap: () async {
                  final success = await heartSystem.restoreHeartViaAd();
                  if (success && context.mounted) {
                    Navigator.pop(context, 'ad');
                  }
                },
              ).animate().fadeIn(delay: 200.ms).slideX(begin: -0.1),

            const SizedBox(height: 12),

            // Opcion 2: Pagar con Oro
            _buildOptionButton(
              icon: Icons.monetization_on,
              iconColor: Colors.amber,
              title: 'Recargar (150 Oro)',
              subtitle: gold >= 150 ? 'Restaura 5 corazones' : 'Oro insuficiente',
              enabled: gold >= 150,
              onTap: () {
                final newGold = heartSystem.restoreHeartsViaGold(gold);
                if (newGold != null) {
                  ref.read(economyProvider.notifier).spendGold(150);
                  Navigator.pop(context, 'gold');
                }
              },
            ).animate().fadeIn(delay: 300.ms).slideX(begin: -0.1),

            const SizedBox(height: 12),

            // Opcion 3: Esperar
            _buildOptionButton(
              icon: Icons.access_time,
              iconColor: Colors.blue,
              title: 'Esperar',
              subtitle: 'Proximo corazon en ${_formatDuration(timeUntilNext)}',
              onTap: () {
                Navigator.pop(context, 'wait');
              },
            ).animate().fadeIn(delay: 400.ms).slideX(begin: -0.1),

            const SizedBox(height: 24),

            // Separador con "o"
            Row(
              children: [
                Expanded(child: Divider(color: Colors.white24)),
                const Padding(
                  padding: EdgeInsets.symmetric(horizontal: 16),
                  child: Text(
                    'o',
                    style: TextStyle(color: Colors.white54),
                  ),
                ),
                Expanded(child: Divider(color: Colors.white24)),
              ],
            ),

            const SizedBox(height: 24),

            // Opcion 4: GRACE MODE (destacada)
            Container(
              width: double.infinity,
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  colors: [
                    Colors.purple.withOpacity(0.3),
                    Colors.indigo.withOpacity(0.3),
                  ],
                ),
                borderRadius: BorderRadius.circular(16),
                border: Border.all(
                  color: Colors.purple.withOpacity(0.5),
                  width: 2,
                ),
              ),
              child: Material(
                color: Colors.transparent,
                child: InkWell(
                  onTap: () {
                    heartSystem.enterGraceMode();
                    Navigator.pop(context, 'grace');
                  },
                  borderRadius: BorderRadius.circular(16),
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: Row(
                      children: [
                        Container(
                          padding: const EdgeInsets.all(12),
                          decoration: BoxDecoration(
                            color: Colors.purple.withOpacity(0.3),
                            borderRadius: BorderRadius.circular(12),
                          ),
                          child: const Icon(
                            Icons.auto_awesome,
                            color: Colors.purple,
                            size: 28,
                          ),
                        ),
                        const SizedBox(width: 16),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: const [
                              Text(
                                'MODO GRACIA',
                                style: TextStyle(
                                  color: Colors.purple,
                                  fontSize: 18,
                                  fontWeight: FontWeight.bold,
                                ),
                              ),
                              SizedBox(height: 4),
                              Text(
                                'Practica sin ganar XP ni Oro\n(Sigue aprendiendo sin penalizacion)',
                                style: TextStyle(
                                  color: Colors.white70,
                                  fontSize: 12,
                                ),
                              ),
                            ],
                          ),
                        ),
                        const Icon(
                          Icons.arrow_forward_ios,
                          color: Colors.purple,
                          size: 20,
                        ),
                      ],
                    ),
                  ),
                ),
              ),
            ).animate().fadeIn(delay: 500.ms).scale(begin: const Offset(0.95, 0.95)),
          ],
        ),
      ),
    );
  }

  Widget _buildOptionButton({
    required IconData icon,
    required Color iconColor,
    required String title,
    required String subtitle,
    required VoidCallback onTap,
    bool enabled = true,
  }) {
    return Opacity(
      opacity: enabled ? 1.0 : 0.5,
      child: Container(
        width: double.infinity,
        decoration: BoxDecoration(
          color: Colors.white.withOpacity(0.05),
          borderRadius: BorderRadius.circular(12),
          border: Border.all(
            color: Colors.white.withOpacity(0.1),
          ),
        ),
        child: Material(
          color: Colors.transparent,
          child: InkWell(
            onTap: enabled ? onTap : null,
            borderRadius: BorderRadius.circular(12),
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Row(
                children: [
                  Icon(icon, color: iconColor, size: 28),
                  const SizedBox(width: 16),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          title,
                          style: const TextStyle(
                            color: Colors.white,
                            fontSize: 16,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                        Text(
                          subtitle,
                          style: TextStyle(
                            color: Colors.white.withOpacity(0.6),
                            fontSize: 12,
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }

  String _formatDuration(Duration duration) {
    final hours = duration.inHours;
    final minutes = duration.inMinutes % 60;
    if (hours > 0) {
      return '${hours}h ${minutes}m';
    }
    return '${minutes}m';
  }
}
