import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import '../../../core/config/app_theme.dart';

/// A prominent banner displayed when the app is in offline mode.
/// Shows cloud-off icon with message "Sin conexion. Modo Entrenamiento Activo."
///
/// Features:
/// - Animated entrance
/// - Cloud-off icon with subtle pulse
/// - Optional retry button
/// - Dismissible option
class OfflineModeBanner extends StatelessWidget {
  /// The message to display
  final String message;

  /// Called when user taps retry button
  final VoidCallback? onRetry;

  /// Whether the banner can be dismissed
  final bool dismissible;

  /// Called when user dismisses the banner
  final VoidCallback? onDismiss;

  /// Whether to show a compact version
  final bool compact;

  const OfflineModeBanner({
    super.key,
    this.message = 'Sin conexion. Modo Entrenamiento Activo.',
    this.onRetry,
    this.dismissible = false,
    this.onDismiss,
    this.compact = false,
  });

  @override
  Widget build(BuildContext context) {
    if (compact) {
      return _buildCompactBanner(context);
    }
    return _buildFullBanner(context);
  }

  Widget _buildCompactBanner(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [
            AppTheme.warningOrange.withOpacity(0.9),
            AppTheme.warningOrange.withOpacity(0.7),
          ],
        ),
        boxShadow: [
          BoxShadow(
            color: AppTheme.warningOrange.withOpacity(0.3),
            blurRadius: 8,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: SafeArea(
        bottom: false,
        child: Row(
          children: [
            // Cloud off icon with pulse animation
            const Icon(
              Icons.cloud_off,
              color: Colors.white,
              size: 18,
            )
                .animate(onPlay: (c) => c.repeat(reverse: true))
                .scale(
                  begin: const Offset(1.0, 1.0),
                  end: const Offset(1.1, 1.1),
                  duration: 1.seconds,
                ),
            const SizedBox(width: 10),
            // Message
            Expanded(
              child: Text(
                message,
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 13,
                  fontWeight: FontWeight.w500,
                ),
              ),
            ),
            // Retry button
            if (onRetry != null)
              GestureDetector(
                onTap: onRetry,
                child: Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 10,
                    vertical: 4,
                  ),
                  decoration: BoxDecoration(
                    color: Colors.white.withOpacity(0.2),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: const Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(Icons.refresh, color: Colors.white, size: 14),
                      SizedBox(width: 4),
                      Text(
                        'Reintentar',
                        style: TextStyle(
                          color: Colors.white,
                          fontSize: 12,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            // Dismiss button
            if (dismissible && onDismiss != null) ...[
              const SizedBox(width: 8),
              GestureDetector(
                onTap: onDismiss,
                child: const Icon(
                  Icons.close,
                  color: Colors.white70,
                  size: 18,
                ),
              ),
            ],
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
            AppTheme.warningOrange.withOpacity(0.15),
            AppTheme.warningOrange.withOpacity(0.05),
          ],
        ),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: AppTheme.warningOrange.withOpacity(0.3),
          width: 1,
        ),
        boxShadow: [
          BoxShadow(
            color: AppTheme.warningOrange.withOpacity(0.1),
            blurRadius: 12,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          // Icon row
          Row(
            children: [
              // Animated cloud-off icon
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: AppTheme.warningOrange.withOpacity(0.2),
                  shape: BoxShape.circle,
                ),
                child: const Icon(
                  Icons.cloud_off,
                  color: AppTheme.warningOrange,
                  size: 28,
                ),
              )
                  .animate(onPlay: (c) => c.repeat(reverse: true))
                  .scale(
                    begin: const Offset(1.0, 1.0),
                    end: const Offset(1.05, 1.05),
                    duration: 1500.ms,
                  )
                  .shimmer(
                    duration: 2.seconds,
                    color: AppTheme.warningOrange.withOpacity(0.3),
                  ),
              const SizedBox(width: 16),
              // Title and message
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'Modo Offline',
                      style: TextStyle(
                        color: AppTheme.warningOrange,
                        fontSize: 16,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      message,
                      style: TextStyle(
                        color: AppTheme.textSecondary,
                        fontSize: 13,
                      ),
                    ),
                  ],
                ),
              ),
              // Dismiss button
              if (dismissible && onDismiss != null)
                GestureDetector(
                  onTap: onDismiss,
                  child: Container(
                    padding: const EdgeInsets.all(4),
                    child: Icon(
                      Icons.close,
                      color: AppTheme.textMuted,
                      size: 20,
                    ),
                  ),
                ),
            ],
          ),

          // Info text
          const SizedBox(height: 16),
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: AppTheme.bgElevated.withOpacity(0.5),
              borderRadius: BorderRadius.circular(8),
            ),
            child: Row(
              children: [
                Icon(
                  Icons.info_outline,
                  color: AppTheme.textMuted,
                  size: 16,
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    'Puedes seguir entrenando. Tu progreso se sincronizara cuando vuelvas a conectarte.',
                    style: TextStyle(
                      color: AppTheme.textMuted,
                      fontSize: 12,
                    ),
                  ),
                ),
              ],
            ),
          ),

          // Retry button
          if (onRetry != null) ...[
            const SizedBox(height: 16),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton.icon(
                onPressed: onRetry,
                icon: const Icon(Icons.refresh, size: 18),
                label: const Text('Reintentar conexion'),
                style: ElevatedButton.styleFrom(
                  backgroundColor: AppTheme.warningOrange.withOpacity(0.2),
                  foregroundColor: AppTheme.warningOrange,
                  elevation: 0,
                  padding: const EdgeInsets.symmetric(vertical: 12),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(10),
                    side: BorderSide(
                      color: AppTheme.warningOrange.withOpacity(0.3),
                    ),
                  ),
                ),
              ),
            ),
          ],
        ],
      ),
    ).animate().fadeIn(duration: 300.ms).slideY(begin: -0.1, end: 0);
  }
}

/// A minimal inline version for use in lists or compact spaces
class OfflineModeChip extends StatelessWidget {
  const OfflineModeChip({super.key});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: AppTheme.warningOrange.withOpacity(0.15),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(
          color: AppTheme.warningOrange.withOpacity(0.3),
        ),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(
            Icons.cloud_off,
            color: AppTheme.warningOrange,
            size: 12,
          ),
          const SizedBox(width: 4),
          Text(
            'Offline',
            style: TextStyle(
              color: AppTheme.warningOrange,
              fontSize: 10,
              fontWeight: FontWeight.bold,
            ),
          ),
        ],
      ),
    );
  }
}
