'use client';

import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Trophy, 
  Zap, 
  TrendingUp, 
  Award, 
  Users, 
  X,
  CheckCircle,
  Star,
  Crown,
  Target
} from 'lucide-react';
import { useRealtimeUpdates } from '@/hooks/useRealtimeUpdates';
import confetti from 'canvas-confetti';

interface NotificationProps {
  id: string;
  type: 'xp' | 'levelup' | 'achievement' | 'ranking' | 'progress';
  title: string;
  message: string;
  icon?: React.ReactNode;
  color?: string;
  duration?: number;
  onClose: (id: string) => void;
}

const Notification: React.FC<NotificationProps> = ({
  id,
  type,
  title,
  message,
  icon,
  color = 'purple',
  duration = 5000,
  onClose
}) => {
  useEffect(() => {
    const timer = setTimeout(() => {
      onClose(id);
    }, duration);

    return () => clearTimeout(timer);
  }, [id, duration, onClose]);

  const getColorClasses = (color: string) => {
    switch (color) {
      case 'yellow':
        return 'from-yellow-500 to-orange-500 border-yellow-500/50';
      case 'green':
        return 'from-green-500 to-emerald-500 border-green-500/50';
      case 'blue':
        return 'from-blue-500 to-cyan-500 border-blue-500/50';
      case 'purple':
      default:
        return 'from-purple-500 to-pink-500 border-purple-500/50';
    }
  };

  return (
    <motion.div
      layout
      initial={{ opacity: 0, x: 300, scale: 0.3 }}
      animate={{ opacity: 1, x: 0, scale: 1 }}
      exit={{ opacity: 0, x: 300, scale: 0.5, transition: { duration: 0.2 } }}
      className={`relative p-4 bg-gradient-to-r ${getColorClasses(color)} rounded-xl shadow-xl border backdrop-blur-sm`}
      style={{ minWidth: '320px' }}
    >
      {/* Background glow */}
      <div className="absolute inset-0 bg-white/10 rounded-xl blur-xl" />
      
      <div className="relative z-10 flex items-start gap-3">
        <div className="flex-shrink-0 p-2 bg-white/20 rounded-lg">
          {icon}
        </div>
        
        <div className="flex-1 min-w-0">
          <h4 className="text-white font-semibold text-sm mb-1">{title}</h4>
          <p className="text-white/90 text-xs leading-relaxed">{message}</p>
        </div>
        
        <button
          onClick={() => onClose(id)}
          className="flex-shrink-0 p-1 hover:bg-white/20 rounded-lg transition-colors"
        >
          <X className="w-4 h-4 text-white/80" />
        </button>
      </div>

      {/* Progress bar */}
      <motion.div
        className="absolute bottom-0 left-0 h-1 bg-white/30 rounded-b-xl origin-left"
        initial={{ scaleX: 1 }}
        animate={{ scaleX: 0 }}
        transition={{ duration: duration / 1000, ease: 'linear' }}
      />
    </motion.div>
  );
};

