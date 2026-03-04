/// Study Plan data models matching backend API response
/// Based on backend schemas: StudyPlanDetail, StudyUnit, etc.

class StudyTopic {
  final String name;
  final int difficulty;
  final int questions;
  final List<String> tags;

  StudyTopic({
    required this.name,
    required this.difficulty,
    required this.questions,
    this.tags = const [],
  });

  factory StudyTopic.fromJson(Map<String, dynamic> json) {
    return StudyTopic(
      name: json['name'] ?? '',
      difficulty: json['difficulty'] ?? 1,
      questions: json['questions'] ?? 0,
      tags: List<String>.from(json['tags'] ?? []),
    );
  }

  Map<String, dynamic> toJson() => {
    'name': name,
    'difficulty': difficulty,
    'questions': questions,
    'tags': tags,
  };
}

class UnitRecommendations {
  final String priority;
  final List<String> weakAreas;
  final List<String> focusTopics;
  final String studyTime;

  UnitRecommendations({
    required this.priority,
    this.weakAreas = const [],
    this.focusTopics = const [],
    required this.studyTime,
  });

  factory UnitRecommendations.fromJson(Map<String, dynamic> json) {
    return UnitRecommendations(
      priority: json['priority'] ?? 'medium',
      weakAreas: List<String>.from(json['weak_areas'] ?? []),
      focusTopics: List<String>.from(json['focus_topics'] ?? []),
      studyTime: json['study_time'] ?? '2 horas',
    );
  }

  Map<String, dynamic> toJson() => {
    'priority': priority,
    'weak_areas': weakAreas,
    'focus_topics': focusTopics,
    'study_time': studyTime,
  };
}

class StudyUnit {
  final int unitNumber;
  final String name;
  final String description;
  final List<StudyTopic> topics;
  final UnitRecommendations recommendations;
  final bool unlocked;
  final double progress;
  final bool aiRecommended;

  StudyUnit({
    required this.unitNumber,
    required this.name,
    required this.description,
    this.topics = const [],
    required this.recommendations,
    required this.unlocked,
    required this.progress,
    this.aiRecommended = false,
  });

  factory StudyUnit.fromJson(Map<String, dynamic> json) {
    return StudyUnit(
      unitNumber: json['unit_number'] ?? 1,
      name: json['name'] ?? 'Unidad',
      description: json['description'] ?? '',
      topics: (json['topics'] as List<dynamic>?)
          ?.map((t) => StudyTopic.fromJson(t as Map<String, dynamic>))
          .toList() ?? [],
      recommendations: UnitRecommendations.fromJson(
        json['recommendations'] as Map<String, dynamic>? ?? {},
      ),
      unlocked: json['unlocked'] ?? false,
      progress: (json['progress'] ?? 0.0).toDouble(),
      aiRecommended: json['ai_recommended'] ?? false,
    );
  }

  /// Returns the unit status based on progress
  UnitStatus get status {
    if (!unlocked) return UnitStatus.locked;
    if (progress >= 100) return UnitStatus.completed;
    if (progress > 0) return UnitStatus.inProgress;
    return UnitStatus.available;
  }

  /// Videos watched estimate (30% of progress)
  int get videosWatched => ((progress / 100) * 3).round();
  int get totalVideos => 3;

  /// Exercises done estimate (50% of progress)
  int get exercisesDone => ((progress / 100) * 10).round();
  int get totalExercises => 10;

  Map<String, dynamic> toJson() => {
    'unit_number': unitNumber,
    'name': name,
    'description': description,
    'topics': topics.map((t) => t.toJson()).toList(),
    'recommendations': recommendations.toJson(),
    'unlocked': unlocked,
    'progress': progress,
    'ai_recommended': aiRecommended,
  };
}

enum UnitStatus {
  locked,
  available,
  inProgress,
  completed,
}

class UnitProgressDetail {
  final int unitNumber;
  final String unitName;
  final bool isCompleted;
  final double score;
  final double progressPercentage;
  final Map<String, dynamic> weightedProgress;

  UnitProgressDetail({
    required this.unitNumber,
    required this.unitName,
    required this.isCompleted,
    required this.score,
    required this.progressPercentage,
    this.weightedProgress = const {},
  });

  factory UnitProgressDetail.fromJson(Map<String, dynamic> json) {
    return UnitProgressDetail(
      unitNumber: json['unit_number'] ?? 0,
      unitName: json['unit_name'] ?? '',
      isCompleted: json['is_completed'] ?? false,
      score: (json['score'] ?? 0.0).toDouble(),
      progressPercentage: (json['progress_percentage'] ?? 0.0).toDouble(),
      weightedProgress: json['weighted_progress'] as Map<String, dynamic>? ?? {},
    );
  }
}

class ProgressDetails {
  final double overallProgress;
  final int completedUnits;
  final List<UnitProgressDetail> unitDetails;

  ProgressDetails({
    required this.overallProgress,
    required this.completedUnits,
    this.unitDetails = const [],
  });

  factory ProgressDetails.fromJson(Map<String, dynamic> json) {
    return ProgressDetails(
      overallProgress: (json['overall_progress'] ?? 0.0).toDouble(),
      completedUnits: json['completed_units'] ?? 0,
      unitDetails: (json['unit_details'] as List<dynamic>?)
          ?.map((d) => UnitProgressDetail.fromJson(d as Map<String, dynamic>))
          .toList() ?? [],
    );
  }
}

