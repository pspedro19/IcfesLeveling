'use client';

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  User, 
  Brain, 
  Target, 
  Zap,
  ChevronRight,
  Trophy,
  Lock,
  Sparkles,
  Timer,
  CheckCircle,
  XCircle
} from 'lucide-react';
import { useAudio } from '../PortalLogin/AudioEngine';
import { useRouter } from 'next/navigation';

interface Question {
  id: string;
  text: string;
  options: string[];
  correct: string;
  subject: string;
  difficulty: number;
}

interface GuestMiniQuizProps {
  onComplete: (score: number, answers: any[]) => void;
  onCancel: () => void;
}

const GUEST_QUESTIONS: Question[] = [
  {
    id: 'q1',
    text: '¿Cuál es el resultado de 2³?',
    options: ['6', '8', '9', '12'],
    correct: '8',
    subject: 'Matemáticas',
    difficulty: 1
  },
  {
    id: 'q2',
    text: '¿Cuál es el sinónimo de "efímero"?',
    options: ['Eterno', 'Breve', 'Intenso', 'Constante'],
    correct: 'Breve',
    subject: 'Lectura Crítica',
    difficulty: 2
  },
  {
    id: 'q3',
    text: '¿Cuál es la capital de Australia?',
    options: ['Sydney', 'Melbourne', 'Canberra', 'Brisbane'],
    correct: 'Canberra',
    subject: 'Sociales',
    difficulty: 2
  },
  {
    id: 'q4',
    text: '¿Qué gas es esencial para la respiración?',
    options: ['Nitrógeno', 'Hidrógeno', 'Oxígeno', 'Helio'],
    correct: 'Oxígeno',
    subject: 'Ciencias',
    difficulty: 1
  },
  {
    id: 'q5',
    text: 'Choose the correct form: "She ___ to school every day."',
    options: ['go', 'goes', 'going', 'gone'],
    correct: 'goes',
    subject: 'Inglés',
    difficulty: 1
  }
];

