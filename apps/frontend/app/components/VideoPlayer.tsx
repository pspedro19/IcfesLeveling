'use client';

import { useState, useEffect, useRef } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { 
  Play, 
  Pause, 
  Volume2, 
  VolumeX, 
  Maximize, 
  CheckCircle,
  Clock,
  Eye
} from 'lucide-react';

interface VideoPlayerProps {
  youtubeUrl: string;
  videoTitle?: string;
  planId: string;
  unitNumber: number;
  onProgressUpdate?: (watchedSeconds: number, percentage: number) => void;
  onVideoComplete?: () => void;
  initialProgress?: number;
  completionThreshold?: number;
}

interface VideoState {
  isPlaying: boolean;
  currentTime: number;
  duration: number;
  volume: number;
  isMuted: boolean;
  isFullscreen: boolean;
  watchedSeconds: number;
  watchPercentage: number;
  isCompleted: boolean;
}

export default function VideoPlayer({
  youtubeUrl,
  videoTitle = "Video Educativo",
  planId,
  unitNumber,
  onProgressUpdate,
  onVideoComplete,
  initialProgress = 0,
  completionThreshold = 80
}: VideoPlayerProps) {
  const [videoState, setVideoState] = useState<VideoState>({
    isPlaying: false,
    currentTime: 0,
    duration: 0,
    volume: 1,
    isMuted: false,
    isFullscreen: false,
    watchedSeconds: initialProgress,
    watchPercentage: 0,
    isCompleted: false
  });

  const [isTracking, setIsTracking] = useState(false);
  const [lastUpdateTime, setLastUpdateTime] = useState(0);
  const iframeRef = useRef<HTMLIFrameElement>(null);
  const progressIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // Extraer ID del video de YouTube
  const extractYouTubeId = (url: string): string => {
    const patterns = [
      /(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([^&\n?#]+)/,
      /youtube\.com\/v\/([^&\n?#]+)/
    ];
    
    for (const pattern of patterns) {
      const match = url.match(pattern);
      if (match) {
        return match[1];
      }
    }
    return '';
  };

  const videoId = extractYouTubeId(youtubeUrl);
  const embedUrl = `https://www.youtube.com/embed/${videoId}?enablejsapi=1&origin=${window.location.origin}`;

  // Función para actualizar progreso en el backend
  const updateVideoProgress = async (watchedSeconds: number, percentage: number) => {
    try {
      const response = await fetch('/api/v1/videos/progress', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          plan_id: planId,
          unit_number: unitNumber,
          youtube_url: youtubeUrl,
          watched_seconds: watchedSeconds,
          video_duration_seconds: videoState.duration
        })
      });

      if (response.ok) {
        const data = await response.json();
        const isCompleted = data.watch_percentage >= completionThreshold;
        
        setVideoState(prev => ({
          ...prev,
          isCompleted
        }));

        if (isCompleted && onVideoComplete) {
          onVideoComplete();
        }

        if (onProgressUpdate) {
          onProgressUpdate(watchedSeconds, percentage);
        }
      }
    } catch (error) {
      console.error('Error updating video progress:', error);
    }
  };

  // Simular tracking de progreso (en producción, esto se haría con la YouTube API)
  useEffect(() => {
    const startProgressTracking = () => {
      if (progressIntervalRef.current) {
        clearInterval(progressIntervalRef.current);
      }

      progressIntervalRef.current = setInterval(() => {
        if (videoState.isPlaying && videoState.duration > 0) {
          const newWatchedSeconds = Math.min(videoState.watchedSeconds + 1, videoState.duration);
          const newPercentage = (newWatchedSeconds / videoState.duration) * 100;

          setVideoState(prev => ({
            ...prev,
            watchedSeconds: newWatchedSeconds,
            watchPercentage: newPercentage
          }));

          // Actualizar progreso cada 5 segundos
          if (Date.now() - lastUpdateTime > 5000) {
            updateVideoProgress(newWatchedSeconds, newPercentage);
            setLastUpdateTime(Date.now());
          }
        }
      }, 1000);

      return () => {
        if (progressIntervalRef.current) {
          clearInterval(progressIntervalRef.current);
        }
      };
    };

    if (videoState.isPlaying) {
      startProgressTracking();
    }

    return () => {
      if (progressIntervalRef.current) {
        clearInterval(progressIntervalRef.current);
      }
    };
  }, [videoState.isPlaying, videoState.duration, lastUpdateTime]);

  // Simular duración del video (en producción, esto vendría de la YouTube API)
  useEffect(() => {
    // Simular una duración de 10 minutos
    setVideoState(prev => ({
      ...prev,
      duration: 600,
      watchPercentage: prev.watchedSeconds > 0 ? (prev.watchedSeconds / 600) * 100 : 0
    }));
  }, []);

  const handlePlayPause = () => {
    setVideoState(prev => ({
      ...prev,
      isPlaying: !prev.isPlaying
    }));
  };

  const handleVolumeChange = (newVolume: number) => {
    setVideoState(prev => ({
      ...prev,
      volume: newVolume,
      isMuted: newVolume === 0
    }));
  };

  const handleMuteToggle = () => {
    setVideoState(prev => ({
      ...prev,
      isMuted: !prev.isMuted,
      volume: prev.isMuted ? 1 : 0
    }));
  };

  const handleFullscreen = () => {
    if (iframeRef.current) {
      if (document.fullscreenElement) {
        document.exitFullscreen();
      } else {
        iframeRef.current.requestFullscreen();
      }
      setVideoState(prev => ({
        ...prev,
        isFullscreen: !prev.isFullscreen
      }));
    }
  };

  const formatTime = (seconds: number): string => {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
  };

  const getProgressColor = (percentage: number): string => {
    if (percentage >= completionThreshold) return 'bg-green-500';
    if (percentage >= 50) return 'bg-yellow-500';
    return 'bg-blue-500';
  };

  return (
    <Card className="w-full max-w-4xl mx-auto">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <Eye className="w-5 h-5" />
            {videoTitle}
          </CardTitle>
          <div className="flex items-center gap-2">
            {videoState.isCompleted && (
              <Badge variant="default" className="bg-green-500">
                <CheckCircle className="w-4 h-4 mr-1" />
                Completado
              </Badge>
            )}
            <Badge variant="secondary">
              <Clock className="w-4 h-4 mr-1" />
              {formatTime(videoState.watchedSeconds)} / {formatTime(videoState.duration)}
            </Badge>
          </div>
        </div>
      </CardHeader>
      
      <CardContent className="space-y-4">
        {/* Reproductor de Video */}
        <div className="relative aspect-video bg-black rounded-lg overflow-hidden">
          <iframe
            ref={iframeRef}
            src={embedUrl}
            title={videoTitle}
            className="w-full h-full"
            frameBorder="0"
            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
            allowFullScreen
          />
          
          {/* Overlay de controles */}
          <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/80 to-transparent p-4">
            <div className="flex items-center justify-between text-white">
              <div className="flex items-center gap-2">
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={handlePlayPause}
                  className="text-white hover:bg-white/20"
                >
                  {videoState.isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
                </Button>
                
                <div className="flex items-center gap-2">
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={handleMuteToggle}
                    className="text-white hover:bg-white/20"
                  >
                    {videoState.isMuted ? <VolumeX className="w-4 h-4" /> : <Volume2 className="w-4 h-4" />}
                  </Button>
                  
                  <input
                    type="range"
                    min="0"
                    max="1"
                    step="0.1"
                    value={videoState.isMuted ? 0 : videoState.volume}
                    onChange={(e) => handleVolumeChange(parseFloat(e.target.value))}
                    className="w-20"
                  />
                </div>
              </div>
              
              <Button
                size="sm"
                variant="ghost"
                onClick={handleFullscreen}
                className="text-white hover:bg-white/20"
              >
                <Maximize className="w-4 h-4" />
              </Button>
            </div>
          </div>
        </div>

        {/* Barra de Progreso */}
        <div className="space-y-2">
          <div className="flex items-center justify-between text-sm">
            <span className="text-gray-600">Progreso de visualización</span>
            <span className="font-medium">
              {videoState.watchPercentage.toFixed(1)}%
            </span>
          </div>
          
          <div className="w-full bg-gray-200 rounded-full h-3">
            <div 
              className={`h-3 rounded-full transition-all duration-300 ${getProgressColor(videoState.watchPercentage)}`}
              style={{ width: `${Math.min(videoState.watchPercentage, 100)}%` }}
            />
          </div>
          
          <div className="flex items-center justify-between text-xs text-gray-500">
            <span>Umbral de completación: {completionThreshold}%</span>
            <span>
              {videoState.watchPercentage >= completionThreshold ? '✅ Completado' : '⏳ En progreso'}
            </span>
          </div>
        </div>

        {/* Información del Video */}
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div className="space-y-1">
            <span className="text-gray-600">Tiempo visto:</span>
            <div className="font-medium">{formatTime(videoState.watchedSeconds)}</div>
          </div>
          
          <div className="space-y-1">
            <span className="text-gray-600">Duración total:</span>
            <div className="font-medium">{formatTime(videoState.duration)}</div>
          </div>
          
          <div className="space-y-1">
            <span className="text-gray-600">Estado:</span>
            <div className="font-medium">
              {videoState.isPlaying ? 'Reproduciendo' : 'Pausado'}
            </div>
          </div>
          
          <div className="space-y-1">
            <span className="text-gray-600">Volumen:</span>
            <div className="font-medium">
              {videoState.isMuted ? 'Silenciado' : `${Math.round(videoState.volume * 100)}%`}
            </div>
          </div>
        </div>

        {/* Botón de tracking manual */}
        <div className="flex justify-center">
          <Button
            onClick={() => {
              setIsTracking(!isTracking);
              if (!isTracking) {
                updateVideoProgress(videoState.watchedSeconds, videoState.watchPercentage);
              }
            }}
            variant={isTracking ? "default" : "outline"}
            className="w-full max-w-xs"
          >
            {isTracking ? '🔄 Tracking Activo' : '📊 Iniciar Tracking'}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
} 