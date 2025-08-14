import { apiClient } from '@/lib/axios';

export interface Battle {
  id: string;
  user_id: string;
  enemy_name: string;
  enemy_level: number;
  enemy_hp: number;
  enemy_max_hp: number;
  player_hp: number;
  player_max_hp: number;
  status: 'in_progress' | 'victory' | 'defeat';
  questions_answered: number;
  correct_answers: number;
  total_damage_dealt: number;
  total_damage_taken: number;
  experience_gained?: number;
  loot_gained?: Record<string, any>;
  started_at: string;
  completed_at?: string;
}

export interface BattleStartRequest {
  enemy_type?: string;
  difficulty?: number;
  subject_id?: string;
}

export interface BattleAnswerRequest {
  question_id: string;
  user_answer: string;
  time_taken: number;
}

export interface BattleResult {
  is_correct: boolean;
  damage_dealt: number;
  damage_taken: number;
  is_critical: boolean;
  combo_count: number;
  experience_gained: number;
  battle_status: string;
}

class BattlesService {
  async startBattle(data: BattleStartRequest = {}): Promise<Battle> {
    try {
      const response = await apiClient.post<Battle>('/battles/start', data);
      return response;
    } catch (error) {
      console.error('Error starting battle:', error);
      throw error;
    }
  }
  
  async submitAnswer(battleId: string, answer: BattleAnswerRequest): Promise<BattleResult> {
    try {
      const response = await apiClient.post<BattleResult>(
        `/battles/${battleId}/answer`,
        answer
      );
      return response;
    } catch (error) {
      console.error('Error submitting answer:', error);
      throw error;
    }
  }
  
  async getCurrentBattle(): Promise<Battle | null> {
    try {
      const response = await apiClient.get<Battle>('/battles/current');
      return response;
    } catch (error: any) {
      if (error.response?.status === 404) {
        return null; // No battle in progress
      }
      console.error('Error fetching current battle:', error);
      throw error;
    }
  }
  
  async forfeitBattle(battleId: string): Promise<Battle> {
    try {
      const response = await apiClient.post<Battle>(`/battles/${battleId}/forfeit`);
      return response;
    } catch (error) {
      console.error('Error forfeiting battle:', error);
      throw error;
    }
  }
  
  async getBattleHistory(limit: number = 10, skip: number = 0): Promise<Battle[]> {
    try {
      const response = await apiClient.get<Battle[]>(
        `/battles/history?limit=${limit}&skip=${skip}`
      );
      return response;
    } catch (error) {
      console.error('Error fetching battle history:', error);
      throw error;
    }
  }
}

export const battlesService = new BattlesService();