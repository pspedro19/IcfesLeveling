'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { authService } from '../services/auth.service.simple';
import { Eye, EyeOff, User, Lock, AlertCircle, CheckCircle, Loader2 } from 'lucide-react';

interface FormErrors {
  username?: string;
  password?: string;
  general?: string;
}

export default function LoginPage() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [errors, setErrors] = useState<FormErrors>({});
  const [touchedFields, setTouchedFields] = useState<{[key: string]: boolean}>({});
  const [loginAttempts, setLoginAttempts] = useState(0);
  const [isFormValid, setIsFormValid] = useState(false);
  const router = useRouter();

  // Validation functions
  const validateUsername = (value: string): string | undefined => {
    if (!value.trim()) return 'El usuario es requerido';
    if (value.length < 2) return 'El usuario debe tener al menos 2 caracteres';
    return undefined;
  };

  const validatePassword = (value: string): string | undefined => {
    if (!value) return 'La contraseña es requerida';
    if (value.length < 3) return 'La contraseña debe tener al menos 3 caracteres';
    return undefined;
  };

  const validateForm = () => {
    const newErrors: FormErrors = {};
    
    const usernameError = validateUsername(username);
    const passwordError = validatePassword(password);
    
    if (usernameError) newErrors.username = usernameError;
    if (passwordError) newErrors.password = passwordError;
    
    setErrors(newErrors);
    const isValid = Object.keys(newErrors).length === 0;
    setIsFormValid(isValid);
    return isValid;
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

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Mark all fields as touched
    setTouchedFields({ username: true, password: true });
    
    if (!validateForm()) {
      return;
    }

    setIsLoading(true);
    setErrors({});
    setLoginAttempts(prev => prev + 1);

    try {
      const data = await authService.login({
        username: username.trim(),
        password
      });
      
      console.log('🔐 Datos de login recibidos:', data);
      
      // Store user data
      localStorage.setItem('user', JSON.stringify(data.user));
      localStorage.setItem('access_token', data.access_token);
      console.log('💾 Token guardado en localStorage');
      
      // Show success message with user info
      const welcomeMessage = `¡Bienvenido de vuelta, ${data.user?.username || data.user?.display_name || 'Hunter'}! 
Nivel: ${data.user?.level || 1} | Rango: ${data.user?.rank || 'E'}`;
      
      // Success notification
      setErrors({ general: '' });
      
      // Redirect after brief delay to show success
      setTimeout(() => {
        router.push('/hub-central');
      }, 1000);
      
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || error.message || 'Error de conexión. Intenta nuevamente.';
      
      // Enhanced error handling
      if (errorMessage.includes('Usuario no encontrado')) {
        setErrors({ username: 'Usuario no encontrado' });
      } else if (errorMessage.includes('Contraseña incorrecta')) {
        setErrors({ password: 'Contraseña incorrecta' });
      } else {
        setErrors({ general: errorMessage });
      }
      
      // Rate limiting feedback
      if (loginAttempts >= 3) {
        setErrors({ general: 'Demasiados intentos fallidos. Espera un momento antes de intentar nuevamente.' });
      }
    } finally {
      setIsLoading(false);
    }
  };

  const quickLogin = async (user: string) => {
    setUsername(user);
    setPassword('secret');
    setTouchedFields({ username: true, password: true });
    
    // Clear previous errors
    setErrors({});
    
    // Auto-submit after setting values
    setTimeout(async () => {
      setIsLoading(true);
      try {
        const data = await authService.login({
          username: user,
          password: 'secret'
        });
        
        localStorage.setItem('user', JSON.stringify(data.user));
        localStorage.setItem('access_token', data.access_token);
        
        setTimeout(() => {
          router.push('/hub-central');
        }, 500);
        
      } catch (error: any) {
        const errorMessage = error.response?.data?.detail || error.message || 'Error en login rápido';
        setErrors({ general: errorMessage });
      } finally {
        setIsLoading(false);
      }
    }, 100);
  };

  // Additional account for student1
  const testAccounts = [
    { username: 'admin', level: 50, rank: 'S', description: 'Administrador' },
    { username: 'test', level: 1, rank: 'E', description: 'Usuario de Prueba' },
    { username: 'student1', level: 5, rank: 'D', description: 'Estudiante Activo' }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 text-white flex items-center justify-center p-4">
      <div className="max-w-md w-full">
        <div className="bg-black/40 backdrop-blur-lg rounded-xl p-8 border border-purple-500/30 shadow-2xl">
          <div className="text-center mb-8">
            <div className="mb-4">
              <h1 className="text-4xl font-bold mb-2 bg-gradient-to-r from-gold-400 to-purple-400 bg-clip-text text-transparent">
                🎮 Hunter Login
              </h1>
            </div>
            <p className="text-gray-300">Acceso al sistema IcfesLeveling</p>
            {loginAttempts > 0 && (
              <div className="mt-2 text-xs text-gray-400">
                Intentos: {loginAttempts}/5
              </div>
            )}
          </div>

          <form onSubmit={handleLogin} className="space-y-6">
            {/* Username Field */}
            <div className="space-y-2">
              <label className="flex items-center gap-2 text-sm font-medium text-gray-200">
                <User className="w-4 h-4" />
                Usuario
              </label>
              <div className="relative">
                <input
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  onBlur={() => handleFieldBlur('username')}
                  className={`
                    w-full px-4 py-3 pl-11 bg-black/30 border rounded-lg text-white 
                    placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-purple-400/50 
                    transition-all duration-200
                    ${errors.username && touchedFields.username 
                      ? 'border-red-500 focus:ring-red-400/50' 
                      : isFormValid && touchedFields.username
                      ? 'border-green-500 focus:ring-green-400/50'
                      : 'border-purple-500/50'
                    }
                  `}
                  placeholder="admin, test o student1"
                />
                <User className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                {touchedFields.username && !errors.username && username && (
                  <CheckCircle className="absolute right-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-green-400" />
                )}
              </div>
              {errors.username && touchedFields.username && (
                <div className="flex items-center gap-2 text-red-400 text-sm">
                  <AlertCircle className="w-4 h-4" />
                  {errors.username}
                </div>
              )}
            </div>

            {/* Password Field */}
            <div className="space-y-2">
              <label className="flex items-center gap-2 text-sm font-medium text-gray-200">
                <Lock className="w-4 h-4" />
                Contraseña
              </label>
              <div className="relative">
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  onBlur={() => handleFieldBlur('password')}
                  className={`
                    w-full px-4 py-3 pl-11 pr-11 bg-black/30 border rounded-lg text-white 
                    placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-purple-400/50 
                    transition-all duration-200
                    ${errors.password && touchedFields.password 
                      ? 'border-red-500 focus:ring-red-400/50' 
                      : isFormValid && touchedFields.password
                      ? 'border-green-500 focus:ring-green-400/50'
                      : 'border-purple-500/50'
                    }
                  `}
                  placeholder="secret"
                />
                <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-300 transition-colors"
                  tabIndex={-1}
                >
                  {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                </button>
              </div>
              {errors.password && touchedFields.password && (
                <div className="flex items-center gap-2 text-red-400 text-sm">
                  <AlertCircle className="w-4 h-4" />
                  {errors.password}
                </div>
              )}
            </div>

            {/* General Error */}
            {errors.general && (
              <div className="p-4 bg-red-500/20 border border-red-500/50 rounded-lg">
                <div className="flex items-center gap-3">
                  <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0" />
                  <p className="text-red-300 text-sm">{errors.general}</p>
                </div>
              </div>
            )}

            {/* Success Message */}
            {isLoading && !errors.general && (
              <div className="p-4 bg-green-500/20 border border-green-500/50 rounded-lg">
                <div className="flex items-center gap-3">
                  <CheckCircle className="w-5 h-5 text-green-400" />
                  <p className="text-green-300 text-sm">Iniciando sesión...</p>
                </div>
              </div>
            )}

            {/* Submit Button */}
            <button
              type="submit"
              disabled={isLoading || loginAttempts >= 5}
              className={`
                w-full py-3 rounded-lg font-bold text-lg transition-all duration-300 
                flex items-center justify-center gap-2
                ${isLoading || loginAttempts >= 5
                  ? 'bg-gray-600 cursor-not-allowed opacity-50' 
                  : isFormValid && !isLoading
                  ? 'bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 hover:scale-105 hover:shadow-lg'
                  : 'bg-gradient-to-r from-gray-600 to-gray-700'
                }
              `}
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  Iniciando sesión...
                </>
              ) : loginAttempts >= 5 ? (
                '🔒 Cuenta bloqueada temporalmente'
              ) : (
                '⚔️ Iniciar Sesión'
              )}
            </button>
          </form>

          {/* Test Accounts */}
          <div className="mt-8 p-4 bg-gray-800/50 rounded-lg border border-gray-700/50">
            <h3 className="text-lg font-bold mb-4 text-gold-400 flex items-center gap-2">
              🧪 Cuentas de Prueba
              <span className="text-xs bg-blue-600/20 text-blue-300 px-2 py-1 rounded">
                Demo
              </span>
            </h3>
            <div className="space-y-3">
              {testAccounts.map((account, index) => (
                <button
                  key={account.username}
                  onClick={() => quickLogin(account.username)}
                  disabled={isLoading}
                  className={`
                    w-full text-left p-3 rounded-lg border transition-all duration-200 
                    hover:scale-102 hover:shadow-md
                    ${isLoading 
                      ? 'opacity-50 cursor-not-allowed' 
                      : 'hover:bg-white/5 hover:border-purple-400/50'
                    }
                    ${index === 0 ? 'bg-purple-600/20 border-purple-500/50' :
                      index === 1 ? 'bg-blue-600/20 border-blue-500/50' :
                      'bg-green-600/20 border-green-500/50'
                    }
                  `}
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="font-bold flex items-center gap-2">
                        {index === 0 && '👑'} 
                        {index === 1 && '🆕'} 
                        {index === 2 && '📚'} 
                        {account.description}
                      </div>
                      <div className="text-sm text-gray-300 mt-1">
                        Usuario: <span className="font-mono bg-black/30 px-2 py-1 rounded text-xs">{account.username}</span> | 
                        Contraseña: <span className="font-mono bg-black/30 px-2 py-1 rounded text-xs">secret</span>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-xs text-gray-400">Nivel {account.level}</div>
                      <div className={`
                        text-sm font-bold px-2 py-1 rounded
                        ${account.rank === 'S' ? 'bg-gold-500/20 text-gold-300' :
                          account.rank === 'E' ? 'bg-gray-500/20 text-gray-300' :
                          'bg-green-500/20 text-green-300'
                        }
                      `}>
                        Rango {account.rank}
                      </div>
                    </div>
                  </div>
                </button>
              ))}
            </div>
            <div className="mt-4 text-xs text-gray-500 text-center">
              Click en cualquier cuenta para hacer login automático
            </div>
          </div>

          {/* Navigation Links */}
          <div className="mt-8 flex flex-col sm:flex-row gap-4 text-center">
            <Link 
              href="/" 
              className="flex-1 py-2 px-4 text-purple-400 hover:text-purple-300 hover:bg-purple-500/10 rounded-lg transition-all duration-200"
            >
              ← Volver al inicio
            </Link>
            <Link 
              href="/signup" 
              className="flex-1 py-2 px-4 text-blue-400 hover:text-blue-300 hover:bg-blue-500/10 rounded-lg transition-all duration-200"
            >
              Crear cuenta nueva →
            </Link>
          </div>

          {/* Developer Tools */}
          <div className="mt-6 text-center">
            <Link 
              href="/login-test" 
              className="inline-flex items-center gap-2 py-2 px-4 text-xs text-gray-500 hover:text-gray-300 hover:bg-gray-800/30 rounded-lg transition-all duration-200 border border-gray-700/50"
            >
              🧪 Sistema de Pruebas Automáticas
            </Link>
          </div>

          {/* System Status */}
          <div className="mt-6 text-center">
            <div className="flex items-center justify-center gap-2 text-xs text-gray-500">
              <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
              Sistema conectado
            </div>
          </div>
        </div>

        {/* Mobile Responsive Improvements */}
        <div className="mt-8 text-center text-xs text-gray-500 px-4">
          <p>¿Problemas para acceder? Verifica tu conexión o contacta soporte.</p>
        </div>
      </div>
    </div>
  );
}