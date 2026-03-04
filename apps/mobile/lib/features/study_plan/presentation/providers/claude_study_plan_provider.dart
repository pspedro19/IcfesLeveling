import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/network/api_client.dart';

/// State class for Claude AI Study Plan
class ClaudeStudyPlanState {
  final bool isLoading;
  final bool isGenerating;
  final String? error;
  final ClaudeStudyPlan? plan;
  final String? planId;

  const ClaudeStudyPlanState({
    this.isLoading = false,
    this.isGenerating = false,
    this.error,
    this.plan,
    this.planId,
  });

  ClaudeStudyPlanState copyWith({
    bool? isLoading,
    bool? isGenerating,
    String? error,
    bool clearError = false,
    ClaudeStudyPlan? plan,
    String? planId,
  }) {
    return ClaudeStudyPlanState(
      isLoading: isLoading ?? this.isLoading,
      isGenerating: isGenerating ?? this.isGenerating,
      error: clearError ? null : error ?? this.error,
      plan: plan ?? this.plan,
      planId: planId ?? this.planId,
    );
  }

  bool get hasPlan => plan != null;
  bool get isAiGenerated => plan?.metadata.aiGenerated ?? false;
}


/// Notifier for Claude AI Study Plan
class ClaudeStudyPlanNotifier extends StateNotifier<ClaudeStudyPlanState> {
  final ApiClient _apiClient;

  ClaudeStudyPlanNotifier(this._apiClient) : super(const ClaudeStudyPlanState());

  /// Generate a new study plan using Claude AI
  Future<bool> generatePlan({
    required String testId,
    required String subjectId,
    String? userId,
  }) async {
    state = state.copyWith(isGenerating: true, clearError: true);

    try {
      final response = await _apiClient.post(
        '/api/v1/claude-study-plan/generate',
        data: {
          'test_id': testId,
          'subject_id': subjectId,
          if (userId != null) 'user_id': userId,
        },
      );

      if (response.statusCode == 200 && response.data != null) {
        final data = response.data as Map<String, dynamic>;

        if (data['success'] == true) {
          final planData = data['plan_data'] as Map<String, dynamic>?;
          final plan = planData != null ? ClaudeStudyPlan.fromJson(planData) : null;

          state = state.copyWith(
            isGenerating: false,
            plan: plan,
            planId: data['plan_id'] as String?,
          );
          return true;
        }
      }

      state = state.copyWith(
        isGenerating: false,
        error: 'Error al generar plan de estudio con IA',
      );
      return false;
    } catch (e) {
      state = state.copyWith(
        isGenerating: false,
        error: e.toString(),
      );
      return false;
    }
  }

  /// Fetch an existing Claude-generated study plan
  Future<void> fetchPlan(String planId) async {
    state = state.copyWith(isLoading: true, clearError: true);

    try {
      final response = await _apiClient.get('/api/v1/claude-study-plan/plan/$planId');

      if (response.statusCode == 200 && response.data != null) {
        final data = response.data as Map<String, dynamic>;

        if (data['success'] == true) {
          final planData = data['plan_data'] as Map<String, dynamic>?;
          final plan = planData != null ? ClaudeStudyPlan.fromJson(planData) : null;

          state = state.copyWith(
            isLoading: false,
            plan: plan,
            planId: data['plan_id'] as String?,
          );
          return;
        }
      }

      state = state.copyWith(
        isLoading: false,
        error: 'Plan de estudio no encontrado',
      );
    } catch (e) {
      state = state.copyWith(
        isLoading: false,
        error: e.toString(),
      );
    }
  }

  /// Clear the current plan
  void clearPlan() {
    state = const ClaudeStudyPlanState();
  }
}


/// Provider
final claudeStudyPlanProvider =
    StateNotifierProvider<ClaudeStudyPlanNotifier, ClaudeStudyPlanState>((ref) {
  final apiClient = ref.watch(apiClientProvider);
  return ClaudeStudyPlanNotifier(apiClient);
});


