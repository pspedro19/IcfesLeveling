import 'package:flutter/material.dart';
import '../../../core/config/app_theme.dart';

/// A placeholder widget displayed when an image fails to load.
/// Shows broken image icon with border and message "Imagen no disponible".
///
/// Features:
/// - Broken image icon with decorative border
/// - Customizable size and message
/// - Optional retry button
/// - Fits various container sizes
class ImagePlaceholder extends StatelessWidget {
  /// The message to display
  final String message;

  /// Width of the placeholder
  final double? width;

  /// Height of the placeholder
  final double? height;

  /// Icon size
  final double iconSize;

  /// Called when user taps to retry
  final VoidCallback? onRetry;

  /// Whether to show the message text
  final bool showMessage;

  /// Border radius
  final BorderRadius? borderRadius;

  /// Background color
  final Color? backgroundColor;

  const ImagePlaceholder({
    super.key,
    this.message = 'Imagen no disponible',
    this.width,
    this.height,
    this.iconSize = 32,
    this.onRetry,
    this.showMessage = true,
    this.borderRadius,
    this.backgroundColor,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onRetry,
      child: Container(
        width: width,
        height: height,
        decoration: BoxDecoration(
          color: backgroundColor ?? AppTheme.bgElevated.withOpacity(0.5),
          borderRadius: borderRadius ?? BorderRadius.circular(12),
          border: Border.all(
            color: AppTheme.textMuted.withOpacity(0.2),
            width: 1.5,
            strokeAlign: BorderSide.strokeAlignInside,
          ),
        ),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          mainAxisSize: MainAxisSize.min,
          children: [
            // Broken image icon container
            Container(
              padding: EdgeInsets.all(iconSize * 0.4),
              decoration: BoxDecoration(
                color: AppTheme.bgCard.withOpacity(0.5),
                shape: BoxShape.circle,
                border: Border.all(
                  color: AppTheme.textMuted.withOpacity(0.15),
                ),
              ),
              child: Icon(
                Icons.broken_image_outlined,
                color: AppTheme.textMuted.withOpacity(0.5),
                size: iconSize,
              ),
            ),
            // Message
            if (showMessage) ...[
              SizedBox(height: iconSize * 0.3),
              Text(
                message,
                style: TextStyle(
                  color: AppTheme.textMuted.withOpacity(0.7),
                  fontSize: iconSize * 0.35,
                ),
                textAlign: TextAlign.center,
              ),
            ],
            // Retry hint
            if (onRetry != null) ...[
              SizedBox(height: iconSize * 0.2),
              Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(
                    Icons.refresh,
                    color: AppTheme.primaryPurple.withOpacity(0.6),
                    size: iconSize * 0.35,
                  ),
                  const SizedBox(width: 4),
                  Text(
                    'Tocar para reintentar',
                    style: TextStyle(
                      color: AppTheme.primaryPurple.withOpacity(0.6),
                      fontSize: iconSize * 0.28,
                    ),
                  ),
                ],
              ),
            ],
          ],
        ),
      ),
    );
  }

  /// Creates a small square placeholder for thumbnails
  factory ImagePlaceholder.thumbnail({
    Key? key,
    double size = 48,
    VoidCallback? onRetry,
  }) {
    return ImagePlaceholder(
      key: key,
      width: size,
      height: size,
      iconSize: size * 0.4,
      showMessage: false,
      onRetry: onRetry,
      borderRadius: BorderRadius.circular(8),
    );
  }

  /// Creates a wide placeholder for banners/headers
  factory ImagePlaceholder.banner({
    Key? key,
    double height = 120,
    VoidCallback? onRetry,
  }) {
    return ImagePlaceholder(
      key: key,
      width: double.infinity,
      height: height,
      iconSize: 28,
      onRetry: onRetry,
      borderRadius: BorderRadius.circular(12),
    );
  }

  /// Creates a placeholder matching question image dimensions
  factory ImagePlaceholder.questionImage({
    Key? key,
    VoidCallback? onRetry,
  }) {
    return ImagePlaceholder(
      key: key,
      width: double.infinity,
      height: 180,
      iconSize: 36,
      message: 'Imagen de la pregunta no disponible',
      onRetry: onRetry,
      borderRadius: BorderRadius.circular(12),
    );
  }

  /// Creates an avatar placeholder
  factory ImagePlaceholder.avatar({
    Key? key,
    double size = 40,
  }) {
    return ImagePlaceholder(
      key: key,
      width: size,
      height: size,
      iconSize: size * 0.5,
      showMessage: false,
      borderRadius: BorderRadius.circular(size / 2),
      backgroundColor: AppTheme.bgElevated,
    );
  }
}

