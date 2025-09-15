'use client';

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Users,
  BarChart3,
  Server,
  AlertTriangle,
  Settings,
  Database,
  Activity,
  TrendingUp,
  TrendingDown,
  Shield,
  Globe,
  Clock,
  UserCheck,
  UserX,
  Zap,
  DollarSign,
  FileText,
  Download,
  RefreshCw,
  Eye,
  MoreVertical,
  ChevronRight,
  Search,
  Filter,
  Calendar,
  Bell,
  Cpu,
  HardDrive,
  Wifi,
  Layout
} from 'lucide-react';
import { useAuthStore } from '@/stores/useAuthStore';
import { useRealtimeUpdates } from '@/hooks/useRealtimeUpdates';
import { useCache } from '@/hooks/useCache';

interface SystemMetrics {
  totalUsers: number;
  activeUsers: number;
  totalSessions: number;
  avgSessionTime: number;
  serverLoad: number;
  memoryUsage: number;
  diskUsage: number;
  databaseConnections: number;
  responseTime: number;
  errorRate: number;
  uptime: number;
}

interface UserAnalytics {
  newUsersToday: number;
  activeUsersToday: number;
  totalRevenue: number;
  conversionRate: number;
  churnRate: number;
  avgEngagement: number;
}

interface TopPerformers {
  students: Array<{
    id: string;
    name: string;
    score: number;
    level: number;
    institution: string;
  }>;
  teachers: Array<{
    id: string;
    name: string;
    institution: string;
    studentsCount: number;
    avgImprovement: number;
  }>;
  institutions: Array<{
    id: string;
    name: string;
    usersCount: number;
    avgScore: number;
    growthRate: number;
  }>;
}

interface SystemAlert {
  id: string;
  type: 'warning' | 'error' | 'info';
  title: string;
  message: string;
  timestamp: Date;
  severity: 'low' | 'medium' | 'high' | 'critical';
  resolved: boolean;
}

type DashboardView = 'overview' | 'users' | 'system' | 'analytics' | 'content' | 'settings';

