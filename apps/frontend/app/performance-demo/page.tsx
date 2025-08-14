'use client';

import React, { useState } from 'react';
import PerformanceMonitor from '../components/Performance/PerformanceMonitor';
import { usePerformanceOptimization, PerformanceStyles } from '../hooks/usePerformanceOptimization';
import { 
  Zap, 
  Cpu, 
  Activity,
  Gauge,
  Settings,
  AlertTriangle,
  CheckCircle,
  HardDrive
} from 'lucide-react';
import { motion } from 'framer-motion';

// Heavy component to test performance
function HeavyAnimation({ enabled }: { enabled: boolean }) {
  if (!enabled) return null;
  
  return (
    <div className="relative h-64 overflow-hidden rounded-lg bg-gray-800/50">
      {Array.from({ length: 50 }).map((_, i) => (
        <motion.div
          key={i}
          className="absolute w-4 h-4 bg-purple-500 rounded-full"
          animate={{
            x: [0, 300, 0],
            y: [0, 200, 0],
            scale: [1, 2, 1],
          }}
          transition={{
            duration: 3 + i * 0.1,
            repeat: Infinity,
            ease: "easeInOut",
            delay: i * 0.05
          }}
          style={{
            left: `${(i % 10) * 10}%`,
            top: `${Math.floor(i / 10) * 20}%`,
          }}
        />
      ))}
    </div>
  );
}

