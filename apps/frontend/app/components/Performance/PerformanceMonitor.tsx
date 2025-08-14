'use client';

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Activity, 
  Cpu, 
  Zap, 
  Wifi,
  HardDrive,
  Settings,
  ChevronRight,
  AlertTriangle,
  CheckCircle
} from 'lucide-react';
import { usePerformanceOptimization, getPerformanceClasses } from '@/hooks/usePerformanceOptimization';
import { cn } from '@/lib/utils';

export default function PerformanceMonitor() {
  const [isExpanded, setIsExpanded] = useState(false);
  const { capabilities, settings, updateSettings, fps, memoryUsage } = usePerformanceOptimization();
  
  // Calculate status color
  const getStatusColor = () => {
    if (capabilities.performanceScore >= 80) return 'text-green-400';
    if (capabilities.performanceScore >= 50) return 'text-yellow-400';
    return 'text-red-400';
  };
  
  const getFPSColor = () => {
    if (fps >= 50) return 'text-green-400';
    if (fps >= 30) return 'text-yellow-400';
    return 'text-red-400';
  };
  
  const getMemoryColor = () => {
    if (!memoryUsage) return 'text-gray-400';
    if (memoryUsage < 50) return 'text-green-400';
    if (memoryUsage < 80) return 'text-yellow-400';
    return 'text-red-400';
  };
  
  return (
    <div className={cn(
      'fixed bottom-4 left-4 z-50',
      getPerformanceClasses(settings)
    )}>
      {/* Compact View */}
      <motion.button
        onClick={() => setIsExpanded(!isExpanded)}
        className="bg-gray-900/90 backdrop-blur-sm rounded-lg p-3 shadow-lg
          flex items-center gap-3 hover:bg-gray-800/90 transition-all"
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
      >
        <Activity className={cn('w-5 h-5', getStatusColor())} />
        
        <div className="flex items-center gap-4 text-sm">
          <div className="flex items-center gap-1">
            <span className="text-gray-400">FPS:</span>
            <span className={cn('font-mono font-bold', getFPSColor())}>
              {fps}
            </span>
          </div>
          
          {memoryUsage !== null && (
            <div className="flex items-center gap-1">
              <span className="text-gray-400">Mem:</span>
              <span className={cn('font-mono font-bold', getMemoryColor())}>
                {memoryUsage.toFixed(0)}%
              </span>
            </div>
          )}
        </div>
        
        <motion.div
          animate={{ rotate: isExpanded ? 90 : 0 }}
          transition={{ duration: 0.2 }}
        >
          <ChevronRight className="w-4 h-4 text-gray-400" />
        </motion.div>
      </motion.button>
      
      {/* Expanded View */}
      <AnimatePresence>
        {isExpanded && (
          <motion.div
            className="absolute bottom-full left-0 mb-2 bg-gray-900/95 
              backdrop-blur-sm rounded-lg shadow-2xl overflow-hidden"
            initial={{ opacity: 0, y: 20, scale: 0.9 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 20, scale: 0.9 }}
            style={{ width: '320px' }}
          >
            {/* Header */}
            <div className="bg-gradient-to-r from-purple-600 to-purple-700 p-4">
              <h3 className="text-white font-semibold flex items-center gap-2">
                <Activity className="w-5 h-5" />
                Monitor de Rendimiento
              </h3>
            </div>
            
            {/* Device Info */}
            <div className="p-4 space-y-3">
              <div className="bg-gray-800/50 rounded-lg p-3">
                <h4 className="text-sm font-semibold text-gray-300 mb-2">
                  Capacidades del Dispositivo
                </h4>
                
                <div className="space-y-2 text-sm">
                  <div className="flex items-center justify-between">
                    <span className="text-gray-400 flex items-center gap-1">
                      <Cpu className="w-3 h-3" />
                      CPU Cores
                    </span>
                    <span className="text-white font-mono">
                      {capabilities.hardwareConcurrency}
                    </span>
                  </div>
                  
                  {capabilities.deviceMemory && (
                    <div className="flex items-center justify-between">
                      <span className="text-gray-400 flex items-center gap-1">
                        <HardDrive className="w-3 h-3" />
                        RAM
                      </span>
                      <span className="text-white font-mono">
                        {capabilities.deviceMemory}GB
                      </span>
                    </div>
                  )}
                  
                  {capabilities.connectionType && (
                    <div className="flex items-center justify-between">
                      <span className="text-gray-400 flex items-center gap-1">
                        <Wifi className="w-3 h-3" />
                        Conexión
                      </span>
                      <span className="text-white font-mono uppercase">
                        {capabilities.connectionType}
                      </span>
                    </div>
                  )}
                  
                  <div className="flex items-center justify-between">
                    <span className="text-gray-400 flex items-center gap-1">
                      <Zap className="w-3 h-3" />
                      Puntuación
                    </span>
                    <span className={cn('font-mono font-bold', getStatusColor())}>
                      {capabilities.performanceScore}/100
                    </span>
                  </div>
                </div>
                
                {capabilities.isLowEnd && (
                  <div className="mt-3 p-2 bg-yellow-900/30 border border-yellow-500/30 
                    rounded flex items-center gap-2">
                    <AlertTriangle className="w-4 h-4 text-yellow-400" />
                    <span className="text-xs text-yellow-300">
                      Dispositivo de gama baja detectado
                    </span>
                  </div>
                )}
              </div>
              
              {/* Quality Settings */}
              <div className="bg-gray-800/50 rounded-lg p-3">
                <h4 className="text-sm font-semibold text-gray-300 mb-3 flex items-center gap-2">
                  <Settings className="w-4 h-4" />
                  Configuración de Calidad
                </h4>
                
                <div className="space-y-2">
                  <label className="flex items-center justify-between">
                    <span className="text-sm text-gray-400">Animaciones</span>
                    <input
                      type="checkbox"
                      checked={settings.enableAnimations}
                      onChange={(e) => updateSettings({ enableAnimations: e.target.checked })}
                      className="toggle"
                    />
                  </label>
                  
                  <label className="flex items-center justify-between">
                    <span className="text-sm text-gray-400">Gráficos 3D</span>
                    <input
                      type="checkbox"
                      checked={settings.enable3D}
                      onChange={(e) => updateSettings({ enable3D: e.target.checked })}
                      className="toggle"
                    />
                  </label>
                  
                  <label className="flex items-center justify-between">
                    <span className="text-sm text-gray-400">Partículas</span>
                    <input
                      type="checkbox"
                      checked={settings.enableParticles}
                      onChange={(e) => updateSettings({ enableParticles: e.target.checked })}
                      className="toggle"
                    />
                  </label>
                  
                  <label className="flex items-center justify-between">
                    <span className="text-sm text-gray-400">Sombras</span>
                    <input
                      type="checkbox"
                      checked={settings.enableShadows}
                      onChange={(e) => updateSettings({ enableShadows: e.target.checked })}
                      className="toggle"
                    />
                  </label>
                  
                  <div className="pt-2 border-t border-gray-700">
                    <label className="text-sm text-gray-400">Calidad de Texturas</label>
                    <select
                      value={settings.textureQuality}
                      onChange={(e) => updateSettings({ 
                        textureQuality: e.target.value as 'low' | 'medium' | 'high' 
                      })}
                      className="mt-1 w-full bg-gray-700 text-white px-2 py-1 rounded text-sm"
                    >
                      <option value="low">Baja</option>
                      <option value="medium">Media</option>
                      <option value="high">Alta</option>
                    </select>
                  </div>
                  
                  <div>
                    <label className="text-sm text-gray-400">
                      Escala de Renderizado: {(settings.renderScale * 100).toFixed(0)}%
                    </label>
                    <input
                      type="range"
                      min="50"
                      max="100"
                      value={settings.renderScale * 100}
                      onChange={(e) => updateSettings({ 
                        renderScale: parseInt(e.target.value) / 100 
                      })}
                      className="w-full mt-1"
                    />
                  </div>
                </div>
              </div>
              
              {/* Auto-optimization Status */}
              <div className="bg-gray-800/50 rounded-lg p-3">
                <div className="flex items-center gap-2 text-sm">
                  <CheckCircle className="w-4 h-4 text-green-400" />
                  <span className="text-gray-300">
                    Optimización automática activa
                  </span>
                </div>
                <p className="text-xs text-gray-500 mt-1">
                  La calidad se ajusta según el rendimiento
                </p>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
      
      <style jsx>{`
        .toggle {
          appearance: none;
          width: 40px;
          height: 20px;
          background-color: #374151;
          border-radius: 10px;
          position: relative;
          cursor: pointer;
          transition: background-color 0.2s;
        }
        
        .toggle:checked {
          background-color: #8b5cf6;
        }
        
        .toggle::after {
          content: '';
          position: absolute;
          width: 16px;
          height: 16px;
          border-radius: 50%;
          background-color: white;
          top: 2px;
          left: 2px;
          transition: transform 0.2s;
        }
        
        .toggle:checked::after {
          transform: translateX(20px);
        }
      `}</style>
    </div>
  );
}