import '../../data/models/video_tracking_model.dart';

/// Abstract repository interface for video tracking operations
///
/// Defines the contract for video tracking functionality
/// that must be implemented by the concrete repository.
abstract class VideoRepository {
  /// Create a new tracking entry for a video
  ///
  /// [videoId] - The ID of the video being watched (could be YouTube ID or internal ID)
  /// [planId] - Optional study plan ID if video is part of a plan
  /// [unitNumber] - Optional unit number within the study plan
  Future<VideoTrackingModel> createTracking({
    required String videoId,
    String? planId,
    int? unitNumber,
  });

  /// Update progress for an existing tracking entry
  ///
  /// [trackingId] - The ID of the tracking entry to update
  /// [watchedSeconds] - Total seconds watched so far
  /// [percentageWatched] - Progress percentage (0.0 to 100.0)
  Future<VideoTrackingModel> updateProgress({
    required String trackingId,
    required int watchedSeconds,
    required double percentageWatched,
  });

  /// Get existing tracking for a video
  ///
  /// Returns null if no tracking exists for this video yet
  Future<VideoTrackingModel?> getTracking(String videoId);

  /// Get video metadata
  ///
  /// Returns null if video info is not available
  Future<VideoInfoModel?> getVideoInfo(String videoId);

  /// Mark a video as complete
  ///
  /// Explicitly marks the video as completed regardless of watch time
  Future<VideoTrackingModel> markComplete(String trackingId);
}
