'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { 
  Flame, 
  Diamond, 
  Trophy, 
  Star,
  TrendingUp,
  Target,
  Zap,
  Crown
} from 'lucide-react';
import { CircularProgress } from './ui/CircularProgress';
import { Badge } from './ui/badge';

interface UserData {
  overallProgress: number;
  rank: string;
  nextRank: string;
  xpToNextRank: number;
  currentStreak: number;
  streakData: { [date: string]: boolean };
  orbs: number;
  recentAchievements: Array<{
    id: string;
    name: string;
    description: string;
    icon: string;
    rarity: 'common' | 'rare' | 'epic' | 'legendary';
  }>;
}

interface ProgressDashboardProps {
  userData: UserData;
  className?: string;
}

function RankBadge({ rank, size = 'medium', animated = false }: { 
  rank: string; 
  size?: 'small' | 'medium' | 'large';
  animated?: boolean;
}) {
  const getRankColor = (rank: string) => {
    switch (rank.toLowerCase()) {
      case 'ss': return 'bg-purple-600 text-white';
      case 's': return 'bg-red-600 text-white';
      case 'a': return 'bg-orange-600 text-white';
      case 'b': return 'bg-yellow-600 text-white';
      case 'c': return 'bg-green-600 text-white';
      case 'd': return 'bg-blue-600 text-white';
      case 'e': return 'bg-gray-600 text-white';
      default: return 'bg-gray-600 text-white';
    }
  };

  const sizeClasses = {
    small: 'px-2 py-1 text-xs',
    medium: 'px-3 py-1.5 text-sm',
    large: 'px-4 py-2 text-base'
  };

  return (
    <motion.div
      className={`inline-flex items-center gap-2 rounded-full font-bold ${getRankColor(rank)} ${sizeClasses[size]}`}
      whileHover={animated ? { scale: 1.05 } : {}}
      animate={animated ? { 
        scale: [1, 1.1, 1],
        transition: { duration: 2, repeat: Infinity }
      } : {}}
    >
      <Crown className="w-4 h-4" />
      <span>Rango {rank}</span>
    </motion.div>
  );
}

function StreakCalendar({ streak, mini = false }: { streak: { [date: string]: boolean }; mini?: boolean }) {
  const today = new Date();
  const last7Days = Array.from({ length: 7 }, (_, i) => {
    const date = new Date(today);
    date.setDate(date.getDate() - i);
    return date.toISOString().split('T')[0];
  }).reverse();

  return (
    <div className={`flex gap-1 ${mini ? 'justify-center' : ''}`}>
      {last7Days.map((date) => {
        const hasStreak = streak[date] || false;
        return (
          <div
            key={date}
            className={`w-3 h-3 rounded-sm ${
              hasStreak ? 'bg-orange-500' : 'bg-gray-300 dark:bg-gray-600'
            }`}
            title={`${date}: ${hasStreak ? 'Racha activa' : 'Sin racha'}`}
          />
        );
      })}
    </div>
  );
}

function AchievementBadge({ 
  achievement, 
  size = 'medium', 
  showTooltip = false 
}: { 
  achievement: any; 
  size?: 'small' | 'medium' | 'large';
  showTooltip?: boolean;
}) {
  const getRarityColor = (rarity: string) => {
    switch (rarity) {
      case 'legendary': return 'bg-gradient-to-r from-yellow-400 to-orange-500';
      case 'epic': return 'bg-gradient-to-r from-purple-400 to-pink-500';
      case 'rare': return 'bg-gradient-to-r from-blue-400 to-cyan-500';
      default: return 'bg-gradient-to-r from-gray-400 to-gray-500';
    }
  };

  const sizeClasses = {
    small: 'w-8 h-8 text-xs',
    medium: 'w-12 h-12 text-sm',
    large: 'w-16 h-16 text-base'
  };

  return (
    <motion.div
      className={`relative ${sizeClasses[size]} rounded-full ${getRarityColor(achievement.rarity)} 
                 flex items-center justify-center text-white font-bold shadow-lg`}
      whileHover={{ scale: 1.1 }}
      title={showTooltip ? achievement.name : undefined}
    >
      <span className="text-center leading-none">{achievement.icon}</span>
    </motion.div>
  );
}

export function ProgressDashboard({ userData, className = '' }: ProgressDashboardProps) {
  return (
    <div className={`bg-gradient-to-br from-blue-50 to-teal-50 
                    dark:from-gray-900 dark:to-gray-800 rounded-2xl p-6 ${className}`}>
      {/* Main Stats Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        {/* Overall Progress Ring */}
        <div className="col-span-2 md:col-span-1">
          <CircularProgress
            value={userData.overallProgress}
            size={120}
            strokeWidth={8}
            color="from-teal-500 to-blue-500"
          >
            <div className="text-center">
              <span className="text-3xl font-bold text-gray-900 dark:text-white">
                {userData.overallProgress}%
              </span>
              <span className="text-xs text-gray-600 dark:text-gray-400 block">
                Progreso Total
              </span>
            </div>
          </CircularProgress>
        </div>

        {/* Rank Card */}
        <div className="bg-white dark:bg-gray-800 rounded-xl p-4">
          <RankBadge rank={userData.rank} size="large" animated />
          <div className="mt-2 text-center">
            <span className="text-sm text-gray-600 dark:text-gray-400">
              {userData.xpToNextRank} XP to {userData.nextRank}
            </span>
          </div>
        </div>

        {/* Streak Card */}
        <div className="bg-white dark:bg-gray-800 rounded-xl p-4">
          <div className="flex items-center justify-center mb-2">
            <Flame className="w-8 h-8 text-orange-500" />
            <span className="text-3xl font-bold text-orange-500 ml-2">
              {userData.currentStreak}
            </span>
          </div>
          <StreakCalendar streak={userData.streakData} mini />
        </div>

        {/* Orbs Card */}
        <div className="bg-white dark:bg-gray-800 rounded-xl p-4">
          <div className="flex items-center justify-center mb-2">
            <Diamond className="w-8 h-8 text-purple-500" />
            <span className="text-3xl font-bold text-purple-500 ml-2">
              {userData.orbs}
            </span>
          </div>
          <button className="w-full mt-2 text-sm text-purple-600 hover:text-purple-700">
            Tienda de Orbs →
          </button>
        </div>
      </div>

      {/* Achievement Showcase */}
      <div className="bg-white dark:bg-gray-800 rounded-xl p-4">
        <h3 className="text-lg font-bold mb-3">Logros Recientes</h3>
        <div className="flex gap-3 overflow-x-auto pb-2">
          {userData.recentAchievements.map(achievement => (
            <AchievementBadge
              key={achievement.id}
              achievement={achievement}
              size="small"
              showTooltip
            />
          ))}
        </div>
      </div>
    </div>
  );
}
