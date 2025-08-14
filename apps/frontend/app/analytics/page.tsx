'use client';

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { 
  BarChart3, 
  TrendingUp, 
  Target, 
  Trophy, 
  Award,
  Download,
  Calendar,
  BookOpen,
  Zap,
  Activity,
  PieChart,
  BarChart,
  LineChart,
  Thermometer,
  Users,
  Star
} from 'lucide-react';

interface SubjectProgress {
  subject_id: string;
  subject_name: string;
  questions_answered: number;
  correct_answers: number;
  accuracy_percentage: number;
  average_difficulty: number;
  total_experience: number;
  level_progress: number;
  last_activity: string;
}

interface ICFESProjection {
  current_score: number;
  projected_score: number;
  improvement_rate: number;
  target_score: number;
  weeks_to_target: number;
  confidence_level: number;
}

interface NationalComparison {
  user_percentile: number;
  national_average: number;
  user_score: number;
  difference_from_average: number;
  ranking_position: number;
  total_students: number;
}

interface StrengthWeaknessHeatmap {
  subject: string;
  topics: string[];
  strength_scores: number[];
  weakness_scores: number[];
  overall_strength: number;
  overall_weakness: number;
}

interface PersonalAnalytics {
  user_id: string;
  username: string;
  current_level: number;
  current_rank: string;
  total_experience: number;
  subjects_progress: SubjectProgress[];
  icfes_projection: ICFESProjection;
  national_comparison: NationalComparison;
  strength_weakness_heatmap: StrengthWeaknessHeatmap[];
  total_battles: number;
  win_rate: number;
  average_session_duration: number;
  streak_days: number;
  total_questions_answered: number;
  overall_accuracy: number;
  weekly_progress: any[];
  monthly_trends: any[];
  generated_at: string;
}

export default function AnalyticsPage() {
  const [analytics, setAnalytics] = useState<PersonalAnalytics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState('overview');

  useEffect(() => {
    fetchAnalytics();
  }, []);

  const fetchAnalytics = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/v1/analytics/personal', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (!response.ok) {
        throw new Error('Error cargando analytics');
      }

      const data = await response.json();
      setAnalytics(data);
    } catch (error) {
      console.error('Error loading analytics:', error);
      setError('Error cargando datos de analytics');
    } finally {
      setLoading(false);
    }
  };

  const exportPDF = async () => {
    try {
      const response = await fetch('/api/v1/analytics/personal/export-pdf', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (!response.ok) {
        throw new Error('Error exportando PDF');
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `analytics_${analytics?.username}_${new Date().toISOString().split('T')[0]}.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error('Error exporting PDF:', error);
      alert('Error exportando PDF');
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gold-400 mx-auto mb-4"></div>
          <p className="text-mist-purple-300">Cargando analytics...</p>
        </div>
      </div>
    );
  }

  if (error || !analytics) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-400 mb-4">{error || 'Error cargando analytics'}</p>
          <button 
            onClick={fetchAnalytics}
            className="bg-gold-500 hover:bg-gold-600 text-white px-4 py-2 rounded-lg"
          >
            Reintentar
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <motion.div 
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8"
        >
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-4xl font-bold text-gold-400 mb-2">
                📊 Dashboard de Analytics Personal
              </h1>
              <p className="text-mist-purple-300">
                Análisis detallado de tu progreso y proyecciones ICFES
              </p>
            </div>
            <button
              onClick={exportPDF}
              className="bg-gold-500 hover:bg-gold-600 text-white px-6 py-3 rounded-lg flex items-center space-x-2"
            >
              <Download className="w-5 h-5" />
              <span>Exportar PDF</span>
            </button>
          </div>
        </motion.div>

        {/* Tabs */}
        <div className="bg-mist-purple-800/50 rounded-lg p-1 mb-8">
          <div className="flex space-x-1">
            {[
              { id: 'overview', label: 'Resumen', icon: BarChart3 },
              { id: 'progress', label: 'Progreso', icon: TrendingUp },
              { id: 'icfes', label: 'Proyección ICFES', icon: Target },
              { id: 'comparison', label: 'Comparación', icon: Users },
              { id: 'heatmap', label: 'Fortalezas/Debilidades', icon: Thermometer }
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex-1 flex items-center justify-center space-x-2 px-4 py-3 rounded-md transition-all ${
                  activeTab === tab.id
                    ? 'bg-gold-500 text-white'
                    : 'text-mist-purple-300 hover:text-white hover:bg-mist-purple-700/50'
                }`}
              >
                <tab.icon className="w-5 h-5" />
                <span>{tab.label}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Content */}
        <motion.div
          key={activeTab}
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.3 }}
        >
          {activeTab === 'overview' && <OverviewTab analytics={analytics} />}
          {activeTab === 'progress' && <ProgressTab analytics={analytics} />}
          {activeTab === 'icfes' && <ICFESTab analytics={analytics} />}
          {activeTab === 'comparison' && <ComparisonTab analytics={analytics} />}
          {activeTab === 'heatmap' && <HeatmapTab analytics={analytics} />}
        </motion.div>
      </div>
    </div>
  );
}

