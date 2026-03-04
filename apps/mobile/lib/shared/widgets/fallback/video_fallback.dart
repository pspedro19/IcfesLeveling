import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import '../../../core/config/app_theme.dart';

/// A fallback widget displayed when a video fails to load or is unavailable.
/// Shows message "Registro en mantenimiento." with option to show Tier 1 explanation.
///
/// Features:
/// - Video unavailable icon
/// - Maintenance message
/// - Optional alternative content (Tier 1 explanation)
/// - Optional refresh button
class VideoFallback extends StatelessWidget {
  /// The message to display
  final String message;

  /// Alternative content to show (e.g., Tier 1 text explanation)
  final Widget? alternativeContent;

  /// Called when user taps refresh button
  final VoidCallback? onRefresh;

  /// Whether to show in compact mode
  final bool compact;

  /// Optional video title for context
  final String? videoTitle;

  const VideoFallback({
    super.key,
    this.message = 'Registro en mantenimiento.',
    this.alternativeContent,
    this.onRefresh,
    this.compact = false,
    this.videoTitle,
  });

  @override
  Widget build(BuildContext context) {
    if (compact) {
      return _buildCompactFallback(context);
    }
    return _buildFullFallback(context);
  }

  Widget _buildCompactFallback(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppTheme.bgCard,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: AppTheme.textMuted.withOpacity(0.2),
        ),
      ),
      child: Row(
        children: [
          // Video icon
          Container(
            padding: const EdgeInsets.all(8),
            decoration: BoxDecoration(
              color: AppTheme.primaryPurple.withOpacity(0.1),
              borderRadius: BorderRadius.circular(8),
            ),
            child: Icon(
              Icons.videocam_off,
              color: AppTheme.primaryPurple.withOpacity(0.5),
              size: 20,
            ),
          ),
          const SizedBox(width: 12),
          // Message
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
                if (alternativeContent != null) ...[
                  const SizedBox(height: 4),
                  Text(
                    'Ver explicacion escrita',
                    style: TextStyle(
                      color: AppTheme.primaryPurple,
                      fontSize: 12,
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                ],
              ],
            ),
          ),
          // Refresh button
          if (onRefresh != null)
            IconButton(
              onPressed: onRefresh,
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

  Widget _buildFullFallback(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topCenter,
          end: Alignment.bottomCenter,
          colors: [
            AppTheme.bgCard,
            AppTheme.bgDark,
          ],
        ),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: AppTheme.textMuted.withOpacity(0.1),
        ),
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          // Video placeholder area
          Container(
            height: 120,
            width: double.infinity,
            decoration: BoxDecoration(
              color: AppTheme.bgElevated.withOpacity(0.5),
              borderRadius: BorderRadius.circular(12),
            ),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                // Video off icon with animation
                Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: AppTheme.primaryPurple.withOpacity(0.1),
                    shape: BoxShape.circle,
                  ),
                  child: Icon(
                    Icons.videocam_off,
                    color: AppTheme.primaryPurple.withOpacity(0.5),
                    size: 36,
                  ),
                )
                    .animate(onPlay: (c) => c.repeat(reverse: true))
                    .scale(
                      begin: const Offset(1.0, 1.0),
                      end: const Offset(1.05, 1.05),
                      duration: 2.seconds,
                    ),
                const SizedBox(height: 12),
                // Message
                Text(
                  message,
                  style: TextStyle(
                    color: AppTheme.textSecondary,
                    fontSize: 14,
                  ),
                ),
              ],
            ),
          ),

          // Video title if provided
          if (videoTitle != null) ...[
            const SizedBox(height: 12),
            Text(
              videoTitle!,
              style: const TextStyle(
                color: AppTheme.textPrimary,
                fontSize: 14,
                fontWeight: FontWeight.w500,
              ),
              textAlign: TextAlign.center,
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
            ),
          ],

          // Alternative content (Tier 1 explanation)
          if (alternativeContent != null) ...[
            const SizedBox(height: 20),
            const Divider(color: AppTheme.bgElevated),
            const SizedBox(height: 16),
            // Header for alternative content
            Row(
              children: [
                Icon(
                  Icons.lightbulb_outline,
                  color: AppTheme.secondaryGold,
                  size: 20,
                ),
                const SizedBox(width: 8),
                const Text(
                  'Explicacion disponible',
                  style: TextStyle(
                    color: AppTheme.secondaryGold,
                    fontSize: 14,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            // The alternative content
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: AppTheme.bgElevated.withOpacity(0.3),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(
                  color: AppTheme.secondaryGold.withOpacity(0.2),
                ),
              ),
              child: alternativeContent,
            ),
          ],

          // Refresh button
          if (onRefresh != null) ...[
            const SizedBox(height: 20),
            TextButton.icon(
              onPressed: onRefresh,
              icon: const Icon(Icons.refresh, size: 18),
              label: const Text('Reintentar'),
              style: TextButton.styleFrom(
                foregroundColor: AppTheme.textMuted,
              ),
            ),
          ],
        ],
      ),
    ).animate().fadeIn(duration: 300.ms);
  }
}

/// A compact inline video error indicator
class VideoErrorChip extends StatelessWidget {
  final VoidCallback? onTap;

  const VideoErrorChip({super.key, this.onTap});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
        decoration: BoxDecoration(
          color: AppTheme.bgElevated,
          borderRadius: BorderRadius.circular(8),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(
              Icons.videocam_off,
              color: AppTheme.textMuted,
              size: 14,
            ),
            const SizedBox(width: 6),
            Text(
              'Video no disponible',
              style: TextStyle(
                color: AppTheme.textMuted,
                fontSize: 11,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

/// A placeholder for video thumbnails that failed to load
class VideoThumbnailPlaceholder extends StatelessWidget {
  final double? width;
  final double? height;
  final BorderRadius? borderRadius;

  const VideoThumbnailPlaceholder({
    super.key,
    this.width,
    this.height,
    this.borderRadius,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      width: width ?? 120,
      height: height ?? 68,
      decoration: BoxDecoration(
        color: AppTheme.bgElevated,
        borderRadius: borderRadius ?? BorderRadius.circular(8),
      ),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(
            Icons.play_circle_outline,
            color: AppTheme.textMuted.withOpacity(0.5),
            size: 24,
          ),
          const SizedBox(height: 4),
          Text(
            'Vista previa',
            style: TextStyle(
              color: AppTheme.textMuted.withOpacity(0.5),
              fontSize: 8,
            ),
          ),
        ],
      ),
    );
  }
}
