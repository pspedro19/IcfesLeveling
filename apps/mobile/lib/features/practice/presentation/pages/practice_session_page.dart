import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../providers/practice_provider.dart';
import '../../domain/entities/question.dart';

import '../widgets/combo_overlay.dart';
import '../widgets/session_error_widget.dart';
import '../../../../shared/widgets/pressable_scale.dart';
import '../../../../shared/widgets/feedback_overlay.dart';
import '../../../../shared/widgets/animated_feedback/correct_answer_overlay.dart';
import '../../../../shared/widgets/animated_feedback/incorrect_answer_overlay.dart';
import '../../../../core/constants/app_strings.dart';
import '../../../../core/services/dopamine_engine.dart';
import '../../../../core/services/psychological_triggers_provider.dart';
import '../../../../shared/widgets/psychological/loss_aversion_alerts.dart';

class PracticeSessionPage extends ConsumerStatefulWidget {
  final String? subjectId;
  const PracticeSessionPage({super.key, this.subjectId});

  @override
  ConsumerState<PracticeSessionPage> createState() => _PracticeSessionPageState();
}

class _PracticeSessionPageState extends ConsumerState<PracticeSessionPage> {
  bool _showDopamineOverlay = false;
  bool _lastAnswerCorrect = false;
  bool _showVariableReward = false;

  @override
  void initState() {
    super.initState();
    // Initialize DopamineEngine
    DopamineEngine().initialize();

    // Use post-frame callback to safely read the provider
    WidgetsBinding.instance.addPostFrameCallback((_) {
      ref.read(practiceProvider.notifier).startSession(subjectId: widget.subjectId);
    });
  }

  /// Trigger dopamine feedback when answer is checked
  void _triggerDopamineFeedback(bool isCorrect, int xpEarned, int combo) {
    setState(() {
      _showDopamineOverlay = true;
      _lastAnswerCorrect = isCorrect;
    });

    if (isCorrect) {
      DopamineEngine.showCorrectAnswerOverlay(
        context,
        xpEarned: xpEarned,
        combo: combo,
      );

      // Check for variable reward bonus
      final reward = ref.read(variableRewardProvider.notifier).getReward('answer_correct', xpEarned);
      if (reward.hasBonus) {
        _showVariableRewardPopup(reward);
      }
    } else {
      DopamineEngine.showIncorrectAnswerOverlay(context);
    }

    // Auto-hide overlay after animation completes
    Future.delayed(Duration(milliseconds: isCorrect ? 600 : 800), () {
      if (mounted) {
        setState(() {
          _showDopamineOverlay = false;
        });
      }
    });
  }