// ============================================
// DATA MODELS
// ============================================

class ClaudeStudyPlan {
  final ClaudeStudyPlanMetadata metadata;
  final List<ClaudeStudyUnit> units;
  final List<String> weaknesses;
  final List<FailedTopic> failedTopics;
  final ClaudeStudyRecommendations recommendations;

  const ClaudeStudyPlan({
    required this.metadata,
    required this.units,
    required this.weaknesses,
    required this.failedTopics,
    required this.recommendations,
  });

  factory ClaudeStudyPlan.fromJson(Map<String, dynamic> json) {
    return ClaudeStudyPlan(
      metadata: ClaudeStudyPlanMetadata.fromJson(json['metadata'] ?? {}),
      units: (json['units'] as List? ?? [])
          .map((u) => ClaudeStudyUnit.fromJson(u))
          .toList(),
      weaknesses: List<String>.from(json['weaknesses'] ?? []),
      failedTopics: (json['failed_topics'] as List? ?? [])
          .map((t) => FailedTopic.fromJson(t))
          .toList(),
      recommendations: ClaudeStudyRecommendations.fromJson(json['recommendations'] ?? {}),
    );
  }

  int get totalVideos => units.fold(0, (sum, unit) => sum + unit.videos.length);
  int get totalDurationMinutes =>
      units.fold(0, (sum, unit) => sum + unit.videos.fold(0, (s, v) => s + v.durationMinutes));
}


class ClaudeStudyPlanMetadata {
  final String testId;
  final String subjectId;
  final String subjectName;
  final double scorePercentage;
  final String generatedAt;
  final int totalUnits;
  final int totalVideos;
  final int totalDurationMinutes;
  final bool aiGenerated;
  final String generator;

  const ClaudeStudyPlanMetadata({
    required this.testId,
    required this.subjectId,
    required this.subjectName,
    required this.scorePercentage,
    required this.generatedAt,
    required this.totalUnits,
    required this.totalVideos,
    required this.totalDurationMinutes,
    required this.aiGenerated,
    required this.generator,
  });

  factory ClaudeStudyPlanMetadata.fromJson(Map<String, dynamic> json) {
    return ClaudeStudyPlanMetadata(
      testId: json['test_id'] ?? '',
      subjectId: json['subject_id'] ?? '',
      subjectName: json['subject_name'] ?? '',
      scorePercentage: (json['score_percentage'] ?? 0).toDouble(),
      generatedAt: json['generated_at'] ?? '',
      totalUnits: json['total_units'] ?? 0,
      totalVideos: json['total_videos'] ?? 0,
      totalDurationMinutes: json['total_duration_minutes'] ?? 0,
      aiGenerated: json['ai_generated'] ?? false,
      generator: json['generator'] ?? 'unknown',
    );
  }
}


class ClaudeStudyUnit {
  final int unitNumber;
  final String title;
  final String description;
  final List<String> failedTopicsCovered;
  final List<ClaudeStudyVideo> videos;
  final String priority;
  final List<String> learningObjectives;
  final String aiRationale;
  final List<IncorrectQuestion> incorrectQuestions;

  const ClaudeStudyUnit({
    required this.unitNumber,
    required this.title,
    required this.description,
    required this.failedTopicsCovered,
    required this.videos,
    required this.priority,
    required this.learningObjectives,
    required this.aiRationale,
    required this.incorrectQuestions,
  });

  factory ClaudeStudyUnit.fromJson(Map<String, dynamic> json) {
    return ClaudeStudyUnit(
      unitNumber: json['unit_number'] ?? 0,
      title: json['title'] ?? '',
      description: json['description'] ?? '',
      failedTopicsCovered: List<String>.from(json['failed_topics_covered'] ?? []),
      videos: (json['videos'] as List? ?? [])
          .map((v) => ClaudeStudyVideo.fromJson(v))
          .toList(),
      priority: json['priority'] ?? 'media',
      learningObjectives: List<String>.from(json['learning_objectives'] ?? []),
      aiRationale: json['ai_rationale'] ?? '',
      incorrectQuestions: (json['incorrect_questions'] as List? ?? [])
          .map((q) => IncorrectQuestion.fromJson(q))
          .toList(),
    );
  }

