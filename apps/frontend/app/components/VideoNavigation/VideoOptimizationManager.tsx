'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { 
  Zap,
  Wifi,
  WifiOff,
  Download,
  Upload,
  Clock,
  Eye,
  Settings,
  Activity,
  BarChart3,
  TrendingUp,
  TrendingDown,
  CheckCircle,
  AlertTriangle,
  Info,
  RefreshCw,
  Pause,
  Play,
  SkipForward,
  Loader,
  HardDrive,
  CloudDownload,
  Signal,
  Gauge,
  Target,
  Layers,
  Minimize,
  Maximize
} from 'lucide-react';

interface VideoMetadata {
  video_id: number;
  youtube_id: string;
  title: string;
  duration_seconds: number;
  thumbnail_url?: string;
  quality_levels: {
    quality: '144p' | '240p' | '360p' | '480p' | '720p' | '1080p';
    bitrate: number;
    file_size_mb: number;
    codec: string;
  }[];
  audio_tracks: {
    language: string;
    bitrate: number;
    codec: string;
  }[];
  captions_available: string[];
  estimated_load_time: {
    '144p': number;
    '240p': number;
    '360p': number;
    '480p': number;
    '720p': number;
    '1080p': number;
  };
}

interface NetworkConditions {
  connection_type: '2g' | '3g' | '4g' | '5g' | 'wifi' | 'ethernet' | 'offline';
  downlink_speed: number; // Mbps
  uplink_speed: number; // Mbps
  rtt: number; // ms
  effective_type: 'slow-2g' | '2g' | '3g' | '4g';
  save_data: boolean;
  is_online: boolean;
  stability_score: number; // 0-1
}

interface CacheStatus {
  total_cache_size: number; // MB
  available_space: number; // MB
  cached_videos: {
    video_id: number;
    quality: string;
    cache_time: string;
    size_mb: number;
    hit_count: number;
    last_accessed: string;
  }[];
  cache_hit_rate: number; // 0-1
  preload_queue: {
    video_id: number;
    priority: number;
    progress: number;
    quality: string;
    estimated_time_remaining: number;
  }[];
}

interface LoadingStrategy {
  adaptive_quality: boolean;
  preload_count: number;
  cache_duration: number; // hours
  progressive_loading: boolean;
  bandwidth_throttling: boolean;
  offline_mode: boolean;
  quality_preference: 'auto' | 'low' | 'medium' | 'high' | 'highest';
  preload_trigger_distance: number; // videos ahead
  background_preload: boolean;
  compression_level: 'none' | 'light' | 'medium' | 'aggressive';
}

interface PerformanceMetrics {
  average_load_time: number;
  buffer_health: number; // 0-1
  playback_interruptions: number;
  quality_switches: number;
  data_usage_mb: number;
  cache_efficiency: number;
  user_satisfaction: number; // 0-5
  bandwidth_utilization: number; // 0-1
  cpu_usage: number; // 0-100
  memory_usage: number; // MB
  battery_impact: 'low' | 'medium' | 'high';
}

interface VideoOptimizationManagerProps {
  videos: VideoMetadata[];
  currentVideoIndex: number;
  isPlaying: boolean;
  onQualityChange?: (videoId: number, quality: string) => void;
  onPreloadComplete?: (videoId: number, success: boolean) => void;
  onNetworkChange?: (conditions: NetworkConditions) => void;
  enableOfflineMode?: boolean;
  enableAdaptiveStreaming?: boolean;
  enableAnalytics?: boolean;
  maxCacheSize?: number; // MB
  className?: string;
}

const defaultStrategy: LoadingStrategy = {
  adaptive_quality: true,
  preload_count: 3,
  cache_duration: 24,
  progressive_loading: true,
  bandwidth_throttling: false,
  offline_mode: false,
  quality_preference: 'auto',
  preload_trigger_distance: 2,
  background_preload: true,
  compression_level: 'medium'
};

