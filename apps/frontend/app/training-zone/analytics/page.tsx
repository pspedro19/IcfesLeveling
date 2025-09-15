'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { 
  BarChart3, 
  TrendingUp, 
  Calendar, 
  Clock, 
  Target, 
  Brain, 
  Zap,
  ArrowLeft,
  Download,
  Filter,
  RefreshCw,
  Trophy,
  Star,
  Timer,
  CheckCircle,
  BookOpen,
  RotateCcw
} from "lucide-react";

interface AnalyticsData {
  overview: {
    total_sessions: number;
    total_questions: number;
    total_correct: number;
    average_accuracy: number;
    current_streak: number;
    mastery_level: number;
    time_spent_hours: number;
    improvement_rate: number;
  };
  by_mode: {
    [key: string]: {
      sessions: number;
      questions: number;
      correct: number;
      accuracy: number;
      avg_time_minutes: number;
    };
  };
  by_difficulty: {
    [key: string]: {
      attempted: number;
      correct: number;
      accuracy: number;
      improvement_trend: number;
    };
  };
  weekly_progress: Array<{
    week: string;
    sessions: number;
    accuracy: number;
    mastery_gained: number;
  }>;
  mastery_progression: Array<{
    date: string;
    mastery_level: number;
    questions_mastered: number;
  }>;
  spaced_repetition_insights: {
    questions_due_today: number;
    questions_overdue: number;
    average_retention_rate: number;
    optimal_review_frequency: number;
  };
  learning_insights: {
    strongest_areas: string[];
    areas_for_improvement: string[];
    recommended_study_time: number;
    predicted_mastery_date: string;
  };
}

