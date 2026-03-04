import 'dart:async';
import 'dart:convert';
import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:hive_flutter/hive_flutter.dart';
import '../auth/data/datasources/auth_local_datasource.dart';
import '../constants/api_constants.dart';
import '../utils/sync_logger.dart';
import 'fallback_handler.dart';

/// Provider for the error recovery service
final errorRecoveryServiceProvider = Provider<ErrorRecoveryService>((ref) {
  return ErrorRecoveryService();
});

/// Service responsible for handling error recovery scenarios:
/// - JWT token refresh with silent reconnection
/// - Partial diagnostic progress saving
/// - League position preservation
/// - Session state recovery
class ErrorRecoveryService {
  static const String _diagnosticProgressBox = 'diagnostic_progress';
  static const String _leagueStateBox = 'league_state';
  static const String _sessionStateBox = 'session_state';

  // Stream controller for recovery status updates
  final _recoveryStatusController =
      StreamController<RecoveryStatus>.broadcast();

  Stream<RecoveryStatus> get recoveryStatus => _recoveryStatusController.stream;

  /// Attempts to silently refresh JWT token
  /// Returns true if refresh was successful, false otherwise
  Future<bool> handleJwtExpired(AuthLocalDataSource localDataSource) async {
    _emitStatus(RecoveryStatus.reconnecting, 'Reconectando...');
    SyncLogger.log('jwt_recovery_started');

    try {
      final refreshToken = await localDataSource.getRefreshToken();
      if (refreshToken == null) {
        SyncLogger.log('jwt_recovery_no_token', success: false);
        _emitStatus(RecoveryStatus.failed, 'No se pudo reconectar');
        return false;
      }

      final dio = Dio(BaseOptions(baseUrl: ApiConstants.baseUrl));
      final response = await dio.post(
        ApiConstants.authRefresh,
        data: {'refresh_token': refreshToken},
      );

      if (response.statusCode == 200) {
        final data = response.data;
        final newAccessToken = data['access_token'];
        final newRefreshToken = data['refresh_token'];

        await localDataSource.saveTokens(newAccessToken, newRefreshToken);
        SyncLogger.log('jwt_recovery_success');
        _emitStatus(RecoveryStatus.recovered, 'Reconectado');
        return true;
      }
    } catch (e) {
      SyncLogger.log('jwt_recovery_error', error: e.toString(), success: false);
    }

    // If refresh failed, clear tokens
    await localDataSource.clearTokens();
    _emitStatus(RecoveryStatus.failed, 'Sesion expirada');
    return false;
  }

  /// Saves partial diagnostic progress to local storage
  Future<void> saveDiagnosticProgress(DiagnosticProgress progress) async {
    try {
      final box = await Hive.openBox(_diagnosticProgressBox);
      await box.put(progress.sessionId, jsonEncode(progress.toJson()));
      SyncLogger.log('diagnostic_progress_saved', data: {
        'session_id': progress.sessionId,
        'questions_answered': progress.answeredQuestions.length,
      });
    } catch (e) {
      SyncLogger.log('diagnostic_progress_save_error',
          error: e.toString(), success: false);
    }
  }

  /// Retrieves saved diagnostic progress
  Future<DiagnosticProgress?> getDiagnosticProgress(String sessionId) async {
    try {
      final box = await Hive.openBox(_diagnosticProgressBox);
      final data = box.get(sessionId);
      if (data != null) {
        return DiagnosticProgress.fromJson(jsonDecode(data));
      }
    } catch (e) {
      SyncLogger.log('diagnostic_progress_load_error',
          error: e.toString(), success: false);
    }
    return null;
  }

  /// Clears saved diagnostic progress after successful submission
  Future<void> clearDiagnosticProgress(String sessionId) async {
    try {
      final box = await Hive.openBox(_diagnosticProgressBox);
      await box.delete(sessionId);
      SyncLogger.log('diagnostic_progress_cleared',
          data: {'session_id': sessionId});
    } catch (e) {
      SyncLogger.log('diagnostic_progress_clear_error',
          error: e.toString(), success: false);
    }
  }