function OverviewTab({ analytics }: { analytics: PersonalAnalytics }) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      {/* Stats Cards */}
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        className="bg-mist-purple-800/50 rounded-lg p-6 border border-mist-purple-600"
      >
        <div className="flex items-center space-x-3 mb-4">
          <div className="p-2 bg-blue-500/20 rounded-lg">
            <Trophy className="w-6 h-6 text-blue-400" />
          </div>
          <div>
            <p className="text-mist-purple-300 text-sm">Nivel Actual</p>
            <p className="text-2xl font-bold text-white">{analytics.current_level}</p>
          </div>
        </div>
        <p className="text-gold-400 text-sm">Rank {analytics.current_rank}</p>
      </motion.div>

      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ delay: 0.1 }}
        className="bg-mist-purple-800/50 rounded-lg p-6 border border-mist-purple-600"
      >
        <div className="flex items-center space-x-3 mb-4">
          <div className="p-2 bg-green-500/20 rounded-lg">
            <Target className="w-6 h-6 text-green-400" />
          </div>
          <div>
            <p className="text-mist-purple-300 text-sm">Precisión General</p>
            <p className="text-2xl font-bold text-white">{analytics.overall_accuracy}%</p>
          </div>
        </div>
        <p className="text-gold-400 text-sm">{analytics.total_questions_answered} preguntas</p>
      </motion.div>

      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ delay: 0.2 }}
        className="bg-mist-purple-800/50 rounded-lg p-6 border border-mist-purple-600"
      >
        <div className="flex items-center space-x-3 mb-4">
          <div className="p-2 bg-purple-500/20 rounded-lg">
            <Zap className="w-6 h-6 text-purple-400" />
          </div>
          <div>
            <p className="text-mist-purple-300 text-sm">Tasa de Victoria</p>
            <p className="text-2xl font-bold text-white">{analytics.win_rate}%</p>
          </div>
        </div>
        <p className="text-gold-400 text-sm">{analytics.total_battles} batallas</p>
      </motion.div>

      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ delay: 0.3 }}
        className="bg-mist-purple-800/50 rounded-lg p-6 border border-mist-purple-600"
      >
        <div className="flex items-center space-x-3 mb-4">
          <div className="p-2 bg-orange-500/20 rounded-lg">
            <Activity className="w-6 h-6 text-orange-400" />
          </div>
          <div>
            <p className="text-mist-purple-300 text-sm">Racha Actual</p>
            <p className="text-2xl font-bold text-white">{analytics.streak_days} días</p>
          </div>
        </div>
        <p className="text-gold-400 text-sm">¡Mantén la racha!</p>
      </motion.div>

      {/* ICFES Projection */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
        className="md:col-span-2 bg-gradient-to-r from-blue-600/20 to-purple-600/20 rounded-lg p-6 border border-blue-500/30"
      >
        <h3 className="text-xl font-bold text-white mb-4 flex items-center space-x-2">
          <Target className="w-6 h-6 text-gold-400" />
          <span>Proyección ICFES</span>
        </h3>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <p className="text-mist-purple-300 text-sm">Puntaje Actual</p>
            <p className="text-3xl font-bold text-blue-400">{analytics.icfes_projection.current_score}</p>
          </div>
          <div>
            <p className="text-mist-purple-300 text-sm">Puntaje Proyectado</p>
            <p className="text-3xl font-bold text-purple-400">{analytics.icfes_projection.projected_score}</p>
          </div>
        </div>
        <div className="mt-4">
          <div className="flex justify-between text-sm">
            <span className="text-mist-purple-300">Progreso hacia objetivo</span>
            <span className="text-gold-400">{analytics.icfes_projection.weeks_to_target} semanas</span>
          </div>
          <div className="w-full bg-mist-purple-700 rounded-full h-2 mt-2">
            <div 
              className="bg-gradient-to-r from-blue-500 to-purple-500 h-2 rounded-full transition-all duration-500"
              style={{ width: `${(analytics.icfes_projection.current_score / 500) * 100}%` }}
            ></div>
          </div>
        </div>
      </motion.div>

      {/* National Comparison */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.5 }}
        className="md:col-span-2 bg-gradient-to-r from-green-600/20 to-teal-600/20 rounded-lg p-6 border border-green-500/30"
      >
        <h3 className="text-xl font-bold text-white mb-4 flex items-center space-x-2">
          <Users className="w-6 h-6 text-gold-400" />
          <span>Comparación Nacional</span>
        </h3>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <p className="text-mist-purple-300 text-sm">Tu Puntaje</p>
            <p className="text-3xl font-bold text-green-400">{analytics.national_comparison.user_score}</p>
          </div>
          <div>
            <p className="text-mist-purple-300 text-sm">Promedio Nacional</p>
            <p className="text-3xl font-bold text-teal-400">{analytics.national_comparison.national_average}</p>
          </div>
        </div>
        <div className="mt-4">
          <p className="text-gold-400 text-sm">
            Estás en el percentil {analytics.national_comparison.user_percentile}%
          </p>
          <p className="text-mist-purple-300 text-sm">
            Posición #{analytics.national_comparison.ranking_position} de {analytics.national_comparison.total_students.toLocaleString()}
          </p>
        </div>
      </motion.div>
    </div>
  );
}

