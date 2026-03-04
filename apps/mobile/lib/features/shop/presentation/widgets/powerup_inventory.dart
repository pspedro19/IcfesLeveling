import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_animate/flutter_animate.dart';
import '../providers/shop_provider.dart';

/// Widget that displays owned but unused power-ups with activation functionality
class PowerupInventory extends ConsumerWidget {
  const PowerupInventory({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(shopProvider);
    final ownedPowerUps = state.ownedPowerUps;

    if (state.isLoadingPowerUps && ownedPowerUps.isEmpty) {
      return _buildLoadingState();
    }

    if (ownedPowerUps.isEmpty) {
      return _buildEmptyState();
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Container(
              padding: const EdgeInsets.all(6),
              decoration: BoxDecoration(
                color: Colors.orange.withOpacity(0.2),
                borderRadius: BorderRadius.circular(8),
              ),
              child: const Icon(
                Icons.inventory_2,
                color: Colors.orangeAccent,
                size: 16,
              ),
            ),
            const SizedBox(width: 8),
            const Text(
              "TU INVENTARIO DE POWER-UPS",
              style: TextStyle(
                color: Colors.orangeAccent,
                fontWeight: FontWeight.bold,
                letterSpacing: 2,
                fontSize: 12,
              ),
            ),
          ],
        ).animate().fadeIn().slideX(begin: -0.1),
        const SizedBox(height: 16),
        GridView.builder(
          shrinkWrap: true,
          physics: const NeverScrollableScrollPhysics(),
          gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
            crossAxisCount: 2,
            childAspectRatio: 1.1,
            crossAxisSpacing: 12,
            mainAxisSpacing: 12,
          ),
          itemCount: ownedPowerUps.length,
          itemBuilder: (context, index) {
            final powerUp = ownedPowerUps[index];
            return _PowerUpInventoryItem(
              powerUp: powerUp,
              index: index,
            );
          },
        ),
        // Error message
        if (state.powerUpError != null)
          Container(
            margin: const EdgeInsets.only(top: 12),
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: Colors.redAccent.withOpacity(0.1),
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: Colors.redAccent.withOpacity(0.3)),
            ),
            child: Row(
              children: [
                const Icon(Icons.error_outline, color: Colors.redAccent, size: 18),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    state.powerUpError!,
                    style: const TextStyle(color: Colors.redAccent, fontSize: 12),
                  ),
                ),
                IconButton(
                  icon: const Icon(Icons.close, size: 16),
                  color: Colors.redAccent,
                  onPressed: () {
                    ref.read(shopProvider.notifier).clearPowerUpError();
                  },
                ),
              ],
            ),
          ).animate().fadeIn().shake(),
        // Success message
        if (state.activationSuccess != null)
          Container(
            margin: const EdgeInsets.only(top: 12),
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: Colors.greenAccent.withOpacity(0.1),
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: Colors.greenAccent.withOpacity(0.3)),
            ),
            child: Row(
              children: [
                const Icon(Icons.check_circle, color: Colors.greenAccent, size: 18),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    state.activationSuccess!,
                    style: const TextStyle(color: Colors.greenAccent, fontSize: 12),
                  ),
                ),
                IconButton(
                  icon: const Icon(Icons.close, size: 16),
                  color: Colors.greenAccent,
                  onPressed: () {
                    ref.read(shopProvider.notifier).clearActivationSuccess();
                  },
                ),
              ],
            ),
          ).animate().fadeIn().scale(),
      ],
    );
  }

  Widget _buildLoadingState() {
    return Container(
      height: 150,
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.02),
        borderRadius: BorderRadius.circular(16),
      ),
      child: const Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            CircularProgressIndicator(
              strokeWidth: 2,
              color: Colors.orangeAccent,
            ),
            SizedBox(height: 12),
            Text(
              "Cargando power-ups...",
              style: TextStyle(color: Colors.white54, fontSize: 12),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildEmptyState() {
    return Container(
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.02),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.white.withOpacity(0.05)),
      ),
      child: Column(
        children: [
          Icon(
            Icons.inventory_2_outlined,
            size: 48,
            color: Colors.white.withOpacity(0.2),
          ),
          const SizedBox(height: 12),
          Text(
            "Sin power-ups",
            style: TextStyle(
              color: Colors.white.withOpacity(0.5),
              fontWeight: FontWeight.bold,
              fontSize: 14,
            ),
          ),
          const SizedBox(height: 4),
          Text(
            "Compra power-ups en la tienda para potenciar tu aprendizaje",
            textAlign: TextAlign.center,
            style: TextStyle(
              color: Colors.white.withOpacity(0.3),
              fontSize: 12,
            ),
          ),
        ],
      ),
    );
  }
}

class _PowerUpInventoryItem extends ConsumerStatefulWidget {
  final OwnedPowerUp powerUp;
  final int index;

  const _PowerUpInventoryItem({
    required this.powerUp,
    required this.index,
  });

