import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/network/api_client.dart';
import '../../../../core/constants/api_constants.dart';
import '../../data/models/study_plan_models.dart';

/// State class for study plan data
class StudyPlanState {
  final StudyPlanDetail? plan;
  final bool isLoading;
  final String? errorMessage;
  final String? infoMessage;
  final bool hasPlan;

  const StudyPlanState({
    this.plan,
    this.isLoading = false,
    this.errorMessage,
    this.infoMessage,
    this.hasPlan = false,
  });

  StudyPlanState copyWith({
    StudyPlanDetail? plan,
    bool? isLoading,
    String? errorMessage,
    String? infoMessage,
    bool? hasPlan,
    bool clearPlan = false,
    bool clearError = false,
    bool clearInfo = false,
  }) {
    return StudyPlanState(
      plan: clearPlan ? null : plan ?? this.plan,
      isLoading: isLoading ?? this.isLoading,
      errorMessage: clearError ? null : errorMessage ?? this.errorMessage,
      infoMessage: clearInfo ? null : infoMessage ?? this.infoMessage,
      hasPlan: hasPlan ?? this.hasPlan,
    );
  }

  /// Quick access to progress percentage
  double get progressPercentage => plan?.progressPercentage ?? 0.0;

  /// Quick access to current unit
  StudyUnit? get currentUnit => plan?.currentUnit;

  /// Quick access to subject name
  String get subjectName => plan?.subject ?? 'General';

  /// Quick access to plan title
  String get planTitle => plan?.title ?? 'Plan de Estudio';
}

class StudyPlanNotifier extends StateNotifier<StudyPlanState> {
  final ApiClient _apiClient;

  StudyPlanNotifier(this._apiClient) : super(const StudyPlanState(isLoading: true)) {
    fetchCurrentPlan();
  }

  /// Fetch the current active study plan
  Future<void> fetchCurrentPlan() async {
    state = state.copyWith(isLoading: true, clearError: true);

    try {
      final response = await _apiClient.get(ApiConstants.studyPlanCurrent);

      if (response.statusCode == 200 && response.data != null) {
        final data = response.data is Map<String, dynamic>
            ? response.data as Map<String, dynamic>
            : Map<String, dynamic>.from(response.data as Map);
        final currentPlanResponse = CurrentStudyPlanResponse.fromJson(data);

        state = StudyPlanState(
          plan: currentPlanResponse.plan,
          hasPlan: currentPlanResponse.hasPlan,
          infoMessage: currentPlanResponse.message,
          isLoading: false,
        );
      } else {
        state = const StudyPlanState(
          hasPlan: false,
          infoMessage: 'No tienes un plan de estudio activo.',
          isLoading: false,
        );
      }
    } catch (e) {
      debugPrint('Error fetching study plan: $e');

      // Handle 404 as valid "no plan" state
      // Check for string "404" or Dio exception status code
      bool is404 = e.toString().contains('404');
      // If we had access to Dio types we would check e.response?.statusCode
      
      if (is404) {
        state = const StudyPlanState(
          hasPlan: false,
          infoMessage: 'Completa el diagnostico para obtener tu plan personalizado.',
          isLoading: false,
        );
      } else {
        state = StudyPlanState(
          hasPlan: false,
          errorMessage: 'Error al cargar el plan de estudio. Intenta de nuevo.',
          isLoading: false,
        );
      }
    }
  }

  /// Fetch a specific study plan by ID
  Future<void> fetchPlanById(String planId) async {
    state = state.copyWith(isLoading: true, clearError: true);

    try {
      final response = await _apiClient.get('${ApiConstants.studyPlanCurrent.replaceFirst('/current', '')}/$planId');

      if (response.statusCode == 200 && response.data != null) {
        final planData = response.data is Map<String, dynamic>
            ? response.data as Map<String, dynamic>
            : Map<String, dynamic>.from(response.data as Map);
        final plan = StudyPlanDetail.fromJson(planData);
        state = StudyPlanState(
          plan: plan,
          hasPlan: true,
          isLoading: false,
        );
      } else {
        state = state.copyWith(
          isLoading: false,
          errorMessage: 'Plan de estudio no encontrado.',
        );
      }
    } catch (e) {
      debugPrint('Error fetching plan by ID: $e');
      state = state.copyWith(
        isLoading: false,
        errorMessage: 'Error al cargar el plan de estudio.',
      );
    }
  }

