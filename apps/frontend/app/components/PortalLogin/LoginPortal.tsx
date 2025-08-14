'use client';

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import BlenderPortal from './BlenderPortal';
import { useAudioEngine } from './AudioEngine';
import { Eye, EyeOff, Loader2, Sparkles, Zap } from 'lucide-react';

interface LoginPortalProps {
  onLogin: (email: string, password: string) => void;
  onShowDemoAccounts: () => void;
  loginError: string;
  onGuestMode?: () => void;
}

export default function LoginPortal({ 
  onLogin, 
  onShowDemoAccounts, 
  loginError,
  onGuestMode
}: LoginPortalProps) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [loginSuccess, setLoginSuccess] = useState(false);
  const [typingTimeout, setTypingTimeout] = useState<NodeJS.Timeout | null>(null);
  
  const { playSound } = useAudioEngine();

  // Handle typing detection
  const handleInputChange = (field: 'email' | 'password', value: string) => {
    if (field === 'email') {
      setEmail(value);
    } else {
      setPassword(value);
    }
    
    setIsTyping(true);
    
    // Clear existing timeout
    if (typingTimeout) {
      clearTimeout(typingTimeout);
    }
    
    // Set new timeout
    const timeout = setTimeout(() => {
      setIsTyping(false);
    }, 500);
    
    setTypingTimeout(timeout);
    
    // Play typing sound
    playSound('click', { volume: 0.1 });
  };

  // Handle form submission
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    
    // Simulate async login
    setTimeout(() => {
      onLogin(email, password);
      setIsLoading(false);
      
      if (!loginError) {
        setLoginSuccess(true);
        playSound('portal_success', { volume: 0.5 });
      }
    }, 1000);
  };

  // Cleanup timeout on unmount
  useEffect(() => {
    return () => {
      if (typingTimeout) {
        clearTimeout(typingTimeout);
      }
    };
  }, [typingTimeout]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900 to-indigo-900 flex items-center justify-center p-4">
      <motion.div 
        className="w-full max-w-5xl"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.5 }}
      >
        {/* Title Section */}
        <motion.div 
          className="text-center mb-8"
          initial={{ y: -20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.2 }}
        >
          <h1 className="text-5xl md:text-7xl font-bold text-white mb-4 font-cinzel relative">
            <span className="relative">
              Portal de Invocación
              <motion.span
                className="absolute -inset-1 bg-purple-600/20 blur-xl"
                animate={{ opacity: [0.5, 0.8, 0.5] }}
                transition={{ duration: 2, repeat: Infinity }}
              />
            </span>
          </h1>
          <p className="text-xl text-purple-300 font-orbitron">
            Un portal dimensional palpita con energía arcana... ¿Posees las credenciales para cruzar?
          </p>
        </motion.div>

        <div className="grid lg:grid-cols-2 gap-8 items-center">
          {/* Portal Animation */}
          <motion.div
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ delay: 0.4, duration: 0.5 }}
          >
            <BlenderPortal 
              isTyping={isTyping} 
              loginError={!!loginError}
              loginSuccess={loginSuccess}
              portalVersion="portal2" // Usar portal2 por defecto (más liviano)
            />
          </motion.div>

          {/* Login Form */}
          <motion.div
            initial={{ x: 50, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            transition={{ delay: 0.6 }}
            className="bg-black/30 backdrop-blur-lg rounded-2xl p-8 border border-purple-500/30"
          >
            <form onSubmit={handleSubmit} className="space-y-6">
              {/* Email Field */}
              <div className="space-y-2">
                <label htmlFor="email" className="text-purple-300 text-sm font-medium flex items-center gap-2">
                  <Sparkles className="w-4 h-4" />
                  Invocación del Hunter
                </label>
                <div className="relative">
                  <input
                    id="email"
                    type="email"
                    value={email}
                    onChange={(e) => handleInputChange('email', e.target.value)}
                    className={`
                      w-full px-4 py-3 bg-purple-900/30 border rounded-lg
                      text-white placeholder-purple-400/50
                      focus:outline-none focus:ring-2 focus:ring-purple-500
                      transition-all duration-300
                      ${loginError ? 'border-red-500' : 'border-purple-500/50'}
                    `}
                    placeholder="hunter@icfesquest.com"
                    required
                  />
                  <motion.div
                    className="absolute inset-0 rounded-lg pointer-events-none"
                    animate={{ 
                      boxShadow: isTyping && email ? 
                        '0 0 20px rgba(139, 92, 246, 0.5)' : 
                        '0 0 0px rgba(139, 92, 246, 0)'
                    }}
                  />
                </div>
              </div>

              {/* Password Field */}
              <div className="space-y-2">
                <label htmlFor="password" className="text-purple-300 text-sm font-medium flex items-center gap-2">
                  <Zap className="w-4 h-4" />
                  Clave Dimensional
                </label>
                <div className="relative">
                  <input
                    id="password"
                    type={showPassword ? 'text' : 'password'}
                    value={password}
                    onChange={(e) => handleInputChange('password', e.target.value)}
                    className={`
                      w-full px-4 py-3 bg-purple-900/30 border rounded-lg
                      text-white placeholder-purple-400/50
                      focus:outline-none focus:ring-2 focus:ring-purple-500
                      transition-all duration-300 pr-12
                      ${loginError ? 'border-red-500' : 'border-purple-500/50'}
                    `}
                    placeholder="••••••••"
                    required
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-purple-400 hover:text-purple-300 transition-colors"
                  >
                    {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                  </button>
                  <motion.div
                    className="absolute inset-0 rounded-lg pointer-events-none"
                    animate={{ 
                      boxShadow: isTyping && password ? 
                        '0 0 20px rgba(139, 92, 246, 0.5)' : 
                        '0 0 0px rgba(139, 92, 246, 0)'
                    }}
                  />
                </div>
              </div>

              {/* Error Message */}
              <AnimatePresence>
                {loginError && (
                  <motion.div
                    initial={{ opacity: 0, y: -10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                    className="bg-red-500/20 border border-red-500/50 rounded-lg p-3"
                  >
                    <p className="text-red-300 text-sm flex items-center gap-2">
                      <span className="text-red-400">⚠️</span>
                      {loginError}
                    </p>
                  </motion.div>
                )}
              </AnimatePresence>

              {/* Submit Button */}
              <motion.button
                type="submit"
                disabled={isLoading || !email || !password}
                className={`
                  w-full py-3 rounded-lg font-semibold text-white
                  transition-all duration-300 relative overflow-hidden
                  ${isLoading || !email || !password 
                    ? 'bg-gray-600 cursor-not-allowed' 
                    : 'bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700'
                  }
                `}
                whileHover={{ scale: (!isLoading && email && password) ? 1.02 : 1 }}
                whileTap={{ scale: (!isLoading && email && password) ? 0.98 : 1 }}
              >
                <span className="relative z-10 flex items-center justify-center gap-2">
                  {isLoading ? (
                    <>
                      <Loader2 className="w-5 h-5 animate-spin" />
                      Invocando Portal...
                    </>
                  ) : (
                    'Cruzar el Portal'
                  )}
                </span>
                {/* Animated background */}
                <motion.div
                  className="absolute inset-0 bg-gradient-to-r from-purple-600/50 to-blue-600/50"
                  initial={{ x: '-100%' }}
                  animate={{ x: isLoading ? '0%' : '-100%' }}
                  transition={{ duration: 1 }}
                />
              </motion.button>

              {/* Additional Options */}
              <div className="flex flex-col gap-3 pt-4 border-t border-purple-500/30">
                <button
                  type="button"
                  onClick={onShowDemoAccounts}
                  className="text-purple-300 hover:text-purple-200 text-sm transition-colors flex items-center justify-center gap-2"
                >
                  <span>Ver Cuentas Demo</span>
                  <span className="text-purple-400">→</span>
                </button>
                
                {onGuestMode && (
                  <button
                    type="button"
                    onClick={onGuestMode}
                    className="bg-purple-900/30 hover:bg-purple-900/50 text-purple-300 py-2 px-4 rounded-lg transition-all duration-300 text-sm"
                  >
                    <div className="flex items-center justify-center gap-2">
                      <span>🎮</span>
                      <span>Modo Invitado: Mini-Quiz (5 preguntas)</span>
                    </div>
                  </button>
                )}
              </div>
            </form>

            {/* Portal Status */}
            <motion.div 
              className="mt-6 text-center"
              animate={{ opacity: [0.5, 1, 0.5] }}
              transition={{ duration: 2, repeat: Infinity }}
            >
              <p className="text-xs text-purple-400 font-mono">
                SISTEMA: {loginSuccess ? 'ACCESO CONCEDIDO' : 'ESPERANDO CREDENCIALES'}
              </p>
            </motion.div>
          </motion.div>
        </div>

        {/* Demo Carousel (placeholder) */}
        <motion.div
          initial={{ y: 50, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.8 }}
          className="mt-12 text-center"
        >
          <p className="text-purple-300 text-sm mb-4">Desliza para ver el poder de los Hunters</p>
          <div className="flex justify-center gap-4 overflow-x-auto pb-4">
            {[1, 2, 3].map((i) => (
              <motion.div
                key={i}
                className="flex-shrink-0 w-64 h-32 bg-purple-900/30 rounded-lg border border-purple-500/30 flex items-center justify-center"
                whileHover={{ scale: 1.05 }}
              >
                <p className="text-purple-300">Demo {i}</p>
              </motion.div>
            ))}
          </div>
        </motion.div>
      </motion.div>
    </div>
  );
}