export default function PerformanceDemoPage() {
  const { capabilities, settings, updateSettings } = usePerformanceOptimization();
  const [stressTest, setStressTest] = useState(false);
  
  const performanceTests = [
    {
      name: 'Animaciones CSS',
      description: 'Múltiples animaciones simultáneas',
      enabled: settings.enableAnimations,
      toggle: () => updateSettings({ enableAnimations: !settings.enableAnimations })
    },
    {
      name: 'Gráficos 3D',
      description: 'Renderizado Three.js',
      enabled: settings.enable3D,
      toggle: () => updateSettings({ enable3D: !settings.enable3D })
    },
    {
      name: 'Sistema de Partículas',
      description: 'Efectos visuales complejos',
      enabled: settings.enableParticles,
      toggle: () => updateSettings({ enableParticles: !settings.enableParticles })
    },
    {
      name: 'Sombras Dinámicas',
      description: 'Cálculo de sombras en tiempo real',
      enabled: settings.enableShadows,
      toggle: () => updateSettings({ enableShadows: !settings.enableShadows })
    }
  ];
  
  return (
    <>
      <PerformanceStyles />
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900 
        to-gray-900 p-4">
        <div className="max-w-6xl mx-auto">
          {/* Header */}
          <div className="text-center mb-8">
            <div className="inline-flex items-center justify-center w-20 h-20 
              bg-purple-600 rounded-full mb-4">
              <Zap className="w-10 h-10 text-white" />
            </div>
            
            <h1 className="text-4xl font-bold text-white mb-4 font-cinzel">
              Optimización de Rendimiento
            </h1>
            
            <p className="text-gray-300 max-w-2xl mx-auto">
              Sistema inteligente que detecta las capacidades de tu dispositivo 
              y ajusta automáticamente la calidad gráfica para la mejor experiencia.
            </p>
          </div>
          
          {/* Device Status */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            <div className="bg-gray-900/80 rounded-lg p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-white">Estado del Dispositivo</h3>
                <Cpu className="w-6 h-6 text-purple-400" />
              </div>
              
              <div className="space-y-3">
                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-gray-400">Rendimiento</span>
                    <span className={`font-bold ${
                      capabilities.performanceScore >= 80 ? 'text-green-400' :
                      capabilities.performanceScore >= 50 ? 'text-yellow-400' :
                      'text-red-400'
                    }`}>
                      {capabilities.performanceScore}/100
                    </span>
                  </div>
                  <div className="w-full bg-gray-700 rounded-full h-2">
                    <div 
                      className={`h-full rounded-full transition-all ${
                        capabilities.performanceScore >= 80 ? 'bg-green-500' :
                        capabilities.performanceScore >= 50 ? 'bg-yellow-500' :
                        'bg-red-500'
                      }`}
                      style={{ width: `${capabilities.performanceScore}%` }}
                    />
                  </div>
                </div>
                
                <div className="text-sm space-y-1">
                  <div className="flex justify-between">
                    <span className="text-gray-400">CPU</span>
                    <span className="text-white">{capabilities.hardwareConcurrency} cores</span>
                  </div>
                  {capabilities.deviceMemory && (
                    <div className="flex justify-between">
                      <span className="text-gray-400">RAM</span>
                      <span className="text-white">{capabilities.deviceMemory}GB</span>
                    </div>
                  )}
                  {capabilities.connectionType && (
                    <div className="flex justify-between">
                      <span className="text-gray-400">Red</span>
                      <span className="text-white uppercase">{capabilities.connectionType}</span>
                    </div>
                  )}
                </div>
              </div>
              
              {capabilities.isLowEnd && (
                <div className="mt-4 p-3 bg-yellow-900/30 border border-yellow-500/30 
                  rounded-lg flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4 text-yellow-400" />
                  <span className="text-sm text-yellow-300">
                    Dispositivo de recursos limitados
                  </span>
                </div>
              )}
            </div>
            
            <div className="bg-gray-900/80 rounded-lg p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-white">Calidad Actual</h3>
                <Settings className="w-6 h-6 text-purple-400" />
              </div>
              
              <div className="space-y-3">
                <div className="bg-gray-800 rounded-lg p-3">
                  <div className="text-center">
                    <span className="text-3xl font-bold text-purple-400">
                      {settings.textureQuality.toUpperCase()}
                    </span>
                    <p className="text-sm text-gray-400 mt-1">Calidad de Texturas</p>
                  </div>
                </div>
                
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div className={`p-2 rounded text-center ${
                    settings.enableAnimations ? 'bg-green-900/30 text-green-400' : 'bg-gray-800 text-gray-500'
                  }`}>
                    Animaciones
                  </div>
                  <div className={`p-2 rounded text-center ${
                    settings.enable3D ? 'bg-green-900/30 text-green-400' : 'bg-gray-800 text-gray-500'
                  }`}>
                    3D
                  </div>
                  <div className={`p-2 rounded text-center ${
                    settings.enableParticles ? 'bg-green-900/30 text-green-400' : 'bg-gray-800 text-gray-500'
                  }`}>
                    Partículas
                  </div>
                  <div className={`p-2 rounded text-center ${
                    settings.enableShadows ? 'bg-green-900/30 text-green-400' : 'bg-gray-800 text-gray-500'
                  }`}>
                    Sombras
                  </div>
                </div>
              </div>
              
              <div className="mt-4 p-3 bg-purple-900/30 border border-purple-500/30 
                rounded-lg flex items-center gap-2">
                <CheckCircle className="w-4 h-4 text-purple-400" />
                <span className="text-sm text-purple-300">
                  Ajuste automático activo
                </span>
              </div>
            </div>
            
            <div className="bg-gray-900/80 rounded-lg p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-white">Prueba de Estrés</h3>
                <Activity className="w-6 h-6 text-purple-400" />
              </div>
              
              <p className="text-gray-400 text-sm mb-4">
                Activa la prueba para ver cómo el sistema ajusta automáticamente 
                la calidad según el rendimiento.
              </p>
              
              <button
                onClick={() => setStressTest(!stressTest)}
                className={`w-full py-3 px-4 rounded-lg font-semibold transition-all ${
                  stressTest 
                    ? 'bg-red-600 hover:bg-red-700 text-white'
                    : 'bg-purple-600 hover:bg-purple-700 text-white'
                }`}
              >
                {stressTest ? 'Detener Prueba' : 'Iniciar Prueba'}
              </button>
              
              {stressTest && (
                <div className="mt-4 p-3 bg-red-900/30 border border-red-500/30 
                  rounded-lg">
                  <p className="text-sm text-red-300">
                    Renderizando elementos pesados...
                  </p>
                </div>
              )}
            </div>
          </div>
          
          {/* Performance Tests */}
          <div className="bg-gray-900/80 rounded-lg p-6 mb-8">
            <h3 className="text-xl font-semibold text-white mb-6">
              Configuración Manual
            </h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {performanceTests.map((test, index) => (
                <div key={index} className="bg-gray-800/50 rounded-lg p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="font-semibold text-white">{test.name}</h4>
                      <p className="text-sm text-gray-400">{test.description}</p>
                    </div>
                    
                    <button
                      onClick={test.toggle}
                      className={`px-4 py-2 rounded-lg font-semibold transition-all ${
                        test.enabled 
                          ? 'bg-green-600 hover:bg-green-700 text-white'
                          : 'bg-gray-700 hover:bg-gray-600 text-gray-300'
                      }`}
                    >
                      {test.enabled ? 'ON' : 'OFF'}
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
          
          {/* Stress Test Animation */}
          {stressTest && (
            <div className="mb-8">
              <h3 className="text-xl font-semibold text-white mb-4">
                Animación de Prueba
              </h3>
              <HeavyAnimation enabled={settings.enableAnimations} />
            </div>
          )}
          
          {/* Tips */}
          <div className="bg-gray-900/80 rounded-lg p-6">
            <h3 className="text-xl font-semibold text-white mb-4">
              Consejos de Rendimiento
            </h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
              <div className="flex items-start gap-3">
                <Gauge className="w-5 h-5 text-purple-400 mt-0.5" />
                <div>
                  <p className="text-white font-semibold">Monitor Integrado</p>
                  <p className="text-gray-400">
                    Observa el FPS y uso de memoria en la esquina inferior izquierda
                  </p>
                </div>
              </div>
              
              <div className="flex items-start gap-3">
                <Zap className="w-5 h-5 text-purple-400 mt-0.5" />
                <div>
                  <p className="text-white font-semibold">Ajuste Automático</p>
                  <p className="text-gray-400">
                    El sistema reduce la calidad si detecta caídas de rendimiento
                  </p>
                </div>
              </div>
              
              <div className="flex items-start gap-3">
                <HardDrive className="w-5 h-5 text-purple-400 mt-0.5" />
                <div>
                  <p className="text-white font-semibold">Ahorro de Recursos</p>
                  <p className="text-gray-400">
                    Las animaciones se pausan cuando la pestaña no está activa
                  </p>
                </div>
              </div>
              
              <div className="flex items-start gap-3">
                <Settings className="w-5 h-5 text-purple-400 mt-0.5" />
                <div>
                  <p className="text-white font-semibold">Personalización</p>
                  <p className="text-gray-400">
                    Ajusta manualmente la calidad según tus preferencias
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        {/* Performance Monitor */}
        <PerformanceMonitor />
      </div>
    </>
  );
}