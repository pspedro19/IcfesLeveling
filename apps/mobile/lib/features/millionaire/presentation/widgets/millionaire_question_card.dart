import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';

import '../../../../core/config/app_theme.dart';
import '../../../practice/domain/entities/question.dart';
import '../../data/models/millionaire_models.dart';

class MillionaireQuestionCard extends StatelessWidget {
  final MillionaireQuestion question;
  final String? selectedAnswer;
  final bool isAnswerRevealed;
  final bool isEnabled;
  final Function(String) onOptionSelected;

  const MillionaireQuestionCard({
    super.key,
    required this.question,
    this.selectedAnswer,
    this.isAnswerRevealed = false,
    this.isEnabled = true,
    required this.onOptionSelected,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        // Question number and difficulty
        _buildHeader(context),
        const SizedBox(height: 16),

        // Question text
        _buildQuestionText(context),
        const SizedBox(height: 8),

        // AI Hint if available
        if (question.aiHint != null) _buildAIHint(context),

        const SizedBox(height: 24),

        // Options
        ...question.question.options.map(
          (option) => _buildOptionButton(context, option),
        ),
      ],
    );
  }

  Widget _buildHeader(BuildContext context) {
    final tier = question.prizeTier;
    final difficultyLabel = _getDifficultyLabel(tier.difficulty);
    final difficultyColor = _getDifficultyColor(tier.difficulty);

    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
          decoration: BoxDecoration(
            color: AppTheme.primaryPurple.withOpacity(0.2),
            borderRadius: BorderRadius.circular(20),
            border: Border.all(
              color: AppTheme.primaryPurple.withOpacity(0.5),
            ),
          ),
          child: Text(
            'Pregunta ${question.questionNumber}/15',
            style: const TextStyle(
              color: AppTheme.textPrimary,
              fontWeight: FontWeight.bold,
              fontSize: 14,
            ),
          ),
        ),
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
          decoration: BoxDecoration(
            color: difficultyColor.withOpacity(0.2),
            borderRadius: BorderRadius.circular(20),
            border: Border.all(color: difficultyColor.withOpacity(0.5)),
          ),
          child: Text(
            difficultyLabel,
            style: TextStyle(
              color: difficultyColor,
              fontWeight: FontWeight.w600,
              fontSize: 12,
            ),
          ),
        ),
      ],
    ).animate().fadeIn(duration: 300.ms);
  }

  String _getDifficultyLabel(MillionaireDifficulty difficulty) {
    switch (difficulty) {
      case MillionaireDifficulty.easy:
        return 'Facil';
      case MillionaireDifficulty.easyMedium:
        return 'Facil-Media';
      case MillionaireDifficulty.medium:
        return 'Media';
      case MillionaireDifficulty.mediumHard:
        return 'Media-Dificil';
      case MillionaireDifficulty.hard:
        return 'Dificil';
    }
  }

  Color _getDifficultyColor(MillionaireDifficulty difficulty) {
    switch (difficulty) {
      case MillionaireDifficulty.easy:
        return AppTheme.successGreen;
      case MillionaireDifficulty.easyMedium:
        return AppTheme.accentCyan;
      case MillionaireDifficulty.medium:
        return AppTheme.warningOrange;
      case MillionaireDifficulty.mediumHard:
        return Colors.deepOrange;
      case MillionaireDifficulty.hard:
        return AppTheme.dangerRed;
    }
  }

  Widget _buildQuestionText(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [
            AppTheme.bgCard,
            AppTheme.bgElevated.withOpacity(0.8),
          ],
        ),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: AppTheme.primaryPurple.withOpacity(0.3),
          width: 2,
        ),
        boxShadow: [
          BoxShadow(
            color: AppTheme.primaryPurple.withOpacity(0.1),
            blurRadius: 20,
            spreadRadius: 2,
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            question.question.text,
            style: const TextStyle(
              color: AppTheme.textPrimary,
              fontSize: 18,
              fontWeight: FontWeight.w500,
              height: 1.5,
            ),
          ),
          if (question.question.imageUrl != null) ...[
            const SizedBox(height: 16),
            ClipRRect(
              borderRadius: BorderRadius.circular(12),
              child: Image.network(
                question.question.imageUrl!,
                fit: BoxFit.contain,
                errorBuilder: (_, __, ___) => Container(
                  height: 150,
                  decoration: BoxDecoration(
                    color: AppTheme.bgElevated,
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: const Center(
                    child: Icon(
                      Icons.image_not_supported,
                      color: AppTheme.textMuted,
                      size: 48,
                    ),
                  ),
                ),
              ),
            ),
          ],
        ],
      ),
    ).animate().fadeIn(duration: 400.ms).slideY(begin: -0.1, end: 0);
  }

  Widget _buildAIHint(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(top: 12),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [
            AppTheme.secondaryGold.withOpacity(0.1),
            AppTheme.secondaryGold.withOpacity(0.05),
          ],
        ),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: AppTheme.secondaryGold.withOpacity(0.3),
        ),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Icon(
            Icons.lightbulb_rounded,
            color: AppTheme.secondaryGold,
            size: 24,
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'Pista de la IA:',
                  style: TextStyle(
                    color: AppTheme.secondaryGold,
                    fontWeight: FontWeight.bold,
                    fontSize: 12,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  question.aiHint!,
                  style: const TextStyle(
                    color: AppTheme.textPrimary,
                    fontSize: 14,
                    fontStyle: FontStyle.italic,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    ).animate().fadeIn(duration: 300.ms).scale(begin: const Offset(0.95, 0.95));
  }

  Widget _buildOptionButton(BuildContext context, Option option) {
    final isEliminated = question.eliminatedOptions.contains(option.id);
    final isSelected = selectedAnswer == option.id;
    final isCorrect = option.id == question.question.correctAnswer;

    // Determine button state and colors
    Color bgColor;
    Color borderColor;
    Color textColor;

    if (isEliminated) {
      bgColor = Colors.grey.shade900.withOpacity(0.3);
      borderColor = Colors.grey.shade700;
      textColor = Colors.grey.shade600;
    } else if (isAnswerRevealed) {
      if (isCorrect) {
        bgColor = AppTheme.successGreen.withOpacity(0.3);
        borderColor = AppTheme.successGreen;
        textColor = AppTheme.successGreen;
      } else if (isSelected) {
        bgColor = AppTheme.dangerRed.withOpacity(0.3);
        borderColor = AppTheme.dangerRed;
        textColor = AppTheme.dangerRed;
      } else {
        bgColor = AppTheme.bgElevated;
        borderColor = AppTheme.bgElevated;
        textColor = AppTheme.textSecondary;
      }
    } else if (isSelected) {
      bgColor = AppTheme.primaryPurple.withOpacity(0.3);
      borderColor = AppTheme.primaryPurple;
      textColor = AppTheme.textPrimary;
    } else {
      bgColor = AppTheme.bgCard;
      borderColor = AppTheme.bgElevated;
      textColor = AppTheme.textPrimary;
    }

    Widget button = Container(
      margin: const EdgeInsets.only(bottom: 12),
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          onTap: isEnabled && !isEliminated && !isAnswerRevealed
              ? () => onOptionSelected(option.id)
              : null,
          borderRadius: BorderRadius.circular(12),
          child: AnimatedContainer(
            duration: const Duration(milliseconds: 300),
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
            decoration: BoxDecoration(
              color: bgColor,
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: borderColor, width: 2),
              boxShadow: isSelected && !isAnswerRevealed
                  ? [
                      BoxShadow(
                        color: AppTheme.primaryPurple.withOpacity(0.3),
                        blurRadius: 12,
                        spreadRadius: 0,
                      ),
                    ]
                  : null,
            ),
            child: Row(
              children: [
                // Option letter
                Container(
                  width: 36,
                  height: 36,
                  decoration: BoxDecoration(
                    color: isEliminated
                        ? Colors.grey.shade800
                        : isAnswerRevealed && isCorrect
                            ? AppTheme.successGreen
                            : isAnswerRevealed && isSelected
                                ? AppTheme.dangerRed
                                : isSelected
                                    ? AppTheme.primaryPurple
                                    : AppTheme.bgElevated,
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Center(
                    child: isAnswerRevealed && isCorrect
                        ? const Icon(
                            Icons.check,
                            color: Colors.white,
                            size: 20,
                          )
                        : isAnswerRevealed && isSelected && !isCorrect
                            ? const Icon(
                                Icons.close,
                                color: Colors.white,
                                size: 20,
                              )
                            : Text(
                                option.id,
                                style: TextStyle(
                                  color: isEliminated
                                      ? Colors.grey.shade600
                                      : Colors.white,
                                  fontWeight: FontWeight.bold,
                                  fontSize: 16,
                                ),
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
                      fontSize: 15,
                      fontWeight: isSelected ? FontWeight.w600 : FontWeight.normal,
                      decoration: isEliminated
                          ? TextDecoration.lineThrough
                          : TextDecoration.none,
                    ),
                  ),
                ),

                // Result icon
                if (isAnswerRevealed && isCorrect)
                  const Icon(
                    Icons.emoji_events,
                    color: AppTheme.secondaryGold,
                    size: 24,
                  )
                      .animate()
                      .scale(begin: const Offset(0, 0), duration: 300.ms)
                      .shake(hz: 2, duration: 500.ms),
              ],
            ),
          ),
        ),
      ),
    );

    // Add entry animation with staggered delay
    final optionIndex = question.question.options.indexOf(option);
    return button
        .animate(delay: Duration(milliseconds: 100 * optionIndex))
        .fadeIn(duration: 300.ms)
        .slideX(begin: 0.1, end: 0);
  }
}
