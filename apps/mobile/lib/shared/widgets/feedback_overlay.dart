import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';

import '../../core/utils/app_haptics.dart';
import '../../core/constants/app_strings.dart';
import '../../core/services/combo_service.dart';
import 'lottie_overlay.dart';
import 'pressable_scale.dart';

/// A floating overlay widget displayed after a user answers a question,
/// providing visual feedback on whether the answer was correct or incorrect.
///
/// It animates from the bottom of the screen and includes XP/combo feedback
/// for correct answers, and displays the correct answer for incorrect ones.
///
/// [isCorrect] True if the user's answer was correct, false otherwise.
/// [correctAnswer] The text of the correct answer, displayed if `isCorrect` is false.
/// [onContinue] Callback function to be executed when the user taps the "Continue" button.
/// [xpAwarded] The total amount of experience points awarded for the answer (base + bonus).
/// [baseXp] The base XP earned for the answer.
/// [bonusXp] The combo bonus XP earned.
/// [comboCount] The current combo streak count, influencing visual feedback.
class FeedbackOverlay extends StatefulWidget {
  final bool isCorrect;
  final String correctAnswer;
  final VoidCallback onContinue;

  final int xpAwarded;
  final int baseXp;
  final int bonusXp;
  final int comboCount;

  const FeedbackOverlay({
    super.key,
    required this.isCorrect,
    required this.correctAnswer,
    required this.onContinue,
    this.xpAwarded = 0,
    this.baseXp = 0,
    this.bonusXp = 0,
    this.comboCount = 0,
  });

  @override
  State<FeedbackOverlay> createState() => _FeedbackOverlayState();
}

class _FeedbackOverlayState extends State<FeedbackOverlay> with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  late Animation<Offset> _offsetAnimation;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      duration: const Duration(milliseconds: 400),
      vsync: this,
    );
    _offsetAnimation = Tween<Offset>(
      begin: const Offset(0, 1),
      end: Offset.zero,
    ).animate(CurvedAnimation(parent: _controller, curve: Curves.elasticOut));

    _controller.forward();
    _triggerFeedback();
  }

  void _triggerFeedback() {
    if (widget.isCorrect) {
      // Note: Haptics and sounds are now handled by DopamineEngine
      // This is kept as a fallback for when DopamineEngine is not active
      AppHaptics.successPattern();

      // Combo haptic for high combos
      if (widget.comboCount >= 3) {
        Future.delayed(const Duration(milliseconds: 100), () {
          AppHaptics.comboPattern(widget.comboCount);
        });
      }
    } else {
      AppHaptics.errorPattern();
      // Heart lost haptic
      Future.delayed(const Duration(milliseconds: 200), () {
        AppHaptics.heartLostPattern();
      });
    }
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final color = widget.isCorrect ? Colors.green : Colors.red;
    
    return SlideTransition(
      position: _offsetAnimation,
      child: Container(
        padding: const EdgeInsets.all(24),
        decoration: BoxDecoration(
          color: color.withOpacity(0.95),
          borderRadius: const BorderRadius.vertical(top: Radius.circular(24)),
          boxShadow: [
            BoxShadow(
              color: color.withOpacity(0.3),
              blurRadius: 20,
              spreadRadius: 5,
            )
          ],
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Row(
              children: [
                SizedBox(
                  width: 48,
                  height: 48,
                  child: Stack(
                    alignment: Alignment.center,
                    children: [
                      // Lottie animation behind the icon
                      Lottie.asset(
                        widget.isCorrect
                            ? LottieAssets.correctCheck
                            : LottieAssets.wrongX,
                        width: 48,
                        height: 48,
                        repeat: false,
                        errorBuilder: (_, __, ___) => const SizedBox.shrink(),
                      ),
                      // Icon fallback
                      Icon(
                        widget.isCorrect ? Icons.check_circle : Icons.cancel,
                        color: Colors.white,
                        size: 32,
                        semanticLabel: widget.isCorrect ? 'Correcto' : 'Incorrecto',
                      ),
                    ],
                  ),
                ),
                const SizedBox(width: 16),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        widget.isCorrect
                            ? (widget.comboCount >= 2
                                ? ComboService.getComboDisplay(widget.comboCount).text
                                : AppStrings.excellent)
                            : AppStrings.incorrect,
                        style: const TextStyle(
                          color: Colors.white,
                          fontSize: 20,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      if (widget.isCorrect && widget.comboCount >= 2)
                        Text(
                          'COMBO x${widget.comboCount}',
                          style: TextStyle(
                            color: Colors.white.withOpacity(0.8),
                            fontSize: 14,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                    ],
                  ),
                ),
              ],
            ),
            if (widget.isCorrect) ...[
              const SizedBox(height: 12),
              _XpBreakdownRow(
                baseXp: widget.baseXp,
                bonusXp: widget.bonusXp,
                totalXp: widget.xpAwarded,
                comboCount: widget.comboCount,
              ),
            ],
            if (!widget.isCorrect) ...[
              const SizedBox(height: 8),
              Text(
                AppStrings.correctWas.replaceFirst('{answer}', widget.correctAnswer),
                style: const TextStyle(color: Colors.white, fontSize: 16),
              ),
            ],
            const SizedBox(height: 24),
            PressableScale(
              onTap: widget.onContinue,
              child: Container(
                height: 56,
                width: double.infinity,
                alignment: Alignment.center,
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(16),
                ),
                child: Text(
                  AppStrings.continueText,
                  style: TextStyle(
                    color: color,
                    fontWeight: FontWeight.bold,
                    fontSize: 18,
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
/// A row widget showing XP breakdown with base XP and combo bonus
class _XpBreakdownRow extends StatelessWidget {
  final int baseXp;
  final int bonusXp;
  final int totalXp;
  final int comboCount;

  const _XpBreakdownRow({
    required this.baseXp,
    required this.bonusXp,
    required this.totalXp,
    required this.comboCount,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
      decoration: BoxDecoration(
        color: Colors.black.withOpacity(0.2),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          // Total XP
          Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Icon(Icons.star, color: Colors.amber, size: 24),
              const SizedBox(width: 6),
              Text(
                '+$totalXp XP',
                style: const TextStyle(
                  color: Colors.amber,
                  fontSize: 20,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ],
          ).animate()
            .scale(begin: const Offset(0.5, 0.5), duration: 300.ms, curve: Curves.elasticOut),

          // Breakdown
          if (bonusXp > 0) ...[
            const SizedBox(width: 16),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
              decoration: BoxDecoration(
                color: Colors.orange.withOpacity(0.3),
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: Colors.orange.withOpacity(0.5)),
              ),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Text(
                    '$baseXp',
                    style: const TextStyle(
                      color: Colors.white70,
                      fontSize: 12,
                    ),
                  ),
                  Text(
                    ' + $bonusXp',
                    style: const TextStyle(
                      color: Colors.orange,
                      fontSize: 12,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const Text(
                    ' bonus',
                    style: TextStyle(
                      color: Colors.orange,
                      fontSize: 10,
                    ),
                  ),
                ],
              ),
            ).animate()
              .fadeIn(delay: 200.ms, duration: 300.ms)
              .slideX(begin: 0.2, end: 0),
          ],
        ],
      ),
    );
  }
}

