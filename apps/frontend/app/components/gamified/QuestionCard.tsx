'use client';

import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface QuestionCardProps {
  questionNumber: number;
  totalQuestions: number;
  questionText: string;
  difficulty: number;
  timeRemaining: number;
  category: string;
  imageUrl?: string;
  combo?: number;
  isBossQuestion?: boolean;
}

export const QuestionCard = React.memo(function QuestionCard({
  questionNumber,
  totalQuestions,
  questionText,
  difficulty,
  timeRemaining,
  category,
  imageUrl,
  combo = 0,
  isBossQuestion = false,
}: QuestionCardProps) {
  const [showCombo, setShowCombo] = useState(false);

  const getPowerRank = () => {
    if (difficulty >= 9) return { rank: 'SS', color: 'game-rankSS' };
    if (difficulty >= 7) return { rank: 'S', color: 'game-rankS' };
    if (difficulty >= 5) return { rank: 'A', color: 'game-rankA' };
    if (difficulty >= 3) return { rank: 'B', color: 'game-rankB' };
    return { rank: 'C', color: 'game-rankC' };
  };

  const { rank, color } = getPowerRank();
  const timeMinutes = Math.floor(timeRemaining / 60);
  const timeSeconds = timeRemaining % 60;
  const isUrgent = timeRemaining < 300;
  const isCritical = timeRemaining < 60;

  useEffect(() => {
    if (combo > 1) {
      setShowCombo(true);
      const timer = setTimeout(() => setShowCombo(false), 2000);
      return () => clearTimeout(timer);
    }
  }, [combo]);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20, scale: 0.95 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, y: -20, scale: 0.95 }}
      transition={{ duration: 0.5, ease: 'easeOut' }}
      className={`question-card-game ${isBossQuestion ? 'boss-question' : ''}`}
    >
      {isBossQuestion && (
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <div className="particle particle-1"></div>
          <div className="particle particle-2"></div>
          <div className="particle particle-3"></div>
        </div>
      )}

      <div className="flex justify-between items-start mb-8">
        <div className="flex items-center gap-6">
          <div className="power-badge relative">
            <div className="power-frame"></div>
            <div className={`power-rank text-${color}`}>{rank}</div>
            <div className="absolute -inset-4">
              <div className="floating-particle delay-0"></div>
              <div className="floating-particle delay-1"></div>
              <div className="floating-particle delay-2"></div>
            </div>
          </div>

          <div>
            <h1 className="text-3xl font-epic text-game-neonPurple text-glow">PRUEBA DE PODER</h1>
            <p className="text-lg text-gray-400 font-game">
              {category} - Pregunta {questionNumber} de {totalQuestions}
            </p>
          </div>

          <AnimatePresence>
            {showCombo && combo > 1 && (
              <motion.div
                initial={{ scale: 0, rotate: -180 }}
                animate={{ scale: 1, rotate: 0 }}
                exit={{ scale: 0, rotate: 180 }}
                className="combo-indicator"
              >
                <span className="text-4xl">🔥</span>
                <span className="combo-text">x{combo}</span>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        <div className={`game-timer ${isCritical ? 'critical' : isUrgent ? 'warning' : 'normal'}`}>
          <span className="tabular-nums">
            {timeMinutes.toString().padStart(2, '0')}:{timeSeconds.toString().padStart(2, '0')}
          </span>
        </div>
      </div>

      <div className="mb-8">
        <div className="xp-bar">
          <motion.div
            className="xp-bar-fill"
            initial={{ width: 0 }}
            animate={{ width: `${(questionNumber / totalQuestions) * 100}%` }}
            transition={{ duration: 1, ease: 'easeOut' }}
          >
            <div className="xp-progress-shine"></div>
          </motion.div>
          <div className="xp-text">{Math.round((questionNumber / totalQuestions) * 100)}% COMPLETADO</div>
        </div>
      </div>

      <motion.div
        className="bg-game-void/50 rounded-xl p-8 border border-game-neonPurple/20"
        initial={{ scale: 0.98 }}
        animate={{ scale: 1 }}
        transition={{ duration: 0.3 }}
      >
        <p className="text-xl leading-relaxed text-gray-100 font-game">{questionText}</p>
        {imageUrl && (
          <motion.img
            src={imageUrl}
            alt="Imagen de la pregunta"
            className="mt-6 rounded-xl shadow-2xl max-w-full h-auto mx-auto"
            loading="lazy"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
          />
        )}
      </motion.div>
    </motion.div>
  );
});

QuestionCard.displayName = 'QuestionCard';


