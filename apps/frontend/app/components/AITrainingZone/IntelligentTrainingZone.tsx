'use client';

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  AcademicCapIcon,
  LightBulbIcon,
  ChartBarIcon,
  ChatBubbleLeftRightIcon,
  ClockIcon,
  CheckCircleIcon,
  XCircleIcon,
  SparklesIcon,
  ArrowRightIcon,
  PlayIcon,
  PauseIcon
} from '@heroicons/react/24/outline';
import AITutor from './AITutor';

interface Question {
  id: string;
  statement: string;
  options: {
    A: string;
    B: string;
    C: string;
    D: string;
  };
  correct_answer: string;
  topic?: string;
  difficulty?: string;
  estimated_time?: string;
}

interface AIExplanation {
  explanation: string;
  confidence_score: number;
  follow_up_questions: string[];
  suggested_actions: string[];
  related_resources: any[];
  learning_objectives: string[];
}

interface TrainingSession {
  questions: Question[];
  current_question_index: number;
  answers: { [questionId: string]: string };
  start_time: Date;
  ai_interactions: number;
  hints_used: number;
}

interface IntelligentTrainingZoneProps {
  subjectId: number;
  initialQuestionCount?: number;
  adaptiveDifficulty?: boolean;
  focusAreas?: string[];
}

