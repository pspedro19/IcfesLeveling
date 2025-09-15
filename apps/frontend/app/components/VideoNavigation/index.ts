/**
 * Video Navigation Interface Components
 * 
 * A comprehensive suite of video navigation components designed for educational platforms.
 * Provides smooth navigation interfaces, playlist management, video bookmarking, 
 * progress tracking, and intelligent video recommendations.
 * 
 * Features:
 * - Seamless video carousel with smooth transitions
 * - Advanced playlist management system  
 * - Intelligent video bookmarking and progress tracking
 * - AI-powered recommendation engine with filtering
 * - Video loading optimization and preloading
 * - Unified navigation hub that integrates all components
 * 
 * Usage:
 * import { VideoNavigationHub, VideoPlaylistManager, VideoBookmarkSystem } from '@/components/VideoNavigation';
 * 
 * @author Claude Code Assistant - Agent #22 Video Navigation Interface Creator
 * @version 1.0.0
 */

// Main hub component that integrates all video navigation features
export { default as VideoNavigationHub } from './VideoNavigationHub';

// Individual specialized components
export { default as VideoPlaylistManager } from './VideoPlaylistManager';
export { default as VideoBookmarkSystem } from './VideoBookmarkSystem';
export { default as EnhancedVideoCarousel } from './EnhancedVideoCarousel';
export { default as IntelligentVideoRecommendationEngine } from './IntelligentVideoRecommendationEngine';
export { default as VideoOptimizationManager } from './VideoOptimizationManager';

// Type definitions for external use
export interface VideoItem {
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

export interface VideoNavigationContext {
  subject_id?: number;
  topic_id?: number;
  question_id?: string;
  session_id?: string;
  study_goal?: string;
}

export interface PlaylistItem {
  id: string;
  name: string;
  description?: string;
  videos: VideoItem[];
  created_at: string;
  updated_at: string;
  is_public: boolean;
  total_duration: number;
  completed_videos: number;
  tags: string[];
  subject_focus?: string;
  difficulty_level?: string;
}

export interface VideoBookmark {
  id: string;
  video_id: number;
  youtube_id: string;
  title: string;
  channel: string;
  thumbnail_url?: string;
  url: string;
  duration_seconds?: number;
  bookmark_timestamp: number;
  bookmark_note?: string;
  bookmark_tags: string[];
  bookmark_category: 'learning' | 'review' | 'practice' | 'concept' | 'example' | 'exercise';
  priority_level: 'low' | 'medium' | 'high' | 'urgent';
  created_at: string;
  updated_at: string;
  is_favorite: boolean;
  is_archived: boolean;
}

// Utility functions
export const VideoNavigationUtils = {
  /**
   * Format video duration from seconds to MM:SS or HH:MM:SS format
   */
  formatDuration: (seconds: number): string => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const remainingSeconds = seconds % 60;
    
    if (hours > 0) {
      return `${hours}:${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`;
    }
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
  },

  /**
   * Get optimal video quality based on network conditions
   */
  getOptimalQuality: (networkSpeed: number, saveData: boolean = false): string => {
    if (saveData || networkSpeed < 1) return '240p';
    if (networkSpeed < 2) return '360p';
    if (networkSpeed < 5) return '480p';
    if (networkSpeed < 10) return '720p';
    return '1080p';
  },

  /**
   * Calculate video completion percentage
   */
  calculateCompletion: (watchedSeconds: number, totalSeconds: number): number => {
    if (totalSeconds === 0) return 0;
    return Math.min((watchedSeconds / totalSeconds) * 100, 100);
  },

  /**
   * Generate YouTube thumbnail URL
   */
  getYouTubeThumbnail: (youtubeId: string, quality: 'default' | 'medium' | 'high' | 'max' = 'medium'): string => {
    const qualityMap = {
      default: 'default',
      medium: 'mqdefault', 
      high: 'hqdefault',
      max: 'maxresdefault'
    };
    return `https://img.youtube.com/vi/${youtubeId}/${qualityMap[quality]}.jpg`;
  },

