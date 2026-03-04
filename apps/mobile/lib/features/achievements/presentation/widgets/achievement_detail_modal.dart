import 'package:flutter/material.dart';
import '../../data/models/achievement_model.dart';

/// Modal showing achievement details
class AchievementDetailModal extends StatelessWidget {
  final AchievementModel achievement;

  const AchievementDetailModal({
    super.key,
    required this.achievement,
  });

  @override
  Widget build(BuildContext context) {
    final isUnlocked = achievement.isUnlocked;
    final rarityColor = Color(achievement.rarity.colorValue);
    final theme = Theme.of(context);

    return Container(
      margin: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: theme.scaffoldBackgroundColor,
        borderRadius: BorderRadius.circular(24),
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          // Handle bar
          Container(
            width: 40,
            height: 4,
            margin: const EdgeInsets.only(top: 12),
            decoration: BoxDecoration(
              color: Colors.grey[600],
              borderRadius: BorderRadius.circular(2),
            ),
          ),

          // Badge display
          Padding(
            padding: const EdgeInsets.all(24),
            child: Column(
              children: [
                // Large badge
                Container(
                  width: 120,
                  height: 120,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    gradient: isUnlocked
                        ? LinearGradient(
                            colors: [
                              rarityColor.withOpacity(0.7),
                              rarityColor,
                            ],
                            begin: Alignment.topLeft,
                            end: Alignment.bottomRight,
                          )
                        : null,
                    color: isUnlocked ? null : Colors.grey[800],
                    border: Border.all(
                      color: isUnlocked ? rarityColor : Colors.grey[600]!,
                      width: 4,
                    ),
                    boxShadow: isUnlocked
                        ? [
                            BoxShadow(
                              color: rarityColor.withOpacity(0.5),
                              blurRadius: 20,
                              spreadRadius: 4,
                            ),
                          ]
                        : null,
                  ),
                  child: Icon(
                    Icons.emoji_events,
                    size: 60,
                    color: isUnlocked ? Colors.white : Colors.grey[600],
                  ),
                ),
                const SizedBox(height: 20),

                // Rarity badge
                Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 16,
                    vertical: 6,
                  ),
                  decoration: BoxDecoration(
                    color: rarityColor.withOpacity(0.2),
                    borderRadius: BorderRadius.circular(20),
                    border: Border.all(color: rarityColor),
                  ),
                  child: Text(
                    achievement.rarity.displayName.toUpperCase(),
                    style: TextStyle(
                      color: rarityColor,
                      fontWeight: FontWeight.bold,
                      fontSize: 12,
                      letterSpacing: 1.2,
                    ),
                  ),
                ),
                const SizedBox(height: 16),

                // Name
                Text(
                  achievement.isSecret && !isUnlocked
                      ? 'Logro Secreto'
                      : achievement.name,
                  style: theme.textTheme.headlineSmall?.copyWith(
                    fontWeight: FontWeight.bold,
                  ),
                  textAlign: TextAlign.center,
                ),
                const SizedBox(height: 8),

                // Description
                Text(
                  achievement.isSecret && !isUnlocked
                      ? 'Completa acciones especiales para desbloquear este logro misterioso.'
                      : achievement.description,
                  style: theme.textTheme.bodyMedium?.copyWith(
                    color: Colors.grey[400],
                  ),
                  textAlign: TextAlign.center,
                ),
                const SizedBox(height: 24),

                // Progress bar for locked achievements
                if (!isUnlocked) ...[
                  Column(
                    children: [
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Text(
                            'Progreso',
                            style: TextStyle(color: Colors.grey[500]),
                          ),
                          Text(
                            '${(achievement.progress * 100).toInt()}%',
                            style: TextStyle(
                              color: rarityColor,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 8),
                      ClipRRect(
                        borderRadius: BorderRadius.circular(8),
                        child: LinearProgressIndicator(
                          value: achievement.progress,
                          backgroundColor: Colors.grey[800],
                          valueColor: AlwaysStoppedAnimation<Color>(rarityColor),
                          minHeight: 8,
                        ),
                      ),
                      const SizedBox(height: 8),
                      // Requirement hint
                      Text(
                        _getRequirementHint(achievement.requirement),
                        style: TextStyle(
                          color: Colors.grey[600],
                          fontSize: 12,
                        ),
                        textAlign: TextAlign.center,
                      ),
                    ],
                  ),
                ],

                // Unlocked info
                if (isUnlocked && achievement.unlockedAt != null) ...[
                  Container(
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: Colors.green.withOpacity(0.1),
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(color: Colors.green.withOpacity(0.3)),
                    ),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        const Icon(Icons.check_circle, color: Colors.green),
                        const SizedBox(width: 8),
                        Text(
                          'Desbloqueado ${_formatDate(achievement.unlockedAt!)}',
                          style: const TextStyle(color: Colors.green),
                        ),
                      ],
                    ),
                  ),
                ],

