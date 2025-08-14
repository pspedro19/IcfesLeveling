'use client';

import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface DamageNumber {
  id: string;
  value: number;
  type: 'damage' | 'heal' | 'critical' | 'miss';
  x: number;
  y: number;
}

interface DamageNumbersProps {
  damage?: number;
  type?: 'damage' | 'heal' | 'critical' | 'miss';
  position?: { x: number; y: number };
  onComplete?: () => void;
}

export default function DamageNumbers({ 
  damage, 
  type = 'damage', 
  position = { x: 50, y: 50 },
  onComplete 
}: DamageNumbersProps) {
  const [numbers, setNumbers] = useState<DamageNumber[]>([]);

  useEffect(() => {
    if (damage && damage > 0) {
      const newNumber: DamageNumber = {
        id: `${Date.now()}-${Math.random()}`,
        value: damage,
        type,
        x: position.x + (Math.random() - 0.5) * 20,
        y: position.y
      };
      
      setNumbers(prev => [...prev, newNumber]);
      
      // Remove after animation
      setTimeout(() => {
        setNumbers(prev => prev.filter(n => n.id !== newNumber.id));
        onComplete?.();
      }, 1500);
    }
  }, [damage, type, position, onComplete]);

  const getColorClass = (type: string) => {
    switch (type) {
      case 'damage': return 'text-red-500';
      case 'heal': return 'text-green-500';
      case 'critical': return 'text-yellow-400';
      case 'miss': return 'text-gray-400';
      default: return 'text-white';
    }
  };

  const getFontSize = (type: string) => {
    switch (type) {
      case 'critical': return 'text-4xl md:text-5xl';
      case 'miss': return 'text-xl md:text-2xl';
      default: return 'text-2xl md:text-3xl';
    }
  };

  return (
    <div className="fixed inset-0 pointer-events-none z-50">
      <AnimatePresence>
        {numbers.map((number) => (
          <motion.div
            key={number.id}
            initial={{ 
              x: number.x + '%', 
              y: number.y + '%',
              scale: 0.5,
              opacity: 0
            }}
            animate={{ 
              x: number.x + '%',
              y: (number.y - 20) + '%',
              scale: [0.5, 1.2, 1],
              opacity: [0, 1, 1, 0]
            }}
            exit={{ opacity: 0 }}
            transition={{ 
              duration: 1.5,
              scale: { times: [0, 0.3, 0.5] },
              opacity: { times: [0, 0.1, 0.8, 1] }
            }}
            className={`
              absolute font-bold ${getColorClass(number.type)} ${getFontSize(number.type)}
              drop-shadow-[0_2px_4px_rgba(0,0,0,0.8)]
            `}
            style={{
              textShadow: number.type === 'critical' 
                ? '0 0 20px currentColor, 0 0 40px currentColor' 
                : '0 2px 4px rgba(0,0,0,0.8)'
            }}
          >
            {number.type === 'critical' && (
              <motion.span
                animate={{ rotate: 360 }}
                transition={{ duration: 0.5 }}
                className="inline-block mr-1"
              >
                ⚡
              </motion.span>
            )}
            {number.type === 'miss' ? 'MISS' : number.value}
            {number.type === 'critical' && (
              <motion.span
                animate={{ scale: [1, 1.2, 1] }}
                transition={{ duration: 0.3, repeat: 2 }}
                className="inline-block ml-1"
              >
                !
              </motion.span>
            )}
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  );
}