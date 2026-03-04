import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/network/api_client.dart';
import '../../data/datasources/video_remote_datasource.dart';
import '../../domain/repositories/video_repository.dart';
import '../../data/repositories/video_repository_impl.dart';
import '../../data/models/video_tracking_model.dart';

// ============================================================================
// State Classes
// ============================================================================

/// State for video info and completion tracking
class VideoPlayerState {
  final VideoTrackingModel? tracking;
  final VideoInfoModel? videoInfo;
  final bool isLoading;
  final String? error;
  final bool isCompleted;

  const VideoPlayerState({
    this.tracking,
    this.videoInfo,
    this.isLoading = false,
    this.error,
    this.isCompleted = false,
  });

  VideoPlayerState copyWith({
    VideoTrackingModel? tracking,
    VideoInfoModel? videoInfo,
    bool? isLoading,
    String? error,
    bool? isCompleted,
    bool clearError = false,
  }) {
    return VideoPlayerState(
      tracking: tracking ?? this.tracking,
      videoInfo: videoInfo ?? this.videoInfo,
      isLoading: isLoading ?? this.isLoading,
      error: clearError ? null : (error ?? this.error),
      isCompleted: isCompleted ?? this.isCompleted,
    );
  }
}

// ============================================================================
// Data Layer Providers
// ============================================================================

/// Provider for the video remote data source
final videoRemoteDataSourceProvider = Provider.autoDispose((ref) {
  final apiClient = ref.watch(apiClientProvider);
  return VideoRemoteDataSource(apiClient);
});

/// Provider for the video repository
final videoRepositoryProvider = Provider.autoDispose<VideoRepository>((ref) {
  final remote = ref.watch(videoRemoteDataSourceProvider);
  return VideoRepositoryImpl(remote);
});

// ============================================================================
// State Notifier
// ============================================================================

/// Notifier for managing video tracking state (external YouTube redirect model)
class VideoPlayerNotifier extends StateNotifier<VideoPlayerState> {
  final VideoRepository _repository;
  final String _videoId;
  final String? _planId;
  final int? _unitNumber;

  VideoPlayerNotifier(
    this._repository,
    this._videoId, {
    String? planId,
    int? unitNumber,
  })  : _planId = planId,
        _unitNumber = unitNumber,
        super(const VideoPlayerState(isLoading: true)) {
    _initialize();
  }

  /// Initialize: fetch existing tracking and video info
  Future<void> _initialize() async {
    try {
      final existingTracking = await _repository.getTracking(_videoId);
      final videoInfo = await _repository.getVideoInfo(_videoId);

      if (existingTracking != null) {
        state = state.copyWith(
          tracking: existingTracking,
          videoInfo: videoInfo,
          isCompleted: existingTracking.completed,
          isLoading: false,
        );
      } else {
        final newTracking = await _repository.createTracking(
          videoId: _videoId,
          planId: _planId,
          unitNumber: _unitNumber,
        );
        state = state.copyWith(
          tracking: newTracking,
          videoInfo: videoInfo,
          isLoading: false,
        );
      }
    } catch (e) {
      debugPrint('Error initializing video: $e');
      state = state.copyWith(
        isLoading: false,
        error: 'No se pudo cargar la informacion del video.',
      );
    }
  }

  /// Mark the video as watched (called by user tapping the button)
  Future<bool> markAsWatched() async {
    final tracking = state.tracking;
    if (tracking == null || state.isCompleted) return false;

    try {
      final updatedTracking = await _repository.markComplete(tracking.id);
      state = state.copyWith(
        tracking: updatedTracking,
        isCompleted: true,
      );
      return true;
    } catch (e) {
      debugPrint('Error marking video complete: $e');
      // Mark as complete locally even if API fails
      state = state.copyWith(isCompleted: true);
      return true;
    }
  }

  /// Retry initialization if it failed
  Future<void> retry() async {
    state = state.copyWith(isLoading: true, clearError: true);
    await _initialize();
  }

  /// Clear any error message
  void clearError() {
    state = state.copyWith(clearError: true);
  }
}

// ============================================================================
// Main Provider
// ============================================================================

/// Provider family for video player - creates a notifier per video ID
final videoPlayerProvider = StateNotifierProvider.autoDispose
    .family<VideoPlayerNotifier, VideoPlayerState, VideoPlayerParams>((ref, params) {
  final repository = ref.watch(videoRepositoryProvider);
  return VideoPlayerNotifier(
    repository,
    params.videoId,
    planId: params.planId,
    unitNumber: params.unitNumber,
  );
});

/// Parameters for the video player provider
class VideoPlayerParams {
  final String videoId;
  final String? planId;
  final int? unitNumber;

  const VideoPlayerParams({
    required this.videoId,
    this.planId,
    this.unitNumber,
  });

  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      other is VideoPlayerParams &&
          runtimeType == other.runtimeType &&
          videoId == other.videoId &&
          planId == other.planId &&
          unitNumber == other.unitNumber;

  @override
  int get hashCode => videoId.hashCode ^ planId.hashCode ^ unitNumber.hashCode;
}
