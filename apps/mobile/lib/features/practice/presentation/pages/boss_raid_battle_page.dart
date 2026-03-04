import 'dart:async';
import 'dart:math' as math;
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/config/app_theme.dart';
import '../../../../shared/widgets/lottie_overlay.dart';
import '../providers/boss_raid_provider.dart';
import '../../domain/entities/question.dart';
import '../../data/models/boss_raid_models.dart';

/// Boss Raid Battle Page - The main battle interface for boss raids
/// Shows questions, timer, boss HP, damage animations, and combo counter
class BossRaidBattlePage extends ConsumerStatefulWidget {
  final String sessionId;

  const BossRaidBattlePage({super.key, required this.sessionId});

  @override
  ConsumerState<BossRaidBattlePage> createState() => _BossRaidBattlePageState();
}

class _BossRaidBattlePageState extends ConsumerState<BossRaidBattlePage>
    with TickerProviderStateMixin {
  // Timer for the battle countdown
  Timer? _countdownTimer;
  int _remainingSeconds = 300; // 5 minutes default

  // Animation controllers
  late AnimationController _damageShakeController;
  late AnimationController _comboPopController;
  late AnimationController _bossHitController;

  // Damage number display
  final List<_DamageNumber> _damageNumbers = [];

  @override
  void initState() {
    super.initState();

    // Initialize animation controllers
    _damageShakeController = AnimationController(
      duration: const Duration(milliseconds: 500),
      vsync: this,
    );

    _comboPopController = AnimationController(
      duration: const Duration(milliseconds: 300),
      vsync: this,
    );

    _bossHitController = AnimationController(
      duration: const Duration(milliseconds: 200),
      vsync: this,
    );

    // Start countdown timer
    _startCountdown();
  }

  void _startCountdown() {
    _countdownTimer = Timer.periodic(const Duration(seconds: 1), (timer) {
      if (mounted) {
        setState(() {
          if (_remainingSeconds > 0) {
            _remainingSeconds--;
          } else {
            timer.cancel();
            // Auto-complete raid when time runs out
            ref.read(bossRaidProvider.notifier).completeRaid();
          }
        });
      }
    });
  }

  @override
  void dispose() {
    _countdownTimer?.cancel();
    _damageShakeController.dispose();
    _comboPopController.dispose();
    _bossHitController.dispose();
    super.dispose();
  }

  void _showDamageNumber(int damage, bool isCritical) {
    final random = math.Random();
    setState(() {
      _damageNumbers.add(_DamageNumber(
        damage: damage,
        isCritical: isCritical,
        offset: Offset(
          random.nextDouble() * 100 - 50,
          random.nextDouble() * 30 - 15,
        ),
        id: DateTime.now().millisecondsSinceEpoch,
      ));
    });

    // Remove after animation
    Future.delayed(const Duration(milliseconds: 1500), () {
      if (mounted) {
        setState(() {
          _damageNumbers.removeWhere(
              (d) => d.id == DateTime.now().millisecondsSinceEpoch - 1500);
        });
      }
    });
  }

  void _onAnswerSubmitted(BossRaidAnswerResult? result) {
    if (result == null) return;

    // Trigger haptic feedback
    HapticFeedback.mediumImpact();

    // Show damage number
    _showDamageNumber(result.damageDealt, result.currentCombo >= 3);

    // Trigger boss hit animation
    _bossHitController.forward().then((_) => _bossHitController.reverse());

    // Trigger combo animation if combo increased
    if (result.currentCombo > 1) {
      _comboPopController.forward().then((_) => _comboPopController.reverse());
    }

    // Shake screen on damage
    if (result.damageDealt > 0) {
      _damageShakeController.forward().then((_) => _damageShakeController.reset());
    }
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(bossRaidProvider);
    final notifier = ref.read(bossRaidProvider.notifier);

    // Listen for answer results to trigger animations
    ref.listen<BossRaidState>(bossRaidProvider, (previous, next) {
      if (previous?.lastAnswerResult != next.lastAnswerResult &&
          next.lastAnswerResult != null) {
        _onAnswerSubmitted(next.lastAnswerResult);
      }
    });

    // Show loading
    if (state.isLoading && state.questions == null) {
      return Scaffold(
        backgroundColor: const Color(0xFF0A0A0A),
        body: Center(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              // Lottie battle start animation
              Lottie.asset(
                LottieAssets.battleStart,
                width: 150,
                height: 150,
                repeat: true,
                errorBuilder: (_, __, ___) => const CircularProgressIndicator(color: Colors.red),
              ),
              const SizedBox(height: 16),
              const Text(
                'Preparando batalla...',
                style: TextStyle(color: Colors.white70),
              ),
            ],
          ),
        ),
      );
    }

    // Show error
    if (state.error != null && state.questions == null) {
      return Scaffold(
        backgroundColor: const Color(0xFF0A0A0A),
        body: Center(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Icon(Icons.error_outline, color: Colors.red, size: 64),
              const SizedBox(height: 16),
              Text(
                'Error: ${state.error}',
                style: const TextStyle(color: Colors.white70),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 24),
              ElevatedButton(
                onPressed: () => context.pop(),
                child: const Text('Volver'),
              ),
            ],
          ),
        ),
      );
    }

    // Show results screen
    if (state.isCompleted && state.results != null) {
      return _BattleResultsScreen(
        results: state.results!,
        onContinue: () {
          notifier.resetRaid();
          context.pop();
        },
      );
    }

    // Main battle interface
    return Scaffold(
      backgroundColor: const Color(0xFF0A0A0A),
      body: AnimatedBuilder(
        animation: _damageShakeController,
        builder: (context, child) {
          final shake = math.sin(_damageShakeController.value * math.pi * 4) * 5;
          return Transform.translate(
            offset: Offset(shake, 0),
            child: child,
          );
        },
        child: Stack(
          children: [
            // Background with animated gradient
            _AnimatedBattleBackground(),

            // Main content
            SafeArea(
              child: Column(
                children: [
                  // Top bar with timer and close
                  _BattleTopBar(
                    remainingSeconds: _remainingSeconds,
                    onClose: () => _showExitConfirmation(context, notifier),
                  ),

                  const SizedBox(height: 8),

                  // Boss section with HP bar
                  _BossSection(
                    bossName: state.boss?.name ?? 'Boss',
                    currentHp: state.bossCurrentHp,
                    maxHp: state.bossMaxHp,
                    hitController: _bossHitController,
                    damageNumbers: _damageNumbers,
                  ),

                  const SizedBox(height: 16),

                  // Battle stats row
                  _BattleStatsRow(
                    combo: state.currentCombo,
                    totalDamage: state.totalDamageDealt,
                    xpEarned: state.totalXpEarned,
                    comboController: _comboPopController,
                  ),

                  const SizedBox(height: 16),

                  // Progress indicator
                  _QuestionProgress(
                    current: state.currentQuestionIndex + 1,
                    total: state.totalQuestions,
                  ),

                  const SizedBox(height: 16),

                  // Question and answers
                  Expanded(
                    child: state.currentQuestion != null
                        ? _QuestionSection(
                            question: state.currentQuestion!,
                            selectedAnswerId: state.selectedAnswerId,
                            isAnswerSubmitted: state.isAnswerSubmitted,
                            lastResult: state.lastAnswerResult,
                            onSelectAnswer: notifier.selectAnswer,
                          )
                        : const Center(
                            child: Text(
                              'Cargando pregunta...',
                              style: TextStyle(color: Colors.white70),
                            ),
                          ),
                  ),

                  // Bottom action button
                  _BottomActionButton(
                    isAnswerSubmitted: state.isAnswerSubmitted,
                    isSubmitting: state.isSubmittingAnswer,
                    hasSelectedAnswer: state.selectedAnswerId != null,
                    hasMoreQuestions: state.hasMoreQuestions,
                    onSubmit: notifier.submitAnswer,
                    onNext: notifier.nextQuestion,
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  void _showExitConfirmation(BuildContext context, BossRaidNotifier notifier) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        backgroundColor: AppTheme.bgCard,
        title: const Text(
          'Abandonar Batalla',
          style: TextStyle(color: Colors.white),
        ),
        content: const Text(
          'Si abandonas ahora, perderas tu progreso en esta batalla. El boss mantendra el dano recibido.',
          style: TextStyle(color: Colors.white70),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Cancelar'),
          ),
          TextButton(
            onPressed: () {
              Navigator.pop(context);
              notifier.completeRaid();
            },
            style: TextButton.styleFrom(foregroundColor: Colors.red),
            child: const Text('Abandonar'),
          ),
        ],
      ),
    );
  }
}

// ============================================================================
// ANIMATED BATTLE BACKGROUND
// ============================================================================

class _AnimatedBattleBackground extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        gradient: RadialGradient(
          colors: [
            Colors.red.withOpacity(0.15),
            Colors.purple.withOpacity(0.1),
            Colors.black,
          ],
          center: Alignment.topCenter,
          radius: 1.5,
        ),
      ),
    ).animate(onPlay: (c) => c.repeat(reverse: true)).shimmer(
          duration: 3.seconds,
          color: Colors.red.withOpacity(0.05),
        );
  }
}

