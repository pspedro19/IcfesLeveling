'use client';

import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Trophy, 
  Sword, 
  Shield, 
  Star, 
  Zap, 
  Heart,
  Skull,
  Lock,
  Unlock,
  TrendingUp,
  Gift,
  Crown
} from 'lucide-react';

export interface Notification {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info' | 'achievement' | 'level_up' | 'quest_complete' | 'loot';
  title: string;
  message: string;
  icon?: React.ReactNode;
  duration?: number;
  visual?: 'explosion' | 'sparkle' | 'glow' | 'shake';
  sound?: string;
  actions?: {
    label: string;
    onClick: () => void;
  }[];
}

interface EpicNotificationProps {
  notification: Notification | null;
  onDismiss?: () => void;
}

export default function EpicNotification({ notification, onDismiss }: EpicNotificationProps) {
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    if (notification) {
      setIsVisible(true);
      
      // Auto dismiss after duration
      if (notification.duration) {
        const timer = setTimeout(() => {
          handleDismiss();
        }, notification.duration);
        
        return () => clearTimeout(timer);
      }
    }
  }, [notification]);

  const handleDismiss = () => {
    setIsVisible(false);
    setTimeout(() => {
      onDismiss?.();
    }, 300);
  };

  const getNotificationStyle = (type: string) => {
    switch (type) {
      case 'success':
        return {
          bg: 'from-green-900/90 to-emerald-900/90',
          border: 'border-green-500/50',
          text: 'text-green-300',
          icon: <Sword className="w-6 h-6" />
        };
      case 'error':
        return {
          bg: 'from-red-900/90 to-rose-900/90',
          border: 'border-red-500/50',
          text: 'text-red-300',
          icon: <Skull className="w-6 h-6" />
        };
      case 'achievement':
        return {
          bg: 'from-yellow-900/90 to-amber-900/90',
          border: 'border-yellow-500/50',
          text: 'text-yellow-300',
          icon: <Trophy className="w-6 h-6" />
        };
      case 'level_up':
        return {
          bg: 'from-purple-900/90 to-violet-900/90',
          border: 'border-purple-500/50',
          text: 'text-purple-300',
          icon: <TrendingUp className="w-6 h-6" />
        };
      case 'quest_complete':
        return {
          bg: 'from-blue-900/90 to-indigo-900/90',
          border: 'border-blue-500/50',
          text: 'text-blue-300',
          icon: <Star className="w-6 h-6" />
        };
      case 'loot':
        return {
          bg: 'from-orange-900/90 to-amber-900/90',
          border: 'border-orange-500/50',
          text: 'text-orange-300',
          icon: <Gift className="w-6 h-6" />
        };
      default:
        return {
          bg: 'from-gray-900/90 to-slate-900/90',
          border: 'border-gray-500/50',
          text: 'text-gray-300',
          icon: <Shield className="w-6 h-6" />
        };
    }
  };

  if (!notification) return null;

  const style = getNotificationStyle(notification.type);

  return (
    <AnimatePresence>
      {isVisible && (
        <motion.div
          initial={{ opacity: 0, y: -100, scale: 0.8 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, y: -50, scale: 0.9 }}
          transition={{ type: 'spring', stiffness: 500, damping: 30 }}
          className="fixed top-8 left-1/2 transform -translate-x-1/2 z-50 max-w-md w-full px-4"
        >
          <div className={`
            relative overflow-hidden rounded-lg shadow-2xl
            bg-gradient-to-r ${style.bg} backdrop-blur-lg
            border-2 ${style.border}
          `}>
            {/* Background effect */}
            {notification.visual === 'sparkle' && (
              <div className="absolute inset-0 pointer-events-none">
                {[...Array(10)].map((_, i) => (
                  <motion.div
                    key={i}
                    className="absolute w-1 h-1 bg-white rounded-full"
                    initial={{ 
                      x: Math.random() * 400,
                      y: Math.random() * 100,
                      opacity: 0
                    }}
                    animate={{ 
                      opacity: [0, 1, 0],
                      scale: [0, 1.5, 0]
                    }}
                    transition={{ 
                      duration: 2,
                      delay: i * 0.1,
                      repeat: Infinity
                    }}
                  />
                ))}
              </div>
            )}

            {/* Glow effect */}
            {notification.visual === 'glow' && (
              <motion.div
                className="absolute inset-0 pointer-events-none"
                animate={{ 
                  boxShadow: [
                    'inset 0 0 20px rgba(255,255,255,0.1)',
                    'inset 0 0 40px rgba(255,255,255,0.2)',
                    'inset 0 0 20px rgba(255,255,255,0.1)'
                  ]
                }}
                transition={{ duration: 2, repeat: Infinity }}
              />
            )}

            <div className="relative p-6">
              <div className="flex items-start gap-4">
                {/* Icon */}
                <motion.div
                  className={`
                    flex-shrink-0 p-3 rounded-full
                    bg-black/30 ${style.text}
                  `}
                  animate={notification.visual === 'shake' ? {
                    x: [0, -2, 2, -2, 2, 0],
                    rotate: [0, -5, 5, -5, 5, 0]
                  } : {}}
                  transition={{ duration: 0.5, repeat: notification.visual === 'shake' ? Infinity : 0 }}
                >
                  {notification.icon || style.icon}
                </motion.div>

                {/* Content */}
                <div className="flex-1">
                  <h3 className="text-white font-bold text-lg mb-1">
                    {notification.title}
                  </h3>
                  <p className={`${style.text} text-sm`}>
                    {notification.message}
                  </p>

                  {/* Actions */}
                  {notification.actions && notification.actions.length > 0 && (
                    <div className="flex gap-2 mt-3">
                      {notification.actions.map((action, index) => (
                        <motion.button
                          key={index}
                          onClick={action.onClick}
                          className="px-3 py-1 bg-white/10 hover:bg-white/20 rounded text-white text-sm font-medium transition-colors"
                          whileHover={{ scale: 1.05 }}
                          whileTap={{ scale: 0.95 }}
                        >
                          {action.label}
                        </motion.button>
                      ))}
                    </div>
                  )}
                </div>

                {/* Close button */}
                <button
                  onClick={handleDismiss}
                  className="flex-shrink-0 text-white/50 hover:text-white transition-colors"
                >
                  ✕
                </button>
              </div>

              {/* Special effects for certain types */}
              {notification.type === 'level_up' && (
                <motion.div
                  className="absolute -bottom-2 -right-2 text-6xl opacity-20"
                  animate={{ rotate: 360 }}
                  transition={{ duration: 10, repeat: Infinity, ease: 'linear' }}
                >
                  <Crown />
                </motion.div>
              )}

              {notification.type === 'achievement' && (
                <div className="mt-4 flex items-center justify-center">
                  <motion.div
                    className="flex gap-1"
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    transition={{ delay: 0.3, type: 'spring' }}
                  >
                    {[...Array(5)].map((_, i) => (
                      <Star
                        key={i}
                        className={`w-4 h-4 ${i < 3 ? 'text-yellow-400 fill-yellow-400' : 'text-gray-600'}`}
                      />
                    ))}
                  </motion.div>
                </div>
              )}
            </div>

            {/* Progress bar for timed notifications */}
            {notification.duration && (
              <motion.div
                className="absolute bottom-0 left-0 h-1 bg-white/30"
                initial={{ width: '100%' }}
                animate={{ width: '0%' }}
                transition={{ duration: notification.duration / 1000, ease: 'linear' }}
              />
            )}
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

// Notification Manager Hook - Versión simplificada temporal
export function useNotifications() {
  const [currentNotification, setCurrentNotification] = useState<Notification | null>(null);

  const showNotification = (notification: Omit<Notification, 'id'>) => {
    const newNotification: Notification = {
      ...notification,
      id: Date.now().toString(),
      duration: notification.duration || 5000
    };
    
    // Mostrar directamente sin cola para evitar bucles
    setCurrentNotification(newNotification);
    
    // Auto-dismiss después de la duración
    if (newNotification.duration > 0) {
      setTimeout(() => {
        setCurrentNotification(null);
      }, newNotification.duration);
    }
  };

  const dismissNotification = () => {
    setCurrentNotification(null);
  };

  return {
    currentNotification,
    showNotification,
    dismissNotification
  };
}