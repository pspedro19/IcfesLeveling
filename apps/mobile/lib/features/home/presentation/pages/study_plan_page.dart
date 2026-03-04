import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/config/app_theme.dart';
import '../../data/models/study_plan_models.dart';
import '../providers/study_plan_provider.dart';

class StudyPlanPage extends ConsumerWidget {
  const StudyPlanPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(studyPlanProvider);

    return Scaffold(
      backgroundColor: const Color(0xFF0A0A0A),
      body: RefreshIndicator(
        onRefresh: () => ref.read(studyPlanProvider.notifier).refresh(),
        color: AppTheme.primaryPurple,
        backgroundColor: const Color(0xFF1A1A2E),
        child: CustomScrollView(
          physics: const AlwaysScrollableScrollPhysics(),
          slivers: [
            // Custom App Bar with gradient
            _buildSliverAppBar(context, state),

            // Content
            if (state.isLoading)
              const SliverFillRemaining(
                child: Center(
                  child: _LoadingIndicator(),
                ),
              )
            else if (state.errorMessage != null)
              SliverFillRemaining(
                child: _ErrorView(
                  message: state.errorMessage!,
                  onRetry: () => ref.read(studyPlanProvider.notifier).refresh(),
                ),
              )
            else if (!state.hasPlan || state.plan == null)
              SliverFillRemaining(
                child: _NoPlanView(
                  message: state.infoMessage ?? 'No tienes un plan de estudio activo.',
                  onCreatePlan: () => _showSubjectSelection(context, ref),
                ),
              )
            else
              ..._buildPlanContent(context, ref, state.plan!),
          ],
        ),
      ),
    );
  }

  SliverAppBar _buildSliverAppBar(BuildContext context, StudyPlanState state) {
    final plan = state.plan;
    final subjectColor = plan != null ? Color(plan.subjectColor) : AppTheme.primaryPurple;

    return SliverAppBar(
      expandedHeight: plan != null ? 200.0 : 120.0,
      floating: false,
      pinned: true,
      backgroundColor: const Color(0xFF0A0A0A),
      flexibleSpace: FlexibleSpaceBar(
        background: Container(
          decoration: BoxDecoration(
            gradient: LinearGradient(
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
              colors: [
                subjectColor.withOpacity(0.3),
                const Color(0xFF0A0A0A),
              ],
            ),
          ),
          child: plan != null
              ? SafeArea(
                  child: Padding(
                    padding: const EdgeInsets.fromLTRB(20, 60, 20, 20),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      mainAxisAlignment: MainAxisAlignment.end,
                      children: [
                        // Subject badge
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                          decoration: BoxDecoration(
                            color: subjectColor.withOpacity(0.2),
                            borderRadius: BorderRadius.circular(20),
                            border: Border.all(color: subjectColor.withOpacity(0.4)),
                          ),
                          child: Text(
                            plan.subject.toUpperCase(),
                            style: TextStyle(
                              color: subjectColor,
                              fontSize: 12,
                              fontWeight: FontWeight.w700,
                              letterSpacing: 1.2,
                            ),
                          ),
                        ),
                        const SizedBox(height: 12),
                        // Plan title
                        Text(
                          plan.title,
                          style: const TextStyle(
                            color: Colors.white,
                            fontSize: 24,
                            fontWeight: FontWeight.w900,
                            letterSpacing: 0.5,
                          ),
                          maxLines: 2,
                          overflow: TextOverflow.ellipsis,
                        ),
                        const SizedBox(height: 8),
                        // Progress info
                        Row(
                          children: [
                            Icon(Icons.access_time, color: Colors.white54, size: 16),
                            const SizedBox(width: 4),
                            Text(
                              plan.estimatedTime,
                              style: const TextStyle(color: Colors.white54, fontSize: 13),
                            ),
                            const SizedBox(width: 16),
                            Icon(Icons.auto_awesome, color: subjectColor, size: 16),
                            const SizedBox(width: 4),
                            Text(
                              '${plan.completedUnits}/${plan.totalUnits} unidades',
                              style: const TextStyle(color: Colors.white54, fontSize: 13),
                            ),
                          ],
                        ),
                      ],
                    ),
                  ),
                )
              : null,
        ),
        title: plan == null
            ? const Text(
                'Plan de Estudio',
                style: TextStyle(
                  color: Colors.white,
                  fontWeight: FontWeight.w800,
                  letterSpacing: 1,
                ),
              )
            : null,
        centerTitle: true,
      ),
      actions: [
        if (state.hasPlan)
          IconButton(
            icon: const Icon(Icons.info_outline, color: Colors.white54),
            onPressed: () => _showPlanInfo(context, state.plan!),
          ),
      ],
    );
  }

  List<Widget> _buildPlanContent(BuildContext context, WidgetRef ref, StudyPlanDetail plan) {
    return [
      // Overall Progress Card
      SliverToBoxAdapter(
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: _OverallProgressCard(plan: plan)
              .animate()
              .fadeIn(duration: 400.ms)
              .slideY(begin: 0.1, end: 0),
        ),
      ),

      // Current Unit Highlight (if there's one in progress)
      if (plan.currentUnit != null)
        SliverToBoxAdapter(
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16),
            child: _CurrentUnitHighlight(
              unit: plan.currentUnit!,
              planId: plan.id,
              subjectColor: Color(plan.subjectColor),
            ).animate().fadeIn(delay: 100.ms, duration: 400.ms).slideY(begin: 0.1, end: 0),
          ),
        ),

      // Section Title
      SliverToBoxAdapter(
        child: Padding(
          padding: const EdgeInsets.fromLTRB(16, 24, 16, 12),
          child: Row(
            children: [
              Container(
                width: 4,
                height: 20,
                decoration: BoxDecoration(
                  color: Color(plan.subjectColor),
                  borderRadius: BorderRadius.circular(2),
                ),
              ),
              const SizedBox(width: 8),
              const Text(
                'TODAS LAS UNIDADES',
                style: TextStyle(
                  color: Colors.white70,
                  fontSize: 13,
                  fontWeight: FontWeight.w700,
                  letterSpacing: 1.5,
                ),
              ),
            ],
          ),
        ),
      ),

      // Units List
      SliverPadding(
        padding: const EdgeInsets.symmetric(horizontal: 16),
        sliver: SliverList(
          delegate: SliverChildBuilderDelegate(
            (context, index) {
              final unit = plan.units[index];
              return Padding(
                padding: const EdgeInsets.only(bottom: 12),
                child: _UnitCard(
                  unit: unit,
                  planId: plan.id,
                  subjectColor: Color(plan.subjectColor),
                  isCurrentUnit: plan.currentUnit?.unitNumber == unit.unitNumber,
                ).animate(delay: (150 + index * 50).ms).fadeIn(duration: 300.ms).slideX(begin: 0.05, end: 0),
              );
            },
            childCount: plan.units.length,
          ),
        ),
      ),

      // Bottom padding
      const SliverToBoxAdapter(
        child: SizedBox(height: 100),
      ),
    ];
  }

  void _showSubjectSelection(BuildContext context, WidgetRef ref) {
    showModalBottomSheet(
      context: context,
      backgroundColor: Colors.transparent,
      isScrollControlled: true,
      builder: (ctx) => _SubjectSelectionSheet(
        onSubjectSelected: (subjectId) {
          Navigator.pop(ctx);
          ref.read(studyPlanProvider.notifier).generatePlan(subjectId);
        },
      ),
    );
  }

  void _showPlanInfo(BuildContext context, StudyPlanDetail plan) {
    showModalBottomSheet(
      context: context,
      backgroundColor: Colors.transparent,
      builder: (ctx) => _PlanInfoSheet(plan: plan),
    );
  }
}

