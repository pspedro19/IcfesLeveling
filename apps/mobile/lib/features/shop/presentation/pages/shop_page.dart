import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_animate/flutter_animate.dart';
import '../../../../shared/providers/balance_provider.dart';
import '../providers/shop_provider.dart';
import '../widgets/inventory_grid.dart';
import '../widgets/active_powerups_card.dart';
import '../widgets/powerup_inventory.dart';

class ShopPage extends ConsumerStatefulWidget {
  const ShopPage({super.key});

  @override
  ConsumerState<ShopPage> createState() => _ShopPageState();
}

class _ShopPageState extends ConsumerState<ShopPage> with SingleTickerProviderStateMixin {
  late TabController _tabController;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 3, vsync: this);
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  (IconData, Color) _getIconForCategory(String category) {
    switch (category) {
      case 'streak':
      case 'streak_freeze':
        return (Icons.ac_unit, Colors.cyanAccent);
      case 'hearts':
        return (Icons.favorite, Colors.red);
      case 'xp':
      case 'xp_boost':
        return (Icons.trending_up, Colors.purpleAccent);
      case 'hint':
      case 'hint_token':
        return (Icons.lightbulb, Colors.amber);
      case 'shield':
        return (Icons.shield, Colors.blueAccent);
      case 'double_coins':
        return (Icons.monetization_on, Colors.yellow);
      case 'time_freezer':
        return (Icons.timer_off, Colors.tealAccent);
      case 'powerup':
      case 'consumable':
        return (Icons.flash_on, Colors.orangeAccent);
      default:
        return (Icons.star, Colors.grey);
    }
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(shopProvider);
    final notifier = ref.read(shopProvider.notifier);
    final balanceState = ref.watch(balanceProvider);

    // Get current gold from balance provider
    final userGold = balanceState.maybeWhen(
      data: (balance) => balance.gold,
      orElse: () => 0,
    );

    // Group inventory items
    final inventoryMap = <String, int>{};
    for (var itemId in state.inventory) {
      inventoryMap[itemId] = (inventoryMap[itemId] ?? 0) + 1;
    }

    final inventoryDisplay = inventoryMap.entries.map((entry) {
      final shopItem = state.items.firstWhere(
        (i) => i.id == entry.key,
        orElse: () => ShopItem(id: entry.key, name: 'Unknown', description: '', priceGold: 0, category: 'unknown'),
      );

      final category = shopItem.category == 'unknown'
          ? (entry.key.contains('streak') ? 'streak' : (entry.key.contains('heart') ? 'hearts' : 'other'))
          : shopItem.category;

      final (icon, color) = _getIconForCategory(category);
      return {
        'icon': icon,
        'color': color,
        'count': entry.value,
        'name': shopItem.name,
      };
    }).toList();

    // Separate items into categories
    final permanentItems = state.permanentItems;
    final consumableItems = state.consumableItems;

    // Show purchase message snackbar
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (state.purchaseMessage != null) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Row(
              children: [
                const Icon(Icons.check_circle, color: Colors.white),
                const SizedBox(width: 8),
                Text(state.purchaseMessage!),
              ],
            ),
            backgroundColor: Colors.green.shade700,
            behavior: SnackBarBehavior.floating,
            duration: const Duration(seconds: 2),
          ),
        );
        notifier.clearPurchaseMessage();
      }
      if (state.error != null) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Row(
              children: [
                const Icon(Icons.error_outline, color: Colors.white),
                const SizedBox(width: 8),
                Expanded(child: Text(state.error!)),
              ],
            ),
            backgroundColor: Colors.red.shade700,
            behavior: SnackBarBehavior.floating,
            duration: const Duration(seconds: 2),
          ),
        );
        notifier.clearError();
      }
      // Power-up activation success
      if (state.activationSuccess != null) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Row(
              children: [
                const Icon(Icons.flash_on, color: Colors.white),
                const SizedBox(width: 8),
                Text(state.activationSuccess!),
              ],
            ),
            backgroundColor: Colors.green.shade700,
            behavior: SnackBarBehavior.floating,
            duration: const Duration(seconds: 2),
          ),
        );
        notifier.clearActivationSuccess();
      }
    });

    return Scaffold(
      backgroundColor: const Color(0xFF0A0A0A),
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        title: const Text(
          "TIENDA DEL SISTEMA",
          style: TextStyle(color: Colors.white, fontWeight: FontWeight.w900, letterSpacing: 2),
        ),
        actions: [
          // Active power-ups indicator
          const ActivePowerUpsBadge(),
          const SizedBox(width: 8),
          _GoldBalanceBadge(balanceState: balanceState),
          const SizedBox(width: 16),
        ],
        bottom: PreferredSize(
          preferredSize: const Size.fromHeight(48),
          child: Container(
            margin: const EdgeInsets.symmetric(horizontal: 16),
            decoration: BoxDecoration(
              color: Colors.white.withOpacity(0.05),
              borderRadius: BorderRadius.circular(12),
            ),
            child: TabBar(
              controller: _tabController,
              indicator: BoxDecoration(
                color: Colors.blue.withOpacity(0.3),
                borderRadius: BorderRadius.circular(12),
              ),
              indicatorSize: TabBarIndicatorSize.tab,
              dividerColor: Colors.transparent,
              labelColor: Colors.white,
              unselectedLabelColor: Colors.white54,
              labelStyle: const TextStyle(
                fontSize: 11,
                fontWeight: FontWeight.bold,
                letterSpacing: 1,
              ),
              tabs: [
                Tab(
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      const Icon(Icons.store, size: 16),
                      const SizedBox(width: 4),
                      Flexible(child: const Text('TIENDA', overflow: TextOverflow.ellipsis)),
                    ],
                  ),
                ),
                Tab(
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      const Icon(Icons.flash_on, size: 16),
                      const SizedBox(width: 4),
                      Flexible(child: const Text('POWER-UPS', overflow: TextOverflow.ellipsis)),
                    ],
                  ),
                ),
                Tab(
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      const Icon(Icons.inventory_2, size: 16),
                      const SizedBox(width: 4),
                      Flexible(child: const Text('INVENTARIO', overflow: TextOverflow.ellipsis)),
                    ],
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
      body: TabBarView(
        controller: _tabController,
        children: [
          // Tab 1: Shop Items
          _buildShopTab(state, notifier, userGold, permanentItems, consumableItems),
          // Tab 2: Power-Ups
          _buildPowerUpsTab(state, notifier),
          // Tab 3: Inventory
          _buildInventoryTab(state, inventoryDisplay),
        ],
      ),
    );
  }

  Widget _buildShopTab(
    ShopState state,
    ShopNotifier notifier,
    int userGold,
    List<ShopItem> permanentItems,
    List<ShopItem> consumableItems,
  ) {
    return RefreshIndicator(
      onRefresh: () async {
        HapticFeedback.mediumImpact();
        await notifier.refresh();
      },
      child: SingleChildScrollView(
        physics: const AlwaysScrollableScrollPhysics(),
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Active Power-ups section at top
            const ActivePowerupsCard(),

            // Consumables / Power-ups section
            if (consumableItems.isNotEmpty) ...[
              Row(
                children: [
                  Container(
                    padding: const EdgeInsets.all(6),
                    decoration: BoxDecoration(
                      color: Colors.orange.withOpacity(0.2),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: const Icon(Icons.flash_on, color: Colors.orangeAccent, size: 16),
                  ),
                  const SizedBox(width: 8),
                  const Text(
                    "CONSUMIBLES",
                    style: TextStyle(
                      color: Colors.orangeAccent,
                      fontWeight: FontWeight.bold,
                      letterSpacing: 2,
                      fontSize: 12,
                    ),
                  ),
                ],
              ).animate().fadeIn(),
              const SizedBox(height: 16),
              SizedBox(
                height: 180,
                child: ListView.builder(
                  scrollDirection: Axis.horizontal,
                  itemCount: consumableItems.length,
                  itemBuilder: (context, index) {
                    final item = consumableItems[index];
                    final (icon, color) = _getIconForCategory(item.category);
                    final canAfford = userGold >= item.priceGold;

                    return GestureDetector(
                      onTap: () {
                        HapticFeedback.selectionClick();
                        _showPurchaseDialog(context, item, userGold, ref.read(shopProvider.notifier));
                      },
                      child: Container(
                        width: 140,
                        margin: EdgeInsets.only(right: index < consumableItems.length - 1 ? 12 : 0),
                        child: _ConsumableItemCard(
                          name: item.name,
                          cost: item.priceGold,
                          icon: icon,
                          color: color,
                          canAfford: canAfford,
                          duration: item.duration,
                        ),
                      ).animate(delay: Duration(milliseconds: index * 100)).fadeIn().slideX(begin: 0.2),
                    );
                  },
                ),
              ),
              const SizedBox(height: 32),
            ],

            // Permanent items section
            if (permanentItems.isNotEmpty) ...[
              Row(
                children: [
                  Container(
                    padding: const EdgeInsets.all(6),
                    decoration: BoxDecoration(
                      color: Colors.blue.withOpacity(0.2),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: const Icon(Icons.diamond, color: Colors.blueAccent, size: 16),
                  ),
                  const SizedBox(width: 8),
                  const Text(
                    "ARTICULOS PERMANENTES",
                    style: TextStyle(
                      color: Colors.blueAccent,
                      fontWeight: FontWeight.bold,
                      letterSpacing: 2,
                      fontSize: 12,
                    ),
                  ),
                ],
              ).animate().fadeIn(),
              const SizedBox(height: 16),
            ],

            if (state.isLoading && state.items.isEmpty)
              const Center(
                child: Padding(
                  padding: EdgeInsets.all(40),
                  child: CircularProgressIndicator(),
                ),
              )
            else if (state.error != null && state.items.isEmpty)
              Center(
                child: Column(
                  children: [
                    const Icon(Icons.error_outline, color: Colors.red, size: 48),
                    const SizedBox(height: 16),
                    Text(state.error!, style: const TextStyle(color: Colors.red)),
                    const SizedBox(height: 16),
                    ElevatedButton(
                      onPressed: () => notifier.refresh(),
                      child: const Text('Reintentar'),
                    ),
                  ],
                ),
              )
            else if (permanentItems.isNotEmpty)
              GridView.builder(
                shrinkWrap: true,
                physics: const NeverScrollableScrollPhysics(),
                gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                  crossAxisCount: 2,
                  childAspectRatio: 0.75,
                  crossAxisSpacing: 16,
                  mainAxisSpacing: 16,
                ),
                itemCount: permanentItems.length,
                itemBuilder: (context, index) {
                  final item = permanentItems[index];
                  final (icon, color) = _getIconForCategory(item.category);
                  final canAfford = userGold >= item.priceGold;

                  return GestureDetector(
                    onTap: () {
                      HapticFeedback.selectionClick();
                      _showPurchaseDialog(context, item, userGold, notifier);
                    },
                    child: _ShopItemCard(
                      name: item.name,
                      cost: item.priceGold,
                      icon: icon,
                      color: color,
                      canAfford: canAfford,
                    ).animate(delay: Duration(milliseconds: index * 100)).fadeIn().scale(),
                  );
                },
              ),
          ],
        ),
      ),
    );
  }

  Widget _buildPowerUpsTab(ShopState state, ShopNotifier notifier) {
    return RefreshIndicator(
      onRefresh: () async {
        HapticFeedback.mediumImpact();
        await notifier.fetchActivePowerUps();
        await notifier.fetchOwnedPowerUps();
      },
      child: SingleChildScrollView(
        physics: const AlwaysScrollableScrollPhysics(),
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Active Power-ups section
            const ActivePowerupsCard(),
            const SizedBox(height: 24),
            // Owned Power-ups inventory
            const PowerupInventory(),
          ],
        ),
      ),
    );
  }

  Widget _buildInventoryTab(ShopState state, List<Map<String, dynamic>> inventoryDisplay) {
    return RefreshIndicator(
      onRefresh: () async {
        HapticFeedback.mediumImpact();
        await ref.read(shopProvider.notifier).refresh();
      },
      child: SingleChildScrollView(
        physics: const AlwaysScrollableScrollPhysics(),
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(6),
                  decoration: BoxDecoration(
                    color: Colors.purple.withOpacity(0.2),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: const Icon(Icons.inventory_2, color: Colors.purpleAccent, size: 16),
                ),
                const SizedBox(width: 8),
                const Text(
                  "TODOS TUS ARTICULOS",
                  style: TextStyle(
                    color: Colors.purpleAccent,
                    fontWeight: FontWeight.bold,
                    letterSpacing: 2,
                    fontSize: 12,
                  ),
                ),
              ],
            ).animate().fadeIn(),
            const SizedBox(height: 16),
            InventoryGrid(items: inventoryDisplay),
            const SizedBox(height: 32),
            // Also show power-up inventory here
            const PowerupInventory(),
          ],
        ),
      ),
    );
  }

  void _showPurchaseDialog(BuildContext context, ShopItem item, int balance, ShopNotifier notifier) {
    final isPowerUp = item.isPowerUp || item.category == 'powerup' || item.category == 'consumable';

    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: const Color(0xFF1E1E1E),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
        title: Row(
          children: [
            if (isPowerUp)
              const Icon(Icons.flash_on, color: Colors.orangeAccent, size: 24)
            else
              const Icon(Icons.shopping_cart, color: Colors.blueAccent, size: 24),
            const SizedBox(width: 8),
            Expanded(
              child: Text(
                'Comprar ${item.name}?',
                style: const TextStyle(color: Colors.white, fontSize: 18),
              ),
            ),
          ],
        ),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(item.description, style: const TextStyle(color: Colors.white70)),
            if (item.duration != null) ...[
              const SizedBox(height: 8),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                decoration: BoxDecoration(
                  color: Colors.orangeAccent.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: Colors.orangeAccent.withOpacity(0.3)),
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    const Icon(Icons.timer, color: Colors.orangeAccent, size: 14),
                    const SizedBox(width: 4),
                    Text(
                      'Duracion: ${_formatDuration(item.duration!)}',
                      style: const TextStyle(color: Colors.orangeAccent, fontSize: 12),
                    ),
                  ],
                ),
              ),
            ],
            const SizedBox(height: 16),
            Row(
              children: [
                const Text('Costo: ', style: TextStyle(color: Colors.white70)),
                const Icon(Icons.monetization_on, color: Colors.yellow, size: 16),
                Text(' ${item.priceGold}', style: const TextStyle(color: Colors.yellow, fontWeight: FontWeight.bold)),
              ],
            ),
            const SizedBox(height: 8),
            Row(
              children: [
                const Text('Tu saldo: ', style: TextStyle(color: Colors.white70)),
                const Icon(Icons.monetization_on, color: Colors.yellow, size: 16),
                Text(' $balance', style: const TextStyle(color: Colors.yellow)),
              ],
            ),
            const SizedBox(height: 8),
            if (balance < item.priceGold)
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                decoration: BoxDecoration(
                  color: Colors.red.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: const Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(Icons.warning, color: Colors.redAccent, size: 14),
                    SizedBox(width: 4),
                    Text('Oro insuficiente', style: TextStyle(color: Colors.redAccent, fontSize: 12)),
                  ],
                ),
              ),
          ],
        ),
        actions: [
          TextButton(
            child: const Text('Cancelar'),
            onPressed: () => Navigator.of(ctx).pop(),
          ),
          ElevatedButton(
            style: ElevatedButton.styleFrom(
              backgroundColor: balance >= item.priceGold ? Colors.blue : Colors.grey,
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
            ),
            onPressed: balance >= item.priceGold
                ? () {
                    HapticFeedback.mediumImpact();
                    Navigator.of(ctx).pop();
                    notifier.purchaseItem(item.id);
                  }
                : null,
            child: const Text('Comprar', style: TextStyle(color: Colors.white)),
          ),
        ],
      ),
    );
  }

  String _formatDuration(int seconds) {
    if (seconds >= 3600) {
      final hours = seconds ~/ 3600;
      final mins = (seconds % 3600) ~/ 60;
      return mins > 0 ? '${hours}h ${mins}m' : '${hours}h';
    } else if (seconds >= 60) {
      final minutes = seconds ~/ 60;
      return '${minutes}m';
    }
    return '${seconds}s';
  }
}

