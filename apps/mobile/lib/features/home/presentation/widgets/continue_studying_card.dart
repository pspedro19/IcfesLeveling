import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/config/app_theme.dart';
import '../providers/study_plan_provider.dart';

class ContinueStudyingCard extends ConsumerWidget {
  const ContinueStudyingCard({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(studyPlanProvider);

    // Don't show anything while loading
    if (state.isLoading) {
      return const SizedBox.shrink();
    }

    // Don't show if no plan or error
    if (!state.hasPlan || state.plan == null) {
      return const SizedBox.shrink();
    }

    final plan = state.plan!;
    final currentUnit = plan.currentUnit;
    final progress = plan.progressPercentage / 100;
    final subjectColor = Color(plan.subjectColor);

    // If plan is 100% complete, show completion message instead
    if (plan.progressPercentage >= 100) {
      return Card(
        elevation: 2,
        color: AppTheme.successGreen.withOpacity(0.15),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(16),
          side: BorderSide(color: AppTheme.successGreen.withOpacity(0.3)),
        ),
        child: Padding(
          padding: const EdgeInsets.all(16.0),
          child: Row(
            children: [
              Container(
                padding: const EdgeInsets.all(10),
                decoration: BoxDecoration(
                  color: AppTheme.successGreen.withOpacity(0.2),
                  shape: BoxShape.circle,
                ),
                child: const Icon(
                  Icons.emoji_events,
                  color: AppTheme.successGreen,
                  size: 28,
                ),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Plan Completado!',
                      style: Theme.of(context).textTheme.titleMedium?.copyWith(
                            color: AppTheme.successGreen,
                            fontWeight: FontWeight.w700,
                          ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      'Has completado ${plan.subject}. Sigue asi!',
                      style: Theme.of(context).textTheme.bodySmall?.copyWith(
                            color: Colors.white60,
                          ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      );
    }

    return Card(
      elevation: 2,
      color: AppTheme.bgCard.withOpacity(0.8),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
        side: BorderSide(color: subjectColor.withOpacity(0.2)),
      ),
      child: InkWell(
        onTap: () => context.go('/study-plan'),
        borderRadius: BorderRadius.circular(16),
        child: Padding(
          padding: const EdgeInsets.all(16.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  // Subject icon
                  Container(
                    padding: const EdgeInsets.all(8),
                    decoration: BoxDecoration(
                      color: subjectColor.withOpacity(0.15),
                      borderRadius: BorderRadius.circular(10),
                    ),
                    child: Icon(
                      _getSubjectIcon(plan.subject),
                      color: subjectColor,
                      size: 20,
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          'Continuar Estudiando',
                          style: Theme.of(context).textTheme.titleMedium?.copyWith(
                                fontWeight: FontWeight.w700,
                              ),
                        ),
                        Text(
                          plan.subject,
                          style: Theme.of(context).textTheme.bodySmall?.copyWith(
                                color: subjectColor,
                              ),
                        ),
                      ],
                    ),
                  ),
                  // Progress badge
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                    decoration: BoxDecoration(
                      color: subjectColor.withOpacity(0.15),
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: Text(
                      '${plan.progressPercentage.toStringAsFixed(0)}%',
                      style: TextStyle(
                        color: subjectColor,
                        fontSize: 13,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 12),
              // Current unit info
              if (currentUnit != null)
                Text(
                  currentUnit.name,
                  style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                        color: Colors.white70,
                      ),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
              const SizedBox(height: 12),
              // Progress bar
              Row(
                children: [
                  Expanded(
                    child: ClipRRect(
                      borderRadius: BorderRadius.circular(8),
                      child: LinearProgressIndicator(
                        value: progress.clamp(0.0, 1.0),
                        minHeight: 8,
                        backgroundColor: AppTheme.bgElevated,
                        valueColor: AlwaysStoppedAnimation<Color>(subjectColor),
                      ),
                    ),
                  ),
                  const SizedBox(width: 16),
                  const Icon(Icons.arrow_forward_ios,
                      size: 16, color: AppTheme.textSecondary),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  IconData _getSubjectIcon(String subject) {
    final subjectLower = subject.toLowerCase();
    if (subjectLower.contains('matem')) return Icons.calculate;
    if (subjectLower.contains('lenguaje') || subjectLower.contains('lectura')) {
      return Icons.menu_book;
    }
    if (subjectLower.contains('natural')) return Icons.science;
    if (subjectLower.contains('social')) return Icons.public;
    if (subjectLower.contains('ingl')) return Icons.language;
    return Icons.school;
  }
}
