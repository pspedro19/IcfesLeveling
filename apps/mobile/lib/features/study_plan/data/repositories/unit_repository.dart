import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/network/api_client.dart';
import '../../../../core/constants/api_constants.dart';
import '../../domain/entities/unit_detail.dart';

/// Repository for fetching and updating unit details
class UnitRepository {
  final ApiClient _apiClient;

  UnitRepository(this._apiClient);

  /// Fetch detailed information for a specific unit
  ///
  /// [unitId] can be in format "planId_unitNumber" or just "unitId"
  Future<UnitDetail> getUnitDetail(String unitId) async {
    try {
      // Parse unitId - it might be "planId_unitNumber" format
      final parts = unitId.split('_');
      String planId;
      int unitNumber;

      if (parts.length >= 2) {
        planId = parts[0];
        unitNumber = int.tryParse(parts[1]) ?? 1;
      } else {
        // Fallback: treat as planId and get unit 1
        planId = unitId;
        unitNumber = 1;
      }

      // Try to fetch from the study plan endpoint
      final response = await _apiClient.get(
        '${ApiConstants.studyPlanCurrent.replaceFirst('/current', '')}/$planId',
      );

      if (response.statusCode == 200 && response.data != null) {
        final planData = response.data as Map<String, dynamic>;
        final units = planData['units'] as List<dynamic>? ?? [];

        // Find the specific unit
        final unitData = units.firstWhere(
          (u) => (u['unit_number'] ?? u['unitNumber']) == unitNumber,
          orElse: () => null,
        );

        if (unitData != null) {
          return _parseUnitFromPlanData(planId, unitData, planData);
        }
      }

      // No unit found for this plan
      throw Exception('Unit not found for id: $unitId');
    } catch (e) {
      rethrow;
    }
  }

  /// Parse unit data from plan response
  UnitDetail _parseUnitFromPlanData(
    String planId,
    Map<String, dynamic> unitData,
    Map<String, dynamic> planData,
  ) {
    final unitNumber = unitData['unit_number'] ?? unitData['unitNumber'] ?? 1;
    final unitContent = unitData['unit_content'] ?? unitData['content'] ?? {};

    // Parse videos
    final videosData = unitContent['videos'] as List<dynamic>? ??
                       unitData['videos'] as List<dynamic>? ?? [];
    final videos = videosData.map((v) => UnitVideo.fromJson(v)).toList();

    // Parse exercises - generate from topics if not present
    List<UnitExercise> exercises = [];
    final exercisesData = unitContent['exercises'] as List<dynamic>? ??
                          unitData['exercises'] as List<dynamic>?;
    if (exercisesData != null) {
      exercises = exercisesData.map((e) => UnitExercise.fromJson(e)).toList();
    } else {
      // Generate exercises from topics
      final topics = unitData['topics'] as List<dynamic>? ?? [];
      exercises = [
        UnitExercise(
          id: '${planId}_${unitNumber}_quiz',
          title: 'Quiz de la Unidad ${unitNumber}',
          description: 'Evalua tu comprension de los temas de esta unidad',
          questionCount: topics.length * 3 + 5,
          difficulty: 'medium',
          topics: topics.map((t) => t['name']?.toString() ?? '').toList(),
        ),
      ];
    }

    // Parse readings
    final readingsData = unitContent['readings'] as List<dynamic>? ??
                         unitData['readings'] as List<dynamic>? ?? [];
    final readings = readingsData.map((r) => UnitReading.fromJson(r)).toList();

    // Parse weighted progress
    final weightedProgressData = unitData['weighted_progress'] ??
                                  unitData['weightedProgress'] ?? {};
    final weightedProgress = WeightedProgress.fromJson({
      'videos': {
        'completed': videos.where((v) => v.isWatched).length,
        'total': videos.length,
        'weight': 0.3,
      },
      'exercises': {
        'completed': exercises.where((e) => e.isCompleted).length,
        'total': exercises.length,
        'weight': 0.5,
      },
      'readings': {
        'completed': readings.where((r) => r.isCompleted).length,
        'total': readings.length,
        'weight': 0.2,
      },
      ...weightedProgressData,
    });

    // Get recommendations
    final recommendations = unitData['recommendations'] ?? {};

    return UnitDetail(
      id: '${planId}_$unitNumber',
      planId: planId,
      unitNumber: unitNumber,
      name: unitData['name'] ?? unitData['unit_name'] ?? 'Unidad $unitNumber',
      description: unitData['description'] ?? unitData['unit_description'] ?? '',
      videos: videos,
      exercises: exercises,
      readings: readings,
      weightedProgress: weightedProgress,
      isUnlocked: unitData['unlocked'] ?? unitData['is_unlocked'] ?? true,
      isCompleted: unitData['is_completed'] ?? false,
      score: (unitData['score'] ?? unitData['progress'] ?? 0.0).toDouble(),
      focusTopics: List<String>.from(recommendations['focus_topics'] ?? []),
      weakAreas: List<String>.from(recommendations['weak_areas'] ?? []),
      recommendedPriority: recommendations['priority'],
      estimatedTime: recommendations['study_time'] ?? unitData['estimated_time'],
    );
  }

