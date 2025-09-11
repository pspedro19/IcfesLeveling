'use client';

import React, { useState, useEffect, useRef } from 'react';
import { motion } from 'framer-motion';
import {
  Filter,
  Download,
  ZoomIn,
  Calendar,
  BookOpen,
  TrendingDown,
  AlertCircle,
  Eye,
  X,
  Info,
  Camera,
  FileImage
} from 'lucide-react';

interface TopicPerformance {
  topicId: string;
  topicName: string;
  subjectId: string;
  subjectName: string;
  masteryLevel: number;
  questionsAttempted: number;
  questionsCorrect: number;
  avgResponseTime: number;
  difficultyProgression: number;
  lastPractice: string;
}

interface StudentHeatmapData {
  userId: string;
  username: string;
  avatarUrl?: string;
  level: number;
  rank: string;
  topics: TopicPerformance[];
}

interface HeatmapFilters {
  subject?: string;
  startDate?: string;
  endDate?: string;
  minDifficulty?: number;
  maxDifficulty?: number;
  performanceThreshold?: number;
}

interface StudentDetailModal {
  student: StudentHeatmapData;
  topic: TopicPerformance;
}

interface StudentWeaknessHeatmapProps {
  classId: string;
  className: string;
}

export default function StudentWeaknessHeatmap({ 
  classId, 
  className 
}: StudentWeaknessHeatmapProps) {
  const [heatmapData, setHeatmapData] = useState<StudentHeatmapData[]>([]);
  const [topics, setTopics] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState<HeatmapFilters>({});
  const [showFilters, setShowFilters] = useState(false);
  const [selectedCell, setSelectedCell] = useState<StudentDetailModal | null>(null);
  const [hoveredCell, setHoveredCell] = useState<{x: number, y: number, data: any} | null>(null);
  const heatmapRef = useRef<HTMLDivElement>(null);

  // Colores para el heatmap basados en performance
  const getPerformanceColor = (mastery: number): string => {
    if (mastery >= 75) return 'bg-green-500';
    if (mastery >= 60) return 'bg-yellow-500';
    if (mastery >= 45) return 'bg-orange-500';
    return 'bg-red-500';
  };

  const getPerformanceIntensity = (mastery: number): string => {
    const intensity = Math.min(Math.max(mastery / 100, 0.2), 1);
    if (mastery >= 75) return `bg-green-500 opacity-${Math.round(intensity * 100)}`;
    if (mastery >= 60) return `bg-yellow-500 opacity-${Math.round(intensity * 100)}`;
    if (mastery >= 45) return `bg-orange-500 opacity-${Math.round(intensity * 100)}`;
    return `bg-red-500 opacity-${Math.round(intensity * 100)}`;
  };

  const getPerformanceText = (mastery: number): string => {
    if (mastery >= 75) return 'Excelente';
    if (mastery >= 60) return 'Bueno';
    if (mastery >= 45) return 'Necesita mejorar';
    return 'Requiere atención';
  };

  // Cargar datos del heatmap
  const fetchHeatmapData = async () => {
    setLoading(true);
    setError(null);

    try {
      // Mock data - reemplazar con API real
      const mockTopics = [
        'Álgebra', 'Geometría', 'Estadística', 'Trigonometría', 'Cálculo',
        'Comprensión Lectora', 'Gramática', 'Literatura', 'Redacción',
        'Física', 'Química', 'Biología', 'Geología',
        'Historia', 'Geografía', 'Civismo', 'Economía'
      ];

      const mockStudents: StudentHeatmapData[] = Array.from({ length: 15 }, (_, i) => ({
        userId: `student-${i}`,
        username: `Estudiante ${i + 1}`,
        level: Math.floor(Math.random() * 50) + 1,
        rank: ['E', 'D', 'C', 'B', 'A', 'S'][Math.floor(Math.random() * 6)],
        topics: mockTopics.map(topic => ({
          topicId: `topic-${topic.toLowerCase().replace(/\s+/g, '-')}`,
          topicName: topic,
          subjectId: `subject-${Math.floor(Math.random() * 4)}`,
          subjectName: ['Matemáticas', 'Español', 'Ciencias', 'Sociales'][Math.floor(Math.random() * 4)],
          masteryLevel: Math.floor(Math.random() * 100),
          questionsAttempted: Math.floor(Math.random() * 50) + 10,
          questionsCorrect: Math.floor(Math.random() * 30) + 5,
          avgResponseTime: Math.floor(Math.random() * 10000) + 3000,
          difficultyProgression: Math.random() * 5 + 1,
          lastPractice: new Date(Date.now() - Math.random() * 30 * 24 * 60 * 60 * 1000).toISOString()
        }))
      }));

      setHeatmapData(mockStudents);
      setTopics(mockTopics);
    } catch (err) {
      setError('Error al cargar datos del heatmap');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHeatmapData();
  }, [classId, filters]);

  // Exportar heatmap como imagen PNG
  const exportHeatmapAsPNG = async () => {
    if (!heatmapRef.current) return;

    try {
      const html2canvas = await import('html2canvas');
      const canvas = await html2canvas.default(heatmapRef.current, {
        backgroundColor: '#111827',
        scale: 2, // High resolution
        useCORS: true,
        allowTaint: true
      });

      const link = document.createElement('a');
      link.download = `heatmap-${className}-${new Date().toISOString().split('T')[0]}.png`;
      link.href = canvas.toDataURL('image/png');
      link.click();
    } catch (error) {
      console.error('Error exporting heatmap:', error);
    }
  };

  // Filtrar datos según filtros activos
  const filteredData = heatmapData.filter(student => {
    if (!filters.subject) return true;
    return student.topics.some(topic => 
      topic.subjectName.toLowerCase().includes(filters.subject!.toLowerCase())
    );
  });

  const filteredTopics = topics.filter(topic => {
    if (!filters.subject) return true;
    const mockSubjects = ['Matemáticas', 'Español', 'Ciencias', 'Sociales'];
    const topicSubject = mockSubjects[Math.floor(Math.random() * mockSubjects.length)];
    return topicSubject.toLowerCase().includes(filters.subject!.toLowerCase());
  });

  // Componente de tooltip
  const HeatmapTooltip = ({ x, y, data }: { x: number, y: number, data: any }) => (
    <motion.div
      className="absolute z-50 bg-gray-900/95 border border-gray-700 rounded-lg p-3 pointer-events-none"
      style={{ left: x + 10, top: y - 10 }}
      initial={{ opacity: 0, scale: 0.8 }}
      animate={{ opacity: 1, scale: 1 }}
    >
      <div className="text-white font-semibold mb-1">{data.studentName}</div>
      <div className="text-gray-300 text-sm mb-2">{data.topicName}</div>
      <div className="space-y-1 text-xs">
        <div className="flex justify-between gap-4">
          <span className="text-gray-400">Mastery:</span>
          <span className={`font-semibold ${
            data.mastery >= 75 ? 'text-green-400' :
            data.mastery >= 60 ? 'text-yellow-400' :
            data.mastery >= 45 ? 'text-orange-400' :
            'text-red-400'
          }`}>
            {data.mastery.toFixed(1)}%
          </span>
        </div>
        <div className="flex justify-between gap-4">
          <span className="text-gray-400">Intentos:</span>
          <span className="text-white">{data.attempts}</span>
        </div>
        <div className="flex justify-between gap-4">
          <span className="text-gray-400">Precisión:</span>
          <span className="text-white">{data.accuracy}%</span>
        </div>
        <div className="text-gray-400 text-xs mt-2">
          {getPerformanceText(data.mastery)}
        </div>
      </div>
    </motion.div>
  );

  // Modal de detalles del estudiante
  const StudentDetailModal = ({ student, topic, onClose }: { 
    student: StudentHeatmapData, 
    topic: TopicPerformance, 
    onClose: () => void 
  }) => (
    <motion.div
      className="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      onClick={onClose}
    >
      <motion.div
        className="bg-gray-900 rounded-lg border border-gray-700 p-6 max-w-md w-full mx-4"
        initial={{ scale: 0.8, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.8, opacity: 0 }}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-white">Detalle del Estudiante</h3>
          <button
            onClick={onClose}
            className="p-1 hover:bg-gray-800 rounded"
          >
            <X className="w-5 h-5 text-gray-400" />
          </button>
        </div>
        
        <div className="space-y-4">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 bg-gradient-to-r from-purple-500 to-blue-500 rounded-full flex items-center justify-center">
              <span className="text-white font-bold text-lg">
                {student.username.charAt(0)}
              </span>
            </div>
            <div>
              <div className="text-white font-semibold">{student.username}</div>
              <div className="text-gray-400 text-sm">Nivel {student.level} • Rango {student.rank}</div>
            </div>
          </div>
          
          <div className="bg-gray-800/50 rounded-lg p-4">
            <h4 className="text-white font-medium mb-2">{topic.topicName}</h4>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-400">Mastery Level:</span>
                <span className={`font-semibold ${
                  topic.masteryLevel >= 75 ? 'text-green-400' :
                  topic.masteryLevel >= 60 ? 'text-yellow-400' :
                  topic.masteryLevel >= 45 ? 'text-orange-400' :
                  'text-red-400'
                }`}>
                  {topic.masteryLevel.toFixed(1)}%
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Preguntas intentadas:</span>
                <span className="text-white">{topic.questionsAttempted}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Preguntas correctas:</span>
                <span className="text-white">{topic.questionsCorrect}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Precisión:</span>
                <span className="text-white">
                  {((topic.questionsCorrect / topic.questionsAttempted) * 100).toFixed(1)}%
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Tiempo promedio:</span>
                <span className="text-white">{(topic.avgResponseTime / 1000).toFixed(1)}s</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Última práctica:</span>
                <span className="text-white">
                  {new Date(topic.lastPractice).toLocaleDateString()}
                </span>
              </div>
            </div>
          </div>
          
          <div className="bg-blue-900/20 border border-blue-500/30 rounded-lg p-3">
            <div className="flex items-center gap-2 mb-2">
              <Info className="w-4 h-4 text-blue-400" />
              <span className="text-blue-400 font-medium text-sm">Recomendaciones</span>
            </div>
            <ul className="text-xs text-gray-300 space-y-1">
              {topic.masteryLevel < 60 && (
                <li>• Programar sesión de refuerzo en este tema</li>
              )}
              {topic.avgResponseTime > 8000 && (
                <li>• Trabajar en velocidad de respuesta</li>
              )}
              {new Date(topic.lastPractice) < new Date(Date.now() - 7 * 24 * 60 * 60 * 1000) && (
                <li>• Motivar práctica más frecuente</li>
              )}
            </ul>
          </div>
        </div>
      </motion.div>
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
          onClick={fetchHeatmapData}
          className="mt-4 px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg"
        >
          Reintentar
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-white">Heatmap de Debilidades</h2>
          <p className="text-gray-400">Análisis de performance por estudiante y tema</p>
        </div>
        
        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowFilters(!showFilters)}
            className={`p-2 rounded-lg transition-all ${
              showFilters ? 'bg-purple-600' : 'bg-gray-800 hover:bg-gray-700'
            }`}
            title="Filtros"
          >
            <Filter className="w-5 h-5 text-gray-400" />
          </button>
          
          <button
            onClick={exportHeatmapAsPNG}
            className="p-2 bg-gray-800 hover:bg-gray-700 rounded-lg transition-all"
            title="Exportar como PNG"
          >
            <FileImage className="w-5 h-5 text-gray-400" />
          </button>
        </div>
      </div>

      {/* Filtros */}
      {showFilters && (
        <motion.div
          className="bg-gray-900/80 rounded-lg border border-gray-700/50 p-4"
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: 'auto' }}
          exit={{ opacity: 0, height: 0 }}
        >
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <label className="block text-sm text-gray-400 mb-2">Materia</label>
              <select
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white"
                value={filters.subject || ''}
                onChange={(e) => setFilters({ ...filters, subject: e.target.value || undefined })}
              >
                <option value="">Todas las materias</option>
                <option value="matemáticas">Matemáticas</option>
                <option value="español">Español</option>
                <option value="ciencias">Ciencias</option>
                <option value="sociales">Sociales</option>
              </select>
            </div>
            
            <div>
              <label className="block text-sm text-gray-400 mb-2">Fecha inicio</label>
              <input
                type="date"
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white"
                value={filters.startDate || ''}
                onChange={(e) => setFilters({ ...filters, startDate: e.target.value || undefined })}
              />
            </div>
            
            <div>
              <label className="block text-sm text-gray-400 mb-2">Fecha fin</label>
              <input
                type="date"
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white"
                value={filters.endDate || ''}
                onChange={(e) => setFilters({ ...filters, endDate: e.target.value || undefined })}
              />
            </div>
            
            <div>
              <label className="block text-sm text-gray-400 mb-2">Performance mínimo</label>
              <input
                type="number"
                min="0"
                max="100"
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white"
                value={filters.performanceThreshold || ''}
                onChange={(e) => setFilters({ 
                  ...filters, 
                  performanceThreshold: e.target.value ? parseInt(e.target.value) : undefined 
                })}
                placeholder="0-100%"
              />
            </div>
          </div>
        </motion.div>
      )}

      {/* Leyenda */}
      <div className="bg-gray-900/80 rounded-lg border border-gray-700/50 p-4">
        <h3 className="text-white font-semibold mb-3">Leyenda de Performance</h3>
        <div className="flex flex-wrap gap-4">
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-green-500 rounded"></div>
            <span className="text-gray-300 text-sm">Excelente (75%+)</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-yellow-500 rounded"></div>
            <span className="text-gray-300 text-sm">Bueno (60-74%)</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-orange-500 rounded"></div>
            <span className="text-gray-300 text-sm">Necesita mejorar (45-59%)</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-red-500 rounded"></div>
            <span className="text-gray-300 text-sm">Requiere atención (&lt;45%)</span>
          </div>
        </div>
      </div>

      {/* Heatmap */}
      <div 
        ref={heatmapRef}
        className="bg-gray-900/80 rounded-lg border border-gray-700/50 p-4 overflow-x-auto"
      >
        <div className="min-w-max">
          {/* Headers de temas */}
          <div className="flex mb-2">
            <div className="w-40 flex-shrink-0"></div>
            {filteredTopics.map((topic) => (
              <div
                key={topic}
                className="w-24 px-1 text-xs text-gray-400 text-center truncate"
                title={topic}
              >
                {topic}
              </div>
            ))}
          </div>
          
          {/* Filas de estudiantes */}
          <div className="space-y-1">
            {filteredData.map((student) => (
              <div key={student.userId} className="flex items-center">
                {/* Nombre del estudiante */}
                <div className="w-40 flex-shrink-0 pr-2">
                  <div className="flex items-center gap-2">
                    <div className="w-6 h-6 bg-gradient-to-r from-purple-500 to-blue-500 rounded-full flex items-center justify-center">
                      <span className="text-white text-xs font-bold">
                        {student.username.charAt(0)}
                      </span>
                    </div>
                    <span className="text-white text-sm truncate" title={student.username}>
                      {student.username}
                    </span>
                  </div>
                </div>
                
                {/* Celdas de performance */}
                {filteredTopics.map((topicName) => {
                  const topicData = student.topics.find(t => t.topicName === topicName);
                  const mastery = topicData?.masteryLevel || 0;
                  
                  return (
                    <div
                      key={`${student.userId}-${topicName}`}
                      className={`w-24 h-8 m-0.5 rounded cursor-pointer transition-all hover:scale-110 border border-gray-600 ${getPerformanceColor(mastery)}`}
                      style={{ 
                        opacity: Math.max(0.3, mastery / 100),
                        backgroundColor: mastery >= 75 ? '#10B981' :
                                      mastery >= 60 ? '#F59E0B' :
                                      mastery >= 45 ? '#F97316' :
                                      '#EF4444'
                      }}
                      onClick={() => topicData && setSelectedCell({ student, topic: topicData })}
                      onMouseEnter={(e) => {
                        if (topicData) {
                          const rect = e.currentTarget.getBoundingClientRect();
                          setHoveredCell({
                            x: rect.left,
                            y: rect.top,
                            data: {
                              studentName: student.username,
                              topicName: topicData.topicName,
                              mastery: topicData.masteryLevel,
                              attempts: topicData.questionsAttempted,
                              accuracy: Math.round((topicData.questionsCorrect / topicData.questionsAttempted) * 100)
                            }
                          });
                        }
                      }}
                      onMouseLeave={() => setHoveredCell(null)}
                    >
                      <div className="w-full h-full flex items-center justify-center">
                        <span className="text-white text-xs font-semibold">
                          {mastery > 0 ? Math.round(mastery) : '-'}
                        </span>
                      </div>
                    </div>
                  );
                })}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Tooltip */}
      {hoveredCell && (
        <HeatmapTooltip
          x={hoveredCell.x}
          y={hoveredCell.y}
          data={hoveredCell.data}
        />
      )}

      {/* Modal de detalles */}
      {selectedCell && (
        <StudentDetailModal
          student={selectedCell.student}
          topic={selectedCell.topic}
          onClose={() => setSelectedCell(null)}
        />
      )}
    </div>
  );
}