'use client';

import React, { useState, useEffect } from 'react';
import { useStatsWorker, useAnalyticsWorker } from '../hooks/useWorker';
import { 
  Calculator, 
  Activity, 
  TrendingUp,
  Loader2,
  CheckCircle,
  AlertCircle,
  BarChart,
  PieChart,
  Brain
} from 'lucide-react';
import { motion } from 'framer-motion';

// Demo data
const generateDemoScores = (count: number) => {
  return Array.from({ length: count }, () => 
    Math.floor(Math.random() * 40) + 60 // Scores between 60-100
  );
};

const generateDemoBattles = (count: number) => {
  const enemyTypes = ['Goblin Matemático', 'Dragón Algebraico', 'Espectro Geométrico', 'Titán Trigonométrico'];
  const now = Date.now();
  
  return Array.from({ length: count }, (_, i) => ({
    id: `battle-${i}`,
    userId: 'demo-user',
    timestamp: now - (i * 24 * 60 * 60 * 1000), // One per day
    duration: Math.floor(Math.random() * 600) + 300, // 5-15 minutes
    questionsAnswered: Math.floor(Math.random() * 10) + 10,
    correctAnswers: Math.floor(Math.random() * 8) + 7,
    experienceGained: Math.floor(Math.random() * 200) + 100,
    enemyLevel: Math.floor(Math.random() * 5) + 1,
    enemyType: enemyTypes[Math.floor(Math.random() * enemyTypes.length)]
  }));
};

