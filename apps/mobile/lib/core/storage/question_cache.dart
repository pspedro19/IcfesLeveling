import 'dart:convert';
import 'package:hive_flutter/hive_flutter.dart';
import '../network/api_client.dart';
import '../constants/api_constants.dart';
import '../utils/sync_logger.dart';

class QuestionCache {
  static const _boxName = 'question_cache';
  static const _minCacheSize = 50;

  Box? _box;

  Future<void> init() async {
    _box = await Hive.openBox(_boxName);
  }

  /// Warm up the cache by downloading a batch of questions
  Future<void> warmUp(ApiClient apiClient) async {
    if (_box == null) await init();
    
    if (_box!.length >= _minCacheSize) return;

    try {
      final response = await apiClient.get(
        ApiConstants.batchQuestions,
        queryParameters: {'limit': _minCacheSize},
      );

      if (response.statusCode == 200 && response.data != null) {
        final data = response.data;
        if (data is Map && data['questions'] is List) {
          final List questions = data['questions'];
          for (var q in questions) {
            if (q != null && q['id'] != null) {
              await _box!.put(q['id'], jsonEncode(q));
            }
          }
        }
      }
    } catch (e) {
      // Silent fail - will use existing cache if any
      SyncLogger.log('question_cache_warmup_failed', error: e.toString(), success: false);
    }
  }

  Future<List<Map<String, dynamic>>> getCachedQuestions({String? subjectId}) async {
    if (_box == null) await init();
    
    final List<Map<String, dynamic>> results = [];
    for (var key in _box!.keys) {
      final q = jsonDecode(_box!.get(key));
      if (subjectId == null || q['subject_id'] == subjectId) {
        results.add(Map<String, dynamic>.from(q));
      }
    }
    return results;
  }

  Future<void> markAnswered(String questionId) async {
    if (_box == null) await init();
    // In a real app, we might move it to an 'answered' box or update metadata
    await _box!.delete(questionId);
  }
}
