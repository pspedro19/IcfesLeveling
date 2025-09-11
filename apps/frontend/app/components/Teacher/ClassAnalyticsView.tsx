'use client';

import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  TrendingUp,
  TrendingDown,
  Users,
  Activity,
  Target,
  Award,
  Calendar,
  Filter,
  Download,
  RefreshCw,
  AlertTriangle,
  BookOpen,
  Clock,
  BarChart3,
  PieChart,
  TrendingDown as Delta,
  Star,
  Medal,
  Crown
} from 'lucide-react';

interface ClassKPIs {
  totalStudents: number;
  activeStudents: number;
  inactiveStudents: number;
  avgMastery: number;
  masteryBySubject: {
    math: number;
    spanish: number;
    science: number;
    social: number;
    english: number;
  };
  progressDelta30d: number;
  rpgDistribution: {
    E: number;
    D: number;
    C: number;
    B: number;
    A: number;
    S: number;
    'S+': number;
  };
  totalBattles: number;
  totalQuestions: number;
  totalCorrect: number;
  avgResponseTime: number;
}

interface StudentRanking {
  userId: string;
  username: string;
  avatarUrl?: string;
  level: number;
  rank: string;
  thetaScore: number;
  masteryAvg: number;
  totalBattles: number;
  winRate: number;
  lastActivity: string;
  streakDays: number;
}

interface ClassAnalyticsViewProps {
  classId: string;
  className: string;
  teacherId: string;
}

