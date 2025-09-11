'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { Crown, Zap, Star, Sparkles } from 'lucide-react';

interface RPGProgressBarProps {
  currentLevel: number;
  currentRank: string;
  experience: number;
  experienceToNext: number;
  rankColor: string;
}

export default function RPGProgressBar({
  currentLevel,
  currentRank,
  experience,
  experienceToNext,
  rankColor
}: RPGProgressBarProps) {
  const progressPercentage = (experience / (experience + experienceToNext)) * 100;
  
  const getRankIcon = (rank: string) => {
    switch (rank) {
      case 'S+':
      case 'S':
        return <Crown className="w-6 h-6" />;
      case 'A+':
      case 'A':
        return <Star className="w-6 h-6" />;
      default:
        return <Zap className="w-6 h-6" />;
    }
  };

  const getRankTitle = (rank: string) => {
    switch (rank) {
      case 'S+': return 'Maestro Supremo';
      case 'S': return 'Maestro Élite';
      case 'A+': return 'Experto Superior';
      case 'A': return 'Experto';
      case 'B+': return 'Avanzado Superior';
      case 'B': return 'Avanzado';
      case 'C+': return 'Intermedio Superior';
      case 'C': return 'Intermedio';
      case 'D+': return 'Básico Superior';
      case 'D': return 'Básico';
      default: return 'Novato';
    }
  };

  return (
    <motion.div
      className="bg-gray-900/80 rounded-xl p-6 border border-purple-500/30 relative overflow-hidden"
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.5 }}
    >
      {/* Background Glow Effect */}
      <div className={`absolute inset-0 bg-gradient-to-r ${rankColor} opacity-5`} />
      
      {/* Floating Particles */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        {[...Array(6)].map((_, i) => (
          <motion.div
            key={i}
            className="absolute w-2 h-2 bg-purple-400/30 rounded-full"
            animate={{
              x: [0, 30, 0],
              y: [0, -20, 0],
              opacity: [0.3, 1, 0.3],
            }}
            transition={{
              duration: 3 + i * 0.5,
              repeat: Infinity,
              ease: 'easeInOut',
            }}
            style={{
              left: `${10 + i * 15}%`,
              top: `${20 + (i % 2) * 60}%`,
            }}
          />
        ))}
      </div>

      <div className="relative z-10">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-4">
            <motion.div
              className={`p-3 rounded-xl bg-gradient-to-br ${rankColor} text-white shadow-lg`}
              whileHover={{ scale: 1.05 }}
              transition={{ duration: 0.2 }}
            >
              {getRankIcon(currentRank)}
            </motion.div>
            
            <div>
              <h3 className="text-2xl font-bold text-white flex items-center gap-2">
                Nivel {currentLevel}
                <motion.span
                  animate={{ rotate: [0, 360] }}
                  transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}
                >
                  <Sparkles className="w-5 h-5 text-yellow-400" />
                </motion.span>
              </h3>
              <p className={`text-lg font-semibold bg-gradient-to-r ${rankColor} bg-clip-text text-transparent`}>
                {getRankTitle(currentRank)} - Rango {currentRank}
              </p>
            </div>
          </div>
          
          {/* Experience Numbers */}
          <div className="text-right">
            <p className="text-2xl font-bold text-white">
              {experience.toLocaleString()}
              <span className="text-lg text-gray-400 ml-1">EXP</span>
            </p>
            <p className="text-sm text-gray-400">
              {experienceToNext.toLocaleString()} para siguiente nivel
            </p>
          </div>
        </div>

        {/* Progress Bar */}
        <div className="space-y-3">
          <div className="flex justify-between items-center">
            <span className="text-sm font-semibold text-gray-300">
              Progreso al Nivel {currentLevel + 1}
            </span>
            <span className="text-sm font-bold text-white">
              {progressPercentage.toFixed(1)}%
            </span>
          </div>
          
          <div className="relative">
            {/* Background Bar */}
            <div className="w-full h-4 bg-gray-800 rounded-full overflow-hidden shadow-inner">
              {/* Progress Fill */}
              <motion.div
                className={`h-full bg-gradient-to-r ${rankColor} relative overflow-hidden`}
                initial={{ width: 0 }}
                animate={{ width: `${progressPercentage}%` }}
                transition={{ duration: 1.5, ease: 'easeOut' }}
              >
                {/* Animated Shine Effect */}
                <motion.div
                  className="absolute inset-0 bg-gradient-to-r from-transparent via-white/30 to-transparent"
                  animate={{ x: ['-100%', '100%'] }}
                  transition={{ duration: 2, repeat: Infinity, ease: 'easeInOut' }}
                />
              </motion.div>
            </div>
            
            {/* Progress Markers */}
            <div className="absolute top-0 w-full h-4 flex justify-between items-center px-1">
              {[25, 50, 75].map((marker) => (
                <div
                  key={marker}
                  className={`w-0.5 h-2 ${
                    progressPercentage >= marker ? 'bg-white/50' : 'bg-gray-600'
                  } rounded-full`}
                />
              ))}
            </div>
          </div>
        </div>

        {/* Next Rank Preview */}
        <motion.div
          className="mt-4 p-3 bg-gray-800/50 rounded-lg border border-gray-700/50"
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 bg-gradient-to-br from-purple-500 to-purple-600 rounded-lg flex items-center justify-center">
                <Crown className="w-4 h-4 text-white" />
              </div>
              <div>
                <p className="text-sm font-semibold text-gray-300">Próximo Rango</p>
                <p className="text-xs text-gray-400">
                  {currentRank === 'S+' ? 'Máximo alcanzado' : `Rango ${
                    currentRank === 'S' ? 'S+' :
                    currentRank === 'A+' ? 'S' :
                    currentRank === 'A' ? 'A+' :
                    currentRank === 'B+' ? 'A' :
                    currentRank === 'B' ? 'B+' :
                    currentRank === 'C+' ? 'B' :
                    currentRank === 'C' ? 'C+' :
                    'C'
                  }`}
                </p>
              </div>
            </div>
            
            <div className="text-right">
              <p className="text-sm font-bold text-purple-400">
                {Math.ceil((100 - progressPercentage) / 10)} batallas
              </p>
              <p className="text-xs text-gray-500">estimadas</p>
            </div>
          </div>
        </motion.div>

        {/* Achievements Hints */}
        <div className="mt-4 flex gap-2 overflow-x-auto scrollbar-hide">
          {[
            { name: 'Perfeccionista', description: '100% precisión en 5 batallas', progress: 60 },
            { name: 'Velocista', description: 'Responder en <30s promedio', progress: 80 },
            { name: 'Consistente', description: '10 días de racha', progress: 70 },
          ].map((achievement, index) => (
            <motion.div
              key={achievement.name}
              className="min-w-[200px] p-3 bg-gray-800/30 rounded-lg border border-gray-700/30"
              whileHover={{ scale: 1.02 }}
              transition={{ duration: 0.2 }}
            >
              <div className="flex items-center gap-2 mb-2">
                <div className="w-6 h-6 bg-yellow-500/20 rounded-full flex items-center justify-center">
                  <Star className="w-3 h-3 text-yellow-400" />
                </div>
                <span className="text-xs font-semibold text-gray-300">{achievement.name}</span>
              </div>
              <p className="text-xs text-gray-400 mb-2">{achievement.description}</p>
              <div className="w-full h-1 bg-gray-800 rounded-full">
                <div 
                  className="h-1 bg-yellow-500 rounded-full transition-all duration-500"
                  style={{ width: `${achievement.progress}%` }}
                />
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </motion.div>
  );
}