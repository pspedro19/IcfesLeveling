import { useState, useEffect, useRef } from 'react';

interface DeviceCapabilities {
  deviceMemory: number | null;
  hardwareConcurrency: number;
  connectionType: string | null;
  saveData: boolean;
  isLowEnd: boolean;
  performanceScore: number;
}

interface PerformanceSettings {
  enableAnimations: boolean;
  enable3D: boolean;
  enableParticles: boolean;
  enableShadows: boolean;
  textureQuality: 'low' | 'medium' | 'high';
  renderScale: number;
  maxFPS: number;
}

interface UsePerformanceOptimizationReturn {
  capabilities: DeviceCapabilities;
  settings: PerformanceSettings;
  updateSettings: (newSettings: Partial<PerformanceSettings>) => void;
  isMonitoring: boolean;
  fps: number;
  memoryUsage: number | null;
}

// Default settings based on device capabilities
const getDefaultSettings = (isLowEnd: boolean): PerformanceSettings => {
  if (isLowEnd) {
    return {
      enableAnimations: false,
      enable3D: false,
      enableParticles: false,
      enableShadows: false,
      textureQuality: 'low',
      renderScale: 0.75,
      maxFPS: 30
    };
  }
  
  return {
    enableAnimations: true,
    enable3D: true,
    enableParticles: true,
    enableShadows: true,
    textureQuality: 'high',
    renderScale: 1,
    maxFPS: 60
  };
};

export function usePerformanceOptimization(): UsePerformanceOptimizationReturn {
  const [capabilities, setCapabilities] = useState<DeviceCapabilities>({
    deviceMemory: null,
    hardwareConcurrency: navigator.hardwareConcurrency || 4,
    connectionType: null,
    saveData: false,
    isLowEnd: false,
    performanceScore: 100
  });
  
  const [settings, setSettings] = useState<PerformanceSettings>(
    getDefaultSettings(false)
  );
  
  const [fps, setFps] = useState(60);
  const [memoryUsage, setMemoryUsage] = useState<number | null>(null);
  const [isMonitoring, setIsMonitoring] = useState(false);
  
  const frameCount = useRef(0);
  const lastTime = useRef(performance.now());
  const animationId = useRef<number>();
  
  // Detect device capabilities
  useEffect(() => {
    const detectCapabilities = async () => {
      const caps: Partial<DeviceCapabilities> = {
        hardwareConcurrency: navigator.hardwareConcurrency || 4
      };
      
      // Device Memory API
      if ('deviceMemory' in navigator) {
        caps.deviceMemory = (navigator as any).deviceMemory;
      }
      
      // Network Information API
      if ('connection' in navigator) {
        const connection = (navigator as any).connection;
        caps.connectionType = connection?.effectiveType || null;
        caps.saveData = connection?.saveData || false;
      }
      
      // Calculate performance score
      let score = 100;
      
      // CPU cores
      if (caps.hardwareConcurrency! < 4) score -= 20;
      if (caps.hardwareConcurrency! < 2) score -= 30;
      
      // RAM
      if (caps.deviceMemory && caps.deviceMemory < 4) score -= 20;
      if (caps.deviceMemory && caps.deviceMemory < 2) score -= 30;
      
      // Network
      if (caps.connectionType === '2g' || caps.connectionType === 'slow-2g') score -= 20;
      if (caps.connectionType === '3g') score -= 10;
      
      // Data saver
      if (caps.saveData) score -= 10;
      
      caps.performanceScore = Math.max(0, score);
      caps.isLowEnd = score < 50;
      
      setCapabilities(prev => ({ ...prev, ...caps }));
      setSettings(getDefaultSettings(caps.isLowEnd || false));
    };
    
    detectCapabilities();
  }, []);
  
  // FPS monitoring
  useEffect(() => {
    if (!isMonitoring) return;
    
    const measureFPS = () => {
      const currentTime = performance.now();
      frameCount.current++;
      
      if (currentTime >= lastTime.current + 1000) {
        setFps(Math.round((frameCount.current * 1000) / (currentTime - lastTime.current)));
        frameCount.current = 0;
        lastTime.current = currentTime;
      }
      
      animationId.current = requestAnimationFrame(measureFPS);
    };
    
    animationId.current = requestAnimationFrame(measureFPS);
    
    return () => {
      if (animationId.current) {
        cancelAnimationFrame(animationId.current);
      }
    };
  }, [isMonitoring]);
  
  // Memory monitoring
  useEffect(() => {
    if (!isMonitoring) return;
    
    const measureMemory = async () => {
      if ('memory' in performance) {
        const memory = (performance as any).memory;
        const usedMemory = memory.usedJSHeapSize;
        const totalMemory = memory.jsHeapSizeLimit;
        const percentage = (usedMemory / totalMemory) * 100;
        setMemoryUsage(percentage);
      }
    };
    
    const interval = setInterval(measureMemory, 1000);
    
    return () => clearInterval(interval);
  }, [isMonitoring]);
  
  // Auto-adjust settings based on performance
  useEffect(() => {
    if (!isMonitoring) return;
    
    const adjustSettings = () => {
      // If FPS drops below threshold, reduce quality
      if (fps < 20 && settings.textureQuality !== 'low') {
        updateSettings({
          enableParticles: false,
          enableShadows: false,
          textureQuality: 'low',
          renderScale: 0.75
        });
      } else if (fps < 30 && settings.textureQuality === 'high') {
        updateSettings({
          enableShadows: false,
          textureQuality: 'medium',
          renderScale: 0.9
        });
      }
      
      // If memory usage is high, disable features
      if (memoryUsage && memoryUsage > 80) {
        updateSettings({
          enableParticles: false,
          enable3D: false
        });
      }
    };
    
    const interval = setInterval(adjustSettings, 5000);
    
    return () => clearInterval(interval);
  }, [fps, memoryUsage, settings, isMonitoring]);
  
  const updateSettings = (newSettings: Partial<PerformanceSettings>) => {
    setSettings(prev => ({ ...prev, ...newSettings }));
  };
  
  // Start monitoring when component using this hook mounts
  useEffect(() => {
    setIsMonitoring(true);
    return () => setIsMonitoring(false);
  }, []);
  
  return {
    capabilities,
    settings,
    updateSettings,
    isMonitoring,
    fps,
    memoryUsage
  };
}

// CSS classes based on performance settings
export function getPerformanceClasses(settings: PerformanceSettings): string {
  const classes: string[] = [];
  
  if (!settings.enableAnimations) {
    classes.push('reduce-motion');
  }
  
  if (settings.textureQuality === 'low') {
    classes.push('low-quality');
  }
  
  if (settings.renderScale < 1) {
    classes.push('reduced-scale');
  }
  
  return classes.join(' ');
}

// Global performance styles
export const PerformanceStyles = () => (
  <style jsx global>{`
    .reduce-motion * {
      animation-duration: 0.001ms !important;
      transition-duration: 0.001ms !important;
    }
    
    .low-quality img,
    .low-quality video {
      image-rendering: pixelated;
      filter: blur(0.5px);
    }
    
    .reduced-scale {
      transform: scale(var(--render-scale, 1));
      transform-origin: top left;
    }
  `}</style>
);