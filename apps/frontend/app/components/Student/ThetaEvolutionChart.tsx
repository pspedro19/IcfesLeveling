'use client';

import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { 
  TrendingUp, 
  TrendingDown, 
  BarChart3, 
  Calendar,
  Filter,
  Eye,
  Zap,
  Target
} from 'lucide-react';

interface ThetaPoint {
  date: string;
  mathematics: number;
  physics: number;
  chemistry: number;
  biology: number;
  spanish: number;
  overall: number;
}

interface ThetaEvolutionChartProps {
  timeFilter: '7d' | '30d' | '90d';
}

export default function ThetaEvolutionChart({ timeFilter }: ThetaEvolutionChartProps) {
  const [selectedSubject, setSelectedSubject] = useState<string>('overall');
  const [chartMode, setChartMode] = useState<'line' | 'comparison'>('line');
  const [data, setData] = useState<ThetaPoint[]>([]);

  // Simulated data generation
  useEffect(() => {
    const generateData = () => {
      const days = timeFilter === '7d' ? 7 : timeFilter === '30d' ? 30 : 90;
      const points: ThetaPoint[] = [];
      
      for (let i = days; i >= 0; i--) {
        const date = new Date();
        date.setDate(date.getDate() - i);
        
        // Simulate theta evolution with some randomness and trend
        const baseProgress = (days - i) / days * 0.5;
        const randomFactor = (Math.random() - 0.5) * 0.3;
        
        points.push({
          date: date.toISOString().split('T')[0],
          mathematics: 0.2 + baseProgress + randomFactor + Math.sin(i * 0.1) * 0.1,
          physics: 0.1 + baseProgress + randomFactor + Math.cos(i * 0.15) * 0.1,
          chemistry: 0.15 + baseProgress + randomFactor + Math.sin(i * 0.12) * 0.1,
          biology: 0.25 + baseProgress + randomFactor + Math.cos(i * 0.08) * 0.1,
          spanish: 0.3 + baseProgress + randomFactor + Math.sin(i * 0.2) * 0.1,
          overall: 0.2 + baseProgress + randomFactor
        });
      }
      
      setData(points);
    };

    generateData();
  }, [timeFilter]);

  const subjects = [
    { key: 'overall', name: 'Promedio General', color: '#8B5CF6', icon: '📊' },
    { key: 'mathematics', name: 'Matemáticas', color: '#3B82F6', icon: '📐' },
    { key: 'physics', name: 'Física', color: '#8B5CF6', icon: '⚛️' },
    { key: 'chemistry', name: 'Química', color: '#10B981', icon: '🧪' },
    { key: 'biology', name: 'Biología', color: '#059669', icon: '🧬' },
    { key: 'spanish', name: 'Español', color: '#F59E0B', icon: '📚' }
  ];

  const getSelectedSubjectData = () => {
    if (!data.length) return [];
    return data.map(point => ({
      date: point.date,
      value: point[selectedSubject as keyof ThetaPoint] as number
    }));
  };

  const getCurrentSubject = () => {
    return subjects.find(s => s.key === selectedSubject) || subjects[0];
  };

  const calculateTrend = () => {
    const subjectData = getSelectedSubjectData();
    if (subjectData.length < 2) return { value: 0, isPositive: true };
    
    const first = subjectData[0].value;
    const last = subjectData[subjectData.length - 1].value;
    const change = ((last - first) / Math.abs(first)) * 100;
    
    return {
      value: Math.abs(change),
      isPositive: change >= 0
    };
  };

  const getMaxValue = () => {
    const subjectData = getSelectedSubjectData();
    return Math.max(...subjectData.map(d => d.value));
  };

  const getMinValue = () => {
    const subjectData = getSelectedSubjectData();
    return Math.min(...subjectData.map(d => d.value));
  };

  const renderLineChart = () => {
    const subjectData = getSelectedSubjectData();
    const currentSubject = getCurrentSubject();
    
    if (!subjectData.length) return null;

    const maxValue = Math.max(...subjectData.map(d => d.value));
    const minValue = Math.min(...subjectData.map(d => d.value));
    const range = maxValue - minValue || 1;
    
    const chartHeight = 200;
    const chartWidth = 600;
    const padding = 40;

    return (
      <div className="relative">
        <svg 
          viewBox={`0 0 ${chartWidth} ${chartHeight + padding * 2}`} 
          className="w-full h-64"
        >
          {/* Grid lines */}
          {[0, 0.25, 0.5, 0.75, 1].map((ratio, i) => (
            <g key={i}>
              <line
                x1={padding}
                y1={padding + (chartHeight * ratio)}
                x2={chartWidth - padding}
                y2={padding + (chartHeight * ratio)}
                stroke="#374151"
                strokeWidth="1"
                strokeDasharray="2,2"
                opacity="0.5"
              />
              <text
                x={padding - 10}
                y={padding + (chartHeight * ratio) + 5}
                fill="#9CA3AF"
                fontSize="12"
                textAnchor="end"
              >
                {(maxValue - (range * ratio)).toFixed(1)}
              </text>
            </g>
          ))}

          {/* Data line */}
          <motion.path
            d={`M ${subjectData.map((point, i) => {
              const x = padding + (i * (chartWidth - padding * 2)) / (subjectData.length - 1);
              const y = padding + ((maxValue - point.value) / range) * chartHeight;
              return `${i === 0 ? 'M' : 'L'} ${x} ${y}`;
            }).join(' ')}`}
            stroke={currentSubject.color}
            strokeWidth="3"
            fill="none"
            strokeLinecap="round"
            strokeLinejoin="round"
            initial={{ pathLength: 0 }}
            animate={{ pathLength: 1 }}
            transition={{ duration: 1.5, ease: 'easeInOut' }}
          />

          {/* Data points */}
          {subjectData.map((point, i) => {
            const x = padding + (i * (chartWidth - padding * 2)) / (subjectData.length - 1);
            const y = padding + ((maxValue - point.value) / range) * chartHeight;
            
            return (
              <motion.circle
                key={i}
                cx={x}
                cy={y}
                r="4"
                fill={currentSubject.color}
                stroke="white"
                strokeWidth="2"
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{ delay: i * 0.1, duration: 0.3 }}
                style={{ filter: 'drop-shadow(0 2px 4px rgba(0,0,0,0.3))' }}
              />
            );
          })}

          {/* Area fill */}
          <motion.path
            d={`M ${subjectData.map((point, i) => {
              const x = padding + (i * (chartWidth - padding * 2)) / (subjectData.length - 1);
              const y = padding + ((maxValue - point.value) / range) * chartHeight;
              return `${i === 0 ? 'M' : 'L'} ${x} ${y}`;
            }).join(' ')} L ${chartWidth - padding} ${padding + chartHeight} L ${padding} ${padding + chartHeight} Z`}
            fill={`url(#gradient-${selectedSubject})`}
            initial={{ opacity: 0 }}
            animate={{ opacity: 0.2 }}
            transition={{ duration: 1, delay: 0.5 }}
          />

          {/* Gradient definition */}
          <defs>
            <linearGradient id={`gradient-${selectedSubject}`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={currentSubject.color} stopOpacity="0.3" />
              <stop offset="100%" stopColor={currentSubject.color} stopOpacity="0" />
            </linearGradient>
          </defs>
        </svg>

        {/* Date labels */}
        <div className="flex justify-between text-xs text-gray-400 px-10 mt-2">
          {subjectData.filter((_, i) => i % Math.ceil(subjectData.length / 5) === 0).map((point, i) => (
            <span key={i}>
              {new Date(point.date).toLocaleDateString('es-ES', { 
                month: 'short', 
                day: 'numeric' 
              })}
            </span>
          ))}
        </div>
      </div>
    );
  };

  const renderComparisonChart = () => {
    if (!data.length) return null;

    const latestData = data[data.length - 1];
    const subjectsToCompare = subjects.filter(s => s.key !== 'overall');

    return (
      <div className="space-y-4">
        {subjectsToCompare.map((subject, index) => {
          const value = latestData[subject.key as keyof ThetaPoint] as number;
          const maxPossible = 3; // Theoretical max theta
          const percentage = Math.min(100, (value + 2) / 4 * 100); // Normalize to 0-100%
          
          return (
            <motion.div
              key={subject.key}
              className="space-y-2"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.1 }}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <span className="text-lg">{subject.icon}</span>
                  <span className="text-gray-300 font-medium">{subject.name}</span>
                </div>
                <div className="text-right">
                  <span className="text-white font-bold">θ = {value.toFixed(2)}</span>
                  <div className="text-xs text-gray-400">
                    {percentage.toFixed(0)}% del máximo
                  </div>
                </div>
              </div>
              
              <div className="relative">
                <div className="w-full h-3 bg-gray-800 rounded-full overflow-hidden">
                  <motion.div
                    className="h-3 rounded-full"
                    style={{ 
                      background: `linear-gradient(90deg, ${subject.color}CC, ${subject.color})`,
                      width: `${percentage}%`
                    }}
                    initial={{ width: 0 }}
                    animate={{ width: `${percentage}%` }}
                    transition={{ duration: 1, delay: index * 0.1 }}
                  />
                </div>
                
                {/* Benchmark lines */}
                <div className="absolute top-0 w-full h-3 flex justify-between">
                  {[25, 50, 75].map(benchmark => (
                    <div
                      key={benchmark}
                      className="w-0.5 h-3 bg-gray-600"
                      style={{ marginLeft: `${benchmark}%` }}
                    />
                  ))}
                </div>
              </div>
            </motion.div>
          );
        })}
      </div>
    );
  };

  const trend = calculateTrend();
  const currentSubject = getCurrentSubject();

  return (
    <motion.div
      className="bg-gray-900/80 rounded-xl p-6 border border-purple-500/30"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      {/* Header */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4 mb-6">
        <div>
          <h3 className="text-xl font-semibold text-white flex items-center gap-3">
            <BarChart3 className="w-6 h-6 text-purple-400" />
            Evolución Temporal de Theta
          </h3>
          <p className="text-gray-400 text-sm mt-1">
            Análisis de tu desarrollo académico durante los últimos {
              timeFilter === '7d' ? '7 días' : 
              timeFilter === '30d' ? '30 días' : 
              '90 días'
            }
          </p>
        </div>

        <div className="flex items-center gap-3">
          {/* Chart Mode Toggle */}
          <div className="flex items-center gap-1 bg-gray-800 rounded-lg p-1">
            <button
              onClick={() => setChartMode('line')}
              className={`px-3 py-2 rounded-lg text-sm font-semibold transition-all ${
                chartMode === 'line'
                  ? 'bg-purple-600 text-white'
                  : 'text-gray-400 hover:text-white'
              }`}
            >
              <TrendingUp className="w-4 h-4" />
            </button>
            <button
              onClick={() => setChartMode('comparison')}
              className={`px-3 py-2 rounded-lg text-sm font-semibold transition-all ${
                chartMode === 'comparison'
                  ? 'bg-purple-600 text-white'
                  : 'text-gray-400 hover:text-white'
              }`}
            >
              <BarChart3 className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Subject Selector (for line chart) */}
      {chartMode === 'line' && (
        <div className="mb-6">
          <div className="flex flex-wrap gap-2">
            {subjects.map((subject) => (
              <button
                key={subject.key}
                onClick={() => setSelectedSubject(subject.key)}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-semibold transition-all ${
                  selectedSubject === subject.key
                    ? 'text-white shadow-lg'
                    : 'text-gray-400 hover:text-white bg-gray-800/50'
                }`}
                style={{
                  backgroundColor: selectedSubject === subject.key ? subject.color : undefined
                }}
              >
                <span>{subject.icon}</span>
                <span className="hidden sm:inline">{subject.name}</span>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Stats Row */}
      {chartMode === 'line' && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <div className="bg-gray-800/50 rounded-lg p-4">
            <div className="flex items-center gap-2 mb-2">
              <TrendingUp className={`w-4 h-4 ${trend.isPositive ? 'text-green-400' : 'text-red-400'}`} />
              <span className="text-sm text-gray-400">Tendencia</span>
            </div>
            <div className={`text-lg font-bold ${trend.isPositive ? 'text-green-400' : 'text-red-400'}`}>
              {trend.isPositive ? '+' : '-'}{trend.value.toFixed(1)}%
            </div>
          </div>

          <div className="bg-gray-800/50 rounded-lg p-4">
            <div className="flex items-center gap-2 mb-2">
              <Target className="w-4 h-4 text-blue-400" />
              <span className="text-sm text-gray-400">Máximo</span>
            </div>
            <div className="text-lg font-bold text-blue-400">
              θ = {getMaxValue().toFixed(2)}
            </div>
          </div>

          <div className="bg-gray-800/50 rounded-lg p-4">
            <div className="flex items-center gap-2 mb-2">
              <Eye className="w-4 h-4 text-yellow-400" />
              <span className="text-sm text-gray-400">Actual</span>
            </div>
            <div className="text-lg font-bold text-yellow-400">
              θ = {getSelectedSubjectData().slice(-1)[0]?.value.toFixed(2) || '0.00'}
            </div>
          </div>

          <div className="bg-gray-800/50 rounded-lg p-4">
            <div className="flex items-center gap-2 mb-2">
              <Zap className="w-4 h-4 text-purple-400" />
              <span className="text-sm text-gray-400">Progreso</span>
            </div>
            <div className="text-lg font-bold text-purple-400">
              {((getSelectedSubjectData().slice(-1)[0]?.value || 0) - getMinValue()).toFixed(2)}
            </div>
          </div>
        </div>
      )}

      {/* Chart Content */}
      <div className="bg-gray-800/30 rounded-lg p-4">
        {chartMode === 'line' ? renderLineChart() : renderComparisonChart()}
      </div>

      {/* Insights */}
      <div className="mt-6 p-4 bg-purple-500/20 rounded-lg border border-purple-500/30">
        <h4 className="font-semibold text-white mb-2 flex items-center gap-2">
          <Zap className="w-4 h-4 text-yellow-400" />
          Análisis Inteligente
        </h4>
        
        {chartMode === 'line' ? (
          <p className="text-sm text-gray-300">
            {trend.isPositive ? (
              <>
                ¡Excelente progreso! Tu theta en <strong>{currentSubject.name}</strong> ha mejorado un{' '}
                <span className="text-green-400 font-semibold">{trend.value.toFixed(1)}%</span> en este período.
                {trend.value > 10 && ' ¡Sigue así para alcanzar el siguiente nivel de maestría!'}
              </>
            ) : (
              <>
                Tu theta en <strong>{currentSubject.name}</strong> ha disminuido un{' '}
                <span className="text-red-400 font-semibold">{trend.value.toFixed(1)}%</span>.
                Considera dedicar más tiempo a practicar conceptos fundamentales.
              </>
            )}
          </p>
        ) : (
          <p className="text-sm text-gray-300">
            Tu rendimiento más fuerte está en{' '}
            <strong className="text-green-400">
              {subjects.filter(s => s.key !== 'overall')
                .sort((a, b) => (data[data.length - 1]?.[b.key as keyof ThetaPoint] as number) - 
                              (data[data.length - 1]?.[a.key as keyof ThetaPoint] as number))[0]?.name}
            </strong>.
            Considera balancear tu tiempo de estudio enfocándote en las materias con menor theta.
          </p>
        )}
      </div>
    </motion.div>
  );
}