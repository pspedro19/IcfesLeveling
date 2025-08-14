'use client';

import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useRouter } from 'next/navigation';
import { useMediaQuery } from '@/hooks/useMediaQuery';
import { useAuthStore } from '@/stores/useAuthStore';
import { useQuestStore } from '@/stores/useQuestStore';
import { useAudio } from './PortalLogin/AudioEngine';
import { 
  Brain, 
  BookOpen, 
  Beaker, 
  Globe, 
  Languages,
  Lock,
  CheckCircle,
  Star,
  Sparkles
} from 'lucide-react';
import { Points } from '@react-three/drei';
import { PointsMaterial } from 'three';

interface Area {
  id: string;
  name: string;
  icon: React.ReactNode;
  color: string;
  glowColor: string;
  description: string;
  totalQuestions: number;
  requiredScore: number;
}

const ICFES_AREAS: Area[] = [
  {
    id: 'math',
    name: 'Matemáticas',
    icon: <Brain className="w-8 h-8" />,
    color: 'from-purple-500 to-purple-700',
    glowColor: 'purple',
    description: 'Conquista álgebra, geometría y cálculo en las mazmorras numéricas',
    totalQuestions: 50,
    requiredScore: 70
  },
  {
    id: 'reading',
    name: 'Lectura Crítica',
    icon: <BookOpen className="w-8 h-8" />,
    color: 'from-blue-500 to-blue-700',
    glowColor: 'blue',
    description: 'Domina la comprensión y análisis de textos antiguos',
    totalQuestions: 40,
    requiredScore: 70
  },
  {
    id: 'science',
    name: 'Ciencias',
    icon: <Beaker className="w-8 h-8" />,
    color: 'from-green-500 to-green-700',
    glowColor: 'green',
    description: 'Explora física, química y biología en laboratorios místicos',
    totalQuestions: 60,
    requiredScore: 70
  },
  {
    id: 'social',
    name: 'Sociales',
    icon: <Globe className="w-8 h-8" />,
    color: 'from-orange-500 to-orange-700',
    glowColor: 'orange',
    description: 'Conquista historia, geografía y competencias ciudadanas en reinos sociales',
    totalQuestions: 45,
    requiredScore: 70
  },
  {
    id: 'english',
    name: 'Inglés',
    icon: <Languages className="w-8 h-8" />,
    color: 'from-indigo-500 to-indigo-700',
    glowColor: 'indigo',
    description: 'Domina la comprensión lectora en el idioma de los antiguos sabios',
    totalQuestions: 35,
    requiredScore: 70
  }
];

interface AreaProgress {
  areaId: string;
  completed: boolean;
  score: number;
  completedQuestions: number;
  lastAttempt?: Date;
}

