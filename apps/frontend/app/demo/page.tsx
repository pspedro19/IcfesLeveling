'use client';

import React, { useState } from 'react';
import { AudioProvider } from '../components/PortalLogin/AudioEngine';
import DamageNumbers from '../components/BattleSystem/DamageNumbers';
import ComboChain from '../components/BattleSystem/ComboChain';
import CrystalSave from '../components/ui/CrystalSave';
import QuestTracker from '../components/DailyQuests/QuestTracker';
import EpicNotification, { useNotifications } from '../components/ui/EpicNotification';
import { Trophy, Sword, Star, Gift } from 'lucide-react';

export default function DemoPage() {
  const [combo, setCombo] = useState(0);
  const [isComboActive, setIsComboActive] = useState(true);
  const [damage, setDamage] = useState<{value: number, type: string} | null>(null);
  const { currentNotification, showNotification, dismissNotification } = useNotifications();

  const handleDamageTest = (type: string) => {
    const damageValue = type === 'critical' ? 999 : type === 'heal' ? 150 : 250;
    setDamage({ value: damageValue, type });
    setTimeout(() => setDamage(null), 100);
  };

  const handleComboIncrease = () => {
    if (isComboActive) {
      setCombo(prev => Math.min(prev + 1, 10));
    }
  };

  const handleComboBreak = () => {
    setIsComboActive(false);
    setCombo(0);
    setTimeout(() => setIsComboActive(true), 1000);
  };

  const showTestNotification = (type: string) => {
    const notifications = {
      achievement: {
        type: 'achievement' as const,
        title: '¡Logro Desbloqueado!',
        message: 'Has completado "Maestro de las Matemáticas"',
        icon: <Trophy className="w-6 h-6" />,
        visual: 'sparkle' as const,
        duration: 5000
      },
      level_up: {
        type: 'level_up' as const,
        title: '¡LEVEL UP!',
        message: 'Has alcanzado el nivel 25',
        visual: 'glow' as const,
        duration: 6000
      },
      quest: {
        type: 'quest_complete' as const,
        title: 'Misión Completada',
        message: 'Has derrotado 10 enemigos',
        icon: <Sword className="w-6 h-6" />,
        visual: 'shake' as const,
        duration: 4000
      },
      loot: {
        type: 'loot' as const,
        title: '¡Recompensa Épica!',
        message: 'Has obtenido: Cristal de Sabiduría x3',
        icon: <Gift className="w-6 h-6" />,
        visual: 'sparkle' as const,
        duration: 5000,
        actions: [
          {
            label: 'Ver Inventario',
            onClick: () => console.log('Opening inventory...')
          }
        ]
      }
    };

    showNotification(notifications[type as keyof typeof notifications]);
  };

  return (
    <AudioProvider>
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900 to-indigo-900 p-8">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-5xl font-bold text-white mb-4 font-cinzel">
            IcfesLeveling - Demo de Componentes
          </h1>
          <p className="text-xl text-purple-300 font-orbitron">
            Experiencia épica estilo Solo Leveling
          </p>
        </div>

        {/* Component Grid */}
        <div className="max-w-7xl mx-auto grid lg:grid-cols-2 gap-8">
          {/* Damage Numbers Demo */}
          <div className="glass-panel rounded-lg p-6">
            <h2 className="text-2xl font-bold text-white mb-4">Sistema de Daño</h2>
            <div className="flex gap-4 flex-wrap">
              <button
                onClick={() => handleDamageTest('damage')}
                className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors"
              >
                Daño Normal (250)
              </button>
              <button
                onClick={() => handleDamageTest('critical')}
                className="px-4 py-2 bg-yellow-600 hover:bg-yellow-700 text-white rounded-lg transition-colors"
              >
                Crítico (999)
              </button>
              <button
                onClick={() => handleDamageTest('heal')}
                className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-colors"
              >
                Curación (150)
              </button>
              <button
                onClick={() => handleDamageTest('miss')}
                className="px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-lg transition-colors"
              >
                Miss
              </button>
            </div>
            <DamageNumbers 
              damage={damage?.value} 
              type={damage?.type as any}
              position={{ x: 50, y: 50 }}
            />
          </div>

          {/* Combo Chain Demo */}
          <div className="glass-panel rounded-lg p-6">
            <h2 className="text-2xl font-bold text-white mb-4">Sistema de Combo</h2>
            <div className="flex gap-4 mb-8">
              <button
                onClick={handleComboIncrease}
                className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition-colors"
              >
                Aumentar Combo
              </button>
              <button
                onClick={handleComboBreak}
                className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors"
              >
                Romper Combo
              </button>
            </div>
            <ComboChain 
              combo={combo} 
              isActive={isComboActive}
              onComboBreak={() => console.log('Combo broken!')}
            />
          </div>

          {/* Notifications Demo */}
          <div className="glass-panel rounded-lg p-6">
            <h2 className="text-2xl font-bold text-white mb-4">Notificaciones Épicas</h2>
            <div className="grid grid-cols-2 gap-4">
              <button
                onClick={() => showTestNotification('achievement')}
                className="px-4 py-2 bg-yellow-600 hover:bg-yellow-700 text-white rounded-lg transition-colors"
              >
                Logro
              </button>
              <button
                onClick={() => showTestNotification('level_up')}
                className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition-colors"
              >
                Level Up
              </button>
              <button
                onClick={() => showTestNotification('quest')}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
              >
                Misión
              </button>
              <button
                onClick={() => showTestNotification('loot')}
                className="px-4 py-2 bg-orange-600 hover:bg-orange-700 text-white rounded-lg transition-colors"
              >
                Loot
              </button>
            </div>
          </div>

          {/* Component Status */}
          <div className="glass-panel rounded-lg p-6">
            <h2 className="text-2xl font-bold text-white mb-4">Componentes Activos</h2>
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
                <span className="text-green-300">Crystal Save System</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
                <span className="text-green-300">Quest Tracker</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
                <span className="text-green-300">Audio Engine</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
                <span className="text-green-300">Portal Animation</span>
              </div>
            </div>
          </div>
        </div>

        {/* Fixed Components */}
        <CrystalSave 
          isOnline={true}
          queuedSaves={2}
          onManualSave={() => console.log('Manual save triggered')}
          onSyncQueue={() => console.log('Sync queue triggered')}
        />
        
        <QuestTracker 
          streakDays={47}
          freezeShields={2}
          onUseFreeze={() => console.log('Freeze shield used')}
        />

        <EpicNotification 
          notification={currentNotification}
          onDismiss={dismissNotification}
        />
      </div>
    </AudioProvider>
  );
}