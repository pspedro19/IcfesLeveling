'use client';

import React, { useState, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  BookOpen, 
  Play, 
  CheckCircle, 
  Lock, 
  Clock,
  TrendingUp,
  Award,
  Calendar,
  Target,
  Zap,
  ChevronRight,
  ChevronDown,
  Brain,
  Video,
  FileText,
  Star,
  BarChart3,
  Users,
  Trophy,
  Sparkles,
  Coffee,
  Moon,
  Sun
} from 'lucide-react';

interface Topic {
  name: string;
  videos: string[];
  exercises: number;
  completed?: boolean;
}

interface Unit {
  number: number;
  title: string;
  description: string;
  topics: Topic[];
  estimated_hours: number;
  difficulty: string;
  progress?: number;
}

interface StudyPlan {
  id: string;
  subject: string;
  subject_id: string;
  title: string;
  description: string;
  units: Unit[];
  total_units: number;
  estimated_total_hours: number;
  recommendations: {
    focus: string;
    daily_time: string;
    strategy: string;
    priority_topics: string[];
  };
  progress: {
    completed_units: number;
    completed_topics: number;
    total_topics: number;
    percentage: number;
  };
  gamification: {
    current_rank: string;
    xp_earned: number;
    achievements: string[];
    next_milestone: string;
  };
  weekly_schedule: Record<string, { topic: string; time: string }>;
  difficulty_level: string;
  diagnostic_score: number;
}

