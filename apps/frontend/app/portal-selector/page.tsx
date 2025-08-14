'use client';

import React, { useState, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { 
  Eye, 
  Monitor, 
  Smartphone, 
  Zap, 
  Download,
  HardDrive,
  Clock,
  Star,
  Settings,
  Sparkles,
  Shield,
  Sword
} from 'lucide-react';

// Portal configurations - STATIC CONST outside component
const PORTAL_CONFIGS = {
  portal: {
    name: 'Portal Legendario',
    size: '24.8 MB',
    quality: 'Ultra Alta',
    polygons: '~100K+',
    description: 'Portal de máxima poder para Hunters Elite, con detalles místicos supremos',
    recommended: 'Reino Desktop Potente',
    color: 'border-purple-500',
    bgGradient: 'from-purple-900 via-purple-700 to-purple-500',
    pros: [
      'Máxima gloria visual',
      'Detalles ultra-rúnicos',
      'Texturas de alta resolución mágica',
      'Efectos arcanos avanzados'
    ],
    cons: [
      'Tamaño épico (24MB)',
      'Requiere más esencia (RAM)',
      'Invocación más lenta',
      'No ideal para reinos móviles'
    ],
    narrative: 'Para conquistas legendarias en mazmorras finales (Rango A+)'
  },
  portal2: {
    name: 'Portal Ágil',
    size: '8.2 MB',
    quality: 'Alta',
    polygons: '~30K',
    description: 'Portal optimizado para velocidad y agilidad en batallas',
    recommended: 'Reinos Móviles y Desktop',
    color: 'border-green-500',
    bgGradient: 'from-green-900 via-green-700 to-green-500',
    pros: [
      'Invocación rápida (8MB)',
      'Optimizado para hunters novatos',
      'Menor drenaje de esencia',
      'Mejor fluidez en combate'
    ],
    cons: [
      'Menos runas que Portal Legendario',
      'Texturas simplificadas'
    ],
    narrative: 'Para batallas rápidas en mazmorras iniciales (Rango E-D)'
  }
} as const;

export default function PortalSelectorPage() {
  // State management - minimal and clean
  const [selectedPortal, setSelectedPortal] = useState<'portal' | 'portal2'>('portal2');
  const [animationState, setAnimationState] = useState<'idle' | 'typing' | 'success' | 'error'>('idle');
  const [orbsEarned, setOrbsEarned] = useState(0);

  // Handlers - using useCallback to prevent recreation
  const handlePortalSelect = useCallback((portal: 'portal' | 'portal2') => {
    if (portal === selectedPortal) return;
    setSelectedPortal(portal);
    setOrbsEarned(prev => prev + 10);
  }, [selectedPortal]);

  const triggerAnimation = useCallback((state: 'typing' | 'success' | 'error') => {
    setAnimationState(state);
    setTimeout(() => setAnimationState('idle'), 3000);
  }, []);

  const handleSavePreference = useCallback(() => {
    localStorage.setItem('preferred-portal', selectedPortal);
    alert(`Portal ${PORTAL_CONFIGS[selectedPortal].name} guardado como predeterminado. ¡+20 Orbs!`);
    setOrbsEarned(prev => prev + 20);
  }, [selectedPortal]);

  const handleOpenTestPortal = useCallback(() => {
    window.open('/test-portal', '_blank');
  }, []);

  // Current config
  const currentConfig = PORTAL_CONFIGS[selectedPortal];

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900 to-black">
      {/* Animated background particles */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-purple-500 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-blob"></div>
        <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-yellow-500 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-blob animation-delay-2000"></div>
        <div className="absolute top-40 left-40 w-80 h-80 bg-pink-500 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-blob animation-delay-4000"></div>
      </div>

      <div className="container mx-auto px-4 py-8 relative z-10">
        {/* Header */}
        <div className="mb-8 text-center">
          <h1 className="text-5xl font-bold mb-2 bg-gradient-to-r from-yellow-400 via-amber-500 to-orange-600 bg-clip-text text-transparent animate-pulse">
            🌀 Selector de Portal Épico del Hunter
          </h1>
          <p className="text-gray-300 text-lg">
            Elige tu entrada a las Mazmorras del Conocimiento que se adapte a tu rango y reino.
          </p>
          <div className="mt-4 inline-flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-yellow-500/20 to-amber-500/20 rounded-full border border-yellow-500/50">
            <Sparkles className="w-5 h-5 text-yellow-400" />
            <span className="text-yellow-300 font-semibold">Orbs Ganados: {orbsEarned}</span>
            <span className="text-2xl">💎</span>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Portal View - SIMPLIFIED WITHOUT 3D */}
          <div className="space-y-6">
            <Card className="bg-gray-900/50 backdrop-blur-xl border-2 border-purple-500/50 shadow-2xl shadow-purple-500/25">
              <CardHeader className="border-b border-purple-500/30">
                <CardTitle className="flex items-center gap-2 text-2xl">
                  <Eye className="w-6 h-6 text-yellow-400" />
                  <span className="bg-gradient-to-r from-yellow-400 to-amber-500 bg-clip-text text-transparent">
                    Portal Actual: {currentConfig.name}
                  </span>
                </CardTitle>
              </CardHeader>
              <CardContent className="pt-6">
                {/* Portal Animation Container */}
                <div className={`aspect-square bg-gradient-to-br ${currentConfig.bgGradient} rounded-2xl overflow-hidden mb-6 flex items-center justify-center relative`}>
                  {/* Portal effect layers */}
                  <div className="absolute inset-0 bg-black/40"></div>
                  <div className="absolute inset-0 bg-gradient-to-t from-transparent via-purple-500/10 to-transparent animate-pulse"></div>
                  
                  {/* Central portal animation */}
                  <div className="relative">
                    <div className={`
                      w-40 h-40 rounded-full border-4
                      ${selectedPortal === 'portal' ? 'border-purple-400' : 'border-green-400'}
                      ${animationState === 'typing' ? 'animate-pulse border-blue-400' : ''}
                      ${animationState === 'success' ? 'animate-bounce border-green-400' : ''}
                      ${animationState === 'error' ? 'animate-ping border-red-400' : ''}
                      ${animationState === 'idle' ? 'animate-spin-slow' : ''}
                      shadow-2xl
                    `}>
                      <div className={`w-full h-full rounded-full bg-gradient-to-br ${currentConfig.bgGradient} opacity-60 blur-sm`} />
                    </div>
                    <div className="absolute inset-0 flex items-center justify-center">
                      {selectedPortal === 'portal' ? (
                        <Shield className="w-16 h-16 text-purple-300 animate-pulse" />
                      ) : (
                        <Sword className="w-16 h-16 text-green-300 animate-pulse" />
                      )}
                    </div>
                  </div>

                  {/* Floating particles */}
                  <div className="absolute inset-0">
                    {[...Array(6)].map((_, i) => (
                      <div
                        key={i}
                        className="absolute w-2 h-2 bg-yellow-400 rounded-full animate-float"
                        style={{
                          left: `${Math.random() * 100}%`,
                          top: `${Math.random() * 100}%`,
                          animationDelay: `${i * 0.5}s`,
                        }}
                      />
                    ))}
                  </div>
                </div>
                
                {/* Animation Controls */}
                <div className="grid grid-cols-2 gap-3">
                  <Button 
                    size="sm" 
                    className="bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white shadow-lg shadow-blue-500/25"
                    onClick={() => triggerAnimation('typing')}
                  >
                    <Zap className="w-4 h-4 mr-2" />
                    Ataque Rápido
                  </Button>
                  <Button 
                    size="sm" 
                    className="bg-gradient-to-r from-green-600 to-green-700 hover:from-green-700 hover:to-green-800 text-white shadow-lg shadow-green-500/25"
                    onClick={() => triggerAnimation('success')}
                  >
                    <Star className="w-4 h-4 mr-2" />
                    Victoria
                  </Button>
                  <Button 
                    size="sm" 
                    className="bg-gradient-to-r from-red-600 to-red-700 hover:from-red-700 hover:to-red-800 text-white shadow-lg shadow-red-500/25"
                    onClick={() => triggerAnimation('error')}
                  >
                    <Shield className="w-4 h-4 mr-2" />
                    Derrota
                  </Button>
                  <Button 
                    size="sm" 
                    className="bg-gradient-to-r from-purple-600 to-purple-700 hover:from-purple-700 hover:to-purple-800 text-white shadow-lg shadow-purple-500/25"
                    onClick={() => setAnimationState('idle')}
                  >
                    <Sparkles className="w-4 h-4 mr-2" />
                    Reinicio
                  </Button>
                </div>
              </CardContent>
            </Card>

            {/* Portal Info */}
            <Card className={`bg-gray-900/50 backdrop-blur-xl border-2 ${currentConfig.color} shadow-2xl`}>
              <CardHeader className={`border-b ${currentConfig.color.replace('border', 'border-b')}/30`}>
                <CardTitle className="text-2xl bg-gradient-to-r from-yellow-400 to-amber-500 bg-clip-text text-transparent">
                  {currentConfig.name}
                </CardTitle>
              </CardHeader>
              <CardContent className="pt-6">
                <div className="space-y-4">
                  <div className="flex justify-between items-center p-3 bg-gray-800/50 rounded-lg">
                    <span className="flex items-center gap-2 text-gray-300">
                      <HardDrive className="w-5 h-5 text-purple-400" />
                      <span className="font-medium">Poder:</span>
                    </span>
                    <Badge className="bg-purple-600/20 text-purple-300 border border-purple-500">
                      {currentConfig.size}
                    </Badge>
                  </div>
                  
                  <div className="flex justify-between items-center p-3 bg-gray-800/50 rounded-lg">
                    <span className="flex items-center gap-2 text-gray-300">
                      <Monitor className="w-5 h-5 text-blue-400" />
                      <span className="font-medium">Gloria:</span>
                    </span>
                    <Badge className="bg-blue-600/20 text-blue-300 border border-blue-500">
                      {currentConfig.quality}
                    </Badge>
                  </div>
                  
                  <div className="flex justify-between items-center p-3 bg-gray-800/50 rounded-lg">
                    <span className="flex items-center gap-2 text-gray-300">
                      <Settings className="w-5 h-5 text-green-400" />
                      <span className="font-medium">Runas:</span>
                    </span>
                    <Badge className="bg-green-600/20 text-green-300 border border-green-500">
                      {currentConfig.polygons}
                    </Badge>
                  </div>
                  
                  <div className="flex justify-between items-center p-3 bg-gray-800/50 rounded-lg">
                    <span className="flex items-center gap-2 text-gray-300">
                      <Smartphone className="w-5 h-5 text-yellow-400" />
                      <span className="font-medium">Reino:</span>
                    </span>
                    <Badge className="bg-yellow-600/20 text-yellow-300 border border-yellow-500">
                      {currentConfig.recommended}
                    </Badge>
                  </div>
                </div>
                
                <p className="mt-6 text-gray-300 text-sm leading-relaxed p-4 bg-gray-800/30 rounded-lg border border-gray-700/50">
                  {currentConfig.description}
                </p>
              </CardContent>
            </Card>
          </div>

          {/* Portal Selector */}
          <div className="space-y-6">
            <Card className="bg-gray-900/50 backdrop-blur-xl border-2 border-purple-500/50 shadow-2xl shadow-purple-500/25">
              <CardHeader className="border-b border-purple-500/30">
                <CardTitle className="flex items-center gap-2 text-2xl">
                  <Download className="w-6 h-6 text-yellow-400" />
                  <span className="bg-gradient-to-r from-yellow-400 to-amber-500 bg-clip-text text-transparent">
                    Portales Épicos Disponibles
                  </span>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4 pt-6">
                {Object.entries(PORTAL_CONFIGS).map(([key, config]) => (
                  <div 
                    key={key}
                    className={`p-5 border-2 rounded-xl cursor-pointer transition-all transform hover:scale-[1.02] ${
                      selectedPortal === key 
                        ? `${config.color} bg-gradient-to-br ${config.bgGradient.replace('from-', 'from-').replace('via-', 'via-').replace('to-', 'to-')}/10 shadow-xl` 
                        : 'border-gray-600 hover:border-gray-400 bg-gray-800/30'
                    }`}
                    onClick={() => handlePortalSelect(key as 'portal' | 'portal2')}
                  >
                    <div className="flex items-center justify-between mb-3">
                      <h3 className="font-bold text-xl bg-gradient-to-r from-yellow-400 to-amber-500 bg-clip-text text-transparent">
                        {config.name}
                      </h3>
                      <div className="flex items-center gap-2">
                        <Badge className="bg-purple-600/20 text-purple-300 border border-purple-500">
                          {config.size}
                        </Badge>
                        {selectedPortal === key && (
                          <Badge className="bg-gradient-to-r from-yellow-500 to-amber-500 text-black font-bold animate-pulse">
                            <Star className="w-3 h-3 mr-1" />
                            Activo
                          </Badge>
                        )}
                      </div>
                    </div>
                    
                    <p className="text-gray-300 mb-4 text-sm">{config.description}</p>
                    
                    {/* Pros and Cons */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div className="bg-green-900/20 p-3 rounded-lg border border-green-500/30">
                        <div className="font-semibold text-green-400 mb-2 flex items-center gap-1">
                          <Sparkles className="w-4 h-4" />
                          Bendiciones:
                        </div>
                        <ul className="space-y-1">
                          {config.pros.map((pro, idx) => (
                            <li key={idx} className="text-green-300 text-xs flex items-start gap-1">
                              <span className="text-green-500 mt-1">•</span>
                              <span>{pro}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                      
                      <div className="bg-orange-900/20 p-3 rounded-lg border border-orange-500/30">
                        <div className="font-semibold text-orange-400 mb-2 flex items-center gap-1">
                          <Shield className="w-4 h-4" />
                          Desafíos:
                        </div>
                        <ul className="space-y-1">
                          {config.cons.map((con, idx) => (
                            <li key={idx} className="text-orange-300 text-xs flex items-start gap-1">
                              <span className="text-orange-500 mt-1">•</span>
                              <span>{con}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    </div>
                    
                    <div className="mt-3 p-2 bg-purple-900/20 rounded-lg border border-purple-500/30">
                      <p className="text-xs text-purple-300 italic">{config.narrative}</p>
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>

            {/* Recommendations */}
            <Alert className="bg-gradient-to-br from-blue-900/30 to-purple-900/30 backdrop-blur-xl border-2 border-blue-500/50">
              <Monitor className="h-5 w-5 text-yellow-400" />
              <AlertTitle className="text-xl bg-gradient-to-r from-yellow-400 to-amber-500 bg-clip-text text-transparent">
                Runas de Sabiduría
              </AlertTitle>
              <AlertDescription className="space-y-3 mt-3">
                <div className="flex items-center gap-3 p-2 bg-gray-800/50 rounded-lg">
                  <Smartphone className="w-5 h-5 text-green-400" />
                  <span className="text-gray-300">
                    <strong className="text-green-400">Reinos Móviles:</strong> Usa Portal Ágil (8MB)
                  </span>
                </div>
                <div className="flex items-center gap-3 p-2 bg-gray-800/50 rounded-lg">
                  <Monitor className="w-5 h-5 text-purple-400" />
                  <span className="text-gray-300">
                    <strong className="text-purple-400">Reinos Desktop:</strong> Portal Legendario (24MB)
                  </span>
                </div>
                <div className="flex items-center gap-3 p-2 bg-gray-800/50 rounded-lg">
                  <Clock className="w-5 h-5 text-yellow-400" />
                  <span className="text-gray-300">
                    <strong className="text-yellow-400">Conexión Débil:</strong> Portal Ágil invoca 3x más rápido
                  </span>
                </div>
              </AlertDescription>
            </Alert>

            {/* Settings */}
            <Card className="bg-gray-900/50 backdrop-blur-xl border-2 border-purple-500/50 shadow-2xl shadow-purple-500/25">
              <CardHeader className="border-b border-purple-500/30">
                <CardTitle className="text-2xl bg-gradient-to-r from-yellow-400 to-amber-500 bg-clip-text text-transparent">
                  Aplicar Hechizo de Configuración
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4 pt-6">
                <Alert className="bg-gradient-to-br from-purple-900/40 to-pink-900/40 border border-purple-500/50">
                  <Settings className="h-5 w-5 text-yellow-400" />
                  <AlertTitle className="text-yellow-300">Portal Invocado</AlertTitle>
                  <AlertDescription className="text-gray-300 mt-2">
                    {currentConfig.name} será tu arma en las mazmorras de login.
                  </AlertDescription>
                </Alert>
                
                <div className="space-y-3">
                  <Button 
                    className="w-full bg-gradient-to-r from-yellow-500 via-amber-500 to-orange-500 hover:from-yellow-600 hover:via-amber-600 hover:to-orange-600 text-black font-bold shadow-xl shadow-yellow-500/25 transform transition hover:scale-105" 
                    onClick={handleSavePreference}
                  >
                    <Star className="w-5 h-5 mr-2" />
                    Establecer como Arma Predeterminada
                  </Button>
                  
                  <Button 
                    variant="outline" 
                    className="w-full border-2 border-purple-500 text-purple-300 hover:bg-purple-500/20 shadow-lg shadow-purple-500/25 transform transition hover:scale-105"
                    onClick={handleOpenTestPortal}
                  >
                    <Eye className="w-5 h-5 mr-2" />
                    Abrir Prueba de Mazmorra
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>

        {/* Performance Stats Table */}
        <Card className="mt-8 bg-gray-900/50 backdrop-blur-xl border-2 border-purple-500/50 shadow-2xl shadow-purple-500/25">
          <CardHeader className="border-b border-purple-500/30">
            <CardTitle className="flex items-center gap-2 text-2xl">
              <Zap className="w-6 h-6 text-yellow-400" />
              <span className="bg-gradient-to-r from-yellow-400 to-amber-500 bg-clip-text text-transparent">
                Comparativa de Poderes Épicos
              </span>
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-6">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b-2 border-purple-500/50">
                    <th className="text-left p-3 text-yellow-400">Runa</th>
                    <th className="text-center p-3 text-purple-400">Portal Legendario ⚔️</th>
                    <th className="text-center p-3 text-green-400">Portal Ágil 🏹</th>
                    <th className="text-center p-3 text-blue-400">Narrativa 🌟</th>
                  </tr>
                </thead>
                <tbody>
                  <tr className="border-b border-gray-700/50 hover:bg-gray-800/30">
                    <td className="p-3 text-gray-300 font-medium">Tiempo de Invocación ⏳</td>
                    <td className="text-center p-3 text-orange-400">~3-5 segundos</td>
                    <td className="text-center p-3 text-green-400 font-semibold">~1-2 segundos</td>
                    <td className="text-center p-3 text-gray-400 text-xs">Rápido para novatos</td>
                  </tr>
                  <tr className="border-b border-gray-700/50 hover:bg-gray-800/30">
                    <td className="p-3 text-gray-300 font-medium">Drenaje de Esencia 💎</td>
                    <td className="text-center p-3 text-orange-400">~150-200 MB</td>
                    <td className="text-center p-3 text-green-400 font-semibold">~50-80 MB</td>
                    <td className="text-center p-3 text-gray-400 text-xs">Eficiente móvil</td>
                  </tr>
                  <tr className="border-b border-gray-700/50 hover:bg-gray-800/30">
                    <td className="p-3 text-gray-300 font-medium">Fluidez en Combate 🔥</td>
                    <td className="text-center p-3 text-orange-400">~20-30 FPS</td>
                    <td className="text-center p-3 text-green-400 font-semibold">~45-60 FPS</td>
                    <td className="text-center p-3 text-gray-400 text-xs">Alta para épicas</td>
                  </tr>
                  <tr className="border-b border-gray-700/50 hover:bg-gray-800/30">
                    <td className="p-3 text-gray-300 font-medium">Gloria Visual 🎨</td>
                    <td className="text-center p-3 text-green-400 font-semibold">Ultra Alta</td>
                    <td className="text-center p-3 text-yellow-400">Alta</td>
                    <td className="text-center p-3 text-gray-400 text-xs">Legendaria A+</td>
                  </tr>
                  <tr className="hover:bg-gray-800/30">
                    <td className="p-3 text-gray-300 font-medium">Compatibilidad 📱</td>
                    <td className="text-center p-3 text-orange-400">Desktop</td>
                    <td className="text-center p-3 text-green-400 font-semibold">Universal</td>
                    <td className="text-center p-3 text-gray-400 text-xs">Para todos</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      </div>

      <style jsx>{`
        @keyframes spin-slow {
          from {
            transform: rotate(0deg);
          }
          to {
            transform: rotate(360deg);
          }
        }
        
        @keyframes float {
          0%, 100% {
            transform: translateY(0px);
          }
          50% {
            transform: translateY(-20px);
          }
        }
        
        @keyframes blob {
          0%, 100% {
            transform: translate(0px, 0px) scale(1);
          }
          33% {
            transform: translate(30px, -50px) scale(1.1);
          }
          66% {
            transform: translate(-20px, 20px) scale(0.9);
          }
        }
        
        .animate-spin-slow {
          animation: spin-slow 3s linear infinite;
        }
        
        .animate-float {
          animation: float 3s ease-in-out infinite;
        }
        
        .animate-blob {
          animation: blob 7s infinite;
        }
        
        .animation-delay-2000 {
          animation-delay: 2s;
        }
        
        .animation-delay-4000 {
          animation-delay: 4s;
        }
      `}</style>
    </div>
  );
}