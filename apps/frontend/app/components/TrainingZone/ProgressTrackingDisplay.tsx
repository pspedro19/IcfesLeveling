'use client';

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  TrendingUp, 
  Target, 
  Clock, 
  Star, 
  Trophy, 
  Flame,
  Zap,
  Brain,
  BarChart3,
  Calendar,
  Award,
  CheckCircle,
  Activity,
  Sparkles
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";

interface ProgressData {
  overall: {
    mastery_percentage: number;
    accuracy: number;
    total_questions: number;
    mastered_questions: number;
    streak: number;
    max_streak: number;
    level: number;
    experience_points: number;
    next_level_xp: number;
  };
  daily: {
    questions_answered: number;
    accuracy: number;
    time_spent: number;
    streak: number;
    points_earned: number;
  };
  weekly: {
    sessions_completed: number;
    avg_accuracy: number;
    total_time: number;
    improvement_rate: number;
    consistency_score: number;
  };
  spaced_repetition: {
    due_today: number;
    overdue: number;
    mastered: number;
    learning: number;
    retention_rate: number;
  };
  achievements: Array<{
    id: string;
    name: string;
    description: string;
    icon: string;
    earned_at: string;
    rarity: 'common' | 'rare' | 'epic' | 'legendary';
    points: number;
  }>;
}

interface ProgressTrackingDisplayProps {
  data: ProgressData;
  subjectName: string;
  onRefresh?: () => void;
  isRefreshing?: boolean;
}

const rarityColors = {
  common: 'from-gray-400 to-gray-600',
  rare: 'from-blue-400 to-blue-600',
  epic: 'from-purple-400 to-purple-600',
  legendary: 'from-yellow-400 to-orange-500'
};

const rarityGlow = {
  common: 'shadow-gray-200',
  rare: 'shadow-blue-200',
  epic: 'shadow-purple-200',
  legendary: 'shadow-yellow-200'
};

