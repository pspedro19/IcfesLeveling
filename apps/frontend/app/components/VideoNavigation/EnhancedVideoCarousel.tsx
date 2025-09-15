'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { 
  ChevronLeft, 
  ChevronRight, 
  Play, 
  Pause,
  Clock, 
  Star,
  Eye,
  Bookmark,
  Heart,
  Share2,
  ExternalLink,
  Maximize,
  Volume2,
  VolumeX,
  SkipBack,
  SkipForward,
  Shuffle,
  Repeat,
  RotateCcw,
  Loader,
  Wifi,
  WifiOff,
  Zap,
  Award,
  Target,
  TrendingUp
} from 'lucide-react';

interface VideoItem {
  video_id: number;
  youtube_id: string;
  title: string;
  description?: string;
  url: string;
  embed_url: string;
  duration_seconds?: number;
  channel?: string;
  thumbnail_url?: string;
  subject_id?: number;
  area_evaluada?: string;
  tema_principal?: string;
  recommendation_type: string;
  confidence_level: string;
  scores: {
    total_score: number;
    semantic_similarity?: number;
    difficulty_match?: number;
  };
  learning_objectives: string[];
  estimated_study_time: number;
  quality_score: number;
  relevance_score: number;
  watched_percentage?: number;
  is_bookmarked?: boolean;
  is_favorite?: boolean;
  preloaded?: boolean;
  loading?: boolean;
}

interface CarouselSettings {
  autoPlay: boolean;
  autoAdvanceTime: number;
  loop: boolean;
  preloadCount: number;
  transitionDuration: number;
  showThumbnails: boolean;
  showProgress: boolean;
  showQuickActions: boolean;
  smoothScrolling: boolean;
  keyboardNavigation: boolean;
  touchGestures: boolean;
}

interface EnhancedVideoCarouselProps {
  videos: VideoItem[];
  initialIndex?: number;
  settings?: Partial<CarouselSettings>;
  onVideoSelect?: (video: VideoItem, index: number) => void;
  onVideoPlay?: (video: VideoItem) => void;
  onVideoEnd?: (video: VideoItem) => void;
  onBookmark?: (video: VideoItem) => void;
  onFavorite?: (video: VideoItem) => void;
  onShare?: (video: VideoItem) => void;
  className?: string;
  height?: string | number;
}

const defaultSettings: CarouselSettings = {
  autoPlay: false,
  autoAdvanceTime: 30000,
  loop: true,
  preloadCount: 3,
  transitionDuration: 500,
  showThumbnails: true,
  showProgress: true,
  showQuickActions: true,
  smoothScrolling: true,
  keyboardNavigation: true,
  touchGestures: true
};

