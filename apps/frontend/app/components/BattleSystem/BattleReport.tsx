'use client';

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Trophy, 
  TrendingUp, 
  AlertCircle, 
  Brain, 
  Target,
  Zap,
  ChevronRight,
  Star,
  Lock,
  Unlock,
  MessageSquare,
  BarChart3
} from 'lucide-react';
import { useAudio } from '../PortalLogin/AudioEngine';
import { apiClient } from '@/lib/axios';
import { useBattleStore } from '@/stores/useBattleStore';
import { useAuthStore } from '@/stores/useAuthStore';

interface BattleStats {
  accuracy: number;
  totalQuestions: number;
  correctAnswers: number;
  incorrectAnswers: number;
  avgResponseTime: number;
  byTag: Record<string, {
    correct: number;
    total: number;
    accuracy: number;
  }>;
  byDifficulty: Record<number, {
    correct: number;
    total: number;
    accuracy: number;
  }>;
}

interface Weakness {
  tag: string;
  accuracy: number;
  zScore: number;
  recommendation: string;
}

interface BattleReportProps {
  stats: BattleStats;
  onClose: () => void;
  onRankUp?: () => void;
  battleId?: string;
}

export default function BattleReport({ stats, onClose, onRankUp, battleId }: BattleReportProps) {
  const { playSound } = useAudio();
  const { user } = useAuthStore();
  const { currentEnemy } = useBattleStore();
  
  const [aiTip, setAiTip] = useState<string | null>(null);
  const [isLoadingTip, setIsLoadingTip] = useState(false);
  const [weaknesses, setWeaknesses] = useState<Weakness[]>([]);
  const [showDetails, setShowDetails] = useState(false);
  const [canRankUp, setCanRankUp] = useState(false);
  
  // Statistical constants
  const POPULATION_MEAN = 70; // Average accuracy percentage
  const POPULATION_STD = 15;  // Standard deviation
  const WEAKNESS_THRESHOLD = -1; // Z-score below -1 is considered weak
  
  // Calculate Z-Score
  const calculateZScore = (accuracy: number, mean = POPULATION_MEAN, std = POPULATION_STD): number => {
    return (accuracy - mean) / std;
  };
  
  // Get performance level based on Z-Score
  const getPerformanceLevel = (zScore: number): { level: string; color: string; icon: React.ReactNode } => {
    if (zScore >= 2) return { 
      level: 'Excepcional', 
      color: 'text-purple-400', 
      icon: <Star className="w-5 h-5" /> 
    };
    if (zScore >= 1) return { 
      level: 'Superior', 
      color: 'text-green-400', 
      icon: <TrendingUp className="w-5 h-5" /> 
    };
    if (zScore >= 0) return { 
      level: 'Promedio', 
      color: 'text-blue-400', 
      icon: <Target className="w-5 h-5" /> 
    };
    if (zScore >= -1) return { 
      level: 'Bajo Promedio', 
      color: 'text-yellow-400', 
      icon: <AlertCircle className="w-5 h-5" /> 
    };
    return { 
      level: 'Necesita Mejora', 
      color: 'text-red-400', 
      icon: <AlertCircle className="w-5 h-5" /> 
    };
  };
  
  // Analyze weaknesses
  useEffect(() => {
    const detectedWeaknesses: Weakness[] = [];
    
    Object.entries(stats.byTag).forEach(([tag, data]) => {
      const zScore = calculateZScore(data.accuracy);
      if (zScore < WEAKNESS_THRESHOLD) {
        detectedWeaknesses.push({
          tag,
          accuracy: data.accuracy,
          zScore,
          recommendation: getRecommendation(tag, data.accuracy)
        });
      }
    });
    
    // Sort by worst performance
    detectedWeaknesses.sort((a, b) => a.zScore - b.zScore);
    setWeaknesses(detectedWeaknesses);
    
    // Check if can rank up (no critical weaknesses and overall accuracy > 80%)
    const hasNoWeaknesses = detectedWeaknesses.length === 0;
    const highAccuracy = stats.accuracy >= 80;
    setCanRankUp(hasNoWeaknesses && highAccuracy);
    
    // Play appropriate sound
    if (stats.accuracy >= 90) {
      playSound('level_up');
    } else if (stats.accuracy >= 70) {
      playSound('quest_complete');
    } else {
      playSound('notification_epic');
    }
  }, [stats, playSound]);
  
  // Get AI tip for weaknesses
  useEffect(() => {
    if (weaknesses.length > 0 && !aiTip) {
      fetchAITip();
    }
  }, [weaknesses]);
  
  const fetchAITip = async () => {
    if (weaknesses.length === 0) return;
    
    setIsLoadingTip(true);
    try {
      const response = await apiClient.post('/ai/battle-tip', {
        weaknesses: weaknesses.map(w => ({
          tag: w.tag,
          accuracy: w.accuracy
        })),
        user_level: user?.level || 1,
        battle_context: currentEnemy?.name || 'General Practice'
      });
      
      setAiTip(response.tip);
      playSound('notification_epic');
    } catch (error) {
      console.error('Failed to get AI tip:', error);
      // Fallback tip
      setAiTip(getGenericTip());
    } finally {
      setIsLoadingTip(false);
    }
  };
  
  const getRecommendation = (tag: string, accuracy: number): string => {
    const recommendations: Record<string, string[]> = {
      'algebra': [
        'Practica ecuaciones lineales diariamente',
        'Revisa las propiedades de exponentes',
        'Enfócate en factorización'
      ],
      'geometry': [
        'Estudia teoremas fundamentales',
        'Practica con figuras 3D',
        'Memoriza fórmulas de áreas'
      ],
      'reading': [
        'Lee textos diversos cada día',
        'Practica identificar ideas principales',
        'Mejora tu vocabulario'
      ],
      'default': [
        'Dedica 30 minutos diarios a este tema',
        'Busca recursos adicionales',
        'Practica con ejercicios variados'
      ]
    };
    
    const tagRecs = recommendations[tag.toLowerCase()] || recommendations.default;
    return tagRecs[Math.floor(accuracy / 30)] || tagRecs[0];
  };
  
  const getGenericTip = (): string => {
    const tips = [
      "Enfócate en los conceptos fundamentales antes de avanzar a temas complejos.",
      "La práctica constante es clave. Dedica al menos 20 minutos diarios.",
      "Identifica patrones en los problemas para resolverlos más eficientemente.",
      "No te desanimes por los errores, son oportunidades de aprendizaje."
    ];
    return tips[Math.floor(Math.random() * tips.length)];
  };
  
  const overallZScore = calculateZScore(stats.accuracy);
  const performance = getPerformanceLevel(overallZScore);
  
  return (
    <motion.div
      className="fixed inset-0 bg-black/80 flex items-center justify-center p-4 z-50"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
    >
      <motion.div
        className="bg-gray-900 rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto"
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.9, opacity: 0 }}
      >
        {/* Header */}
        <div className="bg-gradient-to-r from-purple-900 to-indigo-900 p-6 rounded-t-lg">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-3xl font-bold text-white mb-2 font-cinzel">
                Reporte de Batalla
              </h2>
              <p className="text-purple-200">
                Análisis detallado de tu rendimiento
              </p>
            </div>
            <Trophy className="w-16 h-16 text-yellow-400" />
          </div>
        </div>
        
        {/* Main Stats */}
        <div className="p-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            {/* Overall Accuracy */}
            <motion.div
              className="bg-gray-800 rounded-lg p-6 text-center"
              initial={{ y: 20, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              transition={{ delay: 0.1 }}
            >
              <div className="mb-4">
                <div className="text-5xl font-bold text-white mb-2">
                  {stats.accuracy}%
                </div>
                <div className="text-gray-400">Precisión Total</div>
              </div>
              <div className={`flex items-center justify-center gap-2 ${performance.color}`}>
                {performance.icon}
                <span className="font-semibold">{performance.level}</span>
              </div>
              <div className="mt-2 text-sm text-gray-500">
                Z-Score: {overallZScore.toFixed(2)}
              </div>
            </motion.div>
            
            {/* Questions Summary */}
            <motion.div
              className="bg-gray-800 rounded-lg p-6"
              initial={{ y: 20, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              transition={{ delay: 0.2 }}
            >
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-gray-400">Total Preguntas:</span>
                  <span className="text-white font-semibold">{stats.totalQuestions}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Correctas:</span>
                  <span className="text-green-400 font-semibold">{stats.correctAnswers}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Incorrectas:</span>
                  <span className="text-red-400 font-semibold">{stats.incorrectAnswers}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Tiempo Promedio:</span>
                  <span className="text-blue-400 font-semibold">{stats.avgResponseTime}s</span>
                </div>
              </div>
            </motion.div>
            
            {/* Rank Progress */}
            <motion.div
              className="bg-gray-800 rounded-lg p-6 text-center"
              initial={{ y: 20, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              transition={{ delay: 0.3 }}
            >
              <div className="mb-4">
                {canRankUp ? (
                  <Unlock className="w-12 h-12 text-green-400 mx-auto mb-2" />
                ) : (
                  <Lock className="w-12 h-12 text-gray-500 mx-auto mb-2" />
                )}
                <div className="text-lg font-semibold text-white">
                  {canRankUp ? 'Listo para Ascender' : 'Ascenso Bloqueado'}
                </div>
              </div>
              {!canRankUp && (
                <p className="text-sm text-gray-400">
                  {weaknesses.length > 0
                    ? `Mejora ${weaknesses.length} área${weaknesses.length > 1 ? 's' : ''} débil${weaknesses.length > 1 ? 'es' : ''}`
                    : 'Alcanza 80% de precisión'}
                </p>
              )}
            </motion.div>
          </div>
          
          {/* Performance by Tag */}
          <div className="mb-8">
            <button
              onClick={() => setShowDetails(!showDetails)}
              className="flex items-center gap-2 text-lg font-semibold text-white mb-4 hover:text-purple-400 transition-colors"
            >
              <BarChart3 className="w-5 h-5" />
              Análisis Detallado
              <ChevronRight className={`w-5 h-5 transition-transform ${showDetails ? 'rotate-90' : ''}`} />
            </button>
            
            <AnimatePresence>
              {showDetails && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: 'auto', opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  className="space-y-3 overflow-hidden"
                >
                  {Object.entries(stats.byTag).map(([tag, data], index) => {
                    const zScore = calculateZScore(data.accuracy);
                    const perf = getPerformanceLevel(zScore);
                    
                    return (
                      <motion.div
                        key={tag}
                        className="bg-gray-800 rounded-lg p-4"
                        initial={{ x: -20, opacity: 0 }}
                        animate={{ x: 0, opacity: 1 }}
                        transition={{ delay: index * 0.05 }}
                      >
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center gap-2">
                            <span className="font-semibold text-white capitalize">
                              {tag}
                            </span>
                            <span className={`text-sm ${perf.color}`}>
                              {perf.level}
                            </span>
                          </div>
                          <div className="flex items-center gap-4">
                            <span className="text-sm text-gray-400">
                              {data.correct}/{data.total}
                            </span>
                            <span className="font-semibold text-white">
                              {data.accuracy}%
                            </span>
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          <div className="flex-1 bg-gray-700 rounded-full h-2">
                            <motion.div
                              className={`h-full rounded-full ${
                                data.accuracy >= 80 ? 'bg-green-500' :
                                data.accuracy >= 60 ? 'bg-blue-500' :
                                data.accuracy >= 40 ? 'bg-yellow-500' :
                                'bg-red-500'
                              }`}
                              initial={{ width: 0 }}
                              animate={{ width: `${data.accuracy}%` }}
                              transition={{ duration: 0.5, delay: index * 0.05 }}
                            />
                          </div>
                          <span className="text-xs text-gray-500">
                            Z: {zScore.toFixed(2)}
                          </span>
                        </div>
                      </motion.div>
                    );
                  })}
                </motion.div>
              )}
            </AnimatePresence>
          </div>
          
          {/* Weaknesses & AI Tips */}
          {weaknesses.length > 0 && (
            <motion.div
              className="bg-red-900/20 rounded-lg p-6 border border-red-500/30 mb-8"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.4 }}
            >
              <div className="flex items-center gap-2 mb-4">
                <AlertCircle className="w-5 h-5 text-red-400" />
                <h3 className="text-lg font-semibold text-red-300">
                  Áreas a Mejorar
                </h3>
              </div>
              
              <div className="space-y-3 mb-4">
                {weaknesses.map((weakness, index) => (
                  <div
                    key={weakness.tag}
                    className="bg-gray-800/50 rounded-lg p-3"
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-semibold text-white capitalize">
                        {weakness.tag}
                      </span>
                      <span className="text-red-400">
                        {weakness.accuracy}% (Z: {weakness.zScore.toFixed(2)})
                      </span>
                    </div>
                    <p className="text-sm text-gray-300">
                      {weakness.recommendation}
                    </p>
                  </div>
                ))}
              </div>
              
              {/* AI Tip */}
              <div className="bg-purple-900/30 rounded-lg p-4 border border-purple-500/30">
                <div className="flex items-center gap-2 mb-2">
                  <Brain className="w-5 h-5 text-purple-400" />
                  <span className="font-semibold text-purple-300">
                    Consejo del Sistema IA
                  </span>
                </div>
                {isLoadingTip ? (
                  <div className="flex items-center gap-2 text-gray-400">
                    <motion.div
                      className="w-4 h-4 border-2 border-purple-400 border-t-transparent rounded-full"
                      animate={{ rotate: 360 }}
                      transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                    />
                    Generando consejo personalizado...
                  </div>
                ) : (
                  <p className="text-sm text-gray-300">
                    {aiTip || getGenericTip()}
                  </p>
                )}
              </div>
            </motion.div>
          )}
          
          {/* Action Buttons */}
          <div className="flex gap-4">
            <button
              onClick={onClose}
              className="flex-1 bg-gray-700 hover:bg-gray-600 text-white font-semibold py-3 px-6 rounded-lg transition-all"
            >
              Cerrar Reporte
            </button>
            {canRankUp && onRankUp && (
              <motion.button
                onClick={onRankUp}
                className="flex-1 bg-gradient-to-r from-yellow-500 to-yellow-600 hover:from-yellow-600 hover:to-yellow-700 
                  text-black font-bold py-3 px-6 rounded-lg transition-all flex items-center justify-center gap-2"
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
              >
                <Zap className="w-5 h-5" />
                Subir de Rango
              </motion.button>
            )}
          </div>
        </div>
      </motion.div>
    </motion.div>
  );
}