export default function ClassAnalyticsView({ 
  classId, 
  className, 
  teacherId 
}: ClassAnalyticsViewProps) {
  const [kpis, setKpis] = useState<ClassKPIs | null>(null);
  const [studentRankings, setStudentRankings] = useState<StudentRanking[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedPeriod, setSelectedPeriod] = useState<'7d' | '30d' | '90d'>('30d');
  const [refreshing, setRefreshing] = useState(false);

  // Colores para los rangos RPG
  const getRankColor = (rank: string) => {
    const colors = {
      'E': 'text-gray-400 bg-gray-500/20',
      'D': 'text-orange-400 bg-orange-500/20',
      'C': 'text-yellow-400 bg-yellow-500/20',
      'B': 'text-blue-400 bg-blue-500/20',
      'A': 'text-purple-400 bg-purple-500/20',
      'S': 'text-pink-400 bg-pink-500/20',
      'S+': 'text-yellow-300 bg-gradient-to-r from-yellow-500/20 to-orange-500/20'
    };
    return colors[rank as keyof typeof colors] || colors.E;
  };

  const getRankIcon = (rank: string) => {
    const icons = {
      'E': <Activity className="w-4 h-4" />,
      'D': <Target className="w-4 h-4" />,
      'C': <Award className="w-4 h-4" />,
      'B': <Star className="w-4 h-4" />,
      'A': <Medal className="w-4 h-4" />,
      'S': <Crown className="w-4 h-4" />,
      'S+': <Crown className="w-4 h-4" />
    };
    return icons[rank as keyof typeof icons] || icons.E;
  };

  // Cargar datos de la clase
  const fetchClassAnalytics = async () => {
    if (refreshing) setRefreshing(true);
    else setLoading(true);
    setError(null);

    try {
      // Simular llamada a la API - reemplazar con llamada real
      const mockKpis: ClassKPIs = {
        totalStudents: 28,
        activeStudents: 24,
        inactiveStudents: 4,
        avgMastery: 74.2,
        masteryBySubject: {
          math: 68.5,
          spanish: 79.1,
          science: 72.8,
          social: 76.3,
          english: 69.4
        },
        progressDelta30d: 8.7,
        rpgDistribution: {
          E: 2,
          D: 4,
          C: 8,
          B: 7,
          A: 5,
          S: 2,
          'S+': 0
        },
        totalBattles: 342,
        totalQuestions: 2847,
        totalCorrect: 2114,
        avgResponseTime: 8500
      };

      const mockRankings: StudentRanking[] = [
        {
          userId: '1',
          username: 'María González',
          level: 45,
          rank: 'S',
          thetaScore: 2.34,
          masteryAvg: 89.2,
          totalBattles: 28,
          winRate: 85.7,
          lastActivity: '2024-01-15T14:30:00Z',
          streakDays: 12
        },
        {
          userId: '2',
          username: 'Carlos Rodríguez',
          level: 42,
          rank: 'A',
          thetaScore: 1.89,
          masteryAvg: 82.1,
          totalBattles: 25,
          winRate: 80.0,
          lastActivity: '2024-01-15T16:45:00Z',
          streakDays: 8
        },
        // Agregar más estudiantes...
      ];

      setKpis(mockKpis);
      setStudentRankings(mockRankings);
    } catch (err) {
      setError('Error al cargar analytics de la clase');
      console.error(err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchClassAnalytics();
  }, [classId, selectedPeriod]);

  const renderKPICard = (
    title: string,
    value: string | number,
    icon: React.ReactNode,
    trend?: { value: number; isPositive: boolean; period: string },
    color: string = 'purple',
    subtitle?: string
  ) => (
    <motion.div
      className="bg-gray-900/80 rounded-lg p-6 border border-gray-700/50"
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
            <span>{trend.isPositive ? '+' : ''}{trend.value}%</span>
            <span className="text-gray-500 text-xs">{trend.period}</span>
          </div>
        )}
      </div>
      
      <p className="text-gray-400 text-sm mb-1">{title}</p>
      <p className="text-2xl font-bold text-white">{value}</p>
      {subtitle && <p className="text-gray-500 text-xs mt-1">{subtitle}</p>}
    </motion.div>
  );

  const renderSubjectMastery = () => (
    <motion.div
      className="bg-gray-900/80 rounded-lg p-6 border border-gray-700/50"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
        <BookOpen className="w-5 h-5 text-blue-400" />
        Mastery por Materia
      </h3>
      
      <div className="space-y-4">
        {kpis && Object.entries(kpis.masteryBySubject).map(([subject, mastery]) => (
          <div key={subject} className="space-y-2">
            <div className="flex justify-between items-center">
              <span className="text-gray-300 capitalize">
                {subject === 'math' ? 'Matemáticas' :
                 subject === 'spanish' ? 'Español' :
                 subject === 'science' ? 'Ciencias' :
                 subject === 'social' ? 'Sociales' :
                 subject === 'english' ? 'Inglés' : subject}
              </span>
              <span className={`font-semibold ${
                mastery >= 80 ? 'text-green-400' :
                mastery >= 70 ? 'text-yellow-400' :
                mastery >= 60 ? 'text-orange-400' :
                'text-red-400'
              }`}>
                {mastery.toFixed(1)}%
              </span>
            </div>
            <div className="w-full bg-gray-700/50 rounded-full h-2">
              <div 
                className={`h-2 rounded-full ${
                  mastery >= 80 ? 'bg-green-500' :
                  mastery >= 70 ? 'bg-yellow-500' :
                  mastery >= 60 ? 'bg-orange-500' :
                  'bg-red-500'
                }`}
                style={{ width: `${mastery}%` }}
              />
            </div>
          </div>
        ))}
      </div>
    </motion.div>
  );

  const renderRPGDistribution = () => (
    <motion.div
      className="bg-gray-900/80 rounded-lg p-6 border border-gray-700/50"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
        <Award className="w-5 h-5 text-purple-400" />
        Distribución de Rangos RPG
      </h3>
      
      <div className="grid grid-cols-7 gap-2">
        {kpis && Object.entries(kpis.rpgDistribution).map(([rank, count]) => (
          <div key={rank} className="text-center">
            <div className={`w-12 h-12 rounded-lg flex items-center justify-center mb-2 ${getRankColor(rank)}`}>
              {getRankIcon(rank)}
            </div>
            <div className="text-xs text-gray-400 mb-1">{rank}</div>
            <div className="text-sm font-semibold text-white">{count}</div>
          </div>
        ))}
      </div>
      
      {kpis && (
        <div className="mt-4 pt-4 border-t border-gray-700/50">
          <div className="text-sm text-gray-400">
            Distribución: {Math.round((kpis.rpgDistribution.A + kpis.rpgDistribution.S + kpis.rpgDistribution['S+']) / kpis.totalStudents * 100)}% 
            <span className="text-green-400"> avanzado</span>, {' '}
            {Math.round((kpis.rpgDistribution.B + kpis.rpgDistribution.C) / kpis.totalStudents * 100)}%
            <span className="text-yellow-400"> intermedio</span>, {' '}
            {Math.round((kpis.rpgDistribution.D + kpis.rpgDistribution.E) / kpis.totalStudents * 100)}%
            <span className="text-red-400"> básico</span>
          </div>
        </div>
      )}
    </motion.div>
  );

  const renderStudentRankings = () => (
    <motion.div
      className="bg-gray-900/80 rounded-lg p-6 border border-gray-700/50"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
        <Medal className="w-5 h-5 text-yellow-400" />
        Ranking de Clase (Top 10)
      </h3>
      
      <div className="space-y-3 max-h-96 overflow-y-auto">
        {studentRankings.map((student, index) => (
          <div 
            key={student.userId}
            className="flex items-center justify-between p-3 bg-gray-800/50 rounded-lg hover:bg-gray-800 transition-colors"
          >
            <div className="flex items-center gap-3">
              <div className={`w-8 h-8 rounded-full flex items-center justify-center font-bold ${
                index < 3 ? 'bg-gradient-to-r from-yellow-500 to-orange-500 text-black' : 'bg-gray-700 text-gray-300'
              }`}>
                {index + 1}
              </div>
              
              <div className="flex items-center gap-2">
                <div className={`px-2 py-1 rounded text-xs font-semibold ${getRankColor(student.rank)}`}>
                  {getRankIcon(student.rank)}
                  <span className="ml-1">{student.rank}</span>
                </div>
                <span className="text-white font-medium">{student.username}</span>
                <span className="text-gray-400 text-sm">Nv.{student.level}</span>
              </div>
            </div>
            
            <div className="flex items-center gap-4 text-sm">
              <div className="text-center">
                <div className="text-green-400 font-semibold">{student.masteryAvg.toFixed(1)}%</div>
                <div className="text-gray-500 text-xs">Mastery</div>
              </div>
              
              <div className="text-center">
                <div className="text-blue-400 font-semibold">{student.thetaScore.toFixed(2)}</div>
                <div className="text-gray-500 text-xs">Theta</div>
              </div>
              
              <div className="text-center">
                <div className="text-purple-400 font-semibold">{student.winRate.toFixed(1)}%</div>
                <div className="text-gray-500 text-xs">Win Rate</div>
              </div>
              
              {student.streakDays > 0 && (
                <div className="text-orange-400 text-xs">
                  🔥 {student.streakDays}d
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </motion.div>
  );

  if (loading && !refreshing) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="w-8 h-8 text-purple-400 animate-spin" />
      </div>
    );
  }

  if (error || !kpis) {
    return (
      <div className="bg-red-900/20 border border-red-500/50 rounded-lg p-6 text-center">
        <p className="text-red-400">{error || 'No hay datos disponibles'}</p>
        <button
          onClick={fetchClassAnalytics}
          className="mt-4 px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg"
        >
          Reintentar
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header Controls */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-white">Analytics de Clase</h2>
          <p className="text-gray-400">{className} • {kpis.totalStudents} estudiantes</p>
        </div>
        
        <div className="flex items-center gap-4">
          {/* Period Selector */}
          <div className="flex items-center gap-2 bg-gray-900/80 rounded-lg p-1">
            {(['7d', '30d', '90d'] as const).map(period => (
              <button
                key={period}
                onClick={() => setSelectedPeriod(period)}
                className={`px-4 py-2 rounded-lg text-sm font-semibold transition-all ${
                  selectedPeriod === period
                    ? 'bg-purple-600 text-white'
                    : 'text-gray-400 hover:text-white'
                }`}
              >
                {period === '7d' && 'Última semana'}
                {period === '30d' && 'Último mes'}
                {period === '90d' && 'Últimos 3 meses'}
              </button>
            ))}
          </div>
          
          {/* Action Buttons */}
          <button
            onClick={fetchClassAnalytics}
            disabled={refreshing}
            className="p-2 bg-gray-800 hover:bg-gray-700 rounded-lg transition-all disabled:opacity-50"
            title="Actualizar"
          >
            <RefreshCw className={`w-5 h-5 text-gray-400 ${refreshing ? 'animate-spin' : ''}`} />
          </button>
          
          <button
            className="p-2 bg-gray-800 hover:bg-gray-700 rounded-lg transition-all"
            title="Exportar datos"
          >
            <Download className="w-5 h-5 text-gray-400" />
          </button>
        </div>
      </div>
      
      {/* Key Performance Indicators */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {renderKPICard(
          'Estudiantes Activos',
          `${kpis.activeStudents}/${kpis.totalStudents}`,
          <Users className="w-6 h-6 text-blue-400" />,
          undefined,
          'blue',
          `${Math.round((kpis.activeStudents / kpis.totalStudents) * 100)}% de participación`
        )}
        
        {renderKPICard(
          'Mastery Promedio',
          `${kpis.avgMastery.toFixed(1)}%`,
          <Target className="w-6 h-6 text-green-400" />,
          { value: kpis.progressDelta30d, isPositive: kpis.progressDelta30d > 0, period: '30d' },
          'green'
        )}
        
        {renderKPICard(
          'Batallas Totales',
          kpis.totalBattles.toLocaleString(),
          <Activity className="w-6 h-6 text-purple-400" />,
          undefined,
          'purple',
          `${Math.round(kpis.totalCorrect / kpis.totalQuestions * 100)}% precisión`
        )}
        
        {renderKPICard(
          'Tiempo Respuesta',
          `${(kpis.avgResponseTime / 1000).toFixed(1)}s`,
          <Clock className="w-6 h-6 text-orange-400" />,
          undefined,
          'orange',
          'Promedio de la clase'
        )}
      </div>
      
      {/* Detailed Analytics */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {renderSubjectMastery()}
        {renderRPGDistribution()}
      </div>
      
      {/* Student Rankings */}
      {renderStudentRankings()}
    </div>
  );
}