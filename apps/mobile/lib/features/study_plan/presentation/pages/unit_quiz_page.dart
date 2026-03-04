import 'dart:math';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:go_router/go_router.dart';

import '../providers/unit_quiz_provider.dart';
import '../../../practice/domain/entities/question.dart';
import '../../../practice/presentation/widgets/combo_overlay.dart';
import '../../../../shared/widgets/pressable_scale.dart';
import '../../../../shared/widgets/feedback_overlay.dart';
import '../../../../shared/widgets/animated_feedback/xp_counter.dart';
import '../../../../core/services/dopamine_engine.dart';
import '../../../../core/config/routes.dart';

/// Unit Quiz Page - A quiz session for a specific study unit
class UnitQuizPage extends ConsumerStatefulWidget {
  final String unitId;

  const UnitQuizPage({super.key, required this.unitId});

  @override
  ConsumerState<UnitQuizPage> createState() => _UnitQuizPageState();
}

class _UnitQuizPageState extends ConsumerState<UnitQuizPage>
    with TickerProviderStateMixin {
  late AnimationController _correctAnimController;
  late AnimationController _incorrectAnimController;
  late AnimationController _xpAnimController;

  bool _showCorrectAnimation = false;
  bool _showIncorrectAnimation = false;
  bool _showXpGain = false;
  int _animatedXp = 0;

  @override
  void initState() {
    super.initState();

    _correctAnimController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 600),
    );

    _incorrectAnimController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 800),
    );

    _xpAnimController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1000),
    );

    // Initialize DopamineEngine
    DopamineEngine().initialize();

    // Start the quiz
    WidgetsBinding.instance.addPostFrameCallback((_) {
      ref.read(unitQuizProvider.notifier).startQuiz(unitId: widget.unitId);
    });
  }

  @override
  void dispose() {
    _correctAnimController.dispose();
    _incorrectAnimController.dispose();
    _xpAnimController.dispose();
    super.dispose();
  }

  void _triggerFeedback(bool isCorrect, int xpEarned, int combo) {
    setState(() {
      if (isCorrect) {
        _showCorrectAnimation = true;
        _showXpGain = true;
        _animatedXp = xpEarned;
        _correctAnimController.forward(from: 0);
        _xpAnimController.forward(from: 0);

        DopamineEngine.showCorrectAnswerOverlay(
          context,
          xpEarned: xpEarned,
          combo: combo,
        );
      } else {
        _showIncorrectAnimation = true;
        _incorrectAnimController.forward(from: 0);
        DopamineEngine.showIncorrectAnswerOverlay(context);
      }
    });

    // Auto-hide animations
    Future.delayed(Duration(milliseconds: isCorrect ? 600 : 800), () {
      if (mounted) {
        setState(() {
          _showCorrectAnimation = false;
          _showIncorrectAnimation = false;
        });
      }
    });

    Future.delayed(const Duration(milliseconds: 1500), () {
      if (mounted) {
        setState(() {
          _showXpGain = false;
        });
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(unitQuizProvider);
    final notifier = ref.read(unitQuizProvider.notifier);
    final currentQuestion = state.currentQuestion;

    // Listen for answer checked to trigger feedback
    ref.listen<UnitQuizState>(unitQuizProvider, (previous, next) {
      if (previous != null &&
          !previous.isAnswerChecked &&
          next.isAnswerChecked) {
        _triggerFeedback(
          next.isCurrentCorrect,
          next.xpAwarded,
          next.comboCount,
        );
      }
    });

    if (state.isLoading) {
      return Scaffold(
        backgroundColor: const Color(0xFF0A0A0A),
        body: Center(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const CircularProgressIndicator(
                valueColor: AlwaysStoppedAnimation<Color>(Colors.amber),
              ),
              const SizedBox(height: 16),
              Text(
                'Preparando Quiz...',
                style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                  color: Colors.white70,
                ),
              ),
            ],
          ),
        ),
      );
    }

    if (state.error != null) {
      return Scaffold(
        backgroundColor: const Color(0xFF0A0A0A),
        body: Center(
          child: Padding(
            padding: const EdgeInsets.all(24),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                const Icon(
                  Icons.error_outline,
                  color: Colors.red,
                  size: 64,
                ),
                const SizedBox(height: 16),
                Text(
                  'Error',
                  style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                    color: Colors.white,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const SizedBox(height: 8),
                Text(
                  state.error!,
                  style: const TextStyle(color: Colors.white70),
                  textAlign: TextAlign.center,
                ),
                const SizedBox(height: 24),
                ElevatedButton.icon(
                  onPressed: () => notifier.startQuiz(unitId: widget.unitId),
                  icon: const Icon(Icons.refresh),
                  label: const Text('Reintentar'),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.blue,
                    foregroundColor: Colors.white,
                  ),
                ),
              ],
            ),
          ),
        ),
      );
    }

    if (state.isFinished) {
      return _QuizResultsScreen(
        state: state,
        onRetry: () => notifier.retryQuiz(),
        onReturn: () => context.go(AppRoutes.studyPlan),
      );
    }

    if (currentQuestion == null) {
      return Scaffold(
        backgroundColor: const Color(0xFF0A0A0A),
        body: Center(
          child: Text(
            'Cargando preguntas...',
            style: TextStyle(color: Colors.white70),
          ),
        ),
      );
    }

    return Scaffold(
      backgroundColor: const Color(0xFF0A0A0A),
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.close, color: Colors.white),
          tooltip: 'Cerrar',
          onPressed: () => _showExitConfirmation(context),
        ),
        title: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              state.unitName,
              style: const TextStyle(
                color: Colors.white,
                fontSize: 14,
                fontWeight: FontWeight.w500,
              ),
            ),
            const SizedBox(height: 4),
            ClipRRect(
              borderRadius: BorderRadius.circular(4),
              child: LinearProgressIndicator(
                value: (state.currentIndex + 1) / state.questions.length,
                backgroundColor: Colors.grey[800],
                valueColor: AlwaysStoppedAnimation<Color>(
                  _getProgressColor(state.currentIndex, state.questions.length),
                ),
                minHeight: 6,
              ),
            ),
          ],
        ),
        actions: [
          // XP display
          Container(
            margin: const EdgeInsets.only(right: 16),
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
            decoration: BoxDecoration(
              color: Colors.amber.withOpacity(0.2),
              borderRadius: BorderRadius.circular(20),
              border: Border.all(color: Colors.amber.withOpacity(0.5)),
            ),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                const Icon(Icons.star, color: Colors.amber, size: 18),
                const SizedBox(width: 4),
                Text(
                  '${state.totalXp}',
                  style: const TextStyle(
                    color: Colors.amber,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
      body: Stack(
        children: [
          // Main content
          SafeArea(
            child: Padding(
              padding: const EdgeInsets.all(20),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Question counter
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text(
                        'Pregunta ${state.currentIndex + 1} de ${state.questions.length}',
                        style: TextStyle(
                          color: Colors.grey[400],
                          fontSize: 14,
                        ),
                      ),
                      if (currentQuestion.attemptType != AttemptType.newQuestion)
                        _AttemptTypeBadge(type: currentQuestion.attemptType),
                    ],
                  ),
                  const SizedBox(height: 16),

                  // Question text
                  Expanded(
                    child: SingleChildScrollView(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          // Question image if present
                          if (currentQuestion.imageUrl != null) ...[
                            ClipRRect(
                              borderRadius: BorderRadius.circular(12),
                              child: Image.network(
                                currentQuestion.imageUrl!,
                                width: double.infinity,
                                height: 200,
                                fit: BoxFit.contain,
                                errorBuilder: (_, __, ___) => Container(
                                  height: 200,
                                  color: Colors.grey[800],
                                  child: const Center(
                                    child: Icon(
                                      Icons.image_not_supported,
                                      color: Colors.grey,
                                      size: 48,
                                    ),
                                  ),
                                ),
                              ),
                            ),
                            const SizedBox(height: 16),
                          ],

                          // Question text with animation
                          Text(
                            currentQuestion.text,
                            style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                              color: Colors.white,
                              fontWeight: FontWeight.w600,
                              height: 1.4,
                            ),
                          ).animate().fadeIn(duration: 300.ms).slideX(begin: 0.1, end: 0),

                          const SizedBox(height: 24),

                          // Answer options
                          ...List.generate(
                            currentQuestion.options.length,
                            (index) => Padding(
                              padding: const EdgeInsets.only(bottom: 12),
                              child: _AnswerOption(
                                option: currentQuestion.options[index],
                                isSelected: state.selectedOptionId == currentQuestion.options[index].id,
                                isChecked: state.isAnswerChecked,
                                isCorrect: currentQuestion.options[index].id == currentQuestion.correctAnswer,
                                wasSelected: state.selectedOptionId == currentQuestion.options[index].id,
                                onTap: state.isAnswerChecked
                                    ? null
                                    : () => notifier.selectOption(currentQuestion.options[index].id),
                                index: index,
                              ),
                            ).animate(delay: Duration(milliseconds: 100 * index))
                              .fadeIn(duration: 300.ms)
                              .slideX(begin: 0.2, end: 0),
                          ),
                        ],
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),

          // Combo overlay
          if (state.comboCount >= 2)
            Positioned(
              top: 80,
              right: 20,
              child: ComboOverlay(
                comboCount: state.comboCount,
                bonusXp: state.lastBonusXp,
              ),
            ),

          // Correct answer animation overlay
          if (_showCorrectAnimation)
            Positioned.fill(
              child: IgnorePointer(
                child: _CorrectAnswerAnimation(
                  controller: _correctAnimController,
                ),
              ),
            ),

          // Incorrect answer animation overlay
          if (_showIncorrectAnimation)
            Positioned.fill(
              child: IgnorePointer(
                child: _IncorrectAnswerAnimation(
                  controller: _incorrectAnimController,
                ),
              ),
            ),

          // XP gain floating animation
          if (_showXpGain)
            Positioned(
              top: MediaQuery.of(context).size.height * 0.3,
              left: 0,
              right: 0,
              child: Center(
                child: FloatingXPBubble(value: _animatedXp),
              ),
            ),

          // Feedback overlay at bottom
          if (state.isAnswerChecked)
            Positioned(
              bottom: 0,
              left: 0,
              right: 0,
              child: FeedbackOverlay(
                isCorrect: state.isCurrentCorrect,
                correctAnswer: currentQuestion.correctAnswer,
                onContinue: notifier.nextQuestion,
                xpAwarded: state.xpAwarded,
                baseXp: state.lastBaseXp,
                bonusXp: state.lastBonusXp,
                comboCount: state.comboCount,
              ),
            ),
        ],
      ),
      bottomNavigationBar: state.isAnswerChecked
          ? null
          : SafeArea(
              child: Padding(
                padding: const EdgeInsets.all(20),
                child: PressableScale(
                  onTap: state.selectedOptionId == null ? null : notifier.checkAnswer,
                  child: Container(
                    height: 56,
                    decoration: BoxDecoration(
                      gradient: state.selectedOptionId == null
                          ? null
                          : const LinearGradient(
                              colors: [Color(0xFF2196F3), Color(0xFF1976D2)],
                            ),
                      color: state.selectedOptionId == null ? Colors.grey[800] : null,
                      borderRadius: BorderRadius.circular(16),
                      boxShadow: state.selectedOptionId == null
                          ? null
                          : [
                              BoxShadow(
                                color: Colors.blue.withOpacity(0.4),
                                blurRadius: 12,
                                offset: const Offset(0, 4),
                              ),
                            ],
                    ),
                    alignment: Alignment.center,
                    child: Text(
                      'Comprobar',
                      style: TextStyle(
                        color: state.selectedOptionId == null
                            ? Colors.grey[500]
                            : Colors.white,
                        fontWeight: FontWeight.bold,
                        fontSize: 18,
                      ),
                    ),
                  ),
                ),
              ),
            ),
    );
  }

  Color _getProgressColor(int current, int total) {
    final progress = (current + 1) / total;
    if (progress < 0.33) return Colors.red;
    if (progress < 0.66) return Colors.orange;
    return Colors.green;
  }

  void _showExitConfirmation(BuildContext context) {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: const Color(0xFF1A1A1A),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        title: const Text(
          'Salir del Quiz?',
          style: TextStyle(color: Colors.white),
        ),
        content: const Text(
          'Perderas tu progreso en este quiz. Estas seguro?',
          style: TextStyle(color: Colors.white70),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(),
            child: const Text('Cancelar'),
          ),
          ElevatedButton(
            onPressed: () {
              Navigator.of(ctx).pop();
              context.go(AppRoutes.studyPlan);
            },
            style: ElevatedButton.styleFrom(
              backgroundColor: Colors.red,
              foregroundColor: Colors.white,
            ),
            child: const Text('Salir'),
          ),
        ],
      ),
    );
  }
}