  /// Update progress for a specific content type in a unit
  Future<bool> updateUnitProgress({
    required String unitId,
    required String contentType,
    required int completed,
    required int total,
  }) async {
    try {
      final parts = unitId.split('_');
      if (parts.length < 2) return false;

      final planId = parts[0];
      final unitNumber = int.tryParse(parts[1]) ?? 1;

      final response = await _apiClient.post(
        '${ApiConstants.studyPlanCurrent.replaceFirst('/current', '')}/plans/$planId/weighted-progress',
        data: {
          'unit_number': unitNumber,
          'component_type': contentType,
          'completed': completed,
          'total': total,
        },
      );

      return response.statusCode == 200;
    } catch (e) {
      // Silently fail for now - progress will sync later
      return false;
    }
  }

  /// Mark a video as watched
  Future<bool> markVideoWatched(String unitId, String videoId) async {
    try {
      // For now, just update the weighted progress
      // A dedicated endpoint could be added later
      return true;
    } catch (e) {
      return false;
    }
  }

  /// Mark an exercise as completed
  Future<bool> markExerciseCompleted(String unitId, String exerciseId, double score) async {
    try {
      return true;
    } catch (e) {
      return false;
    }
  }

  /// Mark a reading as completed
  Future<bool> markReadingCompleted(String unitId, String readingId) async {
    try {
      return true;
    } catch (e) {
      return false;
    }
  }

  /// Generate mock data for development/fallback
  UnitDetail _getMockUnitDetail(String unitId) {
    final parts = unitId.split('_');
    final unitNumber = parts.length >= 2 ? int.tryParse(parts[1]) ?? 1 : 1;

    return UnitDetail(
      id: unitId,
      planId: parts.isNotEmpty ? parts[0] : 'mock_plan',
      unitNumber: unitNumber,
      name: 'Unidad $unitNumber: Fundamentos',
      description: 'En esta unidad aprenderas los conceptos fundamentales necesarios para dominar este tema.',
      videos: [
        UnitVideo(
          id: 'video_1',
          title: 'Introduccion al tema',
          youtubeId: 'dQw4w9WgXcQ',
          youtubeUrl: 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
          durationSeconds: 720,
          channelName: 'ICFES Academy',
          thumbnailUrl: 'https://img.youtube.com/vi/dQw4w9WgXcQ/mqdefault.jpg',
          description: 'Video introductorio que cubre los conceptos basicos.',
          relevanceScore: 0.95,
          learningObjective: 'Comprender los fundamentos del tema',
          isRequired: true,
          order: 1,
          isWatched: false,
        ),
        UnitVideo(
          id: 'video_2',
          title: 'Conceptos avanzados',
          youtubeId: 'L_LUpnjgPso',
          youtubeUrl: 'https://www.youtube.com/watch?v=L_LUpnjgPso',
          durationSeconds: 900,
          channelName: 'ICFES Academy',
          thumbnailUrl: 'https://img.youtube.com/vi/L_LUpnjgPso/mqdefault.jpg',
          description: 'Profundizacion en los conceptos mas complejos.',
          relevanceScore: 0.85,
          learningObjective: 'Dominar conceptos intermedios',
          isRequired: true,
          order: 2,
          isWatched: false,
        ),
        UnitVideo(
          id: 'video_3',
          title: 'Ejemplos practicos',
          youtubeId: '9bZkp7q19f0',
          youtubeUrl: 'https://www.youtube.com/watch?v=9bZkp7q19f0',
          durationSeconds: 600,
          channelName: 'ICFES Academy',
          thumbnailUrl: 'https://img.youtube.com/vi/9bZkp7q19f0/mqdefault.jpg',
          description: 'Resolucion de problemas paso a paso.',
          relevanceScore: 0.75,
          isRequired: false,
          order: 3,
          isWatched: false,
        ),
      ],
      exercises: [
        const UnitExercise(
          id: 'exercise_1',
          title: 'Quiz de la Unidad',
          description: 'Evalua tu comprension de los conceptos aprendidos',
          questionCount: 10,
          completedQuestions: 0,
          score: 0,
          difficulty: 'medium',
          topics: ['Fundamentos', 'Conceptos basicos'],
          isCompleted: false,
        ),
        const UnitExercise(
          id: 'exercise_2',
          title: 'Practica adicional',
          description: 'Refuerza tu aprendizaje con mas ejercicios',
          questionCount: 15,
          completedQuestions: 0,
          score: 0,
          difficulty: 'hard',
          topics: ['Aplicacion', 'Problemas'],
          isCompleted: false,
        ),
      ],
      readings: [
        const UnitReading(
          id: 'reading_1',
          title: 'Guia de estudio',
          content: 'Material complementario para reforzar los conceptos del video.',
          estimatedMinutes: 15,
          isCompleted: false,
        ),
        const UnitReading(
          id: 'reading_2',
          title: 'Resumen de formulas',
          content: 'Lista de formulas y conceptos clave para memorizar.',
          estimatedMinutes: 10,
          isCompleted: false,
        ),
      ],
      weightedProgress: const WeightedProgress(
        videos: ContentProgress(completed: 0, total: 3, weight: 0.3),
        exercises: ContentProgress(completed: 0, total: 2, weight: 0.5),
        readings: ContentProgress(completed: 0, total: 2, weight: 0.2),
      ),
      isUnlocked: true,
      isCompleted: false,
      score: 0,
      focusTopics: ['Fundamentos', 'Conceptos basicos'],
      weakAreas: [],
      recommendedPriority: 'high',
      estimatedTime: '2-3 horas',
    );
  }
}

/// Provider for UnitRepository
final unitRepositoryProvider = Provider<UnitRepository>((ref) {
  final apiClient = ref.watch(apiClientProvider);
  return UnitRepository(apiClient);
});
