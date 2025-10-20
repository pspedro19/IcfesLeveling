'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { motion } from 'framer-motion';
import { 
  BookOpen, 
  Sword, 
  Crown, 
  Shield, 
  Trophy, 
  Zap, 
  Star,
  Lock,
  Play,
  Target,
  Clock,
  Award
} from 'lucide-react';
import MainNavigation from '../components/Navigation/MainNavigation';

interface User {
  id: string;
  username: string;
  level: number;
  rank: string;
  experience: number;
  hp: number;
  mp: number;
}

interface GameArea {
  id: string;
  title: string;
  subtitle: string;
  description: string;
  icon: any;
  path: string;
  levelRequired: number;
  rankRequired?: string[];
  isSpecialEvent?: boolean;
  comingSoon?: boolean;
  gradient: string;
  borderColor: string;
  rewards: string[];
}

export default function HubCentralPage() {
  const router = useRouter();
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [hoveredArea, setHoveredArea] = useState<string | null>(null);

  useEffect(() => {
    // Load user data
    const userData = localStorage.getItem('currentUser') || localStorage.getItem('user');
    if (userData) {
      try {
        const user = JSON.parse(userData);
        setCurrentUser({
          id: user.id,
          username: user.username,
          level: user.level || 1,
          rank: user.rank || 'E',
          experience: user.experience || 0,
          hp: user.hp || 100,
          mp: user.mp || 50
        });
      } catch (error) {
        console.error('Error loading user data:', error);
      }
    }
  }, []);

  const gameAreas: GameArea[] = [
    {
      id: 'despertar',
      title: '⚡ Portal del Despertar',
      subtitle: 'Diagnóstico Inicial',
      description: 'Descubre tu nivel actual y áreas de mejora con nuestro diagnóstico inteligente.',
      icon: Zap,
      path: '/portal-despertar',
      levelRequired: 1,
      gradient: 'from-yellow-600 to-orange-600',
      borderColor: 'border-yellow-500/50',
      rewards: ['Desbloquea tu potencial', 'Plan de estudio personalizado', '200 XP inicial']
    },
    {
      id: 'biblioteca',
      title: '📚 Biblioteca de los Ancestros',
      subtitle: 'Req: Nivel 5',
      description: 'Videos y recursos de estudio organizados por competencia ICFES. Contenido curado por expertos.',
      icon: BookOpen,
      path: '/biblioteca-ancestral',
      levelRequired: 5,
      gradient: 'from-purple-600 to-blue-600',
      borderColor: 'border-purple-500/50',
      rewards: ['193 videos educativos', 'Planes de Claude AI', '150 XP por video']
    },
    {
      id: 'arena',
      title: '⚔️ Arena del Conocimiento',
      subtitle: 'Req: Nivel 10',
      description: 'Práctica intensiva con preguntas tipo ICFES. Combate contra enemigos usando tu conocimiento.',
      icon: Sword,
      path: '/arena-conocimiento',
      levelRequired: 10,
      gradient: 'from-red-600 to-pink-600',
      borderColor: 'border-red-500/50',
      rewards: ['1,058 preguntas reales', 'Sistema de combate', '300 XP por batalla']
    },
    {
      id: 'santuario',
      title: '🏛️ Santuario de la Sabiduría',
      subtitle: 'Req: Nivel 20',
      description: 'Reportes PDF personalizados y consolidación de conocimiento. Análisis avanzado de progreso.',
      icon: Crown,
      path: '/santuario-sabiduria',
      levelRequired: 20,
      gradient: 'from-gold-600 to-yellow-600',
      borderColor: 'border-gold-500/50',
      rewards: ['Reportes PDF', 'Análisis avanzado', '500 XP por reporte']
    },
    {
      id: 'mazmorra',
      title: '⏱️ Mazmorra del Tiempo',
      subtitle: 'Evento Especial',
      description: 'Simulacros cronometrados bajo presión. Pon a prueba tu velocidad y precisión.',
      icon: Shield,
      path: '/mazmorra-tiempo',
      levelRequired: 15,
      isSpecialEvent: true,
      gradient: 'from-indigo-600 to-purple-600',
      borderColor: 'border-indigo-500/50',
      rewards: ['Simulacros ICFES', 'Presión temporal', '400 XP por simulacro']
    },
    {
      id: 'torre',
      title: '👑 Torre de los Monarcas',
      subtitle: 'Solo Rango A/S',
      description: 'Desafíos avanzados exclusivos para los hunters de élite. Contenido de máxima dificultad.',
      icon: Trophy,
      path: '/torre-monarcas',
      levelRequired: 50,
      rankRequired: ['A', 'S', 'SS', 'SSS'],
      gradient: 'from-pink-600 to-red-600',
      borderColor: 'border-pink-500/50',
      rewards: ['Desafíos élite', 'Rango SSS', '1000 XP por desafío']
    }
  ];

  const isAreaUnlocked = (area: GameArea) => {
    if (!currentUser) return false;
    
    // Check level requirement
    if (currentUser.level < area.levelRequired) return false;
    
    // Check rank requirement if exists
    if (area.rankRequired && !area.rankRequired.includes(currentUser.rank)) return false;
    
    return true;
  };

  const handleAreaClick = (area: GameArea) => {
    if (!isAreaUnlocked(area)) {
      const requirements = [
        `Nivel ${area.levelRequired}`,
        ...(area.rankRequired ? [`Rango ${area.rankRequired.join(' o ')}`] : [])
      ];
      
      alert(`🔒 Área Bloqueada\n\n${area.title}\n\nRequisitos:\n${requirements.map(r => `• ${r}`).join('\n')}\n\nTu progreso actual:\n• Nivel ${currentUser?.level || 0}\n• Rango ${currentUser?.rank || 'E'}\n\n¡Sigue entrenando para desbloquear esta área!`);
      return;
    }
    
    if (area.comingSoon) {
      alert(`⭐ Próximamente\n\n${area.title}\n\nEsta área estará disponible en una futura actualización.\n\n¡Mantente atento a las novedades!`);
      return;
    }
    
    router.push(area.path);
  };

  const getRankColor = (rank: string) => {
    const colors = {
      'E': 'text-gray-400',
      'D': 'text-green-400', 
      'C': 'text-blue-400',
      'B': 'text-purple-400',
      'A': 'text-yellow-400',
      'S': 'text-red-400',
      'SS': 'text-pink-400',
      'SSS': 'text-gold-400'
    };
    return colors[rank] || 'text-gray-400';
  };

  if (!currentUser) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 text-white flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-gold-400 mx-auto mb-4"></div>
          <h2 className="text-2xl font-bold mb-2">Cargando Hunter Profile...</h2>
          <p className="text-purple-200">Inicializando sistema de entrenamiento</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 text-white">
      <MainNavigation currentUser={currentUser} />
      
      {/* Main Content */}
      <div className="pt-20 lg:pt-24 pb-8">
        <div className="container mx-auto px-4">
          {/* Header */}
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-center mb-12"
          >
            <h1 className="text-5xl font-bold mb-4 bg-gradient-to-r from-gold-400 via-purple-400 to-blue-400 bg-clip-text text-transparent">
              🎮 Hub Central
            </h1>
            <p className="text-xl text-purple-200 mb-6">
              Bienvenido, <span className={`font-bold ${getRankColor(currentUser.rank)}`}>
                Hunter {currentUser.username}
              </span>
            </p>
            
            {/* User Stats Bar */}
            <div className="max-w-4xl mx-auto bg-black/30 rounded-xl p-6 border border-purple-500/30">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
                <div>
                  <div className="text-2xl font-bold text-white">{currentUser.level}</div>
                  <div className="text-purple-300 text-sm">Nivel</div>
                </div>
                <div>
                  <div className={`text-2xl font-bold ${getRankColor(currentUser.rank)}`}>{currentUser.rank}</div>
                  <div className="text-purple-300 text-sm">Rango</div>
              </div>
                <div>
                  <div className="text-2xl font-bold text-gold-400">{currentUser.experience}</div>
                  <div className="text-purple-300 text-sm">XP Total</div>
                </div>
                <div>
                  <div className="text-2xl font-bold text-green-400">{currentUser.hp}</div>
                  <div className="text-purple-300 text-sm">HP</div>
                </div>
              </div>
            </div>
          </motion.div>

          {/* Game Areas Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {gameAreas.map((area, index) => {
              const isUnlocked = isAreaUnlocked(area);
              const Icon = area.icon;
            
            return (
                <motion.div
                  key={area.id}
                  initial={{ opacity: 0, y: 50 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.1 }}
                  className={`relative group cursor-pointer ${
                    isUnlocked ? 'hover:scale-105' : 'hover:scale-102'
                  } transition-all duration-300`}
                  onClick={() => handleAreaClick(area)}
                  onMouseEnter={() => setHoveredArea(area.id)}
                  onMouseLeave={() => setHoveredArea(null)}
                >
                  <div className={`bg-gradient-to-br ${area.gradient}/20 rounded-xl p-6 border-2 ${
                    isUnlocked ? area.borderColor : 'border-gray-600/30'
                  } backdrop-blur-sm relative overflow-hidden ${
                    !isUnlocked ? 'opacity-60' : ''
                  }`}>
                    
                    {/* Background Pattern */}
                    <div className="absolute inset-0 opacity-10">
                      <div className="absolute inset-0 bg-gradient-to-br from-white/5 to-transparent" />
                    </div>
                    
                    {/* Lock Overlay */}
                    {!isUnlocked && (
                      <div className="absolute inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center">
                        <div className="text-center">
                          <Lock className="w-12 h-12 text-gray-400 mx-auto mb-2" />
                          <div className="text-white font-bold">Nivel {area.levelRequired}</div>
                          {area.rankRequired && (
                            <div className="text-gray-300 text-sm">Rango {area.rankRequired.join('/')}</div>
                          )}
                        </div>
                      </div>
                    )}
                    
                    {/* Special Event Badge */}
                    {area.isSpecialEvent && isUnlocked && (
                      <div className="absolute top-3 right-3 bg-yellow-500 text-black px-2 py-1 rounded-full text-xs font-bold animate-pulse">
                        EVENTO
                  </div>
                )}

                    {/* Coming Soon Badge */}
                    {area.comingSoon && (
                      <div className="absolute top-3 right-3 bg-blue-500 text-white px-2 py-1 rounded-full text-xs font-bold">
                        PRÓXIMAMENTE
                      </div>
                )}

                {/* Content */}
                <div className="relative z-10">
                      {/* Icon */}
                      <div className={`w-16 h-16 rounded-full bg-gradient-to-r ${area.gradient} flex items-center justify-center mb-4 mx-auto ${
                        isUnlocked ? 'shadow-lg shadow-purple-500/25' : 'grayscale'
                      }`}>
                        <Icon className="w-8 h-8 text-white" />
                      </div>
                      
                      {/* Title */}
                      <h3 className="text-xl font-bold text-center mb-2 text-white">
                        {area.title}
                    </h3>
                      
                      {/* Subtitle */}
                      <p className={`text-center text-sm mb-3 ${
                        isUnlocked ? 'text-purple-300' : 'text-gray-400'
                      }`}>
                        {area.subtitle}
                      </p>
                      
                      {/* Description */}
                      <p className={`text-center text-sm mb-4 leading-relaxed ${
                        isUnlocked ? 'text-purple-100' : 'text-gray-500'
                      }`}>
                        {area.description}
                      </p>
                      
                      {/* Rewards */}
                      {isUnlocked && (
                        <div className="space-y-1 mb-4">
                          {area.rewards.map((reward, idx) => (
                            <div key={idx} className="text-xs text-gold-300 flex items-center gap-1">
                              <Star className="w-3 h-3" />
                              {reward}
                            </div>
                          ))}
                        </div>
                      )}
                      
                      {/* Action Button */}
                      <div className="text-center">
                        {isUnlocked ? (
                          <button className={`bg-gradient-to-r ${area.gradient} hover:shadow-lg hover:shadow-purple-500/25 px-6 py-3 rounded-lg font-bold text-white transition-all transform hover:scale-105`}>
                            🚀 Entrar
                          </button>
                        ) : area.comingSoon ? (
                          <button className="bg-gray-600 px-6 py-3 rounded-lg font-bold text-gray-300 cursor-not-allowed">
                            ⭐ Próximamente
                          </button>
                        ) : (
                          <button className="bg-gray-700 px-6 py-3 rounded-lg font-bold text-gray-400 cursor-not-allowed">
                            🔒 Bloqueado
                          </button>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Hover Effect */}
                  {hoveredArea === area.id && isUnlocked && (
                    <motion.div
                      layoutId="area-glow"
                      className={`absolute inset-0 bg-gradient-to-br ${area.gradient}/10 rounded-xl blur-xl -z-10`}
                      transition={{ type: "spring", damping: 30, stiffness: 200 }}
                    />
                  )}
                </motion.div>
              );
            })}
          </div>

          {/* Progress Section */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.8 }}
            className="mt-12 max-w-4xl mx-auto"
          >
            <div className="bg-black/30 rounded-xl p-6 border border-purple-500/30">
              <h2 className="text-2xl font-bold text-center mb-6 text-gold-400">
                📊 Tu Progreso Hunter
              </h2>
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {/* Level Progress */}
                <div className="text-center">
                  <div className="text-3xl font-bold text-white mb-2">{currentUser.level}</div>
                  <div className="text-purple-300 mb-3">Nivel Actual</div>
                  <div className="w-full bg-gray-700 rounded-full h-3">
                    <div 
                      className="bg-gradient-to-r from-purple-500 to-gold-500 h-3 rounded-full transition-all"
                      style={{ width: `${(currentUser.experience % 1000) / 10}%` }}
                    />
                  </div>
                  <div className="text-xs text-purple-200 mt-2">
                    {currentUser.experience % 1000}/1000 XP al siguiente nivel
                  </div>
                </div>
                
                {/* Unlocked Areas */}
                <div className="text-center">
                  <div className="text-3xl font-bold text-green-400 mb-2">
                    {gameAreas.filter(area => isAreaUnlocked(area)).length}
                  </div>
                  <div className="text-purple-300 mb-3">Áreas Desbloqueadas</div>
                  <div className="text-sm text-green-300">
                    {gameAreas.filter(area => isAreaUnlocked(area)).map(area => area.title.split(' ')[1]).join(', ')}
                  </div>
                </div>
                
                {/* Next Unlock */}
                <div className="text-center">
                  {(() => {
                    const nextArea = gameAreas.find(area => !isAreaUnlocked(area) && !area.comingSoon);
                    if (nextArea) {
                      return (
                        <>
                          <div className="text-3xl font-bold text-yellow-400 mb-2">{nextArea.levelRequired}</div>
                          <div className="text-purple-300 mb-3">Próximo Desbloqueo</div>
                          <div className="text-sm text-yellow-300">
                            {nextArea.title.split(' ')[1]} en nivel {nextArea.levelRequired}
                          </div>
                        </>
                      );
                    } else {
                      return (
                        <>
                          <div className="text-3xl font-bold text-gold-400 mb-2">👑</div>
                          <div className="text-purple-300 mb-3">Estado</div>
                          <div className="text-sm text-gold-300">
                            ¡Todas las áreas desbloqueadas!
                          </div>
                        </>
                      );
                    }
                  })()}
                </div>
              </div>
        </div>
          </motion.div>

          {/* Quick Actions */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 1.0 }}
            className="mt-8 text-center"
          >
            <h3 className="text-xl font-bold text-purple-300 mb-4">Acciones Rápidas</h3>
            <div className="flex justify-center gap-4 flex-wrap">
              <button
                onClick={() => router.push('/diagnostic-test')}
                className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 px-6 py-3 rounded-lg font-semibold transition-all transform hover:scale-105 flex items-center gap-2"
              >
                <Target className="w-5 h-5" />
                Diagnóstico Rápido
              </button>
              
              <button
                onClick={() => router.push('/simple-recommendations')}
                className="bg-gradient-to-r from-green-600 to-blue-600 hover:from-green-700 hover:to-blue-700 px-6 py-3 rounded-lg font-semibold transition-all transform hover:scale-105 flex items-center gap-2"
              >
                <Play className="w-5 h-5" />
                Ver Recomendaciones
              </button>
              
              <button
                onClick={() => router.push('/study-plans')}
                className="bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 px-6 py-3 rounded-lg font-semibold transition-all transform hover:scale-105 flex items-center gap-2"
              >
                <BookOpen className="w-5 h-5" />
                Mis Planes
              </button>
            </div>
          </motion.div>
        </div>
      </div>
    </div>
  );
}