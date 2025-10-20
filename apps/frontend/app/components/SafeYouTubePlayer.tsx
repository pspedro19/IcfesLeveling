'use client';

import React, { useState } from 'react';
import { Play, AlertTriangle, ExternalLink } from 'lucide-react';

interface SafeYouTubePlayerProps {
  youtubeId: string;
  title: string;
  channel?: string;
  onVideoError?: (youtubeId: string) => void;
  onVideoLoad?: (youtubeId: string) => void;
  className?: string;
}

// Validate YouTube ID format
function isValidYouTubeId(id: string): boolean {
  if (!id || id.length < 11) return false;
  // YouTube IDs are typically 11 characters: alphanumeric, dash, and underscore
  return /^[a-zA-Z0-9_-]{11}$/.test(id);
}

export default function SafeYouTubePlayer({
  youtubeId,
  title,
  channel,
  onVideoError,
  onVideoLoad,
  className = ""
}: SafeYouTubePlayerProps) {
  const [hasError, setHasError] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  // Validate YouTube ID on mount
  React.useEffect(() => {
    if (!isValidYouTubeId(youtubeId)) {
      console.error(`Invalid YouTube ID: "${youtubeId}" for video: ${title}`);
      setHasError(true);
      setIsLoading(false);
      if (onVideoError) {
        onVideoError(youtubeId);
      }
    }
  }, [youtubeId, title, onVideoError]);

  const handleIframeLoad = () => {
    setIsLoading(false);
    if (onVideoLoad) {
      onVideoLoad(youtubeId);
    }
  };

  const handleIframeError = () => {
    setHasError(true);
    setIsLoading(false);
    if (onVideoError) {
      onVideoError(youtubeId);
    }
  };

  const openInYouTube = () => {
    window.open(`https://www.youtube.com/watch?v=${youtubeId}`, '_blank');
  };

  if (hasError) {
    const isInvalidId = !isValidYouTubeId(youtubeId);

    return (
      <div className={`bg-gray-800/50 rounded-lg p-6 border border-red-500/30 ${className}`}>
        <div className="text-center">
          <AlertTriangle className="w-12 h-12 text-red-400 mx-auto mb-3" />
          <h3 className="text-lg font-semibold text-white mb-2">
            {isInvalidId ? 'ID de Video Inválido' : 'Video No Disponible'}
          </h3>
          <p className="text-gray-300 mb-4">{title}</p>
          <p className="text-sm text-red-200 mb-4">
            {isInvalidId
              ? `El ID del video "${youtubeId}" no tiene un formato válido. Por favor, contacta al soporte técnico.`
              : 'Este video no está disponible actualmente. Puede haber sido eliminado o estar restringido.'
            }
          </p>

          <div className="space-y-2">
            {!isInvalidId && (
              <button
                onClick={openInYouTube}
                className="w-full bg-red-600 hover:bg-red-700 py-2 px-4 rounded-lg text-sm font-semibold transition-colors flex items-center justify-center gap-2"
              >
                <ExternalLink className="w-4 h-4" />
                Intentar Abrir en YouTube
              </button>
            )}

            <div className="text-xs text-gray-400">
              Canal: {channel || 'Desconocido'}
              {isInvalidId && <div className="mt-1 text-red-300">ID: {youtubeId || '(vacío)'}</div>}
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={`relative ${className}`}>
      {isLoading && (
        <div className="absolute inset-0 bg-gray-800 rounded-lg flex items-center justify-center">
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-400 mx-auto mb-2"></div>
            <p className="text-sm text-gray-300">Cargando video...</p>
          </div>
        </div>
      )}
      
      <iframe
        src={`https://www.youtube.com/embed/${youtubeId}?rel=0&modestbranding=1`}
        title={title}
        className="w-full h-full rounded-lg"
        allowFullScreen
        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
        onLoad={handleIframeLoad}
        onError={handleIframeError}
        style={{ minHeight: '200px' }}
      />
    </div>
  );
}

// Hook para manejar errores de videos
export function useVideoErrorHandler() {
  const [failedVideos, setFailedVideos] = useState<Set<string>>(new Set());

  const handleVideoError = (youtubeId: string) => {
    setFailedVideos(prev => new Set([...prev, youtubeId]));
    
    // Reportar error al backend para actualizar catálogo
    fetch('/api/v1/simple-recommendations/report-video-error', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ youtube_id: youtubeId })
    }).catch(console.error);
  };

  const isVideoFailed = (youtubeId: string) => failedVideos.has(youtubeId);

  return { handleVideoError, isVideoFailed };
}
