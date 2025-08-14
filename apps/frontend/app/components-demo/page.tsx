'use client';

import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { 
  ThemeToggle, 
  CircularProgress, 
  PriorityBadge, 
  UnitCard,
  ProgressDashboard,
  LearningPathVisualizer,
  CelebrationModal,
  AITutorAssistant,
  MobileNavigation
} from '../components';
import { 
  UnitCardSkeleton, 
  ProgressDashboardSkeleton, 
  LearningPathSkeleton 
} from '../components/SkeletonLoader';

// Mock data for demonstration
const mockUnit = {
  id: '1',
  number: 1,
  title: 'Fundamentos de Álgebra',
  description: 'Aprende los conceptos básicos del álgebra y las ecuaciones lineales',
  priority: 'high' as const,
  isUnlocked: true,
  progress: 75,
  videoCount: 8,
  estimatedHours: 3,
  xpReward: 150,
  aiRecommended: true,
  videos: [
    { id: '1', title: 'Introducción al Álgebra', duration: '15:30', youtube_id: 'abc123', watched: true },
    { id: '2', title: 'Ecuaciones Lineales', duration: '22:15', youtube_id: 'def456', watched: false }
  ],
  objectives: [
    { id: '1', description: 'Entender variables y constantes', completed: true },
    { id: '2', description: 'Resolver ecuaciones simples', completed: false }
  ],
  aiTips: [
    { id: '1', tip: 'Recuerda que una ecuación es como una balanza en equilibrio', category: 'strategy' as const },
    { id: '2', tip: '¡No te rindas! Cada error te acerca más a la solución', category: 'motivation' as const }
  ]
};

const mockUserData = {
  overallProgress: 68,
  rank: 'B',
  nextRank: 'A',
  xpToNextRank: 320,
  currentStreak: 7,
  streakData: {
    '2024-01-15': true,
    '2024-01-16': true,
    '2024-01-17': true,
    '2024-01-18': false,
    '2024-01-19': true,
    '2024-01-20': true,
    '2024-01-21': true
  },
  orbs: 45,
  recentAchievements: [
    { id: '1', name: 'Primer Paso', description: 'Completaste tu primera unidad', icon: '🎯', rarity: 'common' as const },
    { id: '2', name: 'Racha de 7 días', description: 'Estudiaste 7 días seguidos', icon: '🔥', rarity: 'rare' as const }
  ]
};

const mockPhases = [
  {
    id: '1',
    name: 'Fundamentos',
    description: 'Conceptos básicos y teoría fundamental',
    units: [
      { id: '1', name: 'Introducción', description: 'Primeros conceptos', isCompleted: true, isActive: false },
      { id: '2', name: 'Variables', description: 'Trabajo con variables', isCompleted: true, isActive: false },
      { id: '3', name: 'Ecuaciones', description: 'Resolución básica', isCompleted: false, isActive: true }
    ]
  },
  {
    id: '2',
    name: 'Intermedio',
    description: 'Aplicaciones prácticas y problemas',
    units: [
      { id: '4', name: 'Problemas', description: 'Aplicaciones reales', isCompleted: false, isActive: false },
      { id: '5', name: 'Sistemas', description: 'Ecuaciones múltiples', isCompleted: false, isActive: false }
    ]
  }
];

