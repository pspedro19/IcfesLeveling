'use client';

import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { 
  TrendingUp, 
  Target, 
  Users, 
  BarChart3, 
  Award,
  Brain,
  Zap,
  Eye,
  ChevronDown,
  ChevronUp,
  Info
} from 'lucide-react';

interface IRTMetricsPanelProps {
  theta: {
    mathematics: number;
    physics: number;
    chemistry: number;
    biology: number;
    spanish: number;
  };
  mastery: {
    mathematics: number;
    physics: number;
    chemistry: number;
    biology: number;
    spanish: number;
  };
  classRanking: number;
  nationalRanking: number;
}

interface SubjectDetails {
  name: string;
  theta: number;
  mastery: number;
  difficulty: number;
  discrimination: number;
  guessing: number;
  color: string;
  icon: string;
}

export default function IRTMetricsPanel({ 
  theta, 
  mastery, 
  classRanking, 
  nationalRanking 
}: IRTMetricsPanelProps) {
  const [expandedSubject, setExpandedSubject] = useState<string | null>(null);
  const [showTooltip, setShowTooltip] = useState<string | null>(null);

  const subjects: SubjectDetails[] = [
    {
      name: 'Matemáticas',
      theta: theta.mathematics,
      mastery: mastery.mathematics,
      difficulty: 0.8,
      discrimination: 1.2,
      guessing: 0.15,
      color: 'from-blue-500 to-blue-600',
      icon: '📐'
    },
    {
      name: 'Física',
      theta: theta.physics,
      mastery: mastery.physics,
      difficulty: 0.9,
      discrimination: 1.1,
      guessing: 0.18,
      color: 'from-purple-500 to-purple-600',
      icon: '⚛️'
    },
    {
      name: 'Química',
      theta: theta.chemistry,
      mastery: mastery.chemistry,
      difficulty: 0.85,
      discrimination: 1.15,
      guessing: 0.16,
      color: 'from-green-500 to-green-600',
      icon: '🧪'
    },
    {
      name: 'Biología',
      theta: theta.biology,
      mastery: mastery.biology,
      difficulty: 0.7,
      discrimination: 1.0,
      guessing: 0.20,
      color: 'from-emerald-500 to-emerald-600',
      icon: '🧬'
    },
    {
      name: 'Español',
      theta: theta.spanish,
      mastery: mastery.spanish,
      difficulty: 0.6,
      discrimination: 0.9,
      guessing: 0.22,
      color: 'from-orange-500 to-orange-600',
      icon: '📚'
    }
  ];

  const getThetaLevel = (theta: number) => {
    if (theta >= 2) return { level: 'Experto', color: 'text-yellow-400', bgColor: 'bg-yellow-500/20' };
    if (theta >= 1) return { level: 'Avanzado', color: 'text-green-400', bgColor: 'bg-green-500/20' };
    if (theta >= 0) return { level: 'Intermedio', color: 'text-blue-400', bgColor: 'bg-blue-500/20' };
    if (theta >= -1) return { level: 'Básico', color: 'text-orange-400', bgColor: 'bg-orange-500/20' };
    return { level: 'Inicial', color: 'text-red-400', bgColor: 'bg-red-500/20' };
  };

  const getClassAverage = () => {
    const total = Object.values(theta).reduce((sum, val) => sum + val, 0);
    return (total / Object.values(theta).length).toFixed(2);
  };

  const getNationalAverage = () => {
    return "0.15"; // Promedio nacional simulado
  };

  return (
    <div className="space-y-6">
      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Average Theta */}
        <motion.div
          className="bg-gray-900/80 rounded-xl p-6 border border-purple-500/30"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
        >
          <div className="flex items-center gap-3 mb-4">
            <div className="p-3 bg-purple-500/20 rounded-lg">
              <Brain className="w-6 h-6 text-purple-400" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-white">Theta Promedio</h3>
              <p className="text-sm text-gray-400">Habilidad general IRT</p>
            </div>
          </div>
          
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-2xl font-bold text-white">{getClassAverage()}</span>
              <div className={`px-3 py-1 rounded-full text-xs font-semibold ${
                getThetaLevel(parseFloat(getClassAverage())).bgColor
              } ${getThetaLevel(parseFloat(getClassAverage())).color}`}>
                {getThetaLevel(parseFloat(getClassAverage())).level}
              </div>
            </div>
            
            <div className="flex items-center gap-2 text-sm">
              <span className="text-gray-400">vs Clase:</span>
              <span className="text-green-400">+0.35</span>
              <span className="text-gray-400">vs Nacional:</span>
              <span className="text-green-400">+{(parseFloat(getClassAverage()) - parseFloat(getNationalAverage())).toFixed(2)}</span>
            </div>
          </div>
        </motion.div>

        {/* Class Ranking */}
        <motion.div
          className="bg-gray-900/80 rounded-xl p-6 border border-blue-500/30"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
        >
          <div className="flex items-center gap-3 mb-4">
            <div className="p-3 bg-blue-500/20 rounded-lg">
              <Users className="w-6 h-6 text-blue-400" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-white">Ranking de Clase</h3>
              <p className="text-sm text-gray-400">Posición actual</p>
            </div>
          </div>
          
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <span className="text-2xl font-bold text-white">#{classRanking}</span>
              <span className="text-sm text-gray-400">de 45</span>
            </div>
            
            <div className="flex items-center gap-2">
              <div className="flex-1 h-2 bg-gray-800 rounded-full">
                <div 
                  className="h-2 bg-gradient-to-r from-blue-500 to-cyan-500 rounded-full"
                  style={{ width: `${100 - (classRanking / 45 * 100)}%` }}
                />
              </div>
              <span className="text-sm text-blue-400">
                Top {Math.round((classRanking / 45) * 100)}%
              </span>
            </div>
          </div>
        </motion.div>

        {/* National Ranking */}
        <motion.div
          className="bg-gray-900/80 rounded-xl p-6 border border-yellow-500/30"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
        >
          <div className="flex items-center gap-3 mb-4">
            <div className="p-3 bg-yellow-500/20 rounded-lg">
              <Award className="w-6 h-6 text-yellow-400" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-white">Ranking Nacional</h3>
              <p className="text-sm text-gray-400">Entre todos los estudiantes</p>
            </div>
          </div>
          
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <span className="text-2xl font-bold text-white">#{nationalRanking.toLocaleString()}</span>
              <span className="text-sm text-gray-400">de 120,000</span>
            </div>
            
            <div className="flex items-center gap-2">
              <div className="flex-1 h-2 bg-gray-800 rounded-full">
                <div 
                  className="h-2 bg-gradient-to-r from-yellow-500 to-orange-500 rounded-full"
                  style={{ width: `${100 - (nationalRanking / 120000 * 100)}%` }}
                />
              </div>
              <span className="text-sm text-yellow-400">
                Top {((nationalRanking / 120000) * 100).toFixed(1)}%
              </span>
            </div>
          </div>
        </motion.div>
      </div>

      {/* Subject-wise IRT Analysis */}
      <motion.div
        className="bg-gray-900/80 rounded-xl p-6 border border-purple-500/30"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
      >
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-xl font-semibold text-white flex items-center gap-3">
            <BarChart3 className="w-6 h-6 text-purple-400" />
            Análisis IRT por Materia
          </h3>
          
          <div 
            className="relative"
            onMouseEnter={() => setShowTooltip('irt-explanation')}
            onMouseLeave={() => setShowTooltip(null)}
          >
            <Info className="w-5 h-5 text-gray-400 cursor-help" />
            
            {showTooltip === 'irt-explanation' && (
              <motion.div
                className="absolute right-0 top-8 w-80 p-4 bg-gray-800 rounded-lg shadow-xl border border-gray-700 z-10"
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
              >
                <h4 className="font-semibold text-white mb-2">Modelo IRT 3PL</h4>
                <p className="text-sm text-gray-300 mb-2">
                  El modelo de Teoría de Respuesta al Ítem evalúa:
                </p>
                <ul className="text-xs text-gray-400 space-y-1">
                  <li>• <strong>Theta (θ):</strong> Tu nivel de habilidad</li>
                  <li>• <strong>Dificultad:</strong> Qué tan difícil es el tema</li>
                  <li>• <strong>Discriminación:</strong> Qué tan bien diferencia habilidades</li>
                  <li>• <strong>Adivinanza:</strong> Probabilidad de respuesta correcta por azar</li>
                </ul>
              </motion.div>
            )}
          </div>
        </div>

        <div className="space-y-4">
          {subjects.map((subject, index) => {
            const thetaLevel = getThetaLevel(subject.theta);
            const isExpanded = expandedSubject === subject.name;
            
            return (
              <motion.div
                key={subject.name}
                className="border border-gray-700/50 rounded-lg overflow-hidden"
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.1 * index }}
              >
                <button
                  onClick={() => setExpandedSubject(isExpanded ? null : subject.name)}
                  className="w-full p-4 bg-gray-800/30 hover:bg-gray-800/50 transition-all"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <span className="text-2xl">{subject.icon}</span>
                      <div className="text-left">
                        <h4 className="text-lg font-semibold text-white">{subject.name}</h4>
                        <div className="flex items-center gap-4 text-sm">
                          <span className="text-gray-400">
                            θ = {subject.theta.toFixed(2)}
                          </span>
                          <div className={`px-2 py-1 rounded-full text-xs font-semibold ${thetaLevel.bgColor} ${thetaLevel.color}`}>
                            {thetaLevel.level}
                          </div>
                          <span className="text-gray-400">
                            Maestría: {subject.mastery}%
                          </span>
                        </div>
                      </div>
                    </div>
                    
                    <div className="flex items-center gap-3">
                      <div className="text-right">
                        <div className="w-32 h-2 bg-gray-700 rounded-full">
                          <motion.div
                            className={`h-2 bg-gradient-to-r ${subject.color} rounded-full`}
                            initial={{ width: 0 }}
                            animate={{ width: `${subject.mastery}%` }}
                            transition={{ duration: 1, delay: 0.5 + index * 0.1 }}
                          />
                        </div>
                        <span className="text-xs text-gray-400 mt-1">
                          {subject.mastery}% dominado
                        </span>
                      </div>
                      
                      {isExpanded ? (
                        <ChevronUp className="w-5 h-5 text-gray-400" />
                      ) : (
                        <ChevronDown className="w-5 h-5 text-gray-400" />
                      )}
                    </div>
                  </div>
                </button>

                {isExpanded && (
                  <motion.div
                    className="p-4 bg-gray-800/20"
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    exit={{ opacity: 0, height: 0 }}
                    transition={{ duration: 0.3 }}
                  >
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      {/* IRT Parameters */}
                      <div className="space-y-3">
                        <h5 className="font-semibold text-white flex items-center gap-2">
                          <Target className="w-4 h-4 text-purple-400" />
                          Parámetros IRT
                        </h5>
                        
                        <div className="space-y-2">
                          <div className="flex justify-between items-center">
                            <span className="text-sm text-gray-400">Dificultad (b)</span>
                            <span className="text-sm text-white font-mono">{subject.difficulty.toFixed(2)}</span>
                          </div>
                          <div className="flex justify-between items-center">
                            <span className="text-sm text-gray-400">Discriminación (a)</span>
                            <span className="text-sm text-white font-mono">{subject.discrimination.toFixed(2)}</span>
                          </div>
                          <div className="flex justify-between items-center">
                            <span className="text-sm text-gray-400">Adivinanza (c)</span>
                            <span className="text-sm text-white font-mono">{subject.guessing.toFixed(2)}</span>
                          </div>
                        </div>
                      </div>

                      {/* Performance Metrics */}
                      <div className="space-y-3">
                        <h5 className="font-semibold text-white flex items-center gap-2">
                          <TrendingUp className="w-4 h-4 text-green-400" />
                          Rendimiento
                        </h5>
                        
                        <div className="space-y-2">
                          <div className="flex justify-between items-center">
                            <span className="text-sm text-gray-400">Precisión esperada</span>
                            <span className="text-sm text-green-400 font-semibold">
                              {(Math.min(95, Math.max(5, 50 + (subject.theta * 20)))).toFixed(1)}%
                            </span>
                          </div>
                          <div className="flex justify-between items-center">
                            <span className="text-sm text-gray-400">Preguntas resueltas</span>
                            <span className="text-sm text-white">127</span>
                          </div>
                          <div className="flex justify-between items-center">
                            <span className="text-sm text-gray-400">Tiempo promedio</span>
                            <span className="text-sm text-white">2.3 min</span>
                          </div>
                        </div>
                      </div>

                      {/* Recommendations */}
                      <div className="space-y-3">
                        <h5 className="font-semibold text-white flex items-center gap-2">
                          <Zap className="w-4 h-4 text-yellow-400" />
                          Recomendación
                        </h5>
                        
                        <div className="text-sm text-gray-300">
                          {subject.theta >= 1.5 ? (
                            <p>¡Excelente! Mantén tu nivel practicando problemas desafiantes.</p>
                          ) : subject.theta >= 0.5 ? (
                            <p>Buen progreso. Enfócate en temas de dificultad media-alta.</p>
                          ) : subject.theta >= -0.5 ? (
                            <p>Refuerza conceptos básicos antes de avanzar a temas complejos.</p>
                          ) : (
                            <p>Dedica tiempo extra a repasar fundamentos de esta materia.</p>
                          )}
                        </div>
                        
                        <button className={`w-full py-2 px-4 bg-gradient-to-r ${subject.color} text-white rounded-lg text-sm font-semibold hover:scale-105 transition-transform`}>
                          Ver Plan de Estudio
                        </button>
                      </div>
                    </div>
                  </motion.div>
                )}
              </motion.div>
            );
          })}
        </div>
      </motion.div>
    </div>
  );
}