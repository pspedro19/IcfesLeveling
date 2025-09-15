'use client';

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Trophy, 
  Star, 
  Flame, 
  Target, 
  Zap,
  Crown,
  Medal,
  Shield,
  Sparkles,
  Rocket,
  Gem,
  Award,
  TrendingUp,
  Calendar,
  Clock,
  CheckCircle,
  Gift,
  BadgeCheck,
  Swords,
  Heart,
  Lightning
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";

interface Achievement {
  id: string;
  name: string;
  description: string;
  icon: string;
  rarity: 'common' | 'rare' | 'epic' | 'legendary';
  category: 'accuracy' | 'streak' | 'speed' | 'consistency' | 'improvement' | 'milestone';
  points: number;
  progress: number;
  max_progress: number;
  unlocked: boolean;
  unlocked_at?: string;
  conditions: string[];
}

interface Streak {
  current: number;
  best: number;
  type: 'daily' | 'correct_answers' | 'perfect_sessions';
  next_milestone: number;
  milestone_reward: {
    points: number;
    achievement_id?: string;
    special_effect?: string;
  };
}

interface LevelSystem {
  current_level: number;
  current_xp: number;
  xp_to_next_level: number;
  total_xp: number;
  level_rewards: Array<{
    level: number;
    reward_type: 'points' | 'badge' | 'title' | 'feature';
    reward_value: any;
    unlocked: boolean;
  }>;
}

interface MotivationalContent {
  daily_goal: {
    target: number;
    current: number;
    type: 'questions' | 'accuracy' | 'time';
    reward_points: number;
    completed: boolean;
  };
  weekly_challenge: {
    name: string;
    description: string;
    progress: number;
    max_progress: number;
    reward: {
      points: number;
      special_reward?: string;
    };
    time_left: string;
  };
  motivational_message: {
    message: string;
    type: 'encouragement' | 'celebration' | 'challenge' | 'tip';
    context: string;
  };
}

interface GamifiedExperienceHubProps {
  achievements: Achievement[];
  streaks: {
    daily_practice: Streak;
    correct_answers: Streak;
    perfect_sessions: Streak;
  };
  level_system: LevelSystem;
  motivational_content: MotivationalContent;
  onClaimReward: (rewardId: string) => Promise<void>;
  onShareAchievement: (achievementId: string) => void;
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
  legendary: 'shadow-yellow-200 shadow-lg'
};

const categoryIcons = {
  accuracy: Target,
  streak: Flame,
  speed: Zap,
  consistency: Shield,
  improvement: TrendingUp,
  milestone: Trophy
};

