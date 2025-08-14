'use client';

import React from 'react';
import { motion } from 'framer-motion';

interface PortalFallbackProps {
  isTyping?: boolean;
  loginError?: boolean;
  loginSuccess?: boolean;
}

export default function PortalFallback({ 
  isTyping = false, 
  loginError = false,
  loginSuccess = false 
}: PortalFallbackProps) {
  return (
    <div className="w-full h-64 md:h-96 relative overflow-hidden rounded-lg bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900">
      {/* Animated gradient background */}
      <motion.div
        className="absolute inset-0"
        animate={{
          background: loginError 
            ? ['linear-gradient(45deg, #ff4444 0%, #cc0000 100%)', 'linear-gradient(45deg, #cc0000 0%, #ff4444 100%)']
            : loginSuccess
            ? ['linear-gradient(45deg, #ffd700 0%, #ffed4e 100%)', 'linear-gradient(45deg, #ffed4e 0%, #ffd700 100%)']
            : ['linear-gradient(45deg, #8a2be2 0%, #4169e1 100%)', 'linear-gradient(45deg, #4169e1 0%, #8a2be2 100%)']
        }}
        transition={{ duration: 3, repeat: Infinity, repeatType: 'reverse' }}
      />
      
      {/* Portal visual effect with CSS */}
      <div className="absolute inset-0 flex items-center justify-center">
        <motion.div
          className="relative"
          animate={{ scale: loginSuccess ? 1.5 : 1 }}
          transition={{ duration: 0.5 }}
        >
          {/* Outer ring */}
          <motion.div
            className={`
              absolute inset-0 w-64 h-64 md:w-80 md:h-80 rounded-full 
              border-4 ${loginError ? 'border-red-400' : 'border-purple-400'}
              shadow-2xl
            `}
            animate={{ 
              rotate: isTyping ? 360 : 0,
              borderColor: loginError ? '#ff4444' : isTyping ? '#b784ff' : '#8a2be2'
            }}
            transition={{ 
              rotate: { duration: isTyping ? 2 : 10, repeat: Infinity, ease: 'linear' },
              borderColor: { duration: 0.3 }
            }}
            style={{
              boxShadow: loginError 
                ? '0 0 60px rgba(255, 68, 68, 0.7), inset 0 0 60px rgba(255, 68, 68, 0.3)'
                : '0 0 60px rgba(138, 43, 226, 0.7), inset 0 0 60px rgba(138, 43, 226, 0.3)'
            }}
          />
          
          {/* Inner ring */}
          <motion.div
            className={`
              absolute inset-8 rounded-full 
              border-2 ${loginError ? 'border-red-300' : 'border-blue-400'}
            `}
            animate={{ 
              rotate: isTyping ? -360 : 0,
              scale: isTyping ? [1, 1.1, 1] : 1
            }}
            transition={{ 
              rotate: { duration: isTyping ? 3 : 15, repeat: Infinity, ease: 'linear' },
              scale: { duration: 1, repeat: Infinity }
            }}
            style={{
              boxShadow: loginError 
                ? '0 0 40px rgba(255, 68, 68, 0.5)'
                : '0 0 40px rgba(65, 105, 225, 0.5)'
            }}
          />
          
          {/* Center portal effect */}
          <motion.div
            className="absolute inset-16 rounded-full bg-gradient-radial from-transparent via-purple-600/20 to-transparent"
            animate={{ 
              opacity: [0.3, 0.8, 0.3],
              scale: [0.8, 1.2, 0.8]
            }}
            transition={{ duration: 2, repeat: Infinity }}
          />
          
          {/* Particle effects using CSS */}
          {[...Array(8)].map((_, i) => (
            <motion.div
              key={i}
              className={`
                absolute w-2 h-2 rounded-full 
                ${loginError ? 'bg-red-400' : 'bg-purple-400'}
              `}
              style={{
                left: '50%',
                top: '50%',
                transform: `rotate(${i * 45}deg) translateX(${isTyping ? 140 : 120}px)`
              }}
              animate={{
                opacity: [0, 1, 0],
                scale: [0, 1.5, 0]
              }}
              transition={{
                duration: 2,
                repeat: Infinity,
                delay: i * 0.25
              }}
            />
          ))}
        </motion.div>
      </div>
      
      {/* Status text */}
      <div className="absolute bottom-4 left-0 right-0 text-center">
        <motion.p
          className={`
            text-sm font-mono uppercase tracking-wider
            ${loginError ? 'text-red-400' : 'text-purple-300'}
          `}
          animate={{ opacity: [0.5, 1, 0.5] }}
          transition={{ duration: 2, repeat: Infinity }}
        >
          {loginError ? 'Acceso Denegado' : loginSuccess ? 'Portal Abierto' : 'Portal de Invocación'}
        </motion.p>
      </div>
      
      {/* Accessibility description */}
      <span className="sr-only">
        Portal de invocación animado. 
        {loginError && 'Error de acceso detectado.'}
        {loginSuccess && 'Acceso concedido, portal abriéndose.'}
        {isTyping && 'Detectando entrada de usuario.'}
      </span>
    </div>
  );
}