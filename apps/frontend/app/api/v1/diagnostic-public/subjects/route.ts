import { NextResponse } from 'next/server';

// Mock subjects data for diagnostic-public endpoint
const mockPublicSubjects = [
  {
    id: '1',
    name: 'Matemáticas',
    description: 'Álgebra, geometría, cálculo y estadística',
    color: '#8B5CF6',
    config: {
      total_questions: 45,
      time_limit_minutes: 60
    }
  },
  {
    id: '2',
    name: 'Lectura Crítica',
    description: 'Comprensión y análisis de textos',
    color: '#3B82F6',
    config: {
      total_questions: 45,
      time_limit_minutes: 90
    }
  },
  {
    id: '3',
    name: 'Ciencias Naturales',
    description: 'Física, química y biología',
    color: '#10B981',
    config: {
      total_questions: 45,
      time_limit_minutes: 60
    }
  },
  {
    id: '4',
    name: 'Ciencias Sociales',
    description: 'Historia, geografía y ciudadanía',
    color: '#F59E0B',
    config: {
      total_questions: 45,
      time_limit_minutes: 90
    }
  },
  {
    id: '5',
    name: 'Inglés',
    description: 'Comprensión del idioma inglés',
    color: '#EF4444',
    config: {
      total_questions: 45,
      time_limit_minutes: 60
    }
  }
];

export async function GET() {
  try {
    // Add a small delay to simulate network request
    await new Promise(resolve => setTimeout(resolve, 300));

    return NextResponse.json(mockPublicSubjects, {
      status: 200,
      headers: {
        'Content-Type': 'application/json',
      }
    });
  } catch (error) {
    console.error('Error in diagnostic-public/subjects API:', error);
    return NextResponse.json(
      { 
        error: 'Failed to load public subjects',
        message: 'Internal server error'
      },
      { status: 500 }
    );
  }
}