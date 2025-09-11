'use client';

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  ChevronLeft, 
  ChevronRight, 
  X, 
  Clock, 
  Users, 
  Target,
  AlertTriangle,
  Brain,
  Lightbulb,
  Filter,
  Calendar,
  BarChart3,
  Eye,
  ZoomIn,
  RotateCcw,
  CheckCircle,
  XCircle
} from 'lucide-react';

interface WrongAnswer {
  id: string;
  questionId: string;
  subject: string;
  topic: string;
  difficulty: number;
  irtDifficulty: number;
  questionText: string;
  questionImage?: string;
  correctAnswer: string;
  selectedAnswer: string;
  distractors: {
    A: string;
    B: string;
    C: string;
    D: string;
  };
  timeSpent: number;
  averageTime: number;
  percentile: number;
  explanation: string;
  aiAnalysis: string;
  conceptsToReinforce: string[];
  date: string;
  wasReviewed: boolean;
}

export default function ErrorAnalysisCarousel() {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [showModal, setShowModal] = useState(false);
  const [selectedImage, setSelectedImage] = useState<string | null>(null);
  const [filters, setFilters] = useState({
    subject: 'all',
    difficulty: 'all',
    timeframe: '30d',
    reviewed: 'all'
  });
  const [wrongAnswers, setWrongAnswers] = useState<WrongAnswer[]>([]);
  const [loading, setLoading] = useState(true);

  // Simulated data
  useEffect(() => {
    const generateMockData = (): WrongAnswer[] => {
      const subjects = ['Matemáticas', 'Física', 'Química', 'Biología', 'Español'];
      const topics = {
        'Matemáticas': ['Álgebra', 'Geometría', 'Trigonometría', 'Cálculo'],
        'Física': ['Mecánica', 'Termodinámica', 'Electromagnetismo', 'Óptica'],
        'Química': ['Química Orgánica', 'Química Inorgánica', 'Fisicoquímica'],
        'Biología': ['Genética', 'Evolución', 'Ecología', 'Biología Molecular'],
        'Español': ['Comprensión Lectora', 'Gramática', 'Literatura', 'Ortografía']
      };

      return Array.from({ length: 15 }, (_, i) => {
        const subject = subjects[Math.floor(Math.random() * subjects.length)];
        const topicList = topics[subject as keyof typeof topics];
        const topic = topicList[Math.floor(Math.random() * topicList.length)];
        const difficulty = Math.random() * 3 - 1; // -1 to 2 range
        
        return {
          id: `error_${i + 1}`,
          questionId: `q_${1000 + i}`,
          subject,
          topic,
          difficulty: Math.random() * 5 + 1, // 1-5 scale
          irtDifficulty: difficulty,
          questionText: `Esta es una pregunta de ${topic} que presenta conceptos avanzados sobre ${subject.toLowerCase()}. La pregunta requiere análisis crítico y aplicación de múltiples conceptos.`,
          questionImage: Math.random() > 0.5 ? `/images/questions/q_${1000 + i}.png` : undefined,
          correctAnswer: 'C',
          selectedAnswer: ['A', 'B', 'D'][Math.floor(Math.random() * 3)],
          distractors: {
            A: 'Opción incorrecta que podría confundir por similitud conceptual',
            B: 'Opción incorrecta que incluye error común de cálculo',
            C: 'Opción correcta que requiere análisis completo del problema',
            D: 'Opción incorrecta por interpretación literal errónea'
          },
          timeSpent: Math.floor(Math.random() * 300 + 60), // 60-360 seconds
          averageTime: Math.floor(Math.random() * 180 + 120), // 120-300 seconds
          percentile: Math.floor(Math.random() * 100),
          explanation: `La respuesta correcta es C porque requiere la aplicación del concepto fundamental de ${topic}. El error común en esta pregunta surge de...`,
          aiAnalysis: `Tu error indica una dificultad con el concepto de ${topic}. Recomiendo revisar los fundamentos de este tema y practicar problemas similares.`,
          conceptsToReinforce: [
            `Fundamentos de ${topic}`,
            `Aplicación práctica en ${subject}`,
            'Estrategias de resolución'
          ],
          date: new Date(Date.now() - Math.random() * 30 * 24 * 60 * 60 * 1000).toISOString(),
          wasReviewed: Math.random() > 0.6
        };
      });
    };

    setTimeout(() => {
      setWrongAnswers(generateMockData());
      setLoading(false);
    }, 1000);
  }, []);

  const filteredAnswers = wrongAnswers.filter(answer => {
    if (filters.subject !== 'all' && answer.subject !== filters.subject) return false;
    if (filters.difficulty !== 'all') {
      const difficultyRange = filters.difficulty === 'easy' ? [1, 2] : 
                            filters.difficulty === 'medium' ? [2, 4] : [4, 5];
      if (answer.difficulty < difficultyRange[0] || answer.difficulty > difficultyRange[1]) return false;
    }
    if (filters.reviewed !== 'all') {
      if (filters.reviewed === 'reviewed' && !answer.wasReviewed) return false;
      if (filters.reviewed === 'pending' && answer.wasReviewed) return false;
    }
    return true;
  });

  const currentAnswer = filteredAnswers[currentIndex];

  const nextSlide = () => {
    setCurrentIndex((prev) => (prev + 1) % filteredAnswers.length);
  };

  const prevSlide = () => {
    setCurrentIndex((prev) => (prev - 1 + filteredAnswers.length) % filteredAnswers.length);
  };

  const getTimeComparison = (timeSpent: number, averageTime: number) => {
    const ratio = timeSpent / averageTime;
    if (ratio < 0.8) return { status: 'fast', color: 'text-green-400', text: 'Más rápido que el promedio' };
    if (ratio > 1.2) return { status: 'slow', color: 'text-red-400', text: 'Más lento que el promedio' };
    return { status: 'average', color: 'text-yellow-400', text: 'Tiempo promedio' };
  };

  const getDifficultyColor = (difficulty: number) => {
    if (difficulty <= -0.5) return 'bg-green-500';
    if (difficulty <= 0) return 'bg-yellow-500';
    if (difficulty <= 0.5) return 'bg-orange-500';
    return 'bg-red-500';
  };

  const getDifficultyLabel = (difficulty: number) => {
    if (difficulty <= -0.5) return 'Fácil';
    if (difficulty <= 0) return 'Medio-Fácil';
    if (difficulty <= 0.5) return 'Medio-Difícil';
    return 'Difícil';
  };

  if (loading) {
    return (
      <motion.div
        className="bg-gray-900/80 rounded-xl p-8 border border-purple-500/30 flex items-center justify-center"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
      >
        <div className="text-center">
          <motion.div
            className="w-12 h-12 border-4 border-purple-500/30 border-t-purple-500 rounded-full mx-auto mb-4"
            animate={{ rotate: 360 }}
            transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
          />
          <p className="text-gray-400">Cargando análisis de errores...</p>
        </div>
      </motion.div>
    );
  }

  if (filteredAnswers.length === 0) {
    return (
      <motion.div
        className="bg-gray-900/80 rounded-xl p-8 border border-purple-500/30 text-center"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
      >
        <CheckCircle className="w-16 h-16 text-green-400 mx-auto mb-4" />
        <h3 className="text-xl font-semibold text-white mb-2">¡Excelente trabajo!</h3>
        <p className="text-gray-400">No hay errores que revisar con los filtros seleccionados.</p>
      </motion.div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Filters */}
      <motion.div
        className="bg-gray-900/80 rounded-xl p-4 border border-purple-500/30"
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <div className="flex items-center gap-4 mb-4">
          <Filter className="w-5 h-5 text-purple-400" />
          <h3 className="text-lg font-semibold text-white">Filtros de Análisis</h3>
        </div>
        
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <label className="block text-sm text-gray-400 mb-2">Materia</label>
            <select
              value={filters.subject}
              onChange={(e) => setFilters(prev => ({ ...prev, subject: e.target.value }))}
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white text-sm"
            >
              <option value="all">Todas</option>
              <option value="Matemáticas">Matemáticas</option>
              <option value="Física">Física</option>
              <option value="Química">Química</option>
              <option value="Biología">Biología</option>
              <option value="Español">Español</option>
            </select>
          </div>
          
          <div>
            <label className="block text-sm text-gray-400 mb-2">Dificultad</label>
            <select
              value={filters.difficulty}
              onChange={(e) => setFilters(prev => ({ ...prev, difficulty: e.target.value }))}
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white text-sm"
            >
              <option value="all">Todas</option>
              <option value="easy">Fácil</option>
              <option value="medium">Intermedio</option>
              <option value="hard">Difícil</option>
            </select>
          </div>
          
          <div>
            <label className="block text-sm text-gray-400 mb-2">Período</label>
            <select
              value={filters.timeframe}
              onChange={(e) => setFilters(prev => ({ ...prev, timeframe: e.target.value }))}
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white text-sm"
            >
              <option value="7d">Últimos 7 días</option>
              <option value="30d">Últimos 30 días</option>
              <option value="90d">Últimos 90 días</option>
            </select>
          </div>
          
          <div>
            <label className="block text-sm text-gray-400 mb-2">Estado</label>
            <select
              value={filters.reviewed}
              onChange={(e) => setFilters(prev => ({ ...prev, reviewed: e.target.value }))}
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white text-sm"
            >
              <option value="all">Todos</option>
              <option value="reviewed">Revisados</option>
              <option value="pending">Pendientes</option>
            </select>
          </div>
        </div>
      </motion.div>

      {/* Carousel */}
      <motion.div
        className="bg-gray-900/80 rounded-xl border border-purple-500/30 overflow-hidden"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        {/* Header */}
        <div className="p-6 border-b border-gray-700/50">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-3">
                <AlertTriangle className="w-6 h-6 text-red-400" />
                <div>
                  <h3 className="text-xl font-semibold text-white">
                    Análisis de Errores
                  </h3>
                  <p className="text-sm text-gray-400">
                    {currentIndex + 1} de {filteredAnswers.length} errores
                  </p>
                </div>
              </div>
              
              {currentAnswer?.wasReviewed && (
                <div className="flex items-center gap-2 px-3 py-1 bg-green-500/20 rounded-full">
                  <CheckCircle className="w-4 h-4 text-green-400" />
                  <span className="text-green-400 text-sm font-semibold">Revisado</span>
                </div>
              )}
            </div>
            
            <div className="flex items-center gap-2">
              <button
                onClick={prevSlide}
                className="p-2 bg-gray-800 hover:bg-gray-700 rounded-lg transition-all"
                disabled={filteredAnswers.length <= 1}
              >
                <ChevronLeft className="w-5 h-5 text-gray-400" />
              </button>
              <button
                onClick={nextSlide}
                className="p-2 bg-gray-800 hover:bg-gray-700 rounded-lg transition-all"
                disabled={filteredAnswers.length <= 1}
              >
                <ChevronRight className="w-5 h-5 text-gray-400" />
              </button>
            </div>
          </div>
        </div>

        {/* Question Content */}
        <AnimatePresence mode="wait">
          {currentAnswer && (
            <motion.div
              key={currentAnswer.id}
              className="p-6"
              initial={{ opacity: 0, x: 50 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -50 }}
              transition={{ duration: 0.3 }}
            >
              {/* Question Info */}
              <div className="flex flex-wrap items-center gap-4 mb-6">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
                  <span className="text-sm text-gray-300">{currentAnswer.subject}</span>
                </div>
                <div className="flex items-center gap-2">
                  <Target className="w-4 h-4 text-gray-400" />
                  <span className="text-sm text-gray-300">{currentAnswer.topic}</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className={`w-3 h-3 rounded-full ${getDifficultyColor(currentAnswer.irtDifficulty)}`}></div>
                  <span className="text-sm text-gray-300">
                    {getDifficultyLabel(currentAnswer.irtDifficulty)} (θ = {currentAnswer.irtDifficulty.toFixed(2)})
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <Calendar className="w-4 h-4 text-gray-400" />
                  <span className="text-sm text-gray-300">
                    {new Date(currentAnswer.date).toLocaleDateString('es-ES')}
                  </span>
                </div>
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Question */}
                <div className="lg:col-span-2 space-y-4">
                  <div className="bg-gray-800/50 rounded-lg p-4">
                    <h4 className="font-semibold text-white mb-3">Pregunta</h4>
                    <p className="text-gray-300 mb-4">{currentAnswer.questionText}</p>
                    
                    {currentAnswer.questionImage && (
                      <div className="relative">
                        <img
                          src={currentAnswer.questionImage}
                          alt="Imagen de la pregunta"
                          className="w-full max-w-md rounded-lg cursor-pointer hover:opacity-80 transition-opacity"
                          onClick={() => {
                            setSelectedImage(currentAnswer.questionImage!);
                            setShowModal(true);
                          }}
                          onError={(e) => {
                            // Placeholder for missing images
                            e.currentTarget.src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMzAwIiBoZWlnaHQ9IjIwMCIgdmlld0JveD0iMCAwIDMwMCAyMDAiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PHJlY3Qgd2lkdGg9IjMwMCIgaGVpZ2h0PSIyMDAiIGZpbGw9IiM0QjVTNjMiLz48dGV4dCB4PSIxNTAiIHk9IjEwMCIgZm9udC1mYW1pbHk9IkFyaWFsIiBmb250LXNpemU9IjE0IiBmaWxsPSIjOUM5Q0FGIiB0ZXh0LWFuY2hvcj0ibWlkZGxlIiBkeT0iLjNlbSI+SW1hZ2VuIG5vIGRpc3BvbmlibGU8L3RleHQ+PC9zdmc+';
                          }}
                        />
                        <button
                          onClick={() => {
                            setSelectedImage(currentAnswer.questionImage!);
                            setShowModal(true);
                          }}
                          className="absolute top-2 right-2 p-2 bg-gray-900/80 rounded-lg hover:bg-gray-800 transition-all"
                        >
                          <ZoomIn className="w-4 h-4 text-white" />
                        </button>
                      </div>
                    )}
                  </div>

                  {/* Answer Options */}
                  <div className="bg-gray-800/50 rounded-lg p-4">
                    <h4 className="font-semibold text-white mb-3">Opciones de Respuesta</h4>
                    <div className="space-y-3">
                      {Object.entries(currentAnswer.distractors).map(([option, text]) => (
                        <div
                          key={option}
                          className={`p-3 rounded-lg border-2 transition-all ${
                            option === currentAnswer.correctAnswer
                              ? 'border-green-500 bg-green-500/20'
                              : option === currentAnswer.selectedAnswer
                              ? 'border-red-500 bg-red-500/20'
                              : 'border-gray-700 bg-gray-800/30'
                          }`}
                        >
                          <div className="flex items-start gap-3">
                            <div className={`w-6 h-6 rounded-full flex items-center justify-center text-sm font-bold ${
                              option === currentAnswer.correctAnswer
                                ? 'bg-green-500 text-white'
                                : option === currentAnswer.selectedAnswer
                                ? 'bg-red-500 text-white'
                                : 'bg-gray-700 text-gray-300'
                            }`}>
                              {option}
                            </div>
                            <div className="flex-1">
                              <p className="text-gray-300 text-sm">{text}</p>
                              {option === currentAnswer.correctAnswer && (
                                <div className="flex items-center gap-1 mt-1">
                                  <CheckCircle className="w-4 h-4 text-green-400" />
                                  <span className="text-green-400 text-xs font-semibold">Respuesta correcta</span>
                                </div>
                              )}
                              {option === currentAnswer.selectedAnswer && option !== currentAnswer.correctAnswer && (
                                <div className="flex items-center gap-1 mt-1">
                                  <XCircle className="w-4 h-4 text-red-400" />
                                  <span className="text-red-400 text-xs font-semibold">Tu selección</span>
                                </div>
                              )}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Analysis Sidebar */}
                <div className="space-y-4">
                  {/* Performance Stats */}
                  <div className="bg-gray-800/50 rounded-lg p-4">
                    <h4 className="font-semibold text-white mb-3 flex items-center gap-2">
                      <BarChart3 className="w-4 h-4 text-purple-400" />
                      Estadísticas
                    </h4>
                    
                    <div className="space-y-3">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <Clock className="w-4 h-4 text-gray-400" />
                          <span className="text-sm text-gray-400">Tu tiempo</span>
                        </div>
                        <span className="text-white font-semibold">
                          {Math.floor(currentAnswer.timeSpent / 60)}:{(currentAnswer.timeSpent % 60).toString().padStart(2, '0')}
                        </span>
                      </div>
                      
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <Users className="w-4 h-4 text-gray-400" />
                          <span className="text-sm text-gray-400">Promedio</span>
                        </div>
                        <span className="text-gray-300">
                          {Math.floor(currentAnswer.averageTime / 60)}:{(currentAnswer.averageTime % 60).toString().padStart(2, '0')}
                        </span>
                      </div>
                      
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-gray-400">Percentil</span>
                        <span className={`font-semibold ${getTimeComparison(currentAnswer.timeSpent, currentAnswer.averageTime).color}`}>
                          {currentAnswer.percentile}%
                        </span>
                      </div>
                      
                      <div className="pt-2 border-t border-gray-700">
                        <p className={`text-xs ${getTimeComparison(currentAnswer.timeSpent, currentAnswer.averageTime).color}`}>
                          {getTimeComparison(currentAnswer.timeSpent, currentAnswer.averageTime).text}
                        </p>
                      </div>
                    </div>
                  </div>

                  {/* AI Analysis */}
                  <div className="bg-purple-500/20 rounded-lg p-4 border border-purple-500/30">
                    <h4 className="font-semibold text-white mb-3 flex items-center gap-2">
                      <Brain className="w-4 h-4 text-purple-400" />
                      Análisis IA
                    </h4>
                    <p className="text-sm text-gray-300 mb-3">{currentAnswer.aiAnalysis}</p>
                    
                    <div className="space-y-2">
                      <h5 className="text-xs font-semibold text-purple-400 uppercase tracking-wide">
                        Conceptos a reforzar:
                      </h5>
                      {currentAnswer.conceptsToReinforce.map((concept, index) => (
                        <div key={index} className="flex items-center gap-2">
                          <div className="w-1.5 h-1.5 bg-purple-400 rounded-full"></div>
                          <span className="text-xs text-gray-300">{concept}</span>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Explanation */}
                  <div className="bg-blue-500/20 rounded-lg p-4 border border-blue-500/30">
                    <h4 className="font-semibold text-white mb-3 flex items-center gap-2">
                      <Lightbulb className="w-4 h-4 text-blue-400" />
                      Explicación
                    </h4>
                    <p className="text-sm text-gray-300">{currentAnswer.explanation}</p>
                  </div>

                  {/* Actions */}
                  <div className="space-y-2">
                    <button className="w-full py-2 px-4 bg-green-600 hover:bg-green-700 text-white rounded-lg text-sm font-semibold transition-all flex items-center justify-center gap-2">
                      <CheckCircle className="w-4 h-4" />
                      Marcar como Revisado
                    </button>
                    
                    <button className="w-full py-2 px-4 bg-purple-600 hover:bg-purple-700 text-white rounded-lg text-sm font-semibold transition-all flex items-center justify-center gap-2">
                      <RotateCcw className="w-4 h-4" />
                      Practicar Similar
                    </button>
                  </div>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Navigation Dots */}
        <div className="p-4 border-t border-gray-700/50">
          <div className="flex items-center justify-center gap-2">
            {filteredAnswers.slice(0, 10).map((_, index) => (
              <button
                key={index}
                onClick={() => setCurrentIndex(index)}
                className={`w-2 h-2 rounded-full transition-all ${
                  index === currentIndex ? 'bg-purple-500' : 'bg-gray-600 hover:bg-gray-500'
                }`}
              />
            ))}
            {filteredAnswers.length > 10 && (
              <span className="text-gray-500 text-sm">+{filteredAnswers.length - 10}</span>
            )}
          </div>
        </div>
      </motion.div>

      {/* Image Modal */}
      <AnimatePresence>
        {showModal && selectedImage && (
          <motion.div
            className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setShowModal(false)}
          >
            <motion.div
              className="relative max-w-4xl max-h-full"
              initial={{ scale: 0.8 }}
              animate={{ scale: 1 }}
              exit={{ scale: 0.8 }}
              onClick={(e) => e.stopPropagation()}
            >
              <button
                onClick={() => setShowModal(false)}
                className="absolute top-4 right-4 p-2 bg-gray-900/80 rounded-full hover:bg-gray-800 transition-all z-10"
              >
                <X className="w-6 h-6 text-white" />
              </button>
              <img
                src={selectedImage}
                alt="Imagen ampliada de la pregunta"
                className="max-w-full max-h-full rounded-lg"
              />
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}