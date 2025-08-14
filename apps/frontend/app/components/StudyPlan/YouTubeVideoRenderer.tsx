'use client';

import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Play, Pause, Volume2, VolumeX, Maximize, CheckCircle,
  Clock, Eye, EyeOff, ThumbsUp, MessageCircle, Share2,
  BookOpen, Target, TrendingUp, AlertCircle, Info,
  ChevronDown, ChevronRight, Star, Zap, Video
} from 'lucide-react';

// Importar el sistema de diseño
import {
  buildButtonClasses,
  buildCardClasses,
  buildBadgeClasses,
  buildAlertClasses,
  buildSpinnerClasses,
  buildSkeletonClasses,
  spacingClasses,
  typographyClasses,
  animationClasses,
  cn
} from '../../utils/component-classes';

// Interfaces para videos de YouTube
interface YouTubeVideo {
  youtube_url: string;
  video_title: string;
  video_description?: string;
  thumbnail_url?: string;
  duration_seconds: number;
  relevance_score: number;
  difficulty_level?: number;
  content_type?: string;
  channel_name?: string;
  view_count?: number;
  like_count?: number;
  comment_count?: number;
}

interface YouTubeVideoRendererProps {
  videos: YouTubeVideo[];
  subject: string;
  weakTopics?: string[];
  strongTopics?: string[];
  learningStyle?: string;
  onVideoSelect?: (video: YouTubeVideo) => void;
  onVideoComplete?: (video: YouTubeVideo, progress: number) => void;
  showRecommendations?: boolean;
  maxVideos?: number;
}

interface VideoPlayerState {
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

const YouTubeVideoRenderer: React.FC<YouTubeVideoRendererProps> = ({
  videos,
  subject,
  weakTopics = [],
  strongTopics = [],
  learningStyle,
  onVideoSelect,
  onVideoComplete,
  showRecommendations = true,
  maxVideos = 10
}) => {
  const [selectedVideo, setSelectedVideo] = useState<YouTubeVideo | null>(null);
  const [videoState, setVideoState] = useState<VideoPlayerState>({
    isPlaying: false,
    currentTime: 0,
    duration: 0,
    volume: 1,
    isMuted: false,
    isFullscreen: false,
    watchedSeconds: 0,
    watchPercentage: 0,
    isCompleted: false
  });
  const [showVideoPlayer, setShowVideoPlayer] = useState(false);
  const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [recommendations, setRecommendations] = useState<YouTubeVideo[]>([]);
  
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

  // Formatear duración
  const formatDuration = (seconds: number): string => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    
    if (hours > 0) {
      return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }
    return `${minutes}:${secs.toString().padStart(2, '0')}`;
  };

  // Formatear número de vistas
  const formatViewCount = (count: number): string => {
    if (count >= 1000000) {
      return `${(count / 1000000).toFixed(1)}M`;
    } else if (count >= 1000) {
      return `${(count / 1000).toFixed(1)}K`;
    }
    return count.toString();
  };

  // Obtener color de dificultad
  const getDifficultyColor = (level: number): string => {
    switch (level) {
      case 1: return 'success';
      case 2: return 'success';
      case 3: return 'warning';
      case 4: return 'warning';
      case 5: return 'error';
      default: return 'neutral';
    }
  };

  // Obtener texto de dificultad
  const getDifficultyText = (level: number): string => {
    switch (level) {
      case 1: return 'Muy Fácil';
      case 2: return 'Fácil';
      case 3: return 'Intermedio';
      case 4: return 'Difícil';
      case 5: return 'Muy Difícil';
      default: return 'Intermedio';
    }
  };

  // Cargar recomendaciones personalizadas
  useEffect(() => {
    if (showRecommendations && (weakTopics.length > 0 || strongTopics.length > 0)) {
      loadPersonalizedRecommendations();
    }
  }, [weakTopics, strongTopics, subject]);

  const loadPersonalizedRecommendations = async () => {
    try {
      setLoading(true);
      const response = await fetch(`/api/v1/youtube/recommendations/for-yml-plan?` + 
        new URLSearchParams({
          subject,
          weak_topics: weakTopics.join(','),
          strong_topics: strongTopics.join(','),
          learning_style: learningStyle || '',
          limit_per_topic: '3'
        }));
      
      if (response.ok) {
        const data = await response.json();
        setRecommendations(data.data.videos.all_videos || []);
      }
    } catch (error) {
      console.error('Error cargando recomendaciones:', error);
      setError('Error al cargar recomendaciones');
    } finally {
      setLoading(false);
    }
  };

