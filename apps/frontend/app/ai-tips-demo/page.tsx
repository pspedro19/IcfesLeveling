'use client';

import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { 
  Brain,
  Sparkles,
  TrendingUp,
  Target,
  Calendar,
  MessageSquare,
  Award,
  RefreshCw,
  CheckCircle
} from 'lucide-react';
import AIBattleTips from '@/components/AI/AIBattleTips';
import AIExplanation from '@/components/AI/AIExplanation';
import { aiTipsService } from '@/services/ai-tips.service';

export default function AITipsDemoPage() {
  const [serviceStatus, setServiceStatus] = useState<any>(null);
  const [studyPlan, setStudyPlan] = useState<any>(null);
  const [learningPattern, setLearningPattern] = useState<any>(null);
  const [motivationalMessage, setMotivationalMessage] = useState<string>('');
  const [loading, setLoading] = useState<Record<string, boolean>>({});
  
  // Check service status
  useEffect(() => {
    checkServiceStatus();
  }, []);
  
  const checkServiceStatus = async () => {
    try {
      const status = await aiTipsService.checkServiceStatus();
      setServiceStatus(status);
    } catch (error) {
      console.error('Error checking service status:', error);
    }
  };
  
  const fetchStudyPlan = async () => {
    setLoading(prev => ({ ...prev, studyPlan: true }));
    try {
      const plan = await aiTipsService.getStudyPlan(
        [
          { topic: 'Álgebra', accuracy: 65, questionsAnswered: 50 },
          { topic: 'Geometría', accuracy: 72, questionsAnswered: 30 }
        ],
        60, // 60 minutes per day
        350 // Target score
      );
      setStudyPlan(plan);
    } catch (error) {
      console.error('Error fetching study plan:', error);
    } finally {
      setLoading(prev => ({ ...prev, studyPlan: false }));
    }
  };
  
  const fetchLearningPattern = async () => {
    setLoading(prev => ({ ...prev, pattern: true }));
    try {
      const pattern = await aiTipsService.analyzeLearningPattern(7);
      setLearningPattern(pattern);
    } catch (error) {
      console.error('Error analyzing pattern:', error);
    } finally {
      setLoading(prev => ({ ...prev, pattern: false }));
    }
  };
  
  const fetchMotivationalMessage = async (context: any) => {
    setLoading(prev => ({ ...prev, motivation: true }));
    try {
      const message = await aiTipsService.getMotivationalMessage(context);
      setMotivationalMessage(message);
    } catch (error) {
      console.error('Error getting motivational message:', error);
    } finally {
      setLoading(prev => ({ ...prev, motivation: false }));
    }
  };
  
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
            Sistema de Tips con IA
          </h1>
          
          <p className="text-gray-300 max-w-2xl mx-auto">
            Demostración del sistema de inteligencia artificial que proporciona 
            tips personalizados, explicaciones detalladas y planes de estudio adaptados.
          </p>
        </div>
        
        {/* Service Status */}
        {serviceStatus && (
          <motion.div
            className="bg-gray-900/80 rounded-lg p-6 mb-8 border border-gray-700"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
          >
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold text-white flex items-center gap-2">
                <CheckCircle className="w-6 h-6 text-green-400" />
                Estado del Servicio
              </h2>
              <div className={`px-3 py-1 rounded-full text-sm font-semibold ${
                serviceStatus.available 
                  ? 'bg-green-600/20 text-green-400'
                  : 'bg-red-600/20 text-red-400'
              }`}>
                {serviceStatus.service}
              </div>
            </div>
            
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
              {Object.entries(serviceStatus.features).map(([feature, enabled]) => (
                <div
                  key={feature}
                  className={`p-3 rounded-lg text-center ${
                    enabled 
                      ? 'bg-green-900/20 border border-green-500/30'
                      : 'bg-red-900/20 border border-red-500/30'
                  }`}
                >
                  <p className="text-xs text-gray-400 mb-1">
                    {feature.replace(/_/g, ' ')}
                  </p>
                  <p className={`font-semibold ${
                    enabled ? 'text-green-400' : 'text-red-400'
                  }`}>
                    {enabled ? 'Activo' : 'Inactivo'}
                  </p>
                </div>
              ))}
            </div>
          </motion.div>
        )}
        
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Battle Tips Demo */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.1 }}
          >
            <h2 className="text-2xl font-semibold text-white mb-4 flex items-center gap-2">
              <Sparkles className="w-6 h-6 text-purple-400" />
              Tips de Batalla
            </h2>
            <AIBattleTips
              battleId="demo-battle-123"
              currentTopic="Matemáticas"
              difficulty={7}
              battleType="boss"
              onTipClick={(tip) => console.log('Tip clicked:', tip)}
            />
          </motion.div>
          
          {/* Question Explanation Demo */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.2 }}
          >
            <h2 className="text-2xl font-semibold text-white mb-4 flex items-center gap-2">
              <MessageSquare className="w-6 h-6 text-blue-400" />
              Explicación de Pregunta
            </h2>
            <AIExplanation
              questionId="demo-question-456"
              userAnswer="B"
              isCorrect={false}
              correctAnswer="C"
              hint="Recuerda aplicar la fórmula cuadrática paso a paso"
            />
          </motion.div>
          
          {/* Study Plan Demo */}
          <motion.div
            className="lg:col-span-2"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
          >
            <h2 className="text-2xl font-semibold text-white mb-4 flex items-center gap-2">
              <Calendar className="w-6 h-6 text-green-400" />
              Plan de Estudio Personalizado
            </h2>
            
            <div className="bg-gray-900/80 rounded-lg p-6 border border-green-500/30">
              {!studyPlan ? (
                <button
                  onClick={fetchStudyPlan}
                  disabled={loading.studyPlan}
                  className="w-full py-3 bg-green-600 hover:bg-green-700 text-white 
                    rounded-lg font-semibold transition-all disabled:opacity-50"
                >
                  {loading.studyPlan ? 'Generando...' : 'Generar Plan de Estudio'}
                </button>
              ) : (
                <div className="space-y-6">
                  <div>
                    <h3 className="font-semibold text-white mb-3">Objetivos</h3>
                    <ul className="space-y-2">
                      {studyPlan.objectives.map((objective: string, index: number) => (
                        <li key={index} className="flex items-start gap-2">
                          <Target className="w-4 h-4 text-green-400 mt-0.5" />
                          <span className="text-gray-300 text-sm">{objective}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                  
                  <div>
                    <h3 className="font-semibold text-white mb-3">Estrategias</h3>
                    <ul className="space-y-2">
                      {studyPlan.strategies.map((strategy: string, index: number) => (
                        <li key={index} className="flex items-start gap-2">
                          <TrendingUp className="w-4 h-4 text-blue-400 mt-0.5" />
                          <span className="text-gray-300 text-sm">{strategy}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="bg-gray-800/50 rounded-lg p-4">
                      <p className="text-gray-400 text-sm mb-1">Tiempo diario</p>
                      <p className="text-xl font-semibold text-white">
                        {studyPlan.dailyTime}
                      </p>
                    </div>
                    
                    <div className="bg-gray-800/50 rounded-lg p-4">
                      <p className="text-gray-400 text-sm mb-1">Generado por</p>
                      <p className="text-xl font-semibold text-purple-400">
                        {studyPlan.generated ? 'IA Personalizada' : 'Sistema Base'}
                      </p>
                    </div>
                  </div>
                  
                  <button
                    onClick={fetchStudyPlan}
                    className="flex items-center gap-2 text-green-400 hover:text-green-300 
                      transition-colors"
                  >
                    <RefreshCw className="w-4 h-4" />
                    <span>Regenerar Plan</span>
                  </button>
                </div>
              )}
            </div>
          </motion.div>
          
          {/* Learning Pattern Analysis */}
          <motion.div
            className="lg:col-span-2"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
          >
            <h2 className="text-2xl font-semibold text-white mb-4 flex items-center gap-2">
              <TrendingUp className="w-6 h-6 text-purple-400" />
              Análisis de Patrones de Aprendizaje
            </h2>
            
            <div className="bg-gray-900/80 rounded-lg p-6 border border-purple-500/30">
              {!learningPattern ? (
                <button
                  onClick={fetchLearningPattern}
                  disabled={loading.pattern}
                  className="w-full py-3 bg-purple-600 hover:bg-purple-700 text-white 
                    rounded-lg font-semibold transition-all disabled:opacity-50"
                >
                  {loading.pattern ? 'Analizando...' : 'Analizar Patrón de Aprendizaje'}
                </button>
              ) : (
                <div className="space-y-6">
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="bg-gray-800/50 rounded-lg p-4 text-center">
                      <p className="text-gray-400 text-sm mb-1">Patrón</p>
                      <p className="text-xl font-semibold text-purple-400">
                        {learningPattern.pattern}
                      </p>
                    </div>
                    
                    <div className="bg-gray-800/50 rounded-lg p-4 text-center">
                      <p className="text-gray-400 text-sm mb-1">Precisión</p>
                      <p className="text-xl font-semibold text-green-400">
                        {learningPattern.metrics.accuracy}%
                      </p>
                    </div>
                    
                    <div className="bg-gray-800/50 rounded-lg p-4 text-center">
                      <p className="text-gray-400 text-sm mb-1">Tiempo Promedio</p>
                      <p className="text-xl font-semibold text-blue-400">
                        {learningPattern.metrics.avgResponseTime}s
                      </p>
                    </div>
                    
                    <div className="bg-gray-800/50 rounded-lg p-4 text-center">
                      <p className="text-gray-400 text-sm mb-1">Tendencia</p>
                      <p className="text-xl font-semibold text-yellow-400">
                        {learningPattern.metrics.difficultyTrend}
                      </p>
                    </div>
                  </div>
                  
                  <div>
                    <h3 className="font-semibold text-white mb-3">Insights</h3>
                    <div className="space-y-2">
                      {learningPattern.insights.map((insight: string, index: number) => (
                        <div
                          key={index}
                          className="bg-purple-900/20 rounded-lg p-3 border 
                            border-purple-500/30"
                        >
                          <p className="text-gray-300 text-sm">{insight}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                  
                  <button
                    onClick={fetchLearningPattern}
                    className="flex items-center gap-2 text-purple-400 hover:text-purple-300 
                      transition-colors"
                  >
                    <RefreshCw className="w-4 h-4" />
                    <span>Actualizar Análisis</span>
                  </button>
                </div>
              )}
            </div>
          </motion.div>
          
          {/* Motivational Messages */}
          <motion.div
            className="lg:col-span-2"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5 }}
          >
            <h2 className="text-2xl font-semibold text-white mb-4 flex items-center gap-2">
              <Award className="w-6 h-6 text-yellow-400" />
              Mensajes Motivacionales
            </h2>
            
            <div className="bg-gray-900/80 rounded-lg p-6 border border-yellow-500/30">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                {['level_up', 'streak', 'battle_won', 'achievement'].map(context => (
                  <button
                    key={context}
                    onClick={() => fetchMotivationalMessage(context)}
                    disabled={loading.motivation}
                    className="py-2 px-4 bg-yellow-600/20 hover:bg-yellow-600/30 
                      border border-yellow-500/30 rounded-lg text-yellow-400 
                      font-semibold transition-all disabled:opacity-50"
                  >
                    {context.replace('_', ' ')}
                  </button>
                ))}
              </div>
              
              {motivationalMessage && (
                <motion.div
                  className="bg-gradient-to-br from-yellow-900/20 to-orange-900/20 
                    rounded-lg p-6 border border-yellow-500/50 text-center"
                  initial={{ scale: 0.9, opacity: 0 }}
                  animate={{ scale: 1, opacity: 1 }}
                >
                  <Award className="w-12 h-12 text-yellow-400 mx-auto mb-4" />
                  <p className="text-xl text-white font-semibold leading-relaxed">
                    {motivationalMessage}
                  </p>
                </motion.div>
              )}
            </div>
          </motion.div>
        </div>
      </div>
    </div>
  );
}