  /**
   * Validate YouTube URL and extract video ID
   */
  extractYouTubeId: (url: string): string | null => {
    const patterns = [
      /(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([^&\n?#]+)/,
      /youtube\.com\/v\/([^&\n?#]+)/
    ];
    
    for (const pattern of patterns) {
      const match = url.match(pattern);
      if (match && match[1]) {
        return match[1];
      }
    }
    return null;
  },

  /**
   * Create embed URL from YouTube video ID
   */
  createEmbedUrl: (youtubeId: string, options: {
    autoplay?: boolean;
    controls?: boolean;
    mute?: boolean;
    start?: number;
  } = {}): string => {
    const params = new URLSearchParams();
    if (options.autoplay) params.set('autoplay', '1');
    if (options.controls === false) params.set('controls', '0');
    if (options.mute) params.set('mute', '1');
    if (options.start) params.set('start', options.start.toString());
    
    const paramString = params.toString();
    return `https://www.youtube.com/embed/${youtubeId}${paramString ? '?' + paramString : ''}`;
  },

  /**
   * Sort videos by different criteria
   */
  sortVideos: (videos: VideoItem[], sortBy: 'relevance' | 'quality' | 'duration' | 'date', order: 'asc' | 'desc' = 'desc'): VideoItem[] => {
    return [...videos].sort((a, b) => {
      let comparison = 0;
      
      switch (sortBy) {
        case 'relevance':
          comparison = a.scores.total_score - b.scores.total_score;
          break;
        case 'quality':
          comparison = a.quality_score - b.quality_score;
          break;
        case 'duration':
          comparison = (a.duration_seconds || 0) - (b.duration_seconds || 0);
          break;
        default:
          comparison = 0;
      }
      
      return order === 'desc' ? -comparison : comparison;
    });
  },

  /**
   * Filter videos by criteria
   */
  filterVideos: (videos: VideoItem[], filters: {
    searchQuery?: string;
    subject?: string;
    minQuality?: number;
    maxDuration?: number;
    confidenceLevel?: string;
  }): VideoItem[] => {
    return videos.filter(video => {
      if (filters.searchQuery) {
        const query = filters.searchQuery.toLowerCase();
        const matchesSearch = 
          video.title.toLowerCase().includes(query) ||
          video.description?.toLowerCase().includes(query) ||
          video.channel?.toLowerCase().includes(query) ||
          video.learning_objectives.some(obj => obj.toLowerCase().includes(query));
        if (!matchesSearch) return false;
      }
      
      if (filters.subject && video.area_evaluada !== filters.subject) {
        return false;
      }
      
      if (filters.minQuality && video.quality_score < filters.minQuality) {
        return false;
      }
      
      if (filters.maxDuration && (video.duration_seconds || 0) > filters.maxDuration) {
        return false;
      }
      
      if (filters.confidenceLevel && video.confidence_level !== filters.confidenceLevel) {
        return false;
      }
      
      return true;
    });
  }
};

// Component configuration presets
export const VideoNavigationPresets = {
  // Minimal carousel for quick video browsing
  minimalCarousel: {
    autoPlay: false,
    showThumbnails: true,
    showProgress: false,
    showQuickActions: false,
    maxVisibleVideos: 3
  },

  // Full-featured carousel with all controls
  fullCarousel: {
    autoPlay: false,
    showThumbnails: true,
    showProgress: true,
    showQuickActions: true,
    maxVisibleVideos: 5,
    keyboardNavigation: true,
    touchGestures: true
  },

  // Optimized for mobile devices
  mobileOptimized: {
    autoPlay: false,
    showThumbnails: true,
    showProgress: true,
    showQuickActions: false,
    maxVisibleVideos: 1,
    touchGestures: true,
    transitionDuration: 300
  },

  // Study-focused configuration
  studyMode: {
    autoPlay: false,
    showThumbnails: false, // Use actual video player
    showProgress: true,
    showQuickActions: true,
    enableBookmarks: true,
    enableProgress: true
  },

  // Presentation mode for teachers
  presentationMode: {
    autoPlay: true,
    autoAdvanceTime: 45000, // 45 seconds
    showThumbnails: true,
    showProgress: false,
    showQuickActions: false,
    loop: true
  }
};

/**
 * Hook for managing video navigation state
 * 
 * @param initialVideos - Initial list of videos
 * @param options - Configuration options
 * @returns Video navigation state and controls
 */
export const useVideoNavigation = (initialVideos: VideoItem[] = [], options: {
  enablePreloading?: boolean;
  enableAnalytics?: boolean;
  maxCacheSize?: number;
} = {}) => {
  // This would be implemented as a React hook
  // For now, returning a simple object structure
  return {
    videos: initialVideos,
    currentIndex: 0,
    isPlaying: false,
    // ... other state and methods would be implemented here
  };
};

export default VideoNavigationHub;