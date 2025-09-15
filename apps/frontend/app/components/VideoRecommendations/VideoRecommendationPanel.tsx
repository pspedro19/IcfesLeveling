'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  Play, 
  Clock, 
  Eye,
  ThumbsUp,
  ThumbsDown,
  Star,
  ExternalLink,
  BookOpen,
  Target,
  TrendingUp,
  AlertTriangle,
  Sparkles,
  Filter,
  Shuffle,
  RefreshCw
} from 'lucide-react';

// Import the service
import { 
  recommendationsService,
  formatDuration
} from '../../services/recommendations.service';

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
  recommendation_type: string;
  confidence_level: string;
  scores: {
    total_score: number;
    semantic_similarity?: number;
    difficulty_match?: number;
    exact_match?: number;
    popularity?: number;
  };
  learning_objectives: string[];
  estimated_study_time: number;
  quality_score: number;
  relevance_score: number;
}

interface VideoRecommendationPanelProps {
  questionId?: string;
  subjectId?: number;
  userId: string;
  onVideoSelect?: (video: VideoRecommendation) => void;
  maxRecommendations?: number;
  showFilters?: boolean;
}

export default function VideoRecommendationPanel({
  questionId,
  subjectId,
  userId,
  onVideoSelect,
  maxRecommendations = 20,
  showFilters = true
}: VideoRecommendationPanelProps) {
  const [recommendations, setRecommendations] = useState<VideoRecommendation[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState('personalized');
  const [filters, setFilters] = useState({
    confidenceLevel: 'all',
    recommendationType: 'all',
    minQuality: 0
  });

  // Fetch personalized recommendations
  const fetchPersonalizedRecommendations = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const videos = await recommendationsService.getPersonalizedRecommendations({
        subject_id: subjectId,
        limit: maxRecommendations,
        include_watched: false
      });
      setRecommendations(videos);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error loading recommendations');
    } finally {
      setLoading(false);
    }
  };

  // Fetch recommendations for failed question
  const fetchQuestionRecommendations = async (qId: string) => {
    setLoading(true);
    setError(null);
    
    try {
      const videos = await recommendationsService.getRecommendationsForQuestion(qId, maxRecommendations);
      setRecommendations(videos);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error loading recommendations');
    } finally {
      setLoading(false);
    }
  };

  // Fetch popular videos by subject
  const fetchSubjectVideos = async (sId: number) => {
    setLoading(true);
    setError(null);
    
    try {
      const videos = await recommendationsService.getPopularVideosBySubject(sId, maxRecommendations);
      setRecommendations(videos);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error loading videos');
    } finally {
      setLoading(false);
    }
  };

  // Track video interaction
  const trackVideoInteraction = async (video: VideoRecommendation, action: string) => {
    try {
      await recommendationsService.trackVideoInteraction({
        video_id: video.video_id,
        question_id: questionId,
        recommendation_source: 'recommendation_panel',
        watch_start_time: new Date().toISOString(),
        action
      });
    } catch (err) {
      console.error('Error tracking video interaction:', err);
    }
  };

  useEffect(() => {
    if (questionId) {
      fetchQuestionRecommendations(questionId);
      setActiveTab('question');
    } else {
      fetchPersonalizedRecommendations();
    }
  }, [questionId, subjectId]);

  const filteredRecommendations = recommendations.filter(video => {
    if (filters.confidenceLevel !== 'all' && video.confidence_level !== filters.confidenceLevel) {
      return false;
    }
    if (filters.recommendationType !== 'all' && video.recommendation_type !== filters.recommendationType) {
      return false;
    }
    if (video.quality_score < filters.minQuality) {
      return false;
    }
    return true;
  });

  const handleVideoClick = async (video: VideoRecommendation) => {
    await trackVideoInteraction(video, 'click');
    if (onVideoSelect) {
      onVideoSelect(video);
    } else {
      window.open(video.url, '_blank');
    }
  };

  const formatVideoDuration = (seconds: number): string => {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
  };

  const getConfidenceBadgeColor = (level: string): string => {
    switch (level) {
      case 'high': return 'bg-green-500';
      case 'medium': return 'bg-yellow-500';
      case 'low': return 'bg-red-500';
      default: return 'bg-gray-500';
    }
  };

  const getRecommendationTypeIcon = (type: string) => {
    switch (type) {
      case 'error_remediation': return <AlertTriangle className="w-4 h-4" />;
      case 'skill_building': return <TrendingUp className="w-4 h-4" />;
      case 'concept_review': return <BookOpen className="w-4 h-4" />;
      case 'direct_practice': return <Target className="w-4 h-4" />;
      default: return <Play className="w-4 h-4" />;
    }
  };

  const renderVideoCard = (video: VideoRecommendation) => (
    <Card key={video.video_id} className="group hover:shadow-lg transition-all duration-200">
      <CardContent className="p-4">
        <div className="flex gap-4">
          {/* Video Thumbnail */}
          <div className="relative flex-shrink-0">
            <img 
              src={video.thumbnail_url || `https://img.youtube.com/vi/${video.youtube_id}/mqdefault.jpg`}
              alt={video.title}
              className="w-40 h-24 object-cover rounded-lg"
            />
            <div className="absolute inset-0 bg-black/0 group-hover:bg-black/20 rounded-lg transition-all duration-200 flex items-center justify-center">
              <Play className="w-8 h-8 text-white opacity-0 group-hover:opacity-100 transition-opacity duration-200" />
            </div>
            {video.duration_seconds && (
              <Badge className="absolute bottom-1 right-1 text-xs">
                {formatVideoDuration(video.duration_seconds)}
              </Badge>
            )}
          </div>

          {/* Video Info */}
          <div className="flex-1 space-y-2">
            <div className="flex items-start justify-between">
              <h3 className="font-medium text-sm leading-tight line-clamp-2 group-hover:text-blue-600 cursor-pointer" 
                  onClick={() => handleVideoClick(video)}>
                {video.title}
              </h3>
              <Button
                size="sm"
                variant="ghost"
                onClick={() => handleVideoClick(video)}
                className="flex-shrink-0"
              >
                <ExternalLink className="w-4 h-4" />
              </Button>
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

            <div className="flex flex-wrap gap-2">
              <Badge variant="outline" className={`text-xs ${getConfidenceBadgeColor(video.confidence_level)} text-white`}>
                {getRecommendationTypeIcon(video.recommendation_type)}
                <span className="ml-1 capitalize">{video.confidence_level}</span>
              </Badge>
              
              <Badge variant="secondary" className="text-xs">
                <Star className="w-3 h-3 mr-1" />
                {(video.scores.total_score * 100).toFixed(0)}%
              </Badge>

              <Badge variant="outline" className="text-xs">
                <Clock className="w-3 h-3 mr-1" />
                {video.estimated_study_time}min
              </Badge>
            </div>

            {video.learning_objectives.length > 0 && (
              <div className="text-xs text-gray-600">
                <span className="font-medium">Objetivos: </span>
                {video.learning_objectives.slice(0, 2).join(', ')}
              </div>
            )}

            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4 text-xs text-gray-500">
                <span>Calidad: {(video.quality_score * 100).toFixed(0)}%</span>
                <span>Relevancia: {(video.relevance_score * 100).toFixed(0)}%</span>
              </div>
              
              <div className="flex items-center gap-1">
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => trackVideoInteraction(video, 'helpful')}
                  className="h-6 w-6 p-0"
                >
                  <ThumbsUp className="w-3 h-3" />
                </Button>
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => trackVideoInteraction(video, 'not_helpful')}
                  className="h-6 w-6 p-0"
                >
                  <ThumbsDown className="w-3 h-3" />
                </Button>
              </div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );

  return (
    <div className="w-full space-y-4">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Sparkles className="w-5 h-5" />
            Video Recomendaciones Inteligentes
          </CardTitle>
        </CardHeader>
        
        <CardContent>
          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList className="grid w-full grid-cols-3">
              <TabsTrigger value="personalized" onClick={fetchPersonalizedRecommendations}>
                Personalizadas
              </TabsTrigger>
              {questionId && (
                <TabsTrigger value="question" onClick={() => fetchQuestionRecommendations(questionId)}>
                  Para Pregunta
                </TabsTrigger>
              )}
              {subjectId && (
                <TabsTrigger value="subject" onClick={() => fetchSubjectVideos(subjectId)}>
                  Por Materia
                </TabsTrigger>
              )}
            </TabsList>

            {showFilters && (
              <div className="flex items-center gap-4 mt-4 p-3 bg-gray-50 rounded-lg">
                <Filter className="w-4 h-4" />
                <select 
                  value={filters.confidenceLevel}
                  onChange={(e) => setFilters(prev => ({ ...prev, confidenceLevel: e.target.value }))}
                  className="text-sm border rounded px-2 py-1"
                >
                  <option value="all">Todas las confianzas</option>
                  <option value="high">Alta confianza</option>
                  <option value="medium">Media confianza</option>
                  <option value="low">Baja confianza</option>
                </select>

                <select 
                  value={filters.recommendationType}
                  onChange={(e) => setFilters(prev => ({ ...prev, recommendationType: e.target.value }))}
                  className="text-sm border rounded px-2 py-1"
                >
                  <option value="all">Todos los tipos</option>
                  <option value="error_remediation">Corrección de errores</option>
                  <option value="skill_building">Desarrollo de habilidades</option>
                  <option value="concept_review">Repaso de conceptos</option>
                  <option value="direct_practice">Práctica directa</option>
                </select>

                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => setRecommendations(prev => [...prev].sort(() => Math.random() - 0.5))}
                >
                  <Shuffle className="w-4 h-4 mr-1" />
                  Mezclar
                </Button>

                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => {
                    if (questionId) fetchQuestionRecommendations(questionId);
                    else fetchPersonalizedRecommendations();
                  }}
                >
                  <RefreshCw className="w-4 h-4 mr-1" />
                  Actualizar
                </Button>
              </div>
            )}

            <TabsContent value="personalized" className="mt-4">
              {loading && (
                <div className="flex items-center justify-center py-8">
                  <RefreshCw className="w-6 h-6 animate-spin mr-2" />
                  Cargando recomendaciones personalizadas...
                </div>
              )}

              {error && (
                <Alert>
                  <AlertTriangle className="h-4 w-4" />
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              )}

              {!loading && !error && (
                <div className="space-y-3">
                  {filteredRecommendations.length === 0 ? (
                    <Card>
                      <CardContent className="text-center py-8">
                        <Eye className="w-12 h-12 mx-auto text-gray-400 mb-4" />
                        <p className="text-gray-600">No se encontraron recomendaciones</p>
                        <Button 
                          variant="outline" 
                          onClick={fetchPersonalizedRecommendations}
                          className="mt-2"
                        >
                          Intentar de nuevo
                        </Button>
                      </CardContent>
                    </Card>
                  ) : (
                    <>
                      <div className="text-sm text-gray-600 mb-4">
                        Mostrando {filteredRecommendations.length} de {recommendations.length} videos recomendados
                      </div>
                      {filteredRecommendations.map(renderVideoCard)}
                    </>
                  )}
                </div>
              )}
            </TabsContent>

            <TabsContent value="question" className="mt-4">
              {loading && (
                <div className="flex items-center justify-center py-8">
                  <RefreshCw className="w-6 h-6 animate-spin mr-2" />
                  Analizando pregunta y encontrando videos relevantes...
                </div>
              )}

              {!loading && !error && filteredRecommendations.length > 0 && (
                <div className="space-y-3">
                  <Alert>
                    <Target className="h-4 w-4" />
                    <AlertDescription>
                      Estos videos están específicamente recomendados para ayudarte con la pregunta que respondiste incorrectamente.
                    </AlertDescription>
                  </Alert>
                  {filteredRecommendations.map(renderVideoCard)}
                </div>
              )}
            </TabsContent>

            <TabsContent value="subject" className="mt-4">
              {!loading && !error && filteredRecommendations.length > 0 && (
                <div className="space-y-3">
                  <Alert>
                    <BookOpen className="h-4 w-4" />
                    <AlertDescription>
                      Videos populares y de alta calidad para esta materia.
                    </AlertDescription>
                  </Alert>
                  {filteredRecommendations.map(renderVideoCard)}
                </div>
              )}
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
    </div>
  );
}