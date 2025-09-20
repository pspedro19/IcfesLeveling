'use client';

import { useParams } from 'next/navigation';
import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { getApiUrl } from '@/lib/config';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Button } from '@/components/ui/button';
import { CheckCircle, XCircle, Clock, Trophy, BookOpen, TrendingUp, Target, ArrowLeft } from 'lucide-react';
import Link from 'next/link';

interface DiagnosticResultsData {
  test_id: string;
  subject: string;
  final_theta_score: number;
  score_percentage: number;
  questions_answered: number;
  questions_correct: number;
  questions_incorrect: number;
  time_spent_minutes: number;
  completed_at: string;
  correct_questions: QuestionDetail[];
  incorrect_questions: QuestionDetail[];
  competencies_mastered: CompetencyDetail[];
  areas_for_improvement: CompetencyDetail[];
  componente_performance: Record<string, PerformanceStats>;
  proceso_cognitivo_performance: Record<string, PerformanceStats>;
  recommended_study_topics: string[];
  strengths: string[];
  weaknesses: string[];
  score_by_topic: Record<string, number>;
}

interface QuestionDetail {
  id: string;
  question_text: string;
  user_answer: string;
  correct_answer: string;
  response_time_ms: number;
  topic: string;
  difficulty: number;
  componente?: string;
  proceso_cognitivo?: string;
  competencia?: string;
}

interface CompetencyDetail {
  name: string;
  type: string;
  percentage: number;
  questions_correct: number;
  questions_total: number;
  description?: string;
  nivel?: string;
  icon?: string;
  priority?: string;
  irt_ability?: number;
}

interface PerformanceStats {
  percentage: number;
  questions_correct: number;
  questions_total: number;
}

