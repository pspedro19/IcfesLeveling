import { apiClient } from '@/lib/axios';

export interface YAMLGenerationRequest {
  subject: string;
  user_level: number;
  weakness_data?: Record<string, number>;
}

export interface StudyUnit {
  name: string;
  description: string;
  topics: Array<{
    name: string;
    difficulty: number;
    questions: number;
    tags?: string[];
  }>;
  recommendations?: {
    priority: 'high' | 'medium' | 'low';
    weak_areas?: string[];
    focus_topics?: string[];
    study_time?: string;
  };
  unlocked: boolean;
  progress: number;
  ai_recommended?: boolean;
}

export interface StudyDungeon {
  subject: string;
  title: string;
  description: string;
  units: StudyUnit[];
  total_questions: number;
  estimated_time: string;
  difficulty_curve: 'linear' | 'progressive' | 'adaptive';
}

class StudyPlanService {
  async generateYAML(data: YAMLGenerationRequest): Promise<string> {
    try {
      const response = await apiClient.post<string>(
        '/study-plans/generate-yaml',
        data,
        {
          headers: {
            'Accept': 'text/yaml',
          },
        }
      );
      return response;
    } catch (error) {
      console.error('Error generating YAML:', error);
      throw new Error('No se pudo generar el plan de estudio personalizado');
    }
  }
}

export const studyPlanService = new StudyPlanService();