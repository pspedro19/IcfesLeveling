'use client';

import { useState, useEffect, useCallback, useMemo } from 'react';
import confetti from 'canvas-confetti';

// ===== TIPOS E INTERFACES =====
interface UXTheme {
  style: 'khan' | 'coursera' | 'hybrid';
  colorScheme: 'light' | 'dark' | 'auto';
  reducedMotion: boolean;
  highContrast: boolean;
}

interface AnimationConfig {
  duration: 'fast' | 'base' | 'slow';
  easing: 'smooth' | 'bounce' | 'linear';
  enableParticles: boolean;
  enableSounds: boolean;
}

interface GameficationState {
  xp: number;
  rank: 'E' | 'D' | 'C' | 'B' | 'A' | 'S';
  achievements: string[];
  currentStreak: number;
  totalStudyTime: number;
}

interface ProgressMetrics {
  overallProgress: number;
  completedUnits: number;
  totalUnits: number;
  averageScore: number;
  weakTopics: string[];
  strongTopics: string[];
}

// ===== HOOK PRINCIPAL =====
export const useHybridUX = (userId?: string) => {
  // Estados del sistema UX
  const [theme, setTheme] = useState<UXTheme>({
    style: 'hybrid',
    colorScheme: 'dark',
    reducedMotion: false,
    highContrast: false
  });

  const [animationConfig, setAnimationConfig] = useState<AnimationConfig>({
    duration: 'base',
    easing: 'smooth',
    enableParticles: true,
    enableSounds: true
  });

  const [gamification, setGamification] = useState<GameficationState>({
    xp: 0,
    rank: 'E',
    achievements: [],
    currentStreak: 0,
    totalStudyTime: 0
  });

  const [progress, setProgress] = useState<ProgressMetrics>({
    overallProgress: 0,
    completedUnits: 0,
    totalUnits: 0,
    averageScore: 0,
    weakTopics: [],
    strongTopics: []
  });

  // ===== DETECCIÓN DE PREFERENCIAS DEL SISTEMA =====
  useEffect(() => {
    // Detectar preferencias de accesibilidad
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    const contrastQuery = window.matchMedia('(prefers-contrast: high)');
    const colorSchemeQuery = window.matchMedia('(prefers-color-scheme: dark)');

    setTheme(prev => ({
      ...prev,
      reducedMotion: mediaQuery.matches,
      highContrast: contrastQuery.matches,
      colorScheme: colorSchemeQuery.matches ? 'dark' : 'light'
    }));

    // Listeners para cambios en preferencias
    const handleMotionChange = (e: MediaQueryListEvent) => {
      setTheme(prev => ({ ...prev, reducedMotion: e.matches }));
      setAnimationConfig(prev => ({ 
        ...prev, 
        duration: e.matches ? 'fast' : 'base',
        enableParticles: !e.matches 
      }));
    };

    const handleContrastChange = (e: MediaQueryListEvent) => {
      setTheme(prev => ({ ...prev, highContrast: e.matches }));
    };

    const handleColorSchemeChange = (e: MediaQueryListEvent) => {
      setTheme(prev => ({ 
        ...prev, 
        colorScheme: e.matches ? 'dark' : 'light' 
      }));
    };

    mediaQuery.addEventListener('change', handleMotionChange);
    contrastQuery.addEventListener('change', handleContrastChange);
    colorSchemeQuery.addEventListener('change', handleColorSchemeChange);

    return () => {
      mediaQuery.removeEventListener('change', handleMotionChange);
      contrastQuery.removeEventListener('change', handleContrastChange);
      colorSchemeQuery.removeEventListener('change', handleColorSchemeChange);
    };
  }, []);

  // ===== CARGA DE DATOS PERSISTENTES =====
  useEffect(() => {
    if (typeof window !== 'undefined' && userId) {
      // Cargar configuraciones guardadas
      const savedTheme = localStorage.getItem(`ux-theme-${userId}`);
      const savedAnimations = localStorage.getItem(`ux-animations-${userId}`);
      const savedGamification = localStorage.getItem(`ux-gamification-${userId}`);

      if (savedTheme) {
        try {
          setTheme(JSON.parse(savedTheme));
        } catch (e) {
          console.warn('Error loading saved theme:', e);
        }
      }

      if (savedAnimations) {
        try {
          setAnimationConfig(JSON.parse(savedAnimations));
        } catch (e) {
          console.warn('Error loading saved animations:', e);
        }
      }

      if (savedGamification) {
        try {
          setGamification(JSON.parse(savedGamification));
        } catch (e) {
          console.warn('Error loading saved gamification:', e);
        }
      }
    }
  }, [userId]);

  // ===== FUNCIONES DE CONFIGURACIÓN =====
  const updateTheme = useCallback((newTheme: Partial<UXTheme>) => {
    setTheme(prev => {
      const updated = { ...prev, ...newTheme };
      if (typeof window !== 'undefined' && userId) {
        localStorage.setItem(`ux-theme-${userId}`, JSON.stringify(updated));
      }
      return updated;
    });
  }, [userId]);

  const updateAnimationConfig = useCallback((config: Partial<AnimationConfig>) => {
    setAnimationConfig(prev => {
      const updated = { ...prev, ...config };
      if (typeof window !== 'undefined' && userId) {
        localStorage.setItem(`ux-animations-${userId}`, JSON.stringify(updated));
      }
      return updated;
    });
  }, [userId]);

  // ===== FUNCIONES DE GAMIFICACIÓN =====
  const awardXP = useCallback((amount: number, reason?: string) => {
    setGamification(prev => {
      const newXP = prev.xp + amount;
      const newRank = calculateRank(newXP);
      const rankChanged = newRank !== prev.rank;

      const updated = {
        ...prev,
        xp: newXP,
        rank: newRank
      };

      // Efectos visuales
      if (animationConfig.enableParticles && !theme.reducedMotion) {
        // Confetti para XP
        confetti({
          particleCount: Math.min(amount / 10, 50),
          spread: 60,
          origin: { y: 0.8 },
          colors: ['#FCD34D', '#F59E0B', '#D97706']
        });

        // Confetti especial para rank up
        if (rankChanged) {
          setTimeout(() => {
            confetti({
              particleCount: 100,
              spread: 120,
              origin: { y: 0.6 },
              colors: ['#8B5CF6', '#DB2777', '#DC2626']
            });
          }, 500);
        }
      }

      // Persistir datos
      if (typeof window !== 'undefined' && userId) {
        localStorage.setItem(`ux-gamification-${userId}`, JSON.stringify(updated));
      }

      return updated;
    });

    // Notification personalizada
    if (typeof window !== 'undefined') {
      const notification = document.createElement('div');
      notification.className = 'fixed top-4 right-4 z-50 bg-gradient-to-r from-yellow-400 to-orange-500 text-white px-6 py-3 rounded-lg shadow-lg animate-achievement';
      notification.innerHTML = `
        <div class="flex items-center gap-2">
          <span class="text-lg">⚡</span>
          <div>
            <p class="font-bold">+${amount} XP</p>
            ${reason ? `<p class="text-sm opacity-90">${reason}</p>` : ''}
          </div>
        </div>
      `;
      
      document.body.appendChild(notification);
      
      setTimeout(() => {
        notification.remove();
      }, 3000);
    }
  }, [animationConfig.enableParticles, theme.reducedMotion, userId]);

  const unlockAchievement = useCallback((achievementId: string, title: string, description: string) => {
    setGamification(prev => {
      if (prev.achievements.includes(achievementId)) {
        return prev; // Ya desbloqueado
      }

      const updated = {
        ...prev,
        achievements: [...prev.achievements, achievementId]
      };

      // Persistir
      if (typeof window !== 'undefined' && userId) {
        localStorage.setItem(`ux-gamification-${userId}`, JSON.stringify(updated));
      }

      return updated;
    });

    // Efectos de celebración
    if (animationConfig.enableParticles && !theme.reducedMotion) {
      confetti({
        particleCount: 150,
        spread: 180,
        origin: { y: 0.6 },
        colors: ['#10B981', '#059669', '#047857']
      });
    }

    // Notificación de logro
    if (typeof window !== 'undefined') {
      const notification = document.createElement('div');
      notification.className = 'fixed top-4 right-4 z-50 bg-gradient-to-r from-green-500 to-emerald-600 text-white p-6 rounded-xl shadow-xl max-w-sm animate-achievement';
      notification.innerHTML = `
        <div class="flex items-start gap-3">
          <span class="text-2xl">🏆</span>
          <div>
            <p class="font-bold text-lg">¡Logro Desbloqueado!</p>
            <p class="font-medium">${title}</p>
            <p class="text-sm opacity-90 mt-1">${description}</p>
          </div>
        </div>
      `;
      
      document.body.appendChild(notification);
      
      setTimeout(() => {
        notification.remove();
      }, 5000);
    }
  }, [animationConfig.enableParticles, theme.reducedMotion, userId]);

  // ===== FUNCIONES DE PROGRESO =====
  const updateProgress = useCallback((metrics: Partial<ProgressMetrics>) => {
    setProgress(prev => ({ ...prev, ...metrics }));
  }, []);

  const completeUnit = useCallback((unitId: string, score: number, timeSpent: number) => {
    // Actualizar métricas
    setProgress(prev => ({
      ...prev,
      completedUnits: prev.completedUnits + 1,
      totalStudyTime: prev.totalStudyTime + timeSpent,
      overallProgress: ((prev.completedUnits + 1) / prev.totalUnits) * 100
    }));

    // Actualizar gamificación
    setGamification(prev => ({
      ...prev,
      totalStudyTime: prev.totalStudyTime + timeSpent
    }));

    // Otorgar XP basado en desempeño
    const xpReward = calculateXPReward(score, timeSpent);
    awardXP(xpReward, `Unidad completada con ${score}% de acierto`);

    // Verificar logros
    checkAndUnlockAchievements(score, timeSpent);
  }, [awardXP]);

  // ===== FUNCIONES DE UTILIDAD =====
  const calculateRank = (xp: number): GameficationState['rank'] => {
    if (xp >= 50000) return 'S';
    if (xp >= 25000) return 'A';
    if (xp >= 12000) return 'B';
    if (xp >= 5000) return 'C';
    if (xp >= 1000) return 'D';
    return 'E';
  };

  const calculateXPReward = (score: number, timeSpent: number): number => {
    const baseXP = 100;
    const scoreMultiplier = Math.max(0.5, score / 100);
    const timeBonus = timeSpent < 1800 ? 1.2 : 1.0; // Bonus por completar en <30min
    
    return Math.round(baseXP * scoreMultiplier * timeBonus);
  };

  const checkAndUnlockAchievements = (score: number, timeSpent: number) => {
    // Logro por perfección
    if (score === 100) {
      unlockAchievement('perfect_score', 'Puntuación Perfecta', 'Completaste una unidad con 100% de acierto');
    }

    // Logro por velocidad
    if (timeSpent < 900) { // 15 minutos
      unlockAchievement('speed_demon', 'Demonio de Velocidad', 'Completaste una unidad en menos de 15 minutos');
    }

    // Logro por consistencia
    if (gamification.currentStreak >= 7) {
      unlockAchievement('week_warrior', 'Guerrero Semanal', 'Estudiaste 7 días seguidos');
    }
  };

  // ===== CLASES CSS COMPUTADAS =====
  const cssClasses = useMemo(() => {
    const base = {
      theme: {
        khan: 'khan-style',
        coursera: 'coursera-style',
        hybrid: 'hybrid-bg'
      }[theme.style],
      
      card: [
        'glass-card',
        theme.highContrast && 'high-contrast',
        theme.style === 'hybrid' && 'unit-card'
      ].filter(Boolean).join(' '),
      
      button: {
        primary: {
          khan: 'btn-khan',
          coursera: 'btn-coursera',
          hybrid: 'btn-hybrid-primary'
        }[theme.style],
        
        secondary: `btn-hybrid btn-${theme.style}-secondary`
      },
      
      progress: {
        khan: 'progress-hybrid progress-bar-khan',
        coursera: 'progress-hybrid progress-bar-coursera',
        hybrid: 'progress-hybrid progress-bar-hybrid'
      }[theme.style],
      
      text: {
        gradient: {
          khan: 'text-gradient-khan',
          coursera: 'text-gradient-coursera',  
          hybrid: 'text-gradient-hybrid'
        }[theme.style]
      }
    };

    return base;
  }, [theme]);

  // ===== FUNCIONES DE ANIMACIÓN =====
  const triggerCelebration = useCallback((type: 'xp' | 'achievement' | 'levelup' | 'completion') => {
    if (theme.reducedMotion || !animationConfig.enableParticles) return;

    const configs = {
      xp: {
        particleCount: 30,
        spread: 45,
        colors: ['#FCD34D', '#F59E0B']
      },
      achievement: {
        particleCount: 100,
        spread: 120,
        colors: ['#10B981', '#059669', '#047857']
      },
      levelup: {
        particleCount: 150,
        spread: 160,
        colors: ['#8B5CF6', '#DB2777', '#DC2626']
      },
      completion: {
        particleCount: 80,
        spread: 90,
        colors: ['#3B82F6', '#1D4ED8', '#1E40AF']
      }
    };

    const config = configs[type];
    
    confetti({
      ...config,
      origin: { y: 0.7 },
      ticks: 200
    });
  }, [theme.reducedMotion, animationConfig.enableParticles]);

  // ===== RETURN DEL HOOK =====
  return {
    // Estados
    theme,
    animationConfig, 
    gamification,
    progress,
    
    // Configuración
    updateTheme,
    updateAnimationConfig,
    
    // Gamificación
    awardXP,
    unlockAchievement,
    triggerCelebration,
    
    // Progreso
    updateProgress,
    completeUnit,
    
    // Utilidades
    cssClasses,
    
    // Métricas computadas
    rankProgress: useMemo(() => {
      const thresholds = { E: 0, D: 1000, C: 5000, B: 12000, A: 25000, S: 50000 };
      const currentThreshold = thresholds[gamification.rank];
      const nextRank = Object.keys(thresholds).find(rank => 
        thresholds[rank as keyof typeof thresholds] > gamification.xp
      ) as keyof typeof thresholds;
      const nextThreshold = nextRank ? thresholds[nextRank] : currentThreshold;
      
      return {
        current: gamification.xp - currentThreshold,
        total: nextThreshold - currentThreshold,
        percentage: ((gamification.xp - currentThreshold) / (nextThreshold - currentThreshold)) * 100
      };
    }, [gamification.xp, gamification.rank]),
    
    studyEfficiency: useMemo(() => {
      if (gamification.totalStudyTime === 0) return 0;
      return (gamification.xp / gamification.totalStudyTime) * 60; // XP por hora
    }, [gamification.xp, gamification.totalStudyTime])
  };
};

// ===== HOOK PARA COMPONENTES ESPECÍFICOS =====
export const useHybridAnimations = (enabled: boolean = true) => {
  const [isAnimating, setIsAnimating] = useState(false);
  
  const animate = useCallback(async (
    element: HTMLElement, 
    animation: string, 
    duration: number = 300
  ) => {
    if (!enabled) return;
    
    setIsAnimating(true);
    element.style.animation = `${animation} ${duration}ms ease-out`;
    
    return new Promise<void>((resolve) => {
      setTimeout(() => {
        element.style.animation = '';
        setIsAnimating(false);
        resolve();
      }, duration);
    });
  }, [enabled]);
  
  return { animate, isAnimating };
};

export default useHybridUX;
