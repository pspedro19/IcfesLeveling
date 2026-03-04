import 'package:flutter/material.dart';
import '../../data/models/stats_models.dart';

/// Card showing study plan completion progress
class StudyPlanProgressCard extends StatelessWidget {
  final StudyPlanProgress progress;
  final VoidCallback? onTap;
  final VoidCallback? onViewPlan;

  const StudyPlanProgressCard({
    super.key,
    required this.progress,
    this.onTap,
    this.onViewPlan,
  });

  @override
  Widget build(BuildContext context) {
    final isCompleted = progress.isCompleted;

    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.all(20),
        decoration: BoxDecoration(
          gradient: isCompleted
              ? LinearGradient(
                  colors: [
                    Colors.green.shade700,
                    Colors.green.shade900,
                  ],
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                )
              : LinearGradient(
                  colors: [
                    Colors.blue.shade700,
                    Colors.purple.shade900,
                  ],
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                ),
          borderRadius: BorderRadius.circular(20),
          boxShadow: [
            BoxShadow(
              color: (isCompleted ? Colors.green : Colors.blue).withOpacity(0.3),
              blurRadius: 12,
              offset: const Offset(0, 4),
            ),
          ],
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: Colors.white.withOpacity(0.2),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Icon(
                    isCompleted ? Icons.emoji_events : Icons.menu_book,
                    color: Colors.white,
                    size: 28,
                  ),
                ),
                const SizedBox(width: 16),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        isCompleted ? 'Plan Completado!' : 'Plan de Estudio',
                        style: const TextStyle(
                          color: Colors.white,
                          fontWeight: FontWeight.bold,
                          fontSize: 18,
                        ),
                      ),
                      if (!isCompleted && progress.planName.isNotEmpty)
                        Text(
                          progress.planName,
                          style: TextStyle(
                            color: Colors.white.withOpacity(0.8),
                            fontSize: 13,
                          ),
                        ),
                    ],
                  ),
                ),
                // Percentage circle
                _buildProgressCircle(),
              ],
            ),
            const SizedBox(height: 20),

            // Progress bar
            ClipRRect(
              borderRadius: BorderRadius.circular(8),
              child: LinearProgressIndicator(
                value: progress.overallProgress,
                backgroundColor: Colors.white.withOpacity(0.2),
                valueColor: AlwaysStoppedAnimation<Color>(
                  isCompleted ? Colors.greenAccent : Colors.white,
                ),
                minHeight: 10,
              ),
            ),
            const SizedBox(height: 16),

            // Stats row
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceAround,
              children: [
                _buildStatColumn(
                  icon: Icons.layers,
                  value: '${progress.completedUnits}/${progress.totalUnits}',
                  label: 'Unidades',
                ),
                _buildStatColumn(
                  icon: Icons.play_circle,
                  value: '${progress.watchedVideos}/${progress.totalVideos}',
                  label: 'Videos',
                ),
                _buildStatColumn(
                  icon: Icons.quiz,
                  value: '${progress.passedQuizzes}/${progress.totalQuizzes}',
                  label: 'Quizzes',
                ),
              ],
            ),

            if (onViewPlan != null) ...[
              const SizedBox(height: 16),
              SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  onPressed: onViewPlan,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.white.withOpacity(0.2),
                    foregroundColor: Colors.white,
                    elevation: 0,
                    padding: const EdgeInsets.symmetric(vertical: 12),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(12),
                    ),
                  ),
                  child: Text(
                    isCompleted ? 'Ver Resumen' : 'Continuar Estudiando',
                    style: const TextStyle(fontWeight: FontWeight.bold),
                  ),
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildProgressCircle() {
    return Stack(
      alignment: Alignment.center,
      children: [
        SizedBox(
          width: 60,
          height: 60,
          child: CircularProgressIndicator(
            value: progress.overallProgress,
            strokeWidth: 6,
            backgroundColor: Colors.white.withOpacity(0.2),
            valueColor: const AlwaysStoppedAnimation<Color>(Colors.white),
          ),
        ),
        Text(
          '${progress.progressPercent}%',
          style: const TextStyle(
            color: Colors.white,
            fontWeight: FontWeight.bold,
            fontSize: 14,
          ),
        ),
      ],
    );
  }

  Widget _buildStatColumn({
    required IconData icon,
    required String value,
    required String label,
  }) {
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
            color: Colors.white.withOpacity(0.7),
            fontSize: 11,
          ),
        ),
      ],
    );
  }
}

