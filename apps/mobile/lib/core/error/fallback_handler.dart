import 'package:flutter/material.dart';
import '../../shared/widgets/fallback/offline_mode_banner.dart';
import '../../shared/widgets/fallback/video_fallback.dart';
import '../../shared/widgets/fallback/image_placeholder.dart';
import '../../shared/widgets/fallback/no_cache_warning.dart';
import '../../shared/widgets/fallback/grace_mode_banner.dart';

/// Types of network-related errors that can occur
enum NetworkErrorType {
  /// No internet connection available
  noConnection,

  /// Request timed out
  timeout,

  /// Conflict during data synchronization
  syncConflict,

  /// Ad failed to load or play
  adFailed,

  /// Server returned an error
  serverError,

  /// Rate limited by server
  rateLimited,
}

/// Types of content-related errors
enum ContentErrorType {
  /// Requested video not found
  videoNotFound,

  /// Image failed to load
  imageNotLoaded,

  /// No explanation available for question
  noExplanation,

  /// No cached questions available for offline use
  noCachedQuestions,

  /// Content format is invalid
  invalidFormat,

  /// Content is still loading
  loading,
}

/// Types of application state errors
enum StateErrorType {
  /// User has no mana/energy left
  noMana,

  /// JWT token has expired
  jwtExpired,

  /// Diagnostic test timed out
  diagnosticTimeout,

  /// League results not yet processed
  leagueNotProcessed,

  /// Session expired or invalid
  sessionExpired,

  /// Feature not available in current mode
  featureUnavailable,

  /// User not authenticated
  notAuthenticated,
}

/// Fallback messages aligned with LOGICA_DE_NEGOCIO.md
class FallbackMessages {
  static const String noConnection = 'Sin conexion. Modo Entrenamiento Activo.';
  static const String timeout = 'Conectando con el Sistema...';
  static const String syncConflict = 'Sincronizando con el Sistema...';
  static const String adFailed = 'Transmision interrumpida. Tu Mana llegara pronto.';
  static const String serverError = 'El Sistema esta descansando. Reintenta en breve.';
  static const String rateLimited = 'Demasiadas solicitudes. Espera un momento.';

  static const String videoNotFound = 'Registro en mantenimiento.';
  static const String imageNotLoaded = 'Imagen no disponible';
  static const String noExplanation = 'Explicacion en preparacion.';
  static const String noCachedQuestions = 'Necesitas conexion para esta area.';
  static const String invalidFormat = 'Contenido no disponible.';
  static const String loading = 'Cargando contenido...';

  static const String noMana = 'Mana agotado. Entrena sin rango.';
  static const String jwtExpired = 'Reconectando...';
  static const String diagnosticTimeout = 'Tiempo agotado. Tu progreso se guardo.';
  static const String leagueNotProcessed = 'Resultados en proceso.';
  static const String sessionExpired = 'Sesion expirada. Vuelve a iniciar.';
  static const String featureUnavailable = 'Funcion no disponible sin conexion.';
  static const String notAuthenticated = 'Inicia sesion para continuar.';
}

/// Centralized handler for displaying fallback UI based on error types.
/// This class provides static methods to generate appropriate UI widgets
/// for various error scenarios in the application.
class FallbackHandler {
  /// Creates a fallback widget for network-related errors
  static Widget handleNetworkError(
    NetworkErrorType type, {
    VoidCallback? onRetry,
    String? customMessage,
  }) {
    switch (type) {
      case NetworkErrorType.noConnection:
        return OfflineModeBanner(
          message: customMessage ?? FallbackMessages.noConnection,
          onRetry: onRetry,
        );

      case NetworkErrorType.timeout:
        return _buildTimeoutWidget(
          message: customMessage ?? FallbackMessages.timeout,
          onRetry: onRetry,
        );

      case NetworkErrorType.syncConflict:
        return _buildSyncConflictWidget(
          message: customMessage ?? FallbackMessages.syncConflict,
        );

      case NetworkErrorType.adFailed:
        return _buildAdFailedWidget(
          message: customMessage ?? FallbackMessages.adFailed,
          onRetry: onRetry,
        );

      case NetworkErrorType.serverError:
        return _buildGenericErrorWidget(
          icon: Icons.cloud_off,
          message: customMessage ?? FallbackMessages.serverError,
          onRetry: onRetry,
        );

      case NetworkErrorType.rateLimited:
        return _buildGenericErrorWidget(
          icon: Icons.timer,
          message: customMessage ?? FallbackMessages.rateLimited,
          onRetry: onRetry,
        );
    }
  }

