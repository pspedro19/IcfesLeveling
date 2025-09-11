'use client';

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  BookOpen, 
  PlayCircle, 
  CheckCircle2, 
  Clock,
  Trophy,
  Target,
  Zap,
  RefreshCw,
  Calendar,
  BarChart3,
  Award,
  Users,
  Star,
  Flame,
  Download,
  Eye,
  ChevronRight,
  ChevronDown,
  ChevronUp
} from 'lucide-react';

interface StudyPlanTask {
  id: string;
  title: string;
  description: string;
  type: 'video' | 'practice' | 'reading' | 'quiz';
  subject: string;
  estimatedTime: number;
  difficulty: 'easy' | 'medium' | 'hard';
  priority: 'high' | 'medium' | 'low';
  completed: boolean;
  progress: number;
  dueDate: string;
  xpReward: number;
  badge?: string;
}

interface MonthlyPlan {
  month: string;
  year: number;
  totalTasks: number;
  completedTasks: number;
  totalXP: number;
  earnedXP: number;
  weeks: WeeklyPlan[];
}

interface WeeklyPlan {
  week: number;
  startDate: string;
  endDate: string;
  theme: string;
  tasks: StudyPlanTask[];
  targetHours: number;
  completedHours: number;
}

interface VideoRecommendation {
  id: string;
  title: string;
  channel: string;
  duration: number;
  watchedTime: number;
  thumbnail: string;
  subject: string;
  difficulty: number;
  relevanceScore: number;
}

interface Achievement {
  id: string;
  name: string;
  description: string;
  icon: string;
  category: 'study' | 'consistency' | 'improvement' | 'mastery';
  progress: number;
  maxProgress: number;
  earned: boolean;
  xpReward: number;
  rarity: 'common' | 'rare' | 'epic' | 'legendary';
}

