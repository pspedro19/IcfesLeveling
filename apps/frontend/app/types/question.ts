export interface Question {
  id: string;
  topic_id: string;
  subject_id: string;
  question_text: string;
  question_type: string;
  difficulty: number;
  correct_answer: string;
  options: Record<string, string>;
  explanation?: string;
  hint?: string;
  tags?: string[];
  power_stats: Record<string, any>;
  image_url?: string;
  options_images?: Record<string, string>;
  is_validated: string;
  validation_errors: string[];
  usage_count: number;
  average_response_time: number;
  last_used_at?: string;
  created_at: string;
  updated_at: string;
}

export interface QuestionCreate {
  topic_id: string;
  subject_id: string;
  question_text: string;
  question_type?: string;
  difficulty: number;
  correct_answer: string;
  options: Record<string, string>;
  explanation?: string;
  hint?: string;
  tags?: string[];
  image_url?: string;
  options_images?: Record<string, string>;
}

export interface QuestionUpdate {
  question_text?: string;
  difficulty?: number;
  correct_answer?: string;
  options?: Record<string, string>;
  explanation?: string;
  hint?: string;
  tags?: string[];
  image_url?: string;
  options_images?: Record<string, string>;
}

export interface QuestionWithStats extends Question {
  success_rate: number;
  difficulty_rating: number;
}

export interface QuestionValidationRequest {
  question_text: string;
  options: Record<string, string>;
  correct_answer: string;
  image_url?: string;
  options_images?: Record<string, string>;
}

export interface QuestionValidationResponse {
  is_valid: boolean;
  errors: string[];
  warnings: string[];
  suggestions: string[];
}

export interface QuestionFilters {
  subject_id?: string;
  topic_id?: string;
  difficulty?: number;
  limit?: number;
  offset?: number;
  mode?: 'guest';
}

export interface QuestionStats {
  usage_count: number;
  success_rate: number;
  average_response_time: number;
  difficulty_rating: number;
  last_used_at?: string;
}

export interface QuestionPerformance {
  question_id: string;
  is_correct: boolean;
  response_time_ms: number;
  user_answer: string;
  correct_answer: string;
  timestamp: string;
}

export interface QuestionBatch {
  questions: Question[];
  total_count: number;
  has_more: boolean;
  next_offset: number;
}

export interface QuestionSearchParams {
  query?: string;
  subjects?: string[];
  topics?: string[];
  difficulty_range?: [number, number];
  tags?: string[];
  validated_only?: boolean;
  limit?: number;
  offset?: number;
}

export interface QuestionAnalytics {
  total_questions: number;
  questions_by_subject: Record<string, number>;
  questions_by_difficulty: Record<number, number>;
  average_difficulty: number;
  validation_status: {
    pending: number;
    validated: number;
    rejected: number;
  };
  usage_stats: {
    most_used: Question[];
    least_used: Question[];
    highest_success_rate: Question[];
    lowest_success_rate: Question[];
  };
} 