export default function ComponentsDemoPage() {
  const [currentPage, setCurrentPage] = useState('home');
  const [isAIAssistantOpen, setIsAIAssistantOpen] = useState(false);
  const [showCelebration, setShowCelebration] = useState(false);
  const [showSkeletons, setShowSkeletons] = useState(false);

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <header className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
              🎨 Demo de Componentes Frontend
            </h1>
            <ThemeToggle />
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="space-y-12">
          
          {/* Theme Toggle Section */}
          <section>
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
              🌓 Cambio de Tema
            </h2>
            <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
              <ThemeToggle />
            </div>
          </section>

          {/* Priority Badges Section */}
          <section>
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
              🏷️ Badges de Prioridad
            </h2>
            <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
              <div className="flex gap-4 flex-wrap">
                <PriorityBadge priority="critical" />
                <PriorityBadge priority="high" />
                <PriorityBadge priority="medium" />
                <PriorityBadge priority="low" />
              </div>
            </div>
          </section>

          {/* Circular Progress Section */}
          <section>
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
              🔄 Progreso Circular
            </h2>
            <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
              <div className="flex gap-8 justify-center">
                <CircularProgress value={25} size={100} />
                <CircularProgress value={50} size={100} />
                <CircularProgress value={75} size={100} />
                <CircularProgress value={100} size={100} />
              </div>
            </div>
          </section>

          {/* Unit Card Section */}
          <section>
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
              📚 Tarjeta de Unidad
            </h2>
            <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
              <UnitCard unit={mockUnit} />
            </div>
          </section>

          {/* Progress Dashboard Section */}
          <section>
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
              📊 Dashboard de Progreso
            </h2>
            <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
              <ProgressDashboard userData={mockUserData} />
            </div>
          </section>

          {/* Learning Path Section */}
          <section>
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
              🗺️ Camino de Aprendizaje
            </h2>
            <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
              <LearningPathVisualizer 
                phases={mockPhases} 
                currentPhase={0} 
                currentUnit={2} 
              />
            </div>
          </section>

          {/* Celebration Modal Section */}
          <section>
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
              🎉 Modal de Celebración
            </h2>
            <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
              <div className="flex gap-4">
                <button
                  onClick={() => setShowCelebration(true)}
                  className="px-4 py-2 bg-teal-500 text-white rounded-lg hover:bg-teal-600"
                >
                  Mostrar Celebración
                </button>
              </div>
            </div>
          </section>

          {/* Skeleton Loaders Section */}
          <section>
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
              💀 Cargadores de Esqueleto
            </h2>
            <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
              <div className="flex gap-4 mb-4">
                <button
                  onClick={() => setShowSkeletons(!showSkeletons)}
                  className="px-4 py-2 bg-purple-500 text-white rounded-lg hover:bg-purple-600"
                >
                  {showSkeletons ? 'Ocultar' : 'Mostrar'} Esqueletos
                </button>
              </div>
              
              {showSkeletons && (
                <div className="space-y-6">
                  <h3 className="text-lg font-medium">Tarjeta de Unidad</h3>
                  <UnitCardSkeleton />
                  
                  <h3 className="text-lg font-medium">Dashboard de Progreso</h3>
                  <ProgressDashboardSkeleton />
                  
                  <h3 className="text-lg font-medium">Camino de Aprendizaje</h3>
                  <LearningPathSkeleton />
                </div>
              )}
            </div>
          </section>

          {/* Mobile Navigation Section */}
          <section>
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
              📱 Navegación Móvil
            </h2>
            <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
              <div className="relative h-20 bg-gray-100 dark:bg-gray-700 rounded-lg">
                <MobileNavigation
                  currentPage={currentPage}
                  onPageChange={setCurrentPage}
                  notifications={{
                    learn: 3,
                    progress: 1,
                    challenges: 0,
                    profile: 2
                  }}
                />
              </div>
            </div>
          </section>
        </div>
      </main>

      {/* AI Tutor Assistant */}
      <AITutorAssistant
        isExpanded={isAIAssistantOpen}
        onToggle={() => setIsAIAssistantOpen(!isAIAssistantOpen)}
      />

      {/* Celebration Modal */}
      <CelebrationModal
        type="unit_complete"
        data={{
          title: '¡Unidad Completada!',
          message: 'Has completado exitosamente la unidad de Fundamentos de Álgebra. ¡Excelente trabajo!',
          xp: 150,
          orbs: 25,
          celebrationLevel: 4
        }}
        isOpen={showCelebration}
        onClose={() => setShowCelebration(false)}
      />
    </div>
  );
}