export default function GuestMiniQuiz({ onComplete, onCancel }: GuestMiniQuizProps) {
  const { playSound } = useAudio();
  const router = useRouter();
  
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [selectedAnswer, setSelectedAnswer] = useState<string | null>(null);
  const [answers, setAnswers] = useState<Array<{
    questionId: string;
    answer: string;
    correct: boolean;
    time: number;
  }>>([]);
  const [showResult, setShowResult] = useState(false);
  const [questionStartTime, setQuestionStartTime] = useState(Date.now());
  const [showFeedback, setShowFeedback] = useState(false);
  const [timeRemaining, setTimeRemaining] = useState(30); // 30 seconds per question
  
  // Timer effect
  useEffect(() => {
    if (showResult || showFeedback) return;
    
    const timer = setInterval(() => {
      setTimeRemaining(prev => {
        if (prev <= 1) {
          handleTimeOut();
          return 30;
        }
        return prev - 1;
      });
    }, 1000);
    
    return () => clearInterval(timer);
  }, [currentQuestion, showResult, showFeedback]);
  
  // Reset timer on new question
  useEffect(() => {
    setTimeRemaining(30);
    setQuestionStartTime(Date.now());
  }, [currentQuestion]);
  
  const handleTimeOut = () => {
    playSound('notification_epic');
    submitAnswer(true);
  };
  
  const submitAnswer = (timeout = false) => {
    if (!selectedAnswer && !timeout) return;
    
    const question = GUEST_QUESTIONS[currentQuestion];
    const isCorrect = selectedAnswer === question.correct;
    const answerTime = Date.now() - questionStartTime;
    
    setAnswers([...answers, {
      questionId: question.id,
      answer: selectedAnswer || 'No answer',
      correct: isCorrect && !timeout,
      time: answerTime
    }]);
    
    if (!timeout) {
      playSound(isCorrect ? 'quest_complete' : 'damage_hit');
      setShowFeedback(true);
      
      setTimeout(() => {
        setShowFeedback(false);
        if (currentQuestion < GUEST_QUESTIONS.length - 1) {
          setCurrentQuestion(currentQuestion + 1);
          setSelectedAnswer(null);
        } else {
          setShowResult(true);
        }
      }, 1500);
    } else {
      // Skip feedback on timeout
      if (currentQuestion < GUEST_QUESTIONS.length - 1) {
        setCurrentQuestion(currentQuestion + 1);
        setSelectedAnswer(null);
      } else {
        setShowResult(true);
      }
    }
  };
  
  const calculateScore = () => {
    const correct = answers.filter(a => a.correct).length;
    return Math.round((correct / GUEST_QUESTIONS.length) * 100);
  };
  
  const getPerformanceLevel = (score: number) => {
    if (score >= 80) return { level: 'Excelente', color: 'text-green-400', rank: 'A' };
    if (score >= 60) return { level: 'Bueno', color: 'text-blue-400', rank: 'B' };
    if (score >= 40) return { level: 'Regular', color: 'text-yellow-400', rank: 'C' };
    return { level: 'Necesitas Práctica', color: 'text-red-400', rank: 'D' };
  };
  
  const handleComplete = () => {
    const score = calculateScore();
    playSound('level_up');
    onComplete(score, answers);
  };
  
  if (showResult) {
    const score = calculateScore();
    const performance = getPerformanceLevel(score);
    
    return (
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        className="bg-gray-900 rounded-lg p-8 max-w-2xl mx-auto"
      >
        <div className="text-center mb-8">
          <Trophy className="w-20 h-20 text-yellow-400 mx-auto mb-4" />
          <h2 className="text-3xl font-bold text-white mb-2 font-cinzel">
            ¡Quiz Completado!
          </h2>
          <p className="text-gray-400">
            Modo Invitado - Evaluación Inicial
          </p>
        </div>
        
        <div className="bg-gray-800 rounded-lg p-6 mb-6">
          <div className="text-center mb-4">
            <div className="text-5xl font-bold text-white mb-2">
              {score}%
            </div>
            <div className={`text-xl font-semibold ${performance.color}`}>
              {performance.level}
            </div>
            <div className="text-4xl font-bold text-gray-600 mt-2">
              Rango {performance.rank}
            </div>
          </div>
          
          <div className="grid grid-cols-2 gap-4 mt-6">
            <div className="bg-gray-700 rounded-lg p-3 text-center">
              <CheckCircle className="w-8 h-8 text-green-400 mx-auto mb-1" />
              <p className="text-2xl font-bold text-white">
                {answers.filter(a => a.correct).length}
              </p>
              <p className="text-sm text-gray-400">Correctas</p>
            </div>
            
            <div className="bg-gray-700 rounded-lg p-3 text-center">
              <XCircle className="w-8 h-8 text-red-400 mx-auto mb-1" />
              <p className="text-2xl font-bold text-white">
                {answers.filter(a => !a.correct).length}
              </p>
              <p className="text-sm text-gray-400">Incorrectas</p>
            </div>
          </div>
        </div>
        
        <div className="bg-purple-900/30 rounded-lg p-6 border border-purple-500/30 mb-6">
          <h3 className="text-lg font-semibold text-purple-300 mb-3">
            🎯 Recomendación Personalizada
          </h3>
          <p className="text-gray-300">
            {score >= 80 
              ? 'Excelente inicio. Crea una cuenta para desbloquear contenido avanzado y competir en el ranking global.'
              : score >= 60
              ? 'Buen desempeño. Regístrate para acceder a planes de estudio personalizados y mejorar tus habilidades.'
              : 'Te recomendamos crear una cuenta para acceder a tutoriales y prácticas que te ayudarán a mejorar.'}
          </p>
        </div>
        
        <div className="flex gap-4">
          <button
            onClick={handleComplete}
            className="flex-1 bg-gradient-to-r from-purple-600 to-purple-700 hover:from-purple-700 
              hover:to-purple-800 text-white font-bold py-3 px-6 rounded-lg transition-all 
              flex items-center justify-center gap-2"
          >
            <User className="w-5 h-5" />
            Continuar como Invitado
          </button>
          
          <button
            onClick={() => router.push('/?register=true')}
            className="flex-1 bg-gradient-to-r from-green-600 to-green-700 hover:from-green-700 
              hover:to-green-800 text-white font-bold py-3 px-6 rounded-lg transition-all 
              flex items-center justify-center gap-2"
          >
            <Sparkles className="w-5 h-5" />
            Crear Cuenta Gratis
          </button>
        </div>
      </motion.div>
    );
  }
  
  const question = GUEST_QUESTIONS[currentQuestion];
  const progress = ((currentQuestion + 1) / GUEST_QUESTIONS.length) * 100;
  
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-gray-900 rounded-lg p-8 max-w-2xl mx-auto"
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-2xl font-bold text-white font-cinzel">
            Evaluación Rápida
          </h2>
          <p className="text-gray-400 text-sm">
            Modo Invitado - 5 preguntas
          </p>
        </div>
        
        <button
          onClick={onCancel}
          className="text-gray-400 hover:text-white transition-colors"
        >
          ✕
        </button>
      </div>
      
      {/* Progress */}
      <div className="mb-6">
        <div className="flex justify-between text-sm text-gray-400 mb-2">
          <span>Pregunta {currentQuestion + 1} de {GUEST_QUESTIONS.length}</span>
          <span>{Math.round(progress)}%</span>
        </div>
        <div className="w-full bg-gray-700 rounded-full h-2">
          <motion.div
            className="h-full bg-gradient-to-r from-purple-500 to-purple-600 rounded-full"
            initial={{ width: 0 }}
            animate={{ width: `${progress}%` }}
            transition={{ duration: 0.3 }}
          />
        </div>
      </div>
      
      {/* Timer */}
      <div className="flex items-center justify-center mb-6">
        <div className={`flex items-center gap-2 px-4 py-2 rounded-lg ${
          timeRemaining <= 10 ? 'bg-red-900/30 text-red-400' : 'bg-gray-800 text-gray-300'
        }`}>
          <Timer className="w-5 h-5" />
          <span className="font-mono text-lg">
            00:{timeRemaining.toString().padStart(2, '0')}
          </span>
        </div>
      </div>
      
      {/* Question */}
      <div className="mb-8">
        <div className="flex items-center gap-2 mb-4">
          <span className="bg-purple-600/30 text-purple-300 px-3 py-1 rounded-full text-sm">
            {question.subject}
          </span>
          <div className="flex gap-1">
            {[...Array(5)].map((_, i) => (
              <Star
                key={i}
                className={`w-4 h-4 ${
                  i < question.difficulty ? 'text-yellow-400' : 'text-gray-600'
                }`}
                fill={i < question.difficulty ? 'currentColor' : 'none'}
              />
            ))}
          </div>
        </div>
        
        <h3 className="text-xl text-white mb-6">
          {question.text}
        </h3>
        
        {/* Options */}
        <div className="grid grid-cols-2 gap-3">
          {question.options.map((option, index) => (
            <motion.button
              key={index}
              onClick={() => setSelectedAnswer(option)}
              disabled={showFeedback}
              className={`p-4 rounded-lg border-2 transition-all text-left ${
                showFeedback && option === question.correct
                  ? 'border-green-500 bg-green-900/30'
                  : showFeedback && option === selectedAnswer && option !== question.correct
                  ? 'border-red-500 bg-red-900/30'
                  : selectedAnswer === option
                  ? 'border-purple-500 bg-purple-900/30'
                  : 'border-gray-600 bg-gray-800 hover:border-gray-500'
              } disabled:cursor-not-allowed`}
              whileHover={!showFeedback ? { scale: 1.02 } : {}}
              whileTap={!showFeedback ? { scale: 0.98 } : {}}
            >
              <span className="text-white">{option}</span>
            </motion.button>
          ))}
        </div>
      </div>
      
      {/* Action Buttons */}
      <div className="flex gap-4">
        <button
          onClick={() => submitAnswer()}
          disabled={!selectedAnswer || showFeedback}
          className="flex-1 bg-gradient-to-r from-purple-600 to-purple-700 
            hover:from-purple-700 hover:to-purple-800 disabled:from-gray-600 
            disabled:to-gray-700 disabled:cursor-not-allowed text-white 
            font-bold py-3 px-6 rounded-lg transition-all flex items-center 
            justify-center gap-2"
        >
          <ChevronRight className="w-5 h-5" />
          {currentQuestion === GUEST_QUESTIONS.length - 1 ? 'Finalizar' : 'Siguiente'}
        </button>
      </div>
      
      {/* Feedback */}
      <AnimatePresence>
        {showFeedback && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className={`mt-4 p-4 rounded-lg ${
              selectedAnswer === question.correct
                ? 'bg-green-900/30 border border-green-500/50'
                : 'bg-red-900/30 border border-red-500/50'
            }`}
          >
            <p className={`font-semibold ${
              selectedAnswer === question.correct ? 'text-green-400' : 'text-red-400'
            }`}>
              {selectedAnswer === question.correct ? '¡Correcto!' : 'Incorrecto'}
            </p>
            {selectedAnswer !== question.correct && (
              <p className="text-gray-300 text-sm mt-1">
                La respuesta correcta es: {question.correct}
              </p>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}