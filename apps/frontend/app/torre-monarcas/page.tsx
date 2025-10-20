'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { motion } from 'framer-motion';
import { 
  Crown, 
  Trophy, 
  Sword, 
  Shield, 
  ArrowLeft,
  Star,
  Flame,
  Zap,
  Target,
  Award,
  CheckCircle,
  Lock
} from 'lucide-react';
import MainNavigation from '../components/Navigation/MainNavigation';

interface EliteChallenge {
  id: string;
  title: string;
  description: string;
  difficulty: 'SSS' | 'SS' | 'S';
  xpReward: number;
  requirements: string[];
  icon: any;
  color: string;
  status: 'available' | 'locked' | 'completed';
}

export default function TorreMonarcasPage() {
  const router = useRouter();
  const [currentUser, setCurrentUser] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Load user data and check access requirements
    const userData = localStorage.getItem('currentUser') || localStorage.getItem('user');
    if (userData) {
      const user = JSON.parse(userData);
      setCurrentUser(user);
      
      // Check level and rank requirements
      if (user.level < 50 || !['A', 'S', 'SS', 'SSS'].includes(user.rank)) {
        alert('🔒 Acceso Denegado\n\nLa Torre de los Monarcas es exclusiva para:\n• Nivel 50+\n• Rango A o superior\n\nTu progreso actual:\n• Nivel ' + user.level + '\n• Rango ' + user.rank + '\n\n¡Alcanza la élite para acceder a los desafíos supremos!');
        router.push('/hub-central');
        return;
      }
    }
    setLoading(false);
  }, []);

  const eliteChallenges: EliteChallenge[] = [
    {
      id: 'master_trial',
      title: '👑 Prueba del Maestro',
      description: 'El desafío definitivo que solo los verdaderos maestros pueden superar. Todas las competencias, máxima dificultad.',
      difficulty: 'SSS',
      xpReward: 2000,
      requirements: ['Nivel 50+', 'Rango S+', 'Todas las áreas completadas'],
      icon: Crown,
      color: 'from-gold-600 to-yellow-600',
      status: 'available'
    },
    {
      id: 'speed_demon',
      title: '⚡ Demonio de la Velocidad',
      description: 'Responde 50 preguntas en 10 minutos con 95% de precisión. Solo para los más rápidos.',
      difficulty: 'SS',
      xpReward: 1500,
      requirements: ['Nivel 45+', 'Rango A+', 'Mazmorra del Tiempo completada'],
      icon: Zap,
      color: 'from-blue-600 to-cyan-600',
      status: 'available'
    },
    {
      id: 'perfect_scholar',
      title: '🎓 Erudito Perfecto',
      description: 'Demuestra dominio absoluto en todas las competencias ICFES sin cometer errores.',
      difficulty: 'SSS',
      xpReward: 2500,
      requirements: ['Nivel 60+', 'Rango SS+', 'Perfección en diagnósticos'],
      icon: Award,
      color: 'from-purple-600 to-pink-600',
      status: currentUser?.level >= 60 ? 'available' : 'locked'
    },
    {
      id: 'legend_maker',
      title: '🌟 Forjador de Leyendas',
      description: 'Crea tu propia leyenda completando el desafío más difícil jamás diseñado.',
      difficulty: 'SSS',
      xpReward: 5000,
      requirements: ['Nivel 80+', 'Rango SSS', 'Todos los desafíos completados'],
      icon: Star,
      color: 'from-pink-600 to-red-600',
      status: currentUser?.rank === 'SSS' ? 'available' : 'locked'
    }
  ];

  const startEliteChallenge = (challenge: EliteChallenge) => {
    if (challenge.status === 'locked') {
      alert(`🔒 Desafío Bloqueado\n\n${challenge.title}\n\nRequisitos:\n${challenge.requirements.map(r => `• ${r}`).join('\n')}\n\n¡Continúa tu entrenamiento para desbloquear este desafío supremo!`);
      return;
    }
    
    alert(`👑 Iniciando Desafío Élite\n\n${challenge.title}\n\n⚠️ ADVERTENCIA:\nEste es un desafío de máxima dificultad.\nSolo los verdaderos maestros pueden completarlo.\n\n¿Estás preparado para la gloria eterna?`);
    
    // In a real implementation, this would start the elite challenge
    // For now, simulate the challenge experience
    setTimeout(() => {
      alert(`🎉 ¡Desafío Completado!\n\n${challenge.title}\n\n🏆 Recompensas:\n• +${challenge.xpReward} XP\n• Título: "Monarca del ${challenge.title.split(' ')[1]}"\n• Acceso a contenido exclusivo\n\n¡Tu leyenda ha sido forjada!`);
    }, 2000);
  };

  const getDifficultyColor = (difficulty: string) => {
    const colors = {
      'S': 'text-red-400 bg-red-900/30',
      'SS': 'text-pink-400 bg-pink-900/30',
      'SSS': 'text-gold-400 bg-gold-900/30'
    };
    return colors[difficulty] || 'text-gray-400 bg-gray-900/30';
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 text-white flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-gold-400 mx-auto mb-4"></div>
          <h2 className="text-2xl font-bold mb-2">👑 Accediendo a la Torre...</h2>
          <p className="text-purple-200">Verificando credenciales de élite</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 text-white">
      <MainNavigation currentUser={currentUser} />
      
      <div className="pt-20 lg:pt-24 pb-8">
        <div className="container mx-auto px-4">
          {/* Header */}
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-center mb-8"
          >
            <div className="flex items-center justify-center gap-4 mb-4">
              <button
                onClick={() => router.push('/hub-central')}
                className="bg-purple-600/50 hover:bg-purple-700/50 p-3 rounded-lg transition-all"
              >
                <ArrowLeft className="w-5 h-5" />
              </button>
              
              <h1 className="text-4xl font-bold bg-gradient-to-r from-gold-400 to-pink-400 bg-clip-text text-transparent">
                👑 Torre de los Monarcas
              </h1>
            </div>
            
            <p className="text-xl text-purple-200 mb-4">
              Desafíos avanzados exclusivos para hunters de élite
            </p>
            
            {/* Elite Badge */}
            <div className="inline-flex items-center gap-2 bg-gold-800/50 px-4 py-2 rounded-lg">
              <Crown className="w-4 h-4 text-gold-400" />
              <span className="text-gold-200 font-bold">ACCESO ÉLITE CONFIRMADO</span>
            </div>
          </motion.div>

          {/* Elite Status */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="max-w-4xl mx-auto mb-8 bg-gradient-to-r from-gold-900/30 to-pink-900/30 rounded-xl p-6 border border-gold-500/50"
          >
            <h2 className="text-2xl font-bold text-gold-400 mb-4 text-center">🏆 Estado de Monarca</h2>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
              <div className="bg-black/30 rounded-lg p-3">
                <div className="text-2xl font-bold text-gold-400">{currentUser?.level || 0}</div>
                <div className="text-gold-200 text-sm">Nivel Élite</div>
              </div>
              <div className="bg-black/30 rounded-lg p-3">
                <div className="text-2xl font-bold text-pink-400">{currentUser?.rank || 'S'}</div>
                <div className="text-pink-200 text-sm">Rango Supremo</div>
              </div>
              <div className="bg-black/30 rounded-lg p-3">
                <div className="text-2xl font-bold text-purple-400">{currentUser?.experience || 0}</div>
                <div className="text-purple-200 text-sm">XP Maestro</div>
              </div>
              <div className="bg-black/30 rounded-lg p-3">
                <div className="text-2xl font-bold text-red-400">4</div>
                <div className="text-red-200 text-sm">Desafíos Élite</div>
              </div>
            </div>
          </motion.div>

          {/* Elite Challenges */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {eliteChallenges.map((challenge, index) => {
              const isLocked = challenge.status === 'locked';
              const Icon = challenge.icon;
              
              return (
                <motion.div
                  key={challenge.id}
                  initial={{ opacity: 0, y: 50 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.1 }}
                  className={`group cursor-pointer ${isLocked ? 'opacity-60' : ''}`}
                  onClick={() => startEliteChallenge(challenge)}
                >
                  <div className={`bg-gradient-to-br ${challenge.color}/20 rounded-xl p-6 border-2 ${
                    isLocked 
                      ? 'border-gray-600/30' 
                      : 'border-gold-500/30 hover:border-gold-500/70'
                  } transition-all transform ${isLocked ? '' : 'hover:scale-105'} backdrop-blur-sm relative overflow-hidden`}>
                    
                    {/* Difficulty Badge */}
                    <div className={`absolute top-3 right-3 px-3 py-1 rounded-full text-xs font-bold ${getDifficultyColor(challenge.difficulty)}`}>
                      {challenge.difficulty}
                    </div>
                    
                    {/* Lock Overlay */}
                    {isLocked && (
                      <div className="absolute inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center">
                        <div className="text-center">
                          <Lock className="w-8 h-8 text-gray-400 mx-auto mb-2" />
                          <div className="text-white font-bold text-sm">Requisitos no cumplidos</div>
                        </div>
                      </div>
                    )}
                    
                    <div className="relative z-10">
                      {/* Icon */}
                      <div className={`w-20 h-20 rounded-full bg-gradient-to-r ${challenge.color} flex items-center justify-center mb-4 mx-auto shadow-lg shadow-gold-500/25`}>
                        <Icon className="w-10 h-10 text-white" />
                      </div>
                      
                      {/* Title */}
                      <h3 className="text-xl font-bold text-center mb-2 text-white">
                        {challenge.title}
                      </h3>
                      
                      {/* Description */}
                      <p className="text-center text-sm mb-4 text-purple-100 leading-relaxed">
                        {challenge.description}
                      </p>
                      
                      {/* Requirements */}
                      <div className="mb-4">
                        <div className="text-xs text-gold-300 font-semibold mb-2">Requisitos:</div>
                        <div className="space-y-1">
                          {challenge.requirements.map((req, idx) => (
                            <div key={idx} className="text-xs text-purple-200 flex items-center gap-1">
                              <CheckCircle className="w-3 h-3 text-green-400" />
                              {req}
                            </div>
                          ))}
                        </div>
                      </div>
                      
                      {/* Reward */}
                      <div className="text-center mb-4">
                        <div className="bg-gold-900/30 rounded-lg p-3">
                          <div className="text-gold-400 font-bold">+{challenge.xpReward} XP</div>
                          <div className="text-gold-200 text-xs">Recompensa Élite</div>
                        </div>
                      </div>
                      
                      {/* Action Button */}
                      <div className="text-center">
                        {isLocked ? (
                          <button className="bg-gray-700 px-6 py-3 rounded-lg font-bold text-gray-400 cursor-not-allowed w-full">
                            🔒 Bloqueado
                          </button>
                        ) : (
                          <button className={`bg-gradient-to-r ${challenge.color} hover:shadow-lg hover:shadow-gold-500/25 px-6 py-3 rounded-lg font-bold text-white transition-all transform hover:scale-105 w-full`}>
                            ⚔️ Aceptar Desafío
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                </motion.div>
              );
            })}
          </div>

          {/* Elite Hall of Fame */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.6 }}
            className="mt-8 max-w-4xl mx-auto bg-black/30 rounded-xl p-6 border border-gold-500/30"
          >
            <h2 className="text-2xl font-bold text-gold-400 mb-6 text-center">🏛️ Salón de la Fama Élite</h2>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {/* Legendary Hunters */}
              <div className="bg-gold-900/20 rounded-lg p-4 border border-gold-500/30">
                <h3 className="font-bold text-gold-400 mb-3 text-center">👑 Monarcas Legendarios</h3>
                <div className="space-y-2">
                  <div className="flex justify-between items-center">
                    <span className="text-gold-200">🥇 GrandMaster_SSS</span>
                    <span className="text-gold-400 font-bold">50,000 XP</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-silver-200">🥈 EliteScholar_SS</span>
                    <span className="text-silver-400 font-bold">35,000 XP</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-orange-200">🥉 MasterHunter_S</span>
                    <span className="text-orange-400 font-bold">25,000 XP</span>
                  </div>
                </div>
              </div>
              
              {/* Recent Achievements */}
              <div className="bg-purple-900/20 rounded-lg p-4 border border-purple-500/30">
                <h3 className="font-bold text-purple-400 mb-3 text-center">🏆 Logros Recientes</h3>
                <div className="space-y-2 text-sm">
                  <div className="text-purple-200">🎯 SpeedDemon_A completó "Demonio de la Velocidad"</div>
                  <div className="text-purple-200">👑 PerfectMind_S alcanzó Rango SSS</div>
                  <div className="text-purple-200">⚡ QuickThink_B subió a Nivel 55</div>
                </div>
              </div>
              
              {/* Your Progress */}
              <div className="bg-blue-900/20 rounded-lg p-4 border border-blue-500/30">
                <h3 className="font-bold text-blue-400 mb-3 text-center">📈 Tu Progreso Élite</h3>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-blue-200">Desafíos Completados:</span>
                    <span className="text-blue-400 font-bold">0/4</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-blue-200">XP Élite Ganado:</span>
                    <span className="text-blue-400 font-bold">0</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-blue-200">Ranking Élite:</span>
                    <span className="text-blue-400 font-bold">Novato</span>
                  </div>
                </div>
              </div>
            </div>
          </motion.div>

          {/* Back to Hub */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.8 }}
            className="mt-8 text-center"
          >
            <button
              onClick={() => router.push('/hub-central')}
              className="bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 px-6 py-3 rounded-lg font-semibold transition-all transform hover:scale-105 flex items-center gap-2 mx-auto"
            >
              <ArrowLeft className="w-5 h-5" />
              Volver al Hub Central
            </button>
          </motion.div>
        </div>
      </div>
    </div>
  );
}
