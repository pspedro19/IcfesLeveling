'use client';

import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import { Play, Clock, Star, BookOpen, Target, CheckCircle, Award, Brain, Zap, ChevronDown, ChevronRight, ExternalLink } from 'lucide-react';

interface ClaudeVideo {
  id: string;
  youtube_id: string;
  title: string;
  url: string;
  channel: string;
  duration_minutes: number;
  xp: number;
  recommendation_reason: string;
}

interface ClaudeUnit {
  unit_number: number;
  title: string;
  description: string;
  priority: string;
  videos: ClaudeVideo[];
  learning_objectives: string[];
  rationale: string;
}

interface ClaudeStudyPlan {
  success: boolean;
  plan_id: string;
  plan_data: {
    metadata: {
      ai_generated: boolean;
      generator: string;
      total_units: number;
      total_videos: number;
      subject_name: string;
    };
    units: ClaudeUnit[];
    study_strategy: string;
    additional_tips: string[];
  };
}

export default function ClaudeStudyPlanPage() {
  const searchParams = useSearchParams();
  const testId = searchParams.get('test_id');
  const subjectId = searchParams.get('subject_id') || '550e8400-e29b-41d4-a716-446655440001';

  const [studyPlan, setStudyPlan] = useState<ClaudeStudyPlan | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedVideo, setSelectedVideo] = useState<ClaudeVideo | null>(null);
  const [expandedUnits, setExpandedUnits] = useState<Set<number>>(new Set([1]));
  const [completedVideos, setCompletedVideos] = useState<Set<string>>(new Set());

  useEffect(() => {
    const loadPlan = async () => {
      try {
        setLoading(true);
        const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:4000';

        const response = await fetch(`${API_URL}/api/v1/claude-study-plan/generate`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            test_id: testId || '7efe8020-6ccf-4685-bb50-39a299c08b8d',
            subject_id: subjectId
          })
        });

        if (response.ok) {
          const data = await response.json();
          setStudyPlan(data);
          // Auto-select first video
          if (data.plan_data.units.length > 0 && data.plan_data.units[0].videos.length > 0) {
            setSelectedVideo(data.plan_data.units[0].videos[0]);
          }
        } else {
          throw new Error('Error generando plan de estudio');
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Error desconocido');
      } finally {
        setLoading(false);
      }
    };

    loadPlan();
  }, [testId, subjectId]);

  const toggleUnit = (unitNumber: number) => {
    setExpandedUnits(prev => {
      const newSet = new Set(prev);
      if (newSet.has(unitNumber)) {
        newSet.delete(unitNumber);
      } else {
        newSet.add(unitNumber);
      }
      return newSet;
    });
  };

  const markVideoComplete = (videoId: string) => {
    setCompletedVideos(prev => new Set([...prev, videoId]));
  };

  const getYouTubeEmbedUrl = (video: ClaudeVideo) => {
    // Extract YouTube ID from URL or use youtube_id
    let videoId = video.youtube_id;

    if (!videoId && video.url) {
      // Try to extract from URL
      const match = video.url.match(/(?:youtube\.com\/watch\?v=|youtu\.be\/)([^&\s]+)/);
      if (match) {
        videoId = match[1];
      }
    }

    return videoId ? `https://www.youtube.com/embed/${videoId}?rel=0` : null;
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 text-white flex items-center justify-center">
        <div className="text-center">
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
            className="w-16 h-16 border-4 border-blue-500 border-t-transparent rounded-full mx-auto mb-4"
          />
          <h2 className="text-2xl font-bold mb-2 flex items-center justify-center gap-2">
            <Brain className="w-6 h-6" />
            Claude AI Generando Plan...
          </h2>
        </div>
      </div>
    );
  }

  if (error || !studyPlan) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 text-white flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-bold mb-4">Error al cargar el plan</h2>
          <p className="text-red-300">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      {/* Header estilo Coursera */}
      <header className="bg-gray-800 border-b border-gray-700 px-6 py-4 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold text-white">
              {studyPlan.plan_data.metadata.subject_name}
            </h1>
            <p className="text-sm text-gray-400">
              Plan de Estudio Personalizado • {studyPlan.plan_data.metadata.total_videos} Videos
            </p>
          </div>
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2 text-sm">
              <CheckCircle className="w-4 h-4 text-green-400" />
              <span>{completedVideos.size} / {studyPlan.plan_data.metadata.total_videos} completados</span>
            </div>
          </div>
        </div>
      </header>

      <div className="flex max-w-7xl mx-auto">
        {/* Sidebar izquierdo - Lista de videos estilo Coursera */}
        <aside className="w-96 bg-gray-800 border-r border-gray-700 h-[calc(100vh-73px)] overflow-y-auto">
          <div className="p-4">
            <h2 className="text-lg font-bold mb-4 flex items-center gap-2">
              <BookOpen className="w-5 h-5" />
              Contenido del Curso
            </h2>

            <div className="space-y-2">
              {studyPlan.plan_data.units.map((unit) => {
                const isExpanded = expandedUnits.has(unit.unit_number);
                const unitVideosCompleted = unit.videos.filter(v => completedVideos.has(v.id)).length;
                const totalUnitVideos = unit.videos.length;

                return (
                  <div key={unit.unit_number} className="bg-gray-700 rounded-lg overflow-hidden">
                    {/* Unit Header */}
                    <button
                      onClick={() => toggleUnit(unit.unit_number)}
                      className="w-full px-4 py-3 flex items-center justify-between hover:bg-gray-600 transition-colors"
                    >
                      <div className="flex items-center gap-3 flex-1 text-left">
                        {isExpanded ? (
                          <ChevronDown className="w-4 h-4 text-gray-400" />
                        ) : (
                          <ChevronRight className="w-4 h-4 text-gray-400" />
                        )}
                        <div className="flex-1">
                          <div className="font-semibold text-sm text-white">
                            Unidad {unit.unit_number}: {unit.title}
                          </div>
                          <div className="text-xs text-gray-400 mt-1">
                            {unitVideosCompleted}/{totalUnitVideos} videos completados
                          </div>
                        </div>
                      </div>
                      {unitVideosCompleted === totalUnitVideos && totalUnitVideos > 0 && (
                        <CheckCircle className="w-5 h-5 text-green-400" />
                      )}
                    </button>

                    {/* Video List */}
                    <AnimatePresence>
                      {isExpanded && (
                        <motion.div
                          initial={{ height: 0 }}
                          animate={{ height: 'auto' }}
                          exit={{ height: 0 }}
                          transition={{ duration: 0.2 }}
                          className="overflow-hidden"
                        >
                          <div className="px-4 py-2 space-y-1">
                            {unit.videos.map((video, idx) => {
                              const isSelected = selectedVideo?.id === video.id;
                              const isCompleted = completedVideos.has(video.id);

                              return (
                                <button
                                  key={video.id}
                                  onClick={() => setSelectedVideo(video)}
                                  className={`w-full px-3 py-2 rounded text-left flex items-center gap-3 transition-colors ${
                                    isSelected
                                      ? 'bg-blue-600 text-white'
                                      : 'hover:bg-gray-600 text-gray-300'
                                  }`}
                                >
                                  {isCompleted ? (
                                    <CheckCircle className="w-4 h-4 text-green-400 flex-shrink-0" />
                                  ) : (
                                    <Play className="w-4 h-4 flex-shrink-0" />
                                  )}
                                  <div className="flex-1 min-w-0">
                                    <div className="text-sm font-medium truncate">
                                      {video.title}
                                    </div>
                                    <div className="text-xs opacity-75 flex items-center gap-2 mt-1">
                                      <Clock className="w-3 h-3" />
                                      {video.duration_minutes} min
                                    </div>
                                  </div>
                                </button>
                              );
                            })}
                          </div>
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </div>
                );
              })}
            </div>
          </div>
        </aside>

        {/* Main content - Video Player estilo Coursera */}
        <main className="flex-1 bg-gray-900">
          {selectedVideo ? (
            <div className="h-full">
              {/* Video Player */}
              <div className="bg-black aspect-video w-full">
                {getYouTubeEmbedUrl(selectedVideo) ? (
                  <iframe
                    src={getYouTubeEmbedUrl(selectedVideo)!}
                    className="w-full h-full"
                    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                    allowFullScreen
                    title={selectedVideo.title}
                  />
                ) : (
                  <div className="w-full h-full flex items-center justify-center bg-gray-800">
                    <div className="text-center">
                      <p className="text-gray-400 mb-4">Video no disponible</p>
                      <a
                        href={selectedVideo.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-blue-400 hover:text-blue-300 flex items-center gap-2 justify-center"
                      >
                        Ver en YouTube
                        <ExternalLink className="w-4 h-4" />
                      </a>
                    </div>
                  </div>
                )}
              </div>

              {/* Video Info */}
              <div className="p-6">
                <div className="max-w-4xl">
                  <h2 className="text-2xl font-bold mb-2">{selectedVideo.title}</h2>
                  <div className="flex items-center gap-4 text-sm text-gray-400 mb-4">
                    <span className="flex items-center gap-1">
                      <Clock className="w-4 h-4" />
                      {selectedVideo.duration_minutes} minutos
                    </span>
                    <span>•</span>
                    <span>{selectedVideo.channel}</span>
                    <span>•</span>
                    <span className="flex items-center gap-1 text-yellow-400">
                      <Zap className="w-4 h-4" />
                      {selectedVideo.xp} XP
                    </span>
                  </div>

                  {selectedVideo.recommendation_reason && (
                    <div className="bg-blue-900/30 border border-blue-500/30 rounded-lg p-4 mb-4">
                      <h3 className="font-semibold mb-2 flex items-center gap-2">
                        <Brain className="w-4 h-4" />
                        Por qué este video es importante
                      </h3>
                      <p className="text-gray-300 text-sm">{selectedVideo.recommendation_reason}</p>
                    </div>
                  )}

                  {/* Action Buttons */}
                  <div className="flex gap-3 mt-6">
                    {!completedVideos.has(selectedVideo.id) ? (
                      <button
                        onClick={() => markVideoComplete(selectedVideo.id)}
                        className="px-6 py-3 bg-green-600 hover:bg-green-700 text-white font-semibold rounded-lg flex items-center gap-2 transition-colors"
                      >
                        <CheckCircle className="w-5 h-5" />
                        Marcar como completado
                      </button>
                    ) : (
                      <div className="px-6 py-3 bg-green-600/20 border border-green-500 text-green-400 font-semibold rounded-lg flex items-center gap-2">
                        <CheckCircle className="w-5 h-5" />
                        Completado
                      </div>
                    )}

                    <a
                      href={selectedVideo.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="px-6 py-3 bg-gray-700 hover:bg-gray-600 text-white font-semibold rounded-lg flex items-center gap-2 transition-colors"
                    >
                      Ver en YouTube
                      <ExternalLink className="w-4 h-4" />
                    </a>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div className="h-full flex items-center justify-center">
              <div className="text-center">
                <BookOpen className="w-16 h-16 text-gray-600 mx-auto mb-4" />
                <h3 className="text-xl font-semibold text-gray-400">
                  Selecciona un video para comenzar
                </h3>
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
