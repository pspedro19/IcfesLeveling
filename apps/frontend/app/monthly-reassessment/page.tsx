'use client';
import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Calendar, Target, TrendingUp, Clock, CheckCircle, AlertCircle, BookOpen, Trophy, BarChart3, RefreshCw } from 'lucide-react';

interface Subject {
  id: string;
  name: string;
  description: string;
  icon_url: string;
  color: string;
  eligible: boolean;
  reason: string;
  days_since_initial: number;
  initial_score: number;
}

interface Reassessment {
  id: string;
  subject_id: string;
  subject_name: string;
  test_type: string;
  reassessment_type: string;
  score_percentage: number;
  questions_answered: number;
  correct_answers: number;
  time_spent_seconds: number;
  days_since_initial: number;
  comparison_with_initial: any;
  status: string;
  created_at: string;
  completed_at: string;
}

interface ReassessmentSummary {
  subject_id: string;
  total_reassessments: number;
  average_improvement: number;
  best_improvement: number;
  trend: string;
}

export default function MonthlyReassessmentPage() {
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [reassessments, setReassessments] = useState<Reassessment[]>([]);
  const [summaries, setSummaries] = useState<ReassessmentSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState('available');

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      
      // Obtener materias disponibles
      const subjectsResponse = await fetch('/api/v1/monthly-reassessment/available-subjects', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      
      if (subjectsResponse.ok) {
        const subjectsData = await subjectsResponse.json();
        setSubjects(subjectsData);
      }

      // Obtener reevaluaciones del usuario
      const reassessmentsResponse = await fetch('/api/v1/monthly-reassessment/user-reassessments', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      
      if (reassessmentsResponse.ok) {
        const reassessmentsData = await reassessmentsResponse.json();
        setReassessments(reassessmentsData);
      }

      setLoading(false);
    } catch (err) {
      setError('Error cargando datos de reevaluación');
      setLoading(false);
    }
  };

  const startReassessment = async (subjectId: string) => {
    try {
      const response = await fetch('/api/v1/monthly-reassessment/create', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          subject_id: subjectId,
          user_id: localStorage.getItem('userId')
        })
      });

      if (response.ok) {
        const reassessment = await response.json();
        // Redirigir al test de reevaluación
        window.location.href = `/monthly-reassessment/test/${reassessment.id}`;
      } else {
        const error = await response.json();
        alert(`Error: ${error.detail}`);
      }
    } catch (err) {
      alert('Error iniciando reevaluación');
    }
  };

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'improving':
        return <TrendingUp className="w-5 h-5 text-green-500" />;
      case 'declining':
        return <TrendingUp className="w-5 h-5 text-red-500 rotate-180" />;
      default:
        return <BarChart3 className="w-5 h-5 text-yellow-500" />;
    }
  };

  const getTrendText = (trend: string) => {
    switch (trend) {
      case 'improving':
        return 'Mejorando';
      case 'declining':
        return 'Deteriorando';
      default:
        return 'Estable';
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 flex items-center justify-center">
        <div className="text-white text-center">
          <RefreshCw className="w-8 h-8 animate-spin mx-auto mb-4" />
          <p>Cargando reevaluaciones mensuales...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 flex items-center justify-center">
        <div className="text-white text-center">
          <AlertCircle className="w-8 h-8 mx-auto mb-4" />
          <p>{error}</p>
        </div>
      </div>
    );
  }

  const eligibleSubjects = subjects.filter(s => s.eligible);
  const ineligibleSubjects = subjects.filter(s => !s.eligible);

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-8"
        >
          <h1 className="text-4xl font-bold text-white mb-4">
            Reevaluación Mensual
          </h1>
          <p className="text-gray-300 text-lg">
            Evalúa tu progreso después de 30 días de estudio
          </p>
        </motion.div>

        {/* Tabs */}
        <div className="flex justify-center mb-8">
          <div className="bg-gray-800 rounded-lg p-1">
            <button
              onClick={() => setActiveTab('available')}
              className={`px-6 py-2 rounded-md transition-colors ${
                activeTab === 'available'
                  ? 'bg-blue-600 text-white'
                  : 'text-gray-300 hover:text-white'
              }`}
            >
              Disponibles ({eligibleSubjects.length})
            </button>
            <button
              onClick={() => setActiveTab('history')}
              className={`px-6 py-2 rounded-md transition-colors ${
                activeTab === 'history'
                  ? 'bg-blue-600 text-white'
                  : 'text-gray-300 hover:text-white'
              }`}
            >
              Historial ({reassessments.length})
            </button>
          </div>
        </div>

        {/* Content */}
        {activeTab === 'available' && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="space-y-6"
          >
            {/* Materias elegibles */}
            {eligibleSubjects.length > 0 && (
              <div>
                <h2 className="text-2xl font-semibold text-white mb-4 flex items-center">
                  <CheckCircle className="w-6 h-6 text-green-500 mr-2" />
                  Listas para Reevaluación
                </h2>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {eligibleSubjects.map((subject) => (
                    <motion.div
                      key={subject.id}
                      whileHover={{ scale: 1.02 }}
                      className="bg-gray-800 rounded-lg p-6 border border-gray-700"
                    >
                      <div className="flex items-center justify-between mb-4">
                        <div className="flex items-center">
                          <div 
                            className="w-10 h-10 rounded-full mr-3"
                            style={{ backgroundColor: subject.color }}
                          />
                          <div>
                            <h3 className="text-white font-semibold">{subject.name}</h3>
                            <p className="text-gray-400 text-sm">{subject.description}</p>
                          </div>
                        </div>
                        <CheckCircle className="w-5 h-5 text-green-500" />
                      </div>
                      
                      <div className="space-y-2 mb-4">
                        <div className="flex justify-between text-sm">
                          <span className="text-gray-400">Días desde inicial:</span>
                          <span className="text-white">{subject.days_since_initial}</span>
                        </div>
                        <div className="flex justify-between text-sm">
                          <span className="text-gray-400">Puntaje inicial:</span>
                          <span className="text-white">{subject.initial_score}%</span>
                        </div>
                      </div>

                      <button
                        onClick={() => startReassessment(subject.id)}
                        className="w-full bg-blue-600 hover:bg-blue-700 text-white py-2 px-4 rounded-md transition-colors flex items-center justify-center"
                      >
                        <Target className="w-4 h-4 mr-2" />
                        Iniciar Reevaluación
                      </button>
                    </motion.div>
                  ))}
                </div>
              </div>
            )}

            {/* Materias no elegibles */}
            {ineligibleSubjects.length > 0 && (
              <div>
                <h2 className="text-2xl font-semibold text-white mb-4 flex items-center">
                  <AlertCircle className="w-6 h-6 text-yellow-500 mr-2" />
                  No Disponibles
                </h2>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {ineligibleSubjects.map((subject) => (
                    <motion.div
                      key={subject.id}
                      className="bg-gray-800 rounded-lg p-6 border border-gray-700 opacity-75"
                    >
                      <div className="flex items-center justify-between mb-4">
                        <div className="flex items-center">
                          <div 
                            className="w-10 h-10 rounded-full mr-3"
                            style={{ backgroundColor: subject.color }}
                          />
                          <div>
                            <h3 className="text-white font-semibold">{subject.name}</h3>
                            <p className="text-gray-400 text-sm">{subject.description}</p>
                          </div>
                        </div>
                        <AlertCircle className="w-5 h-5 text-yellow-500" />
                      </div>
                      
                      <div className="space-y-2 mb-4">
                        <div className="flex justify-between text-sm">
                          <span className="text-gray-400">Días desde inicial:</span>
                          <span className="text-white">{subject.days_since_initial || 'N/A'}</span>
                        </div>
                        <div className="flex justify-between text-sm">
                          <span className="text-gray-400">Puntaje inicial:</span>
                          <span className="text-white">{subject.initial_score || 'N/A'}%</span>
                        </div>
                      </div>

                      <div className="text-yellow-400 text-sm bg-yellow-900/20 p-3 rounded-md">
                        {subject.reason}
                      </div>
                    </motion.div>
                  ))}
                </div>
              </div>
            )}
          </motion.div>
        )}

        {activeTab === 'history' && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="space-y-6"
          >
            <h2 className="text-2xl font-semibold text-white mb-4 flex items-center">
              <BookOpen className="w-6 h-6 text-blue-500 mr-2" />
              Historial de Reevaluaciones
            </h2>

            {reassessments.length === 0 ? (
              <div className="text-center text-gray-400 py-8">
                <BookOpen className="w-12 h-12 mx-auto mb-4" />
                <p>No hay reevaluaciones realizadas aún</p>
              </div>
            ) : (
              <div className="space-y-4">
                {reassessments.map((reassessment) => (
                  <motion.div
                    key={reassessment.id}
                    whileHover={{ scale: 1.01 }}
                    className="bg-gray-800 rounded-lg p-6 border border-gray-700"
                  >
                    <div className="flex items-center justify-between mb-4">
                      <div>
                        <h3 className="text-white font-semibold text-lg">
                          {reassessment.subject_name}
                        </h3>
                        <p className="text-gray-400 text-sm">
                          {new Date(reassessment.created_at).toLocaleDateString()}
                        </p>
                      </div>
                      <div className="text-right">
                        <div className="text-2xl font-bold text-white">
                          {reassessment.score_percentage}%
                        </div>
                        <div className="text-sm text-gray-400">
                          {reassessment.correct_answers}/{reassessment.questions_answered} correctas
                        </div>
                      </div>
                    </div>

                    {reassessment.comparison_with_initial && (
                      <div className="bg-gray-700 rounded-lg p-4 mb-4">
                        <h4 className="text-white font-semibold mb-2">Comparación con Test Inicial</h4>
                        <div className="grid grid-cols-2 gap-4 text-sm">
                          <div>
                            <span className="text-gray-400">Puntaje inicial:</span>
                            <span className="text-white ml-2">
                              {reassessment.comparison_with_initial.initial_score}%
                            </span>
                          </div>
                          <div>
                            <span className="text-gray-400">Mejora:</span>
                            <span className={`ml-2 ${
                              reassessment.comparison_with_initial.improvement_percentage > 0 
                                ? 'text-green-500' 
                                : 'text-red-500'
                            }`}>
                              {reassessment.comparison_with_initial.improvement_percentage > 0 ? '+' : ''}
                              {reassessment.comparison_with_initial.improvement_percentage}%
                            </span>
                          </div>
                          <div>
                            <span className="text-gray-400">Días transcurridos:</span>
                            <span className="text-white ml-2">
                              {reassessment.days_since_initial}
                            </span>
                          </div>
                          <div>
                            <span className="text-gray-400">Tendencia:</span>
                            <span className="text-white ml-2 flex items-center">
                              {getTrendIcon(reassessment.comparison_with_initial.overall_trend)}
                              <span className="ml-1">
                                {getTrendText(reassessment.comparison_with_initial.overall_trend)}
                              </span>
                            </span>
                          </div>
                        </div>
                      </div>
                    )}

                    <div className="flex items-center justify-between text-sm text-gray-400">
                      <div className="flex items-center">
                        <Clock className="w-4 h-4 mr-1" />
                        {Math.floor(reassessment.time_spent_seconds / 60)} min
                      </div>
                      <div className="flex items-center">
                        <Trophy className="w-4 h-4 mr-1" />
                        {reassessment.status === 'completed' ? 'Completado' : 'En progreso'}
                      </div>
                    </div>
                  </motion.div>
                ))}
              </div>
            )}
          </motion.div>
        )}
      </div>
    </div>
  );
} 