'use client';

import { useState, useEffect, useRef } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { 
  Play, 
  Pause, 
  Clock, 
  CheckCircle, 
  XCircle, 
  AlertCircle,
  Target,
  Trophy,
  Brain,
  Lightbulb
} from 'lucide-react';

interface QuizQuestion {
  id: string;
  question_text: string;
  question_type: string;
  difficulty: number;
  correct_answer: string;
  options: Record<string, string>;
  explanation?: string;
  hint?: string;
  tags?: string[];
}

interface QuizProgress {
  quiz_id: string;
  current_question: number;
  total_questions: number;
  correct_answers: number;
  time_remaining_seconds: number;
  score_percentage: number;
}

interface QuizFeedback {
  quiz_id: string;
  overall_score: number;
  strengths: string[];
  weaknesses: string[];
  recommendations: string[];
  ai_analysis: Record<string, any>;
}

interface UnitQuizProps {
  planId: string;
  unitNumber: number;
  onQuizComplete?: (feedback: QuizFeedback) => void;
  onQuizProgress?: (progress: QuizProgress) => void;
}

interface QuizState {
  quizId: string | null;
  questions: QuizQuestion[];
  currentQuestionIndex: number;
  answers: Record<string, string>;
  isStarted: boolean;
  isCompleted: boolean;
  timeRemaining: number;
  score: number;
  feedback: QuizFeedback | null;
}

