import '../../data/models/spaced_repetition_models.dart';

/// Repository interface for Spaced Repetition (SM-2) operations
abstract class SpacedRepetitionRepository {
  /// Get daily reviews due for the specified date (defaults to today)
  /// Returns items that are due or overdue for review
  Future<DailyReviewsResponse> getDailyReviews({DateTime? date});

  /// Submit a review result for a spaced repetition item
  /// [itemId] - The unique identifier of the spaced item
  /// [result] - The review result (again, hard, good, easy)
  /// [responseTimeMs] - Time taken to answer in milliseconds
  /// [selectedAnswer] - The answer option selected by the user
  Future<SubmitReviewResponse> submitReview({
    required String itemId,
    required ReviewResult result,
    required int responseTimeMs,
    String? selectedAnswer,
  });

  /// Get retention analytics for the user
  /// [daysBack] - Number of days to look back for statistics (default 30)
  Future<RetentionAnalytics> getAnalytics({int daysBack = 30});

  /// Create a spaced repetition schedule from a study plan
  /// [planId] - The study plan to create schedule from
  /// [newCardsPerDay] - Maximum new cards to introduce per day
  /// [maxReviewsPerDay] - Maximum total reviews per day
  Future<CreateScheduleResponse> createSchedule({
    required String planId,
    int newCardsPerDay = 20,
    int maxReviewsPerDay = 100,
  });

  /// Get all spaced repetition items for the user
  /// [status] - Filter by item status (optional)
  /// [subjectId] - Filter by subject (optional)
  Future<List<SpacedItem>> getItems({
    SpacedItemStatus? status,
    String? subjectId,
  });

  /// Add a question to the spaced repetition queue
  /// This is called when a user answers a question incorrectly
  /// to ensure it's reviewed again using spaced repetition
  Future<SpacedItem> addItem({
    required String questionId,
    String? subjectId,
    String? topicId,
  });
}
