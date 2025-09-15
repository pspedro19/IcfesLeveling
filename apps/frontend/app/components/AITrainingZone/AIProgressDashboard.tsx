'use client';

import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  ChartBarIcon,
  TrendingUpIcon,
  TrendingDownIcon,
  AcademicCapIcon,
  ClockIcon,
  SparklesIcon,
  LightBulbIcon,
  TargetIcon,
  CalendarIcon,
  BookOpenIcon
} from '@heroicons/react/24/outline';

interface ProgressData {
  analysis_period: string;
  performance_overview: {
    questions_answered: number;
    overall_accuracy: number;
    average_time_per_question: number;
    trend_direction: 'improving' | 'stable' | 'declining';
    improvement_rate: number;
  };
  strengths: Array<{
    topic: string;
    accuracy: number;
    questions: number;
  }>;
  areas_for_improvement: Array<{
    topic: string;
    accuracy: number;
    questions: number;
  }>;
  subject_breakdown: {
    [subject: string]: {
      accuracy: number;
      questions_answered: number;
    };
  };
  daily_performance: Array<{
    date: string;
    accuracy: number;
    questions: number;
  }>;
  ai_insights: string;
  predictions?: {
    estimated_icfes_score: number;
    confidence_interval: [number, number];
    score_percentile: number;
    factors: {
      accuracy_contribution: number;
      difficulty_contribution: number;
      consistency_contribution: number;
    };
  };
  personalized_recommendations: string[];
  next_steps: {
    immediate: string[];
    this_week: string[];
    this_month: string[];
  };
}

interface AIProgressDashboardProps {
  subjectId?: number;
  timePeriod?: number;
  onRecommendationClick?: (recommendation: string) => void;
}

