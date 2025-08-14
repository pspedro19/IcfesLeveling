'use client';

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Flame, 
  Shield, 
  Star, 
  Sword, 
  Trophy, 
  Clock,
  Target,
  Brain,
  Calendar,
  Lock,
  Unlock,
  ChevronRight
} from 'lucide-react';

interface Quest {
  id: string;
  title: string;
  description: string;
  progress: number;
  total: number;
  type: 'daily' | 'weekly' | 'special';
  icon: React.ReactNode;
  xpReward: number;
  completed: boolean;
  expiresAt?: Date;
}

interface QuestTrackerProps {
  streakDays?: number;
  quests?: Quest[];
  freezeShields?: number;
  onQuestComplete?: (questId: string) => void;
  onUseFreeze?: () => void;
}

export default function QuestTracker({
  streakDays = 0,
  quests = [],
  freezeShields = 2,
  onQuestComplete,
  onUseFreeze
}: QuestTrackerProps) {
  const [expandedView, setExpandedView] = useState(false);
  const [timeUntilReset, setTimeUntilReset] = useState<string>('');
  
  // Calculate time until daily reset
  useEffect(() => {
    const calculateTimeUntilReset = () => {
      const now = new Date();
      const tomorrow = new Date(now);
      tomorrow.setDate(tomorrow.getDate() + 1);
      tomorrow.setHours(0, 0, 0, 0);
      
      const diff = tomorrow.getTime() - now.getTime();
      const hours = Math.floor(diff / (1000 * 60 * 60));
      const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
      const seconds = Math.floor((diff % (1000 * 60)) / 1000);
      
      setTimeUntilReset(`${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`);
    };
    
    calculateTimeUntilReset();
    const interval = setInterval(calculateTimeUntilReset, 1000);
    
    return () => clearInterval(interval);
  }, []);

  // Get streak icon based on days
  const getStreakIcon = () => {
    if (streakDays >= 100) return { icon: '🌟', name: 'Legendario', color: 'text-yellow-400' };
    if (streakDays >= 30) return { icon: '🐲', name: 'Dragón', color: 'text-purple-400' };
    if (streakDays >= 7) return { icon: '🔥🔥', name: 'En llamas', color: 'text-orange-400' };
    if (streakDays >= 1) return { icon: '🔥', name: 'Activo', color: 'text-red-400' };
    return { icon: '💨', name: 'Inactivo', color: 'text-gray-400' };
  };

  const streakInfo = getStreakIcon();

  // Default quests if none provided
  const defaultQuests: Quest[] = [
    {
      id: '1',
      title: 'Derrota 10 enemigos',
      description: 'Completa batallas contra enemigos del conocimiento',
      progress: 3,
      total: 10,
      type: 'daily',
      icon: <Sword className="w-5 h-5" />,
      xpReward: 100,
      completed: false
    },
    {
      id: '2',
      title: 'Completa 1 Mazmorra',
      description: 'Termina cualquier mazmorra de práctica',
      progress: 0,
      total: 1,
      type: 'daily',
      icon: <Target className="w-5 h-5" />,
      xpReward: 150,
      completed: false
    },
    {
      id: '3',
      title: 'Entrena 15 minutos',
      description: 'Tiempo activo de estudio acumulado',
      progress: 12,
      total: 15,
      type: 'daily',
      icon: <Clock className="w-5 h-5" />,
      xpReward: 80,
      completed: false
    },
    {
      id: '4',
      title: 'Domina Trigonometría',
      description: 'Misión personalizada basada en tus debilidades',
      progress: 2,
      total: 5,
      type: 'special',
      icon: <Brain className="w-5 h-5" />,
      xpReward: 200,
      completed: false
    }
  ];

  const activeQuests = quests.length > 0 ? quests : defaultQuests;

  return (
    <>
      {/* Compact Quest Indicator */}
      <motion.div
        className="fixed top-20 left-4 z-40"
        initial={{ opacity: 0, x: -50 }}
        animate={{ opacity: 1, x: 0 }}
      >
        <motion.button
          onClick={() => setExpandedView(!expandedView)}
          className="bg-gray-900/90 backdrop-blur-md rounded-full px-4 py-2 border border-purple-500/30 hover:border-purple-500/50 transition-all"
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
        >
          <div className="flex items-center gap-3">
            {/* Streak Display */}
            <div className="flex items-center gap-2">
              <motion.span
                className="text-2xl"
                animate={{ scale: [1, 1.2, 1] }}
                transition={{ duration: 2, repeat: Infinity }}
              >
                {streakInfo.icon}
              </motion.span>
              <div className="text-left">
                <p className={`text-sm font-bold ${streakInfo.color}`}>
                  Día {streakDays}
                </p>
                <p className="text-xs text-gray-400">{streakInfo.name}</p>
              </div>
            </div>
            
            {/* Quest Progress Summary */}
            <div className="border-l border-gray-700 pl-3">
              <p className="text-sm text-purple-300">
                {activeQuests.filter(q => q.completed).length}/{activeQuests.length} Misiones
              </p>
            </div>
            
            <ChevronRight className={`w-4 h-4 text-gray-400 transition-transform ${expandedView ? 'rotate-90' : ''}`} />
          </div>
        </motion.button>
      </motion.div>

      {/* Expanded Quest View */}
      <AnimatePresence>
        {expandedView && (
          <motion.div
            initial={{ opacity: 0, scale: 0.9, originX: 0, originY: 0 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.9 }}
            className="fixed top-32 left-4 z-30 w-96 bg-gray-900/95 backdrop-blur-lg rounded-lg shadow-2xl border border-purple-500/30 overflow-hidden"
          >
            {/* Header */}
            <div className="bg-gradient-to-r from-purple-900/50 to-blue-900/50 px-6 py-4 border-b border-purple-500/30">
              <div className="flex items-center justify-between mb-2">
                <h2 className="text-xl font-bold text-white flex items-center gap-2">
                  <Trophy className="w-5 h-5 text-yellow-400" />
                  Misión Diaria del Sistema
                </h2>
                <button
                  onClick={() => setExpandedView(false)}
                  className="text-gray-400 hover:text-white transition-colors"
                >
                  ✕
                </button>
              </div>
              
              {/* Streak and Timer */}
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className="flex items-center gap-2">
                    <span className="text-2xl">{streakInfo.icon}</span>
                    <span className={`font-bold ${streakInfo.color}`}>
                      Racha: Día {streakDays}
                    </span>
                  </div>
                  
                  {/* Freeze Shields */}
                  <div className="flex items-center gap-1">
                    {[...Array(3)].map((_, i) => (
                      <Shield
                        key={i}
                        className={`w-4 h-4 ${i < freezeShields ? 'text-blue-400' : 'text-gray-600'}`}
                      />
                    ))}
                  </div>
                </div>
                
                {/* Timer */}
                <div className="text-sm text-orange-300 flex items-center gap-1">
                  <Clock className="w-4 h-4" />
                  {timeUntilReset}
                </div>
              </div>
            </div>

            {/* Quest List */}
            <div className="p-4 space-y-3 max-h-96 overflow-y-auto">
              {activeQuests.map((quest, index) => (
                <motion.div
                  key={quest.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.1 }}
                  className={`
                    bg-gray-800/50 rounded-lg p-4 border transition-all
                    ${quest.completed 
                      ? 'border-green-500/30 opacity-70' 
                      : quest.type === 'special' 
                        ? 'border-purple-500/30 hover:border-purple-500/50' 
                        : 'border-gray-700/30 hover:border-gray-600/50'
                    }
                  `}
                >
                  <div className="flex items-start gap-3">
                    <div className={`
                      p-2 rounded-lg
                      ${quest.completed 
                        ? 'bg-green-900/30 text-green-400' 
                        : quest.type === 'special'
                          ? 'bg-purple-900/30 text-purple-400'
                          : 'bg-gray-700/30 text-gray-400'
                      }
                    `}>
                      {quest.icon}
                    </div>
                    
                    <div className="flex-1">
                      <div className="flex items-center justify-between mb-1">
                        <h3 className={`font-semibold ${quest.completed ? 'text-gray-400' : 'text-white'}`}>
                          {quest.title}
                          {quest.type === 'special' && (
                            <span className="ml-2 text-xs text-purple-400">IA</span>
                          )}
                        </h3>
                        <span className="text-sm text-yellow-400">
                          +{quest.xpReward} XP
                        </span>
                      </div>
                      
                      <p className="text-sm text-gray-400 mb-2">{quest.description}</p>
                      
                      {/* Progress Bar */}
                      <div className="relative h-2 bg-gray-700 rounded-full overflow-hidden">
                        <motion.div
                          className={`
                            h-full rounded-full
                            ${quest.completed 
                              ? 'bg-green-500' 
                              : quest.type === 'special' 
                                ? 'bg-gradient-to-r from-purple-500 to-pink-500'
                                : 'bg-blue-500'
                            }
                          `}
                          initial={{ width: 0 }}
                          animate={{ width: `${(quest.progress / quest.total) * 100}%` }}
                          transition={{ duration: 0.5, ease: 'easeOut' }}
                        />
                      </div>
                      
                      <div className="flex items-center justify-between mt-1">
                        <span className="text-xs text-gray-500">
                          {quest.progress}/{quest.total}
                        </span>
                        {quest.completed && (
                          <span className="text-xs text-green-400 flex items-center gap-1">
                            <Lock className="w-3 h-3" />
                            Completada
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                </motion.div>
              ))}
            </div>

            {/* Calendar Heatmap */}
            <div className="p-4 border-t border-purple-500/30">
              <h3 className="text-sm font-semibold text-gray-300 mb-2 flex items-center gap-2">
                <Calendar className="w-4 h-4" />
                Calendario de Racha
              </h3>
              <div className="grid grid-cols-7 gap-1">
                {['L', 'M', 'M', 'J', 'V', 'S', 'D'].map((day, i) => (
                  <div key={i} className="text-xs text-gray-500 text-center">
                    {day}
                  </div>
                ))}
                {[...Array(35)].map((_, i) => {
                  const isActive = i < streakDays || (i >= 28 && i < 28 + (streakDays % 7));
                  const isToday = i === 34;
                  return (
                    <motion.div
                      key={i}
                      whileHover={{ scale: 1.2 }}
                      className={`
                        aspect-square rounded
                        ${isActive 
                          ? 'bg-gradient-to-br from-purple-500 to-blue-500' 
                          : 'bg-gray-800'
                        }
                        ${isToday ? 'ring-2 ring-yellow-400' : ''}
                      `}
                      style={{
                        opacity: isActive ? 0.8 + (Math.random() * 0.2) : 0.3
                      }}
                    />
                  );
                })}
              </div>
            </div>

            {/* Actions */}
            <div className="p-4 border-t border-purple-500/30 flex justify-between items-center">
              <button
                onClick={onUseFreeze}
                disabled={freezeShields === 0}
                className={`
                  px-4 py-2 rounded-lg font-medium transition-all flex items-center gap-2
                  ${freezeShields > 0 
                    ? 'bg-blue-600 hover:bg-blue-700 text-white' 
                    : 'bg-gray-700 text-gray-400 cursor-not-allowed'
                  }
                `}
              >
                <Shield className="w-4 h-4" />
                Usar Escudo ({freezeShields})
              </button>
              
              <div className="text-sm text-gray-400">
                Total XP disponible: <span className="text-yellow-400 font-bold">
                  {activeQuests.reduce((sum, q) => sum + (q.completed ? 0 : q.xpReward), 0)}
                </span>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}