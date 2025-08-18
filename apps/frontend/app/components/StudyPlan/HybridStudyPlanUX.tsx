'use client';

import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence, useScroll, useTransform } from 'framer-motion';
import confetti from 'canvas-confetti';
import { 
  BookOpen, Play, Lock, Unlock, CheckCircle, Star, Zap, TrendingUp,
  Trophy, Shield, Target, Eye, Clock, Award, Flame, Brain,
  ChevronRight, ChevronDown, Video, FileText, Users, BarChart3,
  Download, Share2, Heart, MessageCircle, ThumbsUp, Lightbulb,
  Calendar, Timer, ArrowRight, Sparkles, Crown, Medal
} from 'lucide-react';

// ===== TIPOS E INTERFACES =====
interface StudyUnit {
  id: string;
  number: number;
  title: string;
  description: string;
  difficulty: 'facil' | 'intermedio' | 'avanzado';
  estimatedTime: number;
  progress: number;
  isLocked: boolean;
  isCompleted: boolean;
  topics: StudyTopic[];
  xpReward: number;
  prerequisites?: string[];
}

interface StudyTopic {
  id: string;
  name: string;
  description: string;
  videos: number;
  exercises: number;
  isCompleted: boolean;
  difficulty: string;
  estimatedMinutes: number;
}

interface HybridStudyPlanProps {
  userId: string;
  subject: string;
  diagnosticScore: number;
  weakTopics: string[];
  strongTopics: string[];
  onUnitStart?: (unitId: string) => void;
  onTopicStart?: (topicId: string, unitId: string) => void;
  onProgressUpdate?: (unitId: string, progress: number) => void;
}

// ===== CONFIGURACIÓN Y CONSTANTES =====
const COURSERA_GRADIENTS = {
  primary: 'from-blue-600 via-purple-600 to-indigo-800',
  secondary: 'from-emerald-500 via-teal-600 to-cyan-600',
  success: 'from-green-500 via-emerald-500 to-teal-500',
  warning: 'from-yellow-500 via-orange-500 to-red-500',
  premium: 'from-purple-600 via-pink-600 to-rose-600'
};

const KHAN_ACADEMY_COLORS = {
  primary: '#1865f2',
  secondary: '#00a60e', 
  background: 'rgba(0, 0, 0, 0.3)',
  cardBg: 'rgba(255, 255, 255, 0.05)',
  textPrimary: '#ffffff',
  textSecondary: 'rgba(255, 255, 255, 0.7)'
};

const DIFFICULTY_STYLES = {
  facil: {
    color: 'bg-green-500/20 text-green-400 border-green-400/30',
    icon: '🟢',
    gradient: 'from-green-400 to-emerald-500'
  },
  intermedio: {
    color: 'bg-yellow-500/20 text-yellow-400 border-yellow-400/30', 
    icon: '🟡',
    gradient: 'from-yellow-400 to-orange-500'
  },
  avanzado: {
    color: 'bg-red-500/20 text-red-400 border-red-400/30',
    icon: '🔴', 
    gradient: 'from-red-400 to-pink-500'
  }
};

