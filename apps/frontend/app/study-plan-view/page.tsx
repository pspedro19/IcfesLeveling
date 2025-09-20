'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { Play, Clock, Trophy, CheckCircle, BookOpen, Target, Calendar, TrendingUp } from 'lucide-react';

interface Video {
  id: string;
  title: string;
  url: string;
  duration_minutes?: number;
  xp: number;
}

interface Unit {
  unit_number: number;
  title: string;
  description: string;
  videos: Video[];
  exercises?: any[];
}

interface StudyPlan {
  units: Unit[];
  metadata?: any;
  summary?: {
    total_units: number;
    total_videos: number;
    total_xp: number;
  };
}

export default function StudyPlanView() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const [plan, setPlan] = useState<StudyPlan | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedUnit, setSelectedUnit] = useState(0);
  const [completedVideos, setCompletedVideos] = useState<Set<string>>(new Set());
  const [selectedVideo, setSelectedVideo] = useState<Video | null>(null);
  const [showVideoModal, setShowVideoModal] = useState(false);

  // Error boundary for component rendering
  const [renderError, setRenderError] = useState<string | null>(null);

  const planId = searchParams.get('plan_id');
  const subjectId = searchParams.get('subject');
  const testId = searchParams.get('test_id');

  const fetchStudyPlan = useCallback(async () => {
    try {
      setLoading(true);
      const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:4000';
      
      // Primero intentar obtener el plan por ID (test ID from diagnostic)
      if (planId) {
        const response = await fetch(`${API_URL}/api/v1/diagnostic-public/study-plan/view/${planId}`);
        if (response.ok) {
          const data = await response.json();
          setPlan(data);
          setLoading(false);
          return;
        }
      }
      
      // Si no hay plan_id o falla, obtener unidades por materia
      if (subjectId) {
        // Construir URL con test_id si está disponible para recomendaciones personalizadas
        const url = testId
          ? `${API_URL}/api/v1/diagnostic-public/study-plan/units/by-subject/${subjectId}?test_id=${testId}`
          : `${API_URL}/api/v1/diagnostic-public/study-plan/units/by-subject/${subjectId}`;

        console.log(`🎯 Fetching study plan: ${url}`);
        const response = await fetch(url);
        if (response.ok) {
          const data = await response.json();
          console.log('📊 Study plan response:', data);
          setPlan({ units: data.units, summary: data });
          setLoading(false);
          return;
        }
      }
      
      setError('No se pudo cargar el plan de estudio');
      setLoading(false);
    } catch (err) {
      console.error('Error fetching study plan:', err);
      setError('Error al cargar el plan de estudio');
      setLoading(false);
    }
  }, [planId, subjectId, testId]);

  useEffect(() => {
    fetchStudyPlan();
  }, [fetchStudyPlan]);

  const handleVideoClick = (video: Video) => {
    // Mostrar el video en el modal con iframe
    setSelectedVideo(video);
    setShowVideoModal(true);
  };

  const handleVideoComplete = () => {
    if (selectedVideo) {
      // Marcar como completado
      setCompletedVideos(prev => new Set(prev).add(selectedVideo.id));
      
      // Enviar progreso al backend
      trackVideoProgress(selectedVideo.id);
      
      // Cerrar modal
      setShowVideoModal(false);
      setSelectedVideo(null);
    }
  };

  const getYouTubeEmbedUrl = (url: string) => {
    if (!url) return '';
    try {
      // Convertir URL de YouTube a formato embed
      const videoId = url.includes('v=') ? url.split('v=')[1]?.split('&')[0] : url.split('/').pop();
      if (!videoId) return '';
      return `https://www.youtube.com/embed/${videoId}?rel=0&modestbranding=1&fs=1&cc_load_policy=1`;
    } catch (error) {
      console.error('Error processing YouTube URL:', error);
      return '';
    }
  };

  const trackVideoProgress = async (videoId: string) => {
    if (!videoId) return;
    
    try {
      const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:4000';
      await fetch(`${API_URL}/api/v1/video-progress/track`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ video_id: videoId, completed: true })
      });
    } catch (err) {
      console.error('Error tracking progress:', err);
    }
  };

  const calculateProgress = () => {
    if (!plan?.units || plan.units.length === 0) return 0;
    try {
      const totalVideos = plan.units.reduce((acc, unit) => {
        return acc + (unit?.videos?.length || 0);
      }, 0);
      if (totalVideos === 0) return 0;
      return Math.round((completedVideos.size / totalVideos) * 100);
    } catch (error) {
      console.error('Error calculating progress:', error);
      return 0;
    }
  };

  const getTotalXP = () => {
    if (!plan?.units || plan.units.length === 0) return 0;
    try {
      return plan.units.reduce((acc, unit) => {
        if (!unit?.videos) return acc;
        return acc + unit.videos
          .filter(v => v?.id && completedVideos.has(v.id))
          .reduce((sum, v) => sum + (v?.xp || 0), 0);
      }, 0);
    } catch (error) {
      console.error('Error calculating total XP:', error);
      return 0;
    }
  };

  // Handle render errors
  if (renderError) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 flex items-center justify-center">
        <div className="text-center bg-red-900/30 p-8 rounded-lg">
          <h1 className="text-2xl font-bold text-red-400 mb-4">Error de renderizado</h1>
          <p className="text-red-300">{renderError}</p>
          <button
            onClick={() => {
              setRenderError(null);
              window.location.reload();
            }}
            className="mt-4 px-6 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg"
          >
            Recargar página
          </button>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-yellow-400 mx-auto mb-4"></div>
          <p className="text-white text-lg">Cargando tu plan personalizado...</p>
        </div>
      </div>
    );
  }

  if (error || !plan || !plan.units || plan.units.length === 0) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 flex items-center justify-center">
        <div className="text-center bg-red-900/30 p-8 rounded-lg">
          <h1 className="text-2xl font-bold text-red-400 mb-4">Error</h1>
          <p className="text-red-300">{error || 'No hay unidades disponibles'}</p>
          <button
            onClick={() => router.push('/diagnostic-test')}
            className="mt-4 px-6 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg"
          >
            Volver al diagnóstico
          </button>
        </div>
      </div>
    );
  }

  const currentUnit = plan?.units?.[selectedUnit];
  const progress = calculateProgress();
  const totalXP = getTotalXP();

  try {
    return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900">
      {/* Header */}
      <div className="bg-black/30 backdrop-blur-sm border-b border-purple-500/30">
        <div className="container mx-auto px-4 py-6">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-3xl font-bold text-yellow-400 mb-2">
                🎯 Tu Plan de Estudio Personalizado
              </h1>
              <p className="text-purple-300">
                Basado en tu diagnóstico - {plan?.units?.length || 0} unidades disponibles
                {plan?.summary?.personalized && (
                  <span className="ml-2 px-2 py-1 bg-green-600/50 text-green-200 rounded-full text-xs">
                    🎯 Personalizado
                  </span>
                )}
              </p>
              {plan?.summary?.personalization_message && (
                <p className="text-blue-300 text-sm mt-1">
                  {plan.summary.personalization_message}
                </p>
              )}
            </div>
            <div className="flex gap-4">
              <div className="bg-purple-900/50 px-4 py-2 rounded-lg">
                <div className="text-yellow-400 text-2xl font-bold">{progress}%</div>
                <div className="text-purple-300 text-sm">Progreso</div>
              </div>
              <div className="bg-blue-900/50 px-4 py-2 rounded-lg">
                <div className="text-yellow-400 text-2xl font-bold">{totalXP}</div>
                <div className="text-purple-300 text-sm">XP Ganados</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="container mx-auto px-4 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Sidebar - Lista de Unidades */}
          <div className="lg:col-span-1">
            <div className="bg-black/30 backdrop-blur-sm rounded-lg border border-purple-500/30 p-4">
              <h2 className="text-xl font-bold text-yellow-400 mb-4 flex items-center gap-2">
                <BookOpen className="w-5 h-5" />
                Unidades
              </h2>
              <div className="space-y-2">
                {(plan?.units || []).map((unit, index) => {
                  if (!unit) return null;
                  const videos = unit.videos || [];
                  const unitCompleted = videos.length > 0 && videos.every(v => v?.id && completedVideos.has(v.id));
                  const unitProgress = videos.length > 0 
                    ? Math.round((videos.filter(v => v?.id && completedVideos.has(v.id)).length / videos.length) * 100)
                    : 0;
                  
                  return (
                    <button
                      key={unit.unit_number}
                      onClick={() => setSelectedUnit(index)}
                      className={`w-full text-left p-3 rounded-lg transition-all ${
                        selectedUnit === index
                          ? 'bg-purple-600/50 border border-yellow-400'
                          : 'bg-black/20 hover:bg-purple-800/30 border border-purple-500/20'
                      }`}
                    >
                      <div className="flex justify-between items-center mb-1">
                        <span className="text-white font-medium text-sm">
                          Unidad {unit.unit_number}
                        </span>
                        {unitCompleted && (
                          <CheckCircle className="w-4 h-4 text-green-400" />
                        )}
                      </div>
                      <div className="text-purple-300 text-xs mb-2">
                        {videos.length} videos
                      </div>
                      <div className="w-full bg-black/50 rounded-full h-2">
                        <div 
                          className="bg-gradient-to-r from-yellow-400 to-green-400 h-2 rounded-full transition-all"
                          style={{ width: `${unitProgress}%` }}
                        />
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>
          </div>

          {/* Main Content - Videos de la Unidad */}
          <div className="lg:col-span-3">
            {currentUnit && (
              <div className="bg-black/30 backdrop-blur-sm rounded-lg border border-purple-500/30 p-6">
                <div className="mb-6">
                  <h2 className="text-2xl font-bold text-yellow-400 mb-2 flex items-center gap-3">
                    🎯 {currentUnit.title}
                  </h2>
                  <p className="text-purple-300">
                    {currentUnit.description}
                  </p>
                  <div className="mt-2 text-sm text-blue-400">
                    Tema específico: Videos relacionados con {currentUnit.title.toLowerCase()}
                  </div>
                </div>

                {/* Videos */}
                <div className="space-y-4">
                  <h3 className="text-lg font-bold text-white mb-3 flex items-center gap-2">
                    <Play className="w-5 h-5 text-yellow-400" />
                    Videos de la Unidad
                  </h3>
                  
                  {(currentUnit?.videos || []).length > 0 ? (
                    (currentUnit?.videos || []).map((video, index) => {
                      if (!video) return null;
                      const isCompleted = video?.id && completedVideos.has(video.id);
                      
                      return (
                        <div
                          key={video.id}
                          className={`bg-black/40 rounded-lg p-4 border transition-all cursor-pointer hover:bg-purple-800/30 ${
                            isCompleted 
                              ? 'border-green-500/50' 
                              : 'border-purple-500/30'
                          }`}
                          onClick={() => handleVideoClick(video)}
                        >
                          <div className="flex justify-between items-start">
                            <div className="flex-1">
                              <div className="flex items-center gap-3 mb-2">
                                <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold ${
                                  isCompleted 
                                    ? 'bg-green-500 text-white' 
                                    : 'bg-purple-600 text-yellow-400'
                                }`}>
                                  {isCompleted ? '✓' : index + 1}
                                </div>
                                <h4 className="text-white font-medium">
                                  {video?.title || 'Video sin título'}
                                </h4>
                              </div>
                              
                              <div className="flex items-center gap-4 text-sm">
                                <span className="text-purple-300 flex items-center gap-1">
                                  <Clock className="w-4 h-4" />
                                  {video?.duration_minutes || Math.floor(Math.random() * 20 + 10)} min
                                </span>
                                <span className="text-yellow-400 flex items-center gap-1">
                                  <Trophy className="w-4 h-4" />
                                  {video?.xp || 0} XP
                                </span>
                                {video?.tema_principal && (
                                  <span className="text-blue-400 flex items-center gap-1 bg-blue-900/30 px-2 py-1 rounded">
                                    🎯 {video.tema_principal}
                                  </span>
                                )}
                                {video?.recommendation_reason && (
                                  <span className="text-green-400 text-xs bg-green-900/30 px-2 py-1 rounded">
                                    💡 {video.recommendation_reason}
                                  </span>
                                )}
                                {isCompleted && (
                                  <span className="text-green-400 text-xs">
                                    ✓ Completado
                                  </span>
                                )}
                              </div>
                            </div>
                            
                            <button className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg flex items-center gap-2 transition-colors">
                              <Play className="w-4 h-4" />
                              {isCompleted ? 'Revisar' : 'Ver'}
                            </button>
                          </div>
                        </div>
                      );
                    })
                  ) : (
                    <div className="text-center py-8 text-purple-300">
                      <p>No hay videos disponibles para esta unidad</p>
                      <button
                        onClick={() => router.push('/diagnostic-test')}
                        className="mt-4 px-6 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg"
                      >
                        Realizar nuevo diagnóstico
                      </button>
                    </div>
                  )}
                </div>

                {/* Ejercicios */}
                {currentUnit?.exercises && currentUnit.exercises.length > 0 && (
                  <div className="mt-8 pt-6 border-t border-purple-500/30">
                    <h3 className="text-lg font-bold text-white mb-3 flex items-center gap-2">
                      <Target className="w-5 h-5 text-yellow-400" />
                      Ejercicios de Práctica
                    </h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {currentUnit.exercises.map((exercise: any, index: number) => (
                        <div
                          key={index}
                          className="bg-black/40 rounded-lg p-4 border border-purple-500/30 hover:bg-purple-800/30 transition-all cursor-pointer"
                        >
                          <h4 className="text-white font-medium mb-2">
                            {exercise.title}
                          </h4>
                          <div className="flex justify-between items-center">
                            <span className="text-purple-300 text-sm">
                              {exercise.questions} preguntas
                            </span>
                            <span className="text-yellow-400 text-sm">
                              {exercise.xp} XP
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Resumen del Plan */}
        <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-black/30 backdrop-blur-sm rounded-lg border border-purple-500/30 p-6 text-center">
            <Calendar className="w-8 h-8 text-yellow-400 mx-auto mb-3" />
            <div className="text-2xl font-bold text-white mb-1">
              {Math.ceil((plan?.units?.length || 0) / 3)} semanas
            </div>
            <div className="text-purple-300">Duración estimada</div>
          </div>
          
          <div className="bg-black/30 backdrop-blur-sm rounded-lg border border-purple-500/30 p-6 text-center">
            <Trophy className="w-8 h-8 text-yellow-400 mx-auto mb-3" />
            <div className="text-2xl font-bold text-white mb-1">
              {plan?.summary?.total_xp || (plan?.units || []).reduce((acc, u) => {
                return acc + (u?.videos || []).reduce((s, v) => s + (v?.xp || 0), 0);
              }, 0)} XP
            </div>
            <div className="text-purple-300">Puntos totales</div>
          </div>
          
          <div className="bg-black/30 backdrop-blur-sm rounded-lg border border-purple-500/30 p-6 text-center">
            <TrendingUp className="w-8 h-8 text-yellow-400 mx-auto mb-3" />
            <div className="text-2xl font-bold text-white mb-1">
              {plan?.summary?.total_videos || (plan?.units || []).reduce((acc, u) => acc + (u?.videos?.length || 0), 0)} videos
            </div>
            <div className="text-purple-300">Contenido disponible</div>
          </div>
        </div>
      </div>

      {/* Modal de Video con iFrame */}
      {showVideoModal && selectedVideo && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 rounded-lg border border-purple-500/30 w-full max-w-6xl max-h-[90vh] overflow-hidden">
            {/* Header del Modal */}
            <div className="bg-black/30 p-4 border-b border-purple-500/30">
              <div className="flex justify-between items-center">
                <div>
                  <h3 className="text-xl font-bold text-yellow-400">
                    {selectedVideo?.title || 'Video sin título'}
                  </h3>
                  <div className="flex items-center gap-4 mt-2">
                    <span className="text-purple-300 text-sm flex items-center gap-1">
                      <Clock className="w-4 h-4" />
                      {selectedVideo?.duration_minutes || Math.floor(Math.random() * 20 + 10)} minutos
                    </span>
                    <span className="text-yellow-400 text-sm flex items-center gap-1">
                      <Trophy className="w-4 h-4" />
                      {selectedVideo?.xp || 0} XP
                    </span>
                  </div>
                </div>
                <button
                  onClick={() => setShowVideoModal(false)}
                  className="text-white hover:text-red-400 transition-colors text-2xl font-bold"
                >
                  ×
                </button>
              </div>
            </div>

            {/* iFrame del Video */}
            <div className="relative w-full" style={{ paddingBottom: '56.25%' }}>
              <iframe
                className="absolute top-0 left-0 w-full h-full"
                src={getYouTubeEmbedUrl(selectedVideo?.url || '')}
                title={selectedVideo?.title || 'Video'}
                frameBorder="0"
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
                allowFullScreen
              />
            </div>

            {/* Footer con botones */}
            <div className="bg-black/30 p-4 border-t border-purple-500/30">
              <div className="flex justify-between items-center">
                <div className="text-purple-300 text-sm">
                  💡 Tip: Completa el video para ganar {selectedVideo?.xp || 0} XP
                </div>
                <div className="flex gap-3">
                  <button
                    onClick={() => setShowVideoModal(false)}
                    className="px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-lg transition-colors"
                  >
                    Ver después
                  </button>
                  <button
                    onClick={handleVideoComplete}
                    className="px-6 py-2 bg-gradient-to-r from-green-500 to-green-600 hover:from-green-600 hover:to-green-700 text-white rounded-lg font-medium transition-all flex items-center gap-2"
                  >
                    <CheckCircle className="w-5 h-5" />
                    Marcar como completado
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
    );
  } catch (renderError: any) {
    console.error('Render error in StudyPlanView:', renderError);
    setRenderError(renderError?.message || 'Error desconocido durante el renderizado');
    
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 flex items-center justify-center">
        <div className="text-center bg-red-900/30 p-8 rounded-lg">
          <h1 className="text-2xl font-bold text-red-400 mb-4">Error</h1>
          <p className="text-red-300">Ha ocurrido un error al cargar la página</p>
          <button
            onClick={() => window.location.reload()}
            className="mt-4 px-6 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg"
          >
            Recargar página
          </button>
        </div>
      </div>
    );
  }
}