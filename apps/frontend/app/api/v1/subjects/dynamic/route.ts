import { NextResponse } from 'next/server';

// Mock subjects data for testing
const mockSubjects = [
  {
    id: '1',
    name: 'Matemáticas',
    description: 'Álgebra, geometría, cálculo y estadística',
    aliases: ['matematicas', 'math', 'mathematics'],
    color: '#8B5CF6',
    display: {
      color_primary: '#8B5CF6',
      color_secondary: '#A78BFA',
      description_short: 'Domina los números y las formas'
    },
    config: {
      total_questions: 45,
      time_limit_minutes: 60,
      difficulty_distribution: {
        easy: 40,
        medium: 40,
        hard: 20
      }
    }
  },
  {
    id: '2',
    name: 'Lectura Crítica',
    description: 'Comprensión y análisis de textos',
    aliases: ['lectura', 'reading', 'lenguaje'],
    color: '#3B82F6',
    display: {
      color_primary: '#3B82F6',
      color_secondary: '#60A5FA',
      description_short: 'Analiza y comprende textos complejos'
    },
    config: {
      total_questions: 45,
      time_limit_minutes: 90,
      difficulty_distribution: {
        easy: 30,
        medium: 50,
        hard: 20
      }
    }
  },
  {
    id: '3',
    name: 'Ciencias Naturales',
    description: 'Física, química y biología',
    aliases: ['ciencias', 'naturales', 'science'],
    color: '#10B981',
    display: {
      color_primary: '#10B981',
      color_secondary: '#34D399',
      description_short: 'Explora los secretos de la naturaleza'
    },
    config: {
      total_questions: 45,
      time_limit_minutes: 60,
      difficulty_distribution: {
        easy: 35,
        medium: 45,
        hard: 20
      }
    }
  },
  {
    id: '4',
    name: 'Ciencias Sociales',
    description: 'Historia, geografía y ciudadanía',
    aliases: ['sociales', 'historia', 'geografia'],
    color: '#F59E0B',
    display: {
      color_primary: '#F59E0B',
      color_secondary: '#FBBF24',
      description_short: 'Comprende la sociedad y su historia'
    },
    config: {
      total_questions: 45,
      time_limit_minutes: 90,
      difficulty_distribution: {
        easy: 45,
        medium: 35,
        hard: 20
      }
    }
  },
  {
    id: '5',
    name: 'Inglés',
    description: 'Comprensión del idioma inglés',
    aliases: ['ingles', 'english', 'idiomas'],
    color: '#EF4444',
    display: {
      color_primary: '#EF4444',
      color_secondary: '#F87171',
      description_short: 'Domina el idioma global'
    },
    config: {
      total_questions: 45,
      time_limit_minutes: 60,
      difficulty_distribution: {
        easy: 40,
        medium: 40,
        hard: 20
      }
    }
  }
];

export async function GET() {
  try {
    // Add a small delay to simulate network request
    await new Promise(resolve => setTimeout(resolve, 500));

    return NextResponse.json(mockSubjects, {
      status: 200,
      headers: {
        'Content-Type': 'application/json',
      }
    });
  } catch (error) {
    console.error('Error in subjects/dynamic API:', error);
    return NextResponse.json(
      { 
        error: 'Failed to load subjects',
        message: 'Internal server error'
      },
      { status: 500 }
    );
  }
}