export default function AIProgressDashboard({ 
  subjectId, 
  timePeriod = 30,
  onRecommendationClick 
}: AIProgressDashboardProps) {
  const [progressData, setProgressData] = useState<ProgressData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedTab, setSelectedTab] = useState<'overview' | 'insights' | 'predictions' | 'recommendations'>('overview');

  useEffect(() => {
    fetchProgressData();
  }, [subjectId, timePeriod]);

  const fetchProgressData = async () => {
    setIsLoading(true);
    try {
      const params = new URLSearchParams({
        time_period: timePeriod.toString(),
        include_predictions: 'true'
      });
      
      if (subjectId) {
        params.append('subject_id', subjectId.toString());
      }

      const response = await fetch(`/api/ai-training/progress-analysis?${params}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setProgressData(data);
      }
    } catch (error) {
      console.error('Error fetching progress data:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const getTrendIcon = (direction: string) => {
    switch (direction) {
      case 'improving':
        return <TrendingUpIcon className="h-5 w-5 text-green-500" />;
      case 'declining':
        return <TrendingDownIcon className="h-5 w-5 text-red-500" />;
      default:
        return <ChartBarIcon className="h-5 w-5 text-yellow-500" />;
    }
  };

  const getPerformanceColor = (accuracy: number) => {
    if (accuracy >= 0.8) return 'text-green-600 bg-green-100 dark:bg-green-900/20 dark:text-green-400';
    if (accuracy >= 0.6) return 'text-yellow-600 bg-yellow-100 dark:bg-yellow-900/20 dark:text-yellow-400';
    return 'text-red-600 bg-red-100 dark:bg-red-900/20 dark:text-red-400';
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('es-ES', { month: 'short', day: 'numeric' });
  };

  if (isLoading) {
    return (
      <div className="bg-white dark:bg-gray-900 rounded-xl shadow-lg p-8">
        <div className="animate-pulse space-y-6">
          <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded w-1/3"></div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {[1, 2, 3].map(i => (
              <div key={i} className="h-24 bg-gray-200 dark:bg-gray-700 rounded"></div>
            ))}
          </div>
          <div className="h-48 bg-gray-200 dark:bg-gray-700 rounded"></div>
        </div>
      </div>
    );
  }

  if (!progressData) {
    return (
      <div className="bg-white dark:bg-gray-900 rounded-xl shadow-lg p-8 text-center">
        <p className="text-gray-500 dark:text-gray-400 mb-4">
          No hay datos de progreso disponibles para el período seleccionado.
        </p>
        <button
          onClick={fetchProgressData}
          className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          Actualizar datos
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white dark:bg-gray-900 rounded-xl shadow-lg p-6">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg">
              <ChartBarIcon className="h-6 w-6 text-white" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-gray-900 dark:text-white">
                Análisis de Progreso IA
              </h2>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                Últimos {progressData.analysis_period}
              </p>
            </div>
          </div>
          
          <div className="flex space-x-1">
            {(['overview', 'insights', 'predictions', 'recommendations'] as const).map((tab) => (
              <button
                key={tab}
                onClick={() => setSelectedTab(tab)}
                className={`px-4 py-2 text-sm rounded-lg transition-colors ${
                  selectedTab === tab
                    ? 'bg-blue-100 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400'
                    : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800'
                }`}
              >
                {tab === 'overview' && 'Resumen'}
                {tab === 'insights' && 'Insights IA'}
                {tab === 'predictions' && 'Predicciones'}
                {tab === 'recommendations' && 'Recomendaciones'}
              </button>
            ))}
          </div>
        </div>

        {/* Key metrics */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="text-center">
            <div className="flex items-center justify-center space-x-2 mb-2">
              <AcademicCapIcon className="h-5 w-5 text-blue-500" />
              {getTrendIcon(progressData.performance_overview.trend_direction)}
            </div>
            <p className="text-2xl font-bold text-gray-900 dark:text-white">
              {(progressData.performance_overview.overall_accuracy * 100).toFixed(1)}%
            </p>
            <p className="text-sm text-gray-500 dark:text-gray-400">Precisión general</p>
          </div>

          <div className="text-center">
            <ClockIcon className="h-5 w-5 text-orange-500 mx-auto mb-2" />
            <p className="text-2xl font-bold text-gray-900 dark:text-white">
              {Math.round(progressData.performance_overview.average_time_per_question)}s
            </p>
            <p className="text-sm text-gray-500 dark:text-gray-400">Tiempo promedio</p>
          </div>

          <div className="text-center">
            <BookOpenIcon className="h-5 w-5 text-green-500 mx-auto mb-2" />
            <p className="text-2xl font-bold text-gray-900 dark:text-white">
              {progressData.performance_overview.questions_answered}
            </p>
            <p className="text-sm text-gray-500 dark:text-gray-400">Preguntas respondidas</p>
          </div>

          <div className="text-center">
            <SparklesIcon className="h-5 w-5 text-purple-500 mx-auto mb-2" />
            <p className="text-2xl font-bold text-gray-900 dark:text-white">
              {progressData.predictions?.estimated_icfes_score || 'N/A'}
            </p>
            <p className="text-sm text-gray-500 dark:text-gray-400">Predicción ICFES</p>
          </div>
        </div>
      </div>

      {/* Tab content */}
      <div className="bg-white dark:bg-gray-900 rounded-xl shadow-lg p-6">
        {selectedTab === 'overview' && (
          <div className="space-y-6">
            {/* Performance chart visualization */}
            <div>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                Rendimiento diario
              </h3>
              <div className="grid grid-cols-7 gap-2 mb-4">
                {progressData.daily_performance.slice(0, 14).reverse().map((day, index) => {
                  const height = Math.max(10, day.accuracy * 100);
                  return (
                    <div key={index} className="flex flex-col items-center">
                      <div className="w-full bg-gray-200 dark:bg-gray-700 rounded h-20 flex items-end p-1">
                        <motion.div
                          initial={{ height: 0 }}
                          animate={{ height: `${height}%` }}
                          transition={{ delay: index * 0.1 }}
                          className={`w-full rounded ${getPerformanceColor(day.accuracy).includes('green') ? 'bg-green-500' : 
                            getPerformanceColor(day.accuracy).includes('yellow') ? 'bg-yellow-500' : 'bg-red-500'}`}
                          title={`${formatDate(day.date)}: ${(day.accuracy * 100).toFixed(1)}%`}
                        />
                      </div>
                      <span className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                        {formatDate(day.date)}
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Strengths and weaknesses */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h4 className="font-semibold text-gray-900 dark:text-white mb-3 flex items-center space-x-2">
                  <span className="w-3 h-3 bg-green-500 rounded-full"></span>
                  <span>Fortalezas</span>
                </h4>
                <div className="space-y-2">
                  {progressData.strengths.slice(0, 5).map((strength, index) => (
                    <div key={index} className="flex items-center justify-between p-3 bg-green-50 dark:bg-green-900/20 rounded-lg">
                      <span className="text-sm font-medium text-gray-900 dark:text-white">
                        {strength.topic}
                      </span>
                      <div className="text-right">
                        <span className="text-sm font-bold text-green-600 dark:text-green-400">
                          {(strength.accuracy * 100).toFixed(1)}%
                        </span>
                        <p className="text-xs text-gray-500 dark:text-gray-400">
                          {strength.questions} preguntas
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div>
                <h4 className="font-semibold text-gray-900 dark:text-white mb-3 flex items-center space-x-2">
                  <span className="w-3 h-3 bg-red-500 rounded-full"></span>
                  <span>Áreas de mejora</span>
                </h4>
                <div className="space-y-2">
                  {progressData.areas_for_improvement.slice(0, 5).map((weakness, index) => (
                    <div key={index} className="flex items-center justify-between p-3 bg-red-50 dark:bg-red-900/20 rounded-lg">
                      <span className="text-sm font-medium text-gray-900 dark:text-white">
                        {weakness.topic}
                      </span>
                      <div className="text-right">
                        <span className="text-sm font-bold text-red-600 dark:text-red-400">
                          {(weakness.accuracy * 100).toFixed(1)}%
                        </span>
                        <p className="text-xs text-gray-500 dark:text-gray-400">
                          {weakness.questions} preguntas
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        {selectedTab === 'insights' && (
          <div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center space-x-2">
              <SparklesIcon className="h-5 w-5 text-blue-500" />
              <span>Análisis IA personalizado</span>
            </h3>
            <div className="prose prose-sm max-w-none text-gray-700 dark:text-gray-300">
              {progressData.ai_insights.split('\n').map((paragraph, index) => (
                <p key={index} className="mb-3">{paragraph}</p>
              ))}
            </div>
          </div>
        )}

        {selectedTab === 'predictions' && progressData.predictions && (
          <div className="space-y-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center space-x-2">
              <TargetIcon className="h-5 w-5 text-purple-500" />
              <span>Predicciones ICFES</span>
            </h3>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="text-center p-6 bg-gradient-to-r from-blue-50 to-purple-50 dark:from-blue-900/20 dark:to-purple-900/20 rounded-xl">
                <h4 className="font-semibold text-gray-900 dark:text-white mb-2">Puntaje estimado</h4>
                <p className="text-3xl font-bold text-blue-600 dark:text-blue-400">
                  {progressData.predictions.estimated_icfes_score}
                </p>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  Rango: {progressData.predictions.confidence_interval[0]} - {progressData.predictions.confidence_interval[1]}
                </p>
              </div>

              <div className="text-center p-6 bg-gradient-to-r from-green-50 to-blue-50 dark:from-green-900/20 dark:to-blue-900/20 rounded-xl">
                <h4 className="font-semibold text-gray-900 dark:text-white mb-2">Percentil</h4>
                <p className="text-3xl font-bold text-green-600 dark:text-green-400">
                  {progressData.predictions.score_percentile}%
                </p>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  Mejor que {progressData.predictions.score_percentile}% de estudiantes
                </p>
              </div>

              <div className="p-6 bg-gray-50 dark:bg-gray-800 rounded-xl">
                <h4 className="font-semibold text-gray-900 dark:text-white mb-3">Factores de contribución</h4>
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600 dark:text-gray-400">Precisión</span>
                    <span className="font-medium text-gray-900 dark:text-white">
                      +{progressData.predictions.factors.accuracy_contribution}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600 dark:text-gray-400">Dificultad</span>
                    <span className="font-medium text-gray-900 dark:text-white">
                      +{progressData.predictions.factors.difficulty_contribution}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600 dark:text-gray-400">Consistencia</span>
                    <span className="font-medium text-gray-900 dark:text-white">
                      +{progressData.predictions.factors.consistency_contribution}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {selectedTab === 'recommendations' && (
          <div className="space-y-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center space-x-2">
              <LightBulbIcon className="h-5 w-5 text-yellow-500" />
              <span>Recomendaciones personalizadas</span>
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div>
                <h4 className="font-medium text-gray-900 dark:text-white mb-3 flex items-center space-x-2">
                  <CalendarIcon className="h-4 w-4 text-red-500" />
                  <span>Inmediato</span>
                </h4>
                <div className="space-y-2">
                  {progressData.next_steps.immediate.map((step, index) => (
                    <button
                      key={index}
                      onClick={() => onRecommendationClick?.(step)}
                      className="w-full text-left p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg hover:bg-red-100 dark:hover:bg-red-900/30 transition-colors"
                    >
                      <p className="text-sm text-red-800 dark:text-red-200">{step}</p>
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <h4 className="font-medium text-gray-900 dark:text-white mb-3 flex items-center space-x-2">
                  <CalendarIcon className="h-4 w-4 text-yellow-500" />
                  <span>Esta semana</span>
                </h4>
                <div className="space-y-2">
                  {progressData.next_steps.this_week.map((step, index) => (
                    <button
                      key={index}
                      onClick={() => onRecommendationClick?.(step)}
                      className="w-full text-left p-3 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg hover:bg-yellow-100 dark:hover:bg-yellow-900/30 transition-colors"
                    >
                      <p className="text-sm text-yellow-800 dark:text-yellow-200">{step}</p>
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <h4 className="font-medium text-gray-900 dark:text-white mb-3 flex items-center space-x-2">
                  <CalendarIcon className="h-4 w-4 text-green-500" />
                  <span>Este mes</span>
                </h4>
                <div className="space-y-2">
                  {progressData.next_steps.this_month.map((step, index) => (
                    <button
                      key={index}
                      onClick={() => onRecommendationClick?.(step)}
                      className="w-full text-left p-3 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg hover:bg-green-100 dark:hover:bg-green-900/30 transition-colors"
                    >
                      <p className="text-sm text-green-800 dark:text-green-200">{step}</p>
                    </button>
                  ))}
                </div>
              </div>
            </div>

            <div className="mt-6 p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
              <h5 className="font-medium text-blue-900 dark:text-blue-100 mb-2">
                Recomendaciones adicionales del algoritmo IA:
              </h5>
              <div className="space-y-2">
                {progressData.personalized_recommendations.map((rec, index) => (
                  <div key={index} className="flex items-start space-x-2">
                    <div className="w-2 h-2 bg-blue-500 rounded-full mt-2 flex-shrink-0"></div>
                    <p className="text-sm text-blue-800 dark:text-blue-200">{rec}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}