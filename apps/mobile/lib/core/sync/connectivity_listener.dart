import 'dart:async';
import 'connectivity_monitor.dart';

class ConnectivityListener {
  final ConnectivityMonitor _monitor;
  StreamSubscription? _subscription;

  ConnectivityListener(this._monitor);

  void listen(Function(bool) onConnectionChanged) {
    _subscription?.cancel();
    _subscription = _monitor.onConnectivityChanged.listen((isOnline) {
      onConnectionChanged(isOnline);
    });
  }

  void dispose() {
    _subscription?.cancel();
  }
}
