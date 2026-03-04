import 'package:flutter/material.dart';
import 'dart:math' as math;
import '../../data/models/achievement_model.dart';

/// Full-screen achievement unlock animation
class AchievementUnlockAnimation extends StatefulWidget {
  final AchievementModel achievement;
  final VoidCallback onComplete;
  final Duration duration;

  const AchievementUnlockAnimation({
    super.key,
    required this.achievement,
    required this.onComplete,
    this.duration = const Duration(milliseconds: 3000),
  });

  @override
  State<AchievementUnlockAnimation> createState() =>
      _AchievementUnlockAnimationState();
}

class _AchievementUnlockAnimationState extends State<AchievementUnlockAnimation>
    with TickerProviderStateMixin {
  late AnimationController _mainController;
  late AnimationController _particleController;
  late AnimationController _pulseController;

  late Animation<double> _scaleAnimation;
  late Animation<double> _opacityAnimation;
  late Animation<double> _textSlideAnimation;
  late Animation<double> _glowAnimation;

  @override
  void initState() {
    super.initState();
    _setupAnimations();
    _startAnimations();
  }

  void _setupAnimations() {
    _mainController = AnimationController(
      duration: widget.duration,
      vsync: this,
    );

    _particleController = AnimationController(
      duration: const Duration(milliseconds: 2000),
      vsync: this,
    );

    _pulseController = AnimationController(
      duration: const Duration(milliseconds: 800),
      vsync: this,
    );

    _scaleAnimation = TweenSequence<double>([
      TweenSequenceItem(
        tween: Tween<double>(begin: 0.0, end: 1.3)
            .chain(CurveTween(curve: Curves.easeOutBack)),
        weight: 30,
      ),
      TweenSequenceItem(
        tween: Tween<double>(begin: 1.3, end: 1.0)
            .chain(CurveTween(curve: Curves.easeInOut)),
        weight: 20,
      ),
      TweenSequenceItem(
        tween: Tween<double>(begin: 1.0, end: 1.0),
        weight: 50,
      ),
    ]).animate(_mainController);

    _opacityAnimation = TweenSequence<double>([
      TweenSequenceItem(
        tween: Tween<double>(begin: 0.0, end: 1.0),
        weight: 20,
      ),
      TweenSequenceItem(
        tween: Tween<double>(begin: 1.0, end: 1.0),
        weight: 60,
      ),
      TweenSequenceItem(
        tween: Tween<double>(begin: 1.0, end: 0.0),
        weight: 20,
      ),
    ]).animate(_mainController);

    _textSlideAnimation = TweenSequence<double>([
      TweenSequenceItem(
        tween: Tween<double>(begin: 50.0, end: 0.0)
            .chain(CurveTween(curve: Curves.easeOutCubic)),
        weight: 40,
      ),
      TweenSequenceItem(
        tween: Tween<double>(begin: 0.0, end: 0.0),
        weight: 60,
      ),
    ]).animate(_mainController);

    _glowAnimation = Tween<double>(begin: 0.0, end: 1.0).animate(
      CurvedAnimation(parent: _pulseController, curve: Curves.easeInOut),
    );

    _mainController.addStatusListener((status) {
      if (status == AnimationStatus.completed) {
        widget.onComplete();
      }
    });
  }

  void _startAnimations() {
    _mainController.forward();
    _particleController.repeat();
    _pulseController.repeat(reverse: true);
  }

  @override
  void dispose() {
    _mainController.dispose();
    _particleController.dispose();
    _pulseController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final rarityColor = Color(widget.achievement.rarity.colorValue);

    return AnimatedBuilder(
      animation: Listenable.merge([
        _mainController,
        _particleController,
        _pulseController,
      ]),
      builder: (context, child) {
        return Opacity(
          opacity: _opacityAnimation.value,
          child: Container(
            color: Colors.black87,
            child: Stack(
              children: [
                // Particle effects
                ..._buildParticles(rarityColor),

                // Main content
                Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      // "Achievement Unlocked" text
                      Transform.translate(
                        offset: Offset(0, -_textSlideAnimation.value),
                        child: Opacity(
                          opacity: _opacityAnimation.value,
                          child: Text(
                            'LOGRO DESBLOQUEADO',
                            style: TextStyle(
                              color: rarityColor,
                              fontSize: 14,
                              fontWeight: FontWeight.bold,
                              letterSpacing: 4,
                            ),
                          ),
                        ),
                      ),
                      const SizedBox(height: 30),

                      // Badge
                      Transform.scale(
                        scale: _scaleAnimation.value,
                        child: Stack(
                          alignment: Alignment.center,
                          children: [
                            // Glow effect
                            AnimatedBuilder(
                              animation: _glowAnimation,
                              builder: (context, child) {
                                return Container(
                                  width: 160 + (_glowAnimation.value * 20),
                                  height: 160 + (_glowAnimation.value * 20),
                                  decoration: BoxDecoration(
                                    shape: BoxShape.circle,
                                    boxShadow: [
                                      BoxShadow(
                                        color: rarityColor.withOpacity(
                                            0.3 + (_glowAnimation.value * 0.3)),
                                        blurRadius:
                                            30 + (_glowAnimation.value * 20),
                                        spreadRadius:
                                            10 + (_glowAnimation.value * 10),
                                      ),
                                    ],
                                  ),
                                );
                              },
                            ),
                            // Badge container
                            Container(
                              width: 140,
                              height: 140,
                              decoration: BoxDecoration(
                                shape: BoxShape.circle,
                                gradient: LinearGradient(
                                  colors: [
                                    rarityColor.withOpacity(0.8),
                                    rarityColor,
                                  ],
                                  begin: Alignment.topLeft,
                                  end: Alignment.bottomRight,
                                ),
                                border: Border.all(
                                  color: Colors.white.withOpacity(0.5),
                                  width: 4,
                                ),
                              ),
                              child: const Icon(
                                Icons.emoji_events,
                                size: 70,
                                color: Colors.white,
                              ),
                            ),
                          ],
                        ),
                      ),
                      const SizedBox(height: 30),

                      // Achievement name
                      Transform.translate(
                        offset: Offset(0, _textSlideAnimation.value),
                        child: Text(
                          widget.achievement.name,
                          style: const TextStyle(
                            color: Colors.white,
                            fontSize: 28,
                            fontWeight: FontWeight.bold,
                          ),
                          textAlign: TextAlign.center,
                        ),
                      ),
                      const SizedBox(height: 12),

                      // Description
                      Padding(
                        padding: const EdgeInsets.symmetric(horizontal: 40),
                        child: Text(
                          widget.achievement.description,
                          style: TextStyle(
                            color: Colors.grey[400],
                            fontSize: 16,
                          ),
                          textAlign: TextAlign.center,
                        ),
                      ),
                      const SizedBox(height: 24),

                      // Rewards
                      if (widget.achievement.xpReward > 0 ||
                          widget.achievement.goldReward > 0)
                        Row(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            if (widget.achievement.xpReward > 0)
                              _RewardChip(
                                icon: Icons.star,
                                value: '+${widget.achievement.xpReward} XP',
                                color: Colors.purple,
                              ),
                            if (widget.achievement.xpReward > 0 &&
                                widget.achievement.goldReward > 0)
                              const SizedBox(width: 16),
                            if (widget.achievement.goldReward > 0)
                              _RewardChip(
                                icon: Icons.monetization_on,
                                value: '+${widget.achievement.goldReward}',
                                color: Colors.amber,
                              ),
                          ],
                        ),
                    ],
                  ),
                ),

                // Tap to dismiss hint
                Positioned(
                  bottom: 50,
                  left: 0,
                  right: 0,
                  child: Center(
                    child: Text(
                      'Toca para continuar',
                      style: TextStyle(
                        color: Colors.grey[600],
                        fontSize: 14,
                      ),
                    ),
                  ),
                ),
              ],
            ),
          ),
        );
      },
    );
  }

  List<Widget> _buildParticles(Color color) {
    final particles = <Widget>[];
    final random = math.Random(42); // Fixed seed for consistent positions

    for (int i = 0; i < 20; i++) {
      final startX = random.nextDouble() * MediaQuery.of(context).size.width;
      final startY = random.nextDouble() * MediaQuery.of(context).size.height;
      final size = 4.0 + random.nextDouble() * 8;
      final delay = random.nextDouble();

      particles.add(
        AnimatedBuilder(
          animation: _particleController,
          builder: (context, child) {
            final progress =
                ((_particleController.value + delay) % 1.0);
            final y = startY - (progress * 200);
            final opacity = 1.0 - progress;

            return Positioned(
              left: startX,
              top: y,
              child: Opacity(
                opacity: opacity * _opacityAnimation.value,
                child: Container(
                  width: size,
                  height: size,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    color: i % 2 == 0 ? color : Colors.white,
                  ),
                ),
              ),
            );
          },
        ),
      );
    }

    return particles;
  }
}