// ============================================================================
// BATTLE TOP BAR
// ============================================================================

class _BattleTopBar extends StatelessWidget {
  final int remainingSeconds;
  final VoidCallback onClose;

  const _BattleTopBar({
    required this.remainingSeconds,
    required this.onClose,
  });

  @override
  Widget build(BuildContext context) {
    final minutes = remainingSeconds ~/ 60;
    final seconds = remainingSeconds % 60;
    final isLowTime = remainingSeconds <= 60;

    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          // Close button
          IconButton(
            icon: const Icon(Icons.close, color: Colors.white70, size: 28),
            onPressed: onClose,
          ),

          // Timer
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            decoration: BoxDecoration(
              color: isLowTime
                  ? Colors.red.withOpacity(0.3)
                  : Colors.white.withOpacity(0.1),
              borderRadius: BorderRadius.circular(20),
              border: Border.all(
                color: isLowTime ? Colors.red : Colors.white.withOpacity(0.2),
              ),
            ),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(
                  Icons.timer,
                  color: isLowTime ? Colors.red : Colors.white70,
                  size: 20,
                ),
                const SizedBox(width: 8),
                Text(
                  '${minutes.toString().padLeft(2, '0')}:${seconds.toString().padLeft(2, '0')}',
                  style: TextStyle(
                    color: isLowTime ? Colors.red : Colors.white,
                    fontWeight: FontWeight.bold,
                    fontSize: 18,
                    fontFamily: 'monospace',
                  ),
                ),
              ],
            ),
          )
              .animate(
                target: isLowTime ? 1 : 0,
                onPlay: (c) => c.repeat(reverse: true),
              )
              .scale(
                begin: const Offset(1, 1),
                end: const Offset(1.05, 1.05),
                duration: 500.ms,
              ),

          // Placeholder for symmetry
          const SizedBox(width: 48),
        ],
      ),
    );
  }
}