export default function VideoOptimizationManager({
  videos,
  currentVideoIndex,
  isPlaying,
  onQualityChange,
  onPreloadComplete,
  onNetworkChange,
  enableOfflineMode = true,
  enableAdaptiveStreaming = true,
  enableAnalytics = true,
  maxCacheSize = 1000,
  className = ''
}: VideoOptimizationManagerProps) {
  // State management
  const [networkConditions, setNetworkConditions] = useState<NetworkConditions>({
    connection_type: 'wifi',
    downlink_speed: 10,
    uplink_speed: 5,
    rtt: 50,
    effective_type: '4g',
    save_data: false,
    is_online: true,
    stability_score: 0.9
  });
  
  const [cacheStatus, setCacheStatus] = useState<CacheStatus>({
    total_cache_size: 0,
    available_space: maxCacheSize,
    cached_videos: [],
    cache_hit_rate: 0,
    preload_queue: []
  });
  
  const [strategy, setStrategy] = useState<LoadingStrategy>(defaultStrategy);
  const [performanceMetrics, setPerformanceMetrics] = useState<PerformanceMetrics>({
    average_load_time: 0,
    buffer_health: 0,
    playback_interruptions: 0,
    quality_switches: 0,
    data_usage_mb: 0,
    cache_efficiency: 0,
    user_satisfaction: 0,
    bandwidth_utilization: 0,
    cpu_usage: 0,
    memory_usage: 0,
    battery_impact: 'low'
  });
  
  const [isOptimizing, setIsOptimizing] = useState(false);
  const [optimizationProgress, setOptimizationProgress] = useState(0);
  const [showAdvancedSettings, setShowAdvancedSettings] = useState(false);
  const [qualityOverride, setQualityOverride] = useState<string | null>(null);

  // Refs for performance monitoring
  const performanceObserver = useRef<PerformanceObserver | null>(null);
  const networkMonitor = useRef<any>(null);
  const preloadQueue = useRef<Map<number, { promise: Promise<void>; controller: AbortController }>>(new Map());
  const cacheWorker = useRef<Worker | null>(null);

  // Network condition monitoring
  useEffect(() => {
    const updateNetworkInfo = () => {
      const connection = (navigator as any).connection;
      if (connection) {
        const newConditions: NetworkConditions = {
          connection_type: connection.type || 'wifi',
          downlink_speed: connection.downlink || 10,
          uplink_speed: connection.uplink || 5,
          rtt: connection.rtt || 50,
          effective_type: connection.effectiveType || '4g',
          save_data: connection.saveData || false,
          is_online: navigator.onLine,
          stability_score: calculateStabilityScore(connection)
        };
        
        setNetworkConditions(newConditions);
        
        if (onNetworkChange) {
          onNetworkChange(newConditions);
        }
        
        // Adjust strategy based on network conditions
        adjustStrategyForNetwork(newConditions);
      }
    };

    const calculateStabilityScore = (connection: any): number => {
      // Simple heuristic based on connection quality
      const rttScore = Math.max(0, 1 - (connection.rtt || 50) / 500);
      const speedScore = Math.min(1, (connection.downlink || 1) / 10);
      return (rttScore + speedScore) / 2;
    };

    const adjustStrategyForNetwork = (conditions: NetworkConditions) => {
      setStrategy(prevStrategy => {
        const newStrategy = { ...prevStrategy };

        // Adjust based on connection speed
        if (conditions.downlink_speed < 1) {
          newStrategy.quality_preference = 'low';
          newStrategy.preload_count = 1;
          newStrategy.background_preload = false;
          newStrategy.compression_level = 'aggressive';
        } else if (conditions.downlink_speed < 5) {
          newStrategy.quality_preference = 'medium';
          newStrategy.preload_count = 2;
          newStrategy.background_preload = true;
          newStrategy.compression_level = 'medium';
        } else {
          newStrategy.quality_preference = 'auto';
          newStrategy.preload_count = 3;
          newStrategy.background_preload = true;
          newStrategy.compression_level = 'light';
        }

        // Enable data saving mode
        if (conditions.save_data) {
          newStrategy.quality_preference = 'low';
          newStrategy.preload_count = 1;
          newStrategy.bandwidth_throttling = true;
        }

        // Offline mode
        if (!conditions.is_online) {
          newStrategy.offline_mode = true;
        }

        return newStrategy;
      });
    };

    // Set up network monitoring
    updateNetworkInfo();
    
    const connection = (navigator as any).connection;
    if (connection) {
      connection.addEventListener('change', updateNetworkInfo);
    }
    
    window.addEventListener('online', updateNetworkInfo);
    window.addEventListener('offline', updateNetworkInfo);

    // Periodic network quality assessment
    const networkQualityInterval = setInterval(updateNetworkInfo, 30000);

    return () => {
      if (connection) {
        connection.removeEventListener('change', updateNetworkInfo);
      }
      window.removeEventListener('online', updateNetworkInfo);
      window.removeEventListener('offline', updateNetworkInfo);
      clearInterval(networkQualityInterval);
    };
  }, [onNetworkChange]);

  // Performance monitoring
  useEffect(() => {
    if (!enableAnalytics) return;

    const observePerformance = () => {
      if ('PerformanceObserver' in window) {
        performanceObserver.current = new PerformanceObserver((list) => {
          const entries = list.getEntries();
          
          entries.forEach(entry => {
            if (entry.entryType === 'navigation') {
              updatePerformanceMetrics('load_time', entry.duration);
            } else if (entry.entryType === 'resource' && entry.name.includes('youtube')) {
              updatePerformanceMetrics('resource_load', entry.duration);
            }
          });
        });

        performanceObserver.current.observe({ entryTypes: ['navigation', 'resource', 'measure'] });
      }

      // Memory and CPU monitoring
      if ('memory' in performance) {
        const memoryInfo = (performance as any).memory;
        setPerformanceMetrics(prev => ({
          ...prev,
          memory_usage: memoryInfo.usedJSHeapSize / (1024 * 1024) // Convert to MB
        }));
      }
    };

    const updatePerformanceMetrics = (type: string, value: number) => {
      setPerformanceMetrics(prev => {
        const updated = { ...prev };
        
        switch (type) {
          case 'load_time':
            updated.average_load_time = (updated.average_load_time + value) / 2;
            break;
          case 'resource_load':
            updated.data_usage_mb += 0.1; // Estimate
            break;
          default:
            break;
        }
        
        return updated;
      });
    };

    observePerformance();

    return () => {
      if (performanceObserver.current) {
        performanceObserver.current.disconnect();
      }
    };
  }, [enableAnalytics]);

  // Video preloading system
  const preloadVideo = useCallback(async (videoIndex: number, quality?: string): Promise<void> => {
    if (videoIndex < 0 || videoIndex >= videos.length) return;
    
    const video = videos[videoIndex];
    const videoQuality = quality || getOptimalQuality(video);
    
    // Check if already preloaded
    const existingPreload = preloadQueue.current.get(video.video_id);
    if (existingPreload) {
      return existingPreload.promise;
    }

    const controller = new AbortController();
    
    const preloadPromise = new Promise<void>(async (resolve, reject) => {
      try {
        // Add to preload queue
        setCacheStatus(prev => ({
          ...prev,
          preload_queue: [
            ...prev.preload_queue,
            {
              video_id: video.video_id,
              priority: calculatePreloadPriority(videoIndex),
              progress: 0,
              quality: videoQuality,
              estimated_time_remaining: video.estimated_load_time[videoQuality as keyof typeof video.estimated_load_time] || 5000
            }
          ]
        }));

        // Simulate preloading (in real implementation, this would load video data)
        const preloadUrl = `${video.thumbnail_url}`;
        const response = await fetch(preloadUrl, { 
          signal: controller.signal,
          headers: {
            'Cache-Control': 'max-age=3600',
            'Priority': videoIndex === currentVideoIndex + 1 ? 'high' : 'low'
          }
        });

        if (response.ok) {
          // Update cache status
          setCacheStatus(prev => ({
            ...prev,
            cached_videos: [
              ...prev.cached_videos,
              {
                video_id: video.video_id,
                quality: videoQuality,
                cache_time: new Date().toISOString(),
                size_mb: video.quality_levels.find(q => q.quality === videoQuality)?.file_size_mb || 10,
                hit_count: 0,
                last_accessed: new Date().toISOString()
              }
            ],
            preload_queue: prev.preload_queue.filter(item => item.video_id !== video.video_id)
          }));

          if (onPreloadComplete) {
            onPreloadComplete(video.video_id, true);
          }

          resolve();
        } else {
          throw new Error('Failed to preload video');
        }
      } catch (error) {
        if (!controller.signal.aborted) {
          console.error('Preload failed:', error);
          
          // Remove from queue
          setCacheStatus(prev => ({
            ...prev,
            preload_queue: prev.preload_queue.filter(item => item.video_id !== video.video_id)
          }));

          if (onPreloadComplete) {
            onPreloadComplete(video.video_id, false);
          }
        }
        reject(error);
      }
    });

    preloadQueue.current.set(video.video_id, { promise: preloadPromise, controller });
    return preloadPromise;
  }, [videos, currentVideoIndex, onPreloadComplete]);

  const calculatePreloadPriority = (videoIndex: number): number => {
    const distance = Math.abs(videoIndex - currentVideoIndex);
    if (distance === 0) return 100; // Current video
    if (distance === 1) return 90;  // Next/previous video
    if (distance === 2) return 70;  // 2 videos away
    return Math.max(10, 50 - distance * 10); // Further videos
  };

  const getOptimalQuality = (video: VideoMetadata): string => {
    if (qualityOverride) return qualityOverride;

    const { downlink_speed, save_data } = networkConditions;
    
    if (save_data || downlink_speed < 1) return '240p';
    if (downlink_speed < 2) return '360p';
    if (downlink_speed < 5) return '480p';
    if (downlink_speed < 10) return '720p';
    return '1080p';
  };

  // Intelligent preloading based on current position
  useEffect(() => {
    if (!strategy.background_preload || !isPlaying) return;

    const preloadVideos = async () => {
      const indicesToPreload = [];
      
      // Preload next videos
      for (let i = 1; i <= strategy.preload_count; i++) {
        const nextIndex = currentVideoIndex + i;
        if (nextIndex < videos.length) {
          indicesToPreload.push(nextIndex);
        }
      }
      
      // Preload previous video for smooth navigation
      if (currentVideoIndex > 0) {
        indicesToPreload.push(currentVideoIndex - 1);
      }

      // Execute preloading with priority
      for (const index of indicesToPreload) {
        try {
          await preloadVideo(index);
        } catch (error) {
          console.error(`Failed to preload video at index ${index}:`, error);
        }
      }
    };

    const preloadDelay = setTimeout(preloadVideos, 1000);
    return () => clearTimeout(preloadDelay);
  }, [currentVideoIndex, isPlaying, strategy.background_preload, strategy.preload_count, videos.length, preloadVideo]);

  // Cache management
  const clearCache = useCallback(async () => {
    try {
      // Cancel all ongoing preloads
      preloadQueue.current.forEach(({ controller }) => {
        controller.abort();
      });
      preloadQueue.current.clear();

      // Clear cache status
      setCacheStatus({
        total_cache_size: 0,
        available_space: maxCacheSize,
        cached_videos: [],
        cache_hit_rate: 0,
        preload_queue: []
      });

      // Clear browser caches
      if ('caches' in window) {
        const cacheNames = await caches.keys();
        await Promise.all(
          cacheNames.filter(name => name.includes('video')).map(name => caches.delete(name))
        );
      }
    } catch (error) {
      console.error('Failed to clear cache:', error);
    }
  }, [maxCacheSize]);

  const optimizeCacheSize = useCallback(() => {
    setCacheStatus(prev => {
      const sortedVideos = [...prev.cached_videos].sort((a, b) => 
        new Date(a.last_accessed).getTime() - new Date(b.last_accessed).getTime()
      );

      let totalSize = prev.total_cache_size;
      const videosToKeep = [];

      // Keep videos that fit within cache limit, prioritizing recently accessed
      for (let i = sortedVideos.length - 1; i >= 0; i--) {
        const video = sortedVideos[i];
        if (totalSize - video.size_mb >= 0) {
          videosToKeep.unshift(video);
          totalSize -= video.size_mb;
        }
      }

      return {
        ...prev,
        cached_videos: videosToKeep,
        total_cache_size: videosToKeep.reduce((sum, video) => sum + video.size_mb, 0),
        available_space: maxCacheSize - videosToKeep.reduce((sum, video) => sum + video.size_mb, 0)
      };
    });
  }, [maxCacheSize]);

  // Automatic optimization
  const runOptimization = useCallback(async () => {
    setIsOptimizing(true);
    setOptimizationProgress(0);

    try {
      // Step 1: Analyze current performance
      setOptimizationProgress(20);
      await new Promise(resolve => setTimeout(resolve, 500));

      // Step 2: Optimize cache
      setOptimizationProgress(40);
      optimizeCacheSize();
      await new Promise(resolve => setTimeout(resolve, 500));

      // Step 3: Adjust quality settings
      setOptimizationProgress(60);
      if (enableAdaptiveStreaming && networkConditions.downlink_speed < 2) {
        setQualityOverride('360p');
      }
      await new Promise(resolve => setTimeout(resolve, 500));

      // Step 4: Preload critical videos
      setOptimizationProgress(80);
      if (currentVideoIndex + 1 < videos.length) {
        await preloadVideo(currentVideoIndex + 1);
      }
      await new Promise(resolve => setTimeout(resolve, 500));

      // Step 5: Complete
      setOptimizationProgress(100);
      await new Promise(resolve => setTimeout(resolve, 500));

    } finally {
      setIsOptimizing(false);
      setOptimizationProgress(0);
    }
  }, [optimizeCacheSize, enableAdaptiveStreaming, networkConditions.downlink_speed, currentVideoIndex, videos.length, preloadVideo]);

  const formatBytes = (bytes: number): string => {
    const mb = bytes / (1024 * 1024);
    return `${mb.toFixed(1)} MB`;
  };

  const getConnectionIcon = () => {
    if (!networkConditions.is_online) return <WifiOff className="w-4 h-4 text-red-500" />;
    if (networkConditions.downlink_speed < 1) return <Signal className="w-4 h-4 text-red-500" />;
    if (networkConditions.downlink_speed < 5) return <Signal className="w-4 h-4 text-yellow-500" />;
    return <Wifi className="w-4 h-4 text-green-500" />;
  };

  const getPerformanceColor = (value: number, reverse = false): string => {
    if (reverse) {
      if (value > 0.8) return 'text-red-500';
      if (value > 0.5) return 'text-yellow-500';
      return 'text-green-500';
    } else {
      if (value > 0.8) return 'text-green-500';
      if (value > 0.5) return 'text-yellow-500';
      return 'text-red-500';
    }
  };

  return (
    <div className={`w-full space-y-4 ${className}`}>
      {/* Network Status and Quick Actions */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <Zap className="w-5 h-5" />
              Optimización de Video
            </CardTitle>
            
            <div className="flex items-center gap-2">
              <Badge variant="outline" className="flex items-center gap-1">
                {getConnectionIcon()}
                {networkConditions.connection_type.toUpperCase()}
                <span className="text-xs">
                  {networkConditions.downlink_speed.toFixed(1)} Mbps
                </span>
              </Badge>
              
              <Button
                variant="outline"
                size="sm"
                onClick={runOptimization}
                disabled={isOptimizing}
              >
                {isOptimizing ? (
                  <>
                    <Loader className="w-4 h-4 mr-1 animate-spin" />
                    Optimizando...
                  </>
                ) : (
                  <>
                    <Gauge className="w-4 h-4 mr-1" />
                    Optimizar
                  </>
                )}
              </Button>
            </div>
          </div>
        </CardHeader>
        
        <CardContent>
          {/* Optimization Progress */}
          {isOptimizing && (
            <div className="mb-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium">Optimizando sistema...</span>
                <span className="text-sm text-gray-600">{optimizationProgress}%</span>
              </div>
              <Progress value={optimizationProgress} className="h-2" />
            </div>
          )}

          {/* Key Metrics */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
            <div className="text-center">
              <div className="text-lg font-bold flex items-center justify-center gap-1">
                <Clock className="w-4 h-4" />
                {performanceMetrics.average_load_time.toFixed(0)}ms
              </div>
              <div className="text-xs text-gray-600">Tiempo de carga</div>
            </div>
            
            <div className="text-center">
              <div className="text-lg font-bold flex items-center justify-center gap-1">
                <HardDrive className="w-4 h-4" />
                {formatBytes(cacheStatus.total_cache_size * 1024 * 1024)}
              </div>
              <div className="text-xs text-gray-600">Cache usado</div>
            </div>
            
            <div className="text-center">
              <div className={`text-lg font-bold flex items-center justify-center gap-1 ${getPerformanceColor(cacheStatus.cache_hit_rate)}`}>
                <Target className="w-4 h-4" />
                {Math.round(cacheStatus.cache_hit_rate * 100)}%
              </div>
              <div className="text-xs text-gray-600">Cache hit rate</div>
            </div>
            
            <div className="text-center">
              <div className="text-lg font-bold flex items-center justify-center gap-1">
                <CloudDownload className="w-4 h-4" />
                {formatBytes(performanceMetrics.data_usage_mb * 1024 * 1024)}
              </div>
              <div className="text-xs text-gray-600">Datos usados</div>
            </div>
          </div>

          {/* Network Quality Indicator */}
          <div className="bg-gray-50 p-3 rounded-lg mb-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium">Calidad de conexión</span>
              <Badge 
                variant={networkConditions.stability_score > 0.7 ? 'default' : 'secondary'}
                className="text-xs"
              >
                {networkConditions.stability_score > 0.7 ? 'Estable' : 'Inestable'}
              </Badge>
            </div>
            
            <div className="grid grid-cols-3 gap-4 text-xs">
              <div>
                <div className="flex items-center gap-1 mb-1">
                  <Download className="w-3 h-3" />
                  <span>Descarga: {networkConditions.downlink_speed.toFixed(1)} Mbps</span>
                </div>
              </div>
              <div>
                <div className="flex items-center gap-1 mb-1">
                  <Upload className="w-3 h-3" />
                  <span>Subida: {networkConditions.uplink_speed.toFixed(1)} Mbps</span>
                </div>
              </div>
              <div>
                <div className="flex items-center gap-1 mb-1">
                  <Activity className="w-3 h-3" />
                  <span>RTT: {networkConditions.rtt}ms</span>
                </div>
              </div>
            </div>
            
            <Progress 
              value={networkConditions.stability_score * 100} 
              className="h-1 mt-2"
            />
          </div>

          {/* Quality Controls */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium">Calidad de video:</span>
              <select
                value={qualityOverride || 'auto'}
                onChange={(e) => setQualityOverride(e.target.value === 'auto' ? null : e.target.value)}
                className="text-sm border rounded px-2 py-1"
              >
                <option value="auto">Automática</option>
                <option value="240p">240p (Datos limitados)</option>
                <option value="360p">360p (Estándar)</option>
                <option value="480p">480p (Buena)</option>
                <option value="720p">720p (Alta)</option>
                <option value="1080p">1080p (Máxima)</option>
              </select>
            </div>
            
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowAdvancedSettings(!showAdvancedSettings)}
            >
              <Settings className="w-4 h-4 mr-1" />
              {showAdvancedSettings ? 'Ocultar' : 'Mostrar'} opciones
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Advanced Settings */}
      {showAdvancedSettings && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Layers className="w-5 h-5" />
              Configuración Avanzada
            </CardTitle>
          </CardHeader>
          
          <CardContent className="space-y-4">
            {/* Strategy Settings */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-3">
                <h4 className="font-medium">Estrategia de carga</h4>
                
                <div className="flex items-center justify-between">
                  <label className="text-sm">Streaming adaptativo</label>
                  <input
                    type="checkbox"
                    checked={strategy.adaptive_quality}
                    onChange={(e) => setStrategy(prev => ({ ...prev, adaptive_quality: e.target.checked }))}
                  />
                </div>
                
                <div className="flex items-center justify-between">
                  <label className="text-sm">Precarga en segundo plano</label>
                  <input
                    type="checkbox"
                    checked={strategy.background_preload}
                    onChange={(e) => setStrategy(prev => ({ ...prev, background_preload: e.target.checked }))}
                  />
                </div>
                
                <div className="flex items-center justify-between">
                  <label className="text-sm">Carga progresiva</label>
                  <input
                    type="checkbox"
                    checked={strategy.progressive_loading}
                    onChange={(e) => setStrategy(prev => ({ ...prev, progressive_loading: e.target.checked }))}
                  />
                </div>
                
                <div className="space-y-2">
                  <label className="text-sm">Videos a precargar: {strategy.preload_count}</label>
                  <input
                    type="range"
                    min="1"
                    max="5"
                    value={strategy.preload_count}
                    onChange={(e) => setStrategy(prev => ({ ...prev, preload_count: parseInt(e.target.value) }))}
                    className="w-full"
                  />
                </div>
              </div>
              
              <div className="space-y-3">
                <h4 className="font-medium">Optimización</h4>
                
                <div className="space-y-2">
                  <label className="text-sm">Nivel de compresión</label>
                  <select
                    value={strategy.compression_level}
                    onChange={(e) => setStrategy(prev => ({ ...prev, compression_level: e.target.value as LoadingStrategy['compression_level'] }))}
                    className="w-full text-sm border rounded px-2 py-1"
                  >
                    <option value="none">Sin compresión</option>
                    <option value="light">Ligera</option>
                    <option value="medium">Media</option>
                    <option value="aggressive">Agresiva</option>
                  </select>
                </div>
                
                <div className="space-y-2">
                  <label className="text-sm">Duración de cache (horas): {strategy.cache_duration}</label>
                  <input
                    type="range"
                    min="1"
                    max="168"
                    value={strategy.cache_duration}
                    onChange={(e) => setStrategy(prev => ({ ...prev, cache_duration: parseInt(e.target.value) }))}
                    className="w-full"
                  />
                </div>
                
                <div className="flex items-center justify-between">
                  <label className="text-sm">Limitación de ancho de banda</label>
                  <input
                    type="checkbox"
                    checked={strategy.bandwidth_throttling}
                    onChange={(e) => setStrategy(prev => ({ ...prev, bandwidth_throttling: e.target.checked }))}
                  />
                </div>
              </div>
            </div>

            {/* Cache Management */}
            <div className="border-t pt-4">
              <div className="flex items-center justify-between mb-3">
                <h4 className="font-medium">Gestión de cache</h4>
                <div className="flex gap-2">
                  <Button variant="outline" size="sm" onClick={optimizeCacheSize}>
                    <Layers className="w-4 h-4 mr-1" />
                    Optimizar
                  </Button>
                  <Button variant="outline" size="sm" onClick={clearCache}>
                    <RefreshCw className="w-4 h-4 mr-1" />
                    Limpiar
                  </Button>
                </div>
              </div>
              
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span>Espacio usado:</span>
                  <span>{formatBytes(cacheStatus.total_cache_size * 1024 * 1024)} / {formatBytes(maxCacheSize * 1024 * 1024)}</span>
                </div>
                <Progress 
                  value={(cacheStatus.total_cache_size / maxCacheSize) * 100} 
                  className="h-2"
                />
                
                <div className="text-xs text-gray-600">
                  {cacheStatus.cached_videos.length} videos en cache • 
                  {cacheStatus.preload_queue.length} en cola de precarga
                </div>
              </div>
            </div>

            {/* Performance Analytics */}
            {enableAnalytics && (
              <div className="border-t pt-4">
                <h4 className="font-medium mb-3">Análisis de rendimiento</h4>
                
                <div className="grid grid-cols-2 md:grid-cols-3 gap-4 text-sm">
                  <div>
                    <div className="flex items-center justify-between">
                      <span>Salud del buffer:</span>
                      <span className={getPerformanceColor(performanceMetrics.buffer_health)}>
                        {Math.round(performanceMetrics.buffer_health * 100)}%
                      </span>
                    </div>
                    <Progress value={performanceMetrics.buffer_health * 100} className="h-1 mt-1" />
                  </div>
                  
                  <div>
                    <div className="flex items-center justify-between">
                      <span>Eficiencia de cache:</span>
                      <span className={getPerformanceColor(performanceMetrics.cache_efficiency)}>
                        {Math.round(performanceMetrics.cache_efficiency * 100)}%
                      </span>
                    </div>
                    <Progress value={performanceMetrics.cache_efficiency * 100} className="h-1 mt-1" />
                  </div>
                  
                  <div>
                    <div className="flex items-center justify-between">
                      <span>Uso de ancho de banda:</span>
                      <span className={getPerformanceColor(performanceMetrics.bandwidth_utilization, true)}>
                        {Math.round(performanceMetrics.bandwidth_utilization * 100)}%
                      </span>
                    </div>
                    <Progress value={performanceMetrics.bandwidth_utilization * 100} className="h-1 mt-1" />
                  </div>
                  
                  <div className="text-xs text-gray-600">
                    Interrupciones: {performanceMetrics.playback_interruptions}
                  </div>
                  <div className="text-xs text-gray-600">
                    Cambios de calidad: {performanceMetrics.quality_switches}
                  </div>
                  <div className="text-xs text-gray-600">
                    Impacto en batería: {performanceMetrics.battery_impact}
                  </div>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Preload Queue Status */}
      {cacheStatus.preload_queue.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Download className="w-5 h-5" />
              Cola de precarga ({cacheStatus.preload_queue.length})
            </CardTitle>
          </CardHeader>
          
          <CardContent>
            <div className="space-y-3">
              {cacheStatus.preload_queue.map((item) => {
                const video = videos.find(v => v.video_id === item.video_id);
                return (
                  <div key={item.video_id} className="flex items-center gap-3 p-2 border rounded">
                    <div className="flex-1">
                      <div className="font-medium text-sm">{video?.title}</div>
                      <div className="text-xs text-gray-600">
                        Calidad: {item.quality} • Prioridad: {item.priority}
                      </div>
                    </div>
                    
                    <div className="flex items-center gap-2">
                      <Progress value={item.progress} className="w-20 h-2" />
                      <span className="text-xs w-12 text-right">{Math.round(item.progress)}%</span>
                      <span className="text-xs text-gray-600 w-16 text-right">
                        {Math.round(item.estimated_time_remaining / 1000)}s
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Offline Mode Status */}
      {!networkConditions.is_online && enableOfflineMode && (
        <Alert>
          <WifiOff className="h-4 w-4" />
          <AlertDescription>
            Modo offline activo. Reproduciendo desde cache local. 
            {cacheStatus.cached_videos.length} videos disponibles sin conexión.
          </AlertDescription>
        </Alert>
      )}
    </div>
  );
}