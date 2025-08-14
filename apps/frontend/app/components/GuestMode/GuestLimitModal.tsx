'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { Lock, Brain, Swords } from 'lucide-react';

interface GuestLimitModalProps {
  isOpen: boolean;
  onClose: () => void;
  limitType: string;
  onUpgrade?: () => void;
}

export default function GuestLimitModal({
  isOpen,
  onClose,
  limitType,
  onUpgrade
}: GuestLimitModalProps) {
  if (!isOpen) return null;

  const getLimitInfo = () => {
    switch (limitType) {
      case 'daily_questions':
        return {
          title: 'Límite de Preguntas',
          description: 'Has alcanzado el límite diario',
          icon: Brain
        };
      case 'dungeon_floors':
        return {
          title: 'Pisos Bloqueados',
          description: 'Solo puedes acceder al primer piso',
          icon: Swords
        };
      default:
        return {
          title: 'Función Bloqueada',
          description: 'Requiere cuenta completa',
          icon: Lock
        };
    }
  };

  const limitInfo = getLimitInfo();
  const IconComponent = limitInfo.icon;

  return (
    <motion.div
      className="fixed inset-0 bg-black/80 z-50 flex items-center justify-center p-4"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
    >
      <motion.div
        className="bg-gray-900 rounded-lg p-8 max-w-md w-full border border-purple-500/30"
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
      >
        <div className="text-center">
          <IconComponent className="w-16 h-16 text-yellow-400 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-white mb-4">
            {limitInfo.title}
          </h2>
          <p className="text-gray-300 mb-6">
            {limitInfo.description}
          </p>
          
          <div className="flex gap-3">
            <button
              onClick={onUpgrade}
              className="flex-1 px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg font-semibold transition-all"
            >
              Crear Cuenta
            </button>
            <button
              onClick={onClose}
              className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg font-semibold transition-all"
            >
              Continuar
            </button>
          </div>
        </div>
      </motion.div>
    </motion.div>
  );
} 