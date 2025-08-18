'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Trophy, 
  Target, 
  TrendingUp, 
  AlertCircle,
  CheckCircle,
  XCircle,
  BookOpen,
  Zap,
  Shield,
  Sparkles,
  ChevronRight,
  Brain,
  BarChart3,
  Clock,
  Award
} from 'lucide-react';

interface DiagnosticResults {
  score?: number;
  percentage?: number;
  strengths?: string[];
  weaknesses?: string[];
  recommendations?: string[];
  subject?: string;
  subject_id?: string;
  test_id?: string;
  total_questions?: number;
  correct_answers?: number;
  answered_questions?: number;
  time_spent?: number;
  rank?: string;
  message?: string;
}

export default function DiagnosticTestResults() {
  const router = useRouter();
  const [results, setResults] = useState<DiagnosticResults | null>(null);
  const [creatingPlan, setCreatingPlan] = useState(false);
  const [planCreated, setPlanCreated] = useState(false);
  const [showDetails, setShowDetails] = useState(false);

  useEffect(() => {
    // Load results from session storage
    const storedResults = sessionStorage.getItem('diagnostic_results');
    if (storedResults) {
      setResults(JSON.parse(storedResults));
    } else {
      // Redirect if no results
      router.push('/diagnostic-test');
    }
  }, []);

  const createStudyPlan = async () => {
    if (!results || creatingPlan) return;
    
    setCreatingPlan(true);
    
    try {
      // Store subject ID and diagnostic results for the study plan page
      if (results?.subject_id) {
        sessionStorage.setItem('last_subject_id', results.subject_id);
        sessionStorage.setItem('diagnostic_score', String(results.percentage || 65));
      }
      
      // Navigate directly to the beautiful Khan Academy style study plan view
      setPlanCreated(true);
      
      setTimeout(() => {
        const subjectId = results?.subject_id || '2a9c9371-b931-41d4-8d3e-ce5aae91a5c3';
        router.push(`/study-plan-view?subject=${subjectId}`);
      }, 1500);
      
    } catch (error) {
      console.error('Error navigating to study plan:', error);
      // Try to navigate anyway
      router.push('/study-plan-view');
    } finally {
      setCreatingPlan(false);
    }
  };

  const getRankByScore = (percentage: number) => {
    if (percentage >= 90) return { rank: 'S', color: 'from-yellow-400 to-orange-400' };
    if (percentage >= 80) return { rank: 'A', color: 'from-purple-400 to-purple-600' };
    if (percentage >= 70) return { rank: 'B', color: 'from-blue-400 to-blue-600' };
    if (percentage >= 60) return { rank: 'C', color: 'from-green-400 to-green-600' };
    if (percentage >= 50) return { rank: 'D', color: 'from-gray-400 to-gray-600' };
    return { rank: 'E', color: 'from-red-400 to-red-600' };
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}m ${secs}s`;
  };

  if (!results) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-900 via-black to-blue-900 flex items-center justify-center">
        <div className="animate-spin rounded-full h-16 w-16 border-t-4 border-purple-500"></div>
      </div>
    );
  }

  const percentage = results.percentage || 0;
  const rankInfo = getRankByScore(percentage);

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-black to-blue-900 relative overflow-hidden">
      {/* Animated Background */}
      <div className="absolute inset-0">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-purple-900/20 via-transparent to-transparent"></div>
        {[...Array(20)].map((_, i) => (
          <motion.div
            key={i}
            className="absolute rounded-full bg-purple-500/10 blur-xl"
            initial={{
              x: Math.random() * window.innerWidth,
              y: Math.random() * window.innerHeight,
            }}
            animate={{
              x: Math.random() * window.innerWidth,
              y: Math.random() * window.innerHeight,
            }}
            transition={{
              duration: Math.random() * 20 + 10,
              repeat: Infinity,
              repeatType: 'reverse',
            }}
            style={{
              width: Math.random() * 300 + 100,
              height: Math.random() * 300 + 100,
            }}
          />
        ))}
      </div>

      <div className="relative z-10 container mx-auto px-4 py-8">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -50 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-8"
        >
          <h1 className="text-5xl font-bold text-yellow-400 mb-4">
            🏆 Resultados del Diagnóstico
          </h1>
          <p className="text-xl text-purple-300">
            {results.subject} - Análisis Completo
          </p>
        </motion.div>

        {/* Main Results Card */}
        <motion.div
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.2 }}
          className="max-w-4xl mx-auto mb-8"
        >
          <div className="bg-black/40 backdrop-blur-xl rounded-2xl border border-purple-500/30 p-8">
            {/* Score Display */}
            <div className="grid md:grid-cols-2 gap-8 mb-8">
              {/* Left - Circular Score */}
              <div className="flex flex-col items-center justify-center">
                <motion.div
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  transition={{ delay: 0.4, type: 'spring' }}
                  className="relative w-48 h-48"
                >
                  {/* Background Circle */}
                  <svg className="w-48 h-48 transform -rotate-90">
                    <circle
                      cx="96"
                      cy="96"
                      r="88"
                      stroke="currentColor"
                      strokeWidth="8"
                      fill="none"
                      className="text-gray-700"
                    />
                    <motion.circle
                      cx="96"
                      cy="96"
                      r="88"
                      stroke="url(#gradient)"
                      strokeWidth="8"
                      fill="none"
                      strokeLinecap="round"
                      strokeDasharray={`${2 * Math.PI * 88}`}
                      initial={{ strokeDashoffset: 2 * Math.PI * 88 }}
                      animate={{ strokeDashoffset: 2 * Math.PI * 88 * (1 - percentage / 100) }}
                      transition={{ duration: 2, ease: 'easeOut' }}
                    />
                    <defs>
                      <linearGradient id="gradient">
                        <stop offset="0%" stopColor="#a855f7" />
                        <stop offset="100%" stopColor="#3b82f6" />
                      </linearGradient>
                    </defs>
                  </svg>
                  
                  {/* Center Content */}
                  <div className="absolute inset-0 flex flex-col items-center justify-center">
                    <motion.div
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      transition={{ delay: 1 }}
                      className="text-center"
                    >
                      <div className="text-5xl font-bold text-white">
                        {percentage}%
                      </div>
                      <div className={`text-2xl font-bold bg-gradient-to-r ${rankInfo.color} text-transparent bg-clip-text`}>
                        Rango {rankInfo.rank}
                      </div>
                    </motion.div>
                  </div>
                </motion.div>

                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: 1.2 }}
                  className="mt-4 text-center"
                >
                  <p className="text-purple-300 text-sm">Respuestas Correctas</p>
                  <p className="text-2xl font-bold text-white">
                    {results.correct_answers || 0} / {results.total_questions || 0}
                  </p>
                </motion.div>
              </div>

              {/* Right - Stats */}
              <div className="space-y-4">
                <motion.div
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.6 }}
                  className="bg-black/30 rounded-xl p-4 border border-purple-500/20"
                >
                  <div className="flex items-center gap-3 mb-2">
                    <Trophy className="w-5 h-5 text-yellow-400" />
                    <span className="text-purple-300">Puntaje</span>
                  </div>
                  <div className="text-2xl font-bold text-white">
                    {results.score || results.correct_answers || 0} puntos
                  </div>
                </motion.div>

                <motion.div
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.7 }}
                  className="bg-black/30 rounded-xl p-4 border border-purple-500/20"
                >
                  <div className="flex items-center gap-3 mb-2">
                    <Clock className="w-5 h-5 text-blue-400" />
                    <span className="text-purple-300">Tiempo Total</span>
                  </div>
                  <div className="text-2xl font-bold text-white">
                    {results.time_spent ? formatTime(results.time_spent) : 'N/A'}
                  </div>
                </motion.div>

                <motion.div
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.8 }}
                  className="bg-black/30 rounded-xl p-4 border border-purple-500/20"
                >
                  <div className="flex items-center gap-3 mb-2">
                    <Target className="w-5 h-5 text-green-400" />
                    <span className="text-purple-300">Precisión</span>
                  </div>
                  <div className="text-2xl font-bold text-white">
                    {percentage.toFixed(1)}%
                  </div>
                </motion.div>
              </div>
            </div>

            {/* Strengths and Weaknesses */}
            <div className="grid md:grid-cols-2 gap-6 mb-8">
              {/* Strengths */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.9 }}
                className="bg-green-900/20 rounded-xl p-6 border border-green-500/30"
              >
                <div className="flex items-center gap-2 mb-4">
                  <CheckCircle className="w-6 h-6 text-green-400" />
                  <h3 className="text-xl font-bold text-green-400">Fortalezas</h3>
                </div>
                <ul className="space-y-2">
                  {(results.strengths && results.strengths.length > 0) ? (
                    results.strengths.map((strength, index) => (
                      <motion.li
                        key={index}
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: 1 + index * 0.1 }}
                        className="flex items-start gap-2 text-green-300"
                      >
                        <Sparkles className="w-4 h-4 mt-0.5 flex-shrink-0" />
                        <span>{strength}</span>
                      </motion.li>
                    ))
                  ) : (
                    <li className="text-green-300">
                      {percentage >= 70 ? 'Buen dominio general del tema' : 'Continúa practicando para mejorar'}
                    </li>
                  )}
                </ul>
              </motion.div>

              {/* Weaknesses */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 1 }}
                className="bg-red-900/20 rounded-xl p-6 border border-red-500/30"
              >
                <div className="flex items-center gap-2 mb-4">
                  <AlertCircle className="w-6 h-6 text-red-400" />
                  <h3 className="text-xl font-bold text-red-400">Áreas de Mejora</h3>
                </div>
                <ul className="space-y-2">
                  {(results.weaknesses && results.weaknesses.length > 0) ? (
                    results.weaknesses.map((weakness, index) => (
                      <motion.li
                        key={index}
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: 1.1 + index * 0.1 }}
                        className="flex items-start gap-2 text-red-300"
                      >
                        <Target className="w-4 h-4 mt-0.5 flex-shrink-0" />
                        <span>{weakness}</span>
                      </motion.li>
                    ))
                  ) : (
                    <li className="text-red-300">
                      {percentage < 50 ? 'Necesitas reforzar conceptos básicos' : 'Sigue practicando para perfeccionar'}
                    </li>
                  )}
                </ul>
              </motion.div>
            </div>

            {/* Recommendations */}
            {results.recommendations && results.recommendations.length > 0 && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 1.2 }}
                className="bg-purple-900/20 rounded-xl p-6 border border-purple-500/30 mb-8"
              >
                <div className="flex items-center gap-2 mb-4">
                  <Brain className="w-6 h-6 text-purple-400" />
                  <h3 className="text-xl font-bold text-purple-400">Recomendaciones</h3>
                </div>
                <ul className="space-y-2">
                  {results.recommendations.map((rec, index) => (
                    <motion.li
                      key={index}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: 1.3 + index * 0.1 }}
                      className="flex items-start gap-2 text-purple-300"
                    >
                      <ChevronRight className="w-4 h-4 mt-0.5 flex-shrink-0" />
                      <span>{rec}</span>
                    </motion.li>
                  ))}
                </ul>
              </motion.div>
            )}

            {/* Action Buttons */}
            <div className="flex flex-col sm:flex-row gap-4">
              <motion.button
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 1.4 }}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={createStudyPlan}
                disabled={creatingPlan || planCreated}
                className={`
                  flex-1 py-4 rounded-xl font-bold text-lg
                  transition-all duration-300 flex items-center justify-center gap-3
                  ${planCreated 
                    ? 'bg-green-600 text-white'
                    : 'bg-gradient-to-r from-purple-600 to-blue-600 text-white hover:from-purple-700 hover:to-blue-700 shadow-lg shadow-purple-500/30'
                  }
                  ${creatingPlan ? 'opacity-75 cursor-not-allowed' : ''}
                `}
              >
                {planCreated ? (
                  <>
                    <CheckCircle className="w-6 h-6" />
                    Plan Creado - Redirigiendo...
                  </>
                ) : creatingPlan ? (
                  <>
                    <div className="animate-spin rounded-full h-6 w-6 border-t-2 border-white"></div>
                    Creando Plan Personalizado...
                  </>
                ) : (
                  <>
                    <BookOpen className="w-6 h-6" />
                    Crear Plan de Estudio Personalizado
                  </>
                )}
              </motion.button>

              <motion.button
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 1.5 }}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={() => setShowDetails(!showDetails)}
                className="px-8 py-4 bg-black/50 border border-purple-500/30 text-purple-300 rounded-xl font-bold text-lg hover:bg-purple-900/20 transition-all duration-300 flex items-center justify-center gap-2"
              >
                <BarChart3 className="w-6 h-6" />
                {showDetails ? 'Ocultar' : 'Ver'} Detalles
              </motion.button>
            </div>
          </div>
        </motion.div>

        {/* Detailed Analysis */}
        <AnimatePresence>
          {showDetails && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="max-w-4xl mx-auto"
            >
              <div className="bg-black/40 backdrop-blur-xl rounded-2xl border border-purple-500/30 p-8">
                <h3 className="text-2xl font-bold text-yellow-400 mb-6 flex items-center gap-3">
                  <Shield className="w-8 h-8" />
                  Análisis Detallado del Rendimiento
                </h3>
                
                <div className="grid md:grid-cols-3 gap-6">
                  <div className="bg-black/30 rounded-xl p-6 border border-purple-500/20 text-center">
                    <Award className="w-12 h-12 text-yellow-400 mx-auto mb-3" />
                    <p className="text-purple-300 mb-2">Rango Alcanzado</p>
                    <p className={`text-4xl font-bold bg-gradient-to-r ${rankInfo.color} text-transparent bg-clip-text`}>
                      {rankInfo.rank}
                    </p>
                  </div>

                  <div className="bg-black/30 rounded-xl p-6 border border-purple-500/20 text-center">
                    <Zap className="w-12 h-12 text-blue-400 mx-auto mb-3" />
                    <p className="text-purple-300 mb-2">Velocidad Promedio</p>
                    <p className="text-2xl font-bold text-white">
                      {results.time_spent && results.total_questions 
                        ? Math.round(results.time_spent / results.total_questions) + 's'
                        : 'N/A'
                      }
                    </p>
                    <p className="text-sm text-purple-400 mt-1">por pregunta</p>
                  </div>

                  <div className="bg-black/30 rounded-xl p-6 border border-purple-500/20 text-center">
                    <TrendingUp className="w-12 h-12 text-green-400 mx-auto mb-3" />
                    <p className="text-purple-300 mb-2">Nivel Recomendado</p>
                    <p className="text-2xl font-bold text-white">
                      {percentage >= 80 ? 'Avanzado' : percentage >= 60 ? 'Intermedio' : 'Básico'}
                    </p>
                  </div>
                </div>

                <div className="mt-6 p-4 bg-purple-900/20 rounded-xl border border-purple-500/30">
                  <p className="text-purple-300 text-center">
                    Basado en tu rendimiento, te recomendamos comenzar con un plan de estudio 
                    <span className="font-bold text-purple-400">
                      {percentage >= 80 ? ' avanzado' : percentage >= 60 ? ' intermedio' : ' básico'}
                    </span> para maximizar tu aprendizaje.
                  </p>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Navigation Buttons */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1.6 }}
          className="max-w-4xl mx-auto mt-8 flex justify-center gap-4"
        >
          <button
            onClick={() => router.push('/diagnostic-test')}
            className="px-6 py-3 bg-black/50 border border-purple-500/30 text-purple-300 rounded-lg font-medium hover:bg-purple-900/20 transition-all duration-300"
          >
            Hacer Otro Test
          </button>
          <button
            onClick={() => router.push('/')}
            className="px-6 py-3 bg-black/50 border border-purple-500/30 text-purple-300 rounded-lg font-medium hover:bg-purple-900/20 transition-all duration-300"
          >
            Ir al Inicio
          </button>
        </motion.div>
      </div>
    </div>
  );
}