'use client';

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import yaml from 'js-yaml';
import { z } from 'zod';
import { useQuery, useQueryClient } from 'react-query';
import { useMediaQuery } from '@/hooks/useMediaQuery';
import { useWebSocket } from '@/hooks/useWebSocket';
import { useAudio } from './PortalLogin/AudioEngine';
import { 
  ChevronRight, 
  ChevronDown, 
  BookOpen, 
  Target, 
  AlertTriangle,
  Sparkles,
  Brain,
  Zap,
  TrendingUp,
  Lock,
  Star
} from 'lucide-react';

// Schema for YAML validation
const TopicSchema = z.object({
  name: z.string(),
  difficulty: z.number().min(1).max(5),
  questions: z.number(),
  tags: z.array(z.string()).optional()
});

const RecommendationSchema = z.object({
  priority: z.enum(['high', 'medium', 'low']),
  weak_areas: z.array(z.string()).optional(),
  focus_topics: z.array(z.string()).optional(),
  study_time: z.string().optional()
});

const UnitSchema = z.object({
  name: z.string(),
  description: z.string(),
  topics: z.array(TopicSchema),
  recommendations: RecommendationSchema.optional(),
  unlocked: z.boolean().default(true),
  progress: z.number().min(0).max(100).default(0),
  ai_recommended: z.boolean().optional()
});

const DungeonSchema = z.object({
  subject: z.string(),
  title: z.string(),
  description: z.string(),
  units: z.array(UnitSchema),
  total_questions: z.number(),
  estimated_time: z.string(),
  difficulty_curve: z.enum(['linear', 'progressive', 'adaptive']).default('progressive')
});

interface YAMLRendererProps {
  subject: string;
  userLevel?: number;
  weaknessData?: Record<string, number>;
  onUnitSelect?: (unit: any) => void;
}