export default function StudyPlanView() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [studyPlan, setStudyPlan] = useState<StudyPlan | null>(null);
  const [loading, setLoading] = useState(true);
  const [expandedUnits, setExpandedUnits] = useState<number[]>([1]);
  const [activeTab, setActiveTab] = useState<'overview' | 'units' | 'schedule' | 'progress'>('overview');
  const [currentTime, setCurrentTime] = useState(new Date());

  useEffect(() => {
    loadStudyPlan();
    const timer = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  const loadStudyPlan = async () => {
    try {
      const subjectId = searchParams.get('subject') || sessionStorage.getItem('last_subject_id') || '2a9c9371-b931-41d4-8d3e-ce5aae91a5c3';
      const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:4000';
      
      const response = await fetch(`${API_URL}/api/v1/study-plans/generate/${subjectId}`);
      
      if (response.ok) {
        const data = await response.json();
        setStudyPlan(data);
      } else {
        throw new Error('Failed to load study plan');
      }
    } catch (error) {
      console.error('Error loading study plan:', error);
    } finally {
      setLoading(false);
    }
  };

  const toggleUnit = (unitNumber: number) => {
    setExpandedUnits(prev => 
      prev.includes(unitNumber) 
        ? prev.filter(n => n !== unitNumber)
        : [...prev, unitNumber]
    );
  };

  const getDifficultyColor = (difficulty: string) => {
    switch(difficulty.toLowerCase()) {
      case 'básico': return 'text-green-400 bg-green-500/20';
      case 'intermedio': return 'text-yellow-400 bg-yellow-500/20';
      case 'avanzado': return 'text-red-400 bg-red-500/20';
      default: return 'text-blue-400 bg-blue-500/20';
    }
  };

  const getRankIcon = (rank: string) => {
    switch(rank) {
      case 'S': return '👑';
      case 'A': return '🏆';
      case 'B': return '🥈';
      case 'C': return '🥉';
      case 'D': return '⭐';
      default: return '🌟';
    }
  };

  const getDayOfWeek = () => {
    const days = ['sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday'];
    return days[currentTime.getDay()];
  };

  const getGreeting = () => {
    const hour = currentTime.getHours();
    if (hour < 12) return { text: 'Buenos días', icon: <Sun className="w-5 h-5" /> };
    if (hour < 18) return { text: 'Buenas tardes', icon: <Coffee className="w-5 h-5" /> };
    return { text: 'Buenas noches', icon: <Moon className="w-5 h-5" /> };
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-indigo-900 via-purple-900 to-pink-900 flex items-center justify-center">
        <motion.div
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          className="text-center"
        >
          <div className="animate-spin rounded-full h-16 w-16 border-t-4 border-purple-500 mx-auto mb-4"></div>
          <p className="text-white text-xl">Generando tu plan personalizado...</p>
        </motion.div>
      </div>
    );
  }

  if (!studyPlan) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-indigo-900 via-purple-900 to-pink-900 flex items-center justify-center">
        <div className="text-center">
          <p className="text-white text-xl mb-4">No se pudo cargar el plan de estudio</p>
          <button
            onClick={() => router.push('/diagnostic-test')}
            className="px-6 py-3 bg-purple-600 hover:bg-purple-700 text-white rounded-lg"
          >
            Volver
          </button>
        </div>
      </div>
    );
  }

  const greeting = getGreeting();
  const todaySchedule = studyPlan.weekly_schedule[getDayOfWeek()];

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-900 via-purple-900 to-pink-900">
      {/* Khan Academy Style Header */}
      <div className="bg-black/30 backdrop-blur-lg border-b border-purple-500/30">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <div className="flex justify-between items-center">
            <div className="flex items-center gap-4">
              <motion.div
                initial={{ rotate: -180, opacity: 0 }}
                animate={{ rotate: 0, opacity: 1 }}
                className="w-12 h-12 bg-gradient-to-br from-purple-500 to-pink-500 rounded-xl flex items-center justify-center"
              >
                <Brain className="w-7 h-7 text-white" />
              </motion.div>
              <div>
                <h1 className="text-2xl font-bold text-white">{studyPlan.title}</h1>
                <p className="text-purple-300 flex items-center gap-2">
                  {greeting.icon}
                  <span>{greeting.text}! Hoy toca: {todaySchedule?.topic}</span>
                </p>
              </div>
            </div>
            
            <div className="flex items-center gap-6">
              {/* Rank Display */}
              <div className="text-center">
                <div className="text-3xl">{getRankIcon(studyPlan.gamification.current_rank)}</div>
                <p className="text-xs text-purple-300">Rango {studyPlan.gamification.current_rank}</p>
              </div>
              
              {/* XP Display */}
              <div className="bg-purple-500/20 rounded-lg px-4 py-2">
                <div className="flex items-center gap-2">
                  <Zap className="w-5 h-5 text-yellow-400" />
                  <span className="text-white font-bold">{studyPlan.gamification.xp_earned} XP</span>
                </div>
              </div>
            </div>
          </div>
          
          {/* Navigation Tabs */}
          <div className="flex gap-2 mt-6">
            {(['overview', 'units', 'schedule', 'progress'] as const).map(tab => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`px-4 py-2 rounded-lg font-medium transition-all ${
                  activeTab === tab
                    ? 'bg-purple-600 text-white'
                    : 'bg-black/20 text-purple-300 hover:bg-purple-600/30'
                }`}
              >
                {tab === 'overview' && 'Vista General'}
                {tab === 'units' && 'Unidades'}
                {tab === 'schedule' && 'Horario'}
                {tab === 'progress' && 'Progreso'}
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 py-8">
        <AnimatePresence mode="wait">
          {/* Overview Tab */}
          {activeTab === 'overview' && (
            <motion.div
              key="overview"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="grid grid-cols-1 lg:grid-cols-3 gap-6"
            >
              {/* Main Stats */}
              <div className="lg:col-span-2 space-y-6">
                {/* Progress Card */}
                <div className="bg-black/30 backdrop-blur-xl rounded-2xl p-6 border border-purple-500/30">
                  <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                    <TrendingUp className="w-5 h-5 text-green-400" />
                    Tu Progreso
                  </h2>
                  
                  <div className="mb-4">
                    <div className="flex justify-between text-sm mb-2">
                      <span className="text-purple-300">Progreso General</span>
                      <span className="text-white font-bold">{studyPlan.progress.percentage}%</span>
                    </div>
                    <div className="w-full bg-black/50 rounded-full h-3">
                      <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: `${studyPlan.progress.percentage}%` }}
                        className="bg-gradient-to-r from-purple-500 to-pink-500 h-3 rounded-full"
                      />
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-3 gap-4">
                    <div className="text-center">
                      <p className="text-2xl font-bold text-purple-400">{studyPlan.progress.completed_units}</p>
                      <p className="text-xs text-purple-300">Unidades Completadas</p>
                    </div>
                    <div className="text-center">
                      <p className="text-2xl font-bold text-blue-400">{studyPlan.progress.completed_topics}</p>
                      <p className="text-xs text-purple-300">Temas Dominados</p>
                    </div>
                    <div className="text-center">
                      <p className="text-2xl font-bold text-green-400">{studyPlan.estimated_total_hours}h</p>
                      <p className="text-xs text-purple-300">Tiempo Estimado</p>
                    </div>
                  </div>
                </div>

                {/* Recommendations */}
                <div className="bg-black/30 backdrop-blur-xl rounded-2xl p-6 border border-purple-500/30">
                  <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                    <Target className="w-5 h-5 text-yellow-400" />
                    Recomendaciones Personalizadas
                  </h2>
                  
                  <div className="space-y-4">
                    <div>
                      <p className="text-purple-300 text-sm mb-1">Enfoque Principal</p>
                      <p className="text-white">{studyPlan.recommendations.focus}</p>
                    </div>
                    
                    <div>
                      <p className="text-purple-300 text-sm mb-1">Tiempo Diario Recomendado</p>
                      <p className="text-white flex items-center gap-2">
                        <Clock className="w-4 h-4 text-blue-400" />
                        {studyPlan.recommendations.daily_time}
                      </p>
                    </div>
                    
                    <div>
                      <p className="text-purple-300 text-sm mb-1">Estrategia</p>
                      <p className="text-white">{studyPlan.recommendations.strategy}</p>
                    </div>
                    
                    <div>
                      <p className="text-purple-300 text-sm mb-2">Temas Prioritarios</p>
                      <div className="flex flex-wrap gap-2">
                        {studyPlan.recommendations.priority_topics.map((topic, i) => (
                          <span key={i} className="px-3 py-1 bg-purple-600/30 rounded-full text-purple-300 text-sm">
                            {topic}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Sidebar */}
              <div className="space-y-6">
                {/* Level Card */}
                <div className="bg-black/30 backdrop-blur-xl rounded-2xl p-6 border border-purple-500/30">
                  <h3 className="text-lg font-bold text-white mb-4">Tu Nivel</h3>
                  <div className="text-center">
                    <div className={`inline-block px-4 py-2 rounded-lg ${getDifficultyColor(studyPlan.difficulty_level)}`}>
                      <p className="text-2xl font-bold">{studyPlan.difficulty_level}</p>
                    </div>
                    <p className="text-purple-300 mt-2">Basado en tu diagnóstico</p>
                    <p className="text-3xl font-bold text-white mt-2">{studyPlan.diagnostic_score}%</p>
                  </div>
                </div>

                {/* Next Milestone */}
                <div className="bg-gradient-to-br from-purple-600/30 to-pink-600/30 rounded-2xl p-6 border border-purple-500/30">
                  <h3 className="text-lg font-bold text-white mb-2 flex items-center gap-2">
                    <Trophy className="w-5 h-5 text-yellow-400" />
                    Próximo Logro
                  </h3>
                  <p className="text-purple-200">{studyPlan.gamification.next_milestone}</p>
                </div>

                {/* Today\'s Focus */}
                <div className="bg-black/30 backdrop-blur-xl rounded-2xl p-6 border border-purple-500/30">
                  <h3 className="text-lg font-bold text-white mb-4">Hoy</h3>
                  <div className="space-y-3">
                    <div className="flex items-center gap-3">
                      <BookOpen className="w-5 h-5 text-blue-400" />
                      <div>
                        <p className="text-white font-medium">{todaySchedule?.topic}</p>
                        <p className="text-purple-300 text-sm">{todaySchedule?.time}</p>
                      </div>
                    </div>
                  </div>
                  
                  <button className="w-full mt-4 px-4 py-3 bg-gradient-to-r from-purple-600 to-pink-600 rounded-lg text-white font-bold hover:from-purple-700 hover:to-pink-700 transition-all">
                    Comenzar Sesión de Hoy
                  </button>
                </div>
              </div>
            </motion.div>
          )}

          {/* Units Tab */}
          {activeTab === 'units' && (
            <motion.div
              key="units"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="space-y-6"
            >
              {studyPlan.units.map((unit, index) => (
                <motion.div
                  key={unit.number}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.1 }}
                  className="bg-black/30 backdrop-blur-xl rounded-2xl border border-purple-500/30 overflow-hidden"
                >
                  <button
                    onClick={() => toggleUnit(unit.number)}
                    className="w-full p-6 flex items-center justify-between hover:bg-purple-600/10 transition-colors"
                  >
                    <div className="flex items-center gap-4">
                      <div className="w-12 h-12 bg-gradient-to-br from-purple-500 to-pink-500 rounded-xl flex items-center justify-center text-white font-bold text-xl">
                        {unit.number}
                      </div>
                      <div className="text-left">
                        <h3 className="text-xl font-bold text-white">{unit.title}</h3>
                        <p className="text-purple-300">{unit.description}</p>
                        <div className="flex items-center gap-4 mt-2">
                          <span className={`px-2 py-1 rounded text-xs ${getDifficultyColor(unit.difficulty)}`}>
                            {unit.difficulty}
                          </span>
                          <span className="text-purple-300 text-sm flex items-center gap-1">
                            <Clock className="w-4 h-4" />
                            {unit.estimated_hours} horas
                          </span>
                          <span className="text-purple-300 text-sm">
                            {unit.topics.length} temas
                          </span>
                        </div>
                      </div>
                    </div>
                    
                    <div className="flex items-center gap-4">
                      <div className="text-right">
                        <p className="text-2xl font-bold text-purple-400">0%</p>
                        <p className="text-xs text-purple-300">Completado</p>
                      </div>
                      {expandedUnits.includes(unit.number) ? (
                        <ChevronDown className="w-6 h-6 text-purple-400" />
                      ) : (
                        <ChevronRight className="w-6 h-6 text-purple-400" />
                      )}
                    </div>
                  </button>
                  
                  <AnimatePresence>
                    {expandedUnits.includes(unit.number) && (
                      <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        className="border-t border-purple-500/30"
                      >
                        <div className="p-6 space-y-4">
                          {unit.topics.map((topic, topicIndex) => {
                            const isWeakness = topic.is_weakness || false;
                            const priority = topic.priority || 'NORMAL';
                            const confidenceScore = topic.confidence_score || 0.8;
                            
                            return (
                              <div
                                key={topicIndex}
                                className={`flex items-center justify-between p-4 rounded-lg transition-all ${
                                  isWeakness 
                                    ? priority === 'HIGH' 
                                      ? 'bg-red-900/30 border border-red-500/50' 
                                      : 'bg-yellow-900/30 border border-yellow-500/50'
                                    : 'bg-black/20 border border-gray-700'
                                }`}
                              >
                                <div className="flex items-center gap-4">
                                  <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                                    topic.completed ? 'bg-green-500' : 
                                    isWeakness ? (priority === 'HIGH' ? 'bg-red-600' : 'bg-yellow-600') : 'bg-gray-600'
                                  }`}>
                                    {topic.completed ? (
                                      <CheckCircle className="w-5 h-5 text-white" />
                                    ) : isWeakness ? (
                                      <span className="text-white font-bold">!</span>
                                    ) : (
                                      <span className="text-white text-sm">{topicIndex + 1}</span>
                                    )}
                                  </div>
                                  <div>
                                    <div className="flex items-center gap-2">
                                      <p className="text-white font-medium">{topic.name}</p>
                                      {isWeakness && (
                                        <span className={`px-2 py-1 rounded-full text-xs font-bold ${
                                          priority === 'HIGH' 
                                            ? 'bg-red-500/20 text-red-400' 
                                            : 'bg-yellow-500/20 text-yellow-400'
                                        }`}>
                                          {priority === 'HIGH' ? '⚠️ URGENTE' : '📚 REVISAR'}
                                        </span>
                                      )}
                                    </div>
                                    <div className="flex items-center gap-4 mt-1">
                                      <span className="text-purple-300 text-sm flex items-center gap-1">
                                        <Video className="w-4 h-4" />
                                        {topic.videos?.length || 1} videos
                                        {isWeakness && <span className="text-green-400">(+extra)</span>}
                                      </span>
                                      <span className="text-purple-300 text-sm flex items-center gap-1">
                                        <FileText className="w-4 h-4" />
                                        {topic.exercises} ejercicios
                                        {isWeakness && <span className="text-green-400">(+10)</span>}
                                      </span>
                                      {confidenceScore < 0.7 && (
                                        <span className="text-orange-400 text-sm flex items-center gap-1">
                                          <Target className="w-4 h-4" />
                                          Confianza: {Math.round(confidenceScore * 100)}%
                                        </span>
                                      )}
                                    </div>
                                    {isWeakness && (
                                      <div className="mt-2 text-xs text-gray-400">
                                        💡 Detectada debilidad estadística - Plan adaptado para tu mejora
                                      </div>
                                    )}
                                  </div>
                                </div>
                                
                                <button 
                                  onClick={() => {
                                    // Track analytics
                                    fetch('/api/v1/analytics/track', {
                                      method: 'POST',
                                      headers: { 'Content-Type': 'application/json' },
                                      body: JSON.stringify({
                                        type: 'topic_start',
                                        data: {
                                          topic: topic.name,
                                          is_weakness: isWeakness,
                                          priority: priority,
                                          unit: unit.number
                                        }
                                      })
                                    });
                                    
                                    router.push(`/video-player?topic=${encodeURIComponent(topic.name)}&unit=${unit.number}&videos=${topic.videos?.length || 1}&priority=${priority}`);
                                  }}
                                  className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                                    isWeakness
                                      ? priority === 'HIGH'
                                        ? 'bg-red-600 hover:bg-red-700 text-white animate-pulse'
                                        : 'bg-yellow-600 hover:bg-yellow-700 text-white'
                                      : 'bg-purple-600 hover:bg-purple-700 text-white'
                                  }`}
                                >
                                  {isWeakness ? (priority === 'HIGH' ? '🚨 Empezar YA' : '📚 Estudiar') : 'Comenzar'}
                                </button>
                              </div>
                            );
                          })}
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </motion.div>
              ))}
            </motion.div>
          )}

          {/* Schedule Tab */}
          {activeTab === 'schedule' && (
            <motion.div
              key="schedule"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="bg-black/30 backdrop-blur-xl rounded-2xl p-6 border border-purple-500/30"
            >
              <h2 className="text-2xl font-bold text-white mb-6 flex items-center gap-2">
                <Calendar className="w-6 h-6 text-purple-400" />
                Horario Semanal Personalizado
              </h2>
              
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                {Object.entries(studyPlan.weekly_schedule).map(([day, schedule]) => (
                  <div
                    key={day}
                    className={`p-4 rounded-lg border ${
                      day === getDayOfWeek()
                        ? 'bg-purple-600/30 border-purple-400'
                        : 'bg-black/20 border-purple-500/30'
                    }`}
                  >
                    <h3 className="text-white font-bold mb-2 capitalize">
                      {day === 'monday' && 'Lunes'}
                      {day === 'tuesday' && 'Martes'}
                      {day === 'wednesday' && 'Miércoles'}
                      {day === 'thursday' && 'Jueves'}
                      {day === 'friday' && 'Viernes'}
                      {day === 'saturday' && 'Sábado'}
                      {day === 'sunday' && 'Domingo'}
                      {day === getDayOfWeek() && ' (Hoy)'}
                    </h3>
                    <p className="text-purple-300 text-sm mb-1">{schedule.topic}</p>
                    <p className="text-white font-medium flex items-center gap-1">
                      <Clock className="w-4 h-4 text-blue-400" />
                      {schedule.time}
                    </p>
                  </div>
                ))}
              </div>
              
              <div className="mt-8 p-6 bg-gradient-to-r from-purple-600/20 to-pink-600/20 rounded-lg border border-purple-500/30">
                <h3 className="text-lg font-bold text-white mb-2">💡 Tip de Estudio</h3>
                <p className="text-purple-200">
                  Mantén una rutina consistente. Estudiar a la misma hora cada día ayuda a crear hábitos duraderos
                  y mejora la retención del conocimiento.
                </p>
              </div>
            </motion.div>
          )}

          {/* Progress Tab */}
          {activeTab === 'progress' && (
            <motion.div
              key="progress"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="space-y-6"
            >
              {/* Stats Grid */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="bg-black/30 backdrop-blur-xl rounded-2xl p-6 border border-purple-500/30">
                  <div className="flex items-center justify-between mb-4">
                    <BarChart3 className="w-8 h-8 text-blue-400" />
                    <span className="text-3xl font-bold text-white">
                      {studyPlan.progress.percentage}%
                    </span>
                  </div>
                  <p className="text-purple-300">Progreso Total</p>
                </div>
                
                <div className="bg-black/30 backdrop-blur-xl rounded-2xl p-6 border border-purple-500/30">
                  <div className="flex items-center justify-between mb-4">
                    <Trophy className="w-8 h-8 text-yellow-400" />
                    <span className="text-3xl font-bold text-white">
                      {studyPlan.gamification.current_rank}
                    </span>
                  </div>
                  <p className="text-purple-300">Rango Actual</p>
                </div>
                
                <div className="bg-black/30 backdrop-blur-xl rounded-2xl p-6 border border-purple-500/30">
                  <div className="flex items-center justify-between mb-4">
                    <Zap className="w-8 h-8 text-green-400" />
                    <span className="text-3xl font-bold text-white">
                      {studyPlan.gamification.xp_earned}
                    </span>
                  </div>
                  <p className="text-purple-300">XP Ganados</p>
                </div>
              </div>

              {/* Achievements */}
              <div className="bg-black/30 backdrop-blur-xl rounded-2xl p-6 border border-purple-500/30">
                <h3 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                  <Award className="w-5 h-5 text-yellow-400" />
                  Logros Desbloqueados
                </h3>
                {studyPlan.gamification.achievements.length > 0 ? (
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    {studyPlan.gamification.achievements.map((achievement, i) => (
                      <div key={i} className="text-center p-4 bg-black/20 rounded-lg">
                        <div className="text-3xl mb-2">🏆</div>
                        <p className="text-purple-300 text-sm">{achievement}</p>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-purple-300">Completa unidades para desbloquear logros</p>
                )}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
        
        {/* Action Buttons */}
        <div className="mt-8 flex gap-4 justify-center">
          <button
            onClick={() => router.push('/diagnostic-test')}
            className="px-6 py-3 bg-black/30 backdrop-blur-xl rounded-lg text-purple-300 hover:bg-purple-600/30 transition-colors"
          >
            Volver al Diagnóstico
          </button>
          <button
            onClick={() => router.push('/dashboard')}
            className="px-6 py-3 bg-gradient-to-r from-purple-600 to-pink-600 rounded-lg text-white font-bold hover:from-purple-700 hover:to-pink-700 transition-all"
          >
            Ir al Dashboard
          </button>
        </div>
      </div>
    </div>
  );
}