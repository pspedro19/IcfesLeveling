'use client';

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  AlertCircle,
  TrendingUp,
  TrendingDown,
  Eye,
  ZoomIn,
  Lightbulb,
  Target,
  Users,
  BarChart3,
  PieChart,
  BookOpen,
  Brain,
  Zap,
  CheckCircle,
  XCircle,
  ArrowRight,
  Info
} from 'lucide-react';

interface DistractorData {
  questionId: string;
  questionText: string;
  questionImage?: string;
  correctAnswer: string;
  subject: string;
  topic: string;
  difficulty: number;
  distractors: {
    option: string;
    text: string;
    selectionCount: number;
    selectionPercentage: number;
    avgStudentLevel: number;
    errorPattern: string;
    insight: string;
  }[];
  totalResponses: number;
  correctPercentage: number;
  avgResponseTime: number;
}

interface Intervention {
  id: string;
  type: 'individual' | 'group' | 'topic_review';
  title: string;
  description: string;
  targetStudents: string[];
  relatedTopics: string[];
  suggestedActivities: string[];
  estimatedTime: number;
  priority: 'low' | 'medium' | 'high' | 'critical';
  effectiveness: number; // 0-1
  status: 'planned' | 'active' | 'completed';
}

interface DistractorAnalysisProps {
  classId: string;
  className: string;
}