// ===== COMPONENTE PRINCIPAL =====
const HybridStudyPlanUX: React.FC<HybridStudyPlanProps> = ({
  userId,
  subject,
  diagnosticScore,
  weakTopics,
  strongTopics,
  onUnitStart,
  onTopicStart,
  onProgressUpdate
}) => {
  // Estados del componente
  const [units, setUnits] = useState<StudyUnit[]>([]);
  const [expandedUnits, setExpandedUnits] = useState<Set<string>>(new Set());
  const [userXP, setUserXP] = useState(0);
  const [currentRank, setCurrentRank] = useState('E');
  const [overallProgress, setOverallProgress] = useState(0);
  const [completedUnits, setCompletedUnits] = useState(0);
  const [totalStudyTime, setTotalStudyTime] = useState(0);
  const [selectedUnit, setSelectedUnit] = useState<StudyUnit | null>(null);
  const [showDetails, setShowDetails] = useState(false);
  const [loading, setLoading] = useState(true);

  // Referencias y scroll
  const containerRef = useRef<HTMLDivElement>(null);
  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ["start start", "end end"]
  });
  
  const headerY = useTransform(scrollYProgress, [0, 0.3], [0, -100]);
  const progressWidth = useTransform(scrollYProgress, [0, 1], ["0%", "100%"]);

  // ===== EFECTOS Y INICIALIZACIÓN =====
  useEffect(() => {
    generateHybridStudyPlan();
    calculateProgress();
  }, [subject, diagnosticScore, weakTopics]);

  const generateHybridStudyPlan = () => {
    // Generar plan híbrido basado en diagnóstico
    const sampleUnits: StudyUnit[] = [
      {
        id: 'unit-1',
        number: 1,
        title: 'Álgebra Avanzada',
        description: 'Funciones y expresiones complejas',
        difficulty: 'intermedio',
        estimatedTime: 720, // 12 horas en minutos
        progress: 0,
        isLocked: false,
        isCompleted: false,
        xpReward: 1500,
        topics: [
          {
            id: 'topic-1-1',
            name: 'Funciones cuadráticas',
            description: 'Aprende a trabajar con funciones de segundo grado',
            videos: 3,
            exercises: 25,
            isCompleted: false,
            difficulty: 'intermedio',
            estimatedMinutes: 180
          },
          {
            id: 'topic-1-2', 
            name: 'Polinomios',
            description: 'Operaciones y factorización de polinomios',
            videos: 4,
            exercises: 30,
            isCompleted: false,
            difficulty: 'intermedio',
            estimatedMinutes: 240
          },
          {
            id: 'topic-1-3',
            name: 'Factorización',
            description: 'Técnicas avanzadas de factorización',
            videos: 2,
            exercises: 28,
            isCompleted: false,
            difficulty: 'avanzado',
            estimatedMinutes: 300
          }
        ]
      },
      {
        id: 'unit-2',
        number: 2,
        title: 'Trigonometría',
        description: 'Funciones trigonométricas y aplicaciones',
        difficulty: 'avanzado',
        estimatedTime: 900, // 15 horas
        progress: 0,
        isLocked: true,
        isCompleted: false,
        xpReward: 2000,
        prerequisites: ['unit-1'],
        topics: [
          {
            id: 'topic-2-1',
            name: 'Razones trigonométricas',
            description: 'Seno, coseno y tangente en triángulos',
            videos: 5,
            exercises: 35,
            isCompleted: false,
            difficulty: 'intermedio',
            estimatedMinutes: 300
          }
        ]
      }
    ];

    setUnits(sampleUnits);
    setLoading(false);
  };

  const calculateProgress = () => {
    if (units.length === 0) return;
    
    const totalUnits = units.length;
    const completed = units.filter(unit => unit.isCompleted).length;
    const avgProgress = units.reduce((sum, unit) => sum + unit.progress, 0) / totalUnits;
    
    setCompletedUnits(completed);
    setOverallProgress(avgProgress);
    setTotalStudyTime(units.reduce((sum, unit) => sum + unit.estimatedTime, 0));
  };

  // ===== HANDLERS =====
  const handleUnitExpand = (unitId: string) => {
    setExpandedUnits(prev => {
      const newSet = new Set(prev);
      if (newSet.has(unitId)) {
        newSet.delete(unitId);
      } else {
        newSet.add(unitId);
      }
      return newSet;
    });
  };

  const handleTopicStart = (topicId: string, unitId: string) => {
    onTopicStart?.(topicId, unitId);
    
    // Celebración estilo Coursera
    confetti({
      particleCount: 50,
      spread: 60,
      origin: { y: 0.8 }
    });
  };

  const handleUnitStart = (unit: StudyUnit) => {
    if (unit.isLocked) return;
    
    setSelectedUnit(unit);
    setShowDetails(true);
    onUnitStart?.(unit.id);
  };

  const getDifficultyBadge = (difficulty: string) => {
    const style = DIFFICULTY_STYLES[difficulty as keyof typeof DIFFICULTY_STYLES];
    return (
      <span className={`px-3 py-1 rounded-full text-xs font-medium border ${style.color}`}>
        {style.icon} {difficulty.charAt(0).toUpperCase() + difficulty.slice(1)}
      </span>
    );
  };

  const formatTime = (minutes: number) => {
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return hours > 0 ? `${hours}h ${mins}m` : `${mins}m`;
  };

  // ===== RENDER =====
  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex items-center justify-center">
        <div className="text-center text-white">
          <div className="animate-spin w-16 h-16 border-4 border-purple-500 border-t-transparent rounded-full mx-auto mb-4"></div>
          <p className="text-lg font-medium">Generando tu plan personalizado...</p>
        </div>
      </div>
    );
  }

  return (
    <div 
      ref={containerRef}
      className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 text-white"
    >
      {/* ===== HEADER HÍBRIDO (Khan Academy + Coursera) ===== */}
      <motion.div 
        style={{ y: headerY }}
        className="sticky top-0 z-50 bg-black/40 backdrop-blur-xl border-b border-purple-500/30"
      >
        <div className="max-w-7xl mx-auto px-6 py-6">
          <div className="flex justify-between items-center">
            {/* Logo y Título (Khan Academy Style) */}
            <div className="flex items-center gap-4">
              <motion.div
                whileHover={{ rotate: 10, scale: 1.1 }}
                className="w-14 h-14 bg-gradient-to-br from-purple-500 to-pink-500 rounded-2xl flex items-center justify-center shadow-xl"
              >
                <Brain className="w-8 h-8 text-white" />
              </motion.div>
              <div>
                <h1 className="text-3xl font-bold bg-gradient-to-r from-white to-purple-200 bg-clip-text text-transparent">
                  Plan Personalizado de {subject}
                </h1>
                <p className="text-purple-300 flex items-center gap-2">
                  <Target className="w-4 h-4" />
                  Basado en tu diagnóstico ({diagnosticScore}%) • Nivel Intermedio
                </p>
              </div>
            </div>

            {/* Estadísticas (Coursera Style) */}
            <div className="flex items-center gap-6">
              <div className="text-center">
                <div className="text-4xl mb-1">
                  {currentRank === 'S' ? '👑' : currentRank === 'A' ? '🏆' : '🎯'}
                </div>
                <p className="text-xs text-purple-300">Rango {currentRank}</p>
              </div>
              
              <div className="bg-gradient-to-r from-purple-500/20 to-pink-500/20 backdrop-blur-sm rounded-xl px-6 py-3 border border-purple-400/30">
                <div className="flex items-center gap-2">
                  <Zap className="w-5 h-5 text-yellow-400" />
                  <span className="text-xl font-bold text-yellow-400">{userXP}</span>
                  <span className="text-purple-300 text-sm">XP</span>
                </div>
              </div>
            </div>
          </div>

          {/* Barra de Progreso Global */}
          <div className="mt-6">
            <div className="flex justify-between text-sm mb-2">
              <span className="text-purple-300">Progreso General</span>
              <span className="font-bold text-white">{Math.round(overallProgress)}%</span>
            </div>
            <div className="w-full bg-black/50 rounded-full h-3 overflow-hidden">
              <motion.div 
                className="h-full bg-gradient-to-r from-purple-500 via-pink-500 to-purple-600 rounded-full"
                style={{ width: progressWidth }}
                initial={{ width: "0%" }}
                animate={{ width: `${overallProgress}%` }}
                transition={{ duration: 1, ease: "easeOut" }}
              />
            </div>
          </div>
        </div>
      </motion.div>

      {/* ===== DASHBOARD DE ESTADÍSTICAS (Hybrid) ===== */}
      <div className="max-w-7xl mx-auto px-6 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 mb-8">
          {/* Progreso Principal */}
          <div className="lg:col-span-2">
            <motion.div 
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-black/30 backdrop-blur-xl rounded-2xl p-6 border border-purple-500/20"
            >
              <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
                <BarChart3 className="w-5 h-5 text-emerald-400" />
                Tu Progreso Detallado
              </h2>
              
              <div className="grid grid-cols-3 gap-4 text-center">
                <div>
                  <p className="text-3xl font-bold text-purple-400">{completedUnits}</p>
                  <p className="text-xs text-purple-300">Unidades Completadas</p>
                </div>
                <div>
                  <p className="text-3xl font-bold text-blue-400">{units.reduce((sum, unit) => sum + unit.topics.filter(t => t.isCompleted).length, 0)}</p>
                  <p className="text-xs text-purple-300">Temas Dominados</p>
                </div>
                <div>
                  <p className="text-3xl font-bold text-emerald-400">{formatTime(totalStudyTime)}</p>
                  <p className="text-xs text-purple-300">Tiempo Total</p>
                </div>
              </div>
            </motion.div>
          </div>

          {/* Sesión de Hoy (Khan Academy Style) */}
          <div className="lg:col-span-2">
            <motion.div 
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 }}
              className="bg-black/30 backdrop-blur-xl rounded-2xl p-6 border border-purple-500/20"
            >
              <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
                <Calendar className="w-5 h-5 text-blue-400" />
                Sesión de Hoy
              </h3>
              
              <div className="space-y-3">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-cyan-500 rounded-lg flex items-center justify-center">
                    <BookOpen className="w-5 h-5 text-white" />
                  </div>
                  <div>
                    <p className="font-medium">Funciones cuadráticas</p>
                    <p className="text-purple-300 text-sm flex items-center gap-1">
                      <Timer className="w-3 h-3" />
                      60-90 minutos recomendados
                    </p>
                  </div>
                </div>
              </div>
              
              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                className="w-full mt-4 px-4 py-3 bg-gradient-to-r from-purple-600 to-pink-600 rounded-xl font-bold hover:from-purple-700 hover:to-pink-700 transition-all shadow-lg"
              >
                Comenzar Sesión de Hoy
              </motion.button>
            </motion.div>
          </div>
        </div>

        {/* ===== UNIDADES DE ESTUDIO (Hybrid Layout) ===== */}
        <div className="space-y-6">
          <h2 className="text-2xl font-bold mb-6 flex items-center gap-2">
            <BookOpen className="w-6 h-6 text-purple-400" />
            Unidades del Curso
          </h2>
          
          {units.map((unit, index) => (
            <motion.div
              key={unit.id}
              initial={{ opacity: 0, x: -50 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.1 }}
              className={`
                bg-black/30 backdrop-blur-xl rounded-2xl overflow-hidden border 
                ${unit.isLocked ? 'border-gray-600/30 opacity-75' : 'border-purple-500/20 hover:border-purple-400/40'}
                transition-all duration-300 hover:transform hover:scale-[1.01]
              `}
            >
              {/* Header de Unidad */}
              <div className="p-6">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-6">
                    {/* Número de Unidad (Khan Academy Style) */}
                    <div className={`
                      w-16 h-16 rounded-2xl flex items-center justify-center text-white font-bold text-xl
                      ${unit.isLocked 
                        ? 'bg-gray-600' 
                        : `bg-gradient-to-br ${DIFFICULTY_STYLES[unit.difficulty].gradient}`
                      }
                    `}>
                      {unit.isLocked ? <Lock className="w-6 h-6" /> : unit.number}
                    </div>
                    
                    {/* Información de Unidad */}
                    <div>
                      <h3 className="text-2xl font-bold text-white mb-1">{unit.title}</h3>
                      <p className="text-purple-300 mb-3">{unit.description}</p>
                      
                      <div className="flex items-center gap-4 flex-wrap">
                        {getDifficultyBadge(unit.difficulty)}
                        <span className="text-purple-300 text-sm flex items-center gap-1">
                          <Clock className="w-4 h-4" />
                          {formatTime(unit.estimatedTime)}
                        </span>
                        <span className="text-purple-300 text-sm flex items-center gap-1">
                          <BookOpen className="w-4 h-4" />
                          {unit.topics.length} temas
                        </span>
                        {!unit.isLocked && (
                          <span className="text-yellow-400 text-sm flex items-center gap-1">
                            <Zap className="w-4 h-4" />
                            {unit.xpReward} XP
                          </span>
                        )}
                        {unit.isLocked && (
                          <span className="text-yellow-400 text-sm flex items-center gap-1">
                            <Lock className="w-4 h-4" />
                            Bloqueada
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                  
                  {/* Progreso y Controles (Coursera Style) */}
                  <div className="text-right">
                    <div className="mb-4">
                      <p className="text-3xl font-bold text-purple-400">{Math.round(unit.progress)}%</p>
                      <p className="text-xs text-purple-300">Completado</p>
                    </div>
                    
                    <div className="flex gap-2">
                      {!unit.isLocked && (
                        <motion.button
                          whileHover={{ scale: 1.05 }}
                          whileTap={{ scale: 0.95 }}
                          onClick={() => handleUnitExpand(unit.id)}
                          className="px-4 py-2 bg-purple-600/30 hover:bg-purple-600/50 rounded-lg transition-colors"
                        >
                          {expandedUnits.has(unit.id) ? (
                            <ChevronDown className="w-4 h-4" />
                          ) : (
                            <ChevronRight className="w-4 h-4" />
                          )}
                        </motion.button>
                      )}
                      
                      <motion.button
                        whileHover={{ scale: 1.05 }}
                        whileTap={{ scale: 0.95 }}
                        onClick={() => handleUnitStart(unit)}
                        disabled={unit.isLocked}
                        className={`
                          px-6 py-2 rounded-lg font-medium transition-all
                          ${unit.isLocked 
                            ? 'bg-gray-600/30 text-gray-400 cursor-not-allowed'
                            : 'bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white shadow-lg'
                          }
                        `}
                      >
                        {unit.isLocked ? 'Bloqueada' : 'Comenzar'}
                      </motion.button>
                    </div>
                  </div>
                </div>
                
                {/* Barra de Progreso de Unidad */}
                {!unit.isLocked && (
                  <div className="mt-6">
                    <div className="w-full bg-black/50 rounded-full h-2 overflow-hidden">
                      <motion.div 
                        className={`h-full bg-gradient-to-r ${DIFFICULTY_STYLES[unit.difficulty].gradient} rounded-full`}
                        initial={{ width: "0%" }}
                        animate={{ width: `${unit.progress}%` }}
                        transition={{ duration: 0.8, ease: "easeOut" }}
                      />
                    </div>
                  </div>
                )}
              </div>

              {/* Temas Expandibles (Khan Academy Style) */}
              <AnimatePresence>
                {expandedUnits.has(unit.id) && !unit.isLocked && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: "auto", opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    transition={{ duration: 0.3 }}
                    className="border-t border-purple-500/20"
                  >
                    <div className="p-6 space-y-4">
                      {unit.topics.map((topic, topicIndex) => (
                        <motion.div
                          key={topic.id}
                          initial={{ opacity: 0, x: -20 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ delay: topicIndex * 0.1 }}
                          className="flex items-center justify-between p-4 bg-black/20 rounded-xl hover:bg-black/30 transition-all"
                        >
                          <div className="flex items-center gap-4">
                            <div className={`
                              w-10 h-10 rounded-full flex items-center justify-center text-white text-sm font-bold
                              ${topic.isCompleted 
                                ? 'bg-green-500' 
                                : 'bg-gray-600'
                              }
                            `}>
                              {topic.isCompleted ? (
                                <CheckCircle className="w-5 h-5" />
                              ) : (
                                topicIndex + 1
                              )}
                            </div>
                            
                            <div>
                              <p className="font-medium text-white">{topic.name}</p>
                              <p className="text-purple-300 text-sm mb-2">{topic.description}</p>
                              <div className="flex items-center gap-4 text-sm text-purple-300">
                                <span className="flex items-center gap-1">
                                  <Video className="w-4 h-4" />
                                  {topic.videos} videos
                                </span>
                                <span className="flex items-center gap-1">
                                  <FileText className="w-4 h-4" />
                                  {topic.exercises} ejercicios
                                </span>
                                <span className="flex items-center gap-1">
                                  <Timer className="w-4 h-4" />
                                  {formatTime(topic.estimatedMinutes)}
                                </span>
                                {getDifficultyBadge(topic.difficulty)}
                              </div>
                            </div>
                          </div>
                          
                          <motion.button
                            whileHover={{ scale: 1.05 }}
                            whileTap={{ scale: 0.95 }}
                            onClick={() => handleTopicStart(topic.id, unit.id)}
                            className={`
                              px-4 py-2 rounded-lg font-medium transition-all
                              ${topic.isCompleted
                                ? 'bg-green-500/20 text-green-400 border border-green-400/30'
                                : 'bg-purple-600 hover:bg-purple-700 text-white'
                              }
                            `}
                          >
                            {topic.isCompleted ? 'Completado' : 'Comenzar'}
                          </motion.button>
                        </motion.div>
                      ))}
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.div>
          ))}
        </div>

        {/* ===== RECOMENDACIONES PERSONALIZADAS ===== */}
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
          className="mt-12 bg-black/30 backdrop-blur-xl rounded-2xl p-6 border border-purple-500/20"
        >
          <h2 className="text-xl font-bold mb-6 flex items-center gap-2">
            <Lightbulb className="w-5 h-5 text-yellow-400" />
            Recomendaciones Personalizadas
          </h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <p className="text-purple-300 text-sm mb-1">Enfoque Principal</p>
              <p className="font-medium text-white">Consolidación de conceptos intermedios</p>
            </div>
            <div>
              <p className="text-purple-300 text-sm mb-1">Tiempo Diario Recomendado</p>
              <p className="font-medium text-white">60-90 minutos</p>
            </div>
            <div>
              <p className="text-purple-300 text-sm mb-1">Estrategia</p>
              <p className="font-medium text-white">Practica consistentemente y revisa conceptos fundamentales</p>
            </div>
            <div>
              <p className="text-purple-300 text-sm mb-1">Temas Prioritarios</p>
              <div className="flex flex-wrap gap-2 mt-2">
                {weakTopics.slice(0, 3).map((topic, index) => (
                  <span 
                    key={index}
                    className="px-3 py-1 bg-red-500/20 text-red-300 rounded-full text-sm border border-red-400/30"
                  >
                    {topic}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  );
};

export default HybridStudyPlanUX;
