'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { 
  Brain, 
  Target, 
  Timer, 
  Trophy, 
  BookOpen, 
  Zap, 
  RotateCcw,
  TrendingUp,
  Calendar,
  Play,
  Star,
  Clock,
  CheckCircle,
  AlertCircle,
  Video,
  Lightbulb
} from "lucide-react";

interface TrainingZoneData {
  training_zone_id: string;
  overview: {
    total_questions: number;
    mastered_questions: number;
    in_progress: number;
    mastery_percentage: number;
    due_for_review: number;
    current_streak: number;
    max_streak: number;
    total_sessions: number;
    overall_accuracy: number;
    improvement_rate: number;
    mastery_level: number;
  };
  recent_sessions: Array<{
    id: string;
    mode: string;
    questions_answered: number;
    correct_answers: number;
    accuracy: number;
    duration_minutes: number;
    started_at: string;
    status: string;
  }>;
  difficulty_performance: {
    [key: string]: {
      accuracy: number;
      avg_time: number;
    };
  };
  spaced_repetition: {
    due_today: number;
    overdue: number;
    mastered: number;
    in_learning: number;
  };
  monthly_rotation: {
    current_month: number;
    current_year: number;
    last_rotation: string;
    rotation_triggered_by_diagnostic: boolean;
  };
  recommended_modes: Array<{
    mode: string;
    reason: string;
    priority: string;
  }>;
}

interface TrainingMode {
  id: string;
  name: string;
  description: string;
  duration_minutes: number;
  question_limit: number;
  focus: string;
  icon: React.ComponentType;
  color: string;
}

const trainingModes: TrainingMode[] = [
  {
    id: 'recovery',
    name: 'Recovery Mode',
    description: '20 prioritized questions based on recency and severity',
    duration_minutes: 30,
    question_limit: 20,
    focus: 'Recent failures and high-priority questions',
    icon: Target,
    color: 'bg-blue-500'
  },
  {
    id: 'sprint',
    name: 'Sprint Mode',
    description: 'Quick 10-minute session with top 10 critical questions',
    duration_minutes: 10,
    question_limit: 10,
    focus: 'Critical errors that need immediate attention',
    icon: Zap,
    color: 'bg-red-500'
  },
  {
    id: 'full_review',
    name: 'Full Review',
    description: 'Comprehensive review of all failed questions',
    duration_minutes: 60,
    question_limit: 50,
    focus: 'Complete coverage of all learning gaps',
    icon: BookOpen,
    color: 'bg-green-500'
  },
  {
    id: 'spaced_rep',
    name: 'Spaced Repetition',
    description: 'Questions scheduled based on spaced repetition algorithm',
    duration_minutes: 25,
    question_limit: 15,
    focus: 'Optimized long-term retention',
    icon: Brain,
    color: 'bg-purple-500'
  },
  {
    id: 'monthly_focus',
    name: 'Monthly Focus',
    description: 'Focus on current month\'s failed questions',
    duration_minutes: 35,
    question_limit: 25,
    focus: 'Recent diagnostic failures',
    icon: Calendar,
    color: 'bg-orange-500'
  }
];