// =====================================================
// WIDGETS
// =====================================================

class _LoadingIndicator extends StatelessWidget {
  const _LoadingIndicator();

  @override
  Widget build(BuildContext context) {
    return Column(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        SizedBox(
          width: 60,
          height: 60,
          child: CircularProgressIndicator(
            strokeWidth: 3,
            valueColor: AlwaysStoppedAnimation<Color>(
              AppTheme.primaryPurple.withOpacity(0.8),
            ),
          ),
        ),
        const SizedBox(height: 24),
        Text(
          'Cargando tu plan...',
          style: TextStyle(
            color: Colors.white.withOpacity(0.6),
            fontSize: 16,
          ),
        ),
      ],
    ).animate(onPlay: (c) => c.repeat()).shimmer(
          duration: 1500.ms,
          color: AppTheme.primaryPurple.withOpacity(0.3),
        );
  }
}

class _ErrorView extends StatelessWidget {
  final String message;
  final VoidCallback onRetry;

  const _ErrorView({required this.message, required this.onRetry});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(32),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Container(
            padding: const EdgeInsets.all(20),
            decoration: BoxDecoration(
              color: AppTheme.dangerRed.withOpacity(0.1),
              shape: BoxShape.circle,
            ),
            child: Icon(
              Icons.error_outline,
              color: AppTheme.dangerRed,
              size: 48,
            ),
          ),
          const SizedBox(height: 24),
          Text(
            'Oops!',
            style: TextStyle(
              color: Colors.white,
              fontSize: 24,
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 8),
          Text(
            message,
            textAlign: TextAlign.center,
            style: TextStyle(
              color: Colors.white60,
              fontSize: 15,
            ),
          ),
          const SizedBox(height: 32),
          ElevatedButton.icon(
            onPressed: onRetry,
            icon: const Icon(Icons.refresh),
            label: const Text('Reintentar'),
            style: ElevatedButton.styleFrom(
              backgroundColor: AppTheme.primaryPurple,
              foregroundColor: Colors.white,
              padding: const EdgeInsets.symmetric(horizontal: 32, vertical: 16),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(12),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _NoPlanView extends StatelessWidget {
  final String message;
  final VoidCallback onCreatePlan;

  const _NoPlanView({required this.message, required this.onCreatePlan});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(32),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Container(
            padding: const EdgeInsets.all(24),
            decoration: BoxDecoration(
              gradient: LinearGradient(
                colors: [
                  AppTheme.primaryPurple.withOpacity(0.2),
                  AppTheme.accentCyan.withOpacity(0.1),
                ],
              ),
              shape: BoxShape.circle,
              border: Border.all(
                color: AppTheme.primaryPurple.withOpacity(0.3),
                width: 2,
              ),
            ),
            child: Icon(
              Icons.auto_stories,
              color: AppTheme.primaryPurple,
              size: 56,
            ),
          )
              .animate(onPlay: (c) => c.repeat(reverse: true))
              .scale(begin: const Offset(1, 1), end: const Offset(1.05, 1.05), duration: 2000.ms),
          const SizedBox(height: 32),
          const Text(
            'Comienza Tu Aventura',
            style: TextStyle(
              color: Colors.white,
              fontSize: 24,
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 12),
          Text(
            message,
            textAlign: TextAlign.center,
            style: const TextStyle(
              color: Colors.white60,
              fontSize: 15,
              height: 1.5,
            ),
          ),
          const SizedBox(height: 40),
          Container(
            width: double.infinity,
            decoration: BoxDecoration(
              gradient: LinearGradient(
                colors: [AppTheme.primaryPurple, AppTheme.accentCyan],
              ),
              borderRadius: BorderRadius.circular(16),
              boxShadow: [
                BoxShadow(
                  color: AppTheme.primaryPurple.withOpacity(0.4),
                  blurRadius: 20,
                  offset: const Offset(0, 8),
                ),
              ],
            ),
            child: ElevatedButton.icon(
              onPressed: onCreatePlan,
              icon: const Icon(Icons.rocket_launch, size: 22),
              label: const Text(
                'Crear Mi Plan',
                style: TextStyle(fontSize: 17, fontWeight: FontWeight.w700),
              ),
              style: ElevatedButton.styleFrom(
                backgroundColor: Colors.transparent,
                foregroundColor: Colors.white,
                shadowColor: Colors.transparent,
                padding: const EdgeInsets.symmetric(vertical: 18),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(16),
                ),
              ),
            ),
          ),
          const SizedBox(height: 16),
          TextButton(
            onPressed: () => context.go('/diagnostic'),
            child: const Text(
              'Hacer diagnostico primero',
              style: TextStyle(color: Colors.white54),
            ),
          ),
        ],
      ),
    );
  }
}

