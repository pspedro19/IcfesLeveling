'use client';

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Brain,
  Target,
  Calendar,
  Swords,
  TrendingUp,
  BookOpen,
  Clock,
  RefreshCw,
  ChevronRight,
  Award,
  Zap,
  BarChart3,
  AlertCircle
} from 'lucide-react';
import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:4000';

interface Recommendation {
  nextTopics: TopicRecommendation[];
  difficultyAdjustment: DifficultyRecommendation;
  studySchedule: StudySchedule;
  battleStrategies: BattleStrategy[];
  goals: Goals;
  confidenceScore: number;
  generatedAt: string;
}

interface TopicRecommendation {
  topic: string;
  reason: string;
  priority: string;
  suggestedQuestions: number;
  estimatedTime: string;
}

interface DifficultyRecommendation {
  currentOptimal: number;
  suggestedRange: { min: number; max: number };
  progressionStrategy: string;
  description: string;
  challengeMode: boolean;
}

interface StudySchedule {
  recommendedDuration: string;
  optimalTimeSlots: TimeSlot[];
  frequency: string;
  focusDistribution: Record<string, number>;
  note?: string;
}

interface TimeSlot {
  time: string;
  period: string;
  effectiveness: string;
}

interface BattleStrategy {
  name: string;
  description: string;
  tips: string[];
  expectedImprovement?: string;
}

interface Goals {
  shortTerm: Goal[];
  mediumTerm: Goal[];
  longTerm: Goal[];
}

interface Goal {
  goal: string;
  current?: string;
  target?: string;
  actions: string[];
  deadline: string;
}

