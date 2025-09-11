/**
 * YAMLRenderer Component
 * Renders YAML-based study plans and recommendations with beautiful UI
 */

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  ChevronRight, 
  ChevronDown, 
  PlayCircle, 
  BookOpen, 
  Target, 
  Clock, 
  Award,
  CheckCircle,
  AlertCircle,
  TrendingUp,
  Brain,
  Video,
  FileText,
  Link as LinkIcon,
  Calendar,
  BarChart,
  Lightbulb,
  Star,
  Flag,
  Zap
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from './card';
import { Badge } from './badge';
import { Button } from './button';
import { Progress } from './progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './tabs';
import { cn } from '@/lib/utils';
import { logger } from '@/lib/logger';

// Types
interface VideoRecommendation {
  video_id: string;
  title: string;
  channel: string;
  duration: string;
  thumbnail: string;
  url: string;
  relevance_score: number;
  icfes_alignment: number;
  topics_covered: string[];
  difficulty: 'basico' | 'intermedio' | 'avanzado';
  watch_time?: string;
  priority: 'alta' | 'media' | 'baja';
  ai_explanation: string;
}

interface StudyResource {
  type: 'video' | 'article' | 'exercise' | 'simulation';
  title: string;
  url?: string;
  duration?: string;
  difficulty?: string;
  completed?: boolean;
}

interface WeeklyGoal {
  week: number;
  focus_areas: string[];
  target_score: number;
  study_hours: number;
  practice_problems: number;
  resources: StudyResource[];
  milestones: string[];
}

interface SubjectRecommendation {
  subject: string;
  current_level: number;
  target_level: number;
  improvement_needed: number;
  priority: 'critical' | 'high' | 'medium' | 'low';
  weak_topics: string[];
  strong_topics: string[];
  video_recommendations: VideoRecommendation[];
  study_plan: {
    total_weeks: number;
    hours_per_week: number;
    weekly_goals: WeeklyGoal[];
  };
  learning_path: {
    current_stage: string;
    next_steps: string[];
    estimated_completion: string;
  };
}

interface YAMLData {
  student_id: string;
  generated_at: string;
  overall_analysis: {
    current_score: number;
    predicted_score: number;
    percentile: number;
    strengths: string[];
    weaknesses: string[];
    study_time_recommendation: number;
  };
  recommendations_by_subject: SubjectRecommendation[];
  personalized_strategy: {
    learning_style: string;
    optimal_study_times: string[];
    recommended_techniques: string[];
    motivation_tips: string[];
  };
  next_actions: {
    immediate: string[];
    this_week: string[];
    this_month: string[];
  };
}

interface YAMLRendererProps {
  yamlData: YAMLData | string;
  onVideoClick?: (video: VideoRecommendation) => void;
  onResourceComplete?: (resource: StudyResource) => void;
  className?: string;
}

// Utility functions
const parseYAMLData = (data: YAMLData | string): YAMLData | null => {
  try {
    if (typeof data === 'string') {
      // In production, you'd parse YAML string here
      // For now, assuming it's already parsed
      return JSON.parse(data) as YAMLData;
    }
    return data;
  } catch (error) {
    logger.error('Failed to parse YAML data', error);
    return null;
  }
};

const getDifficultyColor = (difficulty: string) => {
  switch (difficulty?.toLowerCase()) {
    case 'basico': return 'bg-green-100 text-green-800';
    case 'intermedio': return 'bg-yellow-100 text-yellow-800';
    case 'avanzado': return 'bg-red-100 text-red-800';
    default: return 'bg-gray-100 text-gray-800';
  }
};

const getPriorityColor = (priority: string) => {
  switch (priority?.toLowerCase()) {
    case 'critical':
    case 'alta': return 'bg-red-100 text-red-800 border-red-300';
    case 'high':
    case 'media': return 'bg-orange-100 text-orange-800 border-orange-300';
    case 'medium':
    case 'baja': return 'bg-yellow-100 text-yellow-800 border-yellow-300';
    case 'low': return 'bg-green-100 text-green-800 border-green-300';
    default: return 'bg-gray-100 text-gray-800 border-gray-300';
  }
};

const getIconForResourceType = (type: string) => {
  switch (type) {
    case 'video': return Video;
    case 'article': return FileText;
    case 'exercise': return Brain;
    case 'simulation': return Zap;
    default: return BookOpen;
  }
};

