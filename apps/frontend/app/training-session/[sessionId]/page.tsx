'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { 
  Clock, 
  CheckCircle, 
  XCircle, 
  Brain, 
  Lightbulb, 
  Video, 
  Star,
  Timer,
  Target,
  TrendingUp,
  ArrowRight,
  RotateCcw,
  Zap
} from "lucide-react";

interface Question {
  training_question_id: string;
  question_id: string;
  statement: string;
  options: {
    a: string;
    b: string;
    c: string;
    d: string;
  };
  image_url?: string;
  difficulty: string;
  topic_id?: string;
  original_failure_info: {
    original_answer: string;
    original_time_seconds: number;
    failure_date: string;
  };
  training_info: {
    attempts: number;
    successful_attempts: number;
    consecutive_correct: number;
    next_review_date: string;
    priority_level: number;
    best_time?: number;
  };
}

interface SessionData {
  session_id: string;
  mode: string;
  target_questions: number;
  questions_answered: number;
  correct_answers: number;
  accuracy: number;
  current_streak: number;
  max_streak: number;
  time_limit_minutes: number;
  started_at: string;
  completed_at?: string;
}

interface VideoRecommendation {
  id: string;
  youtube_id: string;
  title: string;
  thumbnail_url: string;
  duration_seconds: number;
  relevance_score: number;
  embed_url: string;
}