export default function AdminDashboard() {
  const { user } = useAuthStore();
  const [currentView, setCurrentView] = useState<DashboardView>('overview');
  const [timeRange, setTimeRange] = useState<'24h' | '7d' | '30d' | '90d'>('24h');
  const [loading, setLoading] = useState(true);
  const [systemAlerts, setSystemAlerts] = useState<SystemAlert[]>([]);
  const [showAlertDetails, setShowAlertDetails] = useState<string | null>(null);

  // Real-time system metrics using cache
  const { 
    data: metrics, 
    isLoading: metricsLoading, 
    refetch: refetchMetrics,
    isStale: metricsStale 
  } = useCache<SystemMetrics>(
    `admin-metrics-${timeRange}`,
    () => fetchSystemMetrics(timeRange),
    { 
      ttl: 30 * 1000, // 30 seconds
      staleTime: 10 * 1000, // 10 seconds
      refreshOnFocus: true 
    }
  );

  const { 
    data: userAnalytics, 
    isLoading: analyticsLoading 
  } = useCache<UserAnalytics>(
    `admin-analytics-${timeRange}`,
    () => fetchUserAnalytics(timeRange),
    { 
      ttl: 2 * 60 * 1000, // 2 minutes
      staleTime: 30 * 1000 
    }
  );

  const { 
    data: topPerformers 
  } = useCache<TopPerformers>(
    `admin-performers-${timeRange}`,
    () => fetchTopPerformers(timeRange),
    { 
      ttl: 5 * 60 * 1000, // 5 minutes
      staleTime: 60 * 1000 
    }
  );

  // Real-time updates
  const { isConnected, notifications } = useRealtimeUpdates();

  // Mock data fetch functions
  async function fetchSystemMetrics(range: string): Promise<SystemMetrics> {
    await new Promise(resolve => setTimeout(resolve, 1000));
    return {
      totalUsers: 15420,
      activeUsers: 1247,
      totalSessions: 3892,
      avgSessionTime: 45.6,
      serverLoad: 67.3,
      memoryUsage: 78.9,
      diskUsage: 45.2,
      databaseConnections: 156,
      responseTime: 245,
      errorRate: 0.12,
      uptime: 99.8
    };
  }

  async function fetchUserAnalytics(range: string): Promise<UserAnalytics> {
    await new Promise(resolve => setTimeout(resolve, 800));
    return {
      newUsersToday: 234,
      activeUsersToday: 1247,
      totalRevenue: 45780,
      conversionRate: 12.4,
      churnRate: 2.1,
      avgEngagement: 78.5
    };
  }

  async function fetchTopPerformers(range: string): Promise<TopPerformers> {
    await new Promise(resolve => setTimeout(resolve, 600));
    return {
      students: [
        { id: '1', name: 'Ana García', score: 97, level: 25, institution: 'Colegio San Martín' },
        { id: '2', name: 'Carlos López', score: 95, level: 23, institution: 'Instituto Nacional' },
        { id: '3', name: 'María Rodríguez', score: 94, level: 22, institution: 'Colegio La Salle' }
      ],
      teachers: [
        { id: '1', name: 'Prof. Elena Vásquez', institution: 'Colegio San Martín', studentsCount: 120, avgImprovement: 15.2 },
        { id: '2', name: 'Prof. Roberto Mendez', institution: 'Instituto Nacional', studentsCount: 95, avgImprovement: 13.8 },
        { id: '3', name: 'Prof. Isabel Torres', institution: 'Colegio La Salle', studentsCount: 87, avgImprovement: 12.9 }
      ],
      institutions: [
        { id: '1', name: 'Colegio San Martín', usersCount: 450, avgScore: 85.2, growthRate: 23.5 },
        { id: '2', name: 'Instituto Nacional', usersCount: 380, avgScore: 82.7, growthRate: 18.9 },
        { id: '3', name: 'Colegio La Salle', usersCount: 320, avgScore: 81.3, growthRate: 16.4 }
      ]
    };
  }

  useEffect(() => {
    // Mock system alerts
    setSystemAlerts([
      {
        id: '1',
        type: 'warning',
        title: 'Alta carga del servidor',
        message: 'El servidor está experimentando una carga del 85%. Considere escalar recursos.',
        timestamp: new Date(),
        severity: 'medium',
        resolved: false
      },
      {
        id: '2',
        type: 'info',
        title: 'Mantenimiento programado',
        message: 'Mantenimiento de base de datos programado para las 2:00 AM.',
        timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000),
        severity: 'low',
        resolved: false
      },
      {
        id: '3',
        type: 'error',
        title: 'Fallos en autenticación',
        message: 'Se detectaron múltiples fallos de autenticación desde la IP 192.168.1.100.',
        timestamp: new Date(Date.now() - 4 * 60 * 60 * 1000),
        severity: 'high',
        resolved: true
      }
    ]);
    setLoading(false);
  }, []);

  const getMetricColor = (value: number, thresholds: { warning: number; critical: number }) => {
    if (value >= thresholds.critical) return 'text-red-400';
    if (value >= thresholds.warning) return 'text-yellow-400';
    return 'text-green-400';
  };

  const getAlertIcon = (type: SystemAlert['type']) => {
    switch (type) {
      case 'error': return <AlertTriangle className="w-5 h-5 text-red-400" />;
      case 'warning': return <AlertTriangle className="w-5 h-5 text-yellow-400" />;
      case 'info': return <Bell className="w-5 h-5 text-blue-400" />;
    }
  };

  const navigationItems = [
    { id: 'overview', label: 'Resumen General', icon: Layout },
    { id: 'users', label: 'Gestión de Usuarios', icon: Users },
    { id: 'system', label: 'Sistema', icon: Server },
    { id: 'analytics', label: 'Analytics Avanzado', icon: BarChart3 },
    { id: 'content', label: 'Gestión de Contenido', icon: FileText },
    { id: 'settings', label: 'Configuración', icon: Settings }
  ];

  const renderSystemMetric = (
    label: string,
    value: number,
    unit: string,
    icon: React.ReactNode,
    thresholds: { warning: number; critical: number },
    trend?: number
  ) => (
    <motion.div
      className="bg-gray-900/80 rounded-xl p-6 border border-gray-700/50"
      whileHover={{ scale: 1.02 }}
      transition={{ duration: 0.2 }}
    >
      <div className="flex items-center justify-between mb-4">
        <div className="p-3 bg-blue-500/20 rounded-lg">
          {icon}
        </div>
        {trend !== undefined && (
          <div className={`flex items-center gap-1 text-sm ${
            trend > 0 ? 'text-green-400' : 'text-red-400'
          }`}>
            {trend > 0 ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
            <span>{Math.abs(trend)}%</span>
          </div>
        )}
      </div>
      <p className="text-gray-400 text-sm mb-2">{label}</p>
      <p className={`text-2xl font-bold ${getMetricColor(value, thresholds)}`}>
        {value}{unit}
      </p>
    </motion.div>
  );

  const renderQuickStat = (
    label: string,
    value: string | number,
    icon: React.ReactNode,
    color: string,
    change?: { value: number; positive: boolean }
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
          {change && (
            <div className={`flex items-center gap-1 text-sm ${
              change.positive ? 'text-green-200' : 'text-red-200'
            }`}>
              {change.positive ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
              <span>{change.value}%</span>
            </div>
          )}
        </div>
        <p className="text-sm opacity-90 mb-1">{label}</p>
        <p className="text-2xl font-bold">{value}</p>
      </div>
    </motion.div>
  );

  const renderOverview = () => (
    <div className="space-y-6">
      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {metrics && userAnalytics && (
          <>
            {renderQuickStat(
              'Usuarios Totales',
              metrics.totalUsers.toLocaleString(),
              <Users className="w-8 h-8" />,
              'from-blue-600 to-blue-700',
              { value: 12.5, positive: true }
            )}
            
            {renderQuickStat(
              'Usuarios Activos',
              metrics.activeUsers.toLocaleString(),
              <UserCheck className="w-8 h-8" />,
              'from-green-600 to-green-700',
              { value: 8.3, positive: true }
            )}
            
            {renderQuickStat(
              'Ingresos Totales',
              `$${userAnalytics.totalRevenue.toLocaleString()}`,
              <DollarSign className="w-8 h-8" />,
              'from-yellow-600 to-yellow-700',
              { value: 15.7, positive: true }
            )}
            
            {renderQuickStat(
              'Tiempo de Respuesta',
              `${metrics.responseTime}ms`,
              <Zap className="w-8 h-8" />,
              'from-purple-600 to-purple-700',
              { value: 2.1, positive: false }
            )}
          </>
        )}
      </div>

      {/* System Health */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <div className="bg-gray-900/80 rounded-xl p-6 border border-gray-700/50">
            <h3 className="text-xl font-semibold text-white mb-6 flex items-center gap-3">
              <Server className="w-6 h-6 text-blue-400" />
              Estado del Sistema
            </h3>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {metrics && (
                <>
                  {renderSystemMetric(
                    'Carga del Servidor',
                    metrics.serverLoad,
                    '%',
                    <Cpu className="w-6 h-6 text-blue-400" />,
                    { warning: 70, critical: 85 },
                    -2.3
                  )}
                  
                  {renderSystemMetric(
                    'Uso de Memoria',
                    metrics.memoryUsage,
                    '%',
                    <HardDrive className="w-6 h-6 text-blue-400" />,
                    { warning: 80, critical: 90 },
                    5.1
                  )}
                  
                  {renderSystemMetric(
                    'Conexiones DB',
                    metrics.databaseConnections,
                    '',
                    <Database className="w-6 h-6 text-blue-400" />,
                    { warning: 200, critical: 300 },
                    1.8
                  )}
                </>
              )}
            </div>
          </div>
        </div>

        {/* System Alerts */}
        <div className="bg-gray-900/80 rounded-xl p-6 border border-gray-700/50">
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-3">
            <AlertTriangle className="w-5 h-5 text-yellow-400" />
            Alertas del Sistema
          </h3>
          
          <div className="space-y-3 max-h-80 overflow-y-auto">
            {systemAlerts.map((alert) => (
              <motion.div
                key={alert.id}
                className={`p-3 rounded-lg border cursor-pointer transition-all ${
                  alert.resolved 
                    ? 'bg-gray-800/50 border-gray-600/50 opacity-60' 
                    : alert.severity === 'critical' 
                      ? 'bg-red-500/20 border-red-500/50' 
                      : alert.severity === 'high'
                        ? 'bg-orange-500/20 border-orange-500/50'
                        : alert.severity === 'medium'
                          ? 'bg-yellow-500/20 border-yellow-500/50'
                          : 'bg-blue-500/20 border-blue-500/50'
                }`}
                whileHover={{ scale: 1.02 }}
                onClick={() => setShowAlertDetails(alert.id)}
              >
                <div className="flex items-start gap-3">
                  {getAlertIcon(alert.type)}
                  <div className="flex-1 min-w-0">
                    <p className="text-white text-sm font-medium">{alert.title}</p>
                    <p className="text-gray-400 text-xs truncate">{alert.message}</p>
                    <p className="text-gray-500 text-xs mt-1">
                      {alert.timestamp.toLocaleTimeString()}
                    </p>
                  </div>
                  {alert.resolved && (
                    <div className="w-2 h-2 bg-green-400 rounded-full"></div>
                  )}
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </div>

      {/* Top Performers */}
      {topPerformers && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="bg-gray-900/80 rounded-xl p-6 border border-gray-700/50">
            <h3 className="text-lg font-semibold text-white mb-4">Top Estudiantes</h3>
            <div className="space-y-3">
              {topPerformers.students.map((student, index) => (
                <div key={student.id} className="flex items-center gap-3 p-3 bg-gray-800/50 rounded-lg">
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold ${
                    index === 0 ? 'bg-yellow-500 text-white' :
                    index === 1 ? 'bg-gray-400 text-white' :
                    'bg-orange-500 text-white'
                  }`}>
                    {index + 1}
                  </div>
                  <div className="flex-1">
                    <p className="text-white font-medium text-sm">{student.name}</p>
                    <p className="text-gray-400 text-xs">{student.institution}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-green-400 font-bold text-sm">{student.score}%</p>
                    <p className="text-gray-400 text-xs">Nivel {student.level}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="bg-gray-900/80 rounded-xl p-6 border border-gray-700/50">
            <h3 className="text-lg font-semibold text-white mb-4">Top Profesores</h3>
            <div className="space-y-3">
              {topPerformers.teachers.map((teacher, index) => (
                <div key={teacher.id} className="flex items-center gap-3 p-3 bg-gray-800/50 rounded-lg">
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold ${
                    index === 0 ? 'bg-blue-500 text-white' :
                    index === 1 ? 'bg-purple-500 text-white' :
                    'bg-indigo-500 text-white'
                  }`}>
                    {index + 1}
                  </div>
                  <div className="flex-1">
                    <p className="text-white font-medium text-sm">{teacher.name}</p>
                    <p className="text-gray-400 text-xs">{teacher.institution}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-blue-400 font-bold text-sm">+{teacher.avgImprovement}%</p>
                    <p className="text-gray-400 text-xs">{teacher.studentsCount} estudiantes</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="bg-gray-900/80 rounded-xl p-6 border border-gray-700/50">
            <h3 className="text-lg font-semibold text-white mb-4">Top Instituciones</h3>
            <div className="space-y-3">
              {topPerformers.institutions.map((institution, index) => (
                <div key={institution.id} className="flex items-center gap-3 p-3 bg-gray-800/50 rounded-lg">
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold ${
                    index === 0 ? 'bg-green-500 text-white' :
                    index === 1 ? 'bg-teal-500 text-white' :
                    'bg-cyan-500 text-white'
                  }`}>
                    {index + 1}
                  </div>
                  <div className="flex-1">
                    <p className="text-white font-medium text-sm">{institution.name}</p>
                    <p className="text-gray-400 text-xs">{institution.usersCount} usuarios</p>
                  </div>
                  <div className="text-right">
                    <p className="text-green-400 font-bold text-sm">{institution.avgScore}%</p>
                    <p className="text-gray-400 text-xs">+{institution.growthRate}%</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );

  if (loading || !user?.isAdmin) {
    return (
      <div className="min-h-screen bg-gray-950 flex items-center justify-center">
        <div className="text-center">
          <motion.div
            className="w-16 h-16 border-4 border-purple-500/30 rounded-full mx-auto mb-4"
            animate={{ rotate: 360 }}
            transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
          >
            <div className="w-full h-full border-4 border-transparent border-t-purple-500 rounded-full"></div>
          </motion.div>
          <p className="text-white">
            {!user?.isAdmin ? 'Acceso denegado. Se requieren permisos de administrador.' : 'Cargando dashboard...'}
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      {/* Header */}
      <header className="bg-gray-900/95 border-b border-gray-700/50 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2 text-gray-400">
              <span>Admin</span>
              <ChevronRight className="w-4 h-4" />
              <span className="text-white">Dashboard</span>
            </div>
          </div>

          <div className="flex items-center gap-4">
            {/* Time Range Selector */}
            <div className="flex items-center gap-2 bg-gray-800 rounded-lg p-1">
              {[
                { key: '24h', label: '24h' },
                { key: '7d', label: '7d' },
                { key: '30d', label: '30d' },
                { key: '90d', label: '90d' }
              ].map(range => (
                <button
                  key={range.key}
                  onClick={() => setTimeRange(range.key as any)}
                  className={`px-3 py-1 rounded text-sm font-medium transition-all ${
                    timeRange === range.key
                      ? 'bg-purple-600 text-white'
                      : 'text-gray-400 hover:text-white'
                  }`}
                >
                  {range.label}
                </button>
              ))}
            </div>

            {/* Refresh Button */}
            <button
              onClick={() => refetchMetrics()}
              className={`p-2 bg-gray-800 hover:bg-gray-700 rounded-lg transition-all ${
                metricsStale ? 'animate-pulse' : ''
              }`}
              title="Actualizar métricas"
            >
              <RefreshCw className={`w-5 h-5 ${metricsStale ? 'text-orange-400' : 'text-gray-400'}`} />
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
      </header>

      <div className="flex">
        {/* Sidebar */}
        <aside className="w-64 bg-gray-900/95 border-r border-gray-700/50 min-h-screen">
          <div className="p-6">
            <div className="flex items-center gap-3 mb-8">
              <div className="w-10 h-10 bg-gradient-to-r from-purple-500 to-blue-500 rounded-lg flex items-center justify-center">
                <Shield className="w-6 h-6 text-white" />
              </div>
              <div>
                <h2 className="text-white font-bold">Admin Panel</h2>
                <p className="text-gray-400 text-sm">{user.name}</p>
              </div>
            </div>

            <nav className="space-y-2">
              {navigationItems.map((item) => (
                <button
                  key={item.id}
                  onClick={() => setCurrentView(item.id as DashboardView)}
                  className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-all ${
                    currentView === item.id
                      ? 'bg-purple-600 text-white'
                      : 'text-gray-400 hover:text-white hover:bg-gray-800'
                  }`}
                >
                  <item.icon className="w-5 h-5" />
                  <span>{item.label}</span>
                </button>
              ))}
            </nav>
          </div>
        </aside>

        {/* Main Content */}
        <main className="flex-1 overflow-y-auto">
          <div className="p-6">
            <div className="mb-6">
              <h1 className="text-3xl font-bold text-white mb-2">
                {currentView === 'overview' && 'Resumen General'}
                {currentView === 'users' && 'Gestión de Usuarios'}
                {currentView === 'system' && 'Sistema'}
                {currentView === 'analytics' && 'Analytics Avanzado'}
                {currentView === 'content' && 'Gestión de Contenido'}
                {currentView === 'settings' && 'Configuración'}
              </h1>
              <p className="text-gray-400">
                Panel de administración del sistema IcfesLeveling
              </p>
            </div>

            <AnimatePresence mode="wait">
              <motion.div
                key={currentView}
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                transition={{ duration: 0.3 }}
              >
                {currentView === 'overview' && renderOverview()}
                {currentView !== 'overview' && (
                  <div className="bg-gray-900/80 rounded-xl p-8 border border-gray-700/50 text-center">
                    <div className="w-16 h-16 bg-gray-800 rounded-full flex items-center justify-center mx-auto mb-4">
                      <Settings className="w-8 h-8 text-gray-400" />
                    </div>
                    <h3 className="text-xl font-semibold text-white mb-2">Próximamente</h3>
                    <p className="text-gray-400">
                      Esta sección estará disponible en futuras actualizaciones.
                    </p>
                  </div>
                )}
              </motion.div>
            </AnimatePresence>
          </div>
        </main>
      </div>

      {/* Alert Details Modal */}
      <AnimatePresence>
        {showAlertDetails && (
          <motion.div
            className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setShowAlertDetails(null)}
          >
            <motion.div
              className="bg-gray-900 rounded-xl p-6 max-w-md w-full border border-gray-700"
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              onClick={(e) => e.stopPropagation()}
            >
              {(() => {
                const alert = systemAlerts.find(a => a.id === showAlertDetails);
                if (!alert) return null;
                
                return (
                  <>
                    <div className="flex items-center gap-3 mb-4">
                      {getAlertIcon(alert.type)}
                      <h3 className="text-white font-semibold">{alert.title}</h3>
                    </div>
                    <p className="text-gray-300 mb-4">{alert.message}</p>
                    <div className="flex items-center justify-between text-sm text-gray-400 mb-4">
                      <span>Severidad: {alert.severity}</span>
                      <span>{alert.timestamp.toLocaleString()}</span>
                    </div>
                    <div className="flex items-center justify-end gap-3">
                      <button
                        onClick={() => setShowAlertDetails(null)}
                        className="px-4 py-2 text-gray-400 hover:text-white transition-colors"
                      >
                        Cerrar
                      </button>
                      {!alert.resolved && (
                        <button className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition-colors">
                          Marcar como resuelto
                        </button>
                      )}
                    </div>
                  </>
                );
              })()}
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}