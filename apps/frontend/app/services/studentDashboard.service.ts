import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3000';

export interface DashboardStats {
  currentLevel: number;
  currentRank: string;
  experience: number;
  experienceToNext: number;
  totalBattles: number;
  winRate: number;
  currentStreak: number;
  mastery: {
    mathematics: number;
    physics: number;
    chemistry: number;
    biology: number;
    spanish: number;
  };
  theta: {
    mathematics: number;
    physics: number;
    chemistry: number;
    biology: number;
    spanish: number;
  };
  classRanking: number;
  nationalRanking: number;
}

export interface ThetaEvolution {
  date: string;
  mathematics: number;
  physics: number;
  chemistry: number;
  biology: number;
  spanish: number;
  overall: number;
}

export interface ErrorAnalysis {
  id: string;
  questionId: string;
  subject: string;
  topic: string;
  difficulty: number;
  irtDifficulty: number;
  questionText: string;
  questionImage?: string;
  correctAnswer: string;
  selectedAnswer: string;
  distractors: {
    A: string;
    B: string;
    C: string;
    D: string;
  };
  timeSpent: number;
  averageTime: number;
  percentile: number;
  explanation: string;
  aiAnalysis: string;
  conceptsToReinforce: string[];
  date: string;
  wasReviewed: boolean;
}

export interface StudyRecommendation {
  id: string;
  type: 'video' | 'practice' | 'reading' | 'quiz';
  title: string;
  description: string;
  subject: string;
  difficulty: string;
  estimatedTime: number;
  priority: string;
  xpReward: number;
  progress: number;
  completed: boolean;
}

class StudentDashboardService {
  private apiClient = axios.create({
    baseURL: `${API_BASE_URL}/api`,
    timeout: 10000,
  });

  constructor() {
    // Add auth interceptor
    this.apiClient.interceptors.request.use((config) => {
      const token = typeof window !== 'undefined' ? localStorage.getItem('auth_token') : null;
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    });

    // Add response interceptor for error handling
    this.apiClient.interceptors.response.use(
      (response) => response,
      (error) => {
        console.error('API Error:', error);
        if (error.response?.status === 401) {
          // Handle unauthorized
          if (typeof window !== 'undefined') {
            localStorage.removeItem('auth_token');
            window.location.href = '/login';
          }
        }
        return Promise.reject(error);
      }
    );
  }

  /**
   * Get dashboard statistics for the current user
   */
  async getDashboardStats(timeFilter: '7d' | '30d' | '90d' = '30d'): Promise<DashboardStats> {
    try {
      const response = await this.apiClient.get('/student/dashboard/stats', {
        params: { timeFilter }
      });
      return response.data;
    } catch (error) {
      console.error('Error fetching dashboard stats:', error);
      throw new Error('No se pudieron cargar las estadísticas del estudiante');
    }
  }

  /**
   * Get theta evolution data over time
   */
  async getThetaEvolution(timeFilter: '7d' | '30d' | '90d' = '30d'): Promise<ThetaEvolution[]> {
    try {
      const response = await this.apiClient.get('/student/dashboard/theta-evolution', {
        params: { timeFilter }
      });
      return response.data;
    } catch (error) {
      console.error('Error fetching theta evolution:', error);
      throw new Error('No se pudieron cargar los datos de evolución theta');
    }
  }

  /**
   * Get error analysis for wrong answers
   */
  async getErrorAnalysis(filters?: {
    subject?: string;
    difficulty?: string;
    timeframe?: string;
    reviewed?: string;
  }): Promise<ErrorAnalysis[]> {
    try {
      const response = await this.apiClient.get('/student/dashboard/error-analysis', {
        params: filters
      });
      return response.data;
    } catch (error) {
      console.error('Error fetching error analysis:', error);
      throw new Error('No se pudieron cargar los datos de análisis de errores');
    }
  }

  /**
   * Get personalized study recommendations
   */
  async getStudyRecommendations(): Promise<StudyRecommendation[]> {
    try {
      const response = await this.apiClient.get('/student/dashboard/recommendations');
      return response.data;
    } catch (error) {
      console.error('Error fetching study recommendations:', error);
      throw new Error('No se pudieron cargar las recomendaciones de estudio');
    }
  }

  /**
   * Mark an error as reviewed
   */
  async markErrorAsReviewed(errorId: string): Promise<void> {
    try {
      await this.apiClient.put(`/student/dashboard/errors/${errorId}/reviewed`);
    } catch (error) {
      console.error('Error marking error as reviewed:', error);
    }
  }

  /**
   * Update task progress
   */
  async updateTaskProgress(taskId: string, progress: number): Promise<void> {
    try {
      await this.apiClient.put(`/student/dashboard/tasks/${taskId}/progress`, { progress });
    } catch (error) {
      console.error('Error updating task progress:', error);
    }
  }

  /**
   * Generate new study plan
   */
  async generateNewStudyPlan(): Promise<void> {
    try {
      await this.apiClient.post('/student/dashboard/generate-plan');
    } catch (error) {
      console.error('Error generating new study plan:', error);
    }
  }

  /**
   * Get IRT metrics for specific subjects
   */
  async getIRTMetrics(subjects?: string[]): Promise<{
    theta: Record<string, number>;
    difficulty: Record<string, number>;
    discrimination: Record<string, number>;
    guessing: Record<string, number>;
  }> {
    try {
      const response = await this.apiClient.get('/student/dashboard/irt-metrics', {
        params: { subjects: subjects?.join(',') }
      });
      return response.data;
    } catch (error) {
      console.error('Error fetching IRT metrics:', error);
      throw new Error('No se pudieron cargar las métricas IRT');
    }
  }

  /**
   * Calculate 3PL IRT probability for a given theta and item parameters
   */
  calculate3PLProbability(theta: number, difficulty: number, discrimination: number, guessing: number): number {
    const exp = Math.exp(discrimination * (theta - difficulty));
    return guessing + (1 - guessing) * (exp / (1 + exp));
  }

  /**
   * Estimate theta using Maximum Likelihood Estimation
   */
  estimateTheta(responses: boolean[], difficulties: number[], discriminations: number[], guessings: number[]): number {
    let theta = 0; // Initial estimate
    const maxIterations = 50;
    const tolerance = 0.001;

    for (let iteration = 0; iteration < maxIterations; iteration++) {
      let firstDerivative = 0;
      let secondDerivative = 0;

      for (let i = 0; i < responses.length; i++) {
        const prob = this.calculate3PLProbability(theta, difficulties[i], discriminations[i], guessings[i]);
        const q = 1 - prob;
        const factor = discriminations[i] * (1 - guessings[i]) * Math.exp(discriminations[i] * (theta - difficulties[i]));
        const denominator = Math.pow(1 + Math.exp(discriminations[i] * (theta - difficulties[i])), 2);
        
        const dP_dTheta = factor / denominator;
        
        if (responses[i]) {
          firstDerivative += dP_dTheta / prob;
          secondDerivative -= Math.pow(dP_dTheta, 2) / Math.pow(prob, 2);
        } else {
          firstDerivative -= dP_dTheta / q;
          secondDerivative -= Math.pow(dP_dTheta, 2) / Math.pow(q, 2);
        }
      }

      const deltaTheta = firstDerivative / secondDerivative;
      theta -= deltaTheta;

      if (Math.abs(deltaTheta) < tolerance) {
        break;
      }
    }

    return theta;
  }

}

export const studentDashboardService = new StudentDashboardService();