  @override
  ConsumerState<_PowerUpInventoryItem> createState() => _PowerUpInventoryItemState();
}

class _PowerUpInventoryItemState extends ConsumerState<_PowerUpInventoryItem>
    with SingleTickerProviderStateMixin {
  late AnimationController _activationController;
  late Animation<double> _pulseAnimation;
  bool _isActivating = false;

  @override
  void initState() {
    super.initState();
    _activationController = AnimationController(
      duration: const Duration(milliseconds: 1500),
      vsync: this,
    );
    _pulseAnimation = Tween<double>(begin: 1.0, end: 1.15).animate(
      CurvedAnimation(parent: _activationController, curve: Curves.easeInOut),
    );
  }

  @override
  void dispose() {
    _activationController.dispose();
    super.dispose();
  }

  IconData _getIconForType(String type) {
    switch (type) {
      case 'xp_boost':
        return Icons.trending_up;
      case 'hint_token':
        return Icons.lightbulb;
      case 'streak_freeze':
        return Icons.ac_unit;
      case 'double_coins':
        return Icons.monetization_on;
      case 'shield':
        return Icons.shield;
      case 'time_freezer':
        return Icons.timer_off;
      default:
        return Icons.flash_on;
    }
  }

  Color _getColorForType(String type) {
    switch (type) {
      case 'xp_boost':
        return Colors.purpleAccent;
      case 'hint_token':
        return Colors.amber;
      case 'streak_freeze':
        return Colors.cyanAccent;
      case 'double_coins':
        return Colors.yellow;
      case 'shield':
        return Colors.blueAccent;
      case 'time_freezer':
        return Colors.tealAccent;
      default:
        return Colors.greenAccent;
    }
  }

  String _formatDuration(int? seconds) {
    if (seconds == null) return '';
    if (seconds >= 3600) {
      final hours = seconds ~/ 3600;
      return '${hours}h';
    } else if (seconds >= 60) {
      final minutes = seconds ~/ 60;
      return '${minutes}m';
    }
    return '${seconds}s';
  }

  Future<void> _handleActivate() async {
    if (_isActivating) return;

    setState(() => _isActivating = true);
    _activationController.repeat(reverse: true);

    // Haptic feedback
    HapticFeedback.mediumImpact();

    final success = await ref.read(shopProvider.notifier).activatePowerUp(widget.powerUp.id);

    if (success && mounted) {
      // Success haptic
      HapticFeedback.heavyImpact();
    }

    if (mounted) {
      _activationController.stop();
      _activationController.reset();
      setState(() => _isActivating = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final color = _getColorForType(widget.powerUp.type);
    final icon = _getIconForType(widget.powerUp.type);
    final isActivatingGlobal = ref.watch(shopProvider).isActivatingPowerUp;

    return AnimatedBuilder(
      animation: _pulseAnimation,
      builder: (context, child) {
        return Transform.scale(
          scale: _isActivating ? _pulseAnimation.value : 1.0,
          child: child,
        );
      },
      child: Container(
        decoration: BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
            colors: [
              color.withOpacity(0.1),
              color.withOpacity(0.03),
            ],
          ),
          borderRadius: BorderRadius.circular(16),
          border: Border.all(
            color: _isActivating
                ? color.withOpacity(0.8)
                : color.withOpacity(0.2),
            width: _isActivating ? 2 : 1,
          ),
          boxShadow: _isActivating
              ? [
                  BoxShadow(
                    color: color.withOpacity(0.4),
                    blurRadius: 16,
                    spreadRadius: 2,
                  ),
                ]
              : null,
        ),
        child: Material(
          color: Colors.transparent,
          child: InkWell(
            onTap: (isActivatingGlobal || widget.powerUp.quantity <= 0)
                ? null
                : _handleActivate,
            borderRadius: BorderRadius.circular(16),
            child: Padding(
              padding: const EdgeInsets.all(12),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Container(
                        padding: const EdgeInsets.all(8),
                        decoration: BoxDecoration(
                          color: color.withOpacity(0.2),
                          borderRadius: BorderRadius.circular(10),
                        ),
                        child: Icon(icon, color: color, size: 22),
                      ),
                      const Spacer(),
                      // Quantity badge
                      Container(
                        padding: const EdgeInsets.symmetric(
                          horizontal: 8,
                          vertical: 4,
                        ),
                        decoration: BoxDecoration(
                          color: Colors.white.withOpacity(0.1),
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: Text(
                          'x${widget.powerUp.quantity}',
                          style: const TextStyle(
                            color: Colors.white,
                            fontWeight: FontWeight.bold,
                            fontSize: 12,
                          ),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 10),
                  Text(
                    widget.powerUp.name,
                    style: TextStyle(
                      color: color,
                      fontWeight: FontWeight.bold,
                      fontSize: 13,
                    ),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                  const SizedBox(height: 2),
                  if (widget.powerUp.duration != null)
                    Text(
                      'Duracion: ${_formatDuration(widget.powerUp.duration)}',
                      style: TextStyle(
                        color: Colors.white.withOpacity(0.5),
                        fontSize: 10,
                      ),
                    ),
                  const Spacer(),
                  // Activate button
                  SizedBox(
                    width: double.infinity,
                    child: ElevatedButton(
                      onPressed: (isActivatingGlobal || widget.powerUp.quantity <= 0)
                          ? null
                          : _handleActivate,
                      style: ElevatedButton.styleFrom(
                        backgroundColor: color.withOpacity(0.2),
                        foregroundColor: color,
                        elevation: 0,
                        padding: const EdgeInsets.symmetric(vertical: 8),
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(8),
                          side: BorderSide(color: color.withOpacity(0.3)),
                        ),
                        disabledBackgroundColor: Colors.white.withOpacity(0.05),
                        disabledForegroundColor: Colors.white30,
                      ),
                      child: _isActivating
                          ? SizedBox(
                              height: 14,
                              width: 14,
                              child: CircularProgressIndicator(
                                strokeWidth: 2,
                                color: color,
                              ),
                            )
                          : Row(
                              mainAxisAlignment: MainAxisAlignment.center,
                              children: [
                                Icon(Icons.flash_on, size: 14),
                                const SizedBox(width: 4),
                                const Text(
                                  'ACTIVAR',
                                  style: TextStyle(
                                    fontWeight: FontWeight.bold,
                                    fontSize: 11,
                                    letterSpacing: 1,
                                  ),
                                ),
                              ],
                            ),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    )
        .animate(delay: Duration(milliseconds: widget.index * 100))
        .fadeIn()
        .scale(begin: const Offset(0.9, 0.9));
  }
}

/// Compact list view for power-up inventory
class PowerupInventoryList extends ConsumerWidget {
  final int? maxItems;

  const PowerupInventoryList({
    super.key,
    this.maxItems,
  });

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final ownedPowerUps = ref.watch(ownedPowerUpsProvider);
    final displayPowerUps = maxItems != null
        ? ownedPowerUps.take(maxItems!).toList()
        : ownedPowerUps;

    if (displayPowerUps.isEmpty) {
      return const SizedBox.shrink();
    }

    return Column(
      children: displayPowerUps.asMap().entries.map((entry) {
        final powerUp = entry.value;
        return _PowerUpListItem(
          powerUp: powerUp,
          index: entry.key,
        );
      }).toList(),
    );
  }
}

class _PowerUpListItem extends ConsumerWidget {
  final OwnedPowerUp powerUp;
  final int index;

  const _PowerUpListItem({
    required this.powerUp,
    required this.index,
  });

  IconData _getIconForType(String type) {
    switch (type) {
      case 'xp_boost':
        return Icons.trending_up;
      case 'hint_token':
        return Icons.lightbulb;
      case 'streak_freeze':
        return Icons.ac_unit;
      case 'double_coins':
        return Icons.monetization_on;
      case 'shield':
        return Icons.shield;
      case 'time_freezer':
        return Icons.timer_off;
      default:
        return Icons.flash_on;
    }
  }

  Color _getColorForType(String type) {
    switch (type) {
      case 'xp_boost':
        return Colors.purpleAccent;
      case 'hint_token':
        return Colors.amber;
      case 'streak_freeze':
        return Colors.cyanAccent;
      case 'double_coins':
        return Colors.yellow;
      case 'shield':
        return Colors.blueAccent;
      case 'time_freezer':
        return Colors.tealAccent;
      default:
        return Colors.greenAccent;
    }
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final color = _getColorForType(powerUp.type);
    final icon = _getIconForType(powerUp.type);
    final isActivating = ref.watch(shopProvider).isActivatingPowerUp;

    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: color.withOpacity(0.05),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: color.withOpacity(0.2)),
      ),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(8),
            decoration: BoxDecoration(
              color: color.withOpacity(0.2),
              borderRadius: BorderRadius.circular(8),
            ),
            child: Icon(icon, color: color, size: 18),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  powerUp.name,
                  style: TextStyle(
                    color: color,
                    fontWeight: FontWeight.bold,
                    fontSize: 13,
                  ),
                ),
                Text(
                  'x${powerUp.quantity} disponible',
                  style: TextStyle(
                    color: Colors.white.withOpacity(0.5),
                    fontSize: 11,
                  ),
                ),
              ],
            ),
          ),
          TextButton(
            onPressed: isActivating
                ? null
                : () {
                    HapticFeedback.selectionClick();
                    ref.read(shopProvider.notifier).activatePowerUp(powerUp.id);
                  },
            style: TextButton.styleFrom(
              foregroundColor: color,
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
            ),
            child: const Text(
              'USAR',
              style: TextStyle(
                fontWeight: FontWeight.bold,
                fontSize: 11,
                letterSpacing: 1,
              ),
            ),
          ),
        ],
      ),
    )
        .animate(delay: Duration(milliseconds: index * 50))
        .fadeIn()
        .slideX(begin: 0.1);
  }
}