export default function TrainingZonePage() {
  const [selectedSubject, setSelectedSubject] = useState<string>('1'); // Default to first subject
  const [trainingData, setTrainingData] = useState<TrainingZoneData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState('dashboard');

  // Simulated subjects (you can fetch this from API)
  const subjects = [
    { id: '1', name: 'Matemáticas' },
    { id: '2', name: 'Ciencias Naturales' },
    { id: '3', name: 'Lenguaje' },
    { id: '4', name: 'Ciencias Sociales' },
    { id: '5', name: 'Inglés' }
  ];

  useEffect(() => {
    fetchTrainingZoneData();
  }, [selectedSubject]);

  const fetchTrainingZoneData = async () => {
    setLoading(true);
    setError(null);
    
    try {
      // This would be your actual API call
      const response = await fetch(`/api/v1/training-zone/dashboard/${selectedSubject}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      
      if (!response.ok) {
        if (response.status === 400) {
          // Training zone not initialized
          const errorData = await response.json();
          if (errorData.action_required === 'complete_diagnostic') {
            setError('Debes completar el diagnóstico de esta materia primero');
            return;
          }
        }
        throw new Error('Error al cargar datos del training zone');
      }
      
      const data = await response.json();
      setTrainingData(data);
    } catch (err) {
      console.error('Error fetching training zone data:', err);
      setError('Error al cargar los datos. Verifica tu conexión.');
    } finally {
      setLoading(false);
    }
  };

  const startTrainingSession = async (mode: string) => {
    try {
      const response = await fetch('/api/v1/training-zone/session/start', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          subject_id: selectedSubject,
          mode: mode
        })
      });

      if (!response.ok) {
        throw new Error('Error al iniciar sesión de entrenamiento');
      }

      const data = await response.json();
      
      // Redirect to training session page
      window.location.href = `/training-session/${data.session_id}`;
    } catch (err) {
      console.error('Error starting training session:', err);
      alert('Error al iniciar la sesión de entrenamiento');
    }
  };

  const initializeTrainingZone = async () => {
    try {
      const response = await fetch(`/api/v1/training-zone/initialize/${selectedSubject}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (!response.ok) {
        throw new Error('Error al inicializar training zone');
      }

      const data = await response.json();
      if (data.success) {
        await fetchTrainingZoneData();
      }
    } catch (err) {
      console.error('Error initializing training zone:', err);
      alert('Error al inicializar el training zone');
    }
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

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-6">
        <div className="max-w-7xl mx-auto">
          <Card className="max-w-2xl mx-auto mt-20">
            <CardHeader className="text-center">
              <CardTitle className="flex items-center justify-center gap-2 text-orange-600">
                <AlertCircle className="h-6 w-6" />
                Training Zone No Disponible
              </CardTitle>
            </CardHeader>
            <CardContent className="text-center space-y-4">
              <p className="text-gray-600">{error}</p>
              {error.includes('diagnóstico') && (
                <Button 
                  onClick={() => window.location.href = `/diagnostic/${selectedSubject}`}
                  className="bg-blue-600 hover:bg-blue-700"
                >
                  Ir al Diagnóstico
                </Button>
              )}
              <Button 
                onClick={initializeTrainingZone}
                variant="outline"
              >
                Inicializar Training Zone
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
              <div className="h-10 w-10 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
                <Brain className="h-6 w-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">Training Zone</h1>
                <p className="text-sm text-gray-600">Zona de entrenamiento personalizada</p>
              </div>
            </div>
            
            {/* Subject Selector */}
            <div className="flex items-center gap-2">
              <label htmlFor="subject" className="text-sm font-medium text-gray-700">
                Materia:
              </label>
              <select 
                id="subject"
                value={selectedSubject}
                onChange={(e) => setSelectedSubject(e.target.value)}
                className="border border-gray-300 rounded-md px-3 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {subjects.map((subject) => (
                  <option key={subject.id} value={subject.id}>
                    {subject.name}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto p-6">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <TabsList className="grid w-full grid-cols-4 lg:w-2/3">
            <TabsTrigger value="dashboard">Dashboard</TabsTrigger>
            <TabsTrigger value="modes">Modos</TabsTrigger>
            <TabsTrigger value="progress">Progreso</TabsTrigger>
            <TabsTrigger value="analytics">Analíticas</TabsTrigger>
          </TabsList>

          {/* Dashboard Tab */}
          <TabsContent value="dashboard" className="space-y-6">
            {/* Overview Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <Card>
                <CardContent className="p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-gray-600">Preguntas Totales</p>
                      <p className="text-2xl font-bold text-gray-900">{trainingData?.overview.total_questions}</p>
                    </div>
                    <BookOpen className="h-8 w-8 text-blue-500" />
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-gray-600">Dominadas</p>
                      <p className="text-2xl font-bold text-green-600">{trainingData?.overview.mastered_questions}</p>
                    </div>
                    <Trophy className="h-8 w-8 text-green-500" />
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-gray-600">Por Revisar</p>
                      <p className="text-2xl font-bold text-orange-600">{trainingData?.overview.due_for_review}</p>
                    </div>
                    <Clock className="h-8 w-8 text-orange-500" />
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-gray-600">Racha Actual</p>
                      <p className="text-2xl font-bold text-purple-600">{trainingData?.overview.current_streak}</p>
                    </div>
                    <Star className="h-8 w-8 text-purple-500" />
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Progress Overview */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <TrendingUp className="h-5 w-5" />
                    Progreso de Dominio
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span>Dominio General</span>
                      <span>{trainingData?.overview.mastery_percentage.toFixed(1)}%</span>
                    </div>
                    <Progress value={trainingData?.overview.mastery_percentage} className="h-2" />
                  </div>
                  
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span>Precisión</span>
                      <span>{trainingData?.overview.overall_accuracy.toFixed(1)}%</span>
                    </div>
                    <Progress value={trainingData?.overview.overall_accuracy} className="h-2" />
                  </div>
                  
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span>Tasa de Mejora</span>
                      <span>{trainingData?.overview.improvement_rate.toFixed(1)}%</span>
                    </div>
                    <Progress value={trainingData?.overview.improvement_rate} className="h-2" />
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <RotateCcw className="h-5 w-5" />
                    Repetición Espaciada
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="text-center p-3 bg-blue-50 rounded-lg">
                      <p className="text-2xl font-bold text-blue-600">{trainingData?.spaced_repetition.due_today}</p>
                      <p className="text-xs text-blue-700">Hoy</p>
                    </div>
                    <div className="text-center p-3 bg-red-50 rounded-lg">
                      <p className="text-2xl font-bold text-red-600">{trainingData?.spaced_repetition.overdue}</p>
                      <p className="text-xs text-red-700">Atrasadas</p>
                    </div>
                    <div className="text-center p-3 bg-green-50 rounded-lg">
                      <p className="text-2xl font-bold text-green-600">{trainingData?.spaced_repetition.mastered}</p>
                      <p className="text-xs text-green-700">Dominadas</p>
                    </div>
                    <div className="text-center p-3 bg-orange-50 rounded-lg">
                      <p className="text-2xl font-bold text-orange-600">{trainingData?.spaced_repetition.in_learning}</p>
                      <p className="text-xs text-orange-700">Aprendiendo</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Recent Sessions */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Timer className="h-5 w-5" />
                  Sesiones Recientes
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {trainingData?.recent_sessions.map((session, index) => (
                    <div key={session.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                      <div className="flex items-center gap-3">
                        <Badge variant={session.status === 'completed' ? 'default' : 'secondary'}>
                          {session.mode}
                        </Badge>
                        <div>
                          <p className="text-sm font-medium">
                            {session.questions_answered} preguntas • {session.correct_answers} correctas
                          </p>
                          <p className="text-xs text-gray-500">
                            {new Date(session.started_at).toLocaleDateString()} • {session.duration_minutes}min
                          </p>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="text-sm font-medium">{(session.accuracy * 100).toFixed(1)}%</p>
                        <p className="text-xs text-gray-500">Precisión</p>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Training Modes Tab */}
          <TabsContent value="modes" className="space-y-6">
            {/* Recommended Modes */}
            {trainingData?.recommended_modes && trainingData.recommended_modes.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Lightbulb className="h-5 w-5" />
                    Modos Recomendados
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {trainingData.recommended_modes.map((rec, index) => (
                      <div key={index} className="p-4 border border-blue-200 bg-blue-50 rounded-lg">
                        <div className="flex items-center gap-2 mb-2">
                          <Badge variant={rec.priority === 'high' ? 'destructive' : 'default'}>
                            {rec.mode}
                          </Badge>
                          {rec.priority === 'high' && <AlertCircle className="h-4 w-4 text-red-500" />}
                        </div>
                        <p className="text-sm text-gray-700">{rec.reason}</p>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* All Training Modes */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {trainingModes.map((mode) => {
                const Icon = mode.icon;
                return (
                  <Card key={mode.id} className="hover:shadow-lg transition-shadow">
                    <CardHeader>
                      <div className="flex items-center gap-3">
                        <div className={`p-2 rounded-lg ${mode.color}`}>
                          <Icon className="h-6 w-6 text-white" />
                        </div>
                        <div>
                          <CardTitle className="text-lg">{mode.name}</CardTitle>
                          <p className="text-sm text-gray-600">{mode.duration_minutes} min • {mode.question_limit} preguntas</p>
                        </div>
                      </div>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <p className="text-sm text-gray-700">{mode.description}</p>
                      <div className="text-xs text-gray-500 bg-gray-50 p-2 rounded">
                        <strong>Enfoque:</strong> {mode.focus}
                      </div>
                      <Button 
                        onClick={() => startTrainingSession(mode.id)}
                        className="w-full"
                      >
                        <Play className="h-4 w-4 mr-2" />
                        Iniciar Sesión
                      </Button>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          </TabsContent>

          {/* Progress Tab */}
          <TabsContent value="progress" className="space-y-6">
            {/* Progress tracking content would go here */}
            <Card>
              <CardHeader>
                <CardTitle>Progreso Detallado</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-gray-600">Análisis detallado de progreso en desarrollo...</p>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Analytics Tab */}
          <TabsContent value="analytics" className="space-y-6">
            {/* Analytics content would go here */}
            <Card>
              <CardHeader>
                <CardTitle>Analíticas Avanzadas</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-gray-600">Analíticas detalladas en desarrollo...</p>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}