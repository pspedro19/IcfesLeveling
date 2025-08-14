'use client';

import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { 
  Trophy, 
  Star, 
  Target, 
  TrendingUp, 
  Calendar, 
  Eye, 
  EyeOff,
  Award,
  Zap,
  Crown,
  Shield,
  BookOpen
} from 'lucide-react';

interface Achievement {
  id: string;
  title: string;
  description: string;
  category: string;
  achievement_type: string;
  icon_url?: string;
  rarity: string;
  points: number;
  requirements: Record<string, any>;
  is_secret: boolean;
  is_active: boolean;
  created_at: string;
}

interface UserAchievement {
  id: string;
  user_id: string;
  achievement_id: string;
  progress: number;
  is_unlocked: boolean;
  unlocked_at?: string;
  progress_data: Record<string, any>;
  created_at: string;
  achievement: Achievement;
  progress_percentage: number;
}

interface AchievementSummary {
  total_achievements: number;
  unlocked_achievements: number;
  total_points: number;
  secret_achievements_found: number;
  achievements_by_category: Record<string, number>;
  recent_achievements: UserAchievement[];
}

const rarityColors = {
  common: 'bg-gray-500',
  rare: 'bg-blue-500',
  epic: 'bg-purple-500',
  legendary: 'bg-orange-500'
};

const rarityIcons = {
  common: Shield,
  rare: Star,
  epic: Zap,
  legendary: Crown
};

const categoryIcons = {
  unit_completion: BookOpen,
  score_improvement: TrendingUp,
  study_streak: Calendar,
  secret: Eye
};

const categoryNames = {
  unit_completion: 'Completar Unidades',
  score_improvement: 'Mejorar Puntajes',
  study_streak: 'Rachas de Estudio',
  secret: 'Logros Secretos'
};

