import 'dart:convert';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:hive_flutter/hive_flutter.dart';
import '../network/api_client.dart';
import '../constants/api_constants.dart';
import '../utils/sync_logger.dart';

/// Difficulty levels for questions
enum Difficulty {
  easy,
  medium,
  hard,
}

/// Service for caching questions offline.
///
/// Maintains a cache of 50 questions per subject area (250 total for 5 areas).
/// Cache is considered valid for 7 days.
class QuestionCacheService {
  static const String _boxName = 'question_cache_v2';
  static const String _metadataBoxName = 'question_cache_metadata';
  static const int _questionsPerArea = 50;
  static const int _cacheValidityDays = 7;

  /// Subject areas to cache (ICFES subjects)
  static const List<String> areas = [
    'matematicas',
    'lectura_critica',
    'sociales_ciudadanas',
    'ciencias_naturales',
    'ingles',
  ];

  Box? _questionsBox;
  Box? _metadataBox;
  bool _isInitialized = false;

  /// Initialize the cache service
  Future<void> init() async {
    if (_isInitialized) return;

    try {
      _questionsBox = await Hive.openBox(_boxName);
      _metadataBox = await Hive.openBox(_metadataBoxName);
      _isInitialized = true;
      SyncLogger.log('question_cache_initialized');
    } catch (e) {
      SyncLogger.log('question_cache_init_failed', error: e.toString());
      rethrow;
    }
  }

  /// Precache questions for a specific area
  ///
  /// Downloads [_questionsPerArea] questions for the given area and stores them locally.
  Future<void> precacheQuestionsForArea(String area, ApiClient apiClient) async {
    await init();

    try {
      SyncLogger.log('precache_start', data: {'area': area});

      final response = await apiClient.get(
        ApiConstants.batchQuestions,
        queryParameters: {
          'subject': area,
          'limit': _questionsPerArea,
          'include_all_difficulties': true,
        },
      );

      if (response.statusCode == 200 && response.data != null) {
        final data = response.data;
        List<dynamic> questions = [];

        if (data is Map && data['questions'] is List) {
          questions = data['questions'];
        } else if (data is List) {
          questions = data;
        }

        // Clear existing questions for this area
        await _clearAreaQuestions(area);

        // Store new questions
        for (var q in questions) {
          if (q != null && q['id'] != null) {
            final key = '${area}_${q['id']}';
            await _questionsBox!.put(key, jsonEncode(q));
          }
        }

        // Update metadata
        await _updateCacheMetadata(area, questions.length);

        SyncLogger.log('precache_complete', data: {
          'area': area,
          'count': questions.length,
        });
      }
    } catch (e) {
      SyncLogger.log('precache_failed', data: {'area': area}, error: e.toString());
      // Don't rethrow - caching is non-critical
    }
  }

  /// Precache questions for all areas
  Future<void> precacheAllAreas(ApiClient apiClient) async {
    await init();

    SyncLogger.log('precache_all_start');

    for (final area in areas) {
      if (!isCacheValid(area)) {
        await precacheQuestionsForArea(area, apiClient);
      }
    }

    SyncLogger.log('precache_all_complete', data: {
      'total_cached': await getTotalCachedCount(),
    });
  }

  /// Get a cached question for a specific area and difficulty
  ///
  /// Returns null if no matching question is found.
  Future<Map<String, dynamic>?> getCachedQuestion(
    String area,
    Difficulty difficulty,
  ) async {
    await init();

    final difficultyStr = difficulty.name;
    final areaQuestions = await _getAreaQuestions(area);

    // Filter by difficulty
    final matchingQuestions = areaQuestions.where((q) {
      final qDifficulty = q['difficulty']?.toString().toLowerCase();
      return qDifficulty == difficultyStr;
    }).toList();

    if (matchingQuestions.isEmpty) {
      // If no exact match, return any question from the area
      return areaQuestions.isNotEmpty ? areaQuestions.first : null;
    }

    // Return a random matching question
    matchingQuestions.shuffle();
    return matchingQuestions.first;
  }

