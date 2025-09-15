'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Activity,
  Users,
  Zap,
  TrendingUp,
  TrendingDown,
  Clock,
  Target,
  Award,
  AlertCircle,
  Wifi,
  WifiOff,
  Play,
  Pause,
  RotateCcw,
  Bell,
  Settings,
  Eye,
  BarChart3
} from 'lucide-react';

interface RealTimeMetrics {
  active_users: number;
  current_battles: number;
  questions_answered_per_minute: number;
  average_accuracy: number;
  server_response_time: number;
  total_experience_gained: number;
  peak_concurrent_users: number;
  system_load: number;
}

interface LiveEvent {
  id: string;
  timestamp: string;
  user_id: string;
  event_type: 'battle_start' | 'battle_complete' | 'question_answered' | 'level_up' | 'achievement_earned';
  data: {
    user_name?: string;
    accuracy?: number;
    experience_gained?: number;
    level?: number;
    achievement?: string;
    subject?: string;
  };
}

interface AlertConfig {
  type: 'info' | 'warning' | 'error' | 'success';
  title: string;
  message: string;
  timestamp: string;
}

export default function RealTimeAnalytics() {
  const [metrics, setMetrics] = useState<RealTimeMetrics>({
    active_users: 0,
    current_battles: 0,
    questions_answered_per_minute: 0,
    average_accuracy: 0,
    server_response_time: 0,
    total_experience_gained: 0,
    peak_concurrent_users: 0,
    system_load: 0
  });

  const [liveEvents, setLiveEvents] = useState<LiveEvent[]>([]);
  const [alerts, setAlerts] = useState<AlertConfig[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [refreshInterval, setRefreshInterval] = useState(5000); // 5 seconds

  // Simulate real-time data updates
  const generateMockMetrics = useCallback((): RealTimeMetrics => {
    const now = new Date();
    const hour = now.getHours();
    
    // Simulate realistic patterns based on time of day
    const baseActiveUsers = hour >= 14 && hour <= 22 ? 120 : hour >= 6 && hour <= 14 ? 80 : 20;
    const variation = Math.random() * 20 - 10; // ±10 variation
    
    return {
      active_users: Math.max(0, Math.floor(baseActiveUsers + variation)),
      current_battles: Math.floor(Math.random() * 50 + 10),
      questions_answered_per_minute: Math.floor(Math.random() * 200 + 50),
      average_accuracy: 0.65 + Math.random() * 0.25, // 65-90%
      server_response_time: Math.floor(Math.random() * 100 + 50), // 50-150ms
      total_experience_gained: Math.floor(Math.random() * 5000 + 10000),
      peak_concurrent_users: Math.max(baseActiveUsers + 20, Math.floor(Math.random() * 150 + 100)),
      system_load: Math.random() * 0.8 + 0.1 // 10-90% load
    };
  }, []);

  const generateMockEvent = useCallback((): LiveEvent => {
    const eventTypes: LiveEvent['event_type'][] = [
      'battle_start', 'battle_complete', 'question_answered', 'level_up', 'achievement_earned'
    ];
    
    const subjects = ['Matemáticas', 'Lenguaje', 'Ciencias', 'Sociales', 'Inglés'];
    const achievements = ['Primera Victoria', 'Racha de 5', 'Maestro del Tiempo', 'Explorador'];
    const names = ['Ana García', 'Carlos López', 'María Rodríguez', 'Juan Pérez', 'Sofia Martínez'];
    
    const eventType = eventTypes[Math.floor(Math.random() * eventTypes.length)];
    const userName = names[Math.floor(Math.random() * names.length)];
    
    let eventData: LiveEvent['data'] = { user_name: userName };
    
    switch (eventType) {
      case 'battle_complete':
        eventData = {
          ...eventData,
          accuracy: Math.random(),
          experience_gained: Math.floor(Math.random() * 100 + 50),
          subject: subjects[Math.floor(Math.random() * subjects.length)]
        };
        break;
      case 'level_up':
        eventData = {
          ...eventData,
          level: Math.floor(Math.random() * 10 + 1)
        };
        break;
      case 'achievement_earned':
        eventData = {
          ...eventData,
          achievement: achievements[Math.floor(Math.random() * achievements.length)]
        };
        break;
    }
    
    return {
      id: `event_${Date.now()}_${Math.random()}`,
      timestamp: new Date().toISOString(),
      user_id: `user_${Math.floor(Math.random() * 1000)}`,
      event_type: eventType,
      data: eventData
    };
  }, []);

  // Real-time data fetching
  useEffect(() => {
    if (!autoRefresh || isPaused) return;

    const interval = setInterval(() => {
      try {
        // Simulate API call
        const newMetrics = generateMockMetrics();
        setMetrics(newMetrics);
        setIsConnected(true);

        // Generate random events
        if (Math.random() < 0.7) { // 70% chance of new event
          const newEvent = generateMockEvent();
          setLiveEvents(prev => [newEvent, ...prev.slice(0, 19)]); // Keep last 20 events
        }

        // Generate alerts based on metrics
        if (newMetrics.system_load > 0.8) {
          addAlert({
            type: 'warning',
            title: 'Alta Carga del Sistema',
            message: `Carga del servidor: ${(newMetrics.system_load * 100).toFixed(1)}%`,
            timestamp: new Date().toISOString()
          });
        }

        if (newMetrics.server_response_time > 120) {
          addAlert({
            type: 'error',
            title: 'Tiempo de Respuesta Alto',
            message: `Latencia: ${newMetrics.server_response_time}ms`,
            timestamp: new Date().toISOString()
          });
        }

      } catch (error) {
        setIsConnected(false);
        console.error('Error fetching real-time data:', error);
      }
    }, refreshInterval);

    return () => clearInterval(interval);
  }, [autoRefresh, isPaused, refreshInterval, generateMockMetrics, generateMockEvent]);

  const addAlert = useCallback((alert: AlertConfig) => {
    setAlerts(prev => {
      // Avoid duplicate alerts
      const exists = prev.some(a => a.title === alert.title && a.message === alert.message);
      if (exists) return prev;
      
      return [alert, ...prev.slice(0, 4)]; // Keep last 5 alerts
    });
  }, []);

  const getEventIcon = (eventType: LiveEvent['event_type']) => {
    switch (eventType) {
      case 'battle_start': return <Play className="w-4 h-4 text-blue-400" />;
      case 'battle_complete': return <Target className="w-4 h-4 text-green-400" />;
      case 'question_answered': return <BarChart3 className="w-4 h-4 text-purple-400" />;
      case 'level_up': return <TrendingUp className="w-4 h-4 text-yellow-400" />;
      case 'achievement_earned': return <Award className="w-4 h-4 text-orange-400" />;
      default: return <Activity className="w-4 h-4 text-gray-400" />;
    }
  };

  const getEventDescription = (event: LiveEvent) => {
    switch (event.event_type) {
      case 'battle_start':
        return `${event.data.user_name} inició una nueva batalla`;
      case 'battle_complete':
        return `${event.data.user_name} completó una batalla en ${event.data.subject} con ${(event.data.accuracy! * 100).toFixed(1)}% de precisión`;
      case 'question_answered':
        return `${event.data.user_name} respondió una pregunta`;
      case 'level_up':
        return `¡${event.data.user_name} subió al nivel ${event.data.level}!`;
      case 'achievement_earned':
        return `¡${event.data.user_name} obtuvo el logro "${event.data.achievement}"!`;
      default:
        return 'Evento desconocido';
    }
  };

  const getAlertIcon = (type: AlertConfig['type']) => {
    switch (type) {
      case 'info': return <Eye className="w-4 h-4 text-blue-400" />;
      case 'warning': return <AlertCircle className="w-4 h-4 text-yellow-400" />;
      case 'error': return <AlertCircle className="w-4 h-4 text-red-400" />;
      case 'success': return <Target className="w-4 h-4 text-green-400" />;
    }
  };

  const renderMetricCard = (
    title: string,
    value: string | number,
    icon: React.ReactNode,
    trend?: { value: number; isPositive: boolean },
    color: string = 'purple'
  ) => (
    <motion.div
      className="bg-gray-900/80 rounded-lg p-4"
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.3 }}
    >
      <div className="flex items-center justify-between mb-2">
        <div className={`p-2 bg-${color}-500/20 rounded-lg`}>
          {icon}
        </div>
        {trend && (
          <div className={`flex items-center gap-1 text-sm ${
            trend.isPositive ? 'text-green-400' : 'text-red-400'
          }`}>
            {trend.isPositive ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
            <span>{Math.abs(trend.value)}%</span>
          </div>
        )}
      </div>
      
      <p className="text-gray-400 text-sm mb-1">{title}</p>
      <p className="text-white text-xl font-bold">
        {typeof value === 'number' && value % 1 !== 0 ? value.toFixed(2) : value}
      </p>
    </motion.div>
  );

  return (
    <div className="space-y-6">
      {/* Header with Controls */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div className="flex items-center gap-4">
          <h2 className="text-2xl font-bold text-white flex items-center gap-2">
            <Activity className="w-8 h-8 text-purple-400" />
            Analytics en Tiempo Real
          </h2>
          
          <div className={`flex items-center gap-2 px-3 py-1 rounded-lg text-sm ${
            isConnected ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'
          }`}>
            {isConnected ? <Wifi className="w-4 h-4" /> : <WifiOff className="w-4 h-4" />}
            <span>{isConnected ? 'Conectado' : 'Desconectado'}</span>
          </div>
        </div>
        
        <div className="flex items-center gap-2">
          <button
            onClick={() => setIsPaused(!isPaused)}
            className={`p-2 rounded-lg transition-colors ${
              isPaused ? 'bg-green-600 hover:bg-green-700' : 'bg-gray-600 hover:bg-gray-700'
            }`}
          >
            {isPaused ? <Play className="w-4 h-4 text-white" /> : <Pause className="w-4 h-4 text-white" />}
          </button>
          
          <button
            onClick={() => setLiveEvents([])}
            className="p-2 bg-gray-600 hover:bg-gray-700 rounded-lg transition-colors"
          >
            <RotateCcw className="w-4 h-4 text-white" />
          </button>
          
          <select
            value={refreshInterval}
            onChange={(e) => setRefreshInterval(Number(e.target.value))}
            className="bg-gray-800 text-white rounded-lg px-3 py-2 text-sm border border-gray-700"
          >
            <option value={1000}>1s</option>
            <option value={5000}>5s</option>
            <option value={10000}>10s</option>
            <option value={30000}>30s</option>
          </select>
        </div>
      </div>

      {/* Alerts */}
      <AnimatePresence>
        {alerts.length > 0 && (
          <motion.div
            className="space-y-2"
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
          >
            {alerts.map((alert, index) => (
              <motion.div
                key={`${alert.timestamp}-${index}`}
                className={`flex items-center gap-3 p-3 rounded-lg border ${
                  alert.type === 'error' ? 'bg-red-500/10 border-red-500/30' :
                  alert.type === 'warning' ? 'bg-yellow-500/10 border-yellow-500/30' :
                  alert.type === 'success' ? 'bg-green-500/10 border-green-500/30' :
                  'bg-blue-500/10 border-blue-500/30'
                }`}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 20 }}
              >
                {getAlertIcon(alert.type)}
                <div className="flex-1">
                  <p className="font-semibold text-white">{alert.title}</p>
                  <p className="text-sm text-gray-300">{alert.message}</p>
                </div>
                <button
                  onClick={() => setAlerts(prev => prev.filter((_, i) => i !== index))}
                  className="text-gray-400 hover:text-white"
                >
                  ×
                </button>
              </motion.div>
            ))}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Real-time Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {renderMetricCard(
          'Usuarios Activos',
          metrics.active_users,
          <Users className="w-5 h-5 text-purple-400" />,
          { value: 12, isPositive: true },
          'purple'
        )}

        {renderMetricCard(
          'Batallas en Curso',
          metrics.current_battles,
          <Zap className="w-5 h-5 text-blue-400" />,
          undefined,
          'blue'
        )}

        {renderMetricCard(
          'Preguntas/min',
          metrics.questions_answered_per_minute,
          <BarChart3 className="w-5 h-5 text-green-400" />,
          { value: 8, isPositive: true },
          'green'
        )}

        {renderMetricCard(
          'Precisión Promedio',
          `${(metrics.average_accuracy * 100).toFixed(1)}%`,
          <Target className="w-5 h-5 text-yellow-400" />,
          { value: 3, isPositive: true },
          'yellow'
        )}

        {renderMetricCard(
          'Latencia del Servidor',
          `${metrics.server_response_time}ms`,
          <Clock className="w-5 h-5 text-orange-400" />,
          { value: 5, isPositive: false },
          'orange'
        )}

        {renderMetricCard(
          'Experiencia Total',
          metrics.total_experience_gained.toLocaleString(),
          <Award className="w-5 h-5 text-pink-400" />,
          undefined,
          'pink'
        )}

        {renderMetricCard(
          'Pico de Usuarios',
          metrics.peak_concurrent_users,
          <TrendingUp className="w-5 h-5 text-indigo-400" />,
          undefined,
          'indigo'
        )}

        {renderMetricCard(
          'Carga del Sistema',
          `${(metrics.system_load * 100).toFixed(1)}%`,
          <Activity className="w-5 h-5 text-red-400" />,
          { value: 2, isPositive: false },
          'red'
        )}
      </div>

      {/* Live Events Feed */}
      <motion.div
        className="bg-gray-900/80 rounded-lg p-6"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
      >
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-xl font-semibold text-white flex items-center gap-2">
            <Activity className="w-6 h-6 text-purple-400" />
            Eventos en Vivo
          </h3>
          
          <div className="flex items-center gap-2 text-sm text-gray-400">
            <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
            <span>En vivo</span>
          </div>
        </div>

        <div className="space-y-3 max-h-96 overflow-y-auto">
          <AnimatePresence>
            {liveEvents.map((event, index) => (
              <motion.div
                key={event.id}
                className="flex items-start gap-3 p-3 bg-gray-800/50 rounded-lg"
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: 10 }}
                transition={{ duration: 0.3 }}
              >
                <div className="flex-shrink-0 mt-1">
                  {getEventIcon(event.event_type)}
                </div>
                
                <div className="flex-1 min-w-0">
                  <p className="text-white text-sm">
                    {getEventDescription(event)}
                  </p>
                  <p className="text-gray-400 text-xs mt-1">
                    {new Date(event.timestamp).toLocaleTimeString()}
                  </p>
                </div>
                
                {event.data.experience_gained && (
                  <div className="flex-shrink-0 bg-purple-500/20 text-purple-400 px-2 py-1 rounded text-xs">
                    +{event.data.experience_gained} EXP
                  </div>
                )}
              </motion.div>
            ))}
          </AnimatePresence>
          
          {liveEvents.length === 0 && (
            <div className="text-center text-gray-500 py-8">
              <Activity className="w-12 h-12 mx-auto mb-2 text-gray-600" />
              <p>Esperando eventos en tiempo real...</p>
            </div>
          )}
        </div>
      </motion.div>

      {/* System Status */}
      <motion.div
        className="bg-gray-900/80 rounded-lg p-6"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
      >
        <h3 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
          <Settings className="w-6 h-6 text-gray-400" />
          Estado del Sistema
        </h3>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-gray-800/50 rounded-lg p-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-gray-400">Base de Datos</span>
              <div className="w-2 h-2 bg-green-400 rounded-full" />
            </div>
            <p className="text-white font-semibold">Operacional</p>
            <p className="text-xs text-gray-400">Último backup: hace 2h</p>
          </div>
          
          <div className="bg-gray-800/50 rounded-lg p-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-gray-400">API Gateway</span>
              <div className="w-2 h-2 bg-green-400 rounded-full" />
            </div>
            <p className="text-white font-semibold">Operacional</p>
            <p className="text-xs text-gray-400">99.9% uptime</p>
          </div>
          
          <div className="bg-gray-800/50 rounded-lg p-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-gray-400">WebSocket</span>
              <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-400' : 'bg-red-400'}`} />
            </div>
            <p className="text-white font-semibold">
              {isConnected ? 'Conectado' : 'Desconectado'}
            </p>
            <p className="text-xs text-gray-400">
              {liveEvents.length} eventos recibidos
            </p>
          </div>
        </div>
      </motion.div>
    </div>
  );
}