export default function UnitQuiz({ 
  planId, 
  unitNumber, 
  onQuizComplete, 
  onQuizProgress 
}: UnitQuizProps) {
  const [quizState, setQuizState] = useState<QuizState>({
    quizId: null,
    questions: [],
    currentQuestionIndex: 0,
    answers: {},
    isStarted: false,
    isCompleted: false,
    timeRemaining: 0,
    score: 0,
    feedback: null
  });

  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const timerRef = useRef<NodeJS.Timeout | null>(null);
  const startTimeRef = useRef<number>(0);

  // Generar quiz al montar el componente
  useEffect(() => {
    generateQuiz();
  }, [planId, unitNumber]);

  // Timer para el quiz
  useEffect(() => {
    if (quizState.isStarted && !quizState.isCompleted && quizState.timeRemaining > 0) {
      timerRef.current = setInterval(() => {
        setQuizState(prev => {
          const newTimeRemaining = prev.timeRemaining - 1;
          
          if (newTimeRemaining <= 0) {
            // Tiempo agotado, completar quiz
            completeQuiz();
            return prev;
          }
          
          return { ...prev, timeRemaining: newTimeRemaining };
        });
      }, 1000);
    }

    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    };
  }, [quizState.isStarted, quizState.isCompleted, quizState.timeRemaining]);

  const generateQuiz = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const unitId = `${planId}_${unitNumber}`;
      const response = await fetch(`/api/v1/quiz/unit/${unitId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          plan_id: planId,
          unit_number: unitNumber
        })
      });

      if (!response.ok) {
        throw new Error('Error generando quiz');
      }

      const quizData = await response.json();
      
      setQuizState(prev => ({
        ...prev,
        quizId: quizData.quiz_id,
        questions: quizData.questions,
        timeRemaining: quizData.time_limit_minutes * 60,
        isStarted: true
      }));

      startTimeRef.current = Date.now();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error desconocido');
    } finally {
      setIsLoading(false);
    }
  };

  const submitAnswer = async (questionId: string, answer: string) => {
    if (!quizState.quizId) return;

    try {
      const responseTime = Date.now() - startTimeRef.current;
      
      const response = await fetch(`/api/v1/quiz/${quizState.quizId}/answer`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          question_id: questionId,
          user_answer: answer,
          response_time_ms: responseTime
        })
      });

      if (!response.ok) {
        throw new Error('Error enviando respuesta');
      }

      const answerData = await response.json();
      
      // Actualizar respuestas
      setQuizState(prev => ({
        ...prev,
        answers: { ...prev.answers, [questionId]: answer },
        currentQuestionIndex: prev.currentQuestionIndex + 1
      }));

      // Actualizar progreso
      updateProgress();
      
      // Si es la última pregunta, completar quiz
      if (quizState.currentQuestionIndex + 1 >= quizState.questions.length) {
        completeQuiz();
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error enviando respuesta');
    }
  };

  const updateProgress = async () => {
    if (!quizState.quizId) return;

    try {
      const response = await fetch(`/api/v1/quiz/${quizState.quizId}/progress`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (response.ok) {
        const progress = await response.json();
        onQuizProgress?.(progress);
      }
    } catch (err) {
      console.error('Error actualizando progreso:', err);
    }
  };

  const completeQuiz = async () => {
    if (!quizState.quizId) return;

    try {
      const response = await fetch(`/api/v1/quiz/${quizState.quizId}/complete`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (!response.ok) {
        throw new Error('Error completando quiz');
      }

      const feedback = await response.json();
      
      setQuizState(prev => ({
        ...prev,
        isCompleted: true,
        feedback,
        score: feedback.overall_score
      }));

      onQuizComplete?.(feedback);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error completando quiz');
    }
  };

  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const getCurrentQuestion = () => {
    if (quizState.questions.length === 0) return null;
    return quizState.questions[quizState.currentQuestionIndex];
  };

  const getProgressPercentage = () => {
    return (quizState.currentQuestionIndex / quizState.questions.length) * 100;
  };

  const getScorePercentage = () => {
    const answered = Object.keys(quizState.answers).length;
    const correct = quizState.questions.filter((q, index) => 
      index < quizState.currentQuestionIndex && 
      quizState.answers[q.id] === q.correct_answer
    ).length;
    
    return answered > 0 ? (correct / answered) * 100 : 0;
  };

  // Extrae una URL de imagen si el valor del texto viene con formato
  // "[Imagen: /ruta/archivo.png]" o si contiene una ruta de imagen.
  const parseOptionContent = (rawValue: string | undefined): {
    text: string | null;
    imageUrl: string | null;
  } => {
    if (!rawValue) {
      return { text: null, imageUrl: null };
    }

    const trimmed = String(rawValue).trim();

    const normalizeWindowsPathToPublic = (candidate: string): string => {
      // Si parece ruta de Windows, quedarnos con el nombre de archivo y servir desde /mathimg
      if (/^[a-zA-Z]:\\/.test(candidate) || candidate.includes('\\')) {
        const parts = candidate.split(/\\|\//);
        const file = parts[parts.length - 1];
        return `/mathimg/${file}`;
      }
      // Agregar slash inicial si apunta a mathimg sin slash
      if (/^mathimg\//i.test(candidate)) {
        return `/${candidate}`;
      }
      return candidate;
    };

    // Caso 1: tokenizado con corchetes
    const bracketMatch = trimmed.match(/^\[(?:Imagen|Image)\s*:\s*(.*?)\]$/i);
    if (bracketMatch && bracketMatch[1]) {
      return { text: null, imageUrl: normalizeWindowsPathToPublic(bracketMatch[1].trim()) };
    }

    // Caso 2: el texto contiene claramente una ruta de imagen
    const urlMatch = trimmed.match(/(\/(?:mathimg|images|img)[^\s\]]*\.(?:png|jpg|jpeg|gif))/i);
    if (urlMatch && urlMatch[1]) {
      return { text: null, imageUrl: normalizeWindowsPathToPublic(urlMatch[1].trim()) };
    }

    // Caso 3: ruta de Windows o con backslashes sin corchetes
    const windowsMatch = trimmed.match(/([a-zA-Z]:\\[^\s]+\.(?:png|jpg|jpeg|gif))/);
    if (windowsMatch && windowsMatch[1]) {
      return { text: null, imageUrl: normalizeWindowsPathToPublic(windowsMatch[1].trim()) };
    }

    return { text: trimmed, imageUrl: null };
  };

  if (isLoading) {
    return (
      <Card className="w-full max-w-4xl mx-auto">
        <CardContent className="p-6">
          <div className="flex items-center justify-center space-x-2">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            <span>Generando quiz...</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className="w-full max-w-4xl mx-auto">
        <CardContent className="p-6">
          <div className="flex items-center space-x-2 text-red-600">
            <AlertCircle className="h-5 w-5" />
            <span>{error}</span>
          </div>
          <Button onClick={generateQuiz} className="mt-4">
            Reintentar
          </Button>
        </CardContent>
      </Card>
    );
  }

  if (quizState.isCompleted && quizState.feedback) {
    return (
      <Card className="w-full max-w-4xl mx-auto">
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Trophy className="h-6 w-6 text-yellow-500" />
            <span>Quiz Completado</span>
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Puntaje */}
          <div className="text-center">
            <div className="text-4xl font-bold text-blue-600">
              {quizState.feedback.overall_score.toFixed(1)}%
            </div>
            <div className="text-lg text-gray-600">
              Puntaje Final
            </div>
          </div>

          {/* Fortalezas */}
          {quizState.feedback.strengths.length > 0 && (
            <div>
              <h3 className="text-lg font-semibold flex items-center space-x-2 text-green-600">
                <CheckCircle className="h-5 w-5" />
                <span>Fortalezas</span>
              </h3>
              <ul className="mt-2 space-y-1">
                {quizState.feedback.strengths.map((strength, index) => (
                  <li key={index} className="text-green-700">• {strength}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Debilidades */}
          {quizState.feedback.weaknesses.length > 0 && (
            <div>
              <h3 className="text-lg font-semibold flex items-center space-x-2 text-red-600">
                <XCircle className="h-5 w-5" />
                <span>Áreas de Mejora</span>
              </h3>
              <ul className="mt-2 space-y-1">
                {quizState.feedback.weaknesses.map((weakness, index) => (
                  <li key={index} className="text-red-700">• {weakness}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Recomendaciones */}
          {quizState.feedback.recommendations.length > 0 && (
            <div>
              <h3 className="text-lg font-semibold flex items-center space-x-2 text-blue-600">
                <Lightbulb className="h-5 w-5" />
                <span>Recomendaciones</span>
              </h3>
              <ul className="mt-2 space-y-1">
                {quizState.feedback.recommendations.map((recommendation, index) => (
                  <li key={index} className="text-blue-700">• {recommendation}</li>
                ))}
              </ul>
            </div>
          )}

          <Button onClick={generateQuiz} className="w-full">
            Intentar Nuevamente
          </Button>
        </CardContent>
      </Card>
    );
  }

  const currentQuestion = getCurrentQuestion();
  if (!currentQuestion) {
    return (
      <Card className="w-full max-w-4xl mx-auto">
        <CardContent className="p-6">
          <div className="text-center text-gray-600">
            No hay preguntas disponibles
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="w-full max-w-4xl mx-auto">
      <CardHeader>
        <div className="flex justify-between items-center">
          <CardTitle className="flex items-center space-x-2">
            <Brain className="h-6 w-6" />
            <span>Quiz Unidad {unitNumber}</span>
          </CardTitle>
          <div className="flex items-center space-x-4">
            <Badge variant="outline" className="flex items-center space-x-1">
              <Target className="h-4 w-4" />
              <span>{quizState.currentQuestionIndex + 1}/{quizState.questions.length}</span>
            </Badge>
            <Badge variant="outline" className="flex items-center space-x-1">
              <Clock className="h-4 w-4" />
              <span>{formatTime(quizState.timeRemaining)}</span>
            </Badge>
          </div>
        </div>
        
        {/* Barra de progreso */}
        <div className="space-y-2">
          <div className="flex justify-between text-sm text-gray-600">
            <span>Progreso</span>
            <span>{getProgressPercentage().toFixed(1)}%</span>
          </div>
          <Progress value={getProgressPercentage()} className="h-2" />
        </div>
      </CardHeader>

      <CardContent className="space-y-6">
        {/* Pregunta */}
        <div className="space-y-4">
          <div className="flex items-center space-x-2">
            <Badge variant="secondary">
              Dificultad: {currentQuestion.difficulty}/10
            </Badge>
            {currentQuestion.tags && currentQuestion.tags.length > 0 && (
              <Badge variant="outline">
                {currentQuestion.tags[0]}
              </Badge>
            )}
          </div>
          
          {(() => {
            const { text, imageUrl } = parseOptionContent(currentQuestion.question_text);
            if (imageUrl) {
              return (
                <img
                  src={imageUrl}
                  alt="Pregunta"
                  className="max-w-full h-auto rounded"
                  onError={(e) => {
                    const target = e.currentTarget as HTMLImageElement;
                    target.style.display = 'none';
                  }}
                />
              );
            }
            return (
              <h3 className="text-lg font-medium">{text}</h3>
            );
          })()}

          {/* Opciones */}
          <div className="space-y-3">
            {Object.entries(currentQuestion.options).map(([key, value]) => {
              const { text, imageUrl } = parseOptionContent(value);
              return (
                <Button
                  key={key}
                  variant="outline"
                  className="w-full justify-start text-left h-auto p-4"
                  onClick={() => submitAnswer(currentQuestion.id, key)}
                  disabled={quizState.answers[currentQuestion.id] !== undefined}
                >
                  <span className="font-medium mr-2">{key}.</span>
                  {imageUrl ? (
                    <img
                      src={imageUrl}
                      alt={`Opción ${key}`}
                      className="max-w-full h-auto rounded"
                      onError={(e) => {
                        // Si falla la imagen, mostramos el texto crudo como fallback
                        const target = e.currentTarget as HTMLImageElement;
                        target.style.display = 'none';
                      }}
                    />
                  ) : (
                    <span>{text}</span>
                  )}
                </Button>
              );
            })}
          </div>

          {/* Pista */}
          {currentQuestion.hint && (
            <div className="bg-blue-50 p-4 rounded-lg">
              <div className="flex items-center space-x-2 text-blue-700">
                <Lightbulb className="h-4 w-4" />
                <span className="font-medium">Pista:</span>
              </div>
              <p className="text-blue-600 mt-1">{currentQuestion.hint}</p>
            </div>
          )}
        </div>

        {/* Puntaje actual */}
        <div className="text-center">
          <div className="text-2xl font-bold text-green-600">
            {getScorePercentage().toFixed(1)}%
          </div>
          <div className="text-sm text-gray-600">
            Puntaje Actual
          </div>
        </div>
      </CardContent>
    </Card>
  );
} 