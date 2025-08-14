'use client';

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Save, Cloud, CloudOff, CheckCircle, AlertCircle, RefreshCw } from 'lucide-react';

interface SaveState {
  id: string;
  timestamp: Date;
  location: string;
  type: 'auto' | 'manual' | 'checkpoint';
  synced: boolean;
}

interface CrystalSaveProps {
  isSaving?: boolean;
  isOnline?: boolean;
  lastSave?: Date;
  queuedSaves?: number;
  onManualSave?: () => void;
  onSyncQueue?: () => void;
}

export default function CrystalSave({
  isSaving = false,
  isOnline = true,
  lastSave,
  queuedSaves = 0,
  onManualSave,
  onSyncQueue
}: CrystalSaveProps) {
  const [showLog, setShowLog] = useState(false);
  const [saveHistory, setSaveHistory] = useState<SaveState[]>([]);
  const [pulseAnimation, setPulseAnimation] = useState(false);

  // Add save to history when saving
  useEffect(() => {
    if (isSaving) {
      setPulseAnimation(true);
      const newSave: SaveState = {
        id: Date.now().toString(),
        timestamp: new Date(),
        location: 'Mazmorra de Álgebra', // This should be dynamic
        type: 'auto',
        synced: isOnline
      };
      
      setSaveHistory(prev => [newSave, ...prev].slice(0, 10)); // Keep last 10
      
      setTimeout(() => setPulseAnimation(false), 1000);
    }
  }, [isSaving, isOnline]);

  const formatTime = (date: Date) => {
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    
    if (minutes < 1) return 'Justo ahora';
    if (minutes < 60) return `Hace ${minutes}m`;
    if (hours < 24) return `Hace ${hours}h`;
    return date.toLocaleDateString();
  };

  return (
    <>
      {/* Crystal Save Indicator */}
      <motion.div
        className="fixed top-4 right-4 z-50"
        initial={{ opacity: 0, scale: 0.8 }}
        animate={{ opacity: 1, scale: 1 }}
      >
        <motion.button
          onClick={() => setShowLog(!showLog)}
          className={`
            relative p-3 rounded-full backdrop-blur-md transition-all duration-300
            ${isOnline ? 'bg-purple-900/80' : 'bg-gray-900/80'}
            ${isOnline ? 'hover:bg-purple-800/80' : 'hover:bg-gray-800/80'}
            border-2 ${isOnline ? 'border-purple-500' : 'border-gray-500'}
          `}
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
        >
          {/* Crystal Icon */}
          <div className="relative">
            <motion.div
              animate={{ 
                rotate: pulseAnimation ? 360 : 0,
                scale: pulseAnimation ? [1, 1.2, 1] : 1
              }}
              transition={{ duration: 0.5 }}
            >
              <Save className={`w-6 h-6 ${isOnline ? 'text-purple-300' : 'text-gray-400'}`} />
            </motion.div>
            
            {/* Saving animation */}
            {isSaving && (
              <motion.div
                className="absolute inset-0"
                initial={{ scale: 1, opacity: 1 }}
                animate={{ scale: 2, opacity: 0 }}
                transition={{ duration: 1 }}
              >
                <Save className="w-6 h-6 text-purple-400" />
              </motion.div>
            )}
            
            {/* Offline indicator */}
            {!isOnline && (
              <CloudOff className="absolute -top-1 -right-1 w-4 h-4 text-red-400" />
            )}
            
            {/* Queue badge */}
            {queuedSaves > 0 && (
              <div className="absolute -bottom-1 -right-1 bg-orange-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center font-bold">
                {queuedSaves}
              </div>
            )}
          </div>
          
          {/* Glow effect */}
          <motion.div
            className={`
              absolute inset-0 rounded-full pointer-events-none
              ${isOnline ? 'bg-purple-500' : 'bg-gray-500'}
            `}
            animate={{ 
              opacity: pulseAnimation ? [0.3, 0, 0.3] : 0,
              scale: pulseAnimation ? [1, 1.5, 1] : 1
            }}
            transition={{ duration: 1 }}
          />
        </motion.button>

        {/* Status text */}
        <AnimatePresence>
          {(isSaving || !isOnline || queuedSaves > 0) && (
            <motion.div
              initial={{ opacity: 0, x: 10 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 10 }}
              className="absolute top-1/2 right-full -translate-y-1/2 mr-2 whitespace-nowrap"
            >
              <div className={`
                px-3 py-1 rounded-lg text-sm font-medium
                ${isSaving ? 'bg-purple-900/80 text-purple-300' : ''}
                ${!isOnline ? 'bg-orange-900/80 text-orange-300' : ''}
                ${queuedSaves > 0 && isOnline ? 'bg-blue-900/80 text-blue-300' : ''}
              `}>
                {isSaving && 'Guardando...'}
                {!isOnline && !isSaving && 'Modo Offline'}
                {queuedSaves > 0 && isOnline && !isSaving && 'Sincronizando...'}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>

      {/* Save Log Modal */}
      <AnimatePresence>
        {showLog && (
          <motion.div
            initial={{ opacity: 0, scale: 0.9, originX: 1, originY: 0 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.9 }}
            className="fixed top-20 right-4 z-40 w-80 bg-gray-900/95 backdrop-blur-lg rounded-lg shadow-2xl border border-purple-500/30 overflow-hidden"
          >
            {/* Header */}
            <div className="bg-purple-900/50 px-4 py-3 border-b border-purple-500/30">
              <div className="flex items-center justify-between">
                <h3 className="text-white font-semibold flex items-center gap-2">
                  <Save className="w-4 h-4" />
                  Cristales de Guardado
                </h3>
                <div className={`flex items-center gap-1 text-xs ${isOnline ? 'text-green-400' : 'text-orange-400'}`}>
                  {isOnline ? <Cloud className="w-3 h-3" /> : <CloudOff className="w-3 h-3" />}
                  {isOnline ? 'Online' : 'Offline'}
                </div>
              </div>
            </div>

            {/* Save History */}
            <div className="max-h-64 overflow-y-auto">
              {saveHistory.length > 0 ? (
                <div className="p-2 space-y-1">
                  {saveHistory.map((save) => (
                    <motion.div
                      key={save.id}
                      initial={{ opacity: 0, y: -10 }}
                      animate={{ opacity: 1, y: 0 }}
                      className="bg-gray-800/50 rounded p-2 text-sm"
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <p className="text-purple-300 font-medium">{save.location}</p>
                          <p className="text-gray-400 text-xs">{formatTime(save.timestamp)}</p>
                        </div>
                        <div className="flex items-center gap-1">
                          {save.synced ? (
                            <CheckCircle className="w-4 h-4 text-green-400" />
                          ) : (
                            <AlertCircle className="w-4 h-4 text-orange-400" />
                          )}
                        </div>
                      </div>
                    </motion.div>
                  ))}
                </div>
              ) : (
                <div className="p-4 text-center text-gray-400">
                  No hay guardados recientes
                </div>
              )}
            </div>

            {/* Queue Status */}
            {queuedSaves > 0 && (
              <div className="border-t border-purple-500/30 p-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2 text-orange-300">
                    <AlertCircle className="w-4 h-4" />
                    <span className="text-sm">{queuedSaves} guardados en cola</span>
                  </div>
                  {isOnline && (
                    <button
                      onClick={onSyncQueue}
                      className="text-xs text-blue-400 hover:text-blue-300 flex items-center gap-1"
                    >
                      <RefreshCw className="w-3 h-3" />
                      Sincronizar
                    </button>
                  )}
                </div>
              </div>
            )}

            {/* Actions */}
            <div className="border-t border-purple-500/30 p-3">
              <button
                onClick={onManualSave}
                disabled={isSaving}
                className={`
                  w-full py-2 rounded-lg font-medium transition-all
                  ${isSaving 
                    ? 'bg-gray-700 text-gray-400 cursor-not-allowed' 
                    : 'bg-purple-600 hover:bg-purple-700 text-white'
                  }
                `}
              >
                {isSaving ? 'Guardando...' : 'Guardar Manualmente'}
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Resume Animation */}
      <AnimatePresence>
        {lastSave && (
          <motion.div
            initial={{ opacity: 0, y: 50 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 50 }}
            className="fixed bottom-4 right-4 bg-purple-900/90 backdrop-blur-md rounded-lg p-4 shadow-2xl border border-purple-500/30"
          >
            <h4 className="text-white font-semibold mb-2">¡Bienvenido de vuelta!</h4>
            <div className="space-y-1 text-sm">
              <p className="text-purple-300">+150 XP ganados</p>
              <p className="text-purple-300">+2 Niveles subidos</p>
              <p className="text-purple-300">Nueva habilidad desbloqueada 🔓</p>
            </div>
            <p className="text-xs text-gray-400 mt-2">
              Último guardado: {formatTime(lastSave)}
            </p>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}