// ============================================================================
// BOSS SECTION WITH HP BAR
// ============================================================================

class _BossSection extends StatelessWidget {
  final String bossName;
  final int currentHp;
  final int maxHp;
  final AnimationController hitController;
  final List<_DamageNumber> damageNumbers;

  const _BossSection({
    required this.bossName,
    required this.currentHp,
    required this.maxHp,
    required this.hitController,
    required this.damageNumbers,
  });

  @override
  Widget build(BuildContext context) {
    final hpPercentage = maxHp > 0 ? currentHp / maxHp : 0.0;
    final hpColor = hpPercentage > 0.5
        ? Colors.red
        : hpPercentage > 0.25
            ? Colors.orange
            : Colors.yellow;

    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 20),
      child: Stack(
        clipBehavior: Clip.none,
        children: [
          Column(
            children: [
              // Boss avatar with hit animation
              AnimatedBuilder(
                animation: hitController,
                builder: (context, child) {
                  return Transform.scale(
                    scale: 1.0 - (hitController.value * 0.1),
                    child: ColorFiltered(
                      colorFilter: ColorFilter.mode(
                        Colors.red.withOpacity(hitController.value * 0.5),
                        BlendMode.srcATop,
                      ),
                      child: child,
                    ),
                  );
                },
                child: Container(
                  width: 100,
                  height: 100,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    gradient: RadialGradient(
                      colors: [
                        Colors.red.shade900,
                        Colors.purple.shade900,
                      ],
                    ),
                    border: Border.all(
                      color: Colors.red.withOpacity(0.5),
                      width: 3,
                    ),
                    boxShadow: [
                      BoxShadow(
                        color: Colors.red.withOpacity(0.3),
                        blurRadius: 20,
                        spreadRadius: 5,
                      ),
                    ],
                  ),
                  child: const Icon(
                    Icons.psychology,
                    color: Colors.white,
                    size: 50,
                  ),
                )
                    .animate(onPlay: (c) => c.repeat(reverse: true))
                    .scale(
                      begin: const Offset(1, 1),
                      end: const Offset(1.05, 1.05),
                      duration: 2.seconds,
                    ),
              ),

              const SizedBox(height: 12),

              // Boss name
              Text(
                bossName,
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                  letterSpacing: 1,
                ),
              ),

              const SizedBox(height: 8),

              // HP Bar
              Container(
                height: 24,
                decoration: BoxDecoration(
                  color: Colors.black.withOpacity(0.5),
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: Colors.white.withOpacity(0.2)),
                ),
                child: Stack(
                  children: [
                    // HP fill
                    FractionallySizedBox(
                      widthFactor: hpPercentage.clamp(0.0, 1.0),
                      child: Container(
                        decoration: BoxDecoration(
                          borderRadius: BorderRadius.circular(12),
                          gradient: LinearGradient(
                            colors: [
                              hpColor.shade700,
                              hpColor.shade500,
                            ],
                          ),
                          boxShadow: [
                            BoxShadow(
                              color: hpColor.withOpacity(0.5),
                              blurRadius: 8,
                            ),
                          ],
                        ),
                      )
                          .animate()
                          .shimmer(duration: 2.seconds, color: Colors.white24),
                    ),

                    // HP text
                    Center(
                      child: Text(
                        '$currentHp / $maxHp HP',
                        style: const TextStyle(
                          color: Colors.white,
                          fontWeight: FontWeight.bold,
                          fontSize: 12,
                          shadows: [
                            Shadow(color: Colors.black, blurRadius: 4),
                          ],
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),

          // Floating damage numbers
          ...damageNumbers.map((d) => Positioned(
                top: 40 + d.offset.dy,
                left: MediaQuery.of(context).size.width / 2 - 50 + d.offset.dx,
                child: _FloatingDamageNumber(
                  damage: d.damage,
                  isCritical: d.isCritical,
                ),
              )),
        ],
      ),
    );
  }
}

class _DamageNumber {
  final int damage;
  final bool isCritical;
  final Offset offset;
  final int id;

  _DamageNumber({
    required this.damage,
    required this.isCritical,
    required this.offset,
    required this.id,
  });
}

class _FloatingDamageNumber extends StatelessWidget {
  final int damage;
  final bool isCritical;

  const _FloatingDamageNumber({
    required this.damage,
    required this.isCritical,
  });

  @override
  Widget build(BuildContext context) {
    return Text(
      '-$damage',
      style: TextStyle(
        color: isCritical ? Colors.yellow : Colors.red,
        fontSize: isCritical ? 32 : 24,
        fontWeight: FontWeight.bold,
        shadows: const [
          Shadow(color: Colors.black, blurRadius: 4),
          Shadow(color: Colors.black, blurRadius: 8),
        ],
      ),
    )
        .animate()
        .fadeIn(duration: 100.ms)
        .slideY(begin: 0, end: -1, duration: 1.seconds)
        .fadeOut(delay: 800.ms, duration: 200.ms)
        .scale(
          begin: const Offset(0.5, 0.5),
          end: isCritical ? const Offset(1.3, 1.3) : const Offset(1, 1),
          duration: 200.ms,
        );
  }
}

// ============================================================================
// BATTLE STATS ROW
// ============================================================================

class _BattleStatsRow extends StatelessWidget {
  final int combo;
  final int totalDamage;
  final int xpEarned;
  final AnimationController comboController;

  const _BattleStatsRow({
    required this.combo,
    required this.totalDamage,
    required this.xpEarned,
    required this.comboController,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 20),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceEvenly,
        children: [
          // Combo counter
          AnimatedBuilder(
            animation: comboController,
            builder: (context, child) {
              return Transform.scale(
                scale: 1.0 + (comboController.value * 0.2),
                child: child,
              );
            },
            child: _StatBadge(
              icon: Icons.bolt,
              label: 'COMBO',
              value: 'x$combo',
              color: combo >= 5
                  ? Colors.yellow
                  : combo >= 3
                      ? Colors.orange
                      : Colors.white,
              isHighlighted: combo >= 3,
            ),
          ),

          // Total damage
          _StatBadge(
            icon: Icons.flash_on,
            label: 'DANO',
            value: totalDamage.toString(),
            color: Colors.red,
          ),

          // XP earned
          _StatBadge(
            icon: Icons.star,
            label: 'XP',
            value: '+$xpEarned',
            color: AppTheme.accentCyan,
          ),
        ],
      ),
    );
  }
}

