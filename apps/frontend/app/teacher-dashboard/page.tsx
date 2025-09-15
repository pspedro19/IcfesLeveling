'use client';

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  BookOpen,
  Users,
  BarChart3,
  AlertCircle,
  Settings,
  Calendar,
  Download,
  Bell,
  Search,
  Filter,
  Home,
  TrendingUp,
  Target,
  Award,
  Clock,
  ChevronLeft,
  ChevronRight,
  Menu,
  X,
  HelpCircle,
  LogOut,
  User,
  Bookmark,
  Archive
} from 'lucide-react';

// Import components
import ClassAnalyticsView from '@/components/Teacher/ClassAnalyticsView';
import StudentWeaknessHeatmap from '@/components/Teacher/StudentWeaknessHeatmap';
import DistractorAnalysis from '@/components/Teacher/DistractorAnalysis';
import ExportService from '@/components/Teacher/ExportService';
import StudentRiskAlerts from '@/components/Teacher/StudentRiskAlerts';
import AdvancedClassAnalytics from '@/components/Teacher/AdvancedClassAnalytics';

interface TeacherClass {
  id: string;
  name: string;
  code: string;
  subject: string;
  gradeLevel: string;
  totalStudents: number;
  activeStudents: number;
  avgMastery: number;
  progressDelta: number;
  lastActivity: string;
}

interface QuickStat {
  label: string;
  value: string | number;
  change?: number;
  color: string;
  icon: React.ReactNode;
}

interface TeacherProfile {
  id: string;
  name: string;
  email: string;
  institution: string;
  specialization: string;
  avatar?: string;
  totalClasses: number;
  totalStudents: number;
}

type ViewType = 'overview' | 'analytics' | 'heatmap' | 'distractors' | 'alerts' | 'settings';

