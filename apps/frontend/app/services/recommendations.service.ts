import { apiClient } from '../lib/axios';

// Interfaces
export interface VideoRecommendation {
  video_id: number;
  title: string;
  description?: string;
  youtube_id: string;
  youtube_url: string;
  duration_seconds?: number;
  channel_name?: string;
  thumbnail_url?: string;
  area_evaluada: string;
  tema_principal: string;
  relevance_score: number;
  context: string;
  reasoning: string;
  learning_objective: string;
  estimated_impact: number;
  difficulty_match: number;
  engagement_prediction: number;
}

export interface StudentProfile {
  user_id: string;
  learning_style: string;
  performance_level: number;
  weak_topics: string[];
  strong_topics: string[];
  preferred_video_duration: number;
  attention_span: number;
  learning_pace: string;
  last_activity: string;
}

export interface VideoAnalytics {
  total_watch_time: number;
  completion_rate: number;
  engagement_score: number;
  replay_count: number;
  skip_rate: number;
  average_session_length: number;
  learning_effectiveness: number;
}

export interface PlaylistRequest {
  learning_goal: string;
  session_duration: number;
  difficulty_progression?: boolean;
  preferred_subjects?: string[];
  max_videos?: number;
}

export interface VideoEventRequest {
  video_id: string;
  event_type: 'play' | 'pause' | 'complete' | 'skip' | 'helpful' | 'not_helpful';
  current_time?: number;
  video_duration?: number;
  session_id: string;
  metadata?: Record<string, any>;
}

export interface RecommendationFilters {
  context?: string;
  limit?: number;
  difficulty_level?: string;
  subject_ids?: number[];
  min_relevance_score?: number;
}

export interface WeaknessBasedRequest {
  weak_topics: string[];
  performance_data?: Record<string, number>;
  learning_style?: string;
  limit?: number;
}

// Cache management
class RecommendationCache {
  private cache = new Map<string, { data: any; timestamp: number; ttl: number }>();
  
  set(key: string, data: any, ttl: number = 5 * 60 * 1000) { // 5 minutes default TTL
    this.cache.set(key, {
      data,
      timestamp: Date.now(),
      ttl
    });
  }
  
  get(key: string) {
    const item = this.cache.get(key);
    if (!item) return null;
    
    const now = Date.now();
    if (now - item.timestamp > item.ttl) {
      this.cache.delete(key);
      return null;
    }
    
    return item.data;
  }
  
  clear() {
    this.cache.clear();
  }
  
  delete(key: string) {
    this.cache.delete(key);
  }
}

const cache = new RecommendationCache();

// Service class
export class RecommendationsService {
  private readonly baseUrl = '/api/v1/intelligent-videos';

  // Student Profile
  async getStudentProfile(): Promise<StudentProfile | null> {
    const cacheKey = 'student-profile';
    const cached = cache.get(cacheKey);
    if (cached) return cached;

    try {
      const response = await apiClient.get<{ data: StudentProfile }>(`${this.baseUrl}/student-profile`);
      const profile = response.data;
      cache.set(cacheKey, profile, 10 * 60 * 1000); // 10 minutes cache
      return profile;
    } catch (error) {
      console.error('Error fetching student profile:', error);
      return null;
    }
  }

  // Video Analytics
  async getVideoAnalytics(): Promise<VideoAnalytics | null> {
    const cacheKey = 'video-analytics';
    const cached = cache.get(cacheKey);
    if (cached) return cached;

    try {
      const response = await apiClient.get<VideoAnalytics>(`${this.baseUrl}/analytics`);
      cache.set(cacheKey, response, 5 * 60 * 1000); // 5 minutes cache
      return response;
    } catch (error) {
      console.error('Error fetching video analytics:', error);
      return null;
    }
  }

