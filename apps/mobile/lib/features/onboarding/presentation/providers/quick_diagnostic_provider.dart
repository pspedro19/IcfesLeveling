import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/network/api_client.dart';
import '../../../../core/constants/api_constants.dart';
import '../../../practice/domain/entities/question.dart';
import '../../../practice/data/models/question_model.dart';

// Results model for quick diagnostic
class QuickDiagnosticResults {
  final int correct;
  final int total;
  final Map<String, double> subjectMastery; // subjectId -> mastery (0-1)
  final String assignedRank;

  QuickDiagnosticResults({
    required this.correct,
    required this.total,
    required this.subjectMastery,
    required this.assignedRank,
  });

  factory QuickDiagnosticResults.fromJson(Map<String, dynamic> json) {
    final masteryMap = <String, double>{};
    if (json['subject_mastery'] != null) {
      (json['subject_mastery'] as Map<String, dynamic>).forEach((key, value) {
        masteryMap[key] = (value as num).toDouble();
      });
    }
    return QuickDiagnosticResults(
      correct: json['correct'] ?? 0,
      total: json['total'] ?? 0,
      subjectMastery: masteryMap,
      assignedRank: json['assigned_rank'] ?? 'E',
    );
  }

  /// Get mastery values as a list for radar chart (5 subjects)
  List<double> get masteryValues {
    const subjects = ['lectura_critica', 'matematicas', 'ciencias_naturales', 'sociales_ciudadanas', 'ingles'];
    return subjects.map((s) => subjectMastery[s] ?? 0.5).toList();
  }
}

// 1. State
class QuickDiagnosticState {
  final bool isLoading;
  final String? error;
  final List<Question> questions;
  final int currentIndex;
  final Map<String, String> answers; // questionId -> optionId
  final bool isFinished;
  final QuickDiagnosticResults? results;

  QuickDiagnosticState({
    this.isLoading = true,
    this.error,
    this.questions = const [],
    this.currentIndex = 0,
    this.answers = const {},
    this.isFinished = false,
    this.results,
  });

  Question? get currentQuestion =>
      questions.isNotEmpty && currentIndex < questions.length
          ? questions[currentIndex]
          : null;

  QuickDiagnosticState copyWith({
    bool? isLoading,
    String? error,
    List<Question>? questions,
    int? currentIndex,
    Map<String, String>? answers,
    bool? isFinished,
    QuickDiagnosticResults? results,
  }) {
    return QuickDiagnosticState(
      isLoading: isLoading ?? this.isLoading,
      error: error, // Don't carry over old errors
      questions: questions ?? this.questions,
      currentIndex: currentIndex ?? this.currentIndex,
      answers: answers ?? this.answers,
      isFinished: isFinished ?? this.isFinished,
      results: results ?? this.results,
    );
  }
}

// 2. Notifier
class QuickDiagnosticNotifier extends StateNotifier<QuickDiagnosticState> {
  final ApiClient _apiClient;

  QuickDiagnosticNotifier(this._apiClient) : super(QuickDiagnosticState()) {
    startDiagnostic();
  }

  Future<void> startDiagnostic() async {
    state = state.copyWith(isLoading: true, error: null);
    try {
      final response = await _apiClient.post(ApiConstants.quickDiagnosticStart);
      
      if (response.statusCode == 200 && response.data['questions'] != null) {
        final List<dynamic> questionData = response.data['questions'];
        final questions = questionData.map((data) => QuestionModel.fromJson(data)).toList();
        state = state.copyWith(isLoading: false, questions: questions);
      } else {
        throw Exception('Failed to load diagnostic questions');
      }
    } catch (e) {
      state = state.copyWith(isLoading: false, error: e.toString());
    }
  }

  void answerQuestion(String questionId, String optionId) {
    final newAnswers = Map<String, String>.from(state.answers);
    newAnswers[questionId] = optionId;
    
    state = state.copyWith(answers: newAnswers);

    if (state.currentIndex < state.questions.length - 1) {
      state = state.copyWith(currentIndex: state.currentIndex + 1);
    } else {
      // Last question answered, now we can submit
      finishDiagnostic();
    }
  }

  Future<void> finishDiagnostic() async {
    state = state.copyWith(isLoading: true, error: null);
    try {
      final formattedAnswers = state.answers.entries.map((e) => {'question_id': e.key, 'answer': e.value}).toList();

      final response = await _apiClient.post(
        ApiConstants.quickDiagnosticSubmit,
        data: {'answers': formattedAnswers},
      );

      QuickDiagnosticResults? results;
      if (response.statusCode == 200 && response.data != null) {
        final data = response.data['data'] ?? response.data;
        results = QuickDiagnosticResults.fromJson(data);
      }

      state = state.copyWith(isLoading: false, isFinished: true, results: results);
    } catch (e) {
      state = state.copyWith(isLoading: false, error: e.toString());
    }
  }
}

// 3. Provider
final quickDiagnosticProvider =
    StateNotifierProvider<QuickDiagnosticNotifier, QuickDiagnosticState>((ref) {
  final apiClient = ref.watch(apiClientProvider);
  return QuickDiagnosticNotifier(apiClient);
});
