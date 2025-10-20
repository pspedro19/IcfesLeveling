'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Shield, 
  Clock, 
  Zap, 
  Target, 
  ArrowLeft,
  Play,
  Pause,
  RotateCcw,
  Trophy,
  Flame,
  AlertTriangle,
  CheckCircle
} from 'lucide-react';
import MainNavigation from '../components/Navigation/MainNavigation';

interface TimedChallenge {
  id: string;
  title: string;
  description: string;
  timeLimit: number; // in seconds
  questionCount: number;
  difficulty: 'Fácil' | 'Medio' | 'Difícil' | 'Extremo';
  xpReward: number;
  icon: string;
  color: string;
}

interface ChallengeStats {
  questionsAnswered: number;
  correctAnswers: number;
  timeRemaining: number;
  score: number;
  combo: number;
}

export default function MazmorraDelTiempoPage() {
  const router = useRouter();
  const [currentUser, setCurrentUser] = useState<any>(null);
  const [selectedChallenge, setSelectedChallenge] = useState<TimedChallenge | null>(null);
  const [challengeActive, setChallengeActive] = useState(false);
  const [challengeStats, setChallengeStats] = useState<ChallengeStats>({
    questionsAnswered: 0,
    correctAnswers: 0,
    timeRemaining: 0,
    score: 0,
    combo: 0
  });
  const [loading, setLoading] = useState(true);

  const timedChallenges: TimedChallenge[] = [
    {
      id: 'speed_math',
      title: '🔢 Velocidad Matemática',
      description: 'Resuelve problemas matemáticos a máxima velocidad. ¡Cada segundo cuenta!',
      timeLimit: 300, // 5 minutes
      questionCount: 15,
      difficulty: 'Medio',
      xpReward: 400,
      icon: '⚡',
      color: 'from-blue-600 to-cyan-600'
    },
    {
      id: 'reading_sprint',
      title: '📖 Sprint de Lectura',
      description: 'Comprensión lectora bajo presión extrema. Analiza textos rápidamente.',
      timeLimit: 600, // 10 minutes
      questionCount: 12,
      difficulty: 'Difícil',
      xpReward: 500,
      icon: '🏃‍♂️',
      color: 'from-green-600 to-emerald-600'
    },
    {
      id: 'science_blitz',
      title: '🧬 Blitz Científico',
      description: 'Preguntas de ciencias naturales en modo relámpago. ¡Demuestra tu conocimiento!',
      timeLimit: 450, // 7.5 minutes
      questionCount: 18,
      difficulty: 'Difícil',
      xpReward: 550,
      icon: '⚡',
      color: 'from-emerald-600 to-teal-600'
    },
    {
      id: 'social_rush',
      title: '🏛️ Carrera Social',
      description: 'Historia y geografía contra el reloj. Navega por el tiempo y el espacio.',
      timeLimit: 480, // 8 minutes
      questionCount: 16,
      difficulty: 'Medio',
      xpReward: 450,
      icon: '🏃‍♀️',
      color: 'from-orange-600 to-red-600'
    },
    {
      id: 'english_dash',
      title: '🌍 English Dash',
      description: 'English comprehension at lightning speed. Think fast, answer faster!',
      timeLimit: 360, // 6 minutes
      questionCount: 20,
      difficulty: 'Fácil',
      xpReward: 350,
      icon: '💨',
      color: 'from-purple-600 to-pink-600'
    },
    {
      id: 'ultimate_trial',
      title: '👑 Prueba Definitiva',
      description: 'El desafío supremo: todas las materias, tiempo limitado, máxima dificultad.',
      timeLimit: 900, // 15 minutes
      questionCount: 25,
      difficulty: 'Extremo',
      xpReward: 1000,
      icon: '🔥',
      color: 'from-red-600 to-pink-600'
    }
  ];

  useEffect(() => {
    // Load user data and check level requirement
    const userData = localStorage.getItem('currentUser') || localStorage.getItem('user');
    if (userData) {
      const user = JSON.parse(userData);
      setCurrentUser(user);
      
      if (user.level < 15) {
        alert('🔒 Acceso Denegado\n\nLa Mazmorra del Tiempo requiere Nivel 15.\nTu nivel actual: ' + user.level + '\n\n¡Entrena más para acceder a los desafíos cronometrados!');
        router.push('/hub-central');
        return;
      }
    }
    setLoading(false);
  }, []);

  const startChallenge = (challenge: TimedChallenge) => {
    setSelectedChallenge(challenge);
    setChallengeStats({
      questionsAnswered: 0,
      correctAnswers: 0,
      timeRemaining: challenge.timeLimit,
      score: 0,
      combo: 0
    });
    setChallengeActive(true);
    
    // Start countdown
    const timer = setInterval(() => {
      setChallengeStats(prev => {
        if (prev.timeRemaining <= 1) {
          clearInterval(timer);
          endChallenge();
          return prev;
        }
        return { ...prev, timeRemaining: prev.timeRemaining - 1 };
      });
    }, 1000);
  };

  const endChallenge = () => {
    setChallengeActive(false);
    if (selectedChallenge) {
      const accuracy = challengeStats.questionsAnswered > 0 ? (challengeStats.correctAnswers / challengeStats.questionsAnswered) * 100 : 0;
      const timeBonus = Math.floor(challengeStats.timeRemaining / 10);
      const totalXP = selectedChallenge.xpReward + timeBonus;
      
      let result = '';
      if (accuracy >= 90) result = '🏆 ¡MAESTRO DEL TIEMPO!';
      else if (accuracy >= 75) result = '⚡ ¡Velocidad Épica!';
      else if (accuracy >= 60) result = '🎯 Buen Ritmo';
      else result = '⏱️ Necesitas Más Velocidad';
      
      alert(`${result}\n\n📊 Resultados del Desafío:\n• Preguntas: ${challengeStats.correctAnswers}/${challengeStats.questionsAnswered}\n• Precisión: ${accuracy.toFixed(1)}%\n• Tiempo restante: ${Math.floor(challengeStats.timeRemaining / 60)}:${(challengeStats.timeRemaining % 60).toString().padStart(2, '0')}\n• Combo máximo: ${challengeStats.combo}\n\n⚡ +${totalXP} XP ganados!`);
    }
    
    setSelectedChallenge(null);
  };

  const getDifficultyColor = (difficulty: string) => {
    const colors = {
      'Fácil': 'text-green-400',
      'Medio': 'text-yellow-400',
      'Difícil': 'text-orange-400',
      'Extremo': 'text-red-400'
    };
    return colors[difficulty] || 'text-gray-400';
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 text-white flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-indigo-400 mx-auto mb-4"></div>
          <h2 className="text-2xl font-bold mb-2">⏱️ Accediendo a la Mazmorra...</h2>
          <p className="text-purple-200">Preparando desafíos cronometrados</p>
        </div>
      </div>
    );
  }

  // Challenge Active Interface
  if (challengeActive && selectedChallenge) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-indigo-900 via-purple-900 to-black text-white">
        <MainNavigation currentUser={currentUser} />
        
        <div className="pt-20 lg:pt-24 pb-8">
          <div className="container mx-auto px-4">
            {/* Challenge HUD */}
            <div className="mb-6 bg-black/50 rounded-xl p-4 border border-indigo-500/30">
              <div className="flex justify-between items-center">
                <div className="flex items-center gap-4">
                  <div className="text-center">
                    <div className="text-indigo-300 text-sm">{selectedChallenge.title}</div>
                    <div className="text-white font-bold">{selectedChallenge.icon}</div>
                  </div>
                  
                  <div className="text-center">
                    <div className="text-gold-400 text-sm">Puntuación</div>
                    <div className="text-2xl font-bold text-gold-400">{challengeStats.score}</div>
                  </div>
                  
                  <div className="text-center">
                    <div className="text-purple-300 text-sm">Combo</div>
                    <div className="text-xl font-bold text-purple-400">{challengeStats.combo}x</div>
                  </div>
                </div>
                
                {/* Timer */}
                <div className="text-center">
                  <div className={`text-4xl font-bold ${challengeStats.timeRemaining <= 30 ? 'text-red-400 animate-pulse' : 'text-white'}`}>
                    {formatTime(challengeStats.timeRemaining)}
                  </div>
                  <div className="text-indigo-300 text-sm">Tiempo restante</div>
                </div>
                
                <div className="text-center">
                  <div className="text-green-300 text-sm">Progreso</div>
                  <div className="text-white font-bold">
                    {challengeStats.correctAnswers}/{challengeStats.questionsAnswered}
                  </div>
                  <div className="text-xs text-purple-300">
                    de {selectedChallenge.questionCount}
                  </div>
                </div>
              </div>
            </div>

            {/* Simulated Question Interface */}
            <div className="bg-black/40 rounded-xl p-6 border border-indigo-500/30">
              <div className="text-center">
                <h2 className="text-2xl font-bold text-white mb-6">
                  🎯 Desafío Cronometrado Activo
                </h2>
                <p className="text-indigo-200 mb-6">
                  En una implementación completa, aquí aparecerían las preguntas de {selectedChallenge.title}
                </p>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                  <div className="bg-indigo-900/30 rounded-lg p-4">
                    <h3 className="font-bold text-indigo-300 mb-2">⚡ Modo Velocidad</h3>
                    <p className="text-sm text-indigo-100">
                      Responde rápido para mantener el combo y ganar puntos extra
                    </p>
                  </div>
                  <div className="bg-purple-900/30 rounded-lg p-4">
                    <h3 className="font-bold text-purple-300 mb-2">🎯 Precisión</h3>
                    <p className="text-sm text-purple-100">
                      Cada respuesta correcta aumenta tu combo multiplicador
                    </p>
                  </div>
                </div>
                
                <button
                  onClick={endChallenge}
                  className="bg-gradient-to-r from-red-600 to-pink-600 hover:from-red-700 hover:to-pink-700 px-8 py-4 rounded-lg font-bold text-white transition-all transform hover:scale-105"
                >
                  🏁 Finalizar Desafío
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Challenge Selection
  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 text-white">
      <MainNavigation currentUser={currentUser} />
      
      <div className="pt-20 lg:pt-24 pb-8">
        <div className="container mx-auto px-4">
          {/* Header */}
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-center mb-8"
          >
            <div className="flex items-center justify-center gap-4 mb-4">
              <button
                onClick={() => router.push('/hub-central')}
                className="bg-purple-600/50 hover:bg-purple-700/50 p-3 rounded-lg transition-all"
              >
                <ArrowLeft className="w-5 h-5" />
              </button>
              
              <h1 className="text-4xl font-bold bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent">
                ⏱️ Mazmorra del Tiempo
              </h1>
            </div>
            
            <p className="text-xl text-purple-200 mb-4">
              Simulacros cronometrados bajo presión
            </p>
            
            {/* Event Badge */}
            <div className="inline-flex items-center gap-2 bg-yellow-800/50 px-4 py-2 rounded-lg animate-pulse">
              <Flame className="w-4 h-4 text-yellow-400" />
              <span className="text-yellow-200 font-bold">EVENTO ESPECIAL ACTIVO</span>
            </div>
          </motion.div>

          {/* Warning */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="max-w-4xl mx-auto mb-8 bg-red-900/20 rounded-xl p-6 border border-red-500/30"
          >
            <div className="flex items-center gap-3 mb-3">
              <AlertTriangle className="w-6 h-6 text-red-400" />
              <h2 className="text-xl font-bold text-red-400">⚠️ Advertencia de Combate</h2>
            </div>
            <p className="text-red-200 mb-4">
              Los desafíos cronometrados son extremadamente intensos. Una vez iniciados, no se pueden pausar. 
              Asegúrate de estar en un ambiente sin distracciones.
            </p>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
              <div className="bg-black/30 rounded-lg p-3">
                <div className="font-bold text-red-300">🎯 Objetivo</div>
                <div className="text-red-100">Responder correctamente bajo presión</div>
              </div>
              <div className="bg-black/30 rounded-lg p-3">
                <div className="font-bold text-yellow-300">⚡ Estrategia</div>
                <div className="text-yellow-100">Velocidad + Precisión = Victoria</div>
              </div>
              <div className="bg-black/30 rounded-lg p-3">
                <div className="font-bold text-green-300">🏆 Recompensa</div>
                <div className="text-green-100">XP masivo por completar</div>
              </div>
            </div>
          </motion.div>

          {/* Challenges Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {timedChallenges.map((challenge, index) => (
              <motion.div
                key={challenge.id}
                initial={{ opacity: 0, y: 50 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
                className="group cursor-pointer"
                onClick={() => startChallenge(challenge)}
              >
                <div className={`bg-gradient-to-br ${challenge.color}/20 rounded-xl p-6 border-2 border-indigo-500/30 hover:border-gold-500/50 transition-all transform hover:scale-105 backdrop-blur-sm relative overflow-hidden`}>
                  
                  {/* Difficulty Badge */}
                  <div className={`absolute top-3 right-3 px-2 py-1 rounded-full text-xs font-bold ${getDifficultyColor(challenge.difficulty)} bg-black/50`}>
                    {challenge.difficulty}
                  </div>
                  
                  <div className="text-center">
                    {/* Icon */}
                    <div className={`w-20 h-20 rounded-full bg-gradient-to-r ${challenge.color} flex items-center justify-center text-3xl mb-4 mx-auto shadow-lg group-hover:shadow-indigo-500/25 transition-all`}>
                      {challenge.icon}
                    </div>
                    
                    {/* Title */}
                    <h3 className="text-xl font-bold text-white mb-2">{challenge.title}</h3>
                    
                    {/* Description */}
                    <p className="text-sm text-purple-100 mb-4 leading-relaxed">
                      {challenge.description}
                    </p>
                    
                    {/* Stats */}
                    <div className="grid grid-cols-3 gap-2 text-xs text-purple-200 mb-4">
                      <div className="flex items-center justify-center gap-1">
                        <Clock className="w-3 h-3" />
                        {Math.floor(challenge.timeLimit / 60)}min
                      </div>
                      <div className="flex items-center justify-center gap-1">
                        <Target className="w-3 h-3" />
                        {challenge.questionCount} preguntas
                      </div>
                      <div className="flex items-center justify-center gap-1">
                        <Trophy className="w-3 h-3" />
                        {challenge.xpReward} XP
                      </div>
                    </div>
                    
                    {/* Action Button */}
                    <button className={`bg-gradient-to-r ${challenge.color} hover:shadow-lg px-6 py-3 rounded-lg font-bold text-white transition-all transform hover:scale-105 w-full`}>
                      ⚡ Iniciar Desafío
                    </button>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>

          {/* Leaderboard Preview */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.8 }}
            className="mt-8 max-w-4xl mx-auto bg-black/30 rounded-xl p-6 border border-indigo-500/30"
          >
            <h2 className="text-xl font-bold text-indigo-400 mb-4 text-center">🏆 Tabla de Líderes Temporales</h2>
            <div className="text-center text-purple-200">
              <p className="mb-4">Los mejores hunters en desafíos cronometrados:</p>
              <div className="space-y-2">
                <div className="bg-gold-900/30 rounded-lg p-3 flex justify-between items-center">
                  <span>🥇 MasterHunter_S</span>
                  <span className="text-gold-400 font-bold">15,750 pts</span>
                </div>
                <div className="bg-gray-800/30 rounded-lg p-3 flex justify-between items-center">
                  <span>🥈 SpeedLearner_A</span>
                  <span className="text-gray-300 font-bold">12,340 pts</span>
                </div>
                <div className="bg-orange-900/30 rounded-lg p-3 flex justify-between items-center">
                  <span>🥉 QuickThink_B</span>
                  <span className="text-orange-400 font-bold">9,820 pts</span>
                </div>
              </div>
            </div>
          </motion.div>

          {/* Back to Hub */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 1.0 }}
            className="mt-8 text-center"
          >
            <button
              onClick={() => router.push('/hub-central')}
              className="bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 px-6 py-3 rounded-lg font-semibold transition-all transform hover:scale-105 flex items-center gap-2 mx-auto"
            >
              <ArrowLeft className="w-5 h-5" />
              Volver al Hub Central
            </button>
          </motion.div>
        </div>
      </div>
    );
  }
}
