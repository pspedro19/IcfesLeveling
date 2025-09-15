'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { 
  Play, 
  BookOpen, 
  Target,
  TrendingUp,
  Clock,
  CheckCircle,
  Brain,
  Lightbulb,
  BarChart3,
  User,
  Playlist,
  Eye,
  Star,
  AlertCircle,
  Zap,
  RefreshCw
} from 'lucide-react';

// Import the service
import { 
  recommendationsService,
  formatDuration,
  getContextIcon,
  getContextColor,
  getScoreColor,
  VideoRecommendation,
  StudentProfile,
  VideoAnalytics
} from '../app/services/recommendations.service';

// Interfaces are now imported from the service

export default function IntelligentVideoRecommendations() {
  const [recommendations, setRecommendations] = useState<VideoRecommendation[]>([]);
  const [profile, setProfile] = useState<StudentProfile | null>(null);
  const [analytics, setAnalytics] = useState<VideoAnalytics | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('weakness_remediation');
  const [selectedVideo, setSelectedVideo] = useState<VideoRecommendation | null>(null);
  const [isGeneratingPlaylist, setIsGeneratingPlaylist] = useState(false);
  const [playlist, setPlaylist] = useState<VideoRecommendation[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadIntelligentData();
  }, []);

  const loadIntelligentData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Load all data concurrently using the service
      const [profileData, analyticsData, recommendationsData] = await Promise.all([
        recommendationsService.getStudentProfile(),
        recommendationsService.getVideoAnalytics(),
        recommendationsService.getContextualRecommendations({
          context: activeTab,
          limit: 10
        })
      ]);

      setProfile(profileData);
      setAnalytics(analyticsData);
      setRecommendations(recommendationsData);

    } catch (error) {
      console.error('Error loading intelligent video data:', error);
      setError('Failed to load video recommendations. Please try again later.');
    } finally {
      setLoading(false);
    }
  };

  const handleContextChange = async (context: string) => {
    setActiveTab(context);
    setError(null);
    
    try {
      setLoading(true);
      const data = await recommendationsService.getContextualRecommendations({
        context,
        limit: 10
      });
      setRecommendations(data);
    } catch (error) {
      console.error('Error loading contextual recommendations:', error);
      setError('Failed to load recommendations for this context.');
    } finally {
      setLoading(false);
    }
  };

  const generateLearningPlaylist = async () => {
    setIsGeneratingPlaylist(true);
    setError(null);
    
    try {
      const data = await recommendationsService.generatePlaylist({
        learning_goal: "Personalized study session",
        session_duration: 30,
        difficulty_progression: true,
        max_videos: 8
      });
      setPlaylist(data);
    } catch (error) {
      console.error('Error generating playlist:', error);
      setError('Failed to generate playlist. Please try again.');
    } finally {
      setIsGeneratingPlaylist(false);
    }
  };

  const trackVideoEvent = async (videoId: string, eventType: string, currentTime: number = 0, duration: number = 0) => {
    try {
      await recommendationsService.trackVideoEvent({
        video_id: videoId,
        event_type: eventType as any,
        current_time: currentTime,
        video_duration: duration,
        session_id: `session_${Date.now()}`,
        metadata: {
          context: activeTab,
          recommendation_source: 'intelligent_system'
        }
      });
    } catch (error) {
      console.error('Error tracking video event:', error);
    }
  };

  // Helper functions are now imported from the service
  
  const getContextIconComponent = (context: string) => {
    switch (context) {
      case 'weakness_remediation': return <Target className="w-4 h-4" />;
      case 'skill_building': return <TrendingUp className="w-4 h-4" />;
      case 'study_plan': return <BookOpen className="w-4 h-4" />;
      case 'review': return <CheckCircle className="w-4 h-4" />;
      case 'exploration': return <Lightbulb className="w-4 h-4" />;
      default: return <Play className="w-4 h-4" />;
    }
  };

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="flex items-center justify-center h-64">
          <RefreshCw className="w-8 h-8 animate-spin text-blue-600 mr-3" />
          <span className="text-gray-600">Cargando recomendaciones inteligentes...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Error Alert */}
      {error && (
        <Alert className="mb-6 border-red-200 bg-red-50">
          <AlertCircle className="h-4 w-4 text-red-600" />
          <AlertDescription className="text-red-700">
            {error}
            <Button 
              variant="outline" 
              size="sm" 
              onClick={loadIntelligentData}
              className="ml-2"
            >
              <RefreshCw className="w-4 h-4 mr-1" />
              Reintentar
            </Button>
          </AlertDescription>
        </Alert>
      )}

      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2 flex items-center gap-3">
          <Brain className="w-8 h-8 text-blue-600" />
          Videos Inteligentes
        </h1>
        <p className="text-gray-600">
          Recomendaciones personalizadas basadas en tu progreso y debilidades identificadas
        </p>
      </div>

      {/* Student Profile Summary */}
      {profile && (
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <User className="w-5 h-5" />
              Tu Perfil de Aprendizaje
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="text-center">
                <div className="text-sm text-gray-500">Estilo de Aprendizaje</div>
                <div className="font-semibold capitalize">{profile.learning_style}</div>
              </div>
              <div className="text-center">
                <div className="text-sm text-gray-500">Nivel de Rendimiento</div>
                <div className="font-semibold">{Math.round(profile.performance_level * 100)}%</div>
              </div>
              <div className="text-center">
                <div className="text-sm text-gray-500">Duración Preferida</div>
                <div className="font-semibold">{formatDuration(profile.preferred_video_duration)}</div>
              </div>
              <div className="text-center">
                <div className="text-sm text-gray-500">Ritmo de Aprendizaje</div>
                <div className="font-semibold capitalize">{profile.learning_pace}</div>
              </div>
            </div>
            
            {profile.weak_topics.length > 0 && (
              <div className="mt-4">
                <div className="text-sm text-gray-500 mb-2">Temas a Reforzar:</div>
                <div className="flex flex-wrap gap-2">
                  {profile.weak_topics.slice(0, 5).map((topic, index) => (
                    <Badge key={index} variant="destructive" className="text-xs">
                      {topic}
                    </Badge>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Analytics Dashboard */}
      {analytics && (
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="w-5 h-5" />
              Tus Métricas de Video
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="text-center">
                <div className="text-sm text-gray-500">Tiempo Total Visto</div>
                <div className="font-semibold">{formatDuration(analytics.total_watch_time)}</div>
              </div>
              <div className="text-center">
                <div className="text-sm text-gray-500">Tasa de Finalización</div>
                <div className="font-semibold">{Math.round(analytics.completion_rate * 100)}%</div>
                <Progress value={analytics.completion_rate * 100} className="mt-1 h-2" />
              </div>
              <div className="text-center">
                <div className="text-sm text-gray-500">Nivel de Compromiso</div>
                <div className="font-semibold">{Math.round(analytics.engagement_score * 100)}%</div>
                <Progress value={analytics.engagement_score * 100} className="mt-1 h-2" />
              </div>
              <div className="text-center">
                <div className="text-sm text-gray-500">Efectividad de Aprendizaje</div>
                <div className={`font-semibold ${getScoreColor(analytics.learning_effectiveness)}`}>
                  {Math.round(analytics.learning_effectiveness * 100)}%
                </div>
                <Progress value={analytics.learning_effectiveness * 100} className="mt-1 h-2" />
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Generate Playlist Button */}
      <div className="mb-6">
        <Button 
          onClick={generateLearningPlaylist}
          disabled={isGeneratingPlaylist}
          className="flex items-center gap-2"
        >
          {isGeneratingPlaylist ? (
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
          ) : (
            <Playlist className="w-4 h-4" />
          )}
          Generar Lista de Reproducción Inteligente
        </Button>
      </div>

      {/* Smart Playlist */}
      {playlist.length > 0 && (
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Zap className="w-5 h-5" />
              Tu Lista de Reproducción Personalizada
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {playlist.map((video, index) => (
                <div key={video.video_id} className="flex items-center gap-3 p-3 border rounded-lg">
                  <div className="flex-shrink-0">
                    <div className="w-8 h-8 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-sm font-semibold">
                      {index + 1}
                    </div>
                  </div>
                  <div className="flex-1">
                    <h4 className="font-medium">{video.title}</h4>
                    <p className="text-sm text-gray-600">{video.reasoning}</p>
                    <div className="flex items-center gap-2 mt-1">
                      <Badge className={getContextColor(video.context)} variant="secondary">
                        {getContextIconComponent(video.context)}
                        <span className="ml-1 capitalize">{video.context.replace('_', ' ')}</span>
                      </Badge>
                      <Badge variant="outline">
                        <Clock className="w-3 h-3 mr-1" />
                        {formatDuration(video.duration_seconds || 600)}
                      </Badge>
                    </div>
                  </div>
                  <Button
                    size="sm"
                    onClick={() => {
                      setSelectedVideo(video);
                      trackVideoEvent(video.youtube_id, 'play');
                    }}
                  >
                    <Play className="w-4 h-4" />
                  </Button>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Contextual Recommendations */}
      <Tabs value={activeTab} onValueChange={handleContextChange} className="space-y-6">
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="weakness_remediation" className="flex items-center gap-2">
            <Target className="w-4 h-4" />
            Debilidades
          </TabsTrigger>
          <TabsTrigger value="skill_building" className="flex items-center gap-2">
            <TrendingUp className="w-4 h-4" />
            Desarrollo
          </TabsTrigger>
          <TabsTrigger value="study_plan" className="flex items-center gap-2">
            <BookOpen className="w-4 h-4" />
            Plan de Estudio
          </TabsTrigger>
          <TabsTrigger value="review" className="flex items-center gap-2">
            <CheckCircle className="w-4 h-4" />
            Repaso
          </TabsTrigger>
          <TabsTrigger value="exploration" className="flex items-center gap-2">
            <Lightbulb className="w-4 h-4" />
            Exploración
          </TabsTrigger>
        </TabsList>

        {/* Recommendations Grid */}
        <TabsContent value={activeTab} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {recommendations.map((video) => (
              <Card key={video.video_id} className="hover:shadow-lg transition-shadow">
                <CardHeader className="pb-3">
                  <div className="flex items-start justify-between mb-2">
                    <CardTitle className="text-lg line-clamp-2">{video.title}</CardTitle>
                    <div className="flex items-center gap-1 ml-2">
                      <Star className="w-4 h-4 text-yellow-500" />
                      <span className="text-sm font-medium">
                        {(video.relevance_score * 5).toFixed(1)}
                      </span>
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-2 flex-wrap">
                    <Badge className={getContextColor(video.context)} variant="secondary">
                      {getContextIconComponent(video.context)}
                      <span className="ml-1 capitalize">{video.context.replace('_', ' ')}</span>
                    </Badge>
                    <Badge variant="outline">
                      <Clock className="w-3 h-3 mr-1" />
                      {formatDuration(video.duration_seconds || 600)}
                    </Badge>
                  </div>
                </CardHeader>
                
                <CardContent className="space-y-4">
                  <div>
                    <div className="text-sm text-gray-600 mb-1">Objetivo de Aprendizaje:</div>
                    <div className="text-sm font-medium">{video.learning_objective}</div>
                  </div>
                  
                  <div>
                    <div className="text-sm text-gray-600 mb-1">¿Por qué es relevante?</div>
                    <div className="text-sm">{video.reasoning}</div>
                  </div>
                  
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <div>
                      <div className="text-gray-500">Impacto Estimado</div>
                      <div className={`font-medium ${getScoreColor(video.estimated_impact)}`}>
                        {Math.round(video.estimated_impact * 100)}%
                      </div>
                    </div>
                    <div>
                      <div className="text-gray-500">Predicción de Compromiso</div>
                      <div className={`font-medium ${getScoreColor(video.engagement_prediction)}`}>
                        {Math.round(video.engagement_prediction * 100)}%
                      </div>
                    </div>
                  </div>
                  
                  <div className="space-y-2">
                    <div className="text-xs text-gray-500">Coincidencia de Dificultad</div>
                    <Progress value={video.difficulty_match * 100} className="h-2" />
                  </div>
                  
                  <Button
                    onClick={() => {
                      setSelectedVideo(video);
                      trackVideoEvent(video.youtube_id, 'play');
                    }}
                    className="w-full"
                  >
                    <Play className="w-4 h-4 mr-2" />
                    Ver Video
                  </Button>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>
      </Tabs>

      {/* Video Player Modal (if selectedVideo) */}
      {selectedVideo && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-auto">
            <div className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-xl font-bold">{selectedVideo.title}</h3>
                <Button variant="outline" onClick={() => setSelectedVideo(null)}>
                  Cerrar
                </Button>
              </div>
              
              <div className="aspect-video mb-4">
                <iframe
                  src={`https://www.youtube.com/embed/${selectedVideo.youtube_id}?autoplay=1&rel=0`}
                  className="w-full h-full rounded-lg"
                  allowFullScreen
                  allow="autoplay"
                />
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <h4 className="font-semibold mb-2">Información del Video</h4>
                  <div className="space-y-2 text-sm">
                    <div><span className="text-gray-600">Canal:</span> {selectedVideo.channel_name}</div>
                    <div><span className="text-gray-600">Área:</span> {selectedVideo.area_evaluada}</div>
                    <div><span className="text-gray-600">Tema:</span> {selectedVideo.tema_principal}</div>
                  </div>
                </div>
                
                <div>
                  <h4 className="font-semibold mb-2">Métricas de Recomendación</h4>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span>Relevancia:</span>
                      <span className={getScoreColor(selectedVideo.relevance_score)}>
                        {Math.round(selectedVideo.relevance_score * 100)}%
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span>Impacto Estimado:</span>
                      <span className={getScoreColor(selectedVideo.estimated_impact)}>
                        {Math.round(selectedVideo.estimated_impact * 100)}%
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span>Coincidencia de Dificultad:</span>
                      <span className={getScoreColor(selectedVideo.difficulty_match)}>
                        {Math.round(selectedVideo.difficulty_match * 100)}%
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}