class _OverallProgressCard extends StatelessWidget {
  final StudyPlanDetail plan;

  const _OverallProgressCard({required this.plan});

  @override
  Widget build(BuildContext context) {
    final progress = plan.progressPercentage / 100;
    final subjectColor = Color(plan.subjectColor);

    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [
            subjectColor.withOpacity(0.15),
            const Color(0xFF1A1A2E),
          ],
        ),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: subjectColor.withOpacity(0.2)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Text(
                'Progreso General',
                style: TextStyle(
                  color: Colors.white70,
                  fontSize: 14,
                  fontWeight: FontWeight.w600,
                ),
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                decoration: BoxDecoration(
                  color: subjectColor.withOpacity(0.2),
                  borderRadius: BorderRadius.circular(20),
                ),
                child: Text(
                  '${plan.progressPercentage.toStringAsFixed(0)}%',
                  style: TextStyle(
                    color: subjectColor,
                    fontSize: 16,
                    fontWeight: FontWeight.w900,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          // Progress bar
          Stack(
            children: [
              Container(
                height: 12,
                decoration: BoxDecoration(
                  color: Colors.white.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(6),
                ),
              ),
              FractionallySizedBox(
                widthFactor: progress.clamp(0.0, 1.0),
                child: Container(
                  height: 12,
                  decoration: BoxDecoration(
                    gradient: LinearGradient(
                      colors: [subjectColor, subjectColor.withOpacity(0.7)],
                    ),
                    borderRadius: BorderRadius.circular(6),
                    boxShadow: [
                      BoxShadow(
                        color: subjectColor.withOpacity(0.5),
                        blurRadius: 8,
                      ),
                    ],
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          // Stats row
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceAround,
            children: [
              _StatItem(
                icon: Icons.check_circle,
                value: '${plan.completedUnits}',
                label: 'Completadas',
                color: AppTheme.successGreen,
              ),
              _StatItem(
                icon: Icons.pending,
                value: '${plan.totalUnits - plan.completedUnits}',
                label: 'Pendientes',
                color: AppTheme.warningOrange,
              ),
              _StatItem(
                icon: Icons.star,
                value: '${(plan.icfesWeight * 100).toInt()}%',
                label: 'Peso ICFES',
                color: AppTheme.secondaryGold,
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class _StatItem extends StatelessWidget {
  final IconData icon;
  final String value;
  final String label;
  final Color color;

  const _StatItem({
    required this.icon,
    required this.value,
    required this.label,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Icon(icon, color: color, size: 20),
        const SizedBox(height: 4),
        Text(
          value,
          style: TextStyle(
            color: Colors.white,
            fontSize: 18,
            fontWeight: FontWeight.w800,
          ),
        ),
        Text(
          label,
          style: TextStyle(
            color: Colors.white54,
            fontSize: 11,
          ),
        ),
      ],
    );
  }
}

class _CurrentUnitHighlight extends StatelessWidget {
  final StudyUnit unit;
  final String planId;
  final Color subjectColor;

  const _CurrentUnitHighlight({
    required this.unit,
    required this.planId,
    required this.subjectColor,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: () => context.push('/study-plan/unit/${unit.unitNumber}'),
      child: Container(
        margin: const EdgeInsets.only(top: 12),
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
            colors: [
              subjectColor.withOpacity(0.25),
              AppTheme.primaryPurple.withOpacity(0.15),
            ],
          ),
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: subjectColor.withOpacity(0.4), width: 2),
          boxShadow: [
            BoxShadow(
              color: subjectColor.withOpacity(0.2),
              blurRadius: 20,
              offset: const Offset(0, 4),
            ),
          ],
        ),
        child: Row(
          children: [
            // Play icon
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: subjectColor.withOpacity(0.2),
                shape: BoxShape.circle,
              ),
              child: Icon(
                Icons.play_arrow_rounded,
                color: subjectColor,
                size: 28,
              ),
            ).animate(onPlay: (c) => c.repeat(reverse: true)).scale(
                  begin: const Offset(1, 1),
                  end: const Offset(1.1, 1.1),
                  duration: 1000.ms,
                ),
            const SizedBox(width: 16),
            // Unit info
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'CONTINUAR ESTUDIANDO',
                    style: TextStyle(
                      color: subjectColor,
                      fontSize: 10,
                      fontWeight: FontWeight.w800,
                      letterSpacing: 1.2,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    unit.name,
                    style: const TextStyle(
                      color: Colors.white,
                      fontSize: 16,
                      fontWeight: FontWeight.w700,
                    ),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                  const SizedBox(height: 6),
                  // Mini progress
                  Row(
                    children: [
                      Expanded(
                        child: ClipRRect(
                          borderRadius: BorderRadius.circular(4),
                          child: LinearProgressIndicator(
                            value: unit.progress / 100,
                            minHeight: 6,
                            backgroundColor: Colors.white.withOpacity(0.1),
                            valueColor: AlwaysStoppedAnimation<Color>(subjectColor),
                          ),
                        ),
                      ),
                      const SizedBox(width: 8),
                      Text(
                        '${unit.progress.toStringAsFixed(0)}%',
                        style: TextStyle(
                          color: subjectColor,
                          fontSize: 12,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
            const SizedBox(width: 8),
            Icon(
              Icons.arrow_forward_ios,
              color: Colors.white54,
              size: 16,
            ),
          ],
        ),
      ),
    );
  }
}

class _UnitCard extends StatelessWidget {
  final StudyUnit unit;
  final String planId;
  final Color subjectColor;
  final bool isCurrentUnit;

  const _UnitCard({
    required this.unit,
    required this.planId,
    required this.subjectColor,
    this.isCurrentUnit = false,
  });

  @override
  Widget build(BuildContext context) {
    final isLocked = unit.status == UnitStatus.locked;
    final isCompleted = unit.status == UnitStatus.completed;

    return GestureDetector(
      onTap: isLocked ? null : () => context.push('/study-plan/unit/${unit.unitNumber}'),
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: isLocked
              ? Colors.white.withOpacity(0.02)
              : const Color(0xFF1A1A2E),
          borderRadius: BorderRadius.circular(16),
          border: Border.all(
            color: isCompleted
                ? AppTheme.successGreen.withOpacity(0.4)
                : isCurrentUnit
                    ? subjectColor.withOpacity(0.4)
                    : Colors.white.withOpacity(0.05),
            width: isCurrentUnit ? 2 : 1,
          ),
        ),
        child: Row(
          children: [
            // Unit number / status icon
            _buildStatusIcon(isLocked, isCompleted),
            const SizedBox(width: 16),
            // Unit details
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Expanded(
                        child: Text(
                          unit.name,
                          style: TextStyle(
                            color: isLocked ? Colors.white38 : Colors.white,
                            fontSize: 15,
                            fontWeight: FontWeight.w600,
                          ),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                      ),
                      if (unit.aiRecommended)
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                          decoration: BoxDecoration(
                            color: AppTheme.accentCyan.withOpacity(0.2),
                            borderRadius: BorderRadius.circular(8),
                          ),
                          child: Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              Icon(Icons.auto_awesome, color: AppTheme.accentCyan, size: 12),
                              const SizedBox(width: 2),
                              Text(
                                'IA',
                                style: TextStyle(
                                  color: AppTheme.accentCyan,
                                  fontSize: 10,
                                  fontWeight: FontWeight.w700,
                                ),
                              ),
                            ],
                          ),
                        ),
                    ],
                  ),
                  const SizedBox(height: 4),
                  Text(
                    unit.description,
                    style: TextStyle(
                      color: isLocked ? Colors.white24 : Colors.white54,
                      fontSize: 12,
                    ),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                  if (!isLocked) ...[
                    const SizedBox(height: 10),
                    // Progress bar
                    Row(
                      children: [
                        Expanded(
                          child: ClipRRect(
                            borderRadius: BorderRadius.circular(4),
                            child: LinearProgressIndicator(
                              value: unit.progress / 100,
                              minHeight: 6,
                              backgroundColor: Colors.white.withOpacity(0.1),
                              valueColor: AlwaysStoppedAnimation<Color>(
                                isCompleted ? AppTheme.successGreen : subjectColor,
                              ),
                            ),
                          ),
                        ),
                        const SizedBox(width: 12),
                        // Progress details
                        _ProgressChip(
                          icon: Icons.play_circle_outline,
                          value: '${unit.videosWatched}/${unit.totalVideos}',
                          isCompleted: unit.videosWatched >= unit.totalVideos,
                        ),
                        const SizedBox(width: 8),
                        _ProgressChip(
                          icon: Icons.edit_note,
                          value: '${unit.exercisesDone}/${unit.totalExercises}',
                          isCompleted: unit.exercisesDone >= unit.totalExercises,
                        ),
                      ],
                    ),
                  ],
                ],
              ),
            ),
            const SizedBox(width: 8),
            // Arrow
            Icon(
              isLocked ? Icons.lock_outline : Icons.chevron_right,
              color: isLocked ? Colors.white24 : Colors.white54,
              size: 20,
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildStatusIcon(bool isLocked, bool isCompleted) {
    if (isCompleted) {
      return Container(
        width: 44,
        height: 44,
        decoration: BoxDecoration(
          color: AppTheme.successGreen.withOpacity(0.2),
          shape: BoxShape.circle,
          border: Border.all(color: AppTheme.successGreen.withOpacity(0.4)),
        ),
        child: const Icon(
          Icons.check_rounded,
          color: AppTheme.successGreen,
          size: 24,
        ),
      );
    }

    if (isLocked) {
      return Container(
        width: 44,
        height: 44,
        decoration: BoxDecoration(
          color: Colors.white.withOpacity(0.05),
          shape: BoxShape.circle,
        ),
        child: Icon(
          Icons.lock_outline,
          color: Colors.white24,
          size: 20,
        ),
      );
    }

    // In progress or available
    return Container(
      width: 44,
      height: 44,
      decoration: BoxDecoration(
        color: subjectColor.withOpacity(0.15),
        shape: BoxShape.circle,
        border: Border.all(color: subjectColor.withOpacity(0.3)),
      ),
      child: Center(
        child: Text(
          '${unit.unitNumber}',
          style: TextStyle(
            color: subjectColor,
            fontSize: 18,
            fontWeight: FontWeight.w800,
          ),
        ),
      ),
    );
  }
}

class _ProgressChip extends StatelessWidget {
  final IconData icon;
  final String value;
  final bool isCompleted;

  const _ProgressChip({
    required this.icon,
    required this.value,
    required this.isCompleted,
  });

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Icon(
          icon,
          size: 14,
          color: isCompleted ? AppTheme.successGreen : Colors.white54,
        ),
        const SizedBox(width: 2),
        Text(
          value,
          style: TextStyle(
            color: isCompleted ? AppTheme.successGreen : Colors.white54,
            fontSize: 11,
            fontWeight: FontWeight.w600,
          ),
        ),
      ],
    );
  }
}

class _SubjectSelectionSheet extends StatelessWidget {
  final Function(String) onSubjectSelected;

  const _SubjectSelectionSheet({required this.onSubjectSelected});

  @override
  Widget build(BuildContext context) {
    final subjects = [
      {'id': 'math', 'name': 'Matematicas', 'icon': Icons.calculate, 'color': 0xFF3B82F6},
      {'id': 'reading', 'name': 'Lectura Critica', 'icon': Icons.menu_book, 'color': 0xFFA855F7},
      {'id': 'science', 'name': 'Ciencias Naturales', 'icon': Icons.science, 'color': 0xFF22C55E},
      {'id': 'social', 'name': 'Sociales', 'icon': Icons.public, 'color': 0xFFF97316},
      {'id': 'english', 'name': 'Ingles', 'icon': Icons.language, 'color': 0xFFEC4899},
    ];

    return Container(
      decoration: const BoxDecoration(
        color: Color(0xFF1A1A2E),
        borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
      ),
      padding: const EdgeInsets.all(24),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Container(
            width: 40,
            height: 4,
            decoration: BoxDecoration(
              color: Colors.white24,
              borderRadius: BorderRadius.circular(2),
            ),
          ),
          const SizedBox(height: 24),
          const Text(
            'Elige una Materia',
            style: TextStyle(
              color: Colors.white,
              fontSize: 22,
              fontWeight: FontWeight.w800,
            ),
          ),
          const SizedBox(height: 8),
          const Text(
            'Selecciona la materia para generar tu plan personalizado',
            textAlign: TextAlign.center,
            style: TextStyle(color: Colors.white54, fontSize: 14),
          ),
          const SizedBox(height: 24),
          ...subjects.map((subject) => Padding(
                padding: const EdgeInsets.only(bottom: 12),
                child: _SubjectTile(
                  name: subject['name'] as String,
                  icon: subject['icon'] as IconData,
                  color: Color(subject['color'] as int),
                  onTap: () => onSubjectSelected(subject['id'] as String),
                ),
              )),
          const SizedBox(height: 16),
        ],
      ),
    );
  }
}

class _SubjectTile extends StatelessWidget {
  final String name;
  final IconData icon;
  final Color color;
  final VoidCallback onTap;

  const _SubjectTile({
    required this.name,
    required this.icon,
    required this.color,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: color.withOpacity(0.1),
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: color.withOpacity(0.3)),
        ),
        child: Row(
          children: [
            Container(
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: color.withOpacity(0.2),
                shape: BoxShape.circle,
              ),
              child: Icon(icon, color: color, size: 24),
            ),
            const SizedBox(width: 16),
            Expanded(
              child: Text(
                name,
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 16,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ),
            Icon(Icons.arrow_forward_ios, color: color.withOpacity(0.6), size: 16),
          ],
        ),
      ),
    );
  }
}