  // Contextual Recommendations
  async getContextualRecommendations(filters: RecommendationFilters): Promise<VideoRecommendation[]> {
    const cacheKey = `contextual-${JSON.stringify(filters)}`;
    const cached = cache.get(cacheKey);
    if (cached) return cached;

    try {
      const params = new URLSearchParams();
      if (filters.context) params.append('context', filters.context);
      if (filters.limit) params.append('limit', filters.limit.toString());
      if (filters.difficulty_level) params.append('difficulty_level', filters.difficulty_level);
      if (filters.subject_ids) params.append('subject_ids', filters.subject_ids.join(','));
      if (filters.min_relevance_score) params.append('min_relevance_score', filters.min_relevance_score.toString());

      const response = await apiClient.get<VideoRecommendation[]>(`${this.baseUrl}/recommendations/contextual?${params}`);
      cache.set(cacheKey, response, 3 * 60 * 1000); // 3 minutes cache
      return response;
    } catch (error) {
      console.error('Error fetching contextual recommendations:', error);
      return [];
    }
  }

  // Weakness-based Recommendations
  async getWeaknessBasedRecommendations(request: WeaknessBasedRequest): Promise<VideoRecommendation[]> {
    const cacheKey = `weakness-${JSON.stringify(request)}`;
    const cached = cache.get(cacheKey);
    if (cached) return cached;

    try {
      const response = await apiClient.post<VideoRecommendation[]>(`${this.baseUrl}/recommendations/weakness-based`, request);
      cache.set(cacheKey, response, 3 * 60 * 1000); // 3 minutes cache
      return response;
    } catch (error) {
      console.error('Error fetching weakness-based recommendations:', error);
      return [];
    }
  }

  // Generate Playlist
  async generatePlaylist(request: PlaylistRequest): Promise<VideoRecommendation[]> {
    try {
      const response = await apiClient.post<VideoRecommendation[]>(`${this.baseUrl}/playlist/generate`, request);
      
      // Clear contextual recommendations cache since new playlist might affect recommendations
      const keys = Array.from(cache['cache'].keys()).filter(key => key.startsWith('contextual-'));
      keys.forEach(key => cache.delete(key));
      
      return response;
    } catch (error) {
      console.error('Error generating playlist:', error);
      throw new Error('Failed to generate playlist. Please try again.');
    }
  }

  // Track Video Event
  async trackVideoEvent(request: VideoEventRequest): Promise<boolean> {
    try {
      await apiClient.post(`${this.baseUrl}/events/track`, request);
      
      // Clear analytics cache after tracking events
      cache.delete('video-analytics');
      
      return true;
    } catch (error) {
      console.error('Error tracking video event:', error);
      return false;
    }
  }

  // Advanced Recommendations with Machine Learning
  async getMLRecommendations(options: {
    user_context?: Record<string, any>;
    session_history?: string[];
    learning_objectives?: string[];
    time_constraint?: number;
    difficulty_preference?: 'adaptive' | 'challenging' | 'comfortable';
  }): Promise<VideoRecommendation[]> {
    try {
      const response = await apiClient.post<VideoRecommendation[]>(`${this.baseUrl}/recommendations/ml-enhanced`, options);
      return response;
    } catch (error) {
      console.error('Error fetching ML recommendations:', error);
      return [];
    }
  }

  // Get Popular Videos by Subject
  async getPopularVideosBySubject(subjectId: number, limit: number = 20): Promise<VideoRecommendation[]> {
    const cacheKey = `popular-subject-${subjectId}-${limit}`;
    const cached = cache.get(cacheKey);
    if (cached) return cached;

    try {
      const response = await apiClient.get<VideoRecommendation[]>(`/api/v1/video-recommendations/by-subject/${subjectId}?limit=${limit}`);
      cache.set(cacheKey, response, 10 * 60 * 1000); // 10 minutes cache
      return response;
    } catch (error) {
      console.error('Error fetching popular videos by subject:', error);
      return [];
    }
  }

  // Get Recommendations for Failed Question
  async getRecommendationsForQuestion(questionId: string, limit: number = 10): Promise<VideoRecommendation[]> {
    const cacheKey = `question-${questionId}-${limit}`;
    const cached = cache.get(cacheKey);
    if (cached) return cached;

    try {
      const response = await apiClient.get<VideoRecommendation[]>(`/api/v1/video-recommendations/for-failed-question/${questionId}?limit=${limit}`);
      cache.set(cacheKey, response, 5 * 60 * 1000); // 5 minutes cache
      return response;
    } catch (error) {
      console.error('Error fetching recommendations for question:', error);
      return [];
    }
  }