  /// Saves current league position for recovery if processing fails
  Future<void> saveLeaguePosition(LeaguePosition position) async {
    try {
      final box = await Hive.openBox(_leagueStateBox);
      await box.put('current_position', jsonEncode(position.toJson()));
      SyncLogger.log('league_position_saved', data: {
        'league': position.leagueName,
        'rank': position.rank,
      });
    } catch (e) {
      SyncLogger.log('league_position_save_error',
          error: e.toString(), success: false);
    }
  }

  /// Retrieves previous league position
  Future<LeaguePosition?> getPreviousLeaguePosition() async {
    try {
      final box = await Hive.openBox(_leagueStateBox);
      final data = box.get('current_position');
      if (data != null) {
        return LeaguePosition.fromJson(jsonDecode(data));
      }
    } catch (e) {
      SyncLogger.log('league_position_load_error',
          error: e.toString(), success: false);
    }
    return null;
  }

  /// Handles league not processed error by showing previous position
  Future<LeaguePosition?> handleLeagueNotProcessed() async {
    _emitStatus(RecoveryStatus.recovering, 'Resultados en proceso...');
    final previousPosition = await getPreviousLeaguePosition();
    if (previousPosition != null) {
      _emitStatus(
          RecoveryStatus.recovered, 'Mostrando posicion anterior');
    } else {
      _emitStatus(RecoveryStatus.failed, 'No hay datos previos');
    }
    return previousPosition;
  }

  /// Saves current session state for recovery
  Future<void> saveSessionState(SessionState state) async {
    try {
      final box = await Hive.openBox(_sessionStateBox);
      await box.put('current_session', jsonEncode(state.toJson()));
    } catch (e) {
      SyncLogger.log('session_state_save_error',
          error: e.toString(), success: false);
    }
  }

  /// Retrieves saved session state
  Future<SessionState?> getSessionState() async {
    try {
      final box = await Hive.openBox(_sessionStateBox);
      final data = box.get('current_session');
      if (data != null) {
        return SessionState.fromJson(jsonDecode(data));
      }
    } catch (e) {
      SyncLogger.log('session_state_load_error',
          error: e.toString(), success: false);
    }
    return null;
  }

  /// Handles diagnostic timeout by saving progress
  Future<void> handleDiagnosticTimeout(DiagnosticProgress progress) async {
    _emitStatus(RecoveryStatus.recovering, 'Guardando progreso...');
    await saveDiagnosticProgress(progress);
    _emitStatus(RecoveryStatus.recovered, 'Progreso guardado');
    SyncLogger.log('diagnostic_timeout_recovered', data: {
      'session_id': progress.sessionId,
      'questions_saved': progress.answeredQuestions.length,
    });
  }

  /// Maps DioException to appropriate NetworkErrorType
  NetworkErrorType mapDioExceptionToType(DioException error) {
    switch (error.type) {
      case DioExceptionType.connectionTimeout:
      case DioExceptionType.sendTimeout:
      case DioExceptionType.receiveTimeout:
        return NetworkErrorType.timeout;

      case DioExceptionType.connectionError:
        return NetworkErrorType.noConnection;

      case DioExceptionType.badResponse:
        final statusCode = error.response?.statusCode;
        if (statusCode == 429) {
          return NetworkErrorType.rateLimited;
        } else if (statusCode == 409) {
          return NetworkErrorType.syncConflict;
        } else if (statusCode != null && statusCode >= 500) {
          return NetworkErrorType.serverError;
        }
        return NetworkErrorType.serverError;

      default:
        return NetworkErrorType.serverError;
    }
  }

  /// Maps error to appropriate StateErrorType
  StateErrorType? mapToStateError(dynamic error, int? statusCode) {
    if (statusCode == 401) {
      return StateErrorType.jwtExpired;
    } else if (statusCode == 403) {
      return StateErrorType.sessionExpired;
    }
    return null;
  }

  void _emitStatus(RecoveryStatus status, String message) {
    _recoveryStatusController.add(
      RecoveryStatusUpdate(status: status, message: message),
    );
  }

  void dispose() {
    _recoveryStatusController.close();
  }
}

