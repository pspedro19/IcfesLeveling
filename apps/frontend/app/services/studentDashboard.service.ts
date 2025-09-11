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
      // Return mock data for development
      return this.getMockDashboardStats();
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
      return this.getMockThetaEvolution(timeFilter);
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
      return this.getMockErrorAnalysis();
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
      return this.getMockStudyRecommendations();
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
      return this.getMockIRTMetrics();
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

  // Mock data methods for development
  private getMockDashboardStats(): DashboardStats {
    return {
      currentLevel: 15,
      currentRank: 'A+',
      experience: 12750,
      experienceToNext: 2250,
      totalBattles: 156,
      winRate: 78.5,
      currentStreak: 7,
      mastery: {
        mathematics: 82,
        physics: 76,
        chemistry: 71,
        biology: 85,
        spanish: 79
      },
      theta: {
        mathematics: 1.2,
        physics: 0.8,
        chemistry: 0.6,
        biology: 1.4,
        spanish: 0.9
      },
      classRanking: 3,
      nationalRanking: 1247
    };
  }

  private getMockThetaEvolution(timeFilter: string): ThetaEvolution[] {
    const days = timeFilter === '7d' ? 7 : timeFilter === '30d' ? 30 : 90;
    const data: ThetaEvolution[] = [];
    
    for (let i = days; i >= 0; i--) {
      const date = new Date();
      date.setDate(date.getDate() - i);
      
      const baseProgress = (days - i) / days * 0.5;
      const randomFactor = (Math.random() - 0.5) * 0.3;
      
      data.push({
        date: date.toISOString().split('T')[0],
        mathematics: 0.2 + baseProgress + randomFactor + Math.sin(i * 0.1) * 0.1,
        physics: 0.1 + baseProgress + randomFactor + Math.cos(i * 0.15) * 0.1,
        chemistry: 0.15 + baseProgress + randomFactor + Math.sin(i * 0.12) * 0.1,
        biology: 0.25 + baseProgress + randomFactor + Math.cos(i * 0.08) * 0.1,
        spanish: 0.3 + baseProgress + randomFactor + Math.sin(i * 0.2) * 0.1,
        overall: 0.2 + baseProgress + randomFactor
      });
    }
    
    return data;
  }

  private getMockErrorAnalysis(): ErrorAnalysis[] {
    return [
      {
        id: 'error_1',
        questionId: 'q_1001',
        subject: 'Matemáticas',
        topic: 'Álgebra',
        difficulty: 3.5,
        irtDifficulty: 0.8,
        questionText: 'Resuelve la siguiente ecuación cuadrática: x² - 5x + 6 = 0',
        correctAnswer: 'C',
        selectedAnswer: 'A',
        distractors: {
          A: 'x = 1, x = 6',
          B: 'x = -2, x = -3',
          C: 'x = 2, x = 3',
          D: 'x = 0, x = 5'
        },
        timeSpent: 180,
        averageTime: 150,
        percentile: 65,
        explanation: 'Para resolver x² - 5x + 6 = 0, factorizamos: (x-2)(x-3) = 0, por lo que x = 2 o x = 3.',
        aiAnalysis: 'Tu error sugiere dificultad con la factorización de ecuaciones cuadráticas. Practica más problemas similares.',
        conceptsToReinforce: ['Factorización', 'Ecuaciones cuadráticas', 'Productos notables'],
        date: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(),
        wasReviewed: false
      }
    ];
  }

  private getMockStudyRecommendations(): StudyRecommendation[] {
    return [
      {
        id: 'rec_1',
        type: 'video',
        title: 'Fundamentos de Álgebra Lineal',
        description: 'Revisar conceptos básicos de vectores y matrices',
        subject: 'Matemáticas',
        difficulty: 'medium',
        estimatedTime: 45,
        priority: 'high',
        xpReward: 150,
        progress: 60,
        completed: false
      }
    ];
  }

  private getMockIRTMetrics() {
    return {
      theta: {
        mathematics: 1.2,
        physics: 0.8,
        chemistry: 0.6,
        biology: 1.4,
        spanish: 0.9
      },
      difficulty: {
        mathematics: 0.8,
        physics: 0.9,
        chemistry: 0.85,
        biology: 0.7,
        spanish: 0.6
      },
      discrimination: {
        mathematics: 1.2,
        physics: 1.1,
        chemistry: 1.15,
        biology: 1.0,
        spanish: 0.9
      },
      guessing: {
        mathematics: 0.15,
        physics: 0.18,
        chemistry: 0.16,
        biology: 0.20,
        spanish: 0.22
      }
    };
  }
}

export const studentDashboardService = new StudentDashboardService();