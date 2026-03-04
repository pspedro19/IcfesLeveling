import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import '../../../core/config/app_theme.dart';

/// A warning widget displayed when cached content is required but unavailable.
/// Shows message "Necesitas conexion para esta area." with retry button.
///
/// Features:
/// - Clear connection required icon
/// - Informative message
/// - Prominent retry button
/// - Optional download suggestion
class NoCacheWarning extends StatelessWidget {
  /// The message to display
  final String message;

  /// Called when user taps retry button
  final VoidCallback? onRetry;

  /// Called when user wants to download content for offline
  final VoidCallback? onDownload;

  /// Whether to show download option
  final bool showDownloadOption;

  /// Optional title for context
  final String? title;

  /// Whether to display in compact mode
  final bool compact;

  const NoCacheWarning({
    super.key,
    this.message = 'Necesitas conexion para esta area.',
    this.onRetry,
    this.onDownload,
    this.showDownloadOption = false,
    this.title,
    this.compact = false,
  });

  @override
  Widget build(BuildContext context) {
    if (compact) {
      return _buildCompactWarning(context);
    }
    return _buildFullWarning(context);
  }

  Widget _buildCompactWarning(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppTheme.warningOrange.withOpacity(0.1),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: AppTheme.warningOrange.withOpacity(0.3),
        ),
      ),
      child: Row(
        children: [
          Icon(
            Icons.wifi_off,
            color: AppTheme.warningOrange,
            size: 24,
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisSize: MainAxisSize.min,
              children: [
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
          if (onRetry != null)
            TextButton(
              onPressed: onRetry,
              child: const Text('Reintentar'),
            ),
        ],
      ),
    );
  }

  Widget _buildFullWarning(BuildContext context) {
    return Container(
      margin: const EdgeInsets.all(16),
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [
            AppTheme.bgCard,
            AppTheme.bgCard.withOpacity(0.8),
          ],
        ),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(
          color: AppTheme.warningOrange.withOpacity(0.3),
        ),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.2),
            blurRadius: 16,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          // Icon with decorative rings
          Stack(
            alignment: Alignment.center,
            children: [
              // Outer ring
              Container(
                width: 100,
                height: 100,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  border: Border.all(
                    color: AppTheme.warningOrange.withOpacity(0.1),
                    width: 2,
                  ),
                ),
              )
                  .animate(onPlay: (c) => c.repeat())
                  .scale(
                    begin: const Offset(0.9, 0.9),
                    end: const Offset(1.1, 1.1),
                    duration: 2.seconds,
                  )
                  .fadeOut(duration: 2.seconds),
              // Middle ring
              Container(
                width: 80,
                height: 80,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  border: Border.all(
                    color: AppTheme.warningOrange.withOpacity(0.2),
                    width: 2,
                  ),
                ),
              ),
              // Inner circle with icon
              Container(
                width: 64,
                height: 64,
                decoration: BoxDecoration(
                  color: AppTheme.warningOrange.withOpacity(0.15),
                  shape: BoxShape.circle,
                ),
                child: Icon(
                  Icons.wifi_off,
                  color: AppTheme.warningOrange,
                  size: 32,
                ),
              ),
            ],
          ),
          const SizedBox(height: 24),

          // Title
          if (title != null) ...[
            Text(
              title!,
              style: const TextStyle(
                color: AppTheme.textPrimary,
                fontSize: 18,
                fontWeight: FontWeight.bold,
              ),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 8),
          ],

          // Message
          Text(
            message,
            style: TextStyle(
              color: AppTheme.textSecondary,
              fontSize: 14,
              height: 1.4,
            ),
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 24),

          // Retry button
          if (onRetry != null)
            SizedBox(
              width: double.infinity,
              child: ElevatedButton.icon(
                onPressed: onRetry,
                icon: const Icon(Icons.refresh, size: 20),
                label: const Text('Reintentar'),
                style: ElevatedButton.styleFrom(
                  backgroundColor: AppTheme.primaryPurple,
                  foregroundColor: Colors.white,
                  padding: const EdgeInsets.symmetric(vertical: 14),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                ),
              ),
            ),

          // Download option
          if (showDownloadOption && onDownload != null) ...[
            const SizedBox(height: 12),
            SizedBox(
              width: double.infinity,
              child: OutlinedButton.icon(
                onPressed: onDownload,
                icon: const Icon(Icons.download, size: 20),
                label: const Text('Descargar para offline'),
                style: OutlinedButton.styleFrom(
                  foregroundColor: AppTheme.accentCyan,
                  padding: const EdgeInsets.symmetric(vertical: 14),
                  side: BorderSide(
                    color: AppTheme.accentCyan.withOpacity(0.5),
                  ),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                ),
              ),
            ),
          ],

          // Hint text
          const SizedBox(height: 20),
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: AppTheme.bgElevated.withOpacity(0.3),
              borderRadius: BorderRadius.circular(8),
            ),
            child: Row(
              children: [
                Icon(
                  Icons.lightbulb_outline,
                  color: AppTheme.secondaryGold.withOpacity(0.7),
                  size: 16,
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    'Consejo: Descarga contenido cuando tengas WiFi para practicar sin conexion.',
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
    ).animate().fadeIn(duration: 300.ms).scale(
          begin: const Offset(0.95, 0.95),
          end: const Offset(1.0, 1.0),
          duration: 300.ms,
        );
  }
}

