'use client';

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Activity,
  Target,
  Zap,
  Clock,
  Trophy,
  TrendingUp,
  TrendingDown,
  Eye,
  Brain,
  Heart,
  Gauge,
  BarChart3,
  Circle,
  CheckCircle2,
  XCircle,
  AlertCircle
} from 'lucide-react';
import { useRealtimeUpdates } from '@/hooks/useRealtimeUpdates';

interface MetricData {
  id: string;
  label: string;
  value: number;
  unit: string;
  change: number;
  trend: 'up' | 'down' | 'stable';
  status: 'excellent' | 'good' | 'average' | 'needs_improvement';
  icon: React.ReactNode;
  color: string;
  description: string;
}

interface SessionMetrics {
  accuracy: number;
  speed: number; // Questions per minute
  focus: number; // Percentage of focused time
  stamina: number; // Energy level
  confidence: number; // Confidence in answers
  consistency: number; // Answer time consistency
}

interface RealTimeMetricsPanelProps {
  userId?: string;
  sessionId?: string;
}

export default function RealTimeMetricsPanel({ userId, sessionId }: RealTimeMetricsPanelProps) {
  const [metrics, setMetrics] = useState<MetricData[]>([]);
  const [sessionMetrics, setSessionMetrics] = useState<SessionMetrics>({
    accuracy: 0,
    speed: 0,
    focus: 0,
    stamina: 0,
    confidence: 0,
    consistency: 0
  });
  const [isActive, setIsActive] = useState(false);
  const [sessionTime, setSessionTime] = useState(0);
  const [questionsAnswered, setQuestionsAnswered] = useState(0);

  const { isConnected, progressUpdates } = useRealtimeUpdates();

  // Simulate real-time metrics updates
  useEffect(() => {
    const updateMetrics = () => {
      const baseAccuracy = 75 + Math.random() * 20;
      const baseSpeed = 1.2 + Math.random() * 0.8;
      const baseFocus = 70 + Math.random() * 25;
      const baseStamina = Math.max(60, 95 - (sessionTime / 60) * 0.5); // Decreases over time
      const baseConfidence = 60 + Math.random() * 30;
      const baseConsistency = 75 + Math.random() * 20;

      setSessionMetrics({
        accuracy: Math.min(100, baseAccuracy),
        speed: baseSpeed,
        focus: Math.min(100, baseFocus),
        stamina: Math.min(100, baseStamina),
        confidence: Math.min(100, baseConfidence),
        consistency: Math.min(100, baseConsistency)
      });

      const newMetrics: MetricData[] = [
        {
          id: 'accuracy',
          label: 'Precisión',
          value: baseAccuracy,
          unit: '%',
          change: Math.random() * 4 - 2,
          trend: baseAccuracy > 80 ? 'up' : baseAccuracy < 70 ? 'down' : 'stable',
          status: baseAccuracy > 85 ? 'excellent' : baseAccuracy > 75 ? 'good' : baseAccuracy > 65 ? 'average' : 'needs_improvement',
          icon: <Target className="w-5 h-5" />,
          color: baseAccuracy > 85 ? 'text-green-400' : baseAccuracy > 75 ? 'text-blue-400' : baseAccuracy > 65 ? 'text-yellow-400' : 'text-red-400',
          description: 'Porcentaje de respuestas correctas'
        },
        {
          id: 'speed',
          label: 'Velocidad',
          value: baseSpeed,
          unit: 'p/min',
          change: Math.random() * 0.4 - 0.2,
          trend: baseSpeed > 1.5 ? 'up' : baseSpeed < 1.0 ? 'down' : 'stable',
          status: baseSpeed > 1.8 ? 'excellent' : baseSpeed > 1.4 ? 'good' : baseSpeed > 1.0 ? 'average' : 'needs_improvement',
          icon: <Zap className="w-5 h-5" />,
          color: baseSpeed > 1.8 ? 'text-green-400' : baseSpeed > 1.4 ? 'text-blue-400' : baseSpeed > 1.0 ? 'text-yellow-400' : 'text-red-400',
          description: 'Preguntas respondidas por minuto'
        },
        {
          id: 'focus',
          label: 'Concentración',
          value: baseFocus,
          unit: '%',
          change: Math.random() * 6 - 3,
          trend: baseFocus > 85 ? 'up' : baseFocus < 70 ? 'down' : 'stable',
          status: baseFocus > 90 ? 'excellent' : baseFocus > 80 ? 'good' : baseFocus > 70 ? 'average' : 'needs_improvement',
          icon: <Eye className="w-5 h-5" />,
          color: baseFocus > 90 ? 'text-green-400' : baseFocus > 80 ? 'text-blue-400' : baseFocus > 70 ? 'text-yellow-400' : 'text-red-400',
          description: 'Nivel de atención durante la sesión'
        },
        {
          id: 'stamina',
          label: 'Resistencia',
          value: baseStamina,
          unit: '%',
          change: -Math.random() * 2,
          trend: baseStamina > 80 ? 'stable' : baseStamina < 60 ? 'down' : 'stable',
          status: baseStamina > 85 ? 'excellent' : baseStamina > 75 ? 'good' : baseStamina > 65 ? 'average' : 'needs_improvement',
          icon: <Heart className="w-5 h-5" />,
          color: baseStamina > 85 ? 'text-green-400' : baseStamina > 75 ? 'text-blue-400' : baseStamina > 65 ? 'text-yellow-400' : 'text-red-400',
          description: 'Nivel de energía y fatiga mental'
        },
        {
          id: 'confidence',
          label: 'Confianza',
          value: baseConfidence,
          unit: '%',
          change: Math.random() * 3 - 1.5,
          trend: baseConfidence > 80 ? 'up' : baseConfidence < 65 ? 'down' : 'stable',
          status: baseConfidence > 85 ? 'excellent' : baseConfidence > 75 ? 'good' : baseConfidence > 65 ? 'average' : 'needs_improvement',
          icon: <Brain className="w-5 h-5" />,
          color: baseConfidence > 85 ? 'text-green-400' : baseConfidence > 75 ? 'text-blue-400' : baseConfidence > 65 ? 'text-yellow-400' : 'text-red-400',
          description: 'Seguridad en las respuestas dadas'
        },
        {
          id: 'consistency',
          label: 'Consistencia',
          value: baseConsistency,
          unit: '%',
          change: Math.random() * 2 - 1,
          trend: baseConsistency > 85 ? 'up' : baseConsistency < 70 ? 'down' : 'stable',
          status: baseConsistency > 90 ? 'excellent' : baseConsistency > 80 ? 'good' : baseConsistency > 70 ? 'average' : 'needs_improvement',
          icon: <Activity className="w-5 h-5" />,
          color: baseConsistency > 90 ? 'text-green-400' : baseConsistency > 80 ? 'text-blue-400' : baseConsistency > 70 ? 'text-yellow-400' : 'text-red-400',
          description: 'Uniformidad en tiempos de respuesta'
        }
      ];

      setMetrics(newMetrics);
    };

    if (isActive) {
      const interval = setInterval(updateMetrics, 2000); // Update every 2 seconds
      const timeInterval = setInterval(() => {
        setSessionTime(prev => prev + 1);
      }, 1000);

      return () => {
        clearInterval(interval);
        clearInterval(timeInterval);
      };
    }
  }, [isActive, sessionTime]);

  const getStatusIcon = (status: MetricData['status']) => {
    switch (status) {
      case 'excellent':
        return <CheckCircle2 className="w-4 h-4 text-green-400" />;
      case 'good':
        return <CheckCircle2 className="w-4 h-4 text-blue-400" />;
      case 'average':
        return <AlertCircle className="w-4 h-4 text-yellow-400" />;
      case 'needs_improvement':
        return <XCircle className="w-4 h-4 text-red-400" />;
    }
  };

  const getTrendIcon = (trend: MetricData['trend']) => {
    switch (trend) {
      case 'up':
        return <TrendingUp className="w-4 h-4 text-green-400" />;
      case 'down':
        return <TrendingDown className="w-4 h-4 text-red-400" />;
      case 'stable':
        return <Circle className="w-4 h-4 text-gray-400" />;
    }
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const getOverallPerformance = () => {
    if (metrics.length === 0) return 'average';
    const avgScore = metrics.reduce((sum, metric) => sum + metric.value, 0) / metrics.length;
    if (avgScore > 85) return 'excellent';
    if (avgScore > 75) return 'good';
    if (avgScore > 65) return 'average';
    return 'needs_improvement';
  };

  const renderMetricCard = (metric: MetricData) => (
    <motion.div
      key={metric.id}
      className="bg-gray-800/50 rounded-lg p-4 border border-gray-700/50 hover:border-purple-500/50 transition-all"
      whileHover={{ scale: 1.02 }}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
    >
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <div className={`p-2 bg-gray-700/50 rounded-lg ${metric.color}`}>
            {metric.icon}
          </div>
          <div>
            <p className="text-white font-medium text-sm">{metric.label}</p>
            <p className="text-gray-400 text-xs">{metric.description}</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {getStatusIcon(metric.status)}
          {getTrendIcon(metric.trend)}
        </div>
      </div>

      <div className="flex items-end justify-between">
        <div>
          <p className={`text-2xl font-bold ${metric.color}`}>
            {typeof metric.value === 'number' && metric.unit === '%' 
              ? metric.value.toFixed(1) 
              : metric.value.toFixed(2)}
            {metric.unit}
          </p>
          <p className={`text-sm flex items-center gap-1 ${
            metric.change > 0 ? 'text-green-400' : metric.change < 0 ? 'text-red-400' : 'text-gray-400'
          }`}>
            {metric.change > 0 ? '+' : ''}{metric.change.toFixed(1)}% desde el último período
          </p>
        </div>
      </div>
    </motion.div>
  );

  return (
    <div className="space-y-6">
      {/* Session Control */}
      <div className="bg-gray-900/80 rounded-xl p-6 border border-purple-500/30">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-xl font-semibold text-white flex items-center gap-3">
              <Gauge className="w-6 h-6 text-purple-400" />
              Métricas en Tiempo Real
            </h3>
            <p className="text-gray-400 text-sm">
              Monitoreo continuo de tu rendimiento académico
            </p>
          </div>

          <div className="flex items-center gap-4">
            {/* Connection Status */}
            <div className={`flex items-center gap-2 px-3 py-2 rounded-lg ${
              isConnected ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'
            }`}>
              <div className={`w-2 h-2 rounded-full ${
                isConnected ? 'bg-green-400 animate-pulse' : 'bg-red-400'
              }`} />
              <span className="text-xs font-semibold">
                {isConnected ? 'Conectado' : 'Desconectado'}
              </span>
            </div>

            {/* Session Toggle */}
            <button
              onClick={() => setIsActive(!isActive)}
              className={`px-6 py-3 rounded-lg font-semibold transition-all ${
                isActive
                  ? 'bg-red-600 hover:bg-red-700 text-white'
                  : 'bg-purple-600 hover:bg-purple-700 text-white'
              }`}
            >
              {isActive ? 'Detener Sesión' : 'Iniciar Sesión'}
            </button>
          </div>
        </div>

        {/* Session Stats */}
        {isActive && (
          <motion.div
            className="grid grid-cols-2 md:grid-cols-4 gap-4 p-4 bg-gray-800/30 rounded-lg"
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
          >
            <div className="text-center">
              <p className="text-2xl font-bold text-white">{formatTime(sessionTime)}</p>
              <p className="text-gray-400 text-sm">Tiempo de Sesión</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-white">{questionsAnswered}</p>
              <p className="text-gray-400 text-sm">Preguntas Respondidas</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-purple-400">
                {questionsAnswered > 0 ? (questionsAnswered / (sessionTime / 60)).toFixed(1) : '0.0'}
              </p>
              <p className="text-gray-400 text-sm">Ritmo (p/min)</p>
            </div>
            <div className="text-center">
              <p className={`text-2xl font-bold ${
                getOverallPerformance() === 'excellent' ? 'text-green-400' :
                getOverallPerformance() === 'good' ? 'text-blue-400' :
                getOverallPerformance() === 'average' ? 'text-yellow-400' : 'text-red-400'
              }`}>
                {getOverallPerformance() === 'excellent' ? 'Excelente' :
                 getOverallPerformance() === 'good' ? 'Bueno' :
                 getOverallPerformance() === 'average' ? 'Regular' : 'Mejorable'}
              </p>
              <p className="text-gray-400 text-sm">Rendimiento General</p>
            </div>
          </motion.div>
        )}
      </div>

      {/* Metrics Grid */}
      <AnimatePresence>
        {isActive && (
          <motion.div
            className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
          >
            {metrics.map(renderMetricCard)}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Performance Radar */}
      {isActive && (
        <motion.div
          className="bg-gray-900/80 rounded-xl p-6 border border-purple-500/30"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
        >
          <h4 className="text-lg font-semibold text-white mb-4 flex items-center gap-3">
            <BarChart3 className="w-5 h-5 text-purple-400" />
            Vista General del Rendimiento
          </h4>
          
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            {Object.entries(sessionMetrics).map(([key, value]) => (
              <div key={key} className="space-y-2">
                <div className="flex justify-between items-center">
                  <span className="text-gray-300 capitalize text-sm">
                    {key === 'accuracy' ? 'Precisión' :
                     key === 'speed' ? 'Velocidad' :
                     key === 'focus' ? 'Concentración' :
                     key === 'stamina' ? 'Resistencia' :
                     key === 'confidence' ? 'Confianza' : 'Consistencia'}
                  </span>
                  <span className="text-white font-semibold">
                    {key === 'speed' ? `${value.toFixed(1)} p/min` : `${value.toFixed(1)}%`}
                  </span>
                </div>
                <div className="w-full bg-gray-800 rounded-full h-2">
                  <motion.div
                    className={`h-2 rounded-full ${
                      value > 85 ? 'bg-green-500' :
                      value > 75 ? 'bg-blue-500' :
                      value > 65 ? 'bg-yellow-500' : 'bg-red-500'
                    }`}
                    style={{ width: `${key === 'speed' ? Math.min(100, (value / 2) * 100) : value}%` }}
                    initial={{ width: 0 }}
                    animate={{ width: `${key === 'speed' ? Math.min(100, (value / 2) * 100) : value}%` }}
                    transition={{ duration: 1 }}
                  />
                </div>
              </div>
            ))}
          </div>
        </motion.div>
      )}
    </div>
  );
}