import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:url_launcher/url_launcher.dart';

import '../../data/models/video_tracking_model.dart';
import '../providers/video_provider.dart';
import '../widgets/video_completion_overlay.dart';

/// Video detail page with external YouTube redirect
///
/// Shows video thumbnail, title, description, and buttons to:
/// - Open the video in the YouTube app/browser
/// - Mark as watched to earn +10 XP
class VideoPlayerPage extends ConsumerStatefulWidget {
  final String videoId;
  final String? planId;
  final int? unitNumber;
  final String? title;
  final String? description;

  const VideoPlayerPage({
    super.key,
    required this.videoId,
    this.planId,
    this.unitNumber,
    this.title,
    this.description,
  });

  @override
  ConsumerState<VideoPlayerPage> createState() => _VideoPlayerPageState();
}

class _VideoPlayerPageState extends ConsumerState<VideoPlayerPage> {
  bool _showCompletionOverlay = false;
  late String _youtubeId;

  @override
  void initState() {
    super.initState();
    _youtubeId = VideoInfoModel.extractYoutubeId(widget.videoId);
  }

  VideoPlayerParams get _params => VideoPlayerParams(
        videoId: widget.videoId,
        planId: widget.planId,
        unitNumber: widget.unitNumber,
      );

  Future<void> _openInYouTube() async {
    final url = Uri.parse('https://www.youtube.com/watch?v=$_youtubeId');
    try {
      await launchUrl(url, mode: LaunchMode.externalApplication);
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('No se pudo abrir YouTube')),
        );
      }
    }
  }

  Future<void> _markAsWatched() async {
    final notifier = ref.read(videoPlayerProvider(_params).notifier);
    final success = await notifier.markAsWatched();
    if (success && mounted) {
      setState(() => _showCompletionOverlay = true);
    }
  }

  void _hideCompletionOverlay() {
    setState(() => _showCompletionOverlay = false);
  }

  @override
  Widget build(BuildContext context) {
    final videoState = ref.watch(videoPlayerProvider(_params));
    final theme = Theme.of(context);
    final videoTitle =
        widget.title ?? videoState.videoInfo?.title ?? 'Video';

    return Scaffold(
      appBar: AppBar(
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () => context.pop(),
        ),
        title: Text(
          videoTitle,
          maxLines: 1,
          overflow: TextOverflow.ellipsis,
        ),
        actions: [
          if (videoState.isCompleted)
            Container(
              margin: const EdgeInsets.only(right: 12),
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
              decoration: BoxDecoration(
                color: Colors.green.withOpacity(0.2),
                borderRadius: BorderRadius.circular(12),
              ),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(Icons.check_circle, color: Colors.green[400], size: 16),
                  const SizedBox(width: 4),
                  Text(
                    'Completado',
                    style: TextStyle(
                      color: Colors.green[400],
                      fontSize: 12,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ],
              ),
            ),
        ],
      ),
      body: Stack(
        children: [
          // Main content
          if (videoState.isLoading)
            const Center(child: CircularProgressIndicator())
          else if (videoState.error != null)
            _buildErrorState(videoState, theme)
          else
            _buildContent(videoState, theme, videoTitle),

          // Completion overlay
          if (_showCompletionOverlay)
            VideoCompletionOverlay(
              onContinue: _hideCompletionOverlay,
              onGoBack: () {
                _hideCompletionOverlay();
                context.pop();
              },
            ),
        ],
      ),
    );
  }

  Widget _buildContent(
      VideoPlayerState state, ThemeData theme, String videoTitle) {
    final description =
        widget.description ?? state.videoInfo?.description;

    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // YouTube Thumbnail with play overlay
          _buildThumbnail(theme),
          const SizedBox(height: 20),

          // Title
          Text(
            videoTitle,
            style: theme.textTheme.headlineSmall?.copyWith(
              fontWeight: FontWeight.bold,
            ),
          ),

          // Description
          if (description != null && description.isNotEmpty) ...[
            const SizedBox(height: 12),
            Text(
              description,
              style: theme.textTheme.bodyMedium?.copyWith(
                color: theme.colorScheme.onSurface.withOpacity(0.8),
                height: 1.5,
              ),
            ),
          ],

          const SizedBox(height: 24),

          // Open in YouTube button (red, prominent)
          SizedBox(
            width: double.infinity,
            height: 52,
            child: ElevatedButton.icon(
              onPressed: _openInYouTube,
              icon: const Icon(Icons.play_arrow, size: 28),
              label: const Text(
                'ABRIR EN YOUTUBE',
                style: TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.bold,
                  letterSpacing: 0.5,
                ),
              ),
              style: ElevatedButton.styleFrom(
                backgroundColor: const Color(0xFFFF0000),
                foregroundColor: Colors.white,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12),
                ),
                elevation: 3,
              ),
            ),
          ),

          const SizedBox(height: 16),

          // Mark as watched button OR completed badge
          if (!state.isCompleted)
            SizedBox(
              width: double.infinity,
              height: 48,
              child: OutlinedButton.icon(
                onPressed: _markAsWatched,
                icon: const Icon(Icons.check_circle_outline),
                label: const Text(
                  'MARCAR COMO VISTO',
                  style: TextStyle(
                    fontSize: 14,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                style: OutlinedButton.styleFrom(
                  foregroundColor: Colors.green,
                  side: const BorderSide(color: Colors.green, width: 1.5),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                ),
              ),
            )
          else
            _buildCompletedBadge(theme),

          const SizedBox(height: 28),

          // Tips section
          _buildTipsSection(theme),
        ],
      ),
    );
  }

  Widget _buildThumbnail(ThemeData theme) {
    final thumbnailUrl =
        'https://img.youtube.com/vi/$_youtubeId/hqdefault.jpg';

    return GestureDetector(
      onTap: _openInYouTube,
      child: ClipRRect(
        borderRadius: BorderRadius.circular(12),
        child: AspectRatio(
          aspectRatio: 16 / 9,
          child: Stack(
            fit: StackFit.expand,
            children: [
              // Thumbnail image
              Image.network(
                thumbnailUrl,
                fit: BoxFit.cover,
                errorBuilder: (_, __, ___) => Container(
                  color: Colors.grey[900],
                  child: const Icon(
                    Icons.video_library,
                    size: 64,
                    color: Colors.white38,
                  ),
                ),
                loadingBuilder: (_, child, loadingProgress) {
                  if (loadingProgress == null) return child;
                  return Container(
                    color: Colors.grey[900],
                    child: const Center(child: CircularProgressIndicator()),
                  );
                },
              ),
              // Dark overlay
              Container(
                decoration: BoxDecoration(
                  gradient: LinearGradient(
                    begin: Alignment.center,
                    end: Alignment.bottomCenter,
                    colors: [
                      Colors.transparent,
                      Colors.black.withOpacity(0.4),
                    ],
                  ),
                ),
              ),
              // Play button overlay
              Center(
                child: Container(
                  width: 68,
                  height: 68,
                  decoration: BoxDecoration(
                    color: const Color(0xFFFF0000).withOpacity(0.9),
                    borderRadius: BorderRadius.circular(34),
                    boxShadow: [
                      BoxShadow(
                        color: Colors.black.withOpacity(0.3),
                        blurRadius: 12,
                        offset: const Offset(0, 4),
                      ),
                    ],
                  ),
                  child: const Icon(
                    Icons.play_arrow,
                    color: Colors.white,
                    size: 40,
                  ),
                ),
              ),
              // "Tap to open" label at bottom
              Positioned(
                bottom: 12,
                left: 0,
                right: 0,
                child: Text(
                  'Toca para abrir en YouTube',
                  textAlign: TextAlign.center,
                  style: TextStyle(
                    color: Colors.white.withOpacity(0.9),
                    fontSize: 13,
                    fontWeight: FontWeight.w500,
                    shadows: [
                      Shadow(
                        color: Colors.black.withOpacity(0.6),
                        blurRadius: 4,
                      ),
                    ],
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildCompletedBadge(ThemeData theme) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [Colors.green.shade700, Colors.green.shade500],
        ),
        borderRadius: BorderRadius.circular(12),
        boxShadow: [
          BoxShadow(
            color: Colors.green.withOpacity(0.3),
            blurRadius: 8,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const Icon(Icons.check_circle, color: Colors.white, size: 22),
          const SizedBox(width: 10),
          Flexible(
            child: const Text(
              'Video Completado',
              style: TextStyle(
                color: Colors.white,
                fontWeight: FontWeight.bold,
                fontSize: 15,
              ),
              overflow: TextOverflow.ellipsis,
            ),
          ),
          const SizedBox(width: 10),
          const Icon(Icons.star, color: Colors.amber, size: 18),
          const SizedBox(width: 4),
          const Text(
            '+10 XP',
            style: TextStyle(
              color: Colors.amber,
              fontWeight: FontWeight.bold,
              fontSize: 14,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildTipsSection(ThemeData theme) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: theme.colorScheme.surfaceContainerHighest.withOpacity(0.5),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(Icons.lightbulb_outline, color: Colors.amber[600], size: 20),
              const SizedBox(width: 8),
              Text(
                'Consejos de estudio',
                style: theme.textTheme.titleSmall?.copyWith(
                  fontWeight: FontWeight.bold,
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          _buildTipItem(
            theme,
            'Ve el video completo para mejor comprension del tema',
          ),
          const SizedBox(height: 8),
          _buildTipItem(
            theme,
            'Toma notas mientras ves el video para reforzar el aprendizaje',
          ),
          const SizedBox(height: 8),
          _buildTipItem(
            theme,
            'Marca como visto cuando termines para ganar +10 XP',
          ),
        ],
      ),
    );
  }

  Widget _buildTipItem(ThemeData theme, String text) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Icon(
          Icons.check_circle_outline,
          size: 16,
          color: theme.colorScheme.primary.withOpacity(0.7),
        ),
        const SizedBox(width: 8),
        Expanded(
          child: Text(
            text,
            style: theme.textTheme.bodySmall?.copyWith(
              color: theme.colorScheme.onSurface.withOpacity(0.8),
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildErrorState(VideoPlayerState state, ThemeData theme) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.error_outline, size: 64, color: Colors.orange[400]),
            const SizedBox(height: 16),
            Text(
              state.error!,
              textAlign: TextAlign.center,
              style: theme.textTheme.bodyLarge,
            ),
            const SizedBox(height: 24),
            ElevatedButton.icon(
              onPressed: () =>
                  ref.read(videoPlayerProvider(_params).notifier).retry(),
              icon: const Icon(Icons.refresh),
              label: const Text('Reintentar'),
            ),
          ],
        ),
      ),
    );
  }
}
