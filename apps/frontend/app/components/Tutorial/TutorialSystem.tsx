'use client';

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  ChevronRight, 
  ChevronLeft,
  X,
  CheckCircle,
  Info,
  Target,
  Sparkles,
  Book,
  Sword,
  Users,
  Trophy,
  Settings,
  HelpCircle
} from 'lucide-react';
import { useAudio } from '../PortalLogin/AudioEngine';
import { trackGameEvent } from '@/lib/analytics';

interface TutorialStep {
  id: string;
  title: string;
  content: string;
  target?: string; // CSS selector for element to highlight
  position?: 'top' | 'bottom' | 'left' | 'right';
  icon?: React.ReactNode;
  action?: () => void;
  requiresAction?: boolean;
}

interface TutorialSystemProps {
  steps: TutorialStep[];
  onComplete?: () => void;
  onSkip?: () => void;
  storageKey?: string;
}

const DEFAULT_STEPS: TutorialStep[] = [
  {
    id: 'welcome',
    title: '¡Bienvenido a ICFES Leveling!',
    content: 'Prepárate para convertirte en el Hunter del Conocimiento más poderoso. Te guiaré en tu primera aventura.',
    icon: <Sparkles className="w-8 h-8" />,
  },
  {
    id: 'character',
    title: 'Tu Personaje',
    content: 'Aquí puedes ver tu nivel, experiencia y estadísticas. Cada batalla ganada te hace más fuerte.',
    target: '.character-stats',
    position: 'bottom',
    icon: <Target className="w-8 h-8" />
  },
  {
    id: 'battles',
    title: 'Sistema de Batallas',
    content: 'Enfréntate a enemigos respondiendo preguntas. Mientras más rápido respondas, más daño harás.',
    target: '.battle-button',
    position: 'right',
    icon: <Sword className="w-8 h-8" />
  },
  {
    id: 'quests',
    title: 'Misiones Diarias',
    content: 'Completa misiones diarias para ganar recompensas extra y mantener tu racha.',
    target: '.quest-tracker',
    position: 'left',
    icon: <Book className="w-8 h-8" />
  },
  {
    id: 'guilds',
    title: 'Sistema de Gremios',
    content: 'Únete a un gremio para participar en raids cooperativos y competir con otros equipos.',
    target: '.guild-button',
    position: 'top',
    icon: <Users className="w-8 h-8" />
  },
  {
    id: 'leaderboard',
    title: 'Tabla de Líderes',
    content: 'Compite por el primer lugar en los rankings globales. ¡Demuestra que eres el mejor!',
    target: '.leaderboard-button',
    position: 'bottom',
    icon: <Trophy className="w-8 h-8" />
  },
  {
    id: 'settings',
    title: 'Configuración',
    content: 'Personaliza tu experiencia con modos de juego, temas y opciones de accesibilidad.',
    target: '.settings-button',
    position: 'left',
    icon: <Settings className="w-8 h-8" />
  },
  {
    id: 'ready',
    title: '¡Estás Listo!',
    content: 'Has completado el tutorial. Es hora de comenzar tu aventura. ¡Que la suerte esté de tu lado, Hunter!',
    icon: <CheckCircle className="w-8 h-8" />
  }
];