  /// Get multiple cached questions for practice session
  Future<List<Map<String, dynamic>>> getCachedQuestions(
    String area, {
    int count = 10,
    Difficulty? difficulty,
  }) async {
    await init();

    var areaQuestions = await _getAreaQuestions(area);

    // Filter by difficulty if specified
    if (difficulty != null) {
      final difficultyStr = difficulty.name;
      areaQuestions = areaQuestions.where((q) {
        final qDifficulty = q['difficulty']?.toString().toLowerCase();
        return qDifficulty == difficultyStr;
      }).toList();
    }

    // Shuffle and take requested count
    areaQuestions.shuffle();
    return areaQuestions.take(count).toList();
  }

  /// Check if cache for an area is still valid (< 7 days old)
  bool isCacheValid(String area) {
    if (_metadataBox == null) return false;

    final metadataJson = _metadataBox!.get('metadata_$area');
    if (metadataJson == null) return false;

    try {
      final metadata = jsonDecode(metadataJson);
      final lastUpdated = DateTime.parse(metadata['last_updated']);
      final validUntil = lastUpdated.add(const Duration(days: _cacheValidityDays));

      return DateTime.now().isBefore(validUntil);
    } catch (e) {
      return false;
    }
  }

  /// Get the cache age in days for an area
  int? getCacheAgeDays(String area) {
    if (_metadataBox == null) return null;

    final metadataJson = _metadataBox!.get('metadata_$area');
    if (metadataJson == null) return null;

    try {
      final metadata = jsonDecode(metadataJson);
      final lastUpdated = DateTime.parse(metadata['last_updated']);
      return DateTime.now().difference(lastUpdated).inDays;
    } catch (e) {
      return null;
    }
  }

  /// Get total number of cached questions
  Future<int> getTotalCachedCount() async {
    await init();
    return _questionsBox?.length ?? 0;
  }

  /// Get number of cached questions for a specific area
  Future<int> getAreaCachedCount(String area) async {
    await init();
    return (await _getAreaQuestions(area)).length;
  }

  /// Get cache status for all areas
  Future<Map<String, CacheStatus>> getAllCacheStatus() async {
    await init();

    final status = <String, CacheStatus>{};
    for (final area in areas) {
      status[area] = CacheStatus(
        isValid: isCacheValid(area),
        questionCount: await getAreaCachedCount(area),
        ageDays: getCacheAgeDays(area),
      );
    }
    return status;
  }

  /// Mark a question as answered (move from cache)
  Future<void> markQuestionAnswered(String area, String questionId) async {
    await init();
    final key = '${area}_$questionId';
    await _questionsBox!.delete(key);
  }

  /// Clear all cached questions
  Future<void> clearAllCache() async {
    await init();
    await _questionsBox!.clear();
    await _metadataBox!.clear();
    SyncLogger.log('cache_cleared');
  }

  /// Clear cached questions for a specific area
  Future<void> _clearAreaQuestions(String area) async {
    final keysToDelete = _questionsBox!.keys
        .where((key) => key.toString().startsWith('${area}_'))
        .toList();

    for (final key in keysToDelete) {
      await _questionsBox!.delete(key);
    }
  }

  /// Get all questions for an area
  Future<List<Map<String, dynamic>>> _getAreaQuestions(String area) async {
    final questions = <Map<String, dynamic>>[];

    for (final key in _questionsBox!.keys) {
      if (key.toString().startsWith('${area}_')) {
        try {
          final q = jsonDecode(_questionsBox!.get(key));
          questions.add(Map<String, dynamic>.from(q));
        } catch (e) {
          // Skip invalid entries
        }
      }
    }

    return questions;
  }

  /// Update cache metadata for an area
  Future<void> _updateCacheMetadata(String area, int count) async {
    final metadata = {
      'last_updated': DateTime.now().toIso8601String(),
      'count': count,
    };
    await _metadataBox!.put('metadata_$area', jsonEncode(metadata));
  }
}

/// Status of the question cache for an area
class CacheStatus {
  final bool isValid;
  final int questionCount;
  final int? ageDays;

  const CacheStatus({
    required this.isValid,
    required this.questionCount,
    this.ageDays,
  });

  bool get isEmpty => questionCount == 0;
  bool get needsRefresh => !isValid || isEmpty;
}

/// Provider for QuestionCacheService
final questionCacheServiceProvider = Provider<QuestionCacheService>((ref) {
  return QuestionCacheService();
});

/// Provider for cache status
final cacheStatusProvider = FutureProvider<Map<String, CacheStatus>>((ref) async {
  final service = ref.watch(questionCacheServiceProvider);
  return service.getAllCacheStatus();
});
