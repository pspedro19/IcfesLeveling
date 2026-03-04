/// Domain entities for Unit Detail feature
library;

import 'package:flutter/foundation.dart';

/// Represents a video content item within a unit
@immutable
class UnitVideo {
  final String id;
  final String title;
  final String youtubeId;
  final String youtubeUrl;
  final int durationSeconds;
  final String channelName;
  final String? thumbnailUrl;
  final String? description;
  final double relevanceScore;
  final String? learningObjective;
  final bool isRequired;
  final int order;
  final bool isWatched;
  final double watchProgress;

  const UnitVideo({
    required this.id,
    required this.title,
    required this.youtubeId,
    required this.youtubeUrl,
    required this.durationSeconds,
    required this.channelName,
    this.thumbnailUrl,
    this.description,
    this.relevanceScore = 0.0,
    this.learningObjective,
    this.isRequired = false,
    this.order = 0,
    this.isWatched = false,
    this.watchProgress = 0.0,
  });

  String get formattedDuration {
    final minutes = durationSeconds ~/ 60;
    final seconds = durationSeconds % 60;
    if (minutes >= 60) {
      final hours = minutes ~/ 60;
      final remainingMinutes = minutes % 60;
      return '${hours}h ${remainingMinutes}m';
    }
    return '${minutes}:${seconds.toString().padLeft(2, '0')}';
  }

  factory UnitVideo.fromJson(Map<String, dynamic> json) {
    return UnitVideo(
      id: json['id']?.toString() ?? '',
      title: json['title'] ?? 'Sin titulo',
      youtubeId: json['youtube_id'] ?? json['youtubeId'] ?? '',
      youtubeUrl: json['youtube_url'] ?? json['youtubeUrl'] ?? '',
      durationSeconds: json['duration_seconds'] ?? json['durationSeconds'] ?? 0,
      channelName: json['channel_name'] ?? json['channelName'] ?? 'Canal desconocido',
      thumbnailUrl: json['thumbnail_url'] ?? json['thumbnailUrl'],
      description: json['description'],
      relevanceScore: (json['relevance_score'] ?? json['relevanceScore'] ?? 0.0).toDouble(),
      learningObjective: json['learning_objective'] ?? json['learningObjective'],
      isRequired: json['is_required'] ?? json['isRequired'] ?? false,
      order: json['order'] ?? 0,
      isWatched: json['is_watched'] ?? json['isWatched'] ?? false,
      watchProgress: (json['watch_progress'] ?? json['watchProgress'] ?? 0.0).toDouble(),
    );
  }

  Map<String, dynamic> toJson() => {
    'id': id,
    'title': title,
    'youtube_id': youtubeId,
    'youtube_url': youtubeUrl,
    'duration_seconds': durationSeconds,
    'channel_name': channelName,
    'thumbnail_url': thumbnailUrl,
    'description': description,
    'relevance_score': relevanceScore,
    'learning_objective': learningObjective,
    'is_required': isRequired,
    'order': order,
    'is_watched': isWatched,
    'watch_progress': watchProgress,
  };

  UnitVideo copyWith({
    String? id,
    String? title,
    String? youtubeId,
    String? youtubeUrl,
    int? durationSeconds,
    String? channelName,
    String? thumbnailUrl,
    String? description,
    double? relevanceScore,
    String? learningObjective,
    bool? isRequired,
    int? order,
    bool? isWatched,
    double? watchProgress,
  }) {
    return UnitVideo(
      id: id ?? this.id,
      title: title ?? this.title,
      youtubeId: youtubeId ?? this.youtubeId,
      youtubeUrl: youtubeUrl ?? this.youtubeUrl,
      durationSeconds: durationSeconds ?? this.durationSeconds,
      channelName: channelName ?? this.channelName,
      thumbnailUrl: thumbnailUrl ?? this.thumbnailUrl,
      description: description ?? this.description,
      relevanceScore: relevanceScore ?? this.relevanceScore,
      learningObjective: learningObjective ?? this.learningObjective,
      isRequired: isRequired ?? this.isRequired,
      order: order ?? this.order,
      isWatched: isWatched ?? this.isWatched,
      watchProgress: watchProgress ?? this.watchProgress,
    );
  }
}

/// Represents an exercise/quiz within a unit
@immutable
class UnitExercise {
  final String id;
  final String title;
  final String? description;
  final int questionCount;
  final int completedQuestions;
  final double score;
  final String difficulty;
  final List<String> topics;
  final bool isCompleted;

  const UnitExercise({
    required this.id,
    required this.title,
    this.description,
    required this.questionCount,
    this.completedQuestions = 0,
    this.score = 0.0,
    this.difficulty = 'medium',
    this.topics = const [],
    this.isCompleted = false,
  });

