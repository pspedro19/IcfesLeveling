'use client';

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  Brain, 
  Target, 
  Clock, 
  Trophy, 
  BarChart3, 
  Play,
  CheckCircle,
  XCircle,
  Lightbulb
} from 'lucide-react';
import UnitQuiz from '@/components/UnitQuiz';

interface QuizStats {
  total_quizzes: number;
  completed_quizzes: number;
  average_score: number;
  best_score: number;
  total_questions_answered: number;
  correct_answers: number;
  accuracy_percentage: number;
}

interface QuizFeedback {
  quiz_id: string;
  overall_score: number;
  strengths: string[];
  weaknesses: string[];
  recommendations: string[];
  ai_analysis: Record<string, any>;
}

export default function UnitQuizPage() {
  const [selectedPlan, setSelectedPlan] = useState<string>('plan-123');
  const [selectedUnit, setSelectedUnit] = useState<number>(1);
  const [quizStats, setQuizStats] = useState<QuizStats | null>(null);
  const [lastFeedback, setLastFeedback] = useState<QuizFeedback | null>(null);

  // Datos de ejemplo
  const examplePlans = [
    { id: 'plan-123', name: 'Plan de Matemáticas', subject: 'Matemáticas' },
    { id: 'plan-456', name: 'Plan de Ciencias', subject: 'Ciencias' },
    { id: 'plan-789', name: 'Plan de Lenguaje', subject: 'Lenguaje' }
  ];

  const exampleUnits = [
    { number: 1, name: 'Fundamentos Básicos', description: 'Conceptos fundamentales del tema' },
    { number: 2, name: 'Aplicaciones Prácticas', description: 'Ejercicios y problemas prácticos' },
    { number: 3, name: 'Análisis Avanzado', description: 'Conceptos avanzados y complejos' },
    { number: 4, name: 'Integración de Conceptos', description: 'Síntesis y aplicación integral' }
  ];

  const handleQuizComplete = (feedback: QuizFeedback) => {
    setLastFeedback(feedback);
    // Aquí se podría actualizar el progreso del plan
    console.log('Quiz completado:', feedback);
  };

  const handleQuizProgress = (progress: any) => {
    // Actualizar estadísticas en tiempo real
    console.log('Progreso del quiz:', progress);
  };

  const fetchQuizStats = async () => {
    try {
      const unitId = `${selectedPlan}_${selectedUnit}`;
      const response = await fetch(`/api/v1/quiz/unit/${unitId}/stats`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (response.ok) {
        const stats = await response.json();
        setQuizStats(stats);
      }
    } catch (error) {
      console.error('Error obteniendo estadísticas:', error);
    }
  };

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="text-center space-y-4">
        <h1 className="text-4xl font-bold text-gray-900">
          Sistema de Quizzes Contextualizados
        </h1>
        <p className="text-xl text-gray-600">
          Evalúa tu comprensión con quizzes personalizados por unidad
        </p>
      </div>

      <Tabs defaultValue="quiz" className="w-full">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="quiz" className="flex items-center space-x-2">
            <Brain className="h-4 w-4" />
            <span>Quiz</span>
          </TabsTrigger>
          <TabsTrigger value="stats" className="flex items-center space-x-2">
            <BarChart3 className="h-4 w-4" />
            <span>Estadísticas</span>
          </TabsTrigger>
          <TabsTrigger value="feedback" className="flex items-center space-x-2">
            <Trophy className="h-4 w-4" />
            <span>Retroalimentación</span>
          </TabsTrigger>
        </TabsList>

        <TabsContent value="quiz" className="space-y-6">
          {/* Selector de Plan y Unidad */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Target className="h-5 w-5" />
                <span>Configuración del Quiz</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Plan de Estudio
                  </label>
                  <select
                    value={selectedPlan}
                    onChange={(e) => setSelectedPlan(e.target.value)}
                    className="w-full p-2 border border-gray-300 rounded-md"
                  >
                    {examplePlans.map((plan) => (
                      <option key={plan.id} value={plan.id}>
                        {plan.name} - {plan.subject}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Unidad
                  </label>
                  <select
                    value={selectedUnit}
                    onChange={(e) => setSelectedUnit(Number(e.target.value))}
                    className="w-full p-2 border border-gray-300 rounded-md"
                  >
                    {exampleUnits.map((unit) => (
                      <option key={unit.number} value={unit.number}>
                        Unidad {unit.number}: {unit.name}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
              
              <div className="bg-blue-50 p-4 rounded-lg">
                <div className="flex items-center space-x-2 text-blue-700 mb-2">
                  <Lightbulb className="h-4 w-4" />
                  <span className="font-medium">Información del Quiz</span>
                </div>
                <ul className="text-blue-600 space-y-1 text-sm">
                  <li>• Mínimo 10 preguntas por quiz</li>
                  <li>• 80% de aciertos para aprobar</li>
                  <li>• Retroalimentación inmediata con IA</li>
                  <li>• Actualización automática del progreso ponderado</li>
                  <li>• Preguntas contextualizadas según la unidad</li>
                </ul>
              </div>
            </CardContent>
          </Card>

          {/* Componente Quiz */}
          <UnitQuiz
            planId={selectedPlan}
            unitNumber={selectedUnit}
            onQuizComplete={handleQuizComplete}
            onQuizProgress={handleQuizProgress}
          />
        </TabsContent>

        <TabsContent value="stats" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <BarChart3 className="h-5 w-5" />
                <span>Estadísticas de Quizzes</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="text-center p-4 bg-blue-50 rounded-lg">
                  <div className="text-2xl font-bold text-blue-600">
                    {quizStats?.total_quizzes || 0}
                  </div>
                  <div className="text-sm text-blue-600">Total Quizzes</div>
                </div>
                <div className="text-center p-4 bg-green-50 rounded-lg">
                  <div className="text-2xl font-bold text-green-600">
                    {quizStats?.completed_quizzes || 0}
                  </div>
                  <div className="text-sm text-green-600">Completados</div>
                </div>
                <div className="text-center p-4 bg-yellow-50 rounded-lg">
                  <div className="text-2xl font-bold text-yellow-600">
                    {quizStats?.average_score?.toFixed(1) || 0}%
                  </div>
                  <div className="text-sm text-yellow-600">Promedio</div>
                </div>
                <div className="text-center p-4 bg-purple-50 rounded-lg">
                  <div className="text-2xl font-bold text-purple-600">
                    {quizStats?.best_score?.toFixed(1) || 0}%
                  </div>
                  <div className="text-sm text-purple-600">Mejor Puntaje</div>
                </div>
              </div>

              <div className="mt-6">
                <Button onClick={fetchQuizStats} className="w-full">
                  Actualizar Estadísticas
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="feedback" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Trophy className="h-5 w-5" />
                <span>Última Retroalimentación</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              {lastFeedback ? (
                <div className="space-y-6">
                  {/* Puntaje */}
                  <div className="text-center">
                    <div className="text-4xl font-bold text-blue-600">
                      {lastFeedback.overall_score.toFixed(1)}%
                    </div>
                    <div className="text-lg text-gray-600">
                      Puntaje Final
                    </div>
                  </div>

                  {/* Fortalezas */}
                  {lastFeedback.strengths.length > 0 && (
                    <div>
                      <h3 className="text-lg font-semibold flex items-center space-x-2 text-green-600">
                        <CheckCircle className="h-5 w-5" />
                        <span>Fortalezas</span>
                      </h3>
                      <ul className="mt-2 space-y-1">
                        {lastFeedback.strengths.map((strength, index) => (
                          <li key={index} className="text-green-700">• {strength}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Debilidades */}
                  {lastFeedback.weaknesses.length > 0 && (
                    <div>
                      <h3 className="text-lg font-semibold flex items-center space-x-2 text-red-600">
                        <XCircle className="h-5 w-5" />
                        <span>Áreas de Mejora</span>
                      </h3>
                      <ul className="mt-2 space-y-1">
                        {lastFeedback.weaknesses.map((weakness, index) => (
                          <li key={index} className="text-red-700">• {weakness}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Recomendaciones */}
                  {lastFeedback.recommendations.length > 0 && (
                    <div>
                      <h3 className="text-lg font-semibold flex items-center space-x-2 text-blue-600">
                        <Lightbulb className="h-5 w-5" />
                        <span>Recomendaciones</span>
                      </h3>
                      <ul className="mt-2 space-y-1">
                        {lastFeedback.recommendations.map((recommendation, index) => (
                          <li key={index} className="text-blue-700">• {recommendation}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              ) : (
                <div className="text-center text-gray-500 py-8">
                  <Brain className="h-12 w-12 mx-auto mb-4 text-gray-400" />
                  <p>Completa un quiz para ver la retroalimentación</p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
} 