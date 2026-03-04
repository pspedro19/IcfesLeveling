import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class ConnectivityMonitor {
  final Connectivity _connectivity = Connectivity();

  Stream<bool> get onConnectivityChanged =>
    _connectivity.onConnectivityChanged.map((results) =>
      results.any((result) => result != ConnectivityResult.none)
    );

  Future<bool> get isOnline async {
    final results = await _connectivity.checkConnectivity();
    return results.any((result) => result != ConnectivityResult.none);
  }
}

final connectivityProvider = StreamProvider<bool>((ref) {
  return ConnectivityMonitor().onConnectivityChanged;
});
