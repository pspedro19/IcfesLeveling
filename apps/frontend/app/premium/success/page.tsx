'use client';

import React, { useEffect, useState } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { motion } from 'framer-motion';
import { 
  CheckCircle, 
  Crown, 
  Sparkles, 
  ArrowRight,
  Gift,
  Trophy,
  Zap
} from 'lucide-react';
import { useAudio } from '@/components/PortalLogin/AudioEngine';
import { useAuthStore } from '@/stores/useAuthStore';
import { trackGameEvent } from '@/lib/analytics';

export default function PremiumSuccessPage() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const { playSound } = useAudio();
  const { user, checkAuth } = useAuthStore();
  const [isVerifying, setIsVerifying] = useState(true);
  
  useEffect(() => {
    const verifyPurchase = async () => {
      const sessionId = searchParams.get('session_id');
      
      if (!sessionId) {
        router.push('/premium');
        return;
      }
      
      // Track successful purchase
      trackGameEvent('premium_purchase_success', { 
        sessionId,
        userId: user?.id 
      });
      
      // Play success sound
      playSound('level_up');
      
      // Refresh user data to get updated premium status
      await checkAuth();
      
      setIsVerifying(false);
    };
    
    verifyPurchase();
  }, [searchParams, router, playSound, user, checkAuth]);
  
  if (isVerifying) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900 to-gray-900 
        flex items-center justify-center">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
        >
          <Crown className="w-16 h-16 text-yellow-400" />
        </motion.div>
      </div>
    );
  }
  
  const benefits = [
    { icon: <Zap className="w-6 h-6" />, text: 'Doble experiencia activada' },
    { icon: <Trophy className="w-6 h-6" />, text: 'Acceso a raids exclusivos' },
    { icon: <Gift className="w-6 h-6" />, text: '1000 orbes de bonus' },
    { icon: <Sparkles className="w-6 h-6" />, text: 'Sin límites ni publicidad' }
  ];
  
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900 to-gray-900 
      flex items-center justify-center p-4">
      <motion.div
        className="max-w-2xl w-full"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        {/* Success Animation */}
        <motion.div
          className="flex justify-center mb-8"
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ delay: 0.2, type: "spring", stiffness: 200 }}
        >
          <div className="relative">
            <div className="absolute inset-0 bg-green-500 rounded-full blur-xl opacity-50"></div>
            <div className="relative bg-gradient-to-br from-green-500 to-green-600 rounded-full p-8">
              <CheckCircle className="w-20 h-20 text-white" />
            </div>
          </div>
        </motion.div>
        
        {/* Content */}
        <div className="bg-gray-900/80 backdrop-blur-sm rounded-lg p-8 text-center">
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.4 }}
          >
            <Crown className="w-12 h-12 text-yellow-400 mx-auto mb-4" />
            
            <h1 className="text-4xl font-bold text-white mb-4 font-cinzel">
              ¡Bienvenido a Premium!
            </h1>
            
            <p className="text-xl text-purple-200 mb-8">
              Tu cuenta ha sido actualizada exitosamente
            </p>
            
            {/* Benefits */}
            <div className="grid grid-cols-2 gap-4 mb-8 max-w-md mx-auto">
              {benefits.map((benefit, index) => (
                <motion.div
                  key={index}
                  className="bg-purple-900/30 rounded-lg p-4 flex items-center gap-3"
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.6 + index * 0.1 }}
                >
                  <div className="text-purple-400">
                    {benefit.icon}
                  </div>
                  <span className="text-white text-sm">
                    {benefit.text}
                  </span>
                </motion.div>
              ))}
            </div>
            
            {/* User Info */}
            {user && (
              <div className="bg-gray-800/50 rounded-lg p-4 mb-8">
                <p className="text-gray-400 mb-2">
                  Premium activo para:
                </p>
                <p className="text-xl text-white font-semibold">
                  {user.display_name || user.username}
                </p>
              </div>
            )}
            
            {/* CTA Button */}
            <motion.button
              onClick={() => router.push('/dashboard')}
              className="bg-gradient-to-r from-purple-600 to-purple-700 hover:from-purple-700 
                hover:to-purple-800 text-white font-bold py-4 px-8 rounded-lg text-lg
                transition-all transform hover:scale-105 flex items-center justify-center 
                gap-3 mx-auto"
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              Explorar Beneficios Premium
              <ArrowRight className="w-5 h-5" />
            </motion.button>
            
            <p className="text-gray-500 text-sm mt-6">
              Recibirás un correo de confirmación con los detalles de tu suscripción
            </p>
          </motion.div>
        </div>
      </motion.div>
    </div>
  );
}