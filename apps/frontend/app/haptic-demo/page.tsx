'use client';

import React, { useState } from 'react';
import HapticButton from '../components/ui/HapticButton';
import { useHapticFeedback } from '../hooks/useHapticFeedback';
import { 
  Vibrate, 
  Zap, 
  Trophy, 
  Sword, 
  Heart,
  Sparkles,
  AlertCircle,
  CheckCircle,
  Smartphone
} from 'lucide-react';

export default function HapticDemoPage() {
  const haptics = useHapticFeedback();
  const [lastAction, setLastAction] = useState('');
  
  const handleAction = (action: string, hapticFn: () => void) => {
    hapticFn();
    setLastAction(action);
  };
  
  const hapticDemos = [
    {
      category: 'Interacciones UI',
      items: [
        {
          name: 'Toque Simple',
          icon: <Smartphone className="w-5 h-5" />,
          action: () => handleAction('Toque Simple', haptics.buttonPress),
          variant: 'primary' as const
        },
        {
          name: 'Toggle Switch',
          icon: <Zap className="w-5 h-5" />,
          action: () => handleAction('Toggle Switch', haptics.toggleSwitch),
          variant: 'secondary' as const
        },
        {
          name: 'Deslizar',
          icon: <Vibrate className="w-5 h-5" />,
          action: () => handleAction('Gesto de Deslizar', haptics.swipeGesture),
          variant: 'ghost' as const
        }
      ]
    },
    {
      category: 'Eventos del Juego',
      items: [
        {
          name: 'Atacar',
          icon: <Sword className="w-5 h-5" />,
          action: () => handleAction('Ataque Normal', haptics.attack),
          variant: 'danger' as const
        },
        {
          name: 'Golpe Crítico',
          icon: <Zap className="w-5 h-5" />,
          action: () => handleAction('¡Golpe Crítico!', haptics.criticalHit),
          variant: 'danger' as const,
          hapticPattern: 'critical' as const
        },
        {
          name: 'Recibir Daño',
          icon: <Heart className="w-5 h-5" />,
          action: () => handleAction('Daño Recibido', haptics.takeDamage),
          variant: 'danger' as const,
          hapticPattern: 'damage' as const
        }
      ]
    },
    {
      category: 'Logros y Recompensas',
      items: [
        {
          name: 'Subir Nivel',
          icon: <Trophy className="w-5 h-5" />,
          action: () => handleAction('¡Subiste de Nivel!', haptics.levelUp),
          variant: 'success' as const,
          hapticPattern: 'levelUp' as const
        },
        {
          name: 'Misión Completa',
          icon: <CheckCircle className="w-5 h-5" />,
          action: () => handleAction('Misión Completada', haptics.questComplete),
          variant: 'success' as const,
          hapticPattern: 'questComplete' as const
        },
        {
          name: 'Momento Épico',
          icon: <Sparkles className="w-5 h-5" />,
          action: () => handleAction('¡MOMENTO ÉPICO!', haptics.epicMoment),
          variant: 'primary' as const,
          hapticPattern: 'epic' as const
        }
      ]
    },
    {
      category: 'Notificaciones',
      items: [
        {
          name: 'Éxito',
          icon: <CheckCircle className="w-5 h-5" />,
          action: () => handleAction('Notificación de Éxito', () => haptics.notification('success')),
          variant: 'success' as const,
          hapticPattern: 'success' as const
        },
        {
          name: 'Advertencia',
          icon: <AlertCircle className="w-5 h-5" />,
          action: () => handleAction('Notificación de Advertencia', () => haptics.notification('warning')),
          variant: 'secondary' as const,
          hapticPattern: 'warning' as const
        },
        {
          name: 'Error',
          icon: <AlertCircle className="w-5 h-5" />,
          action: () => handleAction('Notificación de Error', () => haptics.notification('error')),
          variant: 'danger' as const,
          hapticPattern: 'error' as const
        }
      ]
    }
  ];
  
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900 
      to-gray-900 p-4">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-20 h-20 
            bg-purple-600 rounded-full mb-4">
            <Vibrate className="w-10 h-10 text-white" />
          </div>
          
          <h1 className="text-4xl font-bold text-white mb-4 font-cinzel">
            Sistema de Haptic Feedback
          </h1>
          
          <p className="text-gray-300 max-w-2xl mx-auto mb-4">
            Retroalimentación táctil que hace que cada interacción se sienta más real.
            Prueba los diferentes tipos de vibración en dispositivos móviles.
          </p>
          
          {!haptics.isSupported && (
            <div className="bg-yellow-900/30 border border-yellow-500/50 rounded-lg p-4 
              max-w-md mx-auto">
              <p className="text-yellow-300 text-sm">
                ⚠️ La vibración no está soportada en este dispositivo o navegador
              </p>
            </div>
          )}
        </div>
        
        {/* Last Action Display */}
        {lastAction && (
          <div className="bg-gray-900/80 rounded-lg p-4 mb-8 text-center">
            <p className="text-gray-400 text-sm">Última acción:</p>
            <p className="text-xl text-white font-semibold">{lastAction}</p>
          </div>
        )}
        
        {/* Haptic Demos */}
        <div className="space-y-8">
          {hapticDemos.map((category, categoryIndex) => (
            <div key={categoryIndex}>
              <h2 className="text-xl font-semibold text-white mb-4">
                {category.category}
              </h2>
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {category.items.map((item, itemIndex) => (
                  <HapticButton
                    key={itemIndex}
                    variant={item.variant}
                    size="lg"
                    hapticPattern={item.hapticPattern}
                    onClick={item.action}
                    fullWidth
                  >
                    {item.icon}
                    {item.name}
                  </HapticButton>
                ))}
              </div>
            </div>
          ))}
        </div>
        
        {/* Custom Pattern Demo */}
        <div className="mt-12 bg-gray-900/80 rounded-lg p-6">
          <h3 className="text-xl font-semibold text-white mb-4">
            Patrón Personalizado
          </h3>
          
          <p className="text-gray-300 mb-4">
            Crea tu propio patrón de vibración:
          </p>
          
          <div className="flex flex-wrap gap-2 mb-4">
            {[50, 100, 200, 300, 500].map(duration => (
              <button
                key={duration}
                onClick={() => haptics.vibrate(duration)}
                className="bg-gray-700 hover:bg-gray-600 text-white px-4 py-2 
                  rounded-lg transition-all"
              >
                {duration}ms
              </button>
            ))}
          </div>
          
          <button
            onClick={() => haptics.compose([100, 50, 100, 50, 200, 100, 300], 0.8)}
            className="bg-gradient-to-r from-purple-600 to-purple-700 
              hover:from-purple-700 hover:to-purple-800 text-white font-bold 
              px-6 py-3 rounded-lg transition-all"
          >
            Reproducir Patrón Complejo
          </button>
        </div>
        
        {/* Instructions */}
        <div className="mt-8 bg-gray-900/80 rounded-lg p-6 text-center">
          <h3 className="text-xl font-semibold text-white mb-4">
            Instrucciones
          </h3>
          
          <div className="space-y-2 text-gray-300 max-w-2xl mx-auto">
            <p>
              📱 Esta función solo está disponible en dispositivos móviles
            </p>
            <p>
              🔊 Asegúrate de que el modo vibración esté activado
            </p>
            <p>
              🎮 Cada tipo de interacción tiene un patrón único de vibración
            </p>
            <p>
              ⚡ Los patrones más largos indican eventos más importantes
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}