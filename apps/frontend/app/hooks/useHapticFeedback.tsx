import { useCallback } from 'react';

type HapticStyle = 'light' | 'medium' | 'heavy' | 'soft' | 'rigid';
type NotificationType = 'success' | 'warning' | 'error';

interface HapticPattern {
  pattern: number[];
  intensity?: number;
}

const HAPTIC_PATTERNS: Record<string, HapticPattern> = {
  // UI Interactions
  tap: { pattern: [10] },
  doubleTap: { pattern: [10, 50, 10] },
  longPress: { pattern: [50] },
  
  // Game Events
  levelUp: { pattern: [50, 100, 50, 100, 100], intensity: 1 },
  questComplete: { pattern: [30, 70, 30, 70], intensity: 0.8 },
  damage: { pattern: [100, 50, 100], intensity: 1 },
  critical: { pattern: [150, 50, 150, 50, 200], intensity: 1 },
  
  // Notifications
  success: { pattern: [30, 100, 30], intensity: 0.7 },
  error: { pattern: [200, 100, 200], intensity: 1 },
  warning: { pattern: [50, 50, 50], intensity: 0.6 },
  
  // Navigation
  swipe: { pattern: [5] },
  pageChange: { pattern: [20, 40, 20] },
  
  // Special
  epic: { pattern: [100, 50, 100, 50, 150, 50, 200], intensity: 1 },
  powerUp: { pattern: [20, 40, 60, 80, 100], intensity: 0.9 }
};

export function useHapticFeedback() {
  // Check if Vibration API is supported
  const isSupported = typeof window !== 'undefined' && 'vibrate' in navigator;
  
  // Basic vibration
  const vibrate = useCallback((duration: number | number[]) => {
    if (!isSupported) return false;
    
    try {
      return navigator.vibrate(duration);
    } catch (error) {
      console.error('Haptic feedback error:', error);
      return false;
    }
  }, [isSupported]);
  
  // Pattern-based vibration
  const vibratePattern = useCallback((patternName: keyof typeof HAPTIC_PATTERNS) => {
    if (!isSupported) return false;
    
    const pattern = HAPTIC_PATTERNS[patternName];
    if (!pattern) return false;
    
    return vibrate(pattern.pattern);
  }, [isSupported, vibrate]);
  
  // iOS-style haptic feedback (fallback to vibration)
  const impact = useCallback((style: HapticStyle = 'medium') => {
    if (!isSupported) return;
    
    const durations: Record<HapticStyle, number> = {
      light: 10,
      medium: 20,
      heavy: 30,
      soft: 15,
      rigid: 40
    };
    
    vibrate(durations[style]);
  }, [isSupported, vibrate]);
  
  // Notification feedback
  const notification = useCallback((type: NotificationType) => {
    if (!isSupported) return;
    
    const patterns: Record<NotificationType, number[]> = {
      success: HAPTIC_PATTERNS.success.pattern,
      warning: HAPTIC_PATTERNS.warning.pattern,
      error: HAPTIC_PATTERNS.error.pattern
    };
    
    vibrate(patterns[type]);
  }, [isSupported, vibrate]);
  
  // Selection changed feedback
  const selectionChanged = useCallback(() => {
    if (!isSupported) return;
    vibrate(5);
  }, [isSupported, vibrate]);
  
  // Custom haptic composer
  const compose = useCallback((pattern: number[], intensity = 1) => {
    if (!isSupported) return false;
    
    // Scale pattern by intensity
    const scaledPattern = pattern.map(duration => 
      Math.round(duration * intensity)
    );
    
    return vibrate(scaledPattern);
  }, [isSupported, vibrate]);
  
  // Game-specific haptics
  const gameHaptics = {
    // Battle haptics
    attack: () => vibratePattern('tap'),
    criticalHit: () => vibratePattern('critical'),
    takeDamage: () => vibratePattern('damage'),
    
    // Achievement haptics
    levelUp: () => vibratePattern('levelUp'),
    questComplete: () => vibratePattern('questComplete'),
    achievementUnlock: () => vibratePattern('epic'),
    
    // UI haptics
    buttonPress: () => impact('light'),
    toggleSwitch: () => impact('medium'),
    sliderChange: () => selectionChanged(),
    
    // Navigation haptics
    swipeGesture: () => vibratePattern('swipe'),
    pageTransition: () => vibratePattern('pageChange'),
    
    // Special effects
    powerUp: () => vibratePattern('powerUp'),
    epicMoment: () => vibratePattern('epic')
  };
  
  return {
    isSupported,
    vibrate,
    vibratePattern,
    impact,
    notification,
    selectionChanged,
    compose,
    ...gameHaptics
  };
}

// HOC to add haptic feedback to any component
export function withHapticFeedback<P extends object>(
  Component: React.ComponentType<P>,
  hapticType: keyof typeof HAPTIC_PATTERNS = 'tap'
) {
  return function WithHapticFeedbackComponent(props: P) {
    const { vibratePattern } = useHapticFeedback();
    
    const handleInteraction = useCallback((callback?: () => void) => {
      vibratePattern(hapticType);
      callback?.();
    }, [vibratePattern]);
    
    return <Component {...props} onHapticFeedback={handleInteraction} />;
  };
}