'use client';

import React, { useState } from 'react';
import MultiplayerRaid from '@/components/Raids/MultiplayerRaid';
import { AudioProvider } from '@/components/PortalLogin/AudioEngine';
import { motion } from 'framer-motion';
import { Skull, Users, Timer, Trophy, Sword, Shield } from 'lucide-react';

export default function MultiplayerRaidPage() {
  const [selectedRaid, setSelectedRaid] = useState<string | null>(null);
  const [raidResult, setRaidResult] = useState<'victory' | 'defeat' | null>(null);
  
  // Mock raids for demonstration
  const availableRaids = [
    {
      id: 'raid-001',
      name: 'Sombra del Conocimiento',
      description: 'Un jefe que se alimenta de la ignorancia',
      difficulty: 'normal',
      playerCount: '4-8 jugadores',
      estimatedTime: '10-15 min',
      rewards: '500 EXP, Orbes Sombra',
      icon: '👤',
      color: 'from-purple-600 to-purple-800'
    },
    {
      id: 'raid-002',
      name: 'Dragón de Cálculo',
      description: 'Maestro de las matemáticas complejas',
      difficulty: 'hard',
      playerCount: '6-10 jugadores',
      estimatedTime: '15-20 min',
      rewards: '1000 EXP, Escamas Doradas',
      icon: '🐉',
      color: 'from-red-600 to-orange-800'
    },
    {
      id: 'raid-003',
      name: 'Titán del Teorema',
      description: 'El guardián de las verdades absolutas',
      difficulty: 'mythic',
      playerCount: '8-12 jugadores',
      estimatedTime: '20-30 min',
      rewards: '2000 EXP, Fragmento Mítico',
      icon: '⚔️',
      color: 'from-yellow-600 to-red-800'
    }
  ];
  
  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty) {
      case 'normal': return 'text-green-400';
      case 'hard': return 'text-orange-400';
      case 'mythic': return 'text-red-400';
      default: return 'text-gray-400';
    }
  };
  
  const handleRaidComplete = (result: 'victory' | 'defeat') => {
    setRaidResult(result);
    setTimeout(() => {
      setSelectedRaid(null);
      setRaidResult(null);
    }, 5000);
  };
  
  return (
    <AudioProvider>
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900 to-indigo-900 p-8">
        <div className="max-w-7xl mx-auto">
          <motion.h1 
            className="text-4xl font-bold text-white text-center mb-8 font-cinzel"
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
          >
            Raids Multijugador
          </motion.h1>
          
          {!selectedRaid ? (
            <div>
              <p className="text-center text-gray-300 mb-8">
                Únete a otros cazadores para derrotar jefes épicos y obtener recompensas legendarias
              </p>
              
              {/* Raid Selection */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
                {availableRaids.map((raid, index) => (
                  <motion.div
                    key={raid.id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.1 }}
                    className="bg-gray-800/50 rounded-lg overflow-hidden hover:bg-gray-800/70 
                      transition-all cursor-pointer border-2 border-transparent hover:border-purple-500"
                    onClick={() => setSelectedRaid(raid.id)}
                  >
                    <div className={`h-32 bg-gradient-to-br ${raid.color} flex items-center 
                      justify-center text-6xl`}>
                      {raid.icon}
                    </div>
                    
                    <div className="p-6">
                      <div className="flex items-center justify-between mb-2">
                        <h3 className="text-xl font-bold text-white">
                          {raid.name}
                        </h3>
                        <span className={`text-sm font-semibold ${getDifficultyColor(raid.difficulty)}`}>
                          {raid.difficulty.toUpperCase()}
                        </span>
                      </div>
                      
                      <p className="text-gray-400 text-sm mb-4">
                        {raid.description}
                      </p>
                      
                      <div className="space-y-2 text-sm">
                        <div className="flex items-center gap-2 text-gray-300">
                          <Users className="w-4 h-4" />
                          <span>{raid.playerCount}</span>
                        </div>
                        
                        <div className="flex items-center gap-2 text-gray-300">
                          <Timer className="w-4 h-4" />
                          <span>{raid.estimatedTime}</span>
                        </div>
                        
                        <div className="flex items-center gap-2 text-gray-300">
                          <Trophy className="w-4 h-4" />
                          <span>{raid.rewards}</span>
                        </div>
                      </div>
                      
                      <motion.button
                        className="w-full mt-4 bg-gradient-to-r from-purple-600 to-purple-700 
                          hover:from-purple-700 hover:to-purple-800 text-white font-semibold 
                          py-2 rounded-lg transition-all"
                        whileHover={{ scale: 1.02 }}
                        whileTap={{ scale: 0.98 }}
                      >
                        Unirse a la Raid
                      </motion.button>
                    </div>
                  </motion.div>
                ))}
              </div>
              
              {/* Features */}
              <div className="bg-gray-800/30 rounded-lg p-8">
                <h2 className="text-2xl font-semibold text-white mb-6 text-center">
                  Características del Sistema de Raids
                </h2>
                
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  <div className="flex items-start gap-4">
                    <div className="w-12 h-12 bg-purple-600/20 rounded-lg flex items-center 
                      justify-center flex-shrink-0">
                      <Users className="w-6 h-6 text-purple-400" />
                    </div>
                    <div>
                      <h3 className="font-semibold text-white mb-2">
                        Cooperación en Tiempo Real
                      </h3>
                      <p className="text-gray-400 text-sm">
                        Coordina con tu equipo usando WebSocket para sincronización instantánea
                      </p>
                    </div>
                  </div>
                  
                  <div className="flex items-start gap-4">
                    <div className="w-12 h-12 bg-red-600/20 rounded-lg flex items-center 
                      justify-center flex-shrink-0">
                      <Skull className="w-6 h-6 text-red-400" />
                    </div>
                    <div>
                      <h3 className="font-semibold text-white mb-2">
                        Mecánicas de Jefe Dinámicas
                      </h3>
                      <p className="text-gray-400 text-sm">
                        Cada fase trae nuevos desafíos y patrones de ataque
                      </p>
                    </div>
                  </div>
                  
                  <div className="flex items-start gap-4">
                    <div className="w-12 h-12 bg-yellow-600/20 rounded-lg flex items-center 
                      justify-center flex-shrink-0">
                      <Trophy className="w-6 h-6 text-yellow-400" />
                    </div>
                    <div>
                      <h3 className="font-semibold text-white mb-2">
                        Recompensas Épicas
                      </h3>
                      <p className="text-gray-400 text-sm">
                        Obtén experiencia, objetos únicos y logros especiales
                      </p>
                    </div>
                  </div>
                  
                  <div className="flex items-start gap-4">
                    <div className="w-12 h-12 bg-blue-600/20 rounded-lg flex items-center 
                      justify-center flex-shrink-0">
                      <Shield className="w-6 h-6 text-blue-400" />
                    </div>
                    <div>
                      <h3 className="font-semibold text-white mb-2">
                        Sistema de Roles
                      </h3>
                      <p className="text-gray-400 text-sm">
                        Tank, DPS y Healer con habilidades únicas
                      </p>
                    </div>
                  </div>
                  
                  <div className="flex items-start gap-4">
                    <div className="w-12 h-12 bg-green-600/20 rounded-lg flex items-center 
                      justify-center flex-shrink-0">
                      <Sword className="w-6 h-6 text-green-400" />
                    </div>
                    <div>
                      <h3 className="font-semibold text-white mb-2">
                        Combos y Daño Crítico
                      </h3>
                      <p className="text-gray-400 text-sm">
                        Encadena respuestas correctas para multiplicar tu daño
                      </p>
                    </div>
                  </div>
                  
                  <div className="flex items-start gap-4">
                    <div className="w-12 h-12 bg-orange-600/20 rounded-lg flex items-center 
                      justify-center flex-shrink-0">
                      <Timer className="w-6 h-6 text-orange-400" />
                    </div>
                    <div>
                      <h3 className="font-semibold text-white mb-2">
                        Timer de Enrage
                      </h3>
                      <p className="text-gray-400 text-sm">
                        Derrota al jefe antes de que se vuelva imparable
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
            >
              <div className="mb-4 flex items-center justify-between">
                <h2 className="text-2xl font-semibold text-white">
                  {availableRaids.find(r => r.id === selectedRaid)?.name}
                </h2>
                
                <button
                  onClick={() => setSelectedRaid(null)}
                  className="bg-gray-700 hover:bg-gray-600 text-white px-4 py-2 
                    rounded-lg transition-colors"
                >
                  Salir de la Raid
                </button>
              </div>
              
              <MultiplayerRaid
                raidId={selectedRaid}
                onComplete={handleRaidComplete}
              />
              
              {raidResult && (
                <motion.div
                  className="mt-4 p-4 rounded-lg text-center"
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                >
                  <p className={`text-lg font-semibold ${
                    raidResult === 'victory' ? 'text-green-400' : 'text-red-400'
                  }`}>
                    {raidResult === 'victory' 
                      ? '¡Felicidades! Has completado la raid exitosamente' 
                      : 'La raid ha fallado. ¡Inténtalo de nuevo!'}
                  </p>
                </motion.div>
              )}
            </motion.div>
          )}
        </div>
      </div>
    </AudioProvider>
  );
}