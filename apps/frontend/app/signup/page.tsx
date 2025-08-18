'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { authService } from '../services/auth.service';

export default function SignupPage() {
  const router = useRouter();
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    confirmPassword: '',
    display_name: ''
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (formData.password !== formData.confirmPassword) {
      setError('Las contraseñas no coinciden');
      return;
    }

    if (formData.password.length < 6) {
      setError('La contraseña debe tener al menos 6 caracteres');
      return;
    }

    setLoading(true);
    try {
      await authService.register({
        username: formData.username,
        email: formData.email,
        password: formData.password,
        display_name: formData.display_name || formData.username
      });
      
      // Auto login after successful registration
      await authService.login({
        username: formData.email,
        password: formData.password
      });
      
      router.push('/onboarding');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error al crear la cuenta');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 flex items-center justify-center px-4">
      <div className="max-w-md w-full">
        {/* Logo and Title */}
        <div className="text-center mb-8">
          <Link href="/" className="inline-block">
            <h1 className="text-4xl font-bold bg-gradient-to-r from-gold-400 to-purple-400 bg-clip-text text-transparent mb-2">
              🎮 ICFES LEVELING
            </h1>
          </Link>
          <p className="text-gray-300">Únete a la aventura educativa</p>
        </div>

        {/* Signup Card */}
        <div className="bg-black/40 backdrop-blur-lg rounded-xl p-8 border border-purple-500/30">
          <h2 className="text-2xl font-bold text-white mb-6 text-center">
            Crear Cuenta de Hunter
          </h2>

          {error && (
            <div className="bg-red-500/20 border border-red-500/50 rounded-lg p-3 mb-4">
              <p className="text-red-300 text-sm text-center">{error}</p>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-gray-300 text-sm mb-2">
                Nombre de Usuario
              </label>
              <input
                type="text"
                required
                className="w-full px-4 py-3 bg-black/30 border border-purple-500/30 rounded-lg text-white placeholder-gray-500 focus:border-purple-400 focus:outline-none focus:ring-2 focus:ring-purple-400/20"
                placeholder="hunter123"
                value={formData.username}
                onChange={(e) => setFormData({...formData, username: e.target.value})}
              />
            </div>

            <div>
              <label className="block text-gray-300 text-sm mb-2">
                Correo Electrónico
              </label>
              <input
                type="email"
                required
                className="w-full px-4 py-3 bg-black/30 border border-purple-500/30 rounded-lg text-white placeholder-gray-500 focus:border-purple-400 focus:outline-none focus:ring-2 focus:ring-purple-400/20"
                placeholder="tu@email.com"
                value={formData.email}
                onChange={(e) => setFormData({...formData, email: e.target.value})}
              />
            </div>

            <div>
              <label className="block text-gray-300 text-sm mb-2">
                Nombre para Mostrar (Opcional)
              </label>
              <input
                type="text"
                className="w-full px-4 py-3 bg-black/30 border border-purple-500/30 rounded-lg text-white placeholder-gray-500 focus:border-purple-400 focus:outline-none focus:ring-2 focus:ring-purple-400/20"
                placeholder="Tu nombre en el juego"
                value={formData.display_name}
                onChange={(e) => setFormData({...formData, display_name: e.target.value})}
              />
            </div>

            <div>
              <label className="block text-gray-300 text-sm mb-2">
                Contraseña
              </label>
              <input
                type="password"
                required
                className="w-full px-4 py-3 bg-black/30 border border-purple-500/30 rounded-lg text-white placeholder-gray-500 focus:border-purple-400 focus:outline-none focus:ring-2 focus:ring-purple-400/20"
                placeholder="••••••••"
                value={formData.password}
                onChange={(e) => setFormData({...formData, password: e.target.value})}
              />
            </div>

            <div>
              <label className="block text-gray-300 text-sm mb-2">
                Confirmar Contraseña
              </label>
              <input
                type="password"
                required
                className="w-full px-4 py-3 bg-black/30 border border-purple-500/30 rounded-lg text-white placeholder-gray-500 focus:border-purple-400 focus:outline-none focus:ring-2 focus:ring-purple-400/20"
                placeholder="••••••••"
                value={formData.confirmPassword}
                onChange={(e) => setFormData({...formData, confirmPassword: e.target.value})}
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 bg-gradient-to-r from-purple-600 to-blue-600 text-white font-bold rounded-lg hover:from-purple-700 hover:to-blue-700 transform hover:scale-105 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? (
                <span className="flex items-center justify-center">
                  <svg className="animate-spin h-5 w-5 mr-2" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none"/>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"/>
                  </svg>
                  Creando cuenta...
                </span>
              ) : (
                '🚀 Crear Cuenta'
              )}
            </button>
          </form>

          <div className="mt-6 text-center">
            <p className="text-gray-400 text-sm">
              ¿Ya tienes una cuenta?{' '}
              <Link href="/login" className="text-purple-400 hover:text-purple-300 font-semibold">
                Inicia Sesión
              </Link>
            </p>
          </div>

          <div className="mt-6 pt-6 border-t border-gray-700">
            <p className="text-gray-500 text-xs text-center mb-4">O regístrate con</p>
            <div className="grid grid-cols-2 gap-4">
              <button className="py-2 px-4 bg-blue-600/20 border border-blue-500/30 rounded-lg text-blue-400 hover:bg-blue-600/30 transition-all duration-200">
                Google
              </button>
              <button className="py-2 px-4 bg-gray-600/20 border border-gray-500/30 rounded-lg text-gray-400 hover:bg-gray-600/30 transition-all duration-200">
                GitHub
              </button>
            </div>
          </div>
        </div>

        {/* Footer Links */}
        <div className="mt-8 text-center space-x-4 text-sm">
          <Link href="/landing" className="text-gray-400 hover:text-white transition-colors">
            Inicio
          </Link>
          <span className="text-gray-600">•</span>
          <Link href="/pricing" className="text-gray-400 hover:text-white transition-colors">
            Precios
          </Link>
          <span className="text-gray-600">•</span>
          <Link href="/about" className="text-gray-400 hover:text-white transition-colors">
            Acerca de
          </Link>
          <span className="text-gray-600">•</span>
          <Link href="/contact" className="text-gray-400 hover:text-white transition-colors">
            Contacto
          </Link>
        </div>
      </div>
    </div>
  );
}