"use client";

import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Play, 
  Pause, 
  SkipForward, 
  SkipBack, 
  Volume2, 
  VolumeX,
  Settings,
  Maximize,
  CheckCircle,
  AlertTriangle,
  BookOpen,
  Clock,
  Target,
  Star
} from 'lucide-react';

// =====================================================
// TIPOS Y INTERFACES
// =====================================================

interface YMLVideo {
  video_id: string;
  title: string;
  description: string;
  duration_minutes: number;
  quality: string;
  codigo_tema: string;
  area_evaluada: string;
  difficulty: number;
  learning_style: string;
  embed_url: string;
  watch_url: string;
  thumbnail?: string;
}

interface YMLModule {
  id: string;
  topic_code: string;
  topic_name: string;
  difficulty: string;
  estimated_hours: number;
  priority: string;
  justification: string;
  lessons: Array<{
    id: string;
    title: string;
    primary_resource: {
      videos: YMLVideo[];
      duration_hours: number;
      style: string;
      difficulty: string;
      total_video_duration_minutes: number;
    };
    exercises: {
      count: number;
      difficulty: string;
      focus_areas: string[];
      estimated_time_minutes: number;
    };
  }>;
}

interface YMLVideoPlayerProps {
  module: YMLModule;
  userId: string;
  planId: string;
  unitNumber: number;
  onVideoComplete: (videoData: VideoProgressData) => void;
  onModuleComplete: (moduleData: ModuleProgressData) => void;
  className?: string;
}

interface VideoProgressData {
  userId: string;
  planId: string;
  unitNumber: number;
  videoId: string;
  codigoTema: string;
  watchedSeconds: number;
  watchedPercentage: number;
  isCompleted: boolean;
  replayCount: number;
  speedPreference: string;
}

interface ModuleProgressData {
  moduleId: string;
  topicCode: string;
  completedVideos: number;
  totalVideos: number;
  totalTimeMinutes: number;
  exercisesCompleted: number;
  totalExercises: number;
}

// =====================================================
// COMPONENTE PRINCIPAL
// =====================================================

