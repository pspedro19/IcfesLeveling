import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../../core/config/app_theme.dart';
import '../../../../shared/widgets/pressable_scale.dart';
import '../providers/unit_detail_provider.dart';
import '../../domain/entities/unit_detail.dart';

/// Unit Detail Page - displays videos, exercises, and readings for a study unit
class UnitDetailPage extends ConsumerStatefulWidget {
  final String unitId;

  const UnitDetailPage({super.key, required this.unitId});

  @override
  ConsumerState<UnitDetailPage> createState() => _UnitDetailPageState();
}

class _UnitDetailPageState extends ConsumerState<UnitDetailPage>
    with SingleTickerProviderStateMixin {
  late AnimationController _animationController;
  late Animation<double> _fadeAnimation;
  late Animation<Offset> _slideAnimation;

  @override
  void initState() {
    super.initState();
    _animationController = AnimationController(
      duration: const Duration(milliseconds: 600),
      vsync: this,
    );

    _fadeAnimation = CurvedAnimation(
      parent: _animationController,
      curve: Curves.easeOut,
    );

    _slideAnimation = Tween<Offset>(
      begin: const Offset(0, 0.1),
      end: Offset.zero,
    ).animate(CurvedAnimation(
      parent: _animationController,
      curve: Curves.easeOutCubic,
    ));

    _animationController.forward();
  }

  @override
  void dispose() {
    _animationController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(unitDetailProvider(widget.unitId));

    return Scaffold(
      backgroundColor: AppTheme.bgDark,
      body: state.isLoading
          ? _buildLoadingState()
          : state.error != null
              ? _buildErrorState(state.error!)
              : state.unit != null
                  ? _buildContent(state)
                  : _buildEmptyState(),
    );
  }

  Widget _buildLoadingState() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const CircularProgressIndicator(
            valueColor: AlwaysStoppedAnimation<Color>(AppTheme.primaryPurple),
          ),
          const SizedBox(height: 16),
          Text(
            'Cargando unidad...',
            style: TextStyle(
              color: AppTheme.textSecondary,
              fontSize: 16,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildErrorState(String error) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(
              Icons.error_outline,
              size: 64,
              color: AppTheme.dangerRed,
            ),
            const SizedBox(height: 16),
            Text(
              'Error al cargar la unidad',
              style: TextStyle(
                color: AppTheme.textPrimary,
                fontSize: 20,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 8),
            Text(
              error,
              textAlign: TextAlign.center,
              style: TextStyle(
                color: AppTheme.textSecondary,
                fontSize: 14,
              ),
            ),
            const SizedBox(height: 24),
            ElevatedButton.icon(
              onPressed: () => ref.read(unitDetailProvider(widget.unitId).notifier).refresh(),
              icon: const Icon(Icons.refresh),
              label: const Text('Reintentar'),
              style: ElevatedButton.styleFrom(
                backgroundColor: AppTheme.primaryPurple,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildEmptyState() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(
            Icons.folder_open,
            size: 64,
            color: AppTheme.textMuted,
          ),
          const SizedBox(height: 16),
          Text(
            'Unidad no encontrada',
            style: TextStyle(
              color: AppTheme.textPrimary,
              fontSize: 20,
              fontWeight: FontWeight.bold,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildContent(UnitDetailState state) {
    final unit = state.unit!;

    return FadeTransition(
      opacity: _fadeAnimation,
      child: SlideTransition(
        position: _slideAnimation,
        child: CustomScrollView(
          slivers: [
            // Custom App Bar with Unit Header
            _buildSliverAppBar(unit, state),

            // Progress Overview
            SliverToBoxAdapter(
              child: _buildProgressOverview(state),
            ),

            // Videos Section
            if (unit.videos.isNotEmpty) ...[
              _buildSectionHeader(
                'Videos',
                Icons.play_circle_filled,
                AppTheme.accentCyan,
                '${unit.watchedVideosCount}/${unit.videos.length}',
              ),
              SliverToBoxAdapter(
                child: _buildVideosList(unit.videos),
              ),
            ],

            // Exercises Section
            if (unit.exercises.isNotEmpty) ...[
              _buildSectionHeader(
                'Ejercicios',
                Icons.quiz,
                AppTheme.successGreen,
                '${unit.completedExercisesCount}/${unit.exercises.length}',
              ),
              SliverToBoxAdapter(
                child: _buildExercisesList(unit.exercises),
              ),
            ],

            // Readings Section
            if (unit.readings.isNotEmpty) ...[
              _buildSectionHeader(
                'Lecturas',
                Icons.menu_book,
                AppTheme.warningOrange,
                '${unit.completedReadingsCount}/${unit.readings.length}',
              ),
              SliverToBoxAdapter(
                child: _buildReadingsList(unit.readings),
              ),
            ],

            // Bottom padding and Start Quiz button
            SliverToBoxAdapter(
              child: _buildBottomSection(unit),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildSliverAppBar(UnitDetail unit, UnitDetailState state) {
    return SliverAppBar(
      expandedHeight: 200,
      pinned: true,
      backgroundColor: AppTheme.bgDark,
      leading: IconButton(
        icon: Container(
          padding: const EdgeInsets.all(8),
          decoration: BoxDecoration(
            color: AppTheme.bgCard.withOpacity(0.8),
            shape: BoxShape.circle,
          ),
          child: const Icon(Icons.arrow_back, color: AppTheme.textPrimary),
        ),
        onPressed: () => context.pop(),
      ),
      flexibleSpace: FlexibleSpaceBar(
        background: Container(
          decoration: BoxDecoration(
            gradient: LinearGradient(
              begin: Alignment.topCenter,
              end: Alignment.bottomCenter,
              colors: [
                AppTheme.primaryPurple.withOpacity(0.3),
                AppTheme.bgDark,
              ],
            ),
          ),
          child: SafeArea(
            child: Padding(
              padding: const EdgeInsets.fromLTRB(20, 60, 20, 20),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Unit number badge
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
                      'UNIDAD ${unit.unitNumber}',
                      style: const TextStyle(
                        color: AppTheme.primaryPurple,
                        fontSize: 12,
                        fontWeight: FontWeight.bold,
                        letterSpacing: 1,
                      ),
                    ),
                  ),
                  const SizedBox(height: 12),

                  // Unit name
                  Text(
                    unit.name,
                    style: const TextStyle(
                      color: AppTheme.textPrimary,
                      fontSize: 24,
                      fontWeight: FontWeight.bold,
                    ),
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                  ),
                  const SizedBox(height: 8),

                  // Description
                  Text(
                    unit.description,
                    style: TextStyle(
                      color: AppTheme.textSecondary,
                      fontSize: 14,
                    ),
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                  ),

                  const Spacer(),

                  // Estimated time and priority
                  Row(
                    children: [
                      if (unit.estimatedTime != null) ...[
                        Icon(
                          Icons.access_time,
                          size: 16,
                          color: AppTheme.textMuted,
                        ),
                        const SizedBox(width: 4),
                        Text(
                          unit.estimatedTime!,
                          style: TextStyle(
                            color: AppTheme.textMuted,
                            fontSize: 12,
                          ),
                        ),
                        const SizedBox(width: 16),
                      ],
                      if (unit.recommendedPriority != null)
                        _buildPriorityBadge(unit.recommendedPriority!),
                    ],
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildPriorityBadge(String priority) {
    Color color;
    String label;

    switch (priority.toLowerCase()) {
      case 'high':
        color = AppTheme.dangerRed;
        label = 'Alta prioridad';
        break;
      case 'medium':
        color = AppTheme.warningOrange;
        label = 'Media prioridad';
        break;
      default:
        color = AppTheme.successGreen;
        label = 'Baja prioridad';
    }

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: color.withOpacity(0.2),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(Icons.flag, size: 12, color: color),
          const SizedBox(width: 4),
          Text(
            label,
            style: TextStyle(
              color: color,
              fontSize: 10,
              fontWeight: FontWeight.bold,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildProgressOverview(UnitDetailState state) {
    return Container(
      margin: const EdgeInsets.all(16),
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: AppTheme.bgCard,
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.2),
            blurRadius: 10,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Text(
                'Progreso de la Unidad',
                style: TextStyle(
                  color: AppTheme.textPrimary,
                  fontSize: 16,
                  fontWeight: FontWeight.bold,
                ),
              ),
              TweenAnimationBuilder<double>(
                tween: Tween(begin: 0, end: state.overallProgress),
                duration: const Duration(milliseconds: 800),
                curve: Curves.easeOutCubic,
                builder: (context, value, child) {
                  return Text(
                    '${value.toInt()}%',
                    style: TextStyle(
                      color: _getProgressColor(value),
                      fontSize: 20,
                      fontWeight: FontWeight.bold,
                    ),
                  );
                },
              ),
            ],
          ),
          const SizedBox(height: 16),

          // Overall progress bar
          TweenAnimationBuilder<double>(
            tween: Tween(begin: 0, end: state.overallProgress / 100),
            duration: const Duration(milliseconds: 800),
            curve: Curves.easeOutCubic,
            builder: (context, value, child) {
              return ClipRRect(
                borderRadius: BorderRadius.circular(8),
                child: LinearProgressIndicator(
                  value: value,
                  minHeight: 12,
                  backgroundColor: AppTheme.bgElevated,
                  valueColor: AlwaysStoppedAnimation<Color>(
                    _getProgressColor(state.overallProgress),
                  ),
                ),
              );
            },
          ),
          const SizedBox(height: 20),

          // Individual progress bars
          _buildMiniProgressBar(
            'Videos',
            state.videosProgress,
            AppTheme.accentCyan,
            Icons.play_circle_filled,
          ),
          const SizedBox(height: 12),
          _buildMiniProgressBar(
            'Ejercicios',
            state.exercisesProgress,
            AppTheme.successGreen,
            Icons.quiz,
          ),
          const SizedBox(height: 12),
          _buildMiniProgressBar(
            'Lecturas',
            state.readingsProgress,
            AppTheme.warningOrange,
            Icons.menu_book,
          ),
        ],
      ),
    );
  }

  Widget _buildMiniProgressBar(
    String label,
    double progress,
    Color color,
    IconData icon,
  ) {
    return Row(
      children: [
        Icon(icon, size: 16, color: color),
        const SizedBox(width: 8),
        Expanded(
          flex: 2,
          child: Text(
            label,
            style: TextStyle(
              color: AppTheme.textSecondary,
              fontSize: 12,
            ),
          ),
        ),
        Expanded(
          flex: 5,
          child: TweenAnimationBuilder<double>(
            tween: Tween(begin: 0, end: progress / 100),
            duration: const Duration(milliseconds: 600),
            curve: Curves.easeOutCubic,
            builder: (context, value, child) {
              return ClipRRect(
                borderRadius: BorderRadius.circular(4),
                child: LinearProgressIndicator(
                  value: value,
                  minHeight: 6,
                  backgroundColor: AppTheme.bgElevated,
                  valueColor: AlwaysStoppedAnimation<Color>(color),
                ),
              );
            },
          ),
        ),
        const SizedBox(width: 8),
        SizedBox(
          width: 40,
          child: Text(
            '${progress.toInt()}%',
            textAlign: TextAlign.right,
            style: TextStyle(
              color: color,
              fontSize: 12,
              fontWeight: FontWeight.bold,
            ),
          ),
        ),
      ],
    );
  }

  Color _getProgressColor(double progress) {
    if (progress >= 80) return AppTheme.successGreen;
    if (progress >= 50) return AppTheme.warningOrange;
    return AppTheme.primaryPurple;
  }

  Widget _buildSectionHeader(
    String title,
    IconData icon,
    Color color,
    String count,
  ) {
    return SliverToBoxAdapter(
      child: Padding(
        padding: const EdgeInsets.fromLTRB(16, 24, 16, 12),
        child: Row(
          children: [
            Container(
              padding: const EdgeInsets.all(8),
              decoration: BoxDecoration(
                color: color.withOpacity(0.2),
                borderRadius: BorderRadius.circular(8),
              ),
              child: Icon(icon, color: color, size: 20),
            ),
            const SizedBox(width: 12),
            Text(
              title,
              style: const TextStyle(
                color: AppTheme.textPrimary,
                fontSize: 18,
                fontWeight: FontWeight.bold,
              ),
            ),
            const Spacer(),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
              decoration: BoxDecoration(
                color: AppTheme.bgElevated,
                borderRadius: BorderRadius.circular(12),
              ),
              child: Text(
                count,
                style: TextStyle(
                  color: color,
                  fontSize: 12,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildVideosList(List<UnitVideo> videos) {
    return ListView.builder(
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      padding: const EdgeInsets.symmetric(horizontal: 16),
      itemCount: videos.length,
      itemBuilder: (context, index) {
        return _VideoCard(
          video: videos[index],
          onTap: () => _navigateToVideo(videos[index]),
          onMarkWatched: () => ref
              .read(unitDetailProvider(widget.unitId).notifier)
              .markVideoWatched(videos[index].id),
        );
      },
    );
  }

  Widget _buildExercisesList(List<UnitExercise> exercises) {
    return ListView.builder(
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      padding: const EdgeInsets.symmetric(horizontal: 16),
      itemCount: exercises.length,
      itemBuilder: (context, index) {
        return _ExerciseCard(
          exercise: exercises[index],
          onTap: () => _navigateToQuiz(exercises[index]),
        );
      },
    );
  }

  Widget _buildReadingsList(List<UnitReading> readings) {
    return ListView.builder(
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      padding: const EdgeInsets.symmetric(horizontal: 16),
      itemCount: readings.length,
      itemBuilder: (context, index) {
        return _ReadingCard(
          reading: readings[index],
          onTap: () => _openReading(readings[index]),
          onMarkCompleted: () => ref
              .read(unitDetailProvider(widget.unitId).notifier)
              .markReadingCompleted(readings[index].id),
        );
      },
    );
  }

  Widget _buildBottomSection(UnitDetail unit) {
    return Padding(
      padding: const EdgeInsets.all(16),
      child: Column(
        children: [
          // Focus topics
          if (unit.focusTopics.isNotEmpty) ...[
            _buildTopicsChips('Temas a enfocarse', unit.focusTopics, AppTheme.primaryPurple),
            const SizedBox(height: 16),
          ],

          // Weak areas
          if (unit.weakAreas.isNotEmpty) ...[
            _buildTopicsChips('Areas a mejorar', unit.weakAreas, AppTheme.warningOrange),
            const SizedBox(height: 24),
          ],

          // Start Quiz Button
          if (unit.exercises.isNotEmpty)
            PressableScale(
              onTap: () => context.push('/study-plan/unit/${widget.unitId}/quiz'),
              child: Container(
                width: double.infinity,
                height: 56,
                decoration: BoxDecoration(
                  gradient: const LinearGradient(
                    colors: [AppTheme.primaryPurple, Color(0xFF8B5CF6)],
                  ),
                  borderRadius: BorderRadius.circular(16),
                  boxShadow: [
                    BoxShadow(
                      color: AppTheme.primaryPurple.withOpacity(0.3),
                      blurRadius: 12,
                      offset: const Offset(0, 4),
                    ),
                  ],
                ),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    const Icon(Icons.quiz, color: Colors.white),
                    const SizedBox(width: 12),
                    const Text(
                      'Iniciar Quiz de la Unidad',
                      style: TextStyle(
                        color: Colors.white,
                        fontSize: 16,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ],
                ),
              ),
            ),

          const SizedBox(height: 32),
        ],
      ),
    );
  }

  Widget _buildTopicsChips(String title, List<String> topics, Color color) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          title,
          style: TextStyle(
            color: AppTheme.textSecondary,
            fontSize: 12,
            fontWeight: FontWeight.w500,
          ),
        ),
        const SizedBox(height: 8),
        Wrap(
          spacing: 8,
          runSpacing: 8,
          children: topics.map((topic) {
            return Container(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
              decoration: BoxDecoration(
                color: color.withOpacity(0.1),
                borderRadius: BorderRadius.circular(20),
                border: Border.all(color: color.withOpacity(0.3)),
              ),
              child: Text(
                topic,
                style: TextStyle(
                  color: color,
                  fontSize: 12,
                ),
              ),
            );
          }).toList(),
        ),
      ],
    );
  }

  void _navigateToVideo(UnitVideo video) {
    context.push('/video/${video.youtubeId}');
  }

  void _navigateToQuiz(UnitExercise exercise) {
    context.push('/study-plan/unit/${widget.unitId}/quiz');
  }

  void _openReading(UnitReading reading) {
    // Show reading content in a modal bottom sheet
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (context) => _ReadingModal(
        reading: reading,
        onComplete: () {
          ref
              .read(unitDetailProvider(widget.unitId).notifier)
              .markReadingCompleted(reading.id);
          Navigator.pop(context);
        },
      ),
    );
  }
}

/// Video card widget
class _VideoCard extends StatelessWidget {
  final UnitVideo video;
  final VoidCallback onTap;
  final VoidCallback onMarkWatched;

  const _VideoCard({
    required this.video,
    required this.onTap,
    required this.onMarkWatched,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: PressableScale(
        onTap: onTap,
        child: Container(
          decoration: BoxDecoration(
            color: AppTheme.bgCard,
            borderRadius: BorderRadius.circular(12),
            border: video.isWatched
                ? Border.all(color: AppTheme.successGreen.withOpacity(0.5), width: 2)
                : null,
          ),
          child: Row(
            children: [
              // Thumbnail
              ClipRRect(
                borderRadius: const BorderRadius.horizontal(left: Radius.circular(12)),
                child: Stack(
                  children: [
                    Container(
                      width: 120,
                      height: 90,
                      color: AppTheme.bgElevated,
                      child: video.thumbnailUrl != null
                          ? Image.network(
                              video.thumbnailUrl!,
                              fit: BoxFit.cover,
                              errorBuilder: (_, __, ___) => _buildPlaceholderThumbnail(),
                            )
                          : _buildPlaceholderThumbnail(),
                    ),
                    // Duration overlay
                    Positioned(
                      bottom: 4,
                      right: 4,
                      child: Container(
                        padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                        decoration: BoxDecoration(
                          color: Colors.black.withOpacity(0.8),
                          borderRadius: BorderRadius.circular(4),
                        ),
                        child: Text(
                          video.formattedDuration,
                          style: const TextStyle(
                            color: Colors.white,
                            fontSize: 10,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ),
                    ),
                    // Watched overlay
                    if (video.isWatched)
                      Positioned.fill(
                        child: Container(
                          color: AppTheme.successGreen.withOpacity(0.3),
                          child: const Icon(
                            Icons.check_circle,
                            color: AppTheme.successGreen,
                            size: 32,
                          ),
                        ),
                      ),
                  ],
                ),
              ),

              // Content
              Expanded(
                child: Padding(
                  padding: const EdgeInsets.all(12),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          if (video.isRequired)
                            Container(
                              margin: const EdgeInsets.only(right: 8),
                              padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                              decoration: BoxDecoration(
                                color: AppTheme.warningOrange.withOpacity(0.2),
                                borderRadius: BorderRadius.circular(4),
                              ),
                              child: const Text(
                                'REQUERIDO',
                                style: TextStyle(
                                  color: AppTheme.warningOrange,
                                  fontSize: 8,
                                  fontWeight: FontWeight.bold,
                                ),
                              ),
                            ),
                        ],
                      ),
                      Text(
                        video.title,
                        style: const TextStyle(
                          color: AppTheme.textPrimary,
                          fontSize: 14,
                          fontWeight: FontWeight.w600,
                        ),
                        maxLines: 2,
                        overflow: TextOverflow.ellipsis,
                      ),
                      const SizedBox(height: 4),
                      Text(
                        video.channelName,
                        style: TextStyle(
                          color: AppTheme.textMuted,
                          fontSize: 12,
                        ),
                      ),
                      if (video.learningObjective != null) ...[
                        const SizedBox(height: 4),
                        Text(
                          video.learningObjective!,
                          style: TextStyle(
                            color: AppTheme.textSecondary,
                            fontSize: 11,
                            fontStyle: FontStyle.italic,
                          ),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                      ],
                    ],
                  ),
                ),
              ),

              // Action button
              Padding(
                padding: const EdgeInsets.only(right: 12),
                child: Icon(
                  video.isWatched ? Icons.replay : Icons.play_arrow,
                  color: video.isWatched ? AppTheme.successGreen : AppTheme.accentCyan,
                  size: 28,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildPlaceholderThumbnail() {
    return Container(
      width: 120,
      height: 90,
      color: AppTheme.bgElevated,
      child: const Icon(
        Icons.play_circle_outline,
        color: AppTheme.textMuted,
        size: 40,
      ),
    );
  }
}

/// Exercise card widget
class _ExerciseCard extends StatelessWidget {
  final UnitExercise exercise;
  final VoidCallback onTap;

  const _ExerciseCard({
    required this.exercise,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: PressableScale(
        onTap: onTap,
        child: Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: AppTheme.bgCard,
            borderRadius: BorderRadius.circular(12),
            border: exercise.isCompleted
                ? Border.all(color: AppTheme.successGreen.withOpacity(0.5), width: 2)
                : null,
          ),
          child: Row(
            children: [
              // Icon
              Container(
                width: 48,
                height: 48,
                decoration: BoxDecoration(
                  color: exercise.isCompleted
                      ? AppTheme.successGreen.withOpacity(0.2)
                      : AppTheme.bgElevated,
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Icon(
                  exercise.isCompleted ? Icons.check_circle : Icons.quiz,
                  color: exercise.isCompleted ? AppTheme.successGreen : AppTheme.primaryPurple,
                  size: 24,
                ),
              ),
              const SizedBox(width: 16),

              // Content
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      exercise.title,
                      style: const TextStyle(
                        color: AppTheme.textPrimary,
                        fontSize: 14,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Row(
                      children: [
                        Text(
                          '${exercise.questionCount} preguntas',
                          style: TextStyle(
                            color: AppTheme.textSecondary,
                            fontSize: 12,
                          ),
                        ),
                        const SizedBox(width: 12),
                        _buildDifficultyBadge(exercise.difficulty),
                      ],
                    ),
                    if (exercise.isCompleted) ...[
                      const SizedBox(height: 8),
                      Row(
                        children: [
                          Icon(
                            Icons.star,
                            size: 14,
                            color: AppTheme.secondaryGold,
                          ),
                          const SizedBox(width: 4),
                          Text(
                            'Puntuacion: ${exercise.score.toInt()}%',
                            style: TextStyle(
                              color: AppTheme.secondaryGold,
                              fontSize: 12,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ],
                      ),
                    ],
                  ],
                ),
              ),

              // Arrow
              Icon(
                Icons.arrow_forward_ios,
                color: AppTheme.textMuted,
                size: 16,
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildDifficultyBadge(String difficulty) {
    Color color;
    String label;

    switch (difficulty.toLowerCase()) {
      case 'easy':
        color = AppTheme.successGreen;
        label = 'Facil';
        break;
      case 'hard':
        color = AppTheme.dangerRed;
        label = 'Dificil';
        break;
      default:
        color = AppTheme.warningOrange;
        label = 'Medio';
    }

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
      decoration: BoxDecoration(
        color: color.withOpacity(0.2),
        borderRadius: BorderRadius.circular(4),
      ),
      child: Text(
        label,
        style: TextStyle(
          color: color,
          fontSize: 10,
          fontWeight: FontWeight.bold,
        ),
      ),
    );
  }
}

/// Reading card widget
class _ReadingCard extends StatelessWidget {
  final UnitReading reading;
  final VoidCallback onTap;
  final VoidCallback onMarkCompleted;

  const _ReadingCard({
    required this.reading,
    required this.onTap,
    required this.onMarkCompleted,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: PressableScale(
        onTap: onTap,
        child: Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: AppTheme.bgCard,
            borderRadius: BorderRadius.circular(12),
            border: reading.isCompleted
                ? Border.all(color: AppTheme.successGreen.withOpacity(0.5), width: 2)
                : null,
          ),
          child: Row(
            children: [
              // Icon
              Container(
                width: 48,
                height: 48,
                decoration: BoxDecoration(
                  color: reading.isCompleted
                      ? AppTheme.successGreen.withOpacity(0.2)
                      : AppTheme.bgElevated,
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Icon(
                  reading.isCompleted ? Icons.check_circle : Icons.menu_book,
                  color: reading.isCompleted ? AppTheme.successGreen : AppTheme.warningOrange,
                  size: 24,
                ),
              ),
              const SizedBox(width: 16),

              // Content
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      reading.title,
                      style: const TextStyle(
                        color: AppTheme.textPrimary,
                        fontSize: 14,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Row(
                      children: [
                        Icon(
                          Icons.access_time,
                          size: 12,
                          color: AppTheme.textMuted,
                        ),
                        const SizedBox(width: 4),
                        Text(
                          '${reading.estimatedMinutes} min',
                          style: TextStyle(
                            color: AppTheme.textSecondary,
                            fontSize: 12,
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),

              // Status indicator
              if (reading.isCompleted)
                Icon(
                  Icons.check_circle,
                  color: AppTheme.successGreen,
                  size: 24,
                )
              else
                Icon(
                  Icons.arrow_forward_ios,
                  color: AppTheme.textMuted,
                  size: 16,
                ),
            ],
          ),
        ),
      ),
    );
  }
}

/// Reading modal widget
class _ReadingModal extends StatelessWidget {
  final UnitReading reading;
  final VoidCallback onComplete;

  const _ReadingModal({
    required this.reading,
    required this.onComplete,
  });

  @override
  Widget build(BuildContext context) {
    return DraggableScrollableSheet(
      initialChildSize: 0.7,
      minChildSize: 0.5,
      maxChildSize: 0.95,
      builder: (context, scrollController) {
        return Container(
          decoration: const BoxDecoration(
            color: AppTheme.bgCard,
            borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
          ),
          child: Column(
            children: [
              // Handle
              Container(
                margin: const EdgeInsets.only(top: 12),
                width: 40,
                height: 4,
                decoration: BoxDecoration(
                  color: AppTheme.textMuted,
                  borderRadius: BorderRadius.circular(2),
                ),
              ),

              // Header
              Padding(
                padding: const EdgeInsets.all(20),
                child: Row(
                  children: [
                    Container(
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: AppTheme.warningOrange.withOpacity(0.2),
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: const Icon(
                        Icons.menu_book,
                        color: AppTheme.warningOrange,
                      ),
                    ),
                    const SizedBox(width: 16),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            reading.title,
                            style: const TextStyle(
                              color: AppTheme.textPrimary,
                              fontSize: 18,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                          const SizedBox(height: 4),
                          Text(
                            '${reading.estimatedMinutes} min de lectura',
                            style: TextStyle(
                              color: AppTheme.textSecondary,
                              fontSize: 12,
                            ),
                          ),
                        ],
                      ),
                    ),
                    IconButton(
                      onPressed: () => Navigator.pop(context),
                      icon: const Icon(Icons.close, color: AppTheme.textMuted),
                    ),
                  ],
                ),
              ),

              const Divider(color: AppTheme.bgElevated),

              // Content
              Expanded(
                child: SingleChildScrollView(
                  controller: scrollController,
                  padding: const EdgeInsets.all(20),
                  child: Text(
                    reading.content ?? 'Contenido no disponible.',
                    style: const TextStyle(
                      color: AppTheme.textPrimary,
                      fontSize: 16,
                      height: 1.6,
                    ),
                  ),
                ),
              ),

              // Complete button
              if (!reading.isCompleted)
                SafeArea(
                  child: Padding(
                    padding: const EdgeInsets.all(20),
                    child: PressableScale(
                      onTap: onComplete,
                      child: Container(
                        width: double.infinity,
                        height: 56,
                        decoration: BoxDecoration(
                          color: AppTheme.successGreen,
                          borderRadius: BorderRadius.circular(16),
                        ),
                        child: const Row(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Icon(Icons.check, color: Colors.white),
                            SizedBox(width: 8),
                            Text(
                              'Marcar como leido',
                              style: TextStyle(
                                color: Colors.white,
                                fontSize: 16,
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
                  ),
                ),
            ],
          ),
        );
      },
    );
  }
}
