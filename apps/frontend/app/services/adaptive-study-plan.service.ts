import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:4000';

export interface VideoProgressUpdate {
  youtube_url: string;
  video_title: string;
  video_duration_seconds: number;
  watched_seconds: number;
  watch_percentage: number;
  is_completed?: boolean;
}

export interface ExerciseAttempt {
  question_id: string;
  user_answer: string;
  is_correct: boolean;
  response_time_ms: number;
  difficulty_level: number;
  topic_name: string;
}

export interface ExerciseSessionComplete {
  unit_number: number;
  topic_name: string;
  attempts: ExerciseAttempt[];
  session_duration_seconds: number;
}

export interface UserMetrics {
  overall_progress: number;
  completed_units: number;
  total_videos_watched: number;
  total_exercises_completed: number;
  current_streak: number;
  average_accuracy: number;
  learning_patterns: {
    consistency_score: number;
    improvement_trend: string;
    average_score: number;
    completion_rate: number;
    learning_velocity: string;
  };
}

export interface AdaptiveStudyPlan {
  subject: string;
  title: string;
  description: string;
  units: StudyPlanUnit[];
  total_questions: number;
  total_videos: number;
  estimated_time: string;
  difficulty_curve: string;
  personalization: {
    based_on_performance: boolean;
    adaptation_date: string;
    focus_areas: string[];
  };
}

export interface StudyPlanUnit {
  unit_number: number;
  name: string;
  description: string;
  topics: StudyPlanTopic[];
  video_urls: Record<string, string>;
  reading_materials: Record<string, string>;
  learning_objectives: string[];
  exercise_count: number;
  recommendations: {
    priority: string;
    weak_areas: string[];
    focus_topics: string[];
    study_time: string;
    custom_tips: string[];
  };
  unlocked: boolean;
  progress: number;
  ai_recommended: boolean;
  estimated_completion_time: number;
  difficulty_level: number;
  icfes_weight: number;
}

export interface StudyPlanTopic {
  name: string;
  difficulty: number;
  questions: number;
  tags: string[];
  video_url?: string;
  completed: boolean;
  video_watched: boolean;
  exercises_completed: number;
  total_exercises: number;
}

class AdaptiveStudyPlanService {
  private getAuthHeaders() {
    const token = localStorage.getItem('access_token');
    return {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    };
  }

  async generateAdaptivePlan(subjectId: string): Promise<AdaptiveStudyPlan> {
    try {
      const response = await axios.post(
        `${API_BASE_URL}/api/v1/study-plans/generate-adaptive`,
        { subject_id: subjectId },
        { headers: this.getAuthHeaders() }
      );
      return response.data;
    } catch (error) {
      console.error('Error generating adaptive plan:', error);
      throw error;
    }
  }

  async getAdaptivePlan(planId: string): Promise<AdaptiveStudyPlan> {
    try {
      const response = await axios.get(
        `${API_BASE_URL}/api/v1/study-plans/${planId}/adaptive`,
        { headers: this.getAuthHeaders() }
      );
      return response.data;
    } catch (error) {
      console.error('Error getting adaptive plan:', error);
      throw error;
    }
  }

  async updateVideoProgress(
    planId: string, 
    unitNumber: number, 
    progress: VideoProgressUpdate
  ): Promise<any> {
    try {
      const response = await axios.post(
        `${API_BASE_URL}/api/v1/video-tracking/${planId}/units/${unitNumber}/video-progress`,
        progress,
        { headers: this.getAuthHeaders() }
      );
      return response.data;
    } catch (error) {
      console.error('Error updating video progress:', error);
      throw error;
    }
  }

  async getVideoProgress(planId: string): Promise<any> {
    try {
      const response = await axios.get(
        `${API_BASE_URL}/api/v1/video-tracking/${planId}/video-progress`,
        { headers: this.getAuthHeaders() }
      );
      return response.data;
    } catch (error) {
      console.error('Error getting video progress:', error);
      throw error;
    }
  }

  async getVideoMetrics(planId: string, unitNumber: number): Promise<any> {
    try {
      const response = await axios.get(
        `${API_BASE_URL}/api/v1/video-tracking/${planId}/units/${unitNumber}/video-metrics`,
        { headers: this.getAuthHeaders() }
      );
      return response.data;
    } catch (error) {
      console.error('Error getting video metrics:', error);
      throw error;
    }
  }