export default function AchievementsPage() {
  const [achievements, setAchievements] = useState<UserAchievement[]>([]);
  const [summary, setSummary] = useState<AchievementSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [showSecrets, setShowSecrets] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [unlockedAchievements, setUnlockedAchievements] = useState<UserAchievement[]>([]);

  useEffect(() => {
    fetchAchievements();
    fetchSummary();
  }, []);

  const fetchAchievements = async () => {
    try {
      const response = await fetch('/api/v1/achievements/user?include_secret=true');
      if (response.ok) {
        const data = await response.json();
        setAchievements(data);
        setUnlockedAchievements(data.filter((a: UserAchievement) => a.is_unlocked));
      }
    } catch (error) {
      console.error('Error fetching achievements:', error);
    }
  };

  const fetchSummary = async () => {
    try {
      const response = await fetch('/api/v1/achievements/summary');
      if (response.ok) {
        const data = await response.json();
        setSummary(data);
      }
    } catch (error) {
      console.error('Error fetching summary:', error);
    } finally {
      setLoading(false);
    }
  };

  const filteredAchievements = achievements.filter(ua => {
    if (selectedCategory !== 'all' && ua.achievement.category !== selectedCategory) {
      return false;
    }
    if (!showSecrets && ua.achievement.is_secret) {
      return false;
    }
    return true;
  });

  const getRarityIcon = (rarity: string) => {
    const IconComponent = rarityIcons[rarity as keyof typeof rarityIcons] || Shield;
    return <IconComponent className="w-4 h-4" />;
  };

  const getCategoryIcon = (category: string) => {
    const IconComponent = categoryIcons[category as keyof typeof categoryIcons] || BookOpen;
    return <IconComponent className="w-5 h-5" />;
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-900 via-purple-900 to-indigo-900 flex items-center justify-center">
        <div className="text-white text-xl">Cargando logros...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-900 via-purple-900 to-indigo-900">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-8"
        >
          <h1 className="text-4xl font-bold text-white mb-4 flex items-center justify-center gap-3">
            <Trophy className="w-10 h-10 text-yellow-400" />
            Sistema de Logros
          </h1>
          <p className="text-blue-200 text-lg">
            Descubre y desbloquea logros que reflejan tu progreso real
          </p>
        </motion.div>

        {/* Summary Cards */}
        {summary && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8"
          >
            <div className="bg-white/10 backdrop-blur-sm rounded-lg p-6 border border-white/20">
              <div className="flex items-center gap-3">
                <Trophy className="w-8 h-8 text-yellow-400" />
                <div>
                  <p className="text-blue-200 text-sm">Logros Desbloqueados</p>
                  <p className="text-white text-2xl font-bold">{summary.unlocked_achievements}</p>
                </div>
              </div>
            </div>

            <div className="bg-white/10 backdrop-blur-sm rounded-lg p-6 border border-white/20">
              <div className="flex items-center gap-3">
                <Star className="w-8 h-8 text-blue-400" />
                <div>
                  <p className="text-blue-200 text-sm">Puntos Totales</p>
                  <p className="text-white text-2xl font-bold">{summary.total_points}</p>
                </div>
              </div>
            </div>

            <div className="bg-white/10 backdrop-blur-sm rounded-lg p-6 border border-white/20">
              <div className="flex items-center gap-3">
                <Eye className="w-8 h-8 text-purple-400" />
                <div>
                  <p className="text-blue-200 text-sm">Secretos Encontrados</p>
                  <p className="text-white text-2xl font-bold">{summary.secret_achievements_found}</p>
                </div>
              </div>
            </div>

            <div className="bg-white/10 backdrop-blur-sm rounded-lg p-6 border border-white/20">
              <div className="flex items-center gap-3">
                <Target className="w-8 h-8 text-green-400" />
                <div>
                  <p className="text-blue-200 text-sm">Progreso Total</p>
                  <p className="text-white text-2xl font-bold">
                    {summary.total_achievements > 0 
                      ? Math.round((summary.unlocked_achievements / summary.total_achievements) * 100)
                      : 0}%
                  </p>
                </div>
              </div>
            </div>
          </motion.div>
        )}

        {/* Filters */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex flex-wrap gap-4 mb-8 justify-center"
        >
          <button
            onClick={() => setSelectedCategory('all')}
            className={`px-4 py-2 rounded-lg transition-all ${
              selectedCategory === 'all'
                ? 'bg-blue-500 text-white'
                : 'bg-white/10 text-blue-200 hover:bg-white/20'
            }`}
          >
            Todos
          </button>
          
          {Object.entries(categoryNames).map(([key, name]) => (
            <button
              key={key}
              onClick={() => setSelectedCategory(key)}
              className={`px-4 py-2 rounded-lg transition-all flex items-center gap-2 ${
                selectedCategory === key
                  ? 'bg-blue-500 text-white'
                  : 'bg-white/10 text-blue-200 hover:bg-white/20'
              }`}
            >
              {getCategoryIcon(key)}
              {name}
            </button>
          ))}

          <button
            onClick={() => setShowSecrets(!showSecrets)}
            className={`px-4 py-2 rounded-lg transition-all flex items-center gap-2 ${
              showSecrets
                ? 'bg-purple-500 text-white'
                : 'bg-white/10 text-blue-200 hover:bg-white/20'
            }`}
          >
            {showSecrets ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
            {showSecrets ? 'Ocultar Secretos' : 'Mostrar Secretos'}
          </button>
        </motion.div>

        {/* Recent Achievements */}
        {summary?.recent_achievements && summary.recent_achievements.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-8"
          >
            <h2 className="text-2xl font-bold text-white mb-4 flex items-center gap-2">
              <Award className="w-6 h-6 text-yellow-400" />
              Logros Recientes
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {summary.recent_achievements.map((achievement, index) => (
                <motion.div
                  key={achievement.id}
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: index * 0.1 }}
                  className="bg-white/10 backdrop-blur-sm rounded-lg p-4 border border-white/20"
                >
                  <div className="flex items-center gap-3 mb-2">
                    <div className={`p-2 rounded-full ${rarityColors[achievement.achievement.rarity as keyof typeof rarityColors]}`}>
                      {getRarityIcon(achievement.achievement.rarity)}
                    </div>
                    <div>
                      <h3 className="text-white font-semibold">{achievement.achievement.title}</h3>
                      <p className="text-blue-200 text-sm">{achievement.achievement.points} puntos</p>
                    </div>
                  </div>
                  <p className="text-blue-200 text-sm">{achievement.achievement.description}</p>
                  {achievement.unlocked_at && (
                    <p className="text-green-400 text-xs mt-2">
                      Desbloqueado: {new Date(achievement.unlocked_at).toLocaleDateString()}
                    </p>
                  )}
                </motion.div>
              ))}
            </div>
          </motion.div>
        )}

        {/* All Achievements */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <h2 className="text-2xl font-bold text-white mb-6 flex items-center gap-2">
            <BookOpen className="w-6 h-6 text-blue-400" />
            Todos los Logros ({filteredAchievements.length})
          </h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {filteredAchievements.map((userAchievement, index) => (
              <motion.div
                key={userAchievement.id}
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: index * 0.05 }}
                className={`relative overflow-hidden rounded-lg border-2 transition-all ${
                  userAchievement.is_unlocked
                    ? 'bg-gradient-to-br from-green-500/20 to-emerald-500/20 border-green-400'
                    : 'bg-white/10 border-white/20'
                }`}
              >
                {/* Progress Bar */}
                {!userAchievement.is_unlocked && (
                  <div className="absolute top-0 left-0 right-0 h-1 bg-white/20">
                    <div
                      className="h-full bg-gradient-to-r from-blue-400 to-purple-400 transition-all duration-300"
                      style={{ width: `${userAchievement.progress_percentage}%` }}
                    />
                  </div>
                )}

                <div className="p-4">
                  <div className="flex items-center gap-3 mb-3">
                    <div className={`p-2 rounded-full ${rarityColors[userAchievement.achievement.rarity as keyof typeof rarityColors]}`}>
                      {getRarityIcon(userAchievement.achievement.rarity)}
                    </div>
                    <div className="flex-1">
                      <h3 className="text-white font-semibold text-sm">
                        {userAchievement.achievement.title}
                        {userAchievement.achievement.is_secret && (
                          <Eye className="w-3 h-3 inline ml-1 text-purple-400" />
                        )}
                      </h3>
                      <p className="text-blue-200 text-xs">{userAchievement.achievement.points} puntos</p>
                    </div>
                  </div>

                  <p className="text-blue-200 text-xs mb-3">{userAchievement.achievement.description}</p>

                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      {getCategoryIcon(userAchievement.achievement.category)}
                      <span className="text-blue-200 text-xs">
                        {categoryNames[userAchievement.achievement.category as keyof typeof categoryNames]}
                      </span>
                    </div>

                    {userAchievement.is_unlocked ? (
                      <div className="flex items-center gap-1 text-green-400">
                        <Star className="w-4 h-4" />
                        <span className="text-xs">Desbloqueado</span>
                      </div>
                    ) : (
                      <div className="text-blue-200 text-xs">
                        {userAchievement.progress_percentage}% completado
                      </div>
                    )}
                  </div>

                  {userAchievement.unlocked_at && (
                    <p className="text-green-400 text-xs mt-2 text-center">
                      {new Date(userAchievement.unlocked_at).toLocaleDateString()}
                    </p>
                  )}
                </div>
              </motion.div>
            ))}
          </div>
        </motion.div>
      </div>
    </div>
  );
} 