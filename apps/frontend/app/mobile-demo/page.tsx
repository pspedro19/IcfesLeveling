'use client';

import React from 'react';
import MobileNavigation from '../components/Mobile/MobileNavigation';
import MobileCarousel from '../components/Mobile/MobileCarousel';
import { Smartphone, Zap, Sparkles, Trophy, Users } from 'lucide-react';

export default function MobileDemoPage() {
  // Demo carousel items
  const carouselItems = [
    {
      id: '1',
      content: (
        <div className="bg-gradient-to-br from-purple-600 to-purple-700 rounded-lg p-6 h-64">
          <Zap className="w-12 h-12 text-white mb-4" />
          <h3 className="text-xl font-bold text-white mb-2">Batalla Rápida</h3>
          <p className="text-purple-100">
            Responde preguntas y gana experiencia en batallas épicas
          </p>
        </div>
      )
    },
    {
      id: '2',
      content: (
        <div className="bg-gradient-to-br from-blue-600 to-blue-700 rounded-lg p-6 h-64">
          <Trophy className="w-12 h-12 text-white mb-4" />
          <h3 className="text-xl font-bold text-white mb-2">Tabla de Líderes</h3>
          <p className="text-blue-100">
            Compite con otros jugadores y alcanza el primer lugar
          </p>
        </div>
      )
    },
    {
      id: '3',
      content: (
        <div className="bg-gradient-to-br from-green-600 to-green-700 rounded-lg p-6 h-64">
          <Users className="w-12 h-12 text-white mb-4" />
          <h3 className="text-xl font-bold text-white mb-2">Únete a un Gremio</h3>
          <p className="text-green-100">
            Colabora con otros estudiantes en raids cooperativos
          </p>
        </div>
      )
    },
    {
      id: '4',
      content: (
        <div className="bg-gradient-to-br from-yellow-600 to-yellow-700 rounded-lg p-6 h-64">
          <Sparkles className="w-12 h-12 text-white mb-4" />
          <h3 className="text-xl font-bold text-white mb-2">Recompensas Épicas</h3>
          <p className="text-yellow-100">
            Desbloquea logros y gana premios exclusivos
          </p>
        </div>
      )
    }
  ];
  
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900 
      to-gray-900 pt-20 pb-24 px-4">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-20 h-20 
            bg-purple-600 rounded-full mb-4">
            <Smartphone className="w-10 h-10 text-white" />
          </div>
          
          <h1 className="text-3xl md:text-4xl font-bold text-white mb-4 font-cinzel">
            Experiencia Móvil
          </h1>
          
          <p className="text-gray-300 max-w-2xl mx-auto">
            ICFES Leveling está optimizado para dispositivos móviles con 
            navegación por gestos, carruseles táctiles y una interfaz adaptativa
          </p>
        </div>
        
        {/* Features Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-12">
          <div className="bg-gray-900/80 rounded-lg p-6">
            <h3 className="text-xl font-semibold text-white mb-4">
              🎯 Navegación por Gestos
            </h3>
            <ul className="space-y-2 text-gray-300">
              <li>• Desliza izquierda/derecha para cambiar de sección</li>
              <li>• Toca dos veces para acciones rápidas</li>
              <li>• Pellizca para hacer zoom en contenido</li>
              <li>• Mantén presionado para ver más opciones</li>
            </ul>
          </div>
          
          <div className="bg-gray-900/80 rounded-lg p-6">
            <h3 className="text-xl font-semibold text-white mb-4">
              📱 Interfaz Adaptativa
            </h3>
            <ul className="space-y-2 text-gray-300">
              <li>• Menú inferior optimizado para el pulgar</li>
              <li>• Carruseles táctiles suaves</li>
              <li>• Botones grandes y fáciles de tocar</li>
              <li>• Modo oscuro por defecto para ahorrar batería</li>
            </ul>
          </div>
        </div>
        
        {/* Carousel Demo */}
        <div className="mb-12">
          <h2 className="text-2xl font-semibold text-white mb-6 text-center">
            Carrusel Interactivo
          </h2>
          
          <MobileCarousel
            items={carouselItems}
            showIndicators={true}
            autoPlay={true}
            autoPlayInterval={4000}
            onSlideChange={(index) => console.log('Slide changed to:', index)}
          />
        </div>
        
        {/* Instructions */}
        <div className="bg-gray-900/80 rounded-lg p-6 text-center">
          <h3 className="text-xl font-semibold text-white mb-4">
            Instrucciones Móviles
          </h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-left max-w-2xl mx-auto">
            <div className="flex items-start gap-3">
              <span className="text-2xl">👆</span>
              <div>
                <p className="font-semibold text-white">Toque</p>
                <p className="text-sm text-gray-400">
                  Toca elementos para interactuar
                </p>
              </div>
            </div>
            
            <div className="flex items-start gap-3">
              <span className="text-2xl">👉</span>
              <div>
                <p className="font-semibold text-white">Desliza</p>
                <p className="text-sm text-gray-400">
                  Navega entre secciones
                </p>
              </div>
            </div>
            
            <div className="flex items-start gap-3">
              <span className="text-2xl">🤏</span>
              <div>
                <p className="font-semibold text-white">Pellizca</p>
                <p className="text-sm text-gray-400">
                  Zoom en imágenes y gráficos
                </p>
              </div>
            </div>
            
            <div className="flex items-start gap-3">
              <span className="text-2xl">📱</span>
              <div>
                <p className="font-semibold text-white">Gira</p>
                <p className="text-sm text-gray-400">
                  Algunas vistas se adaptan al girar
                </p>
              </div>
            </div>
          </div>
          
          <p className="text-sm text-gray-500 mt-6">
            💡 Esta página se ve mejor en dispositivos móviles
          </p>
        </div>
      </div>
      
      {/* Mobile Navigation */}
      <MobileNavigation />
    </div>
  );
}