export default function RecommendationsPanel() {
  const [monthlyPlan, setMonthlyPlan] = useState<MonthlyPlan | null>(null);
  const [videoRecommendations, setVideoRecommendations] = useState<VideoRecommendation[]>([]);
  const [achievements, setAchievements] = useState<Achievement[]>([]);
  const [activeTab, setActiveTab] = useState<'plan' | 'videos' | 'achievements'>('plan');
  const [expandedWeek, setExpandedWeek] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const generateMockData = () => {
      // Generate monthly plan
      const currentDate = new Date();
      const monthNames = [
        'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
        'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'
      ];

      const tasks: StudyPlanTask[] = [
        {
          id: 'task_1',
          title: 'Fundamentos de Álgebra Lineal',
          description: 'Revisar conceptos básicos de vectores y matrices',
          type: 'video',
          subject: 'Matemáticas',
          estimatedTime: 45,
          difficulty: 'medium',
          priority: 'high',
          completed: true,
          progress: 100,
          dueDate: new Date(Date.now() + 2 * 24 * 60 * 60 * 1000).toISOString(),
          xpReward: 150,
          badge: 'math_master'
        },
        {
          id: 'task_2',
          title: 'Práctica: Ecuaciones Cuadráticas',
          description: 'Resolver 20 problemas de ecuaciones cuadráticas',
          type: 'practice',
          subject: 'Matemáticas',
          estimatedTime: 60,
          difficulty: 'medium',
          priority: 'high',
          completed: false,
          progress: 65,
          dueDate: new Date(Date.now() + 1 * 24 * 60 * 60 * 1000).toISOString(),
          xpReward: 200
        },
        {
          id: 'task_3',
          title: 'Lectura: Leyes de Newton',
          description: 'Estudiar las tres leyes fundamentales de Newton',
          type: 'reading',
          subject: 'Física',
          estimatedTime: 30,
          difficulty: 'easy',
          priority: 'medium',
          completed: false,
          progress: 20,
          dueDate: new Date(Date.now() + 3 * 24 * 60 * 60 * 1000).toISOString(),
          xpReward: 100
        },
        {
          id: 'task_4',
          title: 'Quiz: Tabla Periódica',
          description: 'Evaluación sobre elementos químicos y sus propiedades',
          type: 'quiz',
          subject: 'Química',
          estimatedTime: 25,
          difficulty: 'hard',
          priority: 'medium',
          completed: false,
          progress: 0,
          dueDate: new Date(Date.now() + 5 * 24 * 60 * 60 * 1000).toISOString(),
          xpReward: 300,
          badge: 'chemistry_expert'
        }
      ];

      const weeks: WeeklyPlan[] = [
        {
          week: 1,
          startDate: new Date(currentDate.getFullYear(), currentDate.getMonth(), 1).toISOString(),
          endDate: new Date(currentDate.getFullYear(), currentDate.getMonth(), 7).toISOString(),
          theme: 'Fundamentos Matemáticos',
          tasks: tasks.slice(0, 2),
          targetHours: 8,
          completedHours: 6.5
        },
        {
          week: 2,
          startDate: new Date(currentDate.getFullYear(), currentDate.getMonth(), 8).toISOString(),
          endDate: new Date(currentDate.getFullYear(), currentDate.getMonth(), 14).toISOString(),
          theme: 'Ciencias Exactas',
          tasks: tasks.slice(2),
          targetHours: 10,
          completedHours: 2.5
        }
      ];

      const plan: MonthlyPlan = {
        month: monthNames[currentDate.getMonth()],
        year: currentDate.getFullYear(),
        totalTasks: tasks.length,
        completedTasks: tasks.filter(t => t.completed).length,
        totalXP: tasks.reduce((sum, task) => sum + task.xpReward, 0),
        earnedXP: tasks.filter(t => t.completed).reduce((sum, task) => sum + task.xpReward, 0),
        weeks
      };

      // Generate video recommendations
      const videos: VideoRecommendation[] = [
        {
          id: 'video_1',
          title: 'Álgebra Lineal: Espacios Vectoriales',
          channel: 'Khan Academy',
          duration: 1200, // 20 minutes
          watchedTime: 720, // 12 minutes
          thumbnail: '/images/videos/algebra_linear.jpg',
          subject: 'Matemáticas',
          difficulty: 0.7,
          relevanceScore: 0.95
        },
        {
          id: 'video_2',
          title: 'Física: Movimiento Circular Uniforme',
          channel: 'Physics Pro',
          duration: 900,
          watchedTime: 0,
          thumbnail: '/images/videos/circular_motion.jpg',
          subject: 'Física',
          difficulty: 0.6,
          relevanceScore: 0.88
        },
        {
          id: 'video_3',
          title: 'Química Orgánica: Reacciones de Sustitución',
          channel: 'ChemExplainer',
          duration: 1500,
          watchedTime: 1500,
          thumbnail: '/images/videos/organic_chemistry.jpg',
          subject: 'Química',
          difficulty: 0.8,
          relevanceScore: 0.92
        }
      ];

      // Generate achievements
      const achievementList: Achievement[] = [
        {
          id: 'achievement_1',
          name: 'Estudioso Constante',
          description: 'Estudia 7 días consecutivos',
          icon: '📚',
          category: 'consistency',
          progress: 5,
          maxProgress: 7,
          earned: false,
          xpReward: 500,
          rarity: 'rare'
        },
        {
          id: 'achievement_2',
          name: 'Maestro Matemático',
          description: 'Completa 10 tareas de matemáticas',
          icon: '🧮',
          category: 'mastery',
          progress: 10,
          maxProgress: 10,
          earned: true,
          xpReward: 1000,
          rarity: 'epic'
        },
        {
          id: 'achievement_3',
          name: 'Velocista Mental',
          description: 'Responde 50 preguntas en menos de 30 segundos cada una',
          icon: '⚡',
          category: 'improvement',
          progress: 32,
          maxProgress: 50,
          earned: false,
          xpReward: 750,
          rarity: 'rare'
        },
        {
          id: 'achievement_4',
          name: 'Explorador del Conocimiento',
          description: 'Completa tu primera semana de estudio',
          icon: '🗺️',
          category: 'study',
          progress: 1,
          maxProgress: 1,
          earned: true,
          xpReward: 250,
          rarity: 'common'
        }
      ];

      setMonthlyPlan(plan);
      setVideoRecommendations(videos);
      setAchievements(achievementList);
      setLoading(false);
    };

    setTimeout(generateMockData, 1000);
  }, []);

  const getTaskIcon = (type: string) => {
    switch (type) {
      case 'video': return <PlayCircle className="w-5 h-5" />;
      case 'practice': return <Target className="w-5 h-5" />;
      case 'reading': return <BookOpen className="w-5 h-5" />;
      case 'quiz': return <BarChart3 className="w-5 h-5" />;
      default: return <BookOpen className="w-5 h-5" />;
    }
  };

  const getTaskColor = (type: string) => {
    switch (type) {
      case 'video': return 'from-blue-500 to-blue-600';
      case 'practice': return 'from-green-500 to-green-600';
      case 'reading': return 'from-purple-500 to-purple-600';
      case 'quiz': return 'from-orange-500 to-orange-600';
      default: return 'from-gray-500 to-gray-600';
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high': return 'text-red-400';
      case 'medium': return 'text-yellow-400';
      case 'low': return 'text-green-400';
      default: return 'text-gray-400';
    }
  };

  const getRarityColor = (rarity: string) => {
    switch (rarity) {
      case 'common': return 'border-gray-500 bg-gray-500/20';
      case 'rare': return 'border-blue-500 bg-blue-500/20';
      case 'epic': return 'border-purple-500 bg-purple-500/20';
      case 'legendary': return 'border-yellow-500 bg-yellow-500/20';
      default: return 'border-gray-500 bg-gray-500/20';
    }
  };

  const formatTime = (seconds: number) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    if (hours > 0) {
      return `${hours}h ${minutes}m`;
    }
    return `${minutes}m`;
  };

  const generateNewPlan = async () => {
    setLoading(true);
    // Simulate API call to regenerate plan
    setTimeout(() => {
      setLoading(false);
      // In reality, this would fetch a new plan from the backend
    }, 2000);
  };

  if (loading) {
    return (
      <motion.div
        className="bg-gray-900/80 rounded-xl p-8 border border-purple-500/30 flex items-center justify-center"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
      >
        <div className="text-center">
          <motion.div
            className="w-12 h-12 border-4 border-purple-500/30 border-t-purple-500 rounded-full mx-auto mb-4"
            animate={{ rotate: 360 }}
            transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
          />
          <p className="text-gray-400">Generando recomendaciones personalizadas...</p>
        </div>
      </motion.div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Navigation Tabs */}
      <motion.div
        className="flex items-center gap-2 bg-gray-900/80 rounded-xl p-2"
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        {[
          { key: 'plan', label: 'Plan de Estudio', icon: <Calendar className="w-5 h-5" /> },
          { key: 'videos', label: 'Videos Recomendados', icon: <PlayCircle className="w-5 h-5" /> },
          { key: 'achievements', label: 'Logros', icon: <Trophy className="w-5 h-5" /> }
        ].map(tab => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key as any)}
            className={`flex items-center gap-2 px-6 py-3 rounded-lg font-semibold transition-all ${
              activeTab === tab.key
                ? 'bg-purple-600 text-white shadow-lg'
                : 'text-gray-400 hover:text-white hover:bg-gray-800'
            }`}
          >
            {tab.icon}
            <span className="hidden sm:inline">{tab.label}</span>
          </button>
        ))}
      </motion.div>

      {/* Plan de Estudio Tab */}
      {activeTab === 'plan' && monthlyPlan && (
        <motion.div
          className="space-y-6"
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
        >
          {/* Monthly Overview */}
          <div className="bg-gray-900/80 rounded-xl p-6 border border-purple-500/30">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h3 className="text-2xl font-bold text-white">
                  Plan de {monthlyPlan.month} {monthlyPlan.year}
                </h3>
                <p className="text-gray-400">Tu plan personalizado generado con IA</p>
              </div>
              
              <button
                onClick={generateNewPlan}
                className="flex items-center gap-2 px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg font-semibold transition-all"
              >
                <RefreshCw className="w-4 h-4" />
                Regenerar Plan
              </button>
            </div>

            {/* Progress Stats */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
              <div className="bg-gray-800/50 rounded-lg p-4">
                <div className="flex items-center gap-2 mb-2">
                  <CheckCircle2 className="w-5 h-5 text-green-400" />
                  <span className="text-sm text-gray-400">Tareas Completadas</span>
                </div>
                <p className="text-2xl font-bold text-white">
                  {monthlyPlan.completedTasks}/{monthlyPlan.totalTasks}
                </p>
              </div>

              <div className="bg-gray-800/50 rounded-lg p-4">
                <div className="flex items-center gap-2 mb-2">
                  <Zap className="w-5 h-5 text-yellow-400" />
                  <span className="text-sm text-gray-400">XP Ganada</span>
                </div>
                <p className="text-2xl font-bold text-white">
                  {monthlyPlan.earnedXP.toLocaleString()}
                </p>
              </div>

              <div className="bg-gray-800/50 rounded-lg p-4">
                <div className="flex items-center gap-2 mb-2">
                  <Target className="w-5 h-5 text-purple-400" />
                  <span className="text-sm text-gray-400">Progreso</span>
                </div>
                <p className="text-2xl font-bold text-white">
                  {Math.round((monthlyPlan.completedTasks / monthlyPlan.totalTasks) * 100)}%
                </p>
              </div>

              <div className="bg-gray-800/50 rounded-lg p-4">
                <div className="flex items-center gap-2 mb-2">
                  <Award className="w-5 h-5 text-orange-400" />
                  <span className="text-sm text-gray-400">XP Restante</span>
                </div>
                <p className="text-2xl font-bold text-white">
                  {(monthlyPlan.totalXP - monthlyPlan.earnedXP).toLocaleString()}
                </p>
              </div>
            </div>

            {/* Overall Progress Bar */}
            <div className="space-y-2">
              <div className="flex justify-between items-center">
                <span className="text-sm font-semibold text-gray-300">Progreso del Mes</span>
                <span className="text-sm font-bold text-white">
                  {Math.round((monthlyPlan.completedTasks / monthlyPlan.totalTasks) * 100)}%
                </span>
              </div>
              <div className="w-full h-3 bg-gray-800 rounded-full overflow-hidden">
                <motion.div
                  className="h-3 bg-gradient-to-r from-purple-500 to-purple-600 rounded-full"
                  initial={{ width: 0 }}
                  animate={{ width: `${(monthlyPlan.completedTasks / monthlyPlan.totalTasks) * 100}%` }}
                  transition={{ duration: 1, ease: 'easeOut' }}
                />
              </div>
            </div>
          </div>

          {/* Weekly Breakdown */}
          <div className="space-y-4">
            {monthlyPlan.weeks.map((week, index) => (
              <motion.div
                key={week.week}
                className="bg-gray-900/80 rounded-xl border border-purple-500/30 overflow-hidden"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
              >
                <button
                  onClick={() => setExpandedWeek(expandedWeek === week.week ? null : week.week)}
                  className="w-full p-6 text-left hover:bg-gray-800/30 transition-all"
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="text-lg font-semibold text-white mb-1">
                        Semana {week.week}: {week.theme}
                      </h4>
                      <p className="text-sm text-gray-400">
                        {new Date(week.startDate).toLocaleDateString('es-ES')} - {new Date(week.endDate).toLocaleDateString('es-ES')}
                      </p>
                    </div>
                    
                    <div className="flex items-center gap-4">
                      <div className="text-right">
                        <p className="text-sm text-gray-400">
                          {week.completedHours}h / {week.targetHours}h
                        </p>
                        <div className="w-20 h-2 bg-gray-800 rounded-full mt-1">
                          <div 
                            className="h-2 bg-gradient-to-r from-green-500 to-green-600 rounded-full"
                            style={{ width: `${Math.min(100, (week.completedHours / week.targetHours) * 100)}%` }}
                          />
                        </div>
                      </div>
                      
                      {expandedWeek === week.week ? (
                        <ChevronUp className="w-5 h-5 text-gray-400" />
                      ) : (
                        <ChevronDown className="w-5 h-5 text-gray-400" />
                      )}
                    </div>
                  </div>
                </button>

                <AnimatePresence>
                  {expandedWeek === week.week && (
                    <motion.div
                      className="px-6 pb-6"
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: 'auto' }}
                      exit={{ opacity: 0, height: 0 }}
                      transition={{ duration: 0.3 }}
                    >
                      <div className="space-y-3">
                        {week.tasks.map((task, taskIndex) => (
                          <motion.div
                            key={task.id}
                            className="bg-gray-800/50 rounded-lg p-4"
                            initial={{ opacity: 0, x: -20 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ delay: taskIndex * 0.1 }}
                          >
                            <div className="flex items-start gap-4">
                              <div className={`p-2 rounded-lg bg-gradient-to-r ${getTaskColor(task.type)} text-white`}>
                                {getTaskIcon(task.type)}
                              </div>
                              
                              <div className="flex-1">
                                <div className="flex items-start justify-between mb-2">
                                  <div>
                                    <h5 className="font-semibold text-white">{task.title}</h5>
                                    <p className="text-sm text-gray-400">{task.description}</p>
                                  </div>
                                  
                                  <div className="flex items-center gap-2">
                                    {task.badge && (
                                      <div className="px-2 py-1 bg-yellow-500/20 rounded-full">
                                        <span className="text-xs text-yellow-400 font-semibold">Badge</span>
                                      </div>
                                    )}
                                    <div className={`px-2 py-1 rounded-full text-xs font-semibold ${getPriorityColor(task.priority)}`}>
                                      {task.priority.toUpperCase()}
                                    </div>
                                  </div>
                                </div>
                                
                                <div className="flex items-center gap-4 mb-3">
                                  <div className="flex items-center gap-1 text-gray-400 text-sm">
                                    <Clock className="w-4 h-4" />
                                    <span>{task.estimatedTime} min</span>
                                  </div>
                                  <div className="flex items-center gap-1 text-gray-400 text-sm">
                                    <Zap className="w-4 h-4" />
                                    <span>{task.xpReward} XP</span>
                                  </div>
                                  <div className="flex items-center gap-1 text-gray-400 text-sm">
                                    <Calendar className="w-4 h-4" />
                                    <span>{new Date(task.dueDate).toLocaleDateString('es-ES')}</span>
                                  </div>
                                </div>
                                
                                <div className="flex items-center justify-between">
                                  <div className="flex-1 mr-4">
                                    <div className="flex justify-between items-center mb-1">
                                      <span className="text-xs text-gray-400">Progreso</span>
                                      <span className="text-xs text-white font-semibold">{task.progress}%</span>
                                    </div>
                                    <div className="w-full h-2 bg-gray-700 rounded-full">
                                      <motion.div
                                        className={`h-2 rounded-full ${task.completed ? 'bg-green-500' : 'bg-purple-500'}`}
                                        initial={{ width: 0 }}
                                        animate={{ width: `${task.progress}%` }}
                                        transition={{ duration: 0.5, delay: taskIndex * 0.1 }}
                                      />
                                    </div>
                                  </div>
                                  
                                  <button className={`px-4 py-2 rounded-lg font-semibold text-sm transition-all ${
                                    task.completed 
                                      ? 'bg-green-600 text-white cursor-default'
                                      : 'bg-purple-600 hover:bg-purple-700 text-white'
                                  }`}>
                                    {task.completed ? 'Completado' : 'Continuar'}
                                  </button>
                                </div>
                              </div>
                            </div>
                          </motion.div>
                        ))}
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </motion.div>
            ))}
          </div>
        </motion.div>
      )}

      {/* Videos Tab */}
      {activeTab === 'videos' && (
        <motion.div
          className="space-y-6"
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
        >
          <div className="bg-gray-900/80 rounded-xl p-6 border border-purple-500/30">
            <h3 className="text-xl font-semibold text-white mb-4 flex items-center gap-3">
              <PlayCircle className="w-6 h-6 text-purple-400" />
              Videos Recomendados
            </h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {videoRecommendations.map((video, index) => (
                <motion.div
                  key={video.id}
                  className="bg-gray-800/50 rounded-lg overflow-hidden hover:bg-gray-800/70 transition-all cursor-pointer"
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.1 }}
                  whileHover={{ scale: 1.02 }}
                >
                  <div className="relative">
                    <img
                      src={video.thumbnail}
                      alt={video.title}
                      className="w-full h-32 object-cover"
                      onError={(e) => {
                        e.currentTarget.src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMzAwIiBoZWlnaHQ9IjE2MCIgdmlld0JveD0iMCAwIDMwMCAxNjAiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PHJlY3Qgd2lkdGg9IjMwMCIgaGVpZ2h0PSIxNjAiIGZpbGw9IiM0QjVTNjMiLz48Y2lyY2xlIGN4PSIxNTAiIGN5PSI4MCIgcj0iMjAiIGZpbGw9IiM5Q0EzQUYiLz48cGF0aCBkPSJNMTQ1IDcwTDE2MCA4MEwxNDUgOTBWNzBaIiBmaWxsPSIjNEI1NTYzIi8+PC9zdmc+';
                      }}
                    />
                    <div className="absolute bottom-2 right-2 px-2 py-1 bg-black/80 rounded text-xs text-white">
                      {formatTime(video.duration)}
                    </div>
                    <div className="absolute top-2 left-2 px-2 py-1 bg-purple-600 rounded text-xs text-white font-semibold">
                      {Math.round(video.relevanceScore * 100)}% relevante
                    </div>
                  </div>
                  
                  <div className="p-4">
                    <h4 className="font-semibold text-white mb-2 line-clamp-2">{video.title}</h4>
                    <p className="text-sm text-gray-400 mb-3">{video.channel}</p>
                    
                    <div className="space-y-2">
                      <div className="flex justify-between items-center text-xs">
                        <span className="text-gray-400">Progreso</span>
                        <span className="text-white">
                          {Math.round((video.watchedTime / video.duration) * 100)}%
                        </span>
                      </div>
                      <div className="w-full h-2 bg-gray-700 rounded-full">
                        <div 
                          className="h-2 bg-gradient-to-r from-blue-500 to-blue-600 rounded-full"
                          style={{ width: `${(video.watchedTime / video.duration) * 100}%` }}
                        />
                      </div>
                    </div>
                    
                    <div className="flex items-center justify-between mt-3">
                      <span className="text-xs text-gray-400">{video.subject}</span>
                      <button className="px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white rounded text-xs font-semibold transition-all">
                        {video.watchedTime > 0 ? 'Continuar' : 'Ver Ahora'}
                      </button>
                    </div>
                  </div>
                </motion.div>
              ))}
            </div>
          </div>
        </motion.div>
      )}

      {/* Achievements Tab */}
      {activeTab === 'achievements' && (
        <motion.div
          className="space-y-6"
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
        >
          <div className="bg-gray-900/80 rounded-xl p-6 border border-purple-500/30">
            <h3 className="text-xl font-semibold text-white mb-6 flex items-center gap-3">
              <Trophy className="w-6 h-6 text-yellow-400" />
              Logros y Badges
            </h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {achievements.map((achievement, index) => (
                <motion.div
                  key={achievement.id}
                  className={`p-4 rounded-lg border-2 ${getRarityColor(achievement.rarity)} ${
                    achievement.earned ? 'opacity-100' : 'opacity-70'
                  }`}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: achievement.earned ? 1 : 0.7, y: 0 }}
                  transition={{ delay: index * 0.1 }}
                  whileHover={{ scale: 1.02 }}
                >
                  <div className="flex items-start gap-4">
                    <div className={`text-4xl ${achievement.earned ? 'grayscale-0' : 'grayscale'}`}>
                      {achievement.icon}
                    </div>
                    
                    <div className="flex-1">
                      <div className="flex items-center justify-between mb-2">
                        <h4 className="font-semibold text-white">{achievement.name}</h4>
                        {achievement.earned && (
                          <CheckCircle2 className="w-5 h-5 text-green-400" />
                        )}
                      </div>
                      
                      <p className="text-sm text-gray-400 mb-3">{achievement.description}</p>
                      
                      <div className="space-y-2">
                        <div className="flex justify-between items-center text-xs">
                          <span className="text-gray-400">Progreso</span>
                          <span className="text-white">
                            {achievement.progress}/{achievement.maxProgress}
                          </span>
                        </div>
                        <div className="w-full h-2 bg-gray-700 rounded-full">
                          <motion.div
                            className={`h-2 rounded-full ${
                              achievement.earned ? 'bg-green-500' : 'bg-yellow-500'
                            }`}
                            initial={{ width: 0 }}
                            animate={{ width: `${(achievement.progress / achievement.maxProgress) * 100}%` }}
                            transition={{ duration: 0.5, delay: index * 0.1 }}
                          />
                        </div>
                      </div>
                      
                      <div className="flex items-center justify-between mt-3">
                        <div className="flex items-center gap-2">
                          <Zap className="w-4 h-4 text-yellow-400" />
                          <span className="text-sm text-yellow-400 font-semibold">
                            {achievement.xpReward} XP
                          </span>
                        </div>
                        <div className={`px-2 py-1 rounded-full text-xs font-semibold ${
                          achievement.rarity === 'common' ? 'text-gray-400' :
                          achievement.rarity === 'rare' ? 'text-blue-400' :
                          achievement.rarity === 'epic' ? 'text-purple-400' :
                          'text-yellow-400'
                        }`}>
                          {achievement.rarity.toUpperCase()}
                        </div>
                      </div>
                    </div>
                  </div>
                </motion.div>
              ))}
            </div>
          </div>
        </motion.div>
      )}
    </div>
  );
}