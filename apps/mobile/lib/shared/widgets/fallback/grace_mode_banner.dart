import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import '../../../core/config/app_theme.dart';

/// A banner displayed when the user has exhausted their mana/energy and
/// enters "Grace Mode" (training mode without earning XP/rank progress).
///
/// Shows message "Mana agotado. Entrena sin rango." with:
/// - Timer until next mana refill
/// - Button to watch ad for instant refill
///
/// Features:
/// - Countdown timer to next mana regeneration
/// - Watch ad button for instant refill
/// - Animated visual feedback
/// - Compact and full display modes
class GraceModeBanner extends StatefulWidget {
  /// The message to display
  final String message;

  /// Time remaining until next mana refill
  final Duration? timeUntilRefill;

  /// Called when user taps "Watch Ad" button
  final VoidCallback? onWatchAd;

  /// Called when user dismisses the banner
  final VoidCallback? onDismiss;

  /// Whether to show in compact mode
  final bool compact;

  /// Whether ads are currently available
  final bool adsAvailable;

  /// Number of ads remaining today
  final int adsRemainingToday;

  const GraceModeBanner({
    super.key,
    this.message = 'Mana agotado. Entrena sin rango.',
    this.timeUntilRefill,
    this.onWatchAd,
    this.onDismiss,
    this.compact = false,
    this.adsAvailable = true,
    this.adsRemainingToday = 3,
  });

  @override
  State<GraceModeBanner> createState() => _GraceModeBannerState();
}

class _GraceModeBannerState extends State<GraceModeBanner> {
  Timer? _countdownTimer;
  Duration _remainingTime = Duration.zero;

  @override
  void initState() {
    super.initState();
    _remainingTime = widget.timeUntilRefill ?? Duration.zero;
    _startCountdown();
  }

  @override
  void didUpdateWidget(GraceModeBanner oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (widget.timeUntilRefill != oldWidget.timeUntilRefill) {
      _remainingTime = widget.timeUntilRefill ?? Duration.zero;
      _startCountdown();
    }
  }

  void _startCountdown() {
    _countdownTimer?.cancel();
    if (_remainingTime.inSeconds > 0) {
      _countdownTimer = Timer.periodic(const Duration(seconds: 1), (timer) {
        if (_remainingTime.inSeconds <= 0) {
          timer.cancel();
        } else {
          setState(() {
            _remainingTime = _remainingTime - const Duration(seconds: 1);
          });
        }
      });
    }
  }

  @override
  void dispose() {
    _countdownTimer?.cancel();
    super.dispose();
  }

  String _formatDuration(Duration duration) {
    final hours = duration.inHours;
    final minutes = duration.inMinutes % 60;
    final seconds = duration.inSeconds % 60;

    if (hours > 0) {
      return '${hours}h ${minutes}m';
    } else if (minutes > 0) {
      return '${minutes}m ${seconds}s';
    } else {
      return '${seconds}s';
    }
  }

  @override
  Widget build(BuildContext context) {
    if (widget.compact) {
      return _buildCompactBanner(context);
    }
    return _buildFullBanner(context);
  }

