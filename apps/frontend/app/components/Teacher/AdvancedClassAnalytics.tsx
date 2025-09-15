'use client';

import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  ScatterChart,
  Scatter,
  ComposedChart,
  Area,
  AreaChart
} from 'recharts';
import {
  Users,
  TrendingUp,
  TrendingDown,
  Target,
  Clock,
  Brain,
  Award,
  AlertTriangle,
  CheckCircle,
  Activity,
  Eye,
  Lightbulb,
  Star,
  BookOpen,
  Zap,
  Heart
} from 'lucide-react';

interface StudentProgress {
  id: string;
  name: string;
  currentLevel: number;
  mastery: number;
  improvement: number;
  timeSpent: number;
  questionsAnswered: number;
  accuracy: number;
  riskLevel: 'low' | 'medium' | 'high';
}

interface SubjectAnalytics {
  subject: string;
  avgMastery: number;
  improvement: number;
  difficultyDistribution: Array<{
    difficulty: string;
    count: number;
    accuracy: number;
  }>;
  topicPerformance: Array<{
    topic: string;
    mastery: number;
    questions: number;
  }>;
}

interface ClassInsights {
  totalStudents: number;
  activeStudents: number;
  averageImprovement: number;
  riskStudents: number;
  topPerformers: number;
  engagementRate: number;
  retentionRate: number;
}

interface AdvancedClassAnalyticsProps {
  classId: string;
  className: string;
  timeRange: '7d' | '30d' | '90d';
}

