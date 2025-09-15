'use client';

import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { 
  TrendingUp,
  TrendingDown,
  Target,
  BookOpen,
  Clock,
  BarChart3,
  PieChart,
  LineChart,
  AlertTriangle,
  CheckCircle,
  Calendar,
  Brain,
  Star,
  Lightbulb
} from 'lucide-react';

interface LearningCurveData {
  date: string;
  battles_count: number;
  accuracy: number;
  avg_duration: number;
  experience_gained: number;
  avg_difficulty_attempted: number;
}

interface SubjectProgressData {
  subject_name: string;
  questions_answered: number;
  accuracy: number;
  avg_difficulty: number;
  first_attempt: string;
  last_attempt: string;
  total_experience: number;
}

interface TopicData {
  topic_name: string;
  subject_name: string;
  attempts: number;
  success_rate: number;
  avg_difficulty: number;
}

interface StudentProgressData {
  learning_curve: LearningCurveData[];
  subject_progress: SubjectProgressData[];
  weaknesses: TopicData[];
  strengths: TopicData[];
}

interface StudentProgressAnalyticsProps {
  studentId?: string;
  isTeacherView?: boolean;
}

export default function StudentProgressAnalytics({ 
  studentId, 
  isTeacherView = false 
}: StudentProgressAnalyticsProps) {
  const [data, setData] = useState<StudentProgressData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchProgressData();
  }, [studentId]);

  const fetchProgressData = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const params = studentId ? `?student_id=${studentId}` : '';
      const response = await fetch(`/api/educational-analytics/student-progress-analytics${params}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      
      if (!response.ok) {
        throw new Error('Error al cargar datos de progreso');
      }
      
      const progressData = await response.json();
      setData(progressData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error desconocido');
    } finally {
      setLoading(false);
    }
  };

  const calculateTrend = (curveData: LearningCurveData[]) => {
    if (curveData.length < 2) return { trend: 0, isPositive: true };
    
    const recent = curveData.slice(-7); // Last 7 days
    const older = curveData.slice(-14, -7); // Previous 7 days
    
    const recentAvg = recent.reduce((sum, item) => sum + item.accuracy, 0) / recent.length;
    const olderAvg = older.reduce((sum, item) => sum + item.accuracy, 0) / older.length;
    
    const trend = ((recentAvg - olderAvg) / olderAvg) * 100;
    return { trend: Math.abs(trend), isPositive: trend > 0 };
  };

  const getPerformanceLevel = (accuracy: number) => {
    if (accuracy >= 0.8) return { level: 'Excelente', color: 'text-green-400', bgColor: 'bg-green-500/20' };
    if (accuracy >= 0.7) return { level: 'Bueno', color: 'text-blue-400', bgColor: 'bg-blue-500/20' };
    if (accuracy >= 0.6) return { level: 'Regular', color: 'text-yellow-400', bgColor: 'bg-yellow-500/20' };
    return { level: 'Necesita Mejora', color: 'text-red-400', bgColor: 'bg-red-500/20' };
  };

  const renderLearningCurveChart = () => (
    <motion.div
      className="bg-gray-900/80 rounded-lg p-6"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-white flex items-center gap-2">
          <LineChart className="w-5 h-5 text-purple-400" />
          Curva de Aprendizaje
        </h3>
        {data && data.learning_curve.length > 0 && (
          <div className="flex items-center gap-2">
            {(() => {
              const trendData = calculateTrend(data.learning_curve);
              return (
                <div className={`flex items-center gap-1 text-sm ${
                  trendData.isPositive ? 'text-green-400' : 'text-red-400'
                }`}>
                  {trendData.isPositive ? 
                    <TrendingUp className="w-4 h-4" /> : 
                    <TrendingDown className="w-4 h-4" />
                  }
                  <span>{trendData.trend.toFixed(1)}%</span>
                </div>
              );
            })()}
          </div>
        )}
      </div>
      
      <div className="h-64 flex items-center justify-center">
        {data && data.learning_curve.length > 0 ? (
          <div className="w-full h-full relative">
            {/* Placeholder for actual chart library integration */}
            <div className="absolute inset-0 flex items-center justify-center text-gray-400">
              <div className="text-center">
                <BarChart3 className="w-12 h-12 mx-auto mb-2 text-purple-400" />
                <p>Curva de aprendizaje con {data.learning_curve.length} puntos de datos</p>
                <p className="text-sm mt-1">
                  Precisión promedio: {(data.learning_curve.reduce((sum, item) => sum + item.accuracy, 0) / data.learning_curve.length * 100).toFixed(1)}%
                </p>
              </div>
            </div>
          </div>
        ) : (
          <div className="text-gray-500">No hay datos suficientes para mostrar la curva</div>
        )}
      </div>
    </motion.div>
  );

  const renderSubjectProgress = () => (
    <motion.div
      className="bg-gray-900/80 rounded-lg p-6"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, delay: 0.1 }}
    >
      <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
        <BookOpen className="w-5 h-5 text-blue-400" />
        Progreso por Materia
      </h3>
      
      <div className="space-y-4">
        {data?.subject_progress.map((subject, index) => {
          const performance = getPerformanceLevel(subject.accuracy);
          
          return (
            <div key={index} className="bg-gray-800/50 rounded-lg p-4">
              <div className="flex items-center justify-between mb-3">
                <h4 className="font-semibold text-white">{subject.subject_name}</h4>
                <span className={`px-3 py-1 rounded-full text-sm font-semibold ${performance.bgColor} ${performance.color}`}>
                  {performance.level}
                </span>
              </div>
              
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                <div>
                  <p className="text-gray-400">Preguntas</p>
                  <p className="text-white font-semibold">{subject.questions_answered}</p>
                </div>
                <div>
                  <p className="text-gray-400">Precisión</p>
                  <p className="text-white font-semibold">{(subject.accuracy * 100).toFixed(1)}%</p>
                </div>
                <div>
                  <p className="text-gray-400">Dificultad Prom.</p>
                  <p className="text-white font-semibold">{subject.avg_difficulty.toFixed(1)}</p>
                </div>
                <div>
                  <p className="text-gray-400">Experiencia</p>
                  <p className="text-white font-semibold">{subject.total_experience}</p>
                </div>
              </div>
              
              {/* Progress bar */}
              <div className="mt-3">
                <div className="bg-gray-700 rounded-full h-2">
                  <div 
                    className="bg-gradient-to-r from-purple-500 to-blue-500 h-2 rounded-full transition-all duration-500"
                    style={{ width: `${Math.min(100, subject.accuracy * 100)}%` }}
                  />
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </motion.div>
  );

  const renderStrengthsAndWeaknesses = () => (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* Fortalezas */}
      <motion.div
        className="bg-gray-900/80 rounded-lg p-6"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3, delay: 0.2 }}
      >
        <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <Star className="w-5 h-5 text-green-400" />
          Fortalezas
        </h3>
        
        <div className="space-y-3">
          {data?.strengths.length > 0 ? (
            data.strengths.map((strength, index) => (
              <div key={index} className="bg-green-500/10 rounded-lg p-3 border border-green-500/20">
                <div className="flex items-center justify-between mb-2">
                  <h4 className="font-semibold text-green-400">{strength.topic_name}</h4>
                  <span className="text-green-300 text-sm">{(strength.success_rate * 100).toFixed(1)}%</span>
                </div>
                <p className="text-gray-300 text-sm">{strength.subject_name}</p>
                <div className="flex items-center gap-4 mt-2 text-xs text-gray-400">
                  <span>{strength.attempts} intentos</span>
                  <span>Dificultad: {strength.avg_difficulty.toFixed(1)}</span>
                </div>
              </div>
            ))
          ) : (
            <div className="text-center text-gray-500 py-8">
              <CheckCircle className="w-12 h-12 mx-auto mb-2 text-gray-600" />
              <p>Continúa practicando para identificar fortalezas</p>
            </div>
          )}
        </div>
      </motion.div>

      {/* Debilidades */}
      <motion.div
        className="bg-gray-900/80 rounded-lg p-6"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3, delay: 0.3 }}
      >
        <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <Target className="w-5 h-5 text-orange-400" />
          Áreas de Mejora
        </h3>
        
        <div className="space-y-3">
          {data?.weaknesses.length > 0 ? (
            data.weaknesses.map((weakness, index) => (
              <div key={index} className="bg-orange-500/10 rounded-lg p-3 border border-orange-500/20">
                <div className="flex items-center justify-between mb-2">
                  <h4 className="font-semibold text-orange-400">{weakness.topic_name}</h4>
                  <span className="text-orange-300 text-sm">{(weakness.success_rate * 100).toFixed(1)}%</span>
                </div>
                <p className="text-gray-300 text-sm">{weakness.subject_name}</p>
                <div className="flex items-center gap-4 mt-2 text-xs text-gray-400">
                  <span>{weakness.attempts} intentos</span>
                  <span>Dificultad: {weakness.avg_difficulty.toFixed(1)}</span>
                </div>
                <div className="mt-2">
                  <button className="text-xs bg-orange-600 hover:bg-orange-700 text-white px-2 py-1 rounded transition-colors">
                    Practicar Ahora
                  </button>
                </div>
              </div>
            ))
          ) : (
            <div className="text-center text-gray-500 py-8">
              <Brain className="w-12 h-12 mx-auto mb-2 text-gray-600" />
              <p>¡Excelente! No se detectaron áreas problemáticas</p>
            </div>
          )}
        </div>
      </motion.div>
    </div>
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-400"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-900/20 border border-red-500/50 rounded-lg p-6 text-center">
        <AlertTriangle className="w-12 h-12 text-red-400 mx-auto mb-4" />
        <p className="text-red-400 mb-4">{error}</p>
        <button
          onClick={fetchProgressData}
          className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors"
        >
          Reintentar
        </button>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="text-center text-gray-500 py-8">
        <BookOpen className="w-12 h-12 mx-auto mb-4 text-gray-600" />
        <p>No hay datos de progreso disponibles</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-white flex items-center gap-2">
          <Brain className="w-8 h-8 text-purple-400" />
          Análisis de Progreso Estudiantil
        </h2>
        
        {isTeacherView && (
          <div className="bg-yellow-500/20 text-yellow-400 px-4 py-2 rounded-lg text-sm">
            Vista de Profesor
          </div>
        )}
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <motion.div
          className="bg-gray-900/80 rounded-lg p-4"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <div className="flex items-center gap-3">
            <div className="p-2 bg-purple-500/20 rounded-lg">
              <Calendar className="w-6 h-6 text-purple-400" />
            </div>
            <div>
              <p className="text-gray-400 text-sm">Días Activos</p>
              <p className="text-white text-lg font-bold">{data.learning_curve.length}</p>
            </div>
          </div>
        </motion.div>

        <motion.div
          className="bg-gray-900/80 rounded-lg p-4"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
        >
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-500/20 rounded-lg">
              <BookOpen className="w-6 h-6 text-blue-400" />
            </div>
            <div>
              <p className="text-gray-400 text-sm">Materias</p>
              <p className="text-white text-lg font-bold">{data.subject_progress.length}</p>
            </div>
          </div>
        </motion.div>

        <motion.div
          className="bg-gray-900/80 rounded-lg p-4"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
        >
          <div className="flex items-center gap-3">
            <div className="p-2 bg-green-500/20 rounded-lg">
              <Star className="w-6 h-6 text-green-400" />
            </div>
            <div>
              <p className="text-gray-400 text-sm">Fortalezas</p>
              <p className="text-white text-lg font-bold">{data.strengths.length}</p>
            </div>
          </div>
        </motion.div>

        <motion.div
          className="bg-gray-900/80 rounded-lg p-4"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
        >
          <div className="flex items-center gap-3">
            <div className="p-2 bg-orange-500/20 rounded-lg">
              <Target className="w-6 h-6 text-orange-400" />
            </div>
            <div>
              <p className="text-gray-400 text-sm">Áreas de Mejora</p>
              <p className="text-white text-lg font-bold">{data.weaknesses.length}</p>
            </div>
          </div>
        </motion.div>
      </div>

      {/* Learning Curve Chart */}
      {renderLearningCurveChart()}

      {/* Subject Progress */}
      {renderSubjectProgress()}

      {/* Strengths and Weaknesses */}
      {renderStrengthsAndWeaknesses()}

      {/* Educational Insights */}
      <motion.div
        className="bg-gradient-to-r from-purple-900/30 to-blue-900/30 rounded-lg p-6 border border-purple-500/30"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3, delay: 0.4 }}
      >
        <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <Lightbulb className="w-5 h-5 text-yellow-400" />
          Recomendaciones Personalizadas
        </h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {data.weaknesses.length > 0 && (
            <div className="bg-gray-800/50 rounded-lg p-4">
              <h4 className="font-semibold text-orange-400 mb-2">Enfoque de Estudio</h4>
              <p className="text-gray-300 text-sm">
                Concentra tu próxima sesión en <strong>{data.weaknesses[0].topic_name}</strong> 
                para mejorar tu rendimiento en {data.weaknesses[0].subject_name}.
              </p>
            </div>
          )}
          
          {data.strengths.length > 0 && (
            <div className="bg-gray-800/50 rounded-lg p-4">
              <h4 className="font-semibold text-green-400 mb-2">Mantén el Ritmo</h4>
              <p className="text-gray-300 text-sm">
                Excelente dominio en <strong>{data.strengths[0].topic_name}</strong>. 
                Considera intentar preguntas de mayor dificultad.
              </p>
            </div>
          )}
        </div>
      </motion.div>
    </div>
  );
}