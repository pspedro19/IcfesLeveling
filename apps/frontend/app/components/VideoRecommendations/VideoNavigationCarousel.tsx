'use client';

import { useState, useEffect, useRef } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { 
  ChevronLeft, 
  ChevronRight, 
  Play, 
  Clock, 
  Star,
  BookOpen,
  Target,
  TrendingUp,
  AlertTriangle,
  ExternalLink,
  Eye,
  Pause
} from 'lucide-react';

interface VideoRecommendation {
  video_id: number;
  youtube_id: string;
  title: string;
  description?: string;
  url: string;
  embed_url: string;
  duration_seconds?: number;
  channel?: string;
  thumbnail_url?: string;
  recommendation_type: string;
  confidence_level: string;
  scores: {
    total_score: number;
  };
  learning_objectives: string[];
  estimated_study_time: number;
  quality_score: number;
}

interface VideoNavigationCarouselProps {
  videos: VideoRecommendation[];
  currentVideoIndex?: number;
  onVideoSelect: (video: VideoRecommendation, index: number) => void;
  onVideoPlay?: (video: VideoRecommendation) => void;
  autoPlay?: boolean;
  showThumbnails?: boolean;
  maxVisibleVideos?: number;
}

export default function VideoNavigationCarousel({
  videos,
  currentVideoIndex = 0,
  onVideoSelect,
  onVideoPlay,
  autoPlay = false,
  showThumbnails = true,
  maxVisibleVideos = 5
}: VideoNavigationCarouselProps) {
  const [activeIndex, setActiveIndex] = useState(currentVideoIndex);
  const [isPlaying, setIsPlaying] = useState(false);
  const [visibleStartIndex, setVisibleStartIndex] = useState(0);
  const carouselRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setActiveIndex(currentVideoIndex);
  }, [currentVideoIndex]);

  useEffect(() => {
    // Auto-advance to next video if auto-play is enabled
    if (autoPlay && isPlaying) {
      const timer = setTimeout(() => {
        if (activeIndex < videos.length - 1) {
          handleNext();
        } else {
          setIsPlaying(false);
        }
      }, 30000); // 30 seconds per video preview

      return () => clearTimeout(timer);
    }
  }, [autoPlay, isPlaying, activeIndex, videos.length]);

  const handlePrevious = () => {
    const newIndex = activeIndex > 0 ? activeIndex - 1 : videos.length - 1;
    setActiveIndex(newIndex);
    onVideoSelect(videos[newIndex], newIndex);
    
    // Adjust visible window if needed
    if (newIndex < visibleStartIndex) {
      setVisibleStartIndex(Math.max(0, newIndex - Math.floor(maxVisibleVideos / 2)));
    }
  };

  const handleNext = () => {
    const newIndex = activeIndex < videos.length - 1 ? activeIndex + 1 : 0;
    setActiveIndex(newIndex);
    onVideoSelect(videos[newIndex], newIndex);
    
    // Adjust visible window if needed
    if (newIndex >= visibleStartIndex + maxVisibleVideos) {
      setVisibleStartIndex(Math.min(videos.length - maxVisibleVideos, newIndex - Math.floor(maxVisibleVideos / 2)));
    }
  };

  const handleVideoClick = (video: VideoRecommendation, index: number) => {
    setActiveIndex(index);
    onVideoSelect(video, index);
  };

  const handlePlayClick = (video: VideoRecommendation) => {
    if (onVideoPlay) {
      onVideoPlay(video);
    }
    setIsPlaying(!isPlaying);
  };

  const formatDuration = (seconds: number): string => {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
  };

  const getRecommendationTypeIcon = (type: string) => {
    switch (type) {
      case 'error_remediation': return <AlertTriangle className="w-3 h-3" />;
      case 'skill_building': return <TrendingUp className="w-3 h-3" />;
      case 'concept_review': return <BookOpen className="w-3 h-3" />;
      case 'direct_practice': return <Target className="w-3 h-3" />;
      default: return <Play className="w-3 h-3" />;
    }
  };

  const getConfidenceBadgeColor = (level: string): string => {
    switch (level) {
      case 'high': return 'bg-green-500';
      case 'medium': return 'bg-yellow-500';
      case 'low': return 'bg-red-500';
      default: return 'bg-gray-500';
    }
  };

  if (videos.length === 0) {
    return (
      <Card>
        <CardContent className="text-center py-8">
          <Eye className="w-12 h-12 mx-auto text-gray-400 mb-4" />
          <p className="text-gray-600">No hay videos para mostrar</p>
        </CardContent>
      </Card>
    );
  }

  const currentVideo = videos[activeIndex];
  const visibleVideos = videos.slice(visibleStartIndex, visibleStartIndex + maxVisibleVideos);

  return (
    <div className="w-full space-y-4">
      {/* Main Video Display */}
      <Card>
        <CardContent className="p-0">
          <div className="relative aspect-video bg-black rounded-t-lg overflow-hidden">
            {showThumbnails ? (
              <img 
                src={currentVideo.thumbnail_url || `https://img.youtube.com/vi/${currentVideo.youtube_id}/maxresdefault.jpg`}
                alt={currentVideo.title}
                className="w-full h-full object-cover"
              />
            ) : (
              <iframe
                src={currentVideo.embed_url}
                title={currentVideo.title}
                className="w-full h-full"
                frameBorder="0"
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                allowFullScreen
              />
            )}
            
            {/* Video Overlay */}
            <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-black/20">
              {/* Play Button */}
              <div className="absolute inset-0 flex items-center justify-center">
                <Button
                  size="lg"
                  onClick={() => handlePlayClick(currentVideo)}
                  className="bg-blue-600 hover:bg-blue-700 text-white rounded-full w-16 h-16"
                >
                  {isPlaying ? <Pause className="w-8 h-8" /> : <Play className="w-8 h-8" />}
                </Button>
              </div>

              {/* Video Info Overlay */}
              <div className="absolute bottom-0 left-0 right-0 p-6 text-white">
                <div className="flex items-center justify-between mb-2">
                  <Badge className={`${getConfidenceBadgeColor(currentVideo.confidence_level)} text-white`}>
                    {getRecommendationTypeIcon(currentVideo.recommendation_type)}
                    <span className="ml-1 capitalize">{currentVideo.confidence_level}</span>
                  </Badge>
                  
                  <div className="flex items-center gap-2">
                    <Badge variant="secondary">
                      <Star className="w-3 h-3 mr-1" />
                      {(currentVideo.scores.total_score * 100).toFixed(0)}%
                    </Badge>
                    
                    {currentVideo.duration_seconds && (
                      <Badge variant="outline" className="border-white text-white">
                        <Clock className="w-3 h-3 mr-1" />
                        {formatDuration(currentVideo.duration_seconds)}
                      </Badge>
                    )}
                  </div>
                </div>
                
                <h2 className="text-xl font-bold mb-2 line-clamp-2">{currentVideo.title}</h2>
                
                <div className="flex items-center justify-between">
                  <p className="text-sm text-gray-200">{currentVideo.channel}</p>
                  
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => window.open(currentVideo.url, '_blank')}
                    className="border-white text-white hover:bg-white hover:text-black"
                  >
                    <ExternalLink className="w-4 h-4 mr-1" />
                    Abrir en YouTube
                  </Button>
                </div>
              </div>

              {/* Navigation Arrows */}
              <Button
                variant="outline"
                size="sm"
                onClick={handlePrevious}
                className="absolute left-4 top-1/2 transform -translate-y-1/2 bg-black/50 border-white text-white hover:bg-black/70"
              >
                <ChevronLeft className="w-4 h-4" />
              </Button>
              
              <Button
                variant="outline"
                size="sm"
                onClick={handleNext}
                className="absolute right-4 top-1/2 transform -translate-y-1/2 bg-black/50 border-white text-white hover:bg-black/70"
              >
                <ChevronRight className="w-4 h-4" />
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Video Navigation Carousel */}
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-medium text-sm">Videos Recomendados ({videos.length})</h3>
            
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setVisibleStartIndex(Math.max(0, visibleStartIndex - 1))}
                disabled={visibleStartIndex === 0}
              >
                <ChevronLeft className="w-4 h-4" />
              </Button>
              
              <span className="text-xs text-gray-500">
                {visibleStartIndex + 1}-{Math.min(visibleStartIndex + maxVisibleVideos, videos.length)} de {videos.length}
              </span>
              
              <Button
                variant="outline"
                size="sm"
                onClick={() => setVisibleStartIndex(Math.min(videos.length - maxVisibleVideos, visibleStartIndex + 1))}
                disabled={visibleStartIndex + maxVisibleVideos >= videos.length}
              >
                <ChevronRight className="w-4 h-4" />
              </Button>
            </div>
          </div>

          <div 
            ref={carouselRef}
            className="flex gap-3 overflow-hidden"
          >
            {visibleVideos.map((video, visibleIndex) => {
              const actualIndex = visibleStartIndex + visibleIndex;
              const isActive = actualIndex === activeIndex;
              
              return (
                <div
                  key={video.video_id}
                  className={`flex-shrink-0 cursor-pointer transition-all duration-200 ${
                    isActive ? 'ring-2 ring-blue-500 scale-105' : 'hover:scale-102'
                  }`}
                  onClick={() => handleVideoClick(video, actualIndex)}
                >
                  <Card className={`w-40 ${isActive ? 'bg-blue-50' : ''}`}>
                    <CardContent className="p-2">
                      <div className="relative mb-2">
                        <img 
                          src={video.thumbnail_url || `https://img.youtube.com/vi/${video.youtube_id}/mqdefault.jpg`}
                          alt={video.title}
                          className="w-full h-20 object-cover rounded"
                        />
                        
                        {video.duration_seconds && (
                          <Badge className="absolute bottom-1 right-1 text-xs">
                            {formatDuration(video.duration_seconds)}
                          </Badge>
                        )}
                        
                        {isActive && (
                          <div className="absolute inset-0 bg-blue-500/20 rounded flex items-center justify-center">
                            <Play className="w-6 h-6 text-blue-600" />
                          </div>
                        )}
                      </div>
                      
                      <h4 className="text-xs font-medium line-clamp-2 mb-1">{video.title}</h4>
                      
                      <div className="flex items-center justify-between">
                        <Badge variant="outline" className="text-xs">
                          {getRecommendationTypeIcon(video.recommendation_type)}
                        </Badge>
                        
                        <span className="text-xs text-gray-500">
                          {(video.scores.total_score * 100).toFixed(0)}%
                        </span>
                      </div>
                    </CardContent>
                  </Card>
                </div>
              );
            })}
          </div>

          {/* Progress Indicator */}
          <div className="flex items-center justify-center mt-4 gap-1">
            {videos.map((_, index) => (
              <div
                key={index}
                className={`w-2 h-2 rounded-full transition-all duration-200 ${
                  index === activeIndex ? 'bg-blue-500' : 'bg-gray-300'
                }`}
              />
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Auto-play Controls */}
      {autoPlay && (
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">Reproducción automática</span>
              
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setIsPlaying(!isPlaying)}
                >
                  {isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
                  {isPlaying ? 'Pausar' : 'Iniciar'}
                </Button>
                
                <span className="text-xs text-gray-500">
                  {activeIndex + 1} / {videos.length}
                </span>
              </div>
            </div>
            
            {isPlaying && (
              <div className="mt-2">
                <div className="w-full bg-gray-200 rounded-full h-1">
                  <div 
                    className="bg-blue-500 h-1 rounded-full transition-all duration-1000"
                    style={{ width: '0%' }}
                  />
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}