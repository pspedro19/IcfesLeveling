'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import MainNavigation from '../components/Navigation/MainNavigation';

export default function PortalDelDespertar() {
  const [currentUser, setCurrentUser] = useState<any>(null);
  const router = useRouter();

  useEffect(() => {
    const userData = localStorage.getItem('currentUser') || localStorage.getItem('user');
    if (userData) {
      setCurrentUser(JSON.parse(userData));
    }
  }, []);

  const handleReturnToHub = () => {
    router.push('/student-dashboard');
  };

  const handleStartTest = () => {
    router.push('/diagnostic-test');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 text-white">
      <MainNavigation currentUser={currentUser} />

      <div className="pt-20 lg:pt-24">
        <div className="relative overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-r from-purple-600/20 to-blue-600/20"></div>
          <div className="relative z-10 text-center py-16 px-4">
            <div className="text-8xl mb-4">🌟</div>
            <h1 className="text-6xl font-bold mb-4 bg-gradient-to-r from-gold-400 to-purple-400 bg-clip-text text-transparent">
              PORTAL DEL DESPERTAR
            </h1>
            <p className="text-2xl text-gray-300 max-w-4xl mx-auto leading-relaxed">
              Inicia tu prueba diagnóstica y descubre tu verdadero potencial
            </p>
          </div>
        </div>

        <div className="container mx-auto px-4 py-12">
          <div className="max-w-4xl mx-auto space-y-8">
            <div className="bg-gradient-to-br from-purple-800/50 to-blue-800/50 rounded-xl p-8 border border-purple-500/30">
              <h2 className="text-3xl font-bold mb-4 text-gold-400">
                ¿Listo para Despertar?
              </h2>
              <p className="text-lg text-gray-300 mb-6">
                Completa la prueba diagnóstica para descubrir tus fortalezas y áreas de mejora.
              </p>
              <button
                onClick={handleStartTest}
                className="px-8 py-4 bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 rounded-lg font-bold text-xl transition-all transform hover:scale-105"
              >
                🚀 Iniciar Prueba Diagnóstica
              </button>
            </div>

            <div className="text-center mt-12">
              <button
                onClick={handleReturnToHub}
                className="px-8 py-3 bg-gray-700 hover:bg-gray-600 rounded-lg font-bold transition-colors"
              >
                ← Volver al Hub Central
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