  double get completionPercentage =>
    questionCount > 0 ? (completedQuestions / questionCount) * 100 : 0;

  factory UnitExercise.fromJson(Map<String, dynamic> json) {
    return UnitExercise(
      id: json['id']?.toString() ?? '',
      title: json['title'] ?? 'Ejercicio',
      description: json['description'],
      questionCount: json['question_count'] ?? json['questionCount'] ?? 0,
      completedQuestions: json['completed_questions'] ?? json['completedQuestions'] ?? 0,
      score: (json['score'] ?? 0.0).toDouble(),
      difficulty: json['difficulty'] ?? 'medium',
      topics: List<String>.from(json['topics'] ?? []),
      isCompleted: json['is_completed'] ?? json['isCompleted'] ?? false,
    );
  }

  Map<String, dynamic> toJson() => {
    'id': id,
    'title': title,
    'description': description,
    'question_count': questionCount,
    'completed_questions': completedQuestions,
    'score': score,
    'difficulty': difficulty,
    'topics': topics,
    'is_completed': isCompleted,
  };
}

/// Represents supplementary reading material
@immutable
class UnitReading {
  final String id;
  final String title;
  final String? content;
  final String? url;
  final int estimatedMinutes;
  final bool isCompleted;
  final String? thumbnailUrl;

  const UnitReading({
    required this.id,
    required this.title,
    this.content,
    this.url,
    this.estimatedMinutes = 10,
    this.isCompleted = false,
    this.thumbnailUrl,
  });

  factory UnitReading.fromJson(Map<String, dynamic> json) {
    return UnitReading(
      id: json['id']?.toString() ?? '',
      title: json['title'] ?? 'Lectura',
      content: json['content'],
      url: json['url'],
      estimatedMinutes: json['estimated_minutes'] ?? json['estimatedMinutes'] ?? 10,
      isCompleted: json['is_completed'] ?? json['isCompleted'] ?? false,
      thumbnailUrl: json['thumbnail_url'] ?? json['thumbnailUrl'],
    );
  }

  Map<String, dynamic> toJson() => {
    'id': id,
    'title': title,
    'content': content,
    'url': url,
    'estimated_minutes': estimatedMinutes,
    'is_completed': isCompleted,
    'thumbnail_url': thumbnailUrl,
  };
}

/// Progress tracking for different content types
@immutable
class ContentProgress {
  final int completed;
  final int total;
  final double weight;

  const ContentProgress({
    this.completed = 0,
    this.total = 0,
    this.weight = 0.0,
  });

  double get percentage => total > 0 ? (completed / total) * 100 : 0;

  factory ContentProgress.fromJson(Map<String, dynamic> json) {
    return ContentProgress(
      completed: json['completed'] ?? 0,
      total: json['total'] ?? 0,
      weight: (json['weight'] ?? 0.0).toDouble(),
    );
  }

  Map<String, dynamic> toJson() => {
    'completed': completed,
    'total': total,
    'weight': weight,
  };
}

/// Weighted progress for different content types in a unit
@immutable
class WeightedProgress {
  final ContentProgress videos;
  final ContentProgress exercises;
  final ContentProgress readings;

  const WeightedProgress({
    this.videos = const ContentProgress(weight: 0.3),
    this.exercises = const ContentProgress(weight: 0.5),
    this.readings = const ContentProgress(weight: 0.2),
  });

  /// Calculate overall weighted progress (0-100)
  double get overallProgress {
    final videoContrib = videos.percentage * videos.weight;
    final exerciseContrib = exercises.percentage * exercises.weight;
    final readingContrib = readings.percentage * readings.weight;
    return videoContrib + exerciseContrib + readingContrib;
  }

  factory WeightedProgress.fromJson(Map<String, dynamic> json) {
    return WeightedProgress(
      videos: json['videos'] != null
        ? ContentProgress.fromJson(json['videos'])
        : const ContentProgress(weight: 0.3),
      exercises: json['exercises'] != null
        ? ContentProgress.fromJson(json['exercises'])
        : const ContentProgress(weight: 0.5),
      readings: json['readings'] != null
        ? ContentProgress.fromJson(json['readings'])
        : const ContentProgress(weight: 0.2),
    );
  }

  Map<String, dynamic> toJson() => {
    'videos': videos.toJson(),
    'exercises': exercises.toJson(),
    'readings': readings.toJson(),
  };
}

/// Complete unit detail model
@immutable
class UnitDetail {
  final String id;
  final String planId;
  final int unitNumber;
  final String name;
  final String description;
  final List<UnitVideo> videos;
  final List<UnitExercise> exercises;
  final List<UnitReading> readings;
  final WeightedProgress weightedProgress;
  final bool isUnlocked;
  final bool isCompleted;
  final double score;
  final List<String> focusTopics;
  final List<String> weakAreas;
  final String? recommendedPriority;
  final String? estimatedTime;