export default function GamifiedExperienceHub({
  achievements,
  streaks,
  level_system,
  motivational_content,
  onClaimReward,
  onShareAchievement
}: GamifiedExperienceHubProps) {
  const [selectedCategory, setSelectedCategory] = useState<'all' | Achievement['category']>('all');
  const [showConfetti, setShowConfetti] = useState(false);
  const [animateLevel, setAnimateLevel] = useState(false);
  const [newUnlocks, setNewUnlocks] = useState<string[]>([]);

  const filteredAchievements = selectedCategory === 'all' 
    ? achievements 
    : achievements.filter(a => a.category === selectedCategory);

  const unlockedCount = achievements.filter(a => a.unlocked).length;
  const totalCount = achievements.length;

  // Trigger effects for new achievements
  useEffect(() => {
    const recentUnlocks = achievements
      .filter(a => a.unlocked && a.unlocked_at)
      .filter(a => {
        const unlockedTime = new Date(a.unlocked_at!).getTime();
        const now = Date.now();
        return (now - unlockedTime) < 5000; // Last 5 seconds
      })
      .map(a => a.id);

    if (recentUnlocks.length > 0) {
      setNewUnlocks(recentUnlocks);
      setShowConfetti(true);
      
      const timer = setTimeout(() => {
        setShowConfetti(false);
        setNewUnlocks([]);
      }, 3000);

      return () => clearTimeout(timer);
    }
  }, [achievements]);

  // Calculate level progress
  const levelProgress = (level_system.current_xp / level_system.xp_to_next_level) * 100;

  const getStreakColor = (streak: number, type: string) => {
    if (streak >= 30) return 'text-orange-500';
    if (streak >= 14) return 'text-red-500';
    if (streak >= 7) return 'text-yellow-500';
    return 'text-blue-500';
  };

  const getStreakEmoji = (streak: number, type: string) => {
    if (type === 'daily_practice') {
      if (streak >= 30) return '🔥';
      if (streak >= 14) return '⚡';
      if (streak >= 7) return '✨';
      return '💪';
    }
    if (type === 'correct_answers') return '🎯';
    if (type === 'perfect_sessions') return '👑';
    return '🌟';
  };

  const getMotivationalIcon = (type: string) => {
    switch (type) {
      case 'encouragement':
        return <Heart className="h-5 w-5 text-pink-500" />;
      case 'celebration':
        return <Sparkles className="h-5 w-5 text-yellow-500" />;
      case 'challenge':
        return <Lightning className="h-5 w-5 text-blue-500" />;
      case 'tip':
        return <Star className="h-5 w-5 text-purple-500" />;
      default:
        return <Sparkles className="h-5 w-5 text-blue-500" />;
    }
  };

  return (
    <div className="w-full space-y-6 relative">
      {/* Confetti effect for achievements */}
      <AnimatePresence>
        {showConfetti && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 pointer-events-none z-50"
          >
            {[...Array(50)].map((_, i) => (
              <motion.div
                key={i}
                initial={{ 
                  opacity: 1, 
                  scale: 0, 
                  x: Math.random() * window.innerWidth,
                  y: -10
                }}
                animate={{ 
                  opacity: 0, 
                  scale: 1,
                  y: window.innerHeight + 100,
                  rotate: Math.random() * 360
                }}
                transition={{ duration: 3, delay: Math.random() * 0.5 }}
                className="absolute w-2 h-2 bg-gradient-to-r from-yellow-400 to-orange-500 rounded-full"
              />
            ))}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Level and XP Header */}
      <Card className="bg-gradient-to-r from-indigo-600 via-purple-600 to-blue-600 text-white overflow-hidden">
        <CardContent className="p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-4">
              <div className="relative">
                <div className="w-16 h-16 bg-white/20 rounded-full flex items-center justify-center">
                  <Crown className="h-8 w-8 text-yellow-300" />
                </div>
                {animateLevel && (
                  <motion.div
                    initial={{ scale: 1 }}
                    animate={{ scale: [1, 1.2, 1] }}
                    transition={{ duration: 0.5 }}
                    className="absolute inset-0 border-2 border-yellow-300 rounded-full"
                  />
                )}
              </div>
              <div>
                <h2 className="text-2xl font-bold">Nivel {level_system.current_level}</h2>
                <p className="opacity-90">
                  {level_system.current_xp.toLocaleString()} / {level_system.xp_to_next_level.toLocaleString()} XP
                </p>
              </div>
            </div>
            
            <div className="text-right">
              <div className="text-lg font-semibold">Total XP</div>
              <div className="text-3xl font-bold text-yellow-300">
                {level_system.total_xp.toLocaleString()}
              </div>
            </div>
          </div>
          
          {/* XP Progress bar */}
          <div className="space-y-2">
            <div className="flex justify-between text-sm opacity-90">
              <span>Progreso al siguiente nivel</span>
              <span>{Math.round(levelProgress)}%</span>
            </div>
            <div className="w-full bg-white/20 rounded-full h-3">
              <motion.div
                className="bg-gradient-to-r from-yellow-400 to-orange-400 h-3 rounded-full flex items-center justify-end pr-2"
                initial={{ width: 0 }}
                animate={{ width: `${levelProgress}%` }}
                transition={{ duration: 1.5, ease: "easeOut" }}
              >
                <Sparkles className="h-3 w-3 text-white" />
              </motion.div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Streaks Section */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {Object.entries(streaks).map(([key, streak]) => (
          <Card key={key} className="hover:shadow-lg transition-shadow">
            <CardContent className="p-4">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center space-x-2">
                  <Flame className={`h-5 w-5 ${getStreakColor(streak.current, key)}`} />
                  <span className="font-medium capitalize">
                    {key.replace('_', ' ')}
                  </span>
                </div>
                <span className="text-2xl">
                  {getStreakEmoji(streak.current, key)}
                </span>
              </div>
              
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Actual</span>
                  <span className={`font-bold ${getStreakColor(streak.current, key)}`}>
                    {streak.current}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Mejor</span>
                  <span className="font-medium text-gray-700">{streak.best}</span>
                </div>
                
                {/* Progress to next milestone */}
                <div className="mt-3">
                  <div className="flex justify-between text-xs text-gray-500 mb-1">
                    <span>Próxima meta</span>
                    <span>{streak.next_milestone}</span>
                  </div>
                  <Progress 
                    value={(streak.current / streak.next_milestone) * 100} 
                    className="h-2" 
                  />
                  <div className="text-xs text-gray-500 mt-1">
                    Recompensa: +{streak.milestone_reward.points} XP
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Daily Goal and Weekly Challenge */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Daily Goal */}
        <Card className="border-2 border-green-200 bg-green-50">
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Calendar className="h-5 w-5 text-green-600" />
              <span>Meta Diaria</span>
              {motivational_content.daily_goal.completed && (
                <CheckCircle className="h-5 w-5 text-green-600" />
              )}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span>Progreso</span>
                <span className="font-bold text-green-700">
                  {motivational_content.daily_goal.current} / {motivational_content.daily_goal.target}
                </span>
              </div>
              
              <Progress 
                value={(motivational_content.daily_goal.current / motivational_content.daily_goal.target) * 100} 
                className="h-3"
              />
              
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-600">
                  {motivational_content.daily_goal.type === 'questions' && 'preguntas'}
                  {motivational_content.daily_goal.type === 'accuracy' && 'precisión'}
                  {motivational_content.daily_goal.type === 'time' && 'minutos'}
                </span>
                <div className="flex items-center space-x-1">
                  <Gift className="h-4 w-4 text-yellow-600" />
                  <span className="text-yellow-700">
                    +{motivational_content.daily_goal.reward_points} XP
                  </span>
                </div>
              </div>
              
              {motivational_content.daily_goal.completed ? (
                <Button className="w-full bg-green-600 hover:bg-green-700">
                  <CheckCircle className="h-4 w-4 mr-2" />
                  ¡Meta completada!
                </Button>
              ) : (
                <div className="text-center text-green-700 text-sm">
                  ¡Sigue así! Te falta poco para completar tu meta diaria.
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Weekly Challenge */}
        <Card className="border-2 border-purple-200 bg-purple-50">
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Swords className="h-5 w-5 text-purple-600" />
              <span>Desafío Semanal</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div>
                <h4 className="font-semibold text-purple-800">
                  {motivational_content.weekly_challenge.name}
                </h4>
                <p className="text-sm text-purple-700">
                  {motivational_content.weekly_challenge.description}
                </p>
              </div>
              
              <div className="flex items-center justify-between">
                <span>Progreso</span>
                <span className="font-bold text-purple-700">
                  {motivational_content.weekly_challenge.progress} / {motivational_content.weekly_challenge.max_progress}
                </span>
              </div>
              
              <Progress 
                value={(motivational_content.weekly_challenge.progress / motivational_content.weekly_challenge.max_progress) * 100} 
                className="h-3"
              />
              
              <div className="flex items-center justify-between text-sm">
                <div className="flex items-center space-x-1">
                  <Clock className="h-4 w-4 text-purple-600" />
                  <span className="text-purple-700">
                    {motivational_content.weekly_challenge.time_left}
                  </span>
                </div>
                <div className="flex items-center space-x-1">
                  <Trophy className="h-4 w-4 text-yellow-600" />
                  <span className="text-yellow-700">
                    +{motivational_content.weekly_challenge.reward.points} XP
                  </span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Motivational Message */}
      <Card className="bg-gradient-to-r from-pink-50 to-blue-50 border-pink-200">
        <CardContent className="p-4">
          <div className="flex items-center space-x-3">
            {getMotivationalIcon(motivational_content.motivational_message.type)}
            <div className="flex-1">
              <p className="text-gray-800 font-medium">
                {motivational_content.motivational_message.message}
              </p>
              <p className="text-sm text-gray-600 mt-1">
                {motivational_content.motivational_message.context}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Achievements Section */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center space-x-2">
              <Trophy className="h-6 w-6 text-yellow-600" />
              <span>Logros</span>
              <Badge variant="secondary">
                {unlockedCount}/{totalCount}
              </Badge>
            </CardTitle>
            
            {/* Category filter */}
            <div className="flex space-x-2">
              <Button
                onClick={() => setSelectedCategory('all')}
                variant={selectedCategory === 'all' ? 'default' : 'outline'}
                size="sm"
              >
                Todos
              </Button>
              {['accuracy', 'streak', 'speed', 'consistency', 'improvement', 'milestone'].map((category) => {
                const Icon = categoryIcons[category as keyof typeof categoryIcons];
                return (
                  <Button
                    key={category}
                    onClick={() => setSelectedCategory(category as Achievement['category'])}
                    variant={selectedCategory === category ? 'default' : 'outline'}
                    size="sm"
                  >
                    <Icon className="h-4 w-4" />
                  </Button>
                );
              })}
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredAchievements.map((achievement) => (
              <motion.div
                key={achievement.id}
                whileHover={{ y: -2 }}
                className={`
                  relative p-4 rounded-xl border-2 transition-all cursor-pointer
                  ${achievement.unlocked 
                    ? `bg-gradient-to-r ${rarityColors[achievement.rarity]} text-white ${rarityGlow[achievement.rarity]}` 
                    : 'bg-gray-50 border-gray-200 text-gray-500'}
                  ${newUnlocks.includes(achievement.id) ? 'ring-4 ring-yellow-400 ring-opacity-75' : ''}
                `}
                initial={newUnlocks.includes(achievement.id) ? { scale: 0.8, opacity: 0 } : {}}
                animate={newUnlocks.includes(achievement.id) ? { scale: 1, opacity: 1 } : {}}
                transition={{ duration: 0.5, type: "spring" }}
              >
                {/* Rarity indicator */}
                {achievement.unlocked && (
                  <div className="absolute top-2 right-2">
                    <Badge className="text-xs bg-white/20 text-white border-white/30">
                      {achievement.rarity}
                    </Badge>
                  </div>
                )}
                
                <div className="flex items-start space-x-3">
                  <div className="text-3xl flex-shrink-0">
                    {achievement.icon}
                  </div>
                  
                  <div className="flex-1 min-w-0">
                    <h4 className={`font-semibold truncate ${
                      achievement.unlocked ? 'text-white' : 'text-gray-700'
                    }`}>
                      {achievement.name}
                    </h4>
                    <p className={`text-sm ${
                      achievement.unlocked ? 'text-white/90' : 'text-gray-500'
                    }`}>
                      {achievement.description}
                    </p>
                    
                    {/* Progress bar for locked achievements */}
                    {!achievement.unlocked && achievement.max_progress > 0 && (
                      <div className="mt-2">
                        <div className="flex justify-between text-xs text-gray-500 mb-1">
                          <span>Progreso</span>
                          <span>{achievement.progress}/{achievement.max_progress}</span>
                        </div>
                        <Progress 
                          value={(achievement.progress / achievement.max_progress) * 100} 
                          className="h-2" 
                        />
                      </div>
                    )}
                    
                    <div className="flex items-center justify-between mt-2">
                      <div className="flex items-center space-x-1">
                        <Star className="h-3 w-3" />
                        <span className="text-xs font-medium">+{achievement.points} XP</span>
                      </div>
                      
                      {achievement.unlocked && (
                        <Button
                          onClick={() => onShareAchievement(achievement.id)}
                          variant="ghost"
                          size="sm"
                          className="text-white hover:bg-white/20 h-6 px-2"
                        >
                          Compartir
                        </Button>
                      )}
                    </div>
                  </div>
                </div>
                
                {/* Unlock animation overlay */}
                {newUnlocks.includes(achievement.id) && (
                  <motion.div
                    initial={{ opacity: 1 }}
                    animate={{ opacity: 0 }}
                    transition={{ delay: 2, duration: 1 }}
                    className="absolute inset-0 bg-yellow-400/20 rounded-xl flex items-center justify-center"
                  >
                    <motion.div
                      initial={{ scale: 0 }}
                      animate={{ scale: 1 }}
                      transition={{ delay: 0.5, duration: 0.5, type: "spring" }}
                      className="text-white font-bold text-lg"
                    >
                      ¡DESBLOQUEADO!
                    </motion.div>
                  </motion.div>
                )}
              </motion.div>
            ))}
          </div>
          
          {filteredAchievements.length === 0 && (
            <div className="text-center py-8 text-gray-500">
              <Trophy className="h-12 w-12 mx-auto mb-3 opacity-30" />
              <p>No hay logros en esta categoría</p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}