/// A minimal version for inline use
class NoCacheChip extends StatelessWidget {
  final VoidCallback? onTap;

  const NoCacheChip({super.key, this.onTap});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
        decoration: BoxDecoration(
          color: AppTheme.warningOrange.withOpacity(0.1),
          borderRadius: BorderRadius.circular(8),
          border: Border.all(
            color: AppTheme.warningOrange.withOpacity(0.3),
          ),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(
              Icons.cloud_download_outlined,
              color: AppTheme.warningOrange,
              size: 14,
            ),
            const SizedBox(width: 6),
            Text(
              'Requiere conexion',
              style: TextStyle(
                color: AppTheme.warningOrange,
                fontSize: 11,
                fontWeight: FontWeight.w500,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

/// A list item version for feature lists
class NoCacheListItem extends StatelessWidget {
  final String featureName;
  final IconData? icon;
  final VoidCallback? onRetry;

  const NoCacheListItem({
    super.key,
    required this.featureName,
    this.icon,
    this.onRetry,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppTheme.bgCard,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: AppTheme.textMuted.withOpacity(0.1),
        ),
      ),
      child: Row(
        children: [
          // Feature icon
          Container(
            padding: const EdgeInsets.all(10),
            decoration: BoxDecoration(
              color: AppTheme.bgElevated,
              borderRadius: BorderRadius.circular(10),
            ),
            child: Icon(
              icon ?? Icons.folder_outlined,
              color: AppTheme.textMuted,
              size: 24,
            ),
          ),
          const SizedBox(width: 12),
          // Feature name and status
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  featureName,
                  style: const TextStyle(
                    color: AppTheme.textPrimary,
                    fontSize: 14,
                    fontWeight: FontWeight.w500,
                  ),
                ),
                const SizedBox(height: 4),
                Row(
                  children: [
                    Icon(
                      Icons.wifi_off,
                      color: AppTheme.warningOrange,
                      size: 12,
                    ),
                    const SizedBox(width: 4),
                    Text(
                      'Necesita conexion',
                      style: TextStyle(
                        color: AppTheme.warningOrange,
                        fontSize: 11,
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
          // Retry button
          if (onRetry != null)
            IconButton(
              onPressed: onRetry,
              icon: Icon(
                Icons.refresh,
                color: AppTheme.textMuted,
                size: 20,
              ),
            ),
        ],
      ),
    );
  }
}