export default function IntelligentTrainingZone({
  subjectId,
  initialQuestionCount = 10,
  adaptiveDifficulty = true,
  focusAreas = []
}: IntelligentTrainingZoneProps) {
  const [session, setSession] = useState<TrainingSession | null>(null);
  const [currentQuestion, setCurrentQuestion] = useState<Question | null>(null);
  const [selectedAnswer, setSelectedAnswer] = useState<string>('');
  const [showExplanation, setShowExplanation] = useState(false);
  const [explanation, setExplanation] = useState<AIExplanation | null>(null);
  const [showHint, setShowHint] = useState(false);
  const [hintContent, setHintContent] = useState<string>('');
  const [hintLevel, setHintLevel] = useState(0);
  const [showAITutor, setShowAITutor] = useState(false);
  const [timeElapsed, setTimeElapsed] = useState(0);
  const [isPaused, setIsPaused] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [sessionStats, setSessionStats] = useState({
    correct: 0,
    incorrect: 0,
    ai_helps: 0,
    avg_time: 0
  });

  // Timer effect
  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (session && !isPaused && !showExplanation) {
      interval = setInterval(() => {
        setTimeElapsed(prev => prev + 1);
      }, 1000);
    }
    return () => clearInterval(interval);
  }, [session, isPaused, showExplanation]);

  // Initialize training session
  useEffect(() => {
    if (subjectId) {
      initializeSession();
    }
  }, [subjectId]);

  const initializeSession = async () => {
    setIsLoading(true);
    try {
      const response = await fetch('/api/ai-training/generate-practice', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          subject_id: subjectId,
          question_count: initialQuestionCount,
          difficulty_level: adaptiveDifficulty ? 'adaptive' : 'medium',
          focus_topics: focusAreas,
          avoid_recent: true
        })
      });

      if (!response.ok) {
        throw new Error('Failed to generate practice questions');
      }

      const data = await response.json();
      
      const newSession: TrainingSession = {
        questions: data.questions,
        current_question_index: 0,
        answers: {},
        start_time: new Date(),
        ai_interactions: 0,
        hints_used: 0
      };

      setSession(newSession);
      setCurrentQuestion(data.questions[0]);
      setTimeElapsed(0);
      
    } catch (error) {
      console.error('Error initializing session:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const submitAnswer = async () => {
    if (!currentQuestion || !selectedAnswer || !session) return;

    const isCorrect = selectedAnswer === currentQuestion.correct_answer;
    
    // Update session
    const updatedSession = {
      ...session,
      answers: {
        ...session.answers,
        [currentQuestion.id]: selectedAnswer
      }
    };
    setSession(updatedSession);

    // Update stats
    setSessionStats(prev => ({
      ...prev,
      [isCorrect ? 'correct' : 'incorrect']: prev[isCorrect ? 'correct' : 'incorrect'] + 1,
      avg_time: ((prev.avg_time * (prev.correct + prev.incorrect)) + timeElapsed) / (prev.correct + prev.incorrect + 1)
    }));

    // Get AI explanation
    await getExplanation(currentQuestion.id, selectedAnswer);
    setShowExplanation(true);
    setIsPaused(true);
  };

  const getExplanation = async (questionId: string, studentAnswer: string) => {
    try {
      const response = await fetch('/api/ai-training/explain-question', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          question_id: questionId,
          student_answer: studentAnswer,
          include_strategy_tips: true
        })
      });

      if (response.ok) {
        const data = await response.json();
        setExplanation({
          explanation: data.response_text,
          confidence_score: data.confidence_score,
          follow_up_questions: data.follow_up_questions,
          suggested_actions: data.suggested_actions,
          related_resources: data.related_resources,
          learning_objectives: data.learning_objectives
        });
        
        setSessionStats(prev => ({
          ...prev,
          ai_helps: prev.ai_helps + 1
        }));
      }
    } catch (error) {
      console.error('Error getting explanation:', error);
    }
  };

  const getHint = async (level: number = hintLevel + 1) => {
    if (!currentQuestion) return;

    try {
      const response = await fetch('/api/ai-training/get-hint', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          question_id: currentQuestion.id,
          attempt_number: level,
          time_spent: timeElapsed,
          difficulty_preference: level === 1 ? 'gentle' : level === 2 ? 'moderate' : 'direct'
        })
      });

      if (response.ok) {
        const data = await response.json();
        setHintContent(data.response_text);
        setHintLevel(level);
        setShowHint(true);
        
        setSession(prev => prev ? { ...prev, hints_used: prev.hints_used + 1 } : null);
        setSessionStats(prev => ({ ...prev, ai_helps: prev.ai_helps + 1 }));
      }
    } catch (error) {
      console.error('Error getting hint:', error);
    }
  };

  const nextQuestion = () => {
    if (!session) return;

    setShowExplanation(false);
    setShowHint(false);
    setExplanation(null);
    setHintContent('');
    setHintLevel(0);
    setSelectedAnswer('');
    setTimeElapsed(0);
    setIsPaused(false);

    const nextIndex = session.current_question_index + 1;
    
    if (nextIndex < session.questions.length) {
      const updatedSession = {
        ...session,
        current_question_index: nextIndex
      };
      setSession(updatedSession);
      setCurrentQuestion(session.questions[nextIndex]);
    } else {
      // Session complete
      finishSession();
    }
  };

  const finishSession = () => {
    // TODO: Send session results to backend for analysis
    console.log('Session completed:', {
      session,
      stats: sessionStats
    });
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <SparklesIcon className="h-12 w-12 text-blue-500 animate-spin mx-auto mb-4" />
          <p className="text-lg font-medium text-gray-700 dark:text-gray-300">
            Generando preguntas personalizadas...
          </p>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Preparando tu sesión de entrenamiento inteligente
          </p>
        </div>
      </div>
    );
  }

  if (!session || !currentQuestion) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500 dark:text-gray-400">
          No se pudieron cargar las preguntas de práctica.
        </p>
        <button
          onClick={initializeSession}
          className="mt-4 px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          Intentar de nuevo
        </button>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Header with progress and stats */}
      <div className="bg-white dark:bg-gray-900 rounded-xl shadow-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-4">
            <div className="p-2 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg">
              <AcademicCapIcon className="h-6 w-6 text-white" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-gray-900 dark:text-white">
                Zona de Entrenamiento IA
              </h2>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                Pregunta {session.current_question_index + 1} de {session.questions.length}
              </p>
            </div>
          </div>
          
          <div className="flex items-center space-x-6">
            {/* Timer */}
            <div className="flex items-center space-x-2">
              <ClockIcon className="h-5 w-5 text-gray-500" />
              <span className="text-lg font-mono text-gray-700 dark:text-gray-300">
                {formatTime(timeElapsed)}
              </span>
              <button
                onClick={() => setIsPaused(!isPaused)}
                className="p-1 text-gray-500 hover:text-gray-700 dark:hover:text-gray-300"
              >
                {isPaused ? <PlayIcon className="h-4 w-4" /> : <PauseIcon className="h-4 w-4" />}
              </button>
            </div>

            {/* Quick stats */}
            <div className="flex items-center space-x-4 text-sm">
              <div className="flex items-center space-x-1">
                <CheckCircleIcon className="h-4 w-4 text-green-500" />
                <span className="text-gray-700 dark:text-gray-300">{sessionStats.correct}</span>
              </div>
              <div className="flex items-center space-x-1">
                <XCircleIcon className="h-4 w-4 text-red-500" />
                <span className="text-gray-700 dark:text-gray-300">{sessionStats.incorrect}</span>
              </div>
              <div className="flex items-center space-x-1">
                <SparklesIcon className="h-4 w-4 text-blue-500" />
                <span className="text-gray-700 dark:text-gray-300">{sessionStats.ai_helps}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Progress bar */}
        <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
          <div
            className="bg-gradient-to-r from-blue-500 to-purple-600 h-2 rounded-full transition-all duration-300"
            style={{ width: `${((session.current_question_index + 1) / session.questions.length) * 100}%` }}
          ></div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main question area */}
        <div className="lg:col-span-2 space-y-6">
          {/* Question card */}
          <div className="bg-white dark:bg-gray-900 rounded-xl shadow-lg p-6">
            <div className="mb-4">
              {currentQuestion.topic && (
                <span className="inline-block px-3 py-1 bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 text-sm rounded-full mb-3">
                  {currentQuestion.topic}
                </span>
              )}
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center space-x-2">
                  {currentQuestion.difficulty && (
                    <span className={`px-2 py-1 text-xs rounded-full ${
                      currentQuestion.difficulty === 'easy' 
                        ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                        : currentQuestion.difficulty === 'hard'
                        ? 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
                        : 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200'
                    }`}>
                      {currentQuestion.difficulty}
                    </span>
                  )}
                  {currentQuestion.estimated_time && (
                    <span className="text-xs text-gray-500 dark:text-gray-400">
                      ⏱️ {currentQuestion.estimated_time}
                    </span>
                  )}
                </div>
              </div>
            </div>

            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-6">
              {currentQuestion.statement}
            </h3>

            {/* Answer options */}
            <div className="space-y-3 mb-6">
              {Object.entries(currentQuestion.options).map(([option, text]) => (
                <motion.button
                  key={option}
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={() => setSelectedAnswer(option)}
                  disabled={showExplanation}
                  className={`w-full text-left p-4 rounded-lg border-2 transition-all ${
                    selectedAnswer === option
                      ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                      : 'border-gray-200 dark:border-gray-600 hover:border-gray-300 dark:hover:border-gray-500'
                  } ${showExplanation ? 'cursor-not-allowed opacity-75' : 'cursor-pointer'}`}
                >
                  <div className="flex items-start space-x-3">
                    <span className={`flex-shrink-0 w-6 h-6 rounded-full border-2 flex items-center justify-center text-sm font-medium ${
                      selectedAnswer === option
                        ? 'border-blue-500 bg-blue-500 text-white'
                        : 'border-gray-300 dark:border-gray-600 text-gray-600 dark:text-gray-400'
                    }`}>
                      {option}
                    </span>
                    <span className="text-gray-900 dark:text-white">{text}</span>
                  </div>
                </motion.button>
              ))}
            </div>

            {/* Action buttons */}
            <div className="flex items-center justify-between">
              <div className="flex space-x-3">
                <button
                  onClick={() => getHint()}
                  disabled={showExplanation || hintLevel >= 3}
                  className="flex items-center space-x-2 px-4 py-2 border border-yellow-500 text-yellow-600 rounded-lg hover:bg-yellow-50 dark:hover:bg-yellow-900/20 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <LightBulbIcon className="h-4 w-4" />
                  <span>Pista {hintLevel > 0 ? `(${hintLevel}/3)` : ''}</span>
                </button>
                
                <button
                  onClick={() => setShowAITutor(!showAITutor)}
                  className="flex items-center space-x-2 px-4 py-2 border border-purple-500 text-purple-600 rounded-lg hover:bg-purple-50 dark:hover:bg-purple-900/20"
                >
                  <ChatBubbleLeftRightIcon className="h-4 w-4" />
                  <span>Tutor IA</span>
                </button>
              </div>

              <button
                onClick={submitAnswer}
                disabled={!selectedAnswer || showExplanation}
                className="flex items-center space-x-2 px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <span>Responder</span>
                <ArrowRightIcon className="h-4 w-4" />
              </button>
            </div>
          </div>

          {/* Hint display */}
          <AnimatePresence>
            {showHint && hintContent && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-xl p-4"
              >
                <div className="flex items-center space-x-2 mb-3">
                  <LightBulbIcon className="h-5 w-5 text-yellow-600" />
                  <h4 className="font-medium text-yellow-800 dark:text-yellow-200">
                    Pista {hintLevel}/3
                  </h4>
                </div>
                <p className="text-yellow-700 dark:text-yellow-300 text-sm leading-relaxed">
                  {hintContent}
                </p>
                {hintLevel < 3 && (
                  <button
                    onClick={() => getHint(hintLevel + 1)}
                    className="mt-3 text-xs text-yellow-600 hover:text-yellow-800 dark:text-yellow-400 dark:hover:text-yellow-200"
                  >
                    Solicitar pista más específica →
                  </button>
                )}
              </motion.div>
            )}
          </AnimatePresence>

          {/* Explanation display */}
          <AnimatePresence>
            {showExplanation && explanation && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                className="bg-white dark:bg-gray-900 rounded-xl shadow-lg p-6"
              >
                <div className="flex items-center justify-between mb-4">
                  <h4 className="text-lg font-semibold text-gray-900 dark:text-white">
                    Explicación IA
                  </h4>
                  <div className="flex items-center space-x-2">
                    <SparklesIcon className="h-4 w-4 text-blue-500" />
                    <span className="text-sm text-gray-500 dark:text-gray-400">
                      Confianza: {(explanation.confidence_score * 100).toFixed(0)}%
                    </span>
                  </div>
                </div>

                <div className="prose prose-sm max-w-none text-gray-700 dark:text-gray-300 mb-4">
                  {explanation.explanation.split('\n').map((paragraph, index) => (
                    <p key={index} className="mb-2">{paragraph}</p>
                  ))}
                </div>

                {explanation.suggested_actions.length > 0 && (
                  <div className="mb-4">
                    <h5 className="font-medium text-gray-900 dark:text-white mb-2">
                      Acciones recomendadas:
                    </h5>
                    <ul className="space-y-1">
                      {explanation.suggested_actions.slice(0, 3).map((action, index) => (
                        <li key={index} className="flex items-start space-x-2 text-sm text-gray-600 dark:text-gray-400">
                          <div className="w-1 h-1 bg-blue-500 rounded-full mt-2 flex-shrink-0"></div>
                          <span>{action}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                <div className="flex justify-between items-center pt-4 border-t border-gray-200 dark:border-gray-700">
                  <div className="text-sm text-gray-500 dark:text-gray-400">
                    {selectedAnswer === currentQuestion.correct_answer ? (
                      <span className="text-green-600 dark:text-green-400 flex items-center space-x-1">
                        <CheckCircleIcon className="h-4 w-4" />
                        <span>¡Respuesta correcta!</span>
                      </span>
                    ) : (
                      <span className="text-red-600 dark:text-red-400 flex items-center space-x-1">
                        <XCircleIcon className="h-4 w-4" />
                        <span>Respuesta incorrecta. La correcta es: {currentQuestion.correct_answer}</span>
                      </span>
                    )}
                  </div>
                  
                  <button
                    onClick={nextQuestion}
                    className="flex items-center space-x-2 px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
                  >
                    <span>
                      {session.current_question_index + 1 < session.questions.length ? 'Siguiente' : 'Finalizar'}
                    </span>
                    <ArrowRightIcon className="h-4 w-4" />
                  </button>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Session stats */}
          <div className="bg-white dark:bg-gray-900 rounded-xl shadow-lg p-6">
            <h4 className="font-semibold text-gray-900 dark:text-white mb-4 flex items-center space-x-2">
              <ChartBarIcon className="h-5 w-5 text-blue-500" />
              <span>Estadísticas</span>
            </h4>
            
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-sm text-gray-600 dark:text-gray-400">Precisión</span>
                <span className="font-medium text-gray-900 dark:text-white">
                  {sessionStats.correct + sessionStats.incorrect > 0 
                    ? Math.round((sessionStats.correct / (sessionStats.correct + sessionStats.incorrect)) * 100)
                    : 0}%
                </span>
              </div>
              
              <div className="flex justify-between">
                <span className="text-sm text-gray-600 dark:text-gray-400">Tiempo promedio</span>
                <span className="font-medium text-gray-900 dark:text-white">
                  {Math.round(sessionStats.avg_time)}s
                </span>
              </div>
              
              <div className="flex justify-between">
                <span className="text-sm text-gray-600 dark:text-gray-400">Ayudas IA</span>
                <span className="font-medium text-gray-900 dark:text-white">
                  {sessionStats.ai_helps}
                </span>
              </div>

              <div className="flex justify-between">
                <span className="text-sm text-gray-600 dark:text-gray-400">Progreso</span>
                <span className="font-medium text-gray-900 dark:text-white">
                  {session.current_question_index + 1}/{session.questions.length}
                </span>
              </div>
            </div>
          </div>

          {/* AI Tutor panel */}
          <AnimatePresence>
            {showAITutor && (
              <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.95 }}
                className="h-96"
              >
                <AITutor
                  studentId="current_user"
                  subjectId={subjectId}
                  initialContext="homework"
                  onInteraction={(interaction) => {
                    console.log('AI Tutor interaction:', interaction);
                  }}
                />
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
}