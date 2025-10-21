'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { motion } from 'framer-motion';
import { 
  Crown, 
  FileText, 
  Download, 
  BarChart3, 
  ArrowLeft,
  Award,
  Target,
  TrendingUp,
  Calendar,
  CheckCircle,
  Lock
} from 'lucide-react';
import MainNavigation from '../components/Navigation/MainNavigation';

interface ReportData {
  id: string;
  title: string;
  description: string;
  type: 'progress' | 'diagnostic' | 'competency' | 'recommendation';
  icon: any;
  status: 'available' | 'generating' | 'locked';
  xpReward: number;
  estimatedPages: number;
}

export default function SantuarioSabiduriaPage() {
  const router = useRouter();
  const [currentUser, setCurrentUser] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [generatingReport, setGeneratingReport] = useState<string | null>(null);

  useEffect(() => {
    // Load user data and check level requirement
    const userData = localStorage.getItem('currentUser') || localStorage.getItem('user');
    if (userData) {
      const user = JSON.parse(userData);
      setCurrentUser(user);
      
      if (user.level < 20) {
        alert('🔒 Acceso Denegado\n\nEl Santuario de la Sabiduría requiere Nivel 20.\nTu nivel actual: ' + user.level + '\n\n¡Continúa entrenando para acceder a los reportes avanzados!');
        router.push('/hub-central');
        return;
      }
    }
    setLoading(false);
  }, []);

  const availableReports: ReportData[] = [
    {
      id: 'progress',
      title: '📊 Reporte de Progreso Integral',
      description: 'Análisis completo de tu evolución, fortalezas y áreas de mejora con gráficos detallados.',
      type: 'progress',
      icon: BarChart3,
      status: 'available',
      xpReward: 500,
      estimatedPages: 12
    },
    {
      id: 'diagnostic',
      title: '🎯 Análisis Diagnóstico Avanzado',
      description: 'Evaluación profunda de tus competencias ICFES con recomendaciones específicas.',
      type: 'diagnostic',
      icon: Target,
      status: 'available',
      xpReward: 400,
      estimatedPages: 8
    },
    {
      id: 'competency',
      title: '🏆 Mapa de Competencias',
      description: 'Visualización detallada de tu dominio en cada competencia y componente ICFES.',
      type: 'competency',
      icon: Award,
      status: 'available',
      xpReward: 350,
      estimatedPages: 6
    },
    {
      id: 'recommendation',
      title: '🧠 Plan de Estudio Personalizado PDF',
      description: 'Tu plan de Claude AI convertido en un documento PDF descargable y imprimible.',
      type: 'recommendation',
      icon: FileText,
      status: 'available',
      xpReward: 300,
      estimatedPages: 10
    },
    {
      id: 'advanced',
      title: '👑 Reporte de Élite',
      description: 'Análisis avanzado con predicciones de rendimiento y estrategias de optimización.',
      type: 'progress',
      icon: Crown,
      status: currentUser?.rank && ['A', 'S', 'SS', 'SSS'].includes(currentUser.rank) ? 'available' : 'locked',
      xpReward: 750,
      estimatedPages: 15
    }
  ];

  const generateReport = async (report: ReportData) => {
    if (report.status === 'locked') {
      alert('🔒 Reporte Bloqueado\n\nEste reporte requiere Rango A o superior.\nTu rango actual: ' + (currentUser?.rank || 'E') + '\n\n¡Alcanza Rango A para desbloquear reportes de élite!');
      return;
    }
    
    setGeneratingReport(report.id);
    
    try {
      // Simulate report generation
      await new Promise(resolve => setTimeout(resolve, 3000));
      
      // Award XP
      alert(`🎉 ¡Reporte Generado!\n\n📄 ${report.title}\n📊 ${report.estimatedPages} páginas\n⚡ +${report.xpReward} XP ganados\n\n💾 El reporte se ha guardado en tu perfil.`);
      
      // In a real implementation, you would:
      // 1. Call API to generate PDF report
      // 2. Download the file
      // 3. Update user XP in database
      
    } catch (error) {
      console.error('Error generating report:', error);
      alert('❌ Error generando reporte. Intenta nuevamente.');
    } finally {
      setGeneratingReport(null);
    }
  };

  const getReportColor = (type: string) => {
    const colors = {
      'progress': 'from-blue-600 to-cyan-600',
      'diagnostic': 'from-green-600 to-emerald-600',
      'competency': 'from-purple-600 to-pink-600',
      'recommendation': 'from-orange-600 to-red-600'
    };
    return colors[type] || 'from-gray-600 to-slate-600';
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 text-white flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-gold-400 mx-auto mb-4"></div>
          <h2 className="text-2xl font-bold mb-2">🏛️ Accediendo al Santuario...</h2>
          <p className="text-purple-200">Preparando sabiduría ancestral</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 text-white">
      <MainNavigation currentUser={currentUser} />
      
      <div className="pt-20 lg:pt-24 pb-8">
        <div className="container mx-auto px-4">
          {/* Header */}
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-center mb-8"
          >
            <div className="flex items-center justify-center gap-4 mb-4">
              <button
                onClick={() => router.push('/hub-central')}
                className="bg-purple-600/50 hover:bg-purple-700/50 p-3 rounded-lg transition-all"
              >
                <ArrowLeft className="w-5 h-5" />
              </button>
              
              <h1 className="text-4xl font-bold bg-gradient-to-r from-gold-400 to-yellow-400 bg-clip-text text-transparent">
                🏛️ Santuario de la Sabiduría
              </h1>
            </div>
            
            <p className="text-xl text-purple-200 mb-4">
              Reportes PDF personalizados y consolidación de conocimiento
            </p>
            
            {/* Level Badge */}
            <div className="inline-flex items-center gap-2 bg-green-800/50 px-4 py-2 rounded-lg">
              <CheckCircle className="w-4 h-4 text-green-400" />
              <span className="text-green-200">Nivel 20+ Requerido - ¡Desbloqueado!</span>
            </div>
          </motion.div>

          {/* User Progress Summary */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="max-w-4xl mx-auto mb-8 bg-black/30 rounded-xl p-6 border border-gold-500/30"
          >
            <h2 className="text-2xl font-bold text-gold-400 mb-4 text-center">📈 Tu Sabiduría Acumulada</h2>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
              <div className="bg-blue-900/30 rounded-lg p-3">
                <div className="text-2xl font-bold text-blue-400">{currentUser?.level || 0}</div>
                <div className="text-blue-200 text-sm">Nivel Hunter</div>
              </div>
              <div className="bg-purple-900/30 rounded-lg p-3">
                <div className="text-2xl font-bold text-purple-400">{currentUser?.rank || 'E'}</div>
                <div className="text-purple-200 text-sm">Rango Actual</div>
              </div>
              <div className="bg-green-900/30 rounded-lg p-3">
                <div className="text-2xl font-bold text-green-400">{currentUser?.experience || 0}</div>
                <div className="text-green-200 text-sm">XP Total</div>
              </div>
              <div className="bg-gold-900/30 rounded-lg p-3">
                <div className="text-2xl font-bold text-gold-400">5</div>
                <div className="text-gold-200 text-sm">Reportes Disponibles</div>
              </div>
            </div>
          </motion.div>

          {/* Available Reports */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {availableReports.map((report, index) => {
              const isLocked = report.status === 'locked';
              const isGenerating = generatingReport === report.id;
              const Icon = report.icon;
              
              return (
                <motion.div
                  key={report.id}
                  initial={{ opacity: 0, y: 50 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.1 }}
                  className={`group cursor-pointer ${isLocked ? 'opacity-60' : ''}`}
                  onClick={() => !isLocked && !isGenerating && generateReport(report)}
                >
                  <div className={`bg-gradient-to-br ${getReportColor(report.type)}/20 rounded-xl p-6 border-2 ${
                    isLocked 
                      ? 'border-gray-600/30' 
                      : 'border-gold-500/30 hover:border-gold-500/50'
                  } transition-all transform ${isLocked ? '' : 'hover:scale-105'} backdrop-blur-sm relative overflow-hidden`}>
                    
                    {/* Lock Overlay */}
                    {isLocked && (
                      <div className="absolute inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center">
                        <div className="text-center">
                          <Lock className="w-8 h-8 text-gray-400 mx-auto mb-2" />
                          <div className="text-white font-bold">Rango A+ Requerido</div>
                        </div>
                      </div>
                    )}
                    
                    {/* Loading Overlay */}
                    {isGenerating && (
                      <div className="absolute inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center">
                        <div className="text-center">
                          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gold-400 mx-auto mb-2"></div>
                          <div className="text-white font-bold">Generando...</div>
                        </div>
                      </div>
                    )}
                    
                    <div className="relative z-10">
                      {/* Icon */}
                      <div className={`w-16 h-16 rounded-full bg-gradient-to-r ${getReportColor(report.type)} flex items-center justify-center mb-4 mx-auto shadow-lg`}>
                        <Icon className="w-8 h-8 text-white" />
                      </div>
                      
                      {/* Title */}
                      <h3 className="text-xl font-bold text-center mb-2 text-white">
                        {report.title}
                      </h3>
                      
                      {/* Description */}
                      <p className="text-center text-sm mb-4 text-purple-100 leading-relaxed">
                        {report.description}
                      </p>
                      
                      {/* Stats */}
                      <div className="flex justify-center gap-4 text-xs text-purple-200 mb-4">
                        <div className="flex items-center gap-1">
                          <FileText className="w-3 h-3" />
                          {report.estimatedPages} páginas
                        </div>
                        <div className="flex items-center gap-1">
                          <Award className="w-3 h-3" />
                          +{report.xpReward} XP
                        </div>
                      </div>
                      
                      {/* Action Button */}
                      <div className="text-center">
                        {isLocked ? (
                          <button className="bg-gray-700 px-6 py-3 rounded-lg font-bold text-gray-400 cursor-not-allowed w-full">
                            🔒 Rango A+ Requerido
                          </button>
                        ) : (
                          <button className={`bg-gradient-to-r ${getReportColor(report.type)} hover:shadow-lg px-6 py-3 rounded-lg font-bold text-white transition-all transform hover:scale-105 w-full`}>
                            📄 Generar Reporte
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                </motion.div>
              );
            })}
          </div>

          {/* Instructions */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.6 }}
            className="mt-8 max-w-4xl mx-auto bg-black/30 rounded-xl p-6 border border-gold-500/30"
          >
            <h2 className="text-xl font-bold text-gold-400 mb-4 text-center">📜 Sabiduría del Santuario</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h3 className="font-bold text-white mb-2">🎯 Cómo Funciona</h3>
                <ul className="text-sm text-purple-200 space-y-1">
                  <li>• Selecciona el tipo de reporte que necesitas</li>
                  <li>• El sistema genera un PDF personalizado</li>
                  <li>• Descarga y guarda tu progreso</li>
                  <li>• Gana XP por cada reporte generado</li>
                </ul>
              </div>
              <div>
                <h3 className="font-bold text-white mb-2">📊 Contenido de Reportes</h3>
                <ul className="text-sm text-gold-200 space-y-1">
                  <li>• Análisis de fortalezas y debilidades</li>
                  <li>• Gráficos de progreso temporal</li>
                  <li>• Recomendaciones personalizadas</li>
                  <li>• Comparación con estándares ICFES</li>
                </ul>
              </div>
            </div>
          </motion.div>

          {/* Back to Hub */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.8 }}
            className="mt-8 text-center"
          >
            <button
              onClick={() => router.push('/hub-central')}
              className="bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 px-6 py-3 rounded-lg font-semibold transition-all transform hover:scale-105 flex items-center gap-2 mx-auto"
            >
              <ArrowLeft className="w-5 h-5" />
              Volver al Hub Central
            </button>
          </motion.div>
        </div>
      </div>
    </div>
  );
}


