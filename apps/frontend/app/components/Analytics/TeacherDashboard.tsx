'use client';

import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { 
  Users,
  TrendingUp,
  TrendingDown,
  BarChart3,
  PieChart,
  LineChart,
  BookOpen,
  Target,
  Clock,
  Award,
  AlertTriangle,
  CheckCircle,
  Calendar,
  Download,
  Filter,
  Search,
  Eye,
  Brain,
  Star,
  Settings
} from 'lucide-react';
import StudentProgressAnalytics from './StudentProgressAnalytics';

interface ClassMetrics {
  total_students: number;
  active_students_30d: number;
  avg_class_accuracy: number;
  total_battles_completed: number;
  avg_session_duration: number;
  improvement_rate: number;
}

interface StudentSummary {
  student_id: string;
  student_name: string;
  accuracy: number;
  battles_completed: number;
  last_activity: string;
  level: number;
  rank: string;
  experience: number;
  status: 'excellent' | 'good' | 'needs_attention' | 'inactive';
}

interface SubjectPerformance {
  subject_name: string;
  avg_accuracy: number;
  total_questions: number;
  student_count: number;
  difficulty_level: number;
}

interface TeacherDashboardData {
  class_metrics: ClassMetrics;
  student_summaries: StudentSummary[];
  subject_performance: SubjectPerformance[];
  top_performers: StudentSummary[];
  students_needing_help: StudentSummary[];
}