/// Answer option widget
class _AnswerOption extends StatelessWidget {
  final Option option;
  final bool isSelected;
  final bool isChecked;
  final bool isCorrect;
  final bool wasSelected;
  final VoidCallback? onTap;
  final int index;

  const _AnswerOption({
    required this.option,
    required this.isSelected,
    required this.isChecked,
    required this.isCorrect,
    required this.wasSelected,
    required this.onTap,
    required this.index,
  });

  @override
  Widget build(BuildContext context) {
    Color borderColor;
    Color? backgroundColor;
    Color textColor = Colors.white;
    IconData? trailingIcon;

    if (isChecked) {
      if (isCorrect) {
        borderColor = Colors.green;
        backgroundColor = Colors.green.withOpacity(0.2);
        trailingIcon = Icons.check_circle;
      } else if (wasSelected) {
        borderColor = Colors.red;
        backgroundColor = Colors.red.withOpacity(0.2);
        trailingIcon = Icons.cancel;
      } else {
        borderColor = Colors.grey[700]!;
        backgroundColor = null;
      }
    } else {
      borderColor = isSelected ? Colors.blue : Colors.grey[700]!;
      backgroundColor = isSelected ? Colors.blue.withOpacity(0.15) : null;
    }

    final optionLabels = ['A', 'B', 'C', 'D'];
    final label = index < optionLabels.length ? optionLabels[index] : option.id;

    return PressableScale(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: backgroundColor,
          border: Border.all(color: borderColor, width: 2),
          borderRadius: BorderRadius.circular(12),
        ),
        child: Row(
          children: [
            // Option label circle
            Container(
              width: 32,
              height: 32,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: isSelected ? borderColor : Colors.transparent,
                border: Border.all(color: borderColor, width: 2),
              ),
              alignment: Alignment.center,
              child: Text(
                label,
                style: TextStyle(
                  color: isSelected ? Colors.white : borderColor,
                  fontWeight: FontWeight.bold,
                  fontSize: 14,
                ),
              ),
            ),
            const SizedBox(width: 16),

            // Option text
            Expanded(
              child: Text(
                option.text,
                style: TextStyle(
                  color: textColor,
                  fontSize: 16,
                ),
              ),
            ),

            // Trailing icon for checked state
            if (trailingIcon != null)
              Icon(
                trailingIcon,
                color: isCorrect ? Colors.green : Colors.red,
                size: 24,
              ),
          ],
        ),
      ),
    );
  }
}

