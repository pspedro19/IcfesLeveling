import '../../../../core/network/api_client.dart';
import '../../../../core/constants/api_constants.dart';
import '../models/video_tracking_model.dart';

/// Remote datasource for video tracking operations
///
/// Handles all HTTP communication with the backend
/// for video progress tracking endpoints.
class VideoRemoteDataSource {
  final ApiClient _apiClient;

  VideoRemoteDataSource(this._apiClient);

  /// Create a new tracking entry for a video
  ///
  /// Called when user starts watching a video for the first time
  /// or when resuming a video that doesn't have tracking yet.
  Future<VideoTrackingModel> createTracking({
    required String videoId,
    String? planId,
    int? unitNumber,
  }) async {
    final request = CreateTrackingRequest(
      videoId: videoId,
      planId: planId,
      unitNumber: unitNumber,
    );

    final response = await _apiClient.post(
      ApiConstants.videoTracking,
      data: request.toJson(),
    );

    if (response.statusCode == 200 || response.statusCode == 201) {
      final data = response.data;
      // Handle both direct response and wrapped response
      final trackingData = data['data'] ?? data;
      return VideoTrackingModel.fromJson(trackingData);
    } else {
      throw Exception('Failed to create video tracking: ${response.statusCode}');
    }
  }

  /// Update progress for an existing tracking entry
  ///
  /// Called periodically while user is watching to save progress.
  /// Also handles marking video as complete when percentage >= 80%.
  Future<VideoTrackingModel> updateProgress({
    required String trackingId,
    required int watchedSeconds,
    required double percentageWatched,
  }) async {
    final request = UpdateProgressRequest(
      trackingId: trackingId,
      watchedSeconds: watchedSeconds,
      percentageWatched: percentageWatched,
    );

    final response = await _apiClient.put(
      '${ApiConstants.videoProgress}/$trackingId',
      data: request.toJson(),
    );

    if (response.statusCode == 200) {
      final data = response.data;
      final trackingData = data['data'] ?? data;
      return VideoTrackingModel.fromJson(trackingData);
    } else {
      throw Exception('Failed to update video progress: ${response.statusCode}');
    }
  }

  /// Get existing tracking for a video
  ///
  /// Returns null if no tracking exists yet.
  Future<VideoTrackingModel?> getTracking(String videoId) async {
    try {
      final response = await _apiClient.get(
        '${ApiConstants.videoTracking}/$videoId',
      );

      if (response.statusCode == 200) {
        final data = response.data;
        if (data == null || (data['data'] == null && data['id'] == null)) {
          return null;
        }
        final trackingData = data['data'] ?? data;
        return VideoTrackingModel.fromJson(trackingData);
      }
      return null;
    } catch (e) {
      // Video tracking might not exist yet, which is fine
      return null;
    }
  }

  /// Get video info by ID
  ///
  /// Fetches metadata about the video (title, description, etc.)
  Future<VideoInfoModel?> getVideoInfo(String videoId) async {
    try {
      final response = await _apiClient.get(
        '/videos/$videoId',
      );

      if (response.statusCode == 200) {
        final data = response.data;
        final videoData = data['data'] ?? data;
        return VideoInfoModel.fromJson(videoData);
      }
      return null;
    } catch (e) {
      // Video info might not be available
      return null;
    }
  }

  /// Mark video as complete
  ///
  /// Explicitly marks a video as completed, useful when user
  /// finishes watching or skips to end.
  Future<VideoTrackingModel> markComplete(String trackingId) async {
    final response = await _apiClient.post(
      '${ApiConstants.videoTracking}/$trackingId/complete',
    );

    if (response.statusCode == 200) {
      final data = response.data;
      final trackingData = data['data'] ?? data;
      return VideoTrackingModel.fromJson(trackingData);
    } else {
      throw Exception('Failed to mark video as complete: ${response.statusCode}');
    }
  }
}