export default function WorkersDemoPage() {
  const statsWorker = useStatsWorker();
  const analyticsWorker = useAnalyticsWorker();
  
  const [activeDemo, setActiveDemo] = useState<string | null>(null);
  const [processingTime, setProcessingTime] = useState<number>(0);
  
  // Track processing time
  useEffect(() => {
    let interval: NodeJS.Timeout;
    
    if (statsWorker.isProcessing || analyticsWorker.isProcessing) {
      const startTime = Date.now();
      interval = setInterval(() => {
        setProcessingTime(Date.now() - startTime);
      }, 10);
    } else {
      setProcessingTime(0);
    }
    
    return () => clearInterval(interval);
  }, [statsWorker.isProcessing, analyticsWorker.isProcessing]);
  
  // Demo functions
  const runZScoreCalculation = () => {
    setActiveDemo('zscore');
    const userScore = 85;
    const mean = 75;
    const stdDev = 10;
    statsWorker.calculateZScore(userScore, mean, stdDev);
  };
  
  const runBatchStatistics = () => {
    setActiveDemo('batch');
    const scores = generateDemoScores(1000);
    const populationScores = generateDemoScores(5000);
    statsWorker.calculateBatchZScore(scores, populationScores);
  };
  
  const runPerformanceAnalysis = () => {
    setActiveDemo('performance');
    const topics = ['Álgebra', 'Geometría', 'Trigonometría', 'Estadística'];
    const userAnswers = Array.from({ length: 100 }, (_, i) => ({
      questionId: `q-${i}`,
      isCorrect: Math.random() > 0.3,
      responseTime: Math.floor(Math.random() * 20000) + 5000,
      difficulty: Math.floor(Math.random() * 5) + 1,
      topic: topics[Math.floor(Math.random() * topics.length)]
    }));
    
    const populationData = {
      averageByTopic: {
        'Álgebra': 75,
        'Geometría': 80,
        'Trigonometría': 70,
        'Estadística': 78
      },
      averageByDifficulty: {
        1: 90,
        2: 85,
        3: 75,
        4: 65,
        5: 55
      }
    };
    
    statsWorker.analyzePerformance(userAnswers, populationData);
  };
  
  const runBattleAnalytics = () => {
    setActiveDemo('battles');
    const battles = generateDemoBattles(30);
    analyticsWorker.processBattleData(battles);
  };
  
  const runProgressAnalytics = () => {
    setActiveDemo('progress');
    const progressHistory = Array.from({ length: 60 }, (_, i) => {
      const date = new Date();
      date.setDate(date.getDate() - (60 - i));
      
      return {
        date: date.toISOString(),
        level: Math.floor(i / 10) + 1,
        experience: (i * 150) + Math.floor(Math.random() * 50),
        rank: i < 10 ? 'E' : i < 20 ? 'D' : i < 35 ? 'C' : i < 50 ? 'B' : 'A',
        battlesWon: Math.floor(Math.random() * 5) + 1,
        questionsAnswered: Math.floor(Math.random() * 50) + 20,
        accuracy: Math.random() * 30 + 60
      };
    });
    
    analyticsWorker.processUserProgress(progressHistory);
  };
  
  const runInsightsGeneration = () => {
    setActiveDemo('insights');
    const userStats = {
      totalBattles: 150,
      winRate: 78,
      avgAccuracy: 82,
      favoriteSubject: 'Matemáticas',
      weakestTopic: 'Trigonometría',
      strongestTopic: 'Álgebra',
      peakHour: 20,
      streakDays: 45
    };
    
    analyticsWorker.generateInsights(userStats, true);
  };
  
  // Get results
  const getActiveResults = () => {
    if (!activeDemo) return null;
    
    switch (activeDemo) {
      case 'zscore':
        return statsWorker.results.Z_SCORE_RESULT;
      case 'batch':
        return statsWorker.results.BATCH_Z_SCORE_RESULT;
      case 'performance':
        return statsWorker.results.PERFORMANCE_ANALYSIS_RESULT;
      case 'battles':
        return analyticsWorker.results.BATTLE_DATA_PROCESSED;
      case 'progress':
        return analyticsWorker.results.USER_PROGRESS_PROCESSED;
      case 'insights':
        return analyticsWorker.results.INSIGHTS_GENERATED;
      default:
        return null;
    }
  };
  
  const results = getActiveResults();
  const isProcessing = statsWorker.isProcessing || analyticsWorker.isProcessing;
  
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900 
      to-gray-900 p-4">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-20 h-20 
            bg-purple-600 rounded-full mb-4">
            <Brain className="w-10 h-10 text-white" />
          </div>
          
          <h1 className="text-4xl font-bold text-white mb-4 font-cinzel">
            Web Workers Demo
          </h1>
          
          <p className="text-gray-300 max-w-2xl mx-auto">
            Los Web Workers ejecutan cálculos pesados en hilos separados, 
            manteniendo la interfaz fluida y responsiva.
          </p>
        </div>
        
        {/* Demo Buttons */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
          {/* Stats Worker Demos */}
          <motion.button
            onClick={runZScoreCalculation}
            disabled={isProcessing}
            className="bg-gray-900/80 hover:bg-gray-800/80 rounded-lg p-6 
              text-left transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            <Calculator className="w-8 h-8 text-purple-400 mb-3" />
            <h3 className="text-lg font-semibold text-white mb-2">
              Cálculo Z-Score
            </h3>
            <p className="text-sm text-gray-400">
              Calcula la puntuación estándar de un valor
            </p>
          </motion.button>
          
          <motion.button
            onClick={runBatchStatistics}
            disabled={isProcessing}
            className="bg-gray-900/80 hover:bg-gray-800/80 rounded-lg p-6 
              text-left transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            <BarChart className="w-8 h-8 text-blue-400 mb-3" />
            <h3 className="text-lg font-semibold text-white mb-2">
              Estadísticas Masivas
            </h3>
            <p className="text-sm text-gray-400">
              Procesa 1000+ puntuaciones simultáneamente
            </p>
          </motion.button>
          
          <motion.button
            onClick={runPerformanceAnalysis}
            disabled={isProcessing}
            className="bg-gray-900/80 hover:bg-gray-800/80 rounded-lg p-6 
              text-left transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            <TrendingUp className="w-8 h-8 text-green-400 mb-3" />
            <h3 className="text-lg font-semibold text-white mb-2">
              Análisis de Rendimiento
            </h3>
            <p className="text-sm text-gray-400">
              Analiza patrones en 100 respuestas
            </p>
          </motion.button>
          
          {/* Analytics Worker Demos */}
          <motion.button
            onClick={runBattleAnalytics}
            disabled={isProcessing}
            className="bg-gray-900/80 hover:bg-gray-800/80 rounded-lg p-6 
              text-left transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            <Activity className="w-8 h-8 text-red-400 mb-3" />
            <h3 className="text-lg font-semibold text-white mb-2">
              Analytics de Batallas
            </h3>
            <p className="text-sm text-gray-400">
              Procesa datos de 30 días de batallas
            </p>
          </motion.button>
          
          <motion.button
            onClick={runProgressAnalytics}
            disabled={isProcessing}
            className="bg-gray-900/80 hover:bg-gray-800/80 rounded-lg p-6 
              text-left transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            <PieChart className="w-8 h-8 text-yellow-400 mb-3" />
            <h3 className="text-lg font-semibold text-white mb-2">
              Progreso del Usuario
            </h3>
            <p className="text-sm text-gray-400">
              Analiza 60 días de progreso histórico
            </p>
          </motion.button>
          
          <motion.button
            onClick={runInsightsGeneration}
            disabled={isProcessing}
            className="bg-gray-900/80 hover:bg-gray-800/80 rounded-lg p-6 
              text-left transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            <Brain className="w-8 h-8 text-purple-400 mb-3" />
            <h3 className="text-lg font-semibold text-white mb-2">
              Generar Insights
            </h3>
            <p className="text-sm text-gray-400">
              Crea recomendaciones personalizadas
            </p>
          </motion.button>
        </div>
        
        {/* Processing Status */}
        {isProcessing && (
          <div className="bg-gray-900/80 rounded-lg p-6 mb-8">
            <div className="flex items-center justify-center">
              <Loader2 className="w-8 h-8 text-purple-400 animate-spin mr-3" />
              <div>
                <p className="text-white font-semibold">Procesando en Worker Thread...</p>
                <p className="text-sm text-gray-400">
                  Tiempo: {(processingTime / 1000).toFixed(2)}s
                </p>
              </div>
            </div>
          </div>
        )}
        
        {/* Results Display */}
        {results && !isProcessing && (
          <motion.div
            className="bg-gray-900/80 rounded-lg p-6"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
          >
            <div className="flex items-center gap-2 mb-4">
              <CheckCircle className="w-6 h-6 text-green-400" />
              <h3 className="text-xl font-semibold text-white">
                Resultados del Worker
              </h3>
              <span className="text-sm text-gray-400 ml-auto">
                Procesado en: {(processingTime / 1000).toFixed(2)}s
              </span>
            </div>
            
            <div className="bg-gray-800 rounded-lg p-4 overflow-auto max-h-96">
              <pre className="text-sm text-gray-300">
                {JSON.stringify(results, null, 2)}
              </pre>
            </div>
            
            {/* Visual Results for specific demos */}
            {activeDemo === 'insights' && results.insights && (
              <div className="mt-4 space-y-2">
                <h4 className="font-semibold text-white mb-2">Insights Generados:</h4>
                {results.insights.map((insight: string, i: number) => (
                  <div key={i} className="bg-gray-800 rounded-lg p-3 text-gray-300">
                    {insight}
                  </div>
                ))}
              </div>
            )}
          </motion.div>
        )}
        
        {/* Info Section */}
        <div className="mt-8 bg-gray-900/80 rounded-lg p-6">
          <h3 className="text-xl font-semibold text-white mb-4">
            ¿Por qué usar Web Workers?
          </h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-gray-300">
            <div>
              <h4 className="font-semibold text-white mb-2">Sin Workers:</h4>
              <ul className="space-y-2 text-sm">
                <li className="flex items-start gap-2">
                  <AlertCircle className="w-4 h-4 text-red-400 mt-0.5" />
                  La UI se congela durante cálculos pesados
                </li>
                <li className="flex items-start gap-2">
                  <AlertCircle className="w-4 h-4 text-red-400 mt-0.5" />
                  Animaciones entrecortadas
                </li>
                <li className="flex items-start gap-2">
                  <AlertCircle className="w-4 h-4 text-red-400 mt-0.5" />
                  Mal rendimiento en dispositivos lentos
                </li>
              </ul>
            </div>
            
            <div>
              <h4 className="font-semibold text-white mb-2">Con Workers:</h4>
              <ul className="space-y-2 text-sm">
                <li className="flex items-start gap-2">
                  <CheckCircle className="w-4 h-4 text-green-400 mt-0.5" />
                  UI siempre responsiva y fluida
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle className="w-4 h-4 text-green-400 mt-0.5" />
                  Cálculos en paralelo
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle className="w-4 h-4 text-green-400 mt-0.5" />
                  Mejor experiencia en todos los dispositivos
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}