/// Attempt type badge
class _AttemptTypeBadge extends StatelessWidget {
  final AttemptType type;

  const _AttemptTypeBadge({required this.type});

  @override
  Widget build(BuildContext context) {
    final isInvalid = type == AttemptType.invalidRepeat;
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: isInvalid ? Colors.red.withOpacity(0.1) : Colors.orange.withOpacity(0.1),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: isInvalid ? Colors.red : Colors.orange),
      ),
      child: Text(
        isInvalid ? '0 XP (REPETIDA)' : '5 XP (REPASO)',
        style: TextStyle(
          color: isInvalid ? Colors.red : Colors.orange,
          fontSize: 10,
          fontWeight: FontWeight.bold,
        ),
      ),
    );
  }
}

/// Correct answer animation overlay
class _CorrectAnswerAnimation extends StatelessWidget {
  final AnimationController controller;

  const _CorrectAnswerAnimation({required this.controller});

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: controller,
      builder: (context, child) {
        final scale = Curves.elasticOut.transform(controller.value);
        final opacity = 1.0 - Curves.easeOut.transform(controller.value);

        return Stack(
          children: [
            // Green radial glow
            Center(
              child: Transform.scale(
                scale: scale * 2,
                child: Opacity(
                  opacity: opacity * 0.6,
                  child: Container(
                    width: 200,
                    height: 200,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      gradient: RadialGradient(
                        colors: [
                          Colors.green.withOpacity(0.6),
                          Colors.green.withOpacity(0.0),
                        ],
                      ),
                    ),
                  ),
                ),
              ),
            ),

            // Checkmark
            Center(
              child: Transform.scale(
                scale: scale,
                child: Opacity(
                  opacity: opacity,
                  child: Container(
                    width: 80,
                    height: 80,
                    decoration: BoxDecoration(
                      color: Colors.green,
                      shape: BoxShape.circle,
                      boxShadow: [
                        BoxShadow(
                          color: Colors.green.withOpacity(0.5),
                          blurRadius: 20,
                          spreadRadius: 5,
                        ),
                      ],
                    ),
                    child: const Icon(
                      Icons.check,
                      color: Colors.white,
                      size: 48,
                    ),
                  ),
                ),
              ),
            ),
          ],
        );
      },
    );
  }
}