  Widget _buildCompactBanner(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [
            Colors.purple.shade900.withOpacity(0.9),
            Colors.purple.shade800.withOpacity(0.8),
          ],
        ),
        boxShadow: [
          BoxShadow(
            color: Colors.purple.withOpacity(0.3),
            blurRadius: 8,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: SafeArea(
        bottom: false,
        child: Row(
          children: [
            // Shield icon (grace mode indicator)
            const Icon(
              Icons.shield_outlined,
              color: Colors.purpleAccent,
              size: 20,
            )
                .animate(onPlay: (c) => c.repeat(reverse: true))
                .scale(
                  begin: const Offset(1.0, 1.0),
                  end: const Offset(1.15, 1.15),
                  duration: 1.seconds,
                ),
            const SizedBox(width: 10),
            // Message and timer
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                mainAxisSize: MainAxisSize.min,
                children: [
                  Text(
                    widget.message,
                    style: const TextStyle(
                      color: Colors.white,
                      fontSize: 12,
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                  if (_remainingTime.inSeconds > 0) ...[
                    const SizedBox(height: 2),
                    Row(
                      children: [
                        Icon(
                          Icons.timer_outlined,
                          color: Colors.purpleAccent.withOpacity(0.7),
                          size: 12,
                        ),
                        const SizedBox(width: 4),
                        Text(
                          'Proximo mana: ${_formatDuration(_remainingTime)}',
                          style: TextStyle(
                            color: Colors.purpleAccent.withOpacity(0.9),
                            fontSize: 10,
                          ),
                        ),
                      ],
                    ),
                  ],
                ],
              ),
            ),
            // Watch ad button
            if (widget.adsAvailable &&
                widget.adsRemainingToday > 0 &&
                widget.onWatchAd != null)
              GestureDetector(
                onTap: widget.onWatchAd,
                child: Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 12,
                    vertical: 6,
                  ),
                  decoration: BoxDecoration(
                    gradient: LinearGradient(
                      colors: [
                        AppTheme.secondaryGold,
                        AppTheme.secondaryGold.withOpacity(0.8),
                      ],
                    ),
                    borderRadius: BorderRadius.circular(16),
                    boxShadow: [
                      BoxShadow(
                        color: AppTheme.secondaryGold.withOpacity(0.3),
                        blurRadius: 4,
                      ),
                    ],
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      const Icon(
                        Icons.play_circle_filled,
                        color: Colors.black87,
                        size: 14,
                      ),
                      const SizedBox(width: 4),
                      const Text(
                        'Ver anuncio',
                        style: TextStyle(
                          color: Colors.black87,
                          fontSize: 11,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
          ],
        ),
      ),
    ).animate().slideY(begin: -1, end: 0, duration: 300.ms).fadeIn();
  }

  Widget _buildFullBanner(BuildContext context) {
    return Container(
      margin: const EdgeInsets.all(16),
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [
            Colors.purple.shade900.withOpacity(0.3),
            Colors.purple.shade800.withOpacity(0.1),
          ],
        ),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(
          color: Colors.purpleAccent.withOpacity(0.3),
        ),
        boxShadow: [
          BoxShadow(
            color: Colors.purple.withOpacity(0.1),
            blurRadius: 16,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          // Header row
          Row(
            children: [
              // Animated shield icon
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: Colors.purpleAccent.withOpacity(0.15),
                  shape: BoxShape.circle,
                ),
                child: const Icon(
                  Icons.shield,
                  color: Colors.purpleAccent,
                  size: 28,
                ),
              )
                  .animate(onPlay: (c) => c.repeat(reverse: true))
                  .shimmer(
                    duration: 2.seconds,
                    color: Colors.purpleAccent.withOpacity(0.3),
                  ),
              const SizedBox(width: 16),
              // Title and message
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'MODO ENTRENAMIENTO',
                      style: TextStyle(
                        color: Colors.purpleAccent,
                        fontSize: 12,
                        fontWeight: FontWeight.bold,
                        letterSpacing: 1,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      widget.message,
                      style: const TextStyle(
                        color: AppTheme.textSecondary,
                        fontSize: 13,
                      ),
                    ),
                  ],
                ),
              ),
              // Dismiss button
              if (widget.onDismiss != null)
                GestureDetector(
                  onTap: widget.onDismiss,
                  child: Icon(
                    Icons.close,
                    color: AppTheme.textMuted,
                    size: 20,
                  ),
                ),
            ],
          ),

          const SizedBox(height: 20),

          // Timer section
          if (_remainingTime.inSeconds > 0) ...[
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: AppTheme.bgElevated.withOpacity(0.3),
                borderRadius: BorderRadius.circular(12),
              ),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  // Timer icon
                  Icon(
                    Icons.hourglass_bottom,
                    color: Colors.purpleAccent.withOpacity(0.7),
                    size: 24,
                  )
                      .animate(onPlay: (c) => c.repeat())
                      .rotate(duration: 2.seconds),
                  const SizedBox(width: 12),
                  // Timer display
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Proximo mana en',
                        style: TextStyle(
                          color: AppTheme.textMuted,
                          fontSize: 11,
                        ),
                      ),
                      const SizedBox(height: 2),
                      Text(
                        _formatDuration(_remainingTime),
                        style: const TextStyle(
                          color: Colors.purpleAccent,
                          fontSize: 24,
                          fontWeight: FontWeight.bold,
                          fontFamily: 'monospace',
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
            const SizedBox(height: 16),
          ],

          // Watch ad button
          if (widget.adsAvailable && widget.adsRemainingToday > 0) ...[
            SizedBox(
              width: double.infinity,
              child: ElevatedButton.icon(
                onPressed: widget.onWatchAd,
                icon: const Icon(Icons.play_circle_filled, size: 22),
                label: Column(
                  children: [
                    const Text('Ver anuncio'),
                    Text(
                      '${widget.adsRemainingToday} restantes hoy',
                      style: TextStyle(
                        fontSize: 10,
                        color: Colors.black.withOpacity(0.6),
                      ),
                    ),
                  ],
                ),
                style: ElevatedButton.styleFrom(
                  backgroundColor: AppTheme.secondaryGold,
                  foregroundColor: Colors.black87,
                  padding: const EdgeInsets.symmetric(vertical: 14),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                ),
              ),
            ),
            const SizedBox(height: 8),
            Text(
              'Recupera mana instantaneamente',
              style: TextStyle(
                color: AppTheme.textMuted,
                fontSize: 11,
              ),
            ),
          ] else if (!widget.adsAvailable || widget.adsRemainingToday <= 0) ...[
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: AppTheme.bgElevated.withOpacity(0.3),
                borderRadius: BorderRadius.circular(8),
              ),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(
                    Icons.info_outline,
                    color: AppTheme.textMuted,
                    size: 16,
                  ),
                  const SizedBox(width: 8),
                  Text(
                    widget.adsAvailable
                        ? 'Sin anuncios disponibles hoy'
                        : 'Anuncios no disponibles',
                    style: TextStyle(
                      color: AppTheme.textMuted,
                      fontSize: 12,
                    ),
                  ),
                ],
              ),
            ),
          ],

          // Info note
          const SizedBox(height: 16),
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: Colors.purpleAccent.withOpacity(0.05),
              borderRadius: BorderRadius.circular(8),
              border: Border.all(
                color: Colors.purpleAccent.withOpacity(0.1),
              ),
            ),
            child: Row(
              children: [
                Icon(
                  Icons.lightbulb_outline,
                  color: Colors.purpleAccent.withOpacity(0.7),
                  size: 16,
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    'En modo entrenamiento puedes practicar sin afectar tu rango en las ligas.',
                    style: TextStyle(
                      color: AppTheme.textMuted,
                      fontSize: 11,
                      height: 1.3,
                    ),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    ).animate().fadeIn(duration: 300.ms).slideY(begin: -0.1, end: 0);
  }
}

/// A compact badge version for headers
class GraceModeBadge extends StatelessWidget {
  final VoidCallback? onTap;

  const GraceModeBadge({super.key, this.onTap});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
        decoration: BoxDecoration(
          color: Colors.purple.withOpacity(0.2),
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: Colors.purple.withOpacity(0.5)),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.shield, color: Colors.purpleAccent, size: 14),
            const SizedBox(width: 6),
            const Text(
              'ENTRENAMIENTO',
              style: TextStyle(
                color: Colors.purpleAccent,
                fontSize: 10,
                fontWeight: FontWeight.bold,
                letterSpacing: 0.5,
              ),
            ),
          ],
        ),
      )
          .animate(onPlay: (c) => c.repeat(reverse: true))
          .shimmer(duration: 3.seconds, color: Colors.purpleAccent.withOpacity(0.2)),
    );
  }
}