class _StatBadge extends StatelessWidget {
  final IconData icon;
  final String label;
  final String value;
  final Color color;
  final bool isHighlighted;

  const _StatBadge({
    required this.icon,
    required this.label,
    required this.value,
    required this.color,
    this.isHighlighted = false,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      decoration: BoxDecoration(
        color: color.withOpacity(0.15),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: color.withOpacity(0.3)),
        boxShadow: isHighlighted
            ? [BoxShadow(color: color.withOpacity(0.3), blurRadius: 8)]
            : null,
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, color: color, size: 20),
          const SizedBox(height: 4),
          Text(
            value,
            style: TextStyle(
              color: color,
              fontWeight: FontWeight.bold,
              fontSize: 16,
            ),
          ),
          Text(
            label,
            style: TextStyle(
              color: color.withOpacity(0.7),
              fontSize: 10,
              fontWeight: FontWeight.w600,
            ),
          ),
        ],
      ),
    );
  }
}

// ============================================================================
// QUESTION PROGRESS
// ============================================================================

class _QuestionProgress extends StatelessWidget {
  final int current;
  final int total;

  const _QuestionProgress({
    required this.current,
    required this.total,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 20),
      child: Column(
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                'Pregunta $current de $total',
                style: const TextStyle(
                  color: Colors.white70,
                  fontSize: 12,
                ),
              ),
              Text(
                '${((current / total) * 100).toInt()}%',
                style: const TextStyle(
                  color: Colors.white70,
                  fontSize: 12,
                ),
              ),
            ],
          ),
          const SizedBox(height: 4),
          ClipRRect(
            borderRadius: BorderRadius.circular(4),
            child: LinearProgressIndicator(
              value: current / total,
              minHeight: 6,
              backgroundColor: Colors.white.withOpacity(0.1),
              valueColor: const AlwaysStoppedAnimation<Color>(AppTheme.primaryPurple),
            ),
          ),
        ],
      ),
    );
  }
}

