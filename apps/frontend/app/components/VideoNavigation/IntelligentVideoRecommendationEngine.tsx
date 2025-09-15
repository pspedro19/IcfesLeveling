'use client';

import { useState, useEffect, useCallback, useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Slider } from '@/components/ui/slider';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { 
  Sparkles,
  Brain,
  Target,
  TrendingUp,
  Filter,
  Search,
  RefreshCw,
  Settings,
  Play,
  Clock,
  Star,
  Eye,
  BookOpen,
  Zap,
  Award,
  AlertTriangle,
  CheckCircle,
  BarChart3,
  PieChart,
  Activity,
  Layers,
  Sliders,
  Shuffle,
  SortAsc,
  SortDesc,
  ThumbsUp,
  ThumbsDown,
  Lightbulb,
  GraduationCap,
  Users,
  Calendar,
  MapPin,
  Compass,
  Flame,
  Shield,
  Rocket
} from 'lucide-react';

interface VideoRecommendation {
  video_id: number;
  youtube_id: string;
  title: string;
  description?: string;
  url: string;
  embed_url: string;
  duration_seconds?: number;
  channel?: string;
  thumbnail_url?: string;
  subject_id?: number;
  topic_id?: number;
  area_evaluada?: string;
  tema_principal?: string;
  nivel?: string;
  recommendation_type: 'error_remediation' | 'skill_building' | 'concept_review' | 'direct_practice' | 'exam_prep' | 'advanced_topics';
  confidence_level: 'high' | 'medium' | 'low';
  scores: {
    total_score: number;
    semantic_similarity?: number;
    difficulty_match?: number;
    exact_match?: number;
    popularity?: number;
    freshness?: number;
    engagement?: number;
    success_rate?: number;
  };
  learning_objectives: string[];
  estimated_study_time: number;
  quality_score: number;
  relevance_score: number;
  personalization_score: number;
  trending_score: number;
  difficulty_level: number; // 1-10
  prerequisite_concepts: string[];
  next_concepts: string[];
  similar_videos: number[];
  engagement_metrics: {
    views: number;
    likes: number;
    comments: number;
    completion_rate: number;
    student_feedback: number;
  };
  ai_insights: {
    learning_path_position: 'beginner' | 'intermediate' | 'advanced' | 'expert';
    concept_density: 'low' | 'medium' | 'high';
    interaction_style: 'theoretical' | 'practical' | 'mixed';
    prerequisite_coverage: number;
    skill_gap_alignment: number;
  };
}

interface UserLearningProfile {
  current_level: {
    mathematics: number;
    language: number;
    science: number;
    social_studies: number;
    english: number;
  };
  learning_preferences: {
    preferred_duration: 'short' | 'medium' | 'long'; // <10min, 10-20min, >20min
    learning_style: 'visual' | 'auditory' | 'kinesthetic' | 'mixed';
    difficulty_preference: 'easy' | 'moderate' | 'challenging';
    content_type: 'theory' | 'examples' | 'exercises' | 'mixed';
    pace_preference: 'slow' | 'normal' | 'fast';
  };
  weaknesses: string[];
  strengths: string[];
  recent_failures: string[];
  study_goals: string[];
  time_availability: number; // minutes per day
}

interface FilterCriteria {
  subjects: string[];
  topics: string[];
  difficulty_range: [number, number];
  duration_range: [number, number];
  quality_threshold: number;
  relevance_threshold: number;
  recommendation_types: string[];
  confidence_levels: string[];
  learning_objectives: string[];
  exclude_watched: boolean;
  only_bookmarked: boolean;
  only_trending: boolean;
  language_preference: string;
  recency_weight: number;
}

interface IntelligentVideoRecommendationEngineProps {
  userId: string;
  currentContext?: {
    subject_id?: number;
    topic_id?: number;
    question_id?: string;
    session_id?: string;
    study_goal?: string;
  };
  userProfile?: UserLearningProfile;
  onVideoSelect?: (video: VideoRecommendation) => void;
  onFeedback?: (videoId: number, feedback: 'helpful' | 'not_helpful', details?: string) => void;
  maxRecommendations?: number;
  enableAIInsights?: boolean;
  enableRealTimeUpdates?: boolean;
  enablePersonalization?: boolean;
  className?: string;
}

