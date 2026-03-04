import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/config/app_theme.dart';

class QuickActions extends StatelessWidget {
  const QuickActions({super.key});

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Que quieres hacer?',
          style: Theme.of(context).textTheme.titleLarge,
        ),
        const SizedBox(height: 16),
        GridView.count(
          crossAxisCount: 2,
          shrinkWrap: true,
          physics: const NeverScrollableScrollPhysics(),
          crossAxisSpacing: 16,
          mainAxisSpacing: 16,
          childAspectRatio: 1.8,
          children: [
            _buildActionCard(
              context: context,
              icon: Icons.play_circle_fill_rounded,
              label: 'Practica',
              color: AppTheme.successGreen,
              onTap: () {
                // Navigate to practice config
                context.go('/practice');
              },
            ),
            _buildActionCard(
              context: context,
              icon: Icons.diamond_rounded,
              label: 'Millonario',
              color: AppTheme.secondaryGold,
              badge: 'NUEVO',
              onTap: () {
                // Navigate to millionaire mode
                context.push('/millionaire');
              },
            ),
            _buildActionCard(
              context: context,
              icon: Icons.menu_book_rounded,
              label: 'Mi Plan',
              color: AppTheme.primaryPurple,
              onTap: () {
                // Navigate to study plan
                context.go('/study-plan');
              },
            ),
            _buildActionCard(
              context: context,
              icon: Icons.emoji_events_rounded,
              label: 'Ligas',
              color: AppTheme.accentCyan,
              onTap: () {
                // Navigate to leagues
                context.go('/leagues');
              },
            ),
          ],
        ),
      ],
    );
  }

  Widget _buildActionCard({
    required BuildContext context,
    required IconData icon,
    required String label,
    required Color color,
    required VoidCallback onTap,
    String? badge,
  }) {
    return Card(
      elevation: 2,
      color: AppTheme.bgElevated,
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(16),
        child: Stack(
          children: [
            Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(icon, size: 32, color: color),
                  const SizedBox(height: 8),
                  Text(
                    label,
                    style: Theme.of(context).textTheme.titleMedium,
                  ),
                ],
              ),
            ),
            if (badge != null)
              Positioned(
                top: 8,
                right: 8,
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                  decoration: BoxDecoration(
                    color: AppTheme.dangerRed,
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Text(
                    badge,
                    style: const TextStyle(
                      color: Colors.white,
                      fontSize: 9,
                      fontWeight: FontWeight.bold,
                      letterSpacing: 0.5,
                    ),
                  ),
                ),
              ),
          ],
        ),
      ),
    );
  }
}