/// Incorrect answer animation overlay
class _IncorrectAnswerAnimation extends StatelessWidget {
  final AnimationController controller;

  const _IncorrectAnswerAnimation({required this.controller});

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: controller,
      builder: (context, child) {
        final shakeOffset = sin(controller.value * pi * 6) * 5 * (1 - controller.value);
        final opacity = 1.0 - Curves.easeOut.transform(controller.value);

        return Stack(
          children: [
            // Red radial pulse
            Center(
              child: Opacity(
                opacity: opacity * 0.5,
                child: Container(
                  width: 150,
                  height: 150,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    gradient: RadialGradient(
                      colors: [
                        Colors.red.withOpacity(0.5),
                        Colors.red.withOpacity(0.0),
                      ],
                    ),
                  ),
                ),
              ),
            ),

            // X mark with shake
            Center(
              child: Transform.translate(
                offset: Offset(shakeOffset, 0),
                child: Opacity(
                  opacity: opacity,
                  child: Container(
                    width: 80,
                    height: 80,
                    decoration: BoxDecoration(
                      color: Colors.red,
                      shape: BoxShape.circle,
                      boxShadow: [
                        BoxShadow(
                          color: Colors.red.withOpacity(0.4),
                          blurRadius: 15,
                          spreadRadius: 3,
                        ),
                      ],
                    ),
                    child: const Icon(
                      Icons.close,
                      color: Colors.white,
                      size: 48,
                    ),
                  ),
                ),
              ),
            ),
          ],
        );
      },
    );
  }
}

