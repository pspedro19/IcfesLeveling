'use client';

import { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  PlayCircle,
  List,
  Bookmark,
  Brain,
  Zap,
  Settings,
  Eye,
  Star,
  TrendingUp,
  Target,
  Users,
  Layers,
  Activity,
  BarChart3,
  Compass,
  Sparkles,
  Navigation,
  Grid3X3,
  Filter,
  RefreshCw,
  AlertTriangle,
  CheckCircle,
  Info
} from 'lucide-react';

// Import our custom components
import VideoPlaylistManager from './VideoPlaylistManager';
import VideoBookmarkSystem from './VideoBookmarkSystem';
import EnhancedVideoCarousel from './EnhancedVideoCarousel';
import IntelligentVideoRecommendationEngine from './IntelligentVideoRecommendationEngine';
import VideoOptimizationManager from './VideoOptimizationManager';

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
  topic_id?: number;
  area_evaluada?: string;
  tema_principal?: string;
  nivel?: string;
  recommendation_type: string;
  confidence_level: string;
  scores: {
    total_score: number;
    semantic_similarity?: number;
    difficulty_match?: number;
    exact_match?: number;
    popularity?: number;
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

interface VideoNavigationHubProps {
  userId: string;
  initialVideos?: VideoItem[];
  currentContext?: {
    subject_id?: number;
    topic_id?: number;
    question_id?: string;
    session_id?: string;
    study_goal?: string;
  };
  onVideoSelect?: (video: VideoItem) => void;
  onVideoPlay?: (video: VideoItem) => void;
  onPlaylistChange?: (playlist: any) => void;
  enableAIRecommendations?: boolean;
  enableBookmarks?: boolean;
  enablePlaylists?: boolean;
  enableOptimization?: boolean;
  enableAnalytics?: boolean;
  className?: string;
}

interface HubStats {
  total_videos: number;
  total_playlists: number;
  total_bookmarks: number;
  watch_time_minutes: number;
  completion_rate: number;
  avg_rating: number;
  data_saved_mb: number;
  cache_efficiency: number;
}

export default function VideoNavigationHub({
  userId,
  initialVideos = [],
  currentContext,
  onVideoSelect,
  onVideoPlay,
  onPlaylistChange,
  enableAIRecommendations = true,
  enableBookmarks = true,
  enablePlaylists = true,
  enableOptimization = true,
  enableAnalytics = true,
  className = ''
}: VideoNavigationHubProps) {
  // Main state
  const [activeTab, setActiveTab] = useState<'carousel' | 'recommendations' | 'playlists' | 'bookmarks' | 'optimization'>('carousel');
  const [videos, setVideos] = useState<VideoItem[]>(initialVideos);
  const [currentVideoIndex, setCurrentVideoIndex] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Hub statistics
  const [hubStats, setHubStats] = useState<HubStats>({
    total_videos: 0,
    total_playlists: 0,
    total_bookmarks: 0,
    watch_time_minutes: 0,
    completion_rate: 0,
    avg_rating: 0,
    data_saved_mb: 0,
    cache_efficiency: 0
  });

  // Settings and preferences
  const [hubSettings, setHubSettings] = useState({
    auto_switch_tabs: false,
    smart_preloading: true,
    unified_search: true,
    cross_component_sync: true,
    advanced_analytics: enableAnalytics,
    background_optimization: enableOptimization
  });

  const [viewMode, setViewMode] = useState<'unified' | 'tabbed' | 'dashboard'>('unified');
  const [showQuickActions, setShowQuickActions] = useState(true);
  const [showStats, setShowStats] = useState(true);

  // Load hub statistics
  const loadHubStats = useCallback(async () => {
    try {
      const response = await fetch(`/api/v1/video-hub/stats/${userId}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setHubStats(data.stats || {});
      }
    } catch (err) {
      console.error('Error loading hub stats:', err);
    }
  }, [userId]);

  // Initialize hub
  useEffect(() => {
    if (enableAnalytics) {
      loadHubStats();
    }
  }, [loadHubStats, enableAnalytics]);

  // Sync videos across components
  const handleVideoUpdate = useCallback((updatedVideo: VideoItem) => {
    setVideos(prev => prev.map(video => 
      video.video_id === updatedVideo.video_id ? { ...video, ...updatedVideo } : video
    ));
  }, []);

  // Handle video selection with cross-component sync
  const handleVideoSelect = useCallback((video: VideoItem, source?: string) => {
    // Update current video index
    const newIndex = videos.findIndex(v => v.video_id === video.video_id);
    if (newIndex !== -1) {
      setCurrentVideoIndex(newIndex);
    }

    // Sync across components if enabled
    if (hubSettings.cross_component_sync) {
      handleVideoUpdate(video);
    }

    // Track interaction
    trackVideoInteraction(video.video_id, 'select', source);

    // Call parent handler
    if (onVideoSelect) {
      onVideoSelect(video);
    }
  }, [videos, hubSettings.cross_component_sync, onVideoSelect, handleVideoUpdate]);

  // Handle video play
  const handleVideoPlay = useCallback((video: VideoItem) => {
    setIsPlaying(true);
    trackVideoInteraction(video.video_id, 'play');

    if (onVideoPlay) {
      onVideoPlay(video);
    }
  }, [onVideoPlay]);

  // Handle bookmark actions
  const handleBookmark = useCallback(async (video: VideoItem) => {
    try {
      const response = await fetch('/api/v1/bookmarks', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          video_id: video.video_id,
          user_id: userId,
          context: currentContext
        })
      });

      if (response.ok) {
        handleVideoUpdate({ ...video, is_bookmarked: true });
        
        // Update stats
        setHubStats(prev => ({
          ...prev,
          total_bookmarks: prev.total_bookmarks + 1
        }));
      }
    } catch (err) {
      console.error('Error bookmarking video:', err);
    }
  }, [userId, currentContext, handleVideoUpdate]);

  // Handle favorite actions
  const handleFavorite = useCallback(async (video: VideoItem) => {
    try {
      const response = await fetch(`/api/v1/videos/${video.video_id}/favorite`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          is_favorite: !video.is_favorite
        })
      });

      if (response.ok) {
        handleVideoUpdate({ ...video, is_favorite: !video.is_favorite });
      }
    } catch (err) {
      console.error('Error updating favorite status:', err);
    }
  }, [handleVideoUpdate]);

  // Handle share actions
  const handleShare = useCallback(async (video: VideoItem) => {
    if (navigator.share) {
      try {
        await navigator.share({
          title: video.title,
          text: `Mira este video educativo: ${video.title}`,
          url: video.url
        });
        
        trackVideoInteraction(video.video_id, 'share', 'native');
      } catch (err) {
        // Fallback to clipboard
        copyToClipboard(video.url);
      }
    } else {
      copyToClipboard(video.url);
    }
  }, []);

  const copyToClipboard = (text: string) => {
    if (navigator.clipboard) {
      navigator.clipboard.writeText(text);
    } else {
      // Fallback for older browsers
      const textArea = document.createElement('textarea');
      textArea.value = text;
      document.body.appendChild(textArea);
      textArea.select();
      document.execCommand('copy');
      document.body.removeChild(textArea);
    }
    
    // Show success message (implement toast notification)
  };

  // Track video interactions for analytics
  const trackVideoInteraction = async (videoId: number, action: string, source?: string) => {
    if (!enableAnalytics) return;

    try {
      await fetch('/api/v1/video-hub/track-interaction', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          video_id: videoId,
          user_id: userId,
          action,
          source,
          context: currentContext,
          timestamp: new Date().toISOString()
        })
      });
    } catch (err) {
      console.error('Error tracking interaction:', err);
    }
  };

  // Auto-switch tabs based on user behavior
  useEffect(() => {
    if (!hubSettings.auto_switch_tabs) return;

    // Smart tab switching logic
    const switchTab = () => {
      if (videos.length === 0 && enableAIRecommendations) {
        setActiveTab('recommendations');
      } else if (videos.length > 0) {
        setActiveTab('carousel');
      }
    };

    const switchDelay = setTimeout(switchTab, 2000);
    return () => clearTimeout(switchDelay);
  }, [videos.length, enableAIRecommendations, hubSettings.auto_switch_tabs]);

  // Format statistics for display
  const formatWatchTime = (minutes: number): string => {
    const hours = Math.floor(minutes / 60);
    const remainingMinutes = minutes % 60;
    if (hours > 0) {
      return `${hours}h ${remainingMinutes}m`;
    }
    return `${remainingMinutes}m`;
  };

  const formatBytes = (bytes: number): string => {
    return `${bytes.toFixed(1)} MB`;
  };

  // Convert videos to required formats for different components
  const convertVideoForOptimization = (video: VideoItem) => ({
    video_id: video.video_id,
    youtube_id: video.youtube_id,
    title: video.title,
    duration_seconds: video.duration_seconds || 0,
    thumbnail_url: video.thumbnail_url,
    quality_levels: [
      { quality: '720p' as const, bitrate: 2500, file_size_mb: 50, codec: 'h264' },
      { quality: '480p' as const, bitrate: 1000, file_size_mb: 25, codec: 'h264' },
      { quality: '360p' as const, bitrate: 500, file_size_mb: 15, codec: 'h264' }
    ],
    audio_tracks: [{ language: 'es', bitrate: 128, codec: 'aac' }],
    captions_available: ['es'],
    estimated_load_time: {
      '144p': 1000,
      '240p': 1500,
      '360p': 2000,
      '480p': 3000,
      '720p': 5000,
      '1080p': 8000
    }
  });

  const renderQuickStats = () => (
    <Card className="mb-4">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-lg">
          <Activity className="w-5 h-5" />
          Resumen de Navegación
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-600">{hubStats.total_videos}</div>
            <div className="text-xs text-gray-600">Videos disponibles</div>
          </div>
          
          <div className="text-center">
            <div className="text-2xl font-bold text-green-600">{formatWatchTime(hubStats.watch_time_minutes)}</div>
            <div className="text-xs text-gray-600">Tiempo de estudio</div>
          </div>
          
          <div className="text-center">
            <div className="text-2xl font-bold text-purple-600">{hubStats.total_bookmarks}</div>
            <div className="text-xs text-gray-600">Marcadores guardados</div>
          </div>
          
          <div className="text-center">
            <div className="text-2xl font-bold text-orange-600">{Math.round(hubStats.completion_rate * 100)}%</div>
            <div className="text-xs text-gray-600">Tasa de finalización</div>
          </div>
        </div>
        
        {enableOptimization && (
          <div className="grid grid-cols-2 gap-4 mt-4 pt-4 border-t">
            <div className="flex items-center justify-between text-sm">
              <span>Datos ahorrados:</span>
              <Badge variant="secondary">{formatBytes(hubStats.data_saved_mb)}</Badge>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span>Eficiencia de cache:</span>
              <Badge variant="secondary">{Math.round(hubStats.cache_efficiency * 100)}%</Badge>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );

  const renderQuickActions = () => (
    <Card className="mb-4">
      <CardContent className="p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Button
              variant={viewMode === 'unified' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setViewMode('unified')}
            >
              <Layers className="w-4 h-4 mr-1" />
              Unificado
            </Button>
            
            <Button
              variant={viewMode === 'tabbed' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setViewMode('tabbed')}
            >
              <Grid3X3 className="w-4 h-4 mr-1" />
              Por pestañas
            </Button>
            
            <Button
              variant={viewMode === 'dashboard' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setViewMode('dashboard')}
            >
              <BarChart3 className="w-4 h-4 mr-1" />
              Dashboard
            </Button>
          </div>
          
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowStats(!showStats)}
            >
              <Eye className="w-4 h-4 mr-1" />
              {showStats ? 'Ocultar' : 'Mostrar'} estadísticas
            </Button>
            
            <Button
              variant="outline"
              size="sm"
              onClick={loadHubStats}
            >
              <RefreshCw className="w-4 h-4" />
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );

  // Render unified view - all components in one page
  const renderUnifiedView = () => (
    <div className="space-y-6">
      {videos.length > 0 && (
        <EnhancedVideoCarousel
          videos={videos}
          initialIndex={currentVideoIndex}
          onVideoSelect={handleVideoSelect}
          onVideoPlay={handleVideoPlay}
          onBookmark={handleBookmark}
          onFavorite={handleFavorite}
          onShare={handleShare}
          settings={{
            autoPlay: false,
            showThumbnails: true,
            showProgress: true,
            showQuickActions: true
          }}
        />
      )}

      {enableAIRecommendations && (
        <IntelligentVideoRecommendationEngine
          userId={userId}
          currentContext={currentContext}
          onVideoSelect={handleVideoSelect}
          enableAIInsights={true}
          enableRealTimeUpdates={true}
          enablePersonalization={true}
        />
      )}

      {enablePlaylists && (
        <VideoPlaylistManager
          initialVideos={videos}
          userId={userId}
          onVideoSelect={handleVideoSelect}
          onPlaylistChange={onPlaylistChange}
          autoPlay={false}
          showControls={true}
          allowCreatePlaylist={true}
        />
      )}
    </div>
  );

  // Render tabbed view
  const renderTabbedView = () => (
    <Tabs value={activeTab} onValueChange={(value) => setActiveTab(value as typeof activeTab)}>
      <TabsList className="grid grid-cols-5 w-full mb-6">
        <TabsTrigger value="carousel" className="flex items-center gap-2">
          <PlayCircle className="w-4 h-4" />
          Carousel
        </TabsTrigger>
        
        {enableAIRecommendations && (
          <TabsTrigger value="recommendations" className="flex items-center gap-2">
            <Brain className="w-4 h-4" />
            IA
          </TabsTrigger>
        )}
        
        {enablePlaylists && (
          <TabsTrigger value="playlists" className="flex items-center gap-2">
            <List className="w-4 h-4" />
            Listas
          </TabsTrigger>
        )}
        
        {enableBookmarks && (
          <TabsTrigger value="bookmarks" className="flex items-center gap-2">
            <Bookmark className="w-4 h-4" />
            Marcadores
          </TabsTrigger>
        )}
        
        {enableOptimization && (
          <TabsTrigger value="optimization" className="flex items-center gap-2">
            <Zap className="w-4 h-4" />
            Optimización
          </TabsTrigger>
        )}
      </TabsList>

      <TabsContent value="carousel" className="space-y-4">
        <EnhancedVideoCarousel
          videos={videos}
          initialIndex={currentVideoIndex}
          onVideoSelect={handleVideoSelect}
          onVideoPlay={handleVideoPlay}
          onBookmark={handleBookmark}
          onFavorite={handleFavorite}
          onShare={handleShare}
          settings={{
            autoPlay: false,
            showThumbnails: true,
            showProgress: true,
            showQuickActions: true
          }}
        />
      </TabsContent>

      {enableAIRecommendations && (
        <TabsContent value="recommendations" className="space-y-4">
          <IntelligentVideoRecommendationEngine
            userId={userId}
            currentContext={currentContext}
            onVideoSelect={handleVideoSelect}
            enableAIInsights={true}
            enableRealTimeUpdates={true}
            enablePersonalization={true}
          />
        </TabsContent>
      )}

      {enablePlaylists && (
        <TabsContent value="playlists" className="space-y-4">
          <VideoPlaylistManager
            initialVideos={videos}
            userId={userId}
            onVideoSelect={handleVideoSelect}
            onPlaylistChange={onPlaylistChange}
            autoPlay={false}
            showControls={true}
            allowCreatePlaylist={true}
          />
        </TabsContent>
      )}

      {enableBookmarks && (
        <TabsContent value="bookmarks" className="space-y-4">
          <VideoBookmarkSystem
            userId={userId}
            currentVideo={videos[currentVideoIndex] ? {
              video_id: videos[currentVideoIndex].video_id,
              youtube_id: videos[currentVideoIndex].youtube_id,
              title: videos[currentVideoIndex].title
            } : undefined}
            onBookmarkSelect={handleVideoSelect}
            showAnalytics={enableAnalytics}
            allowSessions={true}
          />
        </TabsContent>
      )}

      {enableOptimization && (
        <TabsContent value="optimization" className="space-y-4">
          <VideoOptimizationManager
            videos={videos.map(convertVideoForOptimization)}
            currentVideoIndex={currentVideoIndex}
            isPlaying={isPlaying}
            enableOfflineMode={true}
            enableAdaptiveStreaming={true}
            enableAnalytics={enableAnalytics}
            maxCacheSize={1000}
          />
        </TabsContent>
      )}
    </Tabs>
  );

  // Render dashboard view
  const renderDashboardView = () => (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      {/* Main content area */}
      <div className="lg:col-span-2 space-y-6">
        {videos.length > 0 && (
          <EnhancedVideoCarousel
            videos={videos}
            initialIndex={currentVideoIndex}
            onVideoSelect={handleVideoSelect}
            onVideoPlay={handleVideoPlay}
            onBookmark={handleBookmark}
            onFavorite={handleFavorite}
            onShare={handleShare}
            settings={{
              autoPlay: false,
              showThumbnails: true,
              showProgress: true,
              showQuickActions: true
            }}
          />
        )}
        
        {enableAIRecommendations && (
          <IntelligentVideoRecommendationEngine
            userId={userId}
            currentContext={currentContext}
            onVideoSelect={handleVideoSelect}
            maxRecommendations={6}
            enableAIInsights={true}
          />
        )}
      </div>

      {/* Sidebar */}
      <div className="space-y-4">
        {showStats && renderQuickStats()}
        
        {enableBookmarks && (
          <VideoBookmarkSystem
            userId={userId}
            currentVideo={videos[currentVideoIndex] ? {
              video_id: videos[currentVideoIndex].video_id,
              youtube_id: videos[currentVideoIndex].youtube_id,
              title: videos[currentVideoIndex].title
            } : undefined}
            onBookmarkSelect={handleVideoSelect}
            showAnalytics={false}
            allowSessions={false}
          />
        )}
      </div>
    </div>
  );

  return (
    <div className={`w-full space-y-4 ${className}`}>
      {error && (
        <Alert>
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Header */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <Navigation className="w-6 h-6" />
              Hub de Navegación de Videos
              <Badge variant="secondary" className="ml-2">
                {videos.length} videos
              </Badge>
            </CardTitle>
            
            <div className="flex items-center gap-2">
              <Badge variant="outline" className="text-xs">
                <Compass className="w-3 h-3 mr-1" />
                Modo {viewMode}
              </Badge>
              
              {loading && (
                <Badge variant="secondary" className="text-xs">
                  <RefreshCw className="w-3 h-3 mr-1 animate-spin" />
                  Cargando...
                </Badge>
              )}
            </div>
          </div>
        </CardHeader>
      </Card>

      {/* Quick Actions */}
      {showQuickActions && renderQuickActions()}

      {/* Quick Stats */}
      {showStats && viewMode !== 'dashboard' && renderQuickStats()}

      {/* Main Content Based on View Mode */}
      {viewMode === 'unified' && renderUnifiedView()}
      {viewMode === 'tabbed' && renderTabbedView()}
      {viewMode === 'dashboard' && renderDashboardView()}

      {/* Status Messages */}
      {videos.length === 0 && !loading && (
        <Card>
          <CardContent className="text-center py-12">
            <PlayCircle className="w-16 h-16 mx-auto text-gray-400 mb-4" />
            <h3 className="text-xl font-semibold mb-2">No hay videos disponibles</h3>
            <p className="text-gray-600 mb-4">
              Comienza explorando nuestras recomendaciones inteligentes o agrega videos a tus listas de reproducción.
            </p>
            {enableAIRecommendations && (
              <Button onClick={() => setActiveTab('recommendations')}>
                <Brain className="w-4 h-4 mr-2" />
                Explorar Recomendaciones IA
              </Button>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}