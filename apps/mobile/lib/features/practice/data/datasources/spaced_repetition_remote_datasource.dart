import '../../../../core/network/api_client.dart';
import '../../../../core/constants/api_constants.dart';
import '../models/spaced_repetition_models.dart';

/// Remote data source for Spaced Repetition API calls
class SpacedRepetitionRemoteDataSource {
  final ApiClient _apiClient;

  SpacedRepetitionRemoteDataSource(this._apiClient);

  /// Fetch daily reviews due for a specific date
  Future<DailyReviewsResponse> getDailyReviews({DateTime? date}) async {
    final queryParams = <String, dynamic>{};
    if (date != null) {
      queryParams['date'] = date.toIso8601String().split('T')[0];
    }

    final response = await _apiClient.get(
      ApiConstants.spacedRepetitionDailyReviews,
      queryParameters: queryParams.isNotEmpty ? queryParams : null,
    );

    if (response.statusCode == 200) {
      return DailyReviewsResponse.fromJson(response.data);
    } else {
      throw Exception('Failed to get daily reviews: ${response.statusCode}');
    }
  }

  /// Submit a review for a spaced repetition item
  Future<SubmitReviewResponse> submitReview({
    required String itemId,
    required ReviewResult result,
    required int responseTimeMs,
    String? selectedAnswer,
  }) async {
    final response = await _apiClient.post(
      ApiConstants.spacedRepetitionSubmitReview,
      data: {
        'item_id': itemId,
        'result': result.apiValue,
        'quality': result.quality,
        'response_time_ms': responseTimeMs,
        if (selectedAnswer != null) 'selected_answer': selectedAnswer,
      },
    );

    if (response.statusCode == 200) {
      return SubmitReviewResponse.fromJson(response.data);
    } else {
      throw Exception('Failed to submit review: ${response.statusCode}');
    }
  }

  /// Get retention analytics
  Future<RetentionAnalytics> getAnalytics({int daysBack = 30}) async {
    final response = await _apiClient.get(
      ApiConstants.spacedRepetitionAnalytics,
      queryParameters: {'days_back': daysBack},
    );

    if (response.statusCode == 200) {
      return RetentionAnalytics.fromJson(response.data);
    } else {
      throw Exception('Failed to get analytics: ${response.statusCode}');
    }
  }

  /// Create a spaced repetition schedule from a study plan
  Future<CreateScheduleResponse> createSchedule({
    required String planId,
    int newCardsPerDay = 20,
    int maxReviewsPerDay = 100,
  }) async {
    final response = await _apiClient.post(
      ApiConstants.spacedRepetitionCreateSchedule,
      data: CreateScheduleRequest(
        planId: planId,
        newCardsPerDay: newCardsPerDay,
        maxReviewsPerDay: maxReviewsPerDay,
      ).toJson(),
    );

    if (response.statusCode == 200 || response.statusCode == 201) {
      return CreateScheduleResponse.fromJson(response.data);
    } else {
      throw Exception('Failed to create schedule: ${response.statusCode}');
    }
  }

  /// Get all spaced repetition items
  Future<List<SpacedItem>> getItems({
    SpacedItemStatus? status,
    String? subjectId,
  }) async {
    final queryParams = <String, dynamic>{};
    if (status != null) {
      queryParams['status'] = status.apiValue;
    }
    if (subjectId != null) {
      queryParams['subject_id'] = subjectId;
    }

    final response = await _apiClient.get(
      ApiConstants.spacedRepetitionItems,
      queryParameters: queryParams.isNotEmpty ? queryParams : null,
    );

    if (response.statusCode == 200) {
      final data = response.data['data'] ?? response.data;
      final items = data['items'] ?? data;
      if (items is List) {
        return items.map((item) => SpacedItem.fromJson(item)).toList();
      }
      return [];
    } else {
      throw Exception('Failed to get items: ${response.statusCode}');
    }
  }

  /// Add a question to the spaced repetition queue
  Future<SpacedItem> addItem({
    required String questionId,
    String? subjectId,
    String? topicId,
  }) async {
    final response = await _apiClient.post(
      ApiConstants.spacedRepetitionItems,
      data: {
        'question_id': questionId,
        if (subjectId != null) 'subject_id': subjectId,
        if (topicId != null) 'topic_id': topicId,
      },
    );

    if (response.statusCode == 200 || response.statusCode == 201) {
      final data = response.data['data'] ?? response.data;
      return SpacedItem.fromJson(data);
    } else {
      throw Exception('Failed to add item: ${response.statusCode}');
    }
  }
}
