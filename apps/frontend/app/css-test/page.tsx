'use client';

import React from 'react';

export default function CSSTestPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-black text-white p-8">
      {/* Test básico de colores y gradientes */}
      <div className="max-w-4xl mx-auto space-y-8">
        
        {/* Header de prueba */}
        <div className="text-center space-y-4">
          <h1 className="text-6xl font-bold bg-gradient-to-r from-gold-400 via-amber-500 to-orange-600 text-transparent bg-clip-text animate-gradient-shift">
            🎮 CSS TEST PAGE
          </h1>
          <p className="text-2xl text-purple-300 font-orbitron">
            Si ves colores y efectos aquí, CSS funciona perfectamente
          </p>
        </div>

        {/* Cards de prueba */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          
          {/* Card 1 - Gradientes */}
          <div className="bg-black/20 backdrop-blur-lg rounded-lg p-6 border border-purple-500/30 hover:border-gold-400/50 transition-all duration-300">
            <h3 className="text-2xl font-bold text-gold-400 mb-4 font-cinzel">Gradientes</h3>
            <div className="space-y-3">
              <div className="h-4 bg-gradient-to-r from-purple-500 to-pink-500 rounded"></div>
              <div className="h-4 bg-gradient-to-r from-gold-400 to-orange-500 rounded"></div>
              <div className="h-4 bg-gradient-to-r from-blue-500 to-cyan-500 rounded"></div>
            </div>
          </div>

          {/* Card 2 - Animaciones */}
          <div className="bg-black/20 backdrop-blur-lg rounded-lg p-6 border border-green-500/30 hover:border-gold-400/50 transition-all duration-300">
            <h3 className="text-2xl font-bold text-green-400 mb-4 font-cinzel">Animaciones</h3>
            <div className="space-y-3">
              <div className="w-16 h-16 bg-purple-600 rounded-full animate-bounce mx-auto"></div>
              <div className="w-12 h-12 bg-gold-400 rounded-full animate-spin-slow mx-auto"></div>
              <div className="text-center text-green-300 animate-pulse">Pulsando...</div>
            </div>
          </div>

          {/* Card 3 - Fuentes */}
          <div className="bg-black/20 backdrop-blur-lg rounded-lg p-6 border border-blue-500/30 hover:border-gold-400/50 transition-all duration-300">
            <h3 className="text-2xl font-bold text-blue-400 mb-4 font-cinzel">Fuentes</h3>
            <div className="space-y-3 text-center">
              <p className="font-cinzel text-gold-300">Cinzel Font</p>
              <p className="font-orbitron text-purple-300">Orbitron Font</p>
              <p className="font-mono text-green-300">Mono Font</p>
            </div>
          </div>
        </div>

        {/* Portal animation test */}
        <div className="relative bg-black/30 rounded-lg p-8 border border-purple-500/30">
          <h3 className="text-3xl font-bold text-center text-purple-300 mb-6 font-cinzel">
            Portal Animation Test
          </h3>
          <div className="flex justify-center">
            <div className="relative w-48 h-48">
              {/* Portal rings */}
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="w-48 h-48 rounded-full bg-purple-700/50 animate-spin-slow shadow-[0_0_30px_#8a2be2]"></div>
                <div className="absolute w-32 h-32 rounded-full bg-blue-500/50 animate-spin-slow-reverse shadow-[0_0_20px_#4a148c]"></div>
                <div className="absolute w-16 h-16 rounded-full bg-pink-400/50 animate-spin-slow shadow-[0_0_10px_#ff69b4]"></div>
              </div>
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="text-white/70 text-sm font-orbitron animate-pulse">
                  PORTAL ACTIVO
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Status final */}
        <div className="text-center p-6 bg-green-900/20 border border-green-500/30 rounded-lg">
          <h2 className="text-3xl font-bold text-green-400 mb-2 font-cinzel">
            ✅ CSS FUNCIONANDO CORRECTAMENTE
          </h2>
          <p className="text-green-300">
            Si puedes ver todos los colores, gradientes y animaciones arriba, 
            entonces Tailwind CSS está completamente funcional.
          </p>
        </div>

      </div>
    </div>
  );
}