export default function TrainingZoneAnalyticsPage() {
  const [analyticsData, setAnalyticsData] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedPeriod, setSelectedPeriod] = useState('current_month');
  const [selectedSubject, setSelectedSubject] = useState('1');

  // Simulated subjects
  const subjects = [
    { id: '1', name: 'Matemáticas' },
    { id: '2', name: 'Ciencias Naturales' },
    { id: '3', name: 'Lenguaje' },
    { id: '4', name: 'Ciencias Sociales' },
    { id: '5', name: 'Inglés' }
  ];

  const periods = [
    { value: 'current_month', label: 'Este mes' },
    { value: 'last_month', label: 'Mes anterior' },
    { value: 'last_3_months', label: 'Últimos 3 meses' },
    { value: 'all_time', label: 'Todo el tiempo' }
  ];

  useEffect(() => {
    loadAnalyticsData();
  }, [selectedSubject, selectedPeriod]);

  const loadAnalyticsData = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`/api/v1/training-zone/analytics/${selectedSubject}?period=${selectedPeriod}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      
      if (!response.ok) {
        throw new Error('Error al cargar analíticas');
      }
      
      const data = await response.json();
      
      // Mock additional data for comprehensive analytics
      const enhancedData: AnalyticsData = {
        overview: {
          total_sessions: data.analytics.overview.total_sessions || 24,
          total_questions: data.analytics.overview.total_questions || 156,
          total_correct: data.analytics.overview.total_correct || 127,
          average_accuracy: data.analytics.overview.average_accuracy || 81.4,
          current_streak: data.analytics.overview.current_streak || 5,
          mastery_level: data.analytics.overview.mastery_level || 67.3,
          time_spent_hours: 12.5,
          improvement_rate: 15.2
        },
        by_mode: data.analytics.by_mode || {
          recovery: { sessions: 8, questions: 58, correct: 47, accuracy: 81.0, avg_time_minutes: 28 },
          sprint: { sessions: 6, questions: 35, correct: 29, accuracy: 82.9, avg_time_minutes: 9 },
          spaced_rep: { sessions: 5, questions: 32, correct: 28, accuracy: 87.5, avg_time_minutes: 22 },
          full_review: { sessions: 3, questions: 21, correct: 16, accuracy: 76.2, avg_time_minutes: 45 },
          monthly_focus: { sessions: 2, questions: 10, correct: 7, accuracy: 70.0, avg_time_minutes: 32 }
        },
        by_difficulty: {
          easy: { attempted: 45, correct: 42, accuracy: 93.3, improvement_trend: 5.2 },
          medium: { attempted: 67, correct: 54, accuracy: 80.6, improvement_trend: 12.1 },
          hard: { attempted: 44, correct: 31, accuracy: 70.5, improvement_trend: 18.3 }
        },
        weekly_progress: [
          { week: 'Semana 1', sessions: 3, accuracy: 75.2, mastery_gained: 8 },
          { week: 'Semana 2', sessions: 5, accuracy: 78.9, mastery_gained: 12 },
          { week: 'Semana 3', sessions: 7, accuracy: 81.4, mastery_gained: 15 },
          { week: 'Semana 4', sessions: 6, accuracy: 83.1, mastery_gained: 11 }
        ],
        mastery_progression: [
          { date: '2024-01-01', mastery_level: 45.2, questions_mastered: 28 },
          { date: '2024-01-08', mastery_level: 52.8, questions_mastered: 33 },
          { date: '2024-01-15', mastery_level: 59.1, questions_mastered: 37 },
          { date: '2024-01-22', mastery_level: 64.5, questions_mastered: 40 },
          { date: '2024-01-29', mastery_level: 67.3, questions_mastered: 42 }
        ],
        spaced_repetition_insights: {
          questions_due_today: 8,
          questions_overdue: 3,
          average_retention_rate: 78.5,
          optimal_review_frequency: 3.2
        },
        learning_insights: {
          strongest_areas: ['Álgebra básica', 'Geometría plana', 'Estadística descriptiva'],
          areas_for_improvement: ['Cálculo diferencial', 'Trigonometría', 'Probabilidad'],
          recommended_study_time: 45,
          predicted_mastery_date: '2024-03-15'
        }
      };
      
      setAnalyticsData(enhancedData);
    } catch (err) {
      console.error('Error loading analytics:', err);
      setError('Error al cargar las analíticas. Verifica tu conexión.');
    } finally {
      setLoading(false);
    }
  };

  const exportAnalytics = () => {
    if (!analyticsData) return;
    
    const exportData = {
      subject: subjects.find(s => s.id === selectedSubject)?.name,
      period: periods.find(p => p.value === selectedPeriod)?.label,
      generated_at: new Date().toISOString(),
      ...analyticsData
    };
    
    const dataStr = JSON.stringify(exportData, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `training-zone-analytics-${selectedSubject}-${selectedPeriod}.json`;
    link.click();
    
    URL.revokeObjectURL(url);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-6">
        <div className="max-w-7xl mx-auto">
          <div className="flex items-center justify-center h-64">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          </div>
        </div>
      </div>
    );
  }

  if (error || !analyticsData) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-6">
        <div className="max-w-7xl mx-auto">
          <Card className="max-w-2xl mx-auto mt-20">
            <CardContent className="p-6 text-center">
              <p className="text-gray-600">{error || 'No se pudieron cargar las analíticas'}</p>
              <Button onClick={() => window.history.back()} className="mt-4">
                <ArrowLeft className="h-4 w-4 mr-2" />
                Volver
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Button
                onClick={() => window.history.back()}
                variant="outline"
                size="sm"
              >
                <ArrowLeft className="h-4 w-4 mr-2" />
                Volver
              </Button>
              <div className="flex items-center gap-3">
                <div className="h-10 w-10 rounded-lg bg-gradient-to-br from-purple-500 to-blue-600 flex items-center justify-center">
                  <BarChart3 className="h-6 w-6 text-white" />
                </div>
                <div>
                  <h1 className="text-2xl font-bold text-gray-900">Analíticas del Training Zone</h1>
                  <p className="text-sm text-gray-600">Análisis detallado de tu progreso</p>
                </div>
              </div>
            </div>
            
            <div className="flex items-center gap-3">
              <select 
                value={selectedSubject}
                onChange={(e) => setSelectedSubject(e.target.value)}
                className="border border-gray-300 rounded-md px-3 py-1 text-sm"
              >
                {subjects.map((subject) => (
                  <option key={subject.id} value={subject.id}>
                    {subject.name}
                  </option>
                ))}
              </select>
              
              <select 
                value={selectedPeriod}
                onChange={(e) => setSelectedPeriod(e.target.value)}
                className="border border-gray-300 rounded-md px-3 py-1 text-sm"
              >
                {periods.map((period) => (
                  <option key={period.value} value={period.value}>
                    {period.label}
                  </option>
                ))}
              </select>
              
              <Button onClick={loadAnalyticsData} variant="outline" size="sm">
                <RefreshCw className="h-4 w-4 mr-2" />
                Actualizar
              </Button>
              
              <Button onClick={exportAnalytics} variant="outline" size="sm">
                <Download className="h-4 w-4 mr-2" />
                Exportar
              </Button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto p-6">
        {/* Overview Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Sesiones Totales</p>
                  <p className="text-2xl font-bold text-blue-600">{analyticsData.overview.total_sessions}</p>
                  <p className="text-xs text-gray-500">{analyticsData.overview.time_spent_hours}h tiempo total</p>
                </div>
                <Calendar className="h-8 w-8 text-blue-500" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Precisión Promedio</p>
                  <p className="text-2xl font-bold text-green-600">{analyticsData.overview.average_accuracy.toFixed(1)}%</p>
                  <p className="text-xs text-green-600">+{analyticsData.overview.improvement_rate.toFixed(1)}% mejora</p>
                </div>
                <Target className="h-8 w-8 text-green-500" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Nivel de Dominio</p>
                  <p className="text-2xl font-bold text-purple-600">{analyticsData.overview.mastery_level.toFixed(1)}%</p>
                  <Progress value={analyticsData.overview.mastery_level} className="mt-2 h-2" />
                </div>
                <Brain className="h-8 w-8 text-purple-500" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Racha Actual</p>
                  <p className="text-2xl font-bold text-orange-600">{analyticsData.overview.current_streak}</p>
                  <p className="text-xs text-gray-500">días consecutivos</p>
                </div>
                <Star className="h-8 w-8 text-orange-500" />
              </div>
            </CardContent>
          </Card>
        </div>

        <Tabs defaultValue="performance" className="space-y-6">
          <TabsList className="grid w-full grid-cols-5 lg:w-3/4">
            <TabsTrigger value="performance">Rendimiento</TabsTrigger>
            <TabsTrigger value="progress">Progreso</TabsTrigger>
            <TabsTrigger value="spaced-rep">Repetición</TabsTrigger>
            <TabsTrigger value="insights">Insights</TabsTrigger>
            <TabsTrigger value="detailed">Detallado</TabsTrigger>
          </TabsList>

          {/* Performance Tab */}
          <TabsContent value="performance" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Performance by Mode */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Zap className="h-5 w-5" />
                    Rendimiento por Modo
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {Object.entries(analyticsData.by_mode).map(([mode, stats]) => (
                      <div key={mode} className="space-y-2">
                        <div className="flex justify-between items-center">
                          <span className="text-sm font-medium capitalize">{mode.replace('_', ' ')}</span>
                          <Badge variant="outline">{stats.sessions} sesiones</Badge>
                        </div>
                        <div className="flex justify-between text-xs text-gray-600">
                          <span>Precisión: {stats.accuracy.toFixed(1)}%</span>
                          <span>Tiempo: {stats.avg_time_minutes}min</span>
                        </div>
                        <Progress value={stats.accuracy} className="h-2" />
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>

              {/* Performance by Difficulty */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <TrendingUp className="h-5 w-5" />
                    Rendimiento por Dificultad
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {Object.entries(analyticsData.by_difficulty).map(([difficulty, stats]) => (
                      <div key={difficulty} className="space-y-2">
                        <div className="flex justify-between items-center">
                          <span className="text-sm font-medium capitalize">{difficulty}</span>
                          <div className="flex items-center gap-2">
                            <span className="text-xs text-gray-600">{stats.correct}/{stats.attempted}</span>
                            {stats.improvement_trend > 0 && (
                              <Badge variant="outline" className="text-green-600">
                                +{stats.improvement_trend.toFixed(1)}%
                              </Badge>
                            )}
                          </div>
                        </div>
                        <Progress value={stats.accuracy} className="h-2" />
                        <div className="text-xs text-gray-600">
                          Precisión: {stats.accuracy.toFixed(1)}%
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Weekly Progress Chart */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Calendar className="h-5 w-5" />
                  Progreso Semanal
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                  {analyticsData.weekly_progress.map((week, index) => (
                    <div key={index} className="text-center p-4 bg-gray-50 rounded-lg">
                      <p className="text-sm font-medium text-gray-700">{week.week}</p>
                      <p className="text-2xl font-bold text-blue-600">{week.sessions}</p>
                      <p className="text-xs text-gray-500">sesiones</p>
                      <p className="text-sm text-green-600 mt-1">{week.accuracy.toFixed(1)}% precisión</p>
                      <p className="text-xs text-purple-600">+{week.mastery_gained} dominadas</p>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Progress Tab */}
          <TabsContent value="progress" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <TrendingUp className="h-5 w-5" />
                  Progresión de Dominio
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {analyticsData.mastery_progression.map((point, index) => (
                    <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                      <div>
                        <p className="text-sm font-medium">{new Date(point.date).toLocaleDateString()}</p>
                        <p className="text-xs text-gray-600">{point.questions_mastered} preguntas dominadas</p>
                      </div>
                      <div className="text-right">
                        <p className="text-lg font-bold text-blue-600">{point.mastery_level.toFixed(1)}%</p>
                        {index > 0 && (
                          <p className="text-xs text-green-600">
                            +{(point.mastery_level - analyticsData.mastery_progression[index-1].mastery_level).toFixed(1)}%
                          </p>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Spaced Repetition Tab */}
          <TabsContent value="spaced-rep" className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <RotateCcw className="h-5 w-5" />
                    Estado de Repetición Espaciada
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="text-center p-3 bg-blue-50 rounded-lg">
                      <p className="text-2xl font-bold text-blue-600">
                        {analyticsData.spaced_repetition_insights.questions_due_today}
                      </p>
                      <p className="text-xs text-blue-700">Para hoy</p>
                    </div>
                    <div className="text-center p-3 bg-red-50 rounded-lg">
                      <p className="text-2xl font-bold text-red-600">
                        {analyticsData.spaced_repetition_insights.questions_overdue}
                      </p>
                      <p className="text-xs text-red-700">Atrasadas</p>
                    </div>
                  </div>
                  <div className="mt-4 space-y-2">
                    <div className="flex justify-between text-sm">
                      <span>Tasa de retención promedio:</span>
                      <span className="font-medium">{analyticsData.spaced_repetition_insights.average_retention_rate.toFixed(1)}%</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span>Frecuencia óptima de repaso:</span>
                      <span className="font-medium">{analyticsData.spaced_repetition_insights.optimal_review_frequency.toFixed(1)} días</span>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Recomendaciones</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
                      <p className="text-sm font-medium text-blue-800">Sesión recomendada hoy:</p>
                      <p className="text-xs text-blue-700">Modo Repetición Espaciada (25 min)</p>
                    </div>
                    <div className="p-3 bg-green-50 border border-green-200 rounded-lg">
                      <p className="text-sm font-medium text-green-800">Progreso excelente:</p>
                      <p className="text-xs text-green-700">Tu retención está por encima del promedio</p>
                    </div>
                    {analyticsData.spaced_repetition_insights.questions_overdue > 0 && (
                      <div className="p-3 bg-orange-50 border border-orange-200 rounded-lg">
                        <p className="text-sm font-medium text-orange-800">Atención necesaria:</p>
                        <p className="text-xs text-orange-700">Tienes preguntas atrasadas para repaso</p>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* Insights Tab */}
          <TabsContent value="insights" className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Trophy className="h-5 w-5" />
                    Áreas Más Fuertes
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    {analyticsData.learning_insights.strongest_areas.map((area, index) => (
                      <div key={index} className="flex items-center gap-2">
                        <CheckCircle className="h-4 w-4 text-green-500" />
                        <span className="text-sm">{area}</span>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Target className="h-5 w-5" />
                    Áreas de Mejora
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    {analyticsData.learning_insights.areas_for_improvement.map((area, index) => (
                      <div key={index} className="flex items-center gap-2">
                        <Clock className="h-4 w-4 text-orange-500" />
                        <span className="text-sm">{area}</span>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </div>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Brain className="h-5 w-5" />
                  Proyecciones de Aprendizaje
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="text-center p-4 bg-purple-50 rounded-lg">
                    <p className="text-sm font-medium text-purple-700">Tiempo de estudio recomendado</p>
                    <p className="text-2xl font-bold text-purple-600">{analyticsData.learning_insights.recommended_study_time} min/día</p>
                  </div>
                  <div className="text-center p-4 bg-green-50 rounded-lg">
                    <p className="text-sm font-medium text-green-700">Fecha estimada de dominio</p>
                    <p className="text-lg font-bold text-green-600">
                      {new Date(analyticsData.learning_insights.predicted_mastery_date).toLocaleDateString()}
                    </p>
                  </div>
                  <div className="text-center p-4 bg-blue-50 rounded-lg">
                    <p className="text-sm font-medium text-blue-700">Velocidad de aprendizaje</p>
                    <p className="text-2xl font-bold text-blue-600">Alta</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Detailed Tab */}
          <TabsContent value="detailed" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Métricas Detalladas</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    <div className="p-4 border rounded-lg">
                      <p className="text-sm font-medium text-gray-700">Preguntas Totales</p>
                      <p className="text-2xl font-bold">{analyticsData.overview.total_questions}</p>
                    </div>
                    <div className="p-4 border rounded-lg">
                      <p className="text-sm font-medium text-gray-700">Respuestas Correctas</p>
                      <p className="text-2xl font-bold text-green-600">{analyticsData.overview.total_correct}</p>
                    </div>
                    <div className="p-4 border rounded-lg">
                      <p className="text-sm font-medium text-gray-700">Tiempo Total Estudiado</p>
                      <p className="text-2xl font-bold text-blue-600">{analyticsData.overview.time_spent_hours}h</p>
                    </div>
                  </div>
                  
                  <div className="mt-6">
                    <h4 className="text-lg font-semibold mb-4">Desglose por Modo de Entrenamiento</h4>
                    <div className="overflow-x-auto">
                      <table className="min-w-full border border-gray-200 rounded-lg">
                        <thead className="bg-gray-50">
                          <tr>
                            <th className="px-4 py-2 text-left text-sm font-medium text-gray-700">Modo</th>
                            <th className="px-4 py-2 text-left text-sm font-medium text-gray-700">Sesiones</th>
                            <th className="px-4 py-2 text-left text-sm font-medium text-gray-700">Preguntas</th>
                            <th className="px-4 py-2 text-left text-sm font-medium text-gray-700">Correctas</th>
                            <th className="px-4 py-2 text-left text-sm font-medium text-gray-700">Precisión</th>
                            <th className="px-4 py-2 text-left text-sm font-medium text-gray-700">Tiempo Promedio</th>
                          </tr>
                        </thead>
                        <tbody>
                          {Object.entries(analyticsData.by_mode).map(([mode, stats]) => (
                            <tr key={mode} className="border-t">
                              <td className="px-4 py-2 text-sm font-medium capitalize">{mode.replace('_', ' ')}</td>
                              <td className="px-4 py-2 text-sm">{stats.sessions}</td>
                              <td className="px-4 py-2 text-sm">{stats.questions}</td>
                              <td className="px-4 py-2 text-sm text-green-600">{stats.correct}</td>
                              <td className="px-4 py-2 text-sm">{stats.accuracy.toFixed(1)}%</td>
                              <td className="px-4 py-2 text-sm">{stats.avg_time_minutes} min</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}