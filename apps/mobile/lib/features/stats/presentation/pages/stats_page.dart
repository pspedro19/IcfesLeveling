import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../../core/config/routes.dart';
import '../providers/stats_provider.dart';
import '../widgets/subject_mastery_card.dart';
import '../widgets/study_plan_progress_card.dart';
import '../widgets/weekly_chart.dart';
import '../../../profile/presentation/widgets/activity_heatmap.dart';
import '../../data/models/stats_models.dart';

class StatsPage extends ConsumerStatefulWidget {
  const StatsPage({super.key});

  @override
  ConsumerState<StatsPage> createState() => _StatsPageState();
}

class _StatsPageState extends ConsumerState<StatsPage>
    with SingleTickerProviderStateMixin {
  late TabController _tabController;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 3, vsync: this);

    WidgetsBinding.instance.addPostFrameCallback((_) {
      ref.read(statsProvider.notifier).loadAllStats();
    });
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(statsProvider);

    return Scaffold(
      backgroundColor: const Color(0xFF0A0A0A),
      appBar: AppBar(
        title: const Text('Estadisticas y Progreso'),
        backgroundColor: Colors.transparent,
        bottom: TabBar(
          controller: _tabController,
          indicatorColor: Colors.blue,
          tabs: const [
            Tab(text: 'Resumen'),
            Tab(text: 'Materias'),
            Tab(text: 'Plan'),
          ],
        ),
      ),
      body: state.isLoading
          ? const Center(child: CircularProgressIndicator())
          : state.error != null
              ? _buildErrorState(state.error!)
              : RefreshIndicator(
                  onRefresh: () => ref.read(statsProvider.notifier).refresh(),
                  child: TabBarView(
                    controller: _tabController,
                    children: [
                      _buildOverviewTab(state),
                      _buildSubjectsTab(state),
                      _buildPlanTab(state),
                    ],
                  ),
                ),
    );
  }

  Widget _buildErrorState(String error) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const Icon(Icons.error_outline, size: 48, color: Colors.red),
          const SizedBox(height: 16),
          Text(error, style: const TextStyle(color: Colors.grey)),
          const SizedBox(height: 16),
          ElevatedButton(
            onPressed: () => ref.read(statsProvider.notifier).loadAllStats(),
            child: const Text('Reintentar'),
          ),
        ],
      ),
    );
  }

  /// Overview tab with general stats
  Widget _buildOverviewTab(StatsState state) {
    final overview = state.overview ?? UserProgressOverview.empty();
    final weekly = state.weeklyPerformance ?? WeeklyPerformance.empty();

    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // User level card
          _buildLevelCard(overview),
          const SizedBox(height: 20),

          // Quick stats
          _buildQuickStats(overview),
          const SizedBox(height: 24),

          // Weekly chart
          const Text(
            'Esta Semana',
            style: TextStyle(
              color: Colors.white,
              fontSize: 18,
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 12),
          WeeklyChart(data: weekly, metric: 'xp'),
          const SizedBox(height: 16),
          WeeklyStatsSummary(data: weekly),
          const SizedBox(height: 24),

          // Activity heatmap
          const Text(
            'Actividad Anual',
            style: TextStyle(
              color: Colors.white,
              fontSize: 18,
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 12),
          if (state.heatmapData != null)
            ActivityHeatmap(
              heatmapData: state.heatmapData!,
              stats: state.heatmapStats,
            )
          else
            Container(
              height: 150,
              decoration: BoxDecoration(
                color: Colors.grey[900],
                borderRadius: BorderRadius.circular(16),
              ),
              child: const Center(
                child: Text(
                  'Cargando actividad...',
                  style: TextStyle(color: Colors.grey),
                ),
              ),
            ),
        ],
      ),
    );
  }

  Widget _buildLevelCard(UserProgressOverview overview) {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [
            Colors.purple.shade700,
            Colors.blue.shade900,
          ],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(20),
        boxShadow: [
          BoxShadow(
            color: Colors.purple.withOpacity(0.3),
            blurRadius: 12,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Column(
        children: [
          Row(
            children: [
              // Level circle
              Container(
                width: 80,
                height: 80,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  border: Border.all(color: Colors.white, width: 3),
                  gradient: LinearGradient(
                    colors: [Colors.amber, Colors.orange.shade700],
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                  ),
                ),
                child: Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      const Text(
                        'Nivel',
                        style: TextStyle(
                          color: Colors.white70,
                          fontSize: 10,
                        ),
                      ),
                      Text(
                        '${overview.level}',
                        style: const TextStyle(
                          color: Colors.white,
                          fontSize: 28,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(width: 20),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      '${overview.totalXp} XP Total',
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 22,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const SizedBox(height: 8),
                    // Progress to next level
                    ClipRRect(
                      borderRadius: BorderRadius.circular(8),
                      child: LinearProgressIndicator(
                        value: overview.levelProgress,
                        backgroundColor: Colors.white.withOpacity(0.2),
                        valueColor: const AlwaysStoppedAnimation(Colors.white),
                        minHeight: 8,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      '${overview.xpForNextLevel - (overview.totalXp % overview.xpForNextLevel)} XP para nivel ${overview.level + 1}',
                      style: TextStyle(
                        color: Colors.white.withOpacity(0.7),
                        fontSize: 12,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildQuickStats(UserProgressOverview overview) {
    return Row(
      children: [
        Expanded(
          child: _buildStatCard(
            icon: Icons.local_fire_department,
            value: '${overview.currentStreak}',
            label: 'Racha Actual',
            subValue: 'Max: ${overview.maxStreak}',
            color: Colors.orange,
          ),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: _buildStatCard(
            icon: Icons.check_circle,
            value: '${overview.accuracyPercent}%',
            label: 'Precision',
            subValue: '${overview.correctAnswers}/${overview.questionsAnswered}',
            color: Colors.green,
          ),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: _buildStatCard(
            icon: Icons.calendar_today,
            value: '${overview.studyDays}',
            label: 'Dias Estudio',
            subValue: '${overview.totalStudyMinutes ~/ 60}h total',
            color: Colors.blue,
          ),
        ),
      ],
    );
  }

  Widget _buildStatCard({
    required IconData icon,
    required String value,
    required String label,
    required String subValue,
    required Color color,
  }) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: color.withOpacity(0.1),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: color.withOpacity(0.3)),
      ),
      child: Column(
        children: [
          Icon(icon, color: color, size: 28),
          const SizedBox(height: 8),
          Text(
            value,
            style: TextStyle(
              color: color,
              fontWeight: FontWeight.bold,
              fontSize: 22,
            ),
          ),
          Text(
            label,
            style: const TextStyle(
              color: Colors.white70,
              fontSize: 11,
            ),
          ),
          Text(
            subValue,
            style: TextStyle(
              color: Colors.grey[600],
              fontSize: 10,
            ),
          ),
        ],
      ),
    );
  }

  /// Subjects tab with strengths and weaknesses
  Widget _buildSubjectsTab(StatsState state) {
    final subjects = state.subjectProgress;
    final strengths = state.strengths;
    final weaknesses = state.weaknesses;

    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Radar chart
          if (subjects.isNotEmpty) ...[
            const Text(
              'Comparacion con Promedio Nacional',
              style: TextStyle(
                color: Colors.white,
                fontSize: 18,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 8),
            Text(
              'Tu nivel vs el promedio de estudiantes ICFES',
              style: TextStyle(color: Colors.grey[500], fontSize: 13),
            ),
            const SizedBox(height: 16),
            SubjectRadarChart(subjects: subjects),
            const SizedBox(height: 8),
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                _buildLegendItem('Tu nivel', Colors.blue),
                const SizedBox(width: 24),
                _buildLegendItem('Promedio nacional', Colors.grey),
              ],
            ),
            const SizedBox(height: 24),
          ],

          // Weaknesses section (priority)
          if (weaknesses.isNotEmpty) ...[
            Row(
              children: [
                Icon(Icons.trending_down, color: Colors.red[400], size: 20),
                const SizedBox(width: 8),
                const Text(
                  'Materias a Mejorar',
                  style: TextStyle(
                    color: Colors.white,
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 4),
            Text(
              'Enfocate en estas areas para subir tu puntaje',
              style: TextStyle(color: Colors.grey[500], fontSize: 13),
            ),
            const SizedBox(height: 12),
            ...weaknesses.map((subject) => Padding(
              padding: const EdgeInsets.only(bottom: 12),
              child: SubjectMasteryCard(
                subject: subject,
                onTap: () => _showSubjectDetails(subject),
              ),
            )),
            const SizedBox(height: 16),
          ],

          // Strengths section
          if (strengths.isNotEmpty) ...[
            Row(
              children: [
                Icon(Icons.trending_up, color: Colors.green[400], size: 20),
                const SizedBox(width: 8),
                const Text(
                  'Tus Fortalezas',
                  style: TextStyle(
                    color: Colors.white,
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 4),
            Text(
              'Estas por encima del promedio nacional',
              style: TextStyle(color: Colors.grey[500], fontSize: 13),
            ),
            const SizedBox(height: 12),
            ...strengths.map((subject) => Padding(
              padding: const EdgeInsets.only(bottom: 12),
              child: SubjectMasteryCard(
                subject: subject,
                onTap: () => _showSubjectDetails(subject),
              ),
            )),
          ],

          // All subjects
          const SizedBox(height: 16),
          const Text(
            'Todas las Materias',
            style: TextStyle(
              color: Colors.white,
              fontSize: 18,
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 12),
          ...subjects.where((s) => !s.isStrength && !s.isWeakness).map(
            (subject) => Padding(
              padding: const EdgeInsets.only(bottom: 12),
              child: SubjectMasteryCard(
                subject: subject,
                onTap: () => _showSubjectDetails(subject),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildLegendItem(String label, Color color) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Container(
          width: 12,
          height: 12,
          decoration: BoxDecoration(
            color: color,
            shape: BoxShape.circle,
          ),
        ),
        const SizedBox(width: 6),
        Text(
          label,
          style: TextStyle(color: Colors.grey[400], fontSize: 12),
        ),
      ],
    );
  }

  /// Plan tab with study plan progress
  Widget _buildPlanTab(StatsState state) {
    final planProgress = state.studyPlanProgress ?? StudyPlanProgress.empty();

    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Plan progress card
          StudyPlanProgressCard(
            progress: planProgress,
            onViewPlan: () => context.push(AppRoutes.studyPlan),
          ),
          const SizedBox(height: 24),

          // Units progress
          if (planProgress.units.isNotEmpty) ...[
            const Text(
              'Progreso por Unidad',
              style: TextStyle(
                color: Colors.white,
                fontSize: 18,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 12),
            Container(
              decoration: BoxDecoration(
                color: Colors.white.withOpacity(0.03),
                borderRadius: BorderRadius.circular(16),
                border: Border.all(color: Colors.white.withOpacity(0.1)),
              ),
              child: Column(
                children: planProgress.units.map((unit) {
                  return UnitProgressItem(
                    unit: unit,
                    onTap: () {
                      context.push('/study-plan/unit/${unit.unitId}');
                    },
                  );
                }).toList(),
              ),
            ),
          ] else ...[
            // No plan message
            Container(
              padding: const EdgeInsets.all(32),
              decoration: BoxDecoration(
                color: Colors.white.withOpacity(0.03),
                borderRadius: BorderRadius.circular(16),
                border: Border.all(color: Colors.white.withOpacity(0.1)),
              ),
              child: Column(
                children: [
                  Icon(
                    Icons.menu_book_outlined,
                    size: 64,
                    color: Colors.grey[600],
                  ),
                  const SizedBox(height: 16),
                  const Text(
                    'No tienes un plan de estudio activo',
                    style: TextStyle(
                      color: Colors.white,
                      fontSize: 16,
                      fontWeight: FontWeight.bold,
                    ),
                    textAlign: TextAlign.center,
                  ),
                  const SizedBox(height: 8),
                  Text(
                    'Completa el diagnostico para generar tu plan personalizado',
                    style: TextStyle(color: Colors.grey[500], fontSize: 14),
                    textAlign: TextAlign.center,
                  ),
                  const SizedBox(height: 20),
                  ElevatedButton.icon(
                    onPressed: () => context.push(AppRoutes.diagnostic),
                    icon: const Icon(Icons.play_arrow),
                    label: const Text('Iniciar Diagnostico'),
                    style: ElevatedButton.styleFrom(
                      padding: const EdgeInsets.symmetric(
                        horizontal: 24,
                        vertical: 12,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ],
      ),
    );
  }

  void _showSubjectDetails(SubjectProgress subject) {
    showModalBottomSheet(
      context: context,
      backgroundColor: Colors.transparent,
      isScrollControlled: true,
      builder: (context) => _SubjectDetailsModal(subject: subject),
    );
  }
}

class _SubjectDetailsModal extends StatelessWidget {
  final SubjectProgress subject;

  const _SubjectDetailsModal({required this.subject});

  @override
  Widget build(BuildContext context) {
    final color = Color(subject.color);

    return Container(
      margin: const EdgeInsets.all(16),
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        color: const Color(0xFF1A1A1A),
        borderRadius: BorderRadius.circular(24),
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          // Handle
          Container(
            width: 40,
            height: 4,
            decoration: BoxDecoration(
              color: Colors.grey[700],
              borderRadius: BorderRadius.circular(2),
            ),
          ),
          const SizedBox(height: 20),

          // Icon and name
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: color.withOpacity(0.2),
              shape: BoxShape.circle,
            ),
            child: Icon(
              _getSubjectIcon(subject.icon),
              color: color,
              size: 40,
            ),
          ),
          const SizedBox(height: 16),
          Text(
            subject.subjectName,
            style: const TextStyle(
              color: Colors.white,
              fontSize: 22,
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 24),

          // Stats grid
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceAround,
            children: [
              _buildDetailStat(
                'Dominio',
                '${(subject.masteryLevel * 100).toInt()}%',
                color,
              ),
              _buildDetailStat(
                'Precision',
                '${subject.accuracyPercent}%',
                Colors.green,
              ),
              _buildDetailStat(
                'Preguntas',
                '${subject.questionsAnswered}',
                Colors.blue,
              ),
            ],
          ),
          const SizedBox(height: 24),

          // Comparison with national
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: Colors.white.withOpacity(0.05),
              borderRadius: BorderRadius.circular(12),
            ),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Text(
                  'vs Promedio Nacional',
                  style: TextStyle(color: Colors.white70),
                ),
                Text(
                  _getComparisonText(),
                  style: TextStyle(
                    color: _getComparisonColor(),
                    fontWeight: FontWeight.bold,
                    fontSize: 16,
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 24),

          // Topics if available
          if (subject.topics.isNotEmpty) ...[
            const Align(
              alignment: Alignment.centerLeft,
              child: Text(
                'Temas',
                style: TextStyle(
                  color: Colors.white,
                  fontSize: 16,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ),
            const SizedBox(height: 12),
            ...subject.topics.take(5).map((topic) => Padding(
              padding: const EdgeInsets.only(bottom: 8),
              child: Row(
                children: [
                  Expanded(
                    child: Text(
                      topic.topicName,
                      style: const TextStyle(color: Colors.white70),
                    ),
                  ),
                  Text(
                    '${(topic.masteryLevel * 100).toInt()}%',
                    style: TextStyle(
                      color: topic.masteryLevel > 0.6 ? Colors.green : Colors.orange,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ],
              ),
            )),
          ],
        ],
      ),
    );
  }

  Widget _buildDetailStat(String label, String value, Color color) {
    return Column(
      children: [
        Text(
          value,
          style: TextStyle(
            color: color,
            fontSize: 24,
            fontWeight: FontWeight.bold,
          ),
        ),
        Text(
          label,
          style: TextStyle(color: Colors.grey[500], fontSize: 12),
        ),
      ],
    );
  }

  String _getComparisonText() {
    final diff = subject.masteryLevel - subject.nationalAverage;
    if (diff > 0.05) {
      return '+${(diff * 100).toInt()}% arriba';
    } else if (diff < -0.05) {
      return '${(diff * 100).toInt()}% abajo';
    }
    return 'En el promedio';
  }

  Color _getComparisonColor() {
    final diff = subject.masteryLevel - subject.nationalAverage;
    if (diff > 0.05) return Colors.green;
    if (diff < -0.05) return Colors.red;
    return Colors.orange;
  }

  IconData _getSubjectIcon(String icon) {
    switch (icon) {
      case 'calculate':
        return Icons.calculate;
      case 'book':
        return Icons.menu_book;
      case 'public':
        return Icons.public;
      case 'science':
        return Icons.science;
      case 'translate':
        return Icons.translate;
      default:
        return Icons.school;
    }
  }
}
