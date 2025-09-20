'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import { getImageUrl } from '../../lib/config';
import { 
  Clock, 
  ChevronLeft, 
  ChevronRight, 
  Check, 
  X,
  AlertCircle,
  Send,
  BookOpen,
  Target,
  Shield,
  Zap
} from 'lucide-react';

interface Question {
  id: string;
  question_text: string;
  pregunta_texto?: string;
  options?: Record<string, string>;
  option_images?: Record<string, string>;
  opcion_a_texto?: string;
  opcion_b_texto?: string;
  opcion_c_texto?: string;
  opcion_d_texto?: string;
  difficulty: number;
  hint?: string;
  topic?: string | { name: string; description?: string; subject_id?: string; };
  image_url?: string;
  pregunta_imagen?: string;
  opcion_a_imagen?: string;
  opcion_b_imagen?: string;
  opcion_c_imagen?: string;
  opcion_d_imagen?: string;
  correct_answer?: string;
  subject_id?: string;
  explicacion_respuesta?: string;
  error_comun?: string;
}

interface TestAnswer {
  question_id: string;
  user_answer: string;
  response_time_ms: number;
}

interface DiagnosticTestInterfaceProps {
  subjectId: string;
  subjectName: string;
  testId?: string;
  onComplete?: (results: any) => void;
}