/// Recovery status enumeration
enum RecoveryStatus {
  idle,
  reconnecting,
  recovering,
  recovered,
  failed,
}

/// Recovery status update with message
class RecoveryStatusUpdate implements RecoveryStatus {
  final RecoveryStatus status;
  final String message;

  RecoveryStatusUpdate({required this.status, required this.message});

  @override
  int get index => status.index;

  @override
  String toString() => message;
}

/// Model for partial diagnostic progress
class DiagnosticProgress {
  final String sessionId;
  final String subjectId;
  final List<AnsweredQuestion> answeredQuestions;
  final DateTime startedAt;
  final Duration elapsedTime;

  DiagnosticProgress({
    required this.sessionId,
    required this.subjectId,
    required this.answeredQuestions,
    required this.startedAt,
    required this.elapsedTime,
  });

  Map<String, dynamic> toJson() => {
        'session_id': sessionId,
        'subject_id': subjectId,
        'answered_questions':
            answeredQuestions.map((q) => q.toJson()).toList(),
        'started_at': startedAt.toIso8601String(),
        'elapsed_time': elapsedTime.inSeconds,
      };

  factory DiagnosticProgress.fromJson(Map<String, dynamic> json) {
    return DiagnosticProgress(
      sessionId: json['session_id'],
      subjectId: json['subject_id'],
      answeredQuestions: (json['answered_questions'] as List)
          .map((q) => AnsweredQuestion.fromJson(q))
          .toList(),
      startedAt: DateTime.parse(json['started_at']),
      elapsedTime: Duration(seconds: json['elapsed_time']),
    );
  }
}

/// Model for an answered question within diagnostic
class AnsweredQuestion {
  final String questionId;
  final String selectedAnswer;
  final Duration timeSpent;
  final bool isCorrect;

  AnsweredQuestion({
    required this.questionId,
    required this.selectedAnswer,
    required this.timeSpent,
    required this.isCorrect,
  });

  Map<String, dynamic> toJson() => {
        'question_id': questionId,
        'selected_answer': selectedAnswer,
        'time_spent': timeSpent.inSeconds,
        'is_correct': isCorrect,
      };

  factory AnsweredQuestion.fromJson(Map<String, dynamic> json) {
    return AnsweredQuestion(
      questionId: json['question_id'],
      selectedAnswer: json['selected_answer'],
      timeSpent: Duration(seconds: json['time_spent']),
      isCorrect: json['is_correct'],
    );
  }
}

/// Model for league position
class LeaguePosition {
  final String leagueName;
  final int rank;
  final int xp;
  final bool isPromotionZone;
  final bool isDemotionZone;
  final DateTime recordedAt;

  LeaguePosition({
    required this.leagueName,
    required this.rank,
    required this.xp,
    required this.isPromotionZone,
    required this.isDemotionZone,
    required this.recordedAt,
  });

  Map<String, dynamic> toJson() => {
        'league_name': leagueName,
        'rank': rank,
        'xp': xp,
        'is_promotion_zone': isPromotionZone,
        'is_demotion_zone': isDemotionZone,
        'recorded_at': recordedAt.toIso8601String(),
      };

  factory LeaguePosition.fromJson(Map<String, dynamic> json) {
    return LeaguePosition(
      leagueName: json['league_name'],
      rank: json['rank'],
      xp: json['xp'],
      isPromotionZone: json['is_promotion_zone'],
      isDemotionZone: json['is_demotion_zone'],
      recordedAt: DateTime.parse(json['recorded_at']),
    );
  }
}

/// Model for session state
class SessionState {
  final String? currentPage;
  final Map<String, dynamic>? pageState;
  final DateTime lastUpdated;

  SessionState({
    this.currentPage,
    this.pageState,
    required this.lastUpdated,
  });

  Map<String, dynamic> toJson() => {
        'current_page': currentPage,
        'page_state': pageState,
        'last_updated': lastUpdated.toIso8601String(),
      };

  factory SessionState.fromJson(Map<String, dynamic> json) {
    return SessionState(
      currentPage: json['current_page'],
      pageState: json['page_state'],
      lastUpdated: DateTime.parse(json['last_updated']),
    );
  }
}
