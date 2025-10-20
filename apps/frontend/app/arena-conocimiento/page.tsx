'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Sword, 
  Shield, 
  Heart, 
  Zap, 
  Target, 
  ArrowLeft,
  Clock,
  Trophy,
  Flame,
  CheckCircle,
  X
} from 'lucide-react';
import MainNavigation from '../components/Navigation/MainNavigation';

interface Question {
  id: string;
  question_text: string;
  options: { [key: string]: string };
  correct_answer: string;
  difficulty: number;
  hint: string;
  explanation: string;
  topic: { name: string };
}

interface BattleStats {
  hp: number;
  maxHp: number;
  mp: number;
  maxMp: number;
  combo: number;
  score: number;
  questionsAnswered: number;
  correctAnswers: number;
}

export default function ArenaConocimientoPage() {
  const router = useRouter();
  const [currentUser, setCurrentUser] = useState<any>(null);
  const [selectedSubject, setSelectedSubject] = useState<string | null>(null);
  const [questions, setQuestions] = useState<Question[]>([]);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [battleStats, setBattleStats] = useState<BattleStats>({
    hp: 100,
    maxHp: 100,
    mp: 50,
    maxMp: 50,
    combo: 0,
    score: 0,
    questionsAnswered: 0,
    correctAnswers: 0
  });
  const [selectedAnswer, setSelectedAnswer] = useState<string | null>(null);
  const [showResult, setShowResult] = useState(false);
  const [battleActive, setBattleActive] = useState(false);
  const [timeLeft, setTimeLeft] = useState(60); // 60 seconds per question
  const [loading, setLoading] = useState(true);

  const subjects = [
    { id: '550e8400-e29b-41d4-a716-446655440001', name: 'Matemáticas', icon: '🔢', enemy: 'Dragón de los Números' },
    { id: '550e8400-e29b-41d4-a716-446655440002', name: 'Lenguaje', icon: '📖', enemy: 'Esfinge de las Palabras' },
    { id: '550e8400-e29b-41d4-a716-446655440003', name: 'Ciencias Naturales', icon: '🧬', enemy: 'Hidra del Conocimiento' },
    { id: '550e8400-e29b-41d4-a716-446655440004', name: 'Ciencias Sociales', icon: '🏛️', enemy: 'Titán de la Historia' },
    { id: '550e8400-e29b-41d4-a716-446655440005', name: 'Inglés', icon: '🌍', enemy: 'Fénix Lingüístico' }
  ];

  useEffect(() => {
    // Load user data and check level requirement
    const userData = localStorage.getItem('currentUser') || localStorage.getItem('user');
    if (userData) {
      const user = JSON.parse(userData);
      setCurrentUser(user);
      
      if (user.level < 10) {
        alert('🔒 Acceso Denegado\n\nLa Arena del Conocimiento requiere Nivel 10.\nTu nivel actual: ' + user.level + '\n\n¡Entrena más en la Biblioteca para subir de nivel!');
        router.push('/hub-central');
        return;
      }
    }
    setLoading(false);
  }, []);

  // Timer countdown
  useEffect(() => {
    if (battleActive && timeLeft > 0) {
      const timer = setInterval(() => {
        setTimeLeft(prev => prev - 1);
      }, 1000);
      return () => clearInterval(timer);
    } else if (timeLeft === 0 && battleActive) {
      // Time's up - treat as wrong answer
      handleAnswer('');
    }
  }, [battleActive, timeLeft]);

  const startBattle = async (subjectId: string) => {
    try {
      setLoading(true);
      const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:4000';
      
      const response = await fetch(`${API_URL}/api/v1/diagnostic-public/diagnostic-questions/${subjectId}?limit=10`);
      
      if (response.ok) {
        const data = await response.json();
        setQuestions(data);
        setSelectedSubject(subjectId);
        setBattleActive(true);
        setCurrentQuestionIndex(0);
        setTimeLeft(60);
        setBattleStats({
          hp: 100,
          maxHp: 100,
          mp: 50,
          maxMp: 50,
          combo: 0,
          score: 0,
          questionsAnswered: 0,
          correctAnswers: 0
        });
      } else {
        throw new Error('No se pudieron cargar las preguntas');
      }
    } catch (error) {
      console.error('Error starting battle:', error);
      alert('Error iniciando batalla. Intenta nuevamente.');
    } finally {
      setLoading(false);
    }
  };

  const handleAnswer = (answer: string) => {
    if (!battleActive || showResult) return;
    
    const currentQuestion = questions[currentQuestionIndex];
    const isCorrect = answer === currentQuestion.correct_answer;
    
    setSelectedAnswer(answer);
    setShowResult(true);
    
    // Update battle stats
    setBattleStats(prev => {
      const newStats = { ...prev };
      newStats.questionsAnswered += 1;
      
      if (isCorrect) {
        newStats.correctAnswers += 1;
        newStats.combo += 1;
        newStats.score += (10 + newStats.combo * 2) * currentQuestion.difficulty;
        newStats.mp = Math.min(newStats.maxMp, newStats.mp + 5);
        
        // Damage to enemy (visual effect)
        const damage = 20 + (newStats.combo * 5);
        console.log(`💥 Damage dealt: ${damage}`);
      } else {
        newStats.combo = 0;
        newStats.hp = Math.max(0, newStats.hp - 15);
        
        // Take damage
        console.log(`💔 HP lost: 15`);
      }
      
      return newStats;
    });
    
    // Auto-advance after showing result
    setTimeout(() => {
      if (currentQuestionIndex < questions.length - 1 && battleStats.hp > 0) {
        setCurrentQuestionIndex(prev => prev + 1);
        setSelectedAnswer(null);
        setShowResult(false);
        setTimeLeft(60);
      } else {
        // Battle finished
        endBattle();
      }
    }, 2000);
  };

  const endBattle = () => {
    setBattleActive(false);
    const finalScore = battleStats.score;
    const accuracy = battleStats.questionsAnswered > 0 ? (battleStats.correctAnswers / battleStats.questionsAnswered) * 100 : 0;
    
    let battleResult = '';
    let xpGained = 0;
    
    if (battleStats.hp > 0) {
      if (accuracy >= 80) {
        battleResult = '🏆 ¡VICTORIA ÉPICA!';
        xpGained = 500;
      } else if (accuracy >= 60) {
        battleResult = '⚔️ Victoria';
        xpGained = 300;
      } else {
        battleResult = '🛡️ Victoria por Supervivencia';
        xpGained = 200;
      }
    } else {
      battleResult = '💀 Derrota';
      xpGained = 100;
    }
    
    alert(`${battleResult}\n\n📊 Estadísticas de Batalla:\n• Preguntas: ${battleStats.correctAnswers}/${battleStats.questionsAnswered}\n• Precisión: ${accuracy.toFixed(1)}%\n• Combo máximo: ${battleStats.combo}\n• Puntuación: ${finalScore}\n\n⚡ +${xpGained} XP ganados!`);
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
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-red-400 mx-auto mb-4"></div>
          <h2 className="text-2xl font-bold mb-2">⚔️ Preparando Arena...</h2>
          <p className="text-purple-200">Invocando enemigos del conocimiento</p>
        </div>
      </div>
    );
  }

  // Battle Interface
  if (battleActive && questions.length > 0) {
    const currentQuestion = questions[currentQuestionIndex];
    const enemy = subjects.find(s => s.id === selectedSubject);
    
    return (
      <div className="min-h-screen bg-gradient-to-br from-red-900 via-purple-900 to-black text-white">
        <MainNavigation currentUser={currentUser} />
        
        <div className="pt-20 lg:pt-24 pb-8">
          <div className="container mx-auto px-4">
            {/* Battle HUD */}
            <div className="mb-6 bg-black/50 rounded-xl p-4 border border-red-500/30">
              <div className="flex justify-between items-center">
                {/* Player Stats */}
                <div className="flex items-center gap-4">
                  <div className="text-center">
                    <div className="text-blue-300 text-sm">Hunter {currentUser?.username}</div>
                    <div className="flex items-center gap-2">
                      <Heart className="w-4 h-4 text-red-400" />
                      <div className="w-24 bg-gray-700 rounded-full h-3">
                        <div 
                          className="bg-red-500 h-3 rounded-full transition-all"
                          style={{ width: `${(battleStats.hp / battleStats.maxHp) * 100}%` }}
                        />
                      </div>
                      <span className="text-sm">{battleStats.hp}/{battleStats.maxHp}</span>
                    </div>
                    <div className="flex items-center gap-2 mt-1">
                      <Zap className="w-4 h-4 text-blue-400" />
                      <div className="w-24 bg-gray-700 rounded-full h-3">
                        <div 
                          className="bg-blue-500 h-3 rounded-full transition-all"
                          style={{ width: `${(battleStats.mp / battleStats.maxMp) * 100}%` }}
                        />
                      </div>
                      <span className="text-sm">{battleStats.mp}/{battleStats.maxMp}</span>
                    </div>
                  </div>
                  
                  <div className="text-center">
                    <div className="text-gold-400 text-sm">Combo</div>
                    <div className="text-2xl font-bold text-gold-400">{battleStats.combo}x</div>
                  </div>
                </div>
                
                {/* Timer */}
                <div className="text-center">
                  <div className={`text-3xl font-bold ${timeLeft <= 10 ? 'text-red-400 animate-pulse' : 'text-white'}`}>
                    {formatTime(timeLeft)}
                  </div>
                  <div className="text-purple-300 text-sm">Tiempo restante</div>
                </div>
                
                {/* Enemy */}
                <div className="text-center">
                  <div className="text-red-300 text-sm">{enemy?.enemy}</div>
                  <div className="text-xl font-bold text-red-400">{enemy?.icon}</div>
                  <div className="text-sm text-purple-300">
                    Pregunta {currentQuestionIndex + 1}/{questions.length}
                  </div>
                </div>
              </div>
            </div>

            {/* Question */}
            <motion.div
              key={currentQuestionIndex}
              initial={{ opacity: 0, x: 50 }}
              animate={{ opacity: 1, x: 0 }}
              className="bg-black/40 rounded-xl p-6 border border-purple-500/30 mb-6"
            >
              <h2 className="text-xl font-bold text-white mb-4">
                {currentQuestion.question_text}
              </h2>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {Object.entries(currentQuestion.options).map(([key, value]) => (
                  <button
                    key={key}
                    onClick={() => handleAnswer(key)}
                    disabled={showResult}
                    className={`p-4 rounded-lg border-2 text-left transition-all transform hover:scale-105 ${
                      selectedAnswer === key
                        ? selectedAnswer === currentQuestion.correct_answer
                          ? 'bg-green-600/30 border-green-500 text-green-100'
                          : 'bg-red-600/30 border-red-500 text-red-100'
                        : showResult && key === currentQuestion.correct_answer
                          ? 'bg-green-600/30 border-green-500 text-green-100'
                          : 'bg-purple-800/30 border-purple-500/50 text-purple-100 hover:bg-purple-700/30 hover:border-purple-400/70'
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <div className={`w-8 h-8 rounded-full flex items-center justify-center font-bold ${
                        selectedAnswer === key
                          ? selectedAnswer === currentQuestion.correct_answer
                            ? 'bg-green-500 text-white'
                            : 'bg-red-500 text-white'
                          : showResult && key === currentQuestion.correct_answer
                            ? 'bg-green-500 text-white'
                            : 'bg-purple-600 text-white'
                      }`}>
                        {key}
                      </div>
                      <span>{value}</span>
                    </div>
                  </button>
                ))}
              </div>
              
              {/* Result Feedback */}
              <AnimatePresence>
                {showResult && (
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="mt-4 p-4 rounded-lg bg-black/50"
                  >
                    {selectedAnswer === currentQuestion.correct_answer ? (
                      <div className="text-green-300">
                        <div className="flex items-center gap-2 mb-2">
                          <CheckCircle className="w-5 h-5" />
                          <span className="font-bold">¡Correcto! +{10 + battleStats.combo * 2} puntos</span>
                        </div>
                        <p className="text-sm">{currentQuestion.explanation}</p>
                      </div>
                    ) : (
                      <div className="text-red-300">
                        <div className="flex items-center gap-2 mb-2">
                          <X className="w-5 h-5" />
                          <span className="font-bold">Incorrecto. -15 HP</span>
                        </div>
                        <p className="text-sm">Respuesta correcta: {currentQuestion.correct_answer}</p>
                        <p className="text-sm mt-1">{currentQuestion.explanation}</p>
                      </div>
                    )}
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.div>
          </div>
        </div>
      </div>
    );
  }

  // Subject Selection
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
              
              <h1 className="text-4xl font-bold bg-gradient-to-r from-red-400 to-pink-400 bg-clip-text text-transparent">
                ⚔️ Arena del Conocimiento
              </h1>
            </div>
            
            <p className="text-xl text-purple-200 mb-4">
              Práctica intensiva con preguntas tipo ICFES
            </p>
            
            {/* Level Badge */}
            <div className="inline-flex items-center gap-2 bg-green-800/50 px-4 py-2 rounded-lg">
              <CheckCircle className="w-4 h-4 text-green-400" />
              <span className="text-green-200">Nivel 10+ Requerido - ¡Desbloqueado!</span>
            </div>
          </motion.div>

          {/* Battle Instructions */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="max-w-4xl mx-auto mb-8 bg-black/30 rounded-xl p-6 border border-red-500/30"
          >
            <h2 className="text-2xl font-bold text-red-400 mb-4 text-center">🎯 Reglas de Combate</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h3 className="font-bold text-white mb-2">⚔️ Sistema de Batalla</h3>
                <ul className="text-sm text-purple-200 space-y-1">
                  <li>• Responde correctamente para atacar</li>
                  <li>• Respuestas incorrectas te hacen perder HP</li>
                  <li>• Mantén combos para más puntos</li>
                  <li>• 60 segundos por pregunta</li>
                </ul>
              </div>
              <div>
                <h3 className="font-bold text-white mb-2">🏆 Recompensas</h3>
                <ul className="text-sm text-gold-200 space-y-1">
                  <li>• Victoria épica: +500 XP</li>
                  <li>• Victoria normal: +300 XP</li>
                  <li>• Supervivencia: +200 XP</li>
                  <li>• Participación: +100 XP</li>
                </ul>
              </div>
            </div>
          </motion.div>

          {/* Enemy Selection */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {subjects.map((subject, index) => (
              <motion.div
                key={subject.id}
                initial={{ opacity: 0, y: 50 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
                className="group cursor-pointer"
                onClick={() => startBattle(subject.id)}
              >
                <div className="bg-gradient-to-br from-red-900/40 to-purple-900/40 rounded-xl p-6 border-2 border-red-500/30 hover:border-gold-500/50 transition-all transform hover:scale-105 backdrop-blur-sm">
                  <div className="text-center">
                    {/* Enemy Icon */}
                    <div className="w-20 h-20 rounded-full bg-gradient-to-r from-red-600 to-pink-600 flex items-center justify-center text-3xl mb-4 mx-auto shadow-lg group-hover:shadow-red-500/25 transition-all">
                      {subject.icon}
                    </div>
                    
                    <h3 className="text-xl font-bold text-white mb-2">{subject.enemy}</h3>
                    <p className="text-red-300 text-sm mb-4">{subject.name}</p>
                    
                    <div className="flex justify-center gap-4 text-xs text-purple-200 mb-4">
                      <div className="flex items-center gap-1">
                        <Target className="w-3 h-3" />
                        10 preguntas
                      </div>
                      <div className="flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        60s cada una
                      </div>
                      <div className="flex items-center gap-1">
                        <Trophy className="w-3 h-3" />
                        Hasta 500 XP
                      </div>
                    </div>
                    
                    <button className="bg-gradient-to-r from-red-600 to-pink-600 hover:shadow-lg hover:shadow-red-500/25 px-6 py-3 rounded-lg font-bold text-white transition-all transform hover:scale-105 w-full">
                      ⚔️ ¡Desafiar!
                    </button>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>

          {/* Back to Hub */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.8 }}
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
