import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/network/api_client.dart';
import '../../data/models/stats_models.dart';
import '../../../profile/presentation/widgets/activity_heatmap.dart';

/// State for statistics feature
class StatsState {
  final bool isLoading;
  final String? error;
  final UserProgressOverview? overview;
  final List<SubjectProgress> subjectProgress;
  final StudyPlanProgress? studyPlanProgress;
  final List<RecentActivity> recentActivities;
  final WeeklyPerformance? weeklyPerformance;
  final Map<String, HeatmapDay>? heatmapData;
  final HeatmapStats? heatmapStats;

  const StatsState({
    this.isLoading = false,
    this.error,
    this.overview,
    this.subjectProgress = const [],
    this.studyPlanProgress,
    this.recentActivities = const [],
    this.weeklyPerformance,
    this.heatmapData,
    this.heatmapStats,
  });

  List<SubjectProgress> get strengths =>
      subjectProgress.where((s) => s.isStrength).toList();

  List<SubjectProgress> get weaknesses =>
      subjectProgress.where((s) => s.isWeakness).toList();

  bool get hasCompletedPlan =>
      studyPlanProgress?.isCompleted ?? false;

  StatsState copyWith({
    bool? isLoading,
    String? error,
    bool clearError = false,
    UserProgressOverview? overview,
    List<SubjectProgress>? subjectProgress,
    StudyPlanProgress? studyPlanProgress,
    List<RecentActivity>? recentActivities,
    WeeklyPerformance? weeklyPerformance,
    Map<String, HeatmapDay>? heatmapData,
    HeatmapStats? heatmapStats,
  }) {
    return StatsState(
      isLoading: isLoading ?? this.isLoading,
      error: clearError ? null : (error ?? this.error),
      overview: overview ?? this.overview,
      subjectProgress: subjectProgress ?? this.subjectProgress,
      studyPlanProgress: studyPlanProgress ?? this.studyPlanProgress,
      recentActivities: recentActivities ?? this.recentActivities,
      weeklyPerformance: weeklyPerformance ?? this.weeklyPerformance,
      heatmapData: heatmapData ?? this.heatmapData,
      heatmapStats: heatmapStats ?? this.heatmapStats,
    );
  }
}

/// Notifier for stats state management
class StatsNotifier extends StateNotifier<StatsState> {
  final ApiClient _apiClient;

  StatsNotifier(this._apiClient) : super(const StatsState());

  /// Load all statistics
  Future<void> loadAllStats() async {
    state = state.copyWith(isLoading: true, clearError: true);

    try {
      await Future.wait([
        _loadOverview(),
        _loadSubjectProgress(),
        _loadStudyPlanProgress(),
        _loadRecentActivities(),
        _loadWeeklyPerformance(),
        _loadHeatmap(),
      ]);

      state = state.copyWith(isLoading: false);
    } catch (e) {
      state = state.copyWith(
        isLoading: false,
        error: 'Error cargando estadisticas: $e',
      );
    }
  }

  Future<void> _loadOverview() async {
    try {
      final response = await _apiClient.get('/users/cached/profile/me');
      if (response.statusCode == 200 && response.data != null) {
        final overview = UserProgressOverview.fromJson(response.data);
        state = state.copyWith(overview: overview);
      }
    } catch (e) {
      // Use empty overview on error
      state = state.copyWith(overview: UserProgressOverview.empty());
    }
  }

  Future<void> _loadSubjectProgress() async {
    try {
      final response = await _apiClient.get('/mastery/subjects');
      if (response.statusCode == 200 && response.data != null) {
        final subjects = (response.data['subjects'] as List? ?? [])
            .map((s) => SubjectProgress.fromJson(s))
            .toList();
        state = state.copyWith(subjectProgress: subjects);
      }
    } catch (e) {
      // Return empty list on error — no mock data
      state = state.copyWith(subjectProgress: []);
    }
  }

  Future<void> _loadStudyPlanProgress() async {
    try {
      final response = await _apiClient.get('/study-plans/current/progress');
      if (response.statusCode == 200 && response.data != null) {
        final progress = StudyPlanProgress.fromJson(response.data);
        state = state.copyWith(studyPlanProgress: progress);
      }
    } catch (e) {
      state = state.copyWith(studyPlanProgress: StudyPlanProgress.empty());
    }
  }

  Future<void> _loadRecentActivities() async {
    try {
      final response = await _apiClient.get('/stats/recent-activities',
        queryParameters: {'limit': 10});
      if (response.statusCode == 200 && response.data != null) {
        final activities = (response.data['activities'] as List? ?? [])
            .map((a) => RecentActivity.fromJson(a))
            .toList();
        state = state.copyWith(recentActivities: activities);
      }
    } catch (e) {
      state = state.copyWith(recentActivities: []);
    }
  }