// ============================================================================
// QUESTION SECTION
// ============================================================================

class _QuestionSection extends StatelessWidget {
  final Question question;
  final String? selectedAnswerId;
  final bool isAnswerSubmitted;
  final BossRaidAnswerResult? lastResult;
  final Function(String) onSelectAnswer;

  const _QuestionSection({
    required this.question,
    required this.selectedAnswerId,
    required this.isAnswerSubmitted,
    required this.lastResult,
    required this.onSelectAnswer,
  });

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      padding: const EdgeInsets.symmetric(horizontal: 20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Question text
          Container(
            width: double.infinity,
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: Colors.white.withOpacity(0.05),
              borderRadius: BorderRadius.circular(16),
              border: Border.all(color: Colors.white.withOpacity(0.1)),
            ),
            child: Text(
              question.text,
              style: const TextStyle(
                color: Colors.white,
                fontSize: 16,
                height: 1.5,
              ),
            ),
          ).animate().fadeIn().slideY(begin: 0.1, end: 0),

          // Question image if available
          if (question.imageUrl != null) ...[
            const SizedBox(height: 12),
            ClipRRect(
              borderRadius: BorderRadius.circular(12),
              child: Image.network(
                question.imageUrl!,
                fit: BoxFit.contain,
                errorBuilder: (_, __, ___) => const SizedBox.shrink(),
              ),
            ),
          ],

          const SizedBox(height: 16),

          // Answer options
          ...question.options.asMap().entries.map((entry) {
            final index = entry.key;
            final option = entry.value;
            final isSelected = selectedAnswerId == option.id;
            final isCorrect = lastResult?.correctAnswerId == option.id;
            final isWrong = isAnswerSubmitted &&
                isSelected &&
                lastResult?.correctAnswerId != option.id;

            return Padding(
              padding: const EdgeInsets.only(bottom: 12),
              child: _AnswerOption(
                label: String.fromCharCode(65 + index), // A, B, C, D
                text: option.text,
                imageUrl: option.imageUrl,
                isSelected: isSelected,
                isCorrect: isAnswerSubmitted && isCorrect,
                isWrong: isWrong,
                isDisabled: isAnswerSubmitted,
                onTap: () => onSelectAnswer(option.id),
              )
                  .animate(delay: Duration(milliseconds: 100 * index))
                  .fadeIn()
                  .slideX(begin: 0.1, end: 0),
            );
          }),
        ],
      ),
    );
  }
}

