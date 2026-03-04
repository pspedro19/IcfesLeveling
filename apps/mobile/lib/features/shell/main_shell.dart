import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import '../../shared/widgets/heart_indicator.dart';
import '../../shared/widgets/streak_indicator.dart';
import '../../shared/widgets/gold_indicator.dart';

class MainShell extends StatelessWidget {
  final Widget child;

  const MainShell({super.key, required this.child});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: _buildAppBar(context),
      body: child,
      bottomNavigationBar: _buildBottomNav(context),
    );
  }

  PreferredSizeWidget _buildAppBar(BuildContext context) {
    return AppBar(
      title: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          const Icon(Icons.school, size: 24),
          const SizedBox(width: 6),
          const Flexible(
            child: Text(
              'ICFES',
              overflow: TextOverflow.ellipsis,
              style: TextStyle(fontSize: 16),
            ),
          ),
        ],
      ),
      actions: [
        // Indicadores de recursos
        const HeartIndicator(),
        const SizedBox(width: 8),
        const StreakIndicator(),
        const SizedBox(width: 8),
        const GoldIndicator(),
        const SizedBox(width: 16),
      ],
    );
  }

  Widget _buildBottomNav(BuildContext context) {
    dynamic state = GoRouterState.of(context);
    final location = state.uri.path;

    int currentIndex = 0;
    if (location.startsWith('/home')) currentIndex = 0;
    if (location.startsWith('/leagues')) currentIndex = 1;
    if (location.startsWith('/study-plan')) currentIndex = 2;
    if (location.startsWith('/profile')) currentIndex = 3;

    return NavigationBar(
      selectedIndex: currentIndex,
      onDestinationSelected: (index) {
        switch (index) {
          case 0:
            context.go('/home');
            break;
          case 1:
            context.go('/leagues');
            break;
          case 2:
            context.go('/study-plan');
            break;
          case 3:
            context.go('/profile');
            break;
        }
      },
      destinations: const [
        NavigationDestination(
          icon: Icon(Icons.home_outlined),
          selectedIcon: Icon(Icons.home),
          label: 'Inicio',
        ),
        NavigationDestination(
          icon: Icon(Icons.emoji_events_outlined),
          selectedIcon: Icon(Icons.emoji_events),
          label: 'Ligas',
        ),
        NavigationDestination(
          icon: Icon(Icons.menu_book_outlined),
          selectedIcon: Icon(Icons.menu_book),
          label: 'Plan',
        ),
        NavigationDestination(
          icon: Icon(Icons.person_outline),
          selectedIcon: Icon(Icons.person),
          label: 'Perfil',
        ),
      ],
    );
  }
}
