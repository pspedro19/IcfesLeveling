'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { 
  Brain,
  Sparkles,
  ChevronRight
} from 'lucide-react';
import AdaptiveRecommendations from '@/components/Recommendations/AdaptiveRecommendations';

export default function RecommendationsDemoPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900 
      to-gray-900 relative overflow-hidden">
      {/* Background Effects */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-0 right-0 w-96 h-96 bg-purple-600/20 
          rounded-full blur-3xl animate-pulse" />
        <div className="absolute bottom-0 left-0 w-96 h-96 bg-blue-600/20 
          rounded-full blur-3xl animate-pulse animation-delay-2000" />
      </div>
      
      <div className="relative z-10 container mx-auto px-4 py-8">
        {/* Header */}
        <motion.div 
          className="mb-8"
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <div className="flex items-center gap-2 text-gray-400 mb-4">
            <span>Dashboard</span>
            <ChevronRight className="w-4 h-4" />
            <span className="text-white">Recomendaciones</span>
          </div>
          
          <div className="text-center mb-8">
            <div className="inline-flex items-center justify-center w-20 h-20 
              bg-gradient-to-br from-purple-600 to-blue-600 rounded-full mb-4">
              <Brain className="w-10 h-10 text-white" />
            </div>
            
            <h1 className="text-4xl font-bold text-white mb-4 font-cinzel">
              Sistema de Recomendaciones Adaptativas
            </h1>
            
            <p className="text-gray-300 max-w-2xl mx-auto">
              Recomendaciones personalizadas basadas en tu rendimiento, patrones 
              de aprendizaje y objetivos. El sistema se adapta continuamente 
              para optimizar tu experiencia de estudio.
            </p>
          </div>
        </motion.div>
        
        {/* Features Grid */}
        <motion.div 
          className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
        >
          <div className="bg-gray-900/80 rounded-lg p-6 border border-purple-500/30">
            <div className="w-12 h-12 bg-purple-600/20 rounded-lg flex items-center 
              justify-center mb-4">
              <Sparkles className="w-6 h-6 text-purple-400" />
            </div>
            <h3 className="text-lg font-semibold text-white mb-2">
              Análisis Inteligente
            </h3>
            <p className="text-gray-400 text-sm">
              Analiza tu rendimiento en tiempo real para identificar patrones 
              y áreas de mejora.
            </p>
          </div>
          
          <div className="bg-gray-900/80 rounded-lg p-6 border border-blue-500/30">
            <div className="w-12 h-12 bg-blue-600/20 rounded-lg flex items-center 
              justify-center mb-4">
              <Brain className="w-6 h-6 text-blue-400" />
            </div>
            <h3 className="text-lg font-semibold text-white mb-2">
              Personalización Continua
            </h3>
            <p className="text-gray-400 text-sm">
              Las recomendaciones evolucionan según tu progreso y estilo 
              de aprendizaje.
            </p>
          </div>
          
          <div className="bg-gray-900/80 rounded-lg p-6 border border-green-500/30">
            <div className="w-12 h-12 bg-green-600/20 rounded-lg flex items-center 
              justify-center mb-4">
              <ChevronRight className="w-6 h-6 text-green-400" />
            </div>
            <h3 className="text-lg font-semibold text-white mb-2">
              Objetivos Claros
            </h3>
            <p className="text-gray-400 text-sm">
              Define metas a corto, mediano y largo plazo con acciones 
              específicas.
            </p>
          </div>
        </motion.div>
        
        {/* Main Recommendations Component */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
        >
          <AdaptiveRecommendations />
        </motion.div>
        
        {/* Info Section */}
        <motion.div 
          className="mt-8 bg-gray-900/80 rounded-lg p-6 border border-gray-700"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6 }}
        >
          <h3 className="text-xl font-semibold text-white mb-4">
            ¿Cómo funcionan las recomendaciones?
          </h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-gray-300">
            <div>
              <h4 className="font-semibold text-white mb-2">
                Factores Analizados:
              </h4>
              <ul className="space-y-2 text-sm">
                <li className="flex items-start gap-2">
                  <span className="text-purple-400">•</span>
                  <span>Precisión por tema y nivel de dificultad</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-purple-400">•</span>
                  <span>Tiempo de respuesta y patrones de estudio</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-purple-400">•</span>
                  <span>Horarios de mayor rendimiento</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-purple-400">•</span>
                  <span>Progreso histórico y tendencias</span>
                </li>
              </ul>
            </div>
            
            <div>
              <h4 className="font-semibold text-white mb-2">
                Actualización Continua:
              </h4>
              <ul className="space-y-2 text-sm">
                <li className="flex items-start gap-2">
                  <span className="text-green-400">•</span>
                  <span>Se actualizan cada 6 horas automáticamente</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-green-400">•</span>
                  <span>Mayor precisión con más datos de uso</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-green-400">•</span>
                  <span>Ajustes inmediatos según tu feedback</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-green-400">•</span>
                  <span>Considera tu disponibilidad y objetivos</span>
                </li>
              </ul>
            </div>
          </div>
          
          <div className="mt-6 p-4 bg-purple-900/20 rounded-lg border 
            border-purple-500/30">
            <p className="text-sm text-purple-300">
              <strong>Nota:</strong> Mientras más uses la plataforma, más precisas 
              serán las recomendaciones. El sistema necesita al menos 10 respuestas 
              para generar recomendaciones personalizadas.
            </p>
          </div>
        </motion.div>
      </div>
    </div>
  );
}