import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../storage/question_cache.dart';

final questionCacheProvider = Provider<QuestionCache>((ref) {
  return QuestionCache();
});