  bool get isHighPriority => priority == 'alta';
  int get totalDurationMinutes => videos.fold(0, (sum, v) => sum + v.durationMinutes);
}


class ClaudeStudyVideo {
  final String id;
  final String youtubeId;
  final String title;
  final String url;
  final String channel;
  final int durationMinutes;
  final int xp;
  final String coversFailedTopic;
  final String competenceMatch;
  final String componentMatch;
  final String justification;
  final String recommendationReason;

  const ClaudeStudyVideo({
    required this.id,
    required this.youtubeId,
    required this.title,
    required this.url,
    required this.channel,
    required this.durationMinutes,
    required this.xp,
    required this.coversFailedTopic,
    required this.competenceMatch,
    required this.componentMatch,
    required this.justification,
    required this.recommendationReason,
  });

  factory ClaudeStudyVideo.fromJson(Map<String, dynamic> json) {
    return ClaudeStudyVideo(
      id: json['id'] ?? '',
      youtubeId: json['youtube_id'] ?? '',
      title: json['title'] ?? '',
      url: json['url'] ?? '',
      channel: json['channel'] ?? '',
      durationMinutes: json['duration_minutes'] ?? 0,
      xp: json['xp'] ?? 0,
      coversFailedTopic: json['covers_failed_topic'] ?? '',
      competenceMatch: json['competence_match'] ?? '',
      componentMatch: json['component_match'] ?? '',
      justification: json['justification'] ?? '',
      recommendationReason: json['recommendation_reason'] ?? '',
    );
  }
}


class FailedTopic {
  final String topicName;
  final String competencia;
  final String componente;
  final int errorCount;

  const FailedTopic({
    required this.topicName,
    required this.competencia,
    required this.componente,
    required this.errorCount,
  });

  factory FailedTopic.fromJson(Map<String, dynamic> json) {
    return FailedTopic(
      topicName: json['topic_name'] ?? '',
      competencia: json['competencia'] ?? '',
      componente: json['componente'] ?? '',
      errorCount: json['error_count'] ?? 0,
    );
  }
}


class IncorrectQuestion {
  final String id;
  final String preguntaTexto;
  final String competencia;
  final String componente;
  final String topicName;
  final int difficultyLevel;
  final String explanation;

  const IncorrectQuestion({
    required this.id,
    required this.preguntaTexto,
    required this.competencia,
    required this.componente,
    required this.topicName,
    required this.difficultyLevel,
    required this.explanation,
  });

  factory IncorrectQuestion.fromJson(Map<String, dynamic> json) {
    return IncorrectQuestion(
      id: json['id'] ?? '',
      preguntaTexto: json['pregunta_texto'] ?? '',
      competencia: json['competencia'] ?? '',
      componente: json['componente'] ?? '',
      topicName: json['topic_name'] ?? '',
      difficultyLevel: json['difficulty_level'] ?? 0,
      explanation: json['explanation'] ?? '',
    );
  }
}


class ClaudeStudyRecommendations {
  final String studyFrequency;
  final String sessionDuration;
  final String estimatedCompletion;
  final String studyStrategy;
  final List<String> additionalTips;

  const ClaudeStudyRecommendations({
    required this.studyFrequency,
    required this.sessionDuration,
    required this.estimatedCompletion,
    required this.studyStrategy,
    required this.additionalTips,
  });

  factory ClaudeStudyRecommendations.fromJson(Map<String, dynamic> json) {
    return ClaudeStudyRecommendations(
      studyFrequency: json['study_frequency'] ?? '',
      sessionDuration: json['session_duration'] ?? '',
      estimatedCompletion: json['estimated_completion'] ?? '',
      studyStrategy: json['study_strategy'] ?? '',
      additionalTips: List<String>.from(json['additional_tips'] ?? []),
    );
  }
}