export default function OnboardingMap() {
  const router = useRouter();
  const { user } = useAuthStore();
  const { playSound } = useAudio();
  const isMobile = useMediaQuery('(max-width: 768px)');
  const isReducedMotion = useMediaQuery('(prefers-reduced-motion: reduce)');
  
  const [selectedArea, setSelectedArea] = useState<Area | null>(null);
  const [areaProgress, setAreaProgress] = useState<Record<string, AreaProgress>>({});
  const [isLoading, setIsLoading] = useState(false);
  const [showCompletionModal, setShowCompletionModal] = useState(false);
  const [orbsEarned, setOrbsEarned] = useState(0); // Añadido: Gamificación con orbs
  const [hunterRank, setHunterRank] = useState('E'); // Añadido: Gamificación con ranks
  
  const containerRef = useRef<HTMLDivElement>(null);
  const centerRef = useRef<{ x: number; y: number }>({ x: 0, y: 0 });

  // Load progress from localStorage
  useEffect(() => {
    const savedProgress = localStorage.getItem('onboarding_progress');
    if (savedProgress) {
      setAreaProgress(JSON.parse(savedProgress));
    }
    // Simular rank inicial
    setHunterRank('E');
  }, []);

  // Check if all areas completed
  const allAreasCompleted = ICFES_AREAS.every(
    area => areaProgress[area.id]?.completed
  );

  const calculatePosition = (index: number, total: number) => {
    const angle = (index * 2 * Math.PI) / total - Math.PI / 2;
    const radius = isMobile ? 120 : 200;
    
    return {
      x: Math.cos(angle) * radius,
      y: Math.sin(angle) * radius
    };
  };

  const handleAreaClick = (area: Area) => {
    const progress = areaProgress[area.id];
    
    if (!progress || !progress.completed) {
      playSound('typing_click');
      setSelectedArea(area);
      
      // Haptic feedback on mobile
      if (isMobile && 'vibrate' in navigator) {
        navigator.vibrate(50);
      }
    }
  };

  const startAreaTest = async () => {
    if (!selectedArea) return;
    
    playSound('portal_hum');
    setIsLoading(true);
    
    // Navigate to diagnostic test for this area
    setTimeout(() => {
      router.push(`/diagnostic-test?area=${selectedArea.id}`);
    }, 1000);
  };

  const getAreaStatus = (area: Area) => {
    const progress = areaProgress[area.id];
    if (!progress || !progress.completed) return 'locked';
    if (progress.completed) return 'completed';
    if (progress.completedQuestions > 0) return 'in-progress';
    return 'available';
  };

  const getProgressPercentage = (area: Area) => {
    const progress = areaProgress[area.id];
    if (!progress) return 0;
    return (progress.completedQuestions / area.totalQuestions) * 100;
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-black to-purple-900 flex items-center justify-center p-4">
      <div className="w-full max-w-6xl">
        {/* Header con lore */}
        <motion.div 
          className="text-center mb-12"
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <h1 className="text-4xl md:text-5xl font-bold text-gold-500 mb-4 font-cinzel">
            Portal Arcano de Evaluación ICFES
          </h1>
          <p className="text-xl text-purple-300 font-orbitron">
            Hunter Novato, conquista todas las mazmorras para desbloquear tu clase legendaria
          </p>
          <p className="text-sm text-gold-300 mt-2">Rango Actual: {hunterRank} | Orbs Ganados: {orbsEarned} 💎</p> {/* Gamificación */}
          
          {/* Overall Progress */}
          <div className="mt-6 max-w-md mx-auto">
            <div className="flex justify-between text-sm text-purple-300 mb-2">
              <span>Progreso Místico Total</span>
              <span>{Object.values(areaProgress).filter(p => p.completed).length} / {ICFES_AREAS.length}</span>
            </div>
            <div className="w-full bg-gray-800 rounded-full h-3">
              <motion.div
                className="h-full bg-gradient-to-r from-gold-500 to-gold-600 rounded-full"
                initial={{ width: 0 }}
                animate={{ 
                  width: `${(Object.values(areaProgress).filter(p => p.completed).length / ICFES_AREAS.length) * 100}%` 
                }}
                transition={{ duration: 1, ease: "easeOut" }}
              />
            </div>
          </div>
        </motion.div>

        {/* Radial Map */}
        <div 
          ref={containerRef}
          className="relative w-full h-[400px] md:h-[600px] flex items-center justify-center"
        >
          {/* Center Portal con partículas si completado */}
          <motion.div
            className="absolute w-32 h-32 md:w-48 md:h-48"
            animate={allAreasCompleted ? {
              scale: [1, 1.1, 1],
              rotate: 360
            } : {}}
            transition={{
              duration: 3,
              repeat: allAreasCompleted ? Infinity : 0,
              ease: "linear"
            }}
          >
            <div className={`w-full h-full rounded-full bg-gradient-to-r ${
              allAreasCompleted 
                ? 'from-gold-400 to-gold-600 shadow-[0_0_30px_rgba(255,215,0,0.5)]' 
                : 'from-gray-600 to-gray-800'
            } flex items-center justify-center`}>
              {allAreasCompleted ? (
                <Star className="w-16 h-16 md:w-24 md:h-24 text-white" />
              ) : (
                <Lock className="w-12 h-12 md:w-16 md:h-16 text-gray-400" />
              )}
            </div>
            {allAreasCompleted && !isReducedMotion && (
              <Points positions={new Float32Array(1000).map(() => Math.random() * 2 - 1)} scale={1.5}>
                <PointsMaterial color="#ffd700" size={0.02} transparent opacity={0.8} />
              </Points>
            )}
          </motion.div>

          {/* Area Nodes */}
          {ICFES_AREAS.map((area, index) => {
            const position = calculatePosition(index, ICFES_AREAS.length);
            const status = getAreaStatus(area);
            const progress = getProgressPercentage(area);
            
            return (
              <motion.div
                key={area.id}
                className="absolute"
                style={{
                  left: '50%',
                  top: '50%',
                  transform: `translate(-50%, -50%) translate(${position.x}px, ${position.y}px)`
                }}
                initial={{ opacity: 0, scale: 0 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: index * 0.1 }}
              >
                <motion.button
                  className={`relative w-24 h-24 md:w-32 md:h-32 rounded-full p-1 backdrop-blur-md ${
                    status === 'completed' ? 'cursor-default' : 'cursor-pointer'
                  }`}
                  whileHover={status !== 'completed' ? { scale: 1.1 } : {}}
                  whileTap={status !== 'completed' ? { scale: 0.95 } : {}}
                  onClick={() => handleAreaClick(area)}
                  disabled={status === 'completed'}
                >
                  {/* Progress Ring */}
                  <svg className="absolute inset-0 w-full h-full -rotate-90">
                    <circle
                      cx="50%"
                      cy="50%"
                      r="46%"
                      stroke="rgba(255,255,255,0.1)"
                      strokeWidth="4"
                      fill="none"
                    />
                    <circle
                      cx="50%"
                      cy="50%"
                      r="46%"
                      stroke={status === 'completed' ? '#ffd700' : '#8a2be2'}
                      strokeWidth="4"
                      fill="none"
                      strokeDasharray={`${progress * 2.9} 290`}
                      strokeLinecap="round"
                      className="transition-all duration-500"
                    />
                  </svg>

                  {/* Area Content */}
                  <div className={`relative w-full h-full rounded-full bg-gradient-to-br ${area.color} 
                    flex flex-col items-center justify-center text-white
                    ${status === 'completed' ? 'opacity-90' : ''}
                    shadow-lg shadow-${area.glowColor}-500/30`}
                    style={{
                      boxShadow: status === 'completed' 
                        ? `0 0 30px rgba(255,215,0,0.5)` 
                        : `0 0 20px var(--${area.glowColor}-500)`
                    }}
                  >
                    {status === 'completed' && (
                      <CheckCircle className="absolute -top-2 -right-2 w-8 h-8 text-gold-400 bg-black/50 rounded-full p-1" />
                    )}
                    {area.icon}
                    <span className="text-xs md:text-sm font-semibold mt-1">
                      {area.name}
                    </span>
                    {status === 'in-progress' && (
                      <span className="text-xs opacity-75">
                        {Math.round(progress)}%
                      </span>
                    )}
                  </div>

                  {/* Glow Effect */}
                  {!isReducedMotion && status !== 'completed' && (
                    <motion.div
                      className="absolute inset-0 rounded-full"
                      animate={{
                        boxShadow: [
                          `0 0 20px var(--${area.glowColor}-500)`,
                          `0 0 40px var(--${area.glowColor}-500)`,
                          `0 0 20px var(--${area.glowColor}-500)`
                        ]
                      }}
                      transition={{ duration: 2, repeat: Infinity }}
                    />
                  )}
                </motion.button>

                {/* Area Label */}
                <motion.div
                  className="absolute top-full mt-2 left-1/2 transform -translate-x-1/2 text-center"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: index * 0.1 + 0.3 }}
                >
                  <p className="text-xs md:text-sm text-purple-300 whitespace-nowrap">
                    {area.description}
                  </p>
                </motion.div>
              </motion.div>
            );
          })}

          {/* Connection Lines */}
          {!isMobile && ICFES_AREAS.map((area, index) => {
            const nextIndex = (index + 1) % ICFES_AREAS.length;
            const start = calculatePosition(index, ICFES_AREAS.length);
            const end = calculatePosition(nextIndex, ICFES_AREAS.length);
            
            return (
              <motion.svg
                key={`line-${index}`}
                className="absolute inset-0 w-full h-full pointer-events-none"
                initial={{ opacity: 0 }}
                animate={{ opacity: 0.2 }}
                transition={{ delay: 0.5 }}
              >
                <line
                  x1={`${50 + (start.x / 4)}%`}
                  y1={`${50 + (start.y / 4)}%`}
                  x2={`${50 + (end.x / 4)}%`}
                  y2={`${50 + (end.y / 4)}%`}
                  stroke="white"
                  strokeWidth="1"
                  strokeDasharray="5,5"
                />
              </motion.svg>
            );
          })}
        </div>

        {/* Unlock Message */}
        {allAreasCompleted && (
          <motion.div
            className="text-center mt-8"
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.5 }}
          >
            <button
              onClick={() => {
                playSound('level_up');
                router.push('/role-selection');
              }}
              className="bg-gradient-to-r from-gold-400 to-gold-600 text-black font-bold px-8 py-4 rounded-lg text-lg hover:shadow-[0_0_20px_rgba(255,215,0,0.5)] transition-all shadow-[0_0_10px_#ffd700]"
            >
              <Sparkles className="inline-block mr-2" />
              ¡Desbloquear Clase Legendaria de Hunter!
            </button>
          </motion.div>
        )}
      </div>

      {/* Area Selection Modal con glass y glow */}
      <AnimatePresence>
        {selectedArea && (
          <motion.div
            className="fixed inset-0 bg-black/80 flex items-center justify-center p-4 z-50"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setSelectedArea(null)}
          >
            <motion.div
              className="bg-black/50 backdrop-blur-md rounded-lg p-6 max-w-md w-full border-purple-500 shadow-[0_0_10px_#8a2be2]"
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.8, opacity: 0 }}
              onClick={(e) => e.stopPropagation()}
            >
              <div className={`w-20 h-20 mx-auto mb-4 rounded-full bg-gradient-to-br ${selectedArea.color} 
                flex items-center justify-center text-white`}>
                {selectedArea.icon}
              </div>
              
              <h3 className="text-2xl font-bold text-gold-500 text-center mb-2 font-cinzel">
                {selectedArea.name}
              </h3>
              
              <p className="text-purple-300 text-center mb-6">
                {selectedArea.description}
              </p>
              
              <div className="space-y-2 mb-6 text-purple-300">
                <div className="flex justify-between text-sm">
                  <span>Enigmas Arcana:</span>
                  <span>{selectedArea.totalQuestions}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span>Gloria Requerida:</span>
                  <span>{selectedArea.requiredScore}%</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span>Progreso Actual:</span>
                  <span>{Math.round(getProgressPercentage(selectedArea))}%</span>
                </div>
              </div>
              
              <div className="flex gap-3">
                <button
                  onClick={() => setSelectedArea(null)}
                  className="flex-1 bg-gray-700 hover:bg-gray-600 text-white font-semibold py-3 px-4 rounded-lg transition-colors shadow-[0_0_5px_#8a2be2]"
                >
                  Cancelar Invocación
                </button>
                <button
                  onClick={startAreaTest}
                  disabled={isLoading}
                  className="flex-1 bg-gradient-to-r from-purple-600 to-purple-700 hover:from-purple-700 hover:to-purple-800 
                    text-white font-semibold py-3 px-4 rounded-lg transition-all disabled:opacity-50 shadow-[0_0_5px_#ffd700]"
                >
                  {isLoading ? (
                    <span className="flex items-center justify-center">
                      <motion.div
                        className="w-5 h-5 border-2 border-white border-t-transparent rounded-full"
                        animate={{ rotate: 360 }}
                        transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                      />
                    </span>
                  ) : (
                    'Iniciar Prueba Arcana'
                  )}
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}