export default function DistractorAnalysis({ 
  classId, 
  className 
}: DistractorAnalysisProps) {
  const [topDistractors, setTopDistractors] = useState<DistractorData[]>([]);
  const [interventions, setInterventions] = useState<Intervention[]>([]);
  const [selectedQuestion, setSelectedQuestion] = useState<DistractorData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'distractors' | 'interventions' | 'insights'>('distractors');

  // Cargar datos de distractores
  const fetchDistractorData = async () => {
    setLoading(true);
    setError(null);

    try {
      // Mock data - reemplazar con API real
      const mockDistractors: DistractorData[] = [
        {
          questionId: 'q1',
          questionText: '¿Cuál es el resultado de 2x + 5 = 13?',
          subject: 'Matemáticas',
          topic: 'Álgebra Lineal',
          difficulty: 3,
          correctAnswer: 'B',
          distractors: [
            {
              option: 'A',
              text: 'x = 3',
              selectionCount: 8,
              selectionPercentage: 28.6,
              avgStudentLevel: 15.2,
              errorPattern: 'Error de operación básica',
              insight: 'Estudiantes confunden resta con suma en despeje'
            },
            {
              option: 'B',
              text: 'x = 4',
              selectionCount: 15,
              selectionPercentage: 53.6,
              avgStudentLevel: 25.8,
              errorPattern: 'Respuesta correcta',
              insight: 'Más de la mitad domina el despeje básico'
            },
            {
              option: 'C',
              text: 'x = 9',
              selectionCount: 3,
              selectionPercentage: 10.7,
              avgStudentLevel: 12.1,
              errorPattern: 'No realiza operación de despeje',
              insight: 'Pocos estudiantes suman directamente sin despejar'
            },
            {
              option: 'D',
              text: 'x = 18',
              selectionCount: 2,
              selectionPercentage: 7.1,
              avgStudentLevel: 8.5,
              errorPattern: 'Multiplica en lugar de dividir',
              insight: 'Confusión conceptual sobre operaciones inversas'
            }
          ],
          totalResponses: 28,
          correctPercentage: 53.6,
          avgResponseTime: 12500
        },
        {
          questionId: 'q2',
          questionText: 'En el texto "El sol brillaba intensamente", la palabra "intensamente" es:',
          subject: 'Español',
          topic: 'Análisis Morfológico',
          difficulty: 2,
          correctAnswer: 'C',
          distractors: [
            {
              option: 'A',
              text: 'Un adjetivo',
              selectionCount: 12,
              selectionPercentage: 42.9,
              avgStudentLevel: 18.3,
              errorPattern: 'Confunde adverbio con adjetivo',
              insight: 'Necesidad de reforzar diferencias entre clases de palabras'
            },
            {
              option: 'B',
              text: 'Un sustantivo',
              selectionCount: 2,
              selectionPercentage: 7.1,
              avgStudentLevel: 10.2,
              errorPattern: 'Desconocimiento básico de morfología',
              insight: 'Falta conceptos fundamentales de gramática'
            },
            {
              option: 'C',
              text: 'Un adverbio',
              selectionCount: 11,
              selectionPercentage: 39.3,
              avgStudentLevel: 28.7,
              errorPattern: 'Respuesta correcta',
              insight: 'Nivel aceptable pero mejorable en morfología'
            },
            {
              option: 'D',
              text: 'Un verbo',
              selectionCount: 3,
              selectionPercentage: 10.7,
              avgStudentLevel: 8.9,
              errorPattern: 'Confusión total de categorías',
              insight: 'Requiere revisión completa de clases de palabras'
            }
          ],
          totalResponses: 28,
          correctPercentage: 39.3,
          avgResponseTime: 15200
        }
      ];

      const mockInterventions: Intervention[] = [
        {
          id: 'int1',
          type: 'group',
          title: 'Refuerzo de Álgebra Básica',
          description: 'Sesión grupal para reforzar operaciones de despeje y conceptos de álgebra lineal',
          targetStudents: ['student-1', 'student-3', 'student-5'],
          relatedTopics: ['Álgebra Lineal', 'Operaciones Básicas'],
          suggestedActivities: [
            'Ejercicios guiados de despeje paso a paso',
            'Juegos interactivos de operaciones inversas',
            'Práctica con manipulativos algebraicos'
          ],
          estimatedTime: 45,
          priority: 'high',
          effectiveness: 0.78,
          status: 'planned'
        },
        {
          id: 'int2',
          type: 'individual',
          title: 'Tutoría de Morfología',
          description: 'Sesión individual para estudiante con dificultades en clasificación de palabras',
          targetStudents: ['student-7'],
          relatedTopics: ['Análisis Morfológico', 'Clases de Palabras'],
          suggestedActivities: [
            'Mapa conceptual de clases de palabras',
            'Ejercicios de identificación interactiva',
            'Creación de oraciones por categorías'
          ],
          estimatedTime: 30,
          priority: 'medium',
          effectiveness: 0.85,
          status: 'active'
        }
      ];

      setTopDistractors(mockDistractors);
      setInterventions(mockInterventions);
    } catch (err) {
      setError('Error al cargar análisis de distractores');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDistractorData();
  }, [classId]);

  const getPriorityColor = (priority: string) => {
    const colors = {
      low: 'text-green-400 bg-green-500/20',
      medium: 'text-yellow-400 bg-yellow-500/20',
      high: 'text-orange-400 bg-orange-500/20',
      critical: 'text-red-400 bg-red-500/20'
    };
    return colors[priority as keyof typeof colors] || colors.low;
  };

  const generateAutomaticInsights = (distractorData: DistractorData[]) => {
    const insights = [];
    
    for (const question of distractorData) {
      const topDistractor = question.distractors
        .filter(d => d.option !== question.correctAnswer)
        .sort((a, b) => b.selectionPercentage - a.selectionPercentage)[0];
      
      if (topDistractor && topDistractor.selectionPercentage > 30) {
        insights.push({
          type: 'high_distractor',
          message: `En "${question.topic}", el ${topDistractor.selectionPercentage.toFixed(1)}% de estudiantes elige la opción incorrecta "${topDistractor.text}". Patrón: ${topDistractor.errorPattern}`,
          priority: topDistractor.selectionPercentage > 40 ? 'high' : 'medium',
          question: question.questionText
        });
      }
      
      if (question.correctPercentage < 50) {
        insights.push({
          type: 'low_success',
          message: `La pregunta sobre "${question.topic}" tiene solo ${question.correctPercentage.toFixed(1)}% de respuestas correctas. Requiere revisión del material.`,
          priority: 'high',
          question: question.questionText
        });
      }
    }
    
    return insights;
  };

  const renderDistractorCard = (question: DistractorData) => (
    <motion.div
      key={question.questionId}
      className="bg-gray-900/80 rounded-lg border border-gray-700/50 p-6"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
    >
      <div className="flex justify-between items-start mb-4">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-sm text-gray-400">{question.subject}</span>
            <span className="text-gray-600">•</span>
            <span className="text-sm text-purple-400">{question.topic}</span>
            <div className={`px-2 py-1 rounded text-xs ${
              question.difficulty <= 2 ? 'bg-green-500/20 text-green-400' :
              question.difficulty <= 4 ? 'bg-yellow-500/20 text-yellow-400' :
              'bg-red-500/20 text-red-400'
            }`}>
              Dificultad {question.difficulty}/5
            </div>
          </div>
          <p className="text-white font-medium mb-2">{question.questionText}</p>
          <div className="flex items-center gap-4 text-sm">
            <span className="text-gray-400">
              {question.totalResponses} respuestas
            </span>
            <span className={`${
              question.correctPercentage >= 70 ? 'text-green-400' :
              question.correctPercentage >= 50 ? 'text-yellow-400' :
              'text-red-400'
            }`}>
              {question.correctPercentage.toFixed(1)}% correctas
            </span>
            <span className="text-gray-400">
              ⏱️ {(question.avgResponseTime / 1000).toFixed(1)}s promedio
            </span>
          </div>
        </div>
        
        <button
          onClick={() => setSelectedQuestion(question)}
          className="p-2 bg-gray-800 hover:bg-gray-700 rounded-lg transition-all"
          title="Ver detalles"
        >
          <ZoomIn className="w-5 h-5 text-gray-400" />
        </button>
      </div>
      
      <div className="space-y-2">
        <h4 className="text-white font-medium text-sm mb-2">Análisis de Distractores:</h4>
        {question.distractors
          .sort((a, b) => b.selectionPercentage - a.selectionPercentage)
          .map((distractor) => (
            <div 
              key={distractor.option}
              className={`p-3 rounded-lg border ${
                distractor.option === question.correctAnswer
                  ? 'border-green-500/50 bg-green-500/10'
                  : 'border-gray-700/50 bg-gray-800/30'
              }`}
            >
              <div className="flex justify-between items-start mb-2">
                <div className="flex items-center gap-2">
                  <span className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${
                    distractor.option === question.correctAnswer
                      ? 'bg-green-500 text-white'
                      : 'bg-gray-600 text-gray-300'
                  }`}>
                    {distractor.option}
                  </span>
                  <span className="text-white text-sm">{distractor.text}</span>
                  {distractor.option === question.correctAnswer && (
                    <CheckCircle className="w-4 h-4 text-green-400" />
                  )}
                </div>
                <div className="text-right">
                  <div className={`font-semibold ${
                    distractor.option === question.correctAnswer
                      ? 'text-green-400'
                      : distractor.selectionPercentage > 20
                        ? 'text-red-400'
                        : 'text-gray-400'
                  }`}>
                    {distractor.selectionPercentage.toFixed(1)}%
                  </div>
                  <div className="text-xs text-gray-500">
                    {distractor.selectionCount} estudiantes
                  </div>
                </div>
              </div>
              
              {distractor.option !== question.correctAnswer && distractor.selectionPercentage > 10 && (
                <div className="mt-2 p-2 bg-orange-500/10 rounded border border-orange-500/30">
                  <div className="flex items-start gap-2">
                    <AlertCircle className="w-4 h-4 text-orange-400 mt-0.5" />
                    <div className="text-xs">
                      <div className="text-orange-400 font-medium">Patrón de error:</div>
                      <div className="text-gray-300">{distractor.errorPattern}</div>
                      <div className="text-orange-300 mt-1">{distractor.insight}</div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          ))}
      </div>
    </motion.div>
  );

  const renderInterventionCard = (intervention: Intervention) => (
    <motion.div
      key={intervention.id}
      className="bg-gray-900/80 rounded-lg border border-gray-700/50 p-6"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
    >
      <div className="flex justify-between items-start mb-4">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-2">
            <div className={`px-2 py-1 rounded text-xs font-semibold ${getPriorityColor(intervention.priority)}`}>
              {intervention.priority.toUpperCase()}
            </div>
            <div className={`px-2 py-1 rounded text-xs ${
              intervention.status === 'completed' ? 'bg-green-500/20 text-green-400' :
              intervention.status === 'active' ? 'bg-blue-500/20 text-blue-400' :
              'bg-gray-500/20 text-gray-400'
            }`}>
              {intervention.status === 'completed' ? 'Completado' :
               intervention.status === 'active' ? 'Activo' :
               'Planeado'}
            </div>
            <div className="text-xs text-purple-400">
              {intervention.type === 'individual' ? '👤 Individual' :
               intervention.type === 'group' ? '👥 Grupal' :
               '📖 Revisión de tema'}
            </div>
          </div>
          
          <h3 className="text-white font-semibold mb-2">{intervention.title}</h3>
          <p className="text-gray-300 text-sm mb-3">{intervention.description}</p>
          
          <div className="flex items-center gap-4 text-xs text-gray-400 mb-3">
            <span>⏱️ {intervention.estimatedTime} min</span>
            <span>👥 {intervention.targetStudents.length} estudiantes</span>
            <span className="text-green-400">
              📈 {(intervention.effectiveness * 100).toFixed(0)}% efectividad
            </span>
          </div>
          
          <div className="space-y-2">
            <div>
              <span className="text-gray-400 text-xs">Temas relacionados:</span>
              <div className="flex flex-wrap gap-1 mt-1">
                {intervention.relatedTopics.map((topic, index) => (
                  <span 
                    key={index}
                    className="px-2 py-1 bg-purple-500/20 text-purple-300 text-xs rounded"
                  >
                    {topic}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <div className="border-t border-gray-700 pt-4">
        <h4 className="text-white text-sm font-medium mb-2">Actividades sugeridas:</h4>
        <ul className="space-y-1">
          {intervention.suggestedActivities.map((activity, index) => (
            <li key={index} className="flex items-start gap-2 text-sm text-gray-300">
              <ArrowRight className="w-3 h-3 text-gray-500 mt-1 flex-shrink-0" />
              <span>{activity}</span>
            </li>
          ))}
        </ul>
      </div>
    </motion.div>
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-400"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-900/20 border border-red-500/50 rounded-lg p-6 text-center">
        <p className="text-red-400">{error}</p>
        <button
          onClick={fetchDistractorData}
          className="mt-4 px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg"
        >
          Reintentar
        </button>
      </div>
    );
  }

  const automaticInsights = generateAutomaticInsights(topDistractors);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-white">Análisis de Distractores</h2>
          <p className="text-gray-400">Patrones de error comunes e intervenciones pedagógicas</p>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex space-x-1 bg-gray-900/80 p-1 rounded-lg">
        {[
          { id: 'distractors', label: 'Top Distractores', icon: AlertCircle },
          { id: 'interventions', label: 'Intervenciones', icon: Target },
          { id: 'insights', label: 'Insights IA', icon: Brain }
        ].map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            onClick={() => setActiveTab(id as any)}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
              activeTab === id
                ? 'bg-purple-600 text-white'
                : 'text-gray-400 hover:text-white hover:bg-gray-800'
            }`}
          >
            <Icon className="w-4 h-4" />
            {label}
          </button>
        ))}
      </div>

      {/* Content */}
      <AnimatePresence mode="wait">
        {activeTab === 'distractors' && (
          <motion.div
            key="distractors"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            className="space-y-6"
          >
            {topDistractors.map(renderDistractorCard)}
          </motion.div>
        )}

        {activeTab === 'interventions' && (
          <motion.div
            key="interventions"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            className="space-y-6"
          >
            {interventions.map(renderInterventionCard)}
          </motion.div>
        )}

        {activeTab === 'insights' && (
          <motion.div
            key="insights"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            className="space-y-6"
          >
            <div className="bg-gray-900/80 rounded-lg border border-gray-700/50 p-6">
              <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                <Brain className="w-5 h-5 text-purple-400" />
                Insights Automáticos
              </h3>
              
              <div className="space-y-4">
                {automaticInsights.map((insight, index) => (
                  <div 
                    key={index}
                    className={`p-4 rounded-lg border ${
                      insight.priority === 'high' 
                        ? 'border-red-500/50 bg-red-500/10'
                        : insight.priority === 'medium'
                          ? 'border-yellow-500/50 bg-yellow-500/10'
                          : 'border-green-500/50 bg-green-500/10'
                    }`}
                  >
                    <div className="flex items-start gap-3">
                      <div className={`p-2 rounded-full ${
                        insight.priority === 'high' 
                          ? 'bg-red-500/20 text-red-400'
                          : insight.priority === 'medium'
                            ? 'bg-yellow-500/20 text-yellow-400'
                            : 'bg-green-500/20 text-green-400'
                      }`}>
                        {insight.type === 'high_distractor' ? <AlertCircle className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
                      </div>
                      <div className="flex-1">
                        <p className="text-white text-sm">{insight.message}</p>
                        <p className="text-gray-400 text-xs mt-1">Pregunta: {insight.question}</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
              
              <div className="mt-6 p-4 bg-blue-500/10 border border-blue-500/30 rounded-lg">
                <div className="flex items-center gap-2 mb-2">
                  <Lightbulb className="w-5 h-5 text-blue-400" />
                  <span className="text-blue-400 font-medium">Recomendaciones Generales</span>
                </div>
                <ul className="text-sm text-gray-300 space-y-1">
                  <li>• Enfocarse en los distractores con mayor selección (>30%)</li>
                  <li>• Crear intervenciones grupales para patrones comunes</li>
                  <li>• Revisar material didáctico en temas con baja success rate</li>
                  <li>• Implementar ejercicios específicos para errores recurrentes</li>
                </ul>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Question Detail Modal */}
      {selectedQuestion && (
        <motion.div
          className="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={() => setSelectedQuestion(null)}
        >
          <motion.div
            className="bg-gray-900 rounded-lg border border-gray-700 p-6 max-w-2xl w-full mx-4 max-h-[80vh] overflow-y-auto"
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.8, opacity: 0 }}
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex justify-between items-start mb-4">
              <h3 className="text-lg font-semibold text-white">Análisis Detallado</h3>
              <button
                onClick={() => setSelectedQuestion(null)}
                className="text-gray-400 hover:text-white"
              >
                ✕
              </button>
            </div>
            
            <div className="space-y-4">
              <div>
                <p className="text-white font-medium">{selectedQuestion.questionText}</p>
                <div className="flex items-center gap-4 mt-2 text-sm text-gray-400">
                  <span>{selectedQuestion.subject} • {selectedQuestion.topic}</span>
                  <span>Dificultad: {selectedQuestion.difficulty}/5</span>
                </div>
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-gray-800/50 p-3 rounded">
                  <div className="text-gray-400 text-sm">Total Respuestas</div>
                  <div className="text-white font-bold text-xl">{selectedQuestion.totalResponses}</div>
                </div>
                <div className="bg-gray-800/50 p-3 rounded">
                  <div className="text-gray-400 text-sm">Correctas</div>
                  <div className="text-green-400 font-bold text-xl">{selectedQuestion.correctPercentage.toFixed(1)}%</div>
                </div>
              </div>
              
              <div>
                <h4 className="text-white font-medium mb-3">Distribución de Respuestas</h4>
                <div className="space-y-2">
                  {selectedQuestion.distractors.map((distractor) => (
                    <div key={distractor.option} className="flex items-center gap-3">
                      <span className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${
                        distractor.option === selectedQuestion.correctAnswer
                          ? 'bg-green-500 text-white'
                          : 'bg-gray-600 text-gray-300'
                      }`}>
                        {distractor.option}
                      </span>
                      <div className="flex-1">
                        <div className="flex justify-between">
                          <span className="text-gray-300">{distractor.text}</span>
                          <span className="text-white font-medium">{distractor.selectionPercentage.toFixed(1)}%</span>
                        </div>
                        <div className="w-full bg-gray-700 rounded-full h-2 mt-1">
                          <div 
                            className={`h-2 rounded-full ${
                              distractor.option === selectedQuestion.correctAnswer
                                ? 'bg-green-500'
                                : 'bg-red-500'
                            }`}
                            style={{ width: `${distractor.selectionPercentage}%` }}
                          />
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </motion.div>
        </motion.div>
      )}
    </div>
  );
}