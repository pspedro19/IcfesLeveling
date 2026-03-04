import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/config/app_theme.dart';
import '../providers/balance_provider.dart';

/// GoldIndicator - Displays the user's gold balance in the app bar
///
/// Features:
/// - Shows real-time gold balance from balanceProvider
/// - Loading shimmer while fetching
/// - Tap to refresh
/// - Error handling with fallback display
class GoldIndicator extends ConsumerWidget {
  const GoldIndicator({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final balanceState = ref.watch(balanceProvider);

    return balanceState.when(
      data: (balance) => _buildIndicator(context, ref, balance.gold),
      loading: () => _buildSkeleton(),
      error: (_, __) => _buildErrorIndicator(context, ref),
    );
  }

  Widget _buildIndicator(BuildContext context, WidgetRef ref, int gold) {
    return GestureDetector(
      onTap: () => _onTap(context, ref, gold),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
        decoration: BoxDecoration(
          color: AppTheme.bgCard,
          borderRadius: BorderRadius.circular(20),
          border: Border.all(color: AppTheme.secondaryGold.withOpacity(0.5)),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(
              Icons.monetization_on,
              color: AppTheme.secondaryGold,
              size: 20,
            ),
            const SizedBox(width: 4),
            Text(
              _formatGold(gold),
              style: const TextStyle(
                color: AppTheme.secondaryGold,
                fontWeight: FontWeight.bold,
                fontSize: 14,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildSkeleton() {
    return Container(
      width: 70,
      height: 28,
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: AppTheme.bgCard,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: AppTheme.secondaryGold.withOpacity(0.3)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(
            Icons.monetization_on,
            color: AppTheme.secondaryGold.withOpacity(0.5),
            size: 20,
          ),
          const SizedBox(width: 4),
          Expanded(
            child: _ShimmerEffect(
              child: Container(
                height: 14,
                decoration: BoxDecoration(
                  color: AppTheme.bgElevated,
                  borderRadius: BorderRadius.circular(4),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildErrorIndicator(BuildContext context, WidgetRef ref) {
    return GestureDetector(
      onTap: () => ref.read(balanceProvider.notifier).refresh(),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
        decoration: BoxDecoration(
          color: AppTheme.bgCard,
          borderRadius: BorderRadius.circular(20),
          border: Border.all(color: AppTheme.dangerRed.withOpacity(0.5)),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(
              Icons.monetization_on,
              color: AppTheme.secondaryGold.withOpacity(0.5),
              size: 20,
            ),
            const SizedBox(width: 4),
            const Icon(
              Icons.refresh,
              color: AppTheme.textMuted,
              size: 14,
            ),
          ],
        ),
      ),
    );
  }

  /// Format gold for display (e.g., 1000 -> 1K, 1500 -> 1.5K)
  String _formatGold(int gold) {
    if (gold >= 1000000) {
      return '${(gold / 1000000).toStringAsFixed(1)}M';
    } else if (gold >= 1000) {
      final k = gold / 1000;
      return k == k.truncate() ? '${k.truncate()}K' : '${k.toStringAsFixed(1)}K';
    }
    return gold.toString();
  }

  void _onTap(BuildContext context, WidgetRef ref, int gold) {
    showModalBottomSheet(
      context: context,
      backgroundColor: AppTheme.bgCard,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (context) => GoldDetailSheet(gold: gold),
    );
  }
}

/// Detail sheet showing gold balance with options
class GoldDetailSheet extends ConsumerWidget {
  final int gold;

  const GoldDetailSheet({super.key, required this.gold});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
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

          // Gold icon large
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: AppTheme.secondaryGold.withOpacity(0.2),
              shape: BoxShape.circle,
            ),
            child: const Icon(
              Icons.monetization_on,
              color: AppTheme.secondaryGold,
              size: 48,
            ),
          ),
          const SizedBox(height: 16),

          // Balance
          Text(
            '$gold',
            style: const TextStyle(
              fontSize: 36,
              fontWeight: FontWeight.bold,
              color: AppTheme.secondaryGold,
            ),
          ),
          const Text(
            'Monedas de Oro',
            style: TextStyle(color: AppTheme.textSecondary),
          ),

          const SizedBox(height: 24),

          // Info
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: AppTheme.bgElevated,
              borderRadius: BorderRadius.circular(12),
            ),
            child: Column(
              children: [
                _buildInfoRow(
                  icon: Icons.shopping_bag_outlined,
                  title: 'Tienda',
                  subtitle: 'Compra power-ups y mejoras',
                ),
                const SizedBox(height: 12),
                _buildInfoRow(
                  icon: Icons.favorite_outline,
                  title: 'Corazones',
                  subtitle: 'Recarga corazones con oro',
                ),
                const SizedBox(height: 12),
                _buildInfoRow(
                  icon: Icons.local_fire_department_outlined,
                  title: 'Racha',
                  subtitle: 'Repara tu racha si la pierdes',
                ),
              ],
            ),
          ),

          const SizedBox(height: 24),

          // Refresh button
          TextButton.icon(
            onPressed: () {
              ref.read(balanceProvider.notifier).refresh();
              Navigator.pop(context);
            },
            icon: const Icon(Icons.refresh),
            label: const Text('Actualizar saldo'),
          ),

          const SizedBox(height: 16),
        ],
      ),
    );
  }

  Widget _buildInfoRow({
    required IconData icon,
    required String title,
    required String subtitle,
  }) {
    return Row(
      children: [
        Icon(icon, color: AppTheme.textMuted, size: 24),
        const SizedBox(width: 12),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                title,
                style: const TextStyle(fontWeight: FontWeight.bold),
              ),
              Text(
                subtitle,
                style: const TextStyle(
                  color: AppTheme.textSecondary,
                  fontSize: 12,
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }
}

/// Simple shimmer effect widget for loading state
class _ShimmerEffect extends StatefulWidget {
  final Widget child;

  const _ShimmerEffect({required this.child});

  @override
  State<_ShimmerEffect> createState() => _ShimmerEffectState();
}

class _ShimmerEffectState extends State<_ShimmerEffect>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  late Animation<double> _animation;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      duration: const Duration(milliseconds: 1500),
      vsync: this,
    )..repeat();
    _animation = Tween<double>(begin: 0.3, end: 0.7).animate(
      CurvedAnimation(parent: _controller, curve: Curves.easeInOut),
    );
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _animation,
      builder: (context, child) {
        return Opacity(
          opacity: _animation.value,
          child: widget.child,
        );
      },
    );
  }
}