export default function AdaptiveRecommendations() {
  const [recommendations, setRecommendations] = useState<Recommendation | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<string>('topics');
  const [refreshing, setRefreshing] = useState(false);
  
  const getAuthHeaders = () => {
    const token = localStorage.getItem('token');
    return {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json'
    };
  };
  
  const fetchRecommendations = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await axios.get(
        `${API_URL}/api/v1/recommendations/adaptive`,
        { headers: getAuthHeaders() }
      );
      
      // Convert snake_case to camelCase
      const data = response.data;
      setRecommendations({
        nextTopics: data.next_topics,
        difficultyAdjustment: {
          currentOptimal: data.difficulty_adjustment.current_optimal,
          suggestedRange: data.difficulty_adjustment.suggested_range,
          progressionStrategy: data.difficulty_adjustment.progression_strategy,
          description: data.difficulty_adjustment.description,
          challengeMode: data.difficulty_adjustment.challenge_mode
        },
        studySchedule: {
          recommendedDuration: data.study_schedule.recommended_duration,
          optimalTimeSlots: data.study_schedule.optimal_time_slots,
          frequency: data.study_schedule.frequency,
          focusDistribution: data.study_schedule.focus_distribution,
          note: data.study_schedule.note
        },
        battleStrategies: data.battle_strategies,
        goals: {
          shortTerm: data.goals.short_term,
          mediumTerm: data.goals.medium_term,
          longTerm: data.goals.long_term
        },
        confidenceScore: data.confidence_score,
        generatedAt: data.generated_at
      });
    } catch (err) {
      setError('Error al cargar recomendaciones');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };
  
  const refreshRecommendations = async () => {
    setRefreshing(true);
    
    try {
      await axios.post(
        `${API_URL}/api/v1/recommendations/refresh`,
        {},
        { headers: getAuthHeaders() }
      );
      
      await fetchRecommendations();
    } catch (err) {
      console.error('Error refreshing recommendations:', err);
    } finally {
      setRefreshing(false);
    }
  };
  
  useEffect(() => {
    fetchRecommendations();
  }, []);
  
  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high': return 'text-red-400 bg-red-900/20 border-red-500/30';
      case 'medium': return 'text-yellow-400 bg-yellow-900/20 border-yellow-500/30';
      case 'low': return 'text-green-400 bg-green-900/20 border-green-500/30';
      default: return 'text-gray-400 bg-gray-900/20 border-gray-500/30';
    }
  };
  
  const getConfidenceColor = (score: number) => {
    if (score >= 0.8) return 'text-green-400';
    if (score >= 0.6) return 'text-yellow-400';
    return 'text-red-400';
  };
  
  const tabs = [
    { id: 'topics', label: 'Temas', icon: BookOpen },
    { id: 'difficulty', label: 'Dificultad', icon: TrendingUp },
    { id: 'schedule', label: 'Horario', icon: Calendar },
    { id: 'strategies', label: 'Estrategias', icon: Swords },
    { id: 'goals', label: 'Objetivos', icon: Target }
  ];
  
  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
        >
          <Brain className="w-12 h-12 text-purple-400" />
        </motion.div>
      </div>
    );
  }
  
  if (error || !recommendations) {
    return (
      <div className="bg-red-900/20 rounded-lg p-6 border border-red-500/30">
        <div className="flex items-center gap-3">
          <AlertCircle className="w-6 h-6 text-red-400" />
          <p className="text-red-400">{error || 'No hay recomendaciones disponibles'}</p>
        </div>
        <button
          onClick={fetchRecommendations}
          className="mt-4 px-4 py-2 bg-red-600 hover:bg-red-700 text-white 
            rounded-lg transition-all"
        >
          Reintentar
        </button>
      </div>
    );
  }
  
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-gray-900/80 rounded-lg p-6 border border-purple-500/30">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <Brain className="w-8 h-8 text-purple-400" />
            <div>
              <h2 className="text-2xl font-bold text-white">
                Recomendaciones Adaptativas
              </h2>
              <p className="text-gray-400 text-sm">
                Personalizadas según tu rendimiento
              </p>
            </div>
          </div>
          
          <button
            onClick={refreshRecommendations}
            disabled={refreshing}
            className="p-2 bg-purple-600 hover:bg-purple-700 rounded-lg 
              transition-all disabled:opacity-50"
          >
            <RefreshCw className={`w-5 h-5 text-white ${refreshing ? 'animate-spin' : ''}`} />
          </button>
        </div>
        
        {/* Confidence Score */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <BarChart3 className="w-5 h-5 text-gray-400" />
            <span className="text-gray-400 text-sm">Confianza:</span>
            <span className={`font-semibold ${getConfidenceColor(recommendations.confidenceScore)}`}>
              {(recommendations.confidenceScore * 100).toFixed(0)}%
            </span>
          </div>
          
          <p className="text-xs text-gray-500">
            Actualizado {new Date(recommendations.generatedAt).toLocaleDateString()}
          </p>
        </div>
      </div>
      
      {/* Tabs */}
      <div className="bg-gray-900/80 rounded-lg p-1 flex flex-wrap gap-1">
        {tabs.map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex-1 min-w-[120px] flex items-center justify-center gap-2 
              px-4 py-3 rounded-lg transition-all ${
              activeTab === tab.id
                ? 'bg-purple-600 text-white'
                : 'text-gray-400 hover:text-white hover:bg-gray-800'
            }`}
          >
            <tab.icon className="w-5 h-5" />
            <span className="text-sm font-semibold">{tab.label}</span>
          </button>
        ))}
      </div>
      
      {/* Tab Content */}
      <AnimatePresence mode="wait">
        <motion.div
          key={activeTab}
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: -20 }}
          transition={{ duration: 0.2 }}
        >
          {/* Topics Tab */}
          {activeTab === 'topics' && (
            <div className="space-y-4">
              {recommendations.nextTopics.map((topic, index) => (
                <motion.div
                  key={topic.topic}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.1 }}
                  className={`bg-gray-900/80 rounded-lg p-4 border ${getPriorityColor(topic.priority)}`}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <h3 className="text-lg font-semibold text-white">
                          {topic.topic}
                        </h3>
                        <span className={`px-2 py-1 rounded text-xs font-semibold 
                          ${getPriorityColor(topic.priority)}`}>
                          {topic.priority === 'high' ? 'Alta' : 
                           topic.priority === 'medium' ? 'Media' : 'Baja'} Prioridad
                        </span>
                      </div>
                      
                      <p className="text-gray-400 text-sm mb-3">{topic.reason}</p>
                      
                      <div className="flex items-center gap-4 text-sm">
                        <div className="flex items-center gap-1">
                          <Target className="w-4 h-4 text-purple-400" />
                          <span className="text-gray-300">
                            {topic.suggestedQuestions} preguntas
                          </span>
                        </div>
                        
                        <div className="flex items-center gap-1">
                          <Clock className="w-4 h-4 text-blue-400" />
                          <span className="text-gray-300">
                            {topic.estimatedTime}
                          </span>
                        </div>
                      </div>
                    </div>
                    
                    <ChevronRight className="w-5 h-5 text-gray-500" />
                  </div>
                </motion.div>
              ))}
            </div>
          )}
          
          {/* Difficulty Tab */}
          {activeTab === 'difficulty' && (
            <div className="bg-gray-900/80 rounded-lg p-6 border border-purple-500/30">
              <div className="space-y-6">
                <div className="text-center">
                  <h3 className="text-xl font-semibold text-white mb-2">
                    Dificultad Óptima Actual
                  </h3>
                  <div className="inline-flex items-center justify-center w-24 h-24 
                    bg-purple-600 rounded-full">
                    <span className="text-3xl font-bold text-white">
                      {recommendations.difficultyAdjustment.currentOptimal}
                    </span>
                  </div>
                </div>
                
                <div className="bg-gray-800/50 rounded-lg p-4">
                  <h4 className="font-semibold text-white mb-2">
                    Rango Sugerido
                  </h4>
                  <div className="flex items-center gap-4">
                    <span className="text-gray-400">Min:</span>
                    <span className="text-2xl font-bold text-blue-400">
                      {recommendations.difficultyAdjustment.suggestedRange.min}
                    </span>
                    <span className="text-gray-400">-</span>
                    <span className="text-2xl font-bold text-green-400">
                      {recommendations.difficultyAdjustment.suggestedRange.max}
                    </span>
                    <span className="text-gray-400">:Max</span>
                  </div>
                </div>
                
                <div>
                  <h4 className="font-semibold text-white mb-2">
                    Estrategia de Progresión
                  </h4>
                  <p className="text-gray-300 leading-relaxed">
                    {recommendations.difficultyAdjustment.description}
                  </p>
                </div>
                
                {recommendations.difficultyAdjustment.challengeMode && (
                  <div className="bg-purple-900/20 rounded-lg p-4 border 
                    border-purple-500/30">
                    <div className="flex items-center gap-2 mb-2">
                      <Zap className="w-5 h-5 text-purple-400" />
                      <span className="font-semibold text-purple-400">
                        Modo Desafío Disponible
                      </span>
                    </div>
                    <p className="text-sm text-gray-300">
                      Estás preparado para enfrentar desafíos de mayor dificultad
                    </p>
                  </div>
                )}
              </div>
            </div>
          )}
          
          {/* Schedule Tab */}
          {activeTab === 'schedule' && (
            <div className="space-y-6">
              <div className="bg-gray-900/80 rounded-lg p-6 border border-blue-500/30">
                <h3 className="text-xl font-semibold text-white mb-4">
                  Horario de Estudio Recomendado
                </h3>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                  <div className="bg-gray-800/50 rounded-lg p-4">
                    <p className="text-gray-400 text-sm mb-1">Duración diaria</p>
                    <p className="text-2xl font-bold text-white">
                      {recommendations.studySchedule.recommendedDuration}
                    </p>
                  </div>
                  
                  <div className="bg-gray-800/50 rounded-lg p-4">
                    <p className="text-gray-400 text-sm mb-1">Frecuencia</p>
                    <p className="text-2xl font-bold text-white capitalize">
                      {recommendations.studySchedule.frequency}
                    </p>
                  </div>
                </div>
                
                <div className="mb-6">
                  <h4 className="font-semibold text-white mb-3">
                    Mejores Horarios
                  </h4>
                  <div className="space-y-2">
                    {recommendations.studySchedule.optimalTimeSlots.map((slot, index) => (
                      <div
                        key={index}
                        className="flex items-center justify-between bg-gray-800/50 
                          rounded-lg p-3"
                      >
                        <div className="flex items-center gap-3">
                          <Clock className="w-5 h-5 text-blue-400" />
                          <span className="text-white font-semibold">
                            {slot.time}
                          </span>
                          <span className="text-gray-400 text-sm">
                            ({slot.period})
                          </span>
                        </div>
                        
                        <span className={`px-2 py-1 rounded text-xs font-semibold ${
                          slot.effectiveness === 'alta' 
                            ? 'bg-green-900/20 text-green-400'
                            : 'bg-yellow-900/20 text-yellow-400'
                        }`}>
                          Efectividad {slot.effectiveness}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
                
                {recommendations.studySchedule.note && (
                  <div className="bg-blue-900/20 rounded-lg p-4 border 
                    border-blue-500/30">
                    <p className="text-blue-300 text-sm">
                      💡 {recommendations.studySchedule.note}
                    </p>
                  </div>
                )}
              </div>
            </div>
          )}
          
          {/* Strategies Tab */}
          {activeTab === 'strategies' && (
            <div className="space-y-4">
              {recommendations.battleStrategies.map((strategy, index) => (
                <motion.div
                  key={strategy.name}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.1 }}
                  className="bg-gray-900/80 rounded-lg p-6 border border-green-500/30"
                >
                  <div className="flex items-start gap-4">
                    <div className="p-3 bg-green-900/30 rounded-lg">
                      <Swords className="w-6 h-6 text-green-400" />
                    </div>
                    
                    <div className="flex-1">
                      <h3 className="text-xl font-semibold text-white mb-2">
                        {strategy.name}
                      </h3>
                      
                      <p className="text-gray-300 mb-4">
                        {strategy.description}
                      </p>
                      
                      <div className="space-y-2 mb-4">
                        {strategy.tips.map((tip, tipIndex) => (
                          <div key={tipIndex} className="flex items-start gap-2">
                            <span className="text-green-400 mt-0.5">•</span>
                            <p className="text-sm text-gray-300">{tip}</p>
                          </div>
                        ))}
                      </div>
                      
                      {strategy.expectedImprovement && (
                        <div className="bg-green-900/20 rounded-lg px-3 py-2 
                          inline-flex items-center gap-2">
                          <TrendingUp className="w-4 h-4 text-green-400" />
                          <span className="text-sm text-green-400">
                            {strategy.expectedImprovement}
                          </span>
                        </div>
                      )}
                    </div>
                  </div>
                </motion.div>
              ))}
            </div>
          )}
          
          {/* Goals Tab */}
          {activeTab === 'goals' && (
            <div className="space-y-6">
              {/* Short Term Goals */}
              <div className="bg-gray-900/80 rounded-lg p-6 border border-yellow-500/30">
                <h3 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
                  <Award className="w-6 h-6 text-yellow-400" />
                  Objetivos a Corto Plazo (1 semana)
                </h3>
                <div className="space-y-4">
                  {recommendations.goals.shortTerm.map((goal, index) => (
                    <GoalCard key={index} goal={goal} type="short" />
                  ))}
                </div>
              </div>
              
              {/* Medium Term Goals */}
              <div className="bg-gray-900/80 rounded-lg p-6 border border-blue-500/30">
                <h3 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
                  <Target className="w-6 h-6 text-blue-400" />
                  Objetivos a Mediano Plazo (1 mes)
                </h3>
                <div className="space-y-4">
                  {recommendations.goals.mediumTerm.map((goal, index) => (
                    <GoalCard key={index} goal={goal} type="medium" />
                  ))}
                </div>
              </div>
              
              {/* Long Term Goals */}
              <div className="bg-gray-900/80 rounded-lg p-6 border border-purple-500/30">
                <h3 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
                  <TrendingUp className="w-6 h-6 text-purple-400" />
                  Objetivos a Largo Plazo (3 meses)
                </h3>
                <div className="space-y-4">
                  {recommendations.goals.longTerm.map((goal, index) => (
                    <GoalCard key={index} goal={goal} type="long" />
                  ))}
                </div>
              </div>
            </div>
          )}
        </motion.div>
      </AnimatePresence>
    </div>
  );
}

// Goal Card Component
function GoalCard({ goal, type }: { goal: Goal; type: 'short' | 'medium' | 'long' }) {
  const getTypeColor = () => {
    switch (type) {
      case 'short': return 'bg-yellow-900/20 border-yellow-500/30';
      case 'medium': return 'bg-blue-900/20 border-blue-500/30';
      case 'long': return 'bg-purple-900/20 border-purple-500/30';
    }
  };
  
  return (
    <div className={`rounded-lg p-4 border ${getTypeColor()}`}>
      <h4 className="font-semibold text-white mb-2">{goal.goal}</h4>
      
      {(goal.current || goal.target) && (
        <div className="flex items-center gap-4 mb-3 text-sm">
          {goal.current && (
            <div>
              <span className="text-gray-400">Actual:</span>
              <span className="text-white ml-1">{goal.current}</span>
            </div>
          )}
          {goal.target && (
            <div>
              <span className="text-gray-400">Meta:</span>
              <span className="text-green-400 ml-1">{goal.target}</span>
            </div>
          )}
        </div>
      )}
      
      <div className="space-y-1 mb-3">
        {goal.actions.map((action, index) => (
          <div key={index} className="flex items-start gap-2">
            <ChevronRight className="w-4 h-4 text-gray-500 mt-0.5" />
            <p className="text-sm text-gray-300">{action}</p>
          </div>
        ))}
      </div>
      
      <div className="flex items-center gap-2 text-sm">
        <Clock className="w-4 h-4 text-gray-400" />
        <span className="text-gray-400">Plazo: {goal.deadline}</span>
      </div>
    </div>
  );
}