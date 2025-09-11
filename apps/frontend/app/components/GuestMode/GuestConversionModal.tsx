'use client';

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  User, 
  Trophy,
  Brain,
  CheckCircle,
  Sparkles,
  Gift,
  Zap,
  Lock,
  ArrowRight,
  Clock
} from 'lucide-react';
import { useAudio } from '../PortalLogin/AudioEngine';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/stores/useAuthStore';

interface GuestConversionModalProps {
  isOpen: boolean;
  onClose: () => void;
  guestScore: number;
  guestProgress?: {
    questionsAnswered: number;
    timeSpent: number;
    areasExplored: string[];
  };
}

export default function GuestConversionModal({ 
  isOpen, 
  onClose, 
  guestScore,
  guestProgress = {
    questionsAnswered: 5,
    timeSpent: 300,
    areasExplored: ['Matemáticas', 'Lectura']
  }
}: GuestConversionModalProps) {
  const { playSound } = useAudio();
  const router = useRouter();
  const { login } = useAuthStore();
  
  const [isRegistering, setIsRegistering] = useState(false);
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: ''
  });
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  
  const conversionBenefits = [
    {
      icon: <Trophy className="w-6 h-6" />,
      title: 'Conserva tu Puntuación',
      description: `Mantén tu ${guestScore}% de la evaluación inicial`,
      highlight: true
    },
    {
      icon: <Brain className="w-6 h-6" />,
      title: 'Plan Personalizado',
      description: 'Recibe un plan de estudio basado en tu desempeño',
      highlight: false
    },
    {
      icon: <Gift className="w-6 h-6" />,
      title: 'Bonus de Bienvenida',
      description: '500 Orbes + 3 días de Premium gratis',
      highlight: true
    },
    {
      icon: <Zap className="w-6 h-6" />,
      title: 'Acceso Completo',
      description: 'Desbloquea todas las funciones y contenido',
      highlight: false
    }
  ];
  
  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');
    
    try {
      // API call para registrar con datos de guest
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/auth/register-guest`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...formData,
          display_name: formData.username,
          guestData: {
            initialScore: guestScore,
            questionsAnswered: guestProgress.questionsAnswered,
            timeSpent: guestProgress.timeSpent,
            areasExplored: guestProgress.areasExplored
          }
        })
      });
      
      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Error al registrar');
      }
      
      const data = await response.json();
      
      // Auto login después del registro
      await login(formData.username, formData.password);
      
      playSound('level_up');
      
      // Redirigir al dashboard con mensaje de éxito
      router.push('/onboarding?converted=true');
      
    } catch (err: any) {
      setError(err.message || 'Error al crear la cuenta');
      playSound('notification_epic');
    } finally {
      setIsLoading(false);
    }
  };
  
  const handleQuickRegister = () => {
    // Opción de registro rápido con OAuth (futuro)
    playSound('typing_click');
    console.log('Quick register with OAuth');
  };
  
  return (
    <AnimatePresence>
      {isOpen && (
        <>
          <motion.div
            className="fixed inset-0 bg-black/80 z-50"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
          />
          
          <motion.div
            className="fixed top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 
              bg-gray-900 rounded-lg max-w-2xl w-full mx-4 z-50 max-h-[90vh] overflow-y-auto"
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.9, opacity: 0 }}
            onClick={(e) => e.stopPropagation()}
          >
            {/* Header */}
            <div className="bg-gradient-to-r from-purple-900 to-indigo-900 p-6 rounded-t-lg">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-3xl font-bold text-white mb-2 font-cinzel">
                    ¡No Pierdas tu Progreso!
                  </h2>
                  <p className="text-purple-200">
                    Convierte tu cuenta de invitado en una cuenta completa
                  </p>
                </div>
                <Sparkles className="w-12 h-12 text-yellow-400" />
              </div>
            </div>
            
            {/* Guest Progress Summary */}
            <div className="p-6 bg-gray-800/50">
              <h3 className="text-lg font-semibold text-white mb-4">
                Tu Progreso como Invitado
              </h3>
              
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="bg-gray-900/50 rounded-lg p-3 text-center">
                  <div className="text-2xl font-bold text-purple-400">{guestScore}%</div>
                  <p className="text-xs text-gray-400">Puntuación Inicial</p>
                </div>
                
                <div className="bg-gray-900/50 rounded-lg p-3 text-center">
                  <div className="text-2xl font-bold text-blue-400">
                    {guestProgress.questionsAnswered}
                  </div>
                  <p className="text-xs text-gray-400">Preguntas</p>
                </div>
                
                <div className="bg-gray-900/50 rounded-lg p-3 text-center">
                  <div className="text-2xl font-bold text-green-400">
                    {Math.floor(guestProgress.timeSpent / 60)}m
                  </div>
                  <p className="text-xs text-gray-400">Tiempo Jugado</p>
                </div>
                
                <div className="bg-gray-900/50 rounded-lg p-3 text-center">
                  <div className="text-2xl font-bold text-yellow-400">
                    {guestProgress.areasExplored.length}
                  </div>
                  <p className="text-xs text-gray-400">Áreas Exploradas</p>
                </div>
              </div>
            </div>
            
            {/* Benefits */}
            <div className="p-6">
              <h3 className="text-lg font-semibold text-white mb-4">
                Al crear tu cuenta obtienes:
              </h3>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                {conversionBenefits.map((benefit, index) => (
                  <motion.div
                    key={index}
                    className={`flex items-start gap-3 p-4 rounded-lg ${
                      benefit.highlight 
                        ? 'bg-purple-900/30 border border-purple-500/30' 
                        : 'bg-gray-800/30'
                    }`}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.1 }}
                  >
                    <div className={`${
                      benefit.highlight ? 'text-purple-400' : 'text-gray-400'
                    }`}>
                      {benefit.icon}
                    </div>
                    <div>
                      <h4 className="font-semibold text-white mb-1">
                        {benefit.title}
                      </h4>
                      <p className="text-sm text-gray-300">
                        {benefit.description}
                      </p>
                    </div>
                  </motion.div>
                ))}
              </div>
              
              {/* Registration Form */}
              {isRegistering ? (
                <motion.form
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  onSubmit={handleRegister}
                  className="space-y-4"
                >
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Nombre de Usuario
                    </label>
                    <input
                      type="text"
                      value={formData.username}
                      onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                      className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg 
                        text-white placeholder-gray-500 focus:outline-none focus:ring-2 
                        focus:ring-purple-500 focus:border-transparent"
                      placeholder="shadow_hunter"
                      required
                      minLength={3}
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Correo Electrónico
                    </label>
                    <input
                      type="email"
                      value={formData.email}
                      onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                      className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg 
                        text-white placeholder-gray-500 focus:outline-none focus:ring-2 
                        focus:ring-purple-500 focus:border-transparent"
                      placeholder="tu@email.com"
                      required
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Contraseña
                    </label>
                    <input
                      type="password"
                      value={formData.password}
                      onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                      className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg 
                        text-white placeholder-gray-500 focus:outline-none focus:ring-2 
                        focus:ring-purple-500 focus:border-transparent"
                      placeholder="••••••••"
                      required
                      minLength={8}
                    />
                  </div>
                  
                  {error && (
                    <div className="bg-red-900/30 border border-red-500/50 rounded-lg p-3">
                      <p className="text-red-400 text-sm">{error}</p>
                    </div>
                  )}
                  
                  <div className="flex gap-3">
                    <button
                      type="button"
                      onClick={() => setIsRegistering(false)}
                      className="flex-1 bg-gray-700 hover:bg-gray-600 text-white font-semibold 
                        py-3 px-6 rounded-lg transition-all"
                    >
                      Atrás
                    </button>
                    
                    <button
                      type="submit"
                      disabled={isLoading}
                      className="flex-1 bg-gradient-to-r from-purple-600 to-purple-700 
                        hover:from-purple-700 hover:to-purple-800 disabled:from-gray-600 
                        disabled:to-gray-700 disabled:cursor-not-allowed text-white 
                        font-bold py-3 px-6 rounded-lg transition-all flex items-center 
                        justify-center gap-2"
                    >
                      {isLoading ? (
                        <motion.div
                          className="w-5 h-5 border-2 border-white border-t-transparent rounded-full"
                          animate={{ rotate: 360 }}
                          transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                        />
                      ) : (
                        <>
                          <CheckCircle className="w-5 h-5" />
                          Crear Cuenta y Conservar Progreso
                        </>
                      )}
                    </button>
                  </div>
                </motion.form>
              ) : (
                <div className="space-y-3">
                  <motion.button
                    onClick={() => setIsRegistering(true)}
                    className="w-full bg-gradient-to-r from-purple-600 to-purple-700 
                      hover:from-purple-700 hover:to-purple-800 text-white font-bold 
                      py-4 px-6 rounded-lg transition-all flex items-center justify-center gap-3"
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                  >
                    <User className="w-5 h-5" />
                    Crear Cuenta con Email
                    <ArrowRight className="w-5 h-5" />
                  </motion.button>
                  
                  {/* Future OAuth options
                  <div className="flex gap-3">
                    <button
                      onClick={handleQuickRegister}
                      className="flex-1 bg-gray-700 hover:bg-gray-600 text-white 
                        font-semibold py-3 px-6 rounded-lg transition-all flex 
                        items-center justify-center gap-2"
                    >
                      <span>🔷</span>
                      Google
                    </button>
                    
                    <button
                      onClick={handleQuickRegister}
                      className="flex-1 bg-gray-700 hover:bg-gray-600 text-white 
                        font-semibold py-3 px-6 rounded-lg transition-all flex 
                        items-center justify-center gap-2"
                    >
                      <span>📘</span>
                      Facebook
                    </button>
                  </div>
                  */}
                  
                  <button
                    onClick={onClose}
                    className="w-full bg-gray-700 hover:bg-gray-600 text-gray-300 
                      font-semibold py-3 px-6 rounded-lg transition-all"
                  >
                    Continuar como Invitado
                  </button>
                </div>
              )}
            </div>
            
            {/* Limited Time Offer */}
            <div className="bg-yellow-900/20 border-t border-yellow-500/30 p-4 rounded-b-lg">
              <div className="flex items-center justify-center gap-3 text-center">
                <Clock className="w-5 h-5 text-yellow-400" />
                <p className="text-sm text-yellow-300">
                  <span className="font-semibold">Oferta Limitada:</span> Registra ahora y obtén 3 días de Premium gratis
                </p>
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}