// Components
const VideoCard: React.FC<{
  video: VideoRecommendation;
  onClick?: () => void;
}> = ({ video, onClick }) => {
  const [imageError, setImageError] = useState(false);

  return (
    <motion.div
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
      className="cursor-pointer"
      onClick={onClick}
    >
      <Card className="overflow-hidden hover:shadow-lg transition-shadow">
        <div className="aspect-video relative bg-gray-100">
          {!imageError ? (
            <img
              src={video.thumbnail}
              alt={video.title}
              className="w-full h-full object-cover"
              onError={() => setImageError(true)}
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center">
              <Video className="w-12 h-12 text-gray-400" />
            </div>
          )}
          <div className="absolute inset-0 bg-black bg-opacity-0 hover:bg-opacity-30 transition-opacity flex items-center justify-center">
            <PlayCircle className="w-16 h-16 text-white opacity-0 hover:opacity-100 transition-opacity" />
          </div>
          <Badge className="absolute top-2 right-2 bg-black bg-opacity-70 text-white">
            {video.duration}
          </Badge>
        </div>
        <CardContent className="p-4">
          <h4 className="font-semibold text-sm line-clamp-2 mb-2">{video.title}</h4>
          <p className="text-xs text-gray-600 mb-2">{video.channel}</p>
          
          <div className="flex items-center gap-2 mb-3">
            <Badge className={getDifficultyColor(video.difficulty)}>
              {video.difficulty}
            </Badge>
            <Badge variant="outline" className="text-xs">
              {Math.round(video.relevance_score * 100)}% relevante
            </Badge>
          </div>
          
          {video.ai_explanation && (
            <div className="p-2 bg-blue-50 rounded-lg border border-blue-200">
              <div className="flex items-start gap-2">
                <Lightbulb className="w-4 h-4 text-blue-600 mt-0.5" />
                <p className="text-xs text-blue-900">{video.ai_explanation}</p>
              </div>
            </div>
          )}
          
          <div className="mt-3 flex flex-wrap gap-1">
            {video.topics_covered?.slice(0, 3).map((topic, i) => (
              <span key={i} className="text-xs bg-gray-100 px-2 py-1 rounded">
                {topic}
              </span>
            ))}
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
};

const SubjectSection: React.FC<{
  subject: SubjectRecommendation;
  onVideoClick?: (video: VideoRecommendation) => void;
}> = ({ subject, onVideoClick }) => {
  const [expanded, setExpanded] = useState(false);
  const [activeWeek, setActiveWeek] = useState(0);

  const progressPercentage = (subject.current_level / subject.target_level) * 100;

  return (
    <Card className={cn("mb-6 border-2", getPriorityColor(subject.priority))}>
      <CardHeader 
        className="cursor-pointer"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            {expanded ? <ChevronDown /> : <ChevronRight />}
            <CardTitle className="text-xl">{subject.subject}</CardTitle>
            <Badge className={getPriorityColor(subject.priority)}>
              Prioridad: {subject.priority}
            </Badge>
          </div>
          <div className="flex items-center gap-4">
            <div className="text-right">
              <p className="text-sm text-gray-600">Nivel actual</p>
              <p className="text-2xl font-bold">{subject.current_level}</p>
            </div>
            <div className="text-right">
              <p className="text-sm text-gray-600">Objetivo</p>
              <p className="text-2xl font-bold text-green-600">{subject.target_level}</p>
            </div>
          </div>
        </div>
        
        <Progress value={progressPercentage} className="mt-4" />
        <p className="text-sm text-gray-600 mt-2">
          Mejora necesaria: +{subject.improvement_needed} puntos
        </p>
      </CardHeader>

      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.3 }}
          >
            <CardContent>
              <Tabs defaultValue="videos" className="w-full">
                <TabsList className="grid w-full grid-cols-4">
                  <TabsTrigger value="videos">Videos</TabsTrigger>
                  <TabsTrigger value="plan">Plan de Estudio</TabsTrigger>
                  <TabsTrigger value="analysis">Análisis</TabsTrigger>
                  <TabsTrigger value="path">Ruta</TabsTrigger>
                </TabsList>

                <TabsContent value="videos" className="mt-4">
                  <h3 className="font-semibold mb-3 flex items-center gap-2">
                    <Video className="w-5 h-5" />
                    Videos Recomendados
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {subject.video_recommendations?.map((video, idx) => (
                      <VideoCard
                        key={idx}
                        video={video}
                        onClick={() => onVideoClick?.(video)}
                      />
                    ))}
                  </div>
                </TabsContent>

                <TabsContent value="plan" className="mt-4">
                  <div className="space-y-4">
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="font-semibold flex items-center gap-2">
                        <Calendar className="w-5 h-5" />
                        Plan Semanal
                      </h3>
                      <Badge>
                        {subject.study_plan?.total_weeks} semanas • 
                        {subject.study_plan?.hours_per_week}h/semana
                      </Badge>
                    </div>

                    <div className="flex gap-2 mb-4 overflow-x-auto">
                      {subject.study_plan?.weekly_goals?.map((_, idx) => (
                        <Button
                          key={idx}
                          variant={activeWeek === idx ? "default" : "outline"}
                          size="sm"
                          onClick={() => setActiveWeek(idx)}
                        >
                          Semana {idx + 1}
                        </Button>
                      ))}
                    </div>

                    {subject.study_plan?.weekly_goals?.[activeWeek] && (
                      <Card>
                        <CardContent className="pt-6">
                          <div className="space-y-4">
                            <div>
                              <h4 className="font-semibold mb-2 flex items-center gap-2">
                                <Target className="w-4 h-4" />
                                Áreas de Enfoque
                              </h4>
                              <div className="flex flex-wrap gap-2">
                                {subject.study_plan.weekly_goals[activeWeek].focus_areas?.map((area, i) => (
                                  <Badge key={i} variant="secondary">{area}</Badge>
                                ))}
                              </div>
                            </div>

                            <div className="grid grid-cols-3 gap-4">
                              <div className="text-center p-3 bg-blue-50 rounded-lg">
                                <p className="text-2xl font-bold text-blue-600">
                                  {subject.study_plan.weekly_goals[activeWeek].target_score}
                                </p>
                                <p className="text-xs text-gray-600">Puntaje objetivo</p>
                              </div>
                              <div className="text-center p-3 bg-green-50 rounded-lg">
                                <p className="text-2xl font-bold text-green-600">
                                  {subject.study_plan.weekly_goals[activeWeek].study_hours}h
                                </p>
                                <p className="text-xs text-gray-600">Horas de estudio</p>
                              </div>
                              <div className="text-center p-3 bg-purple-50 rounded-lg">
                                <p className="text-2xl font-bold text-purple-600">
                                  {subject.study_plan.weekly_goals[activeWeek].practice_problems}
                                </p>
                                <p className="text-xs text-gray-600">Problemas</p>
                              </div>
                            </div>

                            <div>
                              <h4 className="font-semibold mb-2 flex items-center gap-2">
                                <BookOpen className="w-4 h-4" />
                                Recursos
                              </h4>
                              <div className="space-y-2">
                                {subject.study_plan.weekly_goals[activeWeek].resources?.map((resource, i) => {
                                  const Icon = getIconForResourceType(resource.type);
                                  return (
                                    <div key={i} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                                      <div className="flex items-center gap-3">
                                        <Icon className="w-5 h-5 text-gray-600" />
                                        <div>
                                          <p className="font-medium text-sm">{resource.title}</p>
                                          <p className="text-xs text-gray-600">
                                            {resource.duration} • {resource.difficulty}
                                          </p>
                                        </div>
                                      </div>
                                      {resource.completed ? (
                                        <CheckCircle className="w-5 h-5 text-green-600" />
                                      ) : (
                                        <Button size="sm" variant="ghost">
                                          Iniciar
                                        </Button>
                                      )}
                                    </div>
                                  );
                                })}
                              </div>
                            </div>

                            <div>
                              <h4 className="font-semibold mb-2 flex items-center gap-2">
                                <Flag className="w-4 h-4" />
                                Hitos
                              </h4>
                              <ul className="space-y-1">
                                {subject.study_plan.weekly_goals[activeWeek].milestones?.map((milestone, i) => (
                                  <li key={i} className="flex items-start gap-2">
                                    <CheckCircle className="w-4 h-4 text-gray-400 mt-0.5" />
                                    <span className="text-sm">{milestone}</span>
                                  </li>
                                ))}
                              </ul>
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    )}
                  </div>
                </TabsContent>

                <TabsContent value="analysis" className="mt-4">
                  <div className="space-y-4">
                    <div>
                      <h3 className="font-semibold mb-3 flex items-center gap-2">
                        <TrendingUp className="w-5 h-5 text-green-600" />
                        Fortalezas
                      </h3>
                      <div className="flex flex-wrap gap-2">
                        {subject.strong_topics?.map((topic, i) => (
                          <Badge key={i} className="bg-green-100 text-green-800">
                            {topic}
                          </Badge>
                        ))}
                      </div>
                    </div>

                    <div>
                      <h3 className="font-semibold mb-3 flex items-center gap-2">
                        <AlertCircle className="w-5 h-5 text-red-600" />
                        Áreas de Mejora
                      </h3>
                      <div className="flex flex-wrap gap-2">
                        {subject.weak_topics?.map((topic, i) => (
                          <Badge key={i} className="bg-red-100 text-red-800">
                            {topic}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  </div>
                </TabsContent>

                <TabsContent value="path" className="mt-4">
                  <div className="space-y-4">
                    <Card className="bg-gradient-to-r from-blue-50 to-purple-50">
                      <CardContent className="pt-6">
                        <h3 className="font-semibold mb-2 flex items-center gap-2">
                          <Brain className="w-5 h-5" />
                          Etapa Actual
                        </h3>
                        <p className="text-lg font-medium text-blue-900">
                          {subject.learning_path?.current_stage}
                        </p>
                      </CardContent>
                    </Card>

                    <div>
                      <h3 className="font-semibold mb-3 flex items-center gap-2">
                        <Target className="w-5 h-5" />
                        Próximos Pasos
                      </h3>
                      <div className="space-y-2">
                        {subject.learning_path?.next_steps?.map((step, i) => (
                          <div key={i} className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
                            <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center text-sm font-bold text-blue-600">
                              {i + 1}
                            </div>
                            <p className="text-sm">{step}</p>
                          </div>
                        ))}
                      </div>
                    </div>

                    <Card className="bg-green-50 border-green-200">
                      <CardContent className="pt-6">
                        <div className="flex items-center justify-between">
                          <div>
                            <p className="text-sm text-gray-600">Fecha estimada de completación</p>
                            <p className="text-lg font-semibold text-green-800">
                              {subject.learning_path?.estimated_completion}
                            </p>
                          </div>
                          <Award className="w-8 h-8 text-green-600" />
                        </div>
                      </CardContent>
                    </Card>
                  </div>
                </TabsContent>
              </Tabs>
            </CardContent>
          </motion.div>
        )}
      </AnimatePresence>
    </Card>
  );
};