  Future<void> _loadWeeklyPerformance() async {
    try {
      final response = await _apiClient.get('/stats/weekly');
      if (response.statusCode == 200 && response.data != null) {
        final weekly = WeeklyPerformance.fromJson(response.data);
        state = state.copyWith(weeklyPerformance: weekly);
      }
    } catch (e) {
      state = state.copyWith(weeklyPerformance: WeeklyPerformance.empty());
    }
  }

  Future<void> _loadHeatmap() async {
    try {
      final response = await _apiClient.get('/stats/heatmap',
        queryParameters: {'days': 365});
      if (response.statusCode == 200 && response.data != null) {
        final data = response.data as Map<String, dynamic>;

        final heatmapJson = data['heatmap'] as Map<String, dynamic>? ?? {};
        final heatmapData = <String, HeatmapDay>{};

        heatmapJson.forEach((key, value) {
          if (value is Map<String, dynamic>) {
            heatmapData[key] = HeatmapDay.fromJson(value);
          }
        });

        final statsJson = data['stats'] as Map<String, dynamic>?;
        final stats = statsJson != null ? HeatmapStats.fromJson(statsJson) : null;

        state = state.copyWith(
          heatmapData: heatmapData,
          heatmapStats: stats,
        );
      }
    } catch (e) {
      // Silent fail - heatmap is optional
    }
  }

  /// Refresh all data
  Future<void> refresh() async {
    await loadAllStats();
  }

  /// Get mock subject progress for testing
  List<SubjectProgress> _getMockSubjectProgress() {
    return [
      SubjectProgress(
        subjectId: 'matematicas',
        subjectName: 'Matematicas',
        icon: 'calculate',
        color: 0xFF4CAF50,
        masteryLevel: 0.65,
        questionsAnswered: 120,
        correctAnswers: 78,
        totalQuestions: 500,
        nationalAverage: 0.55,
        strengthLevel: 'strong',
      ),
      SubjectProgress(
        subjectId: 'lectura',
        subjectName: 'Lectura Critica',
        icon: 'book',
        color: 0xFF2196F3,
        masteryLevel: 0.45,
        questionsAnswered: 80,
        correctAnswers: 36,
        totalQuestions: 400,
        nationalAverage: 0.50,
        strengthLevel: 'weak',
      ),
      SubjectProgress(
        subjectId: 'sociales',
        subjectName: 'Sociales y Ciudadanas',
        icon: 'public',
        color: 0xFFFF9800,
        masteryLevel: 0.55,
        questionsAnswered: 90,
        correctAnswers: 50,
        totalQuestions: 350,
        nationalAverage: 0.52,
        strengthLevel: 'average',
      ),
      SubjectProgress(
        subjectId: 'naturales',
        subjectName: 'Ciencias Naturales',
        icon: 'science',
        color: 0xFF9C27B0,
        masteryLevel: 0.40,
        questionsAnswered: 60,
        correctAnswers: 24,
        totalQuestions: 400,
        nationalAverage: 0.48,
        strengthLevel: 'weak',
      ),
      SubjectProgress(
        subjectId: 'ingles',
        subjectName: 'Ingles',
        icon: 'translate',
        color: 0xFFE91E63,
        masteryLevel: 0.70,
        questionsAnswered: 100,
        correctAnswers: 70,
        totalQuestions: 300,
        nationalAverage: 0.45,
        strengthLevel: 'strong',
      ),
    ];
  }
}

// ==================== PROVIDERS ====================

/// Main stats provider
final statsProvider = StateNotifierProvider<StatsNotifier, StatsState>((ref) {
  final apiClient = ref.watch(apiClientProvider);
  return StatsNotifier(apiClient);
});

/// Provider for user overview
final userOverviewProvider = Provider<UserProgressOverview?>((ref) {
  return ref.watch(statsProvider).overview;
});

/// Provider for subject progress
final subjectProgressProvider = Provider<List<SubjectProgress>>((ref) {
  return ref.watch(statsProvider).subjectProgress;
});

/// Provider for strengths
final strengthsProvider = Provider<List<SubjectProgress>>((ref) {
  return ref.watch(statsProvider).strengths;
});

/// Provider for weaknesses
final weaknessesProvider = Provider<List<SubjectProgress>>((ref) {
  return ref.watch(statsProvider).weaknesses;
});

/// Provider for study plan progress
final studyPlanProgressProvider = Provider<StudyPlanProgress?>((ref) {
  return ref.watch(statsProvider).studyPlanProgress;
});

/// Provider for weekly performance
final weeklyPerformanceProvider = Provider<WeeklyPerformance?>((ref) {
  return ref.watch(statsProvider).weeklyPerformance;
});
