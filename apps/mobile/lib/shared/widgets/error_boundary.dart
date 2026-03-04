import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/config/app_theme.dart';
import '../../core/error/fallback_handler.dart';
import '../../core/utils/sync_logger.dart';

/// A widget that catches errors in its child widget tree and displays
/// appropriate fallback UI instead of crashing the app.
///
/// Features:
/// - Catches and logs errors
/// - Shows customizable fallback UI
/// - Allows error reporting
/// - Supports retry functionality
class ErrorBoundary extends StatefulWidget {
  /// The child widget to wrap
  final Widget child;

  /// Optional custom fallback widget
  final Widget? fallback;

  /// Called when an error occurs
  final void Function(Object error, StackTrace stackTrace)? onError;

  /// Whether to show the retry button
  final bool showRetry;

  /// Called when user taps retry
  final VoidCallback? onRetry;

  /// Whether to show error details (debug mode only)
  final bool showDetails;

  /// Tag for error logging
  final String? tag;

  const ErrorBoundary({
    super.key,
    required this.child,
    this.fallback,
    this.onError,
    this.showRetry = true,
    this.onRetry,
    this.showDetails = false,
    this.tag,
  });

  @override
  State<ErrorBoundary> createState() => _ErrorBoundaryState();
}

class _ErrorBoundaryState extends State<ErrorBoundary> {
  Object? _error;
  StackTrace? _stackTrace;
  bool _hasError = false;

  @override
  void initState() {
    super.initState();
  }

  void _handleError(Object error, StackTrace stackTrace) {
    setState(() {
      _error = error;
      _stackTrace = stackTrace;
      _hasError = true;
    });

    // Log the error
    SyncLogger.log(
      'error_boundary_caught${widget.tag != null ? '_${widget.tag}' : ''}',
      error: error.toString(),
      data: {'stack_trace': stackTrace.toString().substring(0, 500)},
      success: false,
    );

    // Call error handler if provided
    widget.onError?.call(error, stackTrace);
  }

  void _retry() {
    setState(() {
      _error = null;
      _stackTrace = null;
      _hasError = false;
    });
    widget.onRetry?.call();
  }

  @override
  Widget build(BuildContext context) {
    if (_hasError) {
      return widget.fallback ??
          _DefaultErrorWidget(
            error: _error,
            stackTrace: _stackTrace,
            showRetry: widget.showRetry,
            showDetails: widget.showDetails,
            onRetry: _retry,
            onReport: () => _reportError(context),
          );
    }

    return _ErrorCatcher(
      onError: _handleError,
      child: widget.child,
    );
  }

  void _reportError(BuildContext context) {
    // Show a dialog to report the error
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: AppTheme.bgCard,
        title: const Text('Reportar Error'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Gracias por reportar este error. Ayuda a mejorar la aplicacion.',
              style: TextStyle(color: AppTheme.textSecondary),
            ),
            const SizedBox(height: 16),
            Text(
              'Detalles del error:',
              style: TextStyle(
                color: AppTheme.textMuted,
                fontSize: 12,
              ),
            ),
            const SizedBox(height: 4),
            Container(
              padding: const EdgeInsets.all(8),
              decoration: BoxDecoration(
                color: AppTheme.bgElevated,
                borderRadius: BorderRadius.circular(8),
              ),
              child: Text(
                _error?.toString() ?? 'Error desconocido',
                style: TextStyle(
                  color: AppTheme.textMuted,
                  fontSize: 10,
                  fontFamily: 'monospace',
                ),
                maxLines: 5,
                overflow: TextOverflow.ellipsis,
              ),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('Cancelar'),
          ),
          ElevatedButton(
            onPressed: () {
              Navigator.pop(ctx);
              _submitErrorReport();
            },
            child: const Text('Enviar'),
          ),
        ],
      ),
    );
  }

  void _submitErrorReport() {
    // In production, this would send the error to a reporting service
    SyncLogger.log(
      'error_report_submitted',
      data: {
        'error': _error?.toString(),
        'tag': widget.tag,
      },
    );

    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text('Reporte enviado. Gracias!'),
        backgroundColor: AppTheme.successGreen,
      ),
    );
  }
}

/// Internal widget that catches errors using ErrorWidget.builder
class _ErrorCatcher extends StatelessWidget {
  final Widget child;
  final void Function(Object error, StackTrace stackTrace) onError;

  const _ErrorCatcher({
    required this.child,
    required this.onError,
  });

  @override
  Widget build(BuildContext context) {
    // Override the error widget for this subtree
    ErrorWidget.builder = (FlutterErrorDetails details) {
      onError(details.exception, details.stack ?? StackTrace.current);
      return const SizedBox.shrink();
    };

    return child;
  }
}

/// Default error widget shown when an error occurs
class _DefaultErrorWidget extends StatelessWidget {
  final Object? error;
  final StackTrace? stackTrace;
  final bool showRetry;
  final bool showDetails;
  final VoidCallback? onRetry;
  final VoidCallback? onReport;