export default function EnhancedVideoCarousel({
  videos,
  initialIndex = 0,
  settings: customSettings = {},
  onVideoSelect,
  onVideoPlay,
  onVideoEnd,
  onBookmark,
  onFavorite,
  onShare,
  className = '',
  height = 'auto'
}: EnhancedVideoCarouselProps) {
  const settings = { ...defaultSettings, ...customSettings };
  
  // State management
  const [currentIndex, setCurrentIndex] = useState(initialIndex);
  const [isPlaying, setIsPlaying] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [volume, setVolume] = useState(1);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [playMode, setPlayMode] = useState<'normal' | 'shuffle' | 'repeat'>('normal');
  const [showControls, setShowControls] = useState(true);
  const [loading, setLoading] = useState(false);
  const [buffering, setBuffering] = useState(false);
  const [connectionQuality, setConnectionQuality] = useState<'good' | 'poor' | 'offline'>('good');
  const [visibleStartIndex, setVisibleStartIndex] = useState(0);
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });

  // Animation states
  const [isTransitioning, setIsTransitioning] = useState(false);
  const [slideDirection, setSlideDirection] = useState<'left' | 'right' | 'none'>('none');

  // Refs
  const mainVideoRef = useRef<HTMLDivElement>(null);
  const carouselRef = useRef<HTMLDivElement>(null);
  const thumbnailsRef = useRef<HTMLDivElement>(null);
  const autoPlayTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const controlsTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const preloadedVideos = useRef<Set<number>>(new Set());

  // Current video
  const currentVideo = videos[currentIndex];
  const maxVisibleThumbnails = 5;

  // Preload videos around current index
  const preloadVideos = useCallback((centerIndex: number) => {
    const preloadIndexes = [];
    for (let i = -settings.preloadCount; i <= settings.preloadCount; i++) {
      const index = centerIndex + i;
      if (index >= 0 && index < videos.length && !preloadedVideos.current.has(index)) {
        preloadIndexes.push(index);
      }
    }

    preloadIndexes.forEach(index => {
      const video = videos[index];
      if (video && !preloadedVideos.current.has(index)) {
        const img = new Image();
        img.src = video.thumbnail_url || `https://img.youtube.com/vi/${video.youtube_id}/maxresdefault.jpg`;
        img.onload = () => {
          preloadedVideos.current.add(index);
          // Update video state to mark as preloaded
          videos[index].preloaded = true;
        };
      }
    });
  }, [videos, settings.preloadCount]);

  // Initialize preloading
  useEffect(() => {
    preloadVideos(currentIndex);
  }, [currentIndex, preloadVideos]);

  // Auto-play functionality
  useEffect(() => {
    if (settings.autoPlay && isPlaying) {
      autoPlayTimeoutRef.current = setTimeout(() => {
        handleNext();
      }, settings.autoAdvanceTime);

      return () => {
        if (autoPlayTimeoutRef.current) {
          clearTimeout(autoPlayTimeoutRef.current);
        }
      };
    }
  }, [settings.autoPlay, isPlaying, currentIndex, settings.autoAdvanceTime]);

  // Auto-hide controls
  useEffect(() => {
    if (isPlaying && showControls) {
      controlsTimeoutRef.current = setTimeout(() => {
        setShowControls(false);
      }, 3000);
    }

    return () => {
      if (controlsTimeoutRef.current) {
        clearTimeout(controlsTimeoutRef.current);
      }
    };
  }, [isPlaying, showControls]);

  // Keyboard navigation
  useEffect(() => {
    if (!settings.keyboardNavigation) return;

    const handleKeyPress = (event: KeyboardEvent) => {
      switch (event.key) {
        case 'ArrowLeft':
          event.preventDefault();
          handlePrevious();
          break;
        case 'ArrowRight':
          event.preventDefault();
          handleNext();
          break;
        case ' ':
          event.preventDefault();
          handlePlayPause();
          break;
        case 'f':
          event.preventDefault();
          toggleFullscreen();
          break;
        case 'm':
          event.preventDefault();
          toggleMute();
          break;
        case 'Escape':
          event.preventDefault();
          if (isFullscreen) {
            toggleFullscreen();
          }
          break;
      }
    };

    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, [settings.keyboardNavigation, isFullscreen, isPlaying]);

  // Touch gesture handling
  useEffect(() => {
    if (!settings.touchGestures || !mainVideoRef.current) return;

    const element = mainVideoRef.current;

    const handleTouchStart = (event: TouchEvent) => {
      setIsDragging(true);
      const touch = event.touches[0];
      setDragStart({ x: touch.clientX, y: touch.clientY });
    };

    const handleTouchMove = (event: TouchEvent) => {
      if (!isDragging) return;
      event.preventDefault(); // Prevent scrolling
    };

    const handleTouchEnd = (event: TouchEvent) => {
      if (!isDragging) return;
      
      const touch = event.changedTouches[0];
      const deltaX = touch.clientX - dragStart.x;
      const deltaY = touch.clientY - dragStart.y;
      
      // Only handle horizontal swipes
      if (Math.abs(deltaX) > Math.abs(deltaY) && Math.abs(deltaX) > 50) {
        if (deltaX > 0) {
          handlePrevious();
        } else {
          handleNext();
        }
      }
      
      setIsDragging(false);
    };

    element.addEventListener('touchstart', handleTouchStart);
    element.addEventListener('touchmove', handleTouchMove, { passive: false });
    element.addEventListener('touchend', handleTouchEnd);

    return () => {
      element.removeEventListener('touchstart', handleTouchStart);
      element.removeEventListener('touchmove', handleTouchMove);
      element.removeEventListener('touchend', handleTouchEnd);
    };
  }, [settings.touchGestures, isDragging, dragStart]);

  // Network quality detection
  useEffect(() => {
    const updateConnectionQuality = () => {
      if (!navigator.onLine) {
        setConnectionQuality('offline');
        return;
      }

      // Simple heuristic based on connection type
      const connection = (navigator as any).connection;
      if (connection) {
        const { effectiveType, downlink } = connection;
        if (effectiveType === '4g' && downlink > 2) {
          setConnectionQuality('good');
        } else if (effectiveType === '3g' || downlink < 1) {
          setConnectionQuality('poor');
        } else {
          setConnectionQuality('good');
        }
      }
    };

    updateConnectionQuality();
    window.addEventListener('online', updateConnectionQuality);
    window.addEventListener('offline', updateConnectionQuality);

    return () => {
      window.removeEventListener('online', updateConnectionQuality);
      window.removeEventListener('offline', updateConnectionQuality);
    };
  }, []);

  const smoothTransition = useCallback((newIndex: number, direction: 'left' | 'right') => {
    if (isTransitioning) return;
    
    setIsTransitioning(true);
    setSlideDirection(direction);
    
    setTimeout(() => {
      setCurrentIndex(newIndex);
      setSlideDirection('none');
      
      setTimeout(() => {
        setIsTransitioning(false);
      }, settings.transitionDuration / 2);
    }, settings.transitionDuration / 2);
  }, [isTransitioning, settings.transitionDuration]);

  const handlePrevious = useCallback(() => {
    let newIndex;
    
    if (playMode === 'shuffle') {
      do {
        newIndex = Math.floor(Math.random() * videos.length);
      } while (newIndex === currentIndex && videos.length > 1);
    } else {
      newIndex = currentIndex - 1;
      if (newIndex < 0) {
        newIndex = settings.loop ? videos.length - 1 : 0;
      }
    }
    
    if (newIndex !== currentIndex) {
      if (settings.smoothScrolling) {
        smoothTransition(newIndex, 'left');
      } else {
        setCurrentIndex(newIndex);
      }
      
      // Update visible thumbnails
      if (newIndex < visibleStartIndex) {
        setVisibleStartIndex(Math.max(0, newIndex - 2));
      }
      
      if (onVideoSelect) {
        onVideoSelect(videos[newIndex], newIndex);
      }
      
      preloadVideos(newIndex);
    }
  }, [currentIndex, playMode, videos.length, settings.loop, settings.smoothScrolling, visibleStartIndex, onVideoSelect, smoothTransition, preloadVideos]);

  const handleNext = useCallback(() => {
    let newIndex;
    
    if (playMode === 'shuffle') {
      do {
        newIndex = Math.floor(Math.random() * videos.length);
      } while (newIndex === currentIndex && videos.length > 1);
    } else {
      newIndex = currentIndex + 1;
      if (newIndex >= videos.length) {
        newIndex = settings.loop ? 0 : videos.length - 1;
        if (!settings.loop && playMode === 'normal') {
          setIsPlaying(false);
          if (onVideoEnd) {
            onVideoEnd(currentVideo);
          }
          return;
        }
      }
    }
    
    if (newIndex !== currentIndex) {
      if (settings.smoothScrolling) {
        smoothTransition(newIndex, 'right');
      } else {
        setCurrentIndex(newIndex);
      }
      
      // Update visible thumbnails
      if (newIndex >= visibleStartIndex + maxVisibleThumbnails) {
        setVisibleStartIndex(Math.min(videos.length - maxVisibleThumbnails, newIndex - 2));
      }
      
      if (onVideoSelect) {
        onVideoSelect(videos[newIndex], newIndex);
      }
      
      preloadVideos(newIndex);
    }
  }, [currentIndex, playMode, videos.length, settings.loop, settings.smoothScrolling, visibleStartIndex, onVideoSelect, smoothTransition, preloadVideos, currentVideo, onVideoEnd]);

  const handlePlayPause = () => {
    const newPlayState = !isPlaying;
    setIsPlaying(newPlayState);
    
    if (newPlayState && onVideoPlay) {
      onVideoPlay(currentVideo);
    }
  };

  const handleThumbnailClick = (index: number) => {
    if (index === currentIndex) return;
    
    const direction = index > currentIndex ? 'right' : 'left';
    
    if (settings.smoothScrolling) {
      smoothTransition(index, direction);
    } else {
      setCurrentIndex(index);
    }
    
    if (onVideoSelect) {
      onVideoSelect(videos[index], index);
    }
    
    preloadVideos(index);
  };

  const toggleFullscreen = () => {
    if (!mainVideoRef.current) return;
    
    if (!isFullscreen) {
      if (mainVideoRef.current.requestFullscreen) {
        mainVideoRef.current.requestFullscreen();
      }
    } else {
      if (document.exitFullscreen) {
        document.exitFullscreen();
      }
    }
    
    setIsFullscreen(!isFullscreen);
  };

  const toggleMute = () => {
    setIsMuted(!isMuted);
  };

  const handleVolumeChange = (newVolume: number) => {
    setVolume(newVolume);
    setIsMuted(newVolume === 0);
  };

  const formatDuration = (seconds: number): string => {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
  };

  const getConfidenceColor = (level: string): string => {
    switch (level) {
      case 'high': return 'bg-green-500';
      case 'medium': return 'bg-yellow-500';
      case 'low': return 'bg-red-500';
      default: return 'bg-gray-500';
    }
  };

  const getRecommendationIcon = (type: string) => {
    switch (type) {
      case 'error_remediation': return <Target className="w-3 h-3" />;
      case 'skill_building': return <TrendingUp className="w-3 h-3" />;
      case 'concept_review': return <Eye className="w-3 h-3" />;
      case 'direct_practice': return <Award className="w-3 h-3" />;
      default: return <Play className="w-3 h-3" />;
    }
  };

  if (videos.length === 0) {
    return (
      <Card className={className}>
        <CardContent className="flex items-center justify-center h-64">
          <div className="text-center">
            <Play className="w-12 h-12 mx-auto text-gray-400 mb-4" />
            <p className="text-gray-600">No hay videos disponibles</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className={`w-full space-y-4 ${className}`} style={{ height }}>
      {/* Main Video Container */}
      <Card className="relative overflow-hidden">
        <div 
          ref={mainVideoRef}
          className="relative aspect-video bg-black rounded-lg overflow-hidden group"
          onMouseEnter={() => setShowControls(true)}
          onMouseLeave={() => setShowControls(isPlaying)}
        >
          {/* Video Content */}
          <div 
            className={`w-full h-full transition-transform duration-${settings.transitionDuration} ${
              isTransitioning ? 
                slideDirection === 'left' ? '-translate-x-full' : 
                slideDirection === 'right' ? 'translate-x-full' : '' 
                : ''
            }`}
          >
            {settings.showThumbnails ? (
              <img 
                src={currentVideo.thumbnail_url || `https://img.youtube.com/vi/${currentVideo.youtube_id}/maxresdefault.jpg`}
                alt={currentVideo.title}
                className="w-full h-full object-cover"
                onError={(e) => {
                  const target = e.target as HTMLImageElement;
                  target.src = `https://img.youtube.com/vi/${currentVideo.youtube_id}/hqdefault.jpg`;
                }}
              />
            ) : (
              <iframe
                src={`${currentVideo.embed_url}?autoplay=${isPlaying ? 1 : 0}&mute=${isMuted ? 1 : 0}`}
                title={currentVideo.title}
                className="w-full h-full"
                frameBorder="0"
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                allowFullScreen
              />
            )}
          </div>

          {/* Loading/Buffering Indicator */}
          {(loading || buffering) && (
            <div className="absolute inset-0 bg-black/50 flex items-center justify-center">
              <div className="flex items-center gap-2 text-white">
                <Loader className="w-6 h-6 animate-spin" />
                <span>{loading ? 'Cargando...' : 'Buffering...'}</span>
              </div>
            </div>
          )}

          {/* Connection Quality Indicator */}
          <div className="absolute top-4 right-4">
            {connectionQuality === 'offline' && (
              <Badge className="bg-red-500 text-white">
                <WifiOff className="w-3 h-3 mr-1" />
                Sin conexión
              </Badge>
            )}
            {connectionQuality === 'poor' && (
              <Badge className="bg-yellow-500 text-white">
                <Wifi className="w-3 h-3 mr-1" />
                Conexión lenta
              </Badge>
            )}
            {connectionQuality === 'good' && currentVideo.preloaded && (
              <Badge className="bg-green-500 text-white">
                <Zap className="w-3 h-3 mr-1" />
                Precargado
              </Badge>
            )}
          </div>

          {/* Video Info Overlay */}
          <div className={`absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-black/30 transition-opacity duration-300 ${
            showControls ? 'opacity-100' : 'opacity-0'
          }`}>
            {/* Top Info Bar */}
            <div className="absolute top-0 left-0 right-0 p-4 flex justify-between items-start">
              <div className="flex items-center gap-2">
                <Badge className={`${getConfidenceColor(currentVideo.confidence_level)} text-white`}>
                  {getRecommendationIcon(currentVideo.recommendation_type)}
                  <span className="ml-1 capitalize">{currentVideo.confidence_level}</span>
                </Badge>
                
                <Badge variant="secondary">
                  <Star className="w-3 h-3 mr-1" />
                  {(currentVideo.scores.total_score * 100).toFixed(0)}%
                </Badge>
              </div>

              {settings.showQuickActions && (
                <div className="flex items-center gap-2">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={(e) => {
                      e.stopPropagation();
                      if (onFavorite) onFavorite(currentVideo);
                    }}
                    className="text-white hover:bg-white/20"
                  >
                    <Heart className={`w-4 h-4 ${currentVideo.is_favorite ? 'fill-current text-red-500' : ''}`} />
                  </Button>
                  
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={(e) => {
                      e.stopPropagation();
                      if (onBookmark) onBookmark(currentVideo);
                    }}
                    className="text-white hover:bg-white/20"
                  >
                    <Bookmark className={`w-4 h-4 ${currentVideo.is_bookmarked ? 'fill-current text-blue-500' : ''}`} />
                  </Button>
                  
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={(e) => {
                      e.stopPropagation();
                      if (onShare) onShare(currentVideo);
                    }}
                    className="text-white hover:bg-white/20"
                  >
                    <Share2 className="w-4 h-4" />
                  </Button>
                </div>
              )}
            </div>

            {/* Central Play Button */}
            <div className="absolute inset-0 flex items-center justify-center">
              <Button
                size="lg"
                onClick={handlePlayPause}
                className="bg-blue-600 hover:bg-blue-700 text-white rounded-full w-16 h-16 shadow-lg"
              >
                {isPlaying ? <Pause className="w-8 h-8" /> : <Play className="w-8 h-8 ml-1" />}
              </Button>
            </div>

            {/* Bottom Info and Controls */}
            <div className="absolute bottom-0 left-0 right-0 p-4 space-y-3">
              {/* Progress Bar */}
              {settings.showProgress && currentVideo.watched_percentage !== undefined && (
                <div className="w-full">
                  <Progress 
                    value={currentVideo.watched_percentage} 
                    className="h-2 bg-white/20"
                  />
                  <div className="flex justify-between text-xs text-white/80 mt-1">
                    <span>{Math.round(currentVideo.watched_percentage)}% visto</span>
                    <span>
                      {currentVideo.duration_seconds && formatDuration(currentVideo.duration_seconds)}
                    </span>
                  </div>
                </div>
              )}

              <div className="flex items-end justify-between">
                {/* Video Title and Info */}
                <div className="flex-1 min-w-0 mr-4">
                  <h2 className="text-lg font-bold text-white line-clamp-2 mb-1">
                    {currentVideo.title}
                  </h2>
                  <div className="flex items-center gap-2 text-sm text-white/80">
                    <span>{currentVideo.channel}</span>
                    {currentVideo.area_evaluada && (
                      <>
                        <span>•</span>
                        <span>{currentVideo.area_evaluada}</span>
                      </>
                    )}
                    {currentVideo.duration_seconds && (
                      <>
                        <span>•</span>
                        <Clock className="w-3 h-3" />
                        <span>{formatDuration(currentVideo.duration_seconds)}</span>
                      </>
                    )}
                  </div>
                </div>

                {/* Control Buttons */}
                <div className="flex items-center gap-2">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={(e) => {
                      e.stopPropagation();
                      toggleMute();
                    }}
                    className="text-white hover:bg-white/20"
                  >
                    {isMuted ? <VolumeX className="w-4 h-4" /> : <Volume2 className="w-4 h-4" />}
                  </Button>

                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={(e) => {
                      e.stopPropagation();
                      window.open(currentVideo.url, '_blank');
                    }}
                    className="text-white hover:bg-white/20"
                  >
                    <ExternalLink className="w-4 h-4" />
                  </Button>

                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={(e) => {
                      e.stopPropagation();
                      toggleFullscreen();
                    }}
                    className="text-white hover:bg-white/20"
                  >
                    <Maximize className="w-4 h-4" />
                  </Button>
                </div>
              </div>
            </div>
          </div>

          {/* Navigation Arrows */}
          <Button
            variant="ghost"
            size="sm"
            onClick={(e) => {
              e.stopPropagation();
              handlePrevious();
            }}
            className={`absolute left-4 top-1/2 -translate-y-1/2 bg-black/50 text-white hover:bg-black/70 transition-opacity duration-300 ${
              showControls ? 'opacity-100' : 'opacity-0'
            }`}
            disabled={!settings.loop && currentIndex === 0}
          >
            <ChevronLeft className="w-6 h-6" />
          </Button>

          <Button
            variant="ghost"
            size="sm"
            onClick={(e) => {
              e.stopPropagation();
              handleNext();
            }}
            className={`absolute right-4 top-1/2 -translate-y-1/2 bg-black/50 text-white hover:bg-black/70 transition-opacity duration-300 ${
              showControls ? 'opacity-100' : 'opacity-0'
            }`}
            disabled={!settings.loop && currentIndex === videos.length - 1}
          >
            <ChevronRight className="w-6 h-6" />
          </Button>
        </div>
      </Card>

      {/* Thumbnails Navigation */}
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-4">
              <h3 className="font-medium">
                Video {currentIndex + 1} de {videos.length}
              </h3>
              
              <div className="flex items-center gap-2">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setPlayMode(
                    playMode === 'normal' ? 'shuffle' : 
                    playMode === 'shuffle' ? 'repeat' : 'normal'
                  )}
                  className="h-8"
                >
                  {playMode === 'shuffle' && <Shuffle className="w-4 h-4" />}
                  {playMode === 'repeat' && <Repeat className="w-4 h-4" />}
                  {playMode === 'normal' && <Play className="w-4 h-4" />}
                </Button>
                
                <Badge variant="outline" className="text-xs">
                  {playMode === 'normal' && 'Normal'}
                  {playMode === 'shuffle' && 'Aleatorio'}
                  {playMode === 'repeat' && 'Repetir'}
                </Badge>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setVisibleStartIndex(Math.max(0, visibleStartIndex - 1))}
                disabled={visibleStartIndex === 0}
              >
                <ChevronLeft className="w-4 h-4" />
              </Button>
              
              <span className="text-xs text-gray-500 min-w-[80px] text-center">
                {visibleStartIndex + 1}-{Math.min(visibleStartIndex + maxVisibleThumbnails, videos.length)} de {videos.length}
              </span>
              
              <Button
                variant="outline"
                size="sm"
                onClick={() => setVisibleStartIndex(Math.min(videos.length - maxVisibleThumbnails, visibleStartIndex + 1))}
                disabled={visibleStartIndex + maxVisibleThumbnails >= videos.length}
              >
                <ChevronRight className="w-4 h-4" />
              </Button>
            </div>
          </div>

          {/* Thumbnails Grid */}
          <div 
            ref={thumbnailsRef}
            className="flex gap-3 overflow-hidden"
          >
            {videos.slice(visibleStartIndex, visibleStartIndex + maxVisibleThumbnails).map((video, visibleIndex) => {
              const actualIndex = visibleStartIndex + visibleIndex;
              const isActive = actualIndex === currentIndex;
              
              return (
                <div
                  key={video.video_id}
                  className={`flex-shrink-0 cursor-pointer transition-all duration-300 ${
                    isActive ? 'ring-2 ring-blue-500 scale-105' : 'hover:scale-102'
                  }`}
                  onClick={() => handleThumbnailClick(actualIndex)}
                >
                  <Card className={`w-40 ${isActive ? 'bg-blue-50 shadow-lg' : 'hover:shadow-md'}`}>
                    <CardContent className="p-2">
                      <div className="relative mb-2">
                        <img 
                          src={video.thumbnail_url || `https://img.youtube.com/vi/${video.youtube_id}/mqdefault.jpg`}
                          alt={video.title}
                          className="w-full h-20 object-cover rounded"
                          onError={(e) => {
                            const target = e.target as HTMLImageElement;
                            target.src = `https://img.youtube.com/vi/${video.youtube_id}/hqdefault.jpg`;
                          }}
                        />
                        
                        {/* Duration badge */}
                        {video.duration_seconds && (
                          <Badge className="absolute bottom-1 right-1 text-xs">
                            {formatDuration(video.duration_seconds)}
                          </Badge>
                        )}
                        
                        {/* Progress indicator */}
                        {video.watched_percentage && video.watched_percentage > 0 && (
                          <div className="absolute bottom-0 left-0 right-0 h-1 bg-black/30 rounded-b">
                            <div 
                              className="h-full bg-blue-500 rounded-bl"
                              style={{ width: `${Math.min(video.watched_percentage, 100)}%` }}
                            />
                          </div>
                        )}
                        
                        {/* Preload indicator */}
                        {video.preloaded && (
                          <div className="absolute top-1 left-1">
                            <Zap className="w-3 h-3 text-green-500" />
                          </div>
                        )}
                        
                        {/* Active video indicator */}
                        {isActive && (
                          <div className="absolute inset-0 bg-blue-500/20 rounded flex items-center justify-center">
                            <Play className="w-6 h-6 text-blue-600" />
                          </div>
                        )}
                      </div>
                      
                      <h4 className="text-xs font-medium line-clamp-2 mb-1">
                        {video.title}
                      </h4>
                      
                      <div className="flex items-center justify-between">
                        <Badge 
                          variant="outline" 
                          className={`text-xs ${getConfidenceColor(video.confidence_level)} text-white border-0`}
                        >
                          {getRecommendationIcon(video.recommendation_type)}
                        </Badge>
                        
                        <div className="flex items-center gap-1">
                          <Star className="w-3 h-3 text-yellow-500" />
                          <span className="text-xs">
                            {(video.scores.total_score * 100).toFixed(0)}%
                          </span>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </div>
              );
            })}
          </div>

          {/* Progress Dots */}
          <div className="flex justify-center mt-4 gap-1">
            {videos.map((_, index) => (
              <button
                key={index}
                onClick={() => handleThumbnailClick(index)}
                className={`w-2 h-2 rounded-full transition-all duration-200 ${
                  index === currentIndex ? 'bg-blue-500 w-4' : 'bg-gray-300 hover:bg-gray-400'
                }`}
              />
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}