export default function DiagnosticTestInterface({ 
  subjectId, 
  subjectName, 
  testId,
  onComplete 
}: DiagnosticTestInterfaceProps) {
  const router = useRouter();
  
  // State management
  const [questions, setQuestions] = useState<Question[]>([]);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [answers, setAnswers] = useState<{ [key: string]: string }>({});
  const [questionStartTime, setQuestionStartTime] = useState<{ [key: string]: number }>({});
  const [responseTimes, setResponseTimes] = useState<{ [key: string]: number }>({});
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showHint, setShowHint] = useState(false);
  const [hintsUsed, setHintsUsed] = useState<{ [questionId: string]: number[] }>({});
  const [currentHintLevel, setCurrentHintLevel] = useState<{ [questionId: string]: number }>({});
  const [hintText, setHintText] = useState<string>('');
  const [loadingHint, setLoadingHint] = useState(false);
  const [timeLeft, setTimeLeft] = useState(90 * 60); // 90 minutes
  const [testStartTime] = useState(Date.now());
  const [currentTestId, setCurrentTestId] = useState<string | null>(testId || null);
  
  // Explanation state
  const [questionFeedback, setQuestionFeedback] = useState<{ [key: string]: any }>({});
  const [showExplanation, setShowExplanation] = useState<{ [key: string]: boolean }>({});

  const loadQuestions = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:4000';
      
      // Use the new diagnostic-questions endpoint
      const endpoint = `${API_URL}/api/v1/diagnostic-public/diagnostic-questions/${subjectId}?limit=20`;
      
      console.log('Loading questions from:', endpoint);
      const questionsResponse = await fetch(endpoint, {
        headers: {
          'Content-Type': 'application/json'
        }
      });
      
      if (questionsResponse.ok) {
        const data = await questionsResponse.json();
        console.log(`Loaded ${data.length} questions successfully:`, data);
        setQuestions(data);
        
        // Set a dummy test ID for tracking
        if (!currentTestId) {
          setCurrentTestId(`diagnostic-test-${subjectId}-${Date.now()}`);
        }
      } else {
        const errorText = await questionsResponse.text();
        console.error('API Error:', errorText);
        throw new Error('No se pudieron cargar las preguntas desde la base de datos');
      }
    } catch (err) {
      console.error('Error loading questions:', err);
      setError(err instanceof Error ? err.message : 'Error desconocido al cargar preguntas');
    } finally {
      setLoading(false);
    }
  }, [subjectId, currentTestId]);

  // Load questions on mount
  useEffect(() => {
    loadQuestions();
  }, [loadQuestions]);

  // Timer countdown
  useEffect(() => {
    if (questions.length > 0 && timeLeft > 0) {
      const timer = setInterval(() => {
        setTimeLeft(prev => {
          if (prev <= 1) {
            // Auto-submit when time runs out
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
      return () => clearInterval(timer);
    }
  }, [questions.length, timeLeft]);

  // Track time when question changes
  useEffect(() => {
    if (questions.length > 0) {
      const currentQuestion = questions[currentQuestionIndex];
      if (currentQuestion && !questionStartTime[currentQuestion.id]) {
        setQuestionStartTime(prev => ({
          ...prev,
          [currentQuestion.id]: Date.now()
        }));
      }
    }
  }, [currentQuestionIndex, questions, questionStartTime]);

  // Request a progressive hint for the current question
  const requestHint = async () => {
    if (!currentTestId || !questions[currentQuestionIndex]) {
      return;
    }

    const currentQuestion = questions[currentQuestionIndex];
    const questionId = currentQuestion.id;
    
    // Determine the next hint level to request
    const usedHints = hintsUsed[questionId] || [];
    let nextLevel = 1;
    
    if (usedHints.includes(1) && usedHints.includes(2) && usedHints.includes(3)) {
      // All hints already used
      setHintText('Ya has usado todas las pistas disponibles para esta pregunta.');
      setShowHint(true);
      return;
    }
    
    if (usedHints.includes(1)) nextLevel = 2;
    if (usedHints.includes(2)) nextLevel = 3;
    
    setLoadingHint(true);
    
    try {
      const response = await fetch(`/api/diagnostic-public/tests/${currentTestId}/questions/${questionId}/hint?hint_level=${nextLevel}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        }
      });
      
      if (!response.ok) {
        throw new Error('Error al solicitar la pista');
      }
      
      const data = await response.json();
      
      if (data.success) {
        // Update hints used tracking
        setHintsUsed(prev => ({
          ...prev,
          [questionId]: [...(prev[questionId] || []), nextLevel]
        }));
        
        setCurrentHintLevel(prev => ({
          ...prev,
          [questionId]: nextLevel
        }));
        
        setHintText(data.hint);
        setShowHint(true);
      } else {
        setHintText('No se pudo obtener la pista para esta pregunta.');
        setShowHint(true);
      }
      
    } catch (error) {
      console.error('Error requesting hint:', error);
      setHintText('Error al solicitar la pista. Intenta de nuevo.');
      setShowHint(true);
    } finally {
      setLoadingHint(false);
    }
  };

  const handleAnswer = async (answer: string) => {
    const currentQuestion = questions[currentQuestionIndex];
    
    // Record answer
    setAnswers(prev => ({
      ...prev,
      [currentQuestion.id]: answer
    }));

    // Record response time
    const startTime = questionStartTime[currentQuestion.id] || testStartTime;
    const responseTime = Date.now() - startTime;
    setResponseTimes(prev => ({
      ...prev,
      [currentQuestion.id]: responseTime
    }));

    // Submit answer to database immediately
    try {
      const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:4000';
      const submitResponse = await fetch(`${API_URL}/api/v1/diagnostic-public/diagnostic-questions/submit-answer`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          question_id: currentQuestion.id,
          user_answer: answer,
          response_time_ms: responseTime,
          test_id: currentTestId
        })
      });
      
      if (submitResponse.ok) {
        const result = await submitResponse.json();
        console.log('Answer submitted successfully:', result);
        
        // Store the feedback for this question
        setQuestionFeedback(prev => ({
          ...prev,
          [currentQuestion.id]: result
        }));
        
        // Show explanation automatically after answering
        setShowExplanation(prev => ({
          ...prev,
          [currentQuestion.id]: true
        }));
      } else {
        console.error('Failed to submit answer:', await submitResponse.text());
      }
    } catch (err) {
      console.error('Error submitting answer:', err);
    }
  };

  const handleNext = () => {
    if (currentQuestionIndex < questions.length - 1) {
      setCurrentQuestionIndex(prev => prev + 1);
      setShowHint(false);
    }
  };

  const handlePrevious = () => {
    if (currentQuestionIndex > 0) {
      setCurrentQuestionIndex(prev => prev - 1);
      setShowHint(false);
    }
  };

  const handleJumpToQuestion = (index: number) => {
    setCurrentQuestionIndex(index);
    setShowHint(false);
  };

  const handleSubmit = useCallback(async () => {
    if (submitting) return;
    
    setSubmitting(true);
    setError(null);

    try {
      const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:4001';
      const token = localStorage.getItem('access_token') || localStorage.getItem('token');

      // Prepare answers for submission
      const testAnswers: TestAnswer[] = questions.map(q => ({
        question_id: q.id,
        user_answer: answers[q.id] || '',
        response_time_ms: responseTimes[q.id] || 0
      }));

      // Calculate results based on actual correct answers from database
        const correctCount = questions.filter(q => 
          answers[q.id] === (q.correct_answer || 'A').toUpperCase()
        ).length;

        const results = {
          score: correctCount,
          percentage: Math.round((correctCount / questions.length) * 100),
          total_questions: questions.length,
          correct_answers: correctCount,
          time_spent: Math.floor((Date.now() - testStartTime) / 1000),
          subject: subjectName,
        subject_id: subjectId,
        test_id: currentTestId,
        answered_questions: Object.keys(answers).length,
        rank: correctCount >= 18 ? 'S' : 
              correctCount >= 15 ? 'A' :
              correctCount >= 12 ? 'B' :
              correctCount >= 8 ? 'C' :
              correctCount >= 5 ? 'D' : 'E',
        message: correctCount >= 15 ? 
          '¡Excelente! Has demostrado un dominio sólido del tema.' :
          correctCount >= 10 ?
          'Buen trabajo. Con un poco más de práctica mejorarás.' :
          'Necesitas reforzar algunos conceptos. ¡Sigue practicando!'
        };

        sessionStorage.setItem('diagnostic_results', JSON.stringify(results));
      
      // Navigate to the new comprehensive results dashboard
        router.push(`/diagnostic-results/${currentTestId}`);
    } catch (err) {
      console.error('Error submitting test:', err);
      setError('Error al enviar el test. Por favor intenta de nuevo.');
    } finally {
      setSubmitting(false);
    }
  }, [submitting, questions, answers, responseTimes, testStartTime, currentTestId, subjectName, subjectId, router]);

  // Auto-submit when time runs out
  useEffect(() => {
    if (timeLeft === 0 && questions.length > 0) {
      handleSubmit();
    }
  }, [timeLeft, questions.length, handleSubmit]);

  const formatTime = (seconds: number) => {
    const hours = Math.floor(seconds / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    
    if (hours > 0) {
      return `${hours}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const getDifficultyColor = (difficulty: number) => {
    if (difficulty <= 2) return 'text-green-400';
    if (difficulty <= 3) return 'text-yellow-400';
    return 'text-red-400';
  };

  const getProgressPercentage = () => {
    const answered = Object.keys(answers).length;
    return (answered / questions.length) * 100;
  };

  // Loading state
  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-900 via-black to-blue-900 flex items-center justify-center">
        <motion.div
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          className="text-center"
        >
          <div className="animate-spin rounded-full h-16 w-16 border-t-4 border-purple-500 mx-auto mb-4"></div>
          <p className="text-white text-xl">Cargando test de {subjectName}...</p>
          <p className="text-purple-300 text-sm mt-2">Preparando {questions.length || '...'} preguntas</p>
        </motion.div>
      </div>
    );
  }

  // Error state
  if (error || questions.length === 0) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-red-900 via-black to-purple-900 flex items-center justify-center">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-black/50 backdrop-blur-xl p-8 rounded-2xl border border-red-500/30 text-center max-w-md"
        >
          <X className="w-16 h-16 text-red-500 mx-auto mb-4" />
          <h2 className="text-red-400 text-2xl mb-4">Error</h2>
          <p className="text-red-300 mb-6">{error || 'No hay preguntas disponibles'}</p>
          <button
            onClick={() => router.push('/diagnostic-test')}
            className="px-6 py-3 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors"
          >
            Volver
          </button>
        </motion.div>
      </div>
    );
  }

  const currentQuestion = questions[currentQuestionIndex];
  
  // Check if current question exists
  if (!currentQuestion) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-red-900 via-black to-purple-900 flex items-center justify-center">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-black/50 backdrop-blur-xl p-8 rounded-2xl border border-red-500/30 text-center max-w-md"
        >
          <X className="w-16 h-16 text-red-500 mx-auto mb-4" />
          <h2 className="text-red-400 text-2xl mb-4">Error</h2>
          <p className="text-red-300 mb-6">Pregunta no encontrada</p>
          <button
            onClick={() => router.push('/diagnostic-test')}
            className="px-6 py-3 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors"
          >
            Volver
          </button>
        </motion.div>
      </div>
    );
  }
  
  const questionText = currentQuestion.pregunta_texto || currentQuestion.question_text;
  // Solo usar imagen si existe y no es una cadena inválida
  const questionImageUrl = getImageUrl(currentQuestion.pregunta_imagen || currentQuestion.image_url || '');
  
  // Get options from the properly formatted API response
  const optionsData = currentQuestion.options || {};
  const optionImages = currentQuestion.option_images || {};
  
  // Create options array with both text and images
  const options = ['A', 'B', 'C', 'D'].map(key => {
    const imageField = optionImages[key] || currentQuestion[`opcion_${key.toLowerCase()}_imagen`];
    const textField = optionsData[key] || currentQuestion[`opcion_${key.toLowerCase()}_texto`];
    
    return {
      letter: key,
      text: textField || '',
      image: getImageUrl(imageField || '')
    };
  });

  // Asegurar que siempre haya opciones válidas - fallback de emergencia
  const validOptions = options.filter(option => {
    const hasText = option.text && option.text.trim() !== '' && option.text !== `Opción ${option.letter}`;
    const hasImage = option.image && option.image.trim() !== '';
    return hasText || hasImage;
  });

  // Si no hay opciones válidas, crear opciones por defecto
  const finalOptions = validOptions.length >= 2 ? validOptions : [
    { letter: 'A', text: 'Opción A', image: '' },
    { letter: 'B', text: 'Opción B', image: '' },
    { letter: 'C', text: 'Opción C', image: '' },
    { letter: 'D', text: 'Opción D', image: '' },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-black to-blue-900">
      <div className="flex h-screen">
        {/* Left Sidebar - Question Matrix */}
        <div className="w-80 bg-black/40 backdrop-blur-xl border-r border-purple-500/30 p-6 overflow-y-auto">
          {/* Header */}
          <div className="mb-6">
            <h2 className="text-2xl font-bold text-yellow-400 mb-2">
              {subjectName}
            </h2>
            <div className="flex items-center gap-2 text-purple-300">
              <Clock className="w-4 h-4" />
              <span className="font-mono">{formatTime(timeLeft)}</span>
            </div>
          </div>

          {/* Progress */}
          <div className="mb-6">
            <div className="flex justify-between text-sm text-purple-300 mb-2">
              <span>Progreso</span>
              <span>{Object.keys(answers).length}/{questions.length}</span>
            </div>
            <div className="w-full bg-black/50 rounded-full h-2">
              <motion.div
                className="bg-gradient-to-r from-purple-500 to-blue-500 h-2 rounded-full"
                initial={{ width: 0 }}
                animate={{ width: `${getProgressPercentage()}%` }}
                transition={{ duration: 0.3 }}
              />
            </div>
          </div>

          {/* Question Grid */}
          <div className="grid grid-cols-5 gap-2">
            {questions.map((q, index) => {
              const isAnswered = !!answers[q.id];
              const isCurrent = index === currentQuestionIndex;
              
              return (
                <motion.button
                  key={q.id}
                  whileHover={{ scale: 1.1 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={() => handleJumpToQuestion(index)}
                  className={`
                    relative w-12 h-12 rounded-lg font-bold text-sm
                    transition-all duration-200
                    ${isCurrent 
                      ? 'bg-purple-600 text-white ring-2 ring-purple-400 shadow-lg shadow-purple-500/50' 
                      : isAnswered
                      ? 'bg-green-600/30 text-green-400 border border-green-500/30'
                      : 'bg-black/50 text-gray-400 border border-gray-700 hover:border-purple-500'
                    }
                  `}
                >
                  {index + 1}
                  {isAnswered && (
                    <Check className="absolute -top-1 -right-1 w-4 h-4 text-green-400" />
                  )}
                </motion.button>
              );
            })}
          </div>

          {/* Legend */}
          <div className="mt-6 space-y-2 text-sm">
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 bg-purple-600 rounded"></div>
              <span className="text-purple-300">Pregunta actual</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 bg-green-600/30 border border-green-500/30 rounded"></div>
              <span className="text-purple-300">Respondida</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 bg-black/50 border border-gray-700 rounded"></div>
              <span className="text-purple-300">Sin responder</span>
            </div>
          </div>

          {/* Submit Button */}
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={handleSubmit}
            disabled={submitting || Object.keys(answers).length === 0}
            className={`
              mt-8 w-full py-4 rounded-xl font-bold text-lg
              transition-all duration-300 flex items-center justify-center gap-2
              ${Object.keys(answers).length === questions.length
                ? 'bg-gradient-to-r from-green-600 to-emerald-600 text-white shadow-lg shadow-green-500/30'
                : Object.keys(answers).length > 0
                ? 'bg-gradient-to-r from-yellow-600 to-orange-600 text-white'
                : 'bg-gray-700 text-gray-400 cursor-not-allowed'
              }
            `}
          >
            {submitting ? (
              <>
                <div className="animate-spin rounded-full h-5 w-5 border-t-2 border-white"></div>
                Enviando...
              </>
            ) : (
              <>
                <Send className="w-5 h-5" />
                {Object.keys(answers).length === questions.length 
                  ? 'Enviar Test Completo'
                  : `Enviar (${Object.keys(answers).length}/${questions.length})`
                }
              </>
            )}
          </motion.button>
        </div>

        {/* Right Side - Question Content */}
        <div className="flex-1 flex flex-col">
          {/* Question Header */}
          <div className="bg-black/30 backdrop-blur-lg border-b border-purple-500/30 p-6">
            <div className="max-w-4xl mx-auto flex justify-between items-center">
              <div>
                <div className="flex items-center gap-3 mb-2">
                  <span className="text-3xl font-bold text-yellow-400">
                    Pregunta {currentQuestionIndex + 1}
                  </span>
                  <span className={`text-sm font-medium ${getDifficultyColor(currentQuestion.difficulty)}`}>
                    {currentQuestion.difficulty <= 2 ? '⭐ Fácil' :
                     currentQuestion.difficulty <= 3 ? '⭐⭐ Medio' :
                     '⭐⭐⭐ Difícil'}
                  </span>
                </div>
                {currentQuestion.topic && (
                  <span className="text-purple-300 text-sm">
                    Tema: {typeof currentQuestion.topic === 'string' ? currentQuestion.topic : currentQuestion.topic.name || 'General'}
                  </span>
                )}
              </div>
              
              <div className="flex gap-2">
                <button
                  onClick={requestHint}
                  disabled={loadingHint}
                  className="px-4 py-2 bg-yellow-600/20 text-yellow-400 rounded-lg hover:bg-yellow-600/30 transition-colors flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <AlertCircle className="w-4 h-4" />
                  {loadingHint ? 'Solicitando...' : 'Solicitar Pista'}
                </button>
                
                {/* Hint level indicator */}
                {currentQuestion && hintsUsed[currentQuestion.id] && hintsUsed[currentQuestion.id].length > 0 && (
                  <div className="px-3 py-2 bg-purple-600/20 text-purple-400 rounded-lg text-sm flex items-center gap-1">
                    <span>Pistas usadas: {hintsUsed[currentQuestion.id].length}/3</span>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Question Content */}
          <div className="flex-1 overflow-y-auto p-8">
            <div className="max-w-4xl mx-auto">
              {/* Question Text */}
              <motion.div
                key={currentQuestion.id}
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.3 }}
                className="mb-8"
              >
                <h3 className="text-2xl text-white mb-4 leading-relaxed">
                  {questionText}
                </h3>

                {/* Image if exists */}
                {questionImageUrl && (
                  <div className="mb-6">
                    <img 
                      src={questionImageUrl} 
                      alt="Imagen de la pregunta"
                      className="max-w-full h-auto rounded-lg shadow-lg"
                      onError={(e) => {
                        console.log('Failed to load question image:', questionImageUrl);
                        e.currentTarget.style.display = 'none';
                      }}
                    />
                  </div>
                )}

                {/* Progressive Hints Display */}
                <AnimatePresence>
                  {showHint && hintText && (
                    <motion.div
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: 'auto' }}
                      exit={{ opacity: 0, height: 0 }}
                      className="bg-yellow-900/20 border border-yellow-500/30 rounded-lg p-4 mb-6"
                    >
                      <div className="flex items-start justify-between mb-2">
                        <div className="flex items-center gap-2">
                          <AlertCircle className="w-5 h-5 text-yellow-400 flex-shrink-0" />
                          <span className="text-yellow-400 font-medium">
                            Pista nivel {currentQuestion && currentHintLevel[currentQuestion.id] ? currentHintLevel[currentQuestion.id] : 1}
                          </span>
                        </div>
                        <button
                          onClick={() => setShowHint(false)}
                          className="text-yellow-400/60 hover:text-yellow-400 transition-colors"
                        >
                          <X className="w-4 h-4" />
                        </button>
                      </div>
                      <p className="text-yellow-300">
                        {hintText}
                      </p>
                      
                      {/* Show hint progress */}
                      {currentQuestion && hintsUsed[currentQuestion.id] && (
                        <div className="flex items-center gap-1 mt-3 pt-3 border-t border-yellow-500/20">
                          <span className="text-yellow-400/80 text-sm">Progreso:</span>
                          {[1, 2, 3].map((level) => (
                            <div
                              key={level}
                              className={`w-2 h-2 rounded-full ${
                                hintsUsed[currentQuestion.id].includes(level)
                                  ? 'bg-yellow-400'
                                  : 'bg-yellow-400/20'
                              }`}
                            />
                          ))}
                          <span className="text-yellow-400/60 text-sm ml-2">
                            {hintsUsed[currentQuestion.id].length}/3 pistas utilizadas
                          </span>
                        </div>
                      )}
                    </motion.div>
                  )}
                </AnimatePresence>

                {/* Options */}
                <div className="space-y-3">
                  {finalOptions.map((option) => {
                    const isSelected = answers[currentQuestion.id] === option.letter;
                    
                    return (
                      <motion.button
                        key={option.letter}
                        whileHover={{ scale: 1.01, x: 5 }}
                        whileTap={{ scale: 0.99 }}
                        onClick={() => handleAnswer(option.letter)}
                        className={`
                          w-full p-5 rounded-xl text-left transition-all duration-200
                          flex items-center gap-4 group
                          ${isSelected
                            ? 'bg-purple-600/30 border-2 border-purple-400 text-white shadow-lg shadow-purple-500/20'
                            : 'bg-black/30 border-2 border-gray-700 text-gray-300 hover:bg-purple-900/20 hover:border-purple-500'
                          }
                        `}
                      >
                        <span className={`
                          flex-shrink-0 w-10 h-10 rounded-full font-bold
                          flex items-center justify-center transition-all
                          ${isSelected
                            ? 'bg-purple-500 text-white'
                            : 'bg-gray-800 text-gray-400 group-hover:bg-purple-800 group-hover:text-purple-300'
                          }
                        `}>
                          {option.letter}
                        </span>
                        
                        <div className="flex-1">
                          <span className="text-lg block">{option.text}</span>
                          
                          {/* Option Image */}
                          {option.image && (
                            <div className="mt-3">
                              <img 
                                src={option.image} 
                                alt={`Imagen opción ${option.letter}`}
                                className="max-w-xs h-auto rounded-lg shadow-md"
                                onError={(e) => {
                                  console.log(`Failed to load option ${option.letter} image:`, option.image);
                                  e.currentTarget.style.display = 'none';
                                }}
                              />
                            </div>
                          )}
                        </div>
                        
                        {isSelected && (
                          <Check className="ml-auto w-6 h-6 text-purple-400" />
                        )}
                      </motion.button>
                    );
                  })}
                </div>

                {/* Explanation Section */}
                <AnimatePresence>
                  {showExplanation[currentQuestion.id] && questionFeedback[currentQuestion.id] && (
                    <motion.div
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: 'auto' }}
                      exit={{ opacity: 0, height: 0 }}
                      className="mt-6"
                    >
                      <div className={`
                        p-6 rounded-xl border-2
                        ${questionFeedback[currentQuestion.id]?.is_correct 
                          ? 'bg-green-900/20 border-green-500/30' 
                          : 'bg-red-900/20 border-red-500/30'
                        }
                      `}>
                        {/* Feedback Header */}
                        <div className="flex items-center gap-3 mb-4">
                          {questionFeedback[currentQuestion.id]?.is_correct ? (
                            <Check className="w-6 h-6 text-green-400" />
                          ) : (
                            <X className="w-6 h-6 text-red-400" />
                          )}
                          <h4 className={`font-bold text-lg
                            ${questionFeedback[currentQuestion.id]?.is_correct 
                              ? 'text-green-400' 
                              : 'text-red-400'
                            }
                          `}>
                            {questionFeedback[currentQuestion.id]?.is_correct ? '¡Correcto!' : 'Incorrecto'}
                          </h4>
                        </div>

                        {/* Show correct answer if wrong */}
                        {!questionFeedback[currentQuestion.id]?.is_correct && (
                          <div className="mb-4 p-3 bg-black/30 rounded-lg">
                            <p className="text-yellow-300">
                              <strong>Respuesta correcta:</strong> {questionFeedback[currentQuestion.id]?.correct_answer}
                            </p>
                          </div>
                        )}

                        {/* Explanation */}
                        {(currentQuestion.explicacion_respuesta || questionFeedback[currentQuestion.id]?.explicacion_respuesta) && (
                          <div className="mb-4">
                            <h5 className="text-blue-300 font-semibold mb-2 flex items-center gap-2">
                              <BookOpen className="w-4 h-4" />
                              Explicación:
                            </h5>
                            <p className="text-gray-300 leading-relaxed">
                              {currentQuestion.explicacion_respuesta || questionFeedback[currentQuestion.id]?.explicacion_respuesta}
                            </p>
                          </div>
                        )}

                        {/* Common Error (only shown for wrong answers) */}
                        {!questionFeedback[currentQuestion.id]?.is_correct && 
                         (currentQuestion.error_comun || questionFeedback[currentQuestion.id]?.error_comun) && (
                          <div className="p-3 bg-orange-900/20 border border-orange-500/30 rounded-lg">
                            <h5 className="text-orange-300 font-semibold mb-2 flex items-center gap-2">
                              <AlertCircle className="w-4 h-4" />
                              Error Común:
                            </h5>
                            <p className="text-orange-200 text-sm">
                              {currentQuestion.error_comun || questionFeedback[currentQuestion.id]?.error_comun}
                            </p>
                          </div>
                        )}

                        {/* Toggle Button */}
                        <div className="mt-4 pt-3 border-t border-gray-700">
                          <button
                            onClick={() => setShowExplanation(prev => ({
                              ...prev,
                              [currentQuestion.id]: false
                            }))}
                            className="text-sm text-purple-300 hover:text-purple-200 transition-colors flex items-center gap-1"
                          >
                            <X className="w-4 h-4" />
                            Ocultar explicación
                          </button>
                        </div>
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>

                {/* Show Explanation Button (if answered but explanation is hidden) */}
                {answers[currentQuestion.id] && questionFeedback[currentQuestion.id] && 
                 !showExplanation[currentQuestion.id] && (
                  <div className="mt-4">
                    <button
                      onClick={() => setShowExplanation(prev => ({
                        ...prev,
                        [currentQuestion.id]: true
                      }))}
                      className="px-4 py-2 bg-blue-600/20 text-blue-300 rounded-lg hover:bg-blue-600/30 transition-colors flex items-center gap-2"
                    >
                      <BookOpen className="w-4 h-4" />
                      Ver explicación
                    </button>
                  </div>
                )}
              </motion.div>
            </div>
          </div>

          {/* Navigation Footer */}
          <div className="bg-black/30 backdrop-blur-lg border-t border-purple-500/30 p-6">
            <div className="max-w-4xl mx-auto flex justify-between items-center">
              <button
                onClick={handlePrevious}
                disabled={currentQuestionIndex === 0}
                className={`
                  px-6 py-3 rounded-lg font-medium flex items-center gap-2
                  transition-all duration-200
                  ${currentQuestionIndex === 0
                    ? 'bg-gray-800 text-gray-500 cursor-not-allowed'
                    : 'bg-purple-600 hover:bg-purple-700 text-white'
                  }
                `}
              >
                <ChevronLeft className="w-5 h-5" />
                Anterior
              </button>

              <div className="flex items-center gap-4">
                <span className="text-purple-300">
                  {currentQuestionIndex + 1} / {questions.length}
                </span>
              </div>

              <button
                onClick={handleNext}
                disabled={currentQuestionIndex === questions.length - 1}
                className={`
                  px-6 py-3 rounded-lg font-medium flex items-center gap-2
                  transition-all duration-200
                  ${currentQuestionIndex === questions.length - 1
                    ? 'bg-gray-800 text-gray-500 cursor-not-allowed'
                    : answers[currentQuestion.id]
                    ? 'bg-purple-600 hover:bg-purple-700 text-white'
                    : 'bg-purple-800 hover:bg-purple-700 text-purple-300'
                  }
                `}
              >
                Siguiente
                <ChevronRight className="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}