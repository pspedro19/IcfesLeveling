'use client';

import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface GameStatsProps {
  streak: number;
  totalXP: number;
  hearts: number;
  level: number;
  nextLevelXP: number;
  onMuteToggle?: () => void;
  isMuted?: boolean;
}

export const GameStats = React.memo(function GameStats({
  streak,
  totalXP,
  hearts,
  level,
  nextLevelXP,
  onMuteToggle,
  isMuted = false,
}: GameStatsProps) {
  const [showXPGain, setShowXPGain] = useState<number | null>(null);
  const [prevHearts, setPrevHearts] = useState(hearts);
  const [shakeHearts, setShakeHearts] = useState(false);
  const [prevXP, setPrevXP] = useState(totalXP);

  useEffect(() => {
    if (totalXP > prevXP) {
      const gained = totalXP - prevXP;
      setShowXPGain(gained);
      setPrevXP(totalXP);
      const t = setTimeout(() => setShowXPGain(null), 2000);
      return () => clearTimeout(t);
    }
  }, [totalXP, prevXP]);

  useEffect(() => {
    if (hearts < prevHearts) {
      setShakeHearts(true);
      setPrevHearts(hearts);
      const t = setTimeout(() => setShakeHearts(false), 500);
      return () => clearTimeout(t);
    }
  }, [hearts, prevHearts]);

  const xpProgress = ((totalXP % nextLevelXP) / nextLevelXP) * 100;

  return (
    <motion.div
      className="glass-panel-game flex items-center justify-between relative"
      initial={{ y: -100, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.5, ease: 'easeOut' }}
    >
      <div className={`streak-counter ${streak > 10 ? 'high-streak' : ''}`}>
        <motion.div
          className="flame-icon"
          animate={streak > 0 ? { scale: [1, 1.2, 1] } : {}}
          transition={{ duration: 0.5, repeat: Infinity, repeatDelay: 2 }}
        >
          🔥
        </motion.div>
        <div>
          <motion.div className="streak-number" key={streak} initial={{ scale: 0.5 }} animate={{ scale: 1 }}>
            {streak}
          </motion.div>
          <div className="streak-label">RACHA</div>
        </div>
      </div>

      <motion.div className="flex gap-2" animate={shakeHearts ? { x: [-10, 10, -10, 10, 0] } : {}} transition={{ duration: 0.5 }}>
        {[...Array(3)].map((_, i) => (
          <motion.span key={i} className="text-3xl" initial={{ scale: 0 }} animate={{ scale: 1 }} transition={{ delay: i * 0.1 }}>
            {i < hearts ? '❤️' : '💔'}
          </motion.span>
        ))}
      </motion.div>

      <div className="text-right flex-1 max-w-xs">
        <div className="flex justify-between items-center mb-2">
          <span className="text-sm text-gray-400">NIVEL {level}</span>
          <motion.div className="text-2xl font-bold text-game-neonGold" key={totalXP} initial={{ scale: 0.8 }} animate={{ scale: 1 }}>
            {totalXP.toLocaleString()} XP
          </motion.div>
        </div>
        <div className="level-progress-bar">
          <motion.div className="level-progress-fill" initial={{ width: 0 }} animate={{ width: `${xpProgress}%` }} transition={{ duration: 0.5 }} />
        </div>
        <div className="text-xs text-gray-500 mt-1">Siguiente nivel: {nextLevelXP - (totalXP % nextLevelXP)} XP</div>
      </div>

      <button onClick={onMuteToggle} className="ml-4 p-2 rounded-lg hover:bg-game-dark/50 transition-colors" aria-label={isMuted ? 'Activar sonido' : 'Silenciar'}>
        {isMuted ? '🔇' : '🔊'}
      </button>

      <AnimatePresence>
        {showXPGain && (
          <motion.div className="xp-gain-popup" initial={{ y: 0, opacity: 1 }} animate={{ y: -50, opacity: 0 }} exit={{ opacity: 0 }} transition={{ duration: 2 }}>
            +{showXPGain} XP
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
});

GameStats.displayName = 'GameStats';


