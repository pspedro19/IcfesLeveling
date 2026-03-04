import 'dart:async';
import '../utils/sync_logger.dart';

class RetryStrategy {
  int _retryCount = 0;
  Timer? _timer;

  void schedule(VoidCallback onRetry) {
    _timer?.cancel();
    _retryCount++;
    
    // Exponential backoff: 2s, 4s, 8s, 16s, max 1 min
    final seconds = (1 << _retryCount).clamp(2, 60);
    SyncLogger.log('sync_retry_scheduled', data: {'delay_seconds': seconds, 'attempt': _retryCount});
    
    _timer = Timer(Duration(seconds: seconds), onRetry);
  }

  void reset() {
    _timer?.cancel();
    _retryCount = 0;
  }

  void dispose() {
    _timer?.cancel();
  }
}

typedef VoidCallback = void Function();
