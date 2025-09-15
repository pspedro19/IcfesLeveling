'use client';

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  BarChart2,
  TrendingUp,
  Users,
  Activity,
  Brain,
  Target,
  Clock,
  Award,
  Download,
  Settings,
  RefreshCw,
  Eye,
  Filter,
  Calendar,
  Lightbulb,
  Shield,
  Globe,
  Zap
} from 'lucide-react';

// Import all our analytics components
import AnalyticsDashboard from './AnalyticsDashboard';
import StudentProgressAnalytics from './StudentProgressAnalytics';
import TeacherDashboard from './TeacherDashboard';
import InteractiveCharts from './InteractiveCharts';
import RealTimeAnalytics from './RealTimeAnalytics';
import EducationalInsightsEngine from './EducationalInsightsEngine';
import { useAuthStore } from '@/stores/useAuthStore';

type DashboardView = 'overview' | 'student-progress' | 'teacher-view' | 'charts' | 'realtime' | 'insights' | 'system-metrics';

interface DashboardConfig {
  view: DashboardView;
  label: string;
  icon: React.ReactNode;
  description: string;
  requiredRole?: 'student' | 'teacher' | 'admin';
}

export default function ComprehensiveAnalyticsDashboard() {
  const { user } = useAuthStore();
  const [activeView, setActiveView] = useState<DashboardView>('overview');
  const [showExportModal, setShowExportModal] = useState(false);
  const [dashboardConfig, setDashboardConfig] = useState<DashboardConfig[]>([]);

  useEffect(() => {
    // Configure available dashboard views based on user role
    const configs: DashboardConfig[] = [
      {
        view: 'overview',
        label: 'Resumen General',
        icon: <BarChart2 className="w-5 h-5" />,
        description: 'Vista general de métricas clave'
      },
      {
        view: 'student-progress',
        label: 'Progreso Estudiantil',
        icon: <TrendingUp className="w-5 h-5" />,
        description: 'Análisis detallado de progreso de aprendizaje'
      },
      {
        view: 'charts',
        label: 'Visualizaciones',
        icon: <Activity className="w-5 h-5" />,
        description: 'Gráficos interactivos y análisis visual'
      },
      {
        view: 'insights',
        label: 'Insights Educativos',
        icon: <Brain className="w-5 h-5" />,
        description: 'Recomendaciones personalizadas basadas en IA'
      },
      {
        view: 'realtime',
        label: 'Tiempo Real',
        icon: <Zap className="w-5 h-5" />,
        description: 'Métricas en vivo y eventos del sistema'
      }
    ];

    // Add teacher-specific views
    if (user?.isTeacher || user?.isAdmin) {
      configs.push({
        view: 'teacher-view',
        label: 'Dashboard Profesor',
        icon: <Users className="w-5 h-5" />,
        description: 'Gestión y análisis de estudiantes',
        requiredRole: 'teacher'
      });
    }

    // Add admin-specific views
    if (user?.isAdmin) {
      configs.push({
        view: 'system-metrics',
        label: 'Métricas del Sistema',
        icon: <Shield className="w-5 h-5" />,
        description: 'Rendimiento y uso de la plataforma',
        requiredRole: 'admin'
      });
    }

    setDashboardConfig(configs);
  }, [user]);

  // Mock data for charts component
  const mockChartsData = {
    timeSeriesData: Array.from({ length: 30 }, (_, i) => ({
      date: new Date(Date.now() - (29 - i) * 24 * 60 * 60 * 1000).toISOString(),
      accuracy: 0.6 + Math.random() * 0.3,
      battles: Math.floor(Math.random() * 10 + 1),
      experience: Math.floor(Math.random() * 200 + 50),
      active_users: Math.floor(Math.random() * 50 + 20)
    })),
    subjectData: [
      { subject: 'Matemáticas', accuracy: 0.75, questions: 150, difficulty: 6.2, trend: 5.2 },
      { subject: 'Lenguaje', accuracy: 0.82, questions: 120, difficulty: 5.8, trend: 3.1 },
      { subject: 'Ciencias', accuracy: 0.68, questions: 90, difficulty: 6.5, trend: -2.1 },
      { subject: 'Sociales', accuracy: 0.79, questions: 80, difficulty: 5.5, trend: 7.3 }
    ],
    difficultyDistribution: {
      labels: ['Básico', 'Intermedio', 'Avanzado', 'Experto'],
      values: [45, 120, 85, 25],
      colors: ['#10B981', '#F59E0B', '#EF4444', '#8B5CF6']
    },
    performanceHeatmap: [
      { topic: 'Álgebra', subject: 'Matemáticas', performance: 0.85 },
      { topic: 'Geometría', subject: 'Matemáticas', performance: 0.72 },
      { topic: 'Lectura Crítica', subject: 'Lenguaje', performance: 0.78 },
      { topic: 'Gramática', subject: 'Lenguaje', performance: 0.91 },
      { topic: 'Química', subject: 'Ciencias', performance: 0.65 },
      { topic: 'Física', subject: 'Ciencias', performance: 0.58 }
    ]
  };

  const renderExportModal = () => (
    <AnimatePresence>
      {showExportModal && (
        <motion.div
          className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={() => setShowExportModal(false)}
        >
          <motion.div
            className="bg-gray-900 rounded-lg p-6 w-full max-w-md mx-4"
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.9, opacity: 0 }}
            onClick={(e) => e.stopPropagation()}
          >
            <h3 className="text-xl font-semibold text-white mb-4">Exportar Analytics</h3>
            
            <div className="space-y-3">
              <button className="w-full bg-red-600 hover:bg-red-700 text-white rounded-lg p-3 flex items-center gap-3 transition-colors">
                <Download className="w-5 h-5" />
                <div className="text-left">
                  <p className="font-semibold">Reporte PDF</p>
                  <p className="text-sm opacity-80">Reporte completo con gráficos</p>
                </div>
              </button>
              
              <button className="w-full bg-green-600 hover:bg-green-700 text-white rounded-lg p-3 flex items-center gap-3 transition-colors">
                <Download className="w-5 h-5" />
                <div className="text-left">
                  <p className="font-semibold">Datos CSV</p>
                  <p className="text-sm opacity-80">Datos en formato tabular</p>
                </div>
              </button>
              
              <button className="w-full bg-blue-600 hover:bg-blue-700 text-white rounded-lg p-3 flex items-center gap-3 transition-colors">
                <Download className="w-5 h-5" />
                <div className="text-left">
                  <p className="font-semibold">Insights JSON</p>
                  <p className="text-sm opacity-80">Datos estructurados para análisis</p>
                </div>
              </button>
            </div>
            
            <div className="mt-6 flex justify-end gap-3">
              <button
                onClick={() => setShowExportModal(false)}
                className="px-4 py-2 text-gray-400 hover:text-white transition-colors"
              >
                Cancelar
              </button>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );

  const renderQuickStats = () => (
    <motion.div
      className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
    >
      <div className="bg-gradient-to-br from-purple-600/20 to-purple-700/20 rounded-lg p-4 border border-purple-500/30">
        <div className="flex items-center gap-3 mb-2">
          <Activity className="w-6 h-6 text-purple-400" />
          <span className="text-gray-300 text-sm">Sesiones Hoy</span>
        </div>
        <p className="text-2xl font-bold text-white">42</p>
        <div className="flex items-center gap-1 text-green-400 text-sm">
          <TrendingUp className="w-3 h-3" />
          <span>+18%</span>
        </div>
      </div>

      <div className="bg-gradient-to-br from-blue-600/20 to-blue-700/20 rounded-lg p-4 border border-blue-500/30">
        <div className="flex items-center gap-3 mb-2">
          <Target className="w-6 h-6 text-blue-400" />
          <span className="text-gray-300 text-sm">Precisión Promedio</span>
        </div>
        <p className="text-2xl font-bold text-white">78.5%</p>
        <div className="flex items-center gap-1 text-green-400 text-sm">
          <TrendingUp className="w-3 h-3" />
          <span>+5.2%</span>
        </div>
      </div>

      <div className="bg-gradient-to-br from-green-600/20 to-green-700/20 rounded-lg p-4 border border-green-500/30">
        <div className="flex items-center gap-3 mb-2">
          <Award className="w-6 h-6 text-green-400" />
          <span className="text-gray-300 text-sm">Exp. Ganada</span>
        </div>
        <p className="text-2xl font-bold text-white">2,340</p>
        <div className="flex items-center gap-1 text-green-400 text-sm">
          <TrendingUp className="w-3 h-3" />
          <span>+12%</span>
        </div>
      </div>

      <div className="bg-gradient-to-br from-orange-600/20 to-orange-700/20 rounded-lg p-4 border border-orange-500/30">
        <div className="flex items-center gap-3 mb-2">
          <Clock className="w-6 h-6 text-orange-400" />
          <span className="text-gray-300 text-sm">Tiempo Estudio</span>
        </div>
        <p className="text-2xl font-bold text-white">3.2h</p>
        <div className="flex items-center gap-1 text-orange-400 text-sm">
          <Clock className="w-3 h-3" />
          <span>Hoy</span>
        </div>
      </div>
    </motion.div>
  );

  const renderNavigationTabs = () => (
    <motion.div
      className="bg-gray-900/80 rounded-lg p-2 mb-6"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.1 }}
    >
      <div className="flex flex-wrap gap-2">
        {dashboardConfig.map((config) => (
          <button
            key={config.view}
            onClick={() => setActiveView(config.view)}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-semibold transition-all ${
              activeView === config.view
                ? 'bg-purple-600 text-white shadow-lg'
                : 'text-gray-400 hover:text-white hover:bg-gray-800'
            }`}
            title={config.description}
          >
            {config.icon}
            {config.label}
          </button>
        ))}
      </div>
    </motion.div>
  );

  const renderActiveView = () => {
    const commonProps = {
      isAdmin: user?.isAdmin || false,
      userId: user?.id
    };

    switch (activeView) {
      case 'overview':
        return <AnalyticsDashboard {...commonProps} />;
      
      case 'student-progress':
        return <StudentProgressAnalytics isTeacherView={user?.isTeacher || user?.isAdmin} />;
      
      case 'teacher-view':
        return user?.isTeacher || user?.isAdmin ? <TeacherDashboard /> : null;
      
      case 'charts':
        return (
          <InteractiveCharts 
            data={mockChartsData} 
            type={user?.isAdmin ? 'admin' : user?.isTeacher ? 'teacher' : 'student'} 
          />
        );
      
      case 'realtime':
        return <RealTimeAnalytics />;
      
      case 'insights':
        return <EducationalInsightsEngine isTeacherView={user?.isTeacher || user?.isAdmin} />;
      
      case 'system-metrics':
        return user?.isAdmin ? (
          <div className="bg-gray-900/80 rounded-lg p-6">
            <h3 className="text-xl font-semibold text-white mb-4">Métricas del Sistema</h3>
            <p className="text-gray-300">Panel de administración del sistema (En desarrollo)</p>
          </div>
        ) : null;
      
      default:
        return <AnalyticsDashboard {...commonProps} />;
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900 to-gray-900 relative overflow-hidden">
      {/* Background Effects */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-0 left-0 w-96 h-96 bg-purple-600/10 rounded-full blur-3xl animate-pulse" />
        <div className="absolute bottom-0 right-0 w-96 h-96 bg-blue-600/10 rounded-full blur-3xl animate-pulse animation-delay-2000" />
      </div>

      <div className="relative z-10 container mx-auto px-4 py-8">
        {/* Header */}
        <motion.div
          className="mb-8"
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-4xl font-bold text-white mb-2 font-cinzel flex items-center gap-4">
                <Brain className="w-10 h-10 text-purple-400" />
                Centro de Analytics Avanzado
              </h1>
              <p className="text-gray-300">
                Análisis integral de rendimiento, progreso y insights educativos
              </p>
            </div>
            
            <div className="flex items-center gap-4">
              <button
                onClick={() => setShowExportModal(true)}
                className="bg-purple-600 hover:bg-purple-700 text-white rounded-lg px-4 py-2 text-sm flex items-center gap-2 transition-colors"
              >
                <Download className="w-4 h-4" />
                Exportar
              </button>
              
              <button className="bg-gray-800 hover:bg-gray-700 text-white rounded-lg px-4 py-2 text-sm flex items-center gap-2 transition-colors">
                <Settings className="w-4 h-4" />
                Configurar
              </button>
            </div>
          </div>
        </motion.div>

        {/* Quick Stats */}
        {renderQuickStats()}

        {/* Navigation Tabs */}
        {renderNavigationTabs()}

        {/* Active View Content */}
        <motion.div
          key={activeView}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
        >
          {renderActiveView()}
        </motion.div>

        {/* Export Modal */}
        {renderExportModal()}

        {/* Footer */}
        <motion.div
          className="mt-12 text-center text-gray-400 text-sm"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1 }}
        >
          <p>
            Centro de Analytics IcfesLeveling • Última actualización: {new Date().toLocaleString()}
          </p>
        </motion.div>
      </div>
    </div>
  );
}