export const YMLVideoPlayer: React.FC<YMLVideoPlayerProps> = ({
  module,
  userId,
  planId,
  unitNumber,
  onVideoComplete,
  onModuleComplete,
  className = ""
}) => {
  // =====================================================
  // ESTADOS
  // =====================================================
  
  const [currentVideoIndex, setCurrentVideoIndex] = useState(0);
  const [currentVideo, setCurrentVideo] = useState<YMLVideo | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [volume, setVolume] = useState(50);
  const [isMuted, setIsMuted] = useState(false);
  const [playbackRate, setPlaybackRate] = useState(1);
  const [showControls, setShowControls] = useState(true);
  const [showSettings, setShowSettings] = useState(false);
  
  // Estados de progreso
  const [videoProgress, setVideoProgress] = useState<{ [videoId: string]: number }>({});
  const [completedVideos, setCompletedVideos] = useState<Set<string>>(new Set());
  const [currentVideoProgress, setCurrentVideoProgress] = useState(0);
  
  // Estados de engagement
  const [focusTime, setFocusTime] = useState(0);
  const [tabSwitches, setTabSwitches] = useState(0);
  const [engagementScore, setEngagementScore] = useState(100);
  
  // Referencias
  const playerRef = useRef<HTMLDivElement>(null);
  const controlsTimeoutRef = useRef<NodeJS.Timeout>();
  const focusTimerRef = useRef<NodeJS.Timeout>();
  const progressTimerRef = useRef<NodeJS.Timeout>();
  
  // =====================================================
  // EFECTOS
  // =====================================================
  
  // Inicializar video actual
  useEffect(() => {
    if (module.lessons.length > 0 && module.lessons[0].primary_resource.videos.length > 0) {
      setCurrentVideo(module.lessons[0].primary_resource.videos[0]);
      setCurrentVideoIndex(0);
    }
  }, [module]);
  
  // Timer de enfoque
  useEffect(() => {
    if (isPlaying) {
      focusTimerRef.current = setInterval(() => {
        setFocusTime(prev => prev + 1);
      }, 1000);
    }
    
    return () => {
      if (focusTimerRef.current) clearInterval(focusTimerRef.current);
    };
  }, [isPlaying]);
  
  // Timer de progreso
  useEffect(() => {
    if (isPlaying && currentVideo) {
      progressTimerRef.current = setInterval(() => {
        updateVideoProgress();
      }, 2000); // Cada 2 segundos
    }
    
    return () => {
      if (progressTimerRef.current) clearInterval(progressTimerRef.current);
    };
  }, [isPlaying, currentVideo]);
  
  // =====================================================
  // FUNCIONES DE CONTROL
  // =====================================================
  
  const updateVideoProgress = () => {
    if (!currentVideo) return;
    
    const newProgress = (currentTime / duration) * 100;
    setCurrentVideoProgress(newProgress);
    
    // Actualizar progreso del video actual
    setVideoProgress(prev => ({
      ...prev,
      [currentVideo.video_id]: newProgress
    }));
    
    // Verificar si el video está completado
    if (newProgress >= 90 && !completedVideos.has(currentVideo.video_id)) {
      handleVideoComplete();
    }
  };
  
  const handleVideoComplete = () => {
    if (!currentVideo) return;
    
    // Marcar video como completado
    setCompletedVideos(prev => new Set([...prev, currentVideo.video_id]));
    
    // Enviar datos de progreso
    const videoProgressData: VideoProgressData = {
      userId,
      planId,
      unitNumber,
      videoId: currentVideo.video_id,
      codigoTema: currentVideo.codigo_tema,
      watchedSeconds: duration,
      watchedPercentage: 100,
      isCompleted: true,
      replayCount: 0,
      speedPreference: playbackRate.toString()
    };
    
    onVideoComplete(videoProgressData);
    
    // Verificar si el módulo está completado
    checkModuleCompletion();
    
    // Avanzar al siguiente video si existe
    if (currentVideoIndex < module.lessons[0].primary_resource.videos.length - 1) {
      setCurrentVideoIndex(prev => prev + 1);
      setCurrentVideo(module.lessons[0].primary_resource.videos[currentVideoIndex + 1]);
      setCurrentTime(0);
      setCurrentVideoProgress(0);
    }
  };
  
  const checkModuleCompletion = () => {
    const totalVideos = module.lessons[0].primary_resource.videos.length;
    const completedCount = completedVideos.size;
    
    if (completedCount >= totalVideos) {
      const moduleProgressData: ModuleProgressData = {
        moduleId: module.id,
        topicCode: module.topic_code,
        completedVideos: completedCount,
        totalVideos,
        totalTimeMinutes: module.lessons[0].primary_resource.total_video_duration_minutes,
        exercisesCompleted: 0, // Por implementar
        totalExercises: module.lessons[0].exercises.count
      };
      
      onModuleComplete(moduleProgressData);
    }
  };
  
  const nextVideo = () => {
    if (currentVideoIndex < module.lessons[0].primary_resource.videos.length - 1) {
      setCurrentVideoIndex(prev => prev + 1);
      setCurrentVideo(module.lessons[0].primary_resource.videos[currentVideoIndex + 1]);
      setCurrentTime(0);
      setCurrentVideoProgress(0);
    }
  };
  
  const previousVideo = () => {
    if (currentVideoIndex > 0) {
      setCurrentVideoIndex(prev => prev - 1);
      setCurrentVideo(module.lessons[0].primary_resource.videos[currentVideoIndex - 1]);
      setCurrentTime(0);
      setCurrentVideoProgress(0);
    }
  };
  
  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };
  
  const getDifficultyColor = (difficulty: string): string => {
    switch (difficulty.toLowerCase()) {
      case 'easy': return 'text-green-500';
      case 'medium': return 'text-yellow-500';
      case 'hard': return 'text-red-500';
      default: return 'text-gray-500';
    }
  };
  
  const getPriorityColor = (priority: string): string => {
    switch (priority.toLowerCase()) {
      case 'high': return 'text-red-500';
      case 'medium': return 'text-yellow-500';
      case 'low': return 'text-green-500';
      default: return 'text-gray-500';
    }
  };
  
  // =====================================================
  // RENDERIZADO
  // =====================================================
  
  if (!currentVideo) {
    return (
      <div className={`bg-gray-100 rounded-lg p-8 text-center ${className}`}>
        <BookOpen className="w-16 h-16 mx-auto mb-4 text-gray-400" />
        <h3 className="text-xl font-semibold text-gray-600 mb-2">No hay videos disponibles</h3>
        <p className="text-gray-500">Este módulo no tiene videos asignados actualmente.</p>
      </div>
    );
  }
  
  return (
    <div className={`bg-white rounded-lg shadow-lg overflow-hidden ${className}`}>
      {/* Header del Módulo */}
      <div className="bg-gradient-to-r from-blue-600 to-purple-600 text-white p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-2xl font-bold">{module.topic_name}</h2>
            <p className="text-blue-100 text-sm">Módulo {module.id} • Semana {Math.ceil(parseInt(module.id.split('_')[1]) / 3)}</p>
          </div>
          <div className="text-right">
            <div className="flex items-center space-x-4 text-sm">
              <div className="flex items-center space-x-1">
                <Clock size={16} />
                <span>{module.estimated_hours}h estimadas</span>
              </div>
              <div className={`flex items-center space-x-1 ${getDifficultyColor(module.difficulty)}`}>
                <Target size={16} />
                <span>{module.difficulty}</span>
              </div>
              <div className={`flex items-center space-x-1 ${getPriorityColor(module.priority)}`}>
                <Star size={16} />
                <span>{module.priority}</span>
              </div>
            </div>
          </div>
        </div>
        
        {/* Progreso del Módulo */}
        <div className="mb-4">
          <div className="flex justify-between text-sm mb-1">
            <span>Progreso del módulo</span>
            <span>{completedVideos.size} / {module.lessons[0].primary_resource.videos.length} videos</span>
          </div>
          <div className="w-full bg-blue-200 rounded-full h-2">
            <div 
              className="bg-white h-2 rounded-full transition-all duration-300"
              style={{ width: `${(completedVideos.size / module.lessons[0].primary_resource.videos.length) * 100}%` }}
            ></div>
          </div>
        </div>
        
        {/* Justificación */}
        <div className="bg-blue-700/50 rounded-lg p-3">
          <p className="text-sm text-blue-100">{module.justification}</p>
        </div>
      </div>
      
      {/* Navegación de Videos */}
      <div className="bg-gray-50 p-4 border-b">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <button
              onClick={previousVideo}
              disabled={currentVideoIndex === 0}
              className="p-2 rounded-lg bg-white shadow-sm disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
            >
              <SkipBack size={16} />
            </button>
            
            <span className="text-sm text-gray-600">
              Video {currentVideoIndex + 1} de {module.lessons[0].primary_resource.videos.length}
            </span>
            
            <button
              onClick={nextVideo}
              disabled={currentVideoIndex === module.lessons[0].primary_resource.videos.length - 1}
              className="p-2 rounded-lg bg-white shadow-sm disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
            >
              <SkipForward size={16} />
            </button>
          </div>
          
          <div className="flex items-center space-x-4 text-sm text-gray-600">
            <div className="flex items-center space-x-1">
              <Clock size={14} />
              <span>{currentVideo.duration_minutes} min</span>
            </div>
            <div className="flex items-center space-x-1">
              <Target size={14} />
              <span>{currentVideo.difficulty}/5</span>
            </div>
            <div className="flex items-center space-x-1">
              <BookOpen size={14} />
              <span>{currentVideo.learning_style}</span>
            </div>
          </div>
        </div>
      </div>
      
      {/* Video Player */}
      <div className="p-6">
        <div className="mb-4">
          <h3 className="text-xl font-semibold text-gray-800 mb-2">{currentVideo.title}</h3>
          <p className="text-gray-600 text-sm mb-4">{currentVideo.description}</p>
          
          {/* Progreso del Video Actual */}
          <div className="mb-4">
            <div className="flex justify-between text-sm text-gray-600 mb-1">
              <span>Progreso del video</span>
              <span>{Math.round(currentVideoProgress)}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div 
                className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                style={{ width: `${currentVideoProgress}%` }}
              ></div>
            </div>
          </div>
        </div>
        
        {/* YouTube Embed */}
        <div className="relative bg-gray-900 rounded-lg overflow-hidden mb-6">
          <div className="aspect-video">
            <iframe
              src={`${currentVideo.embed_url}?enablejsapi=1&origin=${window.location.origin}`}
              title={currentVideo.title}
              className="w-full h-full"
              allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
              allowFullScreen
            ></iframe>
          </div>
          
          {/* Overlay de Controles */}
          <div className="absolute inset-0 bg-black/20 opacity-0 hover:opacity-100 transition-opacity duration-300">
            <div className="absolute bottom-4 left-4 right-4">
              <div className="flex items-center justify-between text-white">
                <div className="flex items-center space-x-2">
                  <button className="p-2 bg-black/50 rounded-full hover:bg-black/70">
                    <Play size={20} />
                  </button>
                  <span className="text-sm">{formatTime(currentTime)} / {formatTime(duration)}</span>
                </div>
                
                <div className="flex items-center space-x-2">
                  <button className="p-2 bg-black/50 rounded-full hover:bg-black/70">
                    <Volume2 size={16} />
                  </button>
                  <button className="p-2 bg-black/50 rounded-full hover:bg-black/70">
                    <Maximize size={16} />
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        {/* Información del Video */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Detalles del Video */}
          <div className="bg-gray-50 rounded-lg p-4">
            <h4 className="font-semibold text-gray-800 mb-3">Detalles del Video</h4>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-600">Duración:</span>
                <span className="font-medium">{currentVideo.duration_minutes} minutos</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Calidad:</span>
                <span className="font-medium">{currentVideo.quality}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Área:</span>
                <span className="font-medium">{currentVideo.area_evaluada}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Estilo de Aprendizaje:</span>
                <span className="font-medium capitalize">{currentVideo.learning_style}</span>
              </div>
            </div>
          </div>
          
          {/* Próximos Pasos */}
          <div className="bg-blue-50 rounded-lg p-4">
            <h4 className="font-semibold text-blue-800 mb-3">Próximos Pasos</h4>
            <div className="space-y-2 text-sm text-blue-700">
              <div className="flex items-center space-x-2">
                <CheckCircle size={16} className="text-blue-600" />
                <span>Completar este video</span>
              </div>
              <div className="flex items-center space-x-2">
                <Target size={16} className="text-blue-600" />
                <span>Practicar con {module.lessons[0].exercises.count} ejercicios</span>
              </div>
              <div className="flex items-center space-x-2">
                <Clock size={16} className="text-blue-600" />
                <span>Dedicar {module.lessons[0].exercises.estimated_time_minutes} min a ejercicios</span>
              </div>
            </div>
          </div>
        </div>
        
        {/* Lista de Videos del Módulo */}
        <div className="mt-6">
          <h4 className="font-semibold text-gray-800 mb-3">Videos del Módulo</h4>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {module.lessons[0].primary_resource.videos.map((video, index) => (
              <div
                key={video.video_id}
                className={`p-4 rounded-lg border-2 cursor-pointer transition-all duration-200 ${
                  index === currentVideoIndex
                    ? 'border-blue-500 bg-blue-50'
                    : completedVideos.has(video.video_id)
                    ? 'border-green-500 bg-green-50'
                    : 'border-gray-200 bg-white hover:border-gray-300'
                }`}
                onClick={() => {
                  setCurrentVideoIndex(index);
                  setCurrentVideo(video);
                  setCurrentTime(0);
                  setCurrentVideoProgress(0);
                }}
              >
                <div className="flex items-start space-x-3">
                  <div className="flex-shrink-0">
                    {completedVideos.has(video.video_id) ? (
                      <div className="w-8 h-8 bg-green-500 rounded-full flex items-center justify-center">
                        <CheckCircle size={16} className="text-white" />
                      </div>
                    ) : (
                      <div className="w-8 h-8 bg-gray-200 rounded-full flex items-center justify-center text-sm font-medium">
                        {index + 1}
                      </div>
                    )}
                  </div>
                  
                  <div className="flex-1 min-w-0">
                    <h5 className="font-medium text-gray-800 text-sm mb-1 line-clamp-2">
                      {video.title}
                    </h5>
                    <div className="flex items-center space-x-4 text-xs text-gray-500">
                      <span>{video.duration_minutes} min</span>
                      <span>{video.difficulty}/5</span>
                      <span className="capitalize">{video.learning_style}</span>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default YMLVideoPlayer;