class _AnswerOption extends StatelessWidget {
  final String label;
  final String text;
  final String? imageUrl;
  final bool isSelected;
  final bool isCorrect;
  final bool isWrong;
  final bool isDisabled;
  final VoidCallback onTap;

  const _AnswerOption({
    required this.label,
    required this.text,
    this.imageUrl,
    required this.isSelected,
    required this.isCorrect,
    required this.isWrong,
    required this.isDisabled,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    Color borderColor = Colors.white.withOpacity(0.2);
    Color bgColor = Colors.white.withOpacity(0.05);
    Color labelBgColor = Colors.white.withOpacity(0.1);

    if (isCorrect) {
      borderColor = AppTheme.successGreen;
      bgColor = AppTheme.successGreen.withOpacity(0.15);
      labelBgColor = AppTheme.successGreen;
    } else if (isWrong) {
      borderColor = AppTheme.dangerRed;
      bgColor = AppTheme.dangerRed.withOpacity(0.15);
      labelBgColor = AppTheme.dangerRed;
    } else if (isSelected) {
      borderColor = AppTheme.primaryPurple;
      bgColor = AppTheme.primaryPurple.withOpacity(0.15);
      labelBgColor = AppTheme.primaryPurple;
    }

    return GestureDetector(
      onTap: isDisabled ? null : onTap,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 200),
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: bgColor,
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: borderColor, width: 2),
        ),
        child: Row(
          children: [
            // Label circle
            Container(
              width: 36,
              height: 36,
              decoration: BoxDecoration(
                color: labelBgColor,
                shape: BoxShape.circle,
              ),
              child: Center(
                child: isCorrect
                    ? const Icon(Icons.check, color: Colors.white, size: 20)
                    : isWrong
                        ? const Icon(Icons.close, color: Colors.white, size: 20)
                        : Text(
                            label,
                            style: TextStyle(
                              color: isSelected ? Colors.white : Colors.white70,
                              fontWeight: FontWeight.bold,
                              fontSize: 16,
                            ),
                          ),
              ),
            ),

            const SizedBox(width: 16),

            // Answer text
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    text,
                    style: const TextStyle(
                      color: Colors.white,
                      fontSize: 15,
                    ),
                  ),
                  if (imageUrl != null) ...[
                    const SizedBox(height: 8),
                    ClipRRect(
                      borderRadius: BorderRadius.circular(8),
                      child: Image.network(
                        imageUrl!,
                        height: 80,
                        fit: BoxFit.contain,
                        errorBuilder: (_, __, ___) => const SizedBox.shrink(),
                      ),
                    ),
                  ],
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

// ============================================================================
// BOTTOM ACTION BUTTON
// ============================================================================

class _BottomActionButton extends StatelessWidget {
  final bool isAnswerSubmitted;
  final bool isSubmitting;
  final bool hasSelectedAnswer;
  final bool hasMoreQuestions;
  final VoidCallback onSubmit;
  final VoidCallback onNext;

  const _BottomActionButton({
    required this.isAnswerSubmitted,
    required this.isSubmitting,
    required this.hasSelectedAnswer,
    required this.hasMoreQuestions,
    required this.onSubmit,
    required this.onNext,
  });

  @override
  Widget build(BuildContext context) {
    final isEnabled = isAnswerSubmitted || hasSelectedAnswer;
    final buttonText = isAnswerSubmitted
        ? (hasMoreQuestions ? 'SIGUIENTE' : 'VER RESULTADOS')
        : 'ATACAR';

    final buttonColor = isAnswerSubmitted
        ? AppTheme.primaryPurple
        : AppTheme.dangerRed;

    return SafeArea(
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: SizedBox(
          width: double.infinity,
          height: 56,
          child: ElevatedButton(
            onPressed: isSubmitting || !isEnabled
                ? null
                : (isAnswerSubmitted ? onNext : onSubmit),
            style: ElevatedButton.styleFrom(
              backgroundColor: isEnabled ? buttonColor : Colors.grey.shade800,
              foregroundColor: Colors.white,
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(16),
              ),
              elevation: isEnabled ? 8 : 0,
              shadowColor: buttonColor.withOpacity(0.5),
            ),
            child: isSubmitting
                ? const SizedBox(
                    width: 24,
                    height: 24,
                    child: CircularProgressIndicator(
                      color: Colors.white,
                      strokeWidth: 2,
                    ),
                  )
                : Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      if (!isAnswerSubmitted) ...[
                        const Icon(Icons.flash_on, size: 24),
                        const SizedBox(width: 8),
                      ],
                      Text(
                        buttonText,
                        style: const TextStyle(
                          fontSize: 18,
                          fontWeight: FontWeight.bold,
                          letterSpacing: 2,
                        ),
                      ),
                      if (isAnswerSubmitted) ...[
                        const SizedBox(width: 8),
                        const Icon(Icons.arrow_forward, size: 24),
                      ],
                    ],
                  ),
          ),
        ),
      ),
    );
  }
}