/// Quiz results screen
class _QuizResultsScreen extends StatelessWidget {
  final UnitQuizState state;
  final VoidCallback onRetry;
  final VoidCallback onReturn;

  const _QuizResultsScreen({
    required this.state,
    required this.onRetry,
    required this.onReturn,
  });

  @override
  Widget build(BuildContext context) {
    final isPerfect = state.accuracy == 100;
    final isGood = state.accuracy >= 70;

    return Scaffold(
      backgroundColor: const Color(0xFF0A0A0A),
      body: SafeArea(
        child: Column(
          children: [
            const Spacer(flex: 1),

            // Trophy/Icon
            _ResultIcon(accuracy: state.accuracy)
                .animate()
                .scale(
                  begin: const Offset(0.5, 0.5),
                  end: const Offset(1.0, 1.0),
                  duration: 500.ms,
                  curve: Curves.elasticOut,
                )
                .shimmer(delay: 500.ms, duration: 1000.ms),

            const SizedBox(height: 24),

            // Title
            Text(
              isPerfect
                  ? 'PERFECTO!'
                  : isGood
                      ? 'BIEN HECHO!'
                      : 'SIGUE PRACTICANDO',
              style: TextStyle(
                fontSize: 28,
                fontWeight: FontWeight.w900,
                color: isPerfect
                    ? Colors.amber
                    : isGood
                        ? Colors.green
                        : Colors.orange,
                letterSpacing: 2,
              ),
            ).animate().fadeIn(delay: 200.ms).slideY(begin: 0.3, end: 0),

            const SizedBox(height: 8),

            Text(
              state.unitName,
              style: TextStyle(
                fontSize: 18,
                color: Colors.grey[400],
              ),
            ).animate().fadeIn(delay: 300.ms),

            const SizedBox(height: 32),

            // Score
            Container(
              margin: const EdgeInsets.symmetric(horizontal: 32),
              padding: const EdgeInsets.all(24),
              decoration: BoxDecoration(
                color: Colors.white.withOpacity(0.05),
                borderRadius: BorderRadius.circular(20),
                border: Border.all(color: Colors.white.withOpacity(0.1)),
              ),
              child: Column(
                children: [
                  // Score row
                  Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Text(
                        '${state.correctAnswers}',
                        style: const TextStyle(
                          fontSize: 48,
                          fontWeight: FontWeight.bold,
                          color: Colors.green,
                        ),
                      ),
                      Text(
                        ' / ${state.questions.length}',
                        style: TextStyle(
                          fontSize: 48,
                          fontWeight: FontWeight.bold,
                          color: Colors.grey[400],
                        ),
                      ),
                    ],
                  ),

                  const SizedBox(height: 8),

                  Text(
                    'Respuestas correctas',
                    style: TextStyle(
                      color: Colors.grey[500],
                      fontSize: 14,
                    ),
                  ),

                  const SizedBox(height: 24),

                  // Stars
                  Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: List.generate(3, (index) {
                      final isEarned = index < state.stars;
                      return Padding(
                        padding: const EdgeInsets.symmetric(horizontal: 4),
                        child: Icon(
                          isEarned ? Icons.star : Icons.star_border,
                          color: isEarned ? Colors.amber : Colors.grey[600],
                          size: index == 1 ? 48 : 40,
                        ),
                      ).animate(delay: Duration(milliseconds: 600 + (index * 150)))
                        .scale(begin: const Offset(0, 0), duration: 300.ms, curve: Curves.elasticOut)
                        .rotate(begin: 0.2, end: 0);
                    }),
                  ),

                  const SizedBox(height: 24),

                  // XP earned
                  XPCounter(
                    targetValue: state.totalXp,
                    delay: const Duration(milliseconds: 800),
                  ),

                  const SizedBox(height: 16),

                  // Stats row
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                    children: [
                      _StatItem(
                        icon: Icons.percent,
                        value: '${state.accuracy}%',
                        label: 'Precision',
                      ),
                      _StatItem(
                        icon: Icons.local_fire_department,
                        value: 'x${state.maxCombo}',
                        label: 'Max Combo',
                      ),
                      _StatItem(
                        icon: Icons.trending_up,
                        value: '+${(state.masteryImprovement * 100).toStringAsFixed(0)}%',
                        label: 'Dominio',
                      ),
                    ],
                  ),
                ],
              ),
            ).animate().fadeIn(delay: 400.ms).slideY(begin: 0.2, end: 0),

            const Spacer(flex: 1),

            // Buttons
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 32),
              child: Column(
                children: [
                  // Retry button (if not perfect)
                  if (state.accuracy < 100)
                    PressableScale(
                      onTap: onRetry,
                      child: Container(
                        height: 56,
                        width: double.infinity,
                        decoration: BoxDecoration(
                          gradient: const LinearGradient(
                            colors: [Color(0xFFFF9800), Color(0xFFF57C00)],
                          ),
                          borderRadius: BorderRadius.circular(16),
                          boxShadow: [
                            BoxShadow(
                              color: Colors.orange.withOpacity(0.4),
                              blurRadius: 12,
                              offset: const Offset(0, 4),
                            ),
                          ],
                        ),
                        alignment: Alignment.center,
                        child: const Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Icon(Icons.replay, color: Colors.white),
                            SizedBox(width: 8),
                            Text(
                              'Reintentar',
                              style: TextStyle(
                                color: Colors.white,
                                fontWeight: FontWeight.bold,
                                fontSize: 18,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ).animate().fadeIn(delay: 1000.ms),

                  const SizedBox(height: 12),

                  // Return button
                  PressableScale(
                    onTap: onReturn,
                    child: Container(
                      height: 56,
                      width: double.infinity,
                      decoration: BoxDecoration(
                        gradient: const LinearGradient(
                          colors: [Color(0xFF4CAF50), Color(0xFF388E3C)],
                        ),
                        borderRadius: BorderRadius.circular(16),
                        boxShadow: [
                          BoxShadow(
                            color: Colors.green.withOpacity(0.4),
                            blurRadius: 12,
                            offset: const Offset(0, 4),
                          ),
                        ],
                      ),
                      alignment: Alignment.center,
                      child: const Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Icon(Icons.check_circle, color: Colors.white),
                          SizedBox(width: 8),
                          Text(
                            'Volver al Plan',
                            style: TextStyle(
                              color: Colors.white,
                              fontWeight: FontWeight.bold,
                              fontSize: 18,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ).animate().fadeIn(delay: 1100.ms),
                ],
              ),
            ),

            const SizedBox(height: 32),
          ],
        ),
      ),
    );
  }
}