class PersonalizedRecommendations {
  final double overallAccuracy;
  final List<Map<String, dynamic>> weakTopics;
  final List<Map<String, dynamic>> strongTopics;
  final List<String> suggestedFocus;
  final Map<String, dynamic> studySchedule;
  final Map<String, dynamic> estimatedImprovement;

  PersonalizedRecommendations({
    required this.overallAccuracy,
    this.weakTopics = const [],
    this.strongTopics = const [],
    this.suggestedFocus = const [],
    this.studySchedule = const {},
    this.estimatedImprovement = const {},
  });

  factory PersonalizedRecommendations.fromJson(Map<String, dynamic> json) {
    return PersonalizedRecommendations(
      overallAccuracy: (json['overall_accuracy'] ?? 0.0).toDouble(),
      weakTopics: (json['weak_topics'] as List<dynamic>?)
          ?.map((t) => t as Map<String, dynamic>)
          .toList() ?? [],
      strongTopics: (json['strong_topics'] as List<dynamic>?)
          ?.map((t) => t as Map<String, dynamic>)
          .toList() ?? [],
      suggestedFocus: List<String>.from(json['suggested_focus'] ?? []),
      studySchedule: json['study_schedule'] as Map<String, dynamic>? ?? {},
      estimatedImprovement: json['estimated_improvement'] as Map<String, dynamic>? ?? {},
    );
  }
}

class StudyPlanDetail {
  final String id;
  final String planName;
  final String subject;
  final String title;
  final String description;
  final List<StudyUnit> units;
  final int totalUnits;
  final int completedUnits;
  final double progressPercentage;
  final String estimatedTime;
  final String difficultyCurve;
  final double icfesWeight;
  final List<String> examSections;
  final PersonalizedRecommendations? personalizedRecommendations;
  final ProgressDetails progressDetails;
  final String? lastUpdated;

  StudyPlanDetail({
    required this.id,
    required this.planName,
    required this.subject,
    required this.title,
    required this.description,
    required this.units,
    required this.totalUnits,
    required this.completedUnits,
    required this.progressPercentage,
    required this.estimatedTime,
    required this.difficultyCurve,
    required this.icfesWeight,
    this.examSections = const [],
    this.personalizedRecommendations,
    required this.progressDetails,
    this.lastUpdated,
  });

  factory StudyPlanDetail.fromJson(Map<String, dynamic> json) {
    return StudyPlanDetail(
      id: json['id'] ?? '',
      planName: json['plan_name'] ?? '',
      subject: json['subject'] ?? '',
      title: json['title'] ?? '',
      description: json['description'] ?? '',
      units: (json['units'] as List<dynamic>?)
          ?.map((u) => StudyUnit.fromJson(u as Map<String, dynamic>))
          .toList() ?? [],
      totalUnits: json['total_units'] ?? 0,
      completedUnits: json['completed_units'] ?? 0,
      progressPercentage: (json['progress_percentage'] ?? 0.0).toDouble(),
      estimatedTime: json['estimated_time'] ?? '8-12 semanas',
      difficultyCurve: json['difficulty_curve'] ?? 'adaptive',
      icfesWeight: (json['icfes_weight'] ?? 0.25).toDouble(),
      examSections: List<String>.from(json['exam_sections'] ?? []),
      personalizedRecommendations: json['personalized_recommendations'] != null
          ? PersonalizedRecommendations.fromJson(
              json['personalized_recommendations'] as Map<String, dynamic>,
            )
          : null,
      progressDetails: ProgressDetails.fromJson(
        json['progress_details'] as Map<String, dynamic>? ?? {},
      ),
      lastUpdated: json['last_updated'],
    );
  }

  /// Get the current unit (first unlocked unit with progress < 100)
  StudyUnit? get currentUnit {
    try {
      return units.firstWhere(
        (u) => u.unlocked && u.progress < 100,
      );
    } catch (_) {
      return units.isNotEmpty ? units.first : null;
    }
  }

  /// Get subject color based on subject name
  int get subjectColor {
    final subjectLower = subject.toLowerCase();
    if (subjectLower.contains('matem')) return 0xFF3B82F6; // Blue
    if (subjectLower.contains('lenguaje') || subjectLower.contains('lectura')) return 0xFFA855F7; // Purple
    if (subjectLower.contains('natural')) return 0xFF22C55E; // Green
    if (subjectLower.contains('social')) return 0xFFF97316; // Orange
    if (subjectLower.contains('ingl')) return 0xFFEC4899; // Pink
    return 0xFF6366F1; // Default purple
  }

  Map<String, dynamic> toJson() => {
    'id': id,
    'plan_name': planName,
    'subject': subject,
    'title': title,
    'description': description,
    'units': units.map((u) => u.toJson()).toList(),
    'total_units': totalUnits,
    'completed_units': completedUnits,
    'progress_percentage': progressPercentage,
    'estimated_time': estimatedTime,
    'difficulty_curve': difficultyCurve,
    'icfes_weight': icfesWeight,
    'exam_sections': examSections,
    'last_updated': lastUpdated,
  };
}

/// Response wrapper for current study plan API
class CurrentStudyPlanResponse {
  final StudyPlanDetail? plan;
  final String? message;
  final bool hasPlan;

  CurrentStudyPlanResponse({
    this.plan,
    this.message,
    required this.hasPlan,
  });

  factory CurrentStudyPlanResponse.fromJson(Map<String, dynamic> json) {
    return CurrentStudyPlanResponse(
      plan: json['plan'] != null
          ? StudyPlanDetail.fromJson(json['plan'] as Map<String, dynamic>)
          : null,
      message: json['message'],
      hasPlan: json['has_plan'] ?? false,
    );
  }
}
