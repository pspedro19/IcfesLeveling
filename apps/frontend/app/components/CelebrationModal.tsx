'use client';

import React, { useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Trophy, Star, Flame, Zap, Diamond, X } from 'lucide-react';

interface CelebrationData {
  title: string;
  message: string;
  xp: number;
  orbs: number;
  celebrationLevel: number;
}

interface CelebrationModalProps {
  type: 'unit_complete' | 'level_up' | 'streak' | 'achievement';
  data: CelebrationData;
  isOpen: boolean;
  onClose: () => void;
}

function RewardItem({ icon, value, color }: { icon: React.ReactNode; value: string; color: string }) {
  return (
    <motion.div
      className="flex items-center gap-2"
      initial={{ scale: 0 }}
      animate={{ scale: 1 }}
      transition={{ delay: 0.5 }}
    >
      <div className={`${color}`}>
        {icon}
      </div>
      <span className="font-bold text-gray-900 dark:text-white">{value}</span>
    </motion.div>
  );
}

function Confetti() {
  const confettiColors = ['#14BF96', '#3B82F6', '#A855F7', '#F59E0B', '#EF4444'];
  
  return (
    <div className="absolute inset-0 pointer-events-none overflow-hidden">
      {Array.from({ length: 50 }).map((_, i) => (
        <motion.div
          key={i}
          className="absolute w-2 h-2 rounded-sm"
          style={{
            backgroundColor: confettiColors[i % confettiColors.length],
            left: `${Math.random() * 100}%`,
            top: '-10px'
          }}
          animate={{
            y: ['0vh', '100vh'],
            x: [0, Math.random() * 200 - 100],
            rotate: [0, 360],
            scale: [1, 0]
          }}
          transition={{
            duration: Math.random() * 3 + 2,
            ease: "easeOut",
            delay: Math.random() * 0.5
          }}
        />
      ))}
    </div>
  );
}

export function CelebrationModal({ type, data, isOpen, onClose }: CelebrationModalProps) {
  useEffect(() => {
    if (isOpen && data.celebrationLevel >= 3) {
      // Trigger confetti for high celebration levels
      const confettiContainer = document.getElementById('confetti-container');
      if (confettiContainer) {
        // Simple confetti effect
        for (let i = 0; i < 100; i++) {
          setTimeout(() => {
            const confetti = document.createElement('div');
            confetti.className = 'absolute w-2 h-2 rounded-sm';
            confetti.style.backgroundColor = ['#14BF96', '#3B82F6', '#A855F7', '#F59E0B', '#EF4444'][Math.floor(Math.random() * 5)];
            confetti.style.left = `${Math.random() * 100}%`;
            confetti.style.top = '-10px';
            confetti.style.zIndex = '9999';
            
            confettiContainer.appendChild(confetti);
            
            // Animate confetti
            confetti.animate([
              { transform: 'translateY(0vh) rotate(0deg)', opacity: 1 },
              { transform: `translateY(100vh) rotate(${Math.random() * 360}deg)`, opacity: 0 }
            ], {
              duration: Math.random() * 3000 + 2000,
              easing: 'ease-out'
            }).onfinish = () => confetti.remove();
          }, i * 50);
        }
      }
    }
  }, [isOpen, data.celebrationLevel]);

  if (!isOpen) return null;

  const getIcon = () => {
    switch (type) {
      case 'unit_complete': return <Trophy className="w-12 h-12 text-white" />;
      case 'level_up': return <Star className="w-12 h-12 text-white" />;
      case 'streak': return <Flame className="w-12 h-12 text-white" />;
      case 'achievement': return <Zap className="w-12 h-12 text-white" />;
      default: return <Trophy className="w-12 h-12 text-white" />;
    }
  };

  const getTitle = () => {
    switch (type) {
      case 'unit_complete': return '¡Unidad Completada!';
      case 'level_up': return '¡Subida de Nivel!';
      case 'streak': return '¡Racha Increíble!';
      case 'achievement': return '¡Logro Desbloqueado!';
      default: return '¡Celebración!';
    }
  };

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm"
        onClick={onClose}
      >
        <motion.div
          initial={{ scale: 0, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          exit={{ scale: 0, opacity: 0 }}
          transition={{ type: "spring", damping: 25, stiffness: 300 }}
          className="relative bg-white dark:bg-gray-800 rounded-2xl p-8 max-w-md mx-4 shadow-2xl"
          onClick={(e) => e.stopPropagation()}
        >
          {/* Close Button */}
          <button
            onClick={onClose}
            className="absolute top-4 right-4 p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
          >
            <X className="w-5 h-5 text-gray-500" />
          </button>

          {/* Confetti Container */}
          <div id="confetti-container" className="absolute inset-0 pointer-events-none overflow-hidden" />

          {/* Celebration Icon */}
          <motion.div
            animate={{ 
              rotate: [0, -10, 10, -10, 0],
              scale: [1, 1.1, 1]
            }}
            transition={{ duration: 0.5 }}
            className="flex justify-center mb-6"
          >
            <div className="w-24 h-24 bg-gradient-to-br from-teal-500 to-blue-500 
                            rounded-full flex items-center justify-center shadow-lg">
              {getIcon()}
            </div>
          </motion.div>

          {/* Message */}
          <motion.h2
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ delay: 0.2 }}
            className="text-2xl font-bold text-center mb-2 text-gray-900 dark:text-white"
          >
            {getTitle()}
          </motion.h2>
          
          <motion.p
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ delay: 0.3 }}
            className="text-center text-gray-600 dark:text-gray-400 mb-6"
          >
            {data.message}
          </motion.p>

          {/* Rewards */}
          <motion.div
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ delay: 0.4 }}
            className="flex justify-center gap-6 mb-6"
          >
            <RewardItem 
              icon={<Zap className="w-5 h-5" />} 
              value={`+${data.xp} XP`} 
              color="text-yellow-500" 
            />
            <RewardItem 
              icon={<Diamond className="w-5 h-5" />} 
              value={`+${data.orbs} Orbs`} 
              color="text-purple-500" 
            />
          </motion.div>

          {/* Action Button */}
          <motion.button
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ delay: 0.5 }}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={onClose}
            className="w-full py-3 bg-gradient-to-r from-teal-500 to-blue-500 
                       text-white font-bold rounded-xl shadow-lg hover:shadow-xl
                       transition-all duration-300"
          >
            ¡Continuar Conquistando!
          </motion.button>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}
