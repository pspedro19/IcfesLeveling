import '../../domain/repositories/video_repository.dart';
import '../datasources/video_remote_datasource.dart';
import '../models/video_tracking_model.dart';

/// Concrete implementation of [VideoRepository]
///
/// Handles video tracking operations by delegating to the remote datasource.
/// In the future, this could also include local caching for offline support.
class VideoRepositoryImpl implements VideoRepository {
  final VideoRemoteDataSource _remoteDataSource;

  VideoRepositoryImpl(this._remoteDataSource);

  @override
  Future<VideoTrackingModel> createTracking({
    required String videoId,
    String? planId,
    int? unitNumber,
  }) async {
    return await _remoteDataSource.createTracking(
      videoId: videoId,
      planId: planId,
      unitNumber: unitNumber,
    );
  }

  @override
  Future<VideoTrackingModel> updateProgress({
    required String trackingId,
    required int watchedSeconds,
    required double percentageWatched,
  }) async {
    return await _remoteDataSource.updateProgress(
      trackingId: trackingId,
      watchedSeconds: watchedSeconds,
      percentageWatched: percentageWatched,
    );
  }

  @override
  Future<VideoTrackingModel?> getTracking(String videoId) async {
    return await _remoteDataSource.getTracking(videoId);
  }

  @override
  Future<VideoInfoModel?> getVideoInfo(String videoId) async {
    return await _remoteDataSource.getVideoInfo(videoId);
  }

  @override
  Future<VideoTrackingModel> markComplete(String trackingId) async {
    return await _remoteDataSource.markComplete(trackingId);
  }
}
