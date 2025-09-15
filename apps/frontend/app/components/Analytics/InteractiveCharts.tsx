'use client';

import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { 
  BarChart3,
  LineChart,
  PieChart,
  TrendingUp,
  TrendingDown,
  Activity,
  Calendar,
  Target,
  Brain,
  Clock,
  Users,
  Award,
  Filter,
  Download,
  Maximize2,
  Minimize2
} from 'lucide-react';

interface ChartData {
  labels: string[];
  values: number[];
  colors?: string[];
  tooltips?: string[];
}

interface TimeSeriesData {
  date: string;
  accuracy: number;
  battles: number;
  experience: number;
  active_users?: number;
}

interface SubjectData {
  subject: string;
  accuracy: number;
  questions: number;
  difficulty: number;
  trend: number;
}

interface InteractiveChartsProps {
  data: {
    timeSeriesData: TimeSeriesData[];
    subjectData: SubjectData[];
    difficultyDistribution: ChartData;
    performanceHeatmap: { topic: string; subject: string; performance: number }[];
  };
  type: 'student' | 'teacher' | 'admin';
}

export default function InteractiveCharts({ data, type }: InteractiveChartsProps) {
  const [activeChart, setActiveChart] = useState<string>('performance-trend');
  const [timeRange, setTimeRange] = useState<'7d' | '30d' | '90d'>('30d');
  const [isExpanded, setIsExpanded] = useState<string | null>(null);

  const chartTypes = [
    { id: 'performance-trend', label: 'Tendencia de Rendimiento', icon: LineChart },
    { id: 'subject-comparison', label: 'Comparación por Materia', icon: BarChart3 },
    { id: 'difficulty-distribution', label: 'Distribución de Dificultad', icon: PieChart },
    { id: 'activity-heatmap', label: 'Mapa de Calor de Actividad', icon: Activity }
  ];

  const getFilteredData = () => {
    const days = timeRange === '7d' ? 7 : timeRange === '30d' ? 30 : 90;
    const cutoffDate = new Date();
    cutoffDate.setDate(cutoffDate.getDate() - days);
    
    return data.timeSeriesData.filter(item => 
      new Date(item.date) >= cutoffDate
    );
  };

  const renderPerformanceTrendChart = () => {
    const filteredData = getFilteredData();
    const maxAccuracy = Math.max(...filteredData.map(d => d.accuracy));
    const minAccuracy = Math.min(...filteredData.map(d => d.accuracy));
    const trend = filteredData.length > 1 ? 
      ((filteredData[filteredData.length - 1].accuracy - filteredData[0].accuracy) / filteredData[0].accuracy) * 100 : 0;

    return (
      <motion.div
        className={`bg-gray-900/80 rounded-lg p-6 ${isExpanded === 'performance-trend' ? 'col-span-2 row-span-2' : ''}`}
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        layout
      >
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-purple-500/20 rounded-lg">
              <LineChart className="w-5 h-5 text-purple-400" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-white">Tendencia de Rendimiento</h3>
              <p className="text-gray-400 text-sm">Progreso en los últimos {timeRange}</p>
            </div>
          </div>
          
          <div className="flex items-center gap-2">
            <div className={`flex items-center gap-1 text-sm ${trend >= 0 ? 'text-green-400' : 'text-red-400'}`}>
              {trend >= 0 ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
              <span>{Math.abs(trend).toFixed(1)}%</span>
            </div>
            
            <button
              onClick={() => setIsExpanded(isExpanded === 'performance-trend' ? null : 'performance-trend')}
              className="p-1 hover:bg-gray-700 rounded"
            >
              {isExpanded === 'performance-trend' ? 
                <Minimize2 className="w-4 h-4 text-gray-400" /> : 
                <Maximize2 className="w-4 h-4 text-gray-400" />
              }
            </button>
          </div>
        </div>

        <div className={`relative ${isExpanded === 'performance-trend' ? 'h-96' : 'h-48'}`}>
          {/* SVG Chart Implementation */}
          <svg className="w-full h-full" viewBox="0 0 400 200">
            <defs>
              <linearGradient id="performanceGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                <stop offset="0%" stopColor="#8B5CF6" stopOpacity="0.3" />
                <stop offset="100%" stopColor="#8B5CF6" stopOpacity="0.1" />
              </linearGradient>
            </defs>
            
            {/* Grid lines */}
            {[0, 1, 2, 3, 4].map(i => (
              <line
                key={i}
                x1="40"
                y1={40 + i * 30}
                x2="380"
                y2={40 + i * 30}
                stroke="#374151"
                strokeWidth="1"
                strokeDasharray="2,2"
              />
            ))}
            
            {/* Performance line */}
            {filteredData.length > 1 && (
              <path
                d={`M ${filteredData.map((d, i) => 
                  `${40 + (i / (filteredData.length - 1)) * 340},${160 - (d.accuracy * 120)}`
                ).join(' L ')}`}
                fill="none"
                stroke="#8B5CF6"
                strokeWidth="3"
                strokeLinecap="round"
              />
            )}
            
            {/* Performance area */}
            {filteredData.length > 1 && (
              <path
                d={`M 40,160 L ${filteredData.map((d, i) => 
                  `${40 + (i / (filteredData.length - 1)) * 340},${160 - (d.accuracy * 120)}`
                ).join(' L ')} L 380,160 Z`}
                fill="url(#performanceGradient)"
              />
            )}
            
            {/* Data points */}
            {filteredData.map((d, i) => (
              <circle
                key={i}
                cx={40 + (i / (filteredData.length - 1)) * 340}
                cy={160 - (d.accuracy * 120)}
                r="4"
                fill="#8B5CF6"
                className="hover:r-6 transition-all cursor-pointer"
              />
            ))}
            
            {/* Axis labels */}
            <text x="20" y="50" fill="#9CA3AF" fontSize="12" textAnchor="middle">100%</text>
            <text x="20" y="80" fill="#9CA3AF" fontSize="12" textAnchor="middle">75%</text>
            <text x="20" y="110" fill="#9CA3AF" fontSize="12" textAnchor="middle">50%</text>
            <text x="20" y="140" fill="#9CA3AF" fontSize="12" textAnchor="middle">25%</text>
            <text x="20" y="170" fill="#9CA3AF" fontSize="12" textAnchor="middle">0%</text>
          </svg>
          
          {/* Stats overlay */}
          <div className="absolute top-4 right-4 bg-gray-800/90 rounded-lg p-3 text-sm">
            <div className="flex items-center gap-4">
              <div>
                <p className="text-gray-400">Máximo</p>
                <p className="text-green-400 font-semibold">{(maxAccuracy * 100).toFixed(1)}%</p>
              </div>
              <div>
                <p className="text-gray-400">Mínimo</p>
                <p className="text-red-400 font-semibold">{(minAccuracy * 100).toFixed(1)}%</p>
              </div>
              <div>
                <p className="text-gray-400">Promedio</p>
                <p className="text-blue-400 font-semibold">
                  {(filteredData.reduce((sum, d) => sum + d.accuracy, 0) / filteredData.length * 100).toFixed(1)}%
                </p>
              </div>
            </div>
          </div>
        </div>
      </motion.div>
    );
  };

  const renderSubjectComparisonChart = () => (
    <motion.div
      className={`bg-gray-900/80 rounded-lg p-6 ${isExpanded === 'subject-comparison' ? 'col-span-2 row-span-2' : ''}`}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.1 }}
      layout
    >
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-blue-500/20 rounded-lg">
            <BarChart3 className="w-5 h-5 text-blue-400" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-white">Comparación por Materia</h3>
            <p className="text-gray-400 text-sm">Rendimiento relativo por área</p>
          </div>
        </div>
        
        <button
          onClick={() => setIsExpanded(isExpanded === 'subject-comparison' ? null : 'subject-comparison')}
          className="p-1 hover:bg-gray-700 rounded"
        >
          {isExpanded === 'subject-comparison' ? 
            <Minimize2 className="w-4 h-4 text-gray-400" /> : 
            <Maximize2 className="w-4 h-4 text-gray-400" />
          }
        </button>
      </div>

      <div className={`${isExpanded === 'subject-comparison' ? 'h-96' : 'h-48'}`}>
        <div className="space-y-3 h-full overflow-y-auto">
          {data.subjectData.map((subject, index) => (
            <div key={index} className="bg-gray-800/50 rounded-lg p-3">
              <div className="flex items-center justify-between mb-2">
                <span className="text-white font-semibold">{subject.subject}</span>
                <div className="flex items-center gap-2">
                  <span className="text-white font-semibold">{(subject.accuracy * 100).toFixed(1)}%</span>
                  <div className={`flex items-center gap-1 text-xs ${
                    subject.trend >= 0 ? 'text-green-400' : 'text-red-400'
                  }`}>
                    {subject.trend >= 0 ? 
                      <TrendingUp className="w-3 h-3" /> : 
                      <TrendingDown className="w-3 h-3" />
                    }
                    <span>{Math.abs(subject.trend).toFixed(1)}%</span>
                  </div>
                </div>
              </div>
              
              {/* Progress bar */}
              <div className="w-full bg-gray-700 rounded-full h-3 mb-2">
                <div 
                  className="bg-gradient-to-r from-blue-500 to-purple-500 h-3 rounded-full transition-all duration-1000"
                  style={{ width: `${subject.accuracy * 100}%` }}
                />
              </div>
              
              <div className="flex justify-between text-xs text-gray-400">
                <span>{subject.questions} preguntas</span>
                <span>Dificultad: {subject.difficulty.toFixed(1)}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </motion.div>
  );

  const renderDifficultyDistributionChart = () => (
    <motion.div
      className={`bg-gray-900/80 rounded-lg p-6 ${isExpanded === 'difficulty-distribution' ? 'col-span-2 row-span-2' : ''}`}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.2 }}
      layout
    >
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-green-500/20 rounded-lg">
            <PieChart className="w-5 h-5 text-green-400" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-white">Distribución de Dificultad</h3>
            <p className="text-gray-400 text-sm">Análisis de preguntas por nivel</p>
          </div>
        </div>
        
        <button
          onClick={() => setIsExpanded(isExpanded === 'difficulty-distribution' ? null : 'difficulty-distribution')}
          className="p-1 hover:bg-gray-700 rounded"
        >
          {isExpanded === 'difficulty-distribution' ? 
            <Minimize2 className="w-4 h-4 text-gray-400" /> : 
            <Maximize2 className="w-4 h-4 text-gray-400" />
          }
        </button>
      </div>

      <div className={`${isExpanded === 'difficulty-distribution' ? 'h-96' : 'h-48'} flex items-center justify-center`}>
        {/* Simplified pie chart representation */}
        <div className="grid grid-cols-2 gap-4 w-full">
          {data.difficultyDistribution.labels.map((label, index) => {
            const value = data.difficultyDistribution.values[index];
            const total = data.difficultyDistribution.values.reduce((sum, v) => sum + v, 0);
            const percentage = (value / total) * 100;
            const colors = ['bg-green-500', 'bg-yellow-500', 'bg-orange-500', 'bg-red-500'];
            
            return (
              <div key={index} className="bg-gray-800/50 rounded-lg p-3">
                <div className="flex items-center gap-3 mb-2">
                  <div className={`w-4 h-4 rounded-full ${colors[index % colors.length]}`} />
                  <span className="text-white font-semibold">{label}</span>
                </div>
                <div className="text-2xl font-bold text-white mb-1">{value}</div>
                <div className="text-sm text-gray-400">{percentage.toFixed(1)}% del total</div>
              </div>
            );
          })}
        </div>
      </div>
    </motion.div>
  );

  const renderActivityHeatmap = () => (
    <motion.div
      className={`bg-gray-900/80 rounded-lg p-6 ${isExpanded === 'activity-heatmap' ? 'col-span-2 row-span-2' : ''}`}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.3 }}
      layout
    >
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-orange-500/20 rounded-lg">
            <Activity className="w-5 h-5 text-orange-400" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-white">Mapa de Calor de Actividad</h3>
            <p className="text-gray-400 text-sm">Rendimiento por tema y materia</p>
          </div>
        </div>
        
        <button
          onClick={() => setIsExpanded(isExpanded === 'activity-heatmap' ? null : 'activity-heatmap')}
          className="p-1 hover:bg-gray-700 rounded"
        >
          {isExpanded === 'activity-heatmap' ? 
            <Minimize2 className="w-4 h-4 text-gray-400" /> : 
            <Maximize2 className="w-4 h-4 text-gray-400" />
          }
        </button>
      </div>

      <div className={`${isExpanded === 'activity-heatmap' ? 'h-96' : 'h-48'} overflow-y-auto`}>
        <div className="grid grid-cols-1 gap-2">
          {data.performanceHeatmap.map((item, index) => {
            const intensity = item.performance;
            const colorClass = 
              intensity >= 0.8 ? 'bg-green-500/80' :
              intensity >= 0.6 ? 'bg-yellow-500/80' :
              intensity >= 0.4 ? 'bg-orange-500/80' :
              'bg-red-500/80';
            
            return (
              <div key={index} className={`${colorClass} rounded-lg p-3 text-white`}>
                <div className="flex items-center justify-between">
                  <div>
                    <span className="font-semibold">{item.topic}</span>
                    <span className="text-sm opacity-80 ml-2">({item.subject})</span>
                  </div>
                  <span className="font-bold">{(intensity * 100).toFixed(1)}%</span>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </motion.div>
  );

  return (
    <div className="space-y-6">
      {/* Chart Controls */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div className="flex items-center gap-4">
          <h3 className="text-xl font-semibold text-white">Visualizaciones Interactivas</h3>
          
          {/* Time Range Selector */}
          <div className="flex items-center gap-2 bg-gray-900/80 rounded-lg p-1">
            {(['7d', '30d', '90d'] as const).map(range => (
              <button
                key={range}
                onClick={() => setTimeRange(range)}
                className={`px-3 py-1 rounded-lg text-sm font-semibold transition-all ${
                  timeRange === range
                    ? 'bg-purple-600 text-white'
                    : 'text-gray-400 hover:text-white'
                }`}
              >
                {range === '7d' && '7 días'}
                {range === '30d' && '30 días'}
                {range === '90d' && '90 días'}
              </button>
            ))}
          </div>
        </div>
        
        <div className="flex items-center gap-2">
          <button className="bg-purple-600 hover:bg-purple-700 text-white rounded-lg px-4 py-2 text-sm flex items-center gap-2 transition-colors">
            <Download className="w-4 h-4" />
            Exportar Gráficos
          </button>
        </div>
      </div>

      {/* Chart Navigation */}
      <div className="flex flex-wrap gap-2">
        {chartTypes.map(chart => {
          const IconComponent = chart.icon;
          return (
            <button
              key={chart.id}
              onClick={() => setActiveChart(chart.id)}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-semibold transition-all ${
                activeChart === chart.id
                  ? 'bg-purple-600 text-white'
                  : 'bg-gray-800 text-gray-400 hover:text-white hover:bg-gray-700'
              }`}
            >
              <IconComponent className="w-4 h-4" />
              {chart.label}
            </button>
          );
        })}
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {activeChart === 'performance-trend' && renderPerformanceTrendChart()}
        {activeChart === 'subject-comparison' && renderSubjectComparisonChart()}
        {activeChart === 'difficulty-distribution' && renderDifficultyDistributionChart()}
        {activeChart === 'activity-heatmap' && renderActivityHeatmap()}
        
        {/* Show all charts if none specifically selected or show complementary charts */}
        {activeChart === 'performance-trend' && renderSubjectComparisonChart()}
        {activeChart === 'subject-comparison' && renderDifficultyDistributionChart()}
        {activeChart === 'difficulty-distribution' && renderActivityHeatmap()}
        {activeChart === 'activity-heatmap' && renderPerformanceTrendChart()}
      </div>

      {/* Chart Legend */}
      <motion.div
        className="bg-gray-900/80 rounded-lg p-4"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
      >
        <h4 className="text-lg font-semibold text-white mb-3">Leyenda y Explicación</h4>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 text-sm">
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-green-500 rounded" />
            <span className="text-gray-300">Excelente (80-100%)</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-yellow-500 rounded" />
            <span className="text-gray-300">Bueno (60-79%)</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-orange-500 rounded" />
            <span className="text-gray-300">Regular (40-59%)</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-red-500 rounded" />
            <span className="text-gray-300">Necesita Mejora (0-39%)</span>
          </div>
        </div>
        
        <div className="mt-4 p-3 bg-blue-500/10 rounded-lg border border-blue-500/20">
          <p className="text-blue-400 text-sm">
            <strong>Tip:</strong> Haz clic en los botones de maximizar para ver cada gráfico en detalle. 
            Los datos se actualizan automáticamente según el rango de tiempo seleccionado.
          </p>
        </div>
      </motion.div>
    </div>
  );
}