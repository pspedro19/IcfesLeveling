'use client';

import React from 'react';
import ModeToggle from '@/components/ui/ModeToggle';
import { AudioProvider } from '@/components/PortalLogin/AudioEngine';
import { useGameModeStore } from '@/stores/useGameModeStore';
import { motion } from 'framer-motion';
import { Lock, Unlock, Trophy, Zap } from 'lucide-react';

export default function ModeTogglePage() {
  const { mode, modeSettings, canAccessContent } = useGameModeStore();
  
  // Ejemplos de contenido con diferentes niveles de acceso
  const contentExamples = [
    {
      title: 'Mazmorra de Álgebra Básica',
      accuracy: 85,
      hasWeaknesses: false,
      icon: '📐',
      difficulty: 'Fácil'
    },
    {
      title: 'Torre del Cálculo Infinito',
      accuracy: 65,
      hasWeaknesses: true,
      icon: '🏰',
      difficulty: 'Difícil'
    },
    {
      title: 'Raid del Teorema Final',
      accuracy: 45,
      hasWeaknesses: true,
      icon: '⚔️',
      difficulty: 'Legendario'
    },
    {
      title: 'Práctica de Geometría',
      accuracy: 92,
      hasWeaknesses: false,
      icon: '📏',
      difficulty: 'Medio'
    }
  ];
  
  return (
    <AudioProvider>
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900 to-indigo-900 p-8">
        <div className="max-w-6xl mx-auto">
          <motion.h1 
            className="text-4xl font-bold text-white text-center mb-8 font-cinzel"
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
          >
            Sistema de Modos de Juego
          </motion.h1>
          
          {/* Mode Toggle Component */}
          <div className="max-w-2xl mx-auto mb-12">
            <ModeToggle 
              onModeChange={(newMode) => {
                console.log('Modo cambiado a:', newMode);
              }}
            />
          </div>
          
          {/* Current Mode Status */}
          <motion.div 
            className="bg-gray-800/50 rounded-lg p-6 mb-8 text-center"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.2 }}
          >
            <h2 className="text-2xl font-semibold text-white mb-4">
              Modo Actual: <span className={mode === 'casual' ? 'text-blue-400' : 'text-purple-400'}>
                {mode === 'casual' ? 'Casual' : 'Progresión'}
              </span>
            </h2>
            
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6">
              <div className="bg-gray-700/50 rounded-lg p-4">
                <p className="text-gray-400 text-sm">Precisión Mínima</p>
                <p className="text-2xl font-bold text-white">{modeSettings.minimumAccuracy}%</p>
              </div>
              <div className="bg-gray-700/50 rounded-lg p-4">
                <p className="text-gray-400 text-sm">Requisitos</p>
                <p className="text-2xl font-bold text-white">
                  {modeSettings.unlockRequirements ? 'Sí' : 'No'}
                </p>
              </div>
              <div className="bg-gray-700/50 rounded-lg p-4">
                <p className="text-gray-400 text-sm">Saltar Contenido</p>
                <p className="text-2xl font-bold text-white">
                  {modeSettings.allowSkipContent ? 'Permitido' : 'No'}
                </p>
              </div>
              <div className="bg-gray-700/50 rounded-lg p-4">
                <p className="text-gray-400 text-sm">Progresión Rango</p>
                <p className="text-2xl font-bold text-white">
                  {modeSettings.rankProgressionLocked ? 'Bloqueada' : 'Libre'}
                </p>
              </div>
            </div>
          </motion.div>
          
          {/* Content Access Examples */}
          <div>
            <h3 className="text-xl font-semibold text-white mb-6 text-center">
              Ejemplos de Acceso a Contenido
            </h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {contentExamples.map((content, index) => {
                const hasAccess = canAccessContent(content.accuracy, content.hasWeaknesses);
                
                return (
                  <motion.div
                    key={content.title}
                    className={`bg-gray-800 rounded-lg p-6 border-2 transition-all ${
                      hasAccess 
                        ? 'border-green-500/50 hover:border-green-500' 
                        : 'border-red-500/50 hover:border-red-500'
                    }`}
                    initial={{ opacity: 0, x: index % 2 === 0 ? -20 : 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.1 }}
                  >
                    <div className="flex items-start justify-between mb-4">
                      <div className="flex items-center gap-3">
                        <span className="text-3xl">{content.icon}</span>
                        <div>
                          <h4 className="text-lg font-semibold text-white">
                            {content.title}
                          </h4>
                          <p className="text-sm text-gray-400">
                            Dificultad: {content.difficulty}
                          </p>
                        </div>
                      </div>
                      {hasAccess ? (
                        <Unlock className="w-6 h-6 text-green-400" />
                      ) : (
                        <Lock className="w-6 h-6 text-red-400" />
                      )}
                    </div>
                    
                    <div className="space-y-2 mb-4">
                      <div className="flex justify-between text-sm">
                        <span className="text-gray-400">Precisión:</span>
                        <span className={content.accuracy >= modeSettings.minimumAccuracy ? 'text-green-400' : 'text-red-400'}>
                          {content.accuracy}%
                        </span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span className="text-gray-400">Áreas Débiles:</span>
                        <span className={content.hasWeaknesses ? 'text-red-400' : 'text-green-400'}>
                          {content.hasWeaknesses ? 'Sí' : 'No'}
                        </span>
                      </div>
                    </div>
                    
                    <div className={`text-center py-3 rounded-lg font-semibold ${
                      hasAccess 
                        ? 'bg-green-600/20 text-green-300' 
                        : 'bg-red-600/20 text-red-300'
                    }`}>
                      {hasAccess ? '✅ Acceso Permitido' : '❌ Acceso Bloqueado'}
                    </div>
                    
                    {!hasAccess && mode === 'gated' && (
                      <p className="text-xs text-gray-400 mt-3 text-center">
                        {content.accuracy < modeSettings.minimumAccuracy && 
                          `Requiere ${modeSettings.minimumAccuracy}% de precisión`}
                        {content.hasWeaknesses && content.accuracy >= modeSettings.minimumAccuracy &&
                          'Elimina las áreas débiles primero'}
                      </p>
                    )}
                  </motion.div>
                );
              })}
            </div>
          </div>
          
          {/* Mode Benefits */}
          <motion.div 
            className="mt-12 bg-gray-800/30 rounded-lg p-8 text-center"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5 }}
          >
            <h3 className="text-2xl font-semibold text-white mb-6">
              Beneficios del Modo {mode === 'casual' ? 'Casual' : 'Progresión'}
            </h3>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {mode === 'casual' ? (
                <>
                  <div className="flex flex-col items-center">
                    <Zap className="w-12 h-12 text-blue-400 mb-3" />
                    <h4 className="font-semibold text-white mb-2">Práctica Libre</h4>
                    <p className="text-sm text-gray-300">
                      Explora todo el contenido sin restricciones
                    </p>
                  </div>
                  <div className="flex flex-col items-center">
                    <Trophy className="w-12 h-12 text-yellow-400 mb-3" />
                    <h4 className="font-semibold text-white mb-2">Sin Presión</h4>
                    <p className="text-sm text-gray-300">
                      Aprende a tu propio ritmo sin requisitos
                    </p>
                  </div>
                  <div className="flex flex-col items-center">
                    <Unlock className="w-12 h-12 text-green-400 mb-3" />
                    <h4 className="font-semibold text-white mb-2">Todo Desbloqueado</h4>
                    <p className="text-sm text-gray-300">
                      Accede a cualquier nivel o desafío
                    </p>
                  </div>
                </>
              ) : (
                <>
                  <div className="flex flex-col items-center">
                    <Lock className="w-12 h-12 text-purple-400 mb-3" />
                    <h4 className="font-semibold text-white mb-2">Progresión Estructurada</h4>
                    <p className="text-sm text-gray-300">
                      Avanza paso a paso dominando cada tema
                    </p>
                  </div>
                  <div className="flex flex-col items-center">
                    <Trophy className="w-12 h-12 text-yellow-400 mb-3" />
                    <h4 className="font-semibold text-white mb-2">Logros Significativos</h4>
                    <p className="text-sm text-gray-300">
                      Cada desbloqueo es un logro real
                    </p>
                  </div>
                  <div className="flex flex-col items-center">
                    <Zap className="w-12 h-12 text-orange-400 mb-3" />
                    <h4 className="font-semibold text-white mb-2">Máximo Aprendizaje</h4>
                    <p className="text-sm text-gray-300">
                      Garantiza dominio completo de cada área
                    </p>
                  </div>
                </>
              )}
            </div>
          </motion.div>
        </div>
      </div>
    </AudioProvider>
  );
}