  const UnitDetail({
    required this.id,
    required this.planId,
    required this.unitNumber,
    required this.name,
    required this.description,
    this.videos = const [],
    this.exercises = const [],
    this.readings = const [],
    this.weightedProgress = const WeightedProgress(),
    this.isUnlocked = true,
    this.isCompleted = false,
    this.score = 0.0,
    this.focusTopics = const [],
    this.weakAreas = const [],
    this.recommendedPriority,
    this.estimatedTime,
  });

  /// Overall progress percentage (0-100)
  double get overallProgress => weightedProgress.overallProgress;

  /// Count of watched videos
  int get watchedVideosCount => videos.where((v) => v.isWatched).length;

  /// Count of completed exercises
  int get completedExercisesCount => exercises.where((e) => e.isCompleted).length;

  /// Count of completed readings
  int get completedReadingsCount => readings.where((r) => r.isCompleted).length;

  factory UnitDetail.fromJson(Map<String, dynamic> json) {
    return UnitDetail(
      id: json['id']?.toString() ?? '',
      planId: json['plan_id']?.toString() ?? json['planId']?.toString() ?? '',
      unitNumber: json['unit_number'] ?? json['unitNumber'] ?? 1,
      name: json['name'] ?? json['unit_name'] ?? 'Unidad',
      description: json['description'] ?? json['unit_description'] ?? '',
      videos: (json['videos'] as List<dynamic>?)
          ?.map((v) => UnitVideo.fromJson(v))
          .toList() ?? [],
      exercises: (json['exercises'] as List<dynamic>?)
          ?.map((e) => UnitExercise.fromJson(e))
          .toList() ?? [],
      readings: (json['readings'] as List<dynamic>?)
          ?.map((r) => UnitReading.fromJson(r))
          .toList() ?? [],
      weightedProgress: json['weighted_progress'] != null || json['weightedProgress'] != null
          ? WeightedProgress.fromJson(json['weighted_progress'] ?? json['weightedProgress'])
          : const WeightedProgress(),
      isUnlocked: json['is_unlocked'] ?? json['isUnlocked'] ?? json['unlocked'] ?? true,
      isCompleted: json['is_completed'] ?? json['isCompleted'] ?? false,
      score: (json['score'] ?? 0.0).toDouble(),
      focusTopics: List<String>.from(json['focus_topics'] ?? json['focusTopics'] ?? []),
      weakAreas: List<String>.from(json['weak_areas'] ?? json['weakAreas'] ?? []),
      recommendedPriority: json['recommended_priority'] ?? json['recommendedPriority'],
      estimatedTime: json['estimated_time'] ?? json['estimatedTime'],
    );
  }

  Map<String, dynamic> toJson() => {
    'id': id,
    'plan_id': planId,
    'unit_number': unitNumber,
    'name': name,
    'description': description,
    'videos': videos.map((v) => v.toJson()).toList(),
    'exercises': exercises.map((e) => e.toJson()).toList(),
    'readings': readings.map((r) => r.toJson()).toList(),
    'weighted_progress': weightedProgress.toJson(),
    'is_unlocked': isUnlocked,
    'is_completed': isCompleted,
    'score': score,
    'focus_topics': focusTopics,
    'weak_areas': weakAreas,
    'recommended_priority': recommendedPriority,
    'estimated_time': estimatedTime,
  };

  UnitDetail copyWith({
    String? id,
    String? planId,
    int? unitNumber,
    String? name,
    String? description,
    List<UnitVideo>? videos,
    List<UnitExercise>? exercises,
    List<UnitReading>? readings,
    WeightedProgress? weightedProgress,
    bool? isUnlocked,
    bool? isCompleted,
    double? score,
    List<String>? focusTopics,
    List<String>? weakAreas,
    String? recommendedPriority,
    String? estimatedTime,
  }) {
    return UnitDetail(
      id: id ?? this.id,
      planId: planId ?? this.planId,
      unitNumber: unitNumber ?? this.unitNumber,
      name: name ?? this.name,
      description: description ?? this.description,
      videos: videos ?? this.videos,
      exercises: exercises ?? this.exercises,
      readings: readings ?? this.readings,
      weightedProgress: weightedProgress ?? this.weightedProgress,
      isUnlocked: isUnlocked ?? this.isUnlocked,
      isCompleted: isCompleted ?? this.isCompleted,
      score: score ?? this.score,
      focusTopics: focusTopics ?? this.focusTopics,
      weakAreas: weakAreas ?? this.weakAreas,
      recommendedPriority: recommendedPriority ?? this.recommendedPriority,
      estimatedTime: estimatedTime ?? this.estimatedTime,
    );
  }
}
