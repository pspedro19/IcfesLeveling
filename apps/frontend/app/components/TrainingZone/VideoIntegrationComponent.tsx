'use client';

import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Play, 
  Pause, 
  Volume2, 
  VolumeX, 
  Maximize, 
  Minimize,
  SkipBack,
  SkipForward,
  Settings,
  Bookmark,
  BookmarkCheck,
  ThumbsUp,
  ThumbsDown,
  ExternalLink,
  Clock,
  User,
  Eye,
  Star
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Slider } from "@/components/ui/slider";

interface VideoRecommendation {
  id: string;
  title: string;
  description: string;
  url: string;
  thumbnail: string;
  duration: string;
  channel: string;
  views: string;
  rating: number;
  relevance_score: number;
  topic: string;
  difficulty: 'beginner' | 'intermediate' | 'advanced';
  created_at: string;
  user_interactions?: {
    viewed: boolean;
    liked: boolean;
    bookmarked: boolean;
    completion_percentage: number;
  };
}

interface VideoIntegrationComponentProps {
  recommendations: VideoRecommendation[];
  questionId: string;
  topic: string;
  onVideoInteraction: (videoId: string, interaction: {
    type: 'view' | 'like' | 'bookmark' | 'complete';
    data?: any;
  }) => void;
  onRequestMoreVideos?: () => Promise<VideoRecommendation[]>;
}

