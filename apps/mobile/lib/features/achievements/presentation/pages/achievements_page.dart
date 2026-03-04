import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../data/models/achievement_model.dart';
import '../providers/achievements_provider.dart';
import '../widgets/achievement_badge.dart';
import '../widgets/achievement_detail_modal.dart';
import '../../../../core/constants/app_strings.dart';

class AchievementsPage extends ConsumerStatefulWidget {
  const AchievementsPage({super.key});

  @override
  ConsumerState<AchievementsPage> createState() => _AchievementsPageState();
}

class _AchievementsPageState extends ConsumerState<AchievementsPage>
    with SingleTickerProviderStateMixin {
  late TabController _tabController;

  final List<AchievementCategory?> _categories = [
    null, // All
    AchievementCategory.streak,
    AchievementCategory.practice,
    AchievementCategory.mastery,
    AchievementCategory.social,
    AchievementCategory.special,
  ];

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: _categories.length, vsync: this);
    _tabController.addListener(_onTabChanged);

    // Load achievements
    WidgetsBinding.instance.addPostFrameCallback((_) {
      ref.read(achievementsProvider.notifier).loadAchievements();
    });
  }

  void _onTabChanged() {
    if (!_tabController.indexIsChanging) {
      final category = _categories[_tabController.index];
      ref.read(achievementsProvider.notifier).filterByCategory(category);
    }
  }

  @override
  void dispose() {
    _tabController.removeListener(_onTabChanged);
    _tabController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(achievementsProvider);
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Logros'),
        bottom: TabBar(
          controller: _tabController,
          isScrollable: true,
          tabs: [
            const Tab(text: 'Todos'),
            Tab(text: AchievementCategory.streak.displayName),
            Tab(text: AchievementCategory.practice.displayName),
            Tab(text: AchievementCategory.mastery.displayName),
            Tab(text: AchievementCategory.social.displayName),
            Tab(text: AchievementCategory.special.displayName),
          ],
        ),
      ),
      body: state.isLoading
          ? const Center(child: CircularProgressIndicator())
          : state.error != null
              ? _buildErrorState(state.error!)
              : RefreshIndicator(
                  onRefresh: () async {
                    await ref.read(achievementsProvider.notifier).refresh();
                  },
                  child: CustomScrollView(
                    slivers: [
                      // Progress Header
                      SliverToBoxAdapter(
                        child: _buildProgressHeader(state, theme),
                      ),

                      // Achievements Grid
                      SliverPadding(
                        padding: const EdgeInsets.all(16),
                        sliver: SliverGrid(
                          gridDelegate:
                              const SliverGridDelegateWithFixedCrossAxisCount(
                            crossAxisCount: 3,
                            mainAxisSpacing: 16,
                            crossAxisSpacing: 16,
                            childAspectRatio: 0.8,
                          ),
                          delegate: SliverChildBuilderDelegate(
                            (context, index) {
                              final achievement =
                                  state.filteredAchievements[index];
                              return AchievementBadge(
                                achievement: achievement,
                                onTap: () => _showAchievementDetail(achievement),
                              );
                            },
                            childCount: state.filteredAchievements.length,
                          ),
                        ),
                      ),

                      // Empty State
                      if (state.filteredAchievements.isEmpty)
                        SliverFillRemaining(
                          child: Center(
                            child: Column(
                              mainAxisAlignment: MainAxisAlignment.center,
                              children: [
                                Icon(
                                  Icons.emoji_events_outlined,
                                  size: 64,
                                  color: Colors.grey[600],
                                ),
                                const SizedBox(height: 16),
                                Text(
                                  'No hay logros en esta categoria',
                                  style: theme.textTheme.bodyLarge?.copyWith(
                                    color: Colors.grey[600],
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ),
                    ],
                  ),
                ),
    );
  }

  Widget _buildProgressHeader(AchievementsState state, ThemeData theme) {
    final percentage = (state.completionPercentage * 100).toInt();

    return Container(
      margin: const EdgeInsets.all(16),
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [
            Colors.amber.shade700,
            Colors.orange.shade800,
          ],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(
            color: Colors.amber.withOpacity(0.3),
            blurRadius: 12,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Column(
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Progreso Total',
                    style: theme.textTheme.titleMedium?.copyWith(
                      color: Colors.white.withOpacity(0.9),
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    '${state.totalUnlocked}/${state.totalAvailable}',
                    style: theme.textTheme.headlineMedium?.copyWith(
                      color: Colors.white,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ],
              ),
              Stack(
                alignment: Alignment.center,
                children: [
                  SizedBox(
                    width: 70,
                    height: 70,
                    child: CircularProgressIndicator(
                      value: state.completionPercentage,
                      strokeWidth: 8,
                      backgroundColor: Colors.white.withOpacity(0.3),
                      valueColor:
                          const AlwaysStoppedAnimation<Color>(Colors.white),
                    ),
                  ),
                  Text(
                    '$percentage%',
                    style: const TextStyle(
                      color: Colors.white,
                      fontWeight: FontWeight.bold,
                      fontSize: 18,
                    ),
                  ),
                ],
              ),
            ],
          ),
          const SizedBox(height: 16),
          // Rarity breakdown
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceAround,
            children: [
              _buildRarityCount(
                  state.achievements, AchievementRarity.common, 'Comun'),
              _buildRarityCount(
                  state.achievements, AchievementRarity.rare, 'Raro'),
              _buildRarityCount(
                  state.achievements, AchievementRarity.epic, 'Epico'),
              _buildRarityCount(
                  state.achievements, AchievementRarity.legendary, 'Legendario'),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildRarityCount(
      List<AchievementModel> achievements, AchievementRarity rarity, String label) {
    final total = achievements.where((a) => a.rarity == rarity).length;
    final unlocked =
        achievements.where((a) => a.rarity == rarity && a.isUnlocked).length;

    return Column(
      children: [
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
          decoration: BoxDecoration(
            color: Color(rarity.colorValue).withOpacity(0.3),
            borderRadius: BorderRadius.circular(8),
          ),
          child: Text(
            '$unlocked/$total',
            style: TextStyle(
              color: Color(rarity.colorValue),
              fontWeight: FontWeight.bold,
              fontSize: 12,
            ),
          ),
        ),
        const SizedBox(height: 4),
        Text(
          label,
          style: TextStyle(
            color: Colors.white.withOpacity(0.8),
            fontSize: 10,
          ),
        ),
      ],
    );
  }

  Widget _buildErrorState(String error) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const Icon(Icons.error_outline, size: 48, color: Colors.red),
          const SizedBox(height: 16),
          Text(error),
          const SizedBox(height: 16),
          ElevatedButton(
            onPressed: () {
              ref.read(achievementsProvider.notifier).loadAchievements();
            },
            child: const Text('Reintentar'),
          ),
        ],
      ),
    );
  }

  void _showAchievementDetail(AchievementModel achievement) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (context) => AchievementDetailModal(achievement: achievement),
    );
  }
}