export default function AdvancedClassAnalytics({ classId, className, timeRange }: AdvancedClassAnalyticsProps) {
  const [students, setStudents] = useState<StudentProgress[]>([]);
  const [subjects, setSubjects] = useState<SubjectAnalytics[]>([]);
  const [insights, setInsights] = useState<ClassInsights | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedSubject, setSelectedSubject] = useState<string>('all');
  const [viewMode, setViewMode] = useState<'overview' | 'individual' | 'subjects' | 'insights'>('overview');

  // Fetch real analytics data
  useEffect(() => {
    const fetchClassAnalytics = async () => {
      setLoading(true);
      try {
        const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:4000';
        const token = localStorage.getItem('access_token');
        
        if (!token) {
          throw new Error('No se encontró token de autenticación');
        }
        
        const response = await fetch(`${API_URL}/api/v1/teacher/classes/${classId}/analytics?timeRange=${timeRange}`, {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        });
        
        if (!response.ok) {
          throw new Error('Error al cargar los datos analíticos de la clase');
        }
        
        const analyticsData = await response.json();
        
        setStudents(analyticsData.students || []);
        setSubjects(analyticsData.subjects || []);
        setInsights(analyticsData.insights || {
          totalStudents: 0,
          activeStudents: 0,
          averageImprovement: 0,
          riskStudents: 0,
          topPerformers: 0,
          engagementRate: 0,
          retentionRate: 0
        });
      } catch (error) {
        console.error('Error fetching class analytics:', error);
        // Set empty data instead of mock data
        setStudents([]);
        setSubjects([]);
        setInsights({
          totalStudents: 0,
          activeStudents: 0,
          averageImprovement: 0,
          riskStudents: 0,
          topPerformers: 0,
          engagementRate: 0,
          retentionRate: 0
        });
      } finally {
        setLoading(false);
      }
    };

    if (classId) {
      fetchClassAnalytics();
    }
  }, [classId, timeRange]);

  const getRiskColor = (riskLevel: StudentProgress['riskLevel']) => {
    switch (riskLevel) {
      case 'high': return 'text-red-400 bg-red-500/20';
      case 'medium': return 'text-yellow-400 bg-yellow-500/20';
      case 'low': return 'text-green-400 bg-green-500/20';
    }
  };

  const renderOverview = () => (
    <div className="space-y-6">
      {/* Class Insights Cards */}
      {insights && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <motion.div 
            className="bg-gray-800/50 rounded-lg p-6 border border-gray-700/50"
            whileHover={{ scale: 1.02 }}
          >
            <div className="flex items-center justify-between mb-4">
              <div className="p-3 bg-blue-500/20 rounded-lg">
                <Users className="w-6 h-6 text-blue-400" />
              </div>
              <div className="text-right">
                <p className="text-2xl font-bold text-white">{insights.activeStudents}/{insights.totalStudents}</p>
                <p className="text-gray-400 text-sm">Estudiantes Activos</p>
              </div>
            </div>
            <div className="w-full bg-gray-700 rounded-full h-2">
              <div 
                className="bg-blue-500 h-2 rounded-full" 
                style={{ width: `${(insights.activeStudents / insights.totalStudents) * 100}%` }}
              />
            </div>
          </motion.div>

          <motion.div 
            className="bg-gray-800/50 rounded-lg p-6 border border-gray-700/50"
            whileHover={{ scale: 1.02 }}
          >
            <div className="flex items-center justify-between mb-4">
              <div className="p-3 bg-green-500/20 rounded-lg">
                <TrendingUp className="w-6 h-6 text-green-400" />
              </div>
              <div className="text-right">
                <p className="text-2xl font-bold text-green-400">+{insights.averageImprovement}%</p>
                <p className="text-gray-400 text-sm">Mejora Promedio</p>
              </div>
            </div>
            <p className="text-green-400 text-sm">↗ Tendencia positiva</p>
          </motion.div>

          <motion.div 
            className="bg-gray-800/50 rounded-lg p-6 border border-gray-700/50"
            whileHover={{ scale: 1.02 }}
          >
            <div className="flex items-center justify-between mb-4">
              <div className="p-3 bg-red-500/20 rounded-lg">
                <AlertTriangle className="w-6 h-6 text-red-400" />
              </div>
              <div className="text-right">
                <p className="text-2xl font-bold text-red-400">{insights.riskStudents}</p>
                <p className="text-gray-400 text-sm">En Riesgo</p>
              </div>
            </div>
            <p className="text-red-400 text-sm">Requieren atención</p>
          </motion.div>

          <motion.div 
            className="bg-gray-800/50 rounded-lg p-6 border border-gray-700/50"
            whileHover={{ scale: 1.02 }}
          >
            <div className="flex items-center justify-between mb-4">
              <div className="p-3 bg-purple-500/20 rounded-lg">
                <Star className="w-6 h-6 text-purple-400" />
              </div>
              <div className="text-right">
                <p className="text-2xl font-bold text-purple-400">{insights.topPerformers}</p>
                <p className="text-gray-400 text-sm">Top Performers</p>
              </div>
            </div>
            <p className="text-purple-400 text-sm">Excelente rendimiento</p>
          </motion.div>
        </div>
      )}

      {/* Performance Distribution Chart */}
      <div className="bg-gray-800/50 rounded-lg p-6 border border-gray-700/50">
        <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-3">
          <Target className="w-5 h-5 text-purple-400" />
          Distribución de Rendimiento
        </h3>
        
        <ResponsiveContainer width="100%" height={300}>
          <ComposedChart data={students}>
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
            <XAxis dataKey="name" stroke="#9ca3af" fontSize={10} />
            <YAxis stroke="#9ca3af" />
            <Tooltip
              content={({ active, payload, label }) => {
                if (active && payload && payload.length) {
                  const student = students.find(s => s.name === label);
                  return (
                    <div className="bg-gray-900/95 border border-gray-700 rounded-lg p-4 shadow-xl">
                      <p className="text-white font-semibold mb-2">{label}</p>
                      <div className="space-y-1">
                        <p className="text-blue-400 text-sm">Nivel: {student?.currentLevel}</p>
                        <p className="text-green-400 text-sm">Dominio: {student?.mastery.toFixed(1)}%</p>
                        <p className="text-purple-400 text-sm">Precisión: {student?.accuracy.toFixed(1)}%</p>
                        <p className={`text-sm ${getRiskColor(student?.riskLevel || 'low').split(' ')[0]}`}>
                          Riesgo: {student?.riskLevel}
                        </p>
                      </div>
                    </div>
                  );
                }
                return null;
              }}
            />
            <Bar dataKey="mastery" fill="#3b82f6" opacity={0.6} />
            <Line type="monotone" dataKey="accuracy" stroke="#10b981" strokeWidth={2} />
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      {/* Subject Performance Comparison */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-gray-800/50 rounded-lg p-6 border border-gray-700/50">
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-3">
            <BookOpen className="w-5 h-5 text-blue-400" />
            Rendimiento por Materia
          </h3>
          
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={subjects}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="subject" stroke="#9ca3af" />
              <YAxis stroke="#9ca3af" />
              <Tooltip
                content={({ active, payload, label }) => {
                  if (active && payload && payload.length) {
                    return (
                      <div className="bg-gray-900/95 border border-gray-700 rounded-lg p-3 shadow-xl">
                        <p className="text-white font-semibold">{label}</p>
                        <p className="text-blue-400 text-sm">Dominio: {payload[0].value}%</p>
                        <p className="text-green-400 text-sm">Mejora: +{payload[1].value}%</p>
                      </div>
                    );
                  }
                  return null;
                }}
              />
              <Bar dataKey="avgMastery" fill="#3b82f6" />
              <Bar dataKey="improvement" fill="#10b981" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-gray-800/50 rounded-lg p-6 border border-gray-700/50">
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-3">
            <Activity className="w-5 h-5 text-purple-400" />
            Engagement y Retención
          </h3>
          
          <div className="space-y-6">
            <div>
              <div className="flex justify-between items-center mb-2">
                <span className="text-gray-300">Engagement Rate</span>
                <span className="text-white font-semibold">{insights?.engagementRate}%</span>
              </div>
              <div className="w-full bg-gray-700 rounded-full h-3">
                <div 
                  className="bg-purple-500 h-3 rounded-full transition-all duration-1000" 
                  style={{ width: `${insights?.engagementRate}%` }}
                />
              </div>
            </div>

            <div>
              <div className="flex justify-between items-center mb-2">
                <span className="text-gray-300">Retention Rate</span>
                <span className="text-white font-semibold">{insights?.retentionRate}%</span>
              </div>
              <div className="w-full bg-gray-700 rounded-full h-3">
                <div 
                  className="bg-green-500 h-3 rounded-full transition-all duration-1000" 
                  style={{ width: `${insights?.retentionRate}%` }}
                />
              </div>
            </div>

            {/* Risk Distribution */}
            <div>
              <h4 className="text-white font-medium mb-3">Distribución de Riesgo</h4>
              <div className="space-y-2">
                {['low', 'medium', 'high'].map((risk) => {
                  const count = students.filter(s => s.riskLevel === risk).length;
                  const percentage = (count / students.length) * 100;
                  return (
                    <div key={risk} className="flex items-center gap-3">
                      <div className={`w-3 h-3 rounded-full ${
                        risk === 'low' ? 'bg-green-500' :
                        risk === 'medium' ? 'bg-yellow-500' : 'bg-red-500'
                      }`} />
                      <span className="text-gray-300 text-sm w-16">
                        {risk === 'low' ? 'Bajo' : risk === 'medium' ? 'Medio' : 'Alto'}
                      </span>
                      <div className="flex-1 bg-gray-700 rounded-full h-2">
                        <div 
                          className={`h-2 rounded-full ${
                            risk === 'low' ? 'bg-green-500' :
                            risk === 'medium' ? 'bg-yellow-500' : 'bg-red-500'
                          }`}
                          style={{ width: `${percentage}%` }}
                        />
                      </div>
                      <span className="text-white text-sm w-8">{count}</span>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  const renderIndividualProgress = () => (
    <div className="space-y-6">
      <div className="bg-gray-800/50 rounded-lg p-6 border border-gray-700/50">
        <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-3">
          <Users className="w-5 h-5 text-blue-400" />
          Progreso Individual de Estudiantes
        </h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {students.map((student, index) => (
            <motion.div
              key={student.id}
              className="bg-gray-900/50 rounded-lg p-4 border border-gray-700/30 hover:border-purple-500/50 transition-all"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.05 }}
              whileHover={{ scale: 1.02 }}
            >
              <div className="flex items-center justify-between mb-3">
                <h4 className="text-white font-medium text-sm">{student.name}</h4>
                <div className={`px-2 py-1 rounded-full text-xs font-semibold ${getRiskColor(student.riskLevel)}`}>
                  {student.riskLevel === 'low' ? 'Bien' : student.riskLevel === 'medium' ? 'Atención' : 'Riesgo'}
                </div>
              </div>
              
              <div className="space-y-2">
                <div className="flex justify-between items-center">
                  <span className="text-gray-400 text-xs">Nivel</span>
                  <span className="text-purple-400 font-semibold text-sm">{student.currentLevel}</span>
                </div>
                
                <div className="flex justify-between items-center">
                  <span className="text-gray-400 text-xs">Dominio</span>
                  <span className="text-blue-400 font-semibold text-sm">{student.mastery.toFixed(1)}%</span>
                </div>
                
                <div className="flex justify-between items-center">
                  <span className="text-gray-400 text-xs">Precisión</span>
                  <span className="text-green-400 font-semibold text-sm">{student.accuracy.toFixed(1)}%</span>
                </div>
                
                <div className="flex justify-between items-center">
                  <span className="text-gray-400 text-xs">Tiempo (min)</span>
                  <span className="text-yellow-400 font-semibold text-sm">{student.timeSpent}</span>
                </div>

                <div className="pt-2">
                  <div className="w-full bg-gray-700 rounded-full h-2">
                    <div 
                      className={`h-2 rounded-full ${
                        student.mastery >= 80 ? 'bg-green-500' :
                        student.mastery >= 70 ? 'bg-blue-500' :
                        student.mastery >= 60 ? 'bg-yellow-500' : 'bg-red-500'
                      }`}
                      style={{ width: `${student.mastery}%` }}
                    />
                  </div>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </div>
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <motion.div
          className="w-8 h-8 border-2 border-purple-500 border-t-transparent rounded-full"
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
        />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* View Mode Selector */}
      <div className="flex items-center gap-2 bg-gray-800/50 rounded-lg p-1">
        {[
          { id: 'overview', label: 'Resumen', icon: Eye },
          { id: 'individual', label: 'Individual', icon: Users },
          { id: 'subjects', label: 'Materias', icon: BookOpen },
          { id: 'insights', label: 'Insights', icon: Lightbulb }
        ].map((mode) => (
          <button
            key={mode.id}
            onClick={() => setViewMode(mode.id as any)}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-all ${
              viewMode === mode.id
                ? 'bg-purple-600 text-white'
                : 'text-gray-400 hover:text-white hover:bg-gray-700'
            }`}
          >
            <mode.icon className="w-4 h-4" />
            <span className="hidden sm:inline">{mode.label}</span>
          </button>
        ))}
      </div>

      {/* Content */}
      <motion.div
        key={viewMode}
        initial={{ opacity: 0, x: 20 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.3 }}
      >
        {viewMode === 'overview' && renderOverview()}
        {viewMode === 'individual' && renderIndividualProgress()}
        {(viewMode === 'subjects' || viewMode === 'insights') && (
          <div className="bg-gray-800/50 rounded-lg p-8 border border-gray-700/50 text-center">
            <div className="w-16 h-16 bg-gray-700 rounded-full flex items-center justify-center mx-auto mb-4">
              <Lightbulb className="w-8 h-8 text-gray-400" />
            </div>
            <h3 className="text-xl font-semibold text-white mb-2">Próximamente</h3>
            <p className="text-gray-400">
              Esta vista estará disponible en futuras actualizaciones.
            </p>
          </div>
        )}
      </motion.div>
    </div>
  );
}