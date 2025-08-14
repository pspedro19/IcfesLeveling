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
      // Return mock YAML for development
      return this.getMockYAML(data.subject);
    }
  }
  
  private getMockYAML(subject: string): string {
    return `
subject: ${subject}
title: "Mazmorra de ${subject}"
description: "Conquista los conceptos fundamentales y avanza tu dominio"
units:
  - name: "Fundamentos Básicos"
    description: "Conceptos esenciales para construir una base sólida"
    topics:
      - name: "Introducción"
        difficulty: 1
        questions: 10
        tags: ["básico", "conceptos"]
      - name: "Teoría Fundamental"
        difficulty: 2
        questions: 15
        tags: ["teoría", "importante"]
    recommendations:
      priority: "high"
      weak_areas: ["conceptos básicos"]
      study_time: "2 horas"
    unlocked: true
    progress: 30
    ai_recommended: true
    
  - name: "Nivel Intermedio"
    description: "Aplica los conceptos en problemas más complejos"
    topics:
      - name: "Aplicaciones Prácticas"
        difficulty: 3
        questions: 20
        tags: ["práctica", "aplicación"]
      - name: "Casos de Estudio"
        difficulty: 3
        questions: 15
        tags: ["análisis", "casos"]
    unlocked: true
    progress: 0
    
  - name: "Dominio Avanzado"
    description: "Desafíos para verdaderos maestros"
    topics:
      - name: "Problemas Complejos"
        difficulty: 4
        questions: 25
        tags: ["avanzado", "complejo"]
      - name: "Síntesis y Evaluación"
        difficulty: 5
        questions: 20
        tags: ["síntesis", "crítico"]
    recommendations:
      priority: "low"
      focus_topics: ["síntesis avanzada"]
      study_time: "3 horas"
    unlocked: false
    progress: 0
    
total_questions: 105
estimated_time: "4-5 horas"
difficulty_curve: "progressive"
    `.trim();
  }
}

export const studyPlanService = new StudyPlanService();