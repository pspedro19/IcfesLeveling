'use client';

import React from 'react';
import { motion } from 'framer-motion';

interface NavigationPillsProps {
  totalQuestions: number;
  currentQuestion: number;
  answeredQuestions: Set<number>;
  skippedQuestions: Set<number>;
  onQuestionClick: (index: number) => void;
}

export function NavigationPills({
  totalQuestions,
  currentQuestion,
  answeredQuestions,
  skippedQuestions,
  onQuestionClick,
}: NavigationPillsProps) {
  return (
    <motion.div className="glass-panel-game" initial={{ x: -100, opacity: 0 }} animate={{ x: 0, opacity: 1 }} transition={{ duration: 0.5 }}>
      <h3 className="text-sm font-game text-game-neonPurple mb-4 uppercase tracking-wider">Navegación de Preguntas</h3>
      <div className="grid grid-cols-5 gap-2 mb-4">
        {Array.from({ length: totalQuestions }, (_, i) => {
          const num = i + 1;
          const isCurrent = num === currentQuestion;
          const isAnswered = answeredQuestions.has(num);
          const isSkipped = skippedQuestions.has(num);
          return (
            <motion.button
              key={num}
              onClick={() => onQuestionClick(num - 1)}
              className={`nav-pill-game ${isCurrent ? 'current' : ''} ${isAnswered ? 'answered' : ''} ${isSkipped ? 'skipped' : ''}`}
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.95 }}
              initial={{ scale: 0, rotate: -180 }}
              animate={{ scale: 1, rotate: 0 }}
              transition={{ delay: i * 0.02 }}
            >
              {!isAnswered && num}
            </motion.button>
          );
        })}
      </div>
      <div className="space-y-2">
        <div className="flex items-center justify-between text-sm">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-game-correct"></div>
            <span className="text-gray-400">Respondidas</span>
          </div>
          <span className="font-bold text-game-correct">{answeredQuestions.size}</span>
        </div>
        <div className="flex items-center justify-between text-sm">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-game-warning"></div>
            <span className="text-gray-400">Saltadas</span>
          </div>
          <span className="font-bold text-game-warning">{skippedQuestions.size}</span>
        </div>
        <div className="flex items-center justify-between text-sm">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-gray-600"></div>
            <span className="text-gray-400">Restantes</span>
          </div>
          <span className="font-bold text-gray-400">{totalQuestions - answeredQuestions.size - skippedQuestions.size}</span>
        </div>
      </div>
    </motion.div>
  );
}


