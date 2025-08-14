import { Question, QuestionCreate, QuestionUpdate, QuestionValidationRequest, QuestionValidationResponse } from '@/types/question';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:4000/api/v1';

export class QuestionService {
  private static instance: QuestionService;
  private cache = new Map<string, any>();

  static getInstance(): QuestionService {
    if (!QuestionService.instance) {
      QuestionService.instance = new QuestionService();
    }
    return QuestionService.instance;
  }

  async getQuestions(params?: {
    subject_id?: string;
    topic_id?: string;
    difficulty?: number;
    limit?: number;
    offset?: number;
    mode?: 'guest';
  }): Promise<Question[]> {
    const queryParams = new URLSearchParams();
    
    if (params?.subject_id) queryParams.append('subject_id', params.subject_id);
    if (params?.topic_id) queryParams.append('topic_id', params.topic_id);
    if (params?.difficulty) queryParams.append('difficulty', params.difficulty.toString());
    if (params?.limit) queryParams.append('limit', params.limit.toString());
    if (params?.offset) queryParams.append('offset', params.offset.toString());
    if (params?.mode) queryParams.append('mode', params.mode);

    const cacheKey = `questions:${queryParams.toString()}`;
    if (this.cache.has(cacheKey)) {
      return this.cache.get(cacheKey);
    }

    try {
      const response = await fetch(`${API_BASE}/questions/?${queryParams}`, {
        headers: {
          'Authorization': `Bearer ${this.getAuthToken()}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const questions = await response.json();
      this.cache.set(cacheKey, questions);
      return questions;
    } catch (error) {
      console.error('Error fetching questions:', error);
      throw error;
    }
  }

  async getQuestion(id: string): Promise<Question> {
    const cacheKey = `question:${id}`;
    if (this.cache.has(cacheKey)) {
      return this.cache.get(cacheKey);
    }

    try {
      const response = await fetch(`${API_BASE}/questions/${id}`, {
        headers: {
          'Authorization': `Bearer ${this.getAuthToken()}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const question = await response.json();
      this.cache.set(cacheKey, question);
      return question;
    } catch (error) {
      console.error('Error fetching question:', error);
      throw error;
    }
  }

  async createQuestion(questionData: QuestionCreate): Promise<Question> {
    try {
      const response = await fetch(`${API_BASE}/questions/`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${this.getAuthToken()}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(questionData),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to create question');
      }

      const question = await response.json();
      this.clearCache();
      return question;
    } catch (error) {
      console.error('Error creating question:', error);
      throw error;
    }
  }

  async updateQuestion(id: string, questionData: QuestionUpdate): Promise<Question> {
    try {
      const response = await fetch(`${API_BASE}/questions/${id}`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${this.getAuthToken()}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(questionData),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to update question');
      }

      const question = await response.json();
      this.clearCache();
      return question;
    } catch (error) {
      console.error('Error updating question:', error);
      throw error;
    }
  }

  async deleteQuestion(id: string): Promise<void> {
    try {
      const response = await fetch(`${API_BASE}/questions/${id}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${this.getAuthToken()}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to delete question');
      }

      this.clearCache();
    } catch (error) {
      console.error('Error deleting question:', error);
      throw error;
    }
  }

  async validateQuestion(validationRequest: QuestionValidationRequest): Promise<QuestionValidationResponse> {
    try {
      const response = await fetch(`${API_BASE}/questions/validate`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${this.getAuthToken()}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(validationRequest),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to validate question');
      }

      return await response.json();
    } catch (error) {
      console.error('Error validating question:', error);
      throw error;
    }
  }

  async getQuestionStats(id: string): Promise<any> {
    const cacheKey = `question-stats:${id}`;
    if (this.cache.has(cacheKey)) {
      return this.cache.get(cacheKey);
    }

    try {
      const response = await fetch(`${API_BASE}/questions/stats/${id}`, {
        headers: {
          'Authorization': `Bearer ${this.getAuthToken()}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const stats = await response.json();
      this.cache.set(cacheKey, stats);
      return stats;
    } catch (error) {
      console.error('Error fetching question stats:', error);
      throw error;
    }
  }

  async updateQuestionStats(id: string, responseTimeMs: number, isCorrect: boolean): Promise<void> {
    try {
      const response = await fetch(`${API_BASE}/questions/${id}/update-stats`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${this.getAuthToken()}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          response_time_ms: responseTimeMs,
          is_correct: isCorrect,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to update question stats');
      }
    } catch (error) {
      console.error('Error updating question stats:', error);
      throw error;
    }
  }

  async getRandomQuestion(params?: {
    subject_id?: string;
    difficulty?: number;
    mode?: 'guest';
  }): Promise<Question> {
    const questions = await this.getQuestions({
      ...params,
      limit: 1,
      offset: Math.floor(Math.random() * 100), // Simple randomization
    });

    if (questions.length === 0) {
      throw new Error('No questions available');
    }

    return questions[0];
  }

  async getQuestionsBySubject(subjectId: string, limit: number = 10): Promise<Question[]> {
    return this.getQuestions({
      subject_id: subjectId,
      limit,
    });
  }

  async getQuestionsByDifficulty(difficulty: number, limit: number = 10): Promise<Question[]> {
    return this.getQuestions({
      difficulty,
      limit,
    });
  }

  // Helper methods
  private getAuthToken(): string {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('auth_token') || '';
    }
    return '';
  }

  private clearCache(): void {
    this.cache.clear();
  }

  // Validation helpers
  validateQuestionData(questionData: Partial<QuestionCreate>): string[] {
    const errors: string[] = [];

    if (!questionData.question_text?.trim()) {
      errors.push('Question text is required');
    }

    if (!questionData.options || Object.keys(questionData.options).length < 2) {
      errors.push('At least 2 options are required');
    }

    if (!questionData.correct_answer) {
      errors.push('Correct answer is required');
    }

    if (questionData.difficulty && (questionData.difficulty < 1 || questionData.difficulty > 10)) {
      errors.push('Difficulty must be between 1 and 10');
    }

    if (questionData.correct_answer && questionData.options) {
      if (!questionData.options[questionData.correct_answer]) {
        errors.push('Correct answer must be one of the available options');
      }
    }

    return errors;
  }

  validateImageUrl(url: string): boolean {
    try {
      const urlObj = new URL(url);
      return urlObj.protocol === 'http:' || urlObj.protocol === 'https:';
    } catch {
      return false;
    }
  }
}

export const questionService = QuestionService.getInstance(); 