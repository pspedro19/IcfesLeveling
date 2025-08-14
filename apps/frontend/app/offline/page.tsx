'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { WifiOff, RefreshCw, Swords, Shield, Star } from 'lucide-react';

export default function OfflinePage() {
  const handleReload = () => {
    if ('serviceWorker' in navigator && navigator.serviceWorker.controller) {
      // Check if we're back online
      if (navigator.onLine) {
        window.location.reload();
      } else {
        // Still offline, show message
        alert('Aún no hay conexión. Intenta más tarde.');
      }
    } else {
      window.location.reload();
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900 to-indigo-900 flex items-center justify-center p-4">
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        className="max-w-md w-full"
      >
        <div className="bg-black/40 backdrop-blur-md rounded-2xl p-8 border-2 border-purple-500/30 text-center">
          {/* Offline Icon */}
          <motion.div
            initial={{ rotate: 0 }}
            animate={{ rotate: 360 }}
            transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
            className="inline-block mb-6"
          >
            <div className="relative">
              <WifiOff className="w-20 h-20 text-orange-400" />
              <motion.div
                className="absolute inset-0"
                animate={{ scale: [1, 1.2, 1] }}
                transition={{ duration: 2, repeat: Infinity }}
              >
                <WifiOff className="w-20 h-20 text-orange-400 opacity-30" />
              </motion.div>
            </div>
          </motion.div>

          <h1 className="text-3xl font-bold text-white mb-4 font-cinzel">
            Portal Sin Conexión
          </h1>
          
          <p className="text-purple-300 mb-8 text-lg">
            El Sistema no puede establecer conexión con las dimensiones principales.
            Estás en modo supervivencia offline.
          </p>

          {/* Offline Features */}
          <div className="space-y-4 mb-8">
            <div className="bg-purple-900/30 rounded-lg p-4 border border-purple-500/30">
              <h3 className="text-white font-semibold mb-2 flex items-center justify-center gap-2">
                <Swords className="w-5 h-5 text-purple-400" />
                Modo Práctica Offline
              </h3>
              <p className="text-sm text-purple-300">
                Las batallas de práctica están disponibles con enemigos cacheados
              </p>
            </div>

            <div className="bg-purple-900/30 rounded-lg p-4 border border-purple-500/30">
              <h3 className="text-white font-semibold mb-2 flex items-center justify-center gap-2">
                <Shield className="w-5 h-5 text-blue-400" />
                Progreso Guardado
              </h3>
              <p className="text-sm text-purple-300">
                Tu progreso se sincronizará cuando recuperes la conexión
              </p>
            </div>

            <div className="bg-purple-900/30 rounded-lg p-4 border border-purple-500/30">
              <h3 className="text-white font-semibold mb-2 flex items-center justify-center gap-2">
                <Star className="w-5 h-5 text-yellow-400" />
                Misiones en Cola
              </h3>
              <p className="text-sm text-purple-300">
                Las misiones completadas se validarán al reconectar
              </p>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="space-y-3">
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={handleReload}
              className="w-full bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white font-bold py-3 px-6 rounded-lg transition-all duration-300 flex items-center justify-center gap-2"
            >
              <RefreshCw className="w-5 h-5" />
              Reintentar Conexión
            </motion.button>

            <button
              onClick={() => window.history.back()}
              className="w-full bg-gray-700 hover:bg-gray-600 text-white font-semibold py-3 px-6 rounded-lg transition-all duration-300"
            >
              Volver
            </button>
          </div>

          {/* Connection Status */}
          <motion.div
            className="mt-6 text-sm"
            animate={{ opacity: [0.5, 1, 0.5] }}
            transition={{ duration: 2, repeat: Infinity }}
          >
            <p className="text-orange-400">
              Estado: {navigator.onLine ? 'Online (Recargando...)' : 'Sin Conexión'}
            </p>
          </motion.div>
        </div>
      </motion.div>
    </div>
  );
}