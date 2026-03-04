import '../../domain/entities/dungeon_gate.dart';
import '../../domain/entities/dungeon_node.dart';
import '../datasources/dungeon_remote_datasource.dart';
import '../models/dungeon_models.dart';

/// Abstract repository interface for dungeon operations
abstract class DungeonRepository {
  /// Get all available dungeon gates
  /// [gateType] - Filter by type: 'normal', 'boss', 'seasonal'
  /// [difficulty] - Filter by difficulty rank: 'D', 'C', 'B', 'A', 'S'
  Future<List<DungeonGate>> getAvailableGates({
    String? gateType,
    String? difficulty,
  });

  /// Enter a dungeon gate and start a new run
  Future<DungeonRunResponse> enterGate(String gateId);

  /// Get the current active dungeon run if any
  Future<DungeonRunResponse?> getCurrentRun();

  /// Get questions for a specific encounter
  Future<DungeonEncounterModel> getEncounterQuestions(String encounterId);

  /// Submit a single answer for an encounter question
  Future<EncounterResultModel> submitAnswer({
    required String encounterId,
    required String questionId,
    required String answerId,
    int? timeSpentSeconds,
  });

  /// Submit multiple answers for an encounter (batch)
  Future<EncounterResultModel> submitAnswers(
    String encounterId,
    List<AnswerSubmission> answers,
  );

  /// Complete or abandon a dungeon run
  Future<DungeonCompletionModel> completeRun({
    required String runId,
    bool abandon = false,
  });

  /// Get dungeon run history
  Future<List<DungeonRunHistoryModel>> getHistory({int limit = 10});

  /// Use an item during dungeon run
  Future<void> useItem({
    required String runId,
    required String itemId,
  });

  /// Request a hint for current question
  Future<String> requestHint({
    required String encounterId,
    required String questionId,
  });
}

/// Implementation of DungeonRepository using remote data source
class DungeonRepositoryImpl implements DungeonRepository {
  final DungeonRemoteDataSource _remoteDataSource;

  DungeonRepositoryImpl(this._remoteDataSource);

  @override
  Future<List<DungeonGate>> getAvailableGates({
    String? gateType,
    String? difficulty,
  }) async {
    try {
      final response = await _remoteDataSource.getAvailableGates(
        gateType: gateType,
        difficulty: difficulty,
      );
      return response.gates.map((g) => g.toEntity()).toList();
    } on DungeonApiException {
      rethrow;
    } catch (e) {
      throw DungeonApiException('Failed to fetch gates: $e');
    }
  }

  @override
  Future<DungeonRunResponse> enterGate(String gateId) async {
    try {
      return await _remoteDataSource.enterGate(gateId);
    } on DungeonApiException {
      rethrow;
    } catch (e) {
      throw DungeonApiException('Failed to enter gate: $e');
    }
  }

  @override
  Future<DungeonRunResponse?> getCurrentRun() async {
    try {
      return await _remoteDataSource.getCurrentRun();
    } on DungeonApiException {
      rethrow;
    } catch (e) {
      throw DungeonApiException('Failed to get current run: $e');
    }
  }

  @override
  Future<DungeonEncounterModel> getEncounterQuestions(String encounterId) async {
    try {
      return await _remoteDataSource.getEncounterQuestions(encounterId);
    } on DungeonApiException {
      rethrow;
    } catch (e) {
      throw DungeonApiException('Failed to get encounter questions: $e');
    }
  }

  @override
  Future<EncounterResultModel> submitAnswer({
    required String encounterId,
    required String questionId,
    required String answerId,
    int? timeSpentSeconds,
  }) async {
    try {
      return await _remoteDataSource.submitAnswer(
        encounterId: encounterId,
        questionId: questionId,
        answerId: answerId,
        timeSpentSeconds: timeSpentSeconds,
      );
    } on DungeonApiException {
      rethrow;
    } catch (e) {
      throw DungeonApiException('Failed to submit answer: $e');
    }
  }

  @override
  Future<EncounterResultModel> submitAnswers(
    String encounterId,
    List<AnswerSubmission> answers,
  ) async {
    try {
      return await _remoteDataSource.submitAnswers(
        encounterId: encounterId,
        answers: answers,
      );
    } on DungeonApiException {
      rethrow;
    } catch (e) {
      throw DungeonApiException('Failed to submit answers: $e');
    }
  }

  @override
  Future<DungeonCompletionModel> completeRun({
    required String runId,
    bool abandon = false,
  }) async {
    try {
      return await _remoteDataSource.completeRun(
        runId: runId,
        abandon: abandon,
      );
    } on DungeonApiException {
      rethrow;
    } catch (e) {
      throw DungeonApiException('Failed to complete run: $e');
    }
  }

  @override
  Future<List<DungeonRunHistoryModel>> getHistory({int limit = 10}) async {
    try {
      return await _remoteDataSource.getHistory(limit: limit);
    } on DungeonApiException {
      rethrow;
    } catch (e) {
      throw DungeonApiException('Failed to get history: $e');
    }
  }

  @override
  Future<void> useItem({
    required String runId,
    required String itemId,
  }) async {
    try {
      return await _remoteDataSource.useItem(runId: runId, itemId: itemId);
    } on DungeonApiException {
      rethrow;
    } catch (e) {
      throw DungeonApiException('Failed to use item: $e');
    }
  }

  @override
  Future<String> requestHint({
    required String encounterId,
    required String questionId,
  }) async {
    try {
      return await _remoteDataSource.requestHint(
        encounterId: encounterId,
        questionId: questionId,
      );
    } on DungeonApiException {
      rethrow;
    } catch (e) {
      throw DungeonApiException('Failed to get hint: $e');
    }
  }
}
