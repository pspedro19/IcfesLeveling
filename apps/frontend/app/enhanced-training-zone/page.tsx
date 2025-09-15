'use client';

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Brain, 
  Play, 
  Settings,
  BarChart3,
  Trophy,
  Target,
  Zap,
  Calendar,
  ArrowLeft,
  Sparkles,
  Users,
  BookOpen,
  Video
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

// Import our custom components
import InteractiveQuestionCard from '@/components/TrainingZone/InteractiveQuestionCard';
import ProgressTrackingDisplay from '@/components/TrainingZone/ProgressTrackingDisplay';
import AIExplanationPanel from '@/components/TrainingZone/AIExplanationPanel';
import VideoIntegrationComponent from '@/components/TrainingZone/VideoIntegrationComponent';
import GamifiedExperienceHub from '@/components/TrainingZone/GamifiedExperienceHub';

// Types
interface Question {
  id: string;
  statement: string;
  options: {
    A: string;
    B: string;
    C: string;
    D: string;
  };
  correct_answer: string;
  topic?: string;
  difficulty?: 'easy' | 'medium' | 'hard';
  estimated_time?: string;
  explanation?: string;
  hints?: string[];
}

interface TrainingSession {
  id: string;
  mode: string;
  questions: Question[];
  current_index: number;
  answers: { [questionId: string]: string };
  start_time: Date;
  streak: number;
  combo_multiplier: number;
  health_points: number;
  max_health: number;
}

const trainingModes = [
  {
    id: 'recovery',
    name: 'Recovery Mode',
    description: '20 prioritized questions based on recency and severity',
    duration: 30,
    questions: 20,
    icon: Target,
    color: 'from-blue-500 to-blue-700'
  },
  {
    id: 'sprint',
    name: 'Sprint Mode', 
    description: 'Quick 10-minute session with critical questions',
    duration: 10,
    questions: 10,
    icon: Zap,
    color: 'from-red-500 to-red-700'
  },
  {
    id: 'spaced_rep',
    name: 'Spaced Repetition',
    description: 'Scientifically optimized review schedule',
    duration: 25,
    questions: 15,
    icon: Brain,
    color: 'from-purple-500 to-purple-700'
  }
];

// Mock data generators
const mockQuestion: Question = {
  id: '1',
  statement: '¿Cuál es el resultado de la integral ∫(2x + 3)dx?',
  options: {
    A: 'x² + 3x + C',
    B: '2x² + 3x + C', 
    C: 'x² + 6x + C',
    D: '2x + 3 + C'
  },
  correct_answer: 'A',
  topic: 'Cálculo Integral',
  difficulty: 'medium',
  estimated_time: '2 min',
  hints: [
    'Recuerda que la integral de una suma es la suma de las integrales',
    'La integral de ax es (a/2)x² + C',
    'No olvides la constante de integración'
  ]
};

const mockProgressData = {
  overall: {
    mastery_percentage: 67.5,
    accuracy: 78.2,
    total_questions: 150,
    mastered_questions: 101,
    streak: 12,
    max_streak: 25,
    level: 8,
    experience_points: 15420,
    next_level_xp: 18000
  },
  daily: {
    questions_answered: 8,
    accuracy: 87.5,
    time_spent: 45,
    streak: 3,
    points_earned: 850
  },
  weekly: {
    sessions_completed: 5,
    avg_accuracy: 82.1,
    total_time: 180,
    improvement_rate: 5.2,
    consistency_score: 91.3
  },
  spaced_repetition: {
    due_today: 12,
    overdue: 3,
    mastered: 89,
    learning: 24,
    retention_rate: 94.2
  },
  achievements: [
    {
      id: '1',
      name: 'Streak Master',
      description: '10 días consecutivos de práctica',
      icon: '🔥',
      earned_at: '2024-01-15',
      rarity: 'rare' as const,
      points: 500
    },
    {
      id: '2', 
      name: 'Perfect Score',
      description: '100% de precisión en una sesión',
      icon: '🎯',
      earned_at: '2024-01-14',
      rarity: 'epic' as const,
      points: 1000
    }
  ]
};

