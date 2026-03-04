import '../../../../core/network/api_client.dart';
import '../../../../core/constants/api_constants.dart';
import '../models/deep_diagnostic_models.dart';

class DiagnosticRemoteDataSource {
  final ApiClient _apiClient;

  DiagnosticRemoteDataSource(this._apiClient);

  Future<DeepDiagnosticSessionModel> startDeepDiagnostic(String subjectId) async {
    final response = await _apiClient.post('${ApiConstants.deepDiagnosticStart}/$subjectId');
    if (response.statusCode == 200) {
      return DeepDiagnosticSessionModel.fromJson(response.data['data']);
    } else {
      throw Exception('Failed to start deep diagnostic');
    }
  }

  Future<DeepDiagnosticResultsModel> submitDeepDiagnostic({
    required String diagnosticId,
    required List<Map<String, dynamic>> answers,
  }) async {
    final response = await _apiClient.post(
      ApiConstants.deepDiagnosticSubmit,
      data: {
        'diagnostic_id': diagnosticId,
        'answers': answers,
      },
    );
    if (response.statusCode == 200) {
      return DeepDiagnosticResultsModel.fromJson(response.data['data']);
    } else {
      throw Exception('Failed to submit deep diagnostic');
    }
  }
}
