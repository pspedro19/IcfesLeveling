/// Video Tracking Models for backend communication
///
/// These models handle the video progress tracking data
/// sent to and received from the backend.

class VideoTrackingModel {
  final String id;
  final String videoId;
  final String? planId;
  final int? unitNumber;
  final int watchedSeconds;
  final double percentageWatched;
  final bool completed;
  final DateTime? completedAt;
  final DateTime createdAt;
  final DateTime updatedAt;

  VideoTrackingModel({
    required this.id,
    required this.videoId,
    this.planId,
    this.unitNumber,
    required this.watchedSeconds,
    required this.percentageWatched,
    required this.completed,
    this.completedAt,
    required this.createdAt,
    required this.updatedAt,
  });

  factory VideoTrackingModel.fromJson(Map<String, dynamic> json) {
    return VideoTrackingModel(
      id: json['id'] as String,
      videoId: json['video_id'] as String,
      planId: json['plan_id'] as String?,
      unitNumber: json['unit_number'] as int?,
      watchedSeconds: json['watched_seconds'] as int? ?? 0,
      percentageWatched: (json['percentage_watched'] as num?)?.toDouble() ?? 0.0,
      completed: json['completed'] as bool? ?? false,
      completedAt: json['completed_at'] != null
          ? DateTime.parse(json['completed_at'] as String)
          : null,
      createdAt: DateTime.parse(json['created_at'] as String),
      updatedAt: DateTime.parse(json['updated_at'] as String),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'video_id': videoId,
      'plan_id': planId,
      'unit_number': unitNumber,
      'watched_seconds': watchedSeconds,
      'percentage_watched': percentageWatched,
      'completed': completed,
      'completed_at': completedAt?.toIso8601String(),
      'created_at': createdAt.toIso8601String(),
      'updated_at': updatedAt.toIso8601String(),
    };
  }

  VideoTrackingModel copyWith({
    String? id,
    String? videoId,
    String? planId,
    int? unitNumber,
    int? watchedSeconds,
    double? percentageWatched,
    bool? completed,
    DateTime? completedAt,
    DateTime? createdAt,
    DateTime? updatedAt,
  }) {
    return VideoTrackingModel(
      id: id ?? this.id,
      videoId: videoId ?? this.videoId,
      planId: planId ?? this.planId,
      unitNumber: unitNumber ?? this.unitNumber,
      watchedSeconds: watchedSeconds ?? this.watchedSeconds,
      percentageWatched: percentageWatched ?? this.percentageWatched,
      completed: completed ?? this.completed,
      completedAt: completedAt ?? this.completedAt,
      createdAt: createdAt ?? this.createdAt,
      updatedAt: updatedAt ?? this.updatedAt,
    );
  }
}

class CreateTrackingRequest {
  final String videoId;
  final String? planId;
  final int? unitNumber;

  CreateTrackingRequest({
    required this.videoId,
    this.planId,
    this.unitNumber,
  });

  Map<String, dynamic> toJson() {
    return {
      'video_id': videoId,
      if (planId != null) 'plan_id': planId,
      if (unitNumber != null) 'unit_number': unitNumber,
    };
  }
}

class UpdateProgressRequest {
  final String trackingId;
  final int watchedSeconds;
  final double percentageWatched;

  UpdateProgressRequest({
    required this.trackingId,
    required this.watchedSeconds,
    required this.percentageWatched,
  });

  Map<String, dynamic> toJson() {
    return {
      'tracking_id': trackingId,
      'watched_seconds': watchedSeconds,
      'percentage_watched': percentageWatched,
    };
  }
}

class VideoInfoModel {
  final String videoId;
  final String title;
  final String? description;
  final String? thumbnailUrl;
  final int? durationSeconds;
  final String youtubeId;

  VideoInfoModel({
    required this.videoId,
    required this.title,
    this.description,
    this.thumbnailUrl,
    this.durationSeconds,
    required this.youtubeId,
  });

  factory VideoInfoModel.fromJson(Map<String, dynamic> json) {
    return VideoInfoModel(
      videoId: json['video_id'] as String? ?? json['id'] as String,
      title: json['title'] as String? ?? 'Video',
      description: json['description'] as String?,
      thumbnailUrl: json['thumbnail_url'] as String?,
      durationSeconds: json['duration_seconds'] as int?,
      youtubeId: json['youtube_id'] as String? ?? json['video_id'] as String,
    );
  }

  /// Extract YouTube video ID from various URL formats or direct ID
  static String extractYoutubeId(String input) {
    // If it's already just an ID (11 characters, alphanumeric with - and _)
    final idPattern = RegExp(r'^[a-zA-Z0-9_-]{11}$');
    if (idPattern.hasMatch(input)) {
      return input;
    }

    // Try to extract from URL patterns
    final patterns = [
      // Standard YouTube URLs
      RegExp(r'youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})'),
      // Short YouTube URLs
      RegExp(r'youtu\.be/([a-zA-Z0-9_-]{11})'),
      // Embed URLs
      RegExp(r'youtube\.com/embed/([a-zA-Z0-9_-]{11})'),
      // YouTube shorts
      RegExp(r'youtube\.com/shorts/([a-zA-Z0-9_-]{11})'),
    ];

    for (final pattern in patterns) {
      final match = pattern.firstMatch(input);
      if (match != null) {
        return match.group(1)!;
      }
    }

    // Return the input as-is if no pattern matches (might be an ID already)
    return input;
  }
}
