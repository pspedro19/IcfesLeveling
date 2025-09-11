'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';

// 🎮 HUB CENTRAL - Torre del Ascenso ICFES
export default function HubCentral() {
  const router = useRouter();
  const [hunterLevel] = useState(15);
  const [currentRank] = useState('C');
  const [experience] = useState(1500);
  const [experienceToNext] = useState(2000);

  // Estado de progreso simulado
  const [subjectsProgress] = useState({
    matematicas: { level: 45, mastery: 0.65, unlocked: true },
    fisica: { level: 30, mastery: 0.45, unlocked: true },
    quimica: { level: 25, mastery: 0.40, unlocked: false },
    biologia: { level: 35, mastery: 0.55, unlocked: false },
    espanol: { level: 50, mastery: 0.75, unlocked: true }
  });

  const zones = [
    {
      id: 'portal-despertar',
      name: 'Portal del Despertar',
      description: 'Diagnóstico inicial ICFES - Descubre tu potencial',
      icon: '🌟',
      color: '#FFD700',
      status: 'available',
      level: 'Obligatorio',
      route: '/portal-despertar'
    },
    {
      id: 'biblioteca',
      name: 'Biblioteca de los Ancestros',
      description: 'Videos y recursos de estudio por competencia',
      icon: '📚',
      color: '#4ECDC4',
      status: hunterLevel >= 5 ? 'available' : 'locked',
      level: 'Req: Nivel 5',
      route: '/biblioteca'
    },
    {
      id: 'arena',
      name: 'Arena del Conocimiento',
      description: 'Práctica intensiva con preguntas tipo ICFES',
      icon: '⚔️',
      color: '#FF6B35',
      status: hunterLevel >= 10 ? 'available' : 'locked',
      level: 'Req: Nivel 10',
      route: '/arena'
    },
    {
      id: 'santuario',
      name: 'Santuario de la Sabiduría',
      description: 'Reportes PDF y consolidación de conocimiento',
      icon: '🏛️',
      color: '#96CEB4',
      status: hunterLevel >= 20 ? 'available' : 'locked',
      level: 'Req: Nivel 20',
      route: '/santuario'
    },
    {
      id: 'mazmorra',
      name: 'Mazmorra del Tiempo',
      description: 'Simulacros cronometrados bajo presión',
      icon: '⏱️',
      color: '#8B5CF6',
      status: 'special',
      level: 'Evento Especial',
      route: '/mazmorra'
    },
    {
      id: 'torre-monarcas',
      name: 'Torre de los Monarcas',
      description: 'Desafíos avanzados para Rango A/S',
      icon: '👑',
      color: '#F59E0B',
      status: currentRank >= 'A' ? 'available' : 'locked',
      level: 'Solo Rango A/S',
      route: '/torre-monarcas'
    }
  ];

  const ranks = {
    'E': { name: 'Aspirante a Cazador', color: '#FFEAA7', icon: '🔰' },
    'D': { name: 'Cazador Novato', color: '#96CEB4', icon: '⚔️' },
    'C': { name: 'Cazador Competente', color: '#45B7D1', icon: '🛡️' },
    'B': { name: 'Cazador Avanzado', color: '#4ECDC4', icon: '⚡' },
    'A': { name: 'Cazador Elite', color: '#FF6B35', icon: '🔥' },
    'S': { name: 'Monarca del Conocimiento', color: '#FFD700', icon: '👑' }
  };

  const handleZoneClick = (zone: any) => {
    if (zone.status === 'available') {
      router.push(zone.route);
    } else if (zone.status === 'locked') {
      alert(`🔒 Esta zona está bloqueada. ${zone.level}`);
    } else if (zone.status === 'special') {
      alert(`⭐ Evento especial próximamente!`);
    }
  };

  const handleDashboardClick = () => {
    router.push('/student-dashboard');
  };

  const progressPercentage = (experience / experienceToNext) * 100;

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 text-white">
      {/* Header con Torre Central */}
      <div className="relative overflow-hidden bg-gradient-to-b from-black/30 to-transparent">
        <div className="container mx-auto px-4 py-8">
          <div className="text-center">
            <div className="text-8xl mb-4">🏰</div>
            <h1 className="text-5xl font-bold mb-2 bg-gradient-to-r from-gold-400 to-purple-400 bg-clip-text text-transparent">
              TORRE DEL ASCENSO ICFES
            </h1>
            <p className="text-xl text-gray-300 mb-8">
              Hub Central - El camino hacia la maestría académica
            </p>

            {/* Panel del Cazador */}
            <div className="bg-black/40 backdrop-blur-sm rounded-xl p-6 max-w-2xl mx-auto border border-purple-500/30">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center space-x-4">
                  <div className="text-4xl">{ranks[currentRank as keyof typeof ranks]?.icon}</div>
                  <div className="text-left">
                    <div className="text-2xl font-bold" style={{color: ranks[currentRank as keyof typeof ranks]?.color}}>
                      Rango {currentRank} - Nivel {hunterLevel}
                    </div>
                    <div className="text-gray-400">{ranks[currentRank as keyof typeof ranks]?.name}</div>
                  </div>
                </div>
                <button
                  onClick={handleDashboardClick}
                  className="px-4 py-2 bg-purple-600 hover:bg-purple-700 rounded-lg font-bold transition-colors"
                >
                  📊 Dashboard
                </button>
              </div>

              {/* Barra de Experiencia */}
              <div className="mb-4">
                <div className="flex justify-between text-sm mb-1">
                  <span>Experiencia</span>
                  <span>{experience} / {experienceToNext} XP</span>
                </div>
                <div className="w-full bg-gray-700 rounded-full h-3">
                  <div 
                    className="bg-gradient-to-r from-gold-400 to-yellow-500 h-3 rounded-full transition-all duration-300"
                    style={{width: `${progressPercentage}%`}}
                  ></div>
                </div>
              </div>

              {/* Progreso por Materias - Mini Torres */}
              <div className="grid grid-cols-5 gap-2">
                {Object.entries(subjectsProgress).map(([subject, progress]) => {
                  const icons = {
                    matematicas: '🔢',
                    fisica: '⚛️', 
                    quimica: '🧪',
                    biologia: '🧬',
                    espanol: '📚'
                  };
                  
                  return (
                    <div key={subject} className="text-center">
                      <div className={`text-2xl mb-1 ${progress.unlocked ? '' : 'grayscale opacity-50'}`}>
                        {icons[subject as keyof typeof icons]}
                      </div>
                      <div className="text-xs font-bold">{Math.round(progress.mastery * 100)}%</div>
                      <div className="w-full bg-gray-700 rounded-full h-1">
                        <div 
                          className={`h-1 rounded-full transition-all duration-300 ${
                            progress.unlocked 
                              ? 'bg-gradient-to-r from-green-400 to-blue-500' 
                              : 'bg-gray-500'
                          }`}
                          style={{width: `${progress.mastery * 100}%`}}
                        ></div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Grid de Zonas */}
      <div className="container mx-auto px-4 py-12">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold mb-4 text-gold-400">
            🗺️ Zonas de Entrenamiento
          </h2>
          <p className="text-lg text-gray-300">
            Cada zona te desafiará de manera diferente. ¡Escoge sabiamente tu próximo destino!
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 max-w-7xl mx-auto">
          {zones.map((zone) => {
            const isLocked = zone.status === 'locked';
            const isSpecial = zone.status === 'special';
            
            return (
              <div
                key={zone.id}
                className={`group relative rounded-xl p-6 border transition-all duration-300 cursor-pointer ${
                  isLocked 
                    ? 'bg-gray-800/40 border-gray-600/30 opacity-60' 
                    : isSpecial
                    ? 'bg-gradient-to-br from-purple-800/40 to-pink-800/40 border-purple-500/50 hover:border-purple-400/70'
                    : 'bg-black/40 backdrop-blur-sm border-purple-500/30 hover:border-gold-400/50 hover:transform hover:scale-105'
                }`}
                onClick={() => handleZoneClick(zone)}
                style={{boxShadow: !isLocked ? `0 0 20px ${zone.color}20` : undefined}}
              >
                {/* Lock Overlay */}
                {isLocked && (
                  <div className="absolute inset-0 flex items-center justify-center bg-black/50 rounded-xl">
                    <div className="text-center">
                      <div className="text-4xl mb-2">🔒</div>
                      <div className="text-sm font-bold">BLOQUEADO</div>
                    </div>
                  </div>
                )}

                {/* Special Glow */}
                {isSpecial && (
                  <div className="absolute inset-0 rounded-xl bg-gradient-to-r from-purple-500/20 via-pink-500/20 to-purple-500/20 animate-pulse"></div>
                )}

                {/* Content */}
                <div className="relative z-10">
                  <div className="text-center mb-4">
                    <div className="text-5xl mb-2">{zone.icon}</div>
                    <h3 className="text-xl font-bold mb-2" style={{color: zone.color}}>
                      {zone.name}
                    </h3>
                    <div className="text-sm text-gray-400 mb-2">
                      {zone.level}
                    </div>
                  </div>

                  <p className="text-sm text-gray-300 text-center mb-4 leading-relaxed">
                    {zone.description}
                  </p>

                  <button 
                    className={`w-full py-2 rounded-lg font-bold text-sm transition-all duration-300 ${
                      isLocked
                        ? 'bg-gray-600 cursor-not-allowed'
                        : isSpecial
                        ? 'bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700'
                        : 'bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700'
                    }`}
                    disabled={isLocked}
                  >
                    {isLocked ? '🔒 Bloqueado' : isSpecial ? '⭐ Próximamente' : '🚀 Entrar'}
                  </button>
                </div>
              </div>
            );
          })}
        </div>

        {/* Call to Action */}
        <div className="mt-16 text-center">
          <div className="bg-gradient-to-r from-gold-500/20 to-purple-500/20 rounded-xl p-8 max-w-4xl mx-auto border border-gold-400/30">
            <h3 className="text-3xl font-bold mb-4 text-gold-400">
              🎯 ¿Listo para tu próximo desafío?
            </h3>
            <p className="text-lg text-gray-300 mb-6">
              Cada zona conquistada te acerca más a convertirte en un verdadero Monarca del Conocimiento ICFES.
            </p>
            <div className="flex flex-wrap justify-center gap-4">
              <button
                onClick={() => router.push('/portal-despertar')}
                className="px-8 py-3 bg-gradient-to-r from-gold-500 to-yellow-500 hover:from-gold-600 hover:to-yellow-600 rounded-lg font-bold text-black transition-all duration-300 hover:shadow-lg"
              >
                🌟 Comenzar Despertar
              </button>
              <button
                onClick={() => router.push('/diagnostic-test')}
                className="px-8 py-3 bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 rounded-lg font-bold transition-all duration-300 hover:shadow-lg"
              >
                📝 Test Rápido
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}