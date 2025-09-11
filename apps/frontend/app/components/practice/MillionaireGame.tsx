'use client';

import React, { useState, useEffect, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import confetti from 'canvas-confetti';
import { useQuery, useMutation } from '@tanstack/react-query';
import { useRouter } from 'next/navigation';
import Image from 'next/image';
import { FaPhone, FaUsers, FaPercentage, FaClock, FaFire, FaCoins, FaStar } from 'react-icons/fa';
import { toast } from 'react-hot-toast';

// Types
interface Question {
  id: string;
  statement: string;
  option_a: string;
  option_b: string;
  option_c: string;
  option_d: string;
  correct_answer: string;
  difficulty: string;
  image_url?: string;
  explanation?: string;
  irt_b?: number;
}

interface GameState {
  sessionId: string;
  currentQuestion: Question | null;
  questionNumber: number;
  totalQuestions: number;
  lifelines: {
    fiftyFifty: boolean;
    phoneAFriend: boolean;
    askTheAudience: boolean;
  };
  eliminatedOptions: string[];
  currentPrize: number;
  totalXP: number;
  totalCoins: number;
  streak: number;
  timeLeft: number;
  isAnswering: boolean;
  selectedAnswer: string | null;
  showResult: boolean;
  isCorrect: boolean;
  aiExplanation: string | null;
  gameOver: boolean;
}

interface LifelineResult {
  type: 'fifty_fifty' | 'phone' | 'audience';
  data: any;
}

// Prize ladder (15 questions)
const PRIZE_LADDER = [
  100, 200, 300, 500, 1000,      // Easy (1-5)
  2000, 4000, 8000, 16000, 32000, // Medium (6-10)
  64000, 125000, 250000, 500000, 1000000 // Hard (11-15)
];

// Sound effects configuration
const SOUNDS = {
  intro: '/sounds/millionaire-intro.mp3',
  questionAppear: '/sounds/question-appear.mp3',
  finalAnswer: '/sounds/final-answer.mp3',
  correct: '/sounds/correct-answer.mp3',
  wrong: '/sounds/wrong-answer.mp3',
  lifeline: '/sounds/lifeline.mp3',
  drumroll: '/sounds/drumroll.mp3',
  win: '/sounds/big-win.mp3',
};

export default function MillionaireGame({ 
  subjectId,
  studentId 
}: { 
  subjectId: number;
  studentId: string;
}) {
  const router = useRouter();
  const [gameState, setGameState] = useState<GameState>({
    sessionId: '',
    currentQuestion: null,
    questionNumber: 0,
    totalQuestions: 15,
    lifelines: {
      fiftyFifty: true,
      phoneAFriend: true,
      askTheAudience: true,
    },
    eliminatedOptions: [],
    currentPrize: 0,
    totalXP: 0,
    totalCoins: 0,
    streak: 0,
    timeLeft: 60,
    isAnswering: false,
    selectedAnswer: null,
    showResult: false,
    isCorrect: false,
    aiExplanation: null,
    gameOver: false,
  });

  const [showExplanationModal, setShowExplanationModal] = useState(false);
  const [audienceVotes, setAudienceVotes] = useState<Record<string, number>>({});
  const [phoneHint, setPhoneHint] = useState<string>('');
  const timerRef = useRef<NodeJS.Timeout | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  // Start game session
  const { mutate: startSession, isLoading: isStarting } = useMutation({
    mutationFn: async () => {
      const response = await fetch('/api/v1/practice/start-millionaire', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          subject_id: subjectId,
          student_id: studentId,
          mode: 'millionaire'
        }),
      });
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.message || 'Error al iniciar el juego');
      }
      
      return response.json();
    },
    onSuccess: (data) => {
      if (data.status === 'NO_FAILURES') {
        toast.success('¡Felicidades! No tienes errores para practicar');
        router.push('/practice');
        return;
      }

      setGameState(prev => ({
        ...prev,
        sessionId: data.session_id,
        currentQuestion: data.first_question,
        questionNumber: 1,
        totalQuestions: data.total_questions || 15,
      }));

      // Play intro sound
      playSound('intro');
    },
    onError: (error: Error) => {
      toast.error(error.message);
      router.push('/practice');
    },
  });

  // Submit answer
  const { mutate: submitAnswer, isLoading: isSubmitting } = useMutation({
    mutationFn: async (answer: string) => {
      const response = await fetch('/api/v1/practice/submit-answer', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: gameState.sessionId,
          question_id: gameState.currentQuestion?.id,
          selected_option: answer,
          time_taken: 60 - gameState.timeLeft,
        }),
      });

      if (!response.ok) {
        throw new Error('Error al enviar respuesta');
      }

      return response.json();
    },
    onSuccess: (data) => {
      handleAnswerResult(data);
    },
    onError: () => {
      toast.error('Error al procesar la respuesta');
      setGameState(prev => ({ ...prev, isAnswering: false }));
    },
  });

  // Get next question
  const { mutate: getNextQuestion } = useMutation({
    mutationFn: async () => {
      const response = await fetch('/api/v1/practice/next-question', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: gameState.sessionId,
          current_number: gameState.questionNumber,
        }),
      });

      if (!response.ok) {
        throw new Error('Error al obtener siguiente pregunta');
      }

      return response.json();
    },
    onSuccess: (data) => {
      if (data.completed) {
        handleGameComplete();
        return;
      }

      setGameState(prev => ({
        ...prev,
        currentQuestion: data.question,
        questionNumber: prev.questionNumber + 1,
        eliminatedOptions: [],
        selectedAnswer: null,
        showResult: false,
        isAnswering: false,
        timeLeft: 60,
        aiExplanation: null,
      }));

      playSound('questionAppear');
    },
  });

  // Timer effect
  useEffect(() => {
    if (gameState.currentQuestion && !gameState.showResult && gameState.timeLeft > 0) {
      timerRef.current = setTimeout(() => {
        setGameState(prev => ({ ...prev, timeLeft: prev.timeLeft - 1 }));
      }, 1000);

      // Auto-submit if time runs out
      if (gameState.timeLeft === 1) {
        handleTimeOut();
      }

      return () => {
        if (timerRef.current) clearTimeout(timerRef.current);
      };
    }
  }, [gameState.timeLeft, gameState.currentQuestion, gameState.showResult]);

  // Initialize game on mount
  useEffect(() => {
    startSession();
    return () => {
      // Cleanup audio
      if (audioRef.current) {
        audioRef.current.pause();
      }
    };
  }, []);

  // Play sound effect
  const playSound = (soundKey: keyof typeof SOUNDS) => {
    if (audioRef.current) {
      audioRef.current.pause();
    }
    audioRef.current = new Audio(SOUNDS[soundKey]);
    audioRef.current.play().catch(console.error);
  };

  // Handle answer selection
  const handleAnswerClick = async (option: string) => {
    if (gameState.isAnswering || gameState.showResult) return;

    setGameState(prev => ({
      ...prev,
      selectedAnswer: option,
      isAnswering: true,
    }));

    // Dramatic pause
    playSound('drumroll');
    
    // Show "Is that your final answer?" effect
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    playSound('finalAnswer');
    
    // Submit answer
    submitAnswer(option);
  };

  // Handle answer result
  const handleAnswerResult = (result: any) => {
    const isCorrect = result.is_correct;
    
    setGameState(prev => ({
      ...prev,
      isCorrect,
      showResult: true,
      isAnswering: false,
      aiExplanation: result.explanation,
      totalXP: prev.totalXP + (result.rewards?.xp || 0),
      totalCoins: prev.totalCoins + (result.rewards?.coins || 0),
      streak: isCorrect ? prev.streak + 1 : 0,
      currentPrize: isCorrect ? PRIZE_LADDER[prev.questionNumber - 1] : prev.currentPrize,
    }));

    if (isCorrect) {
      playSound('correct');
      
      // Celebration effects
      if (gameState.questionNumber % 5 === 0) {
        // Major milestone
        confetti({
          particleCount: 100,
          spread: 70,
          origin: { y: 0.6 },
        });
        playSound('win');
      }

      // Check if game complete
      if (gameState.questionNumber === 15) {
        setTimeout(() => handleGameComplete(), 3000);
      }
    } else {
      playSound('wrong');
      setShowExplanationModal(true);
      
      // Game over after showing explanation
      setTimeout(() => {
        setGameState(prev => ({ ...prev, gameOver: true }));
      }, 1000);
    }
  };

  // Handle timeout
  const handleTimeOut = () => {
    setGameState(prev => ({
      ...prev,
      showResult: true,
      isCorrect: false,
      gameOver: true,
      aiExplanation: 'Se acabó el tiempo. ¡Intenta ser más rápido la próxima vez!',
    }));
    playSound('wrong');
  };

  // Handle game completion
  const handleGameComplete = () => {
    // Epic celebration
    confetti({
      particleCount: 200,
      spread: 100,
      origin: { y: 0.5 },
    });
    
    playSound('win');
    
    setGameState(prev => ({
      ...prev,
      gameOver: true,
    }));

    // Save results and redirect
    setTimeout(() => {
      router.push(`/practice/results?xp=${gameState.totalXP}&coins=${gameState.totalCoins}&prize=${gameState.currentPrize}`);
    }, 5000);
  };

  // Lifeline: 50:50
  const useFiftyFifty = () => {
    if (!gameState.lifelines.fiftyFifty || gameState.showResult) return;

    playSound('lifeline');
    
    const correctAnswer = gameState.currentQuestion?.correct_answer;
    const allOptions = ['A', 'B', 'C', 'D'];
    const incorrectOptions = allOptions.filter(opt => opt !== correctAnswer);
    
    // Randomly eliminate 2 incorrect options
    const toEliminate = incorrectOptions
      .sort(() => Math.random() - 0.5)
      .slice(0, 2);

    setGameState(prev => ({
      ...prev,
      eliminatedOptions: toEliminate,
      lifelines: { ...prev.lifelines, fiftyFifty: false },
    }));

    toast.success('50:50 activado - 2 opciones eliminadas');
  };

  // Lifeline: Phone a Friend
  const usePhoneAFriend = () => {
    if (!gameState.lifelines.phoneAFriend || gameState.showResult) return;

    playSound('lifeline');
    
    const correctAnswer = gameState.currentQuestion?.correct_answer;
    const confidence = Math.random() * 0.3 + 0.7; // 70-100% confidence
    
    const hint = confidence > 0.85 
      ? `Estoy bastante seguro de que es la opción ${correctAnswer}`
      : `Creo que podría ser la opción ${correctAnswer}, pero no estoy 100% seguro`;

    setPhoneHint(hint);
    setGameState(prev => ({
      ...prev,
      lifelines: { ...prev.lifelines, phoneAFriend: false },
    }));

    toast.success('Llamando a un amigo...');
  };

  // Lifeline: Ask the Audience
  const useAskTheAudience = () => {
    if (!gameState.lifelines.askTheAudience || gameState.showResult) return;

    playSound('lifeline');
    
    const correctAnswer = gameState.currentQuestion?.correct_answer || 'A';
    const votes: Record<string, number> = {};
    
    // Generate realistic audience votes
    const correctVotePercentage = Math.random() * 0.3 + 0.4; // 40-70% for correct
    let remaining = 1 - correctVotePercentage;
    
    ['A', 'B', 'C', 'D'].forEach(option => {
      if (option === correctAnswer) {
        votes[option] = Math.round(correctVotePercentage * 100);
      } else if (!gameState.eliminatedOptions.includes(option)) {
        const vote = Math.random() * remaining;
        votes[option] = Math.round(vote * 100);
        remaining -= vote;
      } else {
        votes[option] = 0;
      }
    });

    // Normalize to 100%
    const total = Object.values(votes).reduce((a, b) => a + b, 0);
    Object.keys(votes).forEach(key => {
      votes[key] = Math.round((votes[key] / total) * 100);
    });

    setAudienceVotes(votes);
    setGameState(prev => ({
      ...prev,
      lifelines: { ...prev.lifelines, askTheAudience: false },
    }));

    toast.success('Consultando a la audiencia...');
  };

  // Continue to next question
  const handleContinue = () => {
    if (gameState.isCorrect && !gameState.gameOver) {
      setShowExplanationModal(false);
      getNextQuestion();
    } else {
      // Game over - return to practice menu
      router.push('/practice');
    }
  };

  // Loading screen
  if (isStarting) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-purple-900 via-blue-900 to-indigo-900 flex items-center justify-center">
        <motion.div
          initial={{ opacity: 0, scale: 0.5 }}
          animate={{ opacity: 1, scale: 1 }}
          className="text-center"
        >
          <div className="text-6xl mb-4">🎮</div>
          <h2 className="text-3xl text-white font-bold mb-2">Preparando el Juego...</h2>
          <p className="text-blue-300">¿Quién Quiere Ser Millonario? - Edición ICFES</p>
        </motion.div>
      </div>
    );
  }

  // Game Over screen
  if (gameState.gameOver) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-purple-900 via-blue-900 to-indigo-900 flex items-center justify-center">
        <motion.div
          initial={{ opacity: 0, y: 50 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white/10 backdrop-blur-lg rounded-3xl p-12 max-w-2xl text-center"
        >
          <h1 className="text-5xl font-bold text-white mb-6">
            {gameState.isCorrect && gameState.questionNumber === 15 ? '¡GANASTE!' : 'Juego Terminado'}
          </h1>
          
          <div className="space-y-4 mb-8">
            <div className="text-3xl text-yellow-400">
              💰 Premio Final: ${gameState.currentPrize.toLocaleString()}
            </div>
            <div className="text-2xl text-green-400">
              ⭐ XP Ganado: {gameState.totalXP}
            </div>
            <div className="text-2xl text-orange-400">
              🪙 Monedas: {gameState.totalCoins}
            </div>
            <div className="text-xl text-blue-300">
              📊 Preguntas Correctas: {gameState.questionNumber - (gameState.isCorrect ? 0 : 1)}/15
            </div>
          </div>

          <div className="flex gap-4 justify-center">
            <button
              onClick={() => startSession()}
              className="bg-green-500 hover:bg-green-600 text-white px-8 py-4 rounded-xl font-bold text-lg transition-all transform hover:scale-105"
            >
              Jugar de Nuevo
            </button>
            <button
              onClick={() => router.push('/practice')}
              className="bg-blue-500 hover:bg-blue-600 text-white px-8 py-4 rounded-xl font-bold text-lg transition-all transform hover:scale-105"
            >
              Volver al Menú
            </button>
          </div>
        </motion.div>
      </div>
    );
  }

  // Main game screen
  return (
    <div className="min-h-screen bg-gradient-to-b from-purple-900 via-blue-900 to-indigo-900 relative overflow-hidden">
      {/* Background effects */}
      <div className="absolute inset-0">
        <div className="absolute inset-0 bg-[url('/images/millionaire-bg.jpg')] opacity-20 bg-cover bg-center" />
        <div className="absolute inset-0 bg-gradient-to-t from-black/50 to-transparent" />
      </div>

      {/* Game content */}
      <div className="relative z-10 container mx-auto px-4 py-8">
        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <div className="flex items-center gap-6">
            <div className="text-white">
              <span className="text-sm opacity-70">Pregunta</span>
              <div className="text-3xl font-bold">{gameState.questionNumber}/15</div>
            </div>
            
            <div className="text-yellow-400">
              <span className="text-sm opacity-70">Premio Actual</span>
              <div className="text-3xl font-bold">${gameState.currentPrize.toLocaleString()}</div>
            </div>
          </div>

          <div className="flex items-center gap-6">
            {/* Timer */}
            <div className={`text-4xl font-bold ${gameState.timeLeft < 10 ? 'text-red-500 animate-pulse' : 'text-white'}`}>
              <FaClock className="inline mr-2" />
              {gameState.timeLeft}s
            </div>

            {/* Stats */}
            <div className="flex gap-4 text-white">
              <div className="flex items-center gap-2">
                <FaStar className="text-yellow-400" />
                <span>{gameState.totalXP} XP</span>
              </div>
              <div className="flex items-center gap-2">
                <FaCoins className="text-orange-400" />
                <span>{gameState.totalCoins}</span>
              </div>
              {gameState.streak > 0 && (
                <div className="flex items-center gap-2">
                  <FaFire className="text-red-500" />
                  <span>x{gameState.streak}</span>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Main game area */}
        <div className="grid grid-cols-12 gap-8">
          {/* Prize ladder */}
          <div className="col-span-3">
            <div className="bg-black/50 backdrop-blur rounded-2xl p-4">
              <h3 className="text-white font-bold mb-4 text-center">Escalera de Premios</h3>
              <div className="space-y-2">
                {PRIZE_LADDER.slice().reverse().map((prize, index) => {
                  const questionNum = 15 - index;
                  const isCurrent = questionNum === gameState.questionNumber;
                  const isPassed = questionNum < gameState.questionNumber;
                  const isSafeHaven = questionNum === 5 || questionNum === 10;
                  
                  return (
                    <div
                      key={questionNum}
                      className={`
                        px-3 py-2 rounded-lg text-sm font-medium transition-all
                        ${isCurrent ? 'bg-yellow-500 text-black scale-105' : ''}
                        ${isPassed ? 'bg-green-500/30 text-green-300' : 'bg-white/10 text-white/70'}
                        ${isSafeHaven ? 'border-2 border-yellow-600' : ''}
                      `}
                    >
                      <span className="mr-2">{questionNum}.</span>
                      ${prize.toLocaleString()}
                      {isSafeHaven && <span className="ml-2 text-xs">🔒</span>}
                    </div>
                  );
                })}
              </div>
            </div>
          </div>

          {/* Question area */}
          <div className="col-span-6">
            <AnimatePresence mode="wait">
              {gameState.currentQuestion && (
                <motion.div
                  key={gameState.currentQuestion.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -20 }}
                  className="bg-gradient-to-b from-blue-800/50 to-purple-800/50 backdrop-blur rounded-3xl p-8"
                >
                  {/* Question */}
                  <div className="mb-8">
                    <h2 className="text-2xl text-white font-medium leading-relaxed">
                      {gameState.currentQuestion.statement}
                    </h2>
                    
                    {/* Question image if exists */}
                    {gameState.currentQuestion.image_url && (
                      <div className="mt-6 flex justify-center">
                        <img
                          src={gameState.currentQuestion.image_url}
                          alt="Imagen de la pregunta"
                          className="max-w-full max-h-64 rounded-lg"
                        />
                      </div>
                    )}
                  </div>

                  {/* Options */}
                  <div className="grid grid-cols-2 gap-4">
                    {['A', 'B', 'C', 'D'].map((letter) => {
                      const optionKey = `option_${letter.toLowerCase()}` as keyof Question;
                      const isEliminated = gameState.eliminatedOptions.includes(letter);
                      const isSelected = gameState.selectedAnswer === letter;
                      const isCorrect = gameState.showResult && letter === gameState.currentQuestion?.correct_answer;
                      const isWrong = gameState.showResult && isSelected && !isCorrect;
                      
                      return (
                        <motion.button
                          key={letter}
                          whileHover={!isEliminated && !gameState.showResult ? { scale: 1.05 } : {}}
                          whileTap={!isEliminated && !gameState.showResult ? { scale: 0.95 } : {}}
                          onClick={() => handleAnswerClick(letter)}
                          disabled={isEliminated || gameState.isAnswering || gameState.showResult}
                          className={`
                            relative p-4 rounded-xl font-medium text-left transition-all
                            ${isEliminated ? 'opacity-30 cursor-not-allowed bg-gray-800' : ''}
                            ${isSelected && !gameState.showResult ? 'bg-yellow-500 text-black' : ''}
                            ${isCorrect ? 'bg-green-500 text-white animate-pulse' : ''}
                            ${isWrong ? 'bg-red-500 text-white animate-shake' : ''}
                            ${!isEliminated && !isSelected && !gameState.showResult ? 'bg-blue-700/50 text-white hover:bg-blue-600/50' : ''}
                          `}
                        >
                          <span className="font-bold mr-2">{letter}:</span>
                          {gameState.currentQuestion[optionKey]}
                          
                          {/* Audience votes */}
                          {audienceVotes[letter] !== undefined && (
                            <div className="absolute top-1 right-1 bg-black/50 px-2 py-1 rounded text-xs text-white">
                              {audienceVotes[letter]}%
                            </div>
                          )}
                        </motion.button>
                      );
                    })}
                  </div>

                  {/* Phone hint */}
                  {phoneHint && (
                    <motion.div
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      className="mt-4 p-4 bg-blue-900/50 rounded-xl text-white"
                    >
                      <FaPhone className="inline mr-2" />
                      {phoneHint}
                    </motion.div>
                  )}

                  {/* Continue button */}
                  {gameState.showResult && (
                    <motion.button
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      onClick={handleContinue}
                      className="mt-6 w-full bg-gradient-to-r from-green-500 to-blue-500 text-white py-4 rounded-xl font-bold text-lg hover:from-green-600 hover:to-blue-600 transition-all"
                    >
                      {gameState.isCorrect ? 'Siguiente Pregunta →' : 'Ver Explicación'}
                    </motion.button>
                  )}
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          {/* Lifelines */}
          <div className="col-span-3">
            <div className="bg-black/50 backdrop-blur rounded-2xl p-4">
              <h3 className="text-white font-bold mb-4 text-center">Comodines</h3>
              <div className="space-y-3">
                <button
                  onClick={useFiftyFifty}
                  disabled={!gameState.lifelines.fiftyFifty || gameState.showResult}
                  className={`
                    w-full p-4 rounded-xl font-bold transition-all
                    ${gameState.lifelines.fiftyFifty 
                      ? 'bg-blue-600 hover:bg-blue-700 text-white transform hover:scale-105' 
                      : 'bg-gray-700 text-gray-400 cursor-not-allowed opacity-50'}
                  `}
                >
                  <FaPercentage className="inline mr-2" />
                  50:50
                </button>

                <button
                  onClick={usePhoneAFriend}
                  disabled={!gameState.lifelines.phoneAFriend || gameState.showResult}
                  className={`
                    w-full p-4 rounded-xl font-bold transition-all
                    ${gameState.lifelines.phoneAFriend 
                      ? 'bg-green-600 hover:bg-green-700 text-white transform hover:scale-105' 
                      : 'bg-gray-700 text-gray-400 cursor-not-allowed opacity-50'}
                  `}
                >
                  <FaPhone className="inline mr-2" />
                  Llamar a un Amigo
                </button>

                <button
                  onClick={useAskTheAudience}
                  disabled={!gameState.lifelines.askTheAudience || gameState.showResult}
                  className={`
                    w-full p-4 rounded-xl font-bold transition-all
                    ${gameState.lifelines.askTheAudience 
                      ? 'bg-purple-600 hover:bg-purple-700 text-white transform hover:scale-105' 
                      : 'bg-gray-700 text-gray-400 cursor-not-allowed opacity-50'}
                  `}
                >
                  <FaUsers className="inline mr-2" />
                  Preguntar al Público
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* AI Explanation Modal */}
      <AnimatePresence>
        {showExplanationModal && gameState.aiExplanation && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/80 backdrop-blur flex items-center justify-center z-50 p-4"
            onClick={() => setShowExplanationModal(false)}
          >
            <motion.div
              initial={{ scale: 0.9, y: 50 }}
              animate={{ scale: 1, y: 0 }}
              exit={{ scale: 0.9, y: 50 }}
              className="bg-gradient-to-b from-purple-800 to-blue-900 rounded-3xl p-8 max-w-2xl w-full"
              onClick={(e) => e.stopPropagation()}
            >
              <h3 className="text-3xl font-bold text-yellow-400 mb-6">
                💡 Explicación del Profesor IA
              </h3>
              
              <div className="text-white space-y-4">
                <div className="bg-blue-800/50 p-6 rounded-xl">
                  {gameState.aiExplanation}
                </div>
                
                {gameState.currentQuestion && (
                  <div className="bg-purple-800/50 p-4 rounded-xl">
                    <p className="font-bold mb-2">Respuesta Correcta:</p>
                    <p className="text-green-400">
                      {gameState.currentQuestion.correct_answer}: {
                        gameState.currentQuestion[`option_${gameState.currentQuestion.correct_answer.toLowerCase()}` as keyof Question]
                      }
                    </p>
                  </div>
                )}
              </div>
              
              <button
                onClick={() => {
                  setShowExplanationModal(false);
                  if (!gameState.isCorrect) {
                    router.push('/practice');
                  }
                }}
                className="mt-6 w-full bg-gradient-to-r from-green-500 to-blue-500 text-white py-4 rounded-xl font-bold text-lg hover:from-green-600 hover:to-blue-600 transition-all"
              >
                {gameState.isCorrect ? 'Continuar' : 'Finalizar Juego'}
              </button>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Hidden audio element */}
      <audio ref={audioRef} />
    </div>
  );
}