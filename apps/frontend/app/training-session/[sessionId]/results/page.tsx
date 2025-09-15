'use client';

import React, { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { 
  Trophy, 
  Star, 
  Target, 
  Timer, 
  TrendingUp, 
  Brain, 
  CheckCircle, 
  XCircle,
  RotateCcw,
  Play,
  BarChart3,
  Calendar,
  Award,
  Zap,
  BookOpen,
  ArrowLeft,
  Share2
} from "lucide-react";

interface SessionResults {
  session_id: string;
  training_zone_id: string;
  mode: string;
  performance: {
    questions_answered: number;
    correct_answers: number;
    accuracy: number;
    target_questions: number;
    completion_percentage: number;
    session_time_minutes: number;
    average_response_time: number;
    improvement_over_original: number;
  };
  streak_info: {
    current_streak: number;
    max_streak_in_session: number;
    streak_improvement: number;
  };
  mastery_progress: {
    questions_mastered_this_session: number;
    total_mastered: number;
    mastery_level_before: number;
    mastery_level_after: number;
    mastery_improvement: number;
  };
  spaced_repetition_updates: {
    questions_promoted: number;
    questions_demoted: number;
    average_interval_increase: number;
  };
  difficulty_breakdown: {
    [key: string]: {
      attempted: number;
      correct: number;
      accuracy: number;
    };
  };
  achievements_unlocked: Array<{
    id: string;
    name: string;
    description: string;
    icon: string;
    points: number;
  }>;
  recommendations: {
    next_session_mode: string;
    focus_areas: string[];
    estimated_mastery_time: number;
    should_take_break: boolean;
  };
  detailed_progress: {
    time_improvement_percent: number;
    consistency_score: number;
    learning_velocity: number;
    retention_score: number;
  };
  comparison_metrics: {
    vs_last_session: {
      accuracy_change: number;
      time_change: number;
      streak_change: number;
    };
    vs_average: {
      accuracy_vs_avg: number;
      time_vs_avg: number;
    };
  };
}

const getModeIcon = (mode: string) => {
  switch (mode) {
    case 'recovery': return Target;
    case 'sprint': return Zap;
    case 'full_review': return BookOpen;
    case 'spaced_rep': return Brain;
    case 'monthly_focus': return Calendar;
    default: return Play;
  }
};

const getModeColor = (mode: string) => {
  switch (mode) {
    case 'recovery': return 'bg-blue-500';
    case 'sprint': return 'bg-red-500';
    case 'full_review': return 'bg-green-500';
    case 'spaced_rep': return 'bg-purple-500';
    case 'monthly_focus': return 'bg-orange-500';
    default: return 'bg-gray-500';
  }
};

export default function TrainingSessionResultsPage() {
  const params = useParams();
  const router = useRouter();
  const sessionId = params.sessionId as string;

  const [results, setResults] = useState<SessionResults | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (sessionId) {
      loadSessionResults();
    }
  }, [sessionId]);

  const loadSessionResults = async () => {
    try {
      const response = await fetch(`/api/v1/training-zone/session/${sessionId}/results`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (!response.ok) {
        throw new Error('Error al cargar resultados de la sesión');
      }

      const data = await response.json();
      setResults(data);
    } catch (error) {
      console.error('Error loading session results:', error);
      setError('Error al cargar los resultados. Verifica tu conexión.');
    } finally {
      setLoading(false);
    }
  };

  const startNewSession = async (mode: string) => {
    try {
      const response = await fetch('/api/v1/training-zone/session/start', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          subject_id: new URLSearchParams(window.location.search).get('subject') || '1',
          mode: mode
        })
      });

      if (!response.ok) {
        throw new Error('Error al iniciar nueva sesión');
      }

      const data = await response.json();
      router.push(`/training-session/${data.session_id}`);
    } catch (error) {
      console.error('Error starting new session:', error);
      alert('Error al iniciar nueva sesión');
    }
  };

  const shareResults = () => {
    const shareData = {
      title: 'Resultados de Training Zone - ICFES Leveling',
      text: `¡Completé una sesión de entrenamiento con ${results?.performance.accuracy.toFixed(1)}% de precisión!`,
      url: window.location.href
    };

    if (navigator.share) {
      navigator.share(shareData);
    } else {
      navigator.clipboard.writeText(`${shareData.text} ${shareData.url}`);
      alert('Resultados copiados al portapapeles');
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error || !results) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center">
        <Card className="max-w-md">
          <CardContent className="p-6 text-center">
            <p className="text-gray-600">{error || 'No se pudieron cargar los resultados'}</p>
            <Button onClick={() => router.push('/training-zone')} className="mt-4">
              Volver al Training Zone
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  const ModeIcon = getModeIcon(results.mode);

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Button
                onClick={() => router.push('/training-zone')}
                variant="outline"
                size="sm"
              >
                <ArrowLeft className="h-4 w-4 mr-2" />
                Volver
              </Button>
              <div className="flex items-center gap-3">
                <div className={`p-2 rounded-lg ${getModeColor(results.mode)}`}>
                  <ModeIcon className="h-6 w-6 text-white" />
                </div>
                <div>
                  <h1 className="text-2xl font-bold text-gray-900">Resultados de Sesión</h1>
                  <p className="text-sm text-gray-600">Modo: {results.mode}</p>
                </div>
              </div>
            </div>
            
            <div className="flex items-center gap-3">
              <Button onClick={shareResults} variant="outline" size="sm">
                <Share2 className="h-4 w-4 mr-2" />
                Compartir
              </Button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto p-6">
        {/* Achievements Banner */}
        {results.achievements_unlocked.length > 0 && (
          <div className="mb-6">
            <Card className="bg-gradient-to-r from-yellow-400 to-orange-500 text-white">
              <CardContent className="p-6">
                <div className="flex items-center gap-4">
                  <Trophy className="h-8 w-8" />
                  <div>
                    <h3 className="text-xl font-bold">¡Nuevos Logros Desbloqueados!</h3>
                    <div className="flex gap-2 mt-2">
                      {results.achievements_unlocked.map((achievement) => (
                        <Badge key={achievement.id} variant="secondary" className="bg-white/20 text-white">
                          {achievement.name}
                        </Badge>
                      ))}
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Main Performance Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Precisión</p>
                  <p className="text-3xl font-bold text-green-600">
                    {results.performance.accuracy.toFixed(1)}%
                  </p>
                  {results.comparison_metrics.vs_last_session.accuracy_change !== 0 && (
                    <p className={`text-sm ${results.comparison_metrics.vs_last_session.accuracy_change > 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {results.comparison_metrics.vs_last_session.accuracy_change > 0 ? '+' : ''}
                      {results.comparison_metrics.vs_last_session.accuracy_change.toFixed(1)}% vs última sesión
                    </p>
                  )}
                </div>
                <Target className="h-8 w-8 text-green-500" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Preguntas</p>
                  <p className="text-3xl font-bold text-blue-600">
                    {results.performance.correct_answers}/{results.performance.questions_answered}
                  </p>
                  <p className="text-sm text-gray-500">
                    {results.performance.completion_percentage.toFixed(0)}% completado
                  </p>
                </div>
                <CheckCircle className="h-8 w-8 text-blue-500" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Racha Máxima</p>
                  <p className="text-3xl font-bold text-purple-600">
                    {results.streak_info.max_streak_in_session}
                  </p>
                  {results.streak_info.streak_improvement !== 0 && (
                    <p className={`text-sm ${results.streak_info.streak_improvement > 0 ? 'text-green-600' : 'text-orange-600'}`}>
                      {results.streak_info.streak_improvement > 0 ? '+' : ''}
                      {results.streak_info.streak_improvement} vs promedio
                    </p>
                  )}
                </div>
                <Star className="h-8 w-8 text-purple-500" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Tiempo Promedio</p>
                  <p className="text-3xl font-bold text-orange-600">
                    {Math.round(results.performance.average_response_time)}s
                  </p>
                  {results.performance.improvement_over_original !== 0 && (
                    <p className={`text-sm ${results.performance.improvement_over_original > 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {results.performance.improvement_over_original > 0 ? '' : '+'}
                      {Math.abs(results.performance.improvement_over_original).toFixed(1)}s mejora
                    </p>
                  )}
                </div>
                <Timer className="h-8 w-8 text-orange-500" />
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column - Progress and Mastery */}
          <div className="lg:col-span-2 space-y-6">
            {/* Mastery Progress */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <TrendingUp className="h-5 w-5" />
                  Progreso de Dominio
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="text-center p-4 bg-green-50 rounded-lg">
                    <p className="text-3xl font-bold text-green-600">
                      {results.mastery_progress.questions_mastered_this_session}
                    </p>
                    <p className="text-sm text-green-700">Dominadas esta sesión</p>
                  </div>
                  <div className="text-center p-4 bg-blue-50 rounded-lg">
                    <p className="text-3xl font-bold text-blue-600">
                      {results.mastery_progress.total_mastered}
                    </p>
                    <p className="text-sm text-blue-700">Total dominadas</p>
                  </div>
                </div>
                
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span>Nivel de Dominio</span>
                    <span>{results.mastery_progress.mastery_level_after.toFixed(1)}%</span>
                  </div>
                  <Progress value={results.mastery_progress.mastery_level_after} className="h-3" />
                  {results.mastery_progress.mastery_improvement > 0 && (
                    <p className="text-sm text-green-600">
                      +{results.mastery_progress.mastery_improvement.toFixed(1)}% de mejora
                    </p>
                  )}
                </div>
              </CardContent>
            </Card>

            {/* Performance by Difficulty */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <BarChart3 className="h-5 w-5" />
                  Rendimiento por Dificultad
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {Object.entries(results.difficulty_breakdown).map(([difficulty, stats]) => (
                    <div key={difficulty} className="space-y-2">
                      <div className="flex justify-between text-sm">
                        <span className="capitalize font-medium">{difficulty}</span>
                        <span>{stats.correct}/{stats.attempted} ({stats.accuracy.toFixed(1)}%)</span>
                      </div>
                      <Progress value={stats.accuracy} className="h-2" />
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Spaced Repetition Updates */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <RotateCcw className="h-5 w-5" />
                  Repetición Espaciada
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 gap-4">
                  <div className="text-center p-3 bg-green-50 rounded-lg">
                    <p className="text-2xl font-bold text-green-600">
                      {results.spaced_repetition_updates.questions_promoted}
                    </p>
                    <p className="text-xs text-green-700">Promovidas</p>
                  </div>
                  <div className="text-center p-3 bg-orange-50 rounded-lg">
                    <p className="text-2xl font-bold text-orange-600">
                      {results.spaced_repetition_updates.questions_demoted}
                    </p>
                    <p className="text-xs text-orange-700">Necesitan repaso</p>
                  </div>
                </div>
                <div className="mt-4 text-center">
                  <p className="text-sm text-gray-600">
                    Intervalo promedio: +{results.spaced_repetition_updates.average_interval_increase.toFixed(1)} días
                  </p>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Right Column - Actions and Recommendations */}
          <div className="space-y-6">
            {/* Quick Actions */}
            <Card>
              <CardHeader>
                <CardTitle>Próxima Sesión</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {results.recommendations.should_take_break ? (
                  <div className="p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                    <p className="text-sm text-yellow-800">
                      Recomendamos tomar un descanso de 15-30 minutos antes de continuar.
                    </p>
                  </div>
                ) : (
                  <Button 
                    onClick={() => startNewSession(results.recommendations.next_session_mode)}
                    className="w-full"
                  >
                    <Play className="h-4 w-4 mr-2" />
                    Continuar con {results.recommendations.next_session_mode}
                  </Button>
                )}
                
                <Button 
                  onClick={() => router.push('/training-zone')}
                  variant="outline"
                  className="w-full"
                >
                  Elegir Modo Manualmente
                </Button>
                
                <Button 
                  onClick={() => router.push(`/training-zone/analytics`)}
                  variant="outline"
                  className="w-full"
                >
                  <BarChart3 className="h-4 w-4 mr-2" />
                  Ver Analíticas
                </Button>
              </CardContent>
            </Card>

            {/* Recommendations */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Brain className="h-5 w-5" />
                  Recomendaciones
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div>
                  <p className="text-sm font-medium text-gray-700 mb-2">Áreas de enfoque:</p>
                  <div className="space-y-1">
                    {results.recommendations.focus_areas.map((area, index) => (
                      <Badge key={index} variant="outline" className="text-xs">
                        {area}
                      </Badge>
                    ))}
                  </div>
                </div>
                
                <div className="pt-3 border-t">
                  <p className="text-sm text-gray-600">
                    Tiempo estimado para dominio completo: 
                    <span className="font-medium"> {Math.round(results.recommendations.estimated_mastery_time)} días</span>
                  </p>
                </div>
              </CardContent>
            </Card>

            {/* Detailed Metrics */}
            <Card>
              <CardHeader>
                <CardTitle>Métricas Detalladas</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex justify-between text-sm">
                  <span>Mejora de tiempo:</span>
                  <span className="font-medium">
                    {results.detailed_progress.time_improvement_percent.toFixed(1)}%
                  </span>
                </div>
                <div className="flex justify-between text-sm">
                  <span>Consistencia:</span>
                  <span className="font-medium">
                    {results.detailed_progress.consistency_score.toFixed(1)}/10
                  </span>
                </div>
                <div className="flex justify-between text-sm">
                  <span>Velocidad de aprendizaje:</span>
                  <span className="font-medium">
                    {results.detailed_progress.learning_velocity.toFixed(1)}/10
                  </span>
                </div>
                <div className="flex justify-between text-sm">
                  <span>Retención:</span>
                  <span className="font-medium">
                    {results.detailed_progress.retention_score.toFixed(1)}/10
                  </span>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}