  /// Creates a fallback widget for content-related errors
  static Widget handleContentError(
    ContentErrorType type, {
    VoidCallback? onRetry,
    String? customMessage,
    Widget? alternativeContent,
  }) {
    switch (type) {
      case ContentErrorType.videoNotFound:
        return VideoFallback(
          message: customMessage ?? FallbackMessages.videoNotFound,
          alternativeContent: alternativeContent,
        );

      case ContentErrorType.imageNotLoaded:
        return ImagePlaceholder(
          message: customMessage ?? FallbackMessages.imageNotLoaded,
        );

      case ContentErrorType.noExplanation:
        return _buildNoExplanationWidget(
          message: customMessage ?? FallbackMessages.noExplanation,
        );

      case ContentErrorType.noCachedQuestions:
        return NoCacheWarning(
          message: customMessage ?? FallbackMessages.noCachedQuestions,
          onRetry: onRetry,
        );

      case ContentErrorType.invalidFormat:
        return _buildGenericErrorWidget(
          icon: Icons.broken_image,
          message: customMessage ?? FallbackMessages.invalidFormat,
          onRetry: onRetry,
        );

      case ContentErrorType.loading:
        return _buildLoadingWidget(
          message: customMessage ?? FallbackMessages.loading,
        );
    }
  }

  /// Creates a fallback widget for state-related errors
  static Widget handleStateError(
    StateErrorType type, {
    VoidCallback? onRetry,
    VoidCallback? onWatchAd,
    Duration? timeUntilRefill,
    String? customMessage,
  }) {
    switch (type) {
      case StateErrorType.noMana:
        return GraceModeBanner(
          message: customMessage ?? FallbackMessages.noMana,
          timeUntilRefill: timeUntilRefill,
          onWatchAd: onWatchAd,
        );

      case StateErrorType.jwtExpired:
        return _buildReconnectingWidget(
          message: customMessage ?? FallbackMessages.jwtExpired,
        );

      case StateErrorType.diagnosticTimeout:
        return _buildDiagnosticTimeoutWidget(
          message: customMessage ?? FallbackMessages.diagnosticTimeout,
          onRetry: onRetry,
        );

      case StateErrorType.leagueNotProcessed:
        return _buildLeagueProcessingWidget(
          message: customMessage ?? FallbackMessages.leagueNotProcessed,
        );

      case StateErrorType.sessionExpired:
        return _buildSessionExpiredWidget(
          message: customMessage ?? FallbackMessages.sessionExpired,
          onRetry: onRetry,
        );

      case StateErrorType.featureUnavailable:
        return _buildGenericErrorWidget(
          icon: Icons.lock_outline,
          message: customMessage ?? FallbackMessages.featureUnavailable,
          onRetry: onRetry,
        );

      case StateErrorType.notAuthenticated:
        return _buildAuthRequiredWidget(
          message: customMessage ?? FallbackMessages.notAuthenticated,
          onRetry: onRetry,
        );
    }
  }

  /// Get appropriate message for a network error type
  static String getNetworkErrorMessage(NetworkErrorType type) {
    switch (type) {
      case NetworkErrorType.noConnection:
        return FallbackMessages.noConnection;
      case NetworkErrorType.timeout:
        return FallbackMessages.timeout;
      case NetworkErrorType.syncConflict:
        return FallbackMessages.syncConflict;
      case NetworkErrorType.adFailed:
        return FallbackMessages.adFailed;
      case NetworkErrorType.serverError:
        return FallbackMessages.serverError;
      case NetworkErrorType.rateLimited:
        return FallbackMessages.rateLimited;
    }
  }