class _RewardChip extends StatelessWidget {
  final IconData icon;
  final String value;
  final Color color;

  const _RewardChip({
    required this.icon,
    required this.value,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      decoration: BoxDecoration(
        color: color.withOpacity(0.2),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: color.withOpacity(0.5)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, color: color, size: 20),
          const SizedBox(width: 8),
          Text(
            value,
            style: TextStyle(
              color: color,
              fontWeight: FontWeight.bold,
              fontSize: 16,
            ),
          ),
        ],
      ),
    );
  }
}

/// Notification toast for achievement unlocks
class AchievementToast extends StatefulWidget {
  final AchievementModel achievement;
  final VoidCallback? onTap;
  final VoidCallback onDismiss;

  const AchievementToast({
    super.key,
    required this.achievement,
    this.onTap,
    required this.onDismiss,
  });

  @override
  State<AchievementToast> createState() => _AchievementToastState();
}

class _AchievementToastState extends State<AchievementToast>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  late Animation<Offset> _slideAnimation;
  late Animation<double> _opacityAnimation;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      duration: const Duration(milliseconds: 300),
      vsync: this,
    );

    _slideAnimation = Tween<Offset>(
      begin: const Offset(0, -1),
      end: Offset.zero,
    ).animate(CurvedAnimation(parent: _controller, curve: Curves.easeOutCubic));

    _opacityAnimation = Tween<double>(begin: 0, end: 1).animate(_controller);

    _controller.forward();

    // Auto dismiss after 4 seconds
    Future.delayed(const Duration(seconds: 4), () {
      if (mounted) {
        _dismiss();
      }
    });
  }

  void _dismiss() async {
    await _controller.reverse();
    widget.onDismiss();
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final rarityColor = Color(widget.achievement.rarity.colorValue);

    return AnimatedBuilder(
      animation: _controller,
      builder: (context, child) {
        return SlideTransition(
          position: _slideAnimation,
          child: Opacity(
            opacity: _opacityAnimation.value,
            child: GestureDetector(
              onTap: widget.onTap,
              onVerticalDragEnd: (details) {
                if (details.primaryVelocity! < 0) {
                  _dismiss();
                }
              },
              child: Container(
                margin: const EdgeInsets.all(16),
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: Colors.grey[900],
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(color: rarityColor, width: 2),
                  boxShadow: [
                    BoxShadow(
                      color: rarityColor.withOpacity(0.3),
                      blurRadius: 12,
                      spreadRadius: 2,
                    ),
                  ],
                ),
                child: Row(
                  children: [
                    Container(
                      width: 50,
                      height: 50,
                      decoration: BoxDecoration(
                        shape: BoxShape.circle,
                        gradient: LinearGradient(
                          colors: [
                            rarityColor.withOpacity(0.8),
                            rarityColor,
                          ],
                        ),
                      ),
                      child: const Icon(
                        Icons.emoji_events,
                        color: Colors.white,
                        size: 28,
                      ),
                    ),
                    const SizedBox(width: 16),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Text(
                            'LOGRO DESBLOQUEADO',
                            style: TextStyle(
                              color: rarityColor,
                              fontSize: 10,
                              fontWeight: FontWeight.bold,
                              letterSpacing: 1,
                            ),
                          ),
                          const SizedBox(height: 4),
                          Text(
                            widget.achievement.name,
                            style: const TextStyle(
                              color: Colors.white,
                              fontWeight: FontWeight.bold,
                              fontSize: 16,
                            ),
                          ),
                        ],
                      ),
                    ),
                    if (widget.achievement.xpReward > 0)
                      Container(
                        padding: const EdgeInsets.symmetric(
                          horizontal: 8,
                          vertical: 4,
                        ),
                        decoration: BoxDecoration(
                          color: Colors.purple.withOpacity(0.2),
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: Text(
                          '+${widget.achievement.xpReward} XP',
                          style: const TextStyle(
                            color: Colors.purple,
                            fontWeight: FontWeight.bold,
                            fontSize: 12,
                          ),
                        ),
                      ),
                  ],
                ),
              ),
            ),
          ),
        );
      },
    );
  }
}
