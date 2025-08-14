'use client';

import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { 
  Smartphone,
  Camera,
  Sparkles,
  Shield,
  Sword,
  Gem,
  ChevronRight,
  Info
} from 'lucide-react';
import ARDungeonButton from '@/components/AR/ARDungeonButton';
import { useARSupport, getARReadinessMessage } from '@/hooks/useARSupport';

// Sample dungeon data
const sampleDungeons = [
  {
    id: 1,
    name: 'Torre del Conocimiento',
    difficulty: 5,
    floors: 3,
    theme: 'Matemáticas',
    monsters: ['Espectro Algebraico', 'Golem de Geometría', 'Dragón de Cálculo'],
    color: 'from-purple-600 to-blue-600',
    icon: <Sparkles className="w-6 h-6" />
  },
  {
    id: 2,
    name: 'Cripta de las Ciencias',
    difficulty: 7,
    floors: 4,
    theme: 'Ciencias Naturales',
    monsters: ['Quimera Química', 'Elemental de Física', 'Bestia Biológica', 'Titán Termodinámico'],
    color: 'from-green-600 to-teal-600',
    icon: <Shield className="w-6 h-6" />
  },
  {
    id: 3,
    name: 'Fortaleza del Lenguaje',
    difficulty: 6,
    floors: 3,
    theme: 'Lectura Crítica',
    monsters: ['Espíritu Gramático', 'Sombra Semántica', 'Fantasma de la Comprensión'],
    color: 'from-orange-600 to-red-600',
    icon: <Sword className="w-6 h-6" />
  },
  {
    id: 4,
    name: 'Mazmorra del Razonamiento',
    difficulty: 9,
    floors: 5,
    theme: 'Razonamiento Cuantitativo',
    monsters: ['Hidra Lógica', 'Minotauro Matemático', 'Esfinge Estadística', 'Kraken Probabilístico', 'Dragón de Datos'],
    color: 'from-pink-600 to-purple-600',
    icon: <Gem className="w-6 h-6" />
  }
];

