'use client';

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Gamepad2, 
  GraduationCap, 
  Lock, 
  Unlock,
  Info,
  ChevronRight,
  CheckCircle,
  XCircle,
  Settings
} from 'lucide-react';
import { useGameModeStore } from '@/stores/useGameModeStore';
import { useAudio } from '../PortalLogin/AudioEngine';

interface ModeToggleProps {
  className?: string;
  showDetails?: boolean;
  onModeChange?: (mode: 'casual' | 'gated') => void;
}

export default function ModeToggle({ className = '', showDetails = true, onModeChange }: ModeToggleProps) {
  const { mode, modeSettings, setMode, getModeDescription } = useGameModeStore();
  const { playSound } = useAudio();
  const [showInfo, setShowInfo] = useState(false);
  
  const handleModeChange = (newMode: 'casual' | 'gated') => {
    if (newMode === mode) return;
    
    playSound('typing_click');
    setMode(newMode);
    
    if (onModeChange) {
      onModeChange(newMode);
    }
  };
  
  const modeFeatures = {
    casual: [
      { icon: <Unlock className="w-4 h-4" />, text: 'Acceso libre a todo el contenido', enabled: true },
      { icon: <Gamepad2 className="w-4 h-4" />, text: 'Práctica sin restricciones', enabled: true },
      { icon: <XCircle className="w-4 h-4" />, text: 'Sin requisitos de precisión', enabled: true },
      { icon: <CheckCircle className="w-4 h-4" />, text: 'Progresión flexible', enabled: true },
      { icon: <Info className="w-4 h-4" />, text: 'Ideal para exploración', enabled: true }
    ],
    gated: [
      { icon: <Lock className="w-4 h-4" />, text: 'Contenido desbloqueado por logros', enabled: true },
      { icon: <GraduationCap className="w-4 h-4" />, text: 'Progresión estructurada', enabled: true },
      { icon: <CheckCircle className="w-4 h-4" />, text: 'Mínimo 80% precisión requerida', enabled: true },
      { icon: <ChevronRight className="w-4 h-4" />, text: 'Domina cada tema para avanzar', enabled: true },
      { icon: <Settings className="w-4 h-4" />, text: 'Máximo aprendizaje garantizado', enabled: true }
    ]
  };
  
  return (
    <div className={`relative ${className}`}>
      {/* Toggle Switch */}
      <div className="bg-gray-800 rounded-lg p-1 flex">
        <motion.button
          className={`flex-1 py-3 px-4 rounded-md font-semibold transition-all flex items-center justify-center gap-2 ${
            mode === 'casual'
              ? 'bg-blue-600 text-white'
              : 'text-gray-400 hover:text-white'
          }`}
          onClick={() => handleModeChange('casual')}
          whileHover={{ scale: mode === 'casual' ? 1 : 1.02 }}
          whileTap={{ scale: 0.98 }}
        >
          <Gamepad2 className="w-5 h-5" />
          <span>Modo Casual</span>
        </motion.button>
        
        <motion.button
          className={`flex-1 py-3 px-4 rounded-md font-semibold transition-all flex items-center justify-center gap-2 ${
            mode === 'gated'
              ? 'bg-purple-600 text-white'
              : 'text-gray-400 hover:text-white'
          }`}
          onClick={() => handleModeChange('gated')}
          whileHover={{ scale: mode === 'gated' ? 1 : 1.02 }}
          whileTap={{ scale: 0.98 }}
        >
          <GraduationCap className="w-5 h-5" />
          <span>Modo Progresión</span>
        </motion.button>
      </div>
      
      {/* Mode Description */}
      {showDetails && (
        <motion.div
          className="mt-4 text-center"
          key={mode}
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
        >
          <p className="text-gray-300 text-sm">
            {getModeDescription()}
          </p>
        </motion.div>
      )}
      
      {/* Info Button */}
      <button
        onClick={() => setShowInfo(!showInfo)}
        className="absolute top-2 right-2 text-gray-400 hover:text-white transition-colors"
      >
        <Info className="w-5 h-5" />
      </button>
      
      {/* Detailed Info Modal */}
      <AnimatePresence>
        {showInfo && (
          <>
            <motion.div
              className="fixed inset-0 bg-black/60 z-40"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setShowInfo(false)}
            />
            
            <motion.div
              className="fixed top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 
                bg-gray-900 rounded-lg p-6 max-w-2xl w-full mx-4 z-50 max-h-[80vh] overflow-y-auto"
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
            >
              <h3 className="text-2xl font-bold text-white mb-6 text-center font-cinzel">
                Modos de Juego
              </h3>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Casual Mode */}
                <div className={`bg-gray-800 rounded-lg p-6 border-2 transition-all ${
                  mode === 'casual' ? 'border-blue-500' : 'border-gray-700'
                }`}>
                  <div className="flex items-center gap-3 mb-4">
                    <div className="w-12 h-12 bg-blue-600 rounded-full flex items-center justify-center">
                      <Gamepad2 className="w-6 h-6 text-white" />
                    </div>
                    <div>
                      <h4 className="text-lg font-semibold text-white">Modo Casual</h4>
                      <p className="text-xs text-blue-400">Exploración Libre</p>
                    </div>
                  </div>
                  
                  <ul className="space-y-3">
                    {modeFeatures.casual.map((feature, index) => (
                      <motion.li
                        key={index}
                        className="flex items-start gap-2"
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: index * 0.1 }}
                      >
                        <span className="text-blue-400 mt-0.5">{feature.icon}</span>
                        <span className="text-sm text-gray-300">{feature.text}</span>
                      </motion.li>
                    ))}
                  </ul>
                  
                  {mode !== 'casual' && (
                    <motion.button
                      className="w-full mt-6 bg-blue-600 hover:bg-blue-700 text-white font-semibold 
                        py-2 px-4 rounded-lg transition-all"
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                      onClick={() => {
                        handleModeChange('casual');
                        setShowInfo(false);
                      }}
                    >
                      Activar Modo Casual
                    </motion.button>
                  )}
                </div>
                
                {/* Gated Mode */}
                <div className={`bg-gray-800 rounded-lg p-6 border-2 transition-all ${
                  mode === 'gated' ? 'border-purple-500' : 'border-gray-700'
                }`}>
                  <div className="flex items-center gap-3 mb-4">
                    <div className="w-12 h-12 bg-purple-600 rounded-full flex items-center justify-center">
                      <GraduationCap className="w-6 h-6 text-white" />
                    </div>
                    <div>
                      <h4 className="text-lg font-semibold text-white">Modo Progresión</h4>
                      <p className="text-xs text-purple-400">Aprendizaje Estructurado</p>
                    </div>
                  </div>
                  
                  <ul className="space-y-3">
                    {modeFeatures.gated.map((feature, index) => (
                      <motion.li
                        key={index}
                        className="flex items-start gap-2"
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: index * 0.1 }}
                      >
                        <span className="text-purple-400 mt-0.5">{feature.icon}</span>
                        <span className="text-sm text-gray-300">{feature.text}</span>
                      </motion.li>
                    ))}
                  </ul>
                  
                  {mode !== 'gated' && (
                    <motion.button
                      className="w-full mt-6 bg-purple-600 hover:bg-purple-700 text-white font-semibold 
                        py-2 px-4 rounded-lg transition-all"
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                      onClick={() => {
                        handleModeChange('gated');
                        setShowInfo(false);
                      }}
                    >
                      Activar Modo Progresión
                    </motion.button>
                  )}
                </div>
              </div>
              
              {/* Current Settings */}
              <div className="mt-6 bg-gray-800/50 rounded-lg p-4">
                <h5 className="text-sm font-semibold text-gray-400 mb-3">
                  Configuración Actual ({mode === 'casual' ? 'Casual' : 'Progresión'})
                </h5>
                <div className="grid grid-cols-2 gap-3 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-400">Requisito de precisión:</span>
                    <span className="text-white">{modeSettings.minimumAccuracy}%</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Desbloqueos:</span>
                    <span className="text-white">
                      {modeSettings.unlockRequirements ? 'Requeridos' : 'Libre'}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Saltar contenido:</span>
                    <span className="text-white">
                      {modeSettings.allowSkipContent ? 'Permitido' : 'No permitido'}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Progresión de rango:</span>
                    <span className="text-white">
                      {modeSettings.rankProgressionLocked ? 'Bloqueada' : 'Libre'}
                    </span>
                  </div>
                </div>
              </div>
              
              <button
                onClick={() => setShowInfo(false)}
                className="mt-6 w-full bg-gray-700 hover:bg-gray-600 text-white font-semibold 
                  py-3 px-4 rounded-lg transition-all"
              >
                Cerrar
              </button>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </div>
  );
}