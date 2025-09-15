// Mobile utilities for enhanced responsiveness and mobile-specific features

export interface DeviceInfo {
  isMobile: boolean;
  isTablet: boolean;
  isDesktop: boolean;
  isIOS: boolean;
  isAndroid: boolean;
  isTouchDevice: boolean;
  screenWidth: number;
  screenHeight: number;
  devicePixelRatio: number;
  orientation: 'portrait' | 'landscape' | 'unknown';
  isRetina: boolean;
  hasVibration: boolean;
  hasServiceWorker: boolean;
  hasGeolocation: boolean;
  connection?: {
    effectiveType: string;
    downlink: number;
    rtt: number;
  };
}

/**
 * Get comprehensive device information
 */
export const getDeviceInfo = (): DeviceInfo => {
  if (typeof window === 'undefined') {
    return {
      isMobile: false,
      isTablet: false,
      isDesktop: true,
      isIOS: false,
      isAndroid: false,
      isTouchDevice: false,
      screenWidth: 1920,
      screenHeight: 1080,
      devicePixelRatio: 1,
      orientation: 'unknown',
      isRetina: false,
      hasVibration: false,
      hasServiceWorker: false,
      hasGeolocation: false,
    };
  }

  const userAgent = navigator.userAgent;
  const screenWidth = window.screen.width;
  const screenHeight = window.screen.height;
  const devicePixelRatio = window.devicePixelRatio || 1;
  
  // Device type detection
  const isMobile = screenWidth <= 767;
  const isTablet = screenWidth > 767 && screenWidth <= 1023;
  const isDesktop = screenWidth > 1023;
  
  // Platform detection
  const isIOS = /iPad|iPhone|iPod/.test(userAgent);
  const isAndroid = /Android/.test(userAgent);
  
  // Touch support
  const isTouchDevice = 'ontouchstart' in window || navigator.maxTouchPoints > 0;
  
  // Orientation
  const getOrientation = (): 'portrait' | 'landscape' | 'unknown' => {
    if (screen.orientation) {
      return screen.orientation.type.includes('portrait') ? 'portrait' : 'landscape';
    }
    return screenWidth < screenHeight ? 'portrait' : 'landscape';
  };
  
  // Retina detection
  const isRetina = devicePixelRatio > 1;
  
  // Feature detection
  const hasVibration = 'vibrate' in navigator;
  const hasServiceWorker = 'serviceWorker' in navigator;
  const hasGeolocation = 'geolocation' in navigator;
  
  // Network information (if available)
  const connection = (navigator as any).connection || (navigator as any).mozConnection || (navigator as any).webkitConnection;
  const connectionInfo = connection ? {
    effectiveType: connection.effectiveType || 'unknown',
    downlink: connection.downlink || 0,
    rtt: connection.rtt || 0,
  } : undefined;

  return {
    isMobile,
    isTablet,
    isDesktop,
    isIOS,
    isAndroid,
    isTouchDevice,
    screenWidth,
    screenHeight,
    devicePixelRatio,
    orientation: getOrientation(),
    isRetina,
    hasVibration,
    hasServiceWorker,
    hasGeolocation,
    connection: connectionInfo,
  };
};

/**
 * Haptic feedback utility
 */
export const hapticFeedback = {
  light: () => {
    if (navigator.vibrate) {
      navigator.vibrate(25);
    }
  },
  medium: () => {
    if (navigator.vibrate) {
      navigator.vibrate(50);
    }
  },
  heavy: () => {
    if (navigator.vibrate) {
      navigator.vibrate(100);
    }
  },
  pattern: (pattern: number[]) => {
    if (navigator.vibrate) {
      navigator.vibrate(pattern);
    }
  },
  success: () => {
    if (navigator.vibrate) {
      navigator.vibrate([50, 50, 50]);
    }
  },
  error: () => {
    if (navigator.vibrate) {
      navigator.vibrate([100, 50, 100, 50, 100]);
    }
  },
};

/**
 * Mobile-specific CSS classes generator
 */
export const mobileClasses = {
  touchTarget: 'min-h-[44px] min-w-[44px] touch-manipulation',
  touchTargetLarge: 'min-h-[48px] min-w-[48px] touch-manipulation',
  touchTargetComfortable: 'min-h-[52px] min-w-[52px] touch-manipulation',
  
  // Responsive text sizes
  textResponsive: {
    xs: 'text-xs mobile:text-xs',
    sm: 'text-sm mobile:text-sm',
    base: 'text-base mobile:text-sm',
    lg: 'text-lg mobile:text-base',
    xl: 'text-xl mobile:text-lg',
    '2xl': 'text-2xl mobile:text-xl',
    '3xl': 'text-3xl mobile:text-2xl',
    '4xl': 'text-4xl mobile:text-3xl',
  },
  
  // Responsive padding
  paddingResponsive: {
    sm: 'p-2 mobile:p-1',
    md: 'p-4 mobile:p-3',
    lg: 'p-6 mobile:p-4',
    xl: 'p-8 mobile:p-5',
  },
  
  // Responsive margins
  marginResponsive: {
    sm: 'm-2 mobile:m-1',
    md: 'm-4 mobile:m-3',
    lg: 'm-6 mobile:m-4',
    xl: 'm-8 mobile:m-5',
  },
  
  // Safe area support
  safeArea: 'mobile-viewport-fit',
  
  // Mobile scroll optimization
  mobileScroll: 'mobile-scroll overflow-y-auto',
  
  // Remove tap highlight
  noTapHighlight: 'tap-highlight-none',
  
  // Disable text selection on mobile
  noSelectMobile: 'select-none-mobile',
};

