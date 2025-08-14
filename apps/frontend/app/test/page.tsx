'use client';

import React, { useState, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Brain, 
  Clock, 
  CheckCircle, 
  XCircle, 
  AlertTriangle,
  Lock,
  Users,
  Trophy
} from 'lucide-react';
import { useAuthStore } from '@/stores/useAuthStore';
import { useGameModeStore } from '@/stores/useGameModeStore';

interface Question {
  id: string;
  text: string;
  options: string[];
  correctAnswer: number;
  explanation: string;
  subject: string;
  difficulty: number;
}

interface TestState {
  currentQuestion: number;
  answers: (number | null)[];
  timeSpent: number;
  isComplete: boolean;
  score: number;
  showResults: boolean;
}

// Mock questions for demo
const mockQuestions: Question[] = [
  {
    id: '1',
    text: '¿Cuál es la solución de la ecuación 2x + 5 = 13?',
    options: ['x = 3', 'x = 4', 'x = 5', 'x = 6'],
    correctAnswer: 1,
    explanation: '2x + 5 = 13 → 2x = 8 → x = 4',
    subject: 'Matemáticas',
    difficulty: 3
  },
  {
    id: '2',
    text: '¿Qué tipo de reacción es la fotosíntesis?',
    options: ['Exotérmica', 'Endotérmica', 'Neutra', 'Nuclear'],
    correctAnswer: 1,
    explanation: 'La fotosíntesis absorbe energía solar, por lo que es endotérmica.',
    subject: 'Ciencias',
    difficulty: 4
  },
  {
    id: '3',
    text: '¿Cuál es el sinónimo de "prudente"?',
    options: ['Audaz', 'Cauteloso', 'Impulsivo', 'Valiente'],
    correctAnswer: 1,
    explanation: 'Prudente significa cauteloso o cuidadoso.',
    subject: 'Lenguaje',
    difficulty: 2
  },
  {
    id: '4',
    text: '¿En qué año comenzó la Primera Guerra Mundial?',
    options: ['1914', '1915', '1916', '1917'],
    correctAnswer: 0,
    explanation: 'La Primera Guerra Mundial comenzó en 1914.',
    subject: 'Sociales',
    difficulty: 3
  },
  {
    id: '5',
    text: '¿Cuál es la fórmula del área de un círculo?',
    options: ['A = πr²', 'A = 2πr', 'A = πd', 'A = r²'],
    correctAnswer: 0,
    explanation: 'El área de un círculo es A = πr² donde r es el radio.',
    subject: 'Matemáticas',
    difficulty: 3
  }
];

const GUEST_DAILY_LIMIT = 10;
const GUEST_QUESTIONS_PER_TEST = 5;

