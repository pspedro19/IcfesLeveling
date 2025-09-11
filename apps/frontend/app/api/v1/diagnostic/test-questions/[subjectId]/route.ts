import { NextResponse } from 'next/server';
import { NextRequest } from 'next/server';

// Mock questions for different subjects
const mockQuestions = {
  '1': [ // Matemáticas
    {
      id: 'math_1',
      question_text: '¿Cuál es el resultado de 2x + 5 = 15?',
      pregunta_texto: '¿Cuál es el resultado de 2x + 5 = 15?',
      opcion_a_texto: 'x = 5',
      opcion_b_texto: 'x = 10',
      opcion_c_texto: 'x = 7',
      opcion_d_texto: 'x = 3',
      difficulty: 2,
      topic: { name: 'Álgebra Básica' },
      hint: 'Despeja x moviendo el 5 al otro lado de la ecuación'
    },
    {
      id: 'math_2',
      question_text: '¿Cuál es el área de un círculo con radio 5?',
      pregunta_texto: '¿Cuál es el área de un círculo con radio 5?',
      opcion_a_texto: '25π',
      opcion_b_texto: '10π',
      opcion_c_texto: '5π',
      opcion_d_texto: '15π',
      difficulty: 2,
      topic: { name: 'Geometría' }
    }
  ],
  '2': [ // Lectura Crítica
    {
      id: 'reading_1',
      question_text: '¿Cuál es la idea principal del texto?',
      pregunta_texto: '¿Cuál es la idea principal del texto?',
      opcion_a_texto: 'La importancia de la educación',
      opcion_b_texto: 'Los problemas sociales',
      opcion_c_texto: 'El desarrollo tecnológico',
      opcion_d_texto: 'La comunicación moderna',
      difficulty: 3,
      topic: { name: 'Comprensión de lectura' }
    },
    {
      id: 'reading_2',
      question_text: '¿Qué figura literaria se utiliza en la frase "Sus ojos eran dos estrellas"?',
      pregunta_texto: '¿Qué figura literaria se utiliza en la frase "Sus ojos eran dos estrellas"?',
      opcion_a_texto: 'Metáfora',
      opcion_b_texto: 'Símil',
      opcion_c_texto: 'Hipérbole',
      opcion_d_texto: 'Personificación',
      difficulty: 2,
      topic: { name: 'Figuras literarias' }
    }
  ],
  '3': [ // Ciencias Naturales
    {
      id: 'science_1',
      question_text: '¿Cuál es la fórmula química del agua?',
      pregunta_texto: '¿Cuál es la fórmula química del agua?',
      opcion_a_texto: 'H2O',
      opcion_b_texto: 'CO2',
      opcion_c_texto: 'H2SO4',
      opcion_d_texto: 'NaCl',
      difficulty: 1,
      topic: { name: 'Química básica' }
    },
    {
      id: 'science_2',
      question_text: '¿Cuántos cromosomas tiene el ser humano?',
      pregunta_texto: '¿Cuántos cromosomas tiene el ser humano?',
      opcion_a_texto: '44',
      opcion_b_texto: '46',
      opcion_c_texto: '48',
      opcion_d_texto: '42',
      difficulty: 2,
      topic: { name: 'Biología celular' }
    }
  ],
  '4': [ // Ciencias Sociales
    {
      id: 'social_1',
      question_text: '¿En qué año se descubrió América?',
      pregunta_texto: '¿En qué año se descubrió América?',
      opcion_a_texto: '1491',
      opcion_b_texto: '1492',
      opcion_c_texto: '1493',
      opcion_d_texto: '1490',
      difficulty: 1,
      topic: { name: 'Historia de América' }
    },
    {
      id: 'social_2',
      question_text: '¿Cuál es la capital de Colombia?',
      pregunta_texto: '¿Cuál es la capital de Colombia?',
      opcion_a_texto: 'Medellín',
      opcion_b_texto: 'Bogotá',
      opcion_c_texto: 'Cali',
      opcion_d_texto: 'Cartagena',
      difficulty: 1,
      topic: { name: 'Geografía' }
    }
  ],
  '5': [ // Inglés
    {
      id: 'english_1',
      question_text: 'What is the correct form of "to be" for "I"?',
      pregunta_texto: 'What is the correct form of "to be" for "I"?',
      opcion_a_texto: 'am',
      opcion_b_texto: 'is',
      opcion_c_texto: 'are',
      opcion_d_texto: 'be',
      difficulty: 1,
      topic: { name: 'Grammar basics' }
    },
    {
      id: 'english_2',
      question_text: 'Which word means "libro" in English?',
      pregunta_texto: 'Which word means "libro" in English?',
      opcion_a_texto: 'Book',
      opcion_b_texto: 'Paper',
      opcion_c_texto: 'Pen',
      opcion_d_texto: 'Desk',
      difficulty: 1,
      topic: { name: 'Vocabulary' }
    }
  ]
};

export async function GET(
  request: NextRequest,
  { params }: { params: { subjectId: string } }
) {
  try {
    const subjectId = params.subjectId;
    const { searchParams } = new URL(request.url);
    const limit = parseInt(searchParams.get('limit') || '20', 10);

    // Get questions for the subject
    const subjectQuestions = mockQuestions[subjectId as keyof typeof mockQuestions] || [];
    
    // Generate additional questions if needed
    const questions = [];
    const baseQuestions = subjectQuestions;
    
    for (let i = 0; i < limit; i++) {
      const baseQuestion = baseQuestions[i % baseQuestions.length];
      questions.push({
        ...baseQuestion,
        id: `${baseQuestion.id}_${i + 1}`,
        question_text: `${baseQuestion.question_text}`,
        pregunta_texto: `${baseQuestion.pregunta_texto}`
      });
    }

    // Add a small delay to simulate network request
    await new Promise(resolve => setTimeout(resolve, 800));

    return NextResponse.json(questions, {
      status: 200,
      headers: {
        'Content-Type': 'application/json',
      }
    });
  } catch (error) {
    console.error('Error in test-questions API:', error);
    return NextResponse.json(
      { 
        error: 'Failed to load test questions',
        message: 'Internal server error'
      },
      { status: 500 }
    );
  }
}