  const _DefaultErrorWidget({
    this.error,
    this.stackTrace,
    this.showRetry = true,
    this.showDetails = false,
    this.onRetry,
    this.onReport,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(24),
      child: Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            // Error icon
            Container(
              padding: const EdgeInsets.all(20),
              decoration: BoxDecoration(
                color: AppTheme.dangerRed.withOpacity(0.1),
                shape: BoxShape.circle,
              ),
              child: Icon(
                Icons.error_outline,
                color: AppTheme.dangerRed,
                size: 48,
              ),
            ),
            const SizedBox(height: 24),

            // Title
            const Text(
              'Algo salio mal',
              style: TextStyle(
                color: AppTheme.textPrimary,
                fontSize: 20,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 8),

            // Message
            Text(
              'Ha ocurrido un error inesperado.',
              style: TextStyle(
                color: AppTheme.textSecondary,
                fontSize: 14,
              ),
              textAlign: TextAlign.center,
            ),

            // Error details (debug mode only)
            if (showDetails && error != null) ...[
              const SizedBox(height: 16),
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: AppTheme.bgElevated,
                  borderRadius: BorderRadius.circular(8),
                ),
                constraints: const BoxConstraints(maxHeight: 100),
                child: SingleChildScrollView(
                  child: Text(
                    error.toString(),
                    style: TextStyle(
                      color: AppTheme.textMuted,
                      fontSize: 10,
                      fontFamily: 'monospace',
                    ),
                  ),
                ),
              ),
            ],

            const SizedBox(height: 24),

            // Action buttons
            Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                // Retry button
                if (showRetry)
                  ElevatedButton.icon(
                    onPressed: onRetry,
                    icon: const Icon(Icons.refresh, size: 18),
                    label: const Text('Reintentar'),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: AppTheme.primaryPurple,
                      padding: const EdgeInsets.symmetric(
                        horizontal: 20,
                        vertical: 12,
                      ),
                    ),
                  ),

                const SizedBox(width: 12),

                // Report button
                if (onReport != null)
                  OutlinedButton.icon(
                    onPressed: onReport,
                    icon: const Icon(Icons.flag_outlined, size: 18),
                    label: const Text('Reportar'),
                    style: OutlinedButton.styleFrom(
                      foregroundColor: AppTheme.textSecondary,
                      padding: const EdgeInsets.symmetric(
                        horizontal: 20,
                        vertical: 12,
                      ),
                    ),
                  ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

/// A simpler error boundary that just shows a fallback widget
class SimpleErrorBoundary extends StatelessWidget {
  final Widget child;
  final Widget fallback;

  const SimpleErrorBoundary({
    super.key,
    required this.child,
    required this.fallback,
  });

  @override
  Widget build(BuildContext context) {
    return ErrorBoundary(
      fallback: fallback,
      showRetry: false,
      child: child,
    );
  }
}

/// An error boundary specifically for async data
class AsyncErrorBoundary extends ConsumerWidget {
  final Widget child;
  final Widget? loading;
  final Widget? error;
  final AsyncValue<dynamic>? asyncValue;

  const AsyncErrorBoundary({
    super.key,
    required this.child,
    this.loading,
    this.error,
    this.asyncValue,
  });

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    if (asyncValue != null) {
      return asyncValue!.when(
        data: (_) => child,
        loading: () =>
            loading ??
            const Center(child: CircularProgressIndicator()),
        error: (e, st) =>
            error ??
            FallbackHandler.handleNetworkError(NetworkErrorType.serverError),
      );
    }

    return ErrorBoundary(
      child: child,
    );
  }
}

/// Extension to easily wrap widgets with error boundary
extension ErrorBoundaryExtension on Widget {
  /// Wraps this widget with an ErrorBoundary
  Widget withErrorBoundary({
    Widget? fallback,
    void Function(Object, StackTrace)? onError,
    bool showRetry = true,
    VoidCallback? onRetry,
    String? tag,
  }) {
    return ErrorBoundary(
      fallback: fallback,
      onError: onError,
      showRetry: showRetry,
      onRetry: onRetry,
      tag: tag,
      child: this,
    );
  }
}

/// Mixin for StatefulWidget that provides error handling capabilities
mixin ErrorHandlingMixin<T extends StatefulWidget> on State<T> {
  Object? _lastError;
  bool _hasError = false;

  bool get hasError => _hasError;
  Object? get lastError => _lastError;

  void handleError(Object error, [StackTrace? stackTrace]) {
    setState(() {
      _lastError = error;
      _hasError = true;
    });

    SyncLogger.log(
      'widget_error_${widget.runtimeType}',
      error: error.toString(),
      success: false,
    );
  }

  void clearError() {
    setState(() {
      _lastError = null;
      _hasError = false;
    });
  }

  Widget buildWithError(Widget child, Widget errorWidget) {
    if (_hasError) {
      return errorWidget;
    }
    return child;
  }
}