export default function ARDemoPage() {
  const [selectedDungeon, setSelectedDungeon] = useState(sampleDungeons[0]);
  const arSupport = useARSupport();
  
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900 
      to-gray-900 relative overflow-hidden">
      {/* Background Effects */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-0 left-0 w-96 h-96 bg-purple-600/20 
          rounded-full blur-3xl animate-pulse" />
        <div className="absolute bottom-0 right-0 w-96 h-96 bg-blue-600/20 
          rounded-full blur-3xl animate-pulse animation-delay-2000" />
      </div>
      
      <div className="relative z-10 container mx-auto px-4 py-8">
        {/* Header */}
        <motion.div 
          className="text-center mb-8"
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <div className="inline-flex items-center justify-center w-20 h-20 
            bg-gradient-to-br from-purple-600 to-blue-600 rounded-full mb-4">
            <Camera className="w-10 h-10 text-white" />
          </div>
          
          <h1 className="text-4xl font-bold text-white mb-4 font-cinzel">
            WebAR Preview de Mazmorras
          </h1>
          
          <p className="text-gray-300 max-w-2xl mx-auto">
            Explora las mazmorras en realidad aumentada directamente desde tu 
            navegador. Visualiza la estructura, pisos y desafíos en 3D.
          </p>
        </motion.div>
        
        {/* AR Support Status */}
        <motion.div
          className={`max-w-2xl mx-auto mb-8 p-4 rounded-lg border ${
            arSupport.isSupported 
              ? 'bg-green-900/20 border-green-500/30' 
              : 'bg-yellow-900/20 border-yellow-500/30'
          }`}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
        >
          <div className="flex items-center gap-3">
            {arSupport.isSupported ? (
              <Smartphone className="w-6 h-6 text-green-400" />
            ) : (
              <Info className="w-6 h-6 text-yellow-400" />
            )}
            <div>
              <p className={`font-semibold ${
                arSupport.isSupported ? 'text-green-400' : 'text-yellow-400'
              }`}>
                {getARReadinessMessage(arSupport)}
              </p>
              {!arSupport.isSupported && (
                <p className="text-sm text-gray-400 mt-1">
                  Puedes usar la vista 3D estándar como alternativa
                </p>
              )}
            </div>
          </div>
        </motion.div>
        
        {/* Dungeon Selection */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {sampleDungeons.map((dungeon, index) => (
            <motion.button
              key={dungeon.id}
              onClick={() => setSelectedDungeon(dungeon)}
              className={`
                relative overflow-hidden rounded-lg p-6 
                bg-gradient-to-br ${dungeon.color}
                transform transition-all duration-300
                ${selectedDungeon.id === dungeon.id 
                  ? 'scale-105 ring-4 ring-white/50' 
                  : 'hover:scale-105'
                }
              `}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
              whileHover={{ y: -5 }}
            >
              <div className="relative z-10">
                <div className="w-12 h-12 bg-white/20 rounded-lg flex items-center 
                  justify-center mb-4">
                  {dungeon.icon}
                </div>
                
                <h3 className="text-lg font-bold text-white mb-2">
                  {dungeon.name}
                </h3>
                
                <div className="space-y-1 text-sm text-white/80">
                  <p>Dificultad: {dungeon.difficulty}/10</p>
                  <p>Pisos: {dungeon.floors}</p>
                  <p>Enemigos: {dungeon.monsters.length}</p>
                </div>
              </div>
              
              {/* Selection indicator */}
              {selectedDungeon.id === dungeon.id && (
                <motion.div
                  className="absolute inset-0 bg-white/20"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                />
              )}
            </motion.button>
          ))}
        </div>
        
        {/* Selected Dungeon Details */}
        <motion.div
          key={selectedDungeon.id}
          className="max-w-4xl mx-auto bg-gray-900/80 rounded-lg p-8 border 
            border-purple-500/30"
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
        >
          <div className="text-center mb-6">
            <h2 className="text-3xl font-bold text-white mb-2">
              {selectedDungeon.name}
            </h2>
            <p className="text-gray-400">
              Tema: {selectedDungeon.theme}
            </p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            <div className="bg-gray-800/50 rounded-lg p-4 text-center">
              <p className="text-gray-400 text-sm mb-1">Dificultad</p>
              <p className="text-3xl font-bold text-red-400">
                {selectedDungeon.difficulty}/10
              </p>
            </div>
            
            <div className="bg-gray-800/50 rounded-lg p-4 text-center">
              <p className="text-gray-400 text-sm mb-1">Pisos</p>
              <p className="text-3xl font-bold text-blue-400">
                {selectedDungeon.floors}
              </p>
            </div>
            
            <div className="bg-gray-800/50 rounded-lg p-4 text-center">
              <p className="text-gray-400 text-sm mb-1">Monstruos</p>
              <p className="text-3xl font-bold text-purple-400">
                {selectedDungeon.monsters.length}
              </p>
            </div>
          </div>
          
          <div className="mb-8">
            <h3 className="text-lg font-semibold text-white mb-3">
              Enemigos en esta mazmorra:
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {selectedDungeon.monsters.map((monster, index) => (
                <div
                  key={index}
                  className="flex items-center gap-3 bg-gray-800/50 
                    rounded-lg p-3"
                >
                  <ChevronRight className="w-4 h-4 text-purple-400" />
                  <span className="text-gray-300">{monster}</span>
                </div>
              ))}
            </div>
          </div>
          
          {/* AR Preview Button */}
          <div className="text-center">
            <ARDungeonButton
              dungeonData={selectedDungeon}
              className="inline-flex"
            />
            
            <p className="text-sm text-gray-400 mt-4">
              {arSupport.isSupported 
                ? 'Asegúrate de permitir el acceso a la cámara para AR'
                : 'Vista 3D disponible para todos los dispositivos'
              }
            </p>
          </div>
        </motion.div>
        
        {/* Instructions */}
        <motion.div
          className="mt-8 max-w-4xl mx-auto bg-gray-900/80 rounded-lg p-6 
            border border-gray-700"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
        >
          <h3 className="text-xl font-semibold text-white mb-4">
            Instrucciones de Uso
          </h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-gray-300">
            <div>
              <h4 className="font-semibold text-white mb-2">Para AR:</h4>
              <ol className="space-y-2 text-sm list-decimal list-inside">
                <li>Usa un dispositivo móvil compatible</li>
                <li>Permite el acceso a la cámara cuando se solicite</li>
                <li>Apunta a una superficie plana</li>
                <li>Toca para colocar la mazmorra</li>
                <li>Muévete alrededor para explorar</li>
              </ol>
            </div>
            
            <div>
              <h4 className="font-semibold text-white mb-2">Para Vista 3D:</h4>
              <ol className="space-y-2 text-sm list-decimal list-inside">
                <li>Funciona en cualquier dispositivo</li>
                <li>Arrastra para rotar la vista</li>
                <li>Pellizca o usa la rueda del mouse para zoom</li>
                <li>Doble clic para centrar la vista</li>
                <li>Usa los controles en pantalla</li>
              </ol>
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  );
}