/**
 * Performance utilities for mobile devices
 */
export const mobilePerformance = {
  /**
   * Debounce function for touch/scroll events
   */
  debounce: <T extends (...args: any[]) => void>(func: T, wait: number) => {
    let timeout: NodeJS.Timeout;
    return (...args: Parameters<T>) => {
      clearTimeout(timeout);
      timeout = setTimeout(() => func.apply(null, args), wait);
    };
  },
  
  /**
   * Throttle function for frequent events
   */
  throttle: <T extends (...args: any[]) => void>(func: T, limit: number) => {
    let inThrottle: boolean;
    return (...args: Parameters<T>) => {
      if (!inThrottle) {
        func.apply(null, args);
        inThrottle = true;
        setTimeout(() => inThrottle = false, limit);
      }
    };
  },
  
  /**
   * Measure performance
   */
  measurePerformance: (name: string, fn: () => void) => {
    const start = performance.now();
    fn();
    const end = performance.now();
    console.log(`${name} took ${end - start} milliseconds.`);
  },
  
  /**
   * Check if device is low-end (for performance optimization)
   */
  isLowEndDevice: (): boolean => {
    const deviceInfo = getDeviceInfo();
    const memory = (performance as any).memory;
    
    // Basic heuristics for low-end device detection
    const lowResolution = deviceInfo.screenWidth < 720;
    const lowPixelRatio = deviceInfo.devicePixelRatio < 2;
    const lowMemory = memory && memory.jsHeapSizeLimit < 1073741824; // Less than 1GB
    
    return lowResolution || lowPixelRatio || lowMemory;
  },
};

/**
 * Mobile navigation utilities
 */
export const mobileNavigation = {
  /**
   * Add safe area padding to body for full-screen experiences
   */
  enableSafeArea: () => {
    if (typeof document !== 'undefined') {
      document.body.classList.add('mobile-viewport-fit');
    }
  },
  
  /**
   * Disable safe area padding
   */
  disableSafeArea: () => {
    if (typeof document !== 'undefined') {
      document.body.classList.remove('mobile-viewport-fit');
    }
  },
  
  /**
   * Lock screen orientation (if supported)
   */
  lockOrientation: (orientation: 'portrait' | 'landscape') => {
    if (screen.orientation && screen.orientation.lock) {
      screen.orientation.lock(orientation);
    }
  },
  
  /**
   * Unlock screen orientation
   */
  unlockOrientation: () => {
    if (screen.orientation && screen.orientation.unlock) {
      screen.orientation.unlock();
    }
  },
};

/**
 * Touch gesture utilities
 */
export const touchGestures = {
  /**
   * Simple swipe detection
   */
  detectSwipe: (
    element: HTMLElement,
    onSwipe: (direction: 'left' | 'right' | 'up' | 'down') => void,
    threshold: number = 50
  ) => {
    let startX = 0;
    let startY = 0;
    let endX = 0;
    let endY = 0;
    
    const handleTouchStart = (e: TouchEvent) => {
      startX = e.changedTouches[0].screenX;
      startY = e.changedTouches[0].screenY;
    };
    
    const handleTouchEnd = (e: TouchEvent) => {
      endX = e.changedTouches[0].screenX;
      endY = e.changedTouches[0].screenY;
      handleSwipe();
    };
    
    const handleSwipe = () => {
      const diffX = endX - startX;
      const diffY = endY - startY;
      
      if (Math.abs(diffX) > Math.abs(diffY)) {
        // Horizontal swipe
        if (Math.abs(diffX) > threshold) {
          onSwipe(diffX > 0 ? 'right' : 'left');
        }
      } else {
        // Vertical swipe
        if (Math.abs(diffY) > threshold) {
          onSwipe(diffY > 0 ? 'down' : 'up');
        }
      }
    };
    
    element.addEventListener('touchstart', handleTouchStart, { passive: true });
    element.addEventListener('touchend', handleTouchEnd, { passive: true });
    
    // Return cleanup function
    return () => {
      element.removeEventListener('touchstart', handleTouchStart);
      element.removeEventListener('touchend', handleTouchEnd);
    };
  },
};

/**
 * Mobile-specific validation utilities
 */
export const mobileValidation = {
  /**
   * Check if touch target meets accessibility guidelines
   */
  isValidTouchTarget: (element: HTMLElement): boolean => {
    const rect = element.getBoundingClientRect();
    return rect.width >= 44 && rect.height >= 44;
  },
  
  /**
   * Validate responsive breakpoints
   */
  validateBreakpoints: (): {
    mobile: boolean;
    tablet: boolean;
    desktop: boolean;
    current: string;
  } => {
    const width = window.innerWidth;
    return {
      mobile: width <= 767,
      tablet: width > 767 && width <= 1023,
      desktop: width > 1023,
      current: width <= 767 ? 'mobile' : width <= 1023 ? 'tablet' : 'desktop',
    };
  },
};

export default {
  getDeviceInfo,
  hapticFeedback,
  mobileClasses,
  mobilePerformance,
  mobileNavigation,
  touchGestures,
  mobileValidation,
};