  async startExerciseSession(
    planId: string, 
    unitNumber: number, 
    topicName: string, 
    expectedQuestions: number
  ): Promise<any> {
    try {
      const response = await axios.post(
        `${API_BASE_URL}/api/v1/exercise-tracking/${planId}/exercise-session/start`,
        {
          unit_number: unitNumber,
          topic_name: topicName,
          expected_questions: expectedQuestions
        },
        { headers: this.getAuthHeaders() }
      );
      return response.data;
    } catch (error) {
      console.error('Error starting exercise session:', error);
      throw error;
    }
  }

  async completeExerciseSession(
    planId: string, 
    sessionData: ExerciseSessionComplete
  ): Promise<any> {
    try {
      const response = await axios.post(
        `${API_BASE_URL}/api/v1/exercise-tracking/${planId}/exercise-session/complete`,
        sessionData,
        { headers: this.getAuthHeaders() }
      );
      return response.data;
    } catch (error) {
      console.error('Error completing exercise session:', error);
      throw error;
    }
  }

  async getExerciseMetrics(
    planId: string, 
    unitNumber?: number, 
    topicName?: string
  ): Promise<any> {
    try {
      const params = new URLSearchParams();
      if (unitNumber) params.append('unit_number', unitNumber.toString());
      if (topicName) params.append('topic_name', topicName);

      const response = await axios.get(
        `${API_BASE_URL}/api/v1/exercise-tracking/${planId}/exercise-metrics?${params.toString()}`,
        { headers: this.getAuthHeaders() }
      );
      return response.data;
    } catch (error) {
      console.error('Error getting exercise metrics:', error);
      throw error;
    }
  }

  async getUserMetrics(planId: string): Promise<UserMetrics> {
    try {
      // Combinar métricas de video y ejercicios
      const [videoProgress, exerciseMetrics] = await Promise.all([
        this.getVideoProgress(planId),
        this.getExerciseMetrics(planId)
      ]);

      const userMetrics: UserMetrics = {
        overall_progress: exerciseMetrics.overall_metrics?.average_score || 0,
        completed_units: exerciseMetrics.overall_metrics?.completed_units || 0,
        total_videos_watched: videoProgress.statistics?.completed_videos || 0,
        total_exercises_completed: exerciseMetrics.overall_metrics?.total_exercises_completed || 0,
        current_streak: 0, // TODO: Implementar sistema de rachas
        average_accuracy: exerciseMetrics.overall_metrics?.overall_accuracy || 0,
        learning_patterns: exerciseMetrics.learning_patterns || {
          consistency_score: 0,
          improvement_trend: 'stable',
          average_score: 0,
          completion_rate: 0,
          learning_velocity: 'normal'
        }
      };

      return userMetrics;
    } catch (error) {
      console.error('Error getting user metrics:', error);
      // Retornar métricas por defecto en caso de error
      return {
        overall_progress: 0,
        completed_units: 0,
        total_videos_watched: 0,
        total_exercises_completed: 0,
        current_streak: 0,
        average_accuracy: 0,
        learning_patterns: {
          consistency_score: 0,
          improvement_trend: 'stable',
          average_score: 0,
          completion_rate: 0,
          learning_velocity: 'normal'
        }
      };
    }
  }

  async getPersonalizedRecommendations(planId: string): Promise<string[]> {
    try {
      const metrics = await this.getExerciseMetrics(planId);
      const recommendations: string[] = [];

      // Generar recomendaciones basadas en métricas
      const averageScore = metrics.overall_metrics?.average_score || 0;
      const completionRate = metrics.learning_patterns?.completion_rate || 0;

      if (averageScore < 60) {
        recommendations.push('Dedica más tiempo a revisar los conceptos básicos');
        recommendations.push('Considera ver los videos nuevamente antes de hacer ejercicios');
      } else if (averageScore > 85) {
        recommendations.push('¡Excelente rendimiento! Puedes intentar ejercicios más desafiantes');
        recommendations.push('Considera ayudar a otros estudiantes en los foros');
      }

      if (completionRate < 0.5) {
        recommendations.push('Establece un horario de estudio regular para mejorar la consistencia');
      }

      // Agregar recomendaciones por defecto si no hay suficientes
      if (recommendations.length === 0) {
        recommendations.push('Mantén tu ritmo de estudio actual');
        recommendations.push('Revisa periódicamente los temas anteriores');
      }

      return recommendations;
    } catch (error) {
      console.error('Error getting personalized recommendations:', error);
      return [
        'Mantén un horario de estudio regular',
        'Revisa los videos antes de hacer ejercicios',
        'Practica con ejercicios de diferentes dificultades'
      ];
    }
  }