                const SizedBox(height: 24),

                // Rewards
                if (achievement.xpReward > 0 || achievement.goldReward > 0)
                  Container(
                    padding: const EdgeInsets.all(16),
                    decoration: BoxDecoration(
                      color: Colors.grey[900],
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: Row(
                      mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                      children: [
                        if (achievement.xpReward > 0)
                          _RewardDisplay(
                            icon: Icons.star,
                            value: '+${achievement.xpReward}',
                            label: 'XP',
                            color: Colors.purple,
                          ),
                        if (achievement.xpReward > 0 && achievement.goldReward > 0)
                          Container(
                            width: 1,
                            height: 40,
                            color: Colors.grey[700],
                          ),
                        if (achievement.goldReward > 0)
                          _RewardDisplay(
                            icon: Icons.monetization_on,
                            value: '+${achievement.goldReward}',
                            label: 'Oro',
                            color: Colors.amber,
                          ),
                      ],
                    ),
                  ),

                const SizedBox(height: 16),

                // Category chip
                Chip(
                  avatar: Icon(
                    _getCategoryIcon(achievement.category),
                    size: 18,
                    color: Colors.white70,
                  ),
                  label: Text(achievement.category.displayName),
                  backgroundColor: Colors.grey[800],
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  String _getRequirementHint(AchievementRequirement requirement) {
    final type = requirement.type;
    final target = requirement.targetValue;

    switch (type) {
      case 'streak_days':
        return 'Mantiene una racha de $target dias';
      case 'questions_answered':
        return 'Responde $target preguntas';
      case 'questions_correct':
        return 'Responde correctamente $target preguntas';
      case 'subjects_mastered':
        return 'Domina $target materias';
      case 'perfect_sessions':
        return 'Completa $target sesiones perfectas';
      case 'total_xp':
        return 'Acumula $target XP';
      case 'level_reached':
        return 'Alcanza el nivel $target';
      case 'friends_added':
        return 'Agrega $target amigos';
      case 'battles_won':
        return 'Gana $target batallas';
      default:
        return 'Completa los requisitos para desbloquear';
    }
  }

  String _formatDate(DateTime date) {
    final now = DateTime.now();
    final diff = now.difference(date);

    if (diff.inDays == 0) {
      return 'hoy';
    } else if (diff.inDays == 1) {
      return 'ayer';
    } else if (diff.inDays < 7) {
      return 'hace ${diff.inDays} dias';
    } else {
      return '${date.day}/${date.month}/${date.year}';
    }
  }

  IconData _getCategoryIcon(AchievementCategory category) {
    switch (category) {
      case AchievementCategory.streak:
        return Icons.local_fire_department;
      case AchievementCategory.practice:
        return Icons.fitness_center;
      case AchievementCategory.mastery:
        return Icons.school;
      case AchievementCategory.social:
        return Icons.people;
      case AchievementCategory.special:
        return Icons.auto_awesome;
      case AchievementCategory.general:
        return Icons.emoji_events;
    }
  }
}

class _RewardDisplay extends StatelessWidget {
  final IconData icon;
  final String value;
  final String label;
  final Color color;

  const _RewardDisplay({
    required this.icon,
    required this.value,
    required this.label,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Icon(icon, color: color, size: 28),
        const SizedBox(height: 4),
        Text(
          value,
          style: TextStyle(
            color: color,
            fontWeight: FontWeight.bold,
            fontSize: 18,
          ),
        ),
        Text(
          label,
          style: TextStyle(
            color: Colors.grey[500],
            fontSize: 12,
          ),
        ),
      ],
    );
  }
}
