'use client';

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useRouter } from 'next/navigation';
import { Eye, EyeOff, Loader2, Sparkles, Zap, AlertCircle, CheckCircle, User, Shield, Play, Wand2 } from 'lucide-react';
import { authService } from '../services/auth.service';
import Link from 'next/link';

interface FormErrors {
  username?: string;
  password?: string;
  general?: string;
}

export default function PortalLoginPage() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [loginSuccess, setLoginSuccess] = useState(false);
  const [errors, setErrors] = useState<FormErrors>({});
  const [touchedFields, setTouchedFields] = useState<{[key: string]: boolean}>({});
  const [loginAttempts, setLoginAttempts] = useState(0);
  const [isTyping, setIsTyping] = useState(false);
  const [portalEnergy, setPortalEnergy] = useState(0);
  const [showPortalAnimation, setShowPortalAnimation] = useState(false);
  
  const router = useRouter();

  // Portal energy animation effect
  useEffect(() => {
    if (username || password) {
      setPortalEnergy(Math.min(100, (username.length + password.length) * 5));
    } else {
      setPortalEnergy(0);
    }
  }, [username, password]);

  // Validation functions
  const validateUsername = (value: string): string | undefined => {
    if (!value.trim()) return 'El usuario es requerido para acceder al portal';
    if (value.length < 2) return 'El nombre del Hunter debe tener al menos 2 caracteres';
    return undefined;
  };

  const validatePassword = (value: string): string | undefined => {
    if (!value) return 'La clave dimensional es requerida';
    if (value.length < 3) return 'La clave debe tener al menos 3 caracteres';
    return undefined;
  };

  const validateForm = () => {
    const newErrors: FormErrors = {};
    
    const usernameError = validateUsername(username);
    const passwordError = validatePassword(password);
    
    if (usernameError) newErrors.username = usernameError;
    if (passwordError) newErrors.password = passwordError;
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // Real-time validation
  useEffect(() => {
    if (touchedFields.username || touchedFields.password) {
      validateForm();
    }
  }, [username, password, touchedFields]);

  const handleFieldBlur = (fieldName: string) => {
    setTouchedFields(prev => ({ ...prev, [fieldName]: true }));
  };

  const handleInputChange = (field: 'username' | 'password', value: string) => {
    if (field === 'username') {
      setUsername(value);
    } else {
      setPassword(value);
    }
    
    setIsTyping(true);
    setTimeout(() => setIsTyping(false), 500);
  };

  const handlePortalLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Mark all fields as touched
    setTouchedFields({ username: true, password: true });
    
    if (!validateForm()) {
      return;
    }

    setIsLoading(true);
    setErrors({});
    setShowPortalAnimation(true);
    setLoginAttempts(prev => prev + 1);

    try {
      const data = await authService.login({
        username: username.trim(),
        password
      });
      
      // Store user data
      localStorage.setItem('user', JSON.stringify(data.user));
      localStorage.setItem('access_token', data.access_token);
      
      setLoginSuccess(true);
      
      // Portal success animation
      setTimeout(() => {
        router.push('/hub-central');
      }, 2000);
      
    } catch (error: any) {
      const errorMessage = error.message || 'Error de conexión dimensional';
      
      // Enhanced error handling for portal theme
      if (errorMessage.includes('Usuario no encontrado')) {
        setErrors({ username: 'Hunter no registrado en el portal dimensional' });
      } else if (errorMessage.includes('Contraseña incorrecta')) {
        setErrors({ password: 'Clave dimensional incorrecta' });
      } else {
        setErrors({ general: `Portal dimensional inaccesible: ${errorMessage}` });
      }
      
      setShowPortalAnimation(false);
    } finally {
      setIsLoading(false);
    }
  };

  const quickPortalAccess = async (userAccount: string) => {
    setUsername(userAccount);
    setPassword('secret');
    setTouchedFields({ username: true, password: true });
    
    // Auto-submit after setting values
    setTimeout(async () => {
      setIsLoading(true);
      setShowPortalAnimation(true);
      try {
        const data = await authService.login({
          username: userAccount,
          password: 'secret'
        });
        
        localStorage.setItem('user', JSON.stringify(data.user));
        localStorage.setItem('access_token', data.access_token);
        
        setLoginSuccess(true);
        
        setTimeout(() => {
          router.push('/hub-central');
        }, 1500);
        
      } catch (error: any) {
        setErrors({ general: `Error en acceso rápido: ${error.message}` });
        setShowPortalAnimation(false);
      } finally {
        setIsLoading(false);
      }
    }, 300);
  };

  const testAccounts = [
    { username: 'admin', description: 'Portal Maestro', level: 50, rank: 'S', color: 'from-gold-400 to-yellow-600' },
    { username: 'test', description: 'Portal Novato', level: 1, rank: 'E', color: 'from-blue-400 to-cyan-600' },
    { username: 'student1', description: 'Portal Estudiante', level: 5, rank: 'D', color: 'from-green-400 to-emerald-600' }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-900 via-purple-900 to-pink-900 flex items-center justify-center p-4 relative overflow-hidden">
      {/* Animated Background Elements */}
      <div className="absolute inset-0">
        <div className="absolute top-1/4 left-1/4 w-64 h-64 bg-purple-500/10 rounded-full blur-3xl animate-pulse"></div>
        <div className="absolute top-3/4 right-1/4 w-48 h-48 bg-blue-500/10 rounded-full blur-2xl animate-pulse delay-1000"></div>
        <div className="absolute top-1/2 left-1/2 w-32 h-32 bg-pink-500/10 rounded-full blur-xl animate-pulse delay-500"></div>
      </div>

      <div className="relative z-10 w-full max-w-6xl">
        {/* Portal Header */}
        <motion.div 
          className="text-center mb-12"
          initial={{ opacity: 0, y: -50 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, ease: "easeOut" }}
        >
          <motion.h1 
            className="text-6xl md:text-8xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-purple-400 via-pink-400 to-blue-400 mb-4 relative"
            animate={{ 
              backgroundPosition: isTyping ? '100% 0%' : '0% 0%',
              scale: isTyping ? 1.02 : 1
            }}
            transition={{ duration: 0.3 }}
          >
            ⚡ Portal de Invocación ⚡
            <motion.div
              className="absolute inset-0 bg-gradient-to-r from-purple-600/20 to-blue-600/20 blur-2xl"
              animate={{ opacity: portalEnergy > 0 ? 0.6 : 0.2 }}
              transition={{ duration: 0.5 }}
            />
          </motion.h1>
          
          <motion.p 
            className="text-xl text-purple-200 mb-4"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.5 }}
          >
            Los portales dimensionales palpitan con energía arcana...
          </motion.p>

          {/* Portal Energy Bar */}
          <motion.div 
            className="w-full max-w-md mx-auto bg-gray-800/50 rounded-full h-2 overflow-hidden"
            initial={{ opacity: 0, width: 0 }}
            animate={{ opacity: 1, width: "100%" }}
            transition={{ delay: 0.7, duration: 0.5 }}
          >
            <motion.div 
              className="h-full bg-gradient-to-r from-purple-500 to-blue-500"
              animate={{ width: `${portalEnergy}%` }}
              transition={{ duration: 0.3 }}
            />
          </motion.div>
          <p className="text-xs text-gray-400 mt-2">Energía Portal: {portalEnergy}%</p>
        </motion.div>

        <div className="grid lg:grid-cols-2 gap-12 items-center">
          {/* Portal Visualization */}
          <motion.div
            className="relative"
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.3, duration: 0.8 }}
          >
            <div className={`
              relative w-80 h-80 mx-auto rounded-full border-4 
              transition-all duration-500
              ${showPortalAnimation 
                ? 'border-green-400 shadow-green-400/50 shadow-2xl' 
                : errors.general 
                ? 'border-red-400 shadow-red-400/50 shadow-2xl'
                : 'border-purple-400/50 shadow-purple-400/30 shadow-xl'
              }
            `}>
              {/* Portal Rings */}
              {[1, 2, 3].map((ring) => (
                <motion.div
                  key={ring}
                  className={`
                    absolute inset-4 rounded-full border-2 
                    ${showPortalAnimation 
                      ? 'border-green-400/30' 
                      : loginSuccess
                      ? 'border-gold-400/30'
                      : 'border-purple-400/20'
                    }
                  `}
                  animate={{ 
                    rotate: isLoading ? 360 : 0,
                    scale: isTyping ? 1.1 - (ring * 0.05) : 1 - (ring * 0.1)
                  }}
                  transition={{ 
                    rotate: { duration: 3 + ring, repeat: Infinity, ease: "linear" },
                    scale: { duration: 0.3 }
                  }}
                  style={{ margin: `${ring * 12}px` }}
                />
              ))}
              
              {/* Portal Center */}
              <motion.div 
                className={`
                  absolute inset-16 rounded-full flex items-center justify-center text-6xl
                  ${loginSuccess 
                    ? 'bg-gradient-to-br from-green-400/30 to-emerald-600/30' 
                    : 'bg-gradient-to-br from-purple-400/20 to-blue-600/20'
                  }
                `}
                animate={{ 
                  scale: isLoading ? [1, 1.1, 1] : 1,
                  rotate: showPortalAnimation ? 360 : 0
                }}
                transition={{ 
                  scale: { duration: 1, repeat: isLoading ? Infinity : 0 },
                  rotate: { duration: 2, ease: "easeInOut" }
                }}
              >
                {loginSuccess ? '✨' : isLoading ? '🌀' : errors.general ? '⚠️' : '🎮'}
              </motion.div>
            </div>
          </motion.div>

          {/* Login Form */}
          <motion.div
            className="bg-black/40 backdrop-blur-xl rounded-2xl p-8 border border-purple-500/30 shadow-2xl"
            initial={{ opacity: 0, x: 50 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.5, duration: 0.8 }}
          >
            <form onSubmit={handlePortalLogin} className="space-y-6">
              {/* Username Field */}
              <div className="space-y-2">
                <label className="flex items-center gap-2 text-purple-300 text-sm font-medium">
                  <User className="w-4 h-4" />
                  Nombre del Hunter
                </label>
                <div className="relative">
                  <input
                    type="text"
                    value={username}
                    onChange={(e) => handleInputChange('username', e.target.value)}
                    onBlur={() => handleFieldBlur('username')}
                    className={`
                      w-full px-4 py-3 pl-11 bg-purple-900/30 border rounded-lg text-white 
                      placeholder-purple-400/50 focus:outline-none focus:ring-2 
                      transition-all duration-300
                      ${errors.username && touchedFields.username 
                        ? 'border-red-500 focus:ring-red-400/50' 
                        : 'border-purple-500/50 focus:ring-purple-400/50'
                      }
                    `}
                    placeholder="admin, test, student1..."
                  />
                  <User className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-purple-400" />
                  {touchedFields.username && !errors.username && username && (
                    <CheckCircle className="absolute right-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-green-400" />
                  )}
                </div>
                {errors.username && touchedFields.username && (
                  <motion.div 
                    className="flex items-center gap-2 text-red-400 text-sm"
                    initial={{ opacity: 0, y: -10 }}
                    animate={{ opacity: 1, y: 0 }}
                  >
                    <AlertCircle className="w-4 h-4" />
                    {errors.username}
                  </motion.div>
                )}
              </div>

              {/* Password Field */}
              <div className="space-y-2">
                <label className="flex items-center gap-2 text-purple-300 text-sm font-medium">
                  <Shield className="w-4 h-4" />
                  Clave Dimensional
                </label>
                <div className="relative">
                  <input
                    type={showPassword ? 'text' : 'password'}
                    value={password}
                    onChange={(e) => handleInputChange('password', e.target.value)}
                    onBlur={() => handleFieldBlur('password')}
                    className={`
                      w-full px-4 py-3 pl-11 pr-11 bg-purple-900/30 border rounded-lg text-white 
                      placeholder-purple-400/50 focus:outline-none focus:ring-2 
                      transition-all duration-300
                      ${errors.password && touchedFields.password 
                        ? 'border-red-500 focus:ring-red-400/50' 
                        : 'border-purple-500/50 focus:ring-purple-400/50'
                      }
                    `}
                    placeholder="secret"
                  />
                  <Shield className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-purple-400" />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 transform -translate-y-1/2 text-purple-400 hover:text-purple-300 transition-colors"
                    tabIndex={-1}
                  >
                    {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                  </button>
                </div>
                {errors.password && touchedFields.password && (
                  <motion.div 
                    className="flex items-center gap-2 text-red-400 text-sm"
                    initial={{ opacity: 0, y: -10 }}
                    animate={{ opacity: 1, y: 0 }}
                  >
                    <AlertCircle className="w-4 h-4" />
                    {errors.password}
                  </motion.div>
                )}
              </div>

              {/* General Error */}
              <AnimatePresence>
                {errors.general && (
                  <motion.div
                    initial={{ opacity: 0, y: -10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                    className="p-4 bg-red-500/20 border border-red-500/50 rounded-lg"
                  >
                    <div className="flex items-center gap-3">
                      <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0" />
                      <p className="text-red-300 text-sm">{errors.general}</p>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>

              {/* Success Message */}
              <AnimatePresence>
                {loginSuccess && (
                  <motion.div
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    className="p-4 bg-green-500/20 border border-green-500/50 rounded-lg"
                  >
                    <div className="flex items-center gap-3">
                      <CheckCircle className="w-5 h-5 text-green-400" />
                      <p className="text-green-300 text-sm">Portal activado! Transportando...</p>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>

              {/* Submit Button */}
              <motion.button
                type="submit"
                disabled={isLoading || loginAttempts >= 5}
                className={`
                  w-full py-3 rounded-lg font-bold text-lg transition-all duration-300 
                  flex items-center justify-center gap-2 relative overflow-hidden
                  ${isLoading 
                    ? 'bg-purple-600/50 cursor-not-allowed' 
                    : loginAttempts >= 5
                    ? 'bg-red-600/50 cursor-not-allowed'
                    : 'bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 hover:scale-105'
                  }
                `}
                whileTap={{ scale: isLoading ? 1 : 0.98 }}
              >
                {isLoading ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    Invocando Portal...
                  </>
                ) : loginAttempts >= 5 ? (
                  '🔒 Portal Bloqueado'
                ) : (
                  <>
                    <Wand2 className="w-5 h-5" />
                    Activar Portal Dimensional
                  </>
                )}
              </motion.button>
            </form>

            {/* Quick Access Portals */}
            <div className="mt-8">
              <h3 className="text-lg font-bold text-purple-300 mb-4 text-center">
                ⚡ Portales de Acceso Rápido
              </h3>
              <div className="grid grid-cols-1 gap-3">
                {testAccounts.map((account, index) => (
                  <motion.button
                    key={account.username}
                    onClick={() => quickPortalAccess(account.username)}
                    disabled={isLoading}
                    className={`
                      p-4 bg-gradient-to-r ${account.color} opacity-20 hover:opacity-30 
                      border border-current rounded-lg transition-all duration-200 
                      hover:scale-105 disabled:opacity-10 disabled:cursor-not-allowed
                    `}
                    whileHover={{ scale: isLoading ? 1 : 1.02 }}
                    whileTap={{ scale: isLoading ? 1 : 0.98 }}
                  >
                    <div className="text-white text-left">
                      <div className="font-bold">{account.description}</div>
                      <div className="text-sm opacity-80">
                        Usuario: {account.username} | Nivel {account.level} | Rango {account.rank}
                      </div>
                    </div>
                  </motion.button>
                ))}
              </div>
            </div>

            {/* Navigation */}
            <div className="mt-8 flex flex-col gap-3 text-center text-sm">
              <Link 
                href="/login" 
                className="text-purple-400 hover:text-purple-300 transition-colors"
              >
                ← Portal Clásico
              </Link>
              <Link 
                href="/login-test" 
                className="text-blue-400 hover:text-blue-300 transition-colors"
              >
                🧪 Sistema de Pruebas
              </Link>
            </div>
          </motion.div>
        </div>
      </div>
    </div>
  );
}