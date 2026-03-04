import '../../domain/repositories/diagnostic_repository.dart';
import '../datasources/diagnostic_remote_datasource.dart';
import '../models/deep_diagnostic_models.dart';

class DiagnosticRepositoryImpl implements DiagnosticRepository {
  final DiagnosticRemoteDataSource remoteDataSource;

  DiagnosticRepositoryImpl(this.remoteDataSource);

  @override
  Future<DeepDiagnosticSessionModel> startDeepDiagnostic(String subjectId) async {
    return await remoteDataSource.startDeepDiagnostic(subjectId);
  }

  @override
  Future<DeepDiagnosticResultsModel> submitDeepDiagnostic({
    required String diagnosticId,
    required List<Map<String, dynamic>> answers,
  }) async {
    return await remoteDataSource.submitDeepDiagnostic(
      diagnosticId: diagnosticId,
      answers: answers,
    );
  }
}
