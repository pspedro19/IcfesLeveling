import { apiClient } from '@/lib/axios';

export interface Question {
  id: string;
  question_text: string;
  question_type: string;
  subject_id: string;
  topic_id: string;
  difficulty: number;
  correct_answer: string;
  options: Record<string, string>;
  explanation?: string;
  is_active: boolean;
  created_at: string;
}

export interface QuestionFilters {
  subject_id?: string;
  topic_id?: string;
  difficulty?: number;
  limit?: number;
  skip?: number;
}

class QuestionsService {
  async getQuestions(filters: QuestionFilters = {}): Promise<Question[]> {
    try {
      const params = new URLSearchParams();
      
      if (filters.subject_id) params.append('subject_id', filters.subject_id);
      if (filters.topic_id) params.append('topic_id', filters.topic_id);
      if (filters.difficulty) params.append('difficulty', filters.difficulty.toString());
      if (filters.limit) params.append('limit', filters.limit.toString());
      if (filters.skip) params.append('skip', filters.skip.toString());
      
      const response = await apiClient.get<Question[]>(`/questions?${params.toString()}`);
      return response;
    } catch (error) {
      console.error('Error fetching questions:', error);
      throw error;
    }
  }
  
  async getQuestionById(id: string): Promise<Question> {
    try {
      const response = await apiClient.get<Question>(`/questions/${id}`);
      return response;
    } catch (error) {
      console.error('Error fetching question:', error);
      throw error;
    }
  }
  
  async getRandomQuestions(subject_id?: string, count: number = 5): Promise<Question[]> {
    try {
      const params = new URLSearchParams();
      params.append('count', count.toString());
      if (subject_id) params.append('subject_id', subject_id);
      
      const response = await apiClient.get<Question[]>(`/questions/random?${params.toString()}`);
      return response;
    } catch (error) {
      console.error('Error fetching random questions:', error);
      throw error;
    }
  }
}

export const questionsService = new QuestionsService();