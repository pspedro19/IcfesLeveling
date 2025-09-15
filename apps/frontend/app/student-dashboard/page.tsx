'use client';

import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { 
  BarChart3, 
  TrendingUp, 
  Zap,
  Trophy,
  Clock,
  Users,
  Target,
  BookOpen,
  PlayCircle,
  CheckCircle2,
  ArrowRight,
  Sparkles,
  Shield,
  ChevronRight,
  Filter,
  RefreshCw,
  Activity
} from 'lucide-react';
import { useAuthStore } from '@/stores/useAuthStore';
import IRTMetricsPanel from '@/components/Student/IRTMetricsPanel';
import ErrorAnalysisCarousel from '@/components/Student/ErrorAnalysisCarousel';
import RecommendationsPanel from '@/components/Student/RecommendationsPanel';
import RPGProgressBar from '@/components/Student/RPGProgressBar';
import ThetaEvolutionChart from '@/components/Student/ThetaEvolutionChart';
import AnimatedBackground from '@/components/Student/AnimatedBackground';
import RealtimeNotifications from '@/components/Student/RealtimeNotifications';
import { studentDashboardService } from '@/services/studentDashboard.service';
import { useRealtimeUpdates } from '@/hooks/useRealtimeUpdates';
import { useCache } from '@/hooks/useCache';
import AdvancedProgressChart from '@/components/Student/AdvancedProgressChart';
import RealTimeMetricsPanel from '@/components/Student/RealTimeMetricsPanel';

interface DashboardStats {
  currentLevel: number;
  currentRank: string;
  experience: number;
  experienceToNext: number;
  totalBattles: number;
  winRate: number;
  currentStreak: number;
  mastery: {
    mathematics: number;
    physics: number;
    chemistry: number;
    biology: number;
    spanish: number;
  };
  theta: {
    mathematics: number;
    physics: number;
    chemistry: number;
    biology: number;
    spanish: number;
  };
  classRanking: number;
  nationalRanking: number;
}