  // Get Personalized Recommendations
  async getPersonalizedRecommendations(options: {
    subject_id?: number;
    limit?: number;
    include_watched?: boolean;
  } = {}): Promise<VideoRecommendation[]> {
    const cacheKey = `personalized-${JSON.stringify(options)}`;
    const cached = cache.get(cacheKey);
    if (cached) return cached;

    try {
      const params = new URLSearchParams();
      if (options.subject_id) params.append('subject_id', options.subject_id.toString());
      if (options.limit) params.append('limit', options.limit.toString());
      if (options.include_watched !== undefined) params.append('include_watched', options.include_watched.toString());

      const response = await apiClient.get<{ videos: VideoRecommendation[] }>(`/api/v1/video-recommendations/personalized?${params}`);
      const videos = response.videos || [];
      cache.set(cacheKey, videos, 5 * 60 * 1000); // 5 minutes cache
      return videos;
    } catch (error) {
      console.error('Error fetching personalized recommendations:', error);
      return [];
    }
  }

  // Track Video Interaction (for legacy compatibility)
  async trackVideoInteraction(data: {
    video_id: number;
    question_id?: string;
    recommendation_source: string;
    watch_start_time: string;
    action?: string;
  }): Promise<boolean> {
    try {
      await apiClient.post('/api/v1/video-recommendations/track-interaction', data);
      return true;
    } catch (error) {
      console.error('Error tracking video interaction:', error);
      return false;
    }
  }

  // Utility Methods
  clearCache(): void {
    cache.clear();
  }

  clearCacheForKey(keyPattern: string): void {
    const keys = Array.from(cache['cache'].keys()).filter(key => key.includes(keyPattern));
    keys.forEach(key => cache.delete(key));
  }

  // Batch Operations
  async batchTrackEvents(events: VideoEventRequest[]): Promise<boolean> {
    try {
      await apiClient.post(`${this.baseUrl}/events/batch-track`, { events });
      cache.delete('video-analytics'); // Clear analytics cache
      return true;
    } catch (error) {
      console.error('Error batch tracking events:', error);
      return false;
    }
  }

  // Health Check
  async healthCheck(): Promise<boolean> {
    try {
      const response = await apiClient.get(`${this.baseUrl}/health`);
      return response.status === 'healthy';
    } catch (error) {
      console.error('Recommendation service health check failed:', error);
      return false;
    }
  }
}

// Singleton instance
export const recommendationsService = new RecommendationsService();

// Helper functions
export const formatDuration = (seconds: number): string => {
  const minutes = Math.floor(seconds / 60);
  return `${minutes} min`;
};

export const getContextIcon = (context: string): string => {
  const iconMap: Record<string, string> = {
    'weakness_remediation': 'target',
    'skill_building': 'trending-up',
    'study_plan': 'book-open',
    'review': 'check-circle',
    'exploration': 'lightbulb',
  };
  return iconMap[context] || 'play';
};

export const getContextColor = (context: string): string => {
  const colorMap: Record<string, string> = {
    'weakness_remediation': 'bg-red-100 text-red-800',
    'skill_building': 'bg-green-100 text-green-800',
    'study_plan': 'bg-blue-100 text-blue-800',
    'review': 'bg-yellow-100 text-yellow-800',
    'exploration': 'bg-purple-100 text-purple-800',
  };
  return colorMap[context] || 'bg-gray-100 text-gray-800';
};

export const getScoreColor = (score: number): string => {
  if (score >= 0.8) return 'text-green-600';
  if (score >= 0.6) return 'text-yellow-600';
  return 'text-red-600';
};

// Error handling wrapper
export const withErrorHandling = <T extends any[], R>(
  fn: (...args: T) => Promise<R>,
  fallback: R
) => {
  return async (...args: T): Promise<R> => {
    try {
      return await fn(...args);
    } catch (error) {
      console.error('Service method failed:', error);
      return fallback;
    }
  };
};