export default function TeacherDashboard() {
  const [data, setData] = useState<TeacherDashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedStudent, setSelectedStudent] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState<string>('all');

  useEffect(() => {
    fetchTeacherData();
  }, []);

  const fetchTeacherData = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:4000';
      const token = localStorage.getItem('access_token');
      
      if (!token) {
        throw new Error('No se encontró token de autenticación');
      }
      
      const response = await fetch(`${API_URL}/api/v1/teacher/dashboard/analytics`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (!response.ok) {
        throw new Error('Error al cargar los datos del dashboard');
      }
      
      const dashboardData = await response.json();
      
      // Process the data to separate top performers and students needing help
      const processedData = {
        ...dashboardData,
        top_performers: dashboardData.student_summaries
          ?.filter(s => s.status === 'excellent')
          ?.sort((a, b) => b.accuracy - a.accuracy)
          ?.slice(0, 5) || [],
        students_needing_help: dashboardData.student_summaries
          ?.filter(s => s.status === 'needs_attention')
          ?.sort((a, b) => a.accuracy - b.accuracy)
          ?.slice(0, 5) || []
      };
      
      setData(processedData);
    } catch (err) {
      console.error('Error fetching teacher dashboard data:', err);
      setError(err instanceof Error ? err.message : 'Error desconocido');
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'excellent': return 'text-green-400 bg-green-500/20';
      case 'good': return 'text-blue-400 bg-blue-500/20';
      case 'needs_attention': return 'text-orange-400 bg-orange-500/20';
      case 'inactive': return 'text-red-400 bg-red-500/20';
      default: return 'text-gray-400 bg-gray-500/20';
    }
  };

  const getStatusLabel = (status: string) => {
    switch (status) {
      case 'excellent': return 'Excelente';
      case 'good': return 'Bueno';
      case 'needs_attention': return 'Necesita Atención';
      case 'inactive': return 'Inactivo';
      default: return 'Desconocido';
    }
  };

  const filteredStudents = data?.student_summaries.filter(student => {
    const matchesSearch = student.student_name.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesFilter = filterStatus === 'all' || student.status === filterStatus;
    return matchesSearch && matchesFilter;
  }) || [];

  const renderClassMetrics = () => (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      <motion.div
        className="bg-gray-900/80 rounded-lg p-6"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <div className="flex items-center gap-3 mb-3">
          <div className="p-2 bg-purple-500/20 rounded-lg">
            <Users className="w-6 h-6 text-purple-400" />
          </div>
          <div>
            <p className="text-gray-400 text-sm">Estudiantes Activos</p>
            <p className="text-white text-2xl font-bold">
              {data?.class_metrics.active_students_30d}/{data?.class_metrics.total_students}
            </p>
          </div>
        </div>
        <div className="w-full bg-gray-700 rounded-full h-2">
          <div 
            className="bg-purple-500 h-2 rounded-full"
            style={{ 
              width: `${((data?.class_metrics.active_students_30d || 0) / (data?.class_metrics.total_students || 1)) * 100}%` 
            }}
          />
        </div>
      </motion.div>

      <motion.div
        className="bg-gray-900/80 rounded-lg p-6"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
      >
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-500/20 rounded-lg">
              <Target className="w-6 h-6 text-blue-400" />
            </div>
            <div>
              <p className="text-gray-400 text-sm">Precisión Promedio</p>
              <p className="text-white text-2xl font-bold">
                {((data?.class_metrics.avg_class_accuracy || 0) * 100).toFixed(1)}%
              </p>
            </div>
          </div>
          <div className="flex items-center gap-1 text-green-400 text-sm">
            <TrendingUp className="w-4 h-4" />
            <span>+{data?.class_metrics.improvement_rate}%</span>
          </div>
        </div>
      </motion.div>

      <motion.div
        className="bg-gray-900/80 rounded-lg p-6"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
      >
        <div className="flex items-center gap-3 mb-3">
          <div className="p-2 bg-green-500/20 rounded-lg">
            <BarChart3 className="w-6 h-6 text-green-400" />
          </div>
          <div>
            <p className="text-gray-400 text-sm">Batallas Completadas</p>
            <p className="text-white text-2xl font-bold">{data?.class_metrics.total_battles_completed}</p>
          </div>
        </div>
      </motion.div>

      <motion.div
        className="bg-gray-900/80 rounded-lg p-6"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
      >
        <div className="flex items-center gap-3 mb-3">
          <div className="p-2 bg-orange-500/20 rounded-lg">
            <Clock className="w-6 h-6 text-orange-400" />
          </div>
          <div>
            <p className="text-gray-400 text-sm">Tiempo Promedio</p>
            <p className="text-white text-2xl font-bold">
              {Math.floor((data?.class_metrics.avg_session_duration || 0) / 60)}min
            </p>
          </div>
        </div>
      </motion.div>
    </div>
  );

  const renderStudentList = () => (
    <motion.div
      className="bg-gray-900/80 rounded-lg p-6"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.4 }}
    >
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-xl font-semibold text-white flex items-center gap-2">
          <Users className="w-6 h-6 text-purple-400" />
          Lista de Estudiantes
        </h3>
        
        <div className="flex items-center gap-4">
          {/* Search */}
          <div className="relative">
            <Search className="w-4 h-4 text-gray-400 absolute left-3 top-1/2 transform -translate-y-1/2" />
            <input
              type="text"
              placeholder="Buscar estudiante..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="bg-gray-800 text-white rounded-lg pl-10 pr-4 py-2 text-sm border border-gray-700 focus:border-purple-500 focus:outline-none"
            />
          </div>
          
          {/* Filter */}
          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
            className="bg-gray-800 text-white rounded-lg px-3 py-2 text-sm border border-gray-700 focus:border-purple-500 focus:outline-none"
          >
            <option value="all">Todos</option>
            <option value="excellent">Excelente</option>
            <option value="good">Bueno</option>
            <option value="needs_attention">Necesita Atención</option>
            <option value="inactive">Inactivo</option>
          </select>
          
          {/* Export */}
          <button className="bg-purple-600 hover:bg-purple-700 text-white rounded-lg px-4 py-2 text-sm flex items-center gap-2 transition-colors">
            <Download className="w-4 h-4" />
            Exportar
          </button>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-gray-700">
              <th className="text-left text-gray-400 text-sm font-semibold py-3">Estudiante</th>
              <th className="text-left text-gray-400 text-sm font-semibold py-3">Estado</th>
              <th className="text-center text-gray-400 text-sm font-semibold py-3">Precisión</th>
              <th className="text-center text-gray-400 text-sm font-semibold py-3">Batallas</th>
              <th className="text-center text-gray-400 text-sm font-semibold py-3">Nivel</th>
              <th className="text-center text-gray-400 text-sm font-semibold py-3">Última Actividad</th>
              <th className="text-center text-gray-400 text-sm font-semibold py-3">Acciones</th>
            </tr>
          </thead>
          <tbody>
            {filteredStudents.map((student, index) => (
              <tr key={student.student_id} className="border-b border-gray-800 hover:bg-gray-800/50">
                <td className="py-4">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-purple-500/20 rounded-full flex items-center justify-center">
                      <span className="text-purple-400 font-semibold">
                        {student.student_name.split(' ').map(n => n[0]).join('')}
                      </span>
                    </div>
                    <div>
                      <p className="text-white font-semibold">{student.student_name}</p>
                      <p className="text-gray-400 text-sm">{student.experience} EXP</p>
                    </div>
                  </div>
                </td>
                <td className="py-4">
                  <span className={`px-3 py-1 rounded-full text-xs font-semibold ${getStatusColor(student.status)}`}>
                    {getStatusLabel(student.status)}
                  </span>
                </td>
                <td className="py-4 text-center">
                  <span className="text-white font-semibold">
                    {(student.accuracy * 100).toFixed(1)}%
                  </span>
                </td>
                <td className="py-4 text-center text-white">{student.battles_completed}</td>
                <td className="py-4 text-center">
                  <div className="flex items-center justify-center gap-2">
                    <span className="text-white font-semibold">{student.level}</span>
                    <span className={`px-2 py-1 rounded text-xs font-semibold ${
                      student.rank === 'S' ? 'bg-yellow-500/20 text-yellow-400' :
                      student.rank === 'A' ? 'bg-purple-500/20 text-purple-400' :
                      student.rank === 'B' ? 'bg-blue-500/20 text-blue-400' :
                      student.rank === 'C' ? 'bg-green-500/20 text-green-400' :
                      'bg-gray-500/20 text-gray-400'
                    }`}>
                      {student.rank}
                    </span>
                  </div>
                </td>
                <td className="py-4 text-center text-gray-400 text-sm">
                  {new Date(student.last_activity).toLocaleDateString()}
                </td>
                <td className="py-4 text-center">
                  <button
                    onClick={() => setSelectedStudent(student.student_id)}
                    className="bg-blue-600 hover:bg-blue-700 text-white rounded-lg px-3 py-1 text-sm flex items-center gap-1 mx-auto transition-colors"
                  >
                    <Eye className="w-4 h-4" />
                    Ver Detalles
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </motion.div>
  );

  const renderSubjectPerformance = () => (
    <motion.div
      className="bg-gray-900/80 rounded-lg p-6"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.5 }}
    >
      <h3 className="text-xl font-semibold text-white mb-6 flex items-center gap-2">
        <BookOpen className="w-6 h-6 text-blue-400" />
        Rendimiento por Materia
      </h3>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {data?.subject_performance.map((subject, index) => (
          <div key={index} className="bg-gray-800/50 rounded-lg p-4">
            <div className="flex items-center justify-between mb-3">
              <h4 className="font-semibold text-white">{subject.subject_name}</h4>
              <span className="text-sm text-gray-400">{subject.student_count} estudiantes</span>
            </div>
            
            <div className="space-y-3">
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-gray-400">Precisión Promedio</span>
                  <span className="text-white font-semibold">
                    {(subject.avg_accuracy * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="w-full bg-gray-700 rounded-full h-2">
                  <div 
                    className="bg-blue-500 h-2 rounded-full transition-all duration-500"
                    style={{ width: `${subject.avg_accuracy * 100}%` }}
                  />
                </div>
              </div>
              
              <div className="flex justify-between text-sm">
                <span className="text-gray-400">Preguntas Totales</span>
                <span className="text-white">{subject.total_questions}</span>
              </div>
              
              <div className="flex justify-between text-sm">
                <span className="text-gray-400">Dificultad Promedio</span>
                <span className="text-white">{subject.difficulty_level.toFixed(1)}</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </motion.div>
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
          onClick={fetchTeacherData}
          className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors"
        >
          Reintentar
        </button>
      </div>
    );
  }

  // Show individual student analytics if selected
  if (selectedStudent) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-4">
          <button
            onClick={() => setSelectedStudent(null)}
            className="bg-gray-700 hover:bg-gray-600 text-white rounded-lg px-4 py-2 text-sm transition-colors"
          >
            ← Volver al Dashboard
          </button>
          <h2 className="text-2xl font-bold text-white">
            Análisis Individual - {data?.student_summaries.find(s => s.student_id === selectedStudent)?.student_name}
          </h2>
        </div>
        <StudentProgressAnalytics studentId={selectedStudent} isTeacherView={true} />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-3xl font-bold text-white flex items-center gap-2">
          <Brain className="w-8 h-8 text-purple-400" />
          Dashboard del Profesor
        </h2>
        
        <div className="flex items-center gap-4">
          <button className="bg-purple-600 hover:bg-purple-700 text-white rounded-lg px-4 py-2 text-sm flex items-center gap-2 transition-colors">
            <Settings className="w-4 h-4" />
            Configurar Clase
          </button>
        </div>
      </div>

      {/* Class Metrics */}
      {renderClassMetrics()}

      {/* Subject Performance */}
      {renderSubjectPerformance()}

      {/* Student List */}
      {renderStudentList()}

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <motion.div
          className="bg-gradient-to-r from-green-900/30 to-green-700/30 rounded-lg p-6 border border-green-500/30"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6 }}
        >
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <Star className="w-5 h-5 text-green-400" />
            Estudiantes Destacados
          </h3>
          
          <div className="space-y-3">
            {data?.top_performers.slice(0, 3).map((student, index) => (
              <div key={student.student_id} className="flex items-center justify-between bg-gray-800/50 rounded-lg p-3">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 bg-green-500/20 rounded-full flex items-center justify-center">
                    <span className="text-green-400 text-sm font-semibold">{index + 1}</span>
                  </div>
                  <span className="text-white font-semibold">{student.student_name}</span>
                </div>
                <span className="text-green-400 font-semibold">
                  {(student.accuracy * 100).toFixed(1)}%
                </span>
              </div>
            ))}
          </div>
        </motion.div>

        <motion.div
          className="bg-gradient-to-r from-orange-900/30 to-orange-700/30 rounded-lg p-6 border border-orange-500/30"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.7 }}
        >
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-orange-400" />
            Requieren Atención
          </h3>
          
          <div className="space-y-3">
            {data?.students_needing_help.slice(0, 3).map((student, index) => (
              <div key={student.student_id} className="flex items-center justify-between bg-gray-800/50 rounded-lg p-3">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 bg-orange-500/20 rounded-full flex items-center justify-center">
                    <AlertTriangle className="w-4 h-4 text-orange-400" />
                  </div>
                  <span className="text-white font-semibold">{student.student_name}</span>
                </div>
                <span className="text-orange-400 font-semibold">
                  {(student.accuracy * 100).toFixed(1)}%
                </span>
              </div>
            ))}
          </div>
        </motion.div>
      </div>
    </div>
  );
}