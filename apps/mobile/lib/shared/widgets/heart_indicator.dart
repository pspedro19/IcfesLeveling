import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/config/app_theme.dart';
import '../providers/hearts_provider.dart';
import '../providers/balance_provider.dart';

class HeartIndicator extends ConsumerWidget {
  const HeartIndicator({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final heartsState = ref.watch(heartsProvider);

    return heartsState.when(
      data: (hearts) => _buildIndicator(context, hearts),
      loading: () => _buildSkeleton(),
      error: (_, __) => _buildIndicator(context, HeartsState.empty()),
    );
  }

  Widget _buildIndicator(BuildContext context, HeartsState hearts) {
    final isLow = hearts.current <= 1;
    final isEmpty = hearts.current == 0;

    return GestureDetector(
      onTap: () => _showHeartsDialog(context, hearts),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
        decoration: BoxDecoration(
          color: isEmpty
              ? AppTheme.dangerRed.withOpacity(0.2)
              : AppTheme.bgCard,
          borderRadius: BorderRadius.circular(20),
          border: isLow
              ? Border.all(color: AppTheme.dangerRed, width: 1)
              : null,
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            // Icono de corazon con animacion
            TweenAnimationBuilder<double>(
              tween: Tween(begin: 1.0, end: isLow ? 1.2 : 1.0),
              duration: const Duration(milliseconds: 500),
              builder: (context, scale, child) {
                return Transform.scale(
                  scale: scale,
                  child: Icon(
                    isEmpty ? Icons.favorite_border : Icons.favorite,
                    color: AppTheme.dangerRed,
                    size: 20,
                  ),
                );
              },
            ),
            const SizedBox(width: 4),
            // Contador
            Text(
              '${hearts.current}/${hearts.max}',
              style: TextStyle(
                color: isEmpty ? AppTheme.dangerRed : AppTheme.textPrimary,
                fontWeight: FontWeight.bold,
                fontSize: 14,
              ),
            ),
            // Timer de regeneracion
            if (hearts.current < hearts.max && hearts.nextRegenIn != null) ...[
              const SizedBox(width: 4),
              const Icon(
                Icons.timer_outlined,
                size: 12,
                color: AppTheme.textMuted,
              ),
              const SizedBox(width: 2),
              Text(
                _formatTime(hearts.nextRegenIn!),
                style: const TextStyle(
                  color: AppTheme.textMuted,
                  fontSize: 10,
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildSkeleton() {
    return Container(
      width: 60,
      height: 28,
      decoration: BoxDecoration(
        color: AppTheme.bgCard,
        borderRadius: BorderRadius.circular(20),
      ),
    );
  }

  String _formatTime(Duration duration) {
    final hours = duration.inHours;
    final minutes = duration.inMinutes % 60;
    if (hours > 0) {
      return '${hours}h ${minutes}m';
    }
    return '${minutes}m';
  }

  void _showHeartsDialog(BuildContext context, HeartsState hearts) {
    showModalBottomSheet(
      context: context,
      backgroundColor: AppTheme.bgCard,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (context) => HeartsDetailSheet(hearts: hearts),
    );
  }
}

class HeartsDetailSheet extends ConsumerWidget {
  final HeartsState hearts;

  const HeartsDetailSheet({super.key, required this.hearts});

  static const int goldCostForRefill = 150;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final balanceState = ref.watch(balanceProvider);
    final userGold = balanceState.maybeWhen(
      data: (balance) => balance.gold,
      orElse: () => 0,
    );
    final canAffordRefill = userGold >= goldCostForRefill;

    return Padding(
      padding: const EdgeInsets.all(24),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          // Handle
          Container(
            width: 40,
            height: 4,
            decoration: BoxDecoration(
              color: AppTheme.textMuted,
              borderRadius: BorderRadius.circular(2),
            ),
          ),
          const SizedBox(height: 24),

          // Corazones grandes
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: List.generate(hearts.max, (index) {
              final isFilled = index < hearts.current;
              return Padding(
                padding: const EdgeInsets.symmetric(horizontal: 4),
                child: Icon(
                  isFilled ? Icons.favorite : Icons.favorite_border,
                  color: isFilled ? AppTheme.dangerRed : AppTheme.textMuted,
                  size: 40,
                ),
              );
            }),
          ),
          const SizedBox(height: 16),

          // Info de regeneracion
          if (hearts.current < hearts.max && hearts.nextRegenIn != null)
            Text(
              'Siguiente corazon en ${_formatTime(hearts.nextRegenIn!)}',
              style: const TextStyle(color: AppTheme.textSecondary),
            ),
          if (hearts.current == hearts.max)
            const Text(
              'Corazones completos!',
              style: TextStyle(color: AppTheme.successGreen),
            ),

          const SizedBox(height: 24),

          // Opciones de refill
          if (hearts.current < hearts.max) ...[
            // Ver anuncio
            if (hearts.adsWatchedToday < 3)
              _buildRefillOption(
                context,
                ref,
                icon: Icons.play_circle_outline,
                title: 'Ver anuncio',
                subtitle: 'Gratis (${3 - hearts.adsWatchedToday} restantes hoy)',
                onTap: () => _watchAd(context, ref),
              ),

            const SizedBox(height: 12),

            // Comprar con oro - now shows user's current balance
            _buildGoldRefillOption(
              context,
              ref,
              userGold: userGold,
              canAfford: canAffordRefill,
            ),
          ],

          const SizedBox(height: 24),
        ],
      ),
    );
  }

  Widget _buildRefillOption(
    BuildContext context,
    WidgetRef ref, {
    required IconData icon,
    required String title,
    required String subtitle,
    required VoidCallback onTap,
  }) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(12),
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: AppTheme.bgElevated,
          borderRadius: BorderRadius.circular(12),
        ),
        child: Row(
          children: [
            Icon(icon, color: AppTheme.primaryPurple, size: 32),
            const SizedBox(width: 16),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(title, style: const TextStyle(fontWeight: FontWeight.bold)),
                  Text(subtitle, style: const TextStyle(color: AppTheme.textSecondary, fontSize: 12)),
                ],
              ),
            ),
            const Icon(Icons.chevron_right, color: AppTheme.textMuted),
          ],
        ),
      ),
    );
  }

  Widget _buildGoldRefillOption(
    BuildContext context,
    WidgetRef ref, {
    required int userGold,
    required bool canAfford,
  }) {
    return InkWell(
      onTap: canAfford ? () => _buyWithGold(context, ref) : null,
      borderRadius: BorderRadius.circular(12),
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: AppTheme.bgElevated,
          borderRadius: BorderRadius.circular(12),
          border: canAfford ? null : Border.all(color: AppTheme.dangerRed.withOpacity(0.3)),
        ),
        child: Row(
          children: [
            Icon(
              Icons.monetization_on_outlined,
              color: canAfford ? AppTheme.primaryPurple : AppTheme.textMuted,
              size: 32,
            ),
            const SizedBox(width: 16),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Recargar con Oro',
                    style: TextStyle(
                      fontWeight: FontWeight.bold,
                      color: canAfford ? AppTheme.textPrimary : AppTheme.textMuted,
                    ),
                  ),
                  Row(
                    children: [
                      Text(
                        '$goldCostForRefill Oro = 5 corazones',
                        style: TextStyle(
                          color: canAfford ? AppTheme.textSecondary : AppTheme.textMuted,
                          fontSize: 12,
                        ),
                      ),
                      const SizedBox(width: 8),
                      Text(
                        '(Tienes: $userGold)',
                        style: TextStyle(
                          color: canAfford ? AppTheme.secondaryGold : AppTheme.dangerRed,
                          fontSize: 12,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ],
                  ),
                  if (!canAfford)
                    const Padding(
                      padding: EdgeInsets.only(top: 4),
                      child: Text(
                        'Oro insuficiente',
                        style: TextStyle(color: AppTheme.dangerRed, fontSize: 11),
                      ),
                    ),
                ],
              ),
            ),
            Row(
              children: [
                Icon(
                  Icons.monetization_on,
                  color: canAfford ? AppTheme.secondaryGold : AppTheme.textMuted,
                  size: 16,
                ),
                const SizedBox(width: 4),
                Text(
                  '$goldCostForRefill',
                  style: TextStyle(
                    color: canAfford ? AppTheme.secondaryGold : AppTheme.textMuted,
                  ),
                ),
              ],
            ),
            Icon(
              Icons.chevron_right,
              color: canAfford ? AppTheme.textMuted : AppTheme.textMuted.withOpacity(0.5),
            ),
          ],
        ),
      ),
    );
  }

  String _formatTime(Duration duration) {
    final hours = duration.inHours;
    final minutes = duration.inMinutes % 60;
    if (hours > 0) return '${hours}h ${minutes}m';
    return '${minutes}m';
  }

  Future<void> _watchAd(BuildContext context, WidgetRef ref) async {
    Navigator.pop(context);

    // Show loading indicator
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('Cargando anuncio...'), duration: Duration(seconds: 1)),
    );

    // Call API to refill with ad
    final success = await ref.read(heartsProvider.notifier).refillWithAd();

    if (context.mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(success ? 'Corazones recargados!' : 'Error al recargar corazones'),
          backgroundColor: success ? AppTheme.successGreen : AppTheme.dangerRed,
        ),
      );
    }
  }

  Future<void> _buyWithGold(BuildContext context, WidgetRef ref) async {
    Navigator.pop(context);

    // Call API to refill with gold (this now also updates balance)
    final success = await ref.read(heartsProvider.notifier).refillWithGold();

    if (context.mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(success ? 'Corazones recargados!' : 'Oro insuficiente o error'),
          backgroundColor: success ? AppTheme.successGreen : AppTheme.dangerRed,
        ),
      );
    }
  }
}
