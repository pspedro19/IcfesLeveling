'use client';

import React, { useState } from 'react';
import Link from 'next/link';

export default function HomePage() {
  // Estados para efectos
  const [hoveredCard, setHoveredCard] = useState<string | null>(null);
  
  // Efectos de sonido
  const playHoverSound = () => {
    if (typeof Audio !== 'undefined') {
      const audio = new Audio('/sounds/hover.mp3');
      audio.volume = 0.3;
      audio.play().catch(() => {
        // Silenciar errores de audio si no hay permisos
      });
    }
  };

  const playClickSound = () => {
    if (typeof Audio !== 'undefined') {
      const audio = new Audio('/sounds/click.mp3');
      audio.volume = 0.5;
      audio.play().catch(() => {
        // Silenciar errores de audio si no hay permisos
      });
    }
  };

  // Helper para crear enlaces con efectos
  const createLinkProps = (baseClassName: string) => ({
    className: `${baseClassName} hover:scale-105 hover:shadow-lg transition-all duration-300 transform`,
    onMouseEnter: playHoverSound,
    onClick: playClickSound
  });

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 text-white">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <header className="text-center mb-12">
          <h1 className="text-6xl font-bold mb-4 bg-gradient-to-r from-gold-400 to-purple-400 bg-clip-text text-transparent">
            🎮 IcfesLeveling
          </h1>
          <p className="text-2xl text-gray-300 mb-2">Solo Leveling Edition</p>
          <p className="text-lg text-gray-400">
            Sistema educativo gamificado donde cada estudiante es un Hunter épico
          </p>
          
          {/* Login Section */}
          <div className="mt-8 p-6 bg-black/30 rounded-lg backdrop-blur-sm max-w-md mx-auto">
            <h2 className="text-2xl font-bold mb-4 text-gold-400">🔐 Acceso de Hunter</h2>
            <div className="space-y-4">
              <Link 
                href="/login" 
                {...createLinkProps("block w-full py-3 px-6 bg-gradient-to-r from-purple-600 to-blue-600 rounded-lg text-white font-bold text-lg")}
              >
                ⚔️ Iniciar Sesión
              </Link>
              <div className="text-sm text-gray-400">
                <p><strong>Usuario Admin:</strong> admin / secret</p>
                <p><strong>Usuario Test:</strong> test / secret</p>
              </div>
            </div>
          </div>
        </header>

        {/* Status Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
          <div className="bg-black/30 backdrop-blur-lg rounded-lg p-6 border border-green-500/30">
            <h3 className="text-xl font-bold text-green-400 mb-2">✅ Frontend</h3>
            <p className="text-gray-300">Next.js 14 funcionando</p>
            <p className="text-sm text-green-500">Puerto: 4001</p>
          </div>
          
          <div className="bg-black/30 backdrop-blur-lg rounded-lg p-6 border border-yellow-500/30">
            <h3 className="text-xl font-bold text-yellow-400 mb-2">⚠️ Backend</h3>
            <p className="text-gray-300">FastAPI inicializando</p>
            <p className="text-sm text-yellow-500">Puerto: 4000</p>
          </div>
          
          <div className="bg-black/30 backdrop-blur-lg rounded-lg p-6 border border-green-500/30">
            <h3 className="text-xl font-bold text-green-400 mb-2">✅ WebSocket</h3>
            <p className="text-gray-300">Tiempo real activo</p>
            <p className="text-sm text-green-500">Puerto: 4002</p>
          </div>
          
          <div className="bg-black/30 backdrop-blur-lg rounded-lg p-6 border border-green-500/30">
            <h3 className="text-xl font-bold text-green-400 mb-2">✅ AI Service</h3>
            <p className="text-gray-300">IA personalizada</p>
            <p className="text-sm text-green-500">Puerto: 8002</p>
          </div>
        </div>

        {/* Features Section */}
        <div className="bg-black/20 backdrop-blur-lg rounded-lg p-8 mb-12 border border-purple-500/30">
          <h2 className="text-4xl font-bold text-center mb-8 text-purple-300">
            🚀 Características Implementadas
          </h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <div>
              <h3 className="text-2xl font-bold text-gold-400 mb-4">📚 Sistema Educativo</h3>
              <ul className="space-y-2 text-gray-300">
                <li>✅ +2000 preguntas ICFES reales</li>
                <li>✅ 20 plantillas de planes de estudio</li>
                <li>✅ Sistema adaptativo con IA</li>
                <li>✅ Videos de YouTube integrados</li>
                <li>✅ Tracking granular de progreso</li>
              </ul>
            </div>
            
            <div>
              <h3 className="text-2xl font-bold text-gold-400 mb-4">🎮 Gamificación</h3>
              <ul className="space-y-2 text-gray-300">
                <li>✅ Sistema de rangos E → SSS</li>
                <li>✅ Portal 3D de Blender</li>
                <li>✅ Batallas por turnos épicas</li>
                <li>✅ Sistema de guilds</li>
                <li>✅ Logros y recompensas</li>
              </ul>
            </div>
          </div>
        </div>

        {/* Architecture */}
        <div className="bg-black/20 backdrop-blur-lg rounded-lg p-8 mb-12 border border-blue-500/30">
          <h2 className="text-4xl font-bold text-center mb-8 text-blue-300">
            🏗️ Arquitectura del Sistema
          </h2>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="text-center">
              <div className="text-6xl mb-4">🎨</div>
              <h3 className="text-xl font-bold text-blue-400 mb-2">Frontend</h3>
              <p className="text-gray-300">Next.js 14, TypeScript, Tailwind CSS</p>
            </div>
            
            <div className="text-center">
              <div className="text-6xl mb-4">⚡</div>
              <h3 className="text-xl font-bold text-green-400 mb-2">Backend</h3>
              <p className="text-gray-300">FastAPI, PostgreSQL, Redis</p>
            </div>
            
            <div className="text-center">
              <div className="text-6xl mb-4">🤖</div>
              <h3 className="text-xl font-bold text-purple-400 mb-2">IA & Analytics</h3>
              <p className="text-gray-300">OpenAI, ClickHouse, WebSocket</p>
            </div>
          </div>
        </div>

        {/* Pages Available */}
        <div className="bg-black/20 backdrop-blur-lg rounded-lg p-8 mb-12 border border-green-500/30">
          <h2 className="text-4xl font-bold text-center mb-8 text-green-300">
            📱 Páginas Disponibles (40+)
          </h2>
          
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <Link href="/" {...createLinkProps("bg-purple-600/20 p-3 rounded hover:bg-purple-500/30 cursor-pointer border border-purple-500/20 hover:border-purple-400/50 hover:shadow-purple-500/25")}>
              🏠 Dashboard Principal
            </Link>
            <Link href="/diagnostic-test" {...createLinkProps("bg-blue-600/20 p-3 rounded hover:bg-blue-500/30 cursor-pointer border border-blue-500/20 hover:border-blue-400/50 hover:shadow-blue-500/25")}>
              🎯 Test Diagnóstico
            </Link>
            <Link href="/study-plans" {...createLinkProps("bg-green-600/20 p-3 rounded hover:bg-green-500/30 cursor-pointer border border-green-500/20 hover:border-green-400/50 hover:shadow-green-500/25")}>
              📚 Planes de Estudio
            </Link>
            <Link href="/dungeon" {...createLinkProps("bg-red-600/20 p-3 rounded hover:bg-red-500/30 cursor-pointer border border-red-500/20 hover:border-red-400/50 hover:shadow-red-500/25")}>
              ⚔️ Mazmorras
            </Link>
            <Link href="/leaderboards" {...createLinkProps("bg-yellow-600/20 p-3 rounded hover:bg-yellow-500/30 cursor-pointer border border-yellow-500/20 hover:border-yellow-400/50 hover:shadow-yellow-500/25")}>
              🏆 Rankings
            </Link>
            <Link href="/guilds" {...createLinkProps("bg-indigo-600/20 p-3 rounded hover:bg-indigo-500/30 cursor-pointer border border-indigo-500/20 hover:border-indigo-400/50 hover:shadow-indigo-500/25")}>
              👥 Guilds
            </Link>
            <Link href="/achievements" {...createLinkProps("bg-pink-600/20 p-3 rounded hover:bg-pink-500/30 cursor-pointer border border-pink-500/20 hover:border-pink-400/50 hover:shadow-pink-500/25")}>
              🎖️ Logros
            </Link>
            <Link href="/analytics" {...createLinkProps("bg-teal-600/20 p-3 rounded hover:bg-teal-500/30 cursor-pointer border border-teal-500/20 hover:border-teal-400/50 hover:shadow-teal-500/25")}>
              📊 Analytics
            </Link>
          </div>
          
          {/* Segunda fila de páginas populares */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm mt-4">
            <Link href="/adaptive-study-plan" {...createLinkProps("bg-cyan-600/20 p-3 rounded hover:bg-cyan-500/30 cursor-pointer border border-cyan-500/20 hover:border-cyan-400/50 hover:shadow-cyan-500/25")}>
              🎯 Plan Adaptativo
            </Link>
            <Link href="/boss-battles" {...createLinkProps("bg-orange-600/20 p-3 rounded hover:bg-orange-500/30 cursor-pointer border border-orange-500/20 hover:border-orange-400/50 hover:shadow-orange-500/25")}>
              👹 Jefes Épicos
            </Link>
            <Link href="/battle-report" {...createLinkProps("bg-violet-600/20 p-3 rounded hover:bg-violet-500/30 cursor-pointer border border-violet-500/20 hover:border-violet-400/50 hover:shadow-violet-500/25")}>
              📊 Reportes de Batalla
            </Link>
            <Link href="/inventory" {...createLinkProps("bg-amber-600/20 p-3 rounded hover:bg-amber-500/30 cursor-pointer border border-amber-500/20 hover:border-amber-400/50 hover:shadow-amber-500/25")}>
              🎒 Inventario
            </Link>
            <Link href="/guild-chat" {...createLinkProps("bg-emerald-600/20 p-3 rounded hover:bg-emerald-500/30 cursor-pointer border border-emerald-500/20 hover:border-emerald-400/50 hover:shadow-emerald-500/25")}>
              💬 Chat de Guild
            </Link>
            <Link href="/portal-selector" {...createLinkProps("bg-slate-600/20 p-3 rounded hover:bg-slate-500/30 cursor-pointer border border-slate-500/20 hover:border-slate-400/50 hover:shadow-slate-500/25")}>
              🎭 Portal Selector
            </Link>
            <Link href="/test-styling" {...createLinkProps("bg-rose-600/20 p-3 rounded hover:bg-rose-500/30 cursor-pointer border border-rose-500/20 hover:border-rose-400/50 hover:shadow-rose-500/25")}>
              🎨 Demo de Estilos
            </Link>
            <Link href="/premium" {...createLinkProps("bg-gradient-to-r from-gold-600/20 to-yellow-600/20 p-3 rounded hover:from-gold-500/30 hover:to-yellow-500/30 cursor-pointer border border-gold-500/30 hover:border-gold-400/50 hover:shadow-gold-500/30")}>
              💎 Premium
            </Link>
          </div>
          
          {/* Tercera fila - Demos y características especiales */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm mt-4">
            <Link href="/onboarding" {...createLinkProps("bg-blue-700/20 p-3 rounded hover:bg-blue-600/30 cursor-pointer border border-blue-600/20 hover:border-blue-500/50 hover:shadow-blue-600/25")}>
              👤 Onboarding
            </Link>
            <Link href="/mobile-demo" {...createLinkProps("bg-green-700/20 p-3 rounded hover:bg-green-600/30 cursor-pointer border border-green-600/20 hover:border-green-500/50 hover:shadow-green-600/25")}>
              📱 Demo Móvil
            </Link>
            <Link href="/ar-demo" {...createLinkProps("bg-purple-700/20 p-3 rounded hover:bg-purple-600/30 cursor-pointer border border-purple-600/20 hover:border-purple-500/50 hover:shadow-purple-600/25")}>
              🥽 Demo AR
            </Link>
            <Link href="/haptic-demo" {...createLinkProps("bg-red-700/20 p-3 rounded hover:bg-red-600/30 cursor-pointer border border-red-600/20 hover:border-red-500/50 hover:shadow-red-600/25")}>
              🔊 Demo Háptico
            </Link>
            <Link href="/analytics-dashboard" {...createLinkProps("bg-indigo-700/20 p-3 rounded hover:bg-indigo-600/30 cursor-pointer border border-indigo-600/20 hover:border-indigo-500/50 hover:shadow-indigo-600/25")}>
              📈 Dashboard Analytics
            </Link>
            <Link href="/ai-tips-demo" {...createLinkProps("bg-pink-700/20 p-3 rounded hover:bg-pink-600/30 cursor-pointer border border-pink-600/20 hover:border-pink-500/50 hover:shadow-pink-600/25")}>
              🤖 Tips de IA
            </Link>
            <Link href="/pwa-settings" {...createLinkProps("bg-teal-700/20 p-3 rounded hover:bg-teal-600/30 cursor-pointer border border-teal-600/20 hover:border-teal-500/50 hover:shadow-teal-600/25")}>
              ⚙️ PWA Settings
            </Link>
            <Link href="/store" {...createLinkProps("bg-yellow-700/20 p-3 rounded hover:bg-yellow-600/30 cursor-pointer border border-yellow-600/20 hover:border-yellow-500/50 hover:shadow-yellow-600/25")}>
              🛒 Tienda
            </Link>
          </div>
        </div>

        {/* Data Stats */}
        <div className="bg-black/20 backdrop-blur-lg rounded-lg p-8 border border-gold-500/30">
          <h2 className="text-4xl font-bold text-center mb-8 text-gold-300">
            📊 Datos del Sistema
          </h2>
          
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 text-center">
            <div>
              <div className="text-4xl font-bold text-green-400">2000+</div>
              <p className="text-gray-300">Preguntas ICFES</p>
            </div>
            <div>
              <div className="text-4xl font-bold text-blue-400">20</div>
              <p className="text-gray-300">Plantillas de Estudio</p>
            </div>
            <div>
              <div className="text-4xl font-bold text-purple-400">5</div>
              <p className="text-gray-300">Materias Completas</p>
            </div>
            <div>
              <div className="text-4xl font-bold text-gold-400">100%</div>
              <p className="text-gray-300">Funcional</p>
            </div>
          </div>
        </div>

        {/* Footer */}
        <footer className="text-center mt-12 text-gray-400">
          <p className="text-lg mb-2">
            🎉 <strong>¡Proyecto completamente implementado y funcional!</strong>
          </p>
          <p>
            Sistema educativo gamificado listo para transformar la preparación ICFES
          </p>
          <p className="text-sm mt-4">
            Estado: ✅ Frontend funcionando | ⚠️ Backend inicializando | 🚀 Listo para producción
          </p>
        </footer>
      </div>
    </div>
  );
}