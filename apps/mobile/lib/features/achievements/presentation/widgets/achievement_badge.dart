import 'package:flutter/material.dart';
import '../../data/models/achievement_model.dart';

/// Widget displaying an achievement badge
class AchievementBadge extends StatelessWidget {
  final AchievementModel achievement;
  final VoidCallback? onTap;
  final double size;
  final bool showProgress;

  const AchievementBadge({
    super.key,
    required this.achievement,
    this.onTap,
    this.size = 80,
    this.showProgress = true,
  });

  @override
  Widget build(BuildContext context) {
    final isUnlocked = achievement.isUnlocked;
    final rarityColor = Color(achievement.rarity.colorValue);

    return GestureDetector(
      onTap: onTap,
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          // Badge Container
          Container(
            width: size,
            height: size,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              gradient: isUnlocked
                  ? LinearGradient(
                      colors: [
                        rarityColor.withOpacity(0.8),
                        rarityColor,
                      ],
                      begin: Alignment.topLeft,
                      end: Alignment.bottomRight,
                    )
                  : null,
              color: isUnlocked ? null : Colors.grey[800],
              border: Border.all(
                color: isUnlocked ? rarityColor : Colors.grey[600]!,
                width: 3,
              ),
              boxShadow: isUnlocked
                  ? [
                      BoxShadow(
                        color: rarityColor.withOpacity(0.4),
                        blurRadius: 12,
                        spreadRadius: 2,
                      ),
                    ]
                  : null,
            ),
            child: Stack(
              alignment: Alignment.center,
              children: [
                // Icon
                Icon(
                  _getIconData(achievement.icon),
                  size: size * 0.45,
                  color: isUnlocked ? Colors.white : Colors.grey[600],
                ),
                // Progress indicator for locked achievements
                if (!isUnlocked && showProgress && achievement.progress > 0)
                  SizedBox(
                    width: size,
                    height: size,
                    child: CircularProgressIndicator(
                      value: achievement.progress,
                      strokeWidth: 3,
                      backgroundColor: Colors.transparent,
                      valueColor: AlwaysStoppedAnimation<Color>(
                        rarityColor.withOpacity(0.6),
                      ),
                    ),
                  ),
                // Lock overlay for secret achievements
                if (achievement.isSecret && !isUnlocked)
                  Positioned.fill(
                    child: Container(
                      decoration: BoxDecoration(
                        shape: BoxShape.circle,
                        color: Colors.black54,
                      ),
                      child: Icon(
                        Icons.lock,
                        size: size * 0.3,
                        color: Colors.white54,
                      ),
                    ),
                  ),
              ],
            ),
          ),
          const SizedBox(height: 8),
          // Name
          SizedBox(
            width: size + 20,
            child: Text(
              achievement.isSecret && !isUnlocked ? '???' : achievement.name,
              textAlign: TextAlign.center,
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
              style: TextStyle(
                fontSize: 11,
                fontWeight: isUnlocked ? FontWeight.bold : FontWeight.normal,
                color: isUnlocked ? Colors.white : Colors.grey[500],
              ),
            ),
          ),
          // Progress text for locked achievements
          if (!isUnlocked && showProgress && achievement.progress > 0) ...[
            const SizedBox(height: 2),
            Text(
              '${(achievement.progress * 100).toInt()}%',
              style: TextStyle(
                fontSize: 10,
                color: rarityColor.withOpacity(0.8),
              ),
            ),
          ],
        ],
      ),
    );
  }

  IconData _getIconData(String iconName) {
    // Map icon names to Flutter icons
    final iconMap = <String, IconData>{
      'trophy': Icons.emoji_events,
      'star': Icons.star,
      'fire': Icons.local_fire_department,
      'lightning': Icons.bolt,
      'crown': Icons.workspace_premium,
      'medal': Icons.military_tech,
      'book': Icons.menu_book,
      'brain': Icons.psychology,
      'rocket': Icons.rocket_launch,
      'target': Icons.gps_fixed,
      'diamond': Icons.diamond,
      'heart': Icons.favorite,
      'shield': Icons.shield,
      'sword': Icons.sports_martial_arts,
      'clock': Icons.access_time,
      'calendar': Icons.calendar_today,
      'group': Icons.group,
      'chat': Icons.chat,
      'gift': Icons.card_giftcard,
      'magic': Icons.auto_fix_high,
      'percent': Icons.percent,
      'check': Icons.check_circle,
      'streak': Icons.whatshot,
      'level': Icons.trending_up,
      'science': Icons.science,
      'math': Icons.calculate,
      'language': Icons.translate,
      'history': Icons.history_edu,
      'perfect': Icons.verified,
    };

    return iconMap[iconName] ?? Icons.emoji_events;
  }
}

/// Compact version for lists
class AchievementBadgeCompact extends StatelessWidget {
  final AchievementModel achievement;
  final VoidCallback? onTap;

  const AchievementBadgeCompact({
    super.key,
    required this.achievement,
    this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final isUnlocked = achievement.isUnlocked;
    final rarityColor = Color(achievement.rarity.colorValue);

    return ListTile(
      onTap: onTap,
      leading: Container(
        width: 48,
        height: 48,
        decoration: BoxDecoration(
          shape: BoxShape.circle,
          color: isUnlocked ? rarityColor.withOpacity(0.2) : Colors.grey[800],
          border: Border.all(
            color: isUnlocked ? rarityColor : Colors.grey[600]!,
            width: 2,
          ),
        ),
        child: Icon(
          Icons.emoji_events,
          color: isUnlocked ? rarityColor : Colors.grey[600],
        ),
      ),
      title: Text(
        achievement.isSecret && !isUnlocked ? '???' : achievement.name,
        style: TextStyle(
          fontWeight: isUnlocked ? FontWeight.bold : FontWeight.normal,
        ),
      ),
      subtitle: Text(
        achievement.isSecret && !isUnlocked
            ? 'Logro secreto'
            : achievement.description,
        maxLines: 1,
        overflow: TextOverflow.ellipsis,
      ),
      trailing: isUnlocked
          ? Icon(Icons.check_circle, color: Colors.green)
          : achievement.progress > 0
              ? Text(
                  '${(achievement.progress * 100).toInt()}%',
                  style: TextStyle(color: rarityColor),
                )
              : null,
    );
  }
}