export default function TestPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const mode = searchParams.get('mode');
  const isGuestMode = mode === 'guest';
  
  const { user } = useAuthStore();
  const { mode: gameMode } = useGameModeStore();
  
  const [testState, setTestState] = useState<TestState>({
    currentQuestion: 0,
    answers: new Array(mockQuestions.length).fill(null),
    timeSpent: 0,
    isComplete: false,
    score: 0,
    showResults: false
  });
  
  const [guestQuestionsUsed, setGuestQuestionsUsed] = useState(0);
  const [showGuestLimitModal, setShowGuestLimitModal] = useState(false);
  const [timer, setTimer] = useState(0);

  // Check guest limits on mount
  useEffect(() => {
    if (isGuestMode) {
      const stored = localStorage.getItem('guestQuestionsUsed');
      const used = stored ? parseInt(stored) : 0;
      setGuestQuestionsUsed(used);
      
      if (used >= GUEST_DAILY_LIMIT) {
        setShowGuestLimitModal(true);
      }
    }
  }, [isGuestMode]);

  // Timer effect
  useEffect(() => {
    if (!testState.isComplete && !testState.showResults) {
      const interval = setInterval(() => {
        setTimer(prev => prev + 1);
      }, 1000);
      return () => clearInterval(interval);
    }
  }, [testState.isComplete, testState.showResults]);

  const handleAnswerSelect = (answerIndex: number) => {
    if (testState.answers[testState.currentQuestion] !== null) return;
    
    const newAnswers = [...testState.answers];
    newAnswers[testState.currentQuestion] = answerIndex;
    
    setTestState(prev => ({
      ...prev,
      answers: newAnswers
    }));
  };

  const handleNextQuestion = () => {
    if (testState.currentQuestion < mockQuestions.length - 1) {
      setTestState(prev => ({
        ...prev,
        currentQuestion: prev.currentQuestion + 1
      }));
    } else {
      completeTest();
    }
  };

  const handlePreviousQuestion = () => {
    if (testState.currentQuestion > 0) {
      setTestState(prev => ({
        ...prev,
        currentQuestion: prev.currentQuestion - 1
      }));
    }
  };

  const completeTest = () => {
    const correctAnswers = testState.answers.filter((answer, index) => 
      answer === mockQuestions[index].correctAnswer
    ).length;
    
    const score = Math.round((correctAnswers / mockQuestions.length) * 100);
    
    // Update guest questions used
    if (isGuestMode) {
      const newUsed = guestQuestionsUsed + GUEST_QUESTIONS_PER_TEST;
      setGuestQuestionsUsed(newUsed);
      localStorage.setItem('guestQuestionsUsed', newUsed.toString());
      
      // Set daily reset
      const today = new Date().toDateString();
      localStorage.setItem('guestQuestionsDate', today);
    }
    
    setTestState(prev => ({
      ...prev,
      isComplete: true,
      score,
      timeSpent: timer,
      showResults: true
    }));
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const getQuestionStatus = (index: number) => {
    if (testState.answers[index] === null) return 'unanswered';
    if (testState.answers[index] === mockQuestions[index].correctAnswer) return 'correct';
    return 'incorrect';
  };

  const currentQuestion = mockQuestions[testState.currentQuestion];
  const selectedAnswer = testState.answers[testState.currentQuestion];

  if (showGuestLimitModal) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900 to-gray-900 flex items-center justify-center p-4">
        <motion.div
          className="bg-gray-900/90 rounded-lg p-8 max-w-md w-full border border-purple-500/30"
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
        >
          <div className="text-center">
            <Lock className="w-16 h-16 text-yellow-400 mx-auto mb-4" />
            <h2 className="text-2xl font-bold text-white mb-4">
              Límite Diario Alcanzado
            </h2>
            <p className="text-gray-300 mb-6">
              Has usado tus {GUEST_DAILY_LIMIT} preguntas diarias gratuitas. 
              Crea una cuenta para acceso ilimitado.
            </p>
            
            <div className="space-y-3 mb-6">
              <div className="flex items-center justify-between bg-gray-800/50 rounded-lg p-3">
                <span className="text-gray-300">Preguntas usadas hoy:</span>
                <span className="text-yellow-400 font-bold">{guestQuestionsUsed}/{GUEST_DAILY_LIMIT}</span>
              </div>
            </div>
            
            <div className="flex gap-3">
              <button
                onClick={() => router.push('/')}
                className="flex-1 px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg font-semibold transition-all"
              >
                Crear Cuenta
              </button>
              <button
                onClick={() => router.push('/')}
                className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg font-semibold transition-all"
              >
                Volver
              </button>
            </div>
          </div>
        </motion.div>
      </div>
    );
  }

  if (testState.showResults) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900 to-gray-900 p-4">
        <div className="max-w-4xl mx-auto">
          <motion.div
            className="bg-gray-900/90 rounded-lg p-8 border border-purple-500/30"
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
          >
            <div className="text-center mb-8">
              <h1 className="text-3xl font-bold text-white mb-4">
                Resultados del Test
              </h1>
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                <div className="bg-gray-800/50 rounded-lg p-6">
                  <div className="text-4xl font-bold text-purple-400 mb-2">
                    {testState.score}%
                  </div>
                  <div className="text-gray-400">Puntuación</div>
                </div>
                
                <div className="bg-gray-800/50 rounded-lg p-6">
                  <div className="text-4xl font-bold text-blue-400 mb-2">
                    {formatTime(testState.timeSpent)}
                  </div>
                  <div className="text-gray-400">Tiempo</div>
                </div>
                
                <div className="bg-gray-800/50 rounded-lg p-6">
                  <div className="text-4xl font-bold text-green-400 mb-2">
                    {testState.answers.filter(a => a !== null).length}/{mockQuestions.length}
                  </div>
                  <div className="text-gray-400">Respondidas</div>
                </div>
              </div>
              
              {isGuestMode && (
                <div className="bg-yellow-900/20 rounded-lg p-4 mb-6 border border-yellow-500/30">
                  <p className="text-yellow-300 text-sm">
                    <strong>Modo Invitado:</strong> Has usado {guestQuestionsUsed}/{GUEST_DAILY_LIMIT} preguntas hoy.
                    {guestQuestionsUsed >= GUEST_DAILY_LIMIT && ' ¡Límite alcanzado!'}
                  </p>
                </div>
              )}
              
              <div className="flex gap-4 justify-center">
                <button
                  onClick={() => router.push('/')}
                  className="px-6 py-3 bg-purple-600 hover:bg-purple-700 text-white rounded-lg font-semibold transition-all"
                >
                  Volver al Dashboard
                </button>
                
                {!isGuestMode && (
                  <button
                    onClick={() => window.location.reload()}
                    className="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-semibold transition-all"
                  >
                    Nuevo Test
                  </button>
                )}
              </div>
            </div>
          </motion.div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900 to-gray-900 p-4">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <motion.div
          className="bg-gray-900/90 rounded-lg p-6 mb-6 border border-purple-500/30"
          initial={{ y: -20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
        >
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-white">
                Test de Conocimiento
              </h1>
              <p className="text-gray-400">
                {isGuestMode ? 'Modo Invitado' : 'Modo Completo'} • {gameMode === 'casual' ? 'Progresión Libre' : 'Progresión Gated'}
              </p>
            </div>
            
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2 text-gray-300">
                <Clock className="w-5 h-5" />
                <span className="font-mono">{formatTime(timer)}</span>
              </div>
              
              {isGuestMode && (
                <div className="flex items-center gap-2 text-yellow-400">
                  <AlertTriangle className="w-5 h-5" />
                  <span className="text-sm">
                    {guestQuestionsUsed}/{GUEST_DAILY_LIMIT}
                  </span>
                </div>
              )}
            </div>
          </div>
          
          {/* Progress Bar */}
          <div className="mt-4">
            <div className="flex justify-between text-sm text-gray-400 mb-2">
              <span>Progreso</span>
              <span>{testState.currentQuestion + 1} / {mockQuestions.length}</span>
            </div>
            <div className="w-full bg-gray-700 rounded-full h-2">
              <div 
                className="bg-gradient-to-r from-purple-600 to-blue-600 h-2 rounded-full transition-all duration-300"
                style={{ width: `${((testState.currentQuestion + 1) / mockQuestions.length) * 100}%` }}
              />
            </div>
          </div>
        </motion.div>

        {/* Question Navigation */}
        <motion.div
          className="bg-gray-900/90 rounded-lg p-4 mb-6 border border-purple-500/30"
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.1 }}
        >
          <div className="flex flex-wrap gap-2">
            {mockQuestions.map((_, index) => {
              const status = getQuestionStatus(index);
              return (
                <button
                  key={index}
                  onClick={() => setTestState(prev => ({ ...prev, currentQuestion: index }))}
                  className={`
                    w-10 h-10 rounded-lg flex items-center justify-center text-sm font-semibold transition-all
                    ${index === testState.currentQuestion 
                      ? 'bg-purple-600 text-white ring-2 ring-purple-400' 
                      : status === 'correct' 
                        ? 'bg-green-600 text-white' 
                        : status === 'incorrect' 
                          ? 'bg-red-600 text-white' 
                          : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                    }
                  `}
                >
                  {index + 1}
                </button>
              );
            })}
          </div>
        </motion.div>

        {/* Question */}
        <motion.div
          key={testState.currentQuestion}
          className="bg-gray-900/90 rounded-lg p-8 border border-purple-500/30"
          initial={{ x: 20, opacity: 0 }}
          animate={{ x: 0, opacity: 1 }}
          transition={{ duration: 0.3 }}
        >
          <div className="mb-6">
            <div className="flex items-center gap-2 text-gray-400 mb-4">
              <Brain className="w-5 h-5" />
              <span>{currentQuestion.subject}</span>
              <span>•</span>
              <span>Dificultad: {currentQuestion.difficulty}/5</span>
            </div>
            
            <h2 className="text-xl text-white mb-6">
              {currentQuestion.text}
            </h2>
          </div>

          {/* Options */}
          <div className="space-y-3 mb-8">
            {currentQuestion.options.map((option, index) => {
              const isSelected = selectedAnswer === index;
              const isCorrect = index === currentQuestion.correctAnswer;
              const showCorrect = testState.answers[testState.currentQuestion] !== null;
              
              return (
                <motion.button
                  key={index}
                  onClick={() => handleAnswerSelect(index)}
                  disabled={testState.answers[testState.currentQuestion] !== null}
                  className={`
                    w-full p-4 rounded-lg text-left transition-all duration-200
                    ${isSelected 
                      ? isCorrect 
                        ? 'bg-green-600/20 border-green-500 text-green-300' 
                        : 'bg-red-600/20 border-red-500 text-red-300'
                      : showCorrect && isCorrect 
                        ? 'bg-green-600/20 border-green-500 text-green-300' 
                        : 'bg-gray-800/50 border-gray-600 text-gray-300 hover:bg-gray-700/50'
                    }
                    border-2
                  `}
                  whileHover={{ scale: testState.answers[testState.currentQuestion] === null ? 1.02 : 1 }}
                  whileTap={{ scale: testState.answers[testState.currentQuestion] === null ? 0.98 : 1 }}
                >
                  <div className="flex items-center gap-3">
                    <div className={`
                      w-6 h-6 rounded-full flex items-center justify-center text-sm font-bold
                      ${isSelected 
                        ? isCorrect 
                          ? 'bg-green-500 text-white' 
                          : 'bg-red-500 text-white'
                        : showCorrect && isCorrect 
                          ? 'bg-green-500 text-white' 
                          : 'bg-gray-600 text-gray-300'
                      }
                    `}>
                      {String.fromCharCode(65 + index)}
                    </div>
                    <span>{option}</span>
                  </div>
                </motion.button>
              );
            })}
          </div>

          {/* Explanation */}
          {testState.answers[testState.currentQuestion] !== null && (
            <motion.div
              className="bg-blue-900/20 rounded-lg p-4 mb-6 border border-blue-500/30"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
            >
              <h3 className="font-semibold text-blue-300 mb-2">Explicación:</h3>
              <p className="text-blue-200">{currentQuestion.explanation}</p>
            </motion.div>
          )}

          {/* Navigation */}
          <div className="flex justify-between">
            <button
              onClick={handlePreviousQuestion}
              disabled={testState.currentQuestion === 0}
              className="px-6 py-3 bg-gray-700 hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-lg font-semibold transition-all"
            >
              Anterior
            </button>
            
            <button
              onClick={handleNextQuestion}
              disabled={testState.answers[testState.currentQuestion] === null}
              className="px-6 py-3 bg-purple-600 hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-lg font-semibold transition-all"
            >
              {testState.currentQuestion === mockQuestions.length - 1 ? 'Finalizar' : 'Siguiente'}
            </button>
          </div>
        </motion.div>
      </div>
    </div>
  );
} 