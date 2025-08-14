'use client';

import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface Achievement {
  id: string;
  icon: string;
  title: string;
  description: string;
  rarity?: 'common' | 'rare' | 'epic' | 'legendary';
}

interface AchievementPopupProps {
  achievement: Achievement | null;
  onClose: () => void;
}

export function AchievementPopup({ achievement, onClose }: AchievementPopupProps) {
  const getRarityClass = (rarity?: string) => {
    switch (rarity) {
      case 'legendary':
        return 'border-game-rankSS bg-game-rankSS/20';
      case 'epic':
        return 'border-game-rankS bg-game-rankS/20';
      case 'rare':
        return 'border-game-rankA bg-game-rankA/20';
      default:
        return 'border-game-rankB bg-game-rankB/20';
    }
  };

  return (
    <AnimatePresence>
      {achievement && (
        <motion.div
          className="achievement-popup"
          initial={{ x: 400, opacity: 0 }}
          animate={{ x: 0, opacity: 1 }}
          exit={{ x: 400, opacity: 0 }}
          transition={{ type: 'spring', damping: 25, stiffness: 300 }}
        >
          <motion.div
            className={`achievement-card ${getRarityClass(achievement.rarity)}`}
            initial={{ scale: 0.8, rotate: -10 }}
            animate={{ scale: 1, rotate: 0 }}
            transition={{ delay: 0.2 }}
            onClick={onClose}
          >
            {achievement.rarity === 'legendary' && (
              <div className="legendary-particles">
                {[...Array(8)].map((_, i) => (
                  <div key={i} className={`legendary-particle particle-${i}`}>⭐</div>
                ))}
              </div>
            )}

            <motion.div className="achievement-icon" animate={{ rotate: [0, 10, -10, 0] }} transition={{ duration: 0.5, delay: 0.5 }}>
              {achievement.icon}
            </motion.div>
            <h3 className="achievement-title">{achievement.title}</h3>
            <p className="achievement-desc">{achievement.description}</p>
            <div className="achievement-rarity-bar">
              <div className={`h-1 rounded-full ${getRarityClass(achievement.rarity)}`} />
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}