const mockGamificationData = {
  achievements: [
    {
      id: '1',
      name: 'Primer Paso',
      description: 'Completa tu primera sesión de entrenamiento',
      icon: '🚀',
      rarity: 'common' as const,
      category: 'milestone' as const,
      points: 100,
      progress: 1,
      max_progress: 1,
      unlocked: true,
      unlocked_at: '2024-01-10',
      conditions: ['Complete 1 training session']
    },
    {
      id: '2',
      name: 'Racha de Fuego',
      description: 'Mantén una racha de 7 días',
      icon: '🔥',
      rarity: 'rare' as const,
      category: 'streak' as const,
      points: 500,
      progress: 12,
      max_progress: 7,
      unlocked: true,
      unlocked_at: '2024-01-15',
      conditions: ['7 day streak']
    },
    {
      id: '3',
      name: 'Maestro de la Precisión',
      description: 'Logra 90% de precisión en 10 sesiones',
      icon: '🎯',
      rarity: 'epic' as const,
      category: 'accuracy' as const,
      points: 1000,
      progress: 7,
      max_progress: 10,
      unlocked: false,
      conditions: ['90% accuracy in 10 sessions']
    }
  ],
  streaks: {
    daily_practice: {
      current: 12,
      best: 25,
      type: 'daily' as const,
      next_milestone: 14,
      milestone_reward: { points: 200 }
    },
    correct_answers: {
      current: 8,
      best: 15,
      type: 'correct_answers' as const,
      next_milestone: 10,
      milestone_reward: { points: 150 }
    },
    perfect_sessions: {
      current: 2,
      best: 4,
      type: 'perfect_sessions' as const,
      next_milestone: 3,
      milestone_reward: { points: 300 }
    }
  },
  level_system: {
    current_level: 8,
    current_xp: 15420,
    xp_to_next_level: 18000,
    total_xp: 47820,
    level_rewards: [
      { level: 9, reward_type: 'badge' as const, reward_value: 'Gold Star', unlocked: false },
      { level: 10, reward_type: 'feature' as const, reward_value: 'Custom Themes', unlocked: false }
    ]
  },
  motivational_content: {
    daily_goal: {
      target: 10,
      current: 8,
      type: 'questions' as const,
      reward_points: 100,
      completed: false
    },
    weekly_challenge: {
      name: 'Dominio Matemático',
      description: 'Domina 15 preguntas de matemáticas esta semana',
      progress: 11,
      max_progress: 15,
      reward: { points: 500 },
      time_left: '2 días'
    },
    motivational_message: {
      message: '¡Increíble progreso! Estás a solo 2 respuestas de tu meta diaria. ¡Sigue así!',
      type: 'encouragement' as const,
      context: 'Cerca de completar meta diaria'
    }
  }
};

const mockVideoRecommendations = [
  {
    id: '1',
    title: 'Integrales: Conceptos Fundamentales y Técnicas Básicas',
    description: 'Aprende los conceptos básicos de integración con ejemplos paso a paso',
    url: 'https://youtube.com/watch?v=example1',
    thumbnail: '/api/placeholder/320/180',
    duration: '15:42',
    channel: 'Matemáticas Explicadas',
    views: '125K',
    rating: 4.8,
    relevance_score: 0.95,
    topic: 'Cálculo Integral',
    difficulty: 'intermediate' as const,
    created_at: '2024-01-10',
    user_interactions: {
      viewed: false,
      liked: false,
      bookmarked: false,
      completion_percentage: 0
    }
  },
  {
    id: '2',
    title: 'Resolución de Integrales por Sustitución',
    description: 'Domina la técnica de sustitución para resolver integrales complejas',
    url: 'https://youtube.com/watch?v=example2',
    thumbnail: '/api/placeholder/320/180',
    duration: '22:15',
    channel: 'Calculus Master',
    views: '89K',
    rating: 4.9,
    relevance_score: 0.88,
    topic: 'Cálculo Integral',
    difficulty: 'advanced' as const,
    created_at: '2024-01-08',
    user_interactions: {
      viewed: true,
      liked: true,
      bookmarked: false,
      completion_percentage: 65
    }
  }
];

