import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import '../../../../core/services/combo_service.dart';

class ComboOverlay extends StatelessWidget {
  final int comboCount;
  final int? bonusXp;

  const ComboOverlay({
    super.key,
    required this.comboCount,
    this.bonusXp,
  });

  @override
  Widget build(BuildContext context) {
    if (comboCount < 2) return const SizedBox.shrink();

    final display = ComboService.getComboDisplay(comboCount);

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
      decoration: BoxDecoration(
        color: Colors.black.withOpacity(0.9),
        borderRadius: BorderRadius.circular(24),
        border: Border.all(color: display.color, width: 3),
        boxShadow: [
          BoxShadow(
            color: display.color.withOpacity(0.6),
            blurRadius: display.hasGlow ? 25 : 15,
            spreadRadius: display.hasGlow ? 5 : 2,
          ),
          if (display.hasGlow)
            BoxShadow(
              color: display.color.withOpacity(0.3),
              blurRadius: 40,
              spreadRadius: 10,
            ),
        ],
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              _buildComboIcon(display),
              const SizedBox(width: 10),
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                mainAxisSize: MainAxisSize.min,
                children: [
                  Text(
                    display.text,
                    style: TextStyle(
                      color: display.color,
                      fontWeight: FontWeight.w900,
                      fontSize: display.level >= ComboLevel.legendary ? 20 : 16,
                      letterSpacing: 2,
                      shadows: [
                        Shadow(color: display.color, blurRadius: 15),
                        if (display.hasGlow)
                          Shadow(color: display.color.withOpacity(0.8), blurRadius: 25),
                      ],
                    ),
                  ),
                  Text(
                    'COMBO x$comboCount',
                    style: TextStyle(
                      color: Colors.white.withOpacity(0.9),
                      fontWeight: FontWeight.w700,
                      fontSize: 14,
                      letterSpacing: 1,
                      fontStyle: FontStyle.italic,
                    ),
                  ),
                ],
              ),
              const SizedBox(width: 10),
              _buildComboIcon(display),
            ],
          ),
          if (bonusXp != null && bonusXp! > 0) ...[
            const SizedBox(height: 8),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
              decoration: BoxDecoration(
                color: Colors.amber.withOpacity(0.2),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: Colors.amber.withOpacity(0.5)),
              ),
              child: Text(
                '+$bonusXp XP BONUS',
                style: const TextStyle(
                  color: Colors.amber,
                  fontWeight: FontWeight.bold,
                  fontSize: 12,
                  letterSpacing: 1,
                ),
              ),
            ).animate()
              .fadeIn(duration: 200.ms)
              .scale(begin: const Offset(0.8, 0.8)),
          ],
        ],
      ),
    )
    .animate(key: ValueKey(comboCount))
    .scale(
      begin: const Offset(0.5, 0.5),
      end: const Offset(1, 1),
      duration: 400.ms,
      curve: Curves.easeOutBack,
    )
    .then()
    .custom(
      duration: display.hasShake ? 500.ms : 0.ms,
      builder: (context, value, child) {
        if (!display.hasShake) return child;
        final offset = (1 - value) * 4;
        return Transform.translate(
          offset: Offset(
            offset * (value * 10).remainder(2) - 1,
            0,
          ),
          child: child,
        );
      },
    );
  }

  Widget _buildComboIcon(ComboDisplay display) {
    Widget icon = Icon(
      display.icon,
      color: display.color,
      size: display.level >= ComboLevel.legendary ? 28 : 24,
    );

    // Base animation for all combos
    icon = icon.animate(onPlay: (c) => c.repeat(reverse: true))
      .scale(
        begin: const Offset(1, 1),
        end: const Offset(1.2, 1.2),
        duration: 500.ms,
      );

    // Add shimmer for sparkles effect
    if (display.hasSparkles) {
      icon = icon.animate(onPlay: (c) => c.repeat())
        .shimmer(
          duration: 1500.ms,
          color: Colors.white.withOpacity(0.5),
        );
    }

    // Add rotation for flames effect
    if (display.hasFlames) {
      icon = icon.animate(onPlay: (c) => c.repeat(reverse: true))
        .rotate(
          begin: -0.05,
          end: 0.05,
          duration: 200.ms,
        );
    }

    // Add pulsing glow for explosion/glow effects
    if (display.hasExplosion || display.hasGlow) {
      icon = Stack(
        alignment: Alignment.center,
        children: [
          Container(
            width: 40,
            height: 40,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              boxShadow: [
                BoxShadow(
                  color: display.color.withOpacity(0.6),
                  blurRadius: 20,
                  spreadRadius: 5,
                ),
              ],
            ),
          ).animate(onPlay: (c) => c.repeat(reverse: true))
            .scale(
              begin: const Offset(0.8, 0.8),
              end: const Offset(1.3, 1.3),
              duration: 800.ms,
            )
            .fadeOut(begin: 0.8, duration: 800.ms),
          icon,
        ],
      );
    }

    return icon;
  }
}

/// Widget to show XP earned with combo bonus breakdown
class ComboXpDisplay extends StatelessWidget {
  final int baseXp;
  final int comboBonus;
  final int combo;

  const ComboXpDisplay({
    super.key,
    required this.baseXp,
    required this.comboBonus,
    required this.combo,
  });

  int get totalXp => baseXp + comboBonus;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [
            Colors.amber.withOpacity(0.2),
            Colors.orange.withOpacity(0.1),
          ],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.amber.withOpacity(0.3)),
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(Icons.star, color: Colors.amber, size: 32),
              const SizedBox(width: 8),
              Text(
                '+$totalXp XP',
                style: const TextStyle(
                  color: Colors.amber,
                  fontWeight: FontWeight.w900,
                  fontSize: 28,
                  letterSpacing: 1,
                ),
              ),
            ],
          ).animate()
            .scale(begin: const Offset(0, 0), duration: 300.ms, curve: Curves.elasticOut),
          const SizedBox(height: 8),
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              _buildXpPart('Base', baseXp, Colors.white70),
              if (comboBonus > 0) ...[
                const Padding(
                  padding: EdgeInsets.symmetric(horizontal: 8),
                  child: Text('+', style: TextStyle(color: Colors.white54)),
                ),
                _buildXpPart('Combo x$combo', comboBonus, Colors.orange),
              ],
            ],
          ).animate().fadeIn(delay: 200.ms, duration: 300.ms),
        ],
      ),
    );
  }

  Widget _buildXpPart(String label, int xp, Color color) {
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        Text(
          '$xp',
          style: TextStyle(
            color: color,
            fontWeight: FontWeight.bold,
            fontSize: 18,
          ),
        ),
        Text(
          label,
          style: TextStyle(
            color: color.withOpacity(0.7),
            fontSize: 12,
          ),
        ),
      ],
    );
  }
}