const defaultFilters: FilterCriteria = {
  subjects: [],
  topics: [],
  difficulty_range: [1, 10],
  duration_range: [0, 3600],
  quality_threshold: 0.5,
  relevance_threshold: 0.5,
  recommendation_types: [],
  confidence_levels: [],
  learning_objectives: [],
  exclude_watched: false,
  only_bookmarked: false,
  only_trending: false,
  language_preference: 'es',
  recency_weight: 0.5
};

export default function IntelligentVideoRecommendationEngine({
  userId,
  currentContext,
  userProfile,
  onVideoSelect,
  onFeedback,
  maxRecommendations = 20,
  enableAIInsights = true,
  enableRealTimeUpdates = true,
  enablePersonalization = true,
  className = ''
}: IntelligentVideoRecommendationEngineProps) {
  // State management
  const [recommendations, setRecommendations] = useState<VideoRecommendation[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeEngine, setActiveEngine] = useState<'ai' | 'similarity' | 'popularity' | 'personalized'>('ai');
  
  // Filter and search state
  const [filters, setFilters] = useState<FilterCriteria>(defaultFilters);
  const [searchQuery, setSearchQuery] = useState('');
  const [sortBy, setSortBy] = useState<'relevance' | 'quality' | 'trending' | 'difficulty' | 'duration'>('relevance');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  
  // UI state
  const [showAdvancedFilters, setShowAdvancedFilters] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [viewMode, setViewMode] = useState<'card' | 'compact' | 'detailed'>('card');
  const [showAIInsights, setShowAIInsights] = useState(enableAIInsights);
  
  // Analytics state
  const [enginePerformance, setEnginePerformance] = useState<{
    ai: { accuracy: number; speed: number; satisfaction: number };
    similarity: { accuracy: number; speed: number; satisfaction: number };
    popularity: { accuracy: number; speed: number; satisfaction: number };
    personalized: { accuracy: number; speed: number; satisfaction: number };
  }>({
    ai: { accuracy: 0.85, speed: 1200, satisfaction: 4.2 },
    similarity: { accuracy: 0.72, speed: 800, satisfaction: 3.8 },
    popularity: { accuracy: 0.68, speed: 400, satisfaction: 3.5 },
    personalized: { accuracy: 0.91, speed: 1800, satisfaction: 4.6 }
  });

  // Load recommendations with different engines
  const loadRecommendations = useCallback(async (engine: typeof activeEngine) => {
    try {
      setLoading(true);
      setError(null);
      
      const payload = {
        user_id: userId,
        engine_type: engine,
        context: currentContext,
        user_profile: userProfile,
        filters: filters,
        max_results: maxRecommendations,
        enable_ai_insights: showAIInsights,
        personalization_enabled: enablePersonalization
      };

      const response = await fetch('/api/v1/video-recommendations/intelligent', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        throw new Error(`Failed to load recommendations: ${response.statusText}`);
      }

      const data = await response.json();
      setRecommendations(data.recommendations || []);
      
      // Update engine performance metrics
      if (data.performance_metrics) {
        setEnginePerformance(prev => ({
          ...prev,
          [engine]: data.performance_metrics
        }));
      }

    } catch (err) {
      console.error('Error loading recommendations:', err);
      setError(err instanceof Error ? err.message : 'Error al cargar recomendaciones');
    } finally {
      setLoading(false);
    }
  }, [userId, currentContext, userProfile, filters, maxRecommendations, showAIInsights, enablePersonalization]);

  // Initial load and reload on dependency changes
  useEffect(() => {
    loadRecommendations(activeEngine);
  }, [loadRecommendations, activeEngine]);

  // Real-time updates
  useEffect(() => {
    if (!enableRealTimeUpdates) return;

    const interval = setInterval(() => {
      loadRecommendations(activeEngine);
    }, 300000); // Update every 5 minutes

    return () => clearInterval(interval);
  }, [enableRealTimeUpdates, loadRecommendations, activeEngine]);

  // Filter and sort recommendations
  const filteredAndSortedRecommendations = useMemo(() => {
    let filtered = recommendations.filter(video => {
      // Search query filter
      if (searchQuery) {
        const query = searchQuery.toLowerCase();
        const matchesSearch = 
          video.title.toLowerCase().includes(query) ||
          video.description?.toLowerCase().includes(query) ||
          video.channel?.toLowerCase().includes(query) ||
          video.learning_objectives.some(obj => obj.toLowerCase().includes(query)) ||
          video.area_evaluada?.toLowerCase().includes(query);
        
        if (!matchesSearch) return false;
      }

      // Category filter
      if (selectedCategory !== 'all' && video.recommendation_type !== selectedCategory) {
        return false;
      }

      // Advanced filters
      if (filters.subjects.length > 0 && filters.subjects.includes(video.area_evaluada || '')) {
        return false;
      }

      if (video.difficulty_level < filters.difficulty_range[0] || 
          video.difficulty_level > filters.difficulty_range[1]) {
        return false;
      }

      if ((video.duration_seconds || 0) < filters.duration_range[0] || 
          (video.duration_seconds || 0) > filters.duration_range[1]) {
        return false;
      }

      if (video.quality_score < filters.quality_threshold) {
        return false;
      }

      if (video.relevance_score < filters.relevance_threshold) {
        return false;
      }

      if (filters.recommendation_types.length > 0 && 
          !filters.recommendation_types.includes(video.recommendation_type)) {
        return false;
      }

      if (filters.confidence_levels.length > 0 && 
          !filters.confidence_levels.includes(video.confidence_level)) {
        return false;
      }

      return true;
    });

    // Sort recommendations
    filtered.sort((a, b) => {
      let comparison = 0;

      switch (sortBy) {
        case 'relevance':
          comparison = a.relevance_score - b.relevance_score;
          break;
        case 'quality':
          comparison = a.quality_score - b.quality_score;
          break;
        case 'trending':
          comparison = a.trending_score - b.trending_score;
          break;
        case 'difficulty':
          comparison = a.difficulty_level - b.difficulty_level;
          break;
        case 'duration':
          comparison = (a.duration_seconds || 0) - (b.duration_seconds || 0);
          break;
        default:
          comparison = a.scores.total_score - b.scores.total_score;
      }

      return sortOrder === 'desc' ? -comparison : comparison;
    });

    return filtered;
  }, [recommendations, searchQuery, selectedCategory, filters, sortBy, sortOrder]);

  const handleVideoClick = (video: VideoRecommendation) => {
    // Track interaction
    trackInteraction(video.video_id, 'click');
    
    if (onVideoSelect) {
      onVideoSelect(video);
    }
  };

  const handleFeedback = async (videoId: number, feedback: 'helpful' | 'not_helpful', details?: string) => {
    try {
      await fetch('/api/v1/video-recommendations/feedback', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          video_id: videoId,
          user_id: userId,
          feedback,
          details,
          engine_used: activeEngine,
          context: currentContext
        })
      });

      if (onFeedback) {
        onFeedback(videoId, feedback, details);
      }
    } catch (err) {
      console.error('Error submitting feedback:', err);
    }
  };

  const trackInteraction = async (videoId: number, action: string) => {
    try {
      await fetch('/api/v1/video-recommendations/track-interaction', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          video_id: videoId,
          user_id: userId,
          action,
          engine_used: activeEngine,
          context: currentContext,
          timestamp: new Date().toISOString()
        })
      });
    } catch (err) {
      console.error('Error tracking interaction:', err);
    }
  };

  const formatDuration = (seconds: number): string => {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
  };

  const getEngineIcon = (engine: typeof activeEngine) => {
    switch (engine) {
      case 'ai': return <Brain className="w-4 h-4" />;
      case 'similarity': return <Target className="w-4 h-4" />;
      case 'popularity': return <TrendingUp className="w-4 h-4" />;
      case 'personalized': return <Users className="w-4 h-4" />;
      default: return <Sparkles className="w-4 h-4" />;
    }
  };

  const getRecommendationTypeIcon = (type: string) => {
    switch (type) {
      case 'error_remediation': return <Shield className="w-4 h-4 text-red-500" />;
      case 'skill_building': return <TrendingUp className="w-4 h-4 text-blue-500" />;
      case 'concept_review': return <BookOpen className="w-4 h-4 text-green-500" />;
      case 'direct_practice': return <Target className="w-4 h-4 text-purple-500" />;
      case 'exam_prep': return <GraduationCap className="w-4 h-4 text-orange-500" />;
      case 'advanced_topics': return <Rocket className="w-4 h-4 text-pink-500" />;
      default: return <Play className="w-4 h-4" />;
    }
  };

  const getConfidenceColor = (level: string): string => {
    switch (level) {
      case 'high': return 'bg-green-500';
      case 'medium': return 'bg-yellow-500';
      case 'low': return 'bg-red-500';
      default: return 'bg-gray-500';
    }
  };

  const getDifficultyLabel = (level: number): string => {
    if (level <= 3) return 'Básico';
    if (level <= 6) return 'Intermedio';
    if (level <= 8) return 'Avanzado';
    return 'Experto';
  };

  const renderVideoCard = (video: VideoRecommendation) => (
    <Card 
      key={video.video_id}
      className="group cursor-pointer hover:shadow-lg transition-all duration-300 hover:scale-[1.02]"
      onClick={() => handleVideoClick(video)}
    >
      <CardContent className="p-4">
        <div className={viewMode === 'compact' ? 'flex gap-3' : 'space-y-3'}>
          {/* Thumbnail */}
          <div className={`relative ${viewMode === 'compact' ? 'w-32 h-20 flex-shrink-0' : 'w-full h-48'}`}>
            <img 
              src={video.thumbnail_url || `https://img.youtube.com/vi/${video.youtube_id}/maxresdefault.jpg`}
              alt={video.title}
              className="w-full h-full object-cover rounded"
              onError={(e) => {
                const target = e.target as HTMLImageElement;
                target.src = `https://img.youtube.com/vi/${video.youtube_id}/hqdefault.jpg`;
              }}
            />
            
            {/* Overlays */}
            <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent rounded" />
            
            {/* Play button */}
            <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
              <div className="bg-blue-600 text-white rounded-full p-3">
                <Play className="w-6 h-6 fill-current" />
              </div>
            </div>
            
            {/* Duration */}
            {video.duration_seconds && (
              <Badge className="absolute bottom-2 right-2 bg-black/80 text-white text-xs">
                <Clock className="w-3 h-3 mr-1" />
                {formatDuration(video.duration_seconds)}
              </Badge>
            )}
            
            {/* AI Insights indicator */}
            {showAIInsights && video.ai_insights && (
              <Badge className="absolute top-2 left-2 bg-purple-600 text-white text-xs">
                <Sparkles className="w-3 h-3 mr-1" />
                AI
              </Badge>
            )}
            
            {/* Trending indicator */}
            {video.trending_score > 0.8 && (
              <div className="absolute top-2 right-2">
                <Flame className="w-4 h-4 text-orange-500" />
              </div>
            )}
          </div>
          
          {/* Video Info */}
          <div className="flex-1 space-y-2">
            <div className="flex items-start justify-between">
              <h3 className="font-semibold text-sm line-clamp-2 group-hover:text-blue-600">
                {video.title}
              </h3>
              
              <Badge className={`${getConfidenceColor(video.confidence_level)} text-white ml-2`}>
                {video.confidence_level}
              </Badge>
            </div>
            
            <div className="flex items-center gap-2 text-xs text-gray-600">
              <span>{video.channel}</span>
              {video.area_evaluada && (
                <>
                  <span>•</span>
                  <span>{video.area_evaluada}</span>
                </>
              )}
            </div>
            
            {/* Recommendation type and difficulty */}
            <div className="flex items-center gap-2">
              <Badge variant="outline" className="text-xs">
                {getRecommendationTypeIcon(video.recommendation_type)}
                <span className="ml-1 capitalize">{video.recommendation_type.replace('_', ' ')}</span>
              </Badge>
              
              <Badge variant="secondary" className="text-xs">
                <BarChart3 className="w-3 h-3 mr-1" />
                {getDifficultyLabel(video.difficulty_level)}
              </Badge>
            </div>
            
            {/* Scores */}
            <div className="grid grid-cols-3 gap-2 text-xs">
              <div className="flex items-center gap-1">
                <Star className="w-3 h-3 text-yellow-500" />
                <span>Calidad: {Math.round(video.quality_score * 100)}%</span>
              </div>
              <div className="flex items-center gap-1">
                <Target className="w-3 h-3 text-blue-500" />
                <span>Relevancia: {Math.round(video.relevance_score * 100)}%</span>
              </div>
              <div className="flex items-center gap-1">
                <Activity className="w-3 h-3 text-green-500" />
                <span>Engage: {Math.round(video.engagement_metrics.completion_rate * 100)}%</span>
              </div>
            </div>
            
            {/* Learning objectives */}
            {video.learning_objectives.length > 0 && (
              <div className="space-y-1">
                <div className="text-xs font-medium text-gray-700">Objetivos de aprendizaje:</div>
                <div className="flex flex-wrap gap-1">
                  {video.learning_objectives.slice(0, 3).map((objective, index) => (
                    <Badge key={index} variant="outline" className="text-xs">
                      <Lightbulb className="w-3 h-3 mr-1" />
                      {objective}
                    </Badge>
                  ))}
                  {video.learning_objectives.length > 3 && (
                    <Badge variant="outline" className="text-xs">
                      +{video.learning_objectives.length - 3} más
                    </Badge>
                  )}
                </div>
              </div>
            )}
            
            {/* AI Insights */}
            {showAIInsights && video.ai_insights && viewMode === 'detailed' && (
              <div className="bg-purple-50 p-2 rounded text-xs space-y-1">
                <div className="font-medium text-purple-800">Análisis IA:</div>
                <div className="grid grid-cols-2 gap-2">
                  <div>Posición: {video.ai_insights.learning_path_position}</div>
                  <div>Densidad: {video.ai_insights.concept_density}</div>
                  <div>Estilo: {video.ai_insights.interaction_style}</div>
                  <div>Prerrequisitos: {Math.round(video.ai_insights.prerequisite_coverage * 100)}%</div>
                </div>
              </div>
            )}
            
            {/* Actions */}
            <div className="flex items-center justify-between pt-2">
              <div className="flex items-center gap-1">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={(e) => {
                    e.stopPropagation();
                    handleFeedback(video.video_id, 'helpful');
                  }}
                  className="h-6 px-2"
                >
                  <ThumbsUp className="w-3 h-3" />
                </Button>
                
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={(e) => {
                    e.stopPropagation();
                    handleFeedback(video.video_id, 'not_helpful');
                  }}
                  className="h-6 px-2"
                >
                  <ThumbsDown className="w-3 h-3" />
                </Button>
              </div>
              
              <div className="text-xs text-gray-500">
                Tiempo estimado: {video.estimated_study_time}min
              </div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );

  return (
    <div className={`w-full space-y-6 ${className}`}>
      {error && (
        <Alert>
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Header with engine selection and controls */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <Brain className="w-5 h-5" />
              Motor de Recomendaciones Inteligente
              <Badge variant="secondary" className="ml-2">
                {filteredAndSortedRecommendations.length} videos
              </Badge>
            </CardTitle>
            
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => loadRecommendations(activeEngine)}
                disabled={loading}
              >
                <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
              </Button>
              
              <Dialog open={showAdvancedFilters} onOpenChange={setShowAdvancedFilters}>
                <DialogTrigger asChild>
                  <Button variant="outline" size="sm">
                    <Settings className="w-4 h-4 mr-1" />
                    Configurar
                  </Button>
                </DialogTrigger>
                <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
                  <DialogHeader>
                    <DialogTitle>Configuración Avanzada del Motor</DialogTitle>
                    <DialogDescription>
                      Personaliza los algoritmos y filtros para obtener las mejores recomendaciones.
                    </DialogDescription>
                  </DialogHeader>
                  
                  <Tabs defaultValue="engines" className="w-full">
                    <TabsList className="grid grid-cols-3 w-full">
                      <TabsTrigger value="engines">Motores</TabsTrigger>
                      <TabsTrigger value="filters">Filtros</TabsTrigger>
                      <TabsTrigger value="personalization">Personalización</TabsTrigger>
                    </TabsList>
                    
                    <TabsContent value="engines" className="space-y-4">
                      <div className="grid grid-cols-2 gap-4">
                        {Object.entries(enginePerformance).map(([engine, metrics]) => (
                          <Card 
                            key={engine}
                            className={`cursor-pointer transition-all ${activeEngine === engine ? 'ring-2 ring-blue-500' : ''}`}
                            onClick={() => setActiveEngine(engine as typeof activeEngine)}
                          >
                            <CardContent className="p-4">
                              <div className="flex items-center gap-3 mb-3">
                                {getEngineIcon(engine as typeof activeEngine)}
                                <div>
                                  <h4 className="font-semibold capitalize">{engine.replace('_', ' ')}</h4>
                                  <p className="text-xs text-gray-600">
                                    {engine === 'ai' && 'Análisis avanzado con IA'}
                                    {engine === 'similarity' && 'Basado en similaridad semántica'}
                                    {engine === 'popularity' && 'Basado en tendencias y popularidad'}
                                    {engine === 'personalized' && 'Personalizado por perfil de usuario'}
                                  </p>
                                </div>
                              </div>
                              
                              <div className="space-y-2 text-xs">
                                <div className="flex justify-between">
                                  <span>Precisión:</span>
                                  <span>{Math.round(metrics.accuracy * 100)}%</span>
                                </div>
                                <div className="flex justify-between">
                                  <span>Velocidad:</span>
                                  <span>{metrics.speed}ms</span>
                                </div>
                                <div className="flex justify-between">
                                  <span>Satisfacción:</span>
                                  <span>{metrics.satisfaction}/5</span>
                                </div>
                              </div>
                            </CardContent>
                          </Card>
                        ))}
                      </div>
                    </TabsContent>
                    
                    <TabsContent value="filters" className="space-y-4">
                      <div className="grid grid-cols-2 gap-4">
                        <div className="space-y-2">
                          <label className="text-sm font-medium">Rango de dificultad</label>
                          <Slider
                            value={filters.difficulty_range}
                            onValueChange={(value) => setFilters(prev => ({ ...prev, difficulty_range: value as [number, number] }))}
                            min={1}
                            max={10}
                            step={1}
                            className="w-full"
                          />
                          <div className="flex justify-between text-xs text-gray-600">
                            <span>{getDifficultyLabel(filters.difficulty_range[0])}</span>
                            <span>{getDifficultyLabel(filters.difficulty_range[1])}</span>
                          </div>
                        </div>
                        
                        <div className="space-y-2">
                          <label className="text-sm font-medium">Duración (minutos)</label>
                          <Slider
                            value={[filters.duration_range[0] / 60, filters.duration_range[1] / 60]}
                            onValueChange={(value) => setFilters(prev => ({ 
                              ...prev, 
                              duration_range: [value[0] * 60, value[1] * 60] 
                            }))}
                            min={0}
                            max={60}
                            step={1}
                            className="w-full"
                          />
                          <div className="flex justify-between text-xs text-gray-600">
                            <span>{Math.round(filters.duration_range[0] / 60)}min</span>
                            <span>{Math.round(filters.duration_range[1] / 60)}min</span>
                          </div>
                        </div>
                        
                        <div className="space-y-2">
                          <label className="text-sm font-medium">Umbral de calidad</label>
                          <Slider
                            value={[filters.quality_threshold]}
                            onValueChange={(value) => setFilters(prev => ({ ...prev, quality_threshold: value[0] }))}
                            min={0}
                            max={1}
                            step={0.1}
                            className="w-full"
                          />
                          <div className="text-center text-xs text-gray-600">
                            {Math.round(filters.quality_threshold * 100)}%
                          </div>
                        </div>
                        
                        <div className="space-y-2">
                          <label className="text-sm font-medium">Umbral de relevancia</label>
                          <Slider
                            value={[filters.relevance_threshold]}
                            onValueChange={(value) => setFilters(prev => ({ ...prev, relevance_threshold: value[0] }))}
                            min={0}
                            max={1}
                            step={0.1}
                            className="w-full"
                          />
                          <div className="text-center text-xs text-gray-600">
                            {Math.round(filters.relevance_threshold * 100)}%
                          </div>
                        </div>
                      </div>
                    </TabsContent>
                    
                    <TabsContent value="personalization" className="space-y-4">
                      <div className="grid grid-cols-2 gap-4">
                        <div className="space-y-3">
                          <div className="flex items-center space-x-2">
                            <input
                              type="checkbox"
                              id="ai-insights"
                              checked={showAIInsights}
                              onChange={(e) => setShowAIInsights(e.target.checked)}
                            />
                            <label htmlFor="ai-insights" className="text-sm font-medium">
                              Mostrar análisis IA
                            </label>
                          </div>
                          
                          <div className="flex items-center space-x-2">
                            <input
                              type="checkbox"
                              id="exclude-watched"
                              checked={filters.exclude_watched}
                              onChange={(e) => setFilters(prev => ({ ...prev, exclude_watched: e.target.checked }))}
                            />
                            <label htmlFor="exclude-watched" className="text-sm font-medium">
                              Excluir videos ya vistos
                            </label>
                          </div>
                          
                          <div className="flex items-center space-x-2">
                            <input
                              type="checkbox"
                              id="only-trending"
                              checked={filters.only_trending}
                              onChange={(e) => setFilters(prev => ({ ...prev, only_trending: e.target.checked }))}
                            />
                            <label htmlFor="only-trending" className="text-sm font-medium">
                              Solo contenido en tendencia
                            </label>
                          </div>
                        </div>
                        
                        <div className="space-y-3">
                          <div className="space-y-2">
                            <label className="text-sm font-medium">Peso de recencia</label>
                            <Slider
                              value={[filters.recency_weight]}
                              onValueChange={(value) => setFilters(prev => ({ ...prev, recency_weight: value[0] }))}
                              min={0}
                              max={1}
                              step={0.1}
                              className="w-full"
                            />
                            <div className="text-center text-xs text-gray-600">
                              {Math.round(filters.recency_weight * 100)}%
                            </div>
                          </div>
                        </div>
                      </div>
                    </TabsContent>
                  </Tabs>
                </DialogContent>
              </Dialog>
            </div>
          </div>
        </CardHeader>
        
        <CardContent>
          {/* Engine Tabs */}
          <Tabs value={activeEngine} onValueChange={(value) => setActiveEngine(value as typeof activeEngine)}>
            <TabsList className="grid grid-cols-4 w-full mb-4">
              <TabsTrigger value="ai" className="flex items-center gap-2">
                <Brain className="w-4 h-4" />
                IA Avanzada
              </TabsTrigger>
              <TabsTrigger value="similarity" className="flex items-center gap-2">
                <Target className="w-4 h-4" />
                Similaridad
              </TabsTrigger>
              <TabsTrigger value="popularity" className="flex items-center gap-2">
                <TrendingUp className="w-4 h-4" />
                Tendencias
              </TabsTrigger>
              <TabsTrigger value="personalized" className="flex items-center gap-2">
                <Users className="w-4 h-4" />
                Personalizado
              </TabsTrigger>
            </TabsList>
          </Tabs>

          {/* Search and filter controls */}
          <div className="flex flex-col md:flex-row gap-4 mb-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="w-4 h-4 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
                <Input
                  placeholder="Buscar videos por título, descripción, canal..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>
            
            <div className="flex gap-2">
              <Select value={selectedCategory} onValueChange={setSelectedCategory}>
                <SelectTrigger className="w-40">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Todas las categorías</SelectItem>
                  <SelectItem value="error_remediation">Corrección de errores</SelectItem>
                  <SelectItem value="skill_building">Desarrollo de habilidades</SelectItem>
                  <SelectItem value="concept_review">Repaso de conceptos</SelectItem>
                  <SelectItem value="direct_practice">Práctica directa</SelectItem>
                  <SelectItem value="exam_prep">Preparación examen</SelectItem>
                  <SelectItem value="advanced_topics">Temas avanzados</SelectItem>
                </SelectContent>
              </Select>
              
              <Select value={`${sortBy}-${sortOrder}`} onValueChange={(value) => {
                const [sort, order] = value.split('-');
                setSortBy(sort as typeof sortBy);
                setSortOrder(order as typeof sortOrder);
              }}>
                <SelectTrigger className="w-40">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="relevance-desc">Más relevantes</SelectItem>
                  <SelectItem value="quality-desc">Mayor calidad</SelectItem>
                  <SelectItem value="trending-desc">Más populares</SelectItem>
                  <SelectItem value="difficulty-asc">Más fáciles</SelectItem>
                  <SelectItem value="difficulty-desc">Más difíciles</SelectItem>
                  <SelectItem value="duration-asc">Más cortos</SelectItem>
                  <SelectItem value="duration-desc">Más largos</SelectItem>
                </SelectContent>
              </Select>
              
              <Select value={viewMode} onValueChange={(value) => setViewMode(value as typeof viewMode)}>
                <SelectTrigger className="w-32">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="card">Tarjetas</SelectItem>
                  <SelectItem value="compact">Compacto</SelectItem>
                  <SelectItem value="detailed">Detallado</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* Engine performance indicator */}
          <div className="flex items-center justify-between mb-4 p-3 bg-gray-50 rounded-lg">
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                {getEngineIcon(activeEngine)}
                <span className="text-sm font-medium">
                  Motor {activeEngine.charAt(0).toUpperCase() + activeEngine.slice(1)}
                </span>
              </div>
              
              <div className="flex items-center gap-4 text-xs text-gray-600">
                <div className="flex items-center gap-1">
                  <CheckCircle className="w-3 h-3 text-green-500" />
                  <span>Precisión: {Math.round(enginePerformance[activeEngine].accuracy * 100)}%</span>
                </div>
                <div className="flex items-center gap-1">
                  <Zap className="w-3 h-3 text-yellow-500" />
                  <span>Velocidad: {enginePerformance[activeEngine].speed}ms</span>
                </div>
                <div className="flex items-center gap-1">
                  <Star className="w-3 h-3 text-blue-500" />
                  <span>Satisfacción: {enginePerformance[activeEngine].satisfaction}/5</span>
                </div>
              </div>
            </div>
            
            {loading && (
              <div className="flex items-center gap-2">
                <RefreshCw className="w-4 h-4 animate-spin" />
                <span className="text-sm">Generando recomendaciones...</span>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Recommendations Grid */}
      <div className="space-y-4">
        {filteredAndSortedRecommendations.length === 0 && !loading && (
          <Card>
            <CardContent className="text-center py-12">
              <Compass className="w-12 h-12 mx-auto text-gray-400 mb-4" />
              <h3 className="font-medium text-gray-600 mb-2">
                No se encontraron recomendaciones
              </h3>
              <p className="text-sm text-gray-500 mb-4">
                Prueba ajustando los filtros o cambiando el motor de recomendaciones
              </p>
              <Button 
                variant="outline" 
                onClick={() => loadRecommendations(activeEngine)}
              >
                <RefreshCw className="w-4 h-4 mr-2" />
                Intentar de nuevo
              </Button>
            </CardContent>
          </Card>
        )}

        <div className={
          viewMode === 'compact' ? 'space-y-2' : 
          'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4'
        }>
          {filteredAndSortedRecommendations.map(renderVideoCard)}
        </div>
      </div>

      {/* Load more button */}
      {filteredAndSortedRecommendations.length >= maxRecommendations && (
        <div className="text-center">
          <Button 
            variant="outline" 
            onClick={() => {
              // Load more recommendations with higher limit
              loadRecommendations(activeEngine);
            }}
            disabled={loading}
          >
            {loading ? (
              <>
                <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                Cargando más...
              </>
            ) : (
              'Cargar más recomendaciones'
            )}
          </Button>
        </div>
      )}
    </div>
  );
}