'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { CheckCircle, Lock, Play, Target } from 'lucide-react';

interface Phase {
  id: string;
  name: string;
  description: string;
  units: Array<{
    id: string;
    name: string;
    description: string;
    isCompleted: boolean;
    isActive: boolean;
  }>;
}

interface LearningPathVisualizerProps {
  phases: Phase[];
  currentPhase: number;
  currentUnit: number;
  className?: string;
}

function UnitMiniCard({ 
  unit, 
  isActive, 
  isCompleted 
}: { 
  unit: any; 
  isActive: boolean; 
  isCompleted: boolean;
}) {
  return (
    <motion.div
      className={`
        p-3 rounded-lg border-2 transition-all duration-300
        ${isActive 
          ? 'border-teal-500 bg-teal-50 dark:bg-teal-900/20' 
          : isCompleted 
            ? 'border-green-500 bg-green-50 dark:bg-green-900/20'
            : 'border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-800'
        }
      `}
      whileHover={{ scale: 1.02 }}
    >
      <div className="flex items-center gap-2 mb-2">
        {isCompleted ? (
          <CheckCircle className="w-4 h-4 text-green-500" />
        ) : isActive ? (
          <Play className="w-4 h-4 text-teal-500" />
        ) : (
          <Lock className="w-4 h-4 text-gray-400" />
        )}
        <h4 className={`text-sm font-medium ${
          isActive ? 'text-teal-700 dark:text-teal-300' :
          isCompleted ? 'text-green-700 dark:text-green-300' :
          'text-gray-600 dark:text-gray-400'
        }`}>
          {unit.name}
        </h4>
      </div>
      <p className="text-xs text-gray-500 dark:text-gray-400">
        {unit.description}
      </p>
    </motion.div>
  );
}

export function LearningPathVisualizer({ 
  phases, 
  currentPhase, 
  currentUnit, 
  className = '' 
}: LearningPathVisualizerProps) {
  return (
    <div className={`relative py-12 ${className}`}>
      {/* Path Line */}
      <div className="absolute left-1/2 top-0 bottom-0 w-1 
                      bg-gradient-to-b from-teal-500 via-blue-500 to-purple-500 
                      transform -translate-x-1/2" />

      {/* Phases */}
      {phases.map((phase, phaseIndex) => (
        <motion.div
          key={phase.id}
          initial={{ opacity: 0, x: phaseIndex % 2 === 0 ? -50 : 50 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: phaseIndex * 0.2 }}
          className={`relative mb-16 ${phaseIndex % 2 === 0 ? 'pr-1/2' : 'pl-1/2 ml-auto'}`}
        >
          {/* Phase Marker */}
          <div className={`
            absolute left-1/2 top-8 w-12 h-12 rounded-full
            transform -translate-x-1/2 -translate-y-1/2
            ${phaseIndex <= currentPhase 
              ? 'bg-gradient-to-br from-teal-500 to-blue-500' 
              : 'bg-gray-400'
            }
            flex items-center justify-center text-white font-bold
            ${phaseIndex === currentPhase && 'ring-4 ring-teal-300 ring-opacity-50'}
          `}>
            {phaseIndex + 1}
          </div>

          {/* Phase Card */}
          <div className={`
            bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6
            ${phaseIndex % 2 === 0 ? 'mr-8' : 'ml-8'}
            ${phaseIndex === currentPhase && 'ring-2 ring-teal-500'}
          `}>
            <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-2">
              {phase.name}
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
              {phase.description}
            </p>

            {/* Units Preview */}
            <div className="space-y-2">
              {phase.units.map((unit, unitIndex) => (
                <UnitMiniCard
                  key={unit.id}
                  unit={unit}
                  isActive={phaseIndex === currentPhase && unitIndex === currentUnit}
                  isCompleted={phaseIndex < currentPhase || 
                              (phaseIndex === currentPhase && unitIndex < currentUnit)}
                />
              ))}
            </div>
          </div>
        </motion.div>
      ))}

      {/* Progress Indicator */}
      <div className="absolute bottom-0 left-1/2 transform -translate-x-1/2">
        <div className="flex items-center gap-2 bg-white dark:bg-gray-800 rounded-full px-4 py-2 shadow-lg">
          <Target className="w-4 h-4 text-teal-500" />
          <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
            Fase {currentPhase + 1} de {phases.length}
          </span>
        </div>
      </div>
    </div>
  );
}
