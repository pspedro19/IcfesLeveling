import '../../domain/repositories/spaced_repetition_repository.dart';
import '../datasources/spaced_repetition_remote_datasource.dart';
import '../models/spaced_repetition_models.dart';

/// Implementation of SpacedRepetitionRepository
/// Handles all spaced repetition operations using SM-2 algorithm
class SpacedRepetitionRepositoryImpl implements SpacedRepetitionRepository {
  final SpacedRepetitionRemoteDataSource remoteDataSource;

  SpacedRepetitionRepositoryImpl(this.remoteDataSource);

  @override
  Future<DailyReviewsResponse> getDailyReviews({DateTime? date}) async {
    try {
      return await remoteDataSource.getDailyReviews(date: date);
    } catch (e) {
      // Return empty response on error to prevent UI crashes
      // Errors should be logged and handled appropriately
      rethrow;
    }
  }

  @override
  Future<SubmitReviewResponse> submitReview({
    required String itemId,
    required ReviewResult result,
    required int responseTimeMs,
    String? selectedAnswer,
  }) async {
    try {
      return await remoteDataSource.submitReview(
        itemId: itemId,
        result: result,
        responseTimeMs: responseTimeMs,
        selectedAnswer: selectedAnswer,
      );
    } catch (e) {
      rethrow;
    }
  }

  @override
  Future<RetentionAnalytics> getAnalytics({int daysBack = 30}) async {
    try {
      return await remoteDataSource.getAnalytics(daysBack: daysBack);
    } catch (e) {
      // Return empty analytics on error
      rethrow;
    }
  }

  @override
  Future<CreateScheduleResponse> createSchedule({
    required String planId,
    int newCardsPerDay = 20,
    int maxReviewsPerDay = 100,
  }) async {
    try {
      return await remoteDataSource.createSchedule(
        planId: planId,
        newCardsPerDay: newCardsPerDay,
        maxReviewsPerDay: maxReviewsPerDay,
      );
    } catch (e) {
      rethrow;
    }
  }

  @override
  Future<List<SpacedItem>> getItems({
    SpacedItemStatus? status,
    String? subjectId,
  }) async {
    try {
      return await remoteDataSource.getItems(
        status: status,
        subjectId: subjectId,
      );
    } catch (e) {
      rethrow;
    }
  }

  @override
  Future<SpacedItem> addItem({
    required String questionId,
    String? subjectId,
    String? topicId,
  }) async {
    try {
      return await remoteDataSource.addItem(
        questionId: questionId,
        subjectId: subjectId,
        topicId: topicId,
      );
    } catch (e) {
      rethrow;
    }
  }
}
