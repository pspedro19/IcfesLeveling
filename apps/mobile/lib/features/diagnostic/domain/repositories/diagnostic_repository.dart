import '../../data/models/deep_diagnostic_models.dart';

abstract class DiagnosticRepository {
  Future<DeepDiagnosticSessionModel> startDeepDiagnostic(String subjectId);
  Future<DeepDiagnosticResultsModel> submitDeepDiagnostic({
    required String diagnosticId,
    required List<Map<String, dynamic>> answers,
  });
}
