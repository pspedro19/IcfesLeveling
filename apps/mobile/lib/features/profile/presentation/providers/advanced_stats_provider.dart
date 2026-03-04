import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/network/api_client.dart';
import '../widgets/activity_heatmap.dart';
import '../../../mastery/presentation/widgets/national_comparison_radar.dart';
import '../../../mastery/presentation/widgets/visual_skill_tree.dart';

/// State class for advanced stats
class AdvancedStatsState {
  final bool isLoading;
  final String? error;

  // Heatmap data
  final Map<String, HeatmapDay>? heatmapData;
  final HeatmapStats? heatmapStats;

  // National comparison data
  final List<SubjectComparison>? nationalComparison;
  final OverallComparison? overallComparison;

  // Skill tree data
  final SkillTreeData? skillTreeData;

  // Psychological triggers data
  final Map<String, dynamic>? triggersData;

  const AdvancedStatsState({
    this.isLoading = false,
    this.error,
    this.heatmapData,
    this.heatmapStats,
    this.nationalComparison,
    this.overallComparison,
    this.skillTreeData,
    this.triggersData,
  });

  AdvancedStatsState copyWith({
    bool? isLoading,
    String? error,
    bool clearError = false,
    Map<String, HeatmapDay>? heatmapData,
    HeatmapStats? heatmapStats,
    List<SubjectComparison>? nationalComparison,
    OverallComparison? overallComparison,
    SkillTreeData? skillTreeData,
    Map<String, dynamic>? triggersData,
  }) {
    return AdvancedStatsState(
      isLoading: isLoading ?? this.isLoading,
      error: clearError ? null : error ?? this.error,
      heatmapData: heatmapData ?? this.heatmapData,
      heatmapStats: heatmapStats ?? this.heatmapStats,
      nationalComparison: nationalComparison ?? this.nationalComparison,
      overallComparison: overallComparison ?? this.overallComparison,
      skillTreeData: skillTreeData ?? this.skillTreeData,
      triggersData: triggersData ?? this.triggersData,
    );
  }
}


/// Provider for advanced statistics
class AdvancedStatsNotifier extends StateNotifier<AdvancedStatsState> {
  final ApiClient _apiClient;

  AdvancedStatsNotifier(this._apiClient) : super(const AdvancedStatsState());

  /// Fetch activity heatmap data
  Future<void> fetchHeatmap({int days = 365}) async {
    state = state.copyWith(isLoading: true, clearError: true);

    try {
      final response = await _apiClient.get('/stats/heatmap', queryParameters: {
        'days': days,
      });

      if (response.statusCode == 200 && response.data != null) {
        final data = response.data as Map<String, dynamic>;

        // Parse heatmap data
        final heatmapJson = data['heatmap'] as Map<String, dynamic>? ?? {};
        final heatmapData = <String, HeatmapDay>{};

        heatmapJson.forEach((key, value) {
          if (value is Map<String, dynamic>) {
            heatmapData[key] = HeatmapDay.fromJson(value);
          }
        });

        // Parse stats
        final statsJson = data['stats'] as Map<String, dynamic>?;
        final stats = statsJson != null ? HeatmapStats.fromJson(statsJson) : null;

        state = state.copyWith(
          isLoading: false,
          heatmapData: heatmapData,
          heatmapStats: stats,
        );
      } else {
        state = state.copyWith(
          isLoading: false,
          error: 'Error al cargar heatmap',
        );
      }
    } catch (e) {
      state = state.copyWith(
        isLoading: false,
        error: e.toString(),
      );
    }
  }

  /// Fetch national comparison data
  Future<void> fetchNationalComparison() async {
    state = state.copyWith(isLoading: true, clearError: true);

    try {
      final response = await _apiClient.get('/stats/national-comparison');

      if (response.statusCode == 200 && response.data != null) {
        final data = response.data as Map<String, dynamic>;

        // Parse subjects
        final subjectsJson = data['subjects'] as List? ?? [];
        final subjects = subjectsJson
            .map((s) => SubjectComparison.fromJson(s as Map<String, dynamic>))
            .toList();

        // Parse overall
        final overallJson = data['overall'] as Map<String, dynamic>?;
        final overall = overallJson != null
            ? OverallComparison.fromJson(overallJson)
            : null;

        state = state.copyWith(
          isLoading: false,
          nationalComparison: subjects,
          overallComparison: overall,
        );
      } else {
        state = state.copyWith(
          isLoading: false,
          error: 'Error al cargar comparacion nacional',
        );
      }
    } catch (e) {
      state = state.copyWith(
        isLoading: false,
        error: e.toString(),
      );
    }
  }