export default function ProgressTrackingDisplay({
  data,
  subjectName,
  onRefresh,
  isRefreshing = false
}: ProgressTrackingDisplayProps) {
  const [selectedMetric, setSelectedMetric] = useState<'accuracy' | 'speed' | 'consistency'>('accuracy');
  const [animateProgress, setAnimateProgress] = useState(false);

  useEffect(() => {
    setAnimateProgress(true);
    const timer = setTimeout(() => setAnimateProgress(false), 1000);
    return () => clearTimeout(timer);
  }, [data]);

  const calculateLevelProgress = () => {
    const currentLevelXP = data.overall.experience_points % data.overall.next_level_xp;
    return (currentLevelXP / data.overall.next_level_xp) * 100;
  };

  const formatTime = (minutes: number) => {
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return hours > 0 ? `${hours}h ${mins}m` : `${mins}m`;
  };

  const getStreakColor = (streak: number) => {
    if (streak >= 30) return 'text-orange-500';
    if (streak >= 14) return 'text-red-500';
    if (streak >= 7) return 'text-yellow-500';
    return 'text-blue-500';
  };

  const getStreakEmoji = (streak: number) => {
    if (streak >= 30) return '🔥';
    if (streak >= 14) return '⚡';
    if (streak >= 7) return '✨';
    return '💪';
  };

  return (
    <div className="w-full space-y-6">
      {/* Header with level and XP */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="relative overflow-hidden"
      >
        <Card className="bg-gradient-to-r from-blue-600 via-purple-600 to-indigo-600 text-white">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div className="space-y-2">
                <h2 className="text-2xl font-bold flex items-center space-x-2">
                  <Brain className="h-8 w-8" />
                  <span>Progreso - {subjectName}</span>
                </h2>
                <div className="flex items-center space-x-4">
                  <div className="flex items-center space-x-2">
                    <Trophy className="h-5 w-5 text-yellow-300" />
                    <span className="text-lg font-semibold">Nivel {data.overall.level}</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Star className="h-5 w-5 text-yellow-300" />
                    <span>{data.overall.experience_points.toLocaleString()} XP</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Flame className={`h-5 w-5 ${getStreakColor(data.overall.streak)}`} />
                    <span>{data.overall.streak} días {getStreakEmoji(data.overall.streak)}</span>
                  </div>
                </div>
              </div>
              
              {/* Circular progress for level */}
              <div className="relative w-24 h-24">
                <svg className="w-24 h-24 transform -rotate-90" viewBox="0 0 100 100">
                  <circle
                    cx="50"
                    cy="50"
                    r="45"
                    stroke="rgba(255,255,255,0.2)"
                    strokeWidth="6"
                    fill="none"
                  />
                  <motion.circle
                    cx="50"
                    cy="50"
                    r="45"
                    stroke="white"
                    strokeWidth="6"
                    fill="none"
                    strokeLinecap="round"
                    strokeDasharray={`${2 * Math.PI * 45}`}
                    strokeDashoffset={`${2 * Math.PI * 45 * (1 - calculateLevelProgress() / 100)}`}
                    initial={{ strokeDashoffset: 2 * Math.PI * 45 }}
                    animate={{ strokeDashoffset: `${2 * Math.PI * 45 * (1 - calculateLevelProgress() / 100)}` }}
                    transition={{ duration: 1.5, ease: "easeOut" }}
                  />
                </svg>
                <div className="absolute inset-0 flex items-center justify-center">
                  <span className="text-lg font-bold">{Math.round(calculateLevelProgress())}%</span>
                </div>
              </div>
            </div>
            
            {/* Level progress bar */}
            <div className="mt-4 space-y-2">
              <div className="flex justify-between text-sm opacity-90">
                <span>Progreso al siguiente nivel</span>
                <span>{data.overall.next_level_xp - (data.overall.experience_points % data.overall.next_level_xp)} XP restante</span>
              </div>
              <div className="w-full bg-white/20 rounded-full h-2">
                <motion.div
                  className="bg-white h-2 rounded-full"
                  initial={{ width: 0 }}
                  animate={{ width: `${calculateLevelProgress()}%` }}
                  transition={{ duration: 1.5, ease: "easeOut" }}
                />
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Key metrics grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* Mastery Progress */}
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.1 }}
        >
          <Card className="hover:shadow-lg transition-shadow">
            <CardContent className="p-6">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center space-x-2">
                  <Target className="h-5 w-5 text-green-500" />
                  <span className="font-medium text-gray-700">Dominio</span>
                </div>
                <span className="text-2xl font-bold text-green-600">
                  {data.overall.mastery_percentage.toFixed(1)}%
                </span>
              </div>
              <Progress 
                value={data.overall.mastery_percentage} 
                className="h-2 mb-2"
              />
              <p className="text-sm text-gray-500">
                {data.overall.mastered_questions} de {data.overall.total_questions} preguntas dominadas
              </p>
            </CardContent>
          </Card>
        </motion.div>

        {/* Accuracy */}
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.2 }}
        >
          <Card className="hover:shadow-lg transition-shadow">
            <CardContent className="p-6">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center space-x-2">
                  <CheckCircle className="h-5 w-5 text-blue-500" />
                  <span className="font-medium text-gray-700">Precisión</span>
                </div>
                <span className="text-2xl font-bold text-blue-600">
                  {data.overall.accuracy.toFixed(1)}%
                </span>
              </div>
              <Progress 
                value={data.overall.accuracy} 
                className="h-2 mb-2"
              />
              <p className="text-sm text-gray-500">
                Promedio general
              </p>
            </CardContent>
          </Card>
        </motion.div>

        {/* Daily Progress */}
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.3 }}
        >
          <Card className="hover:shadow-lg transition-shadow">
            <CardContent className="p-6">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center space-x-2">
                  <Activity className="h-5 w-5 text-purple-500" />
                  <span className="font-medium text-gray-700">Hoy</span>
                </div>
                <span className="text-2xl font-bold text-purple-600">
                  {data.daily.questions_answered}
                </span>
              </div>
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span>Precisión</span>
                  <span className="font-medium">{data.daily.accuracy.toFixed(1)}%</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span>Tiempo</span>
                  <span className="font-medium">{formatTime(data.daily.time_spent)}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span>Puntos</span>
                  <span className="font-medium text-yellow-600">+{data.daily.points_earned}</span>
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Spaced Repetition */}
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.4 }}
        >
          <Card className="hover:shadow-lg transition-shadow">
            <CardContent className="p-6">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center space-x-2">
                  <Clock className="h-5 w-5 text-orange-500" />
                  <span className="font-medium text-gray-700">Repaso</span>
                </div>
                <span className="text-2xl font-bold text-orange-600">
                  {data.spaced_repetition.due_today}
                </span>
              </div>
              <div className="grid grid-cols-2 gap-2 text-sm">
                <div className="text-center p-2 bg-red-50 rounded">
                  <div className="font-bold text-red-600">{data.spaced_repetition.overdue}</div>
                  <div className="text-red-700">Atrasadas</div>
                </div>
                <div className="text-center p-2 bg-green-50 rounded">
                  <div className="font-bold text-green-600">{data.spaced_repetition.mastered}</div>
                  <div className="text-green-700">Dominadas</div>
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </div>

      {/* Weekly analysis */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Performance trends */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <BarChart3 className="h-5 w-5 text-blue-500" />
              <span>Análisis Semanal</span>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="text-center p-3 bg-blue-50 rounded-lg">
                <div className="text-2xl font-bold text-blue-600">{data.weekly.sessions_completed}</div>
                <div className="text-sm text-blue-700">Sesiones</div>
              </div>
              <div className="text-center p-3 bg-green-50 rounded-lg">
                <div className="text-2xl font-bold text-green-600">{data.weekly.avg_accuracy.toFixed(1)}%</div>
                <div className="text-sm text-green-700">Precisión promedio</div>
              </div>
            </div>
            
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-sm font-medium text-gray-700">Tasa de mejora</span>
                <div className="flex items-center space-x-2">
                  <TrendingUp className={`h-4 w-4 ${data.weekly.improvement_rate > 0 ? 'text-green-500' : 'text-red-500'}`} />
                  <span className={`font-bold ${data.weekly.improvement_rate > 0 ? 'text-green-600' : 'text-red-600'}`}>
                    {data.weekly.improvement_rate > 0 ? '+' : ''}{data.weekly.improvement_rate.toFixed(1)}%
                  </span>
                </div>
              </div>
              
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span>Consistencia</span>
                  <span>{data.weekly.consistency_score.toFixed(1)}%</span>
                </div>
                <Progress value={data.weekly.consistency_score} className="h-2" />
              </div>
              
              <div className="text-sm text-gray-600">
                <strong>Tiempo total:</strong> {formatTime(data.weekly.total_time)}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Recent achievements */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Award className="h-5 w-5 text-yellow-500" />
              <span>Logros Recientes</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {data.achievements.slice(0, 4).map((achievement, index) => (
                <motion.div
                  key={achievement.id}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.1 }}
                  className={`
                    flex items-center space-x-3 p-3 rounded-lg border-2 
                    bg-gradient-to-r ${rarityColors[achievement.rarity]} 
                    ${rarityGlow[achievement.rarity]} shadow-lg
                  `}
                >
                  <div className="text-2xl">{achievement.icon}</div>
                  <div className="flex-1">
                    <div className="font-semibold text-white">{achievement.name}</div>
                    <div className="text-sm text-gray-100 opacity-90">{achievement.description}</div>
                    <div className="flex items-center space-x-2 mt-1">
                      <Badge variant="secondary" className="text-xs">
                        {achievement.rarity}
                      </Badge>
                      <span className="text-xs text-gray-200">+{achievement.points} XP</span>
                    </div>
                  </div>
                  <div className="text-xs text-gray-200 opacity-75">
                    {new Date(achievement.earned_at).toLocaleDateString()}
                  </div>
                </motion.div>
              ))}
            </div>
            
            {data.achievements.length === 0 && (
              <div className="text-center py-8 text-gray-500">
                <Trophy className="h-12 w-12 mx-auto mb-3 opacity-30" />
                <p>¡Sigue practicando para desbloquear logros!</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Motivational section */}
      <Card className="bg-gradient-to-r from-purple-50 to-pink-50 border-purple-200">
        <CardContent className="p-6">
          <div className="flex items-center justify-between">
            <div className="space-y-2">
              <h3 className="text-lg font-semibold text-purple-800 flex items-center space-x-2">
                <Sparkles className="h-5 w-5" />
                <span>¡Sigue así!</span>
              </h3>
              <p className="text-purple-700">
                {data.overall.streak >= 7 
                  ? `¡Increíble! Has mantenido una racha de ${data.overall.streak} días. ¡Eres imparable! 🚀`
                  : data.daily.questions_answered >= 10
                  ? `¡Excelente trabajo hoy! Has respondido ${data.daily.questions_answered} preguntas.`
                  : `¡Continúa practicando! Cada pregunta te acerca más a tus objetivos.`
                }
              </p>
              <div className="flex items-center space-x-4 text-sm">
                <div className="flex items-center space-x-1">
                  <Target className="h-4 w-4 text-purple-600" />
                  <span>Meta diaria: 10 preguntas</span>
                </div>
                <div className="flex items-center space-x-1">
                  <Flame className="h-4 w-4 text-orange-500" />
                  <span>Próxima meta: {data.overall.max_streak + 1} días</span>
                </div>
              </div>
            </div>
            
            <div className="text-6xl opacity-80">
              {data.overall.streak >= 30 ? '🏆' :
               data.overall.streak >= 14 ? '🔥' :
               data.overall.streak >= 7 ? '⭐' : '💪'}
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}