export default function TutorialSystem({ 
  steps = DEFAULT_STEPS,
  onComplete,
  onSkip,
  storageKey = 'tutorial-completed'
}: TutorialSystemProps) {
  const { playSound } = useAudio();
  const [currentStep, setCurrentStep] = useState(0);
  const [isVisible, setIsVisible] = useState(false);
  const [highlightedElement, setHighlightedElement] = useState<HTMLElement | null>(null);
  
  // Check if tutorial was already completed
  useEffect(() => {
    const completed = localStorage.getItem(storageKey);
    if (!completed) {
      setIsVisible(true);
      trackGameEvent('tutorial_started');
    }
  }, [storageKey]);
  
  // Update highlighted element when step changes
  useEffect(() => {
    if (!isVisible) return;
    
    const step = steps[currentStep];
    if (step.target) {
      const element = document.querySelector(step.target) as HTMLElement;
      if (element) {
        setHighlightedElement(element);
        element.scrollIntoView({ behavior: 'smooth', block: 'center' });
        
        // Add highlight class
        element.classList.add('tutorial-highlight');
        
        return () => {
          element.classList.remove('tutorial-highlight');
        };
      }
    } else {
      setHighlightedElement(null);
    }
  }, [currentStep, steps, isVisible]);
  
  const handleNext = () => {
    playSound('typing_click');
    
    if (currentStep < steps.length - 1) {
      setCurrentStep(currentStep + 1);
      trackGameEvent('tutorial_step_completed', { 
        stepId: steps[currentStep].id,
        stepIndex: currentStep 
      });
    } else {
      handleComplete();
    }
  };
  
  const handlePrevious = () => {
    playSound('typing_click');
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };
  
  const handleSkip = () => {
    playSound('notification_epic');
    trackGameEvent('tutorial_skipped', { 
      skippedAtStep: steps[currentStep].id 
    });
    
    setIsVisible(false);
    localStorage.setItem(storageKey, 'skipped');
    onSkip?.();
  };
  
  const handleComplete = () => {
    playSound('level_up');
    trackGameEvent('tutorial_completed');
    
    setIsVisible(false);
    localStorage.setItem(storageKey, 'completed');
    onComplete?.();
  };
  
  const getTooltipPosition = (element: HTMLElement, position?: string) => {
    const rect = element.getBoundingClientRect();
    const tooltipWidth = 400;
    const tooltipHeight = 200;
    const padding = 20;
    
    switch (position) {
      case 'top':
        return {
          top: rect.top - tooltipHeight - padding,
          left: rect.left + rect.width / 2 - tooltipWidth / 2
        };
      case 'bottom':
        return {
          top: rect.bottom + padding,
          left: rect.left + rect.width / 2 - tooltipWidth / 2
        };
      case 'left':
        return {
          top: rect.top + rect.height / 2 - tooltipHeight / 2,
          left: rect.left - tooltipWidth - padding
        };
      case 'right':
        return {
          top: rect.top + rect.height / 2 - tooltipHeight / 2,
          left: rect.right + padding
        };
      default:
        return {
          top: window.innerHeight / 2 - tooltipHeight / 2,
          left: window.innerWidth / 2 - tooltipWidth / 2
        };
    }
  };
  
  if (!isVisible) return null;
  
  const step = steps[currentStep];
  const progress = ((currentStep + 1) / steps.length) * 100;
  const tooltipPosition = highlightedElement 
    ? getTooltipPosition(highlightedElement, step.position)
    : { top: window.innerHeight / 2 - 150, left: window.innerWidth / 2 - 200 };
  
  return (
    <AnimatePresence>
      {isVisible && (
        <>
          {/* Overlay */}
          <motion.div
            className="fixed inset-0 bg-black/80 z-[9998]"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={handleSkip}
          />
          
          {/* Highlight Box */}
          {highlightedElement && (
            <motion.div
              className="fixed border-4 border-purple-500 rounded-lg z-[9999] pointer-events-none"
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ 
                opacity: 1, 
                scale: 1,
                boxShadow: '0 0 40px rgba(168, 85, 247, 0.8)'
              }}
              style={{
                top: highlightedElement.getBoundingClientRect().top - 8,
                left: highlightedElement.getBoundingClientRect().left - 8,
                width: highlightedElement.getBoundingClientRect().width + 16,
                height: highlightedElement.getBoundingClientRect().height + 16,
              }}
            />
          )}
          
          {/* Tutorial Tooltip */}
          <motion.div
            className="fixed bg-gray-900 rounded-lg shadow-2xl z-[10000] w-[400px]"
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.9 }}
            style={{
              top: `${tooltipPosition.top}px`,
              left: `${tooltipPosition.left}px`,
              maxWidth: '90vw'
            }}
            onClick={e => e.stopPropagation()}
          >
            {/* Progress Bar */}
            <div className="h-2 bg-gray-800 rounded-t-lg overflow-hidden">
              <motion.div
                className="h-full bg-gradient-to-r from-purple-500 to-purple-600"
                initial={{ width: 0 }}
                animate={{ width: `${progress}%` }}
                transition={{ duration: 0.3 }}
              />
            </div>
            
            {/* Content */}
            <div className="p-6">
              {/* Header */}
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center gap-3">
                  {step.icon && (
                    <div className="text-purple-400">
                      {step.icon}
                    </div>
                  )}
                  <div>
                    <h3 className="text-xl font-bold text-white">
                      {step.title}
                    </h3>
                    <p className="text-sm text-gray-400">
                      Paso {currentStep + 1} de {steps.length}
                    </p>
                  </div>
                </div>
                
                <button
                  onClick={handleSkip}
                  className="text-gray-400 hover:text-white transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
              
              {/* Description */}
              <p className="text-gray-300 mb-6">
                {step.content}
              </p>
              
              {/* Navigation */}
              <div className="flex items-center justify-between">
                <button
                  onClick={handlePrevious}
                  disabled={currentStep === 0}
                  className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-all
                    ${currentStep === 0 
                      ? 'bg-gray-800 text-gray-500 cursor-not-allowed'
                      : 'bg-gray-700 hover:bg-gray-600 text-white'
                    }`}
                >
                  <ChevronLeft className="w-4 h-4" />
                  Anterior
                </button>
                
                <div className="flex gap-2">
                  {steps.map((_, index) => (
                    <div
                      key={index}
                      className={`w-2 h-2 rounded-full transition-all ${
                        index === currentStep 
                          ? 'bg-purple-500 w-6' 
                          : index < currentStep
                          ? 'bg-purple-400'
                          : 'bg-gray-600'
                      }`}
                    />
                  ))}
                </div>
                
                <button
                  onClick={handleNext}
                  className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r 
                    from-purple-600 to-purple-700 hover:from-purple-700 hover:to-purple-800 
                    text-white rounded-lg transition-all transform hover:scale-105"
                >
                  {currentStep === steps.length - 1 ? 'Finalizar' : 'Siguiente'}
                  <ChevronRight className="w-4 h-4" />
                </button>
              </div>
              
              {/* Skip Option */}
              <button
                onClick={handleSkip}
                className="w-full text-center text-sm text-gray-500 hover:text-gray-400 
                  transition-colors mt-4"
              >
                Omitir tutorial
              </button>
            </div>
          </motion.div>
          
          {/* Help Button */}
          <motion.button
            className="fixed bottom-8 right-8 bg-purple-600 hover:bg-purple-700 
              text-white rounded-full p-4 shadow-lg z-[10001] transition-all
              transform hover:scale-110"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 20 }}
            onClick={() => setCurrentStep(0)}
            title="Reiniciar tutorial"
          >
            <HelpCircle className="w-6 h-6" />
          </motion.button>
        </>
      )}
    </AnimatePresence>
  );
}