export default function VideoIntegrationComponent({
  recommendations,
  questionId,
  topic,
  onVideoInteraction,
  onRequestMoreVideos
}: VideoIntegrationComponentProps) {
  const [selectedVideo, setSelectedVideo] = useState<VideoRecommendation | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [volume, setVolume] = useState(1);
  const [playbackRate, setPlaybackRate] = useState(1);
  const [showSettings, setShowSettings] = useState(false);

  const videoRef = useRef<HTMLVideoElement>(null);
  const playerRef = useRef<HTMLDivElement>(null);

  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const handleVideoSelect = (video: VideoRecommendation) => {
    setSelectedVideo(video);
    if (!video.user_interactions?.viewed) {
      onVideoInteraction(video.id, { type: 'view' });
    }
  };

  const handlePlayPause = () => {
    if (!videoRef.current) return;
    
    if (isPlaying) {
      videoRef.current.pause();
    } else {
      videoRef.current.play();
    }
    setIsPlaying(!isPlaying);
  };

  const handleMute = () => {
    if (!videoRef.current) return;
    videoRef.current.muted = !isMuted;
    setIsMuted(!isMuted);
  };

  const handleSeek = (value: number[]) => {
    if (!videoRef.current) return;
    const newTime = (value[0] / 100) * duration;
    videoRef.current.currentTime = newTime;
    setCurrentTime(newTime);
  };

  const handleVolumeChange = (value: number[]) => {
    if (!videoRef.current) return;
    const newVolume = value[0] / 100;
    videoRef.current.volume = newVolume;
    setVolume(newVolume);
  };

  const handlePlaybackRateChange = (rate: number) => {
    if (!videoRef.current) return;
    videoRef.current.playbackRate = rate;
    setPlaybackRate(rate);
    setShowSettings(false);
  };

  const handleFullscreen = () => {
    if (!playerRef.current) return;
    
    if (!isFullscreen) {
      if (playerRef.current.requestFullscreen) {
        playerRef.current.requestFullscreen();
      }
    } else {
      if (document.exitFullscreen) {
        document.exitFullscreen();
      }
    }
    setIsFullscreen(!isFullscreen);
  };

  const handleVideoEnd = () => {
    setIsPlaying(false);
    setCurrentTime(0);
    if (selectedVideo) {
      onVideoInteraction(selectedVideo.id, { 
        type: 'complete',
        data: { completion_percentage: 100 }
      });
    }
  };

  const handleLike = (video: VideoRecommendation) => {
    onVideoInteraction(video.id, { type: 'like' });
  };

  const handleBookmark = (video: VideoRecommendation) => {
    onVideoInteraction(video.id, { type: 'bookmark' });
  };

  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty) {
      case 'beginner':
        return 'bg-green-100 text-green-800';
      case 'intermediate':
        return 'bg-yellow-100 text-yellow-800';
      case 'advanced':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;

    const handleTimeUpdate = () => {
      setCurrentTime(video.currentTime);
      
      // Track progress for completion percentage
      if (selectedVideo && video.duration > 0) {
        const completionPercentage = (video.currentTime / video.duration) * 100;
        if (completionPercentage > 0 && completionPercentage % 25 === 0) { // Track every 25%
          onVideoInteraction(selectedVideo.id, {
            type: 'complete',
            data: { completion_percentage: Math.floor(completionPercentage) }
          });
        }
      }
    };

    const handleLoadedMetadata = () => {
      setDuration(video.duration);
    };

    video.addEventListener('timeupdate', handleTimeUpdate);
    video.addEventListener('loadedmetadata', handleLoadedMetadata);
    video.addEventListener('ended', handleVideoEnd);

    return () => {
      video.removeEventListener('timeupdate', handleTimeUpdate);
      video.removeEventListener('loadedmetadata', handleLoadedMetadata);
      video.removeEventListener('ended', handleVideoEnd);
    };
  }, [selectedVideo]);

  if (recommendations.length === 0) {
    return (
      <Card className="border border-dashed border-gray-300">
        <CardContent className="p-8 text-center">
          <Play className="h-12 w-12 mx-auto text-gray-400 mb-4" />
          <h3 className="text-lg font-medium text-gray-700 mb-2">
            No hay videos disponibles
          </h3>
          <p className="text-gray-500">
            No se encontraron videos relacionados con este tema.
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Video player section */}
      <AnimatePresence>
        {selectedVideo && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
          >
            <Card className="overflow-hidden shadow-lg">
              <div
                ref={playerRef}
                className="relative bg-black aspect-video"
              >
                {/* Video element - placeholder for now since we can't embed actual YouTube */}
                <div className="absolute inset-0 flex items-center justify-center bg-gray-900">
                  <div className="text-center text-white">
                    <Play className="h-16 w-16 mx-auto mb-4 opacity-50" />
                    <h3 className="text-lg font-medium mb-2">{selectedVideo.title}</h3>
                    <p className="text-sm opacity-75">Video player placeholder</p>
                    <a
                      href={selectedVideo.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center space-x-2 mt-4 px-4 py-2 bg-red-600 rounded-lg hover:bg-red-700 transition-colors"
                    >
                      <ExternalLink className="h-4 w-4" />
                      <span>Ver en YouTube</span>
                    </a>
                  </div>
                </div>

                {/* Video controls overlay */}
                <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/80 to-transparent p-4">
                  {/* Progress bar */}
                  <div className="mb-4">
                    <Slider
                      value={[duration > 0 ? (currentTime / duration) * 100 : 0]}
                      onValueChange={handleSeek}
                      className="w-full"
                      max={100}
                      step={1}
                    />
                  </div>

                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-4">
                      {/* Play/Pause */}
                      <Button
                        onClick={handlePlayPause}
                        variant="ghost"
                        size="sm"
                        className="text-white hover:bg-white/20"
                      >
                        {isPlaying ? (
                          <Pause className="h-5 w-5" />
                        ) : (
                          <Play className="h-5 w-5" />
                        )}
                      </Button>

                      {/* Skip buttons */}
                      <Button
                        onClick={() => {/* Skip back 10s */}}
                        variant="ghost"
                        size="sm"
                        className="text-white hover:bg-white/20"
                      >
                        <SkipBack className="h-4 w-4" />
                      </Button>
                      
                      <Button
                        onClick={() => {/* Skip forward 10s */}}
                        variant="ghost"
                        size="sm"
                        className="text-white hover:bg-white/20"
                      >
                        <SkipForward className="h-4 w-4" />
                      </Button>

                      {/* Volume */}
                      <div className="flex items-center space-x-2">
                        <Button
                          onClick={handleMute}
                          variant="ghost"
                          size="sm"
                          className="text-white hover:bg-white/20"
                        >
                          {isMuted ? (
                            <VolumeX className="h-4 w-4" />
                          ) : (
                            <Volume2 className="h-4 w-4" />
                          )}
                        </Button>
                        <div className="w-20">
                          <Slider
                            value={[volume * 100]}
                            onValueChange={handleVolumeChange}
                            max={100}
                            step={1}
                            className="h-1"
                          />
                        </div>
                      </div>

                      {/* Time */}
                      <span className="text-white text-sm">
                        {formatDuration(currentTime)} / {formatDuration(duration)}
                      </span>
                    </div>

                    <div className="flex items-center space-x-2">
                      {/* Settings */}
                      <div className="relative">
                        <Button
                          onClick={() => setShowSettings(!showSettings)}
                          variant="ghost"
                          size="sm"
                          className="text-white hover:bg-white/20"
                        >
                          <Settings className="h-4 w-4" />
                        </Button>

                        <AnimatePresence>
                          {showSettings && (
                            <motion.div
                              initial={{ opacity: 0, y: 10 }}
                              animate={{ opacity: 1, y: 0 }}
                              exit={{ opacity: 0, y: 10 }}
                              className="absolute bottom-full right-0 mb-2 bg-gray-900 rounded-lg p-2 min-w-[120px]"
                            >
                              <div className="text-white text-sm mb-2">Velocidad:</div>
                              {[0.5, 0.75, 1, 1.25, 1.5, 2].map((rate) => (
                                <button
                                  key={rate}
                                  onClick={() => handlePlaybackRateChange(rate)}
                                  className={`block w-full text-left px-2 py-1 text-sm rounded hover:bg-gray-700 ${
                                    playbackRate === rate ? 'bg-gray-700 text-white' : 'text-gray-300'
                                  }`}
                                >
                                  {rate}x
                                </button>
                              ))}
                            </motion.div>
                          )}
                        </AnimatePresence>
                      </div>

                      {/* Fullscreen */}
                      <Button
                        onClick={handleFullscreen}
                        variant="ghost"
                        size="sm"
                        className="text-white hover:bg-white/20"
                      >
                        {isFullscreen ? (
                          <Minimize className="h-4 w-4" />
                        ) : (
                          <Maximize className="h-4 w-4" />
                        )}
                      </Button>
                    </div>
                  </div>
                </div>
              </div>

              {/* Video info */}
              <CardContent className="p-4">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <h3 className="font-semibold text-gray-900 mb-1">
                      {selectedVideo.title}
                    </h3>
                    <div className="flex items-center space-x-4 text-sm text-gray-600 mb-2">
                      <div className="flex items-center space-x-1">
                        <User className="h-4 w-4" />
                        <span>{selectedVideo.channel}</span>
                      </div>
                      <div className="flex items-center space-x-1">
                        <Eye className="h-4 w-4" />
                        <span>{selectedVideo.views} views</span>
                      </div>
                      <div className="flex items-center space-x-1">
                        <Clock className="h-4 w-4" />
                        <span>{selectedVideo.duration}</span>
                      </div>
                    </div>
                    <p className="text-sm text-gray-700 mb-3">
                      {selectedVideo.description}
                    </p>
                    <div className="flex items-center space-x-2">
                      <Badge className={getDifficultyColor(selectedVideo.difficulty)}>
                        {selectedVideo.difficulty}
                      </Badge>
                      <Badge variant="secondary">
                        {selectedVideo.topic}
                      </Badge>
                      <div className="flex items-center space-x-1">
                        <Star className="h-4 w-4 text-yellow-500 fill-current" />
                        <span className="text-sm">{selectedVideo.rating.toFixed(1)}</span>
                      </div>
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-2 ml-4">
                    <Button
                      onClick={() => handleLike(selectedVideo)}
                      variant={selectedVideo.user_interactions?.liked ? "default" : "outline"}
                      size="sm"
                    >
                      <ThumbsUp className="h-4 w-4" />
                    </Button>
                    <Button
                      onClick={() => handleBookmark(selectedVideo)}
                      variant={selectedVideo.user_interactions?.bookmarked ? "default" : "outline"}
                      size="sm"
                    >
                      {selectedVideo.user_interactions?.bookmarked ? (
                        <BookmarkCheck className="h-4 w-4" />
                      ) : (
                        <Bookmark className="h-4 w-4" />
                      )}
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Video recommendations */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Play className="h-5 w-5 text-purple-600" />
            <span>Videos Recomendados - {topic}</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {recommendations.map((video) => (
              <motion.div
                key={video.id}
                whileHover={{ y: -4 }}
                className="bg-white border border-gray-200 rounded-lg overflow-hidden hover:shadow-lg transition-shadow cursor-pointer"
                onClick={() => handleVideoSelect(video)}
              >
                {/* Thumbnail */}
                <div className="relative aspect-video bg-gray-100">
                  {video.thumbnail ? (
                    <img
                      src={video.thumbnail}
                      alt={video.title}
                      className="w-full h-full object-cover"
                    />
                  ) : (
                    <div className="flex items-center justify-center h-full">
                      <Play className="h-8 w-8 text-gray-400" />
                    </div>
                  )}
                  
                  {/* Duration badge */}
                  <div className="absolute bottom-2 right-2 bg-black/80 text-white text-xs px-2 py-1 rounded">
                    {video.duration}
                  </div>
                  
                  {/* Viewed indicator */}
                  {video.user_interactions?.viewed && (
                    <div className="absolute top-2 right-2">
                      <div className="bg-blue-600 text-white text-xs px-2 py-1 rounded flex items-center space-x-1">
                        <Eye className="h-3 w-3" />
                        <span>Vista</span>
                      </div>
                    </div>
                  )}
                  
                  {/* Progress bar for partially watched videos */}
                  {video.user_interactions?.completion_percentage && 
                   video.user_interactions.completion_percentage > 0 && 
                   video.user_interactions.completion_percentage < 100 && (
                    <div className="absolute bottom-0 left-0 right-0">
                      <Progress 
                        value={video.user_interactions.completion_percentage} 
                        className="h-1" 
                      />
                    </div>
                  )}
                </div>

                {/* Video info */}
                <div className="p-3">
                  <h4 className="font-medium text-gray-900 text-sm line-clamp-2 mb-2">
                    {video.title}
                  </h4>
                  
                  <div className="flex items-center text-xs text-gray-600 mb-2">
                    <span>{video.channel}</span>
                    <span className="mx-1">•</span>
                    <span>{video.views} views</span>
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-1">
                      <Badge 
                        className={`${getDifficultyColor(video.difficulty)} text-xs`}
                        variant="secondary"
                      >
                        {video.difficulty}
                      </Badge>
                      <div className="flex items-center space-x-1">
                        <Star className="h-3 w-3 text-yellow-500 fill-current" />
                        <span className="text-xs text-gray-600">
                          {video.rating.toFixed(1)}
                        </span>
                      </div>
                    </div>
                    
                    <div className="flex items-center space-x-1">
                      {video.user_interactions?.liked && (
                        <ThumbsUp className="h-3 w-3 text-blue-600" />
                      )}
                      {video.user_interactions?.bookmarked && (
                        <BookmarkCheck className="h-3 w-3 text-green-600" />
                      )}
                    </div>
                  </div>
                  
                  {/* Relevance indicator */}
                  <div className="mt-2">
                    <div className="flex justify-between items-center text-xs">
                      <span className="text-gray-500">Relevancia</span>
                      <span className="text-gray-600">
                        {(video.relevance_score * 100).toFixed(0)}%
                      </span>
                    </div>
                    <Progress value={video.relevance_score * 100} className="h-1 mt-1" />
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
          
          {/* Load more button */}
          {onRequestMoreVideos && (
            <div className="text-center mt-6">
              <Button
                onClick={onRequestMoreVideos}
                variant="outline"
                className="flex items-center space-x-2"
              >
                <Play className="h-4 w-4" />
                <span>Cargar más videos</span>
              </Button>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}