// ============================================================================
// BATTLE RESULTS SCREEN
// ============================================================================

class _BattleResultsScreen extends StatelessWidget {
  final BossRaidResults results;
  final VoidCallback onContinue;

  const _BattleResultsScreen({
    required this.results,
    required this.onContinue,
  });

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0A0A0A),
      body: Stack(
        children: [
          // Background
          Container(
            decoration: BoxDecoration(
              gradient: RadialGradient(
                colors: [
                  (results.bossDefeated ? Colors.green : Colors.purple)
                      .withOpacity(0.2),
                  Colors.black,
                ],
                center: Alignment.center,
                radius: 1.0,
              ),
            ),
          ),

          // Content
          SafeArea(
            child: SingleChildScrollView(
              padding: const EdgeInsets.all(24),
              child: Column(
                children: [
                  const SizedBox(height: 20),

                  // Victory/Defeat icon
                  Container(
                    width: 120,
                    height: 120,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      color: (results.bossDefeated ? Colors.green : Colors.purple)
                          .withOpacity(0.2),
                      border: Border.all(
                        color: results.bossDefeated ? Colors.green : Colors.purple,
                        width: 3,
                      ),
                    ),
                    child: Icon(
                      results.bossDefeated ? Icons.emoji_events : Icons.shield,
                      color: results.bossDefeated ? Colors.amber : Colors.purple,
                      size: 60,
                    ),
                  )
                      .animate()
                      .scale(
                        begin: const Offset(0, 0),
                        end: const Offset(1, 1),
                        duration: 500.ms,
                        curve: Curves.elasticOut,
                      ),

                  const SizedBox(height: 24),

                  // Title
                  Text(
                    results.bossDefeated ? 'VICTORIA!' : 'BATALLA COMPLETADA',
                    style: TextStyle(
                      color: results.bossDefeated ? Colors.amber : Colors.white,
                      fontSize: 28,
                      fontWeight: FontWeight.bold,
                      letterSpacing: 3,
                    ),
                  ).animate().fadeIn(delay: 300.ms),

                  const SizedBox(height: 32),

                  // Stats grid
                  _ResultsStatGrid(results: results),

                  const SizedBox(height: 24),

                  // Rewards section
                  if (results.rewards.isNotEmpty) ...[
                    const Text(
                      'RECOMPENSAS',
                      style: TextStyle(
                        color: Colors.white70,
                        fontSize: 14,
                        fontWeight: FontWeight.bold,
                        letterSpacing: 2,
                      ),
                    ),
                    const SizedBox(height: 12),
                    _RewardsList(rewards: results.rewards),
                    const SizedBox(height: 24),
                  ],

                  // Rank badge if available
                  if (results.rankInRaid != null)
                    Container(
                      padding: const EdgeInsets.symmetric(
                        horizontal: 24,
                        vertical: 12,
                      ),
                      decoration: BoxDecoration(
                        color: Colors.amber.withOpacity(0.2),
                        borderRadius: BorderRadius.circular(20),
                        border: Border.all(color: Colors.amber.withOpacity(0.5)),
                      ),
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          const Icon(Icons.leaderboard, color: Colors.amber),
                          const SizedBox(width: 12),
                          Text(
                            'Puesto #${results.rankInRaid} en la Raid',
                            style: const TextStyle(
                              color: Colors.amber,
                              fontWeight: FontWeight.bold,
                              fontSize: 16,
                            ),
                          ),
                        ],
                      ),
                    ).animate().fadeIn(delay: 800.ms).slideY(begin: 0.2, end: 0),

                  const SizedBox(height: 32),

                  // Continue button
                  SizedBox(
                    width: double.infinity,
                    height: 56,
                    child: ElevatedButton(
                      onPressed: onContinue,
                      style: ElevatedButton.styleFrom(
                        backgroundColor: AppTheme.primaryPurple,
                        foregroundColor: Colors.white,
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(16),
                        ),
                      ),
                      child: const Text(
                        'CONTINUAR',
                        style: TextStyle(
                          fontSize: 18,
                          fontWeight: FontWeight.bold,
                          letterSpacing: 2,
                        ),
                      ),
                    ),
                  ).animate().fadeIn(delay: 1.seconds),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _ResultsStatGrid extends StatelessWidget {
  final BossRaidResults results;

  const _ResultsStatGrid({required this.results});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.05),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: Colors.white.withOpacity(0.1)),
      ),
      child: Column(
        children: [
          Row(
            children: [
              Expanded(
                child: _ResultStatItem(
                  icon: Icons.flash_on,
                  label: 'Dano Total',
                  value: results.totalDamage.toString(),
                  color: Colors.red,
                ),
              ),
              Expanded(
                child: _ResultStatItem(
                  icon: Icons.star,
                  label: 'XP Ganado',
                  value: '+${results.totalXp}',
                  color: AppTheme.accentCyan,
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          Row(
            children: [
              Expanded(
                child: _ResultStatItem(
                  icon: Icons.check_circle,
                  label: 'Correctas',
                  value: '${results.correctAnswers}/${results.totalQuestions}',
                  color: AppTheme.successGreen,
                ),
              ),
              Expanded(
                child: _ResultStatItem(
                  icon: Icons.bolt,
                  label: 'Mejor Combo',
                  value: 'x${results.bestCombo}',
                  color: Colors.orange,
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          Row(
            children: [
              Expanded(
                child: _ResultStatItem(
                  icon: Icons.percent,
                  label: 'Precision',
                  value: '${results.accuracyPercentage.toStringAsFixed(0)}%',
                  color: Colors.purple,
                ),
              ),
              Expanded(
                child: _ResultStatItem(
                  icon: Icons.timer,
                  label: 'Duracion',
                  value: results.formattedDuration,
                  color: Colors.white70,
                ),
              ),
            ],
          ),
        ],
      ),
    )
        .animate()
        .fadeIn(delay: 400.ms)
        .slideY(begin: 0.2, end: 0);
  }
}

class _ResultStatItem extends StatelessWidget {
  final IconData icon;
  final String label;
  final String value;
  final Color color;

  const _ResultStatItem({
    required this.icon,
    required this.label,
    required this.value,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Icon(icon, color: color, size: 28),
        const SizedBox(height: 8),
        Text(
          value,
          style: TextStyle(
            color: color,
            fontSize: 20,
            fontWeight: FontWeight.bold,
          ),
        ),
        const SizedBox(height: 4),
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

class _RewardsList extends StatelessWidget {
  final List<RaidReward> rewards;

  const _RewardsList({required this.rewards});

  @override
  Widget build(BuildContext context) {
    return Wrap(
      spacing: 12,
      runSpacing: 12,
      alignment: WrapAlignment.center,
      children: rewards.asMap().entries.map((entry) {
        final index = entry.key;
        final reward = entry.value;

        IconData icon;
        Color color;
        String text;

        switch (reward.type) {
          case 'gold':
            icon = Icons.monetization_on;
            color = Colors.amber;
            text = '+${reward.amount} Oro';
            break;
          case 'xp':
            icon = Icons.star;
            color = AppTheme.accentCyan;
            text = '+${reward.amount} XP';
            break;
          case 'item':
            icon = Icons.inventory_2;
            color = Colors.purple;
            text = reward.name ?? 'Item';
            break;
          default:
            icon = Icons.card_giftcard;
            color = Colors.white;
            text = reward.name ?? 'Recompensa';
        }

        return Container(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
          decoration: BoxDecoration(
            color: color.withOpacity(0.15),
            borderRadius: BorderRadius.circular(20),
            border: Border.all(color: color.withOpacity(0.3)),
          ),
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(icon, color: color, size: 20),
              const SizedBox(width: 8),
              Text(
                text,
                style: TextStyle(
                  color: color,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ],
          ),
        )
            .animate(delay: Duration(milliseconds: 600 + (index * 100)))
            .fadeIn()
            .scale(begin: const Offset(0.8, 0.8), end: const Offset(1, 1));
      }).toList(),
    );
  }
}