export default function YAMLRenderer({ 
  subject, 
  userLevel = 1,
  weaknessData = {},
  onUnitSelect 
}: YAMLRendererProps) {
  const { playSound } = useAudio();
  const queryClient = useQueryClient();
  const isMobile = useMediaQuery('(max-width: 768px)');
  const { socket } = useWebSocket();
  
  const [expandedUnits, setExpandedUnits] = useState<Set<string>>(new Set());
  const [selectedUnit, setSelectedUnit] = useState<any>(null);
  const [aiRecommendations, setAiRecommendations] = useState<Record<string, boolean>>({});

  // Fetch YAML content
  const { data: dungeonData, isLoading, error } = useQuery({
    queryKey: ['dungeon-yaml', subject, userLevel],
    queryFn: async () => {
      const response = await fetch(`/api/v1/study-plans/generate-yaml/${subject}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          user_level: userLevel,
          weakness_data: weaknessData 
        })
      });
      
      if (!response.ok) throw new Error('Failed to generate YAML');
      
      const yamlText = await response.text();
      const parsed = yaml.load(yamlText) as any;
      return DungeonSchema.parse(parsed);
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 10 * 60 * 1000, // 10 minutes
  });

  // Listen for AI recommendations via WebSocket
  useEffect(() => {
    if (!socket) return;

    const handleRecommendation = (data: any) => {
      if (data.subject === subject && data.unit) {
        setAiRecommendations(prev => ({
          ...prev,
          [data.unit]: true
        }));
        
        // Update query cache
        queryClient.setQueryData(['dungeon-yaml', subject, userLevel], (old: any) => {
          if (!old) return old;
          
          return {
            ...old,
            units: old.units.map((unit: any) => 
              unit.name === data.unit 
                ? { ...unit, ai_recommended: true, recommendations: data.recommendations }
                : unit
            )
          };
        });
        
        playSound('notification_epic');
      }
    };

    socket.on('recommendation-update', handleRecommendation);
    
    return () => {
      socket.off('recommendation-update', handleRecommendation);
    };
  }, [socket, subject, userLevel, queryClient, playSound]);

  const toggleUnit = (unitName: string) => {
    setExpandedUnits(prev => {
      const newSet = new Set(prev);
      if (newSet.has(unitName)) {
        newSet.delete(unitName);
      } else {
        newSet.add(unitName);
        playSound('typing_click');
      }
      return newSet;
    });
  };

  const handleUnitClick = (unit: any) => {
    if (!unit.unlocked) {
      playSound('glitch');
      return;
    }
    
    setSelectedUnit(unit);
    playSound('portal_hum');
    
    if (onUnitSelect) {
      onUnitSelect(unit);
    }
  };

  const getDifficultyColor = (difficulty: number) => {
    const colors = [
      'text-green-400',
      'text-blue-400',
      'text-yellow-400',
      'text-orange-400',
      'text-red-400'
    ];
    return colors[Math.min(difficulty - 1, 4)];
  };

  const getPriorityIcon = (priority?: string) => {
    switch (priority) {
      case 'high':
        return <AlertTriangle className="w-4 h-4 text-red-400" />;
      case 'medium':
        return <Target className="w-4 h-4 text-yellow-400" />;
      default:
        return null;
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-8">
        <motion.div
          className="flex flex-col items-center gap-4"
          animate={{ opacity: [0.5, 1, 0.5] }}
          transition={{ duration: 2, repeat: Infinity }}
        >
          <Brain className="w-12 h-12 text-purple-400" />
          <p className="text-purple-300">Generando mazmorra personalizada...</p>
        </motion.div>
      </div>
    );
  }

  if (error || !dungeonData) {
    return (
      <div className="text-center p-8">
        <AlertTriangle className="w-12 h-12 text-red-400 mx-auto mb-4" />
        <p className="text-red-300">Error al cargar el contenido</p>
      </div>
    );
  }

  return (
    <div className="w-full max-w-4xl mx-auto p-4">
      {/* Dungeon Header */}
      <motion.div
        className="bg-gray-800/50 rounded-lg p-6 mb-6 border border-purple-500/30"
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <h2 className="text-2xl font-bold text-white mb-2 font-cinzel">
          {dungeonData.title}
        </h2>
        <p className="text-gray-300 mb-4">{dungeonData.description}</p>
        
        <div className="flex flex-wrap gap-4 text-sm">
          <div className="flex items-center gap-2">
            <BookOpen className="w-4 h-4 text-blue-400" />
            <span className="text-gray-300">
              {dungeonData.total_questions} preguntas
            </span>
          </div>
          <div className="flex items-center gap-2">
            <Target className="w-4 h-4 text-green-400" />
            <span className="text-gray-300">
              Tiempo estimado: {dungeonData.estimated_time}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <TrendingUp className="w-4 h-4 text-purple-400" />
            <span className="text-gray-300">
              Curva: {dungeonData.difficulty_curve}
            </span>
          </div>
        </div>
      </motion.div>

      {/* Units Tree/Accordion */}
      <div className="space-y-3">
        {dungeonData.units.map((unit, index) => {
          const isExpanded = expandedUnits.has(unit.name);
          const isRecommended = unit.ai_recommended || aiRecommendations[unit.name];
          const hasWeakness = unit.recommendations?.priority === 'high';
          
          return (
            <motion.div
              key={unit.name}
              className={`bg-gray-800/30 rounded-lg border transition-all ${
                unit.unlocked
                  ? 'border-gray-700 hover:border-purple-500/50'
                  : 'border-gray-800 opacity-50'
              } ${isRecommended ? 'ring-2 ring-purple-500/50' : ''}`}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.1 }}
            >
              {/* Unit Header */}
              <button
                className="w-full p-4 flex items-center justify-between text-left"
                onClick={() => unit.unlocked && toggleUnit(unit.name)}
                disabled={!unit.unlocked}
              >
                <div className="flex items-center gap-3 flex-1">
                  <motion.div
                    className="text-gray-400"
                    animate={{ rotate: isExpanded ? 90 : 0 }}
                    transition={{ duration: 0.2 }}
                  >
                    {unit.unlocked ? (
                      <ChevronRight className="w-5 h-5" />
                    ) : (
                      <Lock className="w-5 h-5" />
                    )}
                  </motion.div>
                  
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <h3 className="font-semibold text-white">
                        {unit.name}
                      </h3>
                      {isRecommended && (
                        <motion.div
                          initial={{ scale: 0 }}
                          animate={{ scale: 1 }}
                          className="flex items-center gap-1"
                        >
                          <Sparkles className="w-4 h-4 text-purple-400" />
                          <span className="text-xs text-purple-300">
                            IA Recomienda
                          </span>
                        </motion.div>
                      )}
                      {hasWeakness && (
                        <motion.div
                          className="animate-pulse"
                          title="Área débil detectada"
                        >
                          <AlertTriangle className="w-4 h-4 text-orange-400" />
                        </motion.div>
                      )}
                    </div>
                    <p className="text-sm text-gray-400 mt-1">
                      {unit.description}
                    </p>
                  </div>
                </div>

                {/* Progress Bar */}
                <div className="w-32">
                  <div className="flex justify-between text-xs text-gray-400 mb-1">
                    <span>Progreso</span>
                    <span>{unit.progress}%</span>
                  </div>
                  <div className="w-full bg-gray-700 rounded-full h-2">
                    <motion.div
                      className={`h-full rounded-full ${
                        unit.progress === 100
                          ? 'bg-green-500'
                          : unit.progress >= 70
                          ? 'bg-blue-500'
                          : 'bg-purple-500'
                      }`}
                      initial={{ width: 0 }}
                      animate={{ width: `${unit.progress}%` }}
                      transition={{ duration: 0.5, delay: index * 0.1 }}
                    />
                  </div>
                </div>
              </button>

              {/* Expanded Content */}
              <AnimatePresence>
                {isExpanded && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: 'auto', opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    transition={{ duration: 0.3 }}
                    className="overflow-hidden"
                  >
                    <div className="px-4 pb-4">
                      {/* Recommendations */}
                      {unit.recommendations && (
                        <div className="bg-purple-900/20 rounded-lg p-3 mb-4 border border-purple-500/30">
                          <div className="flex items-center gap-2 mb-2">
                            <Brain className="w-4 h-4 text-purple-400" />
                            <span className="text-sm font-semibold text-purple-300">
                              Recomendaciones IA
                            </span>
                            {getPriorityIcon(unit.recommendations.priority)}
                          </div>
                          
                          {unit.recommendations.weak_areas && (
                            <div className="mb-2">
                              <span className="text-xs text-gray-400">
                                Áreas débiles:
                              </span>
                              <div className="flex flex-wrap gap-1 mt-1">
                                {unit.recommendations.weak_areas.map(area => (
                                  <span
                                    key={area}
                                    className="text-xs bg-red-900/30 text-red-300 px-2 py-1 rounded"
                                  >
                                    {area}
                                  </span>
                                ))}
                              </div>
                            </div>
                          )}
                          
                          {unit.recommendations.study_time && (
                            <p className="text-xs text-gray-300">
                              Tiempo sugerido: {unit.recommendations.study_time}
                            </p>
                          )}
                        </div>
                      )}

                      {/* Topics Grid */}
                      <div className={`grid ${isMobile ? 'grid-cols-1' : 'grid-cols-2'} gap-3`}>
                        {unit.topics.map((topic, topicIndex) => (
                          <motion.div
                            key={topic.name}
                            className="bg-gray-900/50 rounded-lg p-3 border border-gray-700 hover:border-blue-500/50 transition-all cursor-pointer"
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: topicIndex * 0.05 }}
                            onClick={() => handleUnitClick({ ...unit, selectedTopic: topic })}
                          >
                            <div className="flex items-start justify-between mb-2">
                              <h4 className="text-sm font-semibold text-white">
                                {topic.name}
                              </h4>
                              <div className="flex items-center gap-1">
                                {[...Array(5)].map((_, i) => (
                                  <Star
                                    key={i}
                                    className={`w-3 h-3 ${
                                      i < topic.difficulty
                                        ? getDifficultyColor(topic.difficulty)
                                        : 'text-gray-600'
                                    }`}
                                    fill={i < topic.difficulty ? 'currentColor' : 'none'}
                                  />
                                ))}
                              </div>
                            </div>
                            
                            <div className="flex items-center justify-between text-xs text-gray-400">
                              <span>{topic.questions} preguntas</span>
                              {topic.tags && topic.tags.length > 0 && (
                                <div className="flex gap-1">
                                  {topic.tags.slice(0, 2).map(tag => (
                                    <span
                                      key={tag}
                                      className="bg-gray-800 px-1.5 py-0.5 rounded text-xs"
                                    >
                                      {tag}
                                    </span>
                                  ))}
                                </div>
                              )}
                            </div>
                          </motion.div>
                        ))}
                      </div>

                      {/* Action Button */}
                      <motion.button
                        className="w-full mt-4 bg-gradient-to-r from-purple-600 to-purple-700 hover:from-purple-700 hover:to-purple-800 
                          text-white font-semibold py-3 px-4 rounded-lg transition-all flex items-center justify-center gap-2"
                        whileHover={{ scale: 1.02 }}
                        whileTap={{ scale: 0.98 }}
                        onClick={() => handleUnitClick(unit)}
                      >
                        <Zap className="w-5 h-5" />
                        Iniciar Unidad
                      </motion.button>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.div>
          );
        })}
      </div>

      {/* Completion Message */}
      {dungeonData.units.every(u => u.progress === 100) && (
        <motion.div
          className="mt-6 bg-green-900/30 rounded-lg p-6 border border-green-500/50 text-center"
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
        >
          <Star className="w-12 h-12 text-green-400 mx-auto mb-3" />
          <h3 className="text-xl font-bold text-green-300 mb-2">
            ¡Mazmorra Completada!
          </h3>
          <p className="text-gray-300">
            Has dominado todos los temas de {dungeonData.subject}
          </p>
        </motion.div>
      )}
    </div>
  );
}