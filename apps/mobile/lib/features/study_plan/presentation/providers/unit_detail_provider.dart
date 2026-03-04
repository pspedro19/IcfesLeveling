import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../data/repositories/unit_repository.dart';
import '../../domain/entities/unit_detail.dart';

/// State for unit detail page
class UnitDetailState {
  final UnitDetail? unit;
  final bool isLoading;
  final String? error;
  final bool isUpdatingProgress;

  const UnitDetailState({
    this.unit,
    this.isLoading = false,
    this.error,
    this.isUpdatingProgress = false,
  });

  UnitDetailState copyWith({
    UnitDetail? unit,
    bool? isLoading,
    String? error,
    bool? isUpdatingProgress,
  }) {
    return UnitDetailState(
      unit: unit ?? this.unit,
      isLoading: isLoading ?? this.isLoading,
      error: error,
      isUpdatingProgress: isUpdatingProgress ?? this.isUpdatingProgress,
    );
  }

  /// Calculate weighted overall progress
  double get overallProgress => unit?.overallProgress ?? 0;

  /// Videos progress percentage
  double get videosProgress {
    if (unit == null) return 0;
    final total = unit!.videos.length;
    if (total == 0) return 100;
    final watched = unit!.videos.where((v) => v.isWatched).length;
    return (watched / total) * 100;
  }

  /// Exercises progress percentage
  double get exercisesProgress {
    if (unit == null) return 0;
    final total = unit!.exercises.length;
    if (total == 0) return 100;
    final completed = unit!.exercises.where((e) => e.isCompleted).length;
    return (completed / total) * 100;
  }

  /// Readings progress percentage
  double get readingsProgress {
    if (unit == null) return 0;
    final total = unit!.readings.length;
    if (total == 0) return 100;
    final completed = unit!.readings.where((r) => r.isCompleted).length;
    return (completed / total) * 100;
  }
}

/// Notifier for managing unit detail state
class UnitDetailNotifier extends StateNotifier<UnitDetailState> {
  final UnitRepository _repository;
  final String unitId;

  UnitDetailNotifier(this._repository, this.unitId)
      : super(const UnitDetailState(isLoading: true)) {
    loadUnit();
  }

  /// Load unit details from repository
  Future<void> loadUnit() async {
    state = state.copyWith(isLoading: true, error: null);

    try {
      final unit = await _repository.getUnitDetail(unitId);
      state = state.copyWith(unit: unit, isLoading: false);
    } catch (e) {
      state = state.copyWith(
        isLoading: false,
        error: 'Error cargando la unidad: ${e.toString()}',
      );
    }
  }

  /// Mark a video as watched and update progress
  Future<void> markVideoWatched(String videoId) async {
    if (state.unit == null) return;

    state = state.copyWith(isUpdatingProgress: true);

    try {
      // Update local state immediately for responsive UI
      final updatedVideos = state.unit!.videos.map((video) {
        if (video.id == videoId) {
          return video.copyWith(isWatched: true, watchProgress: 100);
        }
        return video;
      }).toList();

      final watchedCount = updatedVideos.where((v) => v.isWatched).length;

      // Update weighted progress
      final newWeightedProgress = WeightedProgress(
        videos: ContentProgress(
          completed: watchedCount,
          total: updatedVideos.length,
          weight: state.unit!.weightedProgress.videos.weight,
        ),
        exercises: state.unit!.weightedProgress.exercises,
        readings: state.unit!.weightedProgress.readings,
      );

      state = state.copyWith(
        unit: state.unit!.copyWith(
          videos: updatedVideos,
          weightedProgress: newWeightedProgress,
        ),
        isUpdatingProgress: false,
      );

      // Sync with backend
      await _repository.updateUnitProgress(
        unitId: unitId,
        contentType: 'videos',
        completed: watchedCount,
        total: updatedVideos.length,
      );
    } catch (e) {
      state = state.copyWith(isUpdatingProgress: false);
    }
  }

