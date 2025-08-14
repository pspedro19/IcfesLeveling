import { axiosInstance } from '../lib/axios';

export interface MultimediaQuestion {
  id: string;
  pregunta_texto?: string;
  pregunta_imagen?: string;
  opcion_a_texto?: string;
  opcion_a_imagen?: string;
  opcion_b_texto?: string;
  opcion_b_imagen?: string;
  opcion_c_texto?: string;
  opcion_c_imagen?: string;
  opcion_d_texto?: string;
  opcion_d_imagen?: string;
  respuesta_correcta: string;
  difficulty?: number;
  explanation?: string;
  hint?: string;
  topic_id?: string;
  subject_id?: string;
  created_at?: string;
  updated_at?: string;
}

export interface QuestionNavigationGrid {
  total_questions: number;
  current_question: number;
  answered_questions: number[];
  question_states: Record<number, string>;
}

export interface QuestionValidationRequest {
  pregunta_texto?: string;
  pregunta_imagen?: string;
  opcion_a_texto?: string;
  opcion_a_imagen?: string;
  opcion_b_texto?: string;
  opcion_b_imagen?: string;
  opcion_c_texto?: string;
  opcion_c_imagen?: string;
  opcion_d_texto?: string;
  opcion_d_imagen?: string;
  respuesta_correcta: string;
}

export interface QuestionValidationResponse {
  is_valid: boolean;
  errors: string[];
  warnings: string[];
  suggestions: string[];
}

export interface ExamSession {
  id: string;
  subject_id: string;
  questions: MultimediaQuestion[];
  current_question: number;
  answers: Record<string, string>;
  time_remaining: number;
  started_at: string;
  completed_at?: string;
}

class MultimediaQuestionsService {
  private baseUrl = '/api/v1/questions';

  /**
   * Obtener preguntas multimedia para un examen
   */
  async getMultimediaQuestions(params: {
    subject_id?: string;
    topic_id?: string;
    limit?: number;
  }): Promise<MultimediaQuestion[]> {
    try {
      const response = await axiosInstance.get(`${this.baseUrl}/multimedia`, {
        params
      });
      return response.data;
    } catch (error) {
      console.error('Error fetching multimedia questions:', error);
      throw new Error('Error al cargar las preguntas multimedia');
    }
  }

  /**
   * Obtener una pregunta específica por ID
   */
  async getQuestion(questionId: string): Promise<MultimediaQuestion> {
    try {
      const response = await axiosInstance.get(`${this.baseUrl}/${questionId}`);
      return response.data;
    } catch (error) {
      console.error('Error fetching question:', error);
      throw new Error('Error al cargar la pregunta');
    }
  }

  /**
   * Obtener cuadrícula de navegación
   */
  async getNavigationGrid(params: {
    subject_id?: string;
    current_question: number;
    answered_questions?: number[];
  }): Promise<QuestionNavigationGrid> {
    try {
      const response = await axiosInstance.get(`${this.baseUrl}/navigation-grid`, {
        params
      });
      return response.data;
    } catch (error) {
      console.error('Error fetching navigation grid:', error);
      throw new Error('Error al cargar la cuadrícula de navegación');
    }
  }

  /**
   * Validar una pregunta antes de guardarla
   */
  async validateQuestion(question: QuestionValidationRequest): Promise<QuestionValidationResponse> {
    try {
      const response = await axiosInstance.post(`${this.baseUrl}/validate`, question);
      return response.data;
    } catch (error) {
      console.error('Error validating question:', error);
      throw new Error('Error al validar la pregunta');
    }
  }

  /**
   * Crear una nueva pregunta
   */
  async createQuestion(question: MultimediaQuestion & { topic_id: string; subject_id: string }): Promise<MultimediaQuestion> {
    try {
      const response = await axiosInstance.post(this.baseUrl, question);
      return response.data;
    } catch (error) {
      console.error('Error creating question:', error);
      throw new Error('Error al crear la pregunta');
    }
  }

  /**
   * Actualizar una pregunta existente
   */
  async updateQuestion(questionId: string, updates: Partial<MultimediaQuestion>): Promise<MultimediaQuestion> {
    try {
      const response = await axiosInstance.put(`${this.baseUrl}/${questionId}`, updates);
      return response.data;
    } catch (error) {
      console.error('Error updating question:', error);
      throw new Error('Error al actualizar la pregunta');
    }
  }

  /**
   * Actualizar estadísticas de uso de una pregunta
   */
  async updateQuestionStats(questionId: string, responseTimeMs: number, isCorrect: boolean): Promise<void> {
    try {
      await axiosInstance.post(`${this.baseUrl}/${questionId}/update-stats`, {
        response_time_ms: responseTimeMs,
        is_correct: isCorrect
      });
    } catch (error) {
      console.error('Error updating question stats:', error);
      // No lanzar error ya que esto no es crítico
    }
  }

  /**
   * Obtener estadísticas de una pregunta
   */
  async getQuestionStats(questionId: string): Promise<{
    usage_count: number;
    success_rate: number;
    average_response_time: number;
    difficulty_rating: number;
  }> {
    try {
      const response = await axiosInstance.get(`${this.baseUrl}/stats/${questionId}`);
      return response.data;
    } catch (error) {
      console.error('Error fetching question stats:', error);
      throw new Error('Error al cargar las estadísticas de la pregunta');
    }
  }