  /// Get appropriate message for a content error type
  static String getContentErrorMessage(ContentErrorType type) {
    switch (type) {
      case ContentErrorType.videoNotFound:
        return FallbackMessages.videoNotFound;
      case ContentErrorType.imageNotLoaded:
        return FallbackMessages.imageNotLoaded;
      case ContentErrorType.noExplanation:
        return FallbackMessages.noExplanation;
      case ContentErrorType.noCachedQuestions:
        return FallbackMessages.noCachedQuestions;
      case ContentErrorType.invalidFormat:
        return FallbackMessages.invalidFormat;
      case ContentErrorType.loading:
        return FallbackMessages.loading;
    }
  }

  /// Get appropriate message for a state error type
  static String getStateErrorMessage(StateErrorType type) {
    switch (type) {
      case StateErrorType.noMana:
        return FallbackMessages.noMana;
      case StateErrorType.jwtExpired:
        return FallbackMessages.jwtExpired;
      case StateErrorType.diagnosticTimeout:
        return FallbackMessages.diagnosticTimeout;
      case StateErrorType.leagueNotProcessed:
        return FallbackMessages.leagueNotProcessed;
      case StateErrorType.sessionExpired:
        return FallbackMessages.sessionExpired;
      case StateErrorType.featureUnavailable:
        return FallbackMessages.featureUnavailable;
      case StateErrorType.notAuthenticated:
        return FallbackMessages.notAuthenticated;
    }
  }

  // Private helper widgets

  static Widget _buildTimeoutWidget({
    required String message,
    VoidCallback? onRetry,
  }) {
    return _FallbackCard(
      icon: Icons.hourglass_empty,
      iconColor: Colors.orange,
      message: message,
      showProgress: true,
      onRetry: onRetry,
    );
  }

  static Widget _buildSyncConflictWidget({required String message}) {
    return _FallbackCard(
      icon: Icons.sync,
      iconColor: Colors.cyan,
      message: message,
      showProgress: true,
      isAnimatedIcon: true,
    );
  }

  static Widget _buildAdFailedWidget({
    required String message,
    VoidCallback? onRetry,
  }) {
    return _FallbackCard(
      icon: Icons.videocam_off,
      iconColor: Colors.amber,
      message: message,
      onRetry: onRetry,
      retryLabel: 'Reintentar',
    );
  }

  static Widget _buildNoExplanationWidget({required String message}) {
    return _FallbackCard(
      icon: Icons.lightbulb_outline,
      iconColor: Colors.yellow,
      message: message,
      compact: true,
    );
  }

  static Widget _buildLoadingWidget({required String message}) {
    return _FallbackCard(
      icon: Icons.downloading,
      iconColor: Colors.blue,
      message: message,
      showProgress: true,
    );
  }

  static Widget _buildReconnectingWidget({required String message}) {
    return _FallbackCard(
      icon: Icons.refresh,
      iconColor: Colors.green,
      message: message,
      showProgress: true,
      isAnimatedIcon: true,
    );
  }

  static Widget _buildDiagnosticTimeoutWidget({
    required String message,
    VoidCallback? onRetry,
  }) {
    return _FallbackCard(
      icon: Icons.timer_off,
      iconColor: Colors.red,
      message: message,
      onRetry: onRetry,
      retryLabel: 'Continuar',
    );
  }

  static Widget _buildLeagueProcessingWidget({required String message}) {
    return _FallbackCard(
      icon: Icons.emoji_events,
      iconColor: Colors.amber,
      message: message,
      showProgress: true,
    );
  }