  /// Mark an exercise as completed
  Future<void> markExerciseCompleted(String exerciseId, double score) async {
    if (state.unit == null) return;

    state = state.copyWith(isUpdatingProgress: true);

    try {
      final updatedExercises = state.unit!.exercises.map((exercise) {
        if (exercise.id == exerciseId) {
          return UnitExercise(
            id: exercise.id,
            title: exercise.title,
            description: exercise.description,
            questionCount: exercise.questionCount,
            completedQuestions: exercise.questionCount,
            score: score,
            difficulty: exercise.difficulty,
            topics: exercise.topics,
            isCompleted: true,
          );
        }
        return exercise;
      }).toList();

      final completedCount = updatedExercises.where((e) => e.isCompleted).length;

      final newWeightedProgress = WeightedProgress(
        videos: state.unit!.weightedProgress.videos,
        exercises: ContentProgress(
          completed: completedCount,
          total: updatedExercises.length,
          weight: state.unit!.weightedProgress.exercises.weight,
        ),
        readings: state.unit!.weightedProgress.readings,
      );

      state = state.copyWith(
        unit: state.unit!.copyWith(
          exercises: updatedExercises,
          weightedProgress: newWeightedProgress,
        ),
        isUpdatingProgress: false,
      );

      await _repository.updateUnitProgress(
        unitId: unitId,
        contentType: 'exercises',
        completed: completedCount,
        total: updatedExercises.length,
      );
    } catch (e) {
      state = state.copyWith(isUpdatingProgress: false);
    }
  }

  /// Mark a reading as completed
  Future<void> markReadingCompleted(String readingId) async {
    if (state.unit == null) return;

    state = state.copyWith(isUpdatingProgress: true);

    try {
      final updatedReadings = state.unit!.readings.map((reading) {
        if (reading.id == readingId) {
          return UnitReading(
            id: reading.id,
            title: reading.title,
            content: reading.content,
            url: reading.url,
            estimatedMinutes: reading.estimatedMinutes,
            isCompleted: true,
            thumbnailUrl: reading.thumbnailUrl,
          );
        }
        return reading;
      }).toList();

      final completedCount = updatedReadings.where((r) => r.isCompleted).length;

      final newWeightedProgress = WeightedProgress(
        videos: state.unit!.weightedProgress.videos,
        exercises: state.unit!.weightedProgress.exercises,
        readings: ContentProgress(
          completed: completedCount,
          total: updatedReadings.length,
          weight: state.unit!.weightedProgress.readings.weight,
        ),
      );

      state = state.copyWith(
        unit: state.unit!.copyWith(
          readings: updatedReadings,
          weightedProgress: newWeightedProgress,
        ),
        isUpdatingProgress: false,
      );

      await _repository.updateUnitProgress(
        unitId: unitId,
        contentType: 'readings',
        completed: completedCount,
        total: updatedReadings.length,
      );
    } catch (e) {
      state = state.copyWith(isUpdatingProgress: false);
    }
  }

  /// Refresh unit data from server
  Future<void> refresh() => loadUnit();
}

/// Provider family for unit detail - each unit gets its own provider instance
final unitDetailProvider = StateNotifierProvider.family<UnitDetailNotifier, UnitDetailState, String>(
  (ref, unitId) {
    final repository = ref.watch(unitRepositoryProvider);
    return UnitDetailNotifier(repository, unitId);
  },
);

/// Provider for checking if a unit is fully completed
final isUnitCompletedProvider = Provider.family<bool, String>((ref, unitId) {
  final state = ref.watch(unitDetailProvider(unitId));
  return state.overallProgress >= 100;
});

/// Provider for unit overall progress
final unitProgressProvider = Provider.family<double, String>((ref, unitId) {
  final state = ref.watch(unitDetailProvider(unitId));
  return state.overallProgress;
});
