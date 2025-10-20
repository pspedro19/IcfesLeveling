'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Swords,
  Shield,
  Zap,
  Target,
  Award,
  Lock,
  Unlock,
  Clock,
  TrendingUp,
  Skull,
  Crown,
  Flame,
  Eye
} from 'lucide-react';
import DynamicSubjectIcon from '../../components/DynamicSubjectIcon';
import DiagnosticTestFlow from './test-flow';

export default function DiagnosticTest() {
  const router = useRouter();
  const [subjects, setSubjects] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedSubject, setSelectedSubject] = useState<any>(null);
  const [hoveredSubject, setHoveredSubject] = useState<string | null>(null);

  useEffect(() => {
    // Fetch subjects with IMAGE questions ONLY for testing
    import('../lib/dynamic-config').then(({ buildApiUrl }) =>
      fetch(buildApiUrl('/diagnostic-images-test/subjects-with-image-questions'))
    )
      .then(res => res.json())
      .then(data => {
        setSubjects(data || []);
        setLoading(false);
      })
      .catch(err => {
        console.error('Error fetching subjects:', err);
        setError('No se pudieron cargar las mazmorras desde el sistema');
        setLoading(false);
      });
  }, []);

  const startDiagnostic = (subject: any) => {
    // Check if subject is available
    if (!subject.is_available) {
      alert(`🔒 MAZMORRA SELLADA\n\n${subject.availability_message}`);
      return;
    }

    // Warn if limited questions
    if (subject.availability_status === 'limited') {
      const confirmStart = confirm(
        `⚠️ ADVERTENCIA DEL SISTEMA\n\n` +
        `La mazmorra "${subject.name}" tiene poder limitado.\n` +
        `${subject.availability_message}\n\n` +
        `¿Deseas entrar de todos modos, Hunter?`
      );
      if (!confirmStart) {
        return;
      }
    }

    setSelectedSubject(subject);
  };

  const handleTestComplete = (results: any) => {
    // Store results in sessionStorage for the results page
    const resultsData = {
      ...results,
      subject: selectedSubject?.name,
      subject_id: selectedSubject?.id,
      test_id: `diagnostic-${selectedSubject?.id}-${Date.now()}`,
      timestamp: new Date().toISOString()
    };

    sessionStorage.setItem('diagnostic_results', JSON.stringify(resultsData));

    // Navigate to results page
    router.push('/diagnostic-test/results');
  };

  // If a subject is selected, show the test interface
  if (selectedSubject) {
    return (
      <DiagnosticTestFlow
        subjectId={selectedSubject.id}
        subjectName={selectedSubject.name}
        onComplete={handleTestComplete}
      />
    );
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-game-abyss via-game-void to-black flex items-center justify-center relative overflow-hidden">
        {/* Epic Loading Background */}
        <div className="absolute inset-0">
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,_var(--tw-gradient-stops))] from-purple-900/20 via-transparent to-transparent animate-pulse"></div>
          {[...Array(50)].map((_, i) => (
            <motion.div
              key={i}
              className="absolute w-1 h-1 bg-purple-500/30 rounded-full"
              style={{
                left: `${Math.random() * 100}%`,
                top: `${Math.random() * 100}%`,
              }}
              animate={{
                scale: [0, 1.5, 0],
                opacity: [0, 1, 0],
              }}
              transition={{
                duration: 2 + Math.random() * 2,
                repeat: Infinity,
                delay: Math.random() * 2,
              }}
            />
          ))}
        </div>

        <div className="relative z-10 text-center">
          <motion.div
            animate={{
              rotate: 360,
              scale: [1, 1.2, 1]
            }}
            transition={{
              rotate: { duration: 2, repeat: Infinity, ease: "linear" },
              scale: { duration: 1.5, repeat: Infinity }
            }}
            className="w-24 h-24 mx-auto mb-6"
          >
            <div className="w-full h-full border-4 border-purple-500 border-t-transparent rounded-full relative">
              <div className="absolute inset-2 border-4 border-yellow-400 border-b-transparent rounded-full"></div>
            </div>
          </motion.div>
          <motion.h2
            className="text-3xl font-cinzel font-bold text-transparent bg-clip-text bg-gradient-to-r from-purple-400 via-yellow-400 to-purple-400 mb-2"
            animate={{ backgroundPosition: ['0%', '100%', '0%'] }}
            transition={{ duration: 3, repeat: Infinity }}
          >
            CARGANDO PORTAL DE MAZMORRAS
          </motion.h2>
          <p className="text-purple-300 font-orbitron">Conectando con el Sistema...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-red-950 via-black to-red-950 flex items-center justify-center">
        <motion.div
          initial={{ scale: 0.8, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          className="text-center bg-red-900/30 backdrop-blur-lg p-12 rounded-xl border-2 border-red-500"
        >
          <Skull className="w-20 h-20 text-red-500 mx-auto mb-4" />
          <h1 className="text-4xl font-cinzel font-bold text-red-400 mb-4">
            ⚠️ ERROR DEL SISTEMA
          </h1>
          <p className="text-red-300 text-lg">{error}</p>
          <p className="text-red-200 text-sm mt-4">El portal no pudo establecer conexión</p>
          <button
            onClick={() => window.location.reload()}
            className="mt-6 px-6 py-3 bg-red-600 hover:bg-red-700 text-white font-bold rounded-lg transition-all"
          >
            🔄 Reintentar Conexión
          </button>
        </motion.div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-game-abyss via-game-void to-black relative overflow-hidden">
      {/* Epic Background Effects */}
      <div className="fixed inset-0 z-0">
        {/* Animated Gradient Orbs */}
        <motion.div
          className="absolute top-1/4 left-1/4 w-96 h-96 bg-purple-600/20 rounded-full blur-3xl"
          animate={{
            scale: [1, 1.3, 1],
            x: [0, 50, 0],
            y: [0, -50, 0],
          }}
          transition={{ duration: 10, repeat: Infinity }}
        />
        <motion.div
          className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-yellow-600/20 rounded-full blur-3xl"
          animate={{
            scale: [1, 1.4, 1],
            x: [0, -50, 0],
            y: [0, 50, 0],
          }}
          transition={{ duration: 12, repeat: Infinity, delay: 1 }}
        />
        <motion.div
          className="absolute top-1/2 right-1/3 w-64 h-64 bg-blue-600/20 rounded-full blur-3xl"
          animate={{
            scale: [1, 1.2, 1],
            x: [0, 30, 0],
          }}
          transition={{ duration: 8, repeat: Infinity, delay: 2 }}
        />

        {/* Floating Particles - FIXED: Pre-calculate positions to avoid SSR mismatch */}
        {typeof window !== 'undefined' && [...Array(30)].map((_, i) => {
          const leftPos = Math.random() * 100;
          const topPos = Math.random() * 100;
          const duration = 3 + Math.random() * 3;
          const delay = Math.random() * 3;

          return (
            <motion.div
              key={i}
              className="absolute w-1 h-1 bg-purple-400/40 rounded-full"
              style={{
                left: `${leftPos}%`,
                top: `${topPos}%`,
              }}
              animate={{
                y: [0, -100, 0],
                opacity: [0, 1, 0],
              }}
              transition={{
                duration,
                repeat: Infinity,
                delay,
              }}
            />
          );
        })}
      </div>

      <div className="relative z-10 container mx-auto px-4 py-12">
        {/* Epic Header */}
        <motion.div
          initial={{ y: -50, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ duration: 0.8 }}
          className="text-center mb-12"
        >
          <motion.div
            className="inline-block mb-4"
            animate={{
              scale: [1, 1.05, 1],
              rotate: [0, 2, 0, -2, 0]
            }}
            transition={{ duration: 4, repeat: Infinity }}
          >
            <Crown className="w-20 h-20 text-yellow-400 mx-auto mb-2 drop-shadow-[0_0_15px_rgba(250,204,21,0.7)]" />
          </motion.div>

          <h1 className="text-6xl font-cinzel font-bold mb-4 text-transparent bg-clip-text bg-gradient-to-r from-yellow-400 via-yellow-200 to-yellow-400 drop-shadow-[0_0_30px_rgba(250,204,21,0.5)]">
            PORTAL DE MAZMORRAS ICFES
          </h1>

          <p className="text-2xl text-purple-300 font-orbitron mb-6">
            「 Solo los Hunters más valientes conquistan el conocimiento 」
          </p>

          <div className="flex flex-wrap justify-center gap-3 mb-6">
            <motion.span
              whileHover={{ scale: 1.05 }}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-full font-semibold bg-gradient-to-r from-purple-600 to-purple-800 text-purple-100 border border-purple-400 shadow-lg shadow-purple-500/50"
            >
              <Zap className="w-4 h-4" />
              Sistema Adaptativo IA
            </motion.span>
            <motion.span
              whileHover={{ scale: 1.05 }}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-full font-semibold bg-gradient-to-r from-yellow-600 to-orange-600 text-yellow-100 border border-yellow-400 shadow-lg shadow-yellow-500/50"
            >
              <Swords className="w-4 h-4" />
              Gamificación Épica
            </motion.span>
            <motion.span
              whileHover={{ scale: 1.05 }}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-full font-semibold bg-gradient-to-r from-blue-600 to-blue-800 text-blue-100 border border-blue-400 shadow-lg shadow-blue-500/50"
            >
              <Target className="w-4 h-4" />
              Análisis en Tiempo Real
            </motion.span>
          </div>

          {/* Rank Display */}
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ delay: 0.3, type: "spring" }}
            className="inline-block bg-black/50 backdrop-blur-lg border-2 border-yellow-400 rounded-lg px-8 py-4 shadow-[0_0_30px_rgba(250,204,21,0.3)]"
          >
            <p className="text-yellow-400 font-orbitron text-sm mb-1">TU RANGO ACTUAL</p>
            <p className="text-5xl font-cinzel font-bold text-transparent bg-clip-text bg-gradient-to-r from-gray-400 to-gray-200">
              E-RANK
            </p>
            <p className="text-purple-300 text-xs font-orbitron mt-1">「 Completa diagnósticos para subir de rango 」</p>
          </motion.div>
        </motion.div>

        {/* Main Content */}
        <motion.div
          initial={{ y: 50, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.4, duration: 0.8 }}
          className="bg-black/50 backdrop-blur-xl rounded-2xl border-2 border-purple-500/50 p-8 mb-12 shadow-[0_0_50px_rgba(168,85,247,0.3)]"
        >
          <div className="mb-8 text-center">
            <motion.div
              animate={{ rotate: [0, 360] }}
              transition={{ duration: 20, repeat: Infinity, ease: "linear" }}
              className="inline-block mb-4"
            >
              <Eye className="w-16 h-16 text-purple-400" />
            </motion.div>
            <h3 className="text-4xl font-cinzel font-bold text-yellow-400 mb-3 drop-shadow-[0_0_10px_rgba(250,204,21,0.5)]">
              ⚔️ SELECCIONA TU PRIMERA CONQUISTA
            </h3>
            <p className="text-xl text-purple-300 font-orbitron">
              Cada mazmorra pondrá a prueba tu poder en diferentes áreas del conocimiento
            </p>
            <div className="mt-4 bg-purple-900/30 border border-purple-500/30 rounded-lg px-4 py-2 inline-block">
              <p className="text-purple-200 text-sm font-orbitron">
                💡 <strong>TIP:</strong> El diagnóstico evaluará tus <strong className="text-yellow-400">fortalezas</strong> y <strong className="text-red-400">debilidades</strong> por tema
              </p>
            </div>
          </div>

          {/* Subjects Grid - Epic Dungeon Selection */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <AnimatePresence>
              {subjects.map((subject, index) => {
                const isUnavailable = !subject.is_available;
                const isLimited = subject.availability_status === 'limited';
                const isHovered = hoveredSubject === subject.id;

                return (
                  <motion.div
                    key={subject.id}
                    initial={{ opacity: 0, y: 50 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.1 }}
                    whileHover={{
                      scale: isUnavailable ? 1 : 1.05,
                      y: isUnavailable ? 0 : -10
                    }}
                    onHoverStart={() => setHoveredSubject(subject.id)}
                    onHoverEnd={() => setHoveredSubject(null)}
                    className={`relative group ${
                      isUnavailable
                        ? 'cursor-not-allowed'
                        : 'cursor-pointer'
                    }`}
                    onClick={() => !isUnavailable && startDiagnostic(subject)}
                  >
                    {/* Card */}
                    <div className={`
                      relative bg-gradient-to-br from-black/80 to-black/60 backdrop-blur-lg
                      rounded-xl border-2 p-6 transition-all duration-300
                      ${isUnavailable
                        ? 'border-gray-600/50 opacity-50 grayscale'
                        : isLimited
                        ? 'border-yellow-500/50 hover:border-yellow-400 shadow-[0_0_30px_rgba(251,191,36,0.3)]'
                        : 'border-purple-500/50 hover:border-yellow-400 shadow-[0_0_30px_rgba(168,85,247,0.3)]'
                      }
                      ${isHovered && !isUnavailable ? 'shadow-[0_0_50px_rgba(250,204,21,0.5)]' : ''}
                    `}>
                      {/* Lock Overlay for Unavailable */}
                      {isUnavailable && (
                        <div className="absolute inset-0 flex items-center justify-center bg-black/60 rounded-xl z-10">
                          <Lock className="w-16 h-16 text-gray-500" />
                        </div>
                      )}

                      {/* Animated Border Glow */}
                      {!isUnavailable && isHovered && (
                        <motion.div
                          className="absolute inset-0 rounded-xl"
                          style={{
                            background: 'linear-gradient(45deg, #fbbf24, #a855f7, #fbbf24)',
                            backgroundSize: '200% 200%',
                          }}
                          animate={{
                            backgroundPosition: ['0% 50%', '100% 50%', '0% 50%'],
                          }}
                          transition={{ duration: 3, repeat: Infinity }}
                        >
                          <div className="absolute inset-[2px] bg-black/90 rounded-xl"></div>
                        </motion.div>
                      )}

                      <div className="relative z-10">
                        {/* Dynamic Subject Icon with Aura */}
                        <motion.div
                          className="relative w-24 h-24 mx-auto mb-4"
                          animate={isHovered && !isUnavailable ? {
                            scale: [1, 1.1, 1],
                            rotate: [0, 5, 0, -5, 0]
                          } : {}}
                          transition={{ duration: 2, repeat: Infinity }}
                        >
                          {/* Aura Effect */}
                          {!isUnavailable && (
                            <motion.div
                              className="absolute inset-0 rounded-full blur-xl opacity-50"
                              style={{
                                backgroundColor: subject.display?.color_primary || subject.color || '#8B5CF6'
                              }}
                              animate={{
                                scale: [1, 1.3, 1],
                                opacity: [0.3, 0.6, 0.3]
                              }}
                              transition={{ duration: 2, repeat: Infinity }}
                            />
                          )}

                          <div
                            className="relative w-full h-full rounded-full flex items-center justify-center shadow-2xl border-2 border-white/20"
                            style={{
                              backgroundColor: subject.display?.color_primary || subject.color || '#8B5CF6',
                              boxShadow: `0 0 30px ${subject.display?.color_primary || subject.color || '#8B5CF6'}80`
                            }}
                          >
                            <DynamicSubjectIcon
                              subjectId={subject.id}
                              subjectName={subject.name}
                              size={56}
                              className="text-white drop-shadow-lg"
                            />
                          </div>
                        </motion.div>

                        {/* Subject Title */}
                        <h3 className="text-2xl font-cinzel font-bold text-yellow-400 mb-2 text-center drop-shadow-[0_0_10px_rgba(250,204,21,0.5)]">
                          {subject.name}
                        </h3>

                        {/* Dungeon Level */}
                        <div className="flex justify-center gap-2 mb-3">
                          {[...Array(5)].map((_, i) => (
                            <Flame
                              key={i}
                              className={`w-4 h-4 ${i < 3 ? 'text-orange-500' : 'text-gray-600'}`}
                              fill={i < 3 ? 'currentColor' : 'none'}
                            />
                          ))}
                        </div>

                        {/* Subject Description */}
                        <p className="text-purple-300 mb-4 text-sm text-center font-orbitron">
                          {subject.display?.description_short || subject.description || 'Conquista esta mazmorra'}
                        </p>

                        {/* Stats */}
                        <div className="space-y-2 text-sm mb-4 bg-black/30 rounded-lg p-3 border border-purple-500/20">
                          <div className="flex justify-between items-center">
                            <span className="text-gray-400 flex items-center gap-1">
                              <Shield className="w-3 h-3" />
                              Preguntas:
                            </span>
                            <span className="font-bold text-purple-300 font-orbitron">
                              {subject.available_for_test || subject.config?.total_questions || 20}
                            </span>
                          </div>
                          <div className="flex justify-between items-center">
                            <span className="text-gray-400 flex items-center gap-1">
                              <Clock className="w-3 h-3" />
                              Tiempo:
                            </span>
                            <span className="font-bold text-purple-300 font-orbitron">
                              {subject.config?.time_limit_minutes || 30} min
                            </span>
                          </div>
                          <div className="flex justify-between items-center">
                            <span className="text-gray-400 flex items-center gap-1">
                              <TrendingUp className="w-3 h-3" />
                              Disponibles:
                            </span>
                            <span className="font-bold text-yellow-300 font-orbitron">
                              {subject.image_question_count || 0}
                            </span>
                          </div>
                        </div>

                        {/* Status Badge */}
                        <div className="mb-4">
                          {isUnavailable ? (
                            <div className="bg-gradient-to-r from-red-900/50 to-gray-900/50 border-2 border-red-500/50 rounded-lg p-3 text-center">
                              <Lock className="w-6 h-6 text-red-400 mx-auto mb-1" />
                              <p className="text-red-300 text-sm font-bold font-orbitron">MAZMORRA SELLADA</p>
                              <p className="text-red-400 text-xs">{subject.availability_message}</p>
                            </div>
                          ) : isLimited ? (
                            <div className="bg-gradient-to-r from-yellow-900/50 to-orange-900/50 border-2 border-yellow-500/50 rounded-lg p-3 text-center">
                              <Unlock className="w-6 h-6 text-yellow-400 mx-auto mb-1" />
                              <p className="text-yellow-300 text-sm font-bold font-orbitron">PODER LIMITADO</p>
                              <p className="text-yellow-400 text-xs">{subject.availability_message}</p>
                            </div>
                          ) : (
                            <div className="bg-gradient-to-r from-green-900/50 to-emerald-900/50 border-2 border-green-500/50 rounded-lg p-3 text-center">
                              <Award className="w-6 h-6 text-green-400 mx-auto mb-1" />
                              <p className="text-green-300 text-sm font-bold font-orbitron">MAZMORRA ACTIVA</p>
                              <p className="text-green-400 text-xs">{subject.availability_message}</p>
                            </div>
                          )}
                        </div>

                        {/* Epic Enter Button */}
                        <motion.button
                          whileHover={!isUnavailable ? { scale: 1.05 } : {}}
                          whileTap={!isUnavailable ? { scale: 0.95 } : {}}
                          className={`
                            w-full font-cinzel font-bold text-lg py-4 px-6 rounded-xl
                            transition-all duration-300 border-2
                            ${isUnavailable
                              ? 'bg-gray-800 border-gray-600 text-gray-500 cursor-not-allowed'
                              : isLimited
                              ? 'bg-gradient-to-r from-yellow-600 via-orange-600 to-yellow-600 hover:from-yellow-500 hover:via-orange-500 hover:to-yellow-500 border-yellow-400 text-white shadow-[0_0_20px_rgba(251,191,36,0.5)] hover:shadow-[0_0_30px_rgba(251,191,36,0.7)]'
                              : 'bg-gradient-to-r from-purple-600 via-blue-600 to-purple-600 hover:from-purple-500 hover:via-blue-500 hover:to-purple-500 border-purple-400 text-white shadow-[0_0_20px_rgba(168,85,247,0.5)] hover:shadow-[0_0_30px_rgba(168,85,247,0.7)]'
                            }
                          `}
                          disabled={isUnavailable}
                        >
                          {isUnavailable ? (
                            <span className="flex items-center justify-center gap-2">
                              <Lock className="w-5 h-5" />
                              SELLADA
                            </span>
                          ) : isLimited ? (
                            <span className="flex items-center justify-center gap-2">
                              <Swords className="w-5 h-5" />
                              ENTRAR (Limitada)
                            </span>
                          ) : (
                            <span className="flex items-center justify-center gap-2">
                              <Swords className="w-5 h-5" />
                              ENTRAR A LA MAZMORRA
                            </span>
                          )}
                        </motion.button>
                      </div>
                    </div>
                  </motion.div>
                );
              })}
            </AnimatePresence>
          </div>
        </motion.div>

        {/* System Status - Epic Style */}
        <motion.div
          initial={{ y: 50, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.6, duration: 0.8 }}
          className="text-center bg-gradient-to-r from-blue-900/50 via-purple-900/50 to-blue-900/50 backdrop-blur-lg rounded-2xl p-8 border-2 border-blue-500/50 shadow-[0_0_30px_rgba(59,130,246,0.3)]"
        >
          <h2 className="text-blue-300 font-cinzel font-bold text-3xl mb-6 flex items-center justify-center gap-3">
            <Target className="w-8 h-8" />
            ESTADO DEL SISTEMA
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
            <motion.div
              whileHover={{ scale: 1.05 }}
              className="bg-gradient-to-br from-green-900/50 to-emerald-900/50 p-5 rounded-xl border-2 border-green-500/50"
            >
              <Award className="w-8 h-8 text-green-400 mx-auto mb-2" />
              <p className="text-green-300 font-orbitron font-semibold text-lg mb-1">Mazmorras Activas</p>
              <p className="text-green-100 text-3xl font-cinzel font-bold">
                {subjects.filter(s => s.availability_status === 'available').length}
              </p>
            </motion.div>
            <motion.div
              whileHover={{ scale: 1.05 }}
              className="bg-gradient-to-br from-yellow-900/50 to-orange-900/50 p-5 rounded-xl border-2 border-yellow-500/50"
            >
              <Flame className="w-8 h-8 text-yellow-400 mx-auto mb-2" />
              <p className="text-yellow-300 font-orbitron font-semibold text-lg mb-1">Poder Limitado</p>
              <p className="text-yellow-100 text-3xl font-cinzel font-bold">
                {subjects.filter(s => s.availability_status === 'limited').length}
              </p>
            </motion.div>
            <motion.div
              whileHover={{ scale: 1.05 }}
              className="bg-gradient-to-br from-blue-900/50 to-purple-900/50 p-5 rounded-xl border-2 border-blue-500/50"
            >
              <Zap className="w-8 h-8 text-blue-400 mx-auto mb-2" />
              <p className="text-blue-300 font-orbitron font-semibold text-lg mb-1">Preguntas Total</p>
              <p className="text-blue-100 text-3xl font-cinzel font-bold">
                {subjects.reduce((sum, s) => sum + (s.image_question_count || 0), 0)}
              </p>
            </motion.div>
          </div>
          <motion.p
            className="text-blue-200 text-base mt-6 font-orbitron"
            animate={{ opacity: [0.7, 1, 0.7] }}
            transition={{ duration: 2, repeat: Infinity }}
          >
            💎 Solo preguntas con contenido visual • Máximo 20 por mazmorra
          </motion.p>
        </motion.div>
      </div>
    </div>
  );
}