/// Card for consumable items (power-ups) shown in horizontal scroll
class _ConsumableItemCard extends StatelessWidget {
  final String name;
  final int cost;
  final IconData icon;
  final Color color;
  final bool canAfford;
  final int? duration;

  const _ConsumableItemCard({
    required this.name,
    required this.cost,
    required this.icon,
    required this.color,
    this.canAfford = true,
    this.duration,
  });

  String _formatDuration(int seconds) {
    if (seconds >= 3600) {
      return '${seconds ~/ 3600}h';
    } else if (seconds >= 60) {
      return '${seconds ~/ 60}m';
    }
    return '${seconds}s';
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [
            color.withOpacity(canAfford ? 0.15 : 0.05),
            color.withOpacity(canAfford ? 0.05 : 0.02),
          ],
        ),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: canAfford ? color.withOpacity(0.3) : Colors.grey.withOpacity(0.2),
        ),
        boxShadow: canAfford
            ? [BoxShadow(color: color.withOpacity(0.2), blurRadius: 12, spreadRadius: -4)]
            : null,
      ),
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
                child: Icon(icon, color: canAfford ? color : Colors.grey, size: 20),
              ),
              const Spacer(),
              if (duration != null)
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                  decoration: BoxDecoration(
                    color: Colors.white.withOpacity(0.1),
                    borderRadius: BorderRadius.circular(6),
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(Icons.timer, size: 10, color: Colors.white.withOpacity(0.7)),
                      const SizedBox(width: 2),
                      Text(
                        _formatDuration(duration!),
                        style: TextStyle(
                          color: Colors.white.withOpacity(0.7),
                          fontSize: 9,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ],
                  ),
                ),
            ],
          ),
          const Spacer(),
          Text(
            name,
            style: TextStyle(
              color: canAfford ? Colors.white : Colors.grey,
              fontWeight: FontWeight.bold,
              fontSize: 12,
            ),
            maxLines: 2,
            overflow: TextOverflow.ellipsis,
          ),
          const SizedBox(height: 8),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
            decoration: BoxDecoration(
              color: Colors.white.withOpacity(0.05),
              borderRadius: BorderRadius.circular(8),
            ),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(
                  Icons.monetization_on,
                  color: canAfford ? Colors.yellow : Colors.grey,
                  size: 12,
                ),
                const SizedBox(width: 4),
                Text(
                  "$cost",
                  style: TextStyle(
                    color: canAfford ? Colors.yellow : Colors.grey,
                    fontWeight: FontWeight.w900,
                    fontSize: 11,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _ShopItemCard extends StatelessWidget {
  final String name;
  final int cost;
  final IconData icon;
  final Color color;
  final bool canAfford;

  const _ShopItemCard({
    required this.name,
    required this.cost,
    required this.icon,
    required this.color,
    this.canAfford = true,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.03),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: canAfford ? color.withOpacity(0.2) : Colors.grey.withOpacity(0.2)),
        boxShadow: [
          BoxShadow(color: color.withOpacity(0.05), blurRadius: 20, spreadRadius: -5),
        ],
      ),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(icon, color: canAfford ? color : Colors.grey, size: 48),
          const SizedBox(height: 16),
          Text(
            name,
            textAlign: TextAlign.center,
            style: TextStyle(
              color: canAfford ? Colors.white : Colors.grey,
              fontWeight: FontWeight.bold,
              fontSize: 14,
            ),
          ),
          const SizedBox(height: 12),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
            decoration: BoxDecoration(
              color: Colors.white.withOpacity(0.05),
              borderRadius: BorderRadius.circular(12),
            ),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(
                  Icons.monetization_on,
                  color: canAfford ? Colors.yellow : Colors.grey,
                  size: 14,
                ),
                const SizedBox(width: 4),
                Text(
                  "$cost",
                  style: TextStyle(
                    color: canAfford ? Colors.yellow : Colors.grey,
                    fontWeight: FontWeight.w900,
                    fontSize: 12,
                  ),
                ),
              ],
            ),
          ),
          if (!canAfford)
            Padding(
              padding: const EdgeInsets.only(top: 8),
              child: Text(
                'Oro insuficiente',
                style: TextStyle(color: Colors.red.shade300, fontSize: 10),
              ),
            ),
        ],
      ),
    );
  }
}

