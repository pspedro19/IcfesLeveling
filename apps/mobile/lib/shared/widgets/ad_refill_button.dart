import 'package:flutter/material.dart';

/// A button that allows the user to refill hearts by watching an advertisement.
/// It displays the current ad watch count and disables if the daily limit is reached.
///
/// [onPressed] Callback when the button is pressed.
/// [adsToday] Number of ads watched today.
/// [maxAds] Maximum number of ads allowed per day.
class AdRefillButton extends StatelessWidget {
  final VoidCallback onPressed;
  final int adsToday;
  final int maxAds;

  const AdRefillButton({
    super.key,
    required this.onPressed,
    required this.adsToday,
    this.maxAds = 3,
  });

  @override
  Widget build(BuildContext context) {
    final canWatch = adsToday < maxAds;

    return ElevatedButton.icon(
      onPressed: canWatch ? onPressed : null,
      icon: Icon(canWatch ? Icons.play_circle_fill : Icons.lock_clock, size: 20),
      label: Text(
        canWatch ? "VER ANUNCIO (+1 ❤)" : "LÍMITE DIARIO ALCANZADO",
        style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13, letterSpacing: 1),
      ),
      style: ElevatedButton.styleFrom(
        backgroundColor: Colors.green.shade700,
        foregroundColor: Colors.white,
        disabledBackgroundColor: Colors.white10,
        disabledForegroundColor: Colors.white24,
        minimumSize: const Size(double.infinity, 50),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      ),
    );
  }
}