export default function TrainingSessionPage() {
  const params = useParams();
  const router = useRouter();
  const sessionId = params.sessionId as string;

  const [sessionData, setSessionData] = useState<SessionData | null>(null);
  const [currentQuestion, setCurrentQuestion] = useState<Question | null>(null);
  const [questionIndex, setQuestionIndex] = useState(0);
  const [selectedAnswer, setSelectedAnswer] = useState<string>('');
  const [submitted, setSubmitted] = useState(false);
  const [isCorrect, setIsCorrect] = useState(false);
  const [timeRemaining, setTimeRemaining] = useState(0);
  const [questionStartTime, setQuestionStartTime] = useState(Date.now());
  const [loading, setLoading] = useState(true);
  const [showExplanation, setShowExplanation] = useState(false);
  const [explanation, setExplanation] = useState<string>('');
  const [videoRecommendations, setVideoRecommendations] = useState<VideoRecommendation[]>([]);
  const [confidenceLevel, setConfidenceLevel] = useState(3);

  useEffect(() => {
    if (sessionId) {
      loadSession();
    }
  }, [sessionId]);

  useEffect(() => {
    if (sessionData && timeRemaining > 0) {
      const timer = setInterval(() => {
        setTimeRemaining(prev => Math.max(0, prev - 1));
      }, 1000);
      return () => clearInterval(timer);
    }
  }, [sessionData, timeRemaining]);

  const loadSession = async () => {
    try {
      const response = await fetch(`/api/v1/training-zone/session/${sessionId}/status`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (!response.ok) {
        throw new Error('Error al cargar la sesión');
      }

      const data = await response.json();
      setSessionData(data.session);
      
      if (data.session.status === 'completed') {
        router.push(`/training-session/${sessionId}/results`);
        return;
      }

      // Calculate time remaining
      const sessionDuration = data.session.time_limit_minutes * 60; // seconds
      const elapsed = Math.floor((Date.now() - new Date(data.session.started_at).getTime()) / 1000);
      setTimeRemaining(Math.max(0, sessionDuration - elapsed));

      // Load next question (this would come from the session start response)
      await loadNextQuestion();
      
      setLoading(false);
    } catch (error) {
      console.error('Error loading session:', error);
      setLoading(false);
    }
  };

  const loadNextQuestion = async () => {
    try {
      const response = await fetch(`/api/v1/training-zone/session/${sessionId}/next-question`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (!response.ok) {
        const errorData = await response.json();
        if (errorData.detail?.includes('Session completed') || errorData.detail?.includes('No more questions')) {
          // Session is complete, redirect to results
          router.push(`/training-session/${sessionId}/results`);
          return;
        }
        throw new Error('Error al cargar la siguiente pregunta');
      }

      const data = await response.json();
      setCurrentQuestion(data.question);
      
      // Update session progress if provided
      if (data.session_progress) {
        setQuestionIndex(data.session_progress.current - 1);
      }
      
    } catch (error) {
      console.error('Error loading next question:', error);
      // Fallback to demo question
      setCurrentQuestion({
        training_question_id: 'tq1',
        question_id: 'q1',
        statement: '¿Cuál es la derivada de f(x) = x²?',
        options: {
          a: '2x',
          b: 'x',
          c: '2',
          d: 'x²'
        },
        difficulty: 'medium',
        original_failure_info: {
          original_answer: 'b',
          original_time_seconds: 45,
          failure_date: '2024-01-15T10:00:00Z'
        },
        training_info: {
          attempts: 2,
          successful_attempts: 1,
          consecutive_correct: 0,
          next_review_date: '2024-01-20T10:00:00Z',
          priority_level: 4,
          best_time: 30
        }
      });
    }
    
    setSubmitted(false);
    setSelectedAnswer('');
    setShowExplanation(false);
    setQuestionStartTime(Date.now());
  };

  const submitAnswer = async () => {
    if (!selectedAnswer || !currentQuestion) return;

    const responseTime = Math.floor((Date.now() - questionStartTime) / 1000);
    
    try {
      const response = await fetch(`/api/v1/training-zone/session/${sessionId}/answer`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          question_id: currentQuestion.question_id,
          user_answer: selectedAnswer,
          response_time_seconds: responseTime,
          confidence_level: confidenceLevel
        })
      });

      if (!response.ok) {
        throw new Error('Error al enviar respuesta');
      }

      const result = await response.json();
      setIsCorrect(result.is_correct);
      setSubmitted(true);

      // Update session data
      if (sessionData) {
        setSessionData(prev => prev ? {
          ...prev,
          questions_answered: result.session_progress.answered,
          correct_answers: result.session_progress.correct,
          accuracy: result.session_accuracy,
          current_streak: result.current_streak
        } : null);
      }

      // Load video recommendations if answer was incorrect
      if (!result.is_correct && result.video_recommendations) {
        setVideoRecommendations(result.video_recommendations);
      }

    } catch (error) {
      console.error('Error submitting answer:', error);
    }
  };

  const getAIExplanation = async () => {
    if (!currentQuestion) return;

    try {
      // This would be the training attempt ID from the submit response
      const trainingAttemptId = 'ta1'; 
      
      const response = await fetch(`/api/v1/training-zone/explanation/${trainingAttemptId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          explanation_type: 'conceptual'
        })
      });

      if (!response.ok) {
        throw new Error('Error al obtener explicación');
      }

      const result = await response.json();
      setExplanation(result.explanation);
      setShowExplanation(true);
    } catch (error) {
      console.error('Error getting AI explanation:', error);
    }
  };

  const nextQuestion = () => {
    if (sessionData && questionIndex + 1 >= sessionData.target_questions) {
      // Session complete
      completeSession();
    } else {
      setQuestionIndex(prev => prev + 1);
      loadNextQuestion();
    }
  };

  const completeSession = async () => {
    try {
      const response = await fetch(`/api/v1/training-zone/session/${sessionId}/complete`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (!response.ok) {
        throw new Error('Error al completar sesión');
      }

      router.push(`/training-session/${sessionId}/results`);
    } catch (error) {
      console.error('Error completing session:', error);
    }
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty) {
      case 'easy': return 'bg-green-100 text-green-800';
      case 'medium': return 'bg-yellow-100 text-yellow-800';
      case 'hard': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!sessionData || !currentQuestion) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center">
        <Card className="max-w-md">
          <CardContent className="p-6 text-center">
            <p className="text-gray-600">Error al cargar la sesión de entrenamiento</p>
            <Button onClick={() => router.push('/training-zone')} className="mt-4">
              Volver al Training Zone
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-4xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Badge className="bg-blue-100 text-blue-800">
                {sessionData.mode}
              </Badge>
              <div className="text-sm text-gray-600">
                Pregunta {questionIndex + 1} de {sessionData.target_questions}
              </div>
            </div>
            
            <div className="flex items-center gap-6">
              <div className="flex items-center gap-2">
                <Timer className="h-4 w-4 text-gray-500" />
                <span className={`text-sm font-medium ${timeRemaining < 300 ? 'text-red-600' : 'text-gray-700'}`}>
                  {formatTime(timeRemaining)}
                </span>
              </div>
              
              <div className="flex items-center gap-2">
                <Target className="h-4 w-4 text-green-500" />
                <span className="text-sm font-medium text-gray-700">
                  {sessionData.correct_answers}/{sessionData.questions_answered}
                </span>
              </div>
              
              <div className="flex items-center gap-2">
                <Zap className="h-4 w-4 text-purple-500" />
                <span className="text-sm font-medium text-gray-700">
                  Racha: {sessionData.current_streak}
                </span>
              </div>
            </div>
          </div>
          
          <div className="mt-4">
            <Progress 
              value={(questionIndex + 1) / sessionData.target_questions * 100} 
              className="h-2"
            />
          </div>
        </div>
      </div>

      <div className="max-w-4xl mx-auto p-6">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Question Area */}
          <div className="lg:col-span-2 space-y-6">
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle>Pregunta de Entrenamiento</CardTitle>
                  <div className="flex items-center gap-2">
                    <Badge className={getDifficultyColor(currentQuestion.difficulty)}>
                      {currentQuestion.difficulty}
                    </Badge>
                    <Badge variant="outline">
                      Prioridad: {currentQuestion.training_info.priority_level}/5
                    </Badge>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="text-lg leading-relaxed">
                  {currentQuestion.statement}
                </div>
                
                {currentQuestion.image_url && (
                  <div className="flex justify-center">
                    <img 
                      src={currentQuestion.image_url} 
                      alt="Imagen de la pregunta"
                      className="max-w-full h-auto rounded-lg shadow-sm"
                    />
                  </div>
                )}
                
                <div className="space-y-3">
                  {Object.entries(currentQuestion.options).map(([key, value]) => (
                    <label
                      key={key}
                      className={`flex items-center p-4 border rounded-lg cursor-pointer transition-colors ${
                        selectedAnswer === key
                          ? 'border-blue-500 bg-blue-50'
                          : 'border-gray-200 hover:border-gray-300'
                      } ${
                        submitted
                          ? key === 'a' // Assuming 'a' is correct for demo
                            ? 'border-green-500 bg-green-50'
                            : selectedAnswer === key && key !== 'a'
                            ? 'border-red-500 bg-red-50'
                            : 'opacity-50'
                          : ''
                      }`}
                    >
                      <input
                        type="radio"
                        name="answer"
                        value={key}
                        checked={selectedAnswer === key}
                        onChange={(e) => setSelectedAnswer(e.target.value)}
                        disabled={submitted}
                        className="mr-3"
                      />
                      <span className="font-medium mr-2">{key.toUpperCase()})</span>
                      <span>{value}</span>
                    </label>
                  ))}
                </div>
                
                {!submitted && (
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Nivel de Confianza (1-5):
                      </label>
                      <div className="flex gap-2">
                        {[1, 2, 3, 4, 5].map((level) => (
                          <button
                            key={level}
                            onClick={() => setConfidenceLevel(level)}
                            className={`w-10 h-10 rounded-full border-2 transition-colors ${
                              confidenceLevel === level
                                ? 'border-blue-500 bg-blue-500 text-white'
                                : 'border-gray-300 hover:border-gray-400'
                            }`}
                          >
                            {level}
                          </button>
                        ))}
                      </div>
                    </div>
                    
                    <Button
                      onClick={submitAnswer}
                      disabled={!selectedAnswer}
                      className="w-full"
                    >
                      Enviar Respuesta
                    </Button>
                  </div>
                )}
                
                {submitted && (
                  <div className="space-y-4">
                    <div className={`p-4 rounded-lg ${
                      isCorrect ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'
                    }`}>
                      <div className="flex items-center gap-2 mb-2">
                        {isCorrect ? (
                          <CheckCircle className="h-5 w-5 text-green-600" />
                        ) : (
                          <XCircle className="h-5 w-5 text-red-600" />
                        )}
                        <span className={`font-medium ${
                          isCorrect ? 'text-green-800' : 'text-red-800'
                        }`}>
                          {isCorrect ? '¡Correcto!' : 'Incorrecto'}
                        </span>
                      </div>
                      {!isCorrect && (
                        <p className="text-sm text-gray-700">
                          La respuesta correcta es: <strong>A</strong>
                        </p>
                      )}
                    </div>
                    
                    <div className="flex gap-3">
                      {!isCorrect && (
                        <Button
                          onClick={getAIExplanation}
                          variant="outline"
                          className="flex-1"
                        >
                          <Lightbulb className="h-4 w-4 mr-2" />
                          Explicación IA
                        </Button>
                      )}
                      
                      <Button
                        onClick={nextQuestion}
                        className="flex-1"
                      >
                        {questionIndex + 1 >= sessionData.target_questions ? 'Finalizar' : 'Siguiente'}
                        <ArrowRight className="h-4 w-4 ml-2" />
                      </Button>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
            
            {/* AI Explanation */}
            {showExplanation && explanation && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Brain className="h-5 w-5" />
                    Explicación IA
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="prose prose-sm max-w-none">
                    <p>{explanation}</p>
                  </div>
                </CardContent>
              </Card>
            )}
            
            {/* Video Recommendations */}
            {videoRecommendations.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Video className="h-5 w-5" />
                    Videos Recomendados
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid gap-4">
                    {videoRecommendations.map((video) => (
                      <div key={video.id} className="flex gap-4 p-3 border rounded-lg">
                        <img
                          src={video.thumbnail_url}
                          alt={video.title}
                          className="w-24 h-16 object-cover rounded"
                        />
                        <div className="flex-1">
                          <h4 className="font-medium text-sm">{video.title}</h4>
                          <p className="text-xs text-gray-500 mt-1">
                            {Math.floor(video.duration_seconds / 60)}:{(video.duration_seconds % 60).toString().padStart(2, '0')} min
                          </p>
                          <div className="flex items-center gap-1 mt-1">
                            <Star className="h-3 w-3 text-yellow-500" />
                            <span className="text-xs text-gray-600">
                              {(video.relevance_score * 100).toFixed(0)}% relevante
                            </span>
                          </div>
                        </div>
                        <Button size="sm" variant="outline">
                          Ver
                        </Button>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Progress Stats */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Progreso de Sesión</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="text-center">
                  <div className="text-2xl font-bold text-blue-600">
                    {((sessionData.questions_answered / sessionData.target_questions) * 100).toFixed(0)}%
                  </div>
                  <div className="text-sm text-gray-600">Completado</div>
                </div>
                
                <div className="space-y-3">
                  <div className="flex justify-between text-sm">
                    <span>Precisión:</span>
                    <span className="font-medium">{(sessionData.accuracy * 100).toFixed(1)}%</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span>Racha actual:</span>
                    <span className="font-medium">{sessionData.current_streak}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span>Mejor racha:</span>
                    <span className="font-medium">{sessionData.max_streak}</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Question History */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Historial de Esta Pregunta</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="text-sm space-y-2">
                  <div className="flex justify-between">
                    <span>Intentos anteriores:</span>
                    <span className="font-medium">{currentQuestion.training_info.attempts}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Respuestas correctas:</span>
                    <span className="font-medium">{currentQuestion.training_info.successful_attempts}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Racha actual:</span>
                    <span className="font-medium">{currentQuestion.training_info.consecutive_correct}</span>
                  </div>
                  {currentQuestion.training_info.best_time && (
                    <div className="flex justify-between">
                      <span>Mejor tiempo:</span>
                      <span className="font-medium">{currentQuestion.training_info.best_time}s</span>
                    </div>
                  )}
                </div>
                
                <div className="pt-3 border-t">
                  <div className="text-xs text-gray-600 mb-1">Fallo original:</div>
                  <div className="text-sm">
                    <div>Respuesta: {currentQuestion.original_failure_info.original_answer.toUpperCase()}</div>
                    <div>Tiempo: {currentQuestion.original_failure_info.original_time_seconds}s</div>
                    <div>Fecha: {new Date(currentQuestion.original_failure_info.failure_date).toLocaleDateString()}</div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Next Review */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg flex items-center gap-2">
                  <RotateCcw className="h-4 w-4" />
                  Próxima Revisión
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-center">
                  <div className="text-sm text-gray-600">
                    {new Date(currentQuestion.training_info.next_review_date).toLocaleDateString()}
                  </div>
                  <div className="text-xs text-gray-500 mt-1">
                    Repetición espaciada
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}