/// Compact version for lists
class StudyPlanProgressCompact extends StatelessWidget {
  final StudyPlanProgress progress;
  final VoidCallback? onTap;

  const StudyPlanProgressCompact({
    super.key,
    required this.progress,
    this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return ListTile(
      onTap: onTap,
      leading: CircleAvatar(
        backgroundColor: progress.isCompleted
            ? Colors.green.withOpacity(0.2)
            : Colors.blue.withOpacity(0.2),
        child: Icon(
          progress.isCompleted ? Icons.check : Icons.menu_book,
          color: progress.isCompleted ? Colors.green : Colors.blue,
        ),
      ),
      title: Text(
        progress.planName.isEmpty ? 'Plan de Estudio' : progress.planName,
        style: const TextStyle(fontWeight: FontWeight.bold),
      ),
      subtitle: Text(
        '${progress.completedUnits}/${progress.totalUnits} unidades completadas',
      ),
      trailing: Text(
        '${progress.progressPercent}%',
        style: TextStyle(
          color: progress.isCompleted ? Colors.green : Colors.blue,
          fontWeight: FontWeight.bold,
          fontSize: 16,
        ),
      ),
    );
  }
}

/// Unit progress list item
class UnitProgressItem extends StatelessWidget {
  final UnitProgress unit;
  final VoidCallback? onTap;

  const UnitProgressItem({
    super.key,
    required this.unit,
    this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return ListTile(
      onTap: unit.isLocked ? null : onTap,
      leading: Container(
        width: 40,
        height: 40,
        decoration: BoxDecoration(
          shape: BoxShape.circle,
          color: unit.isCompleted
              ? Colors.green.withOpacity(0.2)
              : unit.isLocked
                  ? Colors.grey.withOpacity(0.2)
                  : Colors.blue.withOpacity(0.2),
          border: Border.all(
            color: unit.isCompleted
                ? Colors.green
                : unit.isLocked
                    ? Colors.grey
                    : Colors.blue,
            width: 2,
          ),
        ),
        child: Center(
          child: unit.isCompleted
              ? const Icon(Icons.check, color: Colors.green, size: 20)
              : unit.isLocked
                  ? const Icon(Icons.lock, color: Colors.grey, size: 18)
                  : Text(
                      '${unit.unitNumber}',
                      style: const TextStyle(
                        color: Colors.blue,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
        ),
      ),
      title: Text(
        unit.unitName,
        style: TextStyle(
          color: unit.isLocked ? Colors.grey : Colors.white,
          fontWeight: unit.isCompleted ? FontWeight.bold : FontWeight.normal,
        ),
      ),
      subtitle: Row(
        children: [
          Icon(
            Icons.play_circle,
            size: 14,
            color: Colors.grey[600],
          ),
          const SizedBox(width: 4),
          Text(
            '${unit.videosWatched}/${unit.totalVideos}',
            style: TextStyle(color: Colors.grey[600], fontSize: 12),
          ),
          const SizedBox(width: 12),
          Icon(
            Icons.quiz,
            size: 14,
            color: unit.quizPassed ? Colors.green : Colors.grey[600],
          ),
          const SizedBox(width: 4),
          Text(
            unit.quizPassed
                ? '${unit.quizScore ?? 100}%'
                : 'Pendiente',
            style: TextStyle(
              color: unit.quizPassed ? Colors.green : Colors.grey[600],
              fontSize: 12,
            ),
          ),
        ],
      ),
      trailing: unit.isLocked
          ? null
          : SizedBox(
              width: 50,
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Text(
                    '${(unit.progress * 100).toInt()}%',
                    style: TextStyle(
                      color: unit.isCompleted ? Colors.green : Colors.blue,
                      fontWeight: FontWeight.bold,
                      fontSize: 12,
                    ),
                  ),
                  const SizedBox(height: 4),
                  LinearProgressIndicator(
                    value: unit.progress,
                    backgroundColor: Colors.grey[800],
                    valueColor: AlwaysStoppedAnimation(
                      unit.isCompleted ? Colors.green : Colors.blue,
                    ),
                  ),
                ],
              ),
            ),
    );
  }
}
