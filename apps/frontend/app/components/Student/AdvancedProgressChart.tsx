'use client';

import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  AreaChart,
  Area,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar
} from 'recharts';
import {
  TrendingUp,
  BarChart3,
  PieChartIcon,
  Target,
  Calendar,
  Activity,
  Award,
  Clock,
  Filter
} from 'lucide-react';

interface ProgressData {
  date: string;
  mathematics: number;
  physics: number;
  chemistry: number;
  biology: number;
  spanish: number;
  overall: number;
  sessions: number;
  timeSpent: number;
}

interface SubjectMastery {
  subject: string;
  mastery: number;
  improvement: number;
  timeSpent: number;
  questionsAnswered: number;
}

interface AdvancedProgressChartProps {
  timeFilter: '7d' | '30d' | '90d';
  userId?: string;
}

export default function AdvancedProgressChart({ timeFilter, userId }: AdvancedProgressChartProps) {
  const [chartType, setChartType] = useState<'line' | 'area' | 'bar' | 'radar'>('line');
  const [focusSubject, setFocusSubject] = useState<string | null>(null);
  const [progressData, setProgressData] = useState<ProgressData[]>([]);
  const [subjectMastery, setSubjectMastery] = useState<SubjectMastery[]>([]);
  const [loading, setLoading] = useState(true);

  // Generate mock data based on time filter
  useEffect(() => {
    const generateProgressData = () => {
      const days = timeFilter === '7d' ? 7 : timeFilter === '30d' ? 30 : 90;
      const data: ProgressData[] = [];
      
      for (let i = 0; i < days; i++) {
        const date = new Date();
        date.setDate(date.getDate() - (days - 1 - i));
        
        // Simulate realistic progress with some randomness
        const baseProgress = 60 + (i / days) * 20; // Overall improvement over time
        const randomFactor = Math.random() * 10 - 5; // ±5 variation
        
        data.push({
          date: date.toISOString().split('T')[0],
          mathematics: Math.max(0, Math.min(100, baseProgress + randomFactor + Math.random() * 5)),
          physics: Math.max(0, Math.min(100, baseProgress + randomFactor - 2 + Math.random() * 5)),
          chemistry: Math.max(0, Math.min(100, baseProgress + randomFactor + 1 + Math.random() * 5)),
          biology: Math.max(0, Math.min(100, baseProgress + randomFactor - 1 + Math.random() * 5)),
          spanish: Math.max(0, Math.min(100, baseProgress + randomFactor + 3 + Math.random() * 5)),
          overall: Math.max(0, Math.min(100, baseProgress + randomFactor)),
          sessions: Math.floor(Math.random() * 5) + 1,
          timeSpent: Math.floor(Math.random() * 120) + 30 // 30-150 minutes
        });
      }
      
      return data;
    };

    const generateSubjectMastery = (): SubjectMastery[] => [
      {
        subject: 'Matemáticas',
        mastery: 78.5,
        improvement: 12.3,
        timeSpent: 450,
        questionsAnswered: 234
      },
      {
        subject: 'Física',
        mastery: 72.1,
        improvement: 8.7,
        timeSpent: 380,
        questionsAnswered: 189
      },
      {
        subject: 'Química',
        mastery: 81.2,
        improvement: 15.2,
        timeSpent: 420,
        questionsAnswered: 201
      },
      {
        subject: 'Biología',
        mastery: 75.8,
        improvement: 10.1,
        timeSpent: 360,
        questionsAnswered: 167
      },
      {
        subject: 'Español',
        mastery: 85.3,
        improvement: 6.9,
        timeSpent: 290,
        questionsAnswered: 145
      }
    ];

    setLoading(true);
    // Simulate loading delay
    setTimeout(() => {
      setProgressData(generateProgressData());
      setSubjectMastery(generateSubjectMastery());
      setLoading(false);
    }, 800);
  }, [timeFilter]);

  const subjects = ['mathematics', 'physics', 'chemistry', 'biology', 'spanish'];
  const subjectColors = {
    mathematics: '#3b82f6',
    physics: '#8b5cf6',
    chemistry: '#10b981',
    biology: '#f59e0b',
    spanish: '#ef4444',
    overall: '#6366f1'
  };

  const subjectLabels = {
    mathematics: 'Matemáticas',
    physics: 'Física', 
    chemistry: 'Química',
    biology: 'Biología',
    spanish: 'Español',
    overall: 'General'
  };

  const chartVariants = [
    { id: 'line', label: 'Líneas', icon: TrendingUp },
    { id: 'area', label: 'Área', icon: BarChart3 },
    { id: 'bar', label: 'Barras', icon: BarChart3 },
    { id: 'radar', label: 'Radar', icon: Target }
  ];

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-gray-900/95 border border-gray-700 rounded-lg p-4 shadow-xl">
          <p className="text-white font-semibold mb-2">
            {new Date(label).toLocaleDateString()}
          </p>
          {payload.map((entry: any, index: number) => (
            <div key={index} className="flex items-center gap-2 mb-1">
              <div 
                className="w-3 h-3 rounded-full" 
                style={{ backgroundColor: entry.color }}
              />
              <span className="text-gray-300 text-sm">
                {subjectLabels[entry.dataKey as keyof typeof subjectLabels]}: {entry.value}%
              </span>
            </div>
          ))}
        </div>
      );
    }
    return null;
  };

  const renderChart = () => {
    if (loading) {
      return (
        <div className="h-80 flex items-center justify-center">
          <motion.div
            className="w-8 h-8 border-2 border-purple-500 border-t-transparent rounded-full"
            animate={{ rotate: 360 }}
            transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
          />
        </div>
      );
    }

    const dataToShow = focusSubject 
      ? progressData.map(d => ({ ...d, [focusSubject]: d[focusSubject as keyof ProgressData] }))
      : progressData;

    switch (chartType) {
      case 'area':
        return (
          <ResponsiveContainer width="100%" height={320}>
            <AreaChart data={dataToShow}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis 
                dataKey="date" 
                stroke="#9ca3af"
                fontSize={12}
                tickFormatter={(date) => new Date(date).toLocaleDateString('es-ES', { month: 'short', day: 'numeric' })}
              />
              <YAxis stroke="#9ca3af" fontSize={12} />
              <Tooltip content={<CustomTooltip />} />
              {focusSubject ? (
                <Area
                  type="monotone"
                  dataKey={focusSubject}
                  stroke={subjectColors[focusSubject as keyof typeof subjectColors]}
                  fill={subjectColors[focusSubject as keyof typeof subjectColors]}
                  fillOpacity={0.3}
                />
              ) : (
                subjects.map((subject, index) => (
                  <Area
                    key={subject}
                    type="monotone"
                    dataKey={subject}
                    stackId="1"
                    stroke={subjectColors[subject as keyof typeof subjectColors]}
                    fill={subjectColors[subject as keyof typeof subjectColors]}
                    fillOpacity={0.6}
                  />
                ))
              )}
            </AreaChart>
          </ResponsiveContainer>
        );

      case 'bar':
        return (
          <ResponsiveContainer width="100%" height={320}>
            <BarChart data={dataToShow}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis 
                dataKey="date" 
                stroke="#9ca3af"
                fontSize={12}
                tickFormatter={(date) => new Date(date).toLocaleDateString('es-ES', { month: 'short', day: 'numeric' })}
              />
              <YAxis stroke="#9ca3af" fontSize={12} />
              <Tooltip content={<CustomTooltip />} />
              {focusSubject ? (
                <Bar
                  dataKey={focusSubject}
                  fill={subjectColors[focusSubject as keyof typeof subjectColors]}
                  radius={[2, 2, 0, 0]}
                />
              ) : (
                subjects.map((subject) => (
                  <Bar
                    key={subject}
                    dataKey={subject}
                    fill={subjectColors[subject as keyof typeof subjectColors]}
                    radius={[2, 2, 0, 0]}
                  />
                ))
              )}
            </BarChart>
          </ResponsiveContainer>
        );

      case 'radar':
        const radarData = subjectMastery.map(s => ({
          subject: s.subject,
          mastery: s.mastery,
          improvement: s.improvement * 5 // Scale for better visualization
        }));

        return (
          <ResponsiveContainer width="100%" height={320}>
            <RadarChart data={radarData}>
              <PolarGrid stroke="#374151" />
              <PolarAngleAxis dataKey="subject" tick={{ fontSize: 12, fill: '#9ca3af' }} />
              <PolarRadiusAxis 
                angle={90} 
                domain={[0, 100]} 
                tick={{ fontSize: 10, fill: '#9ca3af' }}
              />
              <Radar
                name="Nivel de Dominio"
                dataKey="mastery"
                stroke="#8b5cf6"
                fill="#8b5cf6"
                fillOpacity={0.3}
                strokeWidth={2}
              />
              <Radar
                name="Mejora (x5)"
                dataKey="improvement"
                stroke="#10b981"
                fill="#10b981"
                fillOpacity={0.1}
                strokeWidth={2}
              />
              <Tooltip 
                content={({ active, payload }) => {
                  if (active && payload && payload.length) {
                    return (
                      <div className="bg-gray-900/95 border border-gray-700 rounded-lg p-3 shadow-xl">
                        {payload.map((entry, index) => (
                          <div key={index} className="flex items-center gap-2">
                            <div 
                              className="w-3 h-3 rounded-full" 
                              style={{ backgroundColor: entry.color }}
                            />
                            <span className="text-gray-300 text-sm">
                              {entry.name}: {entry.name === 'Mejora (x5)' ? (entry.value! / 5).toFixed(1) : entry.value}%
                            </span>
                          </div>
                        ))}
                      </div>
                    );
                  }
                  return null;
                }}
              />
            </RadarChart>
          </ResponsiveContainer>
        );

      default: // line
        return (
          <ResponsiveContainer width="100%" height={320}>
            <LineChart data={dataToShow}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis 
                dataKey="date" 
                stroke="#9ca3af"
                fontSize={12}
                tickFormatter={(date) => new Date(date).toLocaleDateString('es-ES', { month: 'short', day: 'numeric' })}
              />
              <YAxis stroke="#9ca3af" fontSize={12} />
              <Tooltip content={<CustomTooltip />} />
              {focusSubject ? (
                <Line
                  type="monotone"
                  dataKey={focusSubject}
                  stroke={subjectColors[focusSubject as keyof typeof subjectColors]}
                  strokeWidth={3}
                  dot={{ fill: subjectColors[focusSubject as keyof typeof subjectColors], r: 4 }}
                  activeDot={{ r: 6 }}
                />
              ) : (
                subjects.map((subject) => (
                  <Line
                    key={subject}
                    type="monotone"
                    dataKey={subject}
                    stroke={subjectColors[subject as keyof typeof subjectColors]}
                    strokeWidth={2}
                    dot={{ r: 3 }}
                    activeDot={{ r: 5 }}
                  />
                ))
              )}
            </LineChart>
          </ResponsiveContainer>
        );
    }
  };

  return (
    <div className="bg-gray-900/80 rounded-xl p-6 border border-purple-500/30">
      {/* Header */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4 mb-6">
        <div>
          <h3 className="text-xl font-semibold text-white mb-2 flex items-center gap-3">
            <Activity className="w-6 h-6 text-purple-400" />
            Evolución del Progreso
          </h3>
          <p className="text-gray-400 text-sm">
            Análisis detallado de tu mejora académica a lo largo del tiempo
          </p>
        </div>

        <div className="flex items-center gap-4">
          {/* Chart Type Selector */}
          <div className="flex items-center gap-1 bg-gray-800/50 rounded-lg p-1">
            {chartVariants.map((variant) => (
              <button
                key={variant.id}
                onClick={() => setChartType(variant.id as any)}
                className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-all ${
                  chartType === variant.id
                    ? 'bg-purple-600 text-white'
                    : 'text-gray-400 hover:text-white hover:bg-gray-700'
                }`}
                title={variant.label}
              >
                <variant.icon className="w-4 h-4" />
                <span className="hidden sm:inline">{variant.label}</span>
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Subject Filter */}
      <div className="flex flex-wrap items-center gap-2 mb-6">
        <button
          onClick={() => setFocusSubject(null)}
          className={`px-3 py-1 rounded-full text-sm font-medium transition-all ${
            !focusSubject
              ? 'bg-purple-600 text-white'
              : 'bg-gray-800 text-gray-400 hover:text-white'
          }`}
        >
          Todas las materias
        </button>
        {subjects.map((subject) => (
          <button
            key={subject}
            onClick={() => setFocusSubject(subject)}
            className={`px-3 py-1 rounded-full text-sm font-medium transition-all flex items-center gap-2 ${
              focusSubject === subject
                ? 'bg-purple-600 text-white'
                : 'bg-gray-800 text-gray-400 hover:text-white'
            }`}
          >
            <div 
              className="w-2 h-2 rounded-full" 
              style={{ backgroundColor: subjectColors[subject as keyof typeof subjectColors] }}
            />
            {subjectLabels[subject as keyof typeof subjectLabels]}
          </button>
        ))}
      </div>

      {/* Chart */}
      <div className="mb-6">
        {renderChart()}
      </div>

      {/* Statistics Summary */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 pt-6 border-t border-gray-700/50">
        <motion.div 
          className="text-center"
          whileHover={{ scale: 1.05 }}
        >
          <div className="w-12 h-12 bg-blue-500/20 rounded-lg flex items-center justify-center mx-auto mb-2">
            <TrendingUp className="w-6 h-6 text-blue-400" />
          </div>
          <p className="text-2xl font-bold text-white">+12.5%</p>
          <p className="text-gray-400 text-sm">Mejora General</p>
        </motion.div>

        <motion.div 
          className="text-center"
          whileHover={{ scale: 1.05 }}
        >
          <div className="w-12 h-12 bg-green-500/20 rounded-lg flex items-center justify-center mx-auto mb-2">
            <Award className="w-6 h-6 text-green-400" />
          </div>
          <p className="text-2xl font-bold text-white">85.3%</p>
          <p className="text-gray-400 text-sm">Mejor Materia</p>
        </motion.div>

        <motion.div 
          className="text-center"
          whileHover={{ scale: 1.05 }}
        >
          <div className="w-12 h-12 bg-purple-500/20 rounded-lg flex items-center justify-center mx-auto mb-2">
            <Clock className="w-6 h-6 text-purple-400" />
          </div>
          <p className="text-2xl font-bold text-white">7.5h</p>
          <p className="text-gray-400 text-sm">Tiempo Semanal</p>
        </motion.div>

        <motion.div 
          className="text-center"
          whileHover={{ scale: 1.05 }}
        >
          <div className="w-12 h-12 bg-yellow-500/20 rounded-lg flex items-center justify-center mx-auto mb-2">
            <Target className="w-6 h-6 text-yellow-400" />
          </div>
          <p className="text-2xl font-bold text-white">936</p>
          <p className="text-gray-400 text-sm">Preguntas Respondidas</p>
        </motion.div>
      </div>
    </div>
  );
}