  /**
   * Guardar sesión de examen en localStorage
   */
  saveExamSession(session: ExamSession): void {
    try {
      localStorage.setItem('exam_session', JSON.stringify(session));
    } catch (error) {
      console.error('Error saving exam session:', error);
    }
  }

  /**
   * Cargar sesión de examen desde localStorage
   */
  loadExamSession(): ExamSession | null {
    try {
      const session = localStorage.getItem('exam_session');
      return session ? JSON.parse(session) : null;
    } catch (error) {
      console.error('Error loading exam session:', error);
      return null;
    }
  }

  /**
   * Limpiar sesión de examen
   */
  clearExamSession(): void {
    try {
      localStorage.removeItem('exam_session');
    } catch (error) {
      console.error('Error clearing exam session:', error);
    }
  }

  /**
   * Verificar si una pregunta tiene contenido multimedia
   */
  hasMultimediaContent(question: MultimediaQuestion): boolean {
    return !!(question.pregunta_imagen || 
              question.opcion_a_imagen || 
              question.opcion_b_imagen || 
              question.opcion_c_imagen || 
              question.opcion_d_imagen);
  }

  /**
   * Obtener el tipo de contenido de una pregunta
   */
  getQuestionContentType(question: MultimediaQuestion): 'text-only' | 'image-only' | 'mixed' {
    const hasText = !!(question.pregunta_texto || 
                       question.opcion_a_texto || 
                       question.opcion_b_texto || 
                       question.opcion_c_texto || 
                       question.opcion_d_texto);
    const hasImage = this.hasMultimediaContent(question);

    if (hasText && hasImage) return 'mixed';
    if (hasImage) return 'image-only';
    return 'text-only';
  }

  /**
   * Validar respuesta del usuario
   */
  validateAnswer(question: MultimediaQuestion, userAnswer: string): {
    isCorrect: boolean;
    correctAnswer: string;
    explanation?: string;
  } {
    const isCorrect = userAnswer.toLowerCase() === question.respuesta_correcta.toLowerCase();
    
    return {
      isCorrect,
      correctAnswer: question.respuesta_correcta.toUpperCase(),
      explanation: question.explanation
    };
  }

  /**
   * Calcular progreso del examen
   */
  calculateProgress(questions: MultimediaQuestion[], answers: Record<string, string>): {
    total: number;
    answered: number;
    percentage: number;
    correct: number;
    incorrect: number;
  } {
    const total = questions.length;
    const answered = Object.keys(answers).length;
    const correct = questions.reduce((count, question) => {
      const userAnswer = answers[question.id];
      return count + (userAnswer === question.respuesta_correcta ? 1 : 0);
    }, 0);
    const incorrect = answered - correct;
    const percentage = total > 0 ? Math.round((answered / total) * 100) : 0;

    return {
      total,
      answered,
      percentage,
      correct,
      incorrect
    };
  }

  /**
   * Generar preguntas de ejemplo para testing
   */
  generateMockQuestions(count: number = 45): MultimediaQuestion[] {
    const questions: MultimediaQuestion[] = [];
    
    for (let i = 1; i <= count; i++) {
      const questionType = i % 3; // 0: solo texto, 1: texto + imagen, 2: opciones con imágenes
      
      let question: MultimediaQuestion = {
        id: i.toString(),
        respuesta_correcta: ['a', 'b', 'c', 'd'][Math.floor(Math.random() * 4)],
        difficulty: Math.floor(Math.random() * 5) + 1
      };

      switch (questionType) {
        case 0:
          question.pregunta_texto = `Pregunta ${i}: ¿Cuál es la respuesta correcta para esta pregunta de ejemplo?`;
          question.opcion_a_texto = `Opción A para pregunta ${i}`;
          question.opcion_b_texto = `Opción B para pregunta ${i}`;
          question.opcion_c_texto = `Opción C para pregunta ${i}`;
          question.opcion_d_texto = `Opción D para pregunta ${i}`;
          break;
        case 1:
          question.pregunta_texto = `Pregunta ${i}: Observa la imagen y responde:`;
          question.pregunta_imagen = `https://via.placeholder.com/400x300/${Math.floor(Math.random()*16777215).toString(16)}/FFFFFF?text=Imagen+${i}`;
          question.opcion_a_texto = `Opción A para pregunta ${i}`;
          question.opcion_b_texto = `Opción B para pregunta ${i}`;
          question.opcion_c_texto = `Opción C para pregunta ${i}`;
          question.opcion_d_texto = `Opción D para pregunta ${i}`;
          break;
        case 2:
          question.pregunta_texto = `Pregunta ${i}: Selecciona la opción correcta:`;
          question.opcion_a_texto = `Opción A`;
          question.opcion_a_imagen = `https://via.placeholder.com/150x100/10B981/FFFFFF?text=A`;
          question.opcion_b_texto = `Opción B`;
          question.opcion_b_imagen = `https://via.placeholder.com/150x100/F59E0B/FFFFFF?text=B`;
          question.opcion_c_texto = `Opción C`;
          question.opcion_c_imagen = `https://via.placeholder.com/150x100/EF4444/FFFFFF?text=C`;
          question.opcion_d_texto = `Opción D`;
          question.opcion_d_imagen = `https://via.placeholder.com/150x100/8B5CF6/FFFFFF?text=D`;
          break;
      }

      questions.push(question);
    }
    
    return questions;
  }
}

export const multimediaQuestionsService = new MultimediaQuestionsService(); 