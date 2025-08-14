import axios from 'axios';
import { trackGameEvent } from '@/lib/analytics';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:4000';

export interface EventData {
  eventType: string;
  eventData: Record<string, any>;
  sessionId?: string;
  platform?: string;
}

export interface BatchEventData {
  events: EventData[];
}

export interface BattleAnalytics {
  battleId: string;
  battleType: string;
  enemyName: string;
  enemyLevel: number;
  questionsAnswered: number;
  correctAnswers: number;
  totalDamageDealt: number;
  totalDamageReceived: number;
  experienceGained: number;
  orbsGained: number;
  durationSeconds: number;
  status: 'completed' | 'abandoned';
  questionPerformance?: QuestionPerformance[];
}

export interface QuestionPerformance {
  questionId: string;
  subjectId: string;
  topicId: string;
  difficulty: number;
  userAnswer: string;
  correctAnswer: string;
  isCorrect: boolean;
  responseTimeMs: number;
  damageDealt?: number;
  damageReceived?: number;
  criticalHit?: boolean;
}

export type AnalyticsPeriod = 'week' | 'month' | 'quarter' | 'year';

export interface UserAnalytics {
  battleStats: {
    totalBattles: number;
    totalQuestions: number;
    totalCorrect: number;
    accuracy: number;
    avgDuration: number;
    totalExperience: number;
    totalOrbs: number;
  };
  topicPerformance: {
    topicId: string;
    questionsCount: number;
    correctCount: number;
    accuracy: number;
    avgResponseTime: number;
  }[];
  dailyActivity: {
    date: string;
    battlesCount: number;
    accuracy: number;
  }[];
  progression: {
    recordedAt: string;
    level: number;
    experience: number;
    rank: string;
    streakDays: number;
  }[];
}

export interface GlobalAnalytics {
  overallStats: {
    uniqueUsers: number;
    totalEvents: number;
    totalSessions: number;
  };
  eventDistribution: {
    eventType: string;
    count: number;
  }[];
  topPlayers: {
    userId: string;
    totalExperience: number;
    battlesCount: number;
    accuracy: number;
  }[];
  popularBattles: {
    battleType: string;
    count: number;
    avgQuestions: number;
    avgAccuracy: number;
  }[];
  dailyMetrics: {
    date: string;
    activeUsers: number;
    totalBattles: number;
    totalQuestions: number;
    correctAnswers: number;
    totalExperience: number;
    accuracy: number;
  }[];
}

class ClickHouseService {
  private getAuthHeaders() {
    const token = localStorage.getItem('token');
    return {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json'
    };
  }

  // Track single event
  async trackEvent(eventData: EventData): Promise<void> {
    try {
      await axios.post(
        `${API_URL}/api/v1/analytics/track`,
        eventData,
        { headers: this.getAuthHeaders() }
      );
      
      // Also track in Google Analytics
      trackGameEvent(eventData.eventType, eventData.eventData);
    } catch (error) {
      console.error('Error tracking event:', error);
    }
  }

  // Track batch events
  async trackBatchEvents(batchData: BatchEventData): Promise<void> {
    try {
      await axios.post(
        `${API_URL}/api/v1/analytics/track/batch`,
        batchData,
        { headers: this.getAuthHeaders() }
      );
    } catch (error) {
      console.error('Error tracking batch events:', error);
    }
  }

  // Track battle completion
  async trackBattleCompletion(battleData: BattleAnalytics): Promise<void> {
    try {
      await axios.post(
        `${API_URL}/api/v1/analytics/battle/complete`,
        battleData,
        { headers: this.getAuthHeaders() }
      );
    } catch (error) {
      console.error('Error tracking battle completion:', error);
    }
  }

  // Update user progression
  async updateUserProgression(): Promise<void> {
    try {
      await axios.post(
        `${API_URL}/api/v1/analytics/user/progression`,
        {},
        { headers: this.getAuthHeaders() }
      );
    } catch (error) {
      console.error('Error updating user progression:', error);
    }
  }

  // Get current user analytics
  async getUserAnalytics(period: AnalyticsPeriod = 'month'): Promise<UserAnalytics> {
    try {
      const response = await axios.get(
        `${API_URL}/api/v1/analytics/user/me`,
        {
          params: { period },
          headers: this.getAuthHeaders()
        }
      );
      return response.data;
    } catch (error) {
      console.error('Error getting user analytics:', error);
      throw error;
    }
  }

  // Get specific user analytics (admin only)
  async getUserAnalyticsById(
    userId: string,
    period: AnalyticsPeriod = 'month'
  ): Promise<UserAnalytics> {
    try {
      const response = await axios.get(
        `${API_URL}/api/v1/analytics/user/${userId}`,
        {
          params: { period },
          headers: this.getAuthHeaders()
        }
      );
      return response.data;
    } catch (error) {
      console.error('Error getting user analytics:', error);
      throw error;
    }
  }

  // Get global analytics (admin only)
  async getGlobalAnalytics(period: AnalyticsPeriod = 'week'): Promise<GlobalAnalytics> {
    try {
      const response = await axios.get(
        `${API_URL}/api/v1/analytics/global`,
        {
          params: { period },
          headers: this.getAuthHeaders()
        }
      );
      return response.data;
    } catch (error) {
      console.error('Error getting global analytics:', error);
      throw error;
    }
  }

  // Get real-time active users
  async getActiveUsers(): Promise<{ activeUsers: number; timestamp: string }> {
    try {
      const response = await axios.get(
        `${API_URL}/api/v1/analytics/realtime/active-users`,
        { headers: this.getAuthHeaders() }
      );
      return response.data;
    } catch (error) {
      console.error('Error getting active users:', error);
      throw error;
    }
  }

  // Get events stream (admin only)
  async getEventsStream(): Promise<any[]> {
    try {
      const response = await axios.get(
        `${API_URL}/api/v1/analytics/realtime/events-stream`,
        { headers: this.getAuthHeaders() }
      );
      return response.data.events;
    } catch (error) {
      console.error('Error getting events stream:', error);
      throw error;
    }
  }

  // Generate daily report (admin only)
  async generateDailyReport(): Promise<any> {
    try {
      const response = await axios.post(
        `${API_URL}/api/v1/analytics/report/daily`,
        {},
        { headers: this.getAuthHeaders() }
      );
      return response.data;
    } catch (error) {
      console.error('Error generating daily report:', error);
      throw error;
    }
  }

  // Helper method to track page views
  async trackPageView(page: string, properties?: Record<string, any>): Promise<void> {
    await this.trackEvent({
      eventType: 'page_view',
      eventData: {
        page,
        ...properties
      }
    });
  }

  // Helper method to track user actions
  async trackAction(
    action: string,
    category: string,
    properties?: Record<string, any>
  ): Promise<void> {
    await this.trackEvent({
      eventType: 'user_action',
      eventData: {
        action,
        category,
        ...properties
      }
    });
  }

  // Helper method to track errors
  async trackError(
    error: string,
    context: string,
    properties?: Record<string, any>
  ): Promise<void> {
    await this.trackEvent({
      eventType: 'error',
      eventData: {
        error,
        context,
        ...properties
      }
    });
  }
}

export const clickhouseService = new ClickHouseService();