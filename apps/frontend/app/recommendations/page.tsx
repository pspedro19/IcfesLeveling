'use client';

import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'next/navigation';
import { motion } from 'framer-motion';
import { Play, Clock, Star, BookOpen, Target, CheckCircle, XCircle } from 'lucide-react';

interface VideoRecommendation {
  video_id: string;
  youtube_id: string;
  youtube_url: string;
  title: string;
  channel_name: string;
  duration_minutes: number;
  relevance_score: number;
  reason: string;
  topic_match: string;
}

interface StudyRecommendation {
  recommendation_id: string;
  subject_name: string;
  total_failed_questions: number;
  priority_topics: string[];
  recommended_videos: VideoRecommendation[];
  study_plan_summary: string;
  estimated_study_time_hours: number;
  created_at: string;
}

export default function RecommendationsPage() {
  const searchParams = useSearchParams();
  const testId = searchParams.get('test_id');
  
  const [recommendation, setRecommendation] = useState<StudyRecommendation | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedVideo, setSelectedVideo] = useState<VideoRecommendation | null>(null);
  const [completedVideos, setCompletedVideos] = useState<Set<string>>(new Set());
  const [generatingRecommendations, setGeneratingRecommendations] = useState(false);

  useEffect(() => {
    if (testId) {
      generateRecommendations();
    } else {
      loadExistingRecommendations();
    }
  }, [testId]);

  const generateRecommendations = async () => {
    try {
      setGeneratingRecommendations(true);
      setLoading(true);
      
      // Simular preguntas falladas para demostración
      const mockFailedQuestions = [
        {
          question_id: "949b6886-7278-43df-bf26-124aabc9301f",
          user_answer: "A",
          correct_answer: "D",
          topic: "Potencias de 10",
          difficulty: 5,
          response_time_ms: 45000
        },
        {
          question_id: "64c83e82-84b7-43d8-9f52-d431713ced75",
          user_answer: "B",
          correct_answer: "A",
          topic: "Equivalencias notación científica",
          difficulty: 4,
          response_time_ms: 38000
        }
      ];

      const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:4000';
      const token = localStorage.getItem('access_token');
      
      const response = await fetch(`${API_URL}/api/v1/intelligent-recommendations/generate-from-diagnostic`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          test_id: testId,
          failed_questions: mockFailedQuestions,
          user_level: 1,
          preferred_duration_minutes: 30
        })
      });

      if (response.ok) {
        const data = await response.json();
        setRecommendation(data);
        setError(null);
      } else {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Error generando recomendaciones');
      }
    } catch (err: any) {
      console.error('Error generating recommendations:', err);
      setError(err.message || 'Error generando recomendaciones');
    } finally {
      setLoading(false);
      setGeneratingRecommendations(false);
    }
  };

  const loadExistingRecommendations = async () => {
    try {
      setLoading(true);
      const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:4000';
      const token = localStorage.getItem('access_token');
      const currentUser = JSON.parse(localStorage.getItem('currentUser') || '{}');
      
      const response = await fetch(`${API_URL}/api/v1/intelligent-recommendations/user-recommendations/${currentUser.id}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        if (data.active_recommendations && data.active_recommendations.length > 0) {
          // Cargar detalles de la primera recomendación activa
          const firstRec = data.active_recommendations[0];
          await loadRecommendationDetails(firstRec.recommendation_id);
        } else {
          setError('No tienes recomendaciones activas. Completa un diagnóstico para generar recomendaciones personalizadas.');
        }
      } else {
        throw new Error('Error cargando recomendaciones');
      }
    } catch (err: any) {
      console.error('Error loading recommendations:', err);
      setError(err.message || 'Error cargando recomendaciones');
      setLoading(false);
    }
  };

  const loadRecommendationDetails = async (recommendationId: string) => {
    try {
      const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:4000';
      const token = localStorage.getItem('access_token');
      
      const response = await fetch(`${API_URL}/api/v1/intelligent-recommendations/recommendation-details/${recommendationId}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        
        // Transformar datos para compatibilidad
        const transformedRec: StudyRecommendation = {
          recommendation_id: data.recommendation_id,
          subject_name: data.subject_name,
          total_failed_questions: data.units?.length || 0,
          priority_topics: data.priority_topics || [],
          recommended_videos: data.units?.map((unit: any) => ({
            video_id: unit.video?.video_id || '',
            youtube_id: unit.video?.youtube_id || '',
            youtube_url: unit.video?.youtube_url || '',
            title: unit.unit_name || '',
            channel_name: unit.video?.channel || 'Canal Educativo',
            duration_minutes: unit.video?.duration_minutes || 15,
            relevance_score: unit.video?.relevance_score || 0.8,
            reason: unit.video?.reason || 'Video recomendado',
            topic_match: unit.video?.topic_match || 'General'
          })) || [],
          study_plan_summary: data.summary || '',
          estimated_study_time_hours: Math.ceil((data.units?.length || 0) * 0.5),
          created_at: new Date().toISOString()
        };
        
        setRecommendation(transformedRec);
        
        // Marcar videos completados
        const completed = new Set<string>();
        data.units?.forEach((unit: any) => {
          if (unit.is_completed) {
            completed.add(unit.video?.youtube_id || '');
          }
        });
        setCompletedVideos(completed);
        
        setError(null);
      } else {
        throw new Error('Error cargando detalles de recomendación');
      }
    } catch (err: any) {
      console.error('Error loading recommendation details:', err);
      setError(err.message || 'Error cargando detalles');
    } finally {
      setLoading(false);
    }
  };

  const markVideoCompleted = async (video: VideoRecommendation, unitNumber: number) => {
    try {
      const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:4000';
      const token = localStorage.getItem('access_token');
      
      const response = await fetch(
        `${API_URL}/api/v1/intelligent-recommendations/mark-video-completed/${recommendation?.recommendation_id}/${unitNumber}`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      );

      if (response.ok) {
        const data = await response.json();
        setCompletedVideos(prev => new Set([...prev, video.youtube_id]));
        
        // Mostrar notificación de XP ganado
        alert(`¡Video completado! +${data.xp_gained} XP ganados`);
      } else {
        throw new Error('Error marcando video como completado');
      }
    } catch (err: any) {
      console.error('Error marking video completed:', err);
      alert('Error marcando video como completado');
    }
  };

  const openVideoModal = (video: VideoRecommendation) => {
    setSelectedVideo(video);
  };

  const closeVideoModal = () => {
    setSelectedVideo(null);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 text-white flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-gold-400 mx-auto mb-4"></div>
          <h2 className="text-2xl font-bold mb-2">
            {generatingRecommendations ? '🧠 Generando Recomendaciones Inteligentes...' : '📊 Cargando Recomendaciones...'}
          </h2>
          <p className="text-purple-200">
            {generatingRecommendations ? 'Analizando tus errores con IA para crear el plan perfecto' : 'Obteniendo tu plan de estudio personalizado'}
          </p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 text-white flex items-center justify-center p-4">
        <div className="text-center max-w-md">
          <XCircle className="w-16 h-16 text-red-400 mx-auto mb-4" />
          <h2 className="text-2xl font-bold mb-4">Error</h2>
          <p className="text-red-200 mb-6">{error}</p>
          <button
            onClick={() => window.location.href = '/diagnostic-test'}
            className="bg-purple-600 hover:bg-purple-700 px-6 py-3 rounded-lg font-semibold transition-colors"
          >
            Realizar Diagnóstico
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
          <p className="text-purple-200">Completa un diagnóstico para generar recomendaciones personalizadas</p>
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
            🧠 Recomendaciones Inteligentes
          </h1>
          <p className="text-xl text-purple-200">
            Plan personalizado para {recommendation.subject_name}
          </p>
          <div className="flex justify-center gap-6 mt-4 text-sm">
            <div className="bg-purple-800/50 px-4 py-2 rounded-lg">
              <Target className="w-4 h-4 inline mr-2" />
              {recommendation.total_failed_questions} preguntas a reforzar
            </div>
            <div className="bg-blue-800/50 px-4 py-2 rounded-lg">
              <Clock className="w-4 h-4 inline mr-2" />
              {recommendation.estimated_study_time_hours} horas estimadas
            </div>
            <div className="bg-green-800/50 px-4 py-2 rounded-lg">
              <Star className="w-4 h-4 inline mr-2" />
              {recommendation.recommended_videos.length} videos curados
            </div>
          </div>
        </motion.div>

        {/* Priority Topics */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="mb-8"
        >
          <h2 className="text-2xl font-bold mb-4 flex items-center">
            <Target className="w-6 h-6 mr-2 text-gold-400" />
            Temas Prioritarios
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {recommendation.priority_topics.map((topic, index) => (
              <div
                key={index}
                className="bg-gradient-to-r from-purple-800/50 to-blue-800/50 p-4 rounded-lg border border-purple-500/30"
              >
                <div className="text-gold-400 font-semibold">#{index + 1}</div>
                <div className="text-white">{topic}</div>
              </div>
            ))}
          </div>
        </motion.div>

        {/* Recommended Videos */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="mb-8"
        >
          <h2 className="text-2xl font-bold mb-4 flex items-center">
            <Play className="w-6 h-6 mr-2 text-gold-400" />
            Videos Recomendados ({recommendation.recommended_videos.length})
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
                    isCompleted ? 'border-green-500/50' : 'border-purple-500/30'
                  } hover:border-gold-500/50 transition-all cursor-pointer group`}
                  onClick={() => openVideoModal(video)}
                >
                  {/* Video Thumbnail */}
                  <div className="relative mb-4">
                    <img
                      src={`https://img.youtube.com/vi/${video.youtube_id}/maxresdefault.jpg`}
                      alt={video.title}
                      className="w-full h-32 object-cover rounded-lg"
                      onError={(e) => {
                        e.currentTarget.src = `https://img.youtube.com/vi/${video.youtube_id}/hqdefault.jpg`;
                      }}
                    />
                    <div className="absolute inset-0 bg-black/50 rounded-lg flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                      <Play className="w-12 h-12 text-white" />
                    </div>
                    
                    {isCompleted && (
                      <div className="absolute top-2 right-2 bg-green-500 rounded-full p-1">
                        <CheckCircle className="w-4 h-4 text-white" />
                      </div>
                    )}
                  </div>

                  {/* Video Info */}
                  <h3 className="font-bold text-white mb-2 line-clamp-2">
                    {video.title}
                  </h3>
                  
                  <div className="text-sm text-purple-200 mb-2">
                    📺 {video.channel_name}
                  </div>
                  
                  <div className="flex justify-between items-center mb-3">
                    <div className="text-sm text-blue-300">
                      <Clock className="w-4 h-4 inline mr-1" />
                      {video.duration_minutes} min
                    </div>
                    <div className="text-sm text-gold-300">
                      <Star className="w-4 h-4 inline mr-1" />
                      {(video.relevance_score * 100).toFixed(0)}% relevante
                    </div>
                  </div>
                  
                  <div className="text-xs text-gray-300 mb-3">
                    🎯 {video.reason}
                  </div>
                  
                  <div className="text-xs bg-purple-800/50 px-2 py-1 rounded">
                    📚 {video.topic_match}
                  </div>
                  
                  {!isCompleted && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        markVideoCompleted(video, index + 1);
                      }}
                      className="w-full mt-3 bg-green-600 hover:bg-green-700 py-2 rounded-lg text-sm font-semibold transition-colors"
                    >
                      Marcar como Visto
                    </button>
                  )}
                </motion.div>
              );
            })}
          </div>
        </motion.div>

        {/* Study Plan Summary */}
        {recommendation.study_plan_summary && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.6 }}
            className="bg-gradient-to-r from-purple-900/50 to-blue-900/50 rounded-xl p-6 border border-purple-500/30"
          >
            <h2 className="text-2xl font-bold mb-4 flex items-center">
              <BookOpen className="w-6 h-6 mr-2 text-gold-400" />
              Plan de Estudio Detallado
            </h2>
            <div className="prose prose-invert max-w-none">
              <pre className="whitespace-pre-wrap text-purple-100 font-mono text-sm">
                {recommendation.study_plan_summary}
              </pre>
            </div>
          </motion.div>
        )}
      </div>

      {/* Video Modal */}
      {selectedVideo && (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
          <div className="bg-gray-900 rounded-xl p-6 max-w-4xl w-full max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-xl font-bold text-white">{selectedVideo.title}</h3>
              <button
                onClick={closeVideoModal}
                className="text-gray-400 hover:text-white text-2xl"
              >
                ×
              </button>
            </div>
            
            <div className="aspect-video mb-4">
              <iframe
                src={`https://www.youtube.com/embed/${selectedVideo.youtube_id}`}
                title={selectedVideo.title}
                className="w-full h-full rounded-lg"
                allowFullScreen
              />
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
              <div>
                <strong className="text-purple-300">Canal:</strong> {selectedVideo.channel_name}
              </div>
              <div>
                <strong className="text-purple-300">Duración:</strong> {selectedVideo.duration_minutes} minutos
              </div>
              <div>
                <strong className="text-purple-300">Relevancia:</strong> {(selectedVideo.relevance_score * 100).toFixed(0)}%
              </div>
              <div>
                <strong className="text-purple-300">Tema:</strong> {selectedVideo.topic_match}
              </div>
            </div>
            
            <div className="mt-4 p-3 bg-purple-800/30 rounded-lg">
              <strong className="text-purple-300">Por qué es recomendado:</strong>
              <p className="text-white mt-1">{selectedVideo.reason}</p>
            </div>
            
            {!completedVideos.has(selectedVideo.youtube_id) && (
              <button
                onClick={() => {
                  const unitNumber = recommendation.recommended_videos.findIndex(v => v.youtube_id === selectedVideo.youtube_id) + 1;
                  markVideoCompleted(selectedVideo, unitNumber);
                  closeVideoModal();
                }}
                className="w-full mt-4 bg-green-600 hover:bg-green-700 py-3 rounded-lg font-semibold transition-colors"
              >
                ✅ Marcar como Completado
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
}