  /// Fetch skill tree data
  Future<void> fetchSkillTree({String? subjectId}) async {
    state = state.copyWith(isLoading: true, clearError: true);

    try {
      final response = await _apiClient.get('/stats/skill-tree', queryParameters: {
        if (subjectId != null) 'subject_id': subjectId,
      });

      if (response.statusCode == 200 && response.data != null) {
        final data = response.data as Map<String, dynamic>;
        final skillTree = SkillTreeData.fromJson(data);

        state = state.copyWith(
          isLoading: false,
          skillTreeData: skillTree,
        );
      } else {
        state = state.copyWith(
          isLoading: false,
          error: 'Error al cargar arbol de maestria',
        );
      }
    } catch (e) {
      state = state.copyWith(
        isLoading: false,
        error: e.toString(),
      );
    }
  }

  /// Fetch psychological triggers
  Future<void> fetchTriggers() async {
    state = state.copyWith(isLoading: true, clearError: true);

    try {
      final response = await _apiClient.get('/stats/triggers');

      if (response.statusCode == 200 && response.data != null) {
        state = state.copyWith(
          isLoading: false,
          triggersData: response.data as Map<String, dynamic>,
        );
      } else {
        state = state.copyWith(
          isLoading: false,
          error: 'Error al cargar triggers',
        );
      }
    } catch (e) {
      state = state.copyWith(
        isLoading: false,
        error: e.toString(),
      );
    }
  }

  /// Fetch all advanced stats data
  Future<void> fetchAll() async {
    state = state.copyWith(isLoading: true, clearError: true);

    try {
      await Future.wait([
        fetchHeatmap(),
        fetchNationalComparison(),
        fetchSkillTree(),
        fetchTriggers(),
      ]);
    } catch (e) {
      state = state.copyWith(
        isLoading: false,
        error: e.toString(),
      );
    }
  }

  /// Apply variable reward
  Future<Map<String, dynamic>?> applyVariableReward({
    required String actionType,
    required int baseReward,
  }) async {
    try {
      final response = await _apiClient.post(
        '/stats/triggers/variable-reward',
        queryParameters: {
          'action_type': actionType,
          'base_reward': baseReward,
        },
      );

      if (response.statusCode == 200 && response.data != null) {
        return response.data as Map<String, dynamic>;
      }
    } catch (e) {
      // Silent fail for rewards
    }
    return null;
  }
}


/// Main provider
final advancedStatsProvider = StateNotifierProvider<AdvancedStatsNotifier, AdvancedStatsState>((ref) {
  final apiClient = ref.watch(apiClientProvider);
  return AdvancedStatsNotifier(apiClient);
});


/// Derived provider for heatmap only
final heatmapProvider = Provider<Map<String, HeatmapDay>?>((ref) {
  return ref.watch(advancedStatsProvider).heatmapData;
});


/// Derived provider for heatmap stats
final heatmapStatsProvider = Provider<HeatmapStats?>((ref) {
  return ref.watch(advancedStatsProvider).heatmapStats;
});


/// Derived provider for national comparison
final nationalComparisonProvider = Provider<List<SubjectComparison>?>((ref) {
  return ref.watch(advancedStatsProvider).nationalComparison;
});


/// Derived provider for skill tree
final skillTreeProvider = Provider<SkillTreeData?>((ref) {
  return ref.watch(advancedStatsProvider).skillTreeData;
});


/// Derived provider for triggers
final triggersProvider = Provider<Map<String, dynamic>?>((ref) {
  return ref.watch(advancedStatsProvider).triggersData;
});