const OverallAnalysis: React.FC<{ analysis: YAMLData['overall_analysis'] }> = ({ analysis }) => {
  return (
    <Card className="mb-6 bg-gradient-to-r from-blue-500 to-purple-600 text-white">
      <CardContent className="pt-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="text-center">
            <p className="text-sm opacity-90">Puntaje Actual</p>
            <p className="text-3xl font-bold">{analysis.current_score}</p>
          </div>
          <div className="text-center">
            <p className="text-sm opacity-90">Predicción</p>
            <p className="text-3xl font-bold">{analysis.predicted_score}</p>
            <p className="text-xs opacity-80">
              +{analysis.predicted_score - analysis.current_score} puntos
            </p>
          </div>
          <div className="text-center">
            <p className="text-sm opacity-90">Percentil</p>
            <p className="text-3xl font-bold">{analysis.percentile}%</p>
          </div>
          <div className="text-center">
            <p className="text-sm opacity-90">Tiempo Recomendado</p>
            <p className="text-3xl font-bold">{analysis.study_time_recommendation}h</p>
            <p className="text-xs opacity-80">por semana</p>
          </div>
        </div>

        <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="bg-white bg-opacity-10 rounded-lg p-4">
            <h3 className="font-semibold mb-2 flex items-center gap-2">
              <Star className="w-5 h-5" />
              Fortalezas
            </h3>
            <ul className="space-y-1">
              {analysis.strengths?.map((strength, i) => (
                <li key={i} className="text-sm opacity-90">• {strength}</li>
              ))}
            </ul>
          </div>
          <div className="bg-white bg-opacity-10 rounded-lg p-4">
            <h3 className="font-semibold mb-2 flex items-center gap-2">
              <AlertCircle className="w-5 h-5" />
              Áreas de Mejora
            </h3>
            <ul className="space-y-1">
              {analysis.weaknesses?.map((weakness, i) => (
                <li key={i} className="text-sm opacity-90">• {weakness}</li>
              ))}
            </ul>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

// Main Component
export const YAMLRenderer: React.FC<YAMLRendererProps> = ({
  yamlData,
  onVideoClick,
  onResourceComplete,
  className
}) => {
  const [data, setData] = useState<YAMLData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const parsed = parseYAMLData(yamlData);
    if (parsed) {
      setData(parsed);
      setError(null);
    } else {
      setError('Failed to parse YAML data');
    }
    setLoading(false);
  }, [yamlData]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <Card className="bg-red-50 border-red-200">
        <CardContent className="pt-6">
          <div className="flex items-center gap-3">
            <AlertCircle className="w-6 h-6 text-red-600" />
            <p className="text-red-800">Error loading recommendations: {error}</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className={cn("space-y-6", className)}>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold">Plan de Estudio Personalizado</h1>
          <p className="text-gray-600">
            Generado el {new Date(data.generated_at).toLocaleDateString('es-ES')}
          </p>
        </div>
        <Button variant="outline" size="sm">
          <BarChart className="w-4 h-4 mr-2" />
          Ver Progreso Completo
        </Button>
      </div>

      {/* Overall Analysis */}
      <OverallAnalysis analysis={data.overall_analysis} />

      {/* Next Actions */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Zap className="w-5 h-5 text-yellow-500" />
            Próximas Acciones
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <h3 className="font-semibold text-sm mb-2 text-red-600">Inmediato</h3>
              <ul className="space-y-1">
                {data.next_actions?.immediate?.map((action, i) => (
                  <li key={i} className="text-sm flex items-start gap-2">
                    <CheckCircle className="w-4 h-4 text-gray-400 mt-0.5" />
                    <span>{action}</span>
                  </li>
                ))}
              </ul>
            </div>
            <div>
              <h3 className="font-semibold text-sm mb-2 text-orange-600">Esta Semana</h3>
              <ul className="space-y-1">
                {data.next_actions?.this_week?.map((action, i) => (
                  <li key={i} className="text-sm flex items-start gap-2">
                    <CheckCircle className="w-4 h-4 text-gray-400 mt-0.5" />
                    <span>{action}</span>
                  </li>
                ))}
              </ul>
            </div>
            <div>
              <h3 className="font-semibold text-sm mb-2 text-blue-600">Este Mes</h3>
              <ul className="space-y-1">
                {data.next_actions?.this_month?.map((action, i) => (
                  <li key={i} className="text-sm flex items-start gap-2">
                    <CheckCircle className="w-4 h-4 text-gray-400 mt-0.5" />
                    <span>{action}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Personalized Strategy */}
      <Card className="bg-gradient-to-r from-purple-50 to-pink-50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Brain className="w-5 h-5 text-purple-600" />
            Estrategia Personalizada
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h3 className="font-semibold text-sm mb-2">Estilo de Aprendizaje</h3>
              <Badge className="mb-3">{data.personalized_strategy?.learning_style}</Badge>
              
              <h3 className="font-semibold text-sm mb-2 mt-4">Horarios Óptimos</h3>
              <div className="flex flex-wrap gap-2">
                {data.personalized_strategy?.optimal_study_times?.map((time, i) => (
                  <Badge key={i} variant="secondary">
                    <Clock className="w-3 h-3 mr-1" />
                    {time}
                  </Badge>
                ))}
              </div>
            </div>
            
            <div>
              <h3 className="font-semibold text-sm mb-2">Técnicas Recomendadas</h3>
              <ul className="space-y-1 mb-4">
                {data.personalized_strategy?.recommended_techniques?.map((technique, i) => (
                  <li key={i} className="text-sm">• {technique}</li>
                ))}
              </ul>
              
              <h3 className="font-semibold text-sm mb-2">Tips de Motivación</h3>
              <ul className="space-y-1">
                {data.personalized_strategy?.motivation_tips?.map((tip, i) => (
                  <li key={i} className="text-sm">• {tip}</li>
                ))}
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Subject Recommendations */}
      <div>
        <h2 className="text-2xl font-bold mb-4">Recomendaciones por Materia</h2>
        {data.recommendations_by_subject?.map((subject, idx) => (
          <SubjectSection
            key={idx}
            subject={subject}
            onVideoClick={onVideoClick}
          />
        ))}
      </div>
    </div>
  );
};

export default YAMLRenderer;