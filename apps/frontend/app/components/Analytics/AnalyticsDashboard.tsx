'use client';

import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { 
  BarChart, 
  LineChart, 
  PieChart,
  TrendingUp,
  TrendingDown,
  Users,
  Activity,
  Target,
  Award,
  Calendar,
  Filter,
  Download,
  RefreshCw
} from 'lucide-react';
import { clickhouseService, UserAnalytics, AnalyticsPeriod } from '@/services/clickhouse.service';
import { useAnalyticsWorker } from '@/hooks/useWorker';
import { formatNumber } from '@/lib/utils';

interface AnalyticsDashboardProps {
  userId?: string;
  isAdmin?: boolean;
}

// Helper function for formatting
function formatPercentage(value: number): string {
  return `${value.toFixed(1)}%`;
}

export default function AnalyticsDashboard({ userId, isAdmin = false }: AnalyticsDashboardProps) {
  const [analytics, setAnalytics] = useState<UserAnalytics | null>(null);
  const [period, setPeriod] = useState<AnalyticsPeriod>('month');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  const analyticsWorker = useAnalyticsWorker();
  
  // Fetch analytics data
  const fetchAnalytics = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const data = userId && isAdmin
        ? await clickhouseService.getUserAnalyticsById(userId, period)
        : await clickhouseService.getUserAnalytics(period);
      
      setAnalytics(data);
      
      // Process data in worker for advanced insights
      if (data.battleStats.totalBattles > 0) {
        analyticsWorker.generateInsights({
          totalBattles: data.battleStats.totalBattles,
          winRate: (data.battleStats.totalCorrect / data.battleStats.totalQuestions) * 100,
          avgAccuracy: data.battleStats.accuracy,
          favoriteSubject: 'Matemáticas', // This would come from real data
          weakestTopic: data.topicPerformance.reduce((min, curr) => 
            curr.accuracy < min.accuracy ? curr : min
          )?.topicId || 'Unknown',
          strongestTopic: data.topicPerformance.reduce((max, curr) => 
            curr.accuracy > max.accuracy ? curr : max
          )?.topicId || 'Unknown',
          peakHour: 20, // This would be calculated from real data
          streakDays: data.progression[data.progression.length - 1]?.streakDays || 0
        }, true);
      }
    } catch (err) {
      setError('Error al cargar analytics');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };
  
  useEffect(() => {
    fetchAnalytics();
  }, [period, userId]);
  
  // Track page view
  useEffect(() => {
    clickhouseService.trackPageView('analytics_dashboard', {
      isAdmin,
      period
    });
  }, []);
  
  const renderStatCard = (
    title: string,
    value: string | number,
    icon: React.ReactNode,
    trend?: { value: number; isPositive: boolean },
    color: string = 'purple'
  ) => (
    <motion.div
      className="bg-gray-900/80 rounded-lg p-6"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      <div className="flex items-start justify-between mb-4">
        <div className={`p-3 rounded-lg bg-${color}-500/20`}>
          {icon}
        </div>
        {trend && (
          <div className={`flex items-center gap-1 text-sm ${
            trend.isPositive ? 'text-green-400' : 'text-red-400'
          }`}>
            {trend.isPositive ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
            <span>{Math.abs(trend.value)}%</span>
          </div>
        )}
      </div>
      
      <p className="text-gray-400 text-sm mb-1">{title}</p>
      <p className="text-2xl font-bold text-white">{value}</p>
    </motion.div>
  );
  
  const renderChart = (title: string, data: any[], type: 'line' | 'bar' | 'pie') => (
    <motion.div
      className="bg-gray-900/80 rounded-lg p-6"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
        {type === 'line' && <LineChart className="w-5 h-5 text-purple-400" />}
        {type === 'bar' && <BarChart className="w-5 h-5 text-blue-400" />}
        {type === 'pie' && <PieChart className="w-5 h-5 text-green-400" />}
        {title}
      </h3>
      
      <div className="h-64 flex items-center justify-center text-gray-500">
        {/* Placeholder for actual chart implementation */}
        <p>Chart visualization would go here</p>
        {/* You would integrate a chart library like recharts or chart.js here */}
      </div>
    </motion.div>
  );
  
  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="w-8 h-8 text-purple-400 animate-spin" />
      </div>
    );
  }
  
  if (error || !analytics) {
    return (
      <div className="bg-red-900/20 border border-red-500/50 rounded-lg p-6 text-center">
        <p className="text-red-400">{error || 'No hay datos disponibles'}</p>
        <button
          onClick={fetchAnalytics}
          className="mt-4 px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg"
        >
          Reintentar
        </button>
      </div>
    );
  }
  
  const insights = analyticsWorker.results.INSIGHTS_GENERATED?.data;
  
  return (
    <div className="space-y-6">
      {/* Header Controls */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <h2 className="text-2xl font-bold text-white">Dashboard de Analytics</h2>
        
        <div className="flex items-center gap-4">
          {/* Period Selector */}
          <div className="flex items-center gap-2 bg-gray-900/80 rounded-lg p-1">
            {(['week', 'month', 'quarter', 'year'] as AnalyticsPeriod[]).map(p => (
              <button
                key={p}
                onClick={() => setPeriod(p)}
                className={`px-4 py-2 rounded-lg text-sm font-semibold transition-all ${
                  period === p
                    ? 'bg-purple-600 text-white'
                    : 'text-gray-400 hover:text-white'
                }`}
              >
                {p === 'week' && 'Semana'}
                {p === 'month' && 'Mes'}
                {p === 'quarter' && 'Trimestre'}
                {p === 'year' && 'Año'}
              </button>
            ))}
          </div>
          
          {/* Action Buttons */}
          <button
            onClick={fetchAnalytics}
            className="p-2 bg-gray-800 hover:bg-gray-700 rounded-lg transition-all"
            title="Actualizar"
          >
            <RefreshCw className="w-5 h-5 text-gray-400" />
          </button>
          
          {isAdmin && (
            <button
              className="p-2 bg-gray-800 hover:bg-gray-700 rounded-lg transition-all"
              title="Exportar"
            >
              <Download className="w-5 h-5 text-gray-400" />
            </button>
          )}
        </div>
      </div>
      
      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {renderStatCard(
          'Batallas Totales',
          analytics.battleStats.totalBattles,
          <Activity className="w-6 h-6 text-purple-400" />,
          undefined,
          'purple'
        )}
        
        {renderStatCard(
          'Precisión',
          formatPercentage(analytics.battleStats.accuracy),
          <Target className="w-6 h-6 text-blue-400" />,
          { value: 5.2, isPositive: true },
          'blue'
        )}
        
        {renderStatCard(
          'Experiencia Ganada',
          formatNumber(analytics.battleStats.totalExperience),
          <TrendingUp className="w-6 h-6 text-green-400" />,
          { value: 12.5, isPositive: true },
          'green'
        )}
        
        {renderStatCard(
          'Orbes Ganados',
          formatNumber(analytics.battleStats.totalOrbs),
          <Award className="w-6 h-6 text-yellow-400" />,
          undefined,
          'yellow'
        )}
      </div>
      
      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Daily Activity Chart */}
        {renderChart(
          'Actividad Diaria',
          analytics.dailyActivity,
          'line'
        )}
        
        {/* Topic Performance Chart */}
        {renderChart(
          'Rendimiento por Tema',
          analytics.topicPerformance,
          'bar'
        )}
      </div>
      
      {/* AI Insights */}
      {insights && (
        <motion.div
          className="bg-gray-900/80 rounded-lg p-6"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
        >
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <Activity className="w-5 h-5 text-purple-400" />
            Insights Personalizados
          </h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {insights.insights.map((insight: string, index: number) => (
              <div
                key={index}
                className="bg-gray-800/50 rounded-lg p-4 border border-purple-500/30"
              >
                <p className="text-gray-300">{insight}</p>
              </div>
            ))}
          </div>
          
          {insights.recommendations && insights.recommendations.length > 0 && (
            <div className="mt-6">
              <h4 className="text-md font-semibold text-white mb-3">
                Recomendaciones
              </h4>
              <ul className="space-y-2">
                {insights.recommendations.map((rec: string, index: number) => (
                  <li key={index} className="flex items-start gap-2 text-gray-300">
                    <span className="text-purple-400">•</span>
                    <span>{rec}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </motion.div>
      )}
      
      {/* Progression Timeline */}
      <motion.div
        className="bg-gray-900/80 rounded-lg p-6"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
      >
        <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <Calendar className="w-5 h-5 text-purple-400" />
          Progresión
        </h3>
        
        <div className="space-y-4">
          {analytics.progression.slice(-5).reverse().map((prog, index) => (
            <div key={index} className="flex items-center gap-4">
              <div className="w-16 text-right text-sm text-gray-400">
                {new Date(prog.recordedAt).toLocaleDateString()}
              </div>
              <div className="flex-1 flex items-center gap-4">
                <div className="bg-purple-600 text-white px-3 py-1 rounded-full text-sm font-semibold">
                  Nivel {prog.level}
                </div>
                <div className="text-gray-300">
                  {formatNumber(prog.experience)} EXP
                </div>
                <div className={`px-2 py-1 rounded text-xs font-semibold ${
                  prog.rank === 'S' ? 'bg-yellow-500/20 text-yellow-400' :
                  prog.rank === 'A' ? 'bg-purple-500/20 text-purple-400' :
                  prog.rank === 'B' ? 'bg-blue-500/20 text-blue-400' :
                  prog.rank === 'C' ? 'bg-green-500/20 text-green-400' :
                  'bg-gray-500/20 text-gray-400'
                }`}>
                  Rango {prog.rank}
                </div>
                {prog.streakDays > 0 && (
                  <div className="text-orange-400 text-sm">
                    🔥 {prog.streakDays} días
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      </motion.div>
    </div>
  );
}