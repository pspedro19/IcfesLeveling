'use client';

import React from 'react';
import AIMentorSystem from '../components/Mentors/AIMentorSystem';
import { Brain, Target, CheckCircle, AlertTriangle } from 'lucide-react';

export default function MentorsPage() {
  // Mock performance data
  const mockPerformance = {
    accuracy: 78,
    weakAreas: ['Álgebra', 'Trigonometría'],
    strongAreas: ['Geometría', 'Estadística']
  };
  
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900 to-gray-900 p-4">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-4xl font-bold text-white text-center mb-8 font-cinzel">
          Sistema de Mentores IA
        </h1>
        
        {/* Info Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="bg-gray-900/80 rounded-lg p-6">
            <div className="flex items-center gap-3 mb-4">
              <Brain className="w-8 h-8 text-purple-400" />
              <h3 className="text-xl font-semibold text-white">
                Mentores Personalizados
              </h3>
            </div>
            <p className="text-gray-300">
              Cada mentor tiene una personalidad única y un enfoque diferente 
              para ayudarte a aprender.
            </p>
          </div>
          
          <div className="bg-gray-900/80 rounded-lg p-6">
            <div className="flex items-center gap-3 mb-4">
              <Target className="w-8 h-8 text-blue-400" />
              <h3 className="text-xl font-semibold text-white">
                Consejos Adaptativos
              </h3>
            </div>
            <p className="text-gray-300">
              Los mentores analizan tu rendimiento y te dan consejos 
              personalizados según tus fortalezas y debilidades.
            </p>
          </div>
          
          <div className="bg-gray-900/80 rounded-lg p-6">
            <div className="flex items-center gap-3 mb-4">
              <CheckCircle className="w-8 h-8 text-green-400" />
              <h3 className="text-xl font-semibold text-white">
                Disponible 24/7
              </h3>
            </div>
            <p className="text-gray-300">
              Tus mentores IA están siempre disponibles para responder 
              preguntas y ofrecer apoyo.
            </p>
          </div>
        </div>
        
        {/* Performance Overview */}
        <div className="bg-gray-900/80 rounded-lg p-6 mb-8">
          <h3 className="text-xl font-semibold text-white mb-6">
            Tu Rendimiento Actual
          </h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <div className="mb-4">
                <div className="flex justify-between items-center mb-2">
                  <span className="text-gray-400">Precisión General</span>
                  <span className="text-2xl font-bold text-white">
                    {mockPerformance.accuracy}%
                  </span>
                </div>
                <div className="w-full bg-gray-700 rounded-full h-3">
                  <div 
                    className="h-full bg-gradient-to-r from-purple-500 to-purple-600 rounded-full"
                    style={{ width: `${mockPerformance.accuracy}%` }}
                  />
                </div>
              </div>
              
              <div>
                <h4 className="text-sm font-semibold text-gray-400 mb-3">
                  Áreas Fuertes
                </h4>
                <div className="flex flex-wrap gap-2">
                  {mockPerformance.strongAreas.map(area => (
                    <span key={area} className="bg-green-900/30 text-green-400 
                      px-3 py-1 rounded-full text-sm">
                      <CheckCircle className="w-3 h-3 inline mr-1" />
                      {area}
                    </span>
                  ))}
                </div>
              </div>
            </div>
            
            <div>
              <h4 className="text-sm font-semibold text-gray-400 mb-3">
                Áreas a Mejorar
              </h4>
              <div className="space-y-3">
                {mockPerformance.weakAreas.map(area => (
                  <div key={area} className="bg-red-900/20 border border-red-500/30 
                    rounded-lg p-3">
                    <div className="flex items-center gap-2 mb-1">
                      <AlertTriangle className="w-4 h-4 text-red-400" />
                      <span className="text-white font-semibold">{area}</span>
                    </div>
                    <p className="text-sm text-gray-400">
                      Los mentores te ayudarán con ejercicios específicos
                    </p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
        
        {/* Instructions */}
        <div className="bg-gray-900/80 rounded-lg p-6 text-center">
          <h3 className="text-xl font-semibold text-white mb-4">
            ¿Cómo usar los Mentores IA?
          </h3>
          
          <div className="space-y-3 text-gray-300 max-w-2xl mx-auto">
            <p>
              1. Haz clic en el botón morado de la esquina inferior izquierda
            </p>
            <p>
              2. Elige el mentor que mejor se adapte a tu estilo de aprendizaje
            </p>
            <p>
              3. Hazles preguntas sobre cualquier tema que necesites ayuda
            </p>
            <p>
              4. Recibe consejos personalizados basados en tu rendimiento
            </p>
          </div>
          
          <div className="mt-6 text-sm text-gray-500">
            <p>
              💡 Tip: Prueba diferentes mentores para encontrar el que mejor te ayude
            </p>
          </div>
        </div>
      </div>
      
      {/* AI Mentor System */}
      <AIMentorSystem
        userLevel={15}
        subject="Matemáticas"
        recentPerformance={mockPerformance}
      />
    </div>
  );
}