class _GoldBalanceBadge extends StatelessWidget {
  final AsyncValue<BalanceState> balanceState;

  const _GoldBalanceBadge({required this.balanceState});

  @override
  Widget build(BuildContext context) {
    return balanceState.when(
      data: (balance) => _buildBadge(balance.gold),
      loading: () => _buildLoadingBadge(),
      error: (_, __) => _buildErrorBadge(),
    );
  }

  Widget _buildBadge(int balance) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      decoration: BoxDecoration(
        color: Colors.yellow.withOpacity(0.1),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Colors.yellow.withOpacity(0.3)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          const Icon(Icons.monetization_on, color: Colors.yellow, size: 18),
          const SizedBox(width: 8),
          Text(
            _formatGold(balance),
            style: const TextStyle(color: Colors.yellow, fontWeight: FontWeight.w900, fontSize: 16),
          ),
        ],
      ),
    ).animate(onPlay: (c) => c.repeat(reverse: true))
        .shimmer(duration: 3.seconds, color: Colors.yellow.withOpacity(0.2));
  }

  Widget _buildLoadingBadge() {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      decoration: BoxDecoration(
        color: Colors.yellow.withOpacity(0.1),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Colors.yellow.withOpacity(0.3)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          const Icon(Icons.monetization_on, color: Colors.yellow, size: 18),
          const SizedBox(width: 8),
          SizedBox(
            width: 30,
            height: 16,
            child: Container(
              decoration: BoxDecoration(
                color: Colors.yellow.withOpacity(0.2),
                borderRadius: BorderRadius.circular(4),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildErrorBadge() {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      decoration: BoxDecoration(
        color: Colors.red.withOpacity(0.1),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Colors.red.withOpacity(0.3)),
      ),
      child: const Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(Icons.monetization_on, color: Colors.grey, size: 18),
          SizedBox(width: 8),
          Icon(Icons.refresh, color: Colors.grey, size: 14),
        ],
      ),
    );
  }

  String _formatGold(int gold) {
    if (gold >= 1000000) {
      return '${(gold / 1000000).toStringAsFixed(1)}M';
    } else if (gold >= 1000) {
      final k = gold / 1000;
      return k == k.truncate() ? '${k.truncate()}K' : '${k.toStringAsFixed(1)}K';
    }
    return gold.toString();
  }
}