const RealtimeNotifications: React.FC = () => {
  const {
    xpUpdates,
    levelUps,
    achievements,
    rankingUpdates,
    progressUpdates,
    clearXPUpdates,
    clearEvents
  } = useRealtimeUpdates();

  const [notifications, setNotifications] = useState<
    Array<Omit<NotificationProps, 'onClose'>>
  >([]);

  // Handle XP updates
  useEffect(() => {
    const latestXP = xpUpdates[0];
    if (latestXP) {
      setNotifications(prev => [...prev, {
        id: `xp-${Date.now()}`,
        type: 'xp',
        title: 'XP Ganada!',
        message: `+${latestXP.amount} XP por ${latestXP.source}`,
        icon: <Zap className="w-5 h-5 text-white" />,
        color: 'yellow',
        duration: 3000
      }]);
    }
  }, [xpUpdates]);

  // Handle level ups
  useEffect(() => {
    const latestLevelUp = levelUps[0];
    if (latestLevelUp) {
      // Trigger confetti
      confetti({
        particleCount: 100,
        spread: 70,
        origin: { y: 0.6 }
      });

      setNotifications(prev => [...prev, {
        id: `levelup-${Date.now()}`,
        type: 'levelup',
        title: '¡NIVEL SUBIDO!',
        message: `¡Alcanzaste el Nivel ${latestLevelUp.newLevel} - Rango ${latestLevelUp.newRank}! +${latestLevelUp.bonusXP} XP de bonus`,
        icon: <Crown className="w-5 h-5 text-white" />,
        color: 'yellow',
        duration: 8000
      }]);
    }
  }, [levelUps]);

  // Handle achievements
  useEffect(() => {
    const latestAchievement = achievements[0];
    if (latestAchievement) {
      // Trigger special confetti for achievements
      confetti({
        particleCount: 50,
        spread: 50,
        origin: { y: 0.7 },
        colors: ['#FFD700', '#FFA500', '#FF6347']
      });

      setNotifications(prev => [...prev, {
        id: `achievement-${Date.now()}`,
        type: 'achievement',
        title: '¡LOGRO DESBLOQUEADO!',
        message: `${latestAchievement.icon} ${latestAchievement.name} - +${latestAchievement.xpReward} XP`,
        icon: <Trophy className="w-5 h-5 text-white" />,
        color: 'yellow',
        duration: 6000
      }]);
    }
  }, [achievements]);

  // Handle ranking changes
  useEffect(() => {
    const latestRanking = rankingUpdates[0];
    if (latestRanking && latestRanking.change !== 0) {
      const isImprovement = latestRanking.change > 0;
      
      setNotifications(prev => [...prev, {
        id: `ranking-${Date.now()}`,
        type: 'ranking',
        title: isImprovement ? '¡Ranking Mejorado!' : 'Cambio de Ranking',
        message: `${isImprovement ? 'Subiste' : 'Bajaste'} ${Math.abs(latestRanking.change)} posiciones. Posición actual: #${latestRanking.nationalRanking}`,
        icon: <Users className="w-5 h-5 text-white" />,
        color: isImprovement ? 'green' : 'blue',
        duration: 5000
      }]);
    }
  }, [rankingUpdates]);

  // Handle progress updates
  useEffect(() => {
    const latestProgress = progressUpdates[0];
    if (latestProgress?.completed) {
      setNotifications(prev => [...prev, {
        id: `progress-${Date.now()}`,
        type: 'progress',
        title: '¡Tarea Completada!',
        message: `Tarea finalizada${latestProgress.xpGained ? ` - +${latestProgress.xpGained} XP` : ''}`,
        icon: <CheckCircle className="w-5 h-5 text-white" />,
        color: 'green',
        duration: 4000
      }]);
    }
  }, [progressUpdates]);

  const removeNotification = (id: string) => {
    setNotifications(prev => prev.filter(notification => notification.id !== id));
  };

  // Create floating XP numbers
  const FloatingXP = ({ amount, onComplete }: { amount: number; onComplete: () => void }) => (
    <motion.div
      className="fixed top-1/2 left-1/2 pointer-events-none z-50"
      initial={{ 
        opacity: 1, 
        scale: 0.5, 
        x: -50, 
        y: -25,
        rotate: -10
      }}
      animate={{ 
        opacity: 0, 
        scale: 1.5, 
        y: -100,
        rotate: 10
      }}
      transition={{ 
        duration: 2,
        ease: 'easeOut'
      }}
      onAnimationComplete={onComplete}
    >
      <div className="px-4 py-2 bg-gradient-to-r from-yellow-400 to-orange-500 rounded-full shadow-lg border-2 border-white/30">
        <span className="text-white font-bold text-lg">+{amount} XP</span>
      </div>
    </motion.div>
  );

  // Floating XP animations
  const [floatingXPs, setFloatingXPs] = useState<{ id: string; amount: number }[]>([]);

  useEffect(() => {
    const latestXP = xpUpdates[0];
    if (latestXP) {
      const id = `floating-${Date.now()}`;
      setFloatingXPs(prev => [...prev, { id, amount: latestXP.amount }]);
    }
  }, [xpUpdates]);

  const removeFloatingXP = (id: string) => {
    setFloatingXPs(prev => prev.filter(xp => xp.id !== id));
  };

  return (
    <>
      {/* Notification Container */}
      <div className="fixed top-4 right-4 z-40 space-y-2 max-w-sm">
        <AnimatePresence mode="popLayout">
          {notifications.map((notification) => (
            <Notification
              key={notification.id}
              {...notification}
              onClose={removeNotification}
            />
          ))}
        </AnimatePresence>
      </div>

      {/* Floating XP Numbers */}
      <AnimatePresence>
        {floatingXPs.map((xp) => (
          <FloatingXP
            key={xp.id}
            amount={xp.amount}
            onComplete={() => removeFloatingXP(xp.id)}
          />
        ))}
      </AnimatePresence>

      {/* Achievement Modal for major achievements */}
      <AnimatePresence>
        {achievements.length > 0 && achievements[0].rarity === 'legendary' && (
          <motion.div
            className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          >
            <motion.div
              className="bg-gradient-to-br from-yellow-500/20 to-orange-500/20 border-2 border-yellow-500/50 rounded-2xl p-8 max-w-md w-full backdrop-blur-md"
              initial={{ scale: 0.5, rotate: -10 }}
              animate={{ scale: 1, rotate: 0 }}
              exit={{ scale: 0.5, rotate: 10 }}
              transition={{ type: 'spring', damping: 15 }}
            >
              <div className="text-center">
                <motion.div
                  className="text-6xl mb-4"
                  animate={{ 
                    scale: [1, 1.2, 1],
                    rotate: [0, 10, -10, 0]
                  }}
                  transition={{ 
                    duration: 0.6,
                    repeat: 3
                  }}
                >
                  {achievements[0].icon}
                </motion.div>
                
                <h2 className="text-2xl font-bold text-yellow-400 mb-2">
                  ¡LOGRO LEGENDARIO!
                </h2>
                
                <h3 className="text-xl font-semibold text-white mb-3">
                  {achievements[0].name}
                </h3>
                
                <p className="text-gray-300 mb-6">
                  {achievements[0].description}
                </p>
                
                <div className="flex items-center justify-center gap-4 mb-6">
                  <div className="flex items-center gap-2 px-4 py-2 bg-yellow-500/20 rounded-full">
                    <Zap className="w-5 h-5 text-yellow-400" />
                    <span className="text-yellow-400 font-bold">
                      +{achievements[0].xpReward} XP
                    </span>
                  </div>
                  
                  <div className="flex items-center gap-2 px-4 py-2 bg-purple-500/20 rounded-full">
                    <Star className="w-5 h-5 text-purple-400" />
                    <span className="text-purple-400 font-bold capitalize">
                      {achievements[0].rarity}
                    </span>
                  </div>
                </div>
                
                <button
                  onClick={() => clearEvents()}
                  className="px-6 py-3 bg-gradient-to-r from-yellow-500 to-orange-500 text-white font-bold rounded-lg hover:from-yellow-600 hover:to-orange-600 transition-all"
                >
                  ¡Increíble!
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
};

export default RealtimeNotifications;