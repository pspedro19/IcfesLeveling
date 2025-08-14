'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';

export default function LoginPage() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const router = useRouter();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');

    try {
      const formData = new URLSearchParams();
      formData.append('username', username);
      formData.append('password', password);

      const response = await fetch('http://localhost:4000/api/v1/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Error desconocido' }));
        throw new Error(errorData.detail || 'Error en el login');
      }

      const data = await response.json();
      console.log('🔐 Datos de login recibidos:', data);
      
      // Guardar token
      localStorage.setItem('access_token', data.access_token);
      localStorage.setItem('user', JSON.stringify(data.user));
      console.log('💾 Token guardado en localStorage con clave "access_token"');
      console.log('💾 Token:', data.access_token ? data.access_token.substring(0, 20) + '...' : 'No recibido');
      
      // Mostrar éxito
      alert(`✅ Login exitoso! Bienvenido ${data.user.username}`);
      
      // Redirigir al diagnostic test
      router.push('/diagnostic-test');
      
    } catch (error: any) {
      setError(error.message || 'Error en el login');
    } finally {
      setIsLoading(false);
    }
  };

  const quickLogin = async (user: string) => {
    setUsername(user);
    setPassword('secret');
    // Trigger login after setting values
    setTimeout(() => {
      const form = document.querySelector('form') as HTMLFormElement;
      if (form) {
        form.dispatchEvent(new Event('submit', { bubbles: true, cancelable: true }));
      }
    }, 100);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 text-white flex items-center justify-center">
      <div className="max-w-md w-full mx-4">
        <div className="bg-black/30 backdrop-blur-sm rounded-lg p-8 border border-purple-500/30">
          <div className="text-center mb-8">
            <h1 className="text-4xl font-bold mb-2 bg-gradient-to-r from-gold-400 to-purple-400 bg-clip-text text-transparent">
              🎮 Hunter Login
            </h1>
            <p className="text-gray-300">Acceso al sistema IcfesLeveling</p>
          </div>

          <form onSubmit={handleLogin} className="space-y-6">
            <div>
              <label className="block text-sm font-medium mb-2">Usuario</label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="w-full px-3 py-2 bg-black/50 border border-purple-500/50 rounded-lg text-white placeholder-gray-400 focus:border-purple-400 focus:outline-none"
                placeholder="Ingresa tu usuario"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Contraseña</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-3 py-2 bg-black/50 border border-purple-500/50 rounded-lg text-white placeholder-gray-400 focus:border-purple-400 focus:outline-none"
                placeholder="Ingresa tu contraseña"
                required
              />
            </div>

            {error && (
              <div className="p-3 bg-red-500/20 border border-red-500 rounded-lg text-red-300">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={isLoading}
              className="w-full py-3 bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 disabled:opacity-50 rounded-lg font-bold text-lg transition-all duration-300"
            >
              {isLoading ? '🔄 Iniciando sesión...' : '⚔️ Iniciar Sesión'}
            </button>
          </form>

          <div className="mt-8 p-4 bg-gray-800/50 rounded-lg">
            <h3 className="text-lg font-bold mb-3 text-gold-400">🧪 Cuentas de Prueba</h3>
            <div className="space-y-2">
              <button
                onClick={() => quickLogin('admin')}
                className="w-full text-left p-2 bg-purple-600/30 hover:bg-purple-600/50 rounded transition-colors"
              >
                <div className="font-bold">👑 Admin (Nivel 50)</div>
                <div className="text-sm text-gray-300">Usuario: admin | Contraseña: secret</div>
              </button>
              <button
                onClick={() => quickLogin('test')}
                className="w-full text-left p-2 bg-blue-600/30 hover:bg-blue-600/50 rounded transition-colors"
              >
                <div className="font-bold">🆕 Usuario Test (Nivel 1)</div>
                <div className="text-sm text-gray-300">Usuario: test | Contraseña: secret</div>
              </button>
            </div>
          </div>

          <div className="mt-6 text-center">
            <Link 
              href="/" 
              className="text-purple-400 hover:text-purple-300 transition-colors"
            >
              ← Volver al inicio
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}