  static Widget _buildSessionExpiredWidget({
    required String message,
    VoidCallback? onRetry,
  }) {
    return _FallbackCard(
      icon: Icons.lock_clock,
      iconColor: Colors.orange,
      message: message,
      onRetry: onRetry,
      retryLabel: 'Iniciar Sesion',
    );
  }

  static Widget _buildAuthRequiredWidget({
    required String message,
    VoidCallback? onRetry,
  }) {
    return _FallbackCard(
      icon: Icons.person_outline,
      iconColor: Colors.purple,
      message: message,
      onRetry: onRetry,
      retryLabel: 'Iniciar Sesion',
    );
  }

  static Widget _buildGenericErrorWidget({
    required IconData icon,
    required String message,
    VoidCallback? onRetry,
  }) {
    return _FallbackCard(
      icon: icon,
      iconColor: Colors.grey,
      message: message,
      onRetry: onRetry,
    );
  }
}

/// Internal widget for displaying fallback cards
class _FallbackCard extends StatefulWidget {
  final IconData icon;
  final Color iconColor;
  final String message;
  final bool showProgress;
  final bool isAnimatedIcon;
  final bool compact;
  final VoidCallback? onRetry;
  final String? retryLabel;

  const _FallbackCard({
    required this.icon,
    required this.iconColor,
    required this.message,
    this.showProgress = false,
    this.isAnimatedIcon = false,
    this.compact = false,
    this.onRetry,
    this.retryLabel,
  });

  @override
  State<_FallbackCard> createState() => _FallbackCardState();
}

class _FallbackCardState extends State<_FallbackCard>
    with SingleTickerProviderStateMixin {
  late AnimationController _animationController;

  @override
  void initState() {
    super.initState();
    _animationController = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 2),
    );
    if (widget.isAnimatedIcon) {
      _animationController.repeat();
    }
  }

  @override
  void dispose() {
    _animationController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    if (widget.compact) {
      return Container(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
        decoration: BoxDecoration(
          color: widget.iconColor.withOpacity(0.1),
          borderRadius: BorderRadius.circular(8),
          border: Border.all(
            color: widget.iconColor.withOpacity(0.3),
          ),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(widget.icon, color: widget.iconColor, size: 16),
            const SizedBox(width: 8),
            Flexible(
              child: Text(
                widget.message,
                style: TextStyle(
                  color: widget.iconColor,
                  fontSize: 12,
                ),
              ),
            ),
          ],
        ),
      );
    }

    return Container(
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        color: theme.cardColor,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: widget.iconColor.withOpacity(0.3),
        ),
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          // Icon
          widget.isAnimatedIcon
              ? RotationTransition(
                  turns: _animationController,
                  child: Icon(
                    widget.icon,
                    size: 48,
                    color: widget.iconColor,
                  ),
                )
              : Icon(
                  widget.icon,
                  size: 48,
                  color: widget.iconColor,
                ),

          const SizedBox(height: 16),

          // Message
          Text(
            widget.message,
            textAlign: TextAlign.center,
            style: theme.textTheme.bodyLarge?.copyWith(
              color: Colors.white70,
            ),
          ),

          // Progress indicator
          if (widget.showProgress) ...[
            const SizedBox(height: 16),
            SizedBox(
              width: 100,
              child: LinearProgressIndicator(
                backgroundColor: widget.iconColor.withOpacity(0.2),
                valueColor: AlwaysStoppedAnimation(widget.iconColor),
              ),
            ),
          ],

          // Retry button
          if (widget.onRetry != null) ...[
            const SizedBox(height: 20),
            ElevatedButton.icon(
              onPressed: widget.onRetry,
              icon: const Icon(Icons.refresh, size: 18),
              label: Text(widget.retryLabel ?? 'Reintentar'),
              style: ElevatedButton.styleFrom(
                backgroundColor: widget.iconColor.withOpacity(0.2),
                foregroundColor: widget.iconColor,
              ),
            ),
          ],
        ],
      ),
    );
  }
}