  /// Update progress for a specific unit
  Future<bool> updateUnitProgress({
    required String planId,
    required int unitNumber,
    int? videosCompleted,
    int? exercisesCompleted,
    double? score,
  }) async {
    try {
      final response = await _apiClient.post(
        '/study-plans/$planId/units/$unitNumber/progress',
        data: {
          if (videosCompleted != null) 'videos_completed': videosCompleted,
          if (exercisesCompleted != null) 'exercises_completed': exercisesCompleted,
          if (score != null) 'score': score,
        },
      );

      if (response.statusCode == 200) {
        // Refresh the plan to get updated progress
        await fetchCurrentPlan();
        return true;
      }
      return false;
    } catch (e) {
      debugPrint('Error updating unit progress: $e');
      return false;
    }
  }

  /// Generate a new study plan for a subject
  Future<bool> generatePlan(String subjectId, {bool useDiagnostic = true}) async {
    state = state.copyWith(isLoading: true, clearError: true);

    try {
      final response = await _apiClient.post(
        '/study-plans/generate-adaptive',
        data: {
          'subject_id': subjectId,
          'use_diagnostic': useDiagnostic,
        },
      );

      if (response.statusCode == 200 && response.data != null) {
        final genData = response.data is Map<String, dynamic>
            ? response.data as Map<String, dynamic>
            : Map<String, dynamic>.from(response.data as Map);
        final plan = StudyPlanDetail.fromJson(genData);
        state = StudyPlanState(
          plan: plan,
          hasPlan: true,
          isLoading: false,
        );
        return true;
      }

      state = state.copyWith(
        isLoading: false,
        errorMessage: 'No se pudo generar el plan de estudio.',
      );
      return false;
    } catch (e) {
      debugPrint('Error generating study plan: $e');
      state = state.copyWith(
        isLoading: false,
        errorMessage: 'Error al generar el plan de estudio.',
      );
      return false;
    }
  }

  /// Clear any error messages
  void clearError() {
    state = state.copyWith(clearError: true);
  }

  /// Refresh the current plan
  Future<void> refresh() async {
    await fetchCurrentPlan();
  }
}

/// Main provider for study plan state
final studyPlanProvider = StateNotifierProvider<StudyPlanNotifier, StudyPlanState>((ref) {
  final apiClient = ref.watch(apiClientProvider);
  return StudyPlanNotifier(apiClient);
});

/// Derived provider for quick progress access (for widgets like ContinueStudyingCard)
final studyPlanProgressProvider = Provider<double>((ref) {
  return ref.watch(studyPlanProvider).progressPercentage / 100;
});

/// Derived provider for checking if user has a plan
final hasStudyPlanProvider = Provider<bool>((ref) {
  return ref.watch(studyPlanProvider).hasPlan;
});

/// Derived provider for current unit
final currentUnitProvider = Provider<StudyUnit?>((ref) {
  return ref.watch(studyPlanProvider).currentUnit;
});

/// Legacy provider for backwards compatibility with existing widgets
class StudyPlanProgress {
  final String subjectName;
  final double progress;
  final String currentUnit;
  final String planId;

  StudyPlanProgress({
    required this.subjectName,
    required this.progress,
    required this.currentUnit,
    required this.planId,
  });
}

/// Legacy async provider for ContinueStudyingCard compatibility
final legacyStudyPlanProvider = Provider<AsyncValue<StudyPlanProgress?>>((ref) {
  final state = ref.watch(studyPlanProvider);

  if (state.isLoading) {
    return const AsyncValue.loading();
  }

  if (state.errorMessage != null) {
    return AsyncValue.error(state.errorMessage!, StackTrace.current);
  }

  if (!state.hasPlan || state.plan == null) {
    return const AsyncValue.data(null);
  }

  return AsyncValue.data(StudyPlanProgress(
    subjectName: state.plan!.subject,
    progress: state.plan!.progressPercentage / 100,
    currentUnit: state.currentUnit?.name ?? 'Unidad 1',
    planId: state.plan!.id,
  ));
});