/// Result icon based on accuracy
class _ResultIcon extends StatelessWidget {
  final int accuracy;

  const _ResultIcon({required this.accuracy});

  @override
  Widget build(BuildContext context) {
    IconData icon;
    Color color;
    List<Color> gradientColors;

    if (accuracy == 100) {
      icon = Icons.emoji_events;
      color = Colors.amber;
      gradientColors = [Colors.amber.shade300, Colors.amber.shade700];
    } else if (accuracy >= 70) {
      icon = Icons.thumb_up;
      color = Colors.green;
      gradientColors = [Colors.green.shade300, Colors.green.shade700];
    } else {
      icon = Icons.lightbulb;
      color = Colors.orange;
      gradientColors = [Colors.orange.shade300, Colors.orange.shade700];
    }

    return Container(
      width: 120,
      height: 120,
      decoration: BoxDecoration(
        shape: BoxShape.circle,
        gradient: RadialGradient(
          colors: [
            color.withOpacity(0.3),
            color.withOpacity(0.1),
            Colors.transparent,
          ],
        ),
      ),
      child: Center(
        child: Container(
          width: 80,
          height: 80,
          decoration: BoxDecoration(
            shape: BoxShape.circle,
            gradient: LinearGradient(
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
              colors: gradientColors,
            ),
            boxShadow: [
              BoxShadow(
                color: color.withOpacity(0.5),
                blurRadius: 20,
                spreadRadius: 5,
              ),
            ],
          ),
          child: Icon(icon, color: Colors.white, size: 40),
        ),
      ),
    );
  }
}

/// Stat item widget
class _StatItem extends StatelessWidget {
  final IconData icon;
  final String value;
  final String label;

  const _StatItem({
    required this.icon,
    required this.value,
    required this.label,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Icon(icon, color: Colors.white70, size: 20),
        const SizedBox(height: 4),
        Text(
          value,
          style: const TextStyle(
            color: Colors.white,
            fontWeight: FontWeight.bold,
            fontSize: 16,
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
