import { apiClient } from '@/lib/axios';

export interface Quest {
  id: string;
  quest_type: 'daily' | 'weekly' | 'monthly' | 'special';
  title: string;
  description: string;
  requirements: {
    type: string;
    target: number;
    subject_id?: string;
    topic_id?: string;
  };
  rewards: {
    experience: number;
    orbs?: number;
    crystals?: number;
    items?: string[];
  };
  is_active: boolean;
  expires_at?: string;
  created_at: string;
}

export interface UserQuest {
  id: string;
  user_id: string;
  quest_id: string;
  progress: number;
  is_completed: boolean;
  claimed_at?: string;
  completed_at?: string;
  created_at: string;
  quest: Quest;
}

export interface QuestProgress {
  quest_id: string;
  progress_increment: number;
}

class QuestsService {
  async getActiveQuests(): Promise<Quest[]> {
    try {
      const response = await apiClient.get<Quest[]>('/quests/active');
      return response;
    } catch (error) {
      console.error('Error fetching active quests:', error);
      throw error;
    }
  }
  
  async getUserQuests(): Promise<UserQuest[]> {
    try {
      const response = await apiClient.get<UserQuest[]>('/quests/user');
      return response;
    } catch (error) {
      console.error('Error fetching user quests:', error);
      throw error;
    }
  }
  
  async getDailyQuests(): Promise<UserQuest[]> {
    try {
      const response = await apiClient.get<UserQuest[]>('/quests/daily');
      return response;
    } catch (error) {
      console.error('Error fetching daily quests:', error);
      throw error;
    }
  }
  
  async updateQuestProgress(data: QuestProgress): Promise<UserQuest> {
    try {
      const response = await apiClient.post<UserQuest>('/quests/progress', data);
      return response;
    } catch (error) {
      console.error('Error updating quest progress:', error);
      throw error;
    }
  }
  
  async claimQuestReward(questId: string): Promise<{ message: string; rewards: any }> {
    try {
      const response = await apiClient.post<{ message: string; rewards: any }>(
        `/quests/${questId}/claim`
      );
      return response;
    } catch (error) {
      console.error('Error claiming quest reward:', error);
      throw error;
    }
  }
  
  async getQuestStreak(): Promise<{ streak_days: number; last_completed: string | null }> {
    try {
      const response = await apiClient.get<{ streak_days: number; last_completed: string | null }>(
        '/quests/streak'
      );
      return response;
    } catch (error) {
      console.error('Error fetching quest streak:', error);
      throw error;
    }
  }
}

export const questsService = new QuestsService();