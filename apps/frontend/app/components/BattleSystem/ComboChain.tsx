'use client';

import React, { useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface ComboChainProps {
  combo: number;
  maxCombo?: number;
  isActive: boolean;
  onComboBreak?: () => void;
}

export default function ComboChain({ 
  combo, 
  maxCombo = 10,
  isActive,
  onComboBreak 
}: ComboChainProps) {
  const prevComboRef = useRef(combo);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  // Draw lightning effect between combo nodes
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    if (!isActive || combo < 2) return;

    // Draw lightning between combo points
    ctx.strokeStyle = combo >= 5 ? '#fbbf24' : '#8b5cf6';
    ctx.lineWidth = 2;
    ctx.shadowBlur = 10;
    ctx.shadowColor = combo >= 5 ? '#fbbf24' : '#8b5cf6';

    const segmentWidth = canvas.width / (maxCombo - 1);
    
    for (let i = 0; i < combo - 1; i++) {
      ctx.beginPath();
      const x1 = i * segmentWidth;
      const x2 = (i + 1) * segmentWidth;
      const y = canvas.height / 2;
      
      // Create lightning effect with random zigzag
      ctx.moveTo(x1, y);
      
      const segments = 3;
      for (let j = 1; j <= segments; j++) {
        const x = x1 + (x2 - x1) * (j / segments);
        const yOffset = (Math.random() - 0.5) * 20;
        ctx.lineTo(x, y + yOffset);
      }
      
      ctx.stroke();
    }
  }, [combo, isActive, maxCombo]);

  // Detect combo break
  useEffect(() => {
    if (prevComboRef.current > combo && prevComboRef.current > 0) {
      onComboBreak?.();
    }
    prevComboRef.current = combo;
  }, [combo, onComboBreak]);

  const getComboTier = () => {
    if (combo >= 10) return { text: 'LEGENDARY', color: 'text-yellow-400', glow: 'shadow-yellow-400' };
    if (combo >= 7) return { text: 'EPIC', color: 'text-purple-400', glow: 'shadow-purple-400' };
    if (combo >= 5) return { text: 'GREAT', color: 'text-blue-400', glow: 'shadow-blue-400' };
    if (combo >= 3) return { text: 'GOOD', color: 'text-green-400', glow: 'shadow-green-400' };
    return { text: 'COMBO', color: 'text-white', glow: 'shadow-white' };
  };

  const tier = getComboTier();

  return (
    <div className="relative w-full max-w-md mx-auto">
      {/* Canvas for lightning effect */}
      <canvas
        ref={canvasRef}
        width={400}
        height={60}
        className="absolute inset-0 w-full h-full pointer-events-none"
        style={{ filter: 'blur(1px)' }}
      />
      
      {/* Combo nodes */}
      <div className="relative flex justify-between items-center py-4">
        {Array.from({ length: maxCombo }, (_, i) => (
          <motion.div
            key={i}
            initial={{ scale: 0 }}
            animate={{ 
              scale: i < combo ? 1 : 0.5,
              opacity: i < combo ? 1 : 0.3
            }}
            transition={{ 
              type: 'spring',
              stiffness: 500,
              damping: 30,
              delay: i * 0.05
            }}
            className="relative"
          >
            <div
              className={`
                w-8 h-8 rounded-full flex items-center justify-center
                ${i < combo ? 'bg-purple-600' : 'bg-gray-700'}
                ${i < combo && combo >= 5 ? 'animate-pulse' : ''}
                transition-all duration-300
              `}
            >
              <span className="text-white text-xs font-bold">{i + 1}</span>
            </div>
            
            {/* Glow effect for active nodes */}
            {i < combo && (
              <motion.div
                className="absolute inset-0 rounded-full"
                animate={{ 
                  boxShadow: [
                    '0 0 10px rgba(139, 92, 246, 0.5)',
                    '0 0 20px rgba(139, 92, 246, 0.8)',
                    '0 0 10px rgba(139, 92, 246, 0.5)'
                  ]
                }}
                transition={{ duration: 1, repeat: Infinity }}
              />
            )}
          </motion.div>
        ))}
      </div>

      {/* Combo counter display */}
      <AnimatePresence>
        {combo > 0 && isActive && (
          <motion.div
            initial={{ scale: 0, y: 20 }}
            animate={{ scale: 1, y: 0 }}
            exit={{ scale: 0, y: -20 }}
            className="absolute -top-16 left-1/2 transform -translate-x-1/2"
          >
            <div className={`
              px-4 py-2 rounded-lg bg-black/80 backdrop-blur-sm
              ${tier.color} font-bold text-xl
              shadow-lg ${tier.glow}
            `}>
              <motion.span
                animate={{ scale: [1, 1.1, 1] }}
                transition={{ duration: 0.3, repeat: Infinity }}
              >
                {tier.text} ×{combo}
              </motion.span>
              
              {combo >= 5 && (
                <motion.span
                  className="ml-2"
                  animate={{ rotate: 360 }}
                  transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                >
                  ⚡
                </motion.span>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Break effect */}
      <AnimatePresence>
        {!isActive && prevComboRef.current > 2 && (
          <motion.div
            initial={{ scale: 0.5, opacity: 0 }}
            animate={{ scale: 1.5, opacity: 1 }}
            exit={{ scale: 2, opacity: 0 }}
            transition={{ duration: 0.5 }}
            className="absolute inset-0 flex items-center justify-center pointer-events-none"
          >
            <div className="text-red-500 font-bold text-3xl drop-shadow-lg">
              COMBO BREAK!
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}