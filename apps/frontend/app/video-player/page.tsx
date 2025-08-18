'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  Play, 
  BookOpen, 
  Target,
  TrendingUp,
  Clock,
  CheckCircle,
  Video,
  Eye
} from 'lucide-react';
import VideoPlayer from '@/components/VideoPlayer';

interface VideoContent {
  id: string;
  youtubeUrl: string;
  title: string;
  description: string;
  subject: string;
  duration: number;
  difficulty: string;
  topics: string[];
}

interface VideoProgress {
  videoId: string;
  watchedSeconds: number;
  percentage: number;
  isCompleted: boolean;
}

export default function VideoPlayerPage() {
  const [selectedVideo, setSelectedVideo] = useState<VideoContent | null>(null);
  const [videoProgress, setVideoProgress] = useState<VideoProgress[]>([]);
  const [showVideoPlayer, setShowVideoPlayer] = useState(false);
  const [topicFromUrl, setTopicFromUrl] = useState<string | null>(null);
  const [unitFromUrl, setUnitFromUrl] = useState<string | null>(null);

  // Leer parámetros de la URL
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const topic = urlParams.get('topic');
    const unit = urlParams.get('unit');
    
    if (topic) {
      setTopicFromUrl(decodeURIComponent(topic));
    }
    if (unit) {
      setUnitFromUrl(unit);
    }
    
    // Auto-cargar videos del backend si hay parámetros
    if (topic) {
      loadVideosFromBackend(decodeURIComponent(topic));
    }
  }, []);

  const loadVideosFromBackend = async (topicName: string) => {
    try {
      const token = localStorage.getItem('access_token');
      if (!token) {
        console.warn('No hay token de acceso, usando videos de ejemplo');
        if (videosBySubject["Matemáticas"].length > 0) {
          setSelectedVideo(videosBySubject["Matemáticas"][0]);
          setShowVideoPlayer(true);
        }
        return;
      }

      // Intentar obtener videos desde el endpoint de recomendaciones
      const response = await fetch(`/api/v1/youtube/recommendations/personalized?subject=Matemáticas&weak_topics=${encodeURIComponent(topicName)}&limit=5`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data = await response.json();
        if (data.success && data.data.recommendations.length > 0) {
          const firstVideo = data.data.recommendations[0];
          const videoContent: VideoContent = {
            id: firstVideo.id || '1',
            youtubeUrl: firstVideo.youtube_url || firstVideo.url,
            title: firstVideo.title || firstVideo.video_title || `Video sobre ${topicName}`,
            description: firstVideo.description || `Contenido educativo sobre ${topicName}`,
            subject: "Matemáticas",
            duration: firstVideo.duration_seconds || 600,
            difficulty: firstVideo.difficulty_level?.toString() || "medio",
            topics: [topicName]
          };
          
          setSelectedVideo(videoContent);
          setShowVideoPlayer(true);
          console.log('✅ Video cargado desde backend:', videoContent.title);
          return;
        }
      }
      
      // Fallback a videos de ejemplo
      console.warn('Usando videos de ejemplo como fallback');
      if (videosBySubject["Matemáticas"].length > 0) {
        setSelectedVideo(videosBySubject["Matemáticas"][0]);
        setShowVideoPlayer(true);
      }
      
    } catch (error) {
      console.error('Error cargando videos del backend:', error);
      // Fallback a videos de ejemplo
      if (videosBySubject["Matemáticas"].length > 0) {
        setSelectedVideo(videosBySubject["Matemáticas"][0]);
        setShowVideoPlayer(true);
      }
    }
  };

  // Videos de ejemplo por materia
  const videosBySubject = {
    "Matemáticas": [
      {
        id: "1",
        youtubeUrl: "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        title: "Álgebra Básica - Ecuaciones Lineales",
        description: "Aprende a resolver ecuaciones lineales paso a paso",
        subject: "Matemáticas",
        duration: 600,
        difficulty: "Básico",
        topics: ["Álgebra", "Ecuaciones", "Matemáticas Básicas"]
      },
      {
        id: "2",
        youtubeUrl: "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        title: "Geometría Analítica - Rectas y Planos",
        description: "Conceptos fundamentales de geometría analítica",
        subject: "Matemáticas",
        duration: 720,
        difficulty: "Intermedio",
        topics: ["Geometría", "Analítica", "Rectas"]
      }
    ],
    "Lectura Crítica": [
      {
        id: "3",
        youtubeUrl: "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        title: "Comprensión de Textos - Estrategias",
        description: "Técnicas para mejorar la comprensión lectora",
        subject: "Lectura Crítica",
        duration: 480,
        difficulty: "Básico",
        topics: ["Comprensión", "Lectura", "Estrategias"]
      }
    ],
    "Ciencias": [
      {
        id: "4",
        youtubeUrl: "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        title: "Biología Celular - Estructura Celular",
        description: "Explorando la estructura y función de las células",
        subject: "Ciencias",
        duration: 900,
        difficulty: "Intermedio",
        topics: ["Biología", "Células", "Estructura"]
      }
    ]
  };

  const handleVideoSelect = (video: VideoContent) => {
    setSelectedVideo(video);
    setShowVideoPlayer(true);
  };

  const handleVideoProgress = (watchedSeconds: number, percentage: number) => {
    if (selectedVideo) {
      const existingProgress = videoProgress.find(p => p.videoId === selectedVideo.id);
      const newProgress: VideoProgress = {
        videoId: selectedVideo.id,
        watchedSeconds,
        percentage,
        isCompleted: percentage >= 80
      };

      if (existingProgress) {
        setVideoProgress(prev => 
          prev.map(p => p.videoId === selectedVideo.id ? newProgress : p)
        );
      } else {
        setVideoProgress(prev => [...prev, newProgress]);
      }
    }
  };

  const handleVideoComplete = () => {
    console.log('Video completado!');
    // Aquí se podría actualizar el progreso del plan de estudio
  };

  const getProgressForVideo = (videoId: string) => {
    return videoProgress.find(p => p.videoId === videoId) || {
      videoId,
      watchedSeconds: 0,
      percentage: 0,
      isCompleted: false
    };
  };

  const formatDuration = (seconds: number): string => {
    const minutes = Math.floor(seconds / 60);
    return `${minutes} min`;
  };

  const getDifficultyColor = (difficulty: string): string => {
    switch (difficulty) {
      case 'Básico': return 'bg-green-100 text-green-800';
      case 'Intermedio': return 'bg-yellow-100 text-yellow-800';
      case 'Avanzado': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          Videos Educativos
        </h1>
        <p className="text-gray-600">
          Explora videos educativos organizados por materia y mejora tu aprendizaje
        </p>
        
        {/* Información del plan de estudio */}
        {topicFromUrl && (
          <div className="mt-6 p-4 bg-blue-50 rounded-lg border border-blue-200">
            <div className="flex items-center gap-3">
              <BookOpen className="w-5 h-5 text-blue-600" />
              <div>
                <h3 className="font-semibold text-blue-800">
                  📚 Plan de Estudio Personalizado
                </h3>
                <p className="text-sm text-blue-700">
                  Tema: <span className="font-medium">{topicFromUrl}</span>
                  {unitFromUrl && (
                    <span className="ml-3">
                      • Unidad: <span className="font-medium">{unitFromUrl}</span>
                    </span>
                  )}
                </p>
                <p className="text-xs text-blue-600 mt-1">
                  ✨ Video seleccionado basado en tu diagnóstico y debilidades identificadas
                </p>
              </div>
            </div>
          </div>
        )}
      </div>

      {showVideoPlayer && selectedVideo ? (
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <Button
              variant="outline"
              onClick={() => setShowVideoPlayer(false)}
              className="mb-4"
            >
              ← Volver a la biblioteca
            </Button>
            
            <div className="flex items-center gap-2">
              <Badge variant="secondary">
                <BookOpen className="w-4 h-4 mr-1" />
                {selectedVideo.subject}
              </Badge>
              <Badge className={getDifficultyColor(selectedVideo.difficulty)}>
                {selectedVideo.difficulty}
              </Badge>
            </div>
          </div>

          <VideoPlayer
            youtubeUrl={selectedVideo.youtubeUrl}
            videoTitle={selectedVideo.title}
            planId="example-plan-id"
            unitNumber={1}
            onProgressUpdate={handleVideoProgress}
            onVideoComplete={handleVideoComplete}
            completionThreshold={80}
          />

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Target className="w-5 h-5" />
                Información del Video
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <h3 className="font-semibold text-lg mb-2">{selectedVideo.title}</h3>
                <p className="text-gray-600">{selectedVideo.description}</p>
              </div>
              
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="space-y-1">
                  <span className="text-sm text-gray-500">Duración</span>
                  <div className="font-medium flex items-center gap-1">
                    <Clock className="w-4 h-4" />
                    {formatDuration(selectedVideo.duration)}
                  </div>
                </div>
                
                <div className="space-y-1">
                  <span className="text-sm text-gray-500">Dificultad</span>
                  <div className="font-medium">{selectedVideo.difficulty}</div>
                </div>
                
                <div className="space-y-1">
                  <span className="text-sm text-gray-500">Materia</span>
                  <div className="font-medium">{selectedVideo.subject}</div>
                </div>
                
                <div className="space-y-1">
                  <span className="text-sm text-gray-500">Progreso</span>
                  <div className="font-medium flex items-center gap-1">
                    <Eye className="w-4 h-4" />
                    {getProgressForVideo(selectedVideo.id).percentage.toFixed(1)}%
                  </div>
                </div>
              </div>
              
              <div>
                <span className="text-sm text-gray-500">Temas cubiertos:</span>
                <div className="flex flex-wrap gap-2 mt-2">
                  {selectedVideo.topics.map((topic, index) => (
                    <Badge key={index} variant="outline">
                      {topic}
                    </Badge>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      ) : (
        <Tabs defaultValue="Matemáticas" className="space-y-6">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="Matemáticas">Matemáticas</TabsTrigger>
            <TabsTrigger value="Lectura Crítica">Lectura Crítica</TabsTrigger>
            <TabsTrigger value="Ciencias">Ciencias</TabsTrigger>
          </TabsList>

          {Object.entries(videosBySubject).map(([subject, videos]) => (
            <TabsContent key={subject} value={subject} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {videos.map((video) => {
                  const progress = getProgressForVideo(video.id);
                  
                  return (
                    <Card key={video.id} className="hover:shadow-lg transition-shadow">
                      <CardHeader>
                        <div className="flex items-center justify-between mb-2">
                          <CardTitle className="text-lg">{video.title}</CardTitle>
                          {progress.isCompleted && (
                            <CheckCircle className="w-5 h-5 text-green-500" />
                          )}
                        </div>
                        <div className="flex items-center gap-2">
                          <Badge className={getDifficultyColor(video.difficulty)}>
                            {video.difficulty}
                          </Badge>
                          <Badge variant="secondary">
                            <Clock className="w-3 h-3 mr-1" />
                            {formatDuration(video.duration)}
                          </Badge>
                        </div>
                      </CardHeader>
                      
                      <CardContent className="space-y-4">
                        <p className="text-gray-600 text-sm">
                          {video.description}
                        </p>
                        
                        <div className="space-y-2">
                          <div className="flex items-center justify-between text-sm">
                            <span className="text-gray-500">Progreso</span>
                            <span className="font-medium">{progress.percentage.toFixed(1)}%</span>
                          </div>
                          <div className="w-full bg-gray-200 rounded-full h-2">
                            <div 
                              className={`h-2 rounded-full transition-all duration-300 ${
                                progress.isCompleted ? 'bg-green-500' : 'bg-blue-500'
                              }`}
                              style={{ width: `${Math.min(progress.percentage, 100)}%` }}
                            />
                          </div>
                        </div>
                        
                        <div className="flex flex-wrap gap-1">
                          {video.topics.slice(0, 3).map((topic, index) => (
                            <Badge key={index} variant="outline" className="text-xs">
                              {topic}
                            </Badge>
                          ))}
                          {video.topics.length > 3 && (
                            <Badge variant="outline" className="text-xs">
                              +{video.topics.length - 3}
                            </Badge>
                          )}
                        </div>
                        
                        <Button
                          onClick={() => handleVideoSelect(video)}
                          className="w-full"
                          variant={progress.isCompleted ? "outline" : "default"}
                        >
                          <Play className="w-4 h-4 mr-2" />
                          {progress.isCompleted ? 'Ver de nuevo' : 'Ver video'}
                        </Button>
                      </CardContent>
                    </Card>
                  );
                })}
              </div>
            </TabsContent>
          ))}
        </Tabs>
      )}
    </div>
  );
} 