export default function TeacherDashboard() {
  const [currentView, setCurrentView] = useState<ViewType>('overview');
  const [selectedClass, setSelectedClass] = useState<string>('');
  const [classes, setClasses] = useState<TeacherClass[]>([]);
  const [profile, setProfile] = useState<TeacherProfile | null>(null);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [notifications, setNotifications] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showNotifications, setShowNotifications] = useState(false);
  const [showExportModal, setShowExportModal] = useState(false);

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyPress = (e: KeyboardEvent) => {
      if (e.ctrlKey || e.metaKey) {
        switch (e.key) {
          case '1':
            e.preventDefault();
            setCurrentView('overview');
            break;
          case '2':
            e.preventDefault();
            setCurrentView('analytics');
            break;
          case '3':
            e.preventDefault();
            setCurrentView('heatmap');
            break;
          case '4':
            e.preventDefault();
            setCurrentView('distractors');
            break;
          case '5':
            e.preventDefault();
            setCurrentView('alerts');
            break;
          case 'k':
            e.preventDefault();
            document.getElementById('search')?.focus();
            break;
        }
      }
    };

    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, []);

  // Load teacher data
  useEffect(() => {
    const loadTeacherData = async () => {
      setLoading(true);
      try {
        const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:4000';
        
        // Load teacher profile
        const profileResponse = await fetch(`${API_URL}/api/v1/teacher/profile`, {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
            'Content-Type': 'application/json'
          }
        });
        
        if (!profileResponse.ok) {
          throw new Error('Failed to load teacher profile');
        }
        
        const teacherProfile = await profileResponse.json();
        setProfile(teacherProfile);
        
        // Load teacher's classes
        const classesResponse = await fetch(`${API_URL}/api/v1/teacher/classes`, {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
            'Content-Type': 'application/json'
          }
        });
        
        if (!classesResponse.ok) {
          throw new Error('Failed to load classes');
        }
        
        const teacherClasses = await classesResponse.json();
        setClasses(teacherClasses);
        
        if (teacherClasses.length > 0) {
          setSelectedClass(teacherClasses[0].id);
        }
        
        // Load notifications
        const notificationsResponse = await fetch(`${API_URL}/api/v1/teacher/notifications`, {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
            'Content-Type': 'application/json'
          }
        });
        
        if (notificationsResponse.ok) {
          const teacherNotifications = await notificationsResponse.json();
          setNotifications(teacherNotifications);
        } else {
          // Notifications are optional, just log the error
          console.warn('Could not load notifications');
          setNotifications([]);
        }
        
      } catch (error) {
        console.error('Error loading teacher data:', error);
        // Set empty data instead of mock data
        setProfile(null);
        setClasses([]);
        setNotifications([]);
      } finally {
        setLoading(false);
      }
    };

    loadTeacherData();
  }, []);

  const navigationItems = [
    {
      id: 'overview',
      label: 'Resumen General',
      icon: Home,
      shortcut: '⌘1'
    },
    {
      id: 'analytics',
      label: 'Analytics de Clase',
      icon: BarChart3,
      shortcut: '⌘2'
    },
    {
      id: 'heatmap',
      label: 'Mapa de Debilidades',
      icon: Target,
      shortcut: '⌘3'
    },
    {
      id: 'distractors',
      label: 'Análisis de Distractores',
      icon: AlertCircle,
      shortcut: '⌘4'
    },
    {
      id: 'alerts',
      label: 'Alertas de Riesgo',
      icon: Bell,
      shortcut: '⌘5'
    }
  ];

  const filteredClasses = classes.filter(cls =>
    cls.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    cls.subject.toLowerCase().includes(searchTerm.toLowerCase()) ||
    cls.code.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const getQuickStats = (): QuickStat[] => [
    {
      label: 'Total Estudiantes',
      value: profile?.totalStudents || 0,
      color: 'blue',
      icon: <Users className="w-5 h-5" />
    },
    {
      label: 'Clases Activas',
      value: classes.length,
      color: 'purple',
      icon: <BookOpen className="w-5 h-5" />
    },
    {
      label: 'Promedio General',
      value: `${(classes.reduce((acc, cls) => acc + cls.avgMastery, 0) / classes.length).toFixed(1)}%`,
      change: 6.8,
      color: 'green',
      icon: <TrendingUp className="w-5 h-5" />
    },
    {
      label: 'Estudiantes Activos',
      value: `${Math.round((classes.reduce((acc, cls) => acc + cls.activeStudents, 0) / classes.reduce((acc, cls) => acc + cls.totalStudents, 0)) * 100)}%`,
      change: 2.3,
      color: 'yellow',
      icon: <Award className="w-5 h-5" />
    }
  ];

  const renderSidebar = () => (
    <motion.div
      className={`bg-gray-900/95 border-r border-gray-700/50 flex flex-col h-full ${
        sidebarCollapsed ? 'w-16' : 'w-64'
      }`}
      animate={{ width: sidebarCollapsed ? 64 : 256 }}
      transition={{ duration: 0.3 }}
    >
      {/* Header */}
      <div className="p-4 border-b border-gray-700/50">
        <div className="flex items-center justify-between">
          {!sidebarCollapsed && (
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 bg-gradient-to-r from-purple-500 to-blue-500 rounded-lg flex items-center justify-center">
                <BookOpen className="w-4 h-4 text-white" />
              </div>
              <span className="text-white font-bold">IcfesLeveling</span>
            </div>
          )}
          <button
            onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
            className="p-1 hover:bg-gray-800 rounded"
          >
            {sidebarCollapsed ? <ChevronRight className="w-4 h-4 text-gray-400" /> : <ChevronLeft className="w-4 h-4 text-gray-400" />}
          </button>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4">
        <div className="space-y-2">
          {navigationItems.map((item) => (
            <button
              key={item.id}
              onClick={() => setCurrentView(item.id as ViewType)}
              className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg transition-all ${
                currentView === item.id
                  ? 'bg-purple-600 text-white'
                  : 'text-gray-400 hover:text-white hover:bg-gray-800'
              }`}
            >
              <item.icon className="w-5 h-5" />
              {!sidebarCollapsed && (
                <>
                  <span className="flex-1 text-left">{item.label}</span>
                  <span className="text-xs opacity-60">{item.shortcut}</span>
                </>
              )}
            </button>
          ))}
        </div>
      </nav>

      {/* Profile */}
      {profile && (
        <div className="p-4 border-t border-gray-700/50">
          <div className={`flex items-center ${sidebarCollapsed ? 'justify-center' : 'gap-3'}`}>
            <div className="w-8 h-8 bg-gradient-to-r from-green-500 to-blue-500 rounded-full flex items-center justify-center">
              <span className="text-white text-sm font-bold">
                {profile.name.split(' ').map(n => n[0]).join('')}
              </span>
            </div>
            {!sidebarCollapsed && (
              <div className="flex-1 min-w-0">
                <p className="text-white text-sm font-medium truncate">{profile.name}</p>
                <p className="text-gray-400 text-xs truncate">{profile.institution}</p>
              </div>
            )}
          </div>
        </div>
      )}
    </motion.div>
  );

  const renderHeader = () => (
    <header className="bg-gray-900/95 border-b border-gray-700/50 px-6 py-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div>
            <h1 className="text-2xl font-bold text-white">
              {currentView === 'overview' && 'Resumen General'}
              {currentView === 'analytics' && 'Analytics de Clase'}
              {currentView === 'heatmap' && 'Mapa de Debilidades'}
              {currentView === 'distractors' && 'Análisis de Distractores'}
              {currentView === 'alerts' && 'Alertas de Riesgo'}
            </h1>
            {selectedClass && (
              <p className="text-gray-400 text-sm">
                {classes.find(c => c.id === selectedClass)?.name}
              </p>
            )}
          </div>
        </div>

        <div className="flex items-center gap-4">
          {/* Search */}
          <div className="relative">
            <Search className="w-4 h-4 text-gray-400 absolute left-3 top-1/2 transform -translate-y-1/2" />
            <input
              id="search"
              type="text"
              placeholder="Buscar clases... (⌘K)"
              className="pl-10 pr-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500 w-64"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>

          {/* Notifications */}
          <div className="relative">
            <button
              onClick={() => setShowNotifications(!showNotifications)}
              className="p-2 hover:bg-gray-800 rounded-lg relative"
            >
              <Bell className="w-5 h-5 text-gray-400" />
              {notifications.filter(n => !n.read).length > 0 && (
                <span className="absolute -top-1 -right-1 w-3 h-3 bg-red-500 rounded-full text-xs"></span>
              )}
            </button>

            {showNotifications && (
              <motion.div
                className="absolute right-0 top-12 w-80 bg-gray-900 border border-gray-700 rounded-lg shadow-xl z-50"
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
              >
                <div className="p-4 border-b border-gray-700">
                  <h3 className="text-white font-medium">Notificaciones</h3>
                </div>
                <div className="max-h-64 overflow-y-auto">
                  {notifications.map((notification) => (
                    <div key={notification.id} className="p-4 border-b border-gray-800 last:border-b-0">
                      <div className="flex gap-3">
                        <div className={`p-1 rounded ${
                          notification.type === 'alert' ? 'bg-red-500/20' : 'bg-green-500/20'
                        }`}>
                          {notification.type === 'alert' ? 
                            <AlertCircle className="w-4 h-4 text-red-400" /> :
                            <TrendingUp className="w-4 h-4 text-green-400" />
                          }
                        </div>
                        <div className="flex-1">
                          <p className="text-white text-sm font-medium">{notification.title}</p>
                          <p className="text-gray-400 text-xs">{notification.message}</p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </motion.div>
            )}
          </div>

          {/* Export */}
          <button 
            onClick={() => setShowExportModal(true)}
            className="p-2 hover:bg-gray-800 rounded-lg"
            title="Exportar datos"
          >
            <Download className="w-5 h-5 text-gray-400" />
          </button>
        </div>
      </div>
    </header>
  );

  const renderClassSelector = () => {
    if (currentView === 'overview') return null;

    return (
      <div className="px-6 py-4 bg-gray-900/50 border-b border-gray-700/50">
        <div className="flex items-center gap-4">
          <label className="text-gray-400 text-sm">Clase:</label>
          <select
            value={selectedClass}
            onChange={(e) => setSelectedClass(e.target.value)}
            className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white min-w-48"
          >
            {filteredClasses.map((cls) => (
              <option key={cls.id} value={cls.id}>
                {cls.name} ({cls.totalStudents} estudiantes)
              </option>
            ))}
          </select>
        </div>
      </div>
    );
  };

  const renderOverview = () => (
    <div className="space-y-6">
      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {getQuickStats().map((stat, index) => (
          <motion.div
            key={index}
            className="bg-gray-900/80 rounded-lg border border-gray-700/50 p-6"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
          >
            <div className="flex items-center justify-between mb-4">
              <div className={`p-3 rounded-lg bg-${stat.color}-500/20`}>
                {stat.icon}
              </div>
              {stat.change && (
                <div className={`flex items-center gap-1 text-sm ${
                  stat.change > 0 ? 'text-green-400' : 'text-red-400'
                }`}>
                  {stat.change > 0 ? <TrendingUp className="w-4 h-4" /> : <TrendingUp className="w-4 h-4 rotate-180" />}
                  <span>{stat.change > 0 ? '+' : ''}{stat.change}%</span>
                </div>
              )}
            </div>
            <p className="text-gray-400 text-sm mb-1">{stat.label}</p>
            <p className="text-2xl font-bold text-white">{stat.value}</p>
          </motion.div>
        ))}
      </div>

      {/* Classes Grid */}
      <div>
        <h2 className="text-xl font-semibold text-white mb-4">Mis Clases</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredClasses.map((cls, index) => (
            <motion.div
              key={cls.id}
              className="bg-gray-900/80 rounded-lg border border-gray-700/50 p-6 hover:border-purple-500/50 transition-all cursor-pointer"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
              onClick={() => {
                setSelectedClass(cls.id);
                setCurrentView('analytics');
              }}
            >
              <div className="flex justify-between items-start mb-4">
                <div>
                  <h3 className="text-white font-semibold">{cls.name}</h3>
                  <p className="text-gray-400 text-sm">{cls.code}</p>
                </div>
                <div className={`px-2 py-1 rounded text-xs ${
                  cls.subject === 'Matemáticas' ? 'bg-blue-500/20 text-blue-400' :
                  cls.subject === 'Física' ? 'bg-purple-500/20 text-purple-400' :
                  cls.subject === 'Química' ? 'bg-green-500/20 text-green-400' :
                  'bg-gray-500/20 text-gray-400'
                }`}>
                  {cls.subject}
                </div>
              </div>

              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-gray-400 text-sm">Estudiantes</span>
                  <span className="text-white">{cls.activeStudents}/{cls.totalStudents}</span>
                </div>
                
                <div className="flex justify-between items-center">
                  <span className="text-gray-400 text-sm">Mastery Promedio</span>
                  <span className={`font-semibold ${
                    cls.avgMastery >= 80 ? 'text-green-400' :
                    cls.avgMastery >= 70 ? 'text-yellow-400' :
                    cls.avgMastery >= 60 ? 'text-orange-400' :
                    'text-red-400'
                  }`}>
                    {cls.avgMastery.toFixed(1)}%
                  </span>
                </div>
                
                <div className="flex justify-between items-center">
                  <span className="text-gray-400 text-sm">Progreso (30d)</span>
                  <span className={`flex items-center gap-1 text-sm ${
                    cls.progressDelta > 0 ? 'text-green-400' : 'text-red-400'
                  }`}>
                    {cls.progressDelta > 0 ? <TrendingUp className="w-3 h-3" /> : <TrendingUp className="w-3 h-3 rotate-180" />}
                    {cls.progressDelta > 0 ? '+' : ''}{cls.progressDelta}%
                  </span>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </div>
  );

  const renderContent = () => {
    const selectedClassData = classes.find(c => c.id === selectedClass);
    
    switch (currentView) {
      case 'overview':
        return renderOverview();
      case 'analytics':
        return selectedClassData ? (
          <ClassAnalyticsView 
            classId={selectedClass}
            className={selectedClassData.name}
            teacherId={profile?.id || ''}
          />
        ) : null;
      case 'heatmap':
        return selectedClassData ? (
          <StudentWeaknessHeatmap
            classId={selectedClass}
            className={selectedClassData.name}
          />
        ) : null;
      case 'distractors':
        return selectedClassData ? (
          <DistractorAnalysis
            classId={selectedClass}
            className={selectedClassData.name}
          />
        ) : null;
      case 'alerts':
        return (
          <StudentRiskAlerts
            classId={selectedClass}
            teacherId={profile?.id || ''}
            onCreateIntervention={(studentId, alertId) => {
              console.log('Creating intervention for student:', studentId, 'alert:', alertId);
              // Implement intervention creation logic
            }}
          />
        );
      default:
        return null;
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-950 flex items-center justify-center">
        <motion.div
          className="flex flex-col items-center gap-4"
          animate={{ opacity: [0.5, 1, 0.5] }}
          transition={{ duration: 2, repeat: Infinity }}
        >
          <div className="relative">
            <div className="w-16 h-16 border-4 border-purple-500/30 rounded-full animate-spin">
              <div className="absolute top-0 left-0 w-16 h-16 border-4 border-transparent border-t-purple-500 rounded-full animate-spin"></div>
            </div>
            <BookOpen className="absolute inset-0 w-8 h-8 m-auto text-purple-400" />
          </div>
          <p className="text-white font-semibold">Cargando datos del profesor...</p>
        </motion.div>
      </div>
    );
  }
  
  // Show error state if no profile data could be loaded
  if (!profile && !loading) {
    return (
      <div className="min-h-screen bg-gray-950 flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-red-400 mb-4">Error al cargar datos</h2>
          <p className="text-gray-400 mb-6">No se pudieron cargar los datos del profesor</p>
          <button 
            onClick={() => window.location.reload()} 
            className="px-6 py-3 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition-colors"
          >
            Intentar de nuevo
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-950 text-white flex">
      {/* Sidebar */}
      {renderSidebar()}
      
      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        {renderHeader()}
        
        {/* Class Selector */}
        {renderClassSelector()}
        
        {/* Content */}
        <main className="flex-1 overflow-y-auto">
          <div className="p-6">
            <AnimatePresence mode="wait">
              <motion.div
                key={currentView}
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                transition={{ duration: 0.3 }}
              >
                {renderContent()}
              </motion.div>
            </AnimatePresence>
          </div>
        </main>
      </div>

      {/* Export Modal */}
      <ExportService
        isOpen={showExportModal}
        onClose={() => setShowExportModal(false)}
        classId={selectedClass}
        className={classes.find(c => c.id === selectedClass)?.name}
        currentView={currentView === 'overview' ? 'analytics' : currentView as any}
      />

      {/* Click outside to close notifications */}
      {showNotifications && (
        <div 
          className="fixed inset-0 z-40" 
          onClick={() => setShowNotifications(false)}
        />
      )}
    </div>
  );
}