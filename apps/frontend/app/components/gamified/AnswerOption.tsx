'use client';

import React, { useState } from 'react';
import { motion } from 'framer-motion';

interface AnswerOptionProps {
  label: string;
  text: string;
  imageUrl?: string;
  isSelected: boolean;
  isCorrect?: boolean;
  isIncorrect?: boolean;
  onClick: () => void;
  disabled?: boolean;
  delay?: number;
  onHover?: () => void;
  isLocked?: boolean;
}

export const AnswerOption = React.memo(function AnswerOption({
  label,
  text,
  imageUrl,
  isSelected,
  isCorrect,
  isIncorrect,
  onClick,
  disabled,
  delay = 0,
  onHover,
  isLocked = false,
}: AnswerOptionProps) {
  const [showParticles, setShowParticles] = useState(false);

  const handleClick = () => {
    if (!disabled && !isLocked) {
      onClick();
      if (isCorrect) {
        setShowParticles(true);
        setTimeout(() => setShowParticles(false), 1000);
      }
    }
  };

  const classes = [
    'answer-option-game',
    isSelected && 'selected',
    isCorrect && 'correct',
    isIncorrect && 'incorrect',
    disabled && 'disabled',
    isLocked && 'locked',
  ]
    .filter(Boolean)
    .join(' ');

  return (
    <motion.button
      onClick={handleClick}
      onHoverStart={onHover}
      disabled={!!disabled || isLocked}
      className={classes}
      initial={{ opacity: 0, x: -50 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.4, delay, ease: 'easeOut' }}
      whileHover={!disabled && !isLocked ? { scale: 1.02, x: 10, transition: { duration: 0.2 } } : {}}
      whileTap={!disabled && !isLocked ? { scale: 0.98 } : {}}
    >
      <motion.div className="option-label" animate={isCorrect ? { rotate: 360 } : {}} transition={{ duration: 0.5 }}>
        {!isCorrect && !isIncorrect && label}
      </motion.div>

      <div className="option-text">
        {imageUrl && (
          <img
            src={imageUrl}
            alt={`Opción ${label}`}
            style={{ maxWidth: '100%', height: 'auto', borderRadius: 8, marginBottom: text ? 8 : 0 }}
          />
        )}
        {text && <span>{text}</span>}
      </div>

      {isLocked && (
        <div className="locked-indicator">
          <span>🔒</span>
        </div>
      )}

      {showParticles && (
        <div className="particle-burst">
          {[...Array(6)].map((_, i) => (
            <div key={i} className={`success-particle particle-${i}`}>✨</div>
          ))}
        </div>
      )}
    </motion.button>
  );
});

AnswerOption.displayName = 'AnswerOption';


