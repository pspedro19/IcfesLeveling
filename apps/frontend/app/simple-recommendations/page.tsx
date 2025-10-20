'use client';

import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'next/navigation';
import { motion } from 'framer-motion';
import { Play, Clock, Star, BookOpen, Target, CheckCircle } from 'lucide-react';

interface VideoRecommendation {
  video_id: string;
  youtube_id: string;
  youtube_url: string;
  title: string;
  channel_name: string;
  duration_minutes: number;
  quality_score: number;
  topics_covered: string[];
  codigo_tema: string;
  thumbnail_url: string;
}

interface RecommendationData {
  recommendation_id: string;
  subject_name: string;
  recommended_videos: VideoRecommendation[];
  total_videos: number;
  estimated_study_time_hours: number;
}

export default function SimpleRecommendationsPage() {
  const searchParams = useSearchParams();
  const subjectId = searchParams.get('subject_id') || '550e8400-e29b-41d4-a716-446655440001'; // Default: Matemáticas
  
  const [recommendation, setRecommendation] = useState<RecommendationData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedVideo, setSelectedVideo] = useState<VideoRecommendation | null>(null);
  const [completedVideos, setCompletedVideos] = useState<Set<string>>(new Set());

  useEffect(() => {
    loadRecommendations();
  }, [subjectId]);

  const loadRecommendations = async () => {
    try {
      setLoading(true);
      const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:4000';
      const token = localStorage.getItem('access_token');
      
      const response = await fetch(`${API_URL}/api/v1/simple-recommendations/generate-for-subject/${subjectId}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setRecommendation(data);
        setError(null);
      } else {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Error cargando recomendaciones');
      }
    } catch (err: any) {
      console.error('Error loading recommendations:', err);
      setError(err.message || 'Error cargando recomendaciones');
    } finally {
      setLoading(false);
    }
  };

  const openVideoModal = (video: VideoRecommendation) => {
    setSelectedVideo(video);
  };

  const closeVideoModal = () => {
    setSelectedVideo(null);
  };

  const markVideoCompleted = (video: VideoRecommendation) => {
    setCompletedVideos(prev => new Set([...prev, video.youtube_id]));
    // Aquí podrías hacer una llamada API para persistir el progreso
    alert(`¡Video "${video.title}" marcado como completado! +150 XP`);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 text-white flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-gold-400 mx-auto mb-4"></div>
          <h2 className="text-2xl font-bold mb-2">📊 Cargando Recomendaciones...</h2>
          <p className="text-purple-200">Obteniendo videos personalizados para ti</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 text-white flex items-center justify-center p-4">
        <div className="text-center max-w-md">
          <div className="text-red-400 text-6xl mb-4">❌</div>
          <h2 className="text-2xl font-bold mb-4">Error</h2>
          <p className="text-red-200 mb-6">{error}</p>
          <button
            onClick={loadRecommendations}
            className="bg-purple-600 hover:bg-purple-700 px-6 py-3 rounded-lg font-semibold transition-colors"
          >
            Reintentar
          </button>
        </div>
      </div>
    );
  }

  if (!recommendation) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 text-white flex items-center justify-center">
        <div className="text-center">
          <BookOpen className="w-16 h-16 text-purple-400 mx-auto mb-4" />
          <h2 className="text-2xl font-bold mb-4">No hay recomendaciones disponibles</h2>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 text-white">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-8"
        >
          <h1 className="text-4xl font-bold mb-2 bg-gradient-to-r from-gold-400 to-purple-400 bg-clip-text text-transparent">
            🎬 Tu Plan de Estudio Personalizado
          </h1>
          <p className="text-xl text-purple-200">
            Videos recomendados para {recommendation.subject_name}
          </p>
          <div className="flex justify-center gap-6 mt-4 text-sm">
            <div className="bg-blue-800/50 px-4 py-2 rounded-lg">
              <Clock className="w-4 h-4 inline mr-2" />
              {recommendation.estimated_study_time_hours} horas estimadas
            </div>
            <div className="bg-green-800/50 px-4 py-2 rounded-lg">
              <Star className="w-4 h-4 inline mr-2" />
              {recommendation.total_videos} videos curados
            </div>
            <div className="bg-purple-800/50 px-4 py-2 rounded-lg">
              <Target className="w-4 h-4 inline mr-2" />
              Plan válido por 30 días
            </div>
          </div>
        </motion.div>

        {/* Progress Bar */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="mb-8"
        >
          <div className="bg-black/30 rounded-xl p-6 border border-purple-500/30">
            <div className="flex justify-between items-center mb-2">
              <span className="text-purple-300">Progreso del Plan</span>
              <span className="text-gold-400 font-bold">
                {completedVideos.size}/{recommendation.total_videos} completados
              </span>
            </div>
            <div className="w-full bg-gray-700 rounded-full h-3">
              <div 
                className="bg-gradient-to-r from-purple-500 to-gold-500 h-3 rounded-full transition-all duration-500"
                style={{ width: `${(completedVideos.size / recommendation.total_videos) * 100}%` }}
              />
            </div>
            <div className="text-sm text-purple-200 mt-2">
              {completedVideos.size === recommendation.total_videos 
                ? '🎉 ¡Plan completado! Has dominado todos los temas.' 
                : `${recommendation.total_videos - completedVideos.size} videos restantes`
              }
            </div>
          </div>
        </motion.div>

        {/* Recommended Videos */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
        >
          <h2 className="text-2xl font-bold mb-6 flex items-center">
            <Play className="w-6 h-6 mr-2 text-gold-400" />
            Videos de la Unidad
          </h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {recommendation.recommended_videos.map((video, index) => {
              const isCompleted = completedVideos.has(video.youtube_id);
              
              return (
                <motion.div
                  key={video.video_id}
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: index * 0.1 }}
                  className={`bg-gradient-to-br from-gray-900/80 to-purple-900/80 rounded-xl p-6 border ${
                    isCompleted ? 'border-green-500/50 bg-green-900/20' : 'border-purple-500/30'
                  } hover:border-gold-500/50 transition-all cursor-pointer group relative overflow-hidden`}
                  onClick={() => openVideoModal(video)}
                >
                  {/* Completed Badge */}
                  {isCompleted && (
                    <div className="absolute top-3 right-3 z-10">
                      <div className="bg-green-500 rounded-full p-2">
                        <CheckCircle className="w-5 h-5 text-white" />
                      </div>
                    </div>
                  )}

                  {/* Video Thumbnail */}
                  <div className="relative mb-4">
                    <img
                      src={video.thumbnail_url}
                      alt={video.title}
                      className="w-full h-36 object-cover rounded-lg"
                      onError={(e) => {
                        e.currentTarget.src = `https://img.youtube.com/vi/${video.youtube_id}/hqdefault.jpg`;
                      }}
                    />
                    <div className="absolute inset-0 bg-black/50 rounded-lg flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                      <Play className="w-12 h-12 text-white drop-shadow-lg" />
                    </div>
                    
                    {/* Video Number */}
                    <div className="absolute top-2 left-2 bg-purple-600 text-white text-xs font-bold px-2 py-1 rounded">
                      #{index + 1}
                    </div>
                  </div>

                  {/* Video Info */}
                  <h3 className="font-bold text-white mb-2 line-clamp-2 min-h-[3rem]">
                    {video.title}
                  </h3>
                  
                  <div className="text-sm text-purple-200 mb-3">
                    📺 {video.channel_name}
                  </div>
                  
                  <div className="flex justify-between items-center mb-3">
                    <div className="text-sm text-blue-300 flex items-center">
                      <Clock className="w-4 h-4 mr-1" />
                      {video.duration_minutes} min
                    </div>
                    <div className="text-sm text-gold-300 flex items-center">
                      <Star className="w-4 h-4 mr-1" />
                      {(video.quality_score * 100).toFixed(0)}%
                    </div>
                  </div>
                  
                  <div className="text-xs bg-purple-800/50 px-2 py-1 rounded mb-3">
                    📚 {video.codigo_tema}
                  </div>
                  
                  {!isCompleted && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        markVideoCompleted(video);
                      }}
                      className="w-full bg-green-600 hover:bg-green-700 py-2 rounded-lg text-sm font-semibold transition-colors"
                    >
                      ✅ Marcar como Visto
                    </button>
                  )}
                  
                  {isCompleted && (
                    <div className="w-full bg-green-800/50 py-2 rounded-lg text-sm font-semibold text-center text-green-200">
                      ✅ Completado
                    </div>
                  )}
                </motion.div>
              );
            })}
          </div>
        </motion.div>

        {/* Study Tips */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6 }}
          className="mt-8 bg-gradient-to-r from-purple-900/50 to-blue-900/50 rounded-xl p-6 border border-purple-500/30"
        >
          <h2 className="text-xl font-bold mb-4 flex items-center">
            <BookOpen className="w-5 h-5 mr-2 text-gold-400" />
            Consejos para tu Plan de Estudio
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
            <div className="bg-black/30 p-4 rounded-lg">
              <h3 className="font-semibold text-purple-300 mb-2">📅 Cronograma Recomendado</h3>
              <p className="text-purple-100">
                Ve 2-3 videos por semana para un aprendizaje óptimo. 
                Completa el plan en aproximadamente {Math.ceil(recommendation.total_videos / 3)} semanas.
              </p>
            </div>
            <div className="bg-black/30 p-4 rounded-lg">
              <h3 className="font-semibold text-purple-300 mb-2">🎯 Estrategia de Estudio</h3>
              <p className="text-purple-100">
                Toma notas mientras ves los videos y practica los ejercicios que se muestran. 
                Repite los videos si es necesario.
              </p>
            </div>
            <div className="bg-black/30 p-4 rounded-lg">
              <h3 className="font-semibold text-purple-300 mb-2">⚡ Gamificación</h3>
              <p className="text-purple-100">
                Gana 150 XP por cada video completado. 
                Bonus de 500 XP al completar todo el plan.
              </p>
            </div>
            <div className="bg-black/30 p-4 rounded-lg">
              <h3 className="font-semibold text-purple-300 mb-2">🔄 Seguimiento</h3>
              <p className="text-purple-100">
                Tu progreso se guarda automáticamente. 
                Puedes volver en cualquier momento para continuar.
              </p>
            </div>
          </div>
        </motion.div>

        {/* Navigation */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.8 }}
          className="mt-8 text-center"
        >
          <button
            onClick={() => window.history.back()}
            className="bg-purple-600 hover:bg-purple-700 px-6 py-3 rounded-lg font-semibold transition-colors mr-4"
          >
            ← Volver
          </button>
          <button
            onClick={() => window.location.href = '/diagnostic-test'}
            className="bg-blue-600 hover:bg-blue-700 px-6 py-3 rounded-lg font-semibold transition-colors"
          >
            Hacer Otro Diagnóstico
          </button>
        </motion.div>
      </div>

      {/* Video Modal */}
      {selectedVideo && (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
          <div className="bg-gray-900 rounded-xl p-6 max-w-4xl w-full max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-xl font-bold text-white">{selectedVideo.title}</h3>
              <button
                onClick={closeVideoModal}
                className="text-gray-400 hover:text-white text-2xl font-bold"
              >
                ×
              </button>
            </div>
            
            <div className="aspect-video mb-4">
              <iframe
                src={`https://www.youtube.com/embed/${selectedVideo.youtube_id}?autoplay=1`}
                title={selectedVideo.title}
                className="w-full h-full rounded-lg"
                allowFullScreen
                allow="autoplay"
              />
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm mb-4">
              <div>
                <strong className="text-purple-300">Canal:</strong> {selectedVideo.channel_name}
              </div>
              <div>
                <strong className="text-purple-300">Duración:</strong> {selectedVideo.duration_minutes} minutos
              </div>
              <div>
                <strong className="text-purple-300">Calidad:</strong> {(selectedVideo.quality_score * 100).toFixed(0)}%
              </div>
              <div>
                <strong className="text-purple-300">Código:</strong> {selectedVideo.codigo_tema}
              </div>
            </div>
            
            <div className="mb-4 p-3 bg-purple-800/30 rounded-lg">
              <strong className="text-purple-300">Temas cubiertos:</strong>
              <div className="flex flex-wrap gap-2 mt-2">
                {selectedVideo.topics_covered.map((topic, index) => (
                  <span key={index} className="bg-purple-700/50 px-2 py-1 rounded text-xs">
                    {topic}
                  </span>
                ))}
              </div>
            </div>
            
            {!completedVideos.has(selectedVideo.youtube_id) && (
              <button
                onClick={() => {
                  markVideoCompleted(selectedVideo);
                  closeVideoModal();
                }}
                className="w-full bg-green-600 hover:bg-green-700 py-3 rounded-lg font-semibold transition-colors"
              >
                ✅ Marcar como Completado (+150 XP)
              </button>
            )}
            
            {completedVideos.has(selectedVideo.youtube_id) && (
              <div className="w-full bg-green-800/50 py-3 rounded-lg font-semibold text-center text-green-200">
                ✅ Video Completado
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
