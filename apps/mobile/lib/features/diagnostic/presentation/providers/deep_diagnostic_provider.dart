import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/network/api_client.dart';
import '../../data/datasources/diagnostic_remote_datasource.dart';
import '../../domain/repositories/diagnostic_repository.dart';
import '../../data/repositories/diagnostic_repository_impl.dart';
import '../../data/models/deep_diagnostic_models.dart';

// Presentation Layer Entities
class DeepDiagnosticState {
  final DeepDiagnosticSessionModel? session;
  final DeepDiagnosticResultsModel? results;
  final bool isLoading;
  final String? error;
  final Map<String, String> answers; // questionId -> answerId
  final Map<String, int> timeSpent; // questionId -> seconds spent

  DeepDiagnosticState({
    this.session,
    this.results,
    this.isLoading = false,
    this.error,
    this.answers = const {},
    this.timeSpent = const {},
  });

  DeepDiagnosticState copyWith({
    DeepDiagnosticSessionModel? session,
    DeepDiagnosticResultsModel? results,
    bool? isLoading,
    String? error,
    Map<String, String>? answers,
    Map<String, int>? timeSpent,
    bool clearResults = false,
    bool clearSession = false,
  }) {
    return DeepDiagnosticState(
      session: clearSession ? null : session ?? this.session,
      results: clearResults ? null : results ?? this.results,
      isLoading: isLoading ?? this.isLoading,
      error: error ?? this.error,
      answers: answers ?? this.answers,
      timeSpent: clearSession ? const {} : timeSpent ?? this.timeSpent,
    );
  }
}

// Data Layer Providers
final diagnosticRemoteDataSourceProvider = Provider.autoDispose((ref) {
  final apiClient = ref.watch(apiClientProvider);
  return DiagnosticRemoteDataSource(apiClient);
});

final diagnosticRepositoryProvider = Provider.autoDispose<DiagnosticRepository>((ref) {
  final remote = ref.watch(diagnosticRemoteDataSourceProvider);
  return DiagnosticRepositoryImpl(remote);
});

// Notifier
class DeepDiagnosticNotifier extends StateNotifier<DeepDiagnosticState> {
  final DiagnosticRepository _repository;
  final Stopwatch _questionStopwatch = Stopwatch();
  String? _currentQuestionId;

  DeepDiagnosticNotifier(this._repository) : super(DeepDiagnosticState());

  Future<void> startDiagnostic(String subjectId) async {
    state = state.copyWith(isLoading: true, error: null, clearSession: true, clearResults: true, answers: {}, timeSpent: {});
    _questionStopwatch.reset();
    _currentQuestionId = null;
    try {
      final sessionModel = await _repository.startDeepDiagnostic(subjectId);
      state = state.copyWith(isLoading: false, session: sessionModel);
      // Start timing the first question
      _questionStopwatch.start();
    } catch (e) {
      state = state.copyWith(isLoading: false, error: e.toString());
    }
  }

  /// Call this when navigating to a new question to track time
  void startQuestionTimer(String questionId) {
    // Save time for previous question if exists
    if (_currentQuestionId != null && _questionStopwatch.isRunning) {
      final elapsed = (_questionStopwatch.elapsedMilliseconds / 1000).ceil();
      final newTimeSpent = Map<String, int>.from(state.timeSpent);
      newTimeSpent[_currentQuestionId!] = (newTimeSpent[_currentQuestionId!] ?? 0) + elapsed;
      state = state.copyWith(timeSpent: newTimeSpent);
    }

    // Start new timer for this question
    _currentQuestionId = questionId;
    _questionStopwatch.reset();
    _questionStopwatch.start();
  }

  void answerQuestion(String questionId, String answerId) {
    // Stop timer and record time for this question
    _questionStopwatch.stop();
    final elapsed = (_questionStopwatch.elapsedMilliseconds / 1000).ceil();

    final newAnswers = Map<String, String>.from(state.answers);
    newAnswers[questionId] = answerId;

    final newTimeSpent = Map<String, int>.from(state.timeSpent);
    newTimeSpent[questionId] = (newTimeSpent[questionId] ?? 0) + elapsed;

    state = state.copyWith(answers: newAnswers, timeSpent: newTimeSpent);

    // Reset stopwatch for next question
    _questionStopwatch.reset();
    _questionStopwatch.start();
  }

  Future<void> submitDiagnostic() async {
    if (state.session == null) return;

    _questionStopwatch.stop();

    state = state.copyWith(isLoading: true, error: null);
    try {
      final answersPayload = state.answers.entries.map((entry) {
        final timeSpent = state.timeSpent[entry.key] ?? 10; // fallback to 10 if not tracked
        return {'question_id': entry.key, 'answer_id': entry.value, 'time_spent_seconds': timeSpent};
      }).toList();

      final resultsModel = await _repository.submitDeepDiagnostic(
        diagnosticId: state.session!.diagnosticId,
        answers: answersPayload,
      );
      state = state.copyWith(isLoading: false, results: resultsModel, clearSession: true);
    } catch (e) {
      state = state.copyWith(isLoading: false, error: e.toString());
    }
  }
}

// Main Provider
final deepDiagnosticProvider = StateNotifierProvider.autoDispose<DeepDiagnosticNotifier, DeepDiagnosticState>((ref) {
  final repo = ref.watch(diagnosticRepositoryProvider);
  return DeepDiagnosticNotifier(repo);
});
