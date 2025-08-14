'use client';

import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { 
  User, 
  Lock, 
  Unlock,
  Trophy,
  Brain,
  Swords,
  Users,
  TrendingUp,
  Star,
  ChevronRight,
  AlertCircle,
  Sparkles
} from 'lucide-react';
import { useRouter } from 'next/navigation';
import { useAudio } from '../PortalLogin/AudioEngine';
import GuestConversionModal from './GuestConversionModal';

interface GuestDashboardProps {
  guestScore: number;
  onLogout: () => void;
}

export default function GuestDashboard({ guestScore, onLogout }: GuestDashboardProps) {
  const router = useRouter();
  const { playSound } = useAudio();
  const [showUpgradeModal, setShowUpgradeModal] = useState(false);
  
  const guestFeatures = [
    {
      id: 'practice',
      title: 'Práctica Básica',
      description: 'Accede a 10 preguntas por día',
      icon: <Brain className="w-8 h-8" />,
      available: true,
      limit: '10/10 preguntas disponibles',
      action: () => router.push('/test?mode=guest'),
      color: 'from-blue-500 to-blue-600'
    },
    {
      id: 'dungeon',
      title: 'Mazmorra Demo',
      description: 'Explora el primer piso',
      icon: <Swords className="w-8 h-8" />,
      available: true,
      limit: 'Solo Piso 1',
      action: () => router.push('/dungeon?mode=guest&floor=1'),
      color: 'from-purple-500 to-purple-600'
    },
    {
      id: 'leaderboard',
      title: 'Tabla de Líderes',
      description: 'Ver rankings globales',
      icon: <Trophy className="w-8 h-8" />,
      available: true,
      limit: 'Solo visualización',
      action: () => router.push('/leaderboards?mode=guest'),
      color: 'from-yellow-500 to-yellow-600'
    },
    {
      id: 'raids',
      title: 'Raids Multijugador',
      description: 'Batalla con otros jugadores',
      icon: <Users className="w-8 h-8" />,
      available: false,
      limit: 'Requiere cuenta',
      action: () => setShowUpgradeModal(true),
      color: 'from-red-500 to-red-600'
    },
    {
      id: 'guilds',
      title: 'Gremios',
      description: 'Únete a una comunidad',
      icon: <Users className="w-8 h-8" />,
      available: false,
      limit: 'Requiere cuenta',
      action: () => setShowUpgradeModal(true),
      color: 'from-green-500 to-green-600'
    },
    {
      id: 'progress',
      title: 'Progreso Guardado',
      description: 'Guarda tu avance',
      icon: <TrendingUp className="w-8 h-8" />,
      available: false,
      limit: 'Requiere cuenta',
      action: () => setShowUpgradeModal(true),
      color: 'from-indigo-500 to-indigo-600'
    }
  ];
  
  const accountBenefits = [
    { icon: <Unlock className="w-5 h-5" />, text: 'Acceso ilimitado a todas las preguntas' },
    { icon: <Trophy className="w-5 h-5" />, text: 'Participa en rankings y competencias' },
    { icon: <Users className="w-5 h-5" />, text: 'Únete a gremios y raids multijugador' },
    { icon: <TrendingUp className="w-5 h-5" />, text: 'Guarda tu progreso y estadísticas' },
    { icon: <Brain className="w-5 h-5" />, text: 'Planes de estudio personalizados con IA' },
    { icon: <Star className="w-5 h-5" />, text: 'Desbloquea logros y recompensas' }
  ];
  
  const getRankFromScore = (score: number) => {
    if (score >= 80) return 'A';
    if (score >= 60) return 'B';
    if (score >= 40) return 'C';
    return 'D';
  };
  
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900 to-gray-900 p-4">
      {/* Header */}
      <header className="flex justify-between items-center mb-8">
        <div className="flex items-center gap-4">
          <div className="w-16 h-16 rounded-full bg-gradient-to-br from-gray-600 to-gray-700 
            flex items-center justify-center border-4 border-gray-500">
            <User className="w-8 h-8 text-white" />
          </div>
          
          <div>
            <h1 className="text-2xl font-bold text-white">Modo Invitado</h1>
            <p className="text-gray-400">Explora con acceso limitado</p>
          </div>
        </div>
        
        <div className="flex items-center gap-4">
          <button
            onClick={() => router.push('/?register=true')}
            className="bg-gradient-to-r from-green-600 to-green-700 hover:from-green-700 
              hover:to-green-800 text-white font-semibold px-6 py-2 rounded-lg 
              transition-all flex items-center gap-2"
          >
            <Sparkles className="w-5 h-5" />
            Crear Cuenta
          </button>
          
          <button
            onClick={onLogout}
            className="bg-gray-700 hover:bg-gray-600 text-white px-4 py-2 rounded-lg transition-all"
          >
            Salir
          </button>
        </div>
      </header>
      
      {/* Guest Stats */}
      <div className="bg-gray-800/50 rounded-lg p-6 mb-8 backdrop-blur-sm">
        <h2 className="text-xl font-semibold text-white mb-4">Tu Evaluación Inicial</h2>
        
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-gray-900/50 rounded-lg p-4 text-center">
            <div className="text-3xl font-bold text-white mb-1">{guestScore}%</div>
            <p className="text-sm text-gray-400">Puntuación</p>
          </div>
          
          <div className="bg-gray-900/50 rounded-lg p-4 text-center">
            <div className="text-3xl font-bold text-purple-400 mb-1">
              {getRankFromScore(guestScore)}
            </div>
            <p className="text-sm text-gray-400">Rango Inicial</p>
          </div>
          
          <div className="bg-gray-900/50 rounded-lg p-4 text-center">
            <div className="text-3xl font-bold text-yellow-400 mb-1">5</div>
            <p className="text-sm text-gray-400">Preguntas</p>
          </div>
          
          <div className="bg-gray-900/50 rounded-lg p-4 text-center">
            <div className="text-3xl font-bold text-gray-500 mb-1">
              <Lock className="w-8 h-8 mx-auto" />
            </div>
            <p className="text-sm text-gray-400">Nivel Bloqueado</p>
          </div>
        </div>
      </div>
      
      {/* Limited Access Notice */}
      <div className="bg-orange-900/20 border border-orange-500/30 rounded-lg p-4 mb-8">
        <div className="flex items-start gap-3">
          <AlertCircle className="w-6 h-6 text-orange-400 flex-shrink-0 mt-0.5" />
          <div>
            <h3 className="font-semibold text-orange-300 mb-1">
              Acceso Limitado de Invitado
            </h3>
            <p className="text-sm text-gray-300">
              Como invitado tienes acceso limitado a las funciones. 
              Crea una cuenta gratuita para desbloquear todo el contenido y guardar tu progreso.
            </p>
          </div>
        </div>
      </div>
      
      {/* Features Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        {guestFeatures.map((feature, index) => (
          <motion.div
            key={feature.id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
            className={`relative overflow-hidden rounded-lg ${
              feature.available 
                ? 'cursor-pointer hover:transform hover:scale-105' 
                : 'cursor-not-allowed opacity-75'
            } transition-all duration-300`}
            onClick={() => {
              if (feature.available || !feature.available) {
                playSound(feature.available ? 'typing_click' : 'glitch');
                feature.action();
              }
            }}
          >
            <div className={`bg-gradient-to-br ${feature.color} p-6`}>
              <div className="flex items-start justify-between mb-4">
                <div className="text-white">
                  {feature.icon}
                </div>
                {!feature.available && (
                  <Lock className="w-5 h-5 text-white/50" />
                )}
              </div>
              
              <h3 className="text-xl font-bold text-white mb-2">
                {feature.title}
              </h3>
              
              <p className="text-white/80 text-sm mb-3">
                {feature.description}
              </p>
              
              <div className="flex items-center justify-between">
                <span className="text-xs text-white/60">
                  {feature.limit}
                </span>
                <ChevronRight className="w-5 h-5 text-white/60" />
              </div>
            </div>
            
            {!feature.available && (
              <div className="absolute inset-0 bg-black/50 flex items-center justify-center">
                <div className="text-center">
                  <Lock className="w-8 h-8 text-white/70 mx-auto mb-2" />
                  <p className="text-white/70 text-sm">Requiere Cuenta</p>
                </div>
              </div>
            )}
          </motion.div>
        ))}
      </div>
      
      {/* Upgrade CTA */}
      <div className="bg-gradient-to-r from-purple-900 to-indigo-900 rounded-lg p-8 text-center">
        <h2 className="text-3xl font-bold text-white mb-4 font-cinzel">
          ¿Listo para la Experiencia Completa?
        </h2>
        
        <p className="text-xl text-purple-200 mb-6">
          Desbloquea todo el potencial de ICFES Leveling
        </p>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-8 max-w-4xl mx-auto">
          {accountBenefits.map((benefit, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.1 }}
              className="flex items-center gap-3 text-left"
            >
              <div className="text-purple-300">
                {benefit.icon}
              </div>
              <span className="text-white/90 text-sm">
                {benefit.text}
              </span>
            </motion.div>
          ))}
        </div>
        
        <motion.button
          onClick={() => router.push('/?register=true')}
          className="bg-white text-purple-900 hover:bg-gray-100 font-bold px-8 py-4 
            rounded-lg text-lg transition-all transform hover:scale-105"
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
        >
          Crear Cuenta Gratuita Ahora
        </motion.button>
      </div>
      
      {/* Upgrade Modal */}
      <GuestConversionModal
        isOpen={showUpgradeModal}
        onClose={() => setShowUpgradeModal(false)}
        guestScore={guestScore}
        guestProgress={{
          questionsAnswered: 10,
          timeSpent: 600,
          areasExplored: ['Matemáticas', 'Lectura Crítica']
        }}
      />
    </div>
  );
}