class _PlanInfoSheet extends StatelessWidget {
  final StudyPlanDetail plan;

  const _PlanInfoSheet({required this.plan});

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: const BoxDecoration(
        color: Color(0xFF1A1A2E),
        borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
      ),
      padding: const EdgeInsets.all(24),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Center(
            child: Container(
              width: 40,
              height: 4,
              decoration: BoxDecoration(
                color: Colors.white24,
                borderRadius: BorderRadius.circular(2),
              ),
            ),
          ),
          const SizedBox(height: 24),
          Text(
            plan.title,
            style: const TextStyle(
              color: Colors.white,
              fontSize: 20,
              fontWeight: FontWeight.w800,
            ),
          ),
          const SizedBox(height: 12),
          Text(
            plan.description,
            style: const TextStyle(color: Colors.white60, fontSize: 14, height: 1.5),
          ),
          const SizedBox(height: 24),
          _InfoRow(icon: Icons.school, label: 'Materia', value: plan.subject),
          _InfoRow(icon: Icons.access_time, label: 'Tiempo estimado', value: plan.estimatedTime),
          _InfoRow(icon: Icons.trending_up, label: 'Curva de dificultad', value: plan.difficultyCurve),
          _InfoRow(
            icon: Icons.star,
            label: 'Peso en ICFES',
            value: '${(plan.icfesWeight * 100).toInt()}%',
          ),
          if (plan.examSections.isNotEmpty)
            _InfoRow(
              icon: Icons.list_alt,
              label: 'Secciones',
              value: plan.examSections.join(', '),
            ),
          const SizedBox(height: 24),
        ],
      ),
    );
  }
}

class _InfoRow extends StatelessWidget {
  final IconData icon;
  final String label;
  final String value;

  const _InfoRow({
    required this.icon,
    required this.label,
    required this.value,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8),
      child: Row(
        children: [
          Icon(icon, color: Colors.white54, size: 20),
          const SizedBox(width: 12),
          Text(
            '$label:',
            style: const TextStyle(color: Colors.white54, fontSize: 14),
          ),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              value,
              style: const TextStyle(color: Colors.white, fontSize: 14, fontWeight: FontWeight.w500),
              textAlign: TextAlign.right,
            ),
          ),
        ],
      ),
    );
  }
}
