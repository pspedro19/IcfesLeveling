import 'package:dio/dio.dart';
import '../../sync/action_queue.dart';
import '../../sync/sync_action.dart';

class OfflineInterceptor extends Interceptor {
  final ActionQueue _actionQueue;

  OfflineInterceptor(this._actionQueue);

  // Endpoints that should be queued when offline
  static const _queueableEndpoints = [
    '/answers/submit',
    '/hearts/use',
    '/streak/extend',
    '/sync/state',
  ];

  @override
  void onError(DioException err, ErrorInterceptorHandler handler) async {
    if (_isNetworkError(err)) {
      final path = err.requestOptions.path;

      if (_queueableEndpoints.any((e) => path.contains(e))) {
        // Map request to SyncAction
        final actionType = _mapPathToActionType(path);
        if (actionType != null) {
          final action = SyncAction(
            type: actionType,
            data: err.requestOptions.data is Map<String, dynamic> 
                ? err.requestOptions.data 
                : (err.requestOptions.data != null ? {'raw_data': err.requestOptions.data} : {}),
          );
          await _actionQueue.add(action);

          // Return a 202 Accepted pseudo-response to the app
          return handler.resolve(Response(
            requestOptions: err.requestOptions,
            statusCode: 202,
            data: {'queued': true, 'message': 'Action queued for later synchronization'},
          ));
        }
      }
    }
    handler.next(err);
  }

  SyncActionType? _mapPathToActionType(String path) {
    if (path.contains('/answers/submit')) return SyncActionType.submitAnswer;
    if (path.contains('/hearts/use')) return SyncActionType.useHeart;
    if (path.contains('/streak/extend')) return SyncActionType.extendStreak;
    if (path.contains('/sync/state')) return SyncActionType.updateState;
    return null;
  }

  bool _isNetworkError(DioException err) {
    return err.type == DioExceptionType.connectionTimeout ||
           err.type == DioExceptionType.connectionError ||
           err.type == DioExceptionType.sendTimeout ||
           err.type == DioExceptionType.receiveTimeout;
  }
}