export default function StudentDashboardPage() {
  const { user } = useAuthStore();
  const [activeTab, setActiveTab] = useState<'overview' | 'metrics' | 'errors' | 'recommendations' | 'realtime' | 'progress'>('overview');
  const [timeFilter, setTimeFilter] = useState<'7d' | '30d' | '90d'>('30d');
  
  // Use cache for dashboard data
  const { 
    data: stats, 
    isLoading: loading, 
    refetch: refetchStats,
    isStale 
  } = useCache<DashboardStats>(
    `dashboard-stats-${user?.id}-${timeFilter}`,
    () => studentDashboardService.getDashboardStats(timeFilter),
    { 
      ttl: 2 * 60 * 1000, // 2 minutes
      staleTime: 30 * 1000, // 30 seconds
      refreshOnFocus: true 
    }
  );

  // Real-time updates
  const { 
    isConnected, 
    progressUpdates, 
    xpUpdates, 
    levelUps, 
    achievements 
  } = useRealtimeUpdates();

  // Auto-refresh when real-time events occur
  useEffect(() => {
    if (progressUpdates.length > 0 || xpUpdates.length > 0 || levelUps.length > 0) {
      refetchStats();
    }
  }, [progressUpdates, xpUpdates, levelUps, refetchStats]);

  const getRankColor = (rank: string) => {
    switch (rank) {
      case 'S+': return 'from-yellow-400 to-orange-500';
      case 'S': return 'from-purple-400 to-pink-500';
      case 'A+': return 'from-blue-400 to-purple-500';
      case 'A': return 'from-blue-400 to-blue-600';
      case 'B+': return 'from-green-400 to-blue-500';
      case 'B': return 'from-green-400 to-green-600';
      default: return 'from-gray-400 to-gray-600';
    }
  };

  const renderQuickStat = (
    title: string,
    value: string | number,
    icon: React.ReactNode,
    color: string,
    trend?: { value: number; isPositive: boolean }
  ) => (
    <motion.div
      className={`bg-gradient-to-br ${color} rounded-xl p-6 text-white relative overflow-hidden`}
      whileHover={{ scale: 1.02, y: -2 }}
      transition={{ duration: 0.2 }}
    >
      <div className="absolute top-0 right-0 w-20 h-20 opacity-10">
        {icon}
      </div>
      <div className="relative z-10">
        <div className="flex items-center justify-between mb-2">
          <div className="p-2 bg-white/20 rounded-lg">
            {icon}
          </div>
          {trend && (
            <div className={`flex items-center gap-1 text-sm ${
              trend.isPositive ? 'text-green-200' : 'text-red-200'
            }`}>
              <TrendingUp className={`w-4 h-4 ${!trend.isPositive ? 'rotate-180' : ''}`} />
              <span>{Math.abs(trend.value)}%</span>
            </div>
          )}
        </div>
        <p className="text-sm opacity-90 mb-1">{title}</p>
        <p className="text-2xl font-bold">{value}</p>
      </div>
    </motion.div>
  );

  if (loading) {
    return (
      <div className="min-h-screen relative">
        <AnimatedBackground variant="default" intensity="medium" />
        <div className="relative z-10 flex items-center justify-center min-h-screen">
          <motion.div
            className="flex flex-col items-center gap-4"
            animate={{ opacity: [0.5, 1, 0.5] }}
            transition={{ duration: 2, repeat: Infinity }}
          >
            <div className="relative">
              <div className="w-16 h-16 border-4 border-purple-500/30 rounded-full animate-spin">
                <div className="absolute top-0 left-0 w-16 h-16 border-4 border-transparent border-t-purple-500 rounded-full animate-spin"></div>
              </div>
              <Sparkles className="absolute inset-0 w-8 h-8 m-auto text-purple-400" />
            </div>
            <p className="text-white font-semibold">Cargando tu progreso...</p>
            {!isConnected && (
              <p className="text-orange-400 text-sm">Conectando al servidor...</p>
            )}
          </motion.div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen relative">
      {/* Animated Background */}
      <AnimatedBackground 
        variant={stats?.currentRank === 'S+' ? 'success' : 'default'} 
        intensity="medium" 
        interactive 
      />
      
      {/* Real-time Notifications */}
      <RealtimeNotifications />

      <div className="relative z-10 container mx-auto px-4 py-8">
        {/* Header */}
        <motion.div 
          className="mb-8"
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <div className="flex items-center gap-2 text-gray-400 mb-4">
            <span>Dashboard</span>
            <ChevronRight className="w-4 h-4" />
            <span className="text-white">Centro de Comando</span>
          </div>
          
          <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-6">
            <div>
              <h1 className="text-4xl font-bold text-white mb-2 font-cinzel flex items-center gap-4">
                <Shield className="w-10 h-10 text-purple-400" />
                Centro de Comando - {user?.name || 'Hunter'}
              </h1>
              <p className="text-gray-300">
                Tu progreso en el camino hacia la maestría académica
              </p>
            </div>
            
            {/* Time Filter */}
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2 bg-gray-900/80 rounded-lg p-1">
                {[
                  { key: '7d', label: '7 días' },
                  { key: '30d', label: '30 días' },
                  { key: '90d', label: '90 días' }
                ].map(filter => (
                  <button
                    key={filter.key}
                    onClick={() => setTimeFilter(filter.key as any)}
                    className={`px-4 py-2 rounded-lg text-sm font-semibold transition-all ${
                      timeFilter === filter.key
                        ? 'bg-purple-600 text-white'
                        : 'text-gray-400 hover:text-white'
                    }`}
                  >
                    {filter.label}
                  </button>
                ))}
              </div>
              
              <button
                onClick={() => refetchStats()}
                className={`p-2 bg-gray-800 hover:bg-gray-700 rounded-lg transition-all ${isStale ? 'animate-pulse' : ''}`}
                title={isStale ? "Datos desactualizados - Actualizar" : "Actualizar"}
              >
                <RefreshCw className={`w-5 h-5 ${isStale ? 'text-orange-400' : 'text-gray-400'}`} />
              </button>
              
              {/* Connection Status */}
              <div className={`flex items-center gap-2 px-3 py-2 rounded-lg ${
                isConnected ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'
              }`}>
                <div className={`w-2 h-2 rounded-full ${
                  isConnected ? 'bg-green-400' : 'bg-red-400'
                } ${isConnected ? 'animate-pulse' : ''}`} />
                <span className="text-xs font-semibold">
                  {isConnected ? 'En vivo' : 'Desconectado'}
                </span>
              </div>
            </div>
          </div>
        </motion.div>

        {/* RPG Progress Bar */}
        {stats && (
          <motion.div
            className="mb-8"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
          >
            <RPGProgressBar
              currentLevel={stats.currentLevel}
              currentRank={stats.currentRank}
              experience={stats.experience}
              experienceToNext={stats.experienceToNext}
              rankColor={getRankColor(stats.currentRank)}
            />
          </motion.div>
        )}

        {/* Quick Stats */}
        <motion.div 
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
        >
          {stats && (
            <>
              {renderQuickStat(
                'Batallas Totales',
                stats.totalBattles,
                <Target className="w-8 h-8" />,
                'from-purple-600 to-purple-700',
                { value: 12, isPositive: true }
              )}
              
              {renderQuickStat(
                'Tasa de Victoria',
                `${stats.winRate}%`,
                <Trophy className="w-8 h-8" />,
                'from-yellow-500 to-orange-600',
                { value: 8, isPositive: true }
              )}
              
              {renderQuickStat(
                'Racha Actual',
                `${stats.currentStreak} días`,
                <Zap className="w-8 h-8" />,
                'from-green-500 to-emerald-600',
                { value: 25, isPositive: true }
              )}
              
              {renderQuickStat(
                'Ranking Nacional',
                `#${stats.nationalRanking}`,
                <Users className="w-8 h-8" />,
                'from-blue-500 to-cyan-600',
                { value: 5, isPositive: true }
              )}
            </>
          )}
        </motion.div>

        {/* Navigation Tabs */}
        <motion.div
          className="mb-8"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
        >
          <div className="flex items-center gap-2 bg-gray-900/80 rounded-xl p-2">
            {[
              { key: 'overview', label: 'Resumen', icon: <BarChart3 className="w-5 h-5" /> },
              { key: 'progress', label: 'Progreso Avanzado', icon: <TrendingUp className="w-5 h-5" /> },
              { key: 'realtime', label: 'Métricas Tiempo Real', icon: <Activity className="w-5 h-5" /> },
              { key: 'metrics', label: 'Métricas IRT', icon: <Target className="w-5 h-5" /> },
              { key: 'errors', label: 'Análisis de Errores', icon: <Target className="w-5 h-5" /> },
              { key: 'recommendations', label: 'Recomendaciones', icon: <BookOpen className="w-5 h-5" /> }
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
          </div>
        </motion.div>

        {/* Content based on active tab */}
        <motion.div
          key={activeTab}
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.3 }}
        >
          {activeTab === 'overview' && stats && (
            <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
              {/* Mastery Overview */}
              <div className="xl:col-span-2">
                <div className="bg-gray-900/80 rounded-xl p-6 border border-purple-500/30">
                  <h3 className="text-xl font-semibold text-white mb-6 flex items-center gap-3">
                    <Trophy className="w-6 h-6 text-yellow-400" />
                    Nivel de Maestría por Materia
                  </h3>
                  
                  <div className="space-y-4">
                    {Object.entries(stats.mastery).map(([subject, mastery]) => (
                      <div key={subject} className="space-y-2">
                        <div className="flex justify-between items-center">
                          <span className="text-gray-300 capitalize">{subject}</span>
                          <span className="text-white font-semibold">{mastery}%</span>
                        </div>
                        <div className="w-full bg-gray-800 rounded-full h-3">
                          <motion.div
                            className={`h-3 rounded-full bg-gradient-to-r ${
                              mastery >= 80 ? 'from-green-500 to-emerald-500' :
                              mastery >= 60 ? 'from-yellow-500 to-orange-500' :
                              'from-red-500 to-pink-500'
                            }`}
                            style={{ width: `${mastery}%` }}
                            initial={{ width: 0 }}
                            animate={{ width: `${mastery}%` }}
                            transition={{ duration: 1, delay: 0.2 }}
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
              
              {/* Quick Actions */}
              <div className="space-y-6">
                <div className="bg-gray-900/80 rounded-xl p-6 border border-purple-500/30">
                  <h3 className="text-lg font-semibold text-white mb-4">Acciones Rápidas</h3>
                  
                  <div className="space-y-3">
                    <button className="w-full flex items-center justify-between p-4 bg-gradient-to-r from-purple-600 to-purple-700 rounded-lg text-white hover:from-purple-700 hover:to-purple-800 transition-all">
                      <div className="flex items-center gap-3">
                        <PlayCircle className="w-5 h-5" />
                        <span>Nueva Batalla</span>
                      </div>
                      <ArrowRight className="w-4 h-4" />
                    </button>
                    
                    <button className="w-full flex items-center justify-between p-4 bg-gradient-to-r from-blue-600 to-blue-700 rounded-lg text-white hover:from-blue-700 hover:to-blue-800 transition-all">
                      <div className="flex items-center gap-3">
                        <BookOpen className="w-5 h-5" />
                        <span>Ver Plan de Estudio</span>
                      </div>
                      <ArrowRight className="w-4 h-4" />
                    </button>
                    
                    <button className="w-full flex items-center justify-between p-4 bg-gradient-to-r from-green-600 to-green-700 rounded-lg text-white hover:from-green-700 hover:to-green-800 transition-all">
                      <div className="flex items-center gap-3">
                        <CheckCircle2 className="w-5 h-5" />
                        <span>Tareas Pendientes</span>
                      </div>
                      <ArrowRight className="w-4 h-4" />
                    </button>
                  </div>
                </div>
                
                {/* Recent Achievements */}
                <div className="bg-gray-900/80 rounded-xl p-6 border border-purple-500/30">
                  <h3 className="text-lg font-semibold text-white mb-4">Logros Recientes</h3>
                  
                  <div className="space-y-3">
                    <div className="flex items-center gap-3 p-3 bg-yellow-500/20 rounded-lg">
                      <div className="w-8 h-8 bg-yellow-500 rounded-full flex items-center justify-center">
                        <Trophy className="w-4 h-4 text-white" />
                      </div>
                      <div>
                        <p className="text-yellow-400 font-semibold text-sm">Matemático Experto</p>
                        <p className="text-gray-400 text-xs">85% de precisión en matemáticas</p>
                      </div>
                    </div>
                    
                    <div className="flex items-center gap-3 p-3 bg-green-500/20 rounded-lg">
                      <div className="w-8 h-8 bg-green-500 rounded-full flex items-center justify-center">
                        <Zap className="w-4 h-4 text-white" />
                      </div>
                      <div>
                        <p className="text-green-400 font-semibold text-sm">Racha de Fuego</p>
                        <p className="text-gray-400 text-xs">7 días consecutivos</p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}
          
          {activeTab === 'progress' && (
            <AdvancedProgressChart 
              timeFilter={timeFilter}
              userId={user?.id}
            />
          )}

          {activeTab === 'realtime' && (
            <RealTimeMetricsPanel 
              userId={user?.id}
            />
          )}

          {activeTab === 'metrics' && stats && (
            <div className="space-y-6">
              <IRTMetricsPanel 
                theta={stats.theta}
                mastery={stats.mastery}
                classRanking={stats.classRanking}
                nationalRanking={stats.nationalRanking}
              />
              <ThetaEvolutionChart timeFilter={timeFilter} />
            </div>
          )}
          
          {activeTab === 'errors' && (
            <ErrorAnalysisCarousel />
          )}
          
          {activeTab === 'recommendations' && (
            <RecommendationsPanel />
          )}
        </motion.div>
      </div>
    </div>
  );
}