  const handleVideoSelect = (video: YouTubeVideo) => {
    setSelectedVideo(video);
    setShowVideoPlayer(true);
    onVideoSelect?.(video);
    
    // Resetear estado del reproductor
    setVideoState({
      isPlaying: false,
      currentTime: 0,
      duration: video.duration_seconds,
      volume: 1,
      isMuted: false,
      isFullscreen: false,
      watchedSeconds: 0,
      watchPercentage: 0,
      isCompleted: false
    });
  };

  const handleVideoComplete = (progress: number) => {
    if (selectedVideo) {
      onVideoComplete?.(selectedVideo, progress);
    }
  };

  const toggleSection = (sectionId: string) => {
    setExpandedSections(prev => ({
      ...prev,
      [sectionId]: !prev[sectionId]
    }));
  };

  const videoId = selectedVideo ? extractYouTubeId(selectedVideo.youtube_url) : '';
  const embedUrl = videoId ? `https://www.youtube.com/embed/${videoId}?enablejsapi=1&origin=${window.location.origin}` : '';

  // Loading State
  if (loading && recommendations.length === 0) {
    return (
      <div className={cn(spacingClasses.container, "py-8")}>
        <div className="space-y-6">
          <div className={buildSkeletonClasses('title', "w-1/3")} />
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {[1, 2, 3, 4, 5, 6].map(i => (
              <div key={i} className={buildSkeletonClasses('card', "h-48")} />
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={cn(spacingClasses.container, "py-8")}>
      <motion.div 
        className="space-y-8"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
      >
        {/* Header */}
        <motion.div 
          className="text-center space-y-4"
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.1, duration: 0.5 }}
        >
          <h1 className={cn(typographyClasses.heading.h1, "text-primary")}>
            Videos Educativos Personalizados
          </h1>
          <p className={cn(typographyClasses.body.large, "text-neutral-600 max-w-2xl mx-auto")}>
            Videos seleccionados específicamente para tu plan de estudio en {subject}
          </p>
          
          {/* Estadísticas rápidas */}
          <div className="flex items-center justify-center space-x-6 text-sm text-neutral-500">
            <span className="flex items-center space-x-1">
              <Video className="h-4 w-4" />
              <span>{videos.length} videos disponibles</span>
            </span>
            <span className="flex items-center space-x-1">
              <Target className="h-4 w-4" />
              <span>{weakTopics.length} temas débiles</span>
            </span>
            <span className="flex items-center space-x-1">
              <Star className="h-4 w-4" />
              <span>{strongTopics.length} temas fuertes</span>
            </span>
          </div>
        </motion.div>

        {/* Video Player Modal */}
        <AnimatePresence>
          {showVideoPlayer && selectedVideo && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4"
              onClick={() => setShowVideoPlayer(false)}
            >
              <motion.div
                initial={{ scale: 0.9, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                exit={{ scale: 0.9, opacity: 0 }}
                className="bg-white rounded-lg shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-hidden"
                onClick={(e) => e.stopPropagation()}
              >
                {/* Header del video */}
                <div className="p-6 border-b border-neutral-200">
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <h2 className={typographyClasses.heading.h3}>{selectedVideo.video_title}</h2>
                      <div className="flex items-center space-x-4 mt-2 text-sm text-neutral-600">
                        {selectedVideo.channel_name && (
                          <span className="flex items-center space-x-1">
                            <BookOpen className="h-4 w-4" />
                            <span>{selectedVideo.channel_name}</span>
                          </span>
                        )}
                        <span className="flex items-center space-x-1">
                          <Clock className="h-4 w-4" />
                          <span>{formatDuration(selectedVideo.duration_seconds)}</span>
                        </span>
                        {selectedVideo.difficulty_level && (
                          <span className={buildBadgeClasses({ 
                            variant: getDifficultyColor(selectedVideo.difficulty_level), 
                            size: 'sm' 
                          })}>
                            {getDifficultyText(selectedVideo.difficulty_level)}
                          </span>
                        )}
                      </div>
                    </div>
                    <button
                      onClick={() => setShowVideoPlayer(false)}
                      className={buildButtonClasses({ variant: 'ghost', size: 'sm' })}
                    >
                      ×
                    </button>
                  </div>
                </div>

                {/* Reproductor de video */}
                <div className="relative aspect-video bg-black">
                  <iframe
                    ref={iframeRef}
                    src={embedUrl}
                    title={selectedVideo.video_title}
                    className="w-full h-full"
                    frameBorder="0"
                    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                    allowFullScreen
                  />
                </div>

                {/* Información del video */}
                <div className="p-6">
                  <div className="space-y-4">
                    <p className="text-neutral-700">{selectedVideo.video_description}</p>
                    
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-4">
                        <span className="flex items-center space-x-1 text-sm text-neutral-600">
                          <Eye className="h-4 w-4" />
                          <span>{selectedVideo.view_count ? formatViewCount(selectedVideo.view_count) : 'N/A'}</span>
                        </span>
                        <span className="flex items-center space-x-1 text-sm text-neutral-600">
                          <ThumbsUp className="h-4 w-4" />
                          <span>{selectedVideo.like_count ? formatViewCount(selectedVideo.like_count) : 'N/A'}</span>
                        </span>
                        <span className="flex items-center space-x-1 text-sm text-neutral-600">
                          <MessageCircle className="h-4 w-4" />
                          <span>{selectedVideo.comment_count ? formatViewCount(selectedVideo.comment_count) : 'N/A'}</span>
                        </span>
                      </div>
                      
                      <div className="flex space-x-2">
                        <button className={buildButtonClasses({ variant: 'outline', size: 'sm' })}>
                          <Share2 className="h-4 w-4 mr-1" />
                          Compartir
                        </button>
                        <button 
                          className={buildButtonClasses({ variant: 'primary', size: 'sm' })}
                          onClick={() => handleVideoComplete(videoState.watchPercentage)}
                        >
                          <CheckCircle className="h-4 w-4 mr-1" />
                          Marcar Completado
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Videos por Temas Débiles */}
        {weakTopics.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2, duration: 0.5 }}
          >
            <div className={buildCardClasses({ size: 'lg', variant: 'elevated' })}>
              <div className="space-y-6">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <div className="p-2 bg-error/10 rounded-lg">
                      <Target className="h-6 w-6 text-error" />
                    </div>
                    <h2 className={typographyClasses.heading.h3}>Temas que Necesitas Reforzar</h2>
                  </div>
                  <button
                    onClick={() => toggleSection('weak-topics')}
                    className="p-2 text-neutral-400 hover:text-neutral-600 transition-colors"
                  >
                    {expandedSections['weak-topics'] ? (
                      <ChevronDown className="h-5 w-5" />
                    ) : (
                      <ChevronRight className="h-5 w-5" />
                    )}
                  </button>
                </div>

                <AnimatePresence>
                  {expandedSections['weak-topics'] && (
                    <motion.div
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: 'auto' }}
                      exit={{ opacity: 0, height: 0 }}
                      transition={{ duration: 0.3 }}
                    >
                      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        {videos
                          .filter(video => video.relevance_score > 0.8)
                          .slice(0, 6)
                          .map((video, index) => (
                            <motion.div
                              key={index}
                              className={buildCardClasses({ 
                                size: 'md', 
                                variant: 'interactive',
                                className: "group cursor-pointer"
                              })}
                              initial={{ opacity: 0, y: 20 }}
                              animate={{ opacity: 1, y: 0 }}
                              transition={{ delay: 0.1 * index, duration: 0.4 }}
                              whileHover={{ y: -2 }}
                              onClick={() => handleVideoSelect(video)}
                            >
                              <div className="aspect-video bg-neutral-100 rounded-lg mb-3 overflow-hidden">
                                {video.thumbnail_url ? (
                                  <img 
                                    src={video.thumbnail_url} 
                                    alt={video.video_title}
                                    className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-200"
                                  />
                                ) : (
                                  <div className="w-full h-full flex items-center justify-center bg-neutral-200">
                                    <Play className="h-12 w-12 text-neutral-400" />
                                  </div>
                                )}
                              </div>
                              
                              <div className="space-y-2">
                                <h3 className={cn(typographyClasses.body.medium, "font-semibold line-clamp-2")}>
                                  {video.video_title}
                                </h3>
                                
                                <div className="flex items-center justify-between text-sm text-neutral-600">
                                  <span className="flex items-center space-x-1">
                                    <Clock className="h-3 w-3" />
                                    <span>{formatDuration(video.duration_seconds)}</span>
                                  </span>
                                  <span className={buildBadgeClasses({ 
                                    variant: video.difficulty_level ? getDifficultyColor(video.difficulty_level) : 'neutral',
                                    size: 'xs' 
                                  })}>
                                    {video.difficulty_level ? getDifficultyText(video.difficulty_level) : 'Intermedio'}
                                  </span>
                                </div>
                                
                                {video.channel_name && (
                                  <p className="text-xs text-neutral-500 truncate">
                                    {video.channel_name}
                                  </p>
                                )}
                              </div>
                            </motion.div>
                          ))}
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            </div>
          </motion.div>
        )}

        {/* Videos Recomendados */}
        {recommendations.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3, duration: 0.5 }}
          >
            <div className={buildCardClasses({ size: 'lg', variant: 'elevated' })}>
              <div className="space-y-6">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <div className="p-2 bg-primary/10 rounded-lg">
                      <Zap className="h-6 w-6 text-primary" />
                    </div>
                    <h2 className={typographyClasses.heading.h3}>Recomendaciones Personalizadas</h2>
                  </div>
                  <button
                    onClick={() => toggleSection('recommendations')}
                    className="p-2 text-neutral-400 hover:text-neutral-600 transition-colors"
                  >
                    {expandedSections['recommendations'] ? (
                      <ChevronDown className="h-5 w-5" />
                    ) : (
                      <ChevronRight className="h-5 w-5" />
                    )}
                  </button>
                </div>

                <AnimatePresence>
                  {expandedSections['recommendations'] && (
                    <motion.div
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: 'auto' }}
                      exit={{ opacity: 0, height: 0 }}
                      transition={{ duration: 0.3 }}
                    >
                      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        {recommendations.slice(0, 9).map((video, index) => (
                          <motion.div
                            key={index}
                            className={buildCardClasses({ 
                              size: 'md', 
                              variant: 'interactive',
                              className: "group cursor-pointer"
                            })}
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: 0.1 * index, duration: 0.4 }}
                            whileHover={{ y: -2 }}
                            onClick={() => handleVideoSelect(video)}
                          >
                            <div className="aspect-video bg-neutral-100 rounded-lg mb-3 overflow-hidden">
                              {video.thumbnail_url ? (
                                <img 
                                  src={video.thumbnail_url} 
                                  alt={video.video_title}
                                  className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-200"
                                />
                              ) : (
                                <div className="w-full h-full flex items-center justify-center bg-neutral-200">
                                  <Play className="h-12 w-12 text-neutral-400" />
                                </div>
                              )}
                            </div>
                            
                            <div className="space-y-2">
                              <h3 className={cn(typographyClasses.body.medium, "font-semibold line-clamp-2")}>
                                {video.video_title}
                              </h3>
                              
                              <div className="flex items-center justify-between text-sm text-neutral-600">
                                <span className="flex items-center space-x-1">
                                  <Clock className="h-3 w-3" />
                                  <span>{formatDuration(video.duration_seconds)}</span>
                                </span>
                                <span className={buildBadgeClasses({ 
                                  variant: video.difficulty_level ? getDifficultyColor(video.difficulty_level) : 'neutral',
                                  size: 'xs' 
                                })}>
                                  {video.difficulty_level ? getDifficultyText(video.difficulty_level) : 'Intermedio'}
                                </span>
                              </div>
                              
                              {video.channel_name && (
                                <p className="text-xs text-neutral-500 truncate">
                                  {video.channel_name}
                                </p>
                              )}
                            </div>
                          </motion.div>
                        ))}
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            </div>
          </motion.div>
        )}

        {/* Error State */}
        {error && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4, duration: 0.5 }}
          >
            <div className={buildAlertClasses({ variant: 'error', size: 'lg' })}>
              <div className="flex items-center space-x-3">
                <AlertCircle className="h-6 w-6 text-error" />
                <div>
                  <h3 className="font-semibold">Error al cargar videos</h3>
                  <p className="text-sm">{error}</p>
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </motion.div>
    </div>
  );
};

export default YouTubeVideoRenderer;
