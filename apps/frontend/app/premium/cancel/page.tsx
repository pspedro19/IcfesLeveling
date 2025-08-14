'use client';

import React from 'react';
import { useRouter } from 'next/navigation';
import { motion } from 'framer-motion';
import { 
  XCircle, 
  ArrowLeft,
  HelpCircle,
  MessageSquare,
  RefreshCw
} from 'lucide-react';
import { useAudio } from '@/components/PortalLogin/AudioEngine';
import { trackGameEvent } from '@/lib/analytics';

export default function PremiumCancelPage() {
  const router = useRouter();
  const { playSound } = useAudio();
  
  const handleRetry = () => {
    playSound('typing_click');
    trackGameEvent('premium_retry_from_cancel');
    router.push('/premium');
  };
  
  const handleGoBack = () => {
    playSound('typing_click');
    trackGameEvent('premium_cancel_confirmed');
    router.push('/');
  };
  
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900 to-gray-900 
      flex items-center justify-center p-4">
      <motion.div
        className="max-w-lg w-full"
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
      >
        <div className="bg-gray-900/80 backdrop-blur-sm rounded-lg p-8 text-center">
          {/* Cancel Icon */}
          <motion.div
            className="flex justify-center mb-6"
            initial={{ rotate: -180, opacity: 0 }}
            animate={{ rotate: 0, opacity: 1 }}
            transition={{ delay: 0.2 }}
          >
            <div className="bg-red-900/30 rounded-full p-6">
              <XCircle className="w-16 h-16 text-red-400" />
            </div>
          </motion.div>
          
          <h1 className="text-3xl font-bold text-white mb-4 font-cinzel">
            Pago Cancelado
          </h1>
          
          <p className="text-gray-300 mb-8">
            No se realizó ningún cargo. Puedes volver a intentarlo cuando quieras.
          </p>
          
          {/* Help Section */}
          <div className="bg-gray-800/50 rounded-lg p-6 mb-8">
            <h3 className="text-lg font-semibold text-white mb-4 flex items-center justify-center gap-2">
              <HelpCircle className="w-5 h-5" />
              ¿Tuviste algún problema?
            </h3>
            
            <div className="space-y-3 text-sm">
              <p className="text-gray-400">
                Problemas comunes:
              </p>
              
              <ul className="text-left text-gray-300 space-y-2 max-w-sm mx-auto">
                <li className="flex items-start gap-2">
                  <span className="text-purple-400 mt-1">•</span>
                  <span>Verifica que tu tarjeta tenga fondos suficientes</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-purple-400 mt-1">•</span>
                  <span>Algunos bancos requieren autorización para pagos en línea</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-purple-400 mt-1">•</span>
                  <span>Intenta con una tarjeta diferente</span>
                </li>
              </ul>
            </div>
          </div>
          
          {/* Action Buttons */}
          <div className="flex flex-col sm:flex-row gap-4">
            <button
              onClick={handleRetry}
              className="flex-1 bg-gradient-to-r from-purple-600 to-purple-700 
                hover:from-purple-700 hover:to-purple-800 text-white font-bold 
                py-3 px-6 rounded-lg transition-all flex items-center justify-center gap-2"
            >
              <RefreshCw className="w-5 h-5" />
              Intentar de Nuevo
            </button>
            
            <button
              onClick={handleGoBack}
              className="flex-1 bg-gray-700 hover:bg-gray-600 text-white 
                font-semibold py-3 px-6 rounded-lg transition-all flex items-center 
                justify-center gap-2"
            >
              <ArrowLeft className="w-5 h-5" />
              Volver al Inicio
            </button>
          </div>
          
          {/* Support Link */}
          <button
            onClick={() => {
              playSound('typing_click');
              // Open support chat or email
              window.open('mailto:support@icfesleveling.com', '_blank');
            }}
            className="mt-6 text-purple-400 hover:text-purple-300 text-sm 
              transition-colors flex items-center justify-center gap-2 mx-auto"
          >
            <MessageSquare className="w-4 h-4" />
            Contactar Soporte
          </button>
        </div>
      </motion.div>
    </div>
  );
}