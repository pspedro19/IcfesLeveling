'use client';

import React from 'react';

export default function TestStylingPage() {
  return (
    <div className="min-h-screen bg-bg-primary text-white p-8">
      <div className="container mx-auto max-w-4xl">
        <h1 className="text-4xl font-bold text-gold-400 mb-8 animate-glow">
          🎮 ICFES LEVELING - Prueba de Estilos
        </h1>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Gradient Card */}
          <div className="card-game p-6">
            <h2 className="text-2xl font-ui text-mist-purple-400 mb-4">
              Tarjeta con Gradientes
            </h2>
            <div className="bg-gradient-gold text-black p-4 rounded-lg mb-4">
              Gradiente dorado
            </div>
            <div className="bg-gradient-mystic text-white p-4 rounded-lg">
              Gradiente místico
            </div>
          </div>

          {/* Animations Card */}
          <div className="card-game p-6">
            <h2 className="text-2xl font-ui text-mystic-blue-400 mb-4">
              Animaciones Épicas
            </h2>
            <div className="animate-float bg-mist-purple-600 p-4 rounded-lg mb-4">
              Flotando ✨
            </div>
            <div className="animate-pulse-gold bg-gold-500 text-black p-4 rounded-lg">
              Pulso dorado 🏆
            </div>
          </div>

          {/* Buttons */}
          <div className="card-game p-6">
            <h2 className="text-2xl font-ui text-success-400 mb-4">
              Botones de Combate
            </h2>
            <button className="btn-primary mr-4 mb-4">
              Botón Principal
            </button>
            <button className="btn-secondary mb-4">
              Botón Secundario
            </button>
          </div>

          {/* Status Bars */}
          <div className="card-game p-6">
            <h2 className="text-2xl font-ui text-danger-400 mb-4">
              Barras de Estado
            </h2>
            <div className="mb-4">
              <p className="text-sm text-success-300 mb-2">HP: 80/100</p>
              <div className="liquid-bar h-4">
                <div className="liquid-bar-fill hp w-4/5"></div>
              </div>
            </div>
            <div>
              <p className="text-sm text-mystic-blue-300 mb-2">MP: 60/100</p>
              <div className="liquid-bar h-4">
                <div className="liquid-bar-fill mp w-3/5"></div>
              </div>
            </div>
          </div>
        </div>

        {/* Background Test */}
        <div className="mt-8 p-8 bg-gradient-mystic rounded-xl relative overflow-hidden">
          <div className="absolute inset-0 bg-stars-bg opacity-30"></div>
          <div className="relative z-10">
            <h3 className="text-xl font-display text-white mb-4">
              Fondo Estrellado
            </h3>
            <p className="text-gray-300">
              Este panel debería mostrar un fondo con estrellas generado por CSS.
            </p>
          </div>
        </div>

        {/* Particle Effects Test */}
        <div className="mt-8 relative">
          <div className="bg-black/50 backdrop-blur-sm p-8 rounded-xl border border-mist-purple-500/30">
            <h3 className="text-xl font-display text-gold-400 mb-4">
              Efectos Visuales
            </h3>
            <div className="flex gap-4">
              <div className="portal-glow w-16 h-16 bg-mist-purple-600 rounded-full animate-portal-pulse"></div>
              <div className="w-16 h-16 bg-gold-500 rounded-full animate-crystal-float"></div>
              <div className="w-16 h-16 bg-gradient-to-r from-red-500 to-purple-600 rounded-full animate-spin-slow"></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}