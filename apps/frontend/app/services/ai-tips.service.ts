import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:4000';

export interface BattleTips {
  tips: string[];
  generated: boolean;
  accuracy?: number;
  weakAreas?: string[];
}

export interface QuestionExplanation {
  explanation: string;
  correctAnswer: string;
  hint?: string;
  generated: boolean;
}

export interface StudyPlan {
  objectives: string[];
  strategies: string[];
  dailyTime: string;
  resources: string[];
  generated: boolean;
}

export interface LearningPattern {
  pattern: string;
  metrics: {
    totalQuestions: number;
    accuracy: number;
    avgResponseTime: number;
    difficultyTrend: string;
  };
  insights: string[];
  recommendations: string[];
}

export interface WeakArea {
  topic: string;
  accuracy: number;
  questionsAnswered: number;
}

class AITipsService {
  private getAuthHeaders() {
    const token = localStorage.getItem('token');
    return {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json'
    };
  }

  // Get battle tips based on performance
  async getBattleTips(
    battleId: string,
    currentTopic: string,
    difficulty: number,
    battleType: string = 'normal'
  ): Promise<BattleTips> {
    try {
      const response = await axios.post(
        `${API_URL}/api/v1/ai/tips/battle`,
        {
          battle_id: battleId,
          current_topic: currentTopic,
          difficulty,
          battle_type: battleType
        },
        { headers: this.getAuthHeaders() }
      );
      
      return response.data;
    } catch (error) {
      console.error('Error getting battle tips:', error);
      // Return default tips if error
      return {
        tips: [
          'Tómate tu tiempo para leer cada pregunta cuidadosamente',
          'Elimina las opciones que sabes que son incorrectas',
          'Confía en tu primera instinto si no estás seguro'
        ],
        generated: false
      };
    }
  }

  // Get detailed explanation for a question
  async getQuestionExplanation(
    questionId: string,
    userAnswer: string,
    isCorrect: boolean
  ): Promise<QuestionExplanation> {
    try {
      const response = await axios.post(
        `${API_URL}/api/v1/ai/tips/explanation`,
        {
          question_id: questionId,
          user_answer: userAnswer,
          is_correct: isCorrect
        },
        { headers: this.getAuthHeaders() }
      );
      
      return response.data;
    } catch (error) {
      console.error('Error getting explanation:', error);
      // Return basic explanation if error
      return {
        explanation: isCorrect 
          ? '¡Correcto! Has demostrado un buen entendimiento del tema.'
          : 'Respuesta incorrecta. Revisa el concepto y vuelve a intentarlo.',
        correctAnswer: '',
        generated: false
      };
    }
  }

  // Get personalized study plan
  async getStudyPlan(
    weakAreas?: WeakArea[],
    timeAvailable?: number,
    targetScore?: number
  ): Promise<StudyPlan> {
    try {
      const response = await axios.post(
        `${API_URL}/api/v1/ai/tips/study-plan`,
        {
          weak_areas: weakAreas,
          time_available: timeAvailable,
          target_score: targetScore
        },
        { headers: this.getAuthHeaders() }
      );
      
      return response.data;
    } catch (error) {
      console.error('Error getting study plan:', error);
      // Return default plan if error
      return {
        objectives: [
          'Mejorar precisión en áreas débiles',
          'Completar al menos 50 preguntas esta semana',
          'Mantener una racha de estudio diaria'
        ],
        strategies: [
          'Enfócate en un tema por día',
          'Revisa todas las respuestas incorrectas',
          'Practica con temporizador'
        ],
        dailyTime: '45-60 minutos',
        resources: [
          'Usa mapas conceptuales',
          'Forma grupos de estudio'
        ],
        generated: false
      };
    }
  }

  // Analyze learning patterns
  async analyzeLearningPattern(days: number = 7): Promise<LearningPattern> {
    try {
      const response = await axios.get(
        `${API_URL}/api/v1/ai/tips/learning-pattern`,
        {
          params: { days },
          headers: this.getAuthHeaders()
        }
      );
      
      return response.data;
    } catch (error) {
      console.error('Error analyzing learning pattern:', error);
      throw error;
    }
  }

  // Get motivational message
  async getMotivationalMessage(
    context: 'level_up' | 'streak' | 'battle_won' | 'achievement',
    achievementName?: string
  ): Promise<string> {
    try {
      const response = await axios.post(
        `${API_URL}/api/v1/ai/tips/motivational`,
        {
          context,
          achievement_name: achievementName
        },
        { headers: this.getAuthHeaders() }
      );
      
      return response.data.message;
    } catch (error) {
      console.error('Error getting motivational message:', error);
      // Return default message
      const defaultMessages = {
        level_up: '¡Felicidades! Has subido de nivel. ¡Sigue así!',
        streak: '¡Increíble racha! Tu dedicación es admirable.',
        battle_won: '¡Victoria! Has demostrado tu valía.',
        achievement: '¡Nuevo logro desbloqueado! Tu leyenda crece.'
      };
      
      return defaultMessages[context];
    }
  }

  // Check service status
  async checkServiceStatus(): Promise<{
    available: boolean;
    service: string;
    features: Record<string, boolean>;
  }> {
    try {
      const response = await axios.get(
        `${API_URL}/api/v1/ai/tips/status`,
        { headers: this.getAuthHeaders() }
      );
      
      return response.data;
    } catch (error) {
      console.error('Error checking service status:', error);
      return {
        available: false,
        service: 'Offline',
        features: {
          battle_tips: false,
          explanations: false,
          study_plans: false,
          pattern_analysis: false,
          motivational_messages: false
        }
      };
    }
  }
}

export const aiTipsService = new AITipsService();