  /// Show variable reward popup when bonus is triggered
  void _showVariableRewardPopup(dynamic reward) {
    setState(() {
      _showVariableReward = true;
    });

    // Auto-hide after 2 seconds
    Future.delayed(const Duration(milliseconds: 2500), () {
      if (mounted) {
        setState(() {
          _showVariableReward = false;
        });
        ref.read(variableRewardProvider.notifier).clearReward();
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(practiceProvider);
    final notifier = ref.read(practiceProvider.notifier);
    final currentQuestion = state.currentQuestion;

    // Listen for answer check and trigger dopamine feedback
    ref.listen<PracticeState>(practiceProvider, (previous, next) {
      if (previous != null &&
          !previous.isAnswerChecked &&
          next.isAnswerChecked) {
        // Answer was just checked - trigger dopamine feedback
        _triggerDopamineFeedback(
          next.isCurrentCorrect,
          next.xpAwarded,
          next.comboCount,
        );
      }
    });

    if (state.isLoading) {
      return const Scaffold(body: Center(child: CircularProgressIndicator()));
    }

    if (state.error != null) {
      return Scaffold(
        body: SessionErrorWidget(
          error: state.error!,
          onRetry: () => notifier.startSession(subjectId: widget.subjectId),
        ),
      );
    }

    if (state.isFinished) {
      return Scaffold(body: Center(child: Text(AppStrings.sessionFinished)));
    }

    if (currentQuestion == null) {
      return Scaffold(body: Center(child: Text(AppStrings.loadingQuestions)));
    }

    return Scaffold(
      appBar: AppBar(
        leading: IconButton(
          icon: const Icon(Icons.close),
          tooltip: AppStrings.close,
          onPressed: () => Navigator.of(context).pop(),
        ),
        title: LinearProgressIndicator(
          value: (state.currentIndex + 1) / state.questions.length,
          backgroundColor: Colors.grey[800],
          valueColor: const AlwaysStoppedAnimation<Color>(Colors.green),
        ),
      ),
      body: Stack(
        children: [
          Padding(
            padding: const EdgeInsets.all(20),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  AppStrings.questionProgress
                      .replaceFirst('{current}', '${state.currentIndex + 1}')
                      .replaceFirst('{total}', '${state.questions.length}'),
                  style: Theme.of(context).textTheme.bodySmall,
                ),
                const SizedBox(height: 16),
                Row(
                  children: [
                    Expanded(
                      child: Text(
                        currentQuestion.text,
                        style: Theme.of(context).textTheme.headlineMedium,
                      ),
                    ),
                    if (currentQuestion.attemptType != AttemptType.newQuestion)
                      _AntiGamingBadge(type: currentQuestion.attemptType),
                  ],
                ),
                const SizedBox(height: 24),
                Expanded(
                  child: ListView.builder(
                    itemCount: currentQuestion.options.length,
                    itemBuilder: (context, index) {
                      final option = currentQuestion.options[index];
                      final isSelected = state.selectedOptionId == option.id;
                      
                      return Padding(
                        key: ValueKey(option.id),
                        padding: const EdgeInsets.only(bottom: 12),
                        child: PressableScale(
                          onTap: state.isAnswerChecked ? null : () => notifier.selectOption(option.id),
                          child: Container(
                            padding: const EdgeInsets.all(16),
                            decoration: BoxDecoration(
                              border: Border.all(
                                color: isSelected ? Colors.blue : Colors.grey[700]!,
                                width: 2,
                              ),
                              borderRadius: BorderRadius.circular(12),
                              color: isSelected ? Colors.blue.withOpacity(0.1) : null,
                            ),
                            child: Row(
                              children: [
                                  CircleAvatar(
                                    radius: 12,
                                    backgroundColor: isSelected ? Colors.blue : Colors.grey[700],
                                    child: Semantics(
                                      label: 'Opción ${option.id}',
                                      child: Text(option.id, style: const TextStyle(fontSize: 12, color: Colors.white)),
                                    ),
                                  ),
                                const SizedBox(width: 16),
                                Expanded(child: Text(option.text)),
                              ],
                            ),
                          ),
                        ),
                      );
                    },
                  ),
                ),
              ],
            ),
          ),
          
          // Combo Overlay with bonus XP display
          if (state.comboCount >= 2)
            Positioned(
              top: 20,
              right: 20,
              child: ComboOverlay(
                comboCount: state.comboCount,
                bonusXp: state.lastBonusXp,
              ),
            ),

          // Feedback Overlay with XP breakdown
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

          // Dopamine Engine Overlays
          if (_showDopamineOverlay && _lastAnswerCorrect)
            Positioned.fill(
              child: IgnorePointer(
                child: CorrectAnswerOverlay(
                  xpEarned: state.xpAwarded,
                  combo: state.comboCount,
                ),
              ),
            ),
          if (_showDopamineOverlay && !_lastAnswerCorrect)
            Positioned.fill(
              child: IgnorePointer(
                child: IncorrectAnswerOverlay(
                  correctAnswer: currentQuestion.correctAnswer,
                  showHeartBreak: true,
                ),
              ),
            ),

          // Variable Reward Popup (psychological trigger)
          if (_showVariableReward)
            Positioned.fill(
              child: GestureDetector(
                onTap: () {
                  setState(() => _showVariableReward = false);
                  ref.read(variableRewardProvider.notifier).clearReward();
                },
                child: Container(
                  color: Colors.black54,
                  child: Center(
                    child: Consumer(
                      builder: (context, ref, _) {
                        final reward = ref.watch(variableRewardProvider);
                        if (reward == null) return const SizedBox.shrink();
                        return VariableRewardPopup(
                          reward: reward,
                          onDismiss: () {
                            setState(() => _showVariableReward = false);
                            ref.read(variableRewardProvider.notifier).clearReward();
                          },
                        );
                      },
                    ),
                  ),
                ),
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
                      color: state.selectedOptionId == null ? Colors.grey : Colors.blue,
                      borderRadius: BorderRadius.circular(16),
                    ),
                    alignment: Alignment.center,
                    child: Text(
                      AppStrings.check,
                      style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 18),
                    ),
                  ),
                ),
              ),
            ),
    );
  }
}

class _AntiGamingBadge extends StatelessWidget {
  final AttemptType type;
  const _AntiGamingBadge({required this.type});

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
        isInvalid ? "0 XP (REPETIDA)" : "5 XP (REPASO)",
        style: TextStyle(
          color: isInvalid ? Colors.red : Colors.orange,
          fontSize: 10,
          fontWeight: FontWeight.bold,
        ),
      ),
    );
  }
}