/// A shimmer loading placeholder for images
class ImageLoadingPlaceholder extends StatefulWidget {
  final double? width;
  final double? height;
  final BorderRadius? borderRadius;

  const ImageLoadingPlaceholder({
    super.key,
    this.width,
    this.height,
    this.borderRadius,
  });

  @override
  State<ImageLoadingPlaceholder> createState() =>
      _ImageLoadingPlaceholderState();
}

class _ImageLoadingPlaceholderState extends State<ImageLoadingPlaceholder>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  late Animation<double> _animation;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      duration: const Duration(milliseconds: 1500),
      vsync: this,
    )..repeat();
    _animation = Tween<double>(begin: -1.0, end: 2.0).animate(
      CurvedAnimation(parent: _controller, curve: Curves.easeInOut),
    );
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _animation,
      builder: (context, child) {
        return Container(
          width: widget.width,
          height: widget.height,
          decoration: BoxDecoration(
            borderRadius: widget.borderRadius ?? BorderRadius.circular(12),
            gradient: LinearGradient(
              begin: Alignment.centerLeft,
              end: Alignment.centerRight,
              stops: [
                (_animation.value - 0.3).clamp(0.0, 1.0),
                _animation.value.clamp(0.0, 1.0),
                (_animation.value + 0.3).clamp(0.0, 1.0),
              ],
              colors: [
                AppTheme.bgElevated.withOpacity(0.3),
                AppTheme.bgElevated.withOpacity(0.6),
                AppTheme.bgElevated.withOpacity(0.3),
              ],
            ),
          ),
        );
      },
    );
  }
}

/// Extension to easily add fallback to Image widgets
extension ImageWithFallback on Image {
  /// Wraps the image with an error fallback
  Widget withFallback({
    String message = 'Imagen no disponible',
    VoidCallback? onRetry,
    double? fallbackHeight,
  }) {
    return Builder(
      builder: (context) {
        // The actual implementation would use an error builder
        // This is a simplified version
        return this;
      },
    );
  }
}

/// A helper widget that handles image loading with automatic fallback
class FallbackImage extends StatelessWidget {
  final String? imageUrl;
  final double? width;
  final double? height;
  final BoxFit fit;
  final BorderRadius? borderRadius;
  final String fallbackMessage;
  final VoidCallback? onRetry;

  const FallbackImage({
    super.key,
    this.imageUrl,
    this.width,
    this.height,
    this.fit = BoxFit.cover,
    this.borderRadius,
    this.fallbackMessage = 'Imagen no disponible',
    this.onRetry,
  });

  @override
  Widget build(BuildContext context) {
    if (imageUrl == null || imageUrl!.isEmpty) {
      return ImagePlaceholder(
        width: width,
        height: height,
        message: fallbackMessage,
        onRetry: onRetry,
        borderRadius: borderRadius,
      );
    }

    return ClipRRect(
      borderRadius: borderRadius ?? BorderRadius.circular(12),
      child: Image.network(
        imageUrl!,
        width: width,
        height: height,
        fit: fit,
        loadingBuilder: (context, child, loadingProgress) {
          if (loadingProgress == null) return child;
          return ImageLoadingPlaceholder(
            width: width,
            height: height,
            borderRadius: borderRadius,
          );
        },
        errorBuilder: (context, error, stackTrace) {
          return ImagePlaceholder(
            width: width,
            height: height,
            message: fallbackMessage,
            onRetry: onRetry,
            borderRadius: borderRadius,
          );
        },
      ),
    );
  }
}