export default function EnhancedTrainingZonePage() {
  const [activeView, setActiveView] = useState<'modes' | 'session' | 'progress' | 'gamification'>('modes');
  const [selectedSubject, setSelectedSubject] = useState('mathematics');
  const [currentSession, setCurrentSession] = useState<TrainingSession | null>(null);
  const [showExplanation, setShowExplanation] = useState(false);
  const [currentExplanation, setCurrentExplanation] = useState<any>(null);
  const [showVideos, setShowVideos] = useState(false);

  const subjects = [
    { id: 'mathematics', name: 'Matemáticas', icon: '📐' },
    { id: 'physics', name: 'Física', icon: '⚡' },
    { id: 'chemistry', name: 'Química', icon: '🧪' },
    { id: 'biology', name: 'Biología', icon: '🧬' },
    { id: 'language', name: 'Lenguaje', icon: '📚' }
  ];

  const startTrainingSession = (modeId: string) => {
    const mode = trainingModes.find(m => m.id === modeId);
    if (!mode) return;

    const session: TrainingSession = {
      id: Date.now().toString(),
      mode: modeId,
      questions: [mockQuestion], // In real app, fetch based on mode
      current_index: 0,
      answers: {},
      start_time: new Date(),
      streak: 12,
      combo_multiplier: 1.5,
      health_points: 85,
      max_health: 100
    };

    setCurrentSession(session);
    setActiveView('session');
  };

  const handleQuestionAnswer = async (answer: string, timeSpent: number, hintsUsed: number) => {
    if (!currentSession) return;

    const currentQ = currentSession.questions[currentSession.current_index];
    const isCorrect = answer === currentQ.correct_answer;

    // Update session
    const updatedSession = {
      ...currentSession,
      answers: {
        ...currentSession.answers,
        [currentQ.id]: answer
      }
    };
    setCurrentSession(updatedSession);

    // Get AI explanation
    const mockExplanation = {
      id: '1',
      explanation: isCorrect 
        ? 'Excelente! La integral de 2x + 3 es x² + 3x + C. La integral de 2x es x² (aplicando la regla de potencias) y la integral de 3 es 3x. No olvides agregar la constante de integración C.'
        : 'La respuesta correcta es A. Para resolver esta integral, debes aplicar la regla de linealidad: la integral de una suma es la suma de las integrales. ∫(2x)dx = x² y ∫(3)dx = 3x, por lo tanto ∫(2x + 3)dx = x² + 3x + C.',
      confidence_score: 0.92,
      explanation_type: isCorrect ? 'conceptual' : 'error_analysis',
      difficulty_level: 'detailed',
      key_concepts: ['Regla de linealidad', 'Regla de potencias', 'Constante de integración'],
      common_mistakes: ['Olvidar la constante C', 'Confundir con la derivada', 'Error en la regla de potencias'],
      study_tips: ['Practica con más integrales básicas', 'Revisa la tabla de integrales', 'Verifica siempre derivando el resultado'],
      related_topics: ['Derivadas', 'Teorema fundamental del cálculo'],
      video_recommendations: mockVideoRecommendations.slice(0, 2)
    };

    setCurrentExplanation(mockExplanation);
    setShowExplanation(true);
  };

  const handleRequestHint = async (): Promise<string> => {
    const hints = mockQuestion.hints || [];
    const randomHint = hints[Math.floor(Math.random() * hints.length)];
    return randomHint;
  };

  const handleVideoInteraction = (videoId: string, interaction: any) => {
    console.log('Video interaction:', videoId, interaction);
    // In real app, track video interactions
  };

  const handleGamificationAction = async (actionType: string, data?: any) => {
    console.log('Gamification action:', actionType, data);
    // In real app, handle achievements, sharing, etc.
  };

  const currentQuestion = currentSession?.questions[currentSession.current_index];

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              {activeView !== 'modes' && (
                <Button
                  onClick={() => {
                    if (activeView === 'session') {
                      setCurrentSession(null);
                      setShowExplanation(false);
                    }
                    setActiveView('modes');
                  }}
                  variant="ghost"
                  size="sm"
                >
                  <ArrowLeft className="h-4 w-4 mr-2" />
                  Volver
                </Button>
              )}
              
              <div className="h-12 w-12 rounded-xl bg-gradient-to-br from-blue-600 to-purple-600 flex items-center justify-center">
                <Brain className="h-6 w-6 text-white" />
              </div>
              
              <div>
                <h1 className="text-2xl font-bold text-gray-900">
                  Training Zone Avanzado
                </h1>
                <p className="text-sm text-gray-600">
                  Entrenamiento personalizado e inteligente
                </p>
              </div>
            </div>

            {/* Subject selector */}
            <div className="flex items-center space-x-4">
              <select
                value={selectedSubject}
                onChange={(e) => setSelectedSubject(e.target.value)}
                className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                {subjects.map(subject => (
                  <option key={subject.id} value={subject.id}>
                    {subject.icon} {subject.name}
                  </option>
                ))}
              </select>
              
              <Button variant="outline" size="sm">
                <Settings className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto p-6">
        <AnimatePresence mode="wait">
          {/* Training Modes Selection */}
          {activeView === 'modes' && (
            <motion.div
              key="modes"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="space-y-8"
            >
              {/* Quick navigation */}
              <div className="flex justify-center space-x-4">
                <Button
                  onClick={() => setActiveView('progress')}
                  variant="outline"
                  className="flex items-center space-x-2"
                >
                  <BarChart3 className="h-4 w-4" />
                  <span>Mi Progreso</span>
                </Button>
                <Button
                  onClick={() => setActiveView('gamification')}
                  variant="outline"
                  className="flex items-center space-x-2"
                >
                  <Trophy className="h-4 w-4" />
                  <span>Logros</span>
                </Button>
                <Button
                  onClick={() => setShowVideos(true)}
                  variant="outline"
                  className="flex items-center space-x-2"
                >
                  <Video className="h-4 w-4" />
                  <span>Videos</span>
                </Button>
              </div>

              {/* Training modes grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                {trainingModes.map((mode) => {
                  const Icon = mode.icon;
                  return (
                    <motion.div
                      key={mode.id}
                      whileHover={{ y: -8, scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                    >
                      <Card className="h-full cursor-pointer hover:shadow-xl transition-all duration-300 border-0 bg-white/80 backdrop-blur-sm">
                        <CardContent className="p-8">
                          <div className="text-center space-y-6">
                            {/* Icon */}
                            <div className={`w-20 h-20 rounded-2xl bg-gradient-to-r ${mode.color} mx-auto flex items-center justify-center shadow-lg`}>
                              <Icon className="h-10 w-10 text-white" />
                            </div>
                            
                            {/* Content */}
                            <div>
                              <h3 className="text-2xl font-bold text-gray-900 mb-2">
                                {mode.name}
                              </h3>
                              <p className="text-gray-600 mb-4">
                                {mode.description}
                              </p>
                              
                              <div className="flex justify-center space-x-4 mb-6">
                                <Badge variant="secondary" className="px-3 py-1">
                                  {mode.duration} min
                                </Badge>
                                <Badge variant="secondary" className="px-3 py-1">
                                  {mode.questions} preguntas
                                </Badge>
                              </div>
                            </div>
                            
                            <Button
                              onClick={() => startTrainingSession(mode.id)}
                              className="w-full bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white font-semibold py-3 rounded-xl shadow-lg"
                            >
                              <Play className="h-5 w-5 mr-2" />
                              Comenzar Entrenamiento
                            </Button>
                          </div>
                        </CardContent>
                      </Card>
                    </motion.div>
                  );
                })}
              </div>
            </motion.div>
          )}

          {/* Training Session View */}
          {activeView === 'session' && currentSession && currentQuestion && (
            <motion.div
              key="session"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              className="space-y-6"
            >
              <InteractiveQuestionCard
                question={currentQuestion}
                onAnswer={handleQuestionAnswer}
                onRequestHint={handleRequestHint}
                showResult={showExplanation}
                userAnswer={currentSession.answers[currentQuestion.id]}
                streakCount={currentSession.streak}
                comboMultiplier={currentSession.combo_multiplier}
                healthPoints={currentSession.health_points}
                maxHealth={currentSession.max_health}
              />

              {/* AI Explanation */}
              {showExplanation && currentExplanation && (
                <AIExplanationPanel
                  explanation={currentExplanation}
                  questionId={currentQuestion.id}
                  userAnswer={currentSession.answers[currentQuestion.id]}
                  correctAnswer={currentQuestion.correct_answer}
                  onFeedback={async (feedback) => {
                    console.log('AI feedback:', feedback);
                  }}
                  onRequestNewExplanation={async (type) => {
                    // Mock returning same explanation
                    return currentExplanation;
                  }}
                />
              )}

              {/* Video recommendations */}
              {showExplanation && (
                <VideoIntegrationComponent
                  recommendations={mockVideoRecommendations}
                  questionId={currentQuestion.id}
                  topic={currentQuestion.topic || 'Matemáticas'}
                  onVideoInteraction={handleVideoInteraction}
                />
              )}
            </motion.div>
          )}

          {/* Progress View */}
          {activeView === 'progress' && (
            <motion.div
              key="progress"
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 1.05 }}
            >
              <ProgressTrackingDisplay
                data={mockProgressData}
                subjectName="Matemáticas"
              />
            </motion.div>
          )}

          {/* Gamification View */}
          {activeView === 'gamification' && (
            <motion.div
              key="gamification"
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 1.05 }}
            >
              <GamifiedExperienceHub
                achievements={mockGamificationData.achievements}
                streaks={mockGamificationData.streaks}
                level_system={mockGamificationData.level_system}
                motivational_content={mockGamificationData.motivational_content}
                onClaimReward={async (rewardId) => handleGamificationAction('claim_reward', { rewardId })}
                onShareAchievement={(achievementId) => handleGamificationAction('share_achievement', { achievementId })}
              />
            </motion.div>
          )}

          {/* Video Modal */}
          {showVideos && (
            <motion.div
              key="videos"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4"
            >
              <div className="bg-white rounded-2xl max-w-6xl w-full max-h-[90vh] overflow-hidden">
                <div className="p-6 border-b flex items-center justify-between">
                  <h2 className="text-2xl font-bold">Videos Recomendados</h2>
                  <Button
                    onClick={() => setShowVideos(false)}
                    variant="outline"
                    size="sm"
                  >
                    Cerrar
                  </Button>
                </div>
                <div className="p-6 overflow-y-auto max-h-[calc(90vh-100px)]">
                  <VideoIntegrationComponent
                    recommendations={mockVideoRecommendations}
                    questionId="general"
                    topic="Matemáticas"
                    onVideoInteraction={handleVideoInteraction}
                  />
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}