  async unlockNextUnit(planId: string, currentUnit: number): Promise<boolean> {
    try {
      // Verificar si el usuario ha completado suficientes elementos de la unidad actual
      const metrics = await this.getExerciseMetrics(planId, currentUnit);
      const unitData = metrics.units?.find((u: any) => u.unit_number === currentUnit);

      if (!unitData) return false;

      const score = unitData.score || 0;
      const isCompleted = unitData.is_completed || false;

      // Criterios para desbloquear: score >= 70% O unidad completada
      return score >= 70 || isCompleted;
    } catch (error) {
      console.error('Error checking unit unlock status:', error);
      return false;
    }
  }

  // Método para generar un plan de estudio YAML personalizado
  async generatePersonalizedYAML(planId: string): Promise<string> {
    try {
      const [adaptivePlan, metrics] = await Promise.all([
        this.getAdaptivePlan(planId),
        this.getUserMetrics(planId)
      ]);

      const yaml = this.buildYAMLFromPlan(adaptivePlan, metrics);
      return yaml;
    } catch (error) {
      console.error('Error generating personalized YAML:', error);
      throw error;
    }
  }

  private buildYAMLFromPlan(plan: AdaptiveStudyPlan, metrics: UserMetrics): string {
    const yaml = `
subject: ${plan.subject}
title: ${plan.title}
description: ${plan.description}
personalization:
  based_on_performance: ${plan.personalization.based_on_performance}
  adaptation_date: ${plan.personalization.adaptation_date}
  focus_areas: ${JSON.stringify(plan.personalization.focus_areas)}
  user_metrics:
    overall_progress: ${metrics.overall_progress}%
    completed_units: ${metrics.completed_units}
    learning_velocity: ${metrics.learning_patterns.learning_velocity}
    
units:${plan.units.map(unit => `
  - unit_number: ${unit.unit_number}
    name: "${unit.name}"
    description: "${unit.description}"
    unlocked: ${unit.unlocked}
    ai_recommended: ${unit.ai_recommended}
    progress: ${unit.progress}%
    estimated_time: ${unit.estimated_completion_time}h
    difficulty_level: ${unit.difficulty_level}
    icfes_weight: ${unit.icfes_weight}
    
    learning_objectives:${unit.learning_objectives.map(obj => `
      - "${obj}"`).join('')}
    
    topics:${unit.topics.map(topic => `
      - name: "${topic.name}"
        difficulty: ${topic.difficulty}
        video_url: "${topic.video_url || ''}"
        video_watched: ${topic.video_watched}
        exercises: ${topic.exercises_completed}/${topic.total_exercises}
        completed: ${topic.completed}
        tags: ${JSON.stringify(topic.tags)}`).join('')}
    
    videos:${Object.entries(unit.video_urls).map(([topic, url]) => `
      - topic: "${topic}"
        url: "${url}"`).join('')}
    
    reading_materials:${Object.entries(unit.reading_materials).map(([name, url]) => `
      - name: "${name}"
        url: "${url}"`).join('')}
    
    recommendations:
      priority: ${unit.recommendations.priority}
      study_time: "${unit.recommendations.study_time}"
      weak_areas: ${JSON.stringify(unit.recommendations.weak_areas)}
      focus_topics: ${JSON.stringify(unit.recommendations.focus_topics)}
      custom_tips: ${JSON.stringify(unit.recommendations.custom_tips)}`).join('')}

statistics:
  total_questions: ${plan.total_questions}
  total_videos: ${plan.total_videos}
  estimated_time: "${plan.estimated_time}"
  difficulty_curve: ${plan.difficulty_curve}
`.trim();

    return yaml;
  }
}

export const adaptiveStudyPlanService = new AdaptiveStudyPlanService();