export default function DiagnosticResultsPage() {
  const params = useParams();
  const testId = params.testId as string;
  const [results, setResults] = useState<DiagnosticResultsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Map subject names to UUIDs
  const getSubjectId = (subjectName: string): string => {
    const subjectMapping: Record<string, string> = {
      'Diagnóstico de Matemáticas': '550e8400-e29b-41d4-a716-446655440001',
      'Matemáticas': '550e8400-e29b-41d4-a716-446655440001',
      'Diagnóstico de Lenguaje': '550e8400-e29b-41d4-a716-446655440002',
      'Lenguaje': '550e8400-e29b-41d4-a716-446655440002',
      'Diagnóstico de Ciencias Naturales': '550e8400-e29b-41d4-a716-446655440003',
      'Ciencias Naturales': '550e8400-e29b-41d4-a716-446655440003',
      'Diagnóstico de Ciencias Sociales': '550e8400-e29b-41d4-a716-446655440004',
      'Ciencias Sociales': '550e8400-e29b-41d4-a716-446655440004',
      'Diagnóstico de Inglés': '550e8400-e29b-41d4-a716-446655440005',
      'Inglés': '550e8400-e29b-41d4-a716-446655440005'
    };

    return subjectMapping[subjectName] || '550e8400-e29b-41d4-a716-446655440001'; // Default to Matemáticas
  };

  useEffect(() => {
    const fetchResults = async () => {
      try {
        // Try authenticated endpoint first
        const token = localStorage.getItem('auth_token');
        let response;
        
        if (token) {
          response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/diagnostic/results/${testId}`, {
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json',
            },
          });
        }
        
        // If no token or authenticated request failed, try public endpoint
        if (!token || !response?.ok) {
          const baseUrl = typeof window !== 'undefined' ? `${window.location.protocol}//${window.location.hostname}:4000` : 'http://localhost:4000';
          response = await fetch(`${baseUrl}/api/v1/diagnostic-public/results/${testId}`, {
            headers: {
              'Content-Type': 'application/json',
            },
          });
        }

        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.detail || 'Error al cargar resultados');
        }

        const data = await response.json();
        setResults(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Error desconocido');
      } finally {
        setLoading(false);
      }
    };

    if (testId) {
      fetchResults();
    }
  }, [testId]);

  const getScoreColor = (percentage: number) => {
    if (percentage >= 80) return 'text-green-600';
    if (percentage >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getScoreBadgeColor = (percentage: number) => {
    if (percentage >= 80) return 'bg-green-100 text-green-800';
    if (percentage >= 60) return 'bg-yellow-100 text-yellow-800';
    return 'bg-red-100 text-red-800';
  };

  const formatTime = (minutes: number) => {
    const hrs = Math.floor(minutes / 60);
    const mins = Math.floor(minutes % 60);
    return hrs > 0 ? `${hrs}h ${mins}m` : `${mins}m`;
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-purple-50 p-8">
        <div className="max-w-6xl mx-auto">
          <div className="animate-pulse">
            <div className="h-8 bg-gray-200 rounded w-1/4 mb-8"></div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
              {[1, 2, 3].map((i) => (
                <div key={i} className="h-32 bg-gray-200 rounded-lg"></div>
              ))}
            </div>
            <div className="h-96 bg-gray-200 rounded-lg"></div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-purple-50 p-8">
        <div className="max-w-6xl mx-auto text-center">
          <Card className="p-8">
            <CardContent>
              <XCircle className="h-16 w-16 text-red-500 mx-auto mb-4" />
              <h2 className="text-2xl font-bold text-gray-900 mb-2">Error al cargar resultados</h2>
              <p className="text-gray-600 mb-4">{error}</p>
              <Button asChild>
                <Link href="/diagnostic-test">Volver a diagnósticos</Link>
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  if (!results) {
    return null;
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-purple-50 p-8">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="flex items-center gap-4 mb-8">
          <Button variant="outline" size="sm" asChild>
            <Link href="/diagnostic-test">
              <ArrowLeft className="h-4 w-4 mr-2" />
              Volver
            </Link>
          </Button>
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Resultados del Diagnóstico</h1>
            <p className="text-gray-600">{results.subject} • {new Date(results.completed_at).toLocaleDateString()}</p>
          </div>
        </div>

        {/* Score Overview Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <Card className="border-l-4 border-l-blue-500">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Puntaje Final</p>
                  <p className={`text-2xl font-bold ${getScoreColor(results.score_percentage)}`}>
                    {results.score_percentage}%
                  </p>
                </div>
                <Trophy className="h-8 w-8 text-blue-500" />
              </div>
            </CardContent>
          </Card>

          <Card className="border-l-4 border-l-green-500">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Theta Score (IRT)</p>
                  <p className="text-2xl font-bold text-gray-900">{results.final_theta_score}</p>
                </div>
                <Target className="h-8 w-8 text-green-500" />
              </div>
            </CardContent>
          </Card>

          <Card className="border-l-4 border-l-purple-500">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Preguntas Correctas</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {results.questions_correct}/{results.questions_answered}
                  </p>
                </div>
                <CheckCircle className="h-8 w-8 text-purple-500" />
              </div>
            </CardContent>
          </Card>

          <Card className="border-l-4 border-l-orange-500">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Tiempo Total</p>
                  <p className="text-2xl font-bold text-gray-900">{formatTime(results.time_spent_minutes)}</p>
                </div>
                <Clock className="h-8 w-8 text-orange-500" />
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
          {/* Competencies Mastered */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Trophy className="h-5 w-5 text-green-500" />
                Competencias Dominadas
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {results.competencies_mastered.length > 0 ? (
                  results.competencies_mastered.map((comp, index) => (
                    <div key={index} className="flex items-center justify-between p-4 bg-green-50 rounded-lg border border-green-200">
                      <div className="flex items-center gap-3">
                        {comp.icon && <span className="text-lg">{comp.icon}</span>}
                        <div>
                          <p className="font-medium text-gray-900">{comp.name}</p>
                          {comp.description && (
                            <p className="text-sm text-gray-600">{comp.description}</p>
                          )}
                          {comp.nivel && (
                            <Badge variant="outline" className="text-xs mt-1">
                              Nivel: {comp.nivel}
                            </Badge>
                          )}
                        </div>
                      </div>
                      <div className="text-right">
                        <Badge className={getScoreBadgeColor(comp.percentage)}>
                          {Math.round(comp.percentage)}%
                        </Badge>
                        <p className="text-xs text-gray-500">
                          {comp.questions_correct}/{comp.questions_total}
                        </p>
                        {comp.irt_ability && (
                          <p className="text-xs text-blue-600">
                            IRT: {comp.irt_ability.toFixed(2)}
                          </p>
                        )}
                      </div>
                    </div>
                  ))
                ) : (
                  <p className="text-gray-500 text-center py-4">
                    No hay competencias dominadas aún. ¡Sigue practicando!
                  </p>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Areas for Improvement */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <TrendingUp className="h-5 w-5 text-red-500" />
                Áreas de Mejora
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {results.areas_for_improvement.length > 0 ? (
                  results.areas_for_improvement.map((area, index) => (
                    <div key={index} className="flex items-center justify-between p-4 bg-red-50 rounded-lg border border-red-200">
                      <div className="flex items-center gap-3">
                        {area.icon && <span className="text-lg">{area.icon}</span>}
                        <div>
                          <p className="font-medium text-gray-900">{area.name}</p>
                          {area.description && (
                            <p className="text-sm text-gray-600">{area.description}</p>
                          )}
                          <div className="flex gap-2 mt-1">
                            {area.nivel && (
                              <Badge variant="outline" className="text-xs">
                                Nivel: {area.nivel}
                              </Badge>
                            )}
                            {area.priority && (
                              <Badge
                                variant={area.priority === 'alta' ? 'destructive' : 'secondary'}
                                className="text-xs"
                              >
                                Prioridad: {area.priority}
                              </Badge>
                            )}
                          </div>
                        </div>
                      </div>
                      <div className="text-right">
                        <Badge className={getScoreBadgeColor(area.percentage)}>
                          {Math.round(area.percentage)}%
                        </Badge>
                        <p className="text-xs text-gray-500">
                          {area.questions_correct}/{area.questions_total}
                        </p>
                        {area.irt_ability && (
                          <p className="text-xs text-blue-600">
                            IRT: {area.irt_ability.toFixed(2)}
                          </p>
                        )}
                      </div>
                    </div>
                  ))
                ) : (
                  <p className="text-gray-500 text-center py-4">
                    ¡Excelente! No se identificaron áreas críticas de mejora.
                  </p>
                )}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Performance Analysis */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
          {/* Componente Performance */}
          <Card>
            <CardHeader>
              <CardTitle>Rendimiento por Componente</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {Object.entries(results.componente_performance).map(([componente, stats]) => (
                  <div key={componente}>
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-sm font-medium text-gray-700">{componente}</span>
                      <span className="text-sm text-gray-600">
                        {stats.questions_correct}/{stats.questions_total}
                      </span>
                    </div>
                    <Progress value={stats.percentage} className="h-2" />
                    <p className="text-xs text-gray-500 mt-1">{stats.percentage}%</p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Proceso Cognitivo Performance */}
          <Card>
            <CardHeader>
              <CardTitle>Rendimiento por Proceso Cognitivo</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {Object.entries(results.proceso_cognitivo_performance).map(([proceso, stats]) => (
                  <div key={proceso}>
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-sm font-medium text-gray-700">{proceso}</span>
                      <span className="text-sm text-gray-600">
                        {stats.questions_correct}/{stats.questions_total}
                      </span>
                    </div>
                    <Progress value={stats.percentage} className="h-2" />
                    <p className="text-xs text-gray-500 mt-1">{stats.percentage}%</p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Study Recommendations */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BookOpen className="h-5 w-5 text-blue-500" />
              Temas de Estudio Recomendados
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
              {results.recommended_study_topics.map((topic, index) => (
                <Badge key={index} variant="outline" className="p-2 text-center">
                  {topic}
                </Badge>
              ))}
            </div>
            {results.recommended_study_topics.length === 0 && (
              <p className="text-gray-500 text-center py-4">
                ¡Excelente rendimiento! Continúa con tu plan de estudios actual.
              </p>
            )}
          </CardContent>
        </Card>

        {/* Question Analysis */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Correct Questions */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <CheckCircle className="h-5 w-5 text-green-500" />
                Preguntas Correctas ({results.correct_questions.length})
              </CardTitle>
            </CardHeader>
            <CardContent className="max-h-96 overflow-y-auto">
              <div className="space-y-3">
                {results.correct_questions.map((question, index) => (
                  <div key={question.id} className="p-3 bg-green-50 rounded-lg border-l-4 border-green-500">
                    <p className="text-sm font-medium text-gray-900 mb-1">
                      Pregunta {index + 1} • {question.topic}
                    </p>
                    <p className="text-xs text-gray-600 mb-2">
                      {question.question_text.length > 100 
                        ? `${question.question_text.substring(0, 100)}...` 
                        : question.question_text}
                    </p>
                    <div className="flex items-center justify-between">
                      <div className="flex gap-2">
                        <Badge variant="outline" className="text-xs">
                          Respuesta: {question.user_answer}
                        </Badge>
                        {question.componente && (
                          <Badge variant="outline" className="text-xs">
                            {question.componente}
                          </Badge>
                        )}
                      </div>
                      <span className="text-xs text-gray-500">
                        {Math.round(question.response_time_ms / 1000)}s
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Incorrect Questions */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <XCircle className="h-5 w-5 text-red-500" />
                Preguntas Incorrectas ({results.incorrect_questions.length})
              </CardTitle>
            </CardHeader>
            <CardContent className="max-h-96 overflow-y-auto">
              <div className="space-y-3">
                {results.incorrect_questions.map((question, index) => (
                  <div key={question.id} className="p-3 bg-red-50 rounded-lg border-l-4 border-red-500">
                    <p className="text-sm font-medium text-gray-900 mb-1">
                      Pregunta {index + 1} • {question.topic}
                    </p>
                    <p className="text-xs text-gray-600 mb-2">
                      {question.question_text.length > 100 
                        ? `${question.question_text.substring(0, 100)}...` 
                        : question.question_text}
                    </p>
                    <div className="flex items-center justify-between">
                      <div className="flex gap-2">
                        <Badge variant="destructive" className="text-xs">
                          Tu respuesta: {question.user_answer}
                        </Badge>
                        <Badge variant="outline" className="text-xs">
                          Correcta: {question.correct_answer}
                        </Badge>
                        {question.componente && (
                          <Badge variant="outline" className="text-xs">
                            {question.componente}
                          </Badge>
                        )}
                      </div>
                      <span className="text-xs text-gray-500">
                        {Math.round(question.response_time_ms / 1000)}s
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Action Buttons */}
        <div className="flex justify-center gap-4 mt-8">
          <Button asChild>
            <Link href="/diagnostic-test">Tomar Otro Diagnóstico</Link>
          </Button>
          <Button variant="outline" asChild>
            <Link href={`/study-plan-view?subject=${getSubjectId(results?.subject || '')}&test_id=${testId}`}>Ver Plan de Estudio</Link>
          </Button>
        </div>
      </div>
    </div>
  );
}