function ProgressTab({ analytics }: { analytics: PersonalAnalytics }) {
  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-white mb-6">Progreso por Materia</h2>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {analytics.subjects_progress.map((subject, index) => (
          <motion.div
            key={subject.subject_id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
            className="bg-mist-purple-800/50 rounded-lg p-6 border border-mist-purple-600"
          >
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-white">{subject.subject_name}</h3>
              <div className="text-right">
                <p className="text-2xl font-bold text-gold-400">{subject.accuracy_percentage}%</p>
                <p className="text-sm text-mist-purple-300">Precisión</p>
              </div>
            </div>
            
            <div className="space-y-3">
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-mist-purple-300">Progreso</span>
                  <span className="text-gold-400">{subject.level_progress}%</span>
                </div>
                <div className="w-full bg-mist-purple-700 rounded-full h-2">
                  <div 
                    className="bg-gradient-to-r from-blue-500 to-purple-500 h-2 rounded-full transition-all duration-500"
                    style={{ width: `${subject.level_progress}%` }}
                  ></div>
                </div>
              </div>
              
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <p className="text-mist-purple-300">Preguntas</p>
                  <p className="text-white font-semibold">{subject.questions_answered}</p>
                </div>
                <div>
                  <p className="text-mist-purple-300">Correctas</p>
                  <p className="text-white font-semibold">{subject.correct_answers}</p>
                </div>
                <div>
                  <p className="text-mist-purple-300">Dificultad</p>
                  <p className="text-white font-semibold">{subject.average_difficulty}/10</p>
                </div>
                <div>
                  <p className="text-mist-purple-300">Experiencia</p>
                  <p className="text-white font-semibold">{subject.total_experience}</p>
                </div>
              </div>
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  );
}

function ICFESTab({ analytics }: { analytics: PersonalAnalytics }) {
  const projection = analytics.icfes_projection;
  
  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-white mb-6">Proyección ICFES</h2>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Current vs Projected */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          className="bg-mist-purple-800/50 rounded-lg p-6 border border-mist-purple-600"
        >
          <h3 className="text-xl font-semibold text-white mb-4">Puntajes</h3>
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <span className="text-mist-purple-300">Puntaje Actual</span>
              <span className="text-2xl font-bold text-blue-400">{projection.current_score}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-mist-purple-300">Puntaje Proyectado</span>
              <span className="text-2xl font-bold text-purple-400">{projection.projected_score}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-mist-purple-300">Puntaje Objetivo</span>
              <span className="text-2xl font-bold text-gold-400">{projection.target_score}</span>
            </div>
          </div>
        </motion.div>

        {/* Improvement Metrics */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          className="bg-mist-purple-800/50 rounded-lg p-6 border border-mist-purple-600"
        >
          <h3 className="text-xl font-semibold text-white mb-4">Métricas de Mejora</h3>
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <span className="text-mist-purple-300">Tasa de Mejora</span>
              <span className={`text-lg font-semibold ${projection.improvement_rate > 0 ? 'text-green-400' : 'text-red-400'}`}>
                {projection.improvement_rate > 0 ? '+' : ''}{projection.improvement_rate}%
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-mist-purple-300">Semanas al Objetivo</span>
              <span className="text-lg font-semibold text-gold-400">{projection.weeks_to_target}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-mist-purple-300">Nivel de Confianza</span>
              <span className="text-lg font-semibold text-blue-400">{projection.confidence_level * 100}%</span>
            </div>
          </div>
        </motion.div>
      </div>

      {/* Progress Chart */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-mist-purple-800/50 rounded-lg p-6 border border-mist-purple-600"
      >
        <h3 className="text-xl font-semibold text-white mb-4">Progreso hacia Objetivo</h3>
        <div className="relative">
          <div className="w-full bg-mist-purple-700 rounded-full h-4">
            <div 
              className="bg-gradient-to-r from-blue-500 via-purple-500 to-gold-500 h-4 rounded-full transition-all duration-1000"
              style={{ width: `${(projection.current_score / projection.target_score) * 100}%` }}
            ></div>
          </div>
          <div className="flex justify-between text-sm mt-2">
            <span className="text-mist-purple-300">200</span>
            <span className="text-gold-400">Objetivo: {projection.target_score}</span>
            <span className="text-mist-purple-300">500</span>
          </div>
        </div>
      </motion.div>
    </div>
  );
}

function ComparisonTab({ analytics }: { analytics: PersonalAnalytics }) {
  const comparison = analytics.national_comparison;
  
  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-white mb-6">Comparación Nacional</h2>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Score Comparison */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          className="bg-mist-purple-800/50 rounded-lg p-6 border border-mist-purple-600"
        >
          <h3 className="text-xl font-semibold text-white mb-4">Comparación de Puntajes</h3>
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <span className="text-mist-purple-300">Tu Puntaje</span>
              <span className="text-2xl font-bold text-green-400">{comparison.user_score}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-mist-purple-300">Promedio Nacional</span>
              <span className="text-2xl font-bold text-blue-400">{comparison.national_average}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-mist-purple-300">Diferencia</span>
              <span className={`text-lg font-semibold ${comparison.difference_from_average > 0 ? 'text-green-400' : 'text-red-400'}`}>
                {comparison.difference_from_average > 0 ? '+' : ''}{comparison.difference_from_average}
              </span>
            </div>
          </div>
        </motion.div>

        {/* Ranking */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          className="bg-mist-purple-800/50 rounded-lg p-6 border border-mist-purple-600"
        >
          <h3 className="text-xl font-semibold text-white mb-4">Posición Nacional</h3>
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <span className="text-mist-purple-300">Percentil</span>
              <span className="text-2xl font-bold text-gold-400">{comparison.user_percentile}%</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-mist-purple-300">Posición</span>
              <span className="text-2xl font-bold text-purple-400">#{comparison.ranking_position}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-mist-purple-300">Total Estudiantes</span>
              <span className="text-lg font-semibold text-blue-400">{comparison.total_students.toLocaleString()}</span>
            </div>
          </div>
        </motion.div>
      </div>

      {/* Percentile Chart */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-mist-purple-800/50 rounded-lg p-6 border border-mist-purple-600"
      >
        <h3 className="text-xl font-semibold text-white mb-4">Distribución Nacional</h3>
        <div className="relative h-32 bg-mist-purple-700 rounded-lg p-4">
          <div className="absolute inset-4">
            <div className="w-full h-full bg-gradient-to-r from-red-500 via-yellow-500 to-green-500 rounded opacity-20"></div>
            <div 
              className="absolute top-0 bottom-0 w-1 bg-white rounded"
              style={{ left: `${comparison.user_percentile}%` }}
            ></div>
            <div className="absolute top-0 left-0 right-0 flex justify-between text-xs text-mist-purple-300">
              <span>0%</span>
              <span>50%</span>
              <span>100%</span>
            </div>
          </div>
        </div>
        <p className="text-center text-gold-400 mt-2">
          Estás en el {comparison.user_percentile}% superior
        </p>
      </motion.div>
    </div>
  );
}

function HeatmapTab({ analytics }: { analytics: PersonalAnalytics }) {
  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-white mb-6">Fortalezas y Debilidades</h2>
      
      <div className="space-y-6">
        {analytics.strength_weakness_heatmap.map((heatmap, index) => (
          <motion.div
            key={heatmap.subject}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
            className="bg-mist-purple-800/50 rounded-lg p-6 border border-mist-purple-600"
          >
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-xl font-semibold text-white">{heatmap.subject}</h3>
              <div className="text-right">
                <p className="text-sm text-mist-purple-300">Fortaleza General</p>
                <p className="text-lg font-bold text-green-400">{heatmap.overall_strength}%</p>
              </div>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Strengths */}
              <div>
                <h4 className="text-lg font-semibold text-green-400 mb-3">Fortalezas</h4>
                <div className="space-y-2">
                  {heatmap.topics.map((topic, topicIndex) => (
                    <div key={topic} className="flex justify-between items-center">
                      <span className="text-mist-purple-300 text-sm">{topic}</span>
                      <div className="flex items-center space-x-2">
                        <div className="w-20 bg-mist-purple-700 rounded-full h-2">
                          <div 
                            className="bg-green-500 h-2 rounded-full transition-all duration-500"
                            style={{ width: `${heatmap.strength_scores[topicIndex]}%` }}
                          ></div>
                        </div>
                        <span className="text-green-400 text-sm font-semibold">
                          {heatmap.strength_scores[topicIndex]}%
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Weaknesses */}
              <div>
                <h4 className="text-lg font-semibold text-red-400 mb-3">Áreas de Mejora</h4>
                <div className="space-y-2">
                  {heatmap.topics.map((topic, topicIndex) => (
                    <div key={topic} className="flex justify-between items-center">
                      <span className="text-mist-purple-300 text-sm">{topic}</span>
                      <div className="flex items-center space-x-2">
                        <div className="w-20 bg-mist-purple-700 rounded-full h-2">
                          <div 
                            className="bg-red-500 h-2 rounded-full transition-all duration-500"
                            style={{ width: `${heatmap.weakness_scores[topicIndex]}%` }}
                          ></div>
                        </div>
                        <span className="text-red-400 text-sm